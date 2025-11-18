"""Tests for the eventing model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.models import common, eventing

EVENTING_CASES = [
    (eventing.NotifyTo, "NotifyTo"),
    (eventing.EndTo, "EndTo"),
    (eventing.SubscriptionManager, "SubscriptionManager"),
    (eventing.DeliveryType, "Delivery"),
    (eventing.FilterType, "Filter"),
    (eventing.Identifier, "Identifier"),
    (eventing.SupportedDeliveryMode, "SupportedDeliveryMode"),
    (eventing.SupportedDialect, "SupportedDialect"),
    (eventing.Reason, "Reason"),
    (eventing.Expires, "Expires"),
    (eventing.GetStatus, "GetStatus"),
    (eventing.GetStatusResponse, "GetStatusResponse"),
    (eventing.Renew, "Renew"),
    (eventing.RenewResponse, "RenewResponse"),
    (eventing.Unsubscribe, "Unsubscribe"),
    (eventing.Subscribe, "Subscribe"),
    (eventing.SubscribeResponse, "SubscribeResponse"),
    (eventing.Status, "Status"),
    (eventing.SubscriptionEnd, "SubscriptionEnd"),
]


@pytest.mark.parametrize(("clazz", "local_name"), EVENTING_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure eventing classes expose the expected TAG value."""
    assert f"{{{eventing.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in EVENTING_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure eventing classes register the expected namespace."""
    assert clazz().nsmap[eventing.PREFIX] == eventing.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in EVENTING_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure eventing classes can be serialized and deserialized correctly."""
    xml = lxml.etree.tostring(clazz())
    parsed_element = lxml.etree.fromstring(xml)
    assert isinstance(parsed_element, clazz)
