"""Lxml models for Extension Point elements from IEEE 11073-10207-2017."""

from __future__ import annotations

import functools
import pathlib
import typing

import lxml.etree

from sdc_xsd_model import converter
from sdc_xsd_model.core import common

PREFIX: typing.Final[str] = "ext"
NAMESPACE: typing.Final[str] = "http://standards.ieee.org/downloads/11073/11073-10207-2017/extension"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.parent.joinpath("xsd", "ExtensionPoint.xsd").absolute()
)
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


MUST_UNDERSTAND_ATTR_TAG: typing.Final[str] = f"{{{NAMESPACE}}}MustUnderstand"


class Extension(common.ElementBase):
    """ExtensionType element allowing arbitrary extension children."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Extension"

    @property
    def must_understand(self) -> bool:
        """Return the ext:MustUnderstand attribute, which defaults to false when absent."""
        value = converter.to_bool(self.get(MUST_UNDERSTAND_ATTR_TAG, "false"))
        assert value is not None
        return value


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register Extension Point elements in the given lookup."""
    ext_namespace = lookup.get_namespace(NAMESPACE)
    ext_namespace["Extension"] = Extension


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get Extension Point parser."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, get_parser())
