# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '19 Apr 2021'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

import subprocess
from typing import Tuple, List
import argparse
import os
import json
from ceda_elasticsearch_tools.elasticsearch import CEDAElasticsearchClient
from elasticsearch.helpers import scan
import pika
from datetime import datetime


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


def run_git_command(command: str) -> str:
    """
    Run git command and return output as a
    decoded string

    :param command: Command to run
    :return: Command output decoded
    """
    output = subprocess.check_output(
        command, shell=True
    )

    return output.decode('UTF-8')


def get_merge_hashes() -> Tuple[str, str]:
    """
    Get the last two merge commit hashes
    :return: head, prev
    """
    # Get the two commit hashes for last two merge commits

    git_command = "git log --merges -n 2 --pretty=format:'%h'"

    git_refs = run_git_command(git_command)

    # Split to get hea and prev merge
    head, prev = git_refs.split('\n')

    return head, prev


def get_changed_files() -> List:

    head, prev = get_merge_hashes()

    git_command = f"git log --name-only --pretty=oneline --full-index {prev}..{head} | grep -vE '^[0-9a-f]{{40}} ' | sort | uniq"

    changed_files = run_git_command(git_command)

    changed_files = changed_files.split('\n')

    return changed_files


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


def environ_or_required(key):
    return (
        {'default': os.environ.get(key)} if os.environ.get(key)
        else {'required': True}
    )


def get_command_line_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--rabbit-user', '-u', help='rabbitMQ username', **environ_or_required('RABBIT_USER')),
    parser.add_argument('--rabbit-password', '-p', help='rabbitMQ password', **environ_or_required('RABBIT_PASSWORD'))
    parser.add_argument('--rabbit-host', help='rabbitMQ server', **environ_or_required('RABBIT_HOST'))
    parser.add_argument('--rabbit-vhost', help='rabbitMQ vhost', **environ_or_required('RABBIT_VHOST'))
    parser.add_argument('--rabbit-exchange', help='rabbitMQ exchange name', **environ_or_required('RABBIT_EXCHANGE'))
    parser.add_argument('--dry-run', action='store_true')

    return parser.parse_args()


def main():

    base = os.path.dirname(os.path.abspath(__file__))
    repo_path = os.path.join(base, '../')
    args = vars(get_command_line_args())
    dry_run = args.pop('dry_run', False)

    print(args)

    rabbit_connection = RabbitMQConnection(**args)

    changed_files = get_changed_files()

    for file in changed_files:
        if dry_run:
            print()
            print(file)

        # Only want to track the changes in the JSON directory
        if file.startswith('cci_tagger_json/json'):
            with open(os.path.join(repo_path, file)) as reader:
                data = json.load(reader)
                datasets = data['datasets']

                # Loop the datasets in the changed files
                for dataset in datasets:

                    if dry_run:
                        print('\t',dataset)
                        continue

                    for item in get_dataset_filelist(dataset):
                        msg = rabbit_connection.create_message(item, 'DEPOSIT')
                        rabbit_connection.publish_message(msg, routing_key='opensearch.tagger.cci')


if __name__ == '__main__':
    main()