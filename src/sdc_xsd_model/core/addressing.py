"""Lxml models for WS-Addressing elements from https://www.w3.org/TR/2006/REC-ws-addr-core-20060509/."""

from __future__ import annotations

import enum
import functools
import pathlib
import typing
import uuid

import lxml.etree

from sdc_xsd_model import converter
from sdc_xsd_model.core import common

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

PREFIX: typing.Final[str] = "wsa"
# namespace has been changed in ws-discovery, therefore dont use "http://schemas.xmlsoap.org/ws/2004/08/addressing"
NAMESPACE: typing.Final[str] = "http://www.w3.org/2005/08/addressing"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent.parent.joinpath("xsd", "ws-addr.xsd").absolute()
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


IS_REFERENCE_PARAMETER_ATTR_TAG: typing.Final[str] = f"{{{NAMESPACE}}}IsReferenceParameter"

# The implied [destination] when wsa:To is absent, and the implied [address] of an absent wsa:ReplyTo.
# See https://www.w3.org/TR/2006/REC-ws-addr-core-20060509/#msgaddrpropsinfoset.
ANONYMOUS_URI: typing.Final[str] = f"{NAMESPACE}/anonymous"
# The [address] marking an endpoint that discards anything sent to it.
NONE_URI: typing.Final[str] = f"{NAMESPACE}/none"
# The [action] designating a WS-Addressing fault, and the one for SOAP-defined faults.
FAULT_ACTION: typing.Final[str] = f"{NAMESPACE}/fault"
SOAP_FAULT_ACTION: typing.Final[str] = f"{NAMESPACE}/soap/fault"


class RelationshipType(enum.StrEnum):
    REPLY = f"{NAMESPACE}/reply"


class FaultCodesType(enum.StrEnum):
    INVALID_ADDRESSING_HEADER = f"{{{NAMESPACE}}}InvalidAddressingHeader"
    INVALID_ADDRESS = f"{{{NAMESPACE}}}InvalidAddress"
    INVALID_EPR = f"{{{NAMESPACE}}}InvalidEPR"
    INVALID_CARDINALITY = f"{{{NAMESPACE}}}InvalidCardinality"
    MISSING_ADDRESS_IN_EPR = f"{{{NAMESPACE}}}MissingAddressInEPR"
    DUPLICATE_MESSAGE_ID = f"{{{NAMESPACE}}}DuplicateMessageID"
    ACTION_MISMATCH = f"{{{NAMESPACE}}}ActionMismatch"
    MESSAGE_ADDRESSING_HEADER_REQUIRED = f"{{{NAMESPACE}}}MessageAddressingHeaderRequired"
    DESTINATION_UNREACHABLE = f"{{{NAMESPACE}}}DestinationUnreachable"
    ACTION_NOT_SUPPORTED = f"{{{NAMESPACE}}}ActionNotSupported"
    ENDPOINT_UNAVAILABLE = f"{{{NAMESPACE}}}EndpointUnavailable"


class AttributedURIType(common.AnyUri):
    @classmethod
    def from_uri(
        cls,
        uri: str | uuid.UUID,
        *children: str | typing.Self,
        attrib: Mapping[str, str | bytes] | None = None,
        nsmap: Mapping[str | None, str] | Mapping[str, str] | None = None,
    ) -> typing.Self:
        """Create an AttributedURIType from a URI string or UUID."""
        return cls(uri.urn if isinstance(uri, uuid.UUID) else uri, *children, attrib=attrib, nsmap=nsmap)

    @classmethod
    def from_random_uri(
        cls,
        *children: str | typing.Self,
        attrib: Mapping[str, str | bytes] | None = None,
        nsmap: Mapping[str | None, str] | Mapping[str, str] | None = None,
    ) -> typing.Self:
        """Create an AttributedURIType with a random UUID URN."""
        return cls.from_uri(uuid.uuid4(), *children, attrib=attrib, nsmap=nsmap)


class Address(AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Address"


class Metadata(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Metadata"


class ReferenceParameters(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ReferenceParameters"


class EndpointReference(common.ElementBase):
    TAG: str = f"{{{NAMESPACE}}}EndpointReference"

    @property
    def address(self) -> Address:
        value = self.find_by_element(Address)
        # schema enforces presence
        assert value is not None
        return value

    @property
    def reference_parameters(self) -> Sequence[ReferenceParameters]:
        return self.findall_by_element(ReferenceParameters)

    @property
    def metadata(self) -> Sequence[Metadata]:
        return self.findall_by_element(Metadata)

    @classmethod
    def with_address(
        cls,
        address: str,
        *children: str | typing.Self,
        attrib: Mapping[str, str | bytes] | None = None,
        nsmap: Mapping[None | str, str] | Mapping[str, str] | None = None,
    ) -> typing.Self:
        """Create an EndpointReference with the given address."""
        return cls(Address.from_uri(address), *children, attrib=attrib, nsmap=nsmap)


class To(AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}To"


class From(EndpointReference):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}From"


class ReplyTo(EndpointReference):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ReplyTo"


class FaultTo(EndpointReference):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}FaultTo"


class Action(AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Action"


class MessageID(AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MessageID"


class RelatesTo(AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}RelatesTo"

    @property
    def relationship_type(self) -> str | None:
        return self.get("RelationshipType")


class RetryAfter(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}RetryAfter"

    @property
    def value(self) -> int:
        value = converter.to_int(self.text)
        # schema enforces presence
        assert value is not None
        return value


class ProblemHeaderQName(common.QNameType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ProblemHeaderQName"


class ProblemIRI(AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ProblemIRI"


class SoapAction(common.AnyUri):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SoapAction"


class ProblemAction(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ProblemAction"

    @property
    def action(self) -> Action | None:
        return self.find_by_element(Action)

    @property
    def soap_action(self) -> SoapAction | None:
        return self.find_by_element(SoapAction)


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register WS-Addressing elements in the given lookup."""
    addressing_namespace = lookup.get_namespace(NAMESPACE)
    addressing_namespace["Address"] = Address
    addressing_namespace["EndpointReference"] = EndpointReference
    addressing_namespace["ReferenceParameters"] = ReferenceParameters
    addressing_namespace["Metadata"] = Metadata
    addressing_namespace["To"] = To
    addressing_namespace["From"] = From
    addressing_namespace["ReplyTo"] = ReplyTo
    addressing_namespace["FaultTo"] = FaultTo
    addressing_namespace["Action"] = Action
    addressing_namespace["MessageID"] = MessageID
    addressing_namespace["RelatesTo"] = RelatesTo
    addressing_namespace["RetryAfter"] = RetryAfter
    addressing_namespace["ProblemHeaderQName"] = ProblemHeaderQName
    addressing_namespace["ProblemIRI"] = ProblemIRI
    addressing_namespace["SoapAction"] = SoapAction
    addressing_namespace["ProblemAction"] = ProblemAction


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get addressing parser."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, get_parser())
