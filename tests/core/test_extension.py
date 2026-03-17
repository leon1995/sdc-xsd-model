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
