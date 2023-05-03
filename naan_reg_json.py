"""
Generate JSON representation of naan_reg_priv/main_naans.

This tool translates the NAAN registry file from ANVL to JSON to
assist downstream programmatic use.

If pydantic is installed then the script can output JSON schema
describing the JSON respresentation of the transformed NAAN entries.
"""

import argparse
import collections
import datetime
import json
import logging
import os
import os.path
import re
import sys
import typing
import urllib.parse

import dataclasses

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


def datestring2date(dstr: str) -> datetime.datetime:
    """Convert yyyy.mm.dd format to a datetime at UTC."""
    res = datetime.datetime.strptime(dstr, "%Y.%m.%d")
    return res.replace(tzinfo=datetime.timezone.utc)


def urlstr2target(ustr: str, include_slash=True) -> str:
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

    url = urllib.parse.urlsplit(ustr, scheme="https")
    return urllib.parse.urlunsplit(
        (
            url.scheme.lower(),
            url.netloc.lower(),
            adjust_path(url.path),
            url.query,
            url.fragment,
        )
    )


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
class PublicNAAN_who:
    """Publicly visible information for organization responsible for NAAN"""

    name: str = dataclasses.field(
        metadata=dict(description="Official organization name")
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
                "NR = No re-assignment. Once a base identifier-to-object association"
                "     has been made public, that association shall remain unique into"
                "     the indefinite future."
                "OP = Opacity. Base identifiers shall be assigned with no widely"
                "     recognizable semantic information."
                "CC = A check character is generated in assigned identifiers to guard"
                "     against common transcription errors."
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
    target: str = dataclasses.field(
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
    who: PublicNAAN_who
    na_policy: NAAN_how

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
        metadata=dict(description="Purpose for this record, 'ARK'")
    )
    contact: NAAN_contact
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
        public_who = PublicNAAN_who(self.who.name, self.who.acronym)
        public = PublicNAAN(
            self.what, self.where, self.target, self.when, public_who, self.na_policy
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
                parts = v.split("(=)", 1)
                _who = NAAN_who(name=parts[0].strip())
                if len(parts) > 1:
                    _who.abbrev = parts[1].strip()
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



def load_naan_reg_priv(naan_src: str, public_only=False):
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


def generate_json_schema(public_only: bool = False):
    if public_only:
        schema = PublicNAAN.__pydantic_model__.schema()
    else:
        schema = NAAN.__pydantic_model__.schema()
    print(json.dumps(schema, indent=2))


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
    sys.exit(main())
