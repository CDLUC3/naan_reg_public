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
import datetime
import json
import logging
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
    logging.basicConfig(level=logging.DEBUG)
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
    if len(repo) < 1:
        _L.info("Installing shadows.")
        shadows = generate_shadow_ark_config()
        for shadow in shadows:
            repo.insert(shadow)
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
        _L.info(json.dumps(entry))
        if entry.get("value", "") == "":
            # Update the NAAN target to point to EZID for resolution
            previous_target = naan_record.target.url
            naan_record.target.url = "https://ezid.cdlib.org/ark:/${content}"
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
            repo.upsert(shoulder_record)
            _L.info(f"Updated shoulder {key} from {previous_target} to {shoulder_record.target.url}")
    repo.store(as_public=True)
    # Now apply magic patches
    magic_path = pathlib.Path("./magic")
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
    return
    '''
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
    '''


@click_main.command()
def generate_schema():
    pass


if __name__ == "__main__":
    sys.exit(click_main())
