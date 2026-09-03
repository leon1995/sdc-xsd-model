"""Tests for the MDPWS model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.core import common, mdpws, soap_envelope
from sdc_xsd_model.extension_registry import ExtensionRegistry
from sdc_xsd_model.parser import SoapEnvelopeParser

MDPWS_CASES = [
    (mdpws.StreamSource, "StreamSource"),
    (mdpws.StreamAddress, "StreamAddress"),
    (mdpws.StreamPeriod, "StreamPeriod"),
    (mdpws.StreamTransmission, "StreamTransmission"),
    (mdpws.StreamType, "StreamType"),
    (mdpws.StreamTypes, "Types"),
    (mdpws.StreamDescriptions, "StreamDescriptions"),
    (mdpws.SafetyReqAssertion, "SafetyReqAssertion"),
    (mdpws.SafetyReq, "SafetyReq"),
    (mdpws.DualChannelDef, "DualChannelDef"),
    (mdpws.SafetyContextDef, "SafetyContextDef"),
    (mdpws.Selector, "Selector"),
    (mdpws.SafetyInfo, "SafetyInfo"),
    (mdpws.DualChannel, "DualChannel"),
    (mdpws.SafetyContext, "SafetyContext"),
    (mdpws.DcValue, "DcValue"),
    (mdpws.CtxtValue, "CtxtValue"),
]


@pytest.mark.parametrize(("clazz", "local_name"), MDPWS_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure MDPWS classes expose the expected TAG value."""
    assert f"{{{mdpws.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in MDPWS_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure MDPWS classes register the expected namespace."""
    assert clazz().nsmap[mdpws.PREFIX] == mdpws.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in MDPWS_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure MDPWS classes can be serialized and deserialized correctly."""
    element, target_tag = _create_mdpws_element(clazz)
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=clazz.PARSER)
    if target_tag is not None:
        found_element = parsed_element.find(target_tag)
        if found_element is None:
            found_element = parsed_element.find(f".//{target_tag}")
        parsed_element = found_element
    assert isinstance(parsed_element, clazz)


def _make_stream_descriptions() -> mdpws.StreamDescriptions:
    return mdpws.StreamDescriptions(
        mdpws.StreamTypes(),
        mdpws.StreamType(
            mdpws.StreamTransmission(
                mdpws.StreamAddress.from_uri("udp://239.0.0.1:5555"),
                mdpws.StreamPeriod("PT0.02S"),
                attrib={"Type": "urn:example:transmission"},
            ),
            attrib={"Id": "st1", "StreamType": "urn:example:stream-type"},
        ),
        attrib={"TargetNamespace": "urn:example:target"},
    )


def _make_safety_req() -> mdpws.SafetyReq:
    return mdpws.SafetyReq(
        mdpws.DualChannelDef(mdpws.Selector("/s:Body/x:Foo/text()", attrib={"Id": "sel1"})),
        mdpws.SafetyContextDef(mdpws.Selector("/x:Mdib/@Value", attrib={"Id": "sel2"})),
    )


def _make_safety_info() -> mdpws.SafetyInfo:
    return mdpws.SafetyInfo(
        mdpws.DualChannel(mdpws.DcValue("QUJD", attrib={"ReferencedSelector": "sel1"})),
        mdpws.SafetyContext(mdpws.CtxtValue("context", attrib={"ReferencedSelector": "sel2"})),
    )


def _create_mdpws_element(  # noqa: PLR0911
    clazz: type[common.ElementBase],
) -> tuple[common.ElementBase, str | None]:
    if clazz is mdpws.StreamSource:
        return mdpws.StreamSource(), None
    if clazz is mdpws.StreamDescriptions:
        return _make_stream_descriptions(), None
    if clazz in (
        mdpws.StreamAddress,
        mdpws.StreamPeriod,
        mdpws.StreamTransmission,
        mdpws.StreamType,
        mdpws.StreamTypes,
    ):
        return _make_stream_descriptions(), clazz.TAG
    if clazz is mdpws.SafetyReqAssertion:
        return mdpws.SafetyReqAssertion(), None
    if clazz is mdpws.SafetyReq:
        return _make_safety_req(), None
    if clazz in (mdpws.DualChannelDef, mdpws.SafetyContextDef, mdpws.Selector):
        return _make_safety_req(), clazz.TAG
    if clazz is mdpws.SafetyInfo:
        return _make_safety_info(), None
    if clazz in (mdpws.DualChannel, mdpws.SafetyContext, mdpws.DcValue, mdpws.CtxtValue):
        return _make_safety_info(), clazz.TAG
    msg = f"Unexpected class: {clazz}"
    raise ValueError(msg)
