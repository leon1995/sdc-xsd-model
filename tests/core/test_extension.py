"""Tests for the Extension Point model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.core import common, extension

EXTENSION_CASES = [
    (extension.Extension, "Extension"),
]


@pytest.mark.parametrize(("clazz", "local_name"), EXTENSION_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure Extension Point classes expose the expected TAG value."""
    assert f"{{{extension.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in EXTENSION_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure Extension Point classes register the expected namespace."""
    assert clazz().nsmap[extension.PREFIX] == extension.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in EXTENSION_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure Extension Point classes can be serialized and deserialized correctly."""
    element = clazz()
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=clazz.PARSER)
    assert isinstance(parsed_element, clazz)


# ── ext:MustUnderstand ─────────────────────────────────────────────────────────────────────────────


def _get_lookup_parser() -> lxml.etree.XMLParser:
    """Non-validating parser with class lookup.

    ext:ExtensionType declares no attributes of its own -- ext:MustUnderstand is a *global* attribute,
    meant for the extension children -- so a fragment carrying it on ext:Extension does not validate.
    """
    lookup = lxml.etree.ElementNamespaceClassLookup()
    extension.set_lookup(lookup)
    parser = lxml.etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    return parser


_LOOKUP_PARSER = _get_lookup_parser()

_EXTENSION_NSMAP = f'xmlns="{extension.NAMESPACE}" xmlns:ext="{extension.NAMESPACE}"'


@pytest.mark.parametrize(("raw", "expected"), [("true", True), ("1", True), ("false", False), ("0", False)])
def test_must_understand(raw: str, expected: bool) -> None:  # noqa: FBT001
    """All four xsd:boolean lexical forms are honoured, so "1" means true."""
    xml = f'<Extension {_EXTENSION_NSMAP} ext:MustUnderstand="{raw}"/>'.encode()
    element = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    assert isinstance(element, extension.Extension)
    assert element.must_understand is expected


def test_must_understand_defaults_to_false() -> None:
    """The schema declares default="false", so an absent attribute reads as False, not None."""
    xml = f'<Extension xmlns="{extension.NAMESPACE}"/>'.encode()
    element = lxml.etree.fromstring(xml, parser=extension.Extension.PARSER)
    assert isinstance(element, extension.Extension)
    assert element.must_understand is False


def test_must_understand_default_without_schema_validation() -> None:
    """The default is applied by the property, so it holds under a non-validating parser too."""
    xml = f'<Extension xmlns="{extension.NAMESPACE}"/>'.encode()
    element = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    assert isinstance(element, extension.Extension)
    assert element.must_understand is False


def test_must_understand_rejects_invalid_literal() -> None:
    """A capitalised True is outside the xsd:boolean lexical space, so it errors rather than reading false."""
    xml = f'<Extension {_EXTENSION_NSMAP} ext:MustUnderstand="True"/>'.encode()
    element = lxml.etree.fromstring(xml, parser=_LOOKUP_PARSER)
    assert isinstance(element, extension.Extension)
    with pytest.raises(ValueError, match="xsd:boolean"):
        _ = element.must_understand
