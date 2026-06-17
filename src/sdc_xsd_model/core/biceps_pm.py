"""Lxml models for BICEPS ParticipantModel elements from IEEE 11073-10207-2017."""

from __future__ import annotations

import decimal
import enum
import functools
import pathlib
import typing

import lxml.etree

from sdc_xsd_model import element_class_lookup
from sdc_xsd_model.core import common, extension
from sdc_xsd_model.core.extension import Extension

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

PREFIX: typing.Final[str] = "pm"
NAMESPACE: typing.Final[str] = "http://standards.ieee.org/downloads/11073/11073-10207-2017/participant"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.parent.joinpath("xsd", "BICEPS_ParticipantModel.xsd").absolute()
)
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


# ── Simple type enums ──────────────────────────────────────────────────────────────────────────────


class MeasurementValidity(enum.StrEnum):
    VLD = "Vld"
    VLDATED = "Vldated"
    ONG = "Ong"
    QST = "Qst"
    CALIB = "Calib"
    INV = "Inv"
    OFLW = "Oflw"
    UFLW = "Uflw"
    NA = "NA"


class SafetyClassification(enum.StrEnum):
    INF = "Inf"
    MED_A = "MedA"
    MED_B = "MedB"
    MED_C = "MedC"


class ComponentActivation(enum.StrEnum):
    ON = "On"
    NOT_RDY = "NotRdy"
    STND_BY = "StndBy"
    OFF = "Off"
    SHTDN = "Shtdn"
    FAIL = "Fail"


class CalibrationState(enum.StrEnum):
    NO = "No"
    REQ = "Req"
    RUN = "Run"
    CAL = "Cal"
    OTH = "Oth"


class CalibrationType(enum.StrEnum):
    OFFSET = "Offset"
    GAIN = "Gain"
    TP = "TP"
    UNSPEC = "Unspec"


class MdsOperatingMode(enum.StrEnum):
    NML = "Nml"
    DMO = "Dmo"
    SRV = "Srv"
    MTN = "Mtn"


class AlertActivation(enum.StrEnum):
    ON = "On"
    OFF = "Off"
    PSD = "Psd"


class AlertConditionKind(enum.StrEnum):
    PHY = "Phy"
    TEC = "Tec"
    OTH = "Oth"


class AlertConditionPriority(enum.StrEnum):
    LO = "Lo"
    ME = "Me"
    HI = "Hi"
    NONE = "None"


class AlertSignalManifestation(enum.StrEnum):
    AUD = "Aud"
    VIS = "Vis"
    TAN = "Tan"
    OTH = "Oth"


class AlertSignalPresence(enum.StrEnum):
    ON = "On"
    OFF = "Off"
    LATCH = "Latch"
    ACK = "Ack"


class AlertSignalPrimaryLocation(enum.StrEnum):
    LOC = "Loc"
    REM = "Rem"


class MetricCategory(enum.StrEnum):
    UNSPEC = "Unspec"
    MSRMT = "Msrmt"
    CLC = "Clc"
    SET = "Set"
    PRESET = "Preset"
    RCMM = "Rcmm"


class DerivationMethod(enum.StrEnum):
    AUTO = "Auto"
    MAN = "Man"


class MetricAvailability(enum.StrEnum):
    INTR = "Intr"
    CONT = "Cont"


class GenerationMode(enum.StrEnum):
    REAL = "Real"
    TEST = "Test"
    DEMO = "Demo"


class Sex(enum.StrEnum):
    UNSPEC = "Unspec"
    M = "M"
    F = "F"
    UNKN = "Unkn"


class PatientType(enum.StrEnum):
    UNSPEC = "Unspec"
    AD = "Ad"
    ADO = "Ado"
    PED = "Ped"
    INF = "Inf"
    NEO = "Neo"
    OTH = "Oth"


class ContextAssociation(enum.StrEnum):
    NO = "No"
    PRE = "Pre"
    ASSOC = "Assoc"
    DIS = "Dis"


class AlertConditionMonitoredLimits(enum.StrEnum):
    ALL = "All"
    LO_OFF = "LoOff"
    HI_OFF = "HiOff"
    NONE = "None"


class OperatingMode(enum.StrEnum):
    DIS = "Dis"
    EN = "En"
    NA = "NA"


class LocalizedTextWidth(enum.StrEnum):
    XS = "xs"
    S = "s"
    M = "m"
    L = "l"
    XL = "xl"
    XXL = "xxl"


class MetricRelationKind(enum.StrEnum):
    RCM = "Rcm"
    PS = "PS"
    SST = "SST"
    ECE = "ECE"
    DCE = "DCE"
    OTH = "Oth"


# ── Common complex types ──────────────────────────────────────────────────────────────────────────


class Handle(str):
    """A HANDLE is used to efficiently identify an object in the MDIB."""

    __slots__ = ()


class HandleRef(str):
    """HandleRef describes a HANDLE reference.

    It is used to form logical connections to ELEMENTs that possess a pm:Handle ATTRIBUTE.
    """

    __slots__ = ()


class CodeIdentifier(str):
    """CodeIdentifier defines an arbitrary CODE identifier with a minimum length of 1 character."""

    __slots__ = ()


class SymbolicCodeName(str):
    """SymbolicCodeName is a symbolic, programmatic form of a pm:CodeIdentifier term.

    NOTE—SymbolicCodeName is the equivalent of the Reference ID attribute that is defined in IEEE 11073-10101.
    """

    __slots__ = ()


class Timestamp(int):
    """An unsigned 64-bit integer value that represents a timestamp."""


class LocalizedText(common.ElementBase):
    """Bundled element for localized text references or content."""

    @property
    def ref(self) -> str | None:
        return self.get("Ref")

    @property
    def lang(self) -> str | None:
        return self.get("Lang")

    @property
    def version(self) -> str | None:
        return self.get("Version")

    @property
    def text_width(self) -> str | None:
        return self.get("TextWidth")


class Translation(common.ElementBase):
    """Set of alternative or equivalent representations."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def code(self) -> CodeIdentifier:
        value = self.get("Code")
        assert value is not None
        return CodeIdentifier(value)

    @property
    def coding_system(self) -> str | None:
        # TODO: return xsd:anyUri?  # noqa: FIX002, TD002, TD003
        return self.get("CodingSystem")

    @property
    def coding_system_version(self) -> str | None:
        return self.get("CodingSystemVersion")


class CodedValue(common.ElementBase):
    """Nomenclature code representation."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def coding_system_names(self) -> Sequence[LocalizedText]:
        return typing.cast("Sequence[LocalizedText]", self.findall(f"{{{NAMESPACE}}}CodingSystemName"))

    @property
    def concept_descriptions(self) -> Sequence[LocalizedText]:
        return typing.cast("Sequence[LocalizedText]", self.findall(f"{{{NAMESPACE}}}ConceptDescription"))

    @property
    def code(self) -> CodeIdentifier:
        value = self.get("Code")
        assert value is not None
        return CodeIdentifier(value)

    @property
    def coding_system(self) -> str | None:
        # TODO: return xsd:anyUri?  # noqa: FIX002, TD002, TD003
        return self.get("CodingSystem")

    @property
    def coding_system_version(self) -> str | None:
        return self.get("CodingSystemVersion")

    @property
    def symbolic_code_name(self) -> SymbolicCodeName | None:
        value = self.get("SymbolicCodeName")
        return SymbolicCodeName(value) if value is not None else None

    @property
    def translations(self) -> Sequence[Translation]:
        return typing.cast("Sequence[Translation]", self.findall(f"{{{NAMESPACE}}}Translation"))


class InstanceIdentifier(common.ElementBase):
    """Uniquely identifies a thing or object."""

    TAG = f"{{{NAMESPACE}}}Identification"

    @property
    def root(self) -> str | None:
        return self.get("Root")

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def extension_attr(self) -> str | None:
        return self.get("Extension")

    @property
    def identifier_names(self) -> Sequence[LocalizedText]:
        return typing.cast("Sequence[LocalizedText]", self.findall(f"{{{NAMESPACE}}}IdentifierName"))

    @property
    def type(self) -> CodedValue | None:
        return typing.cast("CodedValue", self.find(f"{{{NAMESPACE}}}Type"))


class Range(common.ElementBase):
    """A range of decimal values with lower/upper bounds and step width."""

    @property
    def lower(self) -> str | None:
        return self.get("Lower")

    @property
    def upper(self) -> str | None:
        return self.get("Upper")

    @property
    def step_width(self) -> str | None:
        return self.get("StepWidth")

    @property
    def relative_accuracy(self) -> str | None:
        return self.get("RelativeAccuracy")

    @property
    def absolute_accuracy(self) -> str | None:
        return self.get("AbsoluteAccuracy")


class Measurement(common.ElementBase):
    """A measurement value with a unit."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def measured_value(self) -> decimal.Decimal:
        value = self.get("MeasuredValue")
        assert value is not None
        return decimal.Decimal(value)

    @property
    def measurement_unit(self) -> CodedValue:
        value = typing.cast("CodedValue | None", self.find(f"{{{NAMESPACE}}}MeasurementUnit"))
        # schema enforces presence
        assert value is not None
        return value


class PhysicalConnectorInfo(common.ElementBase):
    """Physical connector information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}PhysicalConnector"

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def labels(self) -> Sequence[LocalizedText]:
        return typing.cast("Sequence[LocalizedText]", self.findall(f"{{{NAMESPACE}}}Label"))

    @property
    def number(self) -> str | None:
        return self.get("Number")


class CalibrationResult(common.ElementBase):
    """Calibration result with a code and measurement value."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CalibrationResult"

    @property
    def code(self) -> CodedValue:
        result = typing.cast("CodedValue | None", self.find(f"{{{NAMESPACE}}}Code"))
        assert result is not None
        return result

    @property
    def value(self) -> Measurement:
        result = typing.cast("Measurement | None", self.find(f"{{{NAMESPACE}}}Value"))
        assert result is not None
        return result


class CalibrationDocumentation(common.ElementBase):
    """Documentation and results for a calibration step."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CalibrationDocumentation"

    @property
    def documentation(self) -> Sequence[LocalizedText]:
        return typing.cast("Sequence[LocalizedText]", self.findall(f"{{{NAMESPACE}}}Documentation"))

    @property
    def calibration_results(self) -> Sequence[CalibrationResult]:
        return typing.cast("Sequence[CalibrationResult]", self.findall(f"{{{NAMESPACE}}}CalibrationResult"))


class CalibrationInfo(common.ElementBase):
    """Calibration information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CalibrationInfo"

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def calibration_documentations(self) -> Sequence[CalibrationDocumentation]:
        return typing.cast(
            "Sequence[CalibrationDocumentation]", self.findall(f"{{{NAMESPACE}}}CalibrationDocumentation")
        )

    @property
    def component_calibration_state(self) -> str | None:
        return self.get("ComponentCalibrationState")

    @property
    def calibration_type(self) -> str | None:
        return self.get("Type")

    @property
    def time(self) -> str | None:
        return self.get("Time")


class ApprovedJurisdictions(common.ElementBase):
    """List of regions in which a device component is approved."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ApprovedJurisdictions"

    @property
    def approved_jurisdictions(self) -> Sequence[InstanceIdentifier]:
        return typing.cast("Sequence[InstanceIdentifier]", self.findall(f"{{{NAMESPACE}}}ApprovedJurisdiction"))


class OperatingJurisdiction(InstanceIdentifier):
    """Current region information configured for a component."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}OperatingJurisdiction"


class SystemSignalActivation(common.ElementBase):
    """Tuple of alert signal manifestation and activation."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SystemSignalActivation"

    @property
    def manifestation(self) -> str:
        value = self.get("Manifestation")
        assert value is not None
        return value

    @property
    def state(self) -> str:
        value = self.get("State")
        assert value is not None
        return value


class MetricRelation(common.ElementBase):
    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def code(self) -> CodedValue | None:
        return typing.cast("CodedValue | None", self.find(f"{{{NAMESPACE}}}Code"))

    @property
    def identification(self) -> InstanceIdentifier | None:
        return self.find_by_element(InstanceIdentifier)

    @property
    def kind(self) -> MetricRelationKind:
        value = self.get("Kind")
        assert value is not None
        return MetricRelationKind(value)

    @property
    def entries(self) -> Sequence[HandleRef]:
        entries = self.find(f"{{{NAMESPACE}}}Entries")
        assert entries is not None
        return [HandleRef(text) for text in entries.text.split()] if entries.text is not None else []


# ── MDIB root types ───────────────────────────────────────────────────────────────────────────────


class MdDescription(common.ElementBase):
    """Root container for the descriptive part of the MDIB."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MdDescription"

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def mds(self) -> Sequence[MdsDescriptor]:
        return self.findall_by_element(MdsDescriptor)

    @property
    def description_version(self) -> str | None:
        return self.get("DescriptionVersion")


class MdState(common.ElementBase):
    """Root container for the state part of the MDIB."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MdState"

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def states(self) -> Sequence[ABSTRACT_STATE]:
        return typing.cast("Sequence[ABSTRACT_STATE]", self.findall(f"{{{NAMESPACE}}}State"))

    @property
    def state_version(self) -> str | None:
        return self.get("StateVersion")


class Mdib(common.ElementBase):
    """Root object comprising MdDescription and MdState."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Mdib"

    @property
    def md_description(self) -> MdDescription | None:
        return self.find_by_element(MdDescription)

    @property
    def md_state(self) -> MdState | None:
        return self.find_by_element(MdState)

    @property
    def mdib_version(self) -> str | None:
        return self.get("MdibVersion")

    @property
    def sequence_id(self) -> str:
        value = self.get("SequenceId")
        assert value is not None
        return value

    @property
    def instance_id(self) -> str | None:
        return self.get("InstanceId")

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)


# ── Abstract base classes ─────────────────────────────────────────────────────────────────────────


class AbstractDescriptor(common.ElementBase):
    """Base for all descriptor types."""

    @property
    def handle(self) -> HandleRef:
        value = self.get("Handle")
        assert value is not None
        return HandleRef(value)

    @property
    def descriptor_version(self) -> int | None:
        value = self.get("DescriptorVersion")
        return int(value) if value is not None else None

    @property
    def safety_classification(self) -> SafetyClassification | None:
        value = self.get("SafetyClassification")
        return SafetyClassification(value) if value is not None else None

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def xsi_type(self) -> str:
        # TODO: return qname here?  # noqa: FIX002, TD002, TD003
        value = self.get("{http://www.w3.org/2001/XMLSchema-instance}type")
        assert value is not None
        return value

    @property
    def type(self) -> CodedValue | None:
        return typing.cast("CodedValue | None", self.find(f"{{{NAMESPACE}}}Type"))


class AbstractState(common.ElementBase):
    """Base for all state types."""

    @property
    def state_version(self) -> str | None:
        return self.get("StateVersion")

    @property
    def descriptor_handle(self) -> HandleRef:
        value = self.get("DescriptorHandle")
        assert value is not None
        return HandleRef(value)

    @property
    def descriptor_version(self) -> str | None:
        return self.get("DescriptorVersion")

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def xsi_type(self) -> str:
        # TODO: return qname here?  # noqa: FIX002, TD002, TD003
        value = self.get("{http://www.w3.org/2001/XMLSchema-instance}type")
        assert value is not None
        return value


class AbstractMultiState(AbstractState):
    """Base state with a handle for multi-state relationships."""

    @property
    def handle(self) -> Handle:
        value = self.get("Handle")
        assert value is not None
        return Handle(value)


# ── Device component descriptors ──────────────────────────────────────────────────────────────────


class UDI(common.ElementBase):
    """UDI fragment as defined by the FDA."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Udi"

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def device_identifier(self) -> str:
        node = self.find(f"{{{NAMESPACE}}}DeviceIdentifier")
        assert node is not None
        assert node.text is not None
        return node.text

    @property
    def human_readable_form(self) -> str:
        node = self.find(f"{{{NAMESPACE}}}HumanReadableForm")
        assert node is not None
        assert node.text is not None
        return node.text

    @property
    def issuer(self) -> InstanceIdentifier:
        node = self.find(f"{{{NAMESPACE}}}Issuer")
        assert isinstance(node, InstanceIdentifier)
        return node

    @property
    def jurisdiction(self) -> InstanceIdentifier | None:
        return typing.cast("InstanceIdentifier | None", self.find(f"{{{NAMESPACE}}}Jurisdiction"))


class MetaData(common.ElementBase):
    """Describes POC MEDICAL DEVICE meta data."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MetaData"

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def udis(self) -> Sequence[UDI]:
        return typing.cast("Sequence[UDI]", self.findall(f"{{{NAMESPACE}}}Udi"))

    @property
    def lot_number(self) -> str | None:
        node = self.find(f"{{{NAMESPACE}}}LotNumber")
        return node.text if node is not None else None

    @property
    def manufacturers(self) -> Sequence[LocalizedText]:
        return typing.cast("Sequence[LocalizedText]", self.findall(f"{{{NAMESPACE}}}Manufacturer"))

    @property
    def manufacture_date(self) -> str | None:
        # TODO: convert to xsd:datetime  # noqa: FIX002, TD002, TD003
        node = self.find(f"{{{NAMESPACE}}}ManufactureDate")
        return node.text if node is not None else None

    @property
    def expiration_date(self) -> str | None:
        # TODO: convert to xsd:datetime  # noqa: FIX002, TD002, TD003
        node = self.find(f"{{{NAMESPACE}}}ExpirationDate")
        return node.text if node is not None else None

    @property
    def model_names(self) -> Sequence[LocalizedText]:
        return typing.cast("Sequence[LocalizedText]", self.findall(f"{{{NAMESPACE}}}ModelName"))

    @property
    def model_number(self) -> str | None:
        node = self.find(f"{{{NAMESPACE}}}ModelNumber")
        return node.text if node is not None else None

    @property
    def serial_numbers(self) -> Sequence[str]:
        return [node.text for node in self.findall(f"{{{NAMESPACE}}}SerialNumber") if node.text is not None]


class AbstractDeviceComponentDescriptor(AbstractDescriptor):
    """Base descriptor for device components."""


class AbstractComplexDeviceComponentDescriptor(AbstractDeviceComponentDescriptor):
    """Descriptor with optional alert system and SCO."""


class MdsDescriptor(AbstractComplexDeviceComponentDescriptor):
    """Descriptor for a Medical Device System."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Mds"

    @property
    def meta_data(self) -> MetaData | None:
        return self.find_by_element(MetaData)

    @property
    def system_context(self) -> SystemContextDescriptor | None:
        return self.find_by_element(SystemContextDescriptor)

    @property
    def clock(self) -> ClockDescriptor | None:
        return self.find_by_element(ClockDescriptor)

    @property
    def battery(self) -> Sequence[BatteryDescriptor]:
        return self.findall_by_element(BatteryDescriptor)

    @property
    def approved_jurisdictions(self) -> ApprovedJurisdictions | None:
        return self.find_by_element(ApprovedJurisdictions)

    @property
    def vmd(self) -> Sequence[VmdDescriptor]:
        return self.findall_by_element(VmdDescriptor)


class VmdDescriptor(AbstractComplexDeviceComponentDescriptor):
    """Descriptor for a Virtual Medical Device."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Vmd"

    @property
    def approved_jurisdictions(self) -> ApprovedJurisdictions | None:
        return self.find_by_element(ApprovedJurisdictions)

    @property
    def channels(self) -> Sequence[ChannelDescriptor]:
        return self.findall_by_element(ChannelDescriptor)


class ChannelDescriptor(AbstractDeviceComponentDescriptor):
    """Descriptor for a channel grouping metrics."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Channel"

    @property
    def metrics(self) -> Sequence[AbstractMetricDescriptor]:
        return typing.cast("Sequence[AbstractMetricDescriptor]", self.findall(f"{{{NAMESPACE}}}Metric"))


class ClockDescriptor(AbstractDeviceComponentDescriptor):
    """Descriptor for clock/time capabilities."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Clock"


class BatteryDescriptor(AbstractDeviceComponentDescriptor):
    """Descriptor for battery information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Battery"


class ScoDescriptor(AbstractDeviceComponentDescriptor):
    """Descriptor for Service Control Object."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Sco"


# ── Device component states ───────────────────────────────────────────────────────────────────────


class AbstractDeviceComponentState(AbstractState):
    """Base state for device components."""

    @property
    def activation_state(self) -> ComponentActivation | None:
        value = self.get("ActivationState")
        return ComponentActivation(value) if value is not None else None

    @property
    def operating_hours(self) -> int | None:
        value = self.get("OperatingHours")
        return int(value) if value is not None else None

    @property
    def operating_cycles(self) -> int | None:
        value = self.get("OperatingCycles")
        return int(value) if value is not None else None

    @property
    def calibration_info(self) -> CalibrationInfo | None:
        return self.find_by_element(CalibrationInfo)

    @property
    def next_calibration(self) -> CalibrationInfo | None:
        return typing.cast("CalibrationInfo | None", self.find(f"{{{NAMESPACE}}}NextCalibration"))

    @property
    def physical_connector(self) -> PhysicalConnectorInfo | None:
        return self.find_by_element(PhysicalConnectorInfo)


class AbstractComplexDeviceComponentState(AbstractDeviceComponentState):
    """Base state for complex device components."""


class MdsState(AbstractComplexDeviceComponentState):
    """State of an MDS."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MdsState"

    @property
    def lang(self) -> str | None:
        return self.get("Lang")

    @property
    def operating_mode(self) -> str | None:
        return self.get("OperatingMode")

    @property
    def operating_jurisdiction(self) -> OperatingJurisdiction | None:
        return self.find_by_element(OperatingJurisdiction)


class VmdState(AbstractComplexDeviceComponentState):
    """State of a VMD."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}VmdState"

    @property
    def operating_jurisdiction(self) -> OperatingJurisdiction | None:
        return self.find_by_element(OperatingJurisdiction)


class ChannelState(AbstractDeviceComponentState):
    """State of a channel."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ChannelState"


class ClockState(AbstractDeviceComponentState):
    """State of a clock."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ClockState"

    @property
    def remote_sync(self) -> str:
        value = self.get("RemoteSync")
        assert value is not None
        return value

    @property
    def date_and_time(self) -> str | None:
        return self.get("DateAndTime")

    @property
    def accuracy(self) -> str | None:
        return self.get("Accuracy")

    @property
    def last_set(self) -> str | None:
        return self.get("LastSet")

    @property
    def time_zone(self) -> str | None:
        return self.get("TimeZone")

    @property
    def critical_use(self) -> str | None:
        return self.get("CriticalUse")


class BatteryState(AbstractDeviceComponentState):
    """State of a battery."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}BatteryState"

    @property
    def charge_status(self) -> str | None:
        return self.get("ChargeStatus")

    @property
    def charge_cycles(self) -> str | None:
        return self.get("ChargeCycles")


class ScoState(AbstractDeviceComponentState):
    """State of an SCO."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ScoState"

    @property
    def invocation_requested(self) -> str | None:
        return self.get("InvocationRequested")

    @property
    def invocation_required(self) -> str | None:
        return self.get("InvocationRequired")


class SystemContextState(AbstractDeviceComponentState):
    """State of system context."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SystemContextState"


# ── Alert descriptors ─────────────────────────────────────────────────────────────────────────────


class AbstractAlertDescriptor(AbstractDescriptor):
    """Base for alert descriptors."""


class AlertSystemDescriptor(AbstractAlertDescriptor):
    """Descriptor for an alert system."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}AlertSystem"

    @property
    def max_physiological_parallel_alarms(self) -> str | None:
        return self.get("MaxPhysiologicalParallelAlarms")

    @property
    def max_technical_parallel_alarms(self) -> str | None:
        return self.get("MaxTechnicalParallelAlarms")

    @property
    def self_check_period(self) -> str | None:
        return self.get("SelfCheckPeriod")


class AlertConditionDescriptor(AbstractAlertDescriptor):
    """Descriptor for an alert condition."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}AlertCondition"

    @property
    def kind(self) -> str:
        value = self.get("Kind")
        assert value is not None
        return value

    @property
    def priority(self) -> str:
        value = self.get("Priority")
        assert value is not None
        return value

    @property
    def default_condition_generation_delay(self) -> str | None:
        return self.get("DefaultConditionGenerationDelay")

    @property
    def can_escalate(self) -> str | None:
        return self.get("CanEscalate")

    @property
    def can_deescalate(self) -> str | None:
        return self.get("CanDeescalate")


class LimitAlertConditionDescriptor(AlertConditionDescriptor):
    """Descriptor for limit-based alert conditions."""

    @property
    def auto_limit_supported(self) -> str | None:
        return self.get("AutoLimitSupported")


class AlertSignalDescriptor(AbstractAlertDescriptor):
    """Descriptor for an alert signal."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}AlertSignal"

    @property
    def condition_signaled(self) -> str | None:
        return self.get("ConditionSignaled")

    @property
    def manifestation(self) -> str:
        value = self.get("Manifestation")
        assert value is not None
        return value

    @property
    def latching(self) -> str:
        value = self.get("Latching")
        assert value is not None
        return value

    @property
    def default_signal_generation_delay(self) -> str | None:
        return self.get("DefaultSignalGenerationDelay")

    @property
    def signal_delegation_supported(self) -> str | None:
        return self.get("SignalDelegationSupported")

    @property
    def acknowledgement_supported(self) -> str | None:
        return self.get("AcknowledgementSupported")

    @property
    def acknowledge_timeout(self) -> str | None:
        return self.get("AcknowledgeTimeout")


# ── Alert states ──────────────────────────────────────────────────────────────────────────────────


class AbstractAlertState(AbstractState):
    """Base for alert states."""

    @property
    def activation_state(self) -> str:
        value = self.get("ActivationState")
        assert value is not None
        return value


class AlertSystemState(AbstractAlertState):
    """State of an alert system."""

    @property
    def last_self_check(self) -> str | None:
        return self.get("LastSelfCheck")

    @property
    def self_check_count(self) -> str | None:
        return self.get("SelfCheckCount")

    @property
    def present_physiological_alarm_conditions(self) -> str | None:
        return self.get("PresentPhysiologicalAlarmConditions")

    @property
    def present_technical_alarm_conditions(self) -> str | None:
        return self.get("PresentTechnicalAlarmConditions")

    @property
    def system_signal_activations(self) -> Sequence[SystemSignalActivation]:
        return self.findall_by_element(SystemSignalActivation)


class AlertConditionState(AbstractAlertState):
    """State of an alert condition."""

    @property
    def actual_condition_generation_delay(self) -> str | None:
        return self.get("ActualConditionGenerationDelay")

    @property
    def actual_priority(self) -> str | None:
        return self.get("ActualPriority")

    @property
    def rank(self) -> str | None:
        return self.get("Rank")

    @property
    def presence(self) -> str | None:
        return self.get("Presence")

    @property
    def determination_time(self) -> str | None:
        return self.get("DeterminationTime")


class LimitAlertConditionState(AlertConditionState):
    """State of a limit alert condition."""

    @property
    def monitored_alert_limits(self) -> str:
        value = self.get("MonitoredAlertLimits")
        assert value is not None
        return value

    @property
    def auto_limit_activation_state(self) -> str | None:
        return self.get("AutoLimitActivationState")


class AlertSignalState(AbstractAlertState):
    """State of an alert signal."""

    @property
    def actual_signal_generation_delay(self) -> str | None:
        return self.get("ActualSignalGenerationDelay")

    @property
    def presence(self) -> str | None:
        return self.get("Presence")

    @property
    def location(self) -> str | None:
        return self.get("Location")

    @property
    def slot(self) -> str | None:
        return self.get("Slot")


# ── Metric value types ────────────────────────────────────────────────────────────────────────────


class AbstractMetricValue(common.ElementBase):
    """Abstract metric value."""

    @property
    def start_time(self) -> str | None:
        return self.get("StartTime")

    @property
    def stop_time(self) -> str | None:
        return self.get("StopTime")

    @property
    def determination_time(self) -> str | None:
        return self.get("DeterminationTime")


class NumericMetricValue(AbstractMetricValue):
    """Numeric metric value."""

    @property
    def value(self) -> decimal.Decimal | None:
        value = self.get("Value")
        return decimal.Decimal(value) if value else None


class StringMetricValue(AbstractMetricValue):
    """String metric value."""

    @property
    def value(self) -> str | None:
        return self.get("Value")


class ApplyAnnotation(common.ElementBase):
    """Annotations MAY only apply to specific values in the real-time sample array.

    The ApplyAnnotation set relates annotations to sample indices.
    If no ApplyAnnotation ELEMENT is provided all annotations are valid for all values in the context.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ApplyAnnotation"

    @property
    def annotation_index(self) -> int:
        value = self.get("AnnotationIndex")
        assert value is not None
        return int(value)

    @property
    def sample_index(self) -> int:
        value = self.get("SampleIndex")
        assert value is not None
        return int(value)


class SampleArrayValue(AbstractMetricValue):
    """Sample array value for waveforms."""

    @property
    def apply_annotations(self) -> Sequence[ApplyAnnotation]:
        return self.findall_by_element(ApplyAnnotation)

    @property
    def samples(self) -> str | None:
        return self.get("Samples")


# ── Metric descriptors ────────────────────────────────────────────────────────────────────────────


class AbstractMetricDescriptor(AbstractDescriptor):
    """Abstract descriptor for a metric."""

    @property
    def unit(self) -> CodedValue | None:
        return typing.cast("CodedValue | None", self.find(f"{{{NAMESPACE}}}Unit"))

    @property
    def body_site(self) -> Sequence[CodedValue]:
        return typing.cast("Sequence[CodedValue]", self.findall(f"{{{NAMESPACE}}}BodySite"))

    @property
    def relation(self) -> Sequence[MetricRelation]:
        return typing.cast("Sequence[MetricRelation]", self.findall(f"{{{NAMESPACE}}}Relation"))

    @property
    def metric_category(self) -> MetricCategory:
        value = self.get("MetricCategory")
        assert value is not None
        return MetricCategory(value)

    @property
    def derivation_method(self) -> str | None:
        value = self.get("DerivationMethod")
        return DerivationMethod(value) if value is not None else None

    @property
    def metric_availability(self) -> MetricAvailability:
        value = self.get("MetricAvailability")
        assert value is not None
        return MetricAvailability(value)

    @property
    def max_measurement_time(self) -> str | None:
        # TODO: implement duration type?  # noqa: FIX002, TD002, TD003
        return self.get("MaxMeasurementTime")

    @property
    def max_delay_time(self) -> str | None:
        # TODO: implement duration type?  # noqa: FIX002, TD002, TD003
        return self.get("MaxDelayTime")

    @property
    def determination_period(self) -> str | None:
        # TODO: implement duration type?  # noqa: FIX002, TD002, TD003
        return self.get("DeterminationPeriod")

    @property
    def life_time_period(self) -> str | None:
        # TODO: implement duration type?  # noqa: FIX002, TD002, TD003
        return self.get("LifeTimePeriod")

    @property
    def activation_duration(self) -> str | None:
        # TODO: implement duration type?  # noqa: FIX002, TD002, TD003
        return self.get("ActivationDuration")


class NumericMetricDescriptor(AbstractMetricDescriptor):
    """Descriptor for a numeric metric."""

    @property
    def resolution(self) -> decimal.Decimal:
        value = self.get("Resolution")
        assert value is not None
        return decimal.Decimal(value)

    @property
    def averaging_period(self) -> str | None:
        return self.get("AveragingPeriod")


class StringMetricDescriptor(AbstractMetricDescriptor):
    """Descriptor for a string metric."""


class AllowedValue(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}AllowedValue"

    @property
    def value(self) -> str:
        node = self.find(f"{{{NAMESPACE}}}Value")
        assert node is not None
        assert node.text is not None
        return node.text

    @property
    def type(self) -> CodedValue | None:
        return typing.cast("CodedValue | None", self.find(f"{{{NAMESPACE}}}Type"))

    @property
    def identification(self) -> InstanceIdentifier | None:
        return typing.cast("InstanceIdentifier | None", self.find(f"{{{NAMESPACE}}}Identification"))

    @property
    def characteristic(self) -> Measurement | None:
        return typing.cast("Measurement | None", self.find(f"{{{NAMESPACE}}}Characteristic"))


class EnumStringMetricDescriptor(StringMetricDescriptor):
    """Descriptor for an enumerated string metric."""

    @property
    def allowed_values(self) -> Sequence[AllowedValue]:
        return self.findall_by_element(AllowedValue)


class RealTimeSampleArrayMetricDescriptor(AbstractMetricDescriptor):
    """Descriptor for a real-time sample array."""

    @property
    def technical_ranges(self) -> Sequence[Range]:
        return typing.cast("Sequence[Range]", self.findall(f"{{{NAMESPACE}}}TechnicalRange"))

    @property
    def resolution(self) -> decimal.Decimal:
        value = self.get("Resolution")
        assert value is not None
        return decimal.Decimal(value)

    @property
    def sample_period(self) -> str:
        # TODO: convert to duration  # noqa: FIX002, TD002, TD003
        value = self.get("SamplePeriod")
        assert value is not None
        return value


class DistributionSampleArrayMetricDescriptor(AbstractMetricDescriptor):
    """Descriptor for a distribution sample array."""

    @property
    def technical_ranges(self) -> Sequence[Range]:
        return typing.cast("Sequence[Range]", self.findall(f"{{{NAMESPACE}}}TechnicalRange"))

    @property
    def domain_unit(self) -> CodedValue:
        node = self.find(f"{{{NAMESPACE}}}DomainUnit")
        assert isinstance(node, CodedValue)
        return node

    @property
    def distribution_range(self) -> Range:
        node = self.find(f"{{{NAMESPACE}}}DistributionRange")
        assert isinstance(node, Range)
        return node

    @property
    def resolution(self) -> decimal.Decimal:
        value = self.get("Resolution")
        assert value is not None
        return decimal.Decimal(value)


# ── Metric states ─────────────────────────────────────────────────────────────────────────────────


class AbstractMetricState(AbstractState):
    """Abstract state of a metric."""

    @property
    def activation_state(self) -> str | None:
        return self.get("ActivationState")

    @property
    def active_determination_period(self) -> str | None:
        return self.get("ActiveDeterminationPeriod")

    @property
    def life_time_period(self) -> str | None:
        return self.get("LifeTimePeriod")

    @property
    def physical_connector(self) -> PhysicalConnectorInfo | None:
        return self.find_by_element(PhysicalConnectorInfo)


class NumericMetricState(AbstractMetricState):
    """State of a numeric metric."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}NumericMetricState"

    @property
    def metric_value(self) -> NumericMetricValue | None:
        return typing.cast("NumericMetricValue | None", self.find(f"{{{NAMESPACE}}}MetricValue"))

    @property
    def physiological_range(self) -> Sequence[Range]:
        return typing.cast("Sequence[Range]", self.findall(f"{{{NAMESPACE}}}PhysiologicalRange"))

    @property
    def active_averaging_period(self) -> str | None:
        return self.get("ActiveAveragingPeriod")


class StringMetricState(AbstractMetricState):
    """State of a string metric."""

    TAG: str = f"{{{NAMESPACE}}}StringMetricState"

    @property
    def metric_value(self) -> StringMetricValue | None:
        return typing.cast("StringMetricValue | None", self.find(f"{{{NAMESPACE}}}MetricValue"))


class EnumStringMetricState(StringMetricState):
    """State of an enumerated string metric."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EnumStringMetricState"


class RealTimeSampleArrayMetricState(AbstractMetricState):
    """State of a real-time sample array."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}RealTimeSampleArrayMetricState"

    @property
    def metric_value(self) -> SampleArrayValue | None:
        return typing.cast("SampleArrayValue | None", self.find(f"{{{NAMESPACE}}}MetricValue"))

    @property
    def physiological_range(self) -> Sequence[Range]:
        return typing.cast("Sequence[Range]", self.findall(f"{{{NAMESPACE}}}PhysiologicalRange"))


class DistributionSampleArrayMetricState(AbstractMetricState):
    """State of a distribution sample array."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}DistributionSampleArrayMetricState"

    @property
    def metric_value(self) -> SampleArrayValue | None:
        return typing.cast("SampleArrayValue | None", self.find(f"{{{NAMESPACE}}}MetricValue"))

    @property
    def physiological_range(self) -> Sequence[Range]:
        return typing.cast("Sequence[Range]", self.findall(f"{{{NAMESPACE}}}PhysiologicalRange"))


# ── Operation descriptors ─────────────────────────────────────────────────────────────────────────


class AbstractOperationDescriptor(AbstractDescriptor):
    """Abstract descriptor for an operation."""

    @property
    def operation_target(self) -> str:
        value = self.get("OperationTarget")
        assert value is not None
        return value

    @property
    def max_time_to_finish(self) -> str | None:
        return self.get("MaxTimeToFinish")

    @property
    def invocation_effective_timeout(self) -> str | None:
        return self.get("InvocationEffectiveTimeout")

    @property
    def retriggerable(self) -> str | None:
        return self.get("Retriggerable")

    @property
    def access_level(self) -> str | None:
        return self.get("AccessLevel")


class AbstractSetStateOperationDescriptor(AbstractOperationDescriptor):
    """Abstract descriptor for set-state operations."""


class SetValueOperationDescriptor(AbstractOperationDescriptor):
    """Descriptor for a numeric set operation."""


class SetStringOperationDescriptor(AbstractOperationDescriptor):
    """Descriptor for a string set operation."""

    @property
    def max_length(self) -> str | None:
        return self.get("MaxLength")


class ActivateOperationDescriptor(AbstractSetStateOperationDescriptor):
    """Descriptor for an activate operation."""


class SetContextStateOperationDescriptor(AbstractSetStateOperationDescriptor):
    """Descriptor for a context state set operation."""


class SetMetricStateOperationDescriptor(AbstractSetStateOperationDescriptor):
    """Descriptor for a metric state set operation."""


class SetComponentStateOperationDescriptor(AbstractSetStateOperationDescriptor):
    """Descriptor for a component state set operation."""


class SetAlertStateOperationDescriptor(AbstractSetStateOperationDescriptor):
    """Descriptor for an alert state set operation."""


# ── Operation states ──────────────────────────────────────────────────────────────────────────────


class AbstractOperationState(AbstractState):
    """Base state for operations."""

    @property
    def operating_mode(self) -> str:
        value = self.get("OperatingMode")
        assert value is not None
        return value


class SetValueOperationState(AbstractOperationState):
    """State of a numeric set operation."""


class SetStringOperationState(AbstractOperationState):
    """State of a string set operation."""


class ActivateOperationState(AbstractOperationState):
    """State of an activate operation."""


class SetContextStateOperationState(AbstractOperationState):
    """State of a context state set operation."""


class SetMetricStateOperationState(AbstractOperationState):
    """State of a metric state set operation."""


class SetComponentStateOperationState(AbstractOperationState):
    """State of a component state set operation."""


class SetAlertStateOperationState(AbstractOperationState):
    """State of an alert state set operation."""


# ── Context descriptors ───────────────────────────────────────────────────────────────────────────


class SystemContextDescriptor(AbstractDeviceComponentDescriptor):
    """Descriptor for system context."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SystemContext"


class AbstractContextDescriptor(AbstractDescriptor):
    """Abstract base for context descriptors."""


class PatientContextDescriptor(AbstractContextDescriptor):
    """Context descriptor for patient-device association."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}PatientContext"


class LocationContextDescriptor(AbstractContextDescriptor):
    """Context descriptor for spatial position."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}LocationContext"


class WorkflowContextDescriptor(AbstractContextDescriptor):
    """Context descriptor for workflow information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}WorkflowContext"


class OperatorContextDescriptor(AbstractContextDescriptor):
    """Context descriptor for operator information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}OperatorContext"


class MeansContextDescriptor(AbstractContextDescriptor):
    """Context descriptor for utilized means."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MeansContext"


class EnsembleContextDescriptor(AbstractContextDescriptor):
    """Context descriptor for ensemble information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EnsembleContext"


# ── Context states ────────────────────────────────────────────────────────────────────────────────


class AbstractContextState(AbstractMultiState):
    """Base type for context states."""

    @property
    def validator(self) -> Sequence[InstanceIdentifier]:
        return typing.cast("Sequence[InstanceIdentifier]", self.findall(f"{{{NAMESPACE}}}Validator"))

    @property
    def identification(self) -> Sequence[InstanceIdentifier]:
        return typing.cast("Sequence[InstanceIdentifier]", self.findall(f"{{{NAMESPACE}}}Identification"))

    @property
    def context_association(self) -> ContextAssociation | None:
        value = self.get("ContextAssociation")
        return ContextAssociation(value) if value is not None else None

    @property
    def binding_mdib_version(self) -> int | None:
        value = self.get("BindingMdibVersion")
        return int(value) if value is not None else None

    @property
    def unbinding_mdib_version(self) -> int | None:
        value = self.get("UnbindingMdibVersion")
        return int(value) if value is not None else None

    @property
    def binding_start_time(self) -> int | None:
        value = self.get("BindingStartTime")
        return int(value) if value is not None else None

    @property
    def binding_end_time(self) -> int | None:
        value = self.get("BindingEndTime")
        return int(value) if value is not None else None


class BaseDemographics(common.ElementBase):
    """Basic demographic information."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def given_name(self) -> str | None:
        node = self.find(f"{{{NAMESPACE}}}Givenname")
        return node.text if node is not None else None

    @property
    def middle_names(self) -> Sequence[str]:
        return [node.text for node in self.findall(f"{{{NAMESPACE}}}Middlename") if node.text is not None]

    @property
    def family_name(self) -> str | None:
        node = self.find(f"{{{NAMESPACE}}}Familyname")
        return node.text if node is not None else None

    @property
    def birth_name(self) -> str | None:
        node = self.find(f"{{{NAMESPACE}}}Birthname")
        return node.text if node is not None else None

    @property
    def title(self) -> str | None:
        node = self.find(f"{{{NAMESPACE}}}Title")
        return node.text if node is not None else None


class PersonReference(common.ElementBase):
    """A reference to an identifiable person."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def identification(self) -> Sequence[InstanceIdentifier]:
        return self.findall_by_element(InstanceIdentifier)

    @property
    def name(self) -> BaseDemographics | None:
        return typing.cast("BaseDemographics | None", self.find(f"{{{NAMESPACE}}}Name"))


class PersonParticipation(PersonReference):
    """A person participating in a role."""

    @property
    def roles(self) -> Sequence[CodedValue]:
        return typing.cast("Sequence[CodedValue]", self.findall(f"{{{NAMESPACE}}}Role"))


class LocationDetail(common.ElementBase):
    """Details about a location."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}LocationDetail"

    @property
    def poc(self) -> str | None:
        return self.get("PoC")

    @property
    def room(self) -> str | None:
        return self.get("Room")

    @property
    def bed(self) -> str | None:
        return self.get("Bed")

    @property
    def facility(self) -> str | None:
        return self.get("Facility")

    @property
    def building(self) -> str | None:
        return self.get("Building")

    @property
    def floor(self) -> str | None:
        return self.get("Floor")


class LocationReference(common.ElementBase):
    """A reference to an identifiable location."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def identification(self) -> Sequence[InstanceIdentifier]:
        return self.findall_by_element(InstanceIdentifier)

    @property
    def location_detail(self) -> LocationDetail | None:
        return self.find_by_element(LocationDetail)


class PatientDemographicsCoreData(BaseDemographics):
    """Patient demographics data."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CoreData"

    @property
    def sex(self) -> Sex | None:
        node = self.find(f"{{{NAMESPACE}}}Sex")
        return Sex(node.text) if node is not None else None

    @property
    def patient_type(self) -> PatientType | None:
        node = self.find(f"{{{NAMESPACE}}}PatientType")
        return PatientType(node.text) if node is not None else None

    @property
    def date_of_birth(self) -> str | None:
        # TODO: parse date here?  # noqa: FIX002, TD002, TD003
        node = self.find(f"{{{NAMESPACE}}}DateOfBirth")
        return node.text if node is not None else None

    @property
    def height(self) -> Measurement | None:
        return typing.cast("Measurement | None", self.find(f"{{{NAMESPACE}}}Height"))

    @property
    def weight(self) -> Measurement | None:
        return typing.cast("Measurement | None", self.find(f"{{{NAMESPACE}}}Weight"))

    @property
    def race(self) -> CodedValue | None:
        return typing.cast("CodedValue | None", self.find(f"{{{NAMESPACE}}}Race"))


class NeonatalPatientDemographicsCoreData(PatientDemographicsCoreData):
    """Patient demographics for neonates."""

    @property
    def gestational_age(self) -> Measurement | None:
        return typing.cast("Measurement | None", self.find(f"{{{NAMESPACE}}}GestationalAge"))

    @property
    def birth_length(self) -> Measurement | None:
        return typing.cast("Measurement | None", self.find(f"{{{NAMESPACE}}}BirthLength"))

    @property
    def birth_weight(self) -> Measurement | None:
        return typing.cast("Measurement | None", self.find(f"{{{NAMESPACE}}}BirthWeight"))

    @property
    def head_circumference(self) -> Measurement | None:
        return typing.cast("Measurement | None", self.find(f"{{{NAMESPACE}}}HeadCircumference"))

    @property
    def mother(self) -> PersonReference | None:
        return typing.cast("PersonReference | None", self.find(f"{{{NAMESPACE}}}Mother"))


class PatientContextState(AbstractContextState):
    """Patient context information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}PatientContextState"

    @property
    def core_data(self) -> PatientDemographicsCoreData | None:
        return self.find_by_element(PatientDemographicsCoreData)


class LocationContextState(AbstractContextState):
    """Location context information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}LocationContextState"

    @property
    def location_detail(self) -> LocationDetail | None:
        return self.find_by_element(LocationDetail)


class WorkflowContextState(AbstractContextState):
    """Workflow step context information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}WorkflowContextState"


class OperatorContextState(AbstractContextState):
    """Operator context information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}OperatorContextState"


class MeansContextState(AbstractContextState):
    """Means context information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MeansContextState"


class EnsembleContextState(AbstractContextState):
    """Ensemble context information."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EnsembleContextState"


# ── Miscellaneous types ───────────────────────────────────────────────────────────────────────────


class CauseInfo(common.ElementBase):
    """Cause information for an alert condition."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CauseInfo"


class RemedyInfo(common.ElementBase):
    """Remedy information for a cause of an alert condition."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}RemedyInfo"


class ClinicalInfo(common.ElementBase):
    """Minimal clinical observation."""


class ImagingProcedure(common.ElementBase):
    """Identifiers for imaging procedures (DICOM/HL7)."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ImagingProcedure"


class OrderDetail(common.ElementBase):
    """Details of an order."""


class ContainmentTree(common.ElementBase):
    """Containment tree of an MDS."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ContainmentTree"

    @property
    def handle_ref(self) -> str | None:
        return self.get("HandleRef")

    @property
    def parent_handle_ref(self) -> str | None:
        return self.get("ParentHandleRef")

    @property
    def entry_type(self) -> str | None:
        return self.get("EntryType")

    @property
    def children_count(self) -> str | None:
        return self.get("ChildrenCount")


class ContainmentTreeEntry(common.ElementBase):
    """An entry in a containment tree."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Entry"

    @property
    def handle_ref(self) -> str | None:
        return self.get("HandleRef")

    @property
    def parent_handle_ref(self) -> str | None:
        return self.get("ParentHandleRef")

    @property
    def entry_type(self) -> str | None:
        return self.get("EntryType")

    @property
    def children_count(self) -> str | None:
        return self.get("ChildrenCount")


# ── Namespace lookup registration ─────────────────────────────────────────────────────────────────


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register BICEPS ParticipantModel elements in the given lookup."""
    ns = lookup.get_namespace(NAMESPACE)
    _register_structural_elements(ns)
    _register_common_elements(ns)
    _register_specific_elements(ns)


def _register_structural_elements(ns: lxml.etree._NamespaceRegistry) -> None:
    # MDIB root
    ns["Mdib"] = Mdib
    ns["MdDescription"] = MdDescription
    ns["MdState"] = MdState
    # Device component descriptors
    ns["Mds"] = MdsDescriptor
    ns["Vmd"] = VmdDescriptor
    ns["Channel"] = ChannelDescriptor
    ns["Clock"] = ClockDescriptor
    ns["Battery"] = BatteryDescriptor
    ns["Sco"] = ScoDescriptor
    ns["AlertSystem"] = AlertSystemDescriptor
    ns["AlertCondition"] = AlertConditionDescriptor
    ns["AlertSignal"] = AlertSignalDescriptor
    ns["Metric"] = AbstractMetricDescriptor
    ns["Operation"] = AbstractOperationDescriptor
    ns["State"] = AbstractState
    # Context descriptors
    ns["SystemContext"] = SystemContextDescriptor
    ns["PatientContext"] = PatientContextDescriptor
    ns["LocationContext"] = LocationContextDescriptor
    ns["EnsembleContext"] = EnsembleContextDescriptor
    ns["OperatorContext"] = OperatorContextDescriptor
    ns["WorkflowContext"] = WorkflowContextDescriptor
    ns["MeansContext"] = MeansContextDescriptor


def _register_common_elements(ns: lxml.etree._NamespaceRegistry) -> None:
    # Common elements -> CodedValue
    for name in (
        "Type",
        "Unit",
        "BodySite",
        "Race",
        "DomainUnit",
        "DangerCode",
        "Service",
        "Modality",
        "ProtocolCode",
        "TimeProtocol",
        "ActiveSyncProtocol",
        "SpecType",
        "Code",
        "ArgName",
        "Role",
        "Meaning",
        "MeasurementUnit",
        "Category",
    ):
        ns[name] = CodedValue
    # Common elements -> LocalizedText
    for name in (
        "CodingSystemName",
        "ConceptDescription",
        "Label",
        "Description",
        "Documentation",
        "Manufacturer",
        "ModelName",
    ):
        ns[name] = LocalizedText
    # Common elements -> InstanceIdentifier
    for name in (
        "Identification",
        "Validator",
        "ComponentId",
        "Issuer",
        "Jurisdiction",
        "AccessionIdentifier",
        "RequestedProcedureId",
        "StudyInstanceUid",
        "ScheduledProcedureStepId",
        "VisitNumber",
        "PlacerOrderNumber",
        "FillerOrderNumber",
        "ApprovedJurisdiction",
    ):
        ns[name] = InstanceIdentifier
    # Common elements -> Range
    for name in (
        "TechnicalRange",
        "PhysiologicalRange",
        "MaxLimits",
        "Limits",
        "AllowedRange",
        "DistributionRange",
        "Range",
    ):
        ns[name] = Range
    # Common elements -> Measurement
    for name in (
        "Height",
        "Weight",
        "GestationalAge",
        "BirthLength",
        "BirthWeight",
        "HeadCircumference",
        "CapacityFullCharge",
        "CapacitySpecified",
        "VolTAGeSpecified",
        "CapacityRemaining",
        "VolTAGe",
        "Current",
        "Temperature",
        "RemainingBatteryTime",
        "Characteristic",
        "Value",
    ):
        ns[name] = Measurement


def _register_specific_elements(ns: lxml.etree._NamespaceRegistry) -> None:  # noqa: PLR0915
    ns["PhysicalConnector"] = PhysicalConnectorInfo
    ns["CalibrationInfo"] = CalibrationInfo
    ns["NextCalibration"] = CalibrationInfo
    ns["CalibrationDocumentation"] = CalibrationDocumentation
    ns["CalibrationResult"] = CalibrationResult
    ns["Relation"] = MetricRelation
    ns["ApprovedJurisdictions"] = ApprovedJurisdictions
    ns["OperatingJurisdiction"] = OperatingJurisdiction
    ns["SystemSignalActivation"] = SystemSignalActivation
    ns["CauseInfo"] = CauseInfo
    ns["RemedyInfo"] = RemedyInfo
    ns["ImagingProcedure"] = ImagingProcedure
    ns["LocationDetail"] = LocationDetail
    ns["CoreData"] = PatientDemographicsCoreData
    ns["OperatorDetails"] = BaseDemographics
    ns["Name"] = BaseDemographics
    ns["Entry"] = ContainmentTreeEntry
    # Person/Location references
    ns["Patient"] = PersonReference
    ns["Mother"] = PersonReference
    ns["ReferringPhysician"] = PersonReference
    ns["RequestingPhysician"] = PersonReference
    ns["Performer"] = PersonParticipation
    ns["AssignedLocation"] = LocationReference
    # Metric values (polymorphic — base class + xsi:type dispatch)
    ns["MetricValue"] = AbstractMetricValue
    ns["NumericMetricValue"] = NumericMetricValue
    ns["StringMetricValue"] = StringMetricValue
    ns["SampleArrayValue"] = SampleArrayValue
    # Source element in AlertConditionDescriptor (HandleRef text element)
    ns["Source"] = common.ElementBase
    # ── xsi:type dispatch registrations ──────────────────────────────────────────
    # XSD type names differ from element names (e.g. element "Mds" has type "MdsDescriptor").
    # The _XsiTypeLookup resolves xsi:type="dom:MdsDescriptor" by looking up "MdsDescriptor"
    # in the pm namespace registry, so all concrete types must be registered here.
    #
    # Descriptor types
    ns["MdsDescriptor"] = MdsDescriptor
    ns["VmdDescriptor"] = VmdDescriptor
    ns["ChannelDescriptor"] = ChannelDescriptor
    ns["ClockDescriptor"] = ClockDescriptor
    ns["BatteryDescriptor"] = BatteryDescriptor
    ns["ScoDescriptor"] = ScoDescriptor
    ns["SystemContextDescriptor"] = SystemContextDescriptor
    ns["PatientContextDescriptor"] = PatientContextDescriptor
    ns["LocationContextDescriptor"] = LocationContextDescriptor
    ns["WorkflowContextDescriptor"] = WorkflowContextDescriptor
    ns["OperatorContextDescriptor"] = OperatorContextDescriptor
    ns["MeansContextDescriptor"] = MeansContextDescriptor
    ns["EnsembleContextDescriptor"] = EnsembleContextDescriptor
    ns["AlertSystemDescriptor"] = AlertSystemDescriptor
    ns["AlertConditionDescriptor"] = AlertConditionDescriptor
    ns["LimitAlertConditionDescriptor"] = LimitAlertConditionDescriptor
    ns["AlertSignalDescriptor"] = AlertSignalDescriptor
    ns["NumericMetricDescriptor"] = NumericMetricDescriptor
    ns["StringMetricDescriptor"] = StringMetricDescriptor
    ns["EnumStringMetricDescriptor"] = EnumStringMetricDescriptor
    ns["RealTimeSampleArrayMetricDescriptor"] = RealTimeSampleArrayMetricDescriptor
    ns["DistributionSampleArrayMetricDescriptor"] = DistributionSampleArrayMetricDescriptor
    ns["SetValueOperationDescriptor"] = SetValueOperationDescriptor
    ns["SetStringOperationDescriptor"] = SetStringOperationDescriptor
    ns["ActivateOperationDescriptor"] = ActivateOperationDescriptor
    ns["SetContextStateOperationDescriptor"] = SetContextStateOperationDescriptor
    ns["SetMetricStateOperationDescriptor"] = SetMetricStateOperationDescriptor
    ns["SetComponentStateOperationDescriptor"] = SetComponentStateOperationDescriptor
    ns["SetAlertStateOperationDescriptor"] = SetAlertStateOperationDescriptor
    # Device component states
    ns["MdsState"] = MdsState
    ns["VmdState"] = VmdState
    ns["ChannelState"] = ChannelState
    ns["ClockState"] = ClockState
    ns["BatteryState"] = BatteryState
    ns["ScoState"] = ScoState
    ns["SystemContextState"] = SystemContextState
    # Alert states
    ns["AlertSystemState"] = AlertSystemState
    ns["AlertConditionState"] = AlertConditionState
    ns["LimitAlertConditionState"] = LimitAlertConditionState
    ns["AlertSignalState"] = AlertSignalState
    # Metric states
    ns["NumericMetricState"] = NumericMetricState
    ns["StringMetricState"] = StringMetricState
    ns["EnumStringMetricState"] = EnumStringMetricState
    ns["RealTimeSampleArrayMetricState"] = RealTimeSampleArrayMetricState
    ns["DistributionSampleArrayMetricState"] = DistributionSampleArrayMetricState
    # Operation states
    ns["SetValueOperationState"] = SetValueOperationState
    ns["SetStringOperationState"] = SetStringOperationState
    ns["ActivateOperationState"] = ActivateOperationState
    ns["SetContextStateOperationState"] = SetContextStateOperationState
    ns["SetMetricStateOperationState"] = SetMetricStateOperationState
    ns["SetComponentStateOperationState"] = SetComponentStateOperationState
    ns["SetAlertStateOperationState"] = SetAlertStateOperationState
    # Context states
    ns["LocationContextState"] = LocationContextState
    ns["PatientContextState"] = PatientContextState
    ns["WorkflowContextState"] = WorkflowContextState
    ns["OperatorContextState"] = OperatorContextState
    ns["MeansContextState"] = MeansContextState
    ns["EnsembleContextState"] = EnsembleContextState
    # Polymorphic demographic data
    ns["NeonatalPatientDemographicsCoreData"] = NeonatalPatientDemographicsCoreData


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get BICEPS ParticipantModel parser."""
    ns_lookup = lxml.etree.ElementNamespaceClassLookup()
    extension.set_lookup(ns_lookup)
    set_lookup(ns_lookup)
    custom_lookup = element_class_lookup.BicepsElementClassLookup(ns_lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(custom_lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, get_parser())


type ABSTRACT_DEVICE_COMPONENT_DESCRIPTOR = (
    MdsDescriptor
    | VmdDescriptor
    | ChannelDescriptor
    | ClockDescriptor
    | BatteryDescriptor
    | ScoDescriptor
    | SystemContextDescriptor
)

type ABSTRACT_ALERT_DESCRIPTOR = AlertSystemDescriptor | AlertConditionDescriptor | AlertSignalDescriptor

type ABSTRACT_CONTEXT_DESCRIPTOR = (
    PatientContextDescriptor
    | LocationContextDescriptor
    | WorkflowContextDescriptor
    | OperatorContextDescriptor
    | MeansContextDescriptor
    | EnsembleContextDescriptor
)

type ABSTRACT_METRIC_DESCRIPTOR = (
    NumericMetricDescriptor
    | StringMetricDescriptor
    | EnumStringMetricDescriptor
    | RealTimeSampleArrayMetricDescriptor
    | DistributionSampleArrayMetricDescriptor
)

type ABSTRACT_OPERATION_DESCRIPTOR = (
    SetValueOperationDescriptor
    | SetStringOperationDescriptor
    | ActivateOperationDescriptor
    | SetContextStateOperationDescriptor
    | SetMetricStateOperationDescriptor
    | SetComponentStateOperationDescriptor
    | SetAlertStateOperationDescriptor
)

type ABSTRACT_DESCRIPTOR = (
    ABSTRACT_DEVICE_COMPONENT_DESCRIPTOR
    | ABSTRACT_ALERT_DESCRIPTOR
    | ABSTRACT_CONTEXT_DESCRIPTOR
    | ABSTRACT_METRIC_DESCRIPTOR
    | ABSTRACT_OPERATION_DESCRIPTOR
)

type ABSTRACT_CONTEXT_STATE = (
    PatientContextState
    | LocationContextState
    | WorkflowContextState
    | OperatorContextState
    | MeansContextState
    | EnsembleContextState
)

type ABSTRACT_METRIC_STATE = (
    NumericMetricState
    | StringMetricState
    | EnumStringMetricState
    | RealTimeSampleArrayMetricState
    | DistributionSampleArrayMetricState
)

type ABSTRACT_DEVICE_COMPONENT_STATE = (
    MdsState | VmdState | ChannelState | ClockState | BatteryState | ScoState | SystemContextState
)


type ABSTRACT_ALERT_STATE = AlertSystemState | AlertConditionState | LimitAlertConditionState | AlertSignalState


type ABSTRACT_OPERATION_STATE = (
    SetValueOperationState
    | SetStringOperationState
    | ActivateOperationState
    | SetContextStateOperationState
    | SetMetricStateOperationState
    | SetComponentStateOperationState
    | SetAlertStateOperationState
)

type ABSTRACT_STATE = (
    ABSTRACT_CONTEXT_STATE
    | ABSTRACT_ALERT_STATE
    | ABSTRACT_METRIC_STATE
    | ABSTRACT_OPERATION_STATE
    | ABSTRACT_DEVICE_COMPONENT_STATE
)
