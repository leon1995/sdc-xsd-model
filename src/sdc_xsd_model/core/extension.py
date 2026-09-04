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

IMPLIED_MUST_UNDERSTAND: typing.Final[bool] = False


def must_understand_of(element: common.ElementBase) -> bool | None:
    """Read ``ext:MustUnderstand`` off *element*, or None when the attribute is absent.

    Raises:
        ValueError: if the attribute is present but not a valid ``xsd:boolean`` literal.

    """
    return converter.to_bool(element.get(MUST_UNDERSTAND_ATTR_TAG))


class Extension(common.ElementBase):
    """ExtensionType element allowing arbitrary extension children."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Extension"

    @property
    def must_understand(self) -> bool | None:
        """``ext:MustUnderstand`` as written, or None when the attribute is absent.

        Prefer :attr:`must_understand_or_implied` when deciding whether to reject an unknown extension; use
        this one only when it matters whether the attribute was on the wire, e.g. when re-serializing.
        """
        return must_understand_of(self)

    @property
    def must_understand_or_implied(self) -> bool:
        """``ext:MustUnderstand``; the schema states an absent attribute means ``false``.

        Goes through ``common.with_implied``, which tests ``is None``: writing ``self.must_understand or
        False`` would happen to work here but is the pattern that inverts the numeric and boolean defaults
        elsewhere in the model.
        """
        return common.with_implied(self.must_understand, IMPLIED_MUST_UNDERSTAND)


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
