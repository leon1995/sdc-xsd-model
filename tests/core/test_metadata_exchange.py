"""Tests for the metadata exchange model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.core import addressing, common, metadata_exchange

METADATA_EXCHANGE_CASES = [
    (metadata_exchange.Dialect, "Dialect"),
    (metadata_exchange.Identifier, "Identifier"),
    (metadata_exchange.GetMetadata, "GetMetadata"),
    (metadata_exchange.Location, "Location"),
    (metadata_exchange.MetadataReference, "MetadataReference"),
    (metadata_exchange.MetadataSection, "MetadataSection"),
    (metadata_exchange.Metadata, "Metadata"),
]


@pytest.mark.parametrize(("clazz", "local_name"), METADATA_EXCHANGE_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure metadata exchange classes expose the expected TAG value."""
    assert f"{{{metadata_exchange.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in METADATA_EXCHANGE_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure metadata exchange classes register the expected namespace."""
    assert clazz().nsmap[metadata_exchange.PREFIX] == metadata_exchange.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in METADATA_EXCHANGE_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure metadata exchange classes can be serialized and deserialized correctly."""
    element, target_tag = _create_mex_element(clazz)
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=clazz.PARSER)
    if target_tag is not None:
        parsed_element = parsed_element.find(target_tag)
    assert isinstance(parsed_element, clazz)


def _create_mex_element(  # noqa: PLR0911
    clazz: type[common.ElementBase],
) -> tuple[common.ElementBase, str | None]:
    if clazz is metadata_exchange.Dialect:
        container = metadata_exchange.GetMetadata(metadata_exchange.Dialect.from_uri("http://example.com/dialect"))
        return container, metadata_exchange.Dialect.TAG
    if clazz is metadata_exchange.Identifier:
        container = metadata_exchange.GetMetadata(metadata_exchange.Identifier.from_uri("http://example.com/id"))
        return container, metadata_exchange.Identifier.TAG
    if clazz is metadata_exchange.GetMetadata:
        return metadata_exchange.GetMetadata(), None
    if clazz is metadata_exchange.Location:
        section = metadata_exchange.MetadataSection(
            metadata_exchange.Location.from_uri("http://example.com/location"),
            Dialect="http://example.com/dialect",
        )
        container = metadata_exchange.Metadata(section)
        return container, f"{metadata_exchange.MetadataSection.TAG}/{metadata_exchange.Location.TAG}"
    if clazz is metadata_exchange.MetadataReference:
        ref = metadata_exchange.MetadataReference()
        # MetadataReference requires at least one child element from another namespace
        ref.append(lxml.etree.SubElement(ref, f"{{{addressing.NAMESPACE}}}Address"))
        section = metadata_exchange.MetadataSection(
            ref,
            Dialect="http://example.com/dialect",
        )
        container = metadata_exchange.Metadata(section)
        return container, f"{metadata_exchange.MetadataSection.TAG}/{metadata_exchange.MetadataReference.TAG}"
    if clazz is metadata_exchange.MetadataSection:
        section = metadata_exchange.MetadataSection(
            metadata_exchange.Location.from_uri("http://example.com/location"),
            Dialect="http://example.com/dialect",
        )
        container = metadata_exchange.Metadata(section)
        return container, metadata_exchange.MetadataSection.TAG
    if clazz is metadata_exchange.Metadata:
        return metadata_exchange.Metadata(), None
    msg = f"Unexpected class: {clazz}"
    raise ValueError(msg)


def test_get_metadata_properties() -> None:
    """Ensure GetMetadata exposes dialect and identifier properties."""
    element = metadata_exchange.GetMetadata(
        metadata_exchange.Dialect.from_uri("http://example.com/dialect"),
        metadata_exchange.Identifier.from_uri("http://example.com/id"),
    )
    assert element.dialect is not None
    assert element.dialect.text == "http://example.com/dialect"
    assert element.identifier is not None
    assert element.identifier.text == "http://example.com/id"


def test_metadata_section_properties() -> None:
    """Ensure MetadataSection exposes dialect attribute and child element properties."""
    section = metadata_exchange.MetadataSection(
        metadata_exchange.Location.from_uri("http://example.com/location"),
        Dialect="http://example.com/dialect",
        Identifier="http://example.com/id",
    )
    assert section.dialect == "http://example.com/dialect"
    assert section.identifier == "http://example.com/id"
    assert section.location is not None
    assert section.location.text == "http://example.com/location"


def test_metadata_sections_property() -> None:
    """Ensure Metadata exposes metadata_sections property."""
    section1 = metadata_exchange.MetadataSection(
        metadata_exchange.Location.from_uri("http://example.com/1"),
        Dialect="http://example.com/dialect1",
    )
    section2 = metadata_exchange.MetadataSection(
        metadata_exchange.Location.from_uri("http://example.com/2"),
        Dialect="http://example.com/dialect2",
    )
    element = metadata_exchange.Metadata(section1, section2)
    assert len(element.metadata_sections) == 2  # noqa: PLR2004
