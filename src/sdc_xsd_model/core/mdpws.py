"""Lxml models for MDPWS elements from IEEE 11073-20702-2016."""

from __future__ import annotations

import functools
import pathlib
import typing

import lxml.etree

from sdc_xsd_model import converter
from sdc_xsd_model.core import common

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

PREFIX: typing.Final[str] = "mdpws"
NAMESPACE: typing.Final[str] = "http://standards.ieee.org/downloads/11073/11073-20702-2016"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent.parent.joinpath("xsd", "MDPWS.xsd").absolute()
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


# -- Stream description ----------------------------------------------------------------------


class StreamSource(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}StreamSource"


class StreamAddress(common.AnyUri):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}StreamAddress"


class StreamPeriod(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}StreamPeriod"


class StreamTransmission(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}StreamTransmission"

    @property
    def type(self) -> str | None:
        return self.get("Type")

    @property
    def stream_address(self) -> StreamAddress | None:
        return self.find_by_element(StreamAddress)

    @property
    def stream_period(self) -> StreamPeriod | None:
        return self.find_by_element(StreamPeriod)


class StreamType(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}StreamType"

    @property
    def id(self) -> str:
        value = self.get("Id")
        # schema enforces presence
        assert value is not None
        return value

    @property
    def stream_type(self) -> str:
        value = self.get("StreamType")
        # schema enforces presence
        assert value is not None
        return value

    @property
    def element(self) -> str | None:
        return self.get("Element")

    @property
    def action_uri(self) -> str | None:
        return self.get("ActionUri")

    @property
    def stream_transmission(self) -> StreamTransmission:
        value = self.find_by_element(StreamTransmission)
        # schema enforces presence
        assert value is not None
        return value


class StreamTypes(common.ElementBase):
    """The optional ``mdpws:Types`` container inside ``StreamDescriptions``."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Types"


class StreamDescriptions(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}StreamDescriptions"

    @property
    def target_namespace(self) -> str:
        value = self.get("TargetNamespace")
        # schema enforces presence
        assert value is not None
        return value

    @property
    def types(self) -> StreamTypes | None:
        return self.find_by_element(StreamTypes)

    @property
    def stream_types(self) -> Sequence[StreamType]:
        return self.findall_by_element(StreamType)


# -- Safety requirements ---------------------------------------------------------------------


class Selector(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Selector"

    @property
    def id(self) -> str:
        value = self.get("Id")
        # schema enforces presence
        assert value is not None
        return value


class DualChannelDef(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}DualChannelDef"

    @property
    def algorithm(self) -> lxml.etree.QName | None:
        return converter.to_qname(self.get("Algorithm"), self.nsmap)

    @property
    def transform(self) -> lxml.etree.QName | None:
        return converter.to_qname(self.get("Transform"), self.nsmap)

    @property
    def selectors(self) -> Sequence[Selector]:
        return self.findall_by_element(Selector)


class SafetyContextDef(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SafetyContextDef"

    @property
    def selectors(self) -> Sequence[Selector]:
        return self.findall_by_element(Selector)


class SafetyReq(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SafetyReq"

    @property
    def dual_channel_def(self) -> DualChannelDef | None:
        return self.find_by_element(DualChannelDef)

    @property
    def safety_context_def(self) -> SafetyContextDef | None:
        return self.find_by_element(SafetyContextDef)


class SafetyReqAssertion(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SafetyReqAssertion"

    @property
    def transmit_dual_channel(self) -> bool:
        value = converter.to_bool(self.get("TransmitDualChannel", "true"))
        assert value is not None
        return value

    @property
    def transmit_safety_context(self) -> bool:
        value = converter.to_bool(self.get("TransmitSafetyContext", "true"))
        assert value is not None
        return value


# -- Safety information transmission ---------------------------------------------------------


class DcValue(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}DcValue"

    @property
    def referenced_selector(self) -> str:
        value = self.get("ReferencedSelector")
        # schema enforces presence
        assert value is not None
        return value


class CtxtValue(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CtxtValue"

    @property
    def referenced_selector(self) -> str:
        value = self.get("ReferencedSelector")
        # schema enforces presence
        assert value is not None
        return value


class DualChannel(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}DualChannel"

    @property
    def dc_values(self) -> Sequence[DcValue]:
        return self.findall_by_element(DcValue)


class SafetyContext(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SafetyContext"

    @property
    def ctxt_values(self) -> Sequence[CtxtValue]:
        return self.findall_by_element(CtxtValue)


class SafetyInfo(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SafetyInfo"

    @property
    def dual_channel(self) -> DualChannel | None:
        return self.find_by_element(DualChannel)

    @property
    def safety_context(self) -> SafetyContext | None:
        return self.find_by_element(SafetyContext)


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register MDPWS elements in the given lookup."""
    mdpws_namespace = lookup.get_namespace(NAMESPACE)
    mdpws_namespace["StreamSource"] = StreamSource
    mdpws_namespace["StreamAddress"] = StreamAddress
    mdpws_namespace["StreamPeriod"] = StreamPeriod
    mdpws_namespace["StreamTransmission"] = StreamTransmission
    mdpws_namespace["StreamType"] = StreamType
    mdpws_namespace["Types"] = StreamTypes
    mdpws_namespace["StreamDescriptions"] = StreamDescriptions
    mdpws_namespace["SafetyReqAssertion"] = SafetyReqAssertion
    mdpws_namespace["SafetyReq"] = SafetyReq
    mdpws_namespace["DualChannelDef"] = DualChannelDef
    mdpws_namespace["SafetyContextDef"] = SafetyContextDef
    mdpws_namespace["Selector"] = Selector
    mdpws_namespace["SafetyInfo"] = SafetyInfo
    mdpws_namespace["DualChannel"] = DualChannel
    mdpws_namespace["SafetyContext"] = SafetyContext
    mdpws_namespace["DcValue"] = DcValue
    mdpws_namespace["CtxtValue"] = CtxtValue


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get MDPWS parser."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, get_parser())
