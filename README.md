# naan_reg_public

This is a public representation of the information contained in the private NAAN registry records.

The content is expressed in JSON and is generated using a python script executed by a GitHub 
action that retrieves the current copy of the `main_naans` file from the 
[NAAN registry](https://github.com/CDLUC3/naan_reg_priv), parses the ANVL, and generates the 
JSON records as a [single JSON document](https://cdluc3.github.io/naan_reg_public/naans_public.json) and also as 
a [folder hierarchy of individual JSON records](https://cdluc3.github.io/naan_reg_public/naans/).

The artifacts are published using GitHub pages, accessible at:

[https://cdluc3.github.io/naan_reg_public/](https://cdluc3.github.io/naan_reg_public/)


## The conversion script

`naan_reg_json` provides a tool for converting NAAN registry ANVL to JSON. It 
includes JSON-schema with generated documentation for private and publicly 
visible NAAN records. 


## Usage

```
$python naan_reg_json.py --help
usage: naan_reg_json.py [-h] [-s] [-p] [path]

Generate JSON representation of naan_reg_priv/main_naans. This tool translates the 
NAAN registry file from ANVL to JSON to assist downstream programmatic use. If pydantic 
is installed then the script can output JSON schema describing the JSON respresentation 
of the transformed NAAN entries.

positional arguments:
  path          Path to naan_reg_priv ANVL file.

optional arguments:
  -h, --help    show this help message and exit
  -s, --schema  Generate JSON schema and exit.
  -p, --public  Output public content only.
```

For conversion from ANVL to JSON no additional dependencies are needed if using 
Python3.8 or later. E.g. (portions redacted):

```
$python naan_reg_json.py ../naan_reg_priv/main_naans

{
  "12025": {
    "what": "12025",
    "where": "http://www.nlm.nih.gov",
    "target": "http://www.nlm.nih.gov/$arkpid",
    "when": "2001-03-08T00:00:00+00:00",
    "who": {
      "name": "US National Library of Medicine",
      "acronym": null,
      "address": "#REDACTED#"
    },
    "na_policy": {
      "orgtype": "NP",
      "policy": "(:unkn) unknown",
      "tenure": "2001",
      "policy_url": null
    },
    "why": "ARK",
    "contact": {
      "name": "#REDACTED#",
      "unit": null,
      "tenure": null,
      "email": "#REDACTED#",
      "phone": "#REDACTED#"
    },
    "comments": null,
    "provider": null
  },
  ...
```

A public view of the ANVL to JSON can be generated using the `-p` or `--public` option:

```
$python naan_reg_json.py -p ../naan_reg_priv/main_naans

{
  "12025": {
    "what": "12025",
    "where": "http://www.nlm.nih.gov",
    "target": "http://www.nlm.nih.gov/$arkpid",
    "when": "2001-03-08T00:00:00+00:00",
    "who": {
      "name": "US National Library of Medicine",
      "acronym": null
    },
    "na_policy": {
      "orgtype": "NP",
      "policy": "(:unkn) unknown",
      "tenure": "2001",
      "policy_url": null
    }
  },
```

For JSON-schema generation, `pydantic` is required:
```
pip install pydantic
```

The public view and full view have different schemas, they can be generated like:
```
$python naan_reg_json.py -s > schema/naan_schema.json
```
and
```
$python naan_reg_json.py -s -p > schema/public/naan_schema.json
```

Schema documentation can be generated if `json-schema-for-humans` is installed:
```
pip install json-schema-for-humans
```

To generate the schema documentation:
```
generate-schema-doc --config-file docs_config.yaml ./schema/naan_schema.json ./schema/
generate-schema-doc --config-file docs_config.yaml ./schema/public/naan_schema.json ./schema/public/
```

## Acknowledgement

This work is supported by the California Digital Library.

