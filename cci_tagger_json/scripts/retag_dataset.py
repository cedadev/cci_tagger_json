# encoding: utf-8
"""
CI script to submit changed dataset files to be re-tagged
"""
__author__ = 'Richard Smith'
__date__ = '12 Jun 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from git import Repo
import os
import json
from ceda_elasticsearch_tools.elasticsearch import CEDAElasticsearchClient
from elasticsearch.helpers import scan
import pika
from datetime import datetime
import argparse

class RabbitMQConnection(object):
    """Handles the connection with the RabbitMQ service"""

    def __init__(self, user, password, host, vhost, exchange):

        # Get the username and password for rabbit
        rabbit_user = user
        rabbit_password = password

        # Get the opensearch exchange
        self.exchange = exchange

        # Start the rabbitMQ connection
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host,
                credentials=pika.PlainCredentials(rabbit_user, rabbit_password),
                virtual_host=vhost,
                heartbeat=300
            )
        )

        # Create a new channel
        channel = connection.channel()

        # Declare relevant exchanges
        channel.exchange_declare(exchange=self.exchange, exchange_type='topic')

        self.channel = channel

    @staticmethod
    def create_message(path, action):
        """
        Create message to add to rabbit queue. Message matches format of deposit logs.
        date_time:path:action:size:message

        :param path: Full logical path to file
        :param action: Action constant
        :return: string which matches deposit log format
        """
        time = datetime.now().isoformat(sep='-')

        return json.dumps({
            'datetime': time,
            'filepath': path,
            'action': action.upper(),
            'filesize': 0,
            'message': ''
        })

    def publish_message(self, msg, routing_key=''):
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=msg
        )


def get_changed_files(repo_path):
    """
    Get the diff between the two most recent commits and return
    a list of changed files

    :param repo_path: path which contains the .git dir
    :return: list of file paths relative to the repo_path
    """

    repo = Repo(repo_path)
    hcommit = repo.head.commit

    # Compare with last commit
    diff_with_last = hcommit.diff('HEAD~1')

    # Get list of changed files, excluding deletion events
    return [item.b_path for item in diff_with_last if not item.deleted_file]


def get_dataset_filelist(dataset):
    """
    Query Elasticsearch for the list of files in the changed dataset
    :param dataset: path to root of dataset
    :return: list of file paths
    """

    query = {
        "_source": {
            "includes": ["info.directory", "info.name"]
        },
        "query": {
            "match_phrase_prefix": {
                "info.directory.analyzed": dataset
            }
        }
    }

    es = CEDAElasticsearchClient()
    results = scan(es, query=query, index='opensearch-files')

    file_list = [
        os.path.join(
            item['_source']['info']['directory'],
            item['_source']['info']['name']
        ) for item in results
    ]

    return file_list


def get_commandline_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--user', help='rabbitMQ username', required=True)
    parser.add_argument('--password', help='rabbitMQ password', required=True)
    parser.add_argument('--host', help='rabbitMQ server', required=True)
    parser.add_argument('--vhost', help='rabbitMQ vhost', required=True)
    parser.add_argument('--exchange', help='rabbitMQ exchange name', required=True)

    return parser.parse_args()


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    repo_path = os.path.join(base, '../../')
    args = get_commandline_args()

    # Connect to rabbitMQ
    rabbit_connection = RabbitMQConnection(**args.__dict__)

    changed_files = get_changed_files(repo_path)

    for file in changed_files:

        # Only want to track the changes in the JSON directory
        if file.startswith('cci_tagger_json/json'):
            with open(os.path.join(base, '../../', file)) as reader:
                data = json.load(reader)
                datasets = data['datasets']

                # Loop the datasets in the changed files
                for dataset in datasets:

                    # Push message to trigger rescan of files in dataset
                    for item in get_dataset_filelist(dataset):
                        msg = rabbit_connection.create_message(item, 'DEPOSIT')
                        rabbit_connection.publish_message(msg, routing_key='opensearch.tagger.cci')


if __name__ == '__main__':
    main()
