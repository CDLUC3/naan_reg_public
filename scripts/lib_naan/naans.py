"""
Copyright©2024, Regents of the University of California

License: https://opensource.org/license/mit, See LICENSE

This module implements a repository for NAAN records.
"""

import dataclasses
import datetime
import json
import logging
import os
import pathlib
import typing

import lib_naan
import lib_naan.anvl

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
    __version__ = "1.0"

    """
    Implements an on-disk repository for NAAN records.

    NAAN records are stored to a single JSON file that may contain NAAN records and
    shoulder records for NAANs.

    A corresponding NAAN record must be present for shoulders, hence NAANs should be
    loaded first to avoid consistency exceptions.

    """

    def __init__(self, store_path: typing.Union[str, pathlib.Path]):
        self._store_path = pathlib.Path(store_path)
        self._index: dict[str, int] = {}
        self._records = []
        self._metadata = {
            "version": NaanRepository.__version__,
            "created_date": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            "modified_date": None,
            "description": "Public NAAN records and Shoulder information."
        }

    def __len__(self) -> int:
        return len(self._records)

    def _update_index(self):
        """
        Updates the index.json file.

        Returns:
            Nothing
        """
        self._index = {}
        for i in range(0, len(self._records)):
            entry = self._records[i]
            self._index[entry.identifier] = i

    def get(self, i: int, as_public: bool = False) -> typing.Union[lib_naan.NAAN, lib_naan.PublicNAAN]:
        record = self._records[i]
        if as_public:
            return record.as_public()
        return record

    def read(self, key: str, as_public: bool = False) -> typing.Union[lib_naan.NAAN, lib_naan.PublicNAAN]:
        """
        Retrieve the specified record with exact match of "NAAN" or "NAAN/shoulder"

        If "as_public" is True, then only public information is returned.
        """
        i = self._index[key]
        return self.get(i, as_public=as_public)

    def load(self) -> None:
        """Load the set of records from the specified JSON file.
        """
        self._records = []
        self._index = {}
        with open(self._store_path, "r") as inf:
            data = json.load(inf)
            self._metadata = data["metadata"]
            records = data["data"]
        for record in records:
            entry = lib_naan.entryFromDict(record)
            if entry is not None:
                self._records.append(entry)
            else:
                _L.warning("Unable to parse record '%s'" % record)
        self._update_index()
        _L.info("Loaded %s records from %s", len(self), self._store_path)

    def store(self, as_public: bool = False) -> None:
        """Store the set of records in the specified JSON file
        """
        if not os.path.exists(self._store_path):
            _L.info("Creating directory %s", self._store_path)
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
        records = self._records
        if as_public:
            records = []
            for record in self._records:
                records.append(record.as_public())
        data = {
            "metadata": self._metadata,
            "data": records
        }
        with open(self._store_path, "w") as dest:
            json.dump(data, dest, indent=2, cls=EnhancedJSONEncoder)
        _L.info("Saved %s records to %s", len(self), self._store_path)

    def insert(self, entry: lib_naan.StorableTypes) -> str:
        """
        Adds a record.

        Adds a new naan record if the record does not already exist. The repository
        index is updated.

        Args:
            naan_record: The naan record to be stored.

        Returns:
            The stored naan_record.
        """
        key = self._index.get(entry.identifier, None)
        if key is not None:
            raise ValueError(f"Entry with key {key} already exists. Try update instead.")
        self._records.append(entry)
        self._update_index()
        self._metadata["updated"] = datetime.datetime.now(tz=datetime.timezone.utc)
        return entry.identifier

    def update(self, entry: lib_naan.StorableTypes) -> str:
        key = entry.identifier
        existing = self.read(key)
        existing.update(entry)
        self._update_index()
        self._metadata["updated"] = datetime.datetime.now(tz=datetime.timezone.utc)
        return existing.identifier

    def upsert(self, entry: lib_naan.StorableTypes):
        try:
            return self.insert(entry)
        except ValueError:
            pass
        return self.update(entry)

    def delete(self, key: str):
        i = self._index[key]
        del self._records[i]
        self._update_index()
        self._metadata["updated"] = datetime.datetime.now(tz=datetime.timezone.utc)

    @property
    def index(self):
        """
        Returns a dictionary with keys as naan / shoulder values and values as the
        offset in the internal list of entries.

        Returns:
            dict: key=naan, value=relative path to the corresponding NAAN record
        """
        return self._index

    def load_naan_reg_priv(self, naan_src: str, as_public: bool = True) -> int:
        """Load NAAN records from ANVL formatted source.

        naan_src is the full text of main_naans (i.e. contents, not path to file)

        More insanity: There's at least one NAAN record that appears to be only
        managed in n2t:
          ark:/19156/tkt42/06l redirects to:
            https://vocab.participatory-archives.ch/vocab.participatory-archives.ch/brunner//06l
          That is, only the part remaining after the prefix and shoulder is forwarded in the url, but
          there's no entry for tkt42 anywhere in the shoulders.

        For now, these are handled by redirecting to legacy-n2t.n2t.net, but should be a
        high priority for proper configuration. For 19156 the fix may be to manually add
        a shoulder `tkt42`?
        """
        UNKNOWN_CONFIGS = {
            '19156': 'https://legacy-n2t.n2t.net/ark:/${content}'
        }
        anvl_parser = lib_naan.anvl.AnvlParser()
        n = 0
        for block in anvl_parser.parseBlocks(naan_src):
            try:
                naan = lib_naan.NAAN.from_anvl_block(block)
                if as_public:
                    naan = naan.as_public()
                # TODO: !! this is a hack. Replace with magic files, and eventually with update naan registry.
                if naan.what in UNKNOWN_CONFIGS.keys():
                    naan.target.url = UNKNOWN_CONFIGS[naan.what]
                self.upsert(naan)
                n += 1
            except ValueError:
                _L.warning("Could not parse %s as NAAN", block)
        return n

    def load_shoulder_registry(self, shoulder_src: str, as_public: bool = True) -> int:
        """Load shoulder records from the shoulder_registry
        """
        anvl_parser = lib_naan.anvl.AnvlParser()
        n = 0
        for block in anvl_parser.parseBlocks(shoulder_src):
            try:
                shoulder = lib_naan.NAANShoulder.from_anvl_block(block)
                if as_public:
                    shoulder = shoulder.as_public()
                self.upsert(shoulder)
                n += 1
            except ValueError:
                _L.warning("Could not parse %s as Shoulder", block)
        return n


'''

    def read(self, naan: str, as_public:bool = False) -> StoredTypes:
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

'''
