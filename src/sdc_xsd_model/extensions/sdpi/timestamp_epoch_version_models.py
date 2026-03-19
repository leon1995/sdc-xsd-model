"""SDPi Timestamp Epoch Version extension classes for BICEPS extensions."""

from __future__ import annotations

import typing

from sdc_xsd_model.core import biceps_pm, common, extension
from sdc_xsd_model.extension_registry import register_extension

if typing.TYPE_CHECKING:
    from collections.abc import Sequence


NAMESPACE: typing.Final[str] = "urn:oid:1.3.6.1.4.1.19376.1.6.2.10.1.1.1"
_EPOCH_TAG = f"{{{NAMESPACE}}}Epoch"


@register_extension
class EpochSupport(common.ElementBase):
    """Indicates the MDIB may include versioned timestamps.

    Attaches to pm:ClockDescriptor descriptor.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EpochSupport"

    @property
    def must_understand(self) -> bool | None:
        """Return the optional ext:MustUnderstand attribute."""
        raw = self.get(extension.MUST_UNDERSTAND_ATTR_TAG)
        return raw.lower() == "true" if raw is not None else None

    @property
    def version(self) -> int:
        """Return the Version attribute (default 1)."""
        raw = self.get("Version")
        if raw is None:
            return 1
        return int(raw)


class EpochVersion(int):
    """Time-stamp epoch version. The default version for any timestamp not versioned is the current epoch version."""


@register_extension
class Epoch(common.ElementBase):
    """Type defining a transition between epochs.

    Defines the step-change, which occurs at a single point in time, from the previous time-reference frame to the
    next time-reference frame. Adding this Offset to this Timestamp gives the point in time
    (to an unbiased external observer) when this time-step occurred in the next epoch's time-reference frame.

    For example, if device time advanced by 1 hour in epoch 0 at 10 am, there will be an Epoch entry for
    epoch version 0 with a timestamp of 10am and Offset of +1 hour. The equivalent time in epoch version 1
    will be 11 am.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Epoch"

    @property
    def must_understand(self) -> bool | None:
        """Return the optional ext:MustUnderstand attribute."""
        raw = self.get(extension.MUST_UNDERSTAND_ATTR_TAG)
        return raw.lower() == "true" if raw is not None else None

    @property
    def version(self) -> EpochVersion:
        value = self.get("Version")
        assert value is not None
        return EpochVersion(value)

    @property
    def timestamp(self) -> biceps_pm.Timestamp:
        value = self.get("Timestamp")
        assert value is not None
        return biceps_pm.Timestamp(value)

    @property
    def offset(self) -> str:
        value = self.get("Offset")
        assert value is not None
        # TODO: return duration  # noqa: FIX002, TD002, TD003
        return value


@register_extension
class Epochs(common.ElementBase):
    """Container for epoch transition entries.

    Attaches to pm:ClockState/ext:Extension.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Epochs"

    @property
    def epochs(self) -> Sequence[Epoch]:
        """Return all child Epoch elements (untyped to avoid ambiguity)."""
        return self.findall_by_element(Epoch)

    @property
    def version(self) -> EpochVersion:
        """Return the required current epoch Version attribute."""
        raw = self.get("Version")
        assert raw is not None
        return EpochVersion(raw)


@register_extension
class MetricEpoch(common.ElementBase):
    """Epoch versioning for pm:AbstractMetricValue timestamps."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MetricEpoch"

    @property
    def clock(self) -> str | None:
        """Return the optional Clock attribute (HandleRef)."""
        return self.get("Clock")

    @property
    def determination_time(self) -> EpochVersion | None:
        """Return the optional DeterminationTime epoch version."""
        raw = self.get("DeterminationTime")
        return EpochVersion(raw) if raw is not None else None

    @property
    def start_time(self) -> EpochVersion | None:
        """Return the optional StartTime epoch version."""
        raw = self.get("StartTime")
        return EpochVersion(raw) if raw is not None else None

    @property
    def stop_time(self) -> EpochVersion | None:
        """Return the optional StopTime epoch version."""
        raw = self.get("StopTime")
        return EpochVersion(raw) if raw is not None else None


@register_extension
class CalibrationInfoEpoch(common.ElementBase):
    """Epoch versioning for pm:CalibrationInfo timestamps."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CalibrationInfoEpoch"

    @property
    def clock(self) -> biceps_pm.HandleRef | None:
        """The clock versioned by this element."""
        value = self.get("Clock")
        return biceps_pm.HandleRef(value) if value is not None else None

    @property
    def time(self) -> EpochVersion | None:
        """Return the optional Time epoch version."""
        raw = self.get("Time")
        return EpochVersion(raw) if raw is not None else None


@register_extension
class AlertSystemStateEpoch(common.ElementBase):
    """Epoch versioning for pm:AlertSystemState timestamps."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}AlertSystemStateEpoch"

    @property
    def clock(self) -> biceps_pm.HandleRef | None:
        """The clock versioned by this element."""
        value = self.get("Clock")
        return biceps_pm.HandleRef(value) if value is not None else None

    @property
    def last_self_check(self) -> EpochVersion | None:
        """Return the optional LastSelfCheck epoch version."""
        raw = self.get("LastSelfCheck")
        return EpochVersion(raw) if raw is not None else None


@register_extension
class AlertConditionStateEpoch(common.ElementBase):
    """Epoch versioning for pm:AlertConditionState timestamps."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}AlertConditionStateEpoch"

    @property
    def clock(self) -> biceps_pm.HandleRef | None:
        """The clock versioned by this element."""
        value = self.get("Clock")
        return biceps_pm.HandleRef(value) if value is not None else None

    @property
    def determination_time(self) -> EpochVersion | None:
        """Return the optional DeterminationTime epoch version."""
        raw = self.get("DeterminationTime")
        return EpochVersion(raw) if raw is not None else None


@register_extension
class AbstractContextStateEpoch(common.ElementBase):
    """Epoch versioning for pm:AbstractContextState timestamps."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}AbstractContextStateEpoch"

    @property
    def clock(self) -> biceps_pm.HandleRef | None:
        """The clock versioned by this element."""
        value = self.get("Clock")
        return biceps_pm.HandleRef(value) if value is not None else None

    @property
    def binding_start_time(self) -> EpochVersion | None:
        """Return the optional BindingStartTime epoch version."""
        raw = self.get("BindingStartTime")
        return EpochVersion(raw) if raw is not None else None

    @property
    def binding_end_time(self) -> EpochVersion | None:
        """Return the optional BindingEndTime epoch version."""
        raw = self.get("BindingEndTime")
        return EpochVersion(raw) if raw is not None else None
