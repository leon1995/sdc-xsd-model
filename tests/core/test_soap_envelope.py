"""Tests for the SOAP envelope model classes."""

from collections.abc import Callable, Mapping

import lxml.etree
import pytest

from sdc_xsd_model import element_class_lookup
from sdc_xsd_model.core import addressing, common, discovery, soap_envelope

XMLNS: str = "http://www.w3.org/2000/xmlns/"
XML_LANG: str = "http://www.w3.org/XML/1998/namespace"

ACTION: str = "http://example.org/action"
TO: str = "http://example.org/service"
REFERENCE_PARAMETER_TAG: str = "{urn:example:refparam}SubscriptionId"


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


def _make_app_sequence() -> discovery.AppSequence:
    return discovery.AppSequence(
        attrib={
            "InstanceId": "1",
            "SequenceId": "urn:uuid:66666666-6666-6666-6666-666666666666",
            "MessageNumber": "1",
        },
    )


def _make_reference_parameter() -> lxml.etree._Element:
    """Build an opaque header block marked as a reference parameter (ws-addr-soap 3.2)."""
    element = lxml.etree.Element(REFERENCE_PARAMETER_TAG)
    element.set(addressing.IS_REFERENCE_PARAMETER_ATTR_TAG, "true")
    element.text = "urn:uuid:22e8a584-0d18-4228-b2a8-3716fa2097fa"
    return element


def _make_header() -> soap_envelope.Header:
    return soap_envelope.Header.for_action(ACTION, _make_app_sequence(), to=TO)


def _make_body() -> soap_envelope.Body:
    return soap_envelope.Body(_make_fault())


def _make_envelope() -> soap_envelope.Envelope:
    return soap_envelope.Envelope.for_action(ACTION, _make_fault(), _make_app_sequence(), to=TO)


# Each case pairs a class with the element that must be serialized to reach it: the class itself where it is
# a valid document root, otherwise the container it lives in.
SOAP_ENVELOPE_CASES: list[tuple[type[common.ElementBase], str, Callable[[], common.ElementBase]]] = [
    (soap_envelope.Header, "Header", _make_header),
    (soap_envelope.Body, "Body", _make_body),
    (soap_envelope.Envelope, "Envelope", _make_envelope),
    (soap_envelope.Value, "Value", _make_fault),
    (soap_envelope.FaultReasonText, "Text", _make_fault),
    (soap_envelope.FaultReason, "Reason", _make_fault),
    (soap_envelope.SubCode, "Subcode", _make_fault),
    (soap_envelope.FaultCode, "Code", _make_fault),
    (soap_envelope.Detail, "Detail", _make_fault),
    (soap_envelope.Node, "Node", _make_fault),
    (soap_envelope.Role, "Role", _make_fault),
    (soap_envelope.Fault, "Fault", _make_fault),
    (soap_envelope.NotUnderstood, "NotUnderstood", _make_not_understood),
    (soap_envelope.Upgrade, "Upgrade", _make_upgrade),
    (soap_envelope.SupportedEnvelope, "SupportedEnvelope", _make_upgrade),
]


@pytest.mark.parametrize(("clazz", "local_name"), [(case[0], case[1]) for case in SOAP_ENVELOPE_CASES])
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


@pytest.mark.parametrize(
    ("clazz", "container_factory"),
    [(case[0], case[2]) for case in SOAP_ENVELOPE_CASES],
)
def test_class_lookup(
    clazz: type[common.ElementBase],
    container_factory: Callable[[], common.ElementBase],
) -> None:
    """Ensure SOAP envelope classes can be serialized and deserialized correctly."""
    xml = lxml.etree.tostring(container_factory())
    parsed_element = lxml.etree.fromstring(xml, parser=clazz.PARSER)
    # ``.//`` never matches the root, so only descend when the container is not the class under test.
    found = parsed_element if isinstance(parsed_element, clazz) else parsed_element.find(f".//{clazz.TAG}")
    assert isinstance(found, clazz)


def test_body_as_returns_narrowed_body() -> None:
    """``body_as`` returns the soap:Body child when it matches the requested type."""
    result = _make_envelope().body_as(soap_envelope.Fault)
    assert isinstance(result, soap_envelope.Fault)


def test_body_as_raises_on_type_mismatch() -> None:
    """``body_as`` raises ``TypeError`` when the body is not the requested type."""
    with pytest.raises(TypeError):
        _make_envelope().body_as(soap_envelope.Upgrade)


def test_header_factory_orders_blocks_like_a_real_message() -> None:
    """``Header.for_action`` emits the block order devices actually send, with extras last."""
    header = soap_envelope.Header.for_action(
        ACTION,
        _make_app_sequence(),
        to=TO,
        relates_to="urn:uuid:3d5c8f92-1a4b-4e6d-9c8f-2b7a5e0d3f14",
    )
    assert [child.tag for child in header] == [
        addressing.To.TAG,
        addressing.Action.TAG,
        addressing.MessageID.TAG,
        addressing.RelatesTo.TAG,
        discovery.AppSequence.TAG,
    ]
    assert header.to is not None
    assert header.to.text == TO
    assert header.action.text == ACTION


def test_header_factory_generates_a_random_message_id() -> None:
    """``Header.for_action`` mints a fresh MessageID when none is given."""
    first = soap_envelope.Header.for_action(ACTION).message_id
    second = soap_envelope.Header.for_action(ACTION).message_id
    assert first is not None
    assert second is not None
    assert first.text is not None
    assert first.text.startswith("urn:uuid:")
    assert first.text != second.text


def test_header_factory_omits_optional_blocks() -> None:
    """``Header.for_action`` leaves out the blocks it was not given, rather than emitting empty ones."""
    header = soap_envelope.Header.for_action(ACTION)
    assert [child.tag for child in header] == [addressing.Action.TAG, addressing.MessageID.TAG]
    assert header.to is None
    assert header.relates_to is None
    assert header.reply_to is None
    assert header.fault_to is None
    assert header.from_ is None


def test_envelope_factory_wraps_the_payload() -> None:
    """``Envelope.for_action`` puts the payload inside soap:Body, where ``body`` reads it back."""
    payload = _make_fault()
    envelope = soap_envelope.Envelope.for_action(ACTION, payload, to=TO)
    assert envelope.body is payload
    assert envelope.header.action.text == ACTION


def test_header_action_raises_when_absent() -> None:
    """``Header.action`` raises because ws-addr-core 3.2 makes wsa:Action REQUIRED."""
    with pytest.raises(ValueError, match="wsa:Action"):
        _ = soap_envelope.Header().action


def test_envelope_header_raises_when_absent() -> None:
    """``Envelope.header`` raises on a headerless envelope, which the schema still accepts.

    ``soap-envelope.xsd`` declares soap:Header ``minOccurs="0"``, so this document validates -- the
    requirement is dpws:R5005's, not the schema's, which is why it raises instead of asserting.
    """
    raw = f'<s12:Envelope xmlns:s12="{soap_envelope.NAMESPACE}"><s12:Body/></s12:Envelope>'.encode()
    envelope = lxml.etree.fromstring(raw, parser=soap_envelope.Envelope.PARSER)
    assert isinstance(envelope, soap_envelope.Envelope)
    with pytest.raises(ValueError, match="soap:Header"):
        _ = envelope.header


def test_headers_are_typed_through_the_local_parser() -> None:
    """The module parser must resolve wsa:* headers, not hand back untyped elements.

    ``find_by_element`` is an unchecked cast, so a lookup that only knows the SOAP namespace makes
    ``Header.action`` claim to return an ``addressing.Action`` while yielding a plain element.
    """
    xml = lxml.etree.tostring(_make_envelope())
    envelope = lxml.etree.fromstring(xml, parser=soap_envelope.Envelope.PARSER)
    assert isinstance(envelope, soap_envelope.Envelope)
    header = envelope.header
    assert isinstance(header.action, addressing.Action)
    assert isinstance(header.to, addressing.To)
    assert isinstance(header.message_id, addressing.MessageID)


def _make_biceps_parser() -> lxml.etree.XMLParser:
    """Non-validating parser using the ``xsi:type``-aware BICEPS class lookup."""
    ns_lookup = lxml.etree.ElementNamespaceClassLookup()
    addressing.set_lookup(ns_lookup)
    discovery.set_lookup(ns_lookup)
    soap_envelope.set_lookup(ns_lookup)
    parser = lxml.etree.XMLParser()
    parser.set_element_class_lookup(element_class_lookup.BicepsElementClassLookup(ns_lookup))
    return parser


def test_comment_in_body_does_not_break_class_lookup() -> None:
    """``BicepsElementClassLookup`` must delegate comments and PIs instead of raising.

    Comment and processing-instruction nodes are passed to ``PythonElementClassLookup.lookup`` too,
    but their read-only proxy exposes neither ``get`` nor a string ``tag``.
    """
    raw = (
        f'<s12:Envelope xmlns:s12="{soap_envelope.NAMESPACE}">'
        f"<s12:Header/>"
        f"<s12:Body><!-- a comment --><?pi data?>"
        f'<s12:Upgrade><s12:SupportedEnvelope qname="s12:Envelope"/></s12:Upgrade>'
        f"</s12:Body></s12:Envelope>"
    ).encode()
    envelope = lxml.etree.fromstring(raw, parser=_make_biceps_parser())
    assert isinstance(envelope, soap_envelope.Envelope)
    assert isinstance(envelope.body_as(soap_envelope.Upgrade), soap_envelope.Upgrade)
