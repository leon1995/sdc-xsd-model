"""Tests for the SOAP envelope model classes."""

from collections.abc import Mapping

import lxml.etree
import pytest

from sdc_xsd_model.core import addressing, common, discovery, soap_envelope

XMLNS: str = "http://www.w3.org/2000/xmlns/"
XML_LANG: str = "http://www.w3.org/XML/1998/namespace"

SOAP_ENVELOPE_CASES = [
    (soap_envelope.Header, "Header"),
    (soap_envelope.Body, "Body"),
    (soap_envelope.Envelope, "Envelope"),
    (soap_envelope.Value, "Value"),
    (soap_envelope.FaultReasonText, "Text"),
    (soap_envelope.FaultReason, "Reason"),
    (soap_envelope.SubCode, "Subcode"),
    (soap_envelope.FaultCode, "Code"),
    (soap_envelope.Detail, "Detail"),
    (soap_envelope.Node, "Node"),
    (soap_envelope.Role, "Role"),
    (soap_envelope.Fault, "Fault"),
    (soap_envelope.NotUnderstood, "NotUnderstood"),
    (soap_envelope.Upgrade, "Upgrade"),
    (soap_envelope.SupportedEnvelope, "SupportedEnvelope"),
]


@pytest.mark.parametrize(("clazz", "local_name"), SOAP_ENVELOPE_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure SOAP envelope classes expose the expected TAG value."""
    assert f"{{{soap_envelope.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in SOAP_ENVELOPE_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure SOAP envelope classes register the expected namespace."""
    assert clazz().nsmap[soap_envelope.PREFIX] == soap_envelope.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in SOAP_ENVELOPE_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure eventing classes can be serialized and deserialized correctly."""
    element, target_tag = _create_envelope_element(clazz)
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=clazz.PARSER)
    if target_tag is not None:
        found_element = parsed_element.find(target_tag)
        if found_element is None:
            found_element = parsed_element.find(f".//{target_tag}")
        parsed_element = found_element
    assert isinstance(parsed_element, clazz)


def _create_envelope_element(  # noqa: C901, PLR0911, PLR0912
    clazz: type[common.ElementBase],
) -> tuple[common.ElementBase, str | None]:
    if clazz is soap_envelope.Header:
        return _make_header(), None
    if clazz is soap_envelope.Body:
        return _make_body(), None
    if clazz is soap_envelope.Envelope:
        envelope = soap_envelope.Envelope()
        envelope.append(_make_header())
        envelope.append(_make_body())
        return envelope, None
    if clazz is soap_envelope.Value:
        return _make_fault(), soap_envelope.Value.TAG
    if clazz is soap_envelope.FaultReasonText:
        return _make_fault(), soap_envelope.FaultReasonText.TAG
    if clazz is soap_envelope.FaultReason:
        return _make_fault(), soap_envelope.FaultReason.TAG
    if clazz is soap_envelope.SubCode:
        return _make_fault(), soap_envelope.SubCode.TAG
    if clazz is soap_envelope.FaultCode:
        return _make_fault(), soap_envelope.FaultCode.TAG
    if clazz is soap_envelope.Detail:
        return _make_fault(), soap_envelope.Detail.TAG
    if clazz is soap_envelope.Node:
        return _make_fault(), soap_envelope.Node.TAG
    if clazz is soap_envelope.Role:
        return _make_fault(), soap_envelope.Role.TAG
    if clazz is soap_envelope.Fault:
        return _make_fault(), None
    if clazz is soap_envelope.NotUnderstood:
        return _make_not_understood(), None
    if clazz is soap_envelope.Upgrade:
        return _make_upgrade(), None
    if clazz is soap_envelope.SupportedEnvelope:
        return _make_upgrade(), soap_envelope.SupportedEnvelope.TAG
    return clazz(), None


def _make_not_understood() -> soap_envelope.NotUnderstood:
    return soap_envelope.NotUnderstood(
        attrib={"qname": f"{soap_envelope.PREFIX}:Envelope"},
        nsmap={soap_envelope.PREFIX: soap_envelope.NAMESPACE},
    )


def _make_upgrade() -> soap_envelope.Upgrade:
    return soap_envelope.Upgrade(
        soap_envelope.SupportedEnvelope(
            attrib={"qname": f"{soap_envelope.PREFIX}:Envelope"},
            nsmap={soap_envelope.PREFIX: soap_envelope.NAMESPACE},
        ),
    )


def _make_header() -> soap_envelope.Header:
    return soap_envelope.Header(
        addressing.Action("http://example.org/action"),
        _make_app_sequence(),
    )


def _make_body() -> soap_envelope.Body:
    return soap_envelope.Body(_make_fault())


def _make_fault_value(
    qname: str = f"{soap_envelope.PREFIX}:Receiver",
    nsmap: Mapping[str | None, str] | None = None,
) -> soap_envelope.Value:
    if nsmap is None:
        nsmap: Mapping[str, str] = {soap_envelope.PREFIX: soap_envelope.NAMESPACE}
    return soap_envelope.Value(qname, nsmap=nsmap)


def _make_fault_reason_text() -> soap_envelope.FaultReasonText:
    return soap_envelope.FaultReasonText(
        "Operation failed",
        attrib={f"{{{XML_LANG}}}lang": "en"},
    )


def _make_fault_reason() -> soap_envelope.FaultReason:
    return soap_envelope.FaultReason(_make_fault_reason_text())


def _make_subcode() -> soap_envelope.SubCode:
    return soap_envelope.SubCode(
        _make_fault_value(
            f"{addressing.PREFIX}:Action",
            {addressing.PREFIX: addressing.NAMESPACE},
        ),
    )


def _make_fault_code() -> soap_envelope.FaultCode:
    return soap_envelope.FaultCode(
        _make_fault_value(),
        _make_subcode(),
    )


def _make_detail() -> soap_envelope.Detail:
    element = soap_envelope.Detail()
    element.append(lxml.etree.Element("{urn:example}diagnostic"))
    return element


def _make_node() -> soap_envelope.Node:
    return soap_envelope.Node("http://example.org/node")


def _make_role() -> soap_envelope.Role:
    return soap_envelope.Role("http://example.org/role")


def _make_fault() -> soap_envelope.Fault:
    return soap_envelope.Fault(
        _make_fault_code(),
        _make_fault_reason(),
        _make_node(),
        _make_role(),
        _make_detail(),
    )


def test_body_as_returns_narrowed_body() -> None:
    """``body_as`` returns the soap:Body child when it matches the requested type."""
    envelope = soap_envelope.Envelope(_make_header(), _make_body())
    result = envelope.body_as(soap_envelope.Fault)
    assert isinstance(result, soap_envelope.Fault)


def test_body_as_raises_on_type_mismatch() -> None:
    """``body_as`` raises ``TypeError`` when the body is not the requested type."""
    envelope = soap_envelope.Envelope(_make_header(), _make_body())
    with pytest.raises(TypeError):
        envelope.body_as(soap_envelope.Upgrade)


def test_body_as_returns_none_on_missing_body() -> None:
    """``body_as`` returns ``None`` when there is no soap:Body child (R9981 permits zero)."""
    envelope = soap_envelope.Envelope(_make_header(), soap_envelope.Body())
    assert envelope.body_as(soap_envelope.Fault) is None


def _make_app_sequence() -> discovery.AppSequence:
    return discovery.AppSequence(
        attrib={
            "InstanceId": "1",
            "SequenceId": "urn:uuid:66666666-6666-6666-6666-666666666666",
            "MessageNumber": "1",
        },
    )
