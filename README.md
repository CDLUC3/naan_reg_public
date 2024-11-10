# naan_reg_public

> [!IMPORTANT]
> This repository is deprecated and will be removed 2024-12-01.
>
> The authoritative source for NAAN records is the [`naan_reg_priv`](https://cdluc3.github.io/naan_reg_priv/) private
> repository. Publicly accessible information is avalable at https://cdluc3.github.io/naan_reg_priv/

This is a public representation of the information contained in the private NAAN registry records.

The content is expressed in JSON and is generated using a python script executed by a GitHub 
action that retrieves the current copy of the `main_naans` file from the 
[NAAN registry](https://github.com/CDLUC3/naan_reg_priv), parses the ANVL, and generates the 
JSON records as a [single JSON document](https://cdluc3.github.io/naan_reg_public/naans_public.json) and also as 
a [folder hierarchy of individual JSON records](https://cdluc3.github.io/naan_reg_public/naans/).

The artifacts are published using GitHub pages, accessible at:

[https://cdluc3.github.io/naan_reg_public/](https://cdluc3.github.io/naan_reg_public/)


## The conversion script

`scripts/naan_reg_json.py` provides a tool for converting NAAN registry ANVL to JSON. 

The script performs the following operations:

1. Generate public JSON representation of the private ANVL formatted NAAN records.
2. Augment the NAAN JSON file with a JSON representation of the `shoulder_registry` records.
3. Apply known corrections to the generated JSON through a list of manually configured "magic" files.

Note that several functions performed by this script will be deprecated in conjunction
with progression of the migration from the legacy N2T system in 2024. 


## Usage

```
$python scripts/naan_reg_json.py --help
Usage: naan_reg_json.py [OPTIONS] COMMAND [ARGS]...

  Generate JSON form of naan_reg_priv/main_naans and
  naan_reg_priv/shoulder_registry.

  This tool translates the NAAN and shoulder registry files from ANVL to JSON
  to assist downstream programmatic use.

Options:
  --help  Show this message and exit.

Commands:
  ezid-overrides             Overrides targets known to be managed by EZID.
  main-naans-to-json         Generate a JSON version of the main_naans file.
  shoulder-registry-to-json  Generate JSON representation of the shoulder_registry
```

Dependencies are listed in `scripts/requirements.txt`.


## Acknowledgement

This work is supported by the California Digital Library.
