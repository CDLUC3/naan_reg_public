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

import argparse
import collections
import copy
import dataclasses
import datetime
import json
import logging
import os
import os.path
import re
import sys
import typing
import urllib.parse

import click
import requests

PYDANTIC_AVAILABLE = False
try:
    from pydantic.dataclasses import dataclass

    PYDANTIC_AVAILABLE = True
except ModuleNotFoundError:
    from dataclasses import dataclass


# Global logger handle
_L = logging.getLogger("naan_reg_json")

"""ARK Prefix Resolvers substitute a portion of a registered target URL with an identifier.
When a registered target does not include a 
"""
DEFAULT_ARK_SUBST = "$arkid"

WHO_PATTERN = re.compile(r"\s\(=\)\s")

# Override these target.
# Necessary when migrating from legacy N2T as the replacement does not
# handle resolution of individual identifiers for ezid, instead that
# functionality is handled by ezid.
TARGET_OVERRIDES = {
    "n2t.net":"arks.org",
}

def datestring2date(dstr: str) -> datetime.datetime:
    """Convert yyyy.mm.dd format to a datetime at UTC."""
    res = datetime.datetime.strptime(dstr, "%Y.%m.%d")
    return res.replace(tzinfo=datetime.timezone.utc)


def split_who(who: str) -> typing.Dict[str, str]:
    if isinstance(who, list):
        who = " | ".join(who)
    res = {"name": None, "acronym": None, "name_native": None}
    parts = WHO_PATTERN.split(who)
    if len(parts) == 1:
        res["name"] = who
    elif len(parts) == 2:
        res["name"] = parts[0]
        res["acronym"] = parts[1]
    elif len(parts) == 3:
        res["name_native"] = parts[0]
        res['name'] = parts[1]
        res["acronym"] = parts[2]
    return res


def urlstr2target(ustr: str, include_slash=True) -> dict:
    """
    Computes the redirect target URL.

    If ustr path includes "$pid" or "$arkpid", then the path is unchanged,
    otherwise "$arkpid" is appended to create the target.

    A Prefix Resolver should examine substitute the provided identifier
    minus the scheme portion, i.e. "NAAN/suffix" for "$pid" or the entire provided
    ark identifier for "$arkpid".

    Params:
        ustr: string = URL string to be used for the computed Resource Resolver target
        include_slash: bool = If True, then the target accepts "$arkpid" otherwise "$pid"
    """

    def adjust_path(pstr: str) -> str:
        pstr = pstr.strip()
        if "$pid" in pstr or "$arkpid" in pstr:
            return pstr
        # replace $id or $arkid with $pid or $arkpid
        if "$id" in pstr:
            return pstr.replace("$id", "$pid")
        if "$arkid" in pstr:
            return pstr.replace("$arkid", "$arkpid")
        # There's at least one entry in the NAAN registry like this
        if pstr.endswith("ark:"):
            return pstr + "$pid"
        if pstr.endswith("ark:/"):
            return pstr + "$pid"
        # Always add a slash when constructing the url
        if not pstr.endswith("/"):
            pstr += "/"
        if include_slash:
            return pstr + "$arkpid"
        return pstr + "ark:$pid"

    def adjust_netloc(netloc:str)->str:
        netloc = netloc.lower()
        if netloc in TARGET_OVERRIDES:
            netloc = TARGET_OVERRIDES[netloc]
        return netloc

    http_code = 302
    ustr = ustr.strip()
    parts = ustr.split()
    if len(parts) > 1:
        try:
            http_code = int(parts[0])
        except ValueError as e:
            logging.warning("Invalid status code %s", parts[0])
        ustr = parts[1]

    if ("?" in ustr) and ((ustr[-1] == "=") or (ustr[-1] == "?")):
        return {"http_code": http_code, "url": f"{ustr}$arkpid"}

    url = urllib.parse.urlsplit(ustr, scheme="https")
    structured_url = urllib.parse.urlunsplit(
        (
            url.scheme.lower(),
            adjust_netloc(url.netloc),
            adjust_path(url.path),
            url.query,
            url.fragment,
        )
    )
    return {"http_code": http_code, "url": structured_url}


class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles dataclasses and datetime instances."""

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, datetime.datetime):
            return o.isoformat(timespec="seconds")
        return super().default(o)


class AnvlParseException(Exception):
    pass


class AnvlParser:
    """Simple ANVL parser implementation.

    Intended for parsing the naan registry file.
    """

    _pattern1 = re.compile("[%:\r\n]")
    _pattern2 = re.compile("[%\r\n]")
    _pattern3 = re.compile("%([0-9a-fA-F][0-9a-fA-F])?")

    def __init__(self):
        self.L = logging.getLogger("AnvlParser")

    def _decodeRewriter(self, m):
        if len(m.group(0)) == 3:
            return chr(int(m.group(0)[1:], 16))
        else:
            raise AnvlParseException("percent-decode error")

    def _decode(self, s: str) -> str:
        return self._pattern3.sub(self._decodeRewriter, s)

    def parse_value(self, v: str) -> typing.Union[str, list[str]]:
        parts = v.split("|")
        if len(parts) == 1:
            return v
        res = [element.strip() for element in parts]
        return res

    def parse(self, s: typing.Union[str, list[str]]) -> collections.OrderedDict:
        d = collections.OrderedDict()
        k = None
        k0 = None
        lines = []
        if isinstance(s, str):
            lines = re.split("\r\n?|\n", s)
        else:
            lines = s
        for l in lines:
            l = l.rstrip()
            if len(l) == 0:
                k = None
            elif l[0] == "#":
                pass
            elif l[0].isspace():
                if k is None:
                    raise AnvlParseException("no previous label for continuation line")
                ll = self._decode(l).strip()
                if ll != "":
                    if d[k] == "":
                        d[k] = ll
                    else:
                        d[k] += " " + ll
            else:
                if ":" not in l:
                    raise AnvlParseException("no colon in line")
                k, v = [self._decode(w).strip() for w in l.split(":", 1)]
                v = self.parse_value(v)
                if k0 is None:
                    k0 = k
                if len(k) == 0:
                    raise AnvlParseException("empty label")
                if k in d:
                    if not isinstance(d[k], list):
                        d[k] = [
                            d[k],
                        ]
                    d[k].append(v)
                else:
                    d[k] = v
        # if first key has a value then return a flat dict
        if len(d[k0]) > 0:
            return d
        # otherwise return a dict of dict, with first key as key to sub-dict
        dd = collections.OrderedDict()
        d.pop(k0)
        dd[k0] = d
        return dd

    def parseBlocks(self, txt: str):
        """
        Generator returning parsed anvl blocks from text
        Args:
            txt:

        Returns:

        """
        block = []
        for line in re.split("\r\n?|\n", txt):
            llen = len(line)
            if llen > 0 and line[0] == "#":
                continue
            if llen == 0:
                if (len(block)) > 0:
                    yield self.parse(block)
                    block = []
            else:
                block.append(line)
        if len(block) > 0:
            yield self.parse(block)





@dataclass
class Target:

    url: str = dataclasses.field(
        metadata = dict(
            description=(
                "URL of service endpoint accepting ARK identifiers including subsitution"
                "parameters $arkpid for full ARK or $pid for NAAN/suffix."
            )
        )
    )
    http_code: int = dataclasses.field(
        default=302,
        metadata=dict(
            description="The HTTP code to use for redirection"
        )
    )


@dataclass
class PublicNAAN_who:
    """Publicly visible information for organization responsible for NAAN"""

    name: str = dataclasses.field(
        metadata=dict(description="Official organization name")
    )
    name_native: str = dataclasses.field(
        default=None,
        metadata=dict(description="Non-english variant of the official organization.")
    )
    acronym: typing.Optional[str] = dataclasses.field(
        default=None,
        metadata=dict(description="Optional display acronym derived from DNS name"),
    )


@dataclass
class NAAN_who(PublicNAAN_who):
    """Organization responsible for NAAN"""

    address: str = dataclasses.field(
        default=None, metadata=dict(description="Physical address of organization")
    )


@dataclass
class NAAN_how:
    """Policy and tenure of NAAN management"""

    orgtype: str = dataclasses.field(
        metadata=dict(
            description="Organization type, FP = For profit, NP = Not for profit."
        )
    )
    policy: str = dataclasses.field(
        metadata=dict(
            description=(
                "Which practices do you plan to implement when you assign the base name "
                "of your ARKs? The ARK base name is between your NAAN and any suffix; for "
                "example, in ark:12345/x6np1wh8k/c3.xsl the base name is x6np1wh8k. This "
                "information can help others make the best use of your ARKs. Please submit "
                "updates as your practices evolve. "
                "\n"
                "'''\n"
                "NR = No re-assignment. Once a base identifier-to-object association\n"
                "     has been made public, that association shall remain unique into\n"
                "     the indefinite future.\n"
                "OP = Opacity. Base identifiers shall be assigned with no widely\n"
                "     recognizable semantic information.\n"
                "CC = A check character is generated in assigned identifiers to guard\n"
                "     against common transcription errors.\n"
                "'''\n"
            )
        )
    )
    tenure: str = dataclasses.field(
        metadata=dict(description="<start year YYYY of role tenure>[-<end of tenure> ]")
    )
    policy_url: typing.Optional[str] = dataclasses.field(
        default=None, metadata=dict(description="URL to narrative policy statement")
    )


@dataclass
class NAAN_contact:
    name: str = dataclasses.field(metadata=dict(description="Name of contact"))
    unit: typing.Optional[str] = dataclasses.field(
        default=None, metadata=dict(description="Name of contact organization")
    )
    tenure: typing.Optional[str] = dataclasses.field(
        default=None,
        metadata=dict(
            description="<start year YYYY of role tenure>[-<end of tenure> ]"
        ),
    )
    email: typing.Optional[str] = dataclasses.field(
        default=None, metadata=dict(description="Email address of contact")
    )
    phone: typing.Optional[str] = dataclasses.field(
        default=None, metadata=dict(description="Telephone number for contact")
    )


@dataclass
class PublicNAAN:
    what: str = dataclasses.field(
        metadata=dict(description="The NAAN value, e.g. 12345")
    )
    where: str = dataclasses.field(
        metadata=dict(description="URL of service endpoint accepting ARK identifiers.")
    )
    target: Target
    when: datetime.datetime = dataclasses.field(
        metadata=dict(description="Date when this record was last modified.")
    )
    who: PublicNAAN_who
    na_policy: NAAN_how
    test_identifier: str = dataclasses.field(
        default=None,
        metadata=dict(
            description=(
                "A specific, concrete ARK that you plan to support and that you will permit us to"
                "use periodically for testing service availability."
            )
        )
    )
    service_provider: str = dataclasses.field(
        default=None,
        metadata=dict(
            description=(
                'A "service provider" is different from the NAAN holder organization. It provides '
                "technical assistance to the the NAAN organization such as content hosting, access, "
                "discovery, etc."
            )
        )
    )
    purpose: str = dataclasses.field(
        default="unspecified",
        metadata=dict(
            description=(
                "What are you planning to assign ARKs to using the requested NAAN?"
                "Options: "
                "documents(text or page images, eg, journal articles, technical reports); "
                "audio - and / or video - based objects; "
                "non-text, non-audio / visual documents(eg, maps, posters, musical scores); "
                "datasets (eg, spreadsheets, collections of spreadsheets); "
                "records (eg, bibliographic records, archival finding aids); "
                "physical objects(eg, fine art, archaeological artifacts, scientific samples)"
                "concepts (eg, vocabulary terms, disease codes); "
                "agents (people, groups, and institutions as actors, eg, creators, contributors, publishers, performers, etc); "
                "other; "
                "unspecified; "
            )
        )
    )
    rtype: str = dataclasses.field(
        metadata=dict(description="Type of this record."),
        default="naan"
    )

    def as_flat(self) -> dict:
        return {
            "what": self.what,
            "who": self.who.name,
            "where": self.where,
            "when": self.when,
        }


@dataclass
class NAAN(PublicNAAN):
    who: NAAN_who
    why: str = dataclasses.field(
        default='ARK',
        metadata=dict(description="Purpose for this record, 'ARK'")
    )
    contact: NAAN_contact=None
    alternate_contact: NAAN_contact=None
    comments: typing.Optional[typing.List[dict]] = dataclasses.field(
        default=None, metadata=dict(description="Comments about NAAN record")
    )
    provider: typing.Optional[str] = dataclasses.field(
        default=None, metadata=dict(description="")
    )

    @property
    def key(self) -> str:
        return self.what

    def as_public(self) -> PublicNAAN:
        public_who = PublicNAAN_who(name=self.who.name, name_native=self.who.name_native, acronym=self.who.acronym)
        public = PublicNAAN(
            self.what, self.where, self.target, self.when, public_who, self.na_policy,
            self.test_identifier, self.service_provider, self.purpose
        )
        return public

    @classmethod
    def from_block(cls, block: dict):
        """
        Factory method for creating NAAN from an ANVL parsed block
        """
        data = block.get("naa", {})
        res = {"comments": None, "provider": None}
        _address = None
        for k, v in data.items():
            if k == "who":
                _L.debug(v)
                who_parts = split_who(v)
                _who = NAAN_who(**who_parts)
                res["who"] = _who
            elif k == "when":
                res["when"] = datestring2date(v)
            elif k == "where":
                res["where"] = v
                res["target"] = urlstr2target(v)
            elif k == "how":
                _how = NAAN_how(
                    orgtype=v[0],
                    policy=v[1],
                    tenure=v[2],
                    policy_url=v[3] if v[3] != "" else None,
                )
                res["na_policy"] = _how
            elif k == "!contact":
                _contact = NAAN_contact(
                    name=v[0],
                    unit=v[1] if v[1] != "" else None,
                    tenure=v[2] if v[2] != "" else None,
                    email=v[3] if v[3] != "" else None,
                )
                if len(v) > 4:
                    _contact.phone = v[4] if v[4] != "" else None
                res["contact"] = _contact
            elif k == "!why":
                res["why"] = v
            elif k == "!address":
                _address = v
            elif k == "!provider":
                res["provider"] = str(v)
            else:
                if k.startswith("!"):
                    if res["comments"] is None:
                        res["comments"] = [
                            {k: v},
                        ]
                    else:
                        res["comments"].append({k: v})
                else:
                    res[k] = v
        if "who" in res:
            res["who"].address = _address
        if "what" in res:
            return cls(**res)
        return None


@dataclass
class PublicNAANShoulder:
    shoulder:str = dataclasses.field(
        metadata=dict(description="The shoulder part of the record")
    )
    naan: str = dataclasses.field(
        metadata=dict(description="The naan part of the record")
    )
    who: PublicNAAN_who
    where: str = dataclasses.field(
        metadata=dict(description="URL of service endpoint accepting ARK identifiers.")
    )
    target: Target = dataclasses.field(
        metadata=dict(
            description=(
                "URL of service endpoint accepting ARK identifiers including subsitution"
                "parameters $arkpid for full ARK or $pid for NAAN/suffix."
            )
        )
    )
    when: datetime.datetime = dataclasses.field(
        metadata=dict(description="Date when this record was last modified.")
    )
    na_policy: NAAN_how
    rtype: str = dataclasses.field(
        metadata=dict(description="Type of this record."),
        default="shoulder"
    )


@dataclass
class NAANShoulder(PublicNAANShoulder):
    who: NAAN_who
    contact: NAAN_contact=None
    alternate_contact: NAAN_contact=None
    comments: typing.Optional[typing.List[dict]] = dataclasses.field(
        default=None, metadata=dict(description="Comments about Shoulder record")
    )
    provider: typing.Optional[str] = dataclasses.field(
        default=None, metadata=dict(description="")
    )

    @property
    def key(self) -> str:
        return f"{self.naan}/{self.shoulder}"

    def as_public(self) -> PublicNAANShoulder:
        public_who = PublicNAAN_who(self.who.name, self.who.acronym)
        public = PublicNAANShoulder(
            shoulder=self.shoulder,
            naan=self.naan,
            who=public_who,
            where=self.where,
            target=self.target,
            when=self.when,
            na_policy=self.na_policy,
        )
        return public

    @classmethod
    def from_block(cls, block: dict):
        """
        Factory method for creating NAAN from an ANVL parsed block
        """
        data = block.get("naa", {})
        res = {"comments": None, }
        for k, v in data.items():
            if k == "what":
                scheme, value = v.split(":")
                if scheme.lower() != "ark":
                    raise ValueError("Only ARK shoulders supported.")
                value = value.strip("/")
                naan, shoulder = value.split("/")
                res["naan"] = naan
                res["shoulder"] = shoulder
            elif k == "who":
                who_parts = split_who(v)
                _who = NAAN_who(**who_parts)
                res["who"] = _who
            elif k == "when":
                res["when"] = datestring2date(v)
            elif k == "where":
                res["where"] = v
                res["target"] = urlstr2target(v)
            elif k == "how":
                _how = NAAN_how(
                    orgtype=v[0],
                    policy=v[1],
                    tenure=v[2],
                    policy_url=v[3] if v[3] != "" else None,
                )
                res["na_policy"] = _how
            else:
                if k.startswith("!"):
                    if res["comments"] is None:
                        res["comments"] = [
                            {k: v},
                        ]
                    else:
                        res["comments"].append({k: v})
                else:
                    res[k] = v
        if "shoulder" in res:
            return cls(**res)
        return None

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

def load_naan_reg_priv(naan_src: str, public_only=False) -> dict[str, typing.Union[NAAN, PublicNAAN]]:
    anvl_parser = AnvlParser()
    res = {}
    for block in anvl_parser.parseBlocks(naan_src):
        naan = NAAN.from_block(block)
        if naan is not None:
            if naan.key in res:
                raise ValueError("Key %s elready present", naan.key)
            if public_only:
                res[naan.key] = naan.as_public()
            else:
                res[naan.key] = naan
    return res


def load_naan_shoulders(shoulder_src: str, public_only=False) -> dict[str, typing.Union[NAANShoulder, PublicNAANShoulder]]:
    anvl_parser = AnvlParser()
    res = {}
    for block in anvl_parser.parseBlocks(shoulder_src):
        shoulder = NAANShoulder.from_block(block)
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


def store_json_naan_record(dest_folder: str, record: typing.Union[NAAN, PublicNAAN])->str:
    path_name = naan_to_path_name(record.what)
    os.makedirs(os.path.join(dest_folder, path_name["path"]), exist_ok=True)
    fname = os.path.join(dest_folder, path_name["path"], path_name["name"])
    with open(fname, "w") as dest:
        json.dump(record, dest, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
    return fname


def store_json_shoulder_record(dest_folder: str, record:NAANShoulder)->str:
    path_name = shoulder_to_path_name(record.naan, record.shoulder)
    os.makedirs(os.path.join(dest_folder, path_name["path"]), exist_ok=True)
    fname = os.path.join(dest_folder, path_name["path"], path_name["name"])
    with open(fname, "w") as dest:
        json.dump(record, dest, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
    return fname


def store_json_record(dest_folder:str, record: typing.Union[PublicNAANShoulder, NAANShoulder, PublicNAAN, NAAN])->typing.Optional[str]:
    if isinstance(record, (NAANShoulder, PublicNAANShoulder)):
        return store_json_shoulder_record(dest_folder, record)
    if isinstance(record, (NAAN, PublicNAAN)):
        return store_json_naan_record(dest_folder, record)
    return None


def generate_json_schema(public_only: bool = False):
    if public_only:
        schema = PublicNAAN.__pydantic_model__.schema()
    else:
        schema = NAAN.__pydantic_model__.schema()
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

@click_main.command()
@click.argument("anvl_source", type=click.Path(exists=True))
@click.option("-d", "--dest_folder", default=".")
@click.option("-i", "--individual", is_flag=True, default=False, help="Write individual NAAN records")
@click.option("-p", "--private", is_flag=True, help="Generate private JSON records.")
def naan_anvl_to_json(anvl_source:str, dest_folder: str, individual: bool, private:bool):
    os.makedirs(dest_folder, exist_ok=True)
    naan_src = open(anvl_source, "r").read()
    naan_records = load_naan_reg_priv(naan_src, public_only= not private)
    if individual:
        for k, naan_record in naan_records.items():
            fname = store_json_record(dest_folder, naan_record)
            _L.info("Wrote NAAN record at %s", fname)
    # Write out the json-lines representation of the NAAN records
    # This format is convenient for loading in tools like duckdb
    fname = os.path.join(dest_folder, "naan_records.jsonl")
    with open(fname, "w") as dest:
        for k,v in naan_records.items():
            dest.write(json.dumps(v, ensure_ascii=False, cls=EnhancedJSONEncoder))
            dest.write("\n")
    _L.info("Wrote full NAAN records to %s", fname)
    # Write out a single dictionary representation
    fname = os.path.join(dest_folder, "naan_records.json")
    existing = {}
    if os.path.exists(fname):
        with open(fname, "r") as inf:
            existing = json.load(inf)
    for k, v in naan_records.items():
        existing[k] = v
    with open(fname, "w") as dest:
        json.dump(existing, dest, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
        _L.info("Wrote full NAAN records to %s", fname)


@click_main.command()
@click.argument("anvl_source", type=click.Path(exists=True))
@click.option("-d", "--dest_folder", default=".")
@click.option("-i", "--individual", is_flag=True, default=False, help="Write individual NAAN records")
@click.option("-p", "--private", is_flag=True, help="Generate private JSON records.")
def shoulder_anvl_to_json(anvl_source:str, dest_folder: str, individual:bool, private:bool):
    os.makedirs(dest_folder, exist_ok=True)
    shoulder_src = open(anvl_source, "r").read()
    shoulders = load_naan_shoulders(shoulder_src, public_only=not private)
    if individual:
        for k, shoulder in shoulders.items():
            fname = store_json_record(dest_folder, shoulder)
            _L.info("Wrote Shoulder record at %s", fname)
    fname = os.path.join(dest_folder, "naan_records.json")
    existing = {}
    if os.path.exists(fname):
        with open(fname, "r") as inf:
            existing = json.load(inf)
    for k, v in shoulders.items():
        existing[k] = v
    with open(fname, "w") as dest:
        json.dump(existing, dest, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
        _L.info("Wrote full Shoulder records to %s", fname)

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    if PYDANTIC_AVAILABLE:
        parser.add_argument(
            "-s", "--schema", action="store_true", help="Generate JSON schema and exit."
        )
        parser.add_argument(
            "path",
            default="not-a-source",
            nargs="?",
            help="Path to naan_reg_priv ANVL file.",
        )
    else:
        parser.add_argument("path", help="Path to naan_reg_priv ANVL file.")
    parser.add_argument(
        "-p", "--public", action="store_true", help="Output public content only."
    )
    parser.add_argument(
        "-f",
        "--files",
        default=None,
        help="Write individual json files to folder FILES. WARNING: existing content overwritten!",
    )
    parser.add_argument(
        "-t",
        "--flat",
        action="store_true",
        help="Output flat file compatible public view to stdout.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if PYDANTIC_AVAILABLE:
        if args.schema:
            generate_json_schema(public_only=args.public)
            return 0
    if args.path == "not-a-source":
        _L.error("Path to ANVL source is required.")
        return 1
    if not os.path.exists(args.path):
        _L.error("Path '%s' not found.", args.path)
        return 1
    naan_src = args.path
    _L.info("Loading ANVL %s ...", naan_src)
    naan_txt = open(naan_src, "r").read()
    res = load_naan_reg_priv(naan_txt, public_only=args.public)
    _L.info("Total of %s entries", len(res))
    _output_generated = False
    if args.files is not None:
        _index = {}
        os.makedirs(args.files, exist_ok=True)
        for k, v in res.items():
            fname = f"{k}.json"
            sub_path = fname[0]
            dest_path = os.path.join(args.files, sub_path)
            if not os.path.exists(dest_path):
                os.makedirs(dest_path, exist_ok=True)
            _index[k] = os.path.join(sub_path, fname)
            with open(os.path.join(args.files, _index[k]), "w") as fdest:
                json.dump(
                    v, fdest, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder
                )
        with open(os.path.join(args.files, "index.json"), "w") as fdest:
            json.dump(
                _index, fdest, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder
            )
        with open(os.path.join(args.files, "index.html"), "w") as fdest:
            fdest.write(generate_index_html(res, _index))
        _output_generated = True
    if args.flat:
        flat_list = []
        for k, v in res.items():
            flat_list.append(v.as_flat())
        print(
            json.dumps(flat_list, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
        )
        _output_generated = True
    if not _output_generated:
        print(json.dumps(res, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder))
    return 0

if __name__ == "__main__":
    sys.exit(click_main())
