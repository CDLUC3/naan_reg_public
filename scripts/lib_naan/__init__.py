"""
This module contains the model for NAAN records.

"""
import copy
import dataclasses
import datetime
import logging
import typing

import dacite

from . import anvl

PYDANTIC_AVAILABLE = False
try:
    from pydantic.dataclasses import dataclass

    PYDANTIC_AVAILABLE = True
except ModuleNotFoundError:
    from dataclasses import dataclass


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

    def update(self, record:'Target') -> 'Target':
        self.url = record.url
        self.http_code = record.http_code
        return self


@dataclass
class PublicNAAN_who:
    """Publicly visible information for organization responsible for NAAN"""

    name: str = dataclasses.field(
        metadata=dict(description="Official organization name")
    )
    name_native: typing.Optional[str] = dataclasses.field(
        default=None,
        metadata=dict(description="Non-english variant of the official organization.")
    )
    acronym: typing.Optional[str] = dataclasses.field(
        default=None,
        metadata=dict(description="Optional display acronym derived from DNS name"),
    )
    def update(self, record:'PublicNAAN_who') -> 'PublicNAAN_who':
        self.name = record.name
        self.name_native = record.name_native
        self.acronym = record.acronym
        return self


@dataclass
class NAAN_who(PublicNAAN_who):
    """Organization responsible for NAAN"""

    address: typing.Optional[str] = dataclasses.field(
        default=None, metadata=dict(description="Physical address of organization")
    )

    def update(self, record:'NAAN_who') -> 'NAAN_who':
        super().update(record)
        if isinstance(record, NAAN_who):
            self.address = record.address
        return self


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

    def update(self, record:'NAAN_how') -> 'NAAN_how':
        self.orgtype = record.orgtype
        self.policy = record.policy
        self.tenure = record.tenure
        self.policy_url = record.policy_url
        return self


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

    def update(self, record:'NAAN_contact') -> 'NAAN_contact':
        self.name = record.name
        self.unit = record.unit
        self.tenure = record.tenure
        self.email = record.email
        self.phone = record.phone
        return self


@dataclass
class PublicNAAN:
    what: str = dataclasses.field(
        metadata=dict(description="The NAAN value, e.g. 12345")
    )
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
    who: PublicNAAN_who
    na_policy: NAAN_how
    test_identifier: typing.Optional[str] = dataclasses.field(
        default=None,
        metadata=dict(
            description=(
                "A specific, concrete ARK that you plan to support and that you will permit us to"
                "use periodically for testing service availability."
            )
        )
    )
    service_provider: typing.Optional[str] = dataclasses.field(
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
        default="PublicNAAN"
    )

    @property
    def identifier(self) -> str:
        return self.what


    def as_flat(self) -> dict:
        return {
            "what": self.what,
            "who": self.who.name,
            "where": self.where,
            "when": self.when,
        }

    def update(self, record: 'PublicNAAN') -> 'PublicNAAN':
        if record.what is not None:
            if record.what != self.what:
                raise ValueError(f"Cannot update the naan value, incoming {record.what} != {self.what}.")
        self.where = record.where
        self.target.update(record.target)
        self.who.update(record.who)
        self.na_policy.update(record.na_policy)
        self.test_identifier = record.test_identifier
        self.service_provider = record.service_provider
        self.purpose = record.purpose
        self.when = record.when
        return self

    def as_public(self) -> 'PublicNAAN':
        return self


@dataclass
class NAAN(PublicNAAN):
    who: NAAN_who
    why: str = dataclasses.field(
        default='ARK',
        metadata=dict(description="Purpose for this record, 'ARK'")
    )
    contact: NAAN_contact=None
    alternate_contact: typing.Optional[NAAN_contact]=None
    comments: typing.Optional[typing.List[dict]] = dataclasses.field(
        default=None, metadata=dict(description="Comments about NAAN record")
    )
    provider: typing.Optional[str] = dataclasses.field(
        default=None, metadata=dict(description="")
    )
    rtype: str = dataclasses.field(
        metadata=dict(description="Type of this record."),
        default="NAAN"
    )

    @property
    def key(self) -> str:
        return self.what

    def as_public(self) -> PublicNAAN:
        public_who = PublicNAAN_who(name=self.who.name, name_native=self.who.name_native, acronym=self.who.acronym)
        public = PublicNAAN(
            what=self.what,
            where=self.where,
            target=self.target,
            when=self.when,
            who=public_who,
            na_policy=self.na_policy,
            test_identifier=self.test_identifier,
            service_provider=self.service_provider,
            purpose=self.purpose
        )
        return public

    def update(self, record: 'NAAN') -> 'NAAN':
        if record.what is not None:
            if record.what != self.what:
                raise ValueError(f"Cannot update the naan value, incoming {record.what} != {self.what}.")
        self.where = record.where
        self.target = record.target
        self.test_identifier = record.test_identifier
        self.service_provider = record.service_provider
        self.purpose = record.purpose
        self.when = datetime.datetime.now(tz=datetime.timezone.utc)
        self.who.update(record.who)
        self.na_policy.update(record.na_policy)
        if isinstance(record, NAAN):
            self.why = record.why
            self.contact = copy.deepcopy(record.contact)
            self.alternate_contact = copy.deepcopy(record.alternate_contact)
            self.comments = copy.deepcopy(record.comments)
            self.provider = record.provider
        return self

    @classmethod
    def from_anvl_block(cls, block: dict) -> 'NAAN':
        """
        Factory method for creating NAAN from an ANVL parsed block
        """
        _L = logging.getLogger("lib_naan")
        data = block.get("naa", {})
        res = {"comments": None, "provider": None}
        _address = None
        for k, v in data.items():
            if k == "who":
                _L.debug(v)
                who_parts = anvl.split_who(v)
                _who = NAAN_who(**who_parts)
                res["who"] = _who
            elif k == "when":
                res["when"] = anvl.datestring2date(v)
            elif k == "where":
                res["where"] = v
                _target_dict = anvl.urlstr2target(v)
                res["target"] = Target(**_target_dict)
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
        raise ValueError("NAAN record has no 'what' field!")


@dataclass
class PublicNAANShoulder:
    shoulder:str = dataclasses.field(
        metadata=dict(description="The shoulder part of the record")
    )
    naan: str = dataclasses.field(
        metadata=dict(description="The naan part of the record")
    )
    what: str = dataclasses.field(
        metadata=dict(description="The combination of naan / shoulder"),
        init=False
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
    test_identifier: typing.Optional[str] = dataclasses.field(
        default=None,
        metadata=dict(
            description=(
                "A specific, concrete ARK that you plan to support and that you will permit us to"
                "use periodically for testing service availability."
            )
        )
    )
    rtype: str = dataclasses.field(
        metadata=dict(description="Type of this record."),
        default="PublicNAANShoulder"
    )

    @property
    def identifier(self) -> str:
        return f"{self.naan}/{self.shoulder}"

    def __post_init__(self):
        self.what = f"{self.naan}/{self.shoulder}"

    def as_public(self) -> 'PublicNAANShoulder':
        return self

    def update(self, record:'PublicNAANShoulder') -> 'PublicNAANShoulder':
        if record.shoulder is not None:
            if record.shoulder != self.shoulder:
                raise ValueError(f"Cannot update the shoulder value, incoming {record.shoulder} != {self.shoulder}.")
        if record.naan is not None:
            if record.naan != self.naan:
                raise ValueError(f"Cannot update the naan value, incoming {record.naan} != {self.naan}.")
        self.who.update(record.who)
        self.where = record.where
        self.target.update(record.target)
        self.when = record.when
        self.na_policy.update(record.na_policy)
        return self


@dataclass
class NAANShoulder(PublicNAANShoulder):
    who: NAAN_who
    contact: NAAN_contact=None
    alternate_contact: typing.Optional[NAAN_contact]=None
    comments: typing.Optional[typing.List[dict]] = dataclasses.field(
        default=None, metadata=dict(description="Comments about Shoulder record")
    )
    provider: typing.Optional[str] = dataclasses.field(
        default=None, metadata=dict(description="")
    )
    rtype: str = dataclasses.field(
        metadata=dict(description="Type of this record."),
        default="NAANShoulder"
    )

    @property
    def key(self) -> str:
        return f"{self.naan}/{self.shoulder}"

    def as_public(self) -> PublicNAANShoulder:
        public_who = PublicNAAN_who(
            name=self.who.name,
            name_native=self.who.name_native,
            acronym=self.who.acronym
        )
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

    def update(self, record:'NAANShoulder') -> 'NAANShoulder':
        if record.shoulder is not None:
            if record.shoulder != self.shoulder:
                raise ValueError(f"Cannot update the shoulder value, incoming {record.shoulder} != {self.shoulder}.")
        if record.naan is not None:
            if record.naan != self.naan:
                raise ValueError(f"Cannot update the naan value, incoming {record.naan} != {self.naan}.")
        self.who.update(record.who)
        # deep copy is used where property may be None
        if isinstance(record, NAANShoulder):
            self.contact = copy.deepcopy(record.contact)
            self.alternate_contact = copy.deepcopy(record.alternate_contact)
            self.comments = copy.deepcopy(record.comments)
            self.provider = record.provider
        self.where = record.where
        self.target.update(record.target)
        self.when = record.when
        self.na_policy.update(record.na_policy)
        return self

    @classmethod
    def from_anvl_block(cls, block: dict) -> 'NAANShoulder':
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
                who_parts = anvl.split_who(v)
                _who = NAAN_who(**who_parts)
                res["who"] = _who
            elif k == "when":
                res["when"] = anvl.datestring2date(v)
            elif k == "where":
                res["where"] = v
                _target_dict = anvl.urlstr2target(v)
                res["target"] = Target(**_target_dict)
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
        raise ValueError(f"No 'shoulder' entry in block!")



def datetime_from_iso_string(iso_string: str) -> datetime:
    if isinstance(iso_string, str):
        return datetime.datetime.fromisoformat(iso_string)
    return iso_string


StorableTypes = typing.Union[
        NAAN, PublicNAAN, NAANShoulder, PublicNAANShoulder
    ]

def entryFromDict(data) -> typing.Any:
    _type = data.get("rtype", None)
    config = dacite.Config(type_hooks={datetime.datetime: datetime_from_iso_string})
    if _type is None:
        return None
    if _type == "NAAN":
        return dacite.from_dict(data_class=NAAN, data=data, config=config)
    if _type == "PublicNAAN":
        return dacite.from_dict(data_class=PublicNAAN, data=data, config=config)
    if _type == "NAANShoulder":
        return dacite.from_dict(data_class=NAANShoulder, data=data, config=config)
    if _type == "PublicNAANShoulder":
        return dacite.from_dict(data_class=NAANShoulder, data=data, config=config)
    return None
