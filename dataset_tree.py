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


class DatasetJSONMappings:

    # A mapping between the datasets and the filepath to the JSON file
    # containing the mappings
    _json_lookup = {}

    # Place to cache the loaded mappings from the JSON files once they are required
    # in the processing
    _user_json_cache = {}

    # Place to cache the loaded mappings and URI lookups from the JSON files once
    # they are required in the processing
    _user_uri_cache = {}

    # Place to store mappings between datasets and realisation
    _dataset_realisations = {}


    def __init__(self, json_dir):

        # Init tree
        self._dataset_tree = DatasetNode()

        # Get list of all JSON files
        if json_dir:
            # TODO: Fix issue where this can't handle non relative paths
            json_files = Path().glob(os.path.join(json_dir, '**/*.json'))
        else:
            json_files = []

        # Read all the json files and build a tree of datasets
        for file in json_files:

            with open(file) as json_input:
                try:
                    data = json.load(json_input)
                except json.decoder.JSONDecodeError:
                    print(f'Error loading {file}')
                    continue

                for dataset in data.get('datasets',[]):
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

    def get_dataset_realisation(self, dataset):
        """
        Get the realisation for the specified dataset.
        Returns 'r1' if no user defined realisations.
        :param dataset: (string)
        :return: realisation (string) | 'r1'
        """

        realisation = 'r1'

        ds_real = self._dataset_realisations.get(dataset)

        if ds_real:
            realisation = ds_real

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
