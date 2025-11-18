"""Tests for the discovery model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.models import common, discovery

DISCOVERY_CASES = [
    (discovery.Types, "Types"),
    (discovery.Scopes, "Scopes"),
    (discovery.XAddrs, "XAddrs"),
    (discovery.MetadataVersion, "MetadataVersion"),
    (discovery.Hello, "Hello"),
    (discovery.Bye, "Bye"),
    (discovery.Probe, "Probe"),
    (discovery.ProbeMatch, "ProbeMatch"),
    (discovery.ProbeMatches, "ProbeMatches"),
    (discovery.Resolve, "Resolve"),
    (discovery.ResolveMatch, "ResolveMatch"),
    (discovery.ResolveMatches, "ResolveMatches"),
    (discovery.AppSequence, "AppSequence"),
]


@pytest.mark.parametrize(("clazz", "local_name"), DISCOVERY_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure discovery classes expose the expected TAG value."""
    assert f"{{{discovery.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in DISCOVERY_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure discovery classes register the expected namespace."""
    assert clazz().nsmap[discovery.PREFIX] == discovery.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in DISCOVERY_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure discovery classes can be serialized and deserialized correctly."""
    xml = lxml.etree.tostring(clazz())
    parsed_element = lxml.etree.fromstring(xml)
    assert isinstance(parsed_element, clazz)
