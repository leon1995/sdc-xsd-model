"""Lxml models for WS-Addressing elements from https://www.w3.org/TR/2006/REC-ws-addr-core-20060509/."""
import functools
import pathlib
import typing
import uuid
from collections.abc import Sequence

import lxml.etree

from sdc_xsd_model.models import common

PREFIX: typing.Final[str] = "wsa"
# namespace has been changed in ws-discovery, therefore dont use "http://schemas.xmlsoap.org/ws/2004/08/addressing"
NAMESPACE: typing.Final[str] = "http://www.w3.org/2005/08/addressing"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent.parent.joinpath("xsd", "ws-addr.xsd").absolute()
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


class AttributedURIType(common.AnyUri):

    @classmethod
    def from_uri(cls, uri: str | uuid.UUID, **kwargs: str | bytes) -> typing.Self:
        """Create an AttributedURIType from a URI string or UUID."""
        return cls(uri.urn if isinstance(uri, uuid.UUID) else uri, **kwargs)

    @classmethod
    def from_random_uri(cls, **kwargs: str | bytes) -> typing.Self:
        """Create an AttributedURIType with a random UUID URN."""
        return cls.from_uri(uuid.uuid4(), **kwargs)


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
        # schema enforces presence
        return self.find_by_element(Address)

    @property
    def reference_parameters(self) -> Sequence[ReferenceParameters]:
        return self.findall_by_element(ReferenceParameters)

    @property
    def metadata(self) -> Sequence[Metadata]:
        return self.findall_by_element(Metadata)

    @classmethod
    def with_address(cls, address: str, **kwargs: str | bytes) -> typing.Self:
        """Create an EndpointReference with the given address."""
        return cls(Address.from_uri(address), **kwargs)


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


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    lookup = lxml.etree.ElementNamespaceClassLookup()
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser

for cls in (
    AttributedURIType,
    Address,
    Metadata,
    ReferenceParameters,
    EndpointReference,
    To,
    From,
    ReplyTo,
    FaultTo,
    Action,
    MessageID,
    RelatesTo,
):
    cls.PARSER = get_parser()
