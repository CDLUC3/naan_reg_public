"""Provides various methods for parsing the legacy anvl format.
"""
import collections
import datetime
import logging
import re
import typing
import urllib.parse


WHO_PATTERN = re.compile(r"\s\(=\)\s")


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


"""ARK Prefix Resolvers substitute a portion of a registered target URL with an identifier.
When a registered target does not include a 
"""
DEFAULT_ARK_SUBST = "$arkid"

# Override these target.
# Necessary when migrating from legacy N2T as the replacement does not
# handle resolution of individual identifiers for ezid, instead that
# functionality is handled by ezid.
TARGET_OVERRIDES = {
    "n2t.net":"arks.org",
}

def urlstr2target(ustr: str, include_slash=True) -> dict:
    """
    Computes the redirect target URL.

    Legacy N2T appears to support a couple different substitution patterns, using
    "ark:/12345/foo" as the input PID in a request:

    blank = Append the ARK as provided in the request to the target URL.
            e.g.: http://example.com/ -> http://example.com/ark:/12345/foo
            ${pid} in the JSON NAAN records.

    $id = Replace the $id string with the content portion of the PID (naan/value)
            e.g.: http://example.com/$id -> http://example.com/12345/foo
            ${content} in the JSON NAAN records

    $arkid = Replace the $arkid string with the full PID
            e.g.: http://example.com/$arkid -> http://example.com/ark:/12345/foo
            ${pid} in the JSON NAAN records

    $nlid = Replace the $nlid string with the value portion of the ARK identifier.
            e.g.: http://example.com/$nlid -> http://example.com/foo
            ${value} in the JSON NAAN records

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
        replacements = {
            "$pid": "${pid}",
            "$arkpid": "${pid}",
            "${arkpid}": "${pid}",
            "$id": "${content}",
            "${id}": "${content}",
            "$arkid": "${pid}",
            "${arkid}": "${pid}",
            "$nlid": "${value}",
            "${nlid}": "${value}",
        }
        for k,v in replacements.items():
            if k in pstr:
                return pstr.replace(k, v)
        # There's at least one entry in the NAAN registry like this
        if pstr.endswith("ark:"):
            return pstr + "${content}"
        if pstr.endswith("ark:/"):
            return pstr + "${content}"
        # Always add a slash when constructing the url
        if not pstr.endswith("/"):
            pstr += "/"
        if include_slash:
            return pstr + "ark:/${content}"
        return pstr + "ark:${content}"

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
        _v = "${pid}"
        return {"http_code": http_code, "url": f"{ustr}{_v}"}

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

