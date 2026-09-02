"""Tests for the BICEPS ParticipantModel model classes."""

import datetime
import decimal

import lxml.etree
import pytest

from sdc_xsd_model import converter
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


@pytest.mark.parametrize(("raw", "expected"), [("true", True), ("1", True), ("false", False), ("0", False)])
def test_alert_signal_descriptor_latching(raw: str, expected: bool) -> None:  # noqa: FBT001
    """Ensure the Latching attribute is exposed as a Python bool."""
    xml = f'<AlertSignal xmlns="{biceps_pm.NAMESPACE}" Manifestation="Vis" Latching="{raw}"/>'.encode()
    element = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    assert isinstance(element, biceps_pm.AlertSignalDescriptor)
    assert element.latching is expected


# ── converted property types ───────────────────────────────────────────────────────────────────────


_SELF_CHECK_COUNT = 42
_LAST_SELF_CHECK = 1733317200000


def _parse(xml: str) -> lxml.etree._Element:
    """Parse a hand-written PM fragment with the non-validating lookup parser."""
    return lxml.etree.fromstring(xml.encode(), parser=_LOOKUP_PARSER)


@pytest.mark.parametrize(("raw", "expected"), [("true", True), ("1", True), ("false", False), ("0", False)])
def test_optional_boolean_attribute(raw: str, expected: bool) -> None:  # noqa: FBT001
    """An optional xsd:boolean attribute is exposed as a bool, including the "1"/"0" forms."""
    element = _parse(f'<AlertSignal xmlns="{biceps_pm.NAMESPACE}" AcknowledgementSupported="{raw}"/>')
    assert isinstance(element, biceps_pm.AlertSignalDescriptor)
    assert element.acknowledgement_supported is expected


def test_absent_optional_boolean_attribute_is_none() -> None:
    """An absent optional attribute stays absent rather than defaulting."""
    element = _parse(f'<AlertSignal xmlns="{biceps_pm.NAMESPACE}"/>')
    assert isinstance(element, biceps_pm.AlertSignalDescriptor)
    assert element.acknowledgement_supported is None


def test_invalid_boolean_attribute_raises() -> None:
    """A literal outside the xsd:boolean lexical space is rejected rather than silently false."""
    element = _parse(f'<AlertSignal xmlns="{biceps_pm.NAMESPACE}" AcknowledgementSupported="True"/>')
    assert isinstance(element, biceps_pm.AlertSignalDescriptor)
    with pytest.raises(ValueError, match="xsd:boolean"):
        _ = element.acknowledgement_supported


def test_integer_attribute() -> None:
    """An xsd:long attribute is exposed as an int."""
    element = _parse(f'<AlertSystemState xmlns="{biceps_pm.NAMESPACE}" SelfCheckCount="{_SELF_CHECK_COUNT}"/>')
    assert isinstance(element, biceps_pm.AlertSystemState)
    assert element.self_check_count == _SELF_CHECK_COUNT


def test_integer_attribute_rejects_python_only_literal() -> None:
    """Underscores are valid for int() but not for xsd:integer."""
    element = _parse(f'<AlertSystemState xmlns="{biceps_pm.NAMESPACE}" SelfCheckCount="1_0"/>')
    assert isinstance(element, biceps_pm.AlertSystemState)
    with pytest.raises(ValueError, match="xsd:integer"):
        _ = element.self_check_count


def test_timestamp_attribute_is_nominal_type() -> None:
    """A pm:Timestamp attribute is exposed as the Timestamp int subclass."""
    element = _parse(f'<AlertSystemState xmlns="{biceps_pm.NAMESPACE}" LastSelfCheck="{_LAST_SELF_CHECK}"/>')
    assert isinstance(element, biceps_pm.AlertSystemState)
    assert isinstance(element.last_self_check, biceps_pm.Timestamp)
    assert element.last_self_check == _LAST_SELF_CHECK


def test_decimal_attribute_preserves_precision() -> None:
    """An xsd:decimal attribute becomes a Decimal built from the literal."""
    element = _parse(f'<Range xmlns="{biceps_pm.NAMESPACE}" Lower="1.50" Upper="99"/>')
    assert isinstance(element, biceps_pm.Range)
    assert element.lower == decimal.Decimal("1.5")
    assert str(element.lower) == "1.50"
    assert element.upper == decimal.Decimal(99)


def test_decimal_attribute_rejects_exponent() -> None:
    """decimal.Decimal accepts "1E5"; xsd:decimal does not."""
    element = _parse(f'<Range xmlns="{biceps_pm.NAMESPACE}" Lower="1E5"/>')
    assert isinstance(element, biceps_pm.Range)
    with pytest.raises(ValueError, match="xsd:decimal"):
        _ = element.lower


def test_enum_attribute() -> None:
    """An enumerated attribute resolves to the enum member itself, not a look-alike string."""
    element = _parse(f'<AlertSignal xmlns="{biceps_pm.NAMESPACE}" Manifestation="Vis" Latching="false"/>')
    assert isinstance(element, biceps_pm.AlertSignalDescriptor)
    assert element.manifestation is biceps_pm.AlertSignalManifestation.VIS


def test_enum_attribute_rejects_unknown_value() -> None:
    """A value outside the enumeration facet is rejected, and the message lists what is permitted."""
    element = _parse(f'<AlertSignal xmlns="{biceps_pm.NAMESPACE}" Manifestation="Nope" Latching="false"/>')
    assert isinstance(element, biceps_pm.AlertSignalDescriptor)
    with pytest.raises(ValueError, match="Aud, Vis, Tan, Oth"):
        _ = element.manifestation


def test_narrowed_enum_attribute_excludes_widest_value() -> None:
    """@CanEscalate restricts pm:AlertConditionPriority and drops "None"."""
    element = _parse(f'<AlertCondition xmlns="{biceps_pm.NAMESPACE}" Kind="Phy" Priority="Lo" CanEscalate="Hi"/>')
    assert isinstance(element, biceps_pm.AlertConditionDescriptor)
    assert element.can_escalate is biceps_pm.CanEscalate.HI
    element = _parse(f'<AlertCondition xmlns="{biceps_pm.NAMESPACE}" Kind="Phy" Priority="Lo" CanEscalate="None"/>')
    assert isinstance(element, biceps_pm.AlertConditionDescriptor)
    with pytest.raises(ValueError, match="CanEscalate"):
        _ = element.can_escalate


def test_duration_attribute() -> None:
    """An xsd:duration attribute is exposed as a timedelta."""
    element = _parse(f'<AlertSystem xmlns="{biceps_pm.NAMESPACE}" SelfCheckPeriod="PT1H30M"/>')
    assert isinstance(element, biceps_pm.AlertSystemDescriptor)
    assert element.self_check_period == datetime.timedelta(hours=1, minutes=30)


def test_absent_duration_attribute_is_none() -> None:
    """The explicit None guard on each duration property keeps an absent attribute absent."""
    element = _parse(f'<AlertSystem xmlns="{biceps_pm.NAMESPACE}"/>')
    assert isinstance(element, biceps_pm.AlertSystemDescriptor)
    assert element.self_check_period is None


def test_qname_attribute_resolves_prefix() -> None:
    """An xsd:QName attribute resolves its prefix against the in-scope namespace declarations."""
    element = _parse(f'<Entry xmlns="{biceps_pm.NAMESPACE}" xmlns:pm="{biceps_pm.NAMESPACE}" EntryType="pm:Mds"/>')
    assert isinstance(element, biceps_pm.ContainmentTreeEntry)
    entry_type = element.entry_type
    assert entry_type is not None
    assert entry_type.namespace == biceps_pm.NAMESPACE
    assert entry_type.localname == "Mds"


def test_handle_ref_list_attribute() -> None:
    """A pm:HandleRef list attribute is split into HandleRef items."""
    element = _parse(f'<AlertSystemState xmlns="{biceps_pm.NAMESPACE}" PresentPhysiologicalAlarmConditions="a b  c"/>')
    assert isinstance(element, biceps_pm.AlertSystemState)
    assert element.present_physiological_alarm_conditions == ["a", "b", "c"]


def test_absent_handle_ref_list_attribute_is_empty() -> None:
    """An absent list attribute yields an empty sequence, not None."""
    element = _parse(f'<AlertSystemState xmlns="{biceps_pm.NAMESPACE}"/>')
    assert isinstance(element, biceps_pm.AlertSystemState)
    assert element.present_physiological_alarm_conditions == []


def test_sample_array_samples_are_decimals() -> None:
    """pm:RealTimeValueType is a list of xsd:decimal, so each sample converts individually."""
    element = _parse(f'<SampleArrayValue xmlns="{biceps_pm.NAMESPACE}" Samples="1.5 -2 0.25"/>')
    assert isinstance(element, biceps_pm.SampleArrayValue)
    assert element.samples == [decimal.Decimal("1.5"), decimal.Decimal(-2), decimal.Decimal("0.25")]


def test_metric_relation_entries_reads_the_attribute() -> None:
    """Relation/@Entries is an attribute, not a child element."""
    element = _parse(f'<Relation xmlns="{biceps_pm.NAMESPACE}" Kind="Rcm" Entries="h1 h2"/>')
    assert isinstance(element, biceps_pm.MetricRelation)
    assert element.entries == ["h1", "h2"]
    assert element.kind is biceps_pm.MetricRelationKind.RCM


def test_xsi_type_absent_is_none() -> None:
    """xsi:type is absent on concretely-typed elements, which is not an error."""
    element = _parse(f'<Mds xmlns="{biceps_pm.NAMESPACE}" Handle="mds0"/>')
    assert isinstance(element, biceps_pm.MdsDescriptor)
    assert element.xsi_type is None
    assert element.handle == "mds0"


def test_xsi_type_resolves_to_qname() -> None:
    """A present xsi:type is exposed as a resolved QName rather than the raw prefixed string."""
    xml = (
        f'<AlertSystem xmlns="{biceps_pm.NAMESPACE}" xmlns:pm="{biceps_pm.NAMESPACE}"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xsi:type="pm:AlertSystemDescriptor" Handle="as0"/>'
    )
    element = _parse(xml)
    assert isinstance(element, biceps_pm.AlertSystemDescriptor)
    xsi_type = element.xsi_type
    assert xsi_type is not None
    assert xsi_type.namespace == biceps_pm.NAMESPACE
    assert xsi_type.localname == "AlertSystemDescriptor"


# ── date and time properties ───────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2020", converter.XsdDateTime(2020)),
        ("2020-05", converter.XsdDateTime(2020, 5)),
        ("2020-05-17", converter.XsdDateTime(2020, 5, 17)),
        ("2020-05-17T10:20:30Z", converter.XsdDateTime(2020, 5, 17, datetime.time(10, 20, 30), datetime.UTC)),
    ],
)
def test_core_data_date_of_birth(raw: str, expected: converter.XsdDateTime) -> None:
    """DateOfBirth is a union of four precisions, each of which is exposed as an XsdDateTime."""
    element = _parse(f'<CoreData xmlns="{biceps_pm.NAMESPACE}"><DateOfBirth>{raw}</DateOfBirth></CoreData>')
    assert isinstance(element, biceps_pm.PatientDemographicsCoreData)
    assert element.date_of_birth == expected


def test_core_data_date_of_birth_absent() -> None:
    """DateOfBirth is optional, so an absent one stays absent."""
    element = _parse(f'<CoreData xmlns="{biceps_pm.NAMESPACE}"/>')
    assert isinstance(element, biceps_pm.PatientDemographicsCoreData)
    assert element.date_of_birth is None


def test_core_data_date_of_birth_invalid() -> None:
    """An invalid literal raises rather than being handed back as the raw string it used to be."""
    element = _parse(f'<CoreData xmlns="{biceps_pm.NAMESPACE}"><DateOfBirth>17.05.2020</DateOfBirth></CoreData>')
    assert isinstance(element, biceps_pm.PatientDemographicsCoreData)
    with pytest.raises(ValueError, match="not a valid xsd:dateTime"):
        _ = element.date_of_birth


def _meta_data(**children: str) -> biceps_pm.MetaData:
    """Build a MetaData element with the given child elements and texts.

    Built through the class rather than parsed, because MetaData is not registered in set_lookup, so no
    parser resolves a pm:MetaData element to this class.
    """
    element = biceps_pm.MetaData()
    for name, text in children.items():
        lxml.etree.SubElement(element, f"{{{biceps_pm.NAMESPACE}}}{name}").text = text
    return element


def test_meta_data_dates() -> None:
    """ManufactureDate and ExpirationDate are plain xsd:dateTime, so both are exposed as datetimes."""
    element = _meta_data(ManufactureDate="2020-05-17T10:20:30Z", ExpirationDate="2030-05-17T00:00:00")
    assert element.manufacture_date == datetime.datetime.fromisoformat("2020-05-17T10:20:30+00:00")
    assert element.expiration_date == datetime.datetime.fromisoformat("2030-05-17T00:00:00")


def test_meta_data_dates_absent() -> None:
    """Both elements are optional, so an absent one stays absent."""
    element = _meta_data()
    assert element.manufacture_date is None
    assert element.expiration_date is None


def test_meta_data_date_rejects_shorter_form() -> None:
    """A bare year is a valid xsd:gYear but not a valid xsd:dateTime, so it is not silently accepted."""
    element = _meta_data(ManufactureDate="2020")
    with pytest.raises(ValueError, match="xsd:gYear literal"):
        _ = element.manufacture_date
