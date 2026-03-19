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
