"""Tests for the SDPi EquipmentIdentifier extension model."""

from __future__ import annotations

import pathlib
import typing

import lxml.etree
import pytest

from sdc_xsd_model.core import biceps_msg, biceps_pm, extension
from sdc_xsd_model.extension_registry import ExtensionRegistry
from sdc_xsd_model.extensions import sdpi
from sdc_xsd_model.extensions.sdpi.equipment_identifier_models import (
    NAMESPACE,
    EquipmentIdentifier,
)

if typing.TYPE_CHECKING:
    from sdc_xsd_model.core import common

EQUIP_CASES = [
    (EquipmentIdentifier, "EquipmentIdentifier"),
]

EXAMPLE_XML = pathlib.Path(__file__).parent / "equipment_identifier_example.xml"


@pytest.fixture
def parser() -> lxml.etree.XMLParser:
    """Build a parser with the sdpi namespace class lookup."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    _registry = ExtensionRegistry()
    sdpi.register_equipment_identifier(_registry)
    _registry.set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser()
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


@pytest.fixture
def biceps_parser() -> lxml.etree.XMLParser:
    """Build a full BICEPS parser with schema validation and all namespace lookups."""
    from sdc_xsd_model.parser import biceps_parser  # noqa: PLC0415

    _registry = ExtensionRegistry()
    sdpi.register_equipment_identifier(_registry)
    return biceps_parser(_registry)


@pytest.mark.parametrize(("clazz", "local_name"), EQUIP_CASES)
def test_default_tag(clazz: type[common.ElementBase], local_name: str) -> None:
    """Verify TAG follows the Clark notation {namespace}LocalName."""
    assert f"{{{NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in EQUIP_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Verify that the sdpi namespace is registered in nsmap when constructing an element."""
    assert clazz(nsmap={"sdpi": NAMESPACE}).nsmap["sdpi"] == NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in EQUIP_CASES])
def test_class_lookup(clazz: type[common.ElementBase], parser: lxml.etree.XMLParser) -> None:
    """Verify serialize-then-parse roundtrip resolves to the correct Python class."""
    element = clazz()
    xml = lxml.etree.tostring(element)
    parsed = lxml.etree.fromstring(xml, parser=parser)
    assert isinstance(parsed, clazz)


class TestExampleXml:
    """Tests that parse the equipment_identifier_example.xml and verify its structure and values."""

    @pytest.fixture
    def tree(self, biceps_parser: lxml.etree.XMLParser) -> biceps_msg.GetMdibResponse:
        """Get the GetMdibResponse as fixture."""
        response = lxml.etree.parse(str(EXAMPLE_XML), parser=biceps_parser).getroot()
        assert isinstance(response, biceps_msg.GetMdibResponse)
        return response

    def test_biceps_tree_structure(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the BICEPS tree structure down to MdDescription with one Mds."""
        mdib = tree.mdib
        assert isinstance(mdib, biceps_pm.Mdib)
        md_description = mdib.md_description
        assert isinstance(md_description, biceps_pm.MdDescription)
        assert len(md_description.mds) == 1

    def test_mds_extension_type(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the Mds descriptor has an ext:Extension element."""
        mds = tree.mdib.md_description.mds[0]  # ty:ignore[unresolved-attribute]
        ext = mds.extension
        assert isinstance(ext, extension.Extension)

    def test_mds_equipment_identifier_value(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the Mds EquipmentIdentifier value matches the expected UUID URN."""
        mds = tree.mdib.md_description.mds[0]  # ty:ignore[unresolved-attribute]
        ext = mds.extension
        assert ext is not None
        equip_id = ext.find_by_element(EquipmentIdentifier)
        assert isinstance(equip_id, EquipmentIdentifier)
        assert equip_id.uri == "urn:uuid:9c057bb4-8d83-4fc1-9ad1-832ad543e2b2"

    def test_vmd_extension_type(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the Vmd descriptor has an ext:Extension element."""
        mds = tree.mdib.md_description.mds[0]  # ty:ignore[unresolved-attribute]
        vmds = mds.findall_by_element(biceps_pm.VmdDescriptor)
        assert len(vmds) == 1
        vmd = vmds[0]
        ext = vmd.extension
        assert isinstance(ext, extension.Extension)

    def test_vmd_equipment_identifier_value(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the Vmd EquipmentIdentifier value matches the expected UUID URN."""
        mds = tree.mdib.md_description.mds[0]  # ty:ignore[unresolved-attribute]
        vmd = mds.findall_by_element(biceps_pm.VmdDescriptor)[0]
        ext = vmd.extension
        assert ext is not None
        equip_id = ext.find_by_element(EquipmentIdentifier)
        assert isinstance(equip_id, EquipmentIdentifier)
        assert equip_id.uri == "urn:uuid:84051cdb-5353-47af-a916-b1f007e08ed8"

    def test_must_understand_absent(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify ext:MustUnderstand is None when not present in the example."""
        mds = tree.mdib.md_description.mds[0]  # ty:ignore[unresolved-attribute]
        ext = mds.extension
        assert ext is not None
        equip_id = ext.find_by_element(EquipmentIdentifier)
        assert isinstance(equip_id, EquipmentIdentifier)
        assert equip_id.must_understand is None

    def test_md_state_present(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the MdState element is present in the Mdib."""
        md_state = tree.mdib.md_state
        assert isinstance(md_state, biceps_pm.MdState)
