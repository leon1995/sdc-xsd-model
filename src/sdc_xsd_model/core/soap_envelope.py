"""Lxml models for SOAP elements from https://www.w3.org/TR/soap12-part1/ and https://www.w3.org/TR/soap12-part2/."""

import functools
import pathlib
import typing
from collections.abc import Sequence

import lxml.etree

from sdc_xsd_model.core import addressing, common, discovery

PREFIX: typing.Final[str] = "s12"
NAMESPACE: typing.Final[str] = "http://www.w3.org/2003/05/soap-envelope"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.parent.joinpath("xsd", "soap-envelope.xsd").absolute()
)
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


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
    def body(self) -> common.ElementBase | None:
        # R9981: An ENVELOPE MUST have exactly zero or one child elements of the soap:Body element.
        body = self.find_by_element(Body)
        if body is None:
            return None
        if len(body) > 1:
            msg = f"Soap envelope {self!s} is violating R9981 because it has more than one soap:Body element."
            raise ValueError(msg)
        child = body[0]
        if not isinstance(child, common.ElementBase):
            msg = f"Soap envelope {self!s} contains unknown body element."
            raise TypeError(msg)
        return child

    @classmethod
    def with_header_and_body(cls, to: str | None, relates_to: str | None, action: str, body: Body) -> typing.Self:
        headers = []
        if relates_to is not None:
            headers.append(addressing.RelatesTo(relates_to))
        if to is not None:
            headers.append(addressing.To(to))
        return cls(Header(*headers, addressing.Action(action)), body)


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
    def code(self) -> FaultCode:
        value = self.find_by_element(FaultCode)
        # schema enforces presence
        assert value is not None
        return value

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


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register SOAP elements in the given lookup."""
    soap_namespace = lookup.get_namespace(NAMESPACE)
    soap_namespace["Envelope"] = Envelope
    soap_namespace["Header"] = Header
    soap_namespace["Body"] = Body
    soap_namespace["Text"] = FaultReasonText
    soap_namespace["Reason"] = FaultReason
    soap_namespace["Subcode"] = SubCode
    soap_namespace["Code"] = FaultCode
    soap_namespace["Detail"] = Detail
    soap_namespace["Fault"] = Fault
    soap_namespace["Value"] = Value
    soap_namespace["Node"] = Node
    soap_namespace["Role"] = Role


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get soap envelope parser."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, get_parser())
