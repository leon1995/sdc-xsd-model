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
    xml = lxml.etree.tostring(clazz())
    parsed_element = lxml.etree.fromstring(xml)
    assert isinstance(parsed_element, clazz)
