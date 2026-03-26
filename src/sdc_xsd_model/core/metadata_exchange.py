"""Lxml models for WS-MetadataExchange elements from https://www.w3.org/Submission/WS-MetadataExchange/."""

from __future__ import annotations

import functools
import pathlib
import typing

import lxml.etree

from sdc_xsd_model.core import common

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

PREFIX: typing.Final[str] = "mex"
NAMESPACE: typing.Final[str] = "http://schemas.xmlsoap.org/ws/2004/09/mex"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.parent.joinpath("xsd", "MetadataExchange.xsd").absolute()
)
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


class Dialect(common.AnyUri):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Dialect"


class Identifier(common.AnyUri):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Identifier"


class GetMetadata(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetMetadata"

    @property
    def dialect(self) -> Dialect | None:
        return self.find_by_element(Dialect)

    @property
    def identifier(self) -> Identifier | None:
        return self.find_by_element(Identifier)


class Location(common.AnyUri):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Location"


class MetadataReference(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MetadataReference"


class MetadataSection(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MetadataSection"

    @property
    def dialect(self) -> str:
        value = self.get("Dialect")
        assert value is not None
        return value

    @property
    def identifier(self) -> str | None:
        return self.get("Identifier")

    @property
    def metadata_reference(self) -> MetadataReference | None:
        return self.find_by_element(MetadataReference)

    @property
    def location(self) -> Location | None:
        return self.find_by_element(Location)


class Metadata(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Metadata"

    @property
    def metadata_sections(self) -> Sequence[MetadataSection]:
        return self.findall_by_element(MetadataSection)


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register WS-MetadataExchange elements in the given lookup."""
    mex_namespace = lookup.get_namespace(NAMESPACE)
    mex_namespace["GetMetadata"] = GetMetadata
    mex_namespace["Dialect"] = Dialect
    mex_namespace["Identifier"] = Identifier
    mex_namespace["Metadata"] = Metadata
    mex_namespace["MetadataSection"] = MetadataSection
    mex_namespace["MetadataReference"] = MetadataReference
    mex_namespace["Location"] = Location


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get metadata exchange parser."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, get_parser())
