"""Parse real WS-Discovery messages through the composite SDC parser.

The per-module tests build elements in Python and check that they survive a round trip. These tests come at
the generated modules from the other side: XML that a device would actually put on the wire, validated
against the schema set and read back through the generated properties. That covers what unit tests cannot —
element order, cross-namespace children, whitespace-separated list content and typed attributes all at once.
"""

from __future__ import annotations

import datetime
import decimal
import pathlib
import typing

import lxml.etree
import pytest

from sdc_xsd_model import parser
from sdc_xsd_model.core import (
    addressing,
    biceps_msg,
    biceps_pm,
    discovery,
    dpws,
    eventing,
    mdpws,
    metadata_exchange,
    soap_envelope,
)
from sdc_xsd_model.extension_registry import ExtensionRegistry

DATA_DIR: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent.parent / "data"


@pytest.fixture(scope="module")
def soap_parser() -> parser.SoapEnvelopeParser:
    """Build the composite parser once; it compiles the whole schema set."""
    return parser.SoapEnvelopeParser(ExtensionRegistry())


def _parse(soap_parser: parser.SoapEnvelopeParser, name: str) -> soap_envelope.Envelope:
    return soap_parser.from_string(DATA_DIR.joinpath(name).read_bytes())


@pytest.mark.parametrize(
    ("file_name", "body_class"),
    [
        ("ws_discovery_hello.xml", discovery.Hello),
        ("ws_discovery_bye.xml", discovery.Bye),
        ("ws_discovery_probe_matches.xml", discovery.ProbeMatches),
        # WS-Eventing: the subscription lifecycle an SDC consumer drives.
        ("ws_eventing_subscribe.xml", eventing.Subscribe),
        ("ws_eventing_subscribe_response.xml", eventing.SubscribeResponse),
        ("ws_eventing_renew.xml", eventing.Renew),
        ("ws_eventing_get_status_response.xml", eventing.GetStatusResponse),
        ("ws_eventing_unsubscribe.xml", eventing.Unsubscribe),
        ("ws_eventing_subscription_end.xml", eventing.SubscriptionEnd),
        # Device metadata retrieval.
        ("dpws_get_metadata_response.xml", metadata_exchange.Metadata),
        # BICEPS services.
        ("biceps_get_mdib_response.xml", biceps_msg.GetMdibResponse),
        ("mdpws_safety_info_set_value.xml", biceps_msg.SetValue),
        ("biceps_operation_invoked_report.xml", biceps_msg.OperationInvokedReport),
        ("biceps_waveform_stream.xml", biceps_msg.WaveformStream),
    ],
)
def test_body_is_typed(
    soap_parser: parser.SoapEnvelopeParser,
    file_name: str,
    body_class: type,
) -> None:
    """Ensure the message body is deserialized into the expected generated class."""
    envelope = _parse(soap_parser, file_name)
    assert isinstance(envelope.body, body_class)


def test_hello_reads_every_child(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure the generated child properties of Hello work, including the cross-namespace one."""
    hello = _parse(soap_parser, "ws_discovery_hello.xml").body_as(discovery.Hello)
    assert hello is not None

    endpoint_reference = hello.endpoint_reference
    assert isinstance(endpoint_reference, addressing.EndpointReference)
    assert endpoint_reference.address.text == "urn:uuid:98190dc2-0890-4ef8-ac9a-5940995e6119"

    assert hello.metadata_version.version == 2
    assert hello.scopes is not None
    assert hello.scopes.uris == ["http://example.com/ward/icu", "http://example.com/bed/3"]
    assert hello.x_addrs is not None
    assert hello.x_addrs.uris == ["http://192.168.0.11/device", "http://[2001:db8::11]/device"]


def test_hello_types_resolves_prefixed_qnames(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure wsd:Types is read as QNames, resolving the prefix against the document's namespace map."""
    hello = _parse(soap_parser, "ws_discovery_hello.xml").body_as(discovery.Hello)
    assert hello is not None
    assert hello.types is not None
    assert [str(q_name) for q_name in hello.types.q_names] == [
        "{http://docs.oasis-open.org/ws-dd/ns/dpws/2009/01}Device",
    ]


def test_hello_types_resolves_unprefixed_qnames_against_the_default_namespace(
    soap_parser: parser.SoapEnvelopeParser,
) -> None:
    """Ensure a bare QName in wsd:Types resolves against the default namespace declaration.

    XSD resolves an unprefixed QName through ``xmlns=``, so this message names the same type as the
    prefixed one above. Ignoring the default declaration produced a namespace-free QName instead, which
    silently failed to match dpws:Device -- a device would simply not be discovered.
    """
    hello = _parse(soap_parser, "ws_discovery_hello_default_namespace_type.xml").body_as(discovery.Hello)
    assert hello is not None
    assert hello.types is not None
    assert [str(q_name) for q_name in hello.types.q_names] == [
        "{http://docs.oasis-open.org/ws-dd/ns/dpws/2009/01}Device",
    ]


def test_bye_omits_optional_children(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure optional children are None rather than raising when a message leaves them out."""
    bye = _parse(soap_parser, "ws_discovery_bye.xml").body_as(discovery.Bye)
    assert bye is not None
    assert bye.endpoint_reference.address.text == "urn:uuid:98190dc2-0890-4ef8-ac9a-5940995e6119"
    assert bye.types is None
    assert bye.scopes is None
    assert bye.x_addrs is None
    assert bye.metadata_version is None


def test_probe_matches_reads_repeated_children(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure a repeated child yields every entry, each with its own typed children."""
    probe_matches = _parse(soap_parser, "ws_discovery_probe_matches.xml").body_as(discovery.ProbeMatches)
    assert probe_matches is not None
    matches = probe_matches.probe_match
    assert len(matches) == 2
    assert [match.metadata_version.version for match in matches] == [2, 7]
    assert matches[0].scopes is not None
    assert matches[1].scopes is None
    assert matches[1].x_addrs is not None
    assert matches[1].x_addrs.uris == ["http://192.168.0.12/device"]


def test_headers_are_typed(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure the WS-Addressing and WS-Discovery headers deserialize, including typed attributes."""
    envelope = _parse(soap_parser, "ws_discovery_probe_matches.xml")
    header = envelope.header
    assert header.action.text == "http://docs.oasis-open.org/ws-dd/ns/discovery/2009/01/ProbeMatches"
    assert header.relates_to is not None
    assert header.to is not None
    assert header.to.text == addressing.ANONYMOUS_URI

    app_sequence = header.app_sequence
    assert app_sequence is not None
    assert app_sequence.instance_id == 1077004800
    assert app_sequence.message_number == 12
    assert app_sequence.sequence_id is None


def test_headers_absent_from_a_message_are_none(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure the optional WS-Addressing blocks read as None rather than raising when a message omits them."""
    header = _parse(soap_parser, "ws_discovery_probe_matches.xml").header
    assert header.reply_to is None
    assert header.fault_to is None
    assert header.from_ is None


def test_app_sequence_sequence_id_is_read_when_present(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure an optional attribute is read when the message carries it."""
    header = _parse(soap_parser, "ws_discovery_hello.xml").header
    app_sequence = header.app_sequence
    assert app_sequence is not None
    assert app_sequence.sequence_id == "urn:uuid:369a7d7b-5f87-48a4-aa9a-189edf2a8772"


def test_fault_reply_headers_are_typed(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure the endpoint-reference headers deserialize, which no WS-Discovery message exercises."""
    header = _parse(soap_parser, "soap_fault.xml").header
    assert header.action.text == addressing.SOAP_FAULT_ACTION

    # dpws:R0040 requires a relationship of type reply on every fault.
    relates_to = header.relates_to
    assert relates_to is not None
    assert relates_to.relationship_type == addressing.RelationshipType.REPLY

    from_ = header.from_
    assert isinstance(from_, addressing.From)
    assert from_.address.text == "http://192.168.0.11/device/GetService"

    reply_to = header.reply_to
    assert isinstance(reply_to, addressing.ReplyTo)
    assert reply_to.address.text == "http://192.168.0.42/client/replies"

    fault_to = header.fault_to
    assert isinstance(fault_to, addressing.FaultTo)
    assert fault_to.address.text == "http://192.168.0.42/client/faults"


def test_fault_body_is_typed(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure a soap:Fault body deserializes, including the nested subcode QName."""
    fault = _parse(soap_parser, "soap_fault.xml").body_as(soap_envelope.Fault)
    assert fault is not None
    assert fault.code.value.q_name == soap_envelope.FaultCodeEnum.SENDER
    subcode = fault.code.subcode
    assert subcode is not None
    assert subcode.value.q_name == addressing.FaultCodesType.ACTION_NOT_SUPPORTED
    assert [text.lang for text in fault.reason.texts] == ["en"]
    assert fault.detail is None


def test_containment_tree_response_is_typed(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure msg:ContainmentTree deserializes, together with its pm:Entry children.

    The element is typed pm:ContainmentTree but declared in the *message* namespace, while its Entry children
    come from the participant schema. A TAG naming the wrong namespace made ``containment_tree`` return None on
    a perfectly valid message, which no test noticed because the property is Optional.
    """
    response = _parse(soap_parser, "biceps_get_containment_tree_response.xml").body_as(
        biceps_msg.GetContainmentTreeResponse,
    )
    assert response is not None
    tree = response.containment_tree
    assert isinstance(tree, biceps_msg.ContainmentTree)
    assert tree.handle_ref == "mds0"
    assert tree.entry_type == lxml.etree.QName(biceps_pm.NAMESPACE, "MdsDescriptor")

    entries = tree.entries
    assert [type(entry).__name__ for entry in entries] == ["ContainmentTreeEntry"] * 2
    assert [entry.handle_ref for entry in entries] == ["vmd0", "vmd1"]
    assert tree.children_count == len(entries)
    assert entries[0].entry_type == lxml.etree.QName(biceps_pm.NAMESPACE, "VmdDescriptor")
    assert entries[1].entry_type is None


def test_metric_quality_is_typed(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure every metric value exposes its mandatory pm:MetricQuality, including the implied mode."""
    report = _parse(soap_parser, "biceps_episodic_metric_report.xml").body_as(biceps_msg.EpisodicMetricReport)
    assert report is not None
    states = [state for part in report.report_parts for state in part.metric_states]
    assert [state.descriptor_handle for state in states] == ["numeric0", "numeric1", "string0"]

    values = [state.metric_value for state in states]
    assert isinstance(values[0], biceps_pm.NumericMetricValue)
    assert isinstance(values[2], biceps_pm.StringMetricValue)

    qualities = [value.metric_quality for value in values if value is not None]
    assert [quality.validity for quality in qualities] == [
        biceps_pm.MeasurementValidity.VLD,
        biceps_pm.MeasurementValidity.QST,
        biceps_pm.MeasurementValidity.INV,
    ]
    # numeric0 omits @Mode, so it is a real measurement by implication; numeric1 says so explicitly.
    assert qualities[0].mode is None
    assert qualities[0].mode_or_implied == biceps_pm.GenerationMode.REAL
    assert qualities[1].mode == biceps_pm.GenerationMode.DEMO
    # Qi="0" is the worst quality and must not read back as the implied 1.
    assert qualities[1].qi == 0
    assert qualities[1].qi_or_implied == 0

    annotations = values[2].annotations if values[2] is not None else []
    assert len(annotations) == 1
    annotation_type = annotations[0].type
    assert annotation_type is not None
    assert annotation_type.code == "196616"


def test_observed_value_stream_binds_samples_to_a_metric(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Ensure the stream wrapper and the samples it holds are told apart despite sharing a tag."""
    stream = _parse(soap_parser, "biceps_observed_value_stream.xml").body_as(biceps_msg.ObservedValueStream)
    assert stream is not None
    observed = stream.values
    assert [type(entry).__name__ for entry in observed] == ["ObservedValue"] * 2
    assert [entry.metric for entry in observed] == ["waveform0", "waveform1"]
    assert [entry.state_version for entry in observed] == [9, None]
    assert [entry.state_version_or_implied for entry in observed] == [9, 0]

    samples = observed[0].value
    assert isinstance(samples, biceps_pm.SampleArrayValue)
    assert samples.samples == [
        decimal.Decimal("0.10"),
        decimal.Decimal("0.25"),
        decimal.Decimal("0.40"),
        decimal.Decimal("0.25"),
    ]
    assert samples.metric_quality.validity == biceps_pm.MeasurementValidity.VLD
    # ApplyAnnotation was unregistered, so reading sample_index off it used to raise AttributeError.
    assert [(a.annotation_index, a.sample_index) for a in samples.apply_annotations] == [(0, 2)]


# ── WS-Eventing lifecycle ──────────────────────────────────────────────────────────────────────────


def test_subscribe_reads_delivery_and_filter(soap_parser: parser.SoapEnvelopeParser) -> None:
    """The parts SDC constrains beyond the WS-Eventing schema: delivery mode, filter dialect, expiry."""
    subscribe = _parse(soap_parser, "ws_eventing_subscribe.xml").body_as(eventing.Subscribe)
    assert subscribe is not None

    delivery = subscribe.delivery
    assert isinstance(delivery, eventing.DeliveryType)
    assert delivery.mode == "http://schemas.xmlsoap.org/ws/2004/08/eventing/DeliveryModes/Push"
    notify_to = delivery.find_by_element(eventing.NotifyTo)
    assert isinstance(notify_to, eventing.NotifyTo)
    assert notify_to.address.text == "https://192.168.0.42:6464/client/reports"

    end_to = subscribe.end_to
    assert isinstance(end_to, eventing.EndTo)
    assert end_to.address.text == "https://192.168.0.42:6464/client/subscription-end"

    # SDPi R1018 restricts wse:Expires to a duration, so this parses as a timedelta rather than a datetime.
    assert subscribe.expires is not None
    assert subscribe.expires.expiration == datetime.timedelta(hours=1)


def test_subscribe_filter_uses_the_handle_dialect(soap_parser: parser.SoapEnvelopeParser) -> None:
    """glue:R0038 defines the Handle-based Filter Dialect as a whitespace-delimited list of pm:HandleRef."""
    subscribe = _parse(soap_parser, "ws_eventing_subscribe.xml").body_as(eventing.Subscribe)
    assert subscribe is not None
    message_filter = subscribe.filter
    assert isinstance(message_filter, eventing.FilterType)


def test_subscribe_response_carries_the_subscription_identifier(
    soap_parser: parser.SoapEnvelopeParser,
) -> None:
    """Both children are schema-required; the identifier travels as a reference parameter of the manager EPR."""
    response = _parse(soap_parser, "ws_eventing_subscribe_response.xml").body_as(eventing.SubscribeResponse)
    assert response is not None

    manager = response.subscription_manager
    assert isinstance(manager, eventing.SubscriptionManager)
    assert manager.address.text == "https://192.168.0.11:6464/StateEventService"
    reference_parameters = manager.reference_parameters
    assert len(reference_parameters) == 1
    identifier = reference_parameters[0].find_by_element(eventing.Identifier)
    assert isinstance(identifier, eventing.Identifier)
    assert identifier.text == "urn:uuid:1a2b3c4d-5555-4000-8000-00000000dead"

    # The provider granted less than the consumer asked for, which it is free to do.
    assert response.expires.expiration == datetime.timedelta(minutes=30)


def test_renew_and_get_status_expiry(soap_parser: parser.SoapEnvelopeParser) -> None:
    """wse:Expires is optional on GetStatusResponse but required on SubscribeResponse."""
    renew = _parse(soap_parser, "ws_eventing_renew.xml").body_as(eventing.Renew)
    assert renew is not None
    assert renew.expires is not None
    assert renew.expires.expiration == datetime.timedelta(hours=1)

    status = _parse(soap_parser, "ws_eventing_get_status_response.xml").body_as(eventing.GetStatusResponse)
    assert status is not None
    assert status.expires is not None
    assert status.expires.expiration == datetime.timedelta(minutes=22, seconds=30)


def test_unsubscribe_body_is_empty_but_typed(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Everything identifying the subscription is in the header, so the body element has no children."""
    envelope = _parse(soap_parser, "ws_eventing_unsubscribe.xml")
    unsubscribe = envelope.body_as(eventing.Unsubscribe)
    assert unsubscribe is not None
    assert len(unsubscribe) == 0

    # wse:Identifier is not part of the closed SDC header set, so it is reached with find_by_element.
    identifier = envelope.header.find_by_element(eventing.Identifier)
    assert isinstance(identifier, eventing.Identifier)
    assert identifier.text == "urn:uuid:1a2b3c4d-5555-4000-8000-00000000dead"


def test_subscription_end_status_is_an_open_union(soap_parser: parser.SoapEnvelopeParser) -> None:
    """wse:Status is a union of the three enumerated codes and xs:anyURI, so it resolves to the enum here."""
    end = _parse(soap_parser, "ws_eventing_subscription_end.xml").body_as(eventing.SubscriptionEnd)
    assert end is not None
    assert end.subscription_manager.address.text == "https://192.168.0.11:6464/StateEventService"

    status = end.find_by_element(eventing.Status)
    assert isinstance(status, eventing.Status)
    assert status.code_type() == eventing.SubscriptionEndCodeType.DELIVERY_FAILURE

    reason = end.find_by_element(eventing.Reason)
    assert isinstance(reason, eventing.Reason)
    assert reason.lang == "en"


# ── DPWS / WS-MetadataExchange ─────────────────────────────────────────────────────────────────────


def test_metadata_sections_dispatch_by_dialect(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Each mex:MetadataSection holds a payload from a different namespace, selected by @Dialect."""
    metadata = _parse(soap_parser, "dpws_get_metadata_response.xml").body_as(metadata_exchange.Metadata)
    assert metadata is not None
    sections = metadata.metadata_sections
    assert [section.dialect for section in sections] == [
        dpws.DeviceMetadataDialectURIs.THIS_MODEL,
        dpws.DeviceMetadataDialectURIs.THIS_DEVICE,
        dpws.DeviceMetadataDialectURIs.RELATIONSHIP,
    ]
    assert [type(section[0]).__name__ for section in sections] == ["ThisModel", "ThisDevice", "Relationship"]


def test_this_model_and_this_device_repeat_per_language(soap_parser: parser.SoapEnvelopeParser) -> None:
    """DPWS repeats localized strings once per language, so a consumer has to read xml:lang to choose."""
    sections = (
        _parse(soap_parser, "dpws_get_metadata_response.xml")
        .body_as(
            metadata_exchange.Metadata,
        )
        .metadata_sections
    )

    this_model = sections[0][0]
    assert isinstance(this_model, dpws.ThisModel)
    assert [(name.text, name.lang) for name in this_model.manufacturers] == [
        ("Example Medical Systems", "en"),
        ("Beispiel Medizintechnik", "de"),
    ]
    assert [name.lang for name in this_model.model_names] == ["en", "de"]
    assert this_model.model_number is not None
    assert this_model.model_number.text == "PM-3000"
    assert this_model.presentation_url is not None

    this_device = sections[1][0]
    assert isinstance(this_device, dpws.ThisDevice)
    assert [name.lang for name in this_device.friendly_names] == ["en", "de"]
    assert this_device.serial_number is not None
    assert this_device.serial_number.text == "SN-0000-4711"


def test_relationship_lists_the_hosted_sdc_services(soap_parser: parser.SoapEnvelopeParser) -> None:
    """dpws:Hosted/dpws:Types is a QName list whose prefixes resolve against the document namespace map."""
    sections = (
        _parse(soap_parser, "dpws_get_metadata_response.xml")
        .body_as(
            metadata_exchange.Metadata,
        )
        .metadata_sections
    )
    relationship = sections[2][0]
    assert isinstance(relationship, dpws.Relationship)
    assert relationship.type == dpws.DeviceRelationshipTypeURIs.HOST

    host = relationship.host
    assert isinstance(host, dpws.Host)
    assert host.types is not None
    assert [str(q_name) for q_name in host.types.q_names] == [
        str(dpws.DiscoveryTypeValues.DEVICE),
        "{http://standards.ieee.org/downloads/11073/11073-20701-2018}ServiceProvider",
    ]

    hosted = relationship.hosted
    assert [[q_name.localname for q_name in service.types.q_names] for service in hosted] == [
        ["GetService", "ContainmentTreeService"],
        ["StateEventService", "WaveformService"],
    ]
    assert [service.endpoint_references[0].address.text for service in hosted] == [
        "https://192.168.0.11:6464/GetService",
        "https://192.168.0.11:6464/StateEventService",
    ]


# ── MDPWS safety information ───────────────────────────────────────────────────────────────────────


def test_safety_info_is_typed_in_the_header(soap_parser: parser.SoapEnvelopeParser) -> None:
    """MDPWS 9.4.2 carries safety information in the header, cross-namespace from soap:Header itself."""
    envelope = _parse(soap_parser, "mdpws_safety_info_set_value.xml")
    safety_info = envelope.header.safety_info
    assert isinstance(safety_info, mdpws.SafetyInfo)

    dual_channel = safety_info.dual_channel
    assert isinstance(dual_channel, mdpws.DualChannel)
    assert [(value.referenced_selector, value.text) for value in dual_channel.dc_values] == [
        ("SELECTOR_1", "m6JlmEUEQKZVs9UYQZWDvXlSJ2M="),
        ("SELECTOR_2", "2jmj7l5rSw0yVb-vlWAYkK-YBwk="),
    ]

    safety_context = safety_info.safety_context
    assert isinstance(safety_context, mdpws.SafetyContext)
    assert [value.referenced_selector for value in safety_context.ctxt_values] == [
        "SELECTOR_3",
        "SELECTOR_4",
    ]


def test_set_value_body_alongside_safety_info(soap_parser: parser.SoapEnvelopeParser) -> None:
    """The SET SERVICE request itself: an operation handle and the requested value."""
    set_value = _parse(soap_parser, "mdpws_safety_info_set_value.xml").body_as(biceps_msg.SetValue)
    assert set_value is not None
    assert set_value.operation_handle_ref == "sco.vmd0.set_rate"
    assert set_value.requested_numeric_value == decimal.Decimal("12.5")


# ── BICEPS GET SERVICE: the containment tree ───────────────────────────────────────────────────────

# Version counters fixed by biceps_get_mdib_response.xml. Named so the assertions read as "the value the
# fixture states" rather than as bare magic numbers.
_MDIB_VERSION: typing.Final[int] = 17
_MDIB_INSTANCE_ID: typing.Final[int] = 1
_MD_DESCRIPTION_VERSION: typing.Final[int] = 4
_MD_STATE_VERSION: typing.Final[int] = 9

# Sample counts fixed by biceps_waveform_stream.xml; the two waveforms deliberately differ in length.
_ECG_SAMPLE_COUNT: typing.Final[int] = 10
_PLETH_SAMPLE_COUNT: typing.Final[int] = 4


def _mdib(soap_parser: parser.SoapEnvelopeParser) -> biceps_pm.Mdib:
    response = _parse(soap_parser, "biceps_get_mdib_response.xml").body_as(biceps_msg.GetMdibResponse)
    assert response is not None
    mdib = response.mdib
    assert isinstance(mdib, biceps_pm.Mdib)
    return mdib


def test_mdib_version_group(soap_parser: parser.SoapEnvelopeParser) -> None:
    """The three counters R0046 ties together are all present and read as integers."""
    mdib = _mdib(soap_parser)
    assert mdib.mdib_version == _MDIB_VERSION
    assert mdib.instance_id == _MDIB_INSTANCE_ID
    assert mdib.sequence_id == "urn:uuid:369a7d7b-5f87-48a4-aa9a-189edf2a8772"
    assert mdib.md_description is not None
    assert mdib.md_description.description_version == _MD_DESCRIPTION_VERSION
    assert mdib.md_state is not None
    assert mdib.md_state.state_version == _MD_STATE_VERSION


def test_containment_tree_is_navigable(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Mds -> Vmd -> Channel -> Metric, the four layers of the CONTAINMENT TREE."""
    mds = _mdib(soap_parser).md_description.mds[0]
    assert isinstance(mds, biceps_pm.MdsDescriptor)
    assert mds.handle == "mds0"
    assert mds.safety_classification == biceps_pm.SafetyClassification.MED_A

    vmd = mds.vmd[0]
    assert isinstance(vmd, biceps_pm.VmdDescriptor)
    channel = vmd.channels[0]
    assert isinstance(channel, biceps_pm.ChannelDescriptor)
    metrics = channel.metrics
    assert [type(metric).__name__ for metric in metrics] == [
        "NumericMetricDescriptor",
        "StringMetricDescriptor",
    ]
    assert [metric.unit.code for metric in metrics] == ["262688", "262656"]
    assert metrics[0].metric_category == biceps_pm.MetricCategory.MSRMT


def test_mds_reaches_its_sco_and_alert_system(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Both come from pm:AbstractComplexDeviceComponentDescriptor, so Vmd exposes them too."""
    mds = _mdib(soap_parser).md_description.mds[0]

    sco = mds.sco
    assert isinstance(sco, biceps_pm.ScoDescriptor)
    operation = sco.operations[0]
    # The element is pm:Operation; the concrete class comes from xsi:type.
    assert isinstance(operation, biceps_pm.SetValueOperationDescriptor)
    assert operation.handle == "sco.vmd0.set_rate"
    assert operation.operation_target == "vmd0.ch0.numeric0"

    alert_system = mds.alert_system
    assert isinstance(alert_system, biceps_pm.AlertSystemDescriptor)
    assert alert_system.self_check_period == datetime.timedelta(seconds=30)
    condition = alert_system.alert_conditions[0]
    assert isinstance(condition, biceps_pm.AlertConditionDescriptor)
    assert condition.kind == biceps_pm.AlertConditionKind.PHY
    assert condition.priority == biceps_pm.AlertConditionPriority.HI
    assert list(condition.sources) == ["vmd0.ch0.numeric0"]
    signal = alert_system.alert_signals[0]
    assert isinstance(signal, biceps_pm.AlertSignalDescriptor)
    assert signal.latching is False


def test_alert_condition_cause_and_remedy(soap_parser: parser.SoapEnvelopeParser) -> None:
    """pm:CauseInfo and its nested pm:RemedyInfo, on real schema-validated XML."""
    mds = _mdib(soap_parser).md_description.mds[0]
    cause_info = mds.alert_system.alert_conditions[0].cause_infos[0]
    assert isinstance(cause_info, biceps_pm.CauseInfo)
    assert [text.text for text in cause_info.descriptions] == ["sensor detached"]
    remedy_info = cause_info.remedy_info
    assert isinstance(remedy_info, biceps_pm.RemedyInfo)
    assert [text.text for text in remedy_info.descriptions] == ["reattach the sensor"]


def test_system_context_exposes_each_context_descriptor(soap_parser: parser.SoapEnvelopeParser) -> None:
    """The presence of a context descriptor is what states the provider can process that context (R0106)."""
    system_context = _mdib(soap_parser).md_description.mds[0].system_context
    assert isinstance(system_context, biceps_pm.SystemContextDescriptor)
    assert isinstance(system_context.patient_context, biceps_pm.PatientContextDescriptor)
    assert isinstance(system_context.location_context, biceps_pm.LocationContextDescriptor)
    assert [context.handle for context in system_context.workflow_contexts] == ["mds0.sc.workflow"]
    # Not offered by this device, so absent rather than empty-but-present.
    assert list(system_context.ensemble_contexts) == []
    assert list(system_context.means_contexts) == []


def test_descriptor_extension_carries_retrievability_and_safety_req(
    soap_parser: parser.SoapEnvelopeParser,
) -> None:
    """Two different extensions in descriptor ext:Extension: glue:R0005 msg:Retrievability, R0027 SafetyReq."""
    mds = _mdib(soap_parser).md_description.mds[0]

    extension = mds.extension
    assert extension is not None
    retrievability = extension.find_by_element(biceps_msg.Retrievability)
    assert isinstance(retrievability, biceps_msg.Retrievability)
    assert [info.method for info in retrievability.by] == [
        biceps_msg.RetrievabilityMethod.GET,
        biceps_msg.RetrievabilityMethod.EP,
    ]

    operation_extension = mds.sco.operations[0].extension
    assert operation_extension is not None
    safety_req = operation_extension.find_by_element(mdpws.SafetyReq)
    assert isinstance(safety_req, mdpws.SafetyReq)
    dual_channel_def = safety_req.dual_channel_def
    assert isinstance(dual_channel_def, mdpws.DualChannelDef)
    assert dual_channel_def.algorithm is not None
    assert dual_channel_def.algorithm.localname == "Base64SHA1"
    assert dual_channel_def.transform is not None
    assert dual_channel_def.transform.localname == "xml-exc-c14n"
    # These are the selector ids mdpws_safety_info_set_value.xml then references.
    assert [selector.id for selector in dual_channel_def.selectors] == ["SELECTOR_1", "SELECTOR_2"]
    assert safety_req.safety_context_def is not None
    assert [selector.id for selector in safety_req.safety_context_def.selectors] == [
        "SELECTOR_3",
        "SELECTOR_4",
    ]


def test_md_state_dispatches_every_state_by_xsi_type(soap_parser: parser.SoapEnvelopeParser) -> None:
    """pm:MdState holds a flat list of pm:State whose concrete class is carried only by xsi:type."""
    states = _mdib(soap_parser).md_state.states
    assert sorted({type(state).__name__ for state in states}) == [
        "AlertConditionState",
        "AlertSignalState",
        "AlertSystemState",
        "ChannelState",
        "LocationContextState",
        "MdsState",
        "NumericMetricState",
        "PatientContextState",
        "SetValueOperationState",
        "StringMetricState",
        "SystemContextState",
        "VmdState",
        "WorkflowContextState",
    ]


def test_context_states_carry_their_own_handle(soap_parser: parser.SoapEnvelopeParser) -> None:
    """Context states are multi states: they have @Handle as well as @DescriptorHandle."""
    states = _mdib(soap_parser).md_state.states
    patient = next(state for state in states if isinstance(state, biceps_pm.PatientContextState))
    assert patient.descriptor_handle == "mds0.sc.patient"
    assert patient.handle == "mds0.sc.patient.0"
    assert patient.context_association == biceps_pm.ContextAssociation.ASSOC
    core_data = patient.core_data
    assert isinstance(core_data, biceps_pm.PatientDemographicsCoreData)
    assert core_data.sex == biceps_pm.Sex.UNSPEC


def test_workflow_detail_survives_schema_validation(soap_parser: parser.SoapEnvelopeParser) -> None:
    """The workflow / order / clinical-info branch, read back from XML validated against the real schema.

    The per-module tests reach these classes through a non-validating parser, because the participant model
    declares no global elements and so cannot be a document root. Only here is the branch checked against the
    schema at the same time as the properties.
    """
    states = _mdib(soap_parser).md_state.states
    workflow_state = next(state for state in states if isinstance(state, biceps_pm.WorkflowContextState))
    detail = workflow_state.workflow_detail
    assert isinstance(detail, biceps_pm.WorkflowDetail)
    assert isinstance(detail.patient, biceps_pm.PersonReference)
    assert isinstance(detail.assigned_location, biceps_pm.LocationReference)
    assert detail.visit_number is not None
    assert detail.visit_number.extension_attr == "V-7"

    clinical_info = detail.relevant_clinical_infos[0]
    assert isinstance(clinical_info, biceps_pm.ClinicalInfo)
    assert clinical_info.criticality is biceps_pm.Criticality.HI
    measurement = clinical_info.related_measurements[0]
    assert isinstance(measurement, biceps_pm.RelatedMeasurement)
    assert measurement.value.measured_value == decimal.Decimal("4.2")
    reference_range = measurement.reference_ranges[0]
    assert isinstance(reference_range, biceps_pm.ReferenceRange)
    assert reference_range.range.upper == decimal.Decimal("2.2")

    requested = detail.requested_order_detail
    assert isinstance(requested, biceps_pm.RequestedOrderDetail)
    assert requested.start == datetime.datetime(2026, 9, 4, 8, 30, tzinfo=datetime.UTC)
    procedure = requested.imaging_procedures[0]
    assert isinstance(procedure, biceps_pm.ImagingProcedure)
    assert procedure.modality is not None
    assert procedure.modality.code == "CT"
    assert requested.placer_order_number.extension_attr == "PON-9"

    performed = detail.performed_order_detail
    assert isinstance(performed, biceps_pm.PerformedOrderDetail)
    assert performed.resulting_clinical_infos[0].criticality is biceps_pm.Criticality.LO


# ── BICEPS SET SERVICE and WAVEFORM SERVICE ────────────────────────────────────────────────────────


def test_operation_invoked_report_tracks_a_transaction(soap_parser: parser.SoapEnvelopeParser) -> None:
    """BICEPS 7.4.3 models an invocation as a sequence of msg:InvocationState steps under one transaction."""
    report = _parse(soap_parser, "biceps_operation_invoked_report.xml").body_as(
        biceps_msg.OperationInvokedReport,
    )
    assert report is not None
    parts = report.report_parts
    assert [part.invocation_info.transaction_id for part in parts] == [4711, 4712]
    assert [part.invocation_info.invocation_state for part in parts] == [
        biceps_msg.InvocationState.START,
        biceps_msg.InvocationState.FAIL,
    ]
    # Only the failing part carries an error, and only it carries a message.
    assert parts[0].invocation_info.invocation_error is None
    assert parts[1].invocation_info.invocation_error == biceps_msg.InvocationError.INV
    assert [text.text for text in parts[1].invocation_info.invocation_error_messages] == [
        "requested value outside the allowed range",
    ]
    assert [part.source_mds for part in parts] == ["mds0", "mds0"]


def test_operation_invoked_report_names_the_invoking_participant(
    soap_parser: parser.SoapEnvelopeParser,
) -> None:
    """glue:R0077 fixes this identifier for a participant the provider cannot attribute."""
    report = _parse(soap_parser, "biceps_operation_invoked_report.xml").body_as(
        biceps_msg.OperationInvokedReport,
    )
    assert report is not None
    source = report.report_parts[0].invocation_source
    assert isinstance(source, biceps_pm.InstanceIdentifier)


def test_waveform_stream_reads_sample_arrays(soap_parser: parser.SoapEnvelopeParser) -> None:
    """@Samples is a whitespace-delimited decimal list, and the two waveforms have different lengths."""
    stream = _parse(soap_parser, "biceps_waveform_stream.xml").body_as(biceps_msg.WaveformStream)
    assert stream is not None
    states = stream.states
    assert [state.descriptor_handle for state in states] == ["vmd0.ch0.ecg", "vmd0.ch0.pleth"]
    assert all(isinstance(state, biceps_pm.RealTimeSampleArrayMetricState) for state in states)

    ecg = states[0].metric_value
    assert isinstance(ecg, biceps_pm.SampleArrayValue)
    assert len(ecg.samples) == _ECG_SAMPLE_COUNT
    assert ecg.samples[4] == decimal.Decimal("0.95")
    assert ecg.samples[7] == decimal.Decimal("-0.02")
    # ApplyAnnotation binds one annotation to a single sample by index.
    assert [(a.annotation_index, a.sample_index) for a in ecg.apply_annotations] == [(0, 4)]

    pleth = states[1].metric_value
    assert isinstance(pleth, biceps_pm.SampleArrayValue)
    assert len(pleth.samples) == _PLETH_SAMPLE_COUNT
    assert pleth.metric_quality.validity == biceps_pm.MeasurementValidity.QST
    assert pleth.metric_quality.qi == decimal.Decimal("0.5")


def test_waveform_stream_carries_wsa_from(soap_parser: parser.SoapEnvelopeParser) -> None:
    """glue:R0040 requires wsa:From in every STREAMING message so a packet can be attributed to a provider."""
    header = _parse(soap_parser, "biceps_waveform_stream.xml").header
    from_ = header.from_
    assert isinstance(from_, addressing.From)
    assert from_.address.text == "urn:uuid:98190dc2-0890-4ef8-ac9a-5940995e6119"
