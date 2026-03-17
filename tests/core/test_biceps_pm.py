"""Tests for the BICEPS ParticipantModel model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.core import biceps_pm, common, extension


def _get_lookup_parser() -> lxml.etree.XMLParser:
    """Non-validating parser with class lookup for roundtrip tests.

    The BICEPS XSD only declares complexTypes, not global elements,
    so the schema-validating parser rejects them as standalone roots.
    """
    lookup = lxml.etree.ElementNamespaceClassLookup()
    extension.set_lookup(lookup)
    biceps_pm.set_lookup(lookup)
    parser = lxml.etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    return parser


_LOOKUP_PARSER = _get_lookup_parser()

# (class, local element name) for classes with TAG set
BICEPS_PM_CASES = [
    (biceps_pm.MdDescription, "MdDescription"),
    (biceps_pm.MdState, "MdState"),
    (biceps_pm.MdsDescriptor, "Mds"),
    (biceps_pm.VmdDescriptor, "Vmd"),
    (biceps_pm.ChannelDescriptor, "Channel"),
    (biceps_pm.ClockDescriptor, "Clock"),
    (biceps_pm.BatteryDescriptor, "Battery"),
    (biceps_pm.ScoDescriptor, "Sco"),
    (biceps_pm.AlertSystemDescriptor, "AlertSystem"),
    (biceps_pm.AlertConditionDescriptor, "AlertCondition"),
    (biceps_pm.AlertSignalDescriptor, "AlertSignal"),
    (biceps_pm.SystemContextDescriptor, "SystemContext"),
    (biceps_pm.PatientContextDescriptor, "PatientContext"),
    (biceps_pm.LocationContextDescriptor, "LocationContext"),
    (biceps_pm.WorkflowContextDescriptor, "WorkflowContext"),
    (biceps_pm.OperatorContextDescriptor, "OperatorContext"),
    (biceps_pm.MeansContextDescriptor, "MeansContext"),
    (biceps_pm.EnsembleContextDescriptor, "EnsembleContext"),
    (biceps_pm.PhysicalConnectorInfo, "PhysicalConnector"),
    (biceps_pm.CalibrationInfo, "CalibrationInfo"),
    (biceps_pm.ApprovedJurisdictions, "ApprovedJurisdictions"),
    (biceps_pm.OperatingJurisdiction, "OperatingJurisdiction"),
    (biceps_pm.SystemSignalActivation, "SystemSignalActivation"),
    (biceps_pm.CauseInfo, "CauseInfo"),
    (biceps_pm.RemedyInfo, "RemedyInfo"),
    (biceps_pm.ImagingProcedure, "ImagingProcedure"),
    (biceps_pm.LocationDetail, "LocationDetail"),
    (biceps_pm.PatientDemographicsCoreData, "CoreData"),
    (biceps_pm.ContainmentTreeEntry, "Entry"),
]


@pytest.mark.parametrize(("clazz", "local_name"), BICEPS_PM_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure BICEPS PM classes expose the expected TAG value."""
    assert f"{{{biceps_pm.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in BICEPS_PM_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure BICEPS PM classes register the expected namespace."""
    assert clazz().nsmap[biceps_pm.PREFIX] == biceps_pm.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in BICEPS_PM_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure BICEPS PM classes can be serialized and deserialized via namespace lookup."""
    element = clazz()
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    assert isinstance(parsed_element, clazz)


# ── Property tests ──────────────────────────────────────────────────────────────────────────────


def test_location_detail_properties() -> None:
    """Ensure LocationDetail exposes location attributes."""
    loc = biceps_pm.LocationDetail(
        PoC="ICU",
        Room="101",
        Bed="A",
        Facility="Hospital",
        Building="Main",
        Floor="3",
    )
    assert loc.poc == "ICU"
    assert loc.room == "101"
    assert loc.bed == "A"
    assert loc.facility == "Hospital"
    assert loc.building == "Main"
    assert loc.floor == "3"


def test_system_signal_activation_properties() -> None:
    """Ensure SystemSignalActivation exposes Manifestation and State."""
    ssa = biceps_pm.SystemSignalActivation(
        Manifestation="Aud",
        State="On",
    )
    assert ssa.manifestation == "Aud"
    assert ssa.state == "On"


def test_mds_descriptor_handle() -> None:
    """Ensure MdsDescriptor exposes handle attribute."""
    mds = biceps_pm.MdsDescriptor(Handle="mds-1")
    assert mds.handle == "mds-1"


def test_abstract_state_descriptor_handle() -> None:
    """Ensure AbstractState exposes descriptor_handle."""
    state = biceps_pm.MdsState(DescriptorHandle="mds-1")
    assert state.descriptor_handle == "mds-1"


def test_containment_tree_entry_properties() -> None:
    """Ensure ContainmentTreeEntry exposes its attributes."""
    entry = biceps_pm.ContainmentTreeEntry(HandleRef="h1", ParentHandleRef="p1")
    assert entry.handle_ref == "h1"
    assert entry.parent_handle_ref == "p1"


def test_enum_values() -> None:
    """Ensure key StrEnum values match the XSD specification."""
    assert biceps_pm.SafetyClassification.INF == "Inf"
    assert biceps_pm.SafetyClassification.MED_A == "MedA"
    assert biceps_pm.ComponentActivation.ON == "On"
    assert biceps_pm.AlertActivation.PSD == "Psd"
    assert biceps_pm.MetricCategory.MSRMT == "Msrmt"
    assert biceps_pm.Sex.M == "M"
    assert biceps_pm.ContextAssociation.ASSOC == "Assoc"
    assert biceps_pm.OperatingMode.EN == "En"
