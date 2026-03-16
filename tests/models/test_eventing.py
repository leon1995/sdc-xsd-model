"""Tests for the eventing model classes."""

import uuid

import lxml.etree
import pytest

from sdc_xsd_model.models import addressing, common, eventing

XML_LANG: str = "http://www.w3.org/XML/1998/namespace"

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
    element, target_tag = _create_eventing_element(clazz)
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=clazz.PARSER)
    if target_tag is not None:
        parsed_element = parsed_element.find(target_tag)
    assert isinstance(parsed_element, clazz)


def _create_eventing_element(  # noqa: C901, PLR0911, PLR0912
    clazz: type[common.ElementBase],
) -> tuple[common.ElementBase, str | None]:
    if clazz is eventing.NotifyTo:
        return _make_eventing_endpoint(eventing.NotifyTo), None
    if clazz is eventing.EndTo:
        return _make_subscribe(), eventing.EndTo.TAG
    if clazz is eventing.SubscriptionManager:
        return _make_subscribe_response(), eventing.SubscriptionManager.TAG
    if clazz is eventing.DeliveryType:
        return _make_subscribe(), eventing.DeliveryType.TAG
    if clazz is eventing.FilterType:
        return _make_subscribe(), eventing.FilterType.TAG
    if clazz in (eventing.Identifier, eventing.SupportedDeliveryMode, eventing.SupportedDialect):
        return clazz(uuid.uuid4().urn), None
    if clazz is eventing.Reason:
        return _make_subscription_end(), eventing.Reason.TAG
    if clazz is eventing.Expires:
        return _make_renew_response(), eventing.Expires.TAG
    if clazz is eventing.GetStatus:
        return eventing.GetStatus(), None
    if clazz is eventing.GetStatusResponse:
        return _make_get_status_response(), None
    if clazz is eventing.Renew:
        return _make_renew(), None
    if clazz is eventing.RenewResponse:
        return _make_renew_response(), None
    if clazz is eventing.Unsubscribe:
        return eventing.Unsubscribe(), None
    if clazz is eventing.Subscribe:
        return _make_subscribe(), None
    if clazz is eventing.SubscribeResponse:
        return _make_subscribe_response(), None
    if clazz is eventing.Status:
        return _make_subscription_end(), eventing.Status.TAG
    if clazz is eventing.SubscriptionEnd:
        return _make_subscription_end(), None
    return clazz(), None


def _make_eventing_endpoint(
    endpoint_cls: type[addressing.EndpointReference],
) -> addressing.EndpointReference:
    return endpoint_cls.with_address(uuid.uuid4().urn)


def _make_delivery() -> eventing.DeliveryType:
    return eventing.DeliveryType(
        _make_eventing_endpoint(eventing.NotifyTo),
        attrib={"Mode": "http://schemas.xmlsoap.org/ws/2004/08/eventing/DeliveryModes/Push"},
    )


def _make_filter() -> eventing.FilterType:
    return eventing.FilterType(
        "//wse:Subscribe",
        attrib={"Dialect": uuid.uuid4().urn},
    )


def _make_expires() -> eventing.Expires:
    return eventing.Expires("PT1H")


def _make_reason() -> eventing.Reason:
    return eventing.Reason(
        "Subscription ended",
        attrib={f"{{{XML_LANG}}}lang": "en"},
    )


def _make_status() -> eventing.Status:
    return eventing.Status(eventing.SubscriptionEndCodeType.DELIVERY_FAILURE.value)


def _make_subscribe() -> eventing.Subscribe:
    return eventing.Subscribe(
        _make_eventing_endpoint(eventing.EndTo),
        _make_delivery(),
        _make_expires(),
        _make_filter(),
    )


def _make_subscribe_response() -> eventing.SubscribeResponse:
    return eventing.SubscribeResponse(
        _make_eventing_endpoint(eventing.SubscriptionManager),
        _make_expires(),
    )


def _make_subscription_end() -> eventing.SubscriptionEnd:
    return eventing.SubscriptionEnd(
        _make_eventing_endpoint(eventing.SubscriptionManager),
        _make_status(),
        _make_reason(),
    )


def _make_get_status_response() -> eventing.GetStatusResponse:
    return eventing.GetStatusResponse(_make_expires())


def _make_renew() -> eventing.Renew:
    return eventing.Renew(_make_expires())


def _make_renew_response() -> eventing.RenewResponse:
    return eventing.RenewResponse(_make_expires())
