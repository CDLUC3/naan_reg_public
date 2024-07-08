"""
Copyright©2024, Regents of the University of California

License: https://opensource.org/license/mit, See LICENSE

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
import datetime
import json
import logging
import os.path
import pathlib
import re
import sys
import typing

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
    pass

# Global logger handle
_L = logging.getLogger("naan_reg_json")

MAGIC_PATH = "./magic"
EZID_SHOULDER_FILE = os.path.join(MAGIC_PATH, "shoulder-list.txt")

def generate_json_schema(public_only: bool = False):
    if public_only:
        schema = lib_naan.PublicNAAN.__pydantic_model__.schema()
    else:
        schema = lib_naan.AAN.__pydantic_model__.schema()
    print(json.dumps(schema, indent=2))


def generate_shadow_ark_config() -> list[lib_naan.PublicNAAN]:
    """ This is a very unfortunate situation where "shadow arks" are apparently
    being used in the wild. Shadow arks are used internally by the EZID
    infrastructure, but somehow these got exposed and need to be resolvable
    from the Internet. So we inject them into the configuration here.
    """
    wild_shadow_prefixes = [
        {'prefix': 'b6071', 'test': 'ark:/b6071/m3z07d'},
        {'prefix': 'b7291', 'test': 'ark:/b7291/d1wc74'},
        {'prefix': 'b5060', 'test': 'ark:/b5060/d8bc75'},
        {'prefix': 'b7272', 'test': 'ark:/b7272/q6ms3qnx'},
        {'prefix': 'b7280', 'test': 'ark:/b7280/d1988w'},
        {'prefix': 'b6078', 'test': 'ark:/b6078/d1mw2k'},
    ]
    shadows = []
    for entry in wild_shadow_prefixes:
        shadow = lib_naan.PublicNAAN(
            what=entry['prefix'],
            where="https://ezid.cdlib.org/",
            target=lib_naan.Target(
                url=f"https://doi.org/10.{entry['prefix'][1:]}/$" + "{value}",
                http_code=302
            ),
            when=datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.timezone.utc),
            who=lib_naan.PublicNAAN_who(
                name="CDLIB EZID",
                acronym="EZID"
            ),
            na_policy=lib_naan.NAAN_how(
                orgtype="NP",
                policy="NR",
                tenure="1970",
                policy_url=""
            ),
            test_identifier=entry['test'],
            service_provider=None,
        )
        shadows.append(shadow)
    return shadows


def load_ezid_shoulder_list(url: str) -> typing.List[dict]:
    # regexp to match entries in the shoulder-list output
    re_ark = re.compile(
        r"\b(?P<PID>ark:/?(?P<prefix>[0-9]{5,10})\/(?P<value>\S+)?)\s+(?P<name>.*)",
        re.IGNORECASE | re.MULTILINE,
    )
    text = None
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            _L.info("Shoulder list retrieved from %s", url)
            text = response.text
        else:
            _L.error("HTTP response status %s. Failed to retrieve shoulder list from %s", response.status_code, url)
    except Exception as e:
        _L.error("Exception trying to access remote EZID shoulders: %s", e)
    if text is None:
        _L.info("Falling back to local copy of EZID shoulder list.")
        if os.path.exists(EZID_SHOULDER_FILE):
            with open(EZID_SHOULDER_FILE, "r") as f:
                text = f.read()
        else:
            _L.error("Unable to load EZID shoulders.")
            return []
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


def shoulder_from_naan(naan: typing.Union[lib_naan.NAAN, lib_naan.PublicNAAN]) -> typing.Union[
    lib_naan.NAANShoulder, lib_naan.PublicNAANShoulder]:
    shoulder = lib_naan.NAANShoulder(
        shoulder="",
        naan=naan.what,
        who=copy.deepcopy(naan.who),
        where=naan.where,
        target=copy.deepcopy(naan.target),
        when=naan.when,
        na_policy=copy.deepcopy(naan.na_policy)
    )
    if isinstance(naan, lib_naan.PublicNAAN):
        return shoulder.as_public()
    shoulder.alternate_contact = copy.deepcopy(naan.alternate_contact)
    shoulder.comments = copy.deepcopy(naan.comments)
    shoulder.provider = copy.deepcopy(naan.provider)
    return shoulder


@click.group(name="naan_reg")
def click_main():
    """
    Generate JSON form of naan_reg_priv/main_naans and naan_reg_priv/shoulder_registry.

    This tool translates the NAAN and shoulder registry files from ANVL to JSON to
    assist downstream programmatic use.
    """
    logging.basicConfig(level=logging.INFO)
    pass


@click_main.command("main-naans-to-json")
@click.argument("anvl_source", type=click.Path(exists=True))
@click.option("-d", "--dest_path", default=pathlib.Path("naan_records.json"), type=click.Path(),
              help="JSON destination for NAANs. Existing is updated, path created if necessary.")
@click.option("-p", "--private", is_flag=True, help="Generate private JSON records.")
def naan_anvl_to_json(anvl_source: str, dest_path: pathlib.Path, private: bool):
    """Generate a JSON version of the main_naans file.

    The default behavior is to produce the public JSON naans file.
    """
    if isinstance(dest_path, str):
        dest_path = pathlib.Path(dest_path)
    naan_src = open(anvl_source, "r").read()
    repo = lib_naan.naans.NaanRepository(dest_path)
    #if len(repo) < 1:
    #    _L.info("Installing shadows.")
    #    shadows = generate_shadow_ark_config()
    #    for shadow in shadows:
    #        repo.insert(shadow)
    if dest_path.exists():
        repo.load()
        _L.info(f"Loaded {dest_path}")
    n = repo.load_naan_reg_priv(naan_src, as_public=not private)
    _L.info("Loaded %s records from %s", n, anvl_source)
    repo.store(as_public=not private)


@click_main.command("shoulder-registry-to-json")
@click.argument("anvl_source", type=click.Path(exists=True))
@click.option("-d", "--dest_path", default=pathlib.Path("naan_records.json"), type=click.Path(),
              help="JSON destination for NAANs. Existing is updated, path created if necessary.")
@click.option("-p", "--private", is_flag=True, help="Generate private JSON records.")
def shoulder_anvl_to_json(anvl_source: str, dest_path: pathlib.Path, private: bool):
    """Generate JSON representation of the shoulder_registry file.
    """
    if isinstance(dest_path, str):
        dest_path = pathlib.Path(dest_path)
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
@click.option("-d", "--dest_path", default=pathlib.Path("naan_records.json"), type=click.Path(),
              help="JSON destination for NAANs. Existing is updated, path created if necessary.")
def ezid_overrides(ezid_shoulders_url, dest_path):
    """Overrides targets known to be managed by EZID.

    Ideally the authoritative NAAN and Shoulder records should be updated to avoid the need for a
    manual override such as this.

    Note that to generate the EZID related magic files, we need the NAAN records to aleady be present,
    so we can generate the EZID magic files which are then applied to the NAAN records. It's messed
    up, for sure, but this confusion will go away once the source naan and shoulder records are updated
    with the authoritative information.
    """
    ezid_exceptions = [
        # "87602",
        "21549",  # Even though advertised by ezid shoulder list, it is not actually managed by ezid.
    ]
    if isinstance(dest_path, str):
        dest_path = pathlib.Path(dest_path)
    repo = lib_naan.naans.NaanRepository(dest_path)
    repo.load()
    _L.info(f"Loaded {dest_path}")
    if len(repo) == 0:
        raise ValueError("Must load NAANs and Shoulders before applying ezid overrides")
    ezid_shoulder_list = load_ezid_shoulder_list(ezid_shoulders_url)
    if len(ezid_shoulder_list) == 0:
        raise ValueError("EZID shoulder list could not be loaded. Aborting.")
    for entry in ezid_shoulder_list:
        # Find a matching existing record
        # either a NAAN or a Shoulder entry
        if entry["prefix"] in ezid_exceptions:
            continue
        key = entry['prefix']
        naan_record = repo.read(key)
        shoulder_record = None
        _L.debug(json.dumps(entry))
        if entry.get("value", "") == "":
            # Update the NAAN target to point to EZID for resolution
            previous_target = naan_record.target.url
            naan_record.target.url = "https://ezid.cdlib.org/ark:/${content}"
            new_name = entry.get("name", None)
            if new_name is not None:
                naan_record.who.name = new_name
                naan_record.who.name_native = None
            repo.update(naan_record)
            _L.info(f"Updated naan {key} from {previous_target} to {naan_record.target.url}")
        else:
            # Update or create a shoulder entry pointing to EZID
            key = f"{entry['prefix']}/{entry['value']}"
            try:
                shoulder_record = repo.read(key)
            except KeyError:
                _L.info(f"Create shoulder {key}")
                shoulder_record = shoulder_from_naan(naan_record)
                shoulder_record.shoulder = entry["value"]
                shoulder_record.what = key
            previous_target = shoulder_record.target.url
            shoulder_record.target.url = "https://ezid.cdlib.org/ark:/${content}"
            new_name = entry.get("name", None)
            if new_name is not None:
                shoulder_record.who.name = new_name
                shoulder_record.who.name_native = None
            repo.upsert(shoulder_record)
            _L.info(f"Updated shoulder {key} from {previous_target} to {shoulder_record.target.url}")
    repo.store(as_public=True)
    # Now apply magic patches
    magic_path = pathlib.Path(MAGIC_PATH)
    patches = magic_path.glob("*.json")
    for path in patches:
        record = None
        with open(path, "r") as inf:
            record = json.load(inf)
        if record is not None:
            entry = lib_naan.entryFromDict(record)
            repo.upsert(entry)
            _L.info("Applied magic patch to %s", entry.what)
    repo.store(as_public=True)


if PYDANTIC_AVAILABLE:
    # Section available only if pydantic is installed.

    @click_main.command()
    def generate_schema():
        # TODO: flesh this out from the older code base.
        pass


if __name__ == "__main__":
    sys.exit(click_main())
