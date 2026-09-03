"""Tests for registering every SDPi extension at once.

All four SDPi schemas share one ``targetNamespace``. Because ``xsd:import`` binds a namespace to a
single location, emitting one import per schema made libxml2 keep only the first and silently drop
the rest -- and since the schemas are held in a set, *which* one survived varied per process. The
loss was silent rather than fatal because ``ExtensionPoint.xsd`` declares
``<xsd:any processContents="lax"/>``, so undeclared extension content is skipped instead of
rejected. These tests pin that all four extensions are validated together.
"""

from __future__ import annotations

import pathlib

import lxml.etree
import pytest

from sdc_xsd_model.extension_registry import ExtensionRegistry
from sdc_xsd_model.extensions import sdpi
from sdc_xsd_model.parser import sdc_parser

EXAMPLES = sorted(pathlib.Path(__file__).parent.glob("*_example.xml"))


@pytest.fixture
def registry() -> ExtensionRegistry:
    """Build a registry with every SDPi extension registered."""
    registry = ExtensionRegistry()
    sdpi.register_all(registry)
    return registry


def test_register_all_emits_one_import_for_the_shared_namespace(registry: ExtensionRegistry) -> None:
    """The four SDPi schemas share a namespace, so they must collapse to a single import."""
    assert len(registry.get_schema_lines()) == 1


def test_all_examples_parse_with_every_extension_registered(registry: ExtensionRegistry) -> None:
    """Every SDPi example document validates when all four extensions are registered."""
    assert len(EXAMPLES) == 4
    parser = sdc_parser(registry)
    for example in EXAMPLES:
        assert lxml.etree.parse(str(example), parser=parser) is not None


def test_invalid_extension_attribute_is_rejected(registry: ExtensionRegistry) -> None:
    """An out-of-range extension attribute must fail validation, not be laxly skipped.

    ``sdpi:Epochs/@Version`` is an ``xsd:unsignedInt``. Before the union fix this document was
    accepted whenever the timestamp schema lost the import race, i.e. in most processes.
    """
    example = pathlib.Path(__file__).parent / "timestamp_epoch_version_example.xml"
    corrupted = example.read_text(encoding="utf-8").replace(
        '<sdpi:Epochs Version="5">', '<sdpi:Epochs Version="NOT_A_NUMBER">'
    )
    assert "NOT_A_NUMBER" in corrupted

    parser = sdc_parser(registry)
    with pytest.raises(lxml.etree.XMLSyntaxError, match="Version"):
        lxml.etree.fromstring(corrupted.encode(), parser=parser)
