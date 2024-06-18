"""
This module implements a repository for NAAN records.
"""

import dataclasses
import datetime
import glob
import json
import logging
import os
import re
import typing

import lib_naan

_L = logging.getLogger(__name__)


class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles dataclasses and datetime instances."""

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, datetime.datetime):
            return o.isoformat(timespec="seconds")
        return super().default(o)


class NaanRepository:
    """
    Implements an on-disk repository for NAAN records.

    NAAN records are stored as JSON files in a directory tree. Subfolders
    of the tree are named with the first character of the NAAN value for the record,
    and individual NAAN records are named as NAAN_VALUE.json.

    The top level of the directory tree contains an index.json file which contains
    a dictionary with keys being NAAN_VALUE and values being the relative path to
    the corresponding NAAN record.
    """
    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        if not os.path.exists(self._base_dir):
            _L.info("Creating directory %s", self._base_dir)
            os.makedirs(self._base_dir)
        self._index_name = os.path.join(self._base_dir, "index.json")
        self.naan_value_re = re.compile(r"[0-9]{5}")

    def _naan_path(self, naan_value:str) -> str:
        """
        Returns the path on disk to the naan record for the given NAAN value.

        Args:
            naan_value: A NAAN value, e.g. "33244"

        Returns:
            str: the path on disk to the naan record for the given naan_value

        """
        naan_value = naan_value.strip()
        sub_dir = naan_value[0]
        return os.path.join(self._base_dir, sub_dir, f"{naan_value}.json")

    def _update_index(self):
        """
        Updates the index.json file.

        Returns:
            Nothing
        """
        entries = []
        for filename in glob.iglob(os.path.join(self._base_dir, "**/*.json"), recursive=True):
            entries.append(os.path.relpath(filename, self._base_dir))
        entries.sort()
        index = {}
        for entry in entries:
            file_parts = os.path.splitext(os.path.basename(entry))
            naan_value = file_parts[0]
            if self.naan_value_re.match(naan_value):
                index[naan_value] = entry
        with open(self._index_name, "w") as dest:
            json.dump(index, dest, indent=2, cls=EnhancedJSONEncoder)

    def index(self):
        """
        Returns a dictionary with keys as naan_values and values as the
        relative paths to the corresponding NAAN records.

        Returns:
            dict: key=naan, value=relative path to the corresponding NAAN record
        """
        with open(self._index_name, "r") as inf:
            return json.load(inf)

    def create(self, naan_record: lib_naan.NAAN) -> lib_naan.NAAN:
        """
        Creates a NAAN record.

        Adds a new naan record if the record does not already exist. The repository
        index is updated.

        Args:
            naan_record: The naan record to be stored.

        Returns:
            The stored naan_record.
        """
        fname = self._naan_path(naan_record.what)
        if os.path.exists(fname):
            raise KeyError(f"{naan_record.what} already exists.")
        with open(fname, "w") as dest:
            json.dump(naan_record, dest, indent=2, cls=EnhancedJSONEncoder)
        self._update_index()
        return naan_record

    def read(self, naan: str, as_public:bool = False) -> typing.Union[lib_naan.NAAN, lib_naan.PublicNAAN]:
        """
        Returns the naan record for the specified NAAN.

        Args:
            naan: The naan value of the record to be retrieved.
            as_public: If true, then private fields are excluded in the response.

        Returns:
            A NAAN or PublicNAAN if as_public requested.
        """
        fname = self._naan_path(naan)
        if not os.path.exists(fname):
            raise IndexError(f"NAAN {naan} does not exist.")
        with open(fname, "r") as inf:
            data = json.load(inf)
        naan_record = lib_naan.NAAN(**data)
        if as_public:
            return naan_record.as_public()
        return naan_record

    def update(self, updates: lib_naan.NAAN) -> lib_naan.NAAN:
        """
        Updates the naan record matching update.what.

        Note that this method completely replaces values in the original with the
        values provided in updates. Typical use pattern will be to acquire the
        record with read(), update the values as needed, then call this update()
        method to persist the changes.

        Args:
            updates: NAAN record that replaces values in the original

        Returns:
            NAAN: the updated naan record as read from the repository.
        """
        naan_record = self.read(updates.what)
        naan_record.update(updates)
        fname = self._naan_path(naan_record.what)
        with open(fname, "w") as dest:
            json.dump(naan_record, dest, indent=2, cls=EnhancedJSONEncoder)
        self._update_index()
        return self.read(naan_record.what)

    def list(self, as_public:bool=False) -> typing.Iterator[lib_naan.NAAN]:
        """

        Args:
            as_public:

        Returns:

        """
        index = self.index()
        for key in index:
            yield self.read(key, as_public=as_public)

