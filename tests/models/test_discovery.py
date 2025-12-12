"""Tests for the discovery model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.models import addressing, common, discovery

XMLNS: str = "http://www.w3.org/2000/xmlns/"

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
    element, target_tag = _create_discovery_element(clazz)
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=clazz.PARSER)
    if target_tag is not None:
        parsed_element = parsed_element.find(target_tag)
    assert isinstance(parsed_element, clazz)


def _create_discovery_element(
    clazz: type[common.ElementBase],
) -> tuple[common.ElementBase, str | None]:
    if clazz is discovery.Types:
        return _make_types(), None
    if clazz is discovery.Scopes:
        return _make_scopes(), None
    if clazz is discovery.XAddrs:
        return _make_xaddrs(), None
    if clazz is discovery.MetadataVersion:
        return _make_metadata_version(), None
    if clazz in (discovery.Hello, discovery.Bye):
        element = clazz(
            _make_endpoint_reference(),
            _make_types(),
            _make_scopes(),
            _make_xaddrs(),
            _make_metadata_version(),
        )
        return element, None
    if clazz is discovery.Probe:
        element = discovery.Probe(_make_types(), _make_scopes())
        return element, None
    if clazz is discovery.ProbeMatch:
        container = discovery.ProbeMatches(_make_probe_match())
        return container, discovery.ProbeMatch.TAG
    if clazz is discovery.ProbeMatches:
        element = discovery.ProbeMatches(_make_probe_match())
        return element, None
    if clazz is discovery.Resolve:
        element = discovery.Resolve(_make_endpoint_reference())
        return element, None
    if clazz is discovery.ResolveMatch:
        container = discovery.ResolveMatches(_make_resolve_match())
        return container, discovery.ResolveMatch.TAG
    if clazz is discovery.ResolveMatches:
        element = discovery.ResolveMatches(_make_resolve_match())
        return element, None
    if clazz is discovery.AppSequence:
        element = discovery.AppSequence()
        element.set("InstanceId", "1")
        element.set("SequenceId", "urn:uuid:22222222-2222-2222-2222-222222222222")
        element.set("MessageNumber", "1")
        return element, None
    return clazz(), None


def _make_types() -> discovery.Types:
    return discovery.Types(
        f"{addressing.PREFIX}:Action",
        nsmap={addressing.PREFIX: addressing.NAMESPACE},
    )


def _make_scopes() -> discovery.Scopes:
    return discovery.Scopes(
        "urn:example:scope",
        MatchBy=f"{discovery.NAMESPACE}/ldap",
    )


def _make_xaddrs() -> discovery.XAddrs:
    return discovery.XAddrs("https://example.org/service")


def _make_metadata_version() -> discovery.MetadataVersion:
    return discovery.MetadataVersion("1")


def _make_endpoint_reference() -> addressing.EndpointReference:
    return addressing.EndpointReference(
        addressing.Address("urn:uuid:33333333-3333-3333-3333-333333333333"),
    )


def _make_probe_match() -> discovery.ProbeMatch:
    return discovery.ProbeMatch(
        _make_endpoint_reference(),
        _make_types(),
        _make_scopes(),
        _make_xaddrs(),
        _make_metadata_version(),
    )


def _make_resolve_match() -> discovery.ResolveMatch:
    return discovery.ResolveMatch(
        _make_endpoint_reference(),
        _make_types(),
        _make_scopes(),
        _make_xaddrs(),
        _make_metadata_version(),
    )
