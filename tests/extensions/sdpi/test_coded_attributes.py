"""Tests for the SDPi CodedAttributes extension model."""

from __future__ import annotations

import pathlib
import typing

import lxml.etree
import pytest

from sdc_xsd_model.core import biceps_msg, biceps_pm, extension
from sdc_xsd_model.extension_registry import ExtensionRegistry
from sdc_xsd_model.extensions import sdpi
from sdc_xsd_model.extensions.sdpi.coded_attributes_models import (
    NAMESPACE,
    CodedAttributes,
    CodedDecimalAttribute,
    CodedIntegerAttribute,
    CodedStringAttribute,
    MdcAttribute,
)

if typing.TYPE_CHECKING:
    from sdc_xsd_model.core import common

CODED_ATTR_CASES = [
    (CodedAttributes, "CodedAttributes"),
    (CodedStringAttribute, "CodedStringAttribute"),
    (CodedIntegerAttribute, "CodedIntegerAttribute"),
    (CodedDecimalAttribute, "CodedDecimalAttribute"),
    (MdcAttribute, "MdcAttribute"),
]

EXAMPLE_XML = pathlib.Path(__file__).parent / "coded_attribute_example.xml"


@pytest.fixture
def parser() -> lxml.etree.XMLParser:
    """Build a parser with the sdpi namespace class lookup."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    _registry = ExtensionRegistry()
    sdpi.register_coded_attributes(_registry)
    _registry.set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser()
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


@pytest.fixture
def biceps_parser() -> lxml.etree.XMLParser:
    """Build a full BICEPS parser with schema validation and all namespace lookups."""
    from sdc_xsd_model.parser import sdc_parser  # noqa: PLC0415

    _registry = ExtensionRegistry()
    sdpi.register_coded_attributes(_registry)
    return sdc_parser(_registry)


@pytest.mark.parametrize(("clazz", "local_name"), CODED_ATTR_CASES)
def test_default_tag(clazz: type[common.ElementBase], local_name: str) -> None:
    """Verify TAG follows the Clark notation {namespace}LocalName."""
    assert f"{{{NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in CODED_ATTR_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Verify that the sdpi namespace is registered in nsmap when constructing an element."""
    assert clazz(nsmap={"sdpi": NAMESPACE}).nsmap["sdpi"] == NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in CODED_ATTR_CASES])
def test_class_lookup(clazz: type[common.ElementBase], parser: lxml.etree.XMLParser) -> None:
    """Verify serialize-then-parse roundtrip resolves to the correct Python class."""
    element = clazz()
    xml = lxml.etree.tostring(element)
    parsed = lxml.etree.fromstring(xml, parser=parser)
    assert isinstance(parsed, clazz)


class TestExampleXml:
    """Tests that parse the coded_attribute_example.xml and verify its structure and values."""

    @pytest.fixture
    def tree(self, biceps_parser: lxml.etree.XMLParser) -> biceps_msg.GetMdibResponse:
        """Get the GetMdibResponse as fixture."""
        response = lxml.etree.parse(str(EXAMPLE_XML), parser=biceps_parser).getroot()
        assert isinstance(response, biceps_msg.GetMdibResponse)
        return response

    @pytest.fixture
    def coded_string(self, tree: biceps_msg.GetMdibResponse) -> CodedStringAttribute:
        """Get the CodedStringAttribute as fixture."""
        attribute = tree[0][0][0][0][0][0]
        assert isinstance(attribute, CodedStringAttribute)
        return attribute

    def test_extension_type(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the BICEPS tree structure down to the ext:Extension element."""
        mdib = tree.mdib
        assert isinstance(mdib, biceps_pm.Mdib)
        md_description = mdib.md_description
        assert isinstance(md_description, biceps_pm.MdDescription)

        assert len(md_description.mds) == 1
        mds = md_description.mds[0]
        ext = mds.extension
        assert isinstance(ext, extension.Extension)

    def test_coded_attributes_type(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the CodedAttributes container inside the Extension resolves to the correct class."""
        mds = tree[0][0][0]
        ext = mds.extension  # ty:ignore[unresolved-attribute]
        coded_attrs = ext.find_by_element(CodedAttributes)
        assert isinstance(coded_attrs, CodedAttributes)

    def test_coded_string_attribute_via_property(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify coded_string_attributes property returns the single CodedStringAttribute child."""
        coded_attrs = tree[0][0][0][0][0]
        assert isinstance(coded_attrs, CodedAttributes)
        string_attrs = coded_attrs.coded_string_attributes
        assert len(string_attrs) == 1
        assert isinstance(string_attrs[0], CodedStringAttribute)

    def test_coded_attributes_empty_collections(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify coded_integer_attributes and coded_decimal_attributes are empty in the example."""
        coded_attrs = tree[0][0][0][0][0]
        assert isinstance(coded_attrs, CodedAttributes)
        assert len(coded_attrs.coded_integer_attributes) == 0
        assert len(coded_attrs.coded_decimal_attributes) == 0

    def test_mdc_attribute_type(self, coded_string: CodedStringAttribute) -> None:
        """Verify the MdcAttribute child of CodedStringAttribute resolves to the correct class."""
        mdc_attr = coded_string.mdc_attribute
        assert isinstance(mdc_attr, MdcAttribute)

    def test_mdc_attribute_code(self, coded_string: CodedStringAttribute) -> None:
        """Verify the required Code attribute equals '67886'."""
        assert coded_string.mdc_attribute.code == "67886"

    def test_mdc_attribute_symbolic_code_name(self, coded_string: CodedStringAttribute) -> None:
        """Verify the optional SymbolicCodeName attribute equals 'MDC_ATTR_ID_SOFT'."""
        assert coded_string.mdc_attribute.symbolic_code_name == "MDC_ATTR_ID_SOFT"

    def test_mdc_attribute_coding_system_absent(self, coded_string: CodedStringAttribute) -> None:
        """Verify the optional CodingSystem attribute is None when omitted."""
        assert coded_string.mdc_attribute.coding_system is None

    def test_mdc_attribute_coding_system_version_absent(self, coded_string: CodedStringAttribute) -> None:
        """Verify the optional CodingSystemVersion attribute is None when omitted."""
        assert coded_string.mdc_attribute.coding_system_version is None

    def test_coded_string_attribute_value(self, coded_string: CodedStringAttribute) -> None:
        """Verify the CodedStringAttribute Value element text equals 'PatMon03'."""
        assert coded_string.value == "PatMon03"
