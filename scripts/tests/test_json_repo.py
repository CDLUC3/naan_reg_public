"""
Test module for the NAAN JSON store
"""
import copy
import os

import pytest
import lib_naan
import lib_naan.naans

from common import *

@pytest.fixture
def repo_path():
    fpath = "naan_records.json"
    yield fpath
    if os.path.exists(fpath):
        os.remove(fpath)

def test_json_repo_insert(repo_path, test_naan_instance, test_shoulder_instance):
    repo = lib_naan.naans.NaanRepository(repo_path)
    repo.insert(test_naan_instance)
    repo.insert(test_shoulder_instance)
    assert len(repo) == 2
    with pytest.raises(ValueError):
        repo.insert(test_naan_instance)

def test_json_repo_update(repo_path, test_naan_instance, test_shoulder_instance):
    repo = lib_naan.naans.NaanRepository(repo_path)
    repo.insert(test_naan_instance)
    repo.insert(test_shoulder_instance)
    ns = copy.deepcopy(test_shoulder_instance)
    ns.who.name = "xxx"
    repo.update(ns)
    assert repo.read(ns.identifier).who.name == "xxx"
    ns.shoulder="zzz"
    with pytest.raises(KeyError):
        repo.update(ns)

def test_json_repo_store(repo_path, test_naan_instance, test_shoulder_instance):
    repo = lib_naan.naans.NaanRepository(repo_path)
    repo.insert(test_naan_instance)
    repo.insert(test_shoulder_instance)
    repo.store()
    repo = lib_naan.naans.NaanRepository(repo_path)
    repo.load()
    assert len(repo) == 2
    n = repo.read(test_naan_instance.identifier)
    assert isinstance(n, lib_naan.NAAN)
    assert n.what == test_naan_instance.what
    assert isinstance(n.when, datetime.datetime)

def test_json_repo_store_public(repo_path, test_naan_instance, test_shoulder_instance):
    repo = lib_naan.naans.NaanRepository(repo_path)
    repo.insert(test_naan_instance)
    repo.insert(test_shoulder_instance)
    repo.store(as_public=True)
    repo = lib_naan.naans.NaanRepository(repo_path)
    repo.load()
    assert len(repo) == 2
    n = repo.read(test_naan_instance.identifier)
    assert isinstance(n, lib_naan.PublicNAAN)
    assert n.what == test_naan_instance.what
    assert isinstance(n.when, datetime.datetime)


def test_upsert(repo_path, test_naan_instance, test_shoulder_instance):
    repo = lib_naan.naans.NaanRepository(repo_path)
    repo.insert(test_naan_instance)
    repo.insert(test_shoulder_instance)
    nn = copy.deepcopy(test_naan_instance)
    nn.what = "99999"
    repo.upsert(nn)
    assert len(repo) == 3
    nn.who.name = "nn test upsert"
    repo.upsert(nn)
    assert len(repo) == 3
    assert nn.who.name == "nn test upsert"
    repo.store(as_public=True)
    repo = lib_naan.naans.NaanRepository(repo_path)
    repo.load()
    assert len(repo) == 3
    assert repo.read(nn.what).who.name == "nn test upsert"


def test_delete(repo_path, test_naan_instance, test_shoulder_instance):
    repo = lib_naan.naans.NaanRepository(repo_path)
    repo.insert(test_naan_instance)
    repo.insert(test_shoulder_instance)
    assert len(repo) == 2
    repo.delete(test_naan_instance.identifier)
    assert len(repo) == 1
