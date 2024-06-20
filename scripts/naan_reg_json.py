"""
Generate JSON form of naan_reg_priv/main_naans and naan_reg_priv/shoulder_registry.

This tool translates the NAAN and shoulder registry files from ANVL to JSON to
assist downstream programmatic use.

Note that there is a discrepancy betwen configuration details offered
by the "official" NAAN registry and entries managed by EZID. For example,
main_naans currently reports 54723 target as https://www.hoover.org/ark:$id
however, that NAAN is actually managed by EZID, and so the actual NAAN
target listed in the registry should be ttps://ezid.cdlib.org/ark:$id
since that service handles the resolution.

If pydantic is installed then the script can output JSON schema
describing the JSON representation of the transformed NAAN entries.

To generate the complete NAAN registry from the various ANVL sources,
there are three steps necessary:

1. Generate the NAAN JSON records from main_naans
2. Generate the Shoulder JSON records from shoulder_registry
3. Update NAAN records being managed by EZID using the
   entries from https://ezid.cdlib.org/static/info/shoulder-list.txt
"""

import copy
import dataclasses
import datetime
import json
import logging
import os
import os.path
import pathlib
import re
import sys
import typing
import urllib.parse

import click
import requests

import lib_naan
import lib_naan.anvl
import lib_naan.naans

PYDANTIC_AVAILABLE = False
try:
    from pydantic.dataclasses import dataclass

    PYDANTIC_AVAILABLE = True
except ModuleNotFoundError:
    from dataclasses import dataclass


# Global logger handle
_L = logging.getLogger("naan_reg_json")


class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles dataclasses and datetime instances."""

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, datetime.datetime):
            return o.isoformat(timespec="seconds")
        return super().default(o)


def generate_index_html2(naans, index):
    res = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<title>Public NAAN Records</title><meta charset="utf-8">',
        "</head>",
        "<body>",
        '<div id="naans">' '<input class="search" placeholder="Search" />',
        '<button class="sort" data-sort="name">Sort by name</button>',
        "<table><thead>",
        "<tr><th>NAAN</th><th>Name</th></tr>",
        '</thead><tbody class="list">',
    ]
    keys = list(index)
    keys.sort()
    counts = {}
    for k in keys:
        res.append(
            f'<tr><td class="naan">{k}</td><td class="name">{naans[k].who.name}</td></tr>'
        )
    res += [
        "</tbody>",
        "</table>",
        "</div>",
        '<script src="//cdnjs.cloudflare.com/ajax/libs/list.js/2.3.1/list.min.js"></script>',
        "<script>",
        "const options= {",
        '  valueNames: ["naan","name"]',
        "};",
        'let naanList = new List("naans", options);',
        "</script>",
        "</body>",
        "</html>",
    ]
    return "\n".join(res)

def generate_index_html(naans, index):
    res = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head><title>Public NAAN Records</title><meta charset="utf-8"></head>',
        '<body>',
    ]
    keys = list(index)
    keys.sort()
    counts = {}
    for k in keys:
        i = k[0]
        counts_entry = counts.get(i, {"n":0, "e":[]})
        counts_entry["n"] = counts_entry["n"] + 1
        counts_entry["e"].append({"naan": k, "name": naans[k].who.name})
        counts[i] = counts_entry
    for k,e in counts.items():
        res.append('<details>')
        res.append(f'<summary>Entries starting with {k} (n={e["n"]}):</summary>')
        res.append("<table>")
        res.append("<tr><th>NAAN</th><th>Name</th></tr>")
        for entry in e['e']:
            res.append(f"<tr><td><a href=\"{index[entry['naan']]}\">{entry['naan']}</a></td><td>{entry['name']}</td></tr>")
        res.append("</table>")
        res.append('</details>')
    res.append("</body></html>")
    return "\n".join(res)


def load_naan_shoulders(shoulder_src: str, public_only=False) -> dict[str, typing.Union[lib_naan.NAANShoulder, lib_naan.PublicNAANShoulder]]:
    anvl_parser = lib_naan.anvl.AnvlParser()
    res = {}
    for block in anvl_parser.parseBlocks(shoulder_src):
        shoulder = lib_naan.NAANShoulder.from_anvl_block(block)
        if shoulder is not None:
            if shoulder.key in res:
                raise ValueError("Key %s elready present", shoulder.key)
            if public_only:
                res[shoulder.key] = shoulder.as_public()
            else:
                res[shoulder.key] = shoulder
    return res


def naan_to_path_name(naan:str) -> dict[str, str]:
    res = {"path":"", "name":""}
    res["path"] = naan[0]
    res["name"] = f"{naan}.json"
    return res


def shoulder_to_path_name(naan:str, shoulder:str) -> dict[str, str]:
    res = naan_to_path_name(naan)
    res["path"] = os.path.join(res["path"], naan)
    res["name"] = f"{shoulder}.json"
    return res


def store_json_naan_record(dest_folder: str, record: typing.Union[lib_naan.NAAN, lib_naan.PublicNAAN])->str:
    path_name = naan_to_path_name(record.what)
    os.makedirs(os.path.join(dest_folder, path_name["path"]), exist_ok=True)
    fname = os.path.join(dest_folder, path_name["path"], path_name["name"])
    with open(fname, "w") as dest:
        json.dump(record, dest, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
    return fname


def store_json_shoulder_record(dest_folder: str, record:lib_naan.NAANShoulder)->str:
    path_name = shoulder_to_path_name(record.naan, record.shoulder)
    os.makedirs(os.path.join(dest_folder, path_name["path"]), exist_ok=True)
    fname = os.path.join(dest_folder, path_name["path"], path_name["name"])
    with open(fname, "w") as dest:
        json.dump(record, dest, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
    return fname


def store_json_record(dest_folder:str, record: typing.Union[lib_naan.PublicNAANShoulder, lib_naan.NAANShoulder, lib_naan.PublicNAAN, lib_naan.NAAN])->typing.Optional[str]:
    if isinstance(record, (lib_naan.NAANShoulder, lib_naan.PublicNAANShoulder)):
        return store_json_shoulder_record(dest_folder, record)
    if isinstance(record, (lib_naan.NAAN, lib_naan.PublicNAAN)):
        return store_json_naan_record(dest_folder, record)
    return None


def generate_json_schema(public_only: bool = False):
    if public_only:
        schema = lib_naan.PublicNAAN.__pydantic_model__.schema()
    else:
        schema = lib_naan.AAN.__pydantic_model__.schema()
    print(json.dumps(schema, indent=2))


def load_ezid_shoulder_list(url:str) -> typing.List[dict]:
    # regexp to match entries in the shoulder-list output
    re_ark = re.compile(
        r"\b(?P<PID>ark:/?(?P<prefix>[0-9]{5,10})\/(?P<value>\S+)?)\s+(?P<name>.*)",
        re.IGNORECASE | re.MULTILINE,
    )
    response = requests.get(url)
    if response.status_code == 200:
        _L.info("Shoulder list retrieved from %s", url)
        text = response.text
        result = re_ark.finditer(text)
        pids = []
        for row in result:
            pid = {
                "scheme": "ark",
                "prefix": row.group("prefix"),
                "value": "" if row.group("value") is None else row.group("value"),
                "name": "" if row.group("name") is None else row.group("name"),
            }
            pids.append(pid)
        return pids
    else:
        _L.error("HTTP response status %s. Failed to retrieve shoulder list from %s", response.status_code, url)
    return []


@click.group(name="naan_reg")
def click_main():
    logging.basicConfig(level=logging.DEBUG)
    pass


@click_main.command("main-naans-to-json")
@click.argument("anvl_source", type=click.Path(exists=True))
@click.option("-d", "--dest_path", default=pathlib.Path("naan_records.json"), type=click.Path(), help="JSON destination for NAANs. Existing is updated, path created if necessary.")
@click.option("-p", "--private", is_flag=True, help="Generate private JSON records.")
def naan_anvl_to_json(anvl_source:str, dest_path: pathlib.Path, private:bool):
    """Generate a JSON version of the main_naans file.

    The default behavior is to produce the public JSON naans file.
    """
    naan_src = open(anvl_source, "r").read()
    repo = lib_naan.naans.NaanRepository(dest_path)
    if dest_path.exists():
        repo.load()
        _L.info(f"Loaded {dest_path}")
    n = repo.load_naan_reg_priv(naan_src, as_public=not private)
    _L.info("Loaded %s records from %s", n, anvl_source)
    repo.store(as_public=not private)


@click_main.command("shoulder-registry-to-json")
@click.argument("anvl_source", type=click.Path(exists=True))
@click.option("-d", "--dest_path", default=pathlib.Path("naan_records.json"), type=click.Path(), help="JSON destination for NAANs. Existing is updated, path created if necessary.")
@click.option("-p", "--private", is_flag=True, help="Generate private JSON records.")
def shoulder_anvl_to_json(anvl_source:str, dest_path: pathlib.Path, private:bool):
    shoulder_src = open(anvl_source, "r").read()
    repo = lib_naan.naans.NaanRepository(dest_path)
    if dest_path.exists():
        repo.load()
        _L.info(f"Loaded {dest_path}")
    n = repo.load_shoulder_registry(shoulder_src, as_public=not private)
    _L.info("Loaded %s records from %s", n, anvl_source)
    repo.store(as_public=not private)


@click_main.command()
@click.option(
    "-e",
    "--ezid_shoulders_url",
    default="https://ezid.cdlib.org/static/info/shoulder-list.txt",
    help="URL for the EZID shoulder list."
)
@click.option("-d", "--dest_folder", default=".")
def ezid_overrides(ezid_shoulders_url, dest_folder):
    ezid_exceptions = [
        "87602",
        "21549",
    ]
    fname = os.path.join(dest_folder, "naan_records.json")
    existing = {}
    if os.path.exists(fname):
        with open(fname, "r") as inf:
            existing = json.load(inf)
    if len(existing) == 0:
        raise ValueError("Must load NAANs before running ezid_overrides")
    ezid_shoulder_list = load_ezid_shoulder_list(ezid_shoulders_url)
    if len(ezid_shoulder_list) == 0:
        raise ValueError("EZID shoulder list could not be loaded. Aborting.")
    for entry in ezid_shoulder_list:
        # Find a matching existing record
        # either a NAAN or a Shoulder entry
        shoulder_key:typing.Optional[str] = None
        shoulder_record:typing.Optional[dict[str,typing.Any]] = None
        naan_key = entry["prefix"]
        if naan_key in ezid_exceptions:
            _L.warning("Imposing ezid_exception for NAAN %s", naan_key)
            continue
        naan_record = existing.get(naan_key, None)
        if len(entry["value"]) > 0:
            shoulder_key = f'{entry["prefix"]}/{entry["value"]}'
            shoulder_record = existing.get(shoulder_key, None)
        if shoulder_record is not None:
            # check the target url. If netloc is arks.org then override, otherwise leave it be.
            url = urllib.parse.urlsplit(shoulder_record["target"]["url"], scheme="https")
            if url.netloc == "arks.org":
                shoulder_record["target"]["url"] = "https://ezid.cdlib.org/$arkpid"
                existing[shoulder_key] = shoulder_record
                _L.info("Updated %s shoulder record with ezid target", shoulder_key)
                continue
            _L.warning("Skipping override of existing shoulder record %s / %s", shoulder_record["naan"], shoulder_record["shoulder"])
            continue
        if naan_record is None:
            _L.error("Existing NAAN record not found for EZID record %s / %s", entry["prefix"], entry["value"])
            continue
        if shoulder_key is not None and shoulder_record is None:
            # create a new record based on the naan record.
            shoulder_record = copy.deepcopy(naan_record)
            shoulder_record["rtype"] = "shoulder"
            shoulder_record["naan"] = naan_key
            shoulder_record["shoulder"] = shoulder_record["what"]
            del shoulder_record["what"]
            shoulder_record["who"]["name"] = entry["name"]
            shoulder_record["who"]["acronym"] = None
            shoulder_record["target"]["url"] = "https://ezid.cdlib.org/$arkpid"
            existing[shoulder_key] = shoulder_record
            continue

        # Replace the target URL with ezid.cdlib.org
        _L.info("EZID %s %s updating record %s %s", entry["prefix"], entry["value"], naan_key, naan_record["target"]["url"])
        naan_record["target"]["url"] = "https://ezid.cdlib.org/$arkpid"
        existing[naan_key] = naan_record
    with open(fname, "w") as dest:
        json.dump(existing, dest, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
        _L.info("Wrote EZID updated records to %s", fname)


@click_main.command()
def generate_schema():
    pass


if __name__ == "__main__":
    sys.exit(click_main())
