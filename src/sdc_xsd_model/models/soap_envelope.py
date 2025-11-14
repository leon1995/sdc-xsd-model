"""Lxml models for SOAP elements from https://www.w3.org/TR/soap12-part1/ and https://www.w3.org/TR/soap12-part2/."""

import typing
from collections.abc import Sequence

import lxml.etree

from sdc_xsd_model.models import addressing, common, discovery

PREFIX: typing.Final[str] = "s12"
NAMESPACE: typing.Final[str] = "http://www.w3.org/2003/05/soap-envelope"

lxml.etree.register_namespace(PREFIX, NAMESPACE)


class Header(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Header"

    @property
    def action(self) -> addressing.Action | None:
        return self.find_by_element(addressing.Action)

    @property
    def to(self) -> addressing.To | None:
        return self.find_by_element(addressing.To)

    @property
    def relates_to(self) -> addressing.RelatesTo | None:
        return self.find_by_element(addressing.RelatesTo)

    @property
    def app_seqeunce(self) -> discovery.AppSequence | None:
        return self.find_by_element(discovery.AppSequence)

    @property
    def message_id(self) -> addressing.MessageID | None:
        return self.find_by_element(addressing.MessageID)

    @property
    def reply_to(self) -> addressing.ReplyTo | None:
        return self.find_by_element(addressing.ReplyTo)


class Body(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Body"


class Envelope(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Envelope"

    @property
    def header(self) -> Header | None:
        return self.find_by_element(Header)

    @property
    def body(self) -> Body | None:
        return self.find_by_element(Body)


class Value(common.QNameType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Value"


class FaultReasonText(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Text"

    @property
    def lang(self) -> str | None:
        return self.get("{http://www.w3.org/XML/1998/namespace}lang")


class FaultReason(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Reason"

    @property
    def texts(self) -> Sequence[FaultReasonText]:
        return self.findall_by_element(FaultReasonText)


class SubCode(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Subcode"

    @property
    def value(self) -> Value | None:
        return self.find_by_element(Value)

    @property
    def subcode(self) -> "SubCode | None":
        return self.find_by_element(SubCode)


class FaultCode(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Code"

    @property
    def value(self) -> Value | None:
        return self.find_by_element(Value)

    @property
    def subcode(self) -> SubCode | None:
        return self.find_by_element(SubCode)


class Detail(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Detail"


class Node(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Node"


class Role(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Role"


class Fault(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Fault"

    @property
    def code(self) -> FaultCode | None:
        return self.find_by_element(FaultCode)

    @property
    def reason(self) -> FaultReason | None:
        return self.find_by_element(FaultReason)

    @property
    def node(self) -> Node | None:
        return self.find_by_element(Node)

    @property
    def role(self) -> Role | None:
        return self.find_by_element(Role)

    @property
    def detail(self) -> Detail | None:
        return self.find_by_element(Detail)
