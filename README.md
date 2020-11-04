# CCI Tagger JSON

This is the store and interface for the CCI JSON files which aim to correct mistakes
in the metadata and translate values found in the file and filepath to the controlled
vocab.

## Installing

This can be installed using pip

pip install git+https://github.com/cedadev/cci_tagger_json.git

## Writing JSON files

An example JSON file can be found at [example.json](cci_tagger_json/example_json/example.json)

JSON Files have these attributes which you can find more detail about below:

- [Datasets](#datasets)
- [Filters](#filters)
- [Mappings](#mappings)
- [Defaults](#defaults)
- [Realisations](#realisations)
- [Overrides](#overrides)
- [Aggregations](#aggregations)


Keys to use as facets

| Facet | Key |
| ----- | --- |
| BROADER_PROCESSING_LEVEL | 'broader_processing_level' |
| DATA_TYPE | 'data_type' |
| ECV | 'ecv' |
| FREQUENCY | 'time_coverage_resolution' |
| INSTITUTION | 'institution' |
| PLATFORM | 'platform' |
| PLATFORM_PROGRAMME | 'platform_programme' |
| PLATFORM_GROUP | 'platform_group' |
| PROCESSING_LEVEL | 'processing_level' |
| PRODUCT_STRING | 'product_string' |
| PRODUCT_VERSION | 'product_version' |
| SENSOR | 'sensor'

### Datasets

<table>
<tr>
    <th>Description</th>
    <td>List of Dataset path that this file applies to</td>
</tr>
<tr>
    <th>Structure</th>
    <td>Array</td>
</tr>
<tr>
    <th>Example</th>
    <td>
    <pre>
"datasets": [
    "/path/1",
    "/path/2"
]
    </pre>
    </td>
</tr>
</table>


### Filters

<table>
<tr>
    <th>Description</th>
    <td>Allows you to match different files in the same dataset to different realisations.
    The patterns should be a regular expression to match against the filename
    </td>
</tr>
<tr>
    <th>Structure</th>
    <td>The filters element is a JSON object where the keys are dataset paths.
    The dataset path should then have an array of JSON objects.
    Each object should then have the pattern to match and the realisation to apply.
    <strong>Note: You can map to an <code>EXCLUDE</code> realisation to exclude files from getting a DRS</strong>
    </td>
</tr>
<tr>
    <th>Example</th>
    <td>
    <pre>
	"filters": {
		"/path/1": [
			{
				"pattern": ".*.nc",
				"realisation": "r1"
			},
			{
				"pattern": ".*.txt",
				"realisation": "text"
			},			
			{
				"pattern": ".*.error",
				"realisation": "EXCLUDE"
			}
		]
	}
    </pre>
    </td>
</tr>
</table>

### Mappings

<table>
<tr>
    <th>Description</th>
    <td>Mapping between values per facet. The merged attribute 
    handles labels which contain more than on element</td>
</tr>
<tr>
    <th>Structure</th>
    <td>JSON Object with facet values as keys</td>
</tr>
<tr>
    <th>Example</th>
    <td>
    <pre>
	"mappings": {
		"ecv": {
			"GHRSST": "sea surface temperature"
		},
		"time_coverage_resolution": {
			"daily": "day",
			"P01D": "day"
		},
		"institution": {
			"DTU Space - Div. of Geodynamics": "DTU Space",
			"DTU Space - Div. of Geodynamics and NERSC": "DTU Space"
		},
		"processing_level": {
			"level-3": "l3"
		},
		"platform": {
			"ERS2": "ERS-2",
			"ENV": "ENVISAT"
		},
		"sensor": {
			"AMSR-E": "AMSRE",
			"ATSR2": "ATSR-2"
		},
		"product_version": {
			"03.02.": "03.02"
		},
		"merged": {
			"MERISAATSR": "MERIS,AATSR"
		}
	}
    </pre>
    </td>
</tr>
</table>

### Defaults

<table>
<tr>
    <th>Description</th>
    <td>If no values are found in the file, these values will be used</td>
</tr>
<tr>
    <th>Structure</th>
    <td>JSON Object with facet names as keys</td>
</tr>
<tr>
    <th>Example</th>
    <td>
    <pre>
    "defaults": {
    "platform": "Nimbus-7",
    "sensor": "MERIS"
    }
    </pre>
    </td>
</tr>
</table>

### Realisations

<table>
<tr>
    <th>Description</th>
    <td>Mapping between the datasets and the realisation. Allows you to add 
    different realisations other than r1, r2 ... Also makes the tagging process
    repeatable</td>
</tr>
<tr>
    <th>Structure</th>
    <td>JSON Object. Dataset paths as keys</td>
</tr>
<tr>
    <th>Example</th>
    <td>
    <pre>
    "realisations": {
    "/path/1": "r2"
    }
    </pre>
    </td>
</tr>
</table>

### Overrides

<table>
<tr>
    <th>Description</th>
    <td>Regardless of what is found in the file, override this facet. All values should be a list
    but some facets can only accept a single value</td>
</tr>
<tr>
    <th>Structure</th>
    <td>JSON Object. Facets as keys. 
    Single value facets: <code>processing_level</code>, <code>ecv</code>, <code>data_type</code>, <code>product_string</code>
    </td>
</tr>
<tr>
    <th>Example</th>
    <td>
    <pre>
    "overrides": {
    "freq": ["day"],
    "institution": [],
    "platform": [],
    "sensor": []
}
    </pre>
    </td>
</tr>
</table>

### Aggregations

<table>
<tr>
    <th>Description</th>
    <td>Describes which files should be aggregated by providing a regular expression to match a DRS</td>
</tr>
<tr>
    <th>Structure</th>
    <td>Array. Each element is a JSON object with keys <code>pattern</code>, <code>wms</code></td>
</tr>
<tr>
    <th>Example</th>
    <td>
    <pre>
    "aggregations": [
    	{
        	"pattern": "*.r1",
                "wms": true
            }
    ]
    </pre>
    </td>
</tr>
</table>
