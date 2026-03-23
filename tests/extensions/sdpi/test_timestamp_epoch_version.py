"""Tests for the SDPi Timestamp Epoch Version extension models."""

from __future__ import annotations

import decimal
import pathlib
import typing

import lxml.etree
import pytest

from sdc_xsd_model.core import biceps_msg, biceps_pm, extension
from sdc_xsd_model.extension_registry import ExtensionRegistry
from sdc_xsd_model.extensions import sdpi
from sdc_xsd_model.extensions.sdpi.timestamp_epoch_version_models import (
    NAMESPACE,
    AbstractContextStateEpoch,
    AlertConditionStateEpoch,
    AlertSystemStateEpoch,
    CalibrationInfoEpoch,
    Epochs,
    EpochSupport,
    MetricEpoch,
)

if typing.TYPE_CHECKING:
    from sdc_xsd_model.core import common

TEV_CASES = [
    (EpochSupport, "EpochSupport"),
    (Epochs, "Epochs"),
    (MetricEpoch, "MetricEpoch"),
    (CalibrationInfoEpoch, "CalibrationInfoEpoch"),
    (AlertSystemStateEpoch, "AlertSystemStateEpoch"),
    (AlertConditionStateEpoch, "AlertConditionStateEpoch"),
    (AbstractContextStateEpoch, "AbstractContextStateEpoch"),
]

EXAMPLE_XML = pathlib.Path(__file__).parent / "timestamp_epoch_version_example.xml"


@pytest.fixture
def parser() -> lxml.etree.XMLParser:
    """Build a parser with the sdpi namespace class lookup."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    _registry = ExtensionRegistry()
    sdpi.register_timestamp_epoch_version(_registry)
    _registry.set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser()
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


@pytest.fixture
def biceps_parser() -> lxml.etree.XMLParser:
    """Build a full BICEPS parser with schema validation and all namespace lookups."""
    from sdc_xsd_model.parser import biceps_parser  # noqa: PLC0415

    _registry = ExtensionRegistry()
    sdpi.register_timestamp_epoch_version(_registry)
    return biceps_parser(_registry)


@pytest.mark.parametrize(("clazz", "local_name"), TEV_CASES)
def test_default_tag(clazz: type[common.ElementBase], local_name: str) -> None:
    """Verify TAG follows the Clark notation {namespace}LocalName."""
    assert f"{{{NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in TEV_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Verify that the sdpi namespace is registered in nsmap when constructing an element."""
    assert clazz(nsmap={"sdpi": NAMESPACE}).nsmap["sdpi"] == NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in TEV_CASES])
def test_class_lookup(clazz: type[common.ElementBase], parser: lxml.etree.XMLParser) -> None:
    """Verify serialize-then-parse roundtrip resolves to the correct Python class."""
    element = clazz()
    xml = lxml.etree.tostring(element)
    parsed = lxml.etree.fromstring(xml, parser=parser)
    assert isinstance(parsed, clazz)


class TestExampleXml:
    """Tests that parse the timestamp_epoch_version_example.xml and verify its structure and values."""

    @pytest.fixture
    def tree(self, biceps_parser: lxml.etree.XMLParser) -> biceps_msg.GetMdibResponse:
        """Get the GetMdibResponse as fixture."""
        response = lxml.etree.parse(str(EXAMPLE_XML), parser=biceps_parser).getroot()
        assert isinstance(response, biceps_msg.GetMdibResponse)
        return response

    @pytest.fixture
    def clock_descriptor(self, tree: biceps_msg.GetMdibResponse) -> biceps_pm.ClockDescriptor:
        """Get the ClockDescriptor as fixture."""
        mds = tree.mdib.md_description.mds[0]  # ty:ignore[unresolved-attribute]
        clock = mds.clock
        assert isinstance(clock, biceps_pm.ClockDescriptor)
        return clock

    @pytest.fixture
    def clock_state(self, tree: biceps_msg.GetMdibResponse) -> biceps_pm.ClockState:
        """Get the ClockState as fixture."""
        md_state = tree.mdib.md_state
        assert md_state is not None
        states = md_state.states
        clock_state = states[0]
        assert isinstance(clock_state, biceps_pm.ClockState)
        return clock_state

    @pytest.fixture
    def numeric_metric_state(self, tree: biceps_msg.GetMdibResponse) -> biceps_pm.NumericMetricState:
        """Get the first NumericMetricState as fixture."""
        md_state = tree.mdib.md_state
        assert md_state is not None
        numeric_metric_state = md_state.states[1]
        assert isinstance(numeric_metric_state, biceps_pm.NumericMetricState)
        return numeric_metric_state

    def test_biceps_tree_structure(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the BICEPS tree structure down to MdDescription with one Mds."""
        mdib = tree.mdib
        assert isinstance(mdib, biceps_pm.Mdib)
        md_description = mdib.md_description
        assert isinstance(md_description, biceps_pm.MdDescription)
        assert len(md_description.mds) == 1

    # ── ClockDescriptor / EpochSupport ─────────────────────────────────────

    def test_epoch_support_type(self, clock_descriptor: biceps_pm.ClockDescriptor) -> None:
        """Verify EpochSupport resolves to the correct class inside the ClockDescriptor extension."""
        ext = clock_descriptor.extension
        assert isinstance(ext, extension.Extension)
        epoch_support = ext.find_by_element(EpochSupport)
        assert isinstance(epoch_support, EpochSupport)

    def test_epoch_support_version(self, clock_descriptor: biceps_pm.ClockDescriptor) -> None:
        """Verify EpochSupport Version attribute equals 1."""
        ext = clock_descriptor.extension
        assert ext is not None
        epoch_support = ext.find_by_element(EpochSupport)
        assert epoch_support is not None
        assert epoch_support.version == 1

    def test_epoch_support_must_understand_absent(self, clock_descriptor: biceps_pm.ClockDescriptor) -> None:
        """Verify EpochSupport ext:MustUnderstand is None when not present."""
        ext = clock_descriptor.extension
        assert ext is not None
        epoch_support = ext.find_by_element(EpochSupport)
        assert epoch_support is not None
        assert epoch_support.must_understand is None

    # ── ClockState / Epochs ────────────────────────────────────────────────

    def test_clock_state_type(self, clock_state: biceps_pm.ClockState) -> None:
        """Verify xsi:type dispatch resolves pm:State to ClockState."""

    def test_clock_state_attributes(self, clock_state: biceps_pm.ClockState) -> None:
        """Verify ClockState attributes from the example."""
        assert clock_state.remote_sync == "1"
        assert clock_state.last_set == "1733317200000"
        assert clock_state.date_and_time == "1733328000000"

    def test_epochs_type(self, clock_state: biceps_pm.ClockState) -> None:
        """Verify Epochs resolves to the correct class inside the ClockState extension."""
        ext = clock_state.extension
        assert isinstance(ext, extension.Extension)
        epochs = ext.find_by_element(Epochs)
        assert isinstance(epochs, Epochs)

    def test_epochs_version(self, clock_state: biceps_pm.ClockState) -> None:
        """Verify Epochs Version attribute equals 5."""
        ext = clock_state.extension
        assert ext is not None
        epochs = ext.find_by_element(Epochs)
        assert epochs is not None
        assert epochs.version == 5

    def test_epoch_entries_count(self, clock_state: biceps_pm.ClockState) -> None:
        """Verify two Epoch child entries in the Epochs container."""
        ext = clock_state.extension
        assert ext is not None
        epochs = ext.find_by_element(Epochs)
        assert epochs is not None
        entries = epochs.epochs
        assert len(entries) == 2

    def test_epoch_entry_values(self, clock_state: biceps_pm.ClockState) -> None:
        """Verify attributes of the two Epoch child entries."""
        ext = clock_state.extension
        assert ext is not None
        epochs = ext.find_by_element(Epochs)
        assert epochs is not None
        entries = epochs.epochs

        # First entry: epoch 4
        assert entries[0].version == 4
        assert entries[0].timestamp == 1733317200000
        assert entries[0].offset == "-PT3H"

        # Second entry: epoch 3
        assert entries[1].version == 3
        assert entries[1].timestamp == 1733295600000
        assert entries[1].offset == "PT4H"

    # ── NumericMetricState m1 / MetricEpoch ────────────────────────────────

    def test_metric_epoch_type(self, numeric_metric_state: biceps_pm.NumericMetricState) -> None:
        """Verify MetricEpoch resolves to the correct class inside m1's MetricValue extension."""
        metric_value = numeric_metric_state.metric_value
        assert metric_value is not None
        ext = metric_value.find_by_element(extension.Extension)
        assert isinstance(ext, extension.Extension)
        metric_epoch = ext.find_by_element(MetricEpoch)
        assert isinstance(metric_epoch, MetricEpoch)

    def test_metric_epoch_attributes(self, numeric_metric_state: biceps_pm.NumericMetricState) -> None:
        """Verify MetricEpoch attributes: Clock, DeterminationTime, StartTime, StopTime."""
        metric_value = numeric_metric_state.metric_value
        assert isinstance(metric_value, biceps_pm.NumericMetricValue)
        ext = metric_value.find_by_element(extension.Extension)
        assert ext is not None
        metric_epoch = ext.find_by_element(MetricEpoch)
        assert metric_epoch is not None
        assert metric_epoch.clock == "clk"
        assert metric_epoch.determination_time == 3
        assert metric_epoch.start_time == 3
        assert metric_epoch.stop_time == 3

    def test_m1_metric_value_attributes(self, numeric_metric_state: biceps_pm.NumericMetricState) -> None:
        """Verify m1 MetricValue attributes from the example."""
        metric_value = numeric_metric_state.metric_value
        assert metric_value is not None
        assert isinstance(metric_value, biceps_pm.NumericMetricValue)
        assert metric_value.value == decimal.Decimal(0)
        assert metric_value.determination_time == "1733284800000"
        assert metric_value.start_time == "1733284799850"
        assert metric_value.stop_time == "1733284799950"

    # ── NumericMetricState m2 — no MetricEpoch ─────────────────────────────

    def test_m2_no_metric_epoch(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify m2 MetricValue has no ext:Extension (no MetricEpoch)."""
        md_state = tree.mdib.md_state
        assert md_state is not None
        m2_state = md_state.states[2]
        assert isinstance(m2_state, biceps_pm.NumericMetricState)
        metric_value = m2_state.metric_value
        assert metric_value is not None
        ext = metric_value.find_by_element(extension.Extension)
        assert ext is None

    # ── NumericMetricState m4 — no MetricEpoch, DeterminationTime > LastSet

    def test_m4_determination_time(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify m4 MetricValue DeterminationTime is greater than ClockState LastSet."""
        md_state = tree.mdib.md_state
        assert md_state is not None
        m4_state = md_state.states[4]
        assert isinstance(m4_state, biceps_pm.NumericMetricState)
        metric_value = m4_state.metric_value
        assert metric_value is not None
        assert metric_value.determination_time == "1733320800000"

    # ── State count ────────────────────────────────────────────────────────

    def test_state_count(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the total number of pm:State elements in MdState."""
        md_state = tree.mdib.md_state
        assert md_state is not None
        assert len(md_state.states) == 5
