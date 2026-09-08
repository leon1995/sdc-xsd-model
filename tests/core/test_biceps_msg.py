"""Tests for the BICEPS MessageModel model classes."""

import decimal

import lxml.etree
import pytest

from sdc_xsd_model import element_class_lookup
from sdc_xsd_model.core import biceps_msg, biceps_pm, common, extension


def _get_lookup_parser() -> lxml.etree.XMLParser:
    """Non-validating parser with class lookup for roundtrip tests."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    extension.set_lookup(lookup)
    biceps_pm.set_lookup(lookup)
    biceps_msg.set_lookup(lookup)
    parser = lxml.etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    return parser


_LOOKUP_PARSER = _get_lookup_parser()


def _get_xsi_parser() -> lxml.etree.XMLParser:
    """Non-validating parser that also dispatches on ``xsi:type`` and parent context."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    extension.set_lookup(lookup)
    biceps_pm.set_lookup(lookup)
    biceps_msg.set_lookup(lookup)
    parser = lxml.etree.XMLParser()
    parser.set_element_class_lookup(element_class_lookup.BicepsElementClassLookup(lookup))
    return parser


_XSI_PARSER = _get_xsi_parser()

# (class, local element name) for classes with TAG set
BICEPS_MSG_CASES = [
    (biceps_msg.GetMdib, "GetMdib"),
    (biceps_msg.GetMdibResponse, "GetMdibResponse"),
    (biceps_msg.GetMdDescription, "GetMdDescription"),
    (biceps_msg.GetMdDescriptionResponse, "GetMdDescriptionResponse"),
    (biceps_msg.GetMdState, "GetMdState"),
    (biceps_msg.GetMdStateResponse, "GetMdStateResponse"),
    (biceps_msg.GetContextStates, "GetContextStates"),
    (biceps_msg.GetContextStatesResponse, "GetContextStatesResponse"),
    (biceps_msg.GetContextStatesByIdentification, "GetContextStatesByIdentification"),
    (biceps_msg.GetContextStatesByIdentificationResponse, "GetContextStatesByIdentificationResponse"),
    (biceps_msg.GetContextStatesByFilter, "GetContextStatesByFilter"),
    (biceps_msg.GetContextStatesByFilterResponse, "GetContextStatesByFilterResponse"),
    (biceps_msg.SetContextState, "SetContextState"),
    (biceps_msg.SetContextStateResponse, "SetContextStateResponse"),
    (biceps_msg.PeriodicContextReport, "PeriodicContextReport"),
    (biceps_msg.EpisodicContextReport, "EpisodicContextReport"),
    (biceps_msg.GetLocalizedText, "GetLocalizedText"),
    (biceps_msg.GetLocalizedTextResponse, "GetLocalizedTextResponse"),
    (biceps_msg.GetSupportedLanguages, "GetSupportedLanguages"),
    (biceps_msg.GetSupportedLanguagesResponse, "GetSupportedLanguagesResponse"),
    (biceps_msg.GetDescriptorsFromArchive, "GetDescriptorsFromArchive"),
    (biceps_msg.GetDescriptorsFromArchiveResponse, "GetDescriptorsFromArchiveResponse"),
    (biceps_msg.GetStatesFromArchive, "GetStatesFromArchive"),
    (biceps_msg.GetStatesFromArchiveResponse, "GetStatesFromArchiveResponse"),
    (biceps_msg.SetValue, "SetValue"),
    (biceps_msg.SetValueResponse, "SetValueResponse"),
    (biceps_msg.SetString, "SetString"),
    (biceps_msg.SetStringResponse, "SetStringResponse"),
    (biceps_msg.Activate, "Activate"),
    (biceps_msg.ActivateResponse, "ActivateResponse"),
    (biceps_msg.SetAlertState, "SetAlertState"),
    (biceps_msg.SetAlertStateResponse, "SetAlertStateResponse"),
    (biceps_msg.SetComponentState, "SetComponentState"),
    (biceps_msg.SetComponentStateResponse, "SetComponentStateResponse"),
    (biceps_msg.SetMetricState, "SetMetricState"),
    (biceps_msg.SetMetricStateResponse, "SetMetricStateResponse"),
    (biceps_msg.OperationInvokedReport, "OperationInvokedReport"),
    (biceps_msg.GetContainmentTree, "GetContainmentTree"),
    (biceps_msg.GetContainmentTreeResponse, "GetContainmentTreeResponse"),
    (biceps_msg.GetDescriptor, "GetDescriptor"),
    (biceps_msg.GetDescriptorResponse, "GetDescriptorResponse"),
    (biceps_msg.EpisodicMetricReport, "EpisodicMetricReport"),
    (biceps_msg.PeriodicMetricReport, "PeriodicMetricReport"),
    (biceps_msg.EpisodicComponentReport, "EpisodicComponentReport"),
    (biceps_msg.PeriodicComponentReport, "PeriodicComponentReport"),
    (biceps_msg.EpisodicAlertReport, "EpisodicAlertReport"),
    (biceps_msg.PeriodicAlertReport, "PeriodicAlertReport"),
    (biceps_msg.EpisodicOperationalStateReport, "EpisodicOperationalStateReport"),
    (biceps_msg.PeriodicOperationalStateReport, "PeriodicOperationalStateReport"),
    (biceps_msg.SystemErrorReport, "SystemErrorReport"),
    (biceps_msg.DescriptionModificationReport, "DescriptionModificationReport"),
    (biceps_msg.WaveformStream, "WaveformStream"),
    (biceps_msg.ObservedValueStream, "ObservedValueStream"),
    (biceps_msg.Retrievability, "Retrievability"),
    (biceps_msg.ReportPart, "ReportPart"),
    (biceps_msg.InvocationInfo, "InvocationInfo"),
]


@pytest.mark.parametrize(("clazz", "local_name"), BICEPS_MSG_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure BICEPS MSG classes expose the expected TAG value."""
    assert f"{{{biceps_msg.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in BICEPS_MSG_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure BICEPS MSG classes register the expected namespace."""
    assert clazz().nsmap[biceps_msg.PREFIX] == biceps_msg.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in BICEPS_MSG_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure BICEPS MSG classes can be serialized and deserialized via namespace lookup."""
    element = clazz()
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    assert isinstance(parsed_element, clazz)


# ── locally declared children ──────────────────────────────────────────────────────────────────────
# The message schema declares several children inside a message rather than globally, which puts their name
# in the message namespace while their type stays a participant model one. Reading them as {pm}Name finds
# nothing, and leaving them unregistered yields a plain _Element.


def test_get_md_description_response_reads_the_message_namespace_child() -> None:
    """The child is {msg}MdDescription on the wire, not {pm}MdDescription."""
    xml = (
        f'<GetMdDescriptionResponse xmlns="{biceps_msg.NAMESPACE}" SequenceId="urn:uuid:1">'
        f"<MdDescription/></GetMdDescriptionResponse>"
    ).encode()
    response = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    assert isinstance(response.md_description, biceps_pm.MdDescription)


def test_get_md_state_response_reads_the_message_namespace_child() -> None:
    """The child is {msg}MdState on the wire, not {pm}MdState."""
    xml = (
        f'<GetMdStateResponse xmlns="{biceps_msg.NAMESPACE}" SequenceId="urn:uuid:1"><MdState/></GetMdStateResponse>'
    ).encode()
    response = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    assert isinstance(response.md_state, biceps_pm.MdState)


def test_get_context_states_by_identification_identification_is_typed() -> None:
    """{msg}Identification is declared pm:InstanceIdentifier."""
    xml = (
        f'<GetContextStatesByIdentification xmlns="{biceps_msg.NAMESPACE}">'
        f'<Identification Root="urn:oid:1.2.3" Extension="P-42"/></GetContextStatesByIdentification>'
    ).encode()
    request = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    identifications = request.findall(f"{{{biceps_msg.NAMESPACE}}}Identification")
    assert all(isinstance(node, biceps_pm.InstanceIdentifier) for node in identifications)
    assert identifications[0].extension_attr == "P-42"


def test_invocation_error_message_is_a_localized_text() -> None:
    """The schema declares it pm:LocalizedText, so it carries @Lang and the rest, not just text."""
    xml = (
        f'<InvocationInfo xmlns="{biceps_msg.NAMESPACE}"><TransactionId>1</TransactionId>'
        f"<InvocationState>Fail</InvocationState>"
        f'<InvocationErrorMessage Lang="en">it failed</InvocationErrorMessage></InvocationInfo>'
    ).encode()
    info = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    message = info.invocation_error_messages[0]
    assert isinstance(message, biceps_pm.LocalizedText)
    assert message.lang == "en"
    assert message.text == "it failed"


# ── waveform stream states ─────────────────────────────────────────────────────────────────────────
# msg:WaveformStream/msg:State is the one state-carrying element the schema declares with a concrete type,
# so no xsi:type is sent and only the parent tells the lookup what it is.

_WAVEFORM_STREAM = (
    f'<WaveformStream xmlns="{biceps_msg.NAMESPACE}" xmlns:dom="{biceps_pm.NAMESPACE}" SequenceId="urn:uuid:1">'
    f'<State DescriptorHandle="wf0">'
    f'<dom:MetricValue Samples="1 2 3"><dom:MetricQuality Validity="Vld"/></dom:MetricValue>'
    f"</State></WaveformStream>"
).encode()


def test_waveform_stream_state_carries_no_xsi_type() -> None:
    """Pins why the parent-context entry is needed at all."""
    stream = lxml.etree.fromstring(_WAVEFORM_STREAM, parser=_XSI_PARSER)
    assert stream.states[0].get("{http://www.w3.org/2001/XMLSchema-instance}type") is None


def test_waveform_stream_state_is_a_real_time_sample_array_state() -> None:
    """Resolved from the parent-context table, since the wire carries no xsi:type."""
    stream = lxml.etree.fromstring(_WAVEFORM_STREAM, parser=_XSI_PARSER)
    assert isinstance(stream.states[0], biceps_pm.RealTimeSampleArrayMetricState)


def test_waveform_stream_metric_value_is_a_sample_array() -> None:
    """Resolving this needs the state's own type, which itself came from the parent-context table."""
    stream = lxml.etree.fromstring(_WAVEFORM_STREAM, parser=_XSI_PARSER)
    metric_value = stream.states[0].metric_value
    assert isinstance(metric_value, biceps_pm.SampleArrayValue)
    assert list(metric_value.samples) == [decimal.Decimal(1), decimal.Decimal(2), decimal.Decimal(3)]
