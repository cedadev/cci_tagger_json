# encoding: utf-8
"""
"""
__author__ = 'Richard Smith'
__date__ = '27 Jan 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from directory_tree import DatasetNode
import os
import json
from pathlib import Path
from cci_tagger_json.utils import nested_get
import re


class DatasetJSONMappings:

    # A mapping between the datasets and the filepath to the JSON file
    # containing the mappings
    _json_lookup = {}

    # Place to cache the loaded mappings from the JSON files once they are required
    # in the processing
    _user_json_cache = {}

    # Place to store mappings between datasets and realisation
    _dataset_realisations = {}


    def __init__(self, json_files=None):
        """
        :param json_files: A collection of json files to read in. Defaults to None.
        This means that the local json files will be loaded.
        """

        # Init tree
        if json_files is None:
            json_files = list()
        self._dataset_tree = DatasetNode()

        # Load local JSON files
        if not json_files:
            path_root = os.path.dirname(os.path.abspath(__file__))
            json_files = Path('/').glob(os.path.join(path_root[1:], 'json/**/*.json'))

        # Read all the json files and build a tree of datasets
        for file in json_files:

            with open(file) as json_input:
                try:
                    data = json.load(json_input)
                except json.decoder.JSONDecodeError as e:
                    print(f'Error loading {file}: {e}')
                    continue

                for dataset in data.get('datasets',[]):

                    # Strip trailing slash
                    if dataset.endswith('/'):
                        dataset = dataset[:-1]

                    self._dataset_tree.add_child(dataset)
                    self._json_lookup[dataset] = file

                # Add the realisations
                realisations = data.get('realisations', {})
                for dataset in realisations:
                    self._dataset_realisations[dataset] = realisations[dataset]

    def get_dataset(self, path):
        """
        Returns the dataset which directly matches the given file path
        :param path: Filepath to match (String)
        :return: Dataset (string) | default: None
        """

        ds = self._dataset_tree.search_name(path)

        if ds:
            return ds[:-1]

        return path

    def get_user_defined_mapping(self, dataset):
        """
        Load the relevant JSON file and return the "mappings" section.
        Will return {} if no mapping found.
        :return: mappings (dict) | {}
        """

        data = self.load_mapping(dataset)

        return data.get('mappings', {})

    def load_mapping(self, dataset):
        """
        Handles lazy loading of the file
        :param dataset:
        :return: json_data (Dict)
        """
        json_data = {}

        # Look up the mapping file
        mapping_file = self._json_lookup.get(dataset)

        if mapping_file:

            json_data = self._user_json_cache.get(dataset)

            # If the file hasn't been loaded yet, read the contents of the file
            # and store
            if json_data is None:

                with open(mapping_file) as reader:
                    json_data = json.load(reader)
                    self._user_json_cache[dataset] = json_data

        return json_data

    def get_user_defined_defaults(self, dataset):
        """
        Load the relevant JSON file and return the "defaults" section.
        Will return {} if no defaults found.
        :param dataset: (string)
        :return: defaults (dict) | {}
        """

        data = self.load_mapping(dataset)

        return data.get('defaults', {})

    def get_merged_attribute(self, dataset, attr):
        """
        In some cases, the attribute from the file is a merged list of many attributes.
        This method maps a complex string to a simpler comma separated string
        which can be used in the next steps of the code.
        :param dataset: Dataset we are working with
        :param attr: The attribute to map
        :return: The mapped term or original string if no map found
        """

        # Load the mapping
        mappings = self.get_user_defined_mapping(dataset)

        merged = mappings.get('merged')

        # Check if there is a merged attribute in the mapping
        if merged:
            mapped_val = merged.get(attr)

            # Return the mapped value, if there is one
            if mapped_val:
                return mapped_val

        # Defaults to returning the input attribute
        return attr

    def get_user_defined_overrides(self, dataset):
        """
        Load the relevant JSON file and return the overrides section.
        Will return None if no overrides found.
        :param dataset: (string)
        :return: overrides (dict) | None
        """

        data = self.load_mapping(dataset)

        return data.get('overrides')

    def get_dataset_realisation(self, dataset, filepath):
        """
        Get the realisation for the specified dataset.
        Returns 'r1' if no user defined realisations.
        The filepath is used to match against a filter, if there is one.

        Order:
         - Default realisation 'r1'
         - Checks to see if there a dataset specific realisation
         - Checks to see if there is a filter to hone the realisation

        :param dataset: (string)
        :param filepath: (string)
        :return: realisation (string) | 'r1'
        """

        # Set default
        realisation = 'r1'

        # Load the relevant json file
        data = self.load_mapping(dataset)

        # Check for dataset level realisation mappings
        keys = ('realisations',dataset)
        if nested_get(keys, data):
            realisation = nested_get(keys, data)

        # Check if there are filters
        keys = ('filters',dataset)
        if nested_get(keys, data):
            filename = os.path.basename(filepath)

            # Check file against all filters
            for filter in nested_get(keys, data):
                m = re.match(filter['pattern'],filename)

                if m:
                    ds_real = filter.get('realisation')
                    if ds_real:
                        realisation = ds_real
                    break

        return realisation


if __name__ == '__main__':

    files = ['/neodc/esacci/sea_surface_salinity/data/v01.8/30days/2013/ESACCI-SEASURFACESALINITY-L4-SSS-MERGED_OI_Monthly_CENTRED_15Day_25km-20130101-fv1.8.nc',
             '/neodc/esacci/sea_surface_salinity/data/v01.8/7days/2014/ ESACCI-SEASURFACESALINITY-L4-SSS-MERGED_OI_7DAY_RUNNINGMEAN_DAILY_25km-20140101-fv1.8.nc']

    tree = DatasetJSONMappings(None)

    for file in files:
        print("Dataset")
        ds = tree.get_dataset(file)
        print(ds)
        print()

        print("Mapping")
        print(tree.get_user_defined_mapping(ds))
        print()

        print("Defaults")
        print(tree.get_user_defined_defaults(ds))
        print()

        print("Overrides")
        print(tree.get_user_defined_overrides(ds))
        print()

        print("Realisation")
        print(tree.get_user_defined_overrides(ds))
        print()

        print(tree._json_lookup)
