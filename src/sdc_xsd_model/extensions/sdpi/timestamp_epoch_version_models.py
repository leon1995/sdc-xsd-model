"""SDPi Timestamp Epoch Version extension classes for BICEPS extensions."""

from __future__ import annotations

import pathlib
import typing

from sdc_xsd_model import converter
from sdc_xsd_model.core import biceps_pm, common, extension

if typing.TYPE_CHECKING:
    import datetime
    from collections.abc import Sequence

PREFIX: typing.Final[str] = "sdpi"
NAMESPACE: typing.Final[str] = "urn:oid:1.3.6.1.4.1.19376.1.6.2.10.1.1.1"
SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.joinpath("timestamp_epoch_version_schema.xsd").absolute()
)


class EpochSupport(common.ElementBase):
    """Indicates the MDIB may include versioned timestamps.

    Attaches to pm:ClockDescriptor descriptor.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EpochSupport"

    @property
    def must_understand(self) -> bool | None:
        """``ext:MustUnderstand`` as written, or None when absent; see :attr:`must_understand_or_implied`."""
        return extension.must_understand_of(self)

    @property
    def must_understand_or_implied(self) -> bool:
        """``ext:MustUnderstand``; the schema states an absent attribute means ``false``."""
        return common.with_implied(self.must_understand, extension.IMPLIED_MUST_UNDERSTAND)

    @property
    def version(self) -> int:
        """Return the Version attribute (default 1)."""
        value = converter.to_int(self.get("Version", "1"))
        assert value is not None
        return value


class EpochVersion(int):
    """Time-stamp epoch version. The default version for any timestamp not versioned is the current epoch version."""

    __slots__ = ()


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
        """``ext:MustUnderstand`` as written, or None when absent; see :attr:`must_understand_or_implied`."""
        return extension.must_understand_of(self)

    @property
    def must_understand_or_implied(self) -> bool:
        """``ext:MustUnderstand``; the schema states an absent attribute means ``false``."""
        return common.with_implied(self.must_understand, extension.IMPLIED_MUST_UNDERSTAND)

    @property
    def version(self) -> EpochVersion:
        value = converter.to_int(self.get("Version"))
        assert value is not None
        return EpochVersion(value)

    @property
    def timestamp(self) -> biceps_pm.Timestamp:
        value = converter.to_int(self.get("Timestamp"))
        assert value is not None
        return biceps_pm.Timestamp(value)

    @property
    def offset(self) -> datetime.timedelta:
        """Return the required Offset, which may be negative to step the time reference backwards."""
        value = self.get("Offset")
        assert value is not None
        return converter.DurationConverter.deserialize(value, allow_negative=True)


class Epochs(common.ElementBase):
    """Container for epoch transition entries.

    Attaches to pm:ClockState/ext:Extension.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Epochs"

    @property
    def epochs(self) -> Sequence[Epoch]:
        """Return all child Epoch elements (untyped to avoid ambiguity)."""
        return_value = []
        # schema contains a bug which is hidden here. see https://github.com/IHE/DEV.SDPi/issues/520
        for epochs in self.findall_by_element(Epoch):
            return_value.extend(epochs.findall_by_element(Epoch))
        return return_value

    @property
    def version(self) -> EpochVersion:
        """Return the required current epoch Version attribute."""
        raw = converter.to_int(self.get("Version"))
        assert raw is not None
        return EpochVersion(raw)


class MetricEpoch(common.ElementBase):
    """Epoch versioning for pm:AbstractMetricValue timestamps."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MetricEpoch"

    @property
    def clock(self) -> biceps_pm.HandleRef | None:
        """Return the optional Clock attribute (HandleRef)."""
        value = self.get("Clock")
        return biceps_pm.HandleRef(value) if value is not None else None

    @property
    def determination_time(self) -> EpochVersion | None:
        """Return the optional DeterminationTime epoch version."""
        raw = converter.to_int(self.get("DeterminationTime"))
        return EpochVersion(raw) if raw is not None else None

    @property
    def start_time(self) -> EpochVersion | None:
        """Return the optional StartTime epoch version."""
        raw = converter.to_int(self.get("StartTime"))
        return EpochVersion(raw) if raw is not None else None

    @property
    def stop_time(self) -> EpochVersion | None:
        """Return the optional StopTime epoch version."""
        raw = converter.to_int(self.get("StopTime"))
        return EpochVersion(raw) if raw is not None else None


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
        raw = converter.to_int(self.get("Time"))
        return EpochVersion(raw) if raw is not None else None


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
        raw = converter.to_int(self.get("LastSelfCheck"))
        return EpochVersion(raw) if raw is not None else None


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
        raw = converter.to_int(self.get("DeterminationTime"))
        return EpochVersion(raw) if raw is not None else None


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
        raw = converter.to_int(self.get("BindingStartTime"))
        return EpochVersion(raw) if raw is not None else None

    @property
    def binding_end_time(self) -> EpochVersion | None:
        """Return the optional BindingEndTime epoch version."""
        raw = converter.to_int(self.get("BindingEndTime"))
        return EpochVersion(raw) if raw is not None else None
