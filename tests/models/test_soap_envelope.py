"""Tests for the SOAP envelope model classes."""

import pytest

from sdc_xsd_model.models import common, soap_envelope

SOAP_ENVELOPE_CASES = [
    (soap_envelope.Header, "Header"),
    (soap_envelope.Body, "Body"),
    (soap_envelope.Envelope, "Envelope"),
    (soap_envelope.Value, "Value"),
    (soap_envelope.FaultReasonText, "Text"),
    (soap_envelope.FaultReason, "Reason"),
    (soap_envelope.SubCode, "Subcode"),
    (soap_envelope.FaultCode, "Code"),
    (soap_envelope.Detail, "Detail"),
    (soap_envelope.Node, "Node"),
    (soap_envelope.Role, "Role"),
    (soap_envelope.Fault, "Fault"),
]


@pytest.mark.parametrize(("clazz", "local_name"), SOAP_ENVELOPE_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure SOAP envelope classes expose the expected TAG value."""
    assert f"{{{soap_envelope.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in SOAP_ENVELOPE_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure SOAP envelope classes register the expected namespace."""
    assert clazz().nsmap[soap_envelope.PREFIX] == soap_envelope.NAMESPACE
