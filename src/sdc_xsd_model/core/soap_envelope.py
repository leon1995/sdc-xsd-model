"""Lxml models for SOAP elements from https://www.w3.org/TR/soap12-part1/ and https://www.w3.org/TR/soap12-part2/."""

import enum
import functools
import pathlib
import typing
import uuid
from collections.abc import Sequence

import lxml.etree

from sdc_xsd_model import converter
from sdc_xsd_model.core import addressing, common, discovery, eventing, mdpws

PREFIX: typing.Final[str] = "s12"
NAMESPACE: typing.Final[str] = "http://www.w3.org/2003/05/soap-envelope"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.parent.joinpath("xsd", "soap-envelope.xsd").absolute()
)
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


class FaultCodeEnum(enum.StrEnum):
    DATA_ENCODING_UNKNOWN = f"{{{NAMESPACE}}}DataEncodingUnknown"
    MUST_UNDERSTAND = f"{{{NAMESPACE}}}MustUnderstand"
    RECEIVER = f"{{{NAMESPACE}}}Receiver"
    SENDER = f"{{{NAMESPACE}}}Sender"
    VERSION_MISMATCH = f"{{{NAMESPACE}}}VersionMismatch"


class Header(common.ElementBase):
    """The SOAP header: a bag of namespace-qualified blocks, in any order."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Header"

    @property
    def action(self) -> addressing.Action:
        """Return the wsa:Action block, which every SDC message carries.

        ``wsa:Action`` is the one REQUIRED message addressing property (ws-addr-core 3.2) and dpws:R5005
        obliges every SERVICE to support WS-Addressing, so an SDC message without one is malformed. It is the
        profile rather than the schema that guarantees this, so a missing block raises rather than asserting.

        Raises:
            ValueError: if the header carries no wsa:Action block.

        """
        action = self.find_by_element(addressing.Action)
        if action is None:
            msg = f"Soap header {self!s} has no wsa:Action, which ws-addr-core 3.2 requires."
            raise ValueError(msg)
        return action

    @property
    def to(self) -> addressing.To | None:
        """Return the wsa:To block; ``None`` implies ``addressing.ANONYMOUS_URI`` (ws-addr-core 3.2)."""
        return self.find_by_element(addressing.To)

    @property
    def message_id(self) -> addressing.MessageID | None:
        return self.find_by_element(addressing.MessageID)

    @property
    def relates_to(self) -> addressing.RelatesTo | None:
        """Return the first wsa:RelatesTo block, or ``None``.

        dpws:R0019 and dpws:R0040 require one of relationship type reply in every response and every SOAP
        Fault. An absent ``RelationshipType`` attribute already means reply, so responses need not set it.
        """
        return self.find_by_element(addressing.RelatesTo)

    @property
    def reply_to(self) -> addressing.ReplyTo | None:
        """Return the wsa:ReplyTo block; an absent one implies ``addressing.ANONYMOUS_URI``."""
        return self.find_by_element(addressing.ReplyTo)

    @property
    def fault_to(self) -> addressing.FaultTo | None:
        return self.find_by_element(addressing.FaultTo)

    @property
    def from_(self) -> addressing.From | None:
        """Return the wsa:From block. Trailing underscore because ``from`` is a keyword."""
        return self.find_by_element(addressing.From)

    @property
    def app_sequence(self) -> discovery.AppSequence | None:
        return self.find_by_element(discovery.AppSequence)

    @property
    def safety_info(self) -> mdpws.SafetyInfo | None:
        """Return the mdpws:SafetyInfo block, or ``None``.

        MDPWS 9.4.2 transports safety information in the MESSAGE header: the dual-channel representation of
        safety-relevant values (``mdpws:DualChannel``) and the safety context they were determined in
        (``mdpws:SafetyContext``). A provider announces that it requires them per operation with an
        ``mdpws:SafetyReq`` in the operation descriptor's ``ext:Extension`` (glue:R0027), so a consumer
        invoking such an operation has to put this block in the request header.
        """
        return self.find_by_element(mdpws.SafetyInfo)

    @classmethod
    def for_action(
        cls,
        action: str,
        *blocks: common.ElementBase,
        to: str | None = None,
        relates_to: str | uuid.UUID | None = None,
        message_id: str | uuid.UUID | None = None,
    ) -> typing.Self:
        """Build a header for *action*, followed by any extra *blocks*.

        Blocks are emitted as ``To, Action, MessageID, RelatesTo``, then *blocks*. Order is not normative --
        wsdd-discovery states header blocks may appear in any order -- but matching the order real devices
        send keeps round-trip diffs readable. *message_id* defaults to a fresh UUID URN; pass any extra block
        (``wsd:AppSequence``, ``mdpws:SafetyInfo``, a reference parameter) positionally.
        """
        children: list[common.ElementBase] = []
        if to is not None:
            children.append(addressing.To.from_uri(to))
        children.append(addressing.Action.from_uri(action))
        children.append(
            addressing.MessageID.from_uri(message_id)
            if message_id is not None
            else addressing.MessageID.from_random_uri(),
        )
        if relates_to is not None:
            children.append(addressing.RelatesTo.from_uri(relates_to))
        return cls(*children, *blocks)


class Body(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Body"


class Envelope(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Envelope"

    @property
    def header(self) -> Header:
        """Return the soap:Header, which every SDC message carries.

        The schema makes it optional (``minOccurs="0"``), but dpws:R5005 requires WS-Addressing and
        ws-addr-core 3.2 makes ``wsa:Action`` REQUIRED, so an SDC envelope always has one. As with
        ``Header.action`` the guarantee is the profile's, not the schema's, so this raises on wire input that
        breaks it rather than asserting.

        Raises:
            ValueError: if the envelope has no soap:Header.

        """
        header = self.find_by_element(Header)
        if header is None:
            msg = f"Soap envelope {self!s} has no soap:Header, which dpws:R5005 requires for wsa:Action."
            raise ValueError(msg)
        return header

    @property
    def body(self) -> common.ElementBase | None:
        # R9981: An ENVELOPE MUST have exactly zero or one child elements of the soap:Body element.
        body = self.find_by_element(Body)
        if body is None:
            return None
        # ``findall("*")`` matches element children only; comments and processing instructions are
        # legal inside soap:Body and must not be counted or returned.
        children = body.findall("*")
        if not children:
            return None
        if len(children) > 1:
            msg = f"Soap envelope {self!s} is violating R9981 because soap:Body has more than one child element."
            raise ValueError(msg)
        child = children[0]
        if not isinstance(child, common.ElementBase):
            msg = f"Soap envelope {self!s} contains unknown body element."
            raise TypeError(msg)
        return child

    def body_as[B: common.ElementBase](self, element: type[B]) -> B:
        """Return the ``soap:Body`` child, checked to be an instance of *element*.

        Returns ``None`` if the envelope has no ``soap:Body`` child (permitted by R9981).
        Raises ``TypeError`` if a body is present but is not an instance of *element*.
        """
        body = self.body
        if body is None:
            msg = f"Soap envelope {self!s} expected a soap:Body child but has none."
            raise TypeError(msg)
        if not isinstance(body, element):
            actual = type(body).__name__
            msg = f"Soap envelope {self!s} expected a soap:Body child of type {element.__name__}, got {actual}."
            raise TypeError(msg)
        return body

    @classmethod
    def for_action(
        cls,
        action: str,
        payload: common.ElementBase | None = None,
        *blocks: common.ElementBase,
        to: str | None = None,
        relates_to: str | uuid.UUID | None = None,
        message_id: str | uuid.UUID | None = None,
    ) -> typing.Self:
        """Build an envelope carrying *payload* in its soap:Body and a header for *action*.

        *payload* is the body child -- the same element ``body`` returns -- and is wrapped in a ``soap:Body``
        here; pass ``None`` for a message with an empty body, which is still mandatory (``minOccurs="1"``).
        Header *blocks*, *to*, *relates_to* and *message_id* are forwarded to ``Header.for_action``.
        """
        header = Header.for_action(action, *blocks, to=to, relates_to=relates_to, message_id=message_id)
        return cls(header, Body(payload) if payload is not None else Body())


class Value(common.QNameType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Value"


class FaultReasonText(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Text"

    @property
    def lang(self) -> str:
        value = self.get("{http://www.w3.org/XML/1998/namespace}lang")
        # schema enforces presence
        assert value is not None
        return value


class FaultReason(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Reason"

    @property
    def texts(self) -> Sequence[FaultReasonText]:
        return self.findall_by_element(FaultReasonText)


class SubCode(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Subcode"

    @property
    def value(self) -> Value:
        value = self.find_by_element(Value)
        # schema enforces presence
        assert value is not None
        return value

    @property
    def subcode(self) -> "SubCode | None":
        return self.find_by_element(SubCode)


class FaultCode(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Code"

    @property
    def value(self) -> Value:
        value = self.find_by_element(Value)
        # schema enforces presence
        assert value is not None
        return value

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
    def reason(self) -> FaultReason:
        value = self.find_by_element(FaultReason)
        # schema enforces presence
        assert value is not None
        return value

    @property
    def node(self) -> Node | None:
        return self.find_by_element(Node)

    @property
    def role(self) -> Role | None:
        return self.find_by_element(Role)

    @property
    def detail(self) -> Detail | None:
        return self.find_by_element(Detail)


class NotUnderstood(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}NotUnderstood"

    @property
    def qname(self) -> lxml.etree.QName:
        value = converter.to_qname(self.get("qname"), self.nsmap)
        # schema enforces presence
        assert value is not None
        return value


class SupportedEnvelope(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SupportedEnvelope"

    @property
    def qname(self) -> lxml.etree.QName:
        value = converter.to_qname(self.get("qname"), self.nsmap)
        # schema enforces presence
        assert value is not None
        return value


class Upgrade(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Upgrade"

    @property
    def supported_envelopes(self) -> Sequence[SupportedEnvelope]:
        return self.findall_by_element(SupportedEnvelope)


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
    soap_namespace["NotUnderstood"] = NotUnderstood
    soap_namespace["Upgrade"] = Upgrade
    soap_namespace["SupportedEnvelope"] = SupportedEnvelope


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get soap envelope parser.

    Every namespace ``Header`` returns a class from is registered here, because ``find_by_element`` is an
    unchecked cast: without the registration it hands back a plain ``_Element`` typed as the expected class,
    and the error surfaces far from here rather than at the property. That means WS-Addressing (all but two
    ``Header`` properties), WS-Discovery (``app_sequence``) and MDPWS (``safety_info``).

    Validity is unaffected -- ``soap-envelope.xsd`` imports none of these schemas, so the
    ``processContents="lax"`` wildcard skips those blocks either way. A *body* in one of these namespaces
    still only resolves through ``parser.sdc_parser``, which registers every module and validates against the
    whole schema set.
    """
    lookup = lxml.etree.ElementNamespaceClassLookup()
    addressing.set_lookup(lookup)
    discovery.set_lookup(lookup)
    mdpws.set_lookup(lookup)
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, get_parser())
