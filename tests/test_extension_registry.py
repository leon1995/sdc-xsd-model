# ruff: noqa: PLR2004, SLF001
"""Tests for the simplified extension registration API."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib

import lxml.etree
import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from sdc_xsd_model.core import common
from sdc_xsd_model.extension_registry import ExtensionRegistry

TEST_NS = "http://test.example.com/registry"


@st.composite
def nc_name(draw: st.DrawFn) -> str:
    """Generate XML prefixes conforming to https://www.w3.org/TR/xml-names11/#NT-NCName.

    NOTE: A prefix is also a ncname https://www.w3.org/TR/xml-names11/#NT-Prefix
          A local part is also a ncname https://www.w3.org/TR/xml-names11/#NT-LocalPart
    """
    # https://www.w3.org/TR/xml-names11/#NT-NCNameStartChar
    name_start_chars = st.one_of(
        st.characters(
            whitelist_categories=(), whitelist_characters="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
        )
        | st.characters(min_codepoint=0xC0, max_codepoint=0xD6)
        | st.characters(min_codepoint=0xD8, max_codepoint=0xF6)
        | st.characters(min_codepoint=0xF8, max_codepoint=0x2FF)
        | st.characters(min_codepoint=0x370, max_codepoint=0x37D)
        | st.characters(min_codepoint=0x37F, max_codepoint=0x1FFF)
        | st.characters(min_codepoint=0x200C, max_codepoint=0x200D)
        | st.characters(min_codepoint=0x2070, max_codepoint=0x218F)
        | st.characters(min_codepoint=0x2C00, max_codepoint=0x2FEF)
        | st.characters(min_codepoint=0x3001, max_codepoint=0xD7FF)
        | st.characters(min_codepoint=0xF900, max_codepoint=0xFDCF)
        | st.characters(min_codepoint=0xFDF0, max_codepoint=0xFFFD)
        | st.characters(min_codepoint=0x10000, max_codepoint=0xEFFFF)
    )

    # https://www.w3.org/TR/xml11/#NT-NameChar
    name_chars = st.one_of(
        name_start_chars
        | st.characters(whitelist_categories=(), whitelist_characters="-.0123456789\u00b7")
        | st.characters(min_codepoint=0x0300, max_codepoint=0x036F)
        | st.characters(min_codepoint=0x203F, max_codepoint=0x2040)
    )
    start_char = draw(name_start_chars)
    rest = draw(st.text(alphabet=name_chars, min_size=0))
    return start_char + rest


def test_register_with_prefix_and_schema(tmp_path: pathlib.Path) -> None:
    """Register with explicit prefix and schema stores all fields in the registry."""
    schema_file = tmp_path / "test.xsd"
    schema_file.write_text("<xsd:schema xmlns:xsd='http://www.w3.org/2001/XMLSchema'/>")

    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS, prefix="treg", schema=schema_file)

    @decorator
    class Foo(common.ElementBase):
        TAG = f"{{{TEST_NS}}}Foo"

    assert TEST_NS in registry._namespaces
    info = registry._namespaces[TEST_NS]
    assert info.prefix == "treg"
    assert schema_file.absolute() in info.schemas
    assert info.classes["Foo"] is Foo


@given(local_part=nc_name())
def test_register_without_prefix(local_part: str) -> None:
    """Creating a factory without a prefix still registers classes."""
    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS)

    @decorator
    class Bar(common.ElementBase):
        TAG = f"{{{TEST_NS}}}{local_part}"

    assert local_part in registry._namespaces[TEST_NS].classes
    assert registry._namespaces[TEST_NS].classes[local_part] is Bar


@given(prefix=nc_name(), local_name_alpha=nc_name(), local_name_beta=nc_name())
def test_multiple_classes_same_namespace(prefix: str, local_name_alpha: str, local_name_beta: str) -> None:
    """Multiple classes in the same namespace are collected under one registry entry."""
    assume(local_name_alpha != local_name_beta)
    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS, prefix=prefix)

    @decorator
    class Alpha(common.ElementBase):
        TAG = f"{{{TEST_NS}}}{local_name_alpha}"

    @decorator
    class Beta(common.ElementBase):
        TAG = f"{{{TEST_NS}}}{local_name_beta}"

    info = registry._namespaces[TEST_NS]
    assert info.prefix == prefix
    assert len(info.classes) == 2
    assert info.classes[local_name_alpha] is Alpha
    assert info.classes[local_name_beta] is Beta


def test_register_invalid_tag_raises() -> None:
    """A TAG without Clark notation raises ValueError."""
    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS)
    with pytest.raises(ValueError, match="Clark notation"):

        @decorator
        class BadTag(common.ElementBase):
            TAG = "NoNamespace"


def test_register_duplicate_local_name_raises() -> None:
    """Registering the same local name twice in the same namespace raises RuntimeError."""
    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS)

    @decorator
    class Dup(common.ElementBase):
        TAG: str = f"{{{TEST_NS}}}Dup"

    with pytest.raises(RuntimeError, match=re.escape(f"{Dup.TAG} already registered")):

        @decorator
        class Dup2(common.ElementBase):
            TAG = Dup.TAG


def test_tag_namespace_mismatch_raises() -> None:
    """A class whose TAG namespace doesn't match the factory namespace raises ValueError."""
    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS)
    with pytest.raises(
        ValueError,
        match=re.escape(f"TAG namespace 'http://wrong.example.com' does not match factory namespace {TEST_NS!r}"),
    ):

        @decorator
        class Wrong(common.ElementBase):
            TAG = "{http://wrong.example.com}Wrong"


@given(prefix=nc_name())
def test_same_prefix_reregistration_is_idempotent(prefix: str) -> None:
    """Calling register_namespace twice with the same prefix does not raise."""
    registry = ExtensionRegistry()
    registry.register_extension(namespace=TEST_NS, prefix=prefix)
    decorator = registry.register_extension(namespace=TEST_NS, prefix=prefix)

    @decorator
    class Ok(common.ElementBase):
        TAG = f"{{{TEST_NS}}}Ok"

    assert registry._namespaces[TEST_NS].prefix == prefix
    assert Ok.__name__ in registry._namespaces[TEST_NS].classes


@given(first=nc_name(), second=nc_name())
def test_conflicting_prefix_raises(first: str, second: str) -> None:
    """Calling register_namespace with a different prefix for the same namespace raises ValueError."""
    assume(first != second)
    registry = ExtensionRegistry()
    registry.register_extension(namespace=TEST_NS, prefix=first)
    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Namespace {TEST_NS!r} already registered with prefix {first!r}, cannot re-register with {second!r}"
        ),
    ):
        registry.register_extension(namespace=TEST_NS, prefix=second)


@given(prefix=nc_name(), local_part=nc_name())
def test_set_lookup_registers_into_lookup(prefix: str, local_part: str) -> None:
    """set_lookup populates an ElementNamespaceClassLookup so parsed XML yields typed instances."""
    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS, prefix=prefix)

    @decorator
    class LookupTest(common.ElementBase):
        TAG = f"{{{TEST_NS}}}{local_part}"

    lookup = lxml.etree.ElementNamespaceClassLookup()
    registry.set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser()
    xml_parser.set_element_class_lookup(lookup)

    xml = f'<{prefix}:{local_part} xmlns:{prefix}="{TEST_NS}"/>'.encode()
    parsed = lxml.etree.fromstring(xml, parser=xml_parser)
    assert isinstance(parsed, LookupTest)


@given(prefix=nc_name(), local_part=nc_name())
def test_serialization_uses_registered_prefix_and_namespace(prefix: str, local_part: str) -> None:
    """Creating and serializing an element uses the registered prefix and namespace."""
    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS, prefix=prefix)

    @decorator
    class MyExtensionClass(common.ElementBase):
        TAG = f"{{{TEST_NS}}}{local_part}"

    lookup = lxml.etree.ElementNamespaceClassLookup()
    registry.set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser()
    xml_parser.set_element_class_lookup(lookup)

    elem = xml_parser.makeelement(MyExtensionClass.TAG)
    xml_unicode = lxml.etree.tostring(elem, encoding="unicode")

    assert f'<{prefix}:{local_part} xmlns:{prefix}="{TEST_NS}"/>' == xml_unicode

    parsed = lxml.etree.fromstring(xml_unicode, parser=xml_parser)
    assert isinstance(parsed, MyExtensionClass)
    assert parsed.tag == MyExtensionClass.TAG
    assert parsed.prefix == prefix
    assert parsed.nsmap[prefix] == TEST_NS


def test_get_schema_lines_returns_import_for_registered_schema(tmp_path: pathlib.Path) -> None:
    """get_schema_lines returns a xsd:import element for each namespace with a schema."""
    schema_file = tmp_path / "ext.xsd"
    schema_file.write_text("<xsd:schema xmlns:xsd='http://www.w3.org/2001/XMLSchema'/>")

    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS, prefix="ext", schema=schema_file)

    @decorator
    class ExtElem(common.ElementBase):
        TAG = f"{{{TEST_NS}}}ExtElem"

    lines = registry.get_schema_lines()
    assert len(lines) == 1
    assert lines[0] == f'<xsd:import namespace="{TEST_NS}" schemaLocation="{schema_file.absolute().as_uri()}"/>'


def test_get_schema_lines_excludes_entries_without_schema() -> None:
    """Namespaces registered without a schema are omitted from get_schema_lines."""
    registry = ExtensionRegistry()
    decorator = registry.register_extension(namespace=TEST_NS, prefix="noschema")

    @decorator
    class NoSchema(common.ElementBase):
        TAG = f"{{{TEST_NS}}}NoSchema"

    lines = registry.get_schema_lines()
    assert len(lines) == 0
