"""Tests for the hand-written element bases in ``core.common``.

The scalar lexical mappings (``to_bool``, ``to_qname``, ...) live in ``sdc_xsd_model.converter`` and
are pinned in ``tests/test_converter.py``; this module covers only what ``common`` adds on top of
them, namely the ``xsd:list`` handling in :class:`~sdc_xsd_model.core.common.QNameListType`.

That list handling is deliberately tested through a throwaway class rather than a real model class.
Clark notation is not a valid ``xsd:QName`` literal, so a schema-validating parser rejects it before
``q_names`` ever runs, yet ``converter.to_qname`` accepts it -- which is exactly the seam worth
pinning. The real-document cases (a prefixed and an unprefixed name) are covered end to end by
``tests/core/test_roundtrip.py``; both hold a single item, so multi-item lists, Clark notation inside
a list and the empty list are only covered here.
"""

from __future__ import annotations

import typing

import lxml.etree
import pytest

from sdc_xsd_model.core import common

DPWS: typing.Final[str] = "http://docs.oasis-open.org/ws-dd/ns/dpws/2009/01"
NAMESPACE: typing.Final[str] = "urn:test:common"
PREFIX: typing.Final[str] = "tc"

lxml.etree.register_namespace(PREFIX, NAMESPACE)


class _Types(common.QNameListType):
    """Throwaway stand-in for an element whose type is an ``xsd:list`` of ``xsd:QName``."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Types"


class _Type(common.QNameType):
    """Throwaway stand-in for an element whose type is a single ``xsd:QName``."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Type"


def _get_parser() -> lxml.etree.XMLParser:
    """Build a parser for this module; no schema, so lexically invalid QNames still reach the property."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    namespace = lookup.get_namespace(NAMESPACE)
    namespace["Types"] = _Types
    namespace["Type"] = _Type
    xml_parser = lxml.etree.XMLParser()
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, _get_parser())


def _parse_types(text: str, *, declarations: str = f'xmlns:dpws="{DPWS}"') -> _Types:
    xml = f'<{PREFIX}:Types xmlns:{PREFIX}="{NAMESPACE}" {declarations}>{text}</{PREFIX}:Types>'.encode()
    element = lxml.etree.fromstring(xml, parser=_Types.PARSER)
    assert isinstance(element, _Types)
    return element


def test_q_names_resolves_each_item_of_the_list() -> None:
    """Ensure every notation in one list resolves, and that whitespace between items is collapsed.

    Clark notation is included on purpose: ``converter.to_qname`` accepts it even though it is not a
    valid ``xsd:QName`` literal, so this is the only place the list path sees it.
    """
    element = _parse_types(
        f"  dpws:Device\n Other  {{{DPWS}}}Third ",
        declarations=f'xmlns:dpws="{DPWS}" xmlns="{DPWS}"',
    )
    assert element.q_names == [
        lxml.etree.QName(DPWS, "Device"),
        lxml.etree.QName(DPWS, "Other"),
        lxml.etree.QName(DPWS, "Third"),
    ]


def test_q_names_resolves_a_bare_name_against_the_default_namespace() -> None:
    """Ensure an unprefixed item uses the default namespace declaration, as XSD requires for QNames."""
    element = _parse_types("Device", declarations=f'xmlns="{DPWS}"')
    assert element.q_names == [lxml.etree.QName(DPWS, "Device")]


def test_q_names_of_a_bare_name_without_a_default_namespace_has_no_namespace() -> None:
    """Ensure a bare item stays namespace-free when no default namespace is in scope."""
    element = _parse_types("Device", declarations="")
    assert element.q_names == [lxml.etree.QName("Device")]


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_q_names_of_an_empty_list_is_empty(text: str) -> None:
    """Ensure an empty or whitespace-only value yields no items; the empty string is a valid xsd:list."""
    assert _parse_types(text).q_names == []


def test_q_names_of_an_absent_value_is_empty() -> None:
    """Ensure a self-closing element yields no items rather than raising on ``text`` being None."""
    element = lxml.etree.fromstring(f'<{PREFIX}:Types xmlns:{PREFIX}="{NAMESPACE}"/>'.encode(), parser=_Types.PARSER)
    assert isinstance(element, _Types)
    assert element.text is None
    assert element.q_names == []


def test_q_names_rejects_an_undeclared_prefix() -> None:
    """Ensure an unresolvable prefix raises rather than yielding a silently mismatching QName."""
    element = _parse_types("nope:Device")
    with pytest.raises(ValueError, match="is not declared"):
        _ = element.q_names


def test_q_name_resolves_a_single_value() -> None:
    """Ensure the single-QName base resolves its text against the in-scope declarations."""
    xml = f'<{PREFIX}:Type xmlns:{PREFIX}="{NAMESPACE}" xmlns:dpws="{DPWS}">dpws:Device</{PREFIX}:Type>'.encode()
    element = lxml.etree.fromstring(xml, parser=_Type.PARSER)
    assert isinstance(element, _Type)
    assert element.q_name == lxml.etree.QName(DPWS, "Device")


def test_q_name_of_an_absent_value_is_none() -> None:
    """Ensure an empty element yields None rather than raising."""
    xml = f'<{PREFIX}:Type xmlns:{PREFIX}="{NAMESPACE}"/>'.encode()
    element = lxml.etree.fromstring(xml, parser=_Type.PARSER)
    assert isinstance(element, _Type)
    assert element.q_name is None
