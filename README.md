# CCI Tagger JSON

This is the store and interface for the CCI JSON files which aim to correct mistakes
in the metadata and translate values found in the file and filepath to the controlled
vocab.

## Installing

This can be installed using pip

pip install git+https://github.com/cedadev/cci_tagger_json.git

## Writing JSON files
An example JSON file can be found at [example.json](cci_tagger_json/cci_tagger_json/json/example.json)

### datasets
| Description: | List of Dataset path that this file applies to |
| Structure: | Python list |

Example:
```python
"datasets": [
    "/path/1",
    "/path/2"
]
```

### filters
### mappings
### defaults
### realisations
### overrides

## Checking JSON files

The interface will read all JSON files in the JSON directory