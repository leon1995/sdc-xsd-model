"""Tests for the BICEPS implied values.

BICEPS states defaults in ``xsd:documentation`` prose ("The implied value SHALL be ...") rather than as an XSD
``default``, so an absent optional attribute does not mean "unknown" -- it means the stated value. Each affected
property has an ``<name>_or_implied`` companion applying that default; see ``common.with_implied``.

The expected values here are extracted from the schema documentation rather than written out by hand, so a
constant that disagrees with the standard fails even though the code is self-consistent.
"""

from __future__ import annotations

import datetime
import enum
import re
import typing

import lxml.etree
import pytest

from sdc_xsd_model import converter
from sdc_xsd_model.core import biceps_msg, biceps_pm, common

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

XSD_NAMESPACE: typing.Final[str] = "http://www.w3.org/2001/XMLSchema"

# ``pm:InstanceIdentifier/@Root`` is the one implied value the schema does not state inline: its documentation
# defers to R0135, "A PARTICIPANT SHALL encode the instance identifier root by the URI 'biceps.uri.unk' if and
# only if its value is unknown" (BICEPS 5.2.4.2).
R0135_UNKNOWN_ROOT: typing.Final[str] = "biceps.uri.unk"

# 28 attribute declarations in the participant model and 3 in the message model state an implied value.
EXPECTED_IMPLIED_VALUE_COUNT: typing.Final[int] = 31

# (class, literal property, attribute, a wire value differing from the implied one)
CASES: typing.Final[Sequence[tuple[type[common.ElementBase], str, str, str]]] = [
    (biceps_pm.MdDescription, "description_version", "DescriptionVersion", "3"),
    (biceps_pm.MdState, "state_version", "StateVersion", "3"),
    (biceps_pm.Mdib, "mdib_version", "MdibVersion", "42"),
    (biceps_pm.AbstractState, "state_version", "StateVersion", "7"),
    (biceps_pm.AbstractState, "descriptor_version", "DescriptorVersion", "7"),
    (biceps_pm.CodedValue, "coding_system", "CodingSystem", "urn:oid:9.9.9"),
    (biceps_pm.InstanceIdentifier, "root", "Root", "urn:oid:1.2.3"),
    (biceps_pm.AbstractDescriptor, "descriptor_version", "DescriptorVersion", "5"),
    (biceps_pm.AbstractDescriptor, "safety_classification", "SafetyClassification", "MedA"),
    (biceps_pm.CalibrationInfo, "calibration_type", "Type", "Gain"),
    (biceps_pm.AbstractDeviceComponentState, "activation_state", "ActivationState", "Off"),
    (biceps_pm.MdsState, "lang", "Lang", "de"),
    (biceps_pm.MdsState, "operating_mode", "OperatingMode", "Dmo"),
    (
        biceps_pm.AlertConditionDescriptor,
        "default_condition_generation_delay",
        "DefaultConditionGenerationDelay",
        "PT5S",
    ),
    (biceps_pm.AlertConditionState, "presence", "Presence", "true"),
    (biceps_pm.LimitAlertConditionDescriptor, "auto_limit_supported", "AutoLimitSupported", "true"),
    (biceps_pm.AlertSignalDescriptor, "default_signal_generation_delay", "DefaultSignalGenerationDelay", "PT2S"),
    (biceps_pm.AlertSignalDescriptor, "signal_delegation_supported", "SignalDelegationSupported", "true"),
    (biceps_pm.AlertSignalDescriptor, "acknowledgement_supported", "AcknowledgementSupported", "true"),
    (biceps_pm.AlertSignalState, "presence", "Presence", "On"),
    (biceps_pm.AlertSignalState, "location", "Location", "Rem"),
    (biceps_pm.MetricQuality, "mode", "Mode", "Demo"),
    (biceps_pm.MetricQuality, "qi", "Qi", "0.5"),
    (biceps_pm.AbstractMetricState, "activation_state", "ActivationState", "StndBy"),
    (biceps_pm.AbstractOperationDescriptor, "retriggerable", "Retriggerable", "false"),
    (biceps_pm.AbstractOperationDescriptor, "access_level", "AccessLevel", "RO"),
    (biceps_pm.ClockState, "critical_use", "CriticalUse", "true"),
    (biceps_pm.AbstractContextState, "context_association", "ContextAssociation", "Assoc"),
    (biceps_msg.AbstractReport, "mdib_version", "MdibVersion", "11"),
    (biceps_msg.ReportPart, "modification_type", "ModificationType", "Crt"),
    (biceps_msg.RetrievabilityInfo, "update_period", "UpdatePeriod", "PT30S"),
]

IDS: typing.Final[list[str]] = [f"{cls.__name__}.{prop}" for cls, prop, _, _ in CASES]


def _owning_type(node: lxml.etree._Element) -> str | None:
    """Return the name of the nearest enclosing named ``complexType``, or ``None`` for an anonymous one."""
    for ancestor in node.iterancestors():
        if ancestor.tag == f"{{{XSD_NAMESPACE}}}complexType":
            return ancestor.get("name")
    return None


def _implied_from_schema(attribute: str, owner: str) -> str:
    """Return the implied value the BICEPS schemas state for *owner*/*attribute*, read from ``xsd:documentation``.

    An attribute name may be declared on several types, sometimes with *different* implied values: ``@Presence``
    is ``"false"`` on ``pm:AlertConditionState`` (a boolean) but ``"Off"`` on ``pm:AlertSignalState`` (an
    ``AlertSignalPresence``). So declarations are narrowed by owning type when that disambiguates, and otherwise
    every declaration of the name must agree -- asserted, not assumed.
    """
    if attribute == "Root":
        return R0135_UNKNOWN_ROOT
    found: dict[str | None, set[str]] = {}
    for module in (biceps_pm, biceps_msg):
        tree = lxml.etree.parse(str(module.SCHEMA_PATH))
        for node in tree.iter(f"{{{XSD_NAMESPACE}}}attribute"):
            if node.get("name") != attribute:
                continue
            documentation = " ".join(doc.text or "" for doc in node.iter(f"{{{XSD_NAMESPACE}}}documentation"))
            match = re.search(r'implied value[^."]*?SHALL be\s*"([^"]+)"', documentation, re.IGNORECASE | re.DOTALL)
            if match is not None:
                found.setdefault(_owning_type(node), set()).add(match.group(1))
    assert found, f"no implied value stated for @{attribute} in either schema"
    # The Python class name matches the XSD type name wherever the type is named; MetricQuality and ReportPart
    # are anonymous inline types, which fall through to the agreement check below.
    if owner in found and len(found[owner]) == 1:
        return found[owner].pop()
    values = {value for group in found.values() for value in group}
    assert len(values) == 1, f"@{attribute} states differing implied values by owner: {found}"
    return values.pop()


def _lexical(value: object) -> str:
    """Render a Python value back into the XSD lexical form the schema documentation quotes."""
    if isinstance(value, bool):
        # Must precede the int branch: bool is a subclass of int.
        return "true" if value else "false"
    if isinstance(value, enum.Enum):
        return str(value.value)
    if isinstance(value, datetime.timedelta):
        return converter.DurationConverter.serialize(value)
    return str(value)


@pytest.mark.parametrize(("clazz", "prop", "attribute", "wire_value"), CASES, ids=IDS)
def test_absent_attribute_reads_as_the_implied_value(
    clazz: type[common.ElementBase],
    prop: str,
    attribute: str,
    wire_value: str,  # noqa: ARG001 - only the absent case matters here
) -> None:
    """With the attribute absent, the literal property is None and the companion returns the spec default."""
    element = clazz()
    assert getattr(element, prop) is None
    assert _lexical(getattr(element, f"{prop}_or_implied")) == _implied_from_schema(attribute, clazz.__name__)


@pytest.mark.parametrize(("clazz", "prop", "attribute", "wire_value"), CASES, ids=IDS)
def test_present_attribute_wins_over_the_implied_value(
    clazz: type[common.ElementBase],
    prop: str,
    attribute: str,
    wire_value: str,
) -> None:
    """A value on the wire is returned as-is, never replaced by the implied one."""
    element = clazz(attrib={attribute: wire_value})
    assert _lexical(getattr(element, f"{prop}_or_implied")) == wire_value
    assert getattr(element, prop) is not None
    assert attribute != "Root" or getattr(element, prop) != R0135_UNKNOWN_ROOT


@pytest.mark.parametrize(
    ("clazz", "prop", "attribute", "wire_value", "expected"),
    [
        # `self.x or IMPLIED` would invert each of these, because the wire value is falsy.
        (biceps_pm.AbstractOperationDescriptor, "retriggerable", "Retriggerable", "false", False),
        (biceps_pm.MetricQuality, "qi", "Qi", "0", 0),
        (biceps_pm.AlertConditionState, "presence", "Presence", "false", False),
        (biceps_pm.ClockState, "critical_use", "CriticalUse", "false", False),
        (biceps_pm.Mdib, "mdib_version", "MdibVersion", "0", 0),
        (
            biceps_pm.AlertSignalDescriptor,
            "default_signal_generation_delay",
            "DefaultSignalGenerationDelay",
            "PT0S",
            datetime.timedelta(0),
        ),
    ],
)
def test_falsy_wire_value_is_not_replaced_by_the_implied_value(
    clazz: type[common.ElementBase],
    prop: str,
    attribute: str,
    wire_value: str,
    expected: object,
) -> None:
    """A falsy value present on the wire must survive.

    ``@Qi="0"`` is the worst quality and ``@Retriggerable="false"`` disables retriggering; had these been
    written as ``value or implied`` they would read back as the implied ``1`` and ``True`` -- inverting the
    meaning of the message. This is why ``common.with_implied`` tests ``is None``.
    """
    element = clazz(attrib={attribute: wire_value})
    assert getattr(element, f"{prop}_or_implied") == expected


def test_every_schema_stated_implied_value_has_an_accessor() -> None:
    """Guard against a new implied value appearing in a schema with no ``_or_implied`` accessor to match.

    Counting rather than naming, because the attribute-to-class mapping is what ``CASES`` already encodes; this
    only has to notice when the schemas grow one.
    """
    stated = 0
    for module in (biceps_pm, biceps_msg):
        tree = lxml.etree.parse(str(module.SCHEMA_PATH))
        for node in tree.iter(f"{{{XSD_NAMESPACE}}}attribute"):
            documentation = " ".join(doc.text or "" for doc in node.iter(f"{{{XSD_NAMESPACE}}}documentation"))
            if "implied value" in documentation.lower():
                stated += 1
    # @StateVersion, @DescriptorVersion, @ActivationState and @Presence are each stated on two types, so the
    # declaration count and the case count line up one-to-one.
    assert stated == len(CASES) == EXPECTED_IMPLIED_VALUE_COUNT
