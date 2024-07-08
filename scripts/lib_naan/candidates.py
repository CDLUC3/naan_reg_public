"""
Copyright©2024, Regents of the University of California

License: https://opensource.org/license/mit, See LICENSE

This module contains methods for managing the candidate_naans list.
"""

import datetime
import logging
import os
import re
import shutil

_L = logging.getLogger(__name__)


def get_timestamp():
    ds = datetime.datetime.now(tz=datetime.timezone.utc)
    return ds.isoformat(timespec="seconds")


class CandidateNaans:
    def __init__(self, candidate_naan_file: str):
        self.candidate_naans_file = candidate_naan_file
        self.line_match = re.compile(r"(?P<comment>#\s*)?(?P<naan>[0-9]{5})(?P<msg>.*)")

    def get_next_naan(self) -> str:
        """
        Returns the next available NAAN value.

        No changes are made to the file.

        Returns:
            str: The next available NAAN value
        """
        with open(self.candidate_naans_file) as inf:
            data = inf.read()
        rows = data.split("\n")
        for row in rows:
            match = self.line_match.match(row.strip())
            if match is None:
                continue
            if match.group("naan") == "90909":
                continue
            if match.group("comment") is not None:
                continue
            naan_value = match.group("naan")
            return naan_value

    def allocate_next_naan(self, message: str) -> str:
        """
        Allocates the next available NAAN value and mutates the
        candidate_naans file to record that it has been allocated.

        A backup of the candidate_naans file is made prior to any
        changes being made to the file.

        Parameters:
            message: The message to add to the NAAN entry

        Returns:
            str: The next available NAAN
        """
        bak_file = f"{self.candidate_naans_file}.bak"
        new_file = f"{self.candidate_naans_file}.new"
        shutil.copyfile(self.candidate_naans_file, new_file)
        with open(new_file) as inf:
            data = inf.read()
        rows = data.split("\n")
        assigned = None
        try:
            with open(new_file, "w") as dest:
                for row in rows:
                    if assigned is not None:
                        print(row, file=dest)
                        continue
                    match = self.line_match.match(row.strip())
                    if match is None:
                        print(row, file=dest)
                        continue
                    if match.group("naan") == "90909":
                        print(row, file=dest)
                        continue
                    if match.group("comment") is not None:
                        print(row, file=dest)
                        continue
                    assigned = match.group("naan")
                    print(f"# {assigned} {get_timestamp()} {message}", file=dest)
                    _L.info("Assigned NAAN %s to %s", assigned, message)
        except Exception as e:
            _L.warning("Unable to create new NAAN file")
            _L.error(e)
            if os.path.exists(new_file):
                os.remove(new_file)
            raise e
        try:
            if os.path.exists(bak_file):
                os.remove(bak_file)
        except Exception as e:
            _L.error("Unable to remove existing backup file. NAAN not allocated.")
            raise e
        try:
            os.rename(self.candidate_naans_file, bak_file)
        except Exception as e:
            _L.warning("An error was encountered while making a backup of the candidate naans file.")
            _L.error(e)
            raise e
        try:
            os.rename(new_file, self.candidate_naans_file)
        except Exception as e:
            # Roll back.
            _L.warning("An error was encountered updating the candidate naans file.")
            _L.error(e)
            os.rename(bak_file, self.candidate_naans_file)
            os.remove(new_file)
            raise e
        return assigned
