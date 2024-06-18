"""
Test cases for lib_naan data instances
"""
import copy
import datetime
import time
import pytest

import lib_naan


def get_timestamp():
    ds = datetime.datetime.now(tz=datetime.timezone.utc)
    return ds


@pytest.fixture()
def test_naan_instance():
    return lib_naan.NAAN(
        what="12345",
        where="location",
        target=lib_naan.Target(url="target",http_code=302),
        when=get_timestamp(),
        who=lib_naan.NAAN_who(
            name="name",
        ),
        na_policy=lib_naan.NAAN_how(
            orgtype = "NP",
            policy = "NR",
            tenure="2024"
        ),
        contact=lib_naan.NAAN_contact(
            email="<EMAIL>",
            name="<NAME>",
            phone="0123456789",
            unit="unit",
            tenure="2023"
        )
    )

def test_naan_who_update():
    a = lib_naan.NAAN_who(
        name="name",
        acronym="acronym",
        address="address"
    )
    o = copy.deepcopy(a)
    b = copy.deepcopy(a)
    b.name = "name-2"
    b.acronym = "acronym-2"
    b.address = "address-2"
    a.update(b)
    assert a.name == b.name and a.name != o.name
    assert a.acronym == b.acronym and a.acronym != o.acronym
    assert a.address == b.address and a.address != o.address


def test_update_what(test_naan_instance):
    nv = copy.deepcopy(test_naan_instance)
    nv.what = "00000"
    with pytest.raises(ValueError):
        test_naan_instance.update(nv)


def test_update(test_naan_instance):
    original = copy.deepcopy(test_naan_instance)
    nv = copy.deepcopy(test_naan_instance)
    nv.where = "location-2"
    nv.target.url = "http://example.com"
    nv.who.name = "name-2"
    nv.contact.email = "email-2"
    time.sleep(0.1)
    res = test_naan_instance.update(nv)
    assert res.when != original.when
    assert res.where == nv.where and res.where != original.where
    assert res.target.url == nv.target.url and res.target.url != original.target.url
    assert res.who.name == nv.who.name and res.who.name != original.who.name
    assert isinstance(res.contact, lib_naan.NAAN_contact)
    assert res.contact.email == nv.contact.email and res.contact.email != original.contact.email

def test_update2(test_naan_instance):
    original = copy.deepcopy(test_naan_instance)
    nv = copy.deepcopy(test_naan_instance)
    nv.contact = None
    res = test_naan_instance.update(nv)
    assert res.contact is None and isinstance(original.contact, lib_naan.NAAN_contact)
