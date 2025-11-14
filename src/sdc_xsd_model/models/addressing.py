"""Lxml models for WS-Addressing elements from https://www.w3.org/TR/2006/REC-ws-addr-core-20060509/."""

import typing
from collections.abc import Sequence

import lxml.etree

from sdc_xsd_model.models import common

PREFIX: typing.Final[str] = "wsa"
NAMESPACE: typing.Final[str] = "http://www.w3.org/2005/08/addressing"

lxml.etree.register_namespace(PREFIX, NAMESPACE)


class AttributedURIType(common.AnyUri):
    pass


class Address(AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Address"


class Metadata(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Metadata"


class ReferenceParameters(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ReferenceParameters"


class EndpointReference(common.ElementBase):
    TAG: str = f"{{{NAMESPACE}}}EndpointReference"

    @property
    def address(self) -> Address | None:
        return self.find_by_element(Address)

    @property
    def reference_parameters(self) -> Sequence[ReferenceParameters]:
        return self.findall_by_element(ReferenceParameters)

    @property
    def metadata(self) -> Sequence[Metadata]:
        return self.findall_by_element(Metadata)


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
