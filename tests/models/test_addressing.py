"""Tests for the addressing model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.models import addressing, common

ADDRESSING_CASES = [
    (addressing.Address, "Address"),
    (addressing.Metadata, "Metadata"),
    (addressing.ReferenceParameters, "ReferenceParameters"),
    (addressing.EndpointReference, "EndpointReference"),
    (addressing.To, "To"),
    (addressing.From, "From"),
    (addressing.ReplyTo, "ReplyTo"),
    (addressing.FaultTo, "FaultTo"),
    (addressing.Action, "Action"),
    (addressing.MessageID, "MessageID"),
    (addressing.RelatesTo, "RelatesTo"),
]


@pytest.mark.parametrize(("clazz", "local_name"), ADDRESSING_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure addressing classes expose the expected TAG value."""
    assert f"{{{addressing.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in ADDRESSING_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure addressing classes register the expected namespace."""
    assert clazz().nsmap[addressing.PREFIX] == addressing.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in ADDRESSING_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure addressing classes can be serialized and deserialized correctly."""
    element, target_tag = _create_addressing_element(clazz)
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=clazz.PARSER)
    if target_tag is not None:
        parsed_element = parsed_element.find(target_tag)
    assert isinstance(parsed_element, clazz)


def _create_addressing_element(
    clazz: type[common.ElementBase],
) -> tuple[common.ElementBase, str | None]:
    if clazz is addressing.Address:
        container = addressing.EndpointReference(addressing.Address.from_random_uri())
        return container, addressing.Address.TAG
    if issubclass(clazz, addressing.EndpointReference):
        element = clazz(addressing.Address.from_random_uri())
        return element, None
    if issubclass(clazz, addressing.AttributedURIType):
        if clazz is addressing.RelatesTo:
            return clazz.from_random_uri(attrib={"RelationshipType": f"{addressing.NAMESPACE}/reply"}), None
        return clazz.from_random_uri(), None
    return clazz(), None
