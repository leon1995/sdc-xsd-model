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

from sdc_xsd_model.core import biceps_pm, common

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


@pytest.mark.parametrize(
    ("value", "implied", "expected"),
    [
        (0, 1, 0),
        (None, 1, 1),
        (None, None, None),
        (False, True, False),
        ("", "implied", ""),
        ("value", "implied", "value"),
    ],
)
def test_with_implied(
    value: int | bool | str | None,  # noqa: FBT001
    implied: int | bool | str | None,  # noqa: FBT001
    expected: int | bool | str | None,  # noqa: FBT001
) -> None:
    """Ensure the ``with_implied`` context manager adds the namespace to the element's ``nsmap``."""
    assert common.with_implied(value, implied) == expected


def test_text_is_writable() -> None:
    """Re-declaring ``text`` as a property must not drop lxml's setter.

    Without the setter every caller that builds or copies an element has to reach for lxml's own descriptor.
    """
    element = biceps_pm.LocalizedText()
    element.text = "hello"
    assert element.text == "hello"
    assert b">hello<" in lxml.etree.tostring(element)


def test_text_can_be_cleared() -> None:
    """Assigning None removes the text content again."""
    element = biceps_pm.LocalizedText()
    element.text = "hello"
    element.text = None
    assert element.text is None


class _Parent(common.ElementBase):
    """Throwaway container used to reach the checked child accessors."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Parent"


class _Child(common.ElementBase):
    """Throwaway child that ``_Parent`` claims to contain."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Child"


class _Sub(_Child):
    """Subclass of the declared child type; an accessor asking for ``_Child`` must accept one."""


class _Other(common.ElementBase):
    """A registered class that is *not* a ``_Child``, standing in for a wrong ``xsi:type``."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Other"


type _EITHER = _Child | _Other

_CHILD_TAG: typing.Final[str] = f"{{{NAMESPACE}}}Child"


def _checked_parser(*, child_class: type[common.ElementBase] | None) -> lxml.etree.XMLParser:
    """Build a parser that resolves ``tc:Child`` to *child_class*, or to nothing at all.

    Passing None reproduces the failure this guard exists for: the element parses, but with no class
    attached, so before the guard an accessor's ``typing.cast`` claimed a type nothing had checked.
    """
    lookup = lxml.etree.ElementNamespaceClassLookup()
    namespace = lookup.get_namespace(NAMESPACE)
    namespace["Parent"] = _Parent
    namespace["Other"] = _Other
    if child_class is not None:
        namespace["Child"] = child_class
    xml_parser = lxml.etree.XMLParser()
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


def _parse_parent(body: str, *, child_class: type[common.ElementBase] | None = _Child) -> _Parent:
    xml = f'<{PREFIX}:Parent xmlns:{PREFIX}="{NAMESPACE}">{body}</{PREFIX}:Parent>'.encode()
    element = lxml.etree.fromstring(xml, parser=_checked_parser(child_class=child_class))
    assert isinstance(element, _Parent)
    return element


def test_find_child_returns_the_typed_child() -> None:
    """The happy path: a registered child comes back as its class."""
    parent = _parse_parent(f"<{PREFIX}:Child/>")
    assert isinstance(parent.find_child(_CHILD_TAG, _Child), _Child)


def test_find_child_absent_is_not_a_mismatch() -> None:
    """An absent optional child is ``None``, not an error -- most accessors are ``| None`` for that reason."""
    assert _parse_parent("").find_child(_CHILD_TAG, _Child) is None


def test_find_child_accepts_a_subclass() -> None:
    """A child narrower than the declared type satisfies it.

    This is the common case on real traffic, not an edge one: ``xsi:type`` and the parent-context table both
    resolve an element to a subclass of what its element name alone registers -- ``msg:State`` registers an
    abstract state and dispatches to ``RealTimeSampleArrayMetricState``. A guard that demanded an exact class
    would reject every one of those.
    """
    parent = _parse_parent(f"<{PREFIX}:Child/>", child_class=_Sub)
    found = parent.find_child(_CHILD_TAG, _Child)
    assert isinstance(found, _Sub)


def test_find_child_rejects_an_unregistered_child() -> None:
    """The bug class this guard exists for: no class attached, so the annotation was a lie.

    Before the guard this returned a plain ``_Element`` and the caller met an ``AttributeError`` on the
    first property read, one seam away from the missing registration that caused it.
    """
    parent = _parse_parent(f"<{PREFIX}:Child/>", child_class=None)
    with pytest.raises(TypeError, match="missing from its module's set_lookup"):
        parent.find_child(_CHILD_TAG, _Child)


def test_find_child_rejects_a_different_registered_class() -> None:
    """A child that *is* typed, but not as the accessor promises, blames the document rather than the setup."""
    parent = _parse_parent("")
    other = _Other()
    other.tag = _CHILD_TAG
    parent.append(other)
    with pytest.raises(TypeError, match="is a _Other, not a _Child"):
        parent.find_child(_CHILD_TAG, _Child)


def test_find_child_accepts_a_union_alias() -> None:
    """Abstract state and descriptor accessors pass a ``type`` alias for a union, which has no ``TAG``.

    ``isinstance`` rejects a PEP 695 alias outright, so this pins the unwrapping rather than the union.
    """
    parent = _parse_parent(f"<{PREFIX}:Child/>")
    assert isinstance(parent.find_child(_CHILD_TAG, _EITHER), _Child)


def test_find_child_rejects_anything_outside_a_union_alias() -> None:
    """A union still constrains: an unregistered child satisfies no member of it."""
    parent = _parse_parent(f"<{PREFIX}:Child/>", child_class=None)
    with pytest.raises(TypeError, match="did not deserialize to _EITHER"):
        parent.find_child(_CHILD_TAG, _EITHER)


def test_findall_child_returns_every_typed_child() -> None:
    """The list counterpart checks each element, and an empty result is not an error."""
    parent = _parse_parent(f"<{PREFIX}:Child/><{PREFIX}:Child/>")
    assert [type(child) for child in parent.findall_child(_CHILD_TAG, _Child)] == [_Child, _Child]
    assert _parse_parent("").findall_child(_CHILD_TAG, _Child) == []


def test_findall_child_raises_on_the_first_bad_child() -> None:
    """Raises rather than filtering: a mismatch is a registration fault that affects every sibling.

    Returning the children that happen to be typed would hide exactly the defect worth reporting.
    """
    parent = _parse_parent(f"<{PREFIX}:Child/><{PREFIX}:Child/>", child_class=None)
    with pytest.raises(TypeError):
        parent.findall_child(_CHILD_TAG, _Child)


def test_find_by_element_delegates_to_find_child() -> None:
    """The ``TAG``-derived form is the same seam, so it carries the same guard."""
    parent = _parse_parent(f"<{PREFIX}:Child/>", child_class=None)
    with pytest.raises(TypeError, match="missing from its module's set_lookup"):
        parent.find_by_element(_Child)
    with pytest.raises(TypeError, match="missing from its module's set_lookup"):
        parent.findall_by_element(_Child)
