"""Lxml models for BICEPS MessageModel elements from IEEE 11073-10207-2017."""

from __future__ import annotations

import decimal
import enum
import functools
import pathlib
import typing

import lxml.etree

from sdc_xsd_model.models import biceps_pm, common, extension
from sdc_xsd_model.models.extension import Extension

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

PREFIX: typing.Final[str] = "msg"
NAMESPACE: typing.Final[str] = "http://standards.ieee.org/downloads/11073/11073-10207-2017/message"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.parent.joinpath("xsd", "BICEPS_MessageModel.xsd").absolute()
)
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


# ── Simple type enums ──────────────────────────────────────────────────────────────────────────────


class InvocationState(enum.StrEnum):
    WAIT = "Wait"
    START = "Start"
    CNCLLD = "Cnclld"
    CNCLLD_MAN = "CnclldMan"
    FIN = "Fin"
    FIN_MOD = "FinMod"
    FAIL = "Fail"


class InvocationError(enum.StrEnum):
    UNSPEC = "Unspec"
    UNKN = "Unkn"
    INV = "Inv"
    OTH = "Oth"


class DescriptionModificationType(enum.StrEnum):
    CRT = "Crt"
    UPT = "Upt"
    DEL = "Del"


class RetrievabilityMethod(enum.StrEnum):
    GET = "Get"
    PER = "Per"
    EP = "Ep"
    STRM = "Strm"


class InvocationInfo(common.ElementBase):
    """Conveys information to describe a transaction operation."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}InvocationInfo"

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def transaction_id(self) -> int:
        el = self.find(f"{{{NAMESPACE}}}TransactionId")
        assert el is not None
        assert el.text is not None
        return int(el.text)

    @property
    def invocation_state(self) -> InvocationState:
        el = self.find(f"{{{NAMESPACE}}}InvocationState")
        assert el is not None
        assert el.text is not None
        return InvocationState(el.text)

    @property
    def invocation_error(self) -> InvocationError | None:
        el = self.find(f"{{{NAMESPACE}}}InvocationError")
        if el is None:
            return None
        return InvocationError(el.text)

    @property
    def invocation_error_messages(self) -> Sequence[biceps_pm.LocalizedText]:
        return typing.cast("Sequence[biceps_pm.LocalizedText]", self.findall(f"{{{NAMESPACE}}}InvocationErrorMessage"))


class AbstractGet(common.ElementBase):
    """Building block for any GET SERVICE request MESSAGE."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)


class AbstractGetResponse(common.ElementBase):
    """Building block for any GET SERVICE response MESSAGE."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

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


class AbstractReportPart(common.ElementBase):
    """Building block for a single report part in an AbstractReport."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def source_mds(self) -> str | None:
        el = self.find(f"{{{NAMESPACE}}}SourceMds")
        if el is None:
            return None
        return el.text


class AbstractReport(common.ElementBase):
    """Building block for any event MESSAGE delivered to an event sink."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def mdib_version(self) -> int | None:
        value = self.get("MdibVersion")
        return int(value) if value is not None else None

    @property
    def sequence_id(self) -> str:
        value = self.get("SequenceId")
        assert value is not None
        return value

    @property
    def instance_id(self) -> int | None:
        value = self.get("InstanceId")
        return int(value) if value is not None else None


class AbstractSet(common.ElementBase):
    """Building block for any SET SERVICE request MESSAGE."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def operation_handle_ref(self) -> biceps_pm.HandleRef:
        el = self.find(f"{{{NAMESPACE}}}OperationHandleRef")
        assert el is not None
        assert el.text is not None
        return biceps_pm.HandleRef(el.text)


class AbstractSetResponse(common.ElementBase):
    """Building block for any SET SERVICE response MESSAGE."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def invocation_info(self) -> InvocationInfo:
        el = self.find_by_element(InvocationInfo)
        assert el is not None
        return el

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


class VersionFrame(common.ElementBase):
    """A version frame with start and end."""

    @property
    def start(self) -> int | None:
        value = self.get("Start")
        if value is None:
            return value
        return int(value)

    @property
    def end(self) -> int | None:
        value = self.get("End")
        if value is None:
            return value
        return int(value)


class TimeFrame(common.ElementBase):
    """A time frame with start and end."""

    @property
    def start(self) -> int | None:
        value = self.get("Start")
        if value is None:
            return value
        return int(value)

    @property
    def end(self) -> int | None:
        value = self.get("End")
        if value is None:
            return value
        return int(value)


class RetrievabilityInfo(common.ElementBase):
    """Information on how to access a state."""

    @property
    def extension(self) -> Extension | None:
        return self.find_by_element(Extension)

    @property
    def method(self) -> RetrievabilityMethod:
        value = self.get("Method")
        assert value is not None
        return RetrievabilityMethod(value)

    @property
    def update_period(self) -> str | None:
        return self.get("UpdatePeriod")


class ReportPart(AbstractReportPart):
    """Unified ReportPart class for all report types.

    Since lxml maps one element name to one class per namespace, a single ReportPart
    class handles all report part variants. Properties return non-empty results only
    when the parent report type populates them.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ReportPart"

    @property
    def context_states(self) -> Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]", self.findall(f"{{{NAMESPACE}}}ContextState"))

    @property
    def metric_states(self) -> Sequence[biceps_pm.ABSTRACT_METRIC_STATE]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_METRIC_STATE]", self.findall(f"{{{NAMESPACE}}}MetricState"))

    @property
    def component_states(self) -> Sequence[biceps_pm.ABSTRACT_DEVICE_COMPONENT_STATE]:
        return typing.cast(
            "Sequence[biceps_pm.ABSTRACT_DEVICE_COMPONENT_STATE]", self.findall(f"{{{NAMESPACE}}}ComponentState")
        )

    @property
    def alert_states(self) -> Sequence[biceps_pm.ABSTRACT_ALERT_STATE]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_ALERT_STATE]", self.findall(f"{{{NAMESPACE}}}AlertState"))

    @property
    def operation_states(self) -> Sequence[biceps_pm.ABSTRACT_OPERATION_STATE]:
        return typing.cast(
            "Sequence[biceps_pm.ABSTRACT_OPERATION_STATE]", self.findall(f"{{{NAMESPACE}}}OperationState")
        )

    @property
    def invocation_info(self) -> InvocationInfo | None:
        return self.find_by_element(InvocationInfo)

    @property
    def invocation_source(self) -> biceps_pm.InstanceIdentifier | None:
        return typing.cast("biceps_pm.InstanceIdentifier | None", self.find(f"{{{NAMESPACE}}}InvocationSource"))

    @property
    def descriptors(self) -> Sequence[biceps_pm.ABSTRACT_DESCRIPTOR]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_DESCRIPTOR]", self.findall(f"{{{NAMESPACE}}}Descriptor"))

    @property
    def states(self) -> Sequence[biceps_pm.ABSTRACT_STATE]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_STATE]", self.findall(f"{{{NAMESPACE}}}State"))

    @property
    def error_code(self) -> biceps_pm.CodedValue | None:
        return typing.cast("biceps_pm.CodedValue | None", self.find(f"{{{NAMESPACE}}}ErrorCode"))

    @property
    def error_info(self) -> biceps_pm.LocalizedText | None:
        return typing.cast("biceps_pm.LocalizedText | None", self.find(f"{{{NAMESPACE}}}ErrorInfo"))

    @property
    def operation_handle_ref(self) -> str | None:
        return self.get("OperationHandleRef")

    @property
    def operation_target(self) -> str | None:
        return self.get("OperationTarget")

    @property
    def parent_descriptor(self) -> str | None:
        return self.get("ParentDescriptor")

    @property
    def modification_type(self) -> DescriptionModificationType | None:
        value = self.get("ModificationType")
        return DescriptionModificationType(value) if value is not None else None


# ── Abstract report subtypes ──────────────────────────────────────────────────────────────────────


class AbstractContextReport(AbstractReport):
    """Change report containing updated AbstractContextState instances."""

    @property
    def report_parts(self) -> Sequence[ReportPart]:
        return self.findall_by_element(ReportPart)


class AbstractMetricReport(AbstractReport):
    """Change report containing updated AbstractMetricState instances."""

    @property
    def report_parts(self) -> Sequence[ReportPart]:
        return self.findall_by_element(ReportPart)


class AbstractComponentReport(AbstractReport):
    """Change report containing updated AbstractComponentState instances."""

    @property
    def report_parts(self) -> Sequence[ReportPart]:
        return self.findall_by_element(ReportPart)


class AbstractAlertReport(AbstractReport):
    """Change report containing updated AbstractAlertState instances."""

    @property
    def report_parts(self) -> Sequence[ReportPart]:
        return self.findall_by_element(ReportPart)


class AbstractOperationalStateReport(AbstractReport):
    """Change report containing updated AbstractOperationState instances."""

    @property
    def report_parts(self) -> Sequence[ReportPart]:
        return self.findall_by_element(ReportPart)


# ── Get Section ────────────────────────────────────────────────────────────────────────────────────


class GetMdib(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetMdib"


class GetMdibResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetMdibResponse"

    @property
    def mdib(self) -> biceps_pm.Mdib | None:
        return self.find_by_element(biceps_pm.Mdib)


class GetMdDescription(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetMdDescription"

    @property
    def handle_refs(self) -> Sequence[biceps_pm.HandleRef]:
        return [biceps_pm.HandleRef(handle) for handle in self.findall(f"{{{NAMESPACE}}}HandleRef")]


class GetMdDescriptionResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetMdDescriptionResponse"

    @property
    def md_description(self) -> biceps_pm.MdDescription | None:
        return self.find_by_element(biceps_pm.MdDescription)


class GetMdState(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetMdState"

    @property
    def handle_refs(self) -> Sequence[biceps_pm.HandleRef]:
        return [biceps_pm.HandleRef(handle) for handle in self.findall(f"{{{NAMESPACE}}}HandleRef")]


class GetMdStateResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetMdStateResponse"

    @property
    def md_state(self) -> biceps_pm.MdState | None:
        return self.find_by_element(biceps_pm.MdState)


# ── Context Section ────────────────────────────────────────────────────────────────────────────────


class GetContextStates(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetContextStates"

    @property
    def handle_refs(self) -> Sequence[biceps_pm.HandleRef]:
        return [biceps_pm.HandleRef(handle) for handle in self.findall(f"{{{NAMESPACE}}}HandleRef")]


class GetContextStatesResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetContextStatesResponse"

    @property
    def context_states(self) -> Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]", self.findall(f"{{{NAMESPACE}}}ContextState"))


class GetContextStatesByIdentification(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetContextStatesByIdentification"

    @property
    def identifications(self) -> Sequence[biceps_pm.InstanceIdentifier]:
        return self.findall_by_element(biceps_pm.InstanceIdentifier)

    @property
    def context_type(self) -> str | None:
        # TODO: should return Qname instead of string  # noqa: FIX002, TD002, TD003
        return self.get("ContextType")


class GetContextStatesByIdentificationResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetContextStatesByIdentificationResponse"

    @property
    def context_states(self) -> Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]", self.findall(f"{{{NAMESPACE}}}ContextState"))


class GetContextStatesByFilter(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetContextStatesByFilter"

    @property
    def filters(self) -> Sequence[str]:
        # TODO: clarify whether this is correct  # noqa: FIX002, TD002, TD003
        return [node.text for node in self.findall(f"{{{NAMESPACE}}}Filter")]

    @property
    def context_type(self) -> str | None:
        # TODO: should return Qname instead of string  # noqa: FIX002, TD002, TD003
        return self.get("ContextType")


class GetContextStatesByFilterResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetContextStatesByFilterResponse"

    @property
    def context_states(self) -> Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]", self.findall(f"{{{NAMESPACE}}}ContextState"))


class SetContextState(AbstractSet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetContextState"

    @property
    def proposed_context_states(self) -> Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]:
        return typing.cast(
            "Sequence[biceps_pm.ABSTRACT_CONTEXT_STATE]", self.findall(f"{{{NAMESPACE}}}ProposedContextState")
        )


class SetContextStateResponse(AbstractSetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetContextStateResponse"


class PeriodicContextReport(AbstractContextReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}PeriodicContextReport"


class EpisodicContextReport(AbstractContextReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EpisodicContextReport"


# ── Localization Section ───────────────────────────────────────────────────────────────────────────


class GetLocalizedText(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetLocalizedText"

    @property
    def refs(self) -> Sequence[str]:
        # TODO: return str, proper type or just the element itself?  # noqa: FIX002, TD002, TD003
        return [node.text for node in self.findall(f"{{{NAMESPACE}}}Ref")]

    @property
    def version(self) -> str | None:
        # TODO: return str, proper type or just the element itself?  # noqa: FIX002, TD002, TD003
        node = self.find(f"{{{NAMESPACE}}}Version")
        return node.text if node else None

    @property
    def langs(self) -> Sequence[str]:
        # TODO: return str, proper type or just the element itself?  # noqa: FIX002, TD002, TD003
        return [node.text for node in self.findall(f"{{{NAMESPACE}}}Lang")]

    @property
    def text_widths(self) -> Sequence[biceps_pm.LocalizedTextWidth]:
        return [biceps_pm.LocalizedTextWidth(node.text) for node in self.findall(f"{{{NAMESPACE}}}TextWidth")]

    @property
    def number_of_lines(self) -> Sequence[int]:
        return [int(node.text) for node in self.findall(f"{{{NAMESPACE}}}NumberOfLines")]


class GetLocalizedTextResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetLocalizedTextResponse"

    @property
    def texts(self) -> Sequence[biceps_pm.LocalizedText]:
        return typing.cast("Sequence[biceps_pm.LocalizedText]", self.findall(f"{{{NAMESPACE}}}Text"))


class GetSupportedLanguages(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetSupportedLanguages"


class GetSupportedLanguagesResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetSupportedLanguagesResponse"

    @property
    def langs(self) -> Sequence[str]:
        # TODO: return str, proper type or just the element itself?  # noqa: FIX002, TD002, TD003
        return [node.text for node in self.findall(f"{{{NAMESPACE}}}Lang")]


# ── Archive Section ────────────────────────────────────────────────────────────────────────────────


class GetDescriptorsFromArchive(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetDescriptorsFromArchive"

    @property
    def descriptor_revisions(self) -> VersionFrame | None:
        return typing.cast("VersionFrame | None", self.find(f"{{{NAMESPACE}}}DescriptorRevisions"))

    @property
    def time_frame(self) -> TimeFrame | None:
        return typing.cast("TimeFrame | None", self.find(f"{{{NAMESPACE}}}TimeFrame"))

    @property
    def handles(self) -> Sequence[biceps_pm.HandleRef]:
        return [biceps_pm.HandleRef(node.text) for node in self.findall(f"{{{NAMESPACE}}}Handle")]


class GetDescriptorsFromArchiveResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetDescriptorsFromArchiveResponse"

    @property
    def descriptors(self) -> Sequence[biceps_pm.ABSTRACT_DESCRIPTOR]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_DESCRIPTOR]", self.findall(f"{{{NAMESPACE}}}Descriptor"))


class GetStatesFromArchive(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetStatesFromArchive"

    @property
    def state_revisions(self) -> VersionFrame | None:
        return typing.cast("VersionFrame | None", self.find(f"{{{NAMESPACE}}}StateRevisions"))

    @property
    def time_frame(self) -> TimeFrame | None:
        return typing.cast("TimeFrame | None", self.find(f"{{{NAMESPACE}}}TimeFrame"))

    @property
    def handles(self) -> Sequence[biceps_pm.HandleRef]:
        return [biceps_pm.HandleRef(node.text) for node in self.findall(f"{{{NAMESPACE}}}Handle")]


class GetStatesFromArchiveResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetStatesFromArchiveResponse"

    @property
    def states(self) -> Sequence[biceps_pm.ABSTRACT_STATE]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_STATE]", self.findall(f"{{{NAMESPACE}}}State"))


# ── Set Section ────────────────────────────────────────────────────────────────────────────────────


class SetValue(AbstractSet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetValue"

    @property
    def requested_numeric_value(self) -> decimal.Decimal | None:
        el = self.find(f"{{{NAMESPACE}}}RequestedNumericValue")
        if el is None:
            return None
        return decimal.Decimal(el.text)


class SetValueResponse(AbstractSetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetValueResponse"


class SetString(AbstractSet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetString"

    @property
    def requested_string_value(self) -> str | None:
        el = self.find(f"{{{NAMESPACE}}}RequestedStringValue")
        if el is None:
            return None
        return el.text


class SetStringResponse(AbstractSetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetStringResponse"


class Activate(AbstractSet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Activate"

    @property
    def arguments(self) -> Sequence[common.ElementBase]:
        # TODO: clarify what "xsd:anySimpleType" is  # noqa: FIX002, TD002, TD003
        return typing.cast("Sequence[common.ElementBase]", self.findall(f"{{{NAMESPACE}}}Argument"))


class ActivateResponse(AbstractSetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ActivateResponse"


class SetAlertState(AbstractSet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetAlertState"

    @property
    def proposed_alert_state(self) -> biceps_pm.ABSTRACT_ALERT_STATE | None:
        return typing.cast("biceps_pm.ABSTRACT_ALERT_STATE | None", self.find(f"{{{NAMESPACE}}}ProposedAlertState"))


class SetAlertStateResponse(AbstractSetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetAlertStateResponse"


class SetComponentState(AbstractSet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetComponentState"

    @property
    def proposed_component_states(self) -> Sequence[biceps_pm.ABSTRACT_DEVICE_COMPONENT_STATE]:
        return typing.cast(
            "Sequence[biceps_pm.ABSTRACT_DEVICE_COMPONENT_STATE]",
            self.findall(f"{{{NAMESPACE}}}ProposedComponentState"),
        )


class SetComponentStateResponse(AbstractSetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetComponentStateResponse"


class SetMetricState(AbstractSet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetMetricState"

    @property
    def proposed_metric_states(self) -> Sequence[biceps_pm.ABSTRACT_METRIC_STATE]:
        return typing.cast(
            "Sequence[biceps_pm.ABSTRACT_METRIC_STATE]", self.findall(f"{{{NAMESPACE}}}ProposedMetricState")
        )


class SetMetricStateResponse(AbstractSetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SetMetricStateResponse"


class OperationInvokedReport(AbstractReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}OperationInvokedReport"

    @property
    def report_parts(self) -> Sequence[ReportPart]:
        return typing.cast("Sequence[ReportPart]", self.findall(f"{{{NAMESPACE}}}ReportPart"))


# ── ContainmentTree Section ────────────────────────────────────────────────────────────────────────


class GetContainmentTree(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetContainmentTree"

    @property
    def handle_refs(self) -> Sequence[biceps_pm.HandleRef]:
        return [biceps_pm.HandleRef(node.text) for node in self.findall(f"{{{NAMESPACE}}}HandleRef")]


class GetContainmentTreeResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetContainmentTreeResponse"

    @property
    def containment_tree(self) -> biceps_pm.ContainmentTree | None:
        return self.find_by_element(biceps_pm.ContainmentTree)


class GetDescriptor(AbstractGet):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetDescriptor"

    @property
    def handle_refs(self) -> Sequence[biceps_pm.HandleRef]:
        return [biceps_pm.HandleRef(node.text) for node in self.findall(f"{{{NAMESPACE}}}HandleRef")]


class GetDescriptorResponse(AbstractGetResponse):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetDescriptorResponse"

    @property
    def descriptors(self) -> Sequence[biceps_pm.ABSTRACT_DESCRIPTOR]:
        return typing.cast("Sequence[biceps_pm.ABSTRACT_DESCRIPTOR]", self.findall(f"{{{NAMESPACE}}}Descriptor"))


# ── Report Section (simple extensions) ─────────────────────────────────────────────────────────────


class EpisodicMetricReport(AbstractMetricReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EpisodicMetricReport"


class PeriodicMetricReport(AbstractMetricReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}PeriodicMetricReport"


class EpisodicComponentReport(AbstractComponentReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EpisodicComponentReport"


class PeriodicComponentReport(AbstractComponentReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}PeriodicComponentReport"


class EpisodicAlertReport(AbstractAlertReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EpisodicAlertReport"


class PeriodicAlertReport(AbstractAlertReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}PeriodicAlertReport"


class EpisodicOperationalStateReport(AbstractOperationalStateReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EpisodicOperationalStateReport"


class PeriodicOperationalStateReport(AbstractOperationalStateReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}PeriodicOperationalStateReport"


class SystemErrorReport(AbstractReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SystemErrorReport"

    @property
    def report_parts(self) -> Sequence[ReportPart]:
        return typing.cast("Sequence[ReportPart]", self.findall(f"{{{NAMESPACE}}}ReportPart"))


class DescriptionModificationReport(AbstractReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}DescriptionModificationReport"

    @property
    def report_parts(self) -> Sequence[ReportPart]:
        return typing.cast("Sequence[ReportPart]", self.findall(f"{{{NAMESPACE}}}ReportPart"))


# ── Waveform Section ──────────────────────────────────────────────────────────────────────────────


class WaveformStream(AbstractReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}WaveformStream"

    @property
    def states(self) -> Sequence[biceps_pm.RealTimeSampleArrayMetricState]:
        return self.findall_by_element(biceps_pm.RealTimeSampleArrayMetricState)


class ObservedValueStream(AbstractReport):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ObservedValueStream"

    @property
    def values(self) -> Sequence[common.ElementBase]:
        # TODO: return proper type  # noqa: FIX002, TD002, TD003
        return typing.cast("Sequence[common.ElementBase]", self.findall(f"{{{NAMESPACE}}}Value"))


# ── Retrievability Section ─────────────────────────────────────────────────────────────────────────


class Retrievability(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Retrievability"

    @property
    def by(self) -> Sequence[RetrievabilityInfo]:
        # TODO: check correct type  # noqa: FIX002, TD002, TD003
        return typing.cast("Sequence[RetrievabilityInfo]", self.findall(f"{{{NAMESPACE}}}By"))


# ── Namespace lookup registration ─────────────────────────────────────────────────────────────────


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register BICEPS MessageModel elements in the given lookup."""
    ns = lookup.get_namespace(NAMESPACE)
    _register_get_context_elements(ns)
    _register_set_report_elements(ns)
    _register_child_elements(ns)


def _register_get_context_elements(ns: lxml.etree._NamespaceRegistry) -> None:
    # Get section
    ns["GetMdib"] = GetMdib
    ns["GetMdibResponse"] = GetMdibResponse
    ns["GetMdDescription"] = GetMdDescription
    ns["GetMdDescriptionResponse"] = GetMdDescriptionResponse
    ns["GetMdState"] = GetMdState
    ns["GetMdStateResponse"] = GetMdStateResponse
    # Context section
    ns["GetContextStates"] = GetContextStates
    ns["GetContextStatesResponse"] = GetContextStatesResponse
    ns["GetContextStatesByIdentification"] = GetContextStatesByIdentification
    ns["GetContextStatesByIdentificationResponse"] = GetContextStatesByIdentificationResponse
    ns["GetContextStatesByFilter"] = GetContextStatesByFilter
    ns["GetContextStatesByFilterResponse"] = GetContextStatesByFilterResponse
    ns["SetContextState"] = SetContextState
    ns["SetContextStateResponse"] = SetContextStateResponse
    ns["PeriodicContextReport"] = PeriodicContextReport
    ns["EpisodicContextReport"] = EpisodicContextReport
    # Localization section
    ns["GetLocalizedText"] = GetLocalizedText
    ns["GetLocalizedTextResponse"] = GetLocalizedTextResponse
    ns["GetSupportedLanguages"] = GetSupportedLanguages
    ns["GetSupportedLanguagesResponse"] = GetSupportedLanguagesResponse
    # Archive section
    ns["GetDescriptorsFromArchive"] = GetDescriptorsFromArchive
    ns["GetDescriptorsFromArchiveResponse"] = GetDescriptorsFromArchiveResponse
    ns["GetStatesFromArchive"] = GetStatesFromArchive
    ns["GetStatesFromArchiveResponse"] = GetStatesFromArchiveResponse
    # ContainmentTree section
    ns["GetContainmentTree"] = GetContainmentTree
    ns["GetContainmentTreeResponse"] = GetContainmentTreeResponse
    ns["GetDescriptor"] = GetDescriptor
    ns["GetDescriptorResponse"] = GetDescriptorResponse


def _register_set_report_elements(ns: lxml.etree._NamespaceRegistry) -> None:
    # Set section
    ns["SetValue"] = SetValue
    ns["SetValueResponse"] = SetValueResponse
    ns["SetString"] = SetString
    ns["SetStringResponse"] = SetStringResponse
    ns["Activate"] = Activate
    ns["ActivateResponse"] = ActivateResponse
    ns["SetAlertState"] = SetAlertState
    ns["SetAlertStateResponse"] = SetAlertStateResponse
    ns["SetComponentState"] = SetComponentState
    ns["SetComponentStateResponse"] = SetComponentStateResponse
    ns["SetMetricState"] = SetMetricState
    ns["SetMetricStateResponse"] = SetMetricStateResponse
    ns["OperationInvokedReport"] = OperationInvokedReport
    # Report section
    ns["EpisodicMetricReport"] = EpisodicMetricReport
    ns["PeriodicMetricReport"] = PeriodicMetricReport
    ns["EpisodicComponentReport"] = EpisodicComponentReport
    ns["PeriodicComponentReport"] = PeriodicComponentReport
    ns["EpisodicAlertReport"] = EpisodicAlertReport
    ns["PeriodicAlertReport"] = PeriodicAlertReport
    ns["EpisodicOperationalStateReport"] = EpisodicOperationalStateReport
    ns["PeriodicOperationalStateReport"] = PeriodicOperationalStateReport
    ns["SystemErrorReport"] = SystemErrorReport
    ns["DescriptionModificationReport"] = DescriptionModificationReport
    # Waveform section
    ns["WaveformStream"] = WaveformStream
    ns["ObservedValueStream"] = ObservedValueStream
    # Retrievability section
    ns["Retrievability"] = Retrievability

    ns["Text"] = biceps_pm.LocalizedText


def _register_child_elements(ns: lxml.etree._NamespaceRegistry) -> None:
    ns["ReportPart"] = ReportPart
    ns["InvocationInfo"] = InvocationInfo
    ns["By"] = RetrievabilityInfo
    # Polymorphic msg child elements — map to pm base classes so properties and
    # xsi:type dispatch work correctly (xsi:type resolves to concrete pm subclasses)
    ns["ContextState"] = biceps_pm.AbstractContextState
    ns["Descriptor"] = biceps_pm.AbstractDescriptor
    ns["State"] = biceps_pm.AbstractState
    ns["MetricState"] = biceps_pm.AbstractMetricState
    ns["ComponentState"] = biceps_pm.AbstractDeviceComponentState
    ns["AlertState"] = biceps_pm.AbstractAlertState
    ns["OperationState"] = biceps_pm.AbstractOperationState
    ns["ProposedContextState"] = biceps_pm.AbstractContextState
    ns["ProposedAlertState"] = biceps_pm.AbstractAlertState
    ns["ProposedComponentState"] = biceps_pm.AbstractDeviceComponentState
    ns["ProposedMetricState"] = biceps_pm.AbstractMetricState
    # Child elements that are simple text/type wrappers
    # msg-namespace child elements with known types
    ns["DescriptorRevisions"] = VersionFrame
    ns["StateRevisions"] = VersionFrame
    ns["TimeFrame"] = TimeFrame
    ns["ErrorCode"] = biceps_pm.CodedValue
    ns["ErrorInfo"] = biceps_pm.LocalizedText
    ns["InvocationSource"] = biceps_pm.InstanceIdentifier
    # Child elements that are simple text/type wrappers
    for name in (
        "TransactionId",
        "InvocationState",
        "InvocationError",
        "InvocationErrorMessage",
        "HandleRef",
        "SourceMds",
        "OperationHandleRef",
        "Filter",
        "Ref",
        "Version",
        "Lang",
        "TextWidth",
        "NumberOfLines",
        "RequestedNumericValue",
        "RequestedStringValue",
        "Handle",
        "ArgValue",
        "Value",
        "Argument",
    ):
        # Only register if not already registered as a specific class
        try:
            ns[name]
        except KeyError:
            ns[name] = common.ElementBase


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get BICEPS MessageModel parser."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    extension.set_lookup(lookup)
    biceps_pm.set_lookup(lookup)
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


_TAGGED_CLASSES: typing.Final[tuple[type[common.ElementBase], ...]] = (
    GetMdib,
    GetMdibResponse,
    GetMdDescription,
    GetMdDescriptionResponse,
    GetMdState,
    GetMdStateResponse,
    GetContextStates,
    GetContextStatesResponse,
    GetContextStatesByIdentification,
    GetContextStatesByIdentificationResponse,
    GetContextStatesByFilter,
    GetContextStatesByFilterResponse,
    SetContextState,
    SetContextStateResponse,
    PeriodicContextReport,
    EpisodicContextReport,
    GetLocalizedText,
    GetLocalizedTextResponse,
    GetSupportedLanguages,
    GetSupportedLanguagesResponse,
    GetDescriptorsFromArchive,
    GetDescriptorsFromArchiveResponse,
    GetStatesFromArchive,
    GetStatesFromArchiveResponse,
    SetValue,
    SetValueResponse,
    SetString,
    SetStringResponse,
    Activate,
    ActivateResponse,
    SetAlertState,
    SetAlertStateResponse,
    SetComponentState,
    SetComponentStateResponse,
    SetMetricState,
    SetMetricStateResponse,
    OperationInvokedReport,
    GetContainmentTree,
    GetContainmentTreeResponse,
    GetDescriptor,
    GetDescriptorResponse,
    EpisodicMetricReport,
    PeriodicMetricReport,
    EpisodicComponentReport,
    PeriodicComponentReport,
    EpisodicAlertReport,
    PeriodicAlertReport,
    EpisodicOperationalStateReport,
    PeriodicOperationalStateReport,
    SystemErrorReport,
    DescriptionModificationReport,
    WaveformStream,
    ObservedValueStream,
    Retrievability,
    ReportPart,
    InvocationInfo,
)

for cls in _TAGGED_CLASSES:
    cls.PARSER = get_parser()
