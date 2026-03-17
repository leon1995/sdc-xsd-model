"""Tests for the BICEPS MessageModel model classes."""

import lxml.etree
import pytest

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


# ── Enum tests ─────────────────────────────────────────────────────────────────────────────────────


def test_enum_values() -> None:
    """Ensure key StrEnum values match the XSD specification."""
    assert biceps_msg.InvocationState.WAIT == "Wait"
    assert biceps_msg.InvocationState.START == "Start"
    assert biceps_msg.InvocationState.CNCLLD == "Cnclld"
    assert biceps_msg.InvocationState.CNCLLD_MAN == "CnclldMan"
    assert biceps_msg.InvocationState.FIN == "Fin"
    assert biceps_msg.InvocationState.FIN_MOD == "FinMod"
    assert biceps_msg.InvocationState.FAIL == "Fail"
    assert biceps_msg.InvocationError.UNSPEC == "Unspec"
    assert biceps_msg.InvocationError.UNKN == "Unkn"
    assert biceps_msg.InvocationError.INV == "Inv"
    assert biceps_msg.InvocationError.OTH == "Oth"
    assert biceps_msg.DescriptionModificationType.CRT == "Crt"
    assert biceps_msg.DescriptionModificationType.UPT == "Upt"
    assert biceps_msg.DescriptionModificationType.DEL == "Del"
    assert biceps_msg.RetrievabilityMethod.GET == "Get"
    assert biceps_msg.RetrievabilityMethod.PER == "Per"
    assert biceps_msg.RetrievabilityMethod.EP == "Ep"
    assert biceps_msg.RetrievabilityMethod.STRM == "Strm"


# ── Property tests ─────────────────────────────────────────────────────────────────────────────────


def test_abstract_get_response_mdib_version_group() -> None:
    """Ensure AbstractGetResponse exposes MdibVersionGroup attributes."""
    resp = biceps_msg.GetMdibResponse(SequenceId="urn:uuid:test", MdibVersion="42", InstanceId="1")
    assert resp.sequence_id == "urn:uuid:test"
    assert resp.mdib_version == "42"
    assert resp.instance_id == "1"


def test_abstract_report_mdib_version_group() -> None:
    """Ensure AbstractReport exposes MdibVersionGroup attributes."""
    report = biceps_msg.EpisodicMetricReport(SequenceId="urn:uuid:report")
    assert report.sequence_id == "urn:uuid:report"
    assert report.mdib_version is None
    assert report.instance_id is None


def test_version_frame_properties() -> None:
    """Ensure VersionFrame exposes start and end attributes."""
    vf = biceps_msg.VersionFrame(Start="0", End="10")
    assert vf.start == 0
    assert vf.end == 10


def test_time_frame_properties() -> None:
    """Ensure TimeFrame exposes start and end attributes."""
    tf = biceps_msg.TimeFrame(Start="1532", End="3212")
    assert tf.start == 1532
    assert tf.end == 3212


def test_retrievability_info_properties() -> None:
    """Ensure RetrievabilityInfo exposes method and update_period."""
    ri = biceps_msg.RetrievabilityInfo(Method="Get")
    assert ri.method == "Get"
    assert ri.update_period is None

    ri2 = biceps_msg.RetrievabilityInfo(Method="Per", UpdatePeriod="PT1S")
    assert ri2.method == "Per"
    assert ri2.update_period == "PT1S"


def test_report_part_attributes() -> None:
    """Ensure ReportPart exposes operation attributes."""
    rp = biceps_msg.ReportPart(OperationHandleRef="op-1", OperationTarget="target-1")
    assert rp.operation_handle_ref == "op-1"
    assert rp.operation_target == "target-1"
    assert rp.parent_descriptor is None
    assert rp.modification_type is None


def test_report_part_modification_type() -> None:
    """Ensure ReportPart exposes description modification attributes."""
    rp = biceps_msg.ReportPart(ParentDescriptor="mds-1", ModificationType="Crt")
    assert rp.parent_descriptor == "mds-1"
    assert rp.modification_type == "Crt"


def test_get_context_states_by_identification_context_type() -> None:
    """Ensure GetContextStatesByIdentification exposes ContextType attribute."""
    el = biceps_msg.GetContextStatesByIdentification(ContextType="pm:LocationContextState")
    assert el.context_type == "pm:LocationContextState"


def test_abstract_set_response_mdib_version_group() -> None:
    """Ensure AbstractSetResponse exposes MdibVersionGroup attributes."""
    resp = biceps_msg.SetValueResponse(SequenceId="urn:uuid:set")
    assert resp.sequence_id == "urn:uuid:set"
    assert resp.mdib_version is None
