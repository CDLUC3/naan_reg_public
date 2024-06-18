"""
Tests parsing ANVL sources
"""
import json
import pytest
import naan_reg_json

who_cases = (
    ("DataMares (=) DATAMARES", {"name": "DataMares", "acronym": "DATAMARES"}),
    ("EZID example suffix passthrough (=) EZEXSPT", {"name": "EZID example suffix passthrough", "acronym": "EZEXSPT"}),
    ("Bibliothèque Nationale du Royaume du Maroc (=) National Library of the Kingdom of Morocco (=) BNRM", {"name": "National Library of the Kingdom of Morocco", "acronym": "BNRM"}),
    ("Российский Лингвистический Бюллетень (=) Russian Linguistic Bulletin (=) RULB", {"name": "Russian Linguistic Bulletin", "acronym": "RULB"}),
)


@pytest.mark.parametrize("source,expected", who_cases)
def test_split_who(source, expected):
    res = naan_reg_json.split_who(source)
    assert res["name"] == expected["name"]
    assert res["acronym"] == expected["acronym"]


naan_cases = (
    (
        """
        
naa:
who:    World Intellectual Property Organization (=) WIPO
what:   13038
when:   2002.07.12
where:  http://www.wipo.int
how:    NP | (:unkn) unknown | 2002 |
!why:   ARK
!contact: Surname, Firstname ||| test.email@example.com | +12 34 567 8901
!address: 123, Rue du Vidollet, CH-1211 Geneva, Switzerland
          
        """,
        {
            "what": "13038",
            "where": "http://www.wipo.int",
            "target": {"url":"http://www.wipo.int/$arkpid","http_code":302},
            "when": "2002-07-12T00:00:00+00:00",
            "who": {
                "name": "World Intellectual Property Organization",
                "acronym": None,
                "address": "123, Rue du Vidollet, CH-1211 Geneva, Switzerland"
            },
            "na_policy": {
                "orgtype": "NP",
                "policy": "(:unkn) unknown",
                "tenure": "2002",
                "policy_url": None,
            },
            "test_identifier": None,
            "service_provider": None,
            "purpose": "unspecified",
            "why": "ARK",
            "contact": {
                "name": "Surname, Firstname",
                "unit": None,
                "tenure": None,
                "email": "test.email@example.com",
                "phone": "+12 34 567 8901"
            },
            "alternate_contact": None,
            "comments": None,
            "provider": None,
        }
    ),
    (
        """
        
naa:
who:    Archives West (=) AWEST
what:   80444
when:   2006.01.06
where:  http://archiveswest.orbiscascade.org
how:    NP | (:unkn) unknown | 2006 |
!why:   ARK
!contact: Surname, firstname ||| user@example.net |
!address: 1234 W 13th St Suite 999 Eugene, OR 97402, USA
#!updated 2021.04.16 -- old info below
#!who:    Northwest Digital Archives (=) NWDA
#!where:  http://nwda.wsulibs.wsu.edu
#!contact: Surname, Firstname | Washington State University Libraries || user@example.com | +1 123-456-7890
#!address: 123 Test Road, Pullman, WA 99164, USA
  
        """,
        {
            "what": "80444",
            "where": "http://archiveswest.orbiscascade.org",
            "target": {"url": "http://archiveswest.orbiscascade.org/$arkpid", "http_code": 302},
            "when": "2006-01-06T00:00:00+00:00",
            "who": {
                "name": "Archives West",
                "acronym": None,
                "address": "1234 W 13th St Suite 999 Eugene, OR 97402, USA"
            },
            "na_policy": {
                "orgtype": "NP",
                "policy": "(:unkn) unknown",
                "tenure": "2006",
                "policy_url": None
            },
            "test_identifier": None,
            "service_provider": None,
            "purpose": "unspecified",
            "why": "ARK",
            "contact": {
                "name": "Surname, firstname",
                "unit": None,
                "tenure": None,
                "email": "user@example.net",
                "phone": None
            },
            "alternate_contact": None,
            "comments": None,
            "provider": None
        }
    ),
    (
        """
naa:
who:    Российский Лингвистический Бюллетень (=) Russian Linguistic Bulletin (=) RULB
what:   45487
when:   2015.05.22
where:  http://rulb.org
how:    NP | (:unkn) unknown | 2015 |
!why:   ARK
!contact: Miller, Anna ||| editors@rulb.org |
!address: Ekaterinburg, 620137, Russia
        """,
        {
            "what": "45487",
            "where": "http://rulb.org",
            "target": {
                "url": "http://rulb.org/$arkpid",
                "http_code": 302
            },
            "when": "2015-05-22T00:00:00+00:00",
            "who": {
                "name": "Russian Linguistic Bulletin",
                "name_native": "Российский Лингвистический Бюллетень",
                "acronym": "RULB",
                "address": "Ekaterinburg, 620137, Russia"
            },
            "na_policy": {
                "orgtype": "NP",
                "policy": "(:unkn) unknown",
                "tenure": "2015",
                "policy_url": None
            },
            "test_identifier": None,
            "service_provider": None,
            "purpose": "unspecified",
            "why": "ARK",
            "contact": {
                "name": "Miller, Anna",
                "unit": None,
                "tenure": None,
                "email": "user@example.org",
                "phone": None
            },
            "alternate_contact": None,
            "comments": None,
            "provider": None
        }
    )
)


@pytest.mark.parametrize('source,expected', naan_cases)
def test_parse_anvl_naan(source, expected):
    anvl_parser = naan_reg_json.AnvlParser()
    block = anvl_parser.parse(source)
    naan = naan_reg_json.NAAN.from_block(block)
    print(f"NAAN = {json.dumps(naan, indent=2, ensure_ascii=False, cls=naan_reg_json.EnhancedJSONEncoder)}")


shoulder_cases = (
    (
        """

naa:
who:    EZID CDL agents (=) EZAGENTS
what:   ark:/99166/p9
when:   2010.09.01
where:  https://n2t.net
how:    NP | NR, OP, CC | 2010 |

        """,
        {}
    ),
    (
        """

naa:
who:    Social Networks and Archival Context Cooperative - historical persons, families, organizations (=) SNACC
what:   ark:/99166/w6
when:   2013.02.12
where:  303 http://socialarchive.iath.virginia.edu
how:    NP | NR, OP, CC | 2013 |
# note: uses 303 redirect to code http://socialarchive.iath.virginia.edu

        """,
        {}
    )
)


@pytest.mark.parametrize('source,expected', shoulder_cases)
def test_parse_anvl_shoulder(source, expected):
    anvl_parser = naan_reg_json.AnvlParser()
    block = anvl_parser.parse(source)
    shoulder = naan_reg_json.NAANShoulder.from_block(block)
    print(f"SHOULDER = {json.dumps(shoulder, indent=2, ensure_ascii=False, cls=naan_reg_json.EnhancedJSONEncoder)}")
