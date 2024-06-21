
import datetime
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


@pytest.fixture()
def test_shoulder_instance():
    return lib_naan.NAANShoulder(
        shoulder="foo",
        naan = "12345",
        who=lib_naan.NAAN_who(
            name="name"
        ),
        contact=lib_naan.NAAN_contact(
          email="a@b.com",
          name="<NAME>",
          phone="0123456789",
          unit="unit",
          tenure="2023"
        ),
        where="http://example.com/",
        target = lib_naan.Target(
            url="https://example.com/data/",
            http_code=302
        ),
        when = get_timestamp(),
        na_policy = lib_naan.NAAN_how(
            orgtype="NP",
            policy="NR",
            tenure="2024"
        )
    )