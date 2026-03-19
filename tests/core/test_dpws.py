"""Tests for the DPWS model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.core import addressing, common, dpws

DPWS_CASES = [
    (dpws.Manufacturer, "Manufacturer"),
    (dpws.ManufacturerUrl, "ManufacturerUrl"),
    (dpws.ModelName, "ModelName"),
    (dpws.ModelNumber, "ModelNumber"),
    (dpws.ModelUrl, "ModelUrl"),
    (dpws.PresentationUrl, "PresentationUrl"),
    (dpws.ThisModel, "ThisModel"),
    (dpws.FriendlyName, "FriendlyName"),
    (dpws.FirmwareVersion, "FirmwareVersion"),
    (dpws.SerialNumber, "SerialNumber"),
    (dpws.ThisDevice, "ThisDevice"),
    (dpws.Relationship, "Relationship"),
    (dpws.Types, "Types"),
    (dpws.ServiceId, "ServiceId"),
    (dpws.Host, "Host"),
    (dpws.Hosted, "Hosted"),
    (dpws.Profile, "Profile"),
]


@pytest.mark.parametrize(("clazz", "local_name"), DPWS_CASES)
def test_default_tag(
    clazz: type[common.ElementBase],
    local_name: str,
) -> None:
    """Ensure DPWS classes expose the expected TAG value."""
    assert f"{{{dpws.NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in DPWS_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Ensure DPWS classes register the expected namespace."""
    assert clazz().nsmap[dpws.PREFIX] == dpws.NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in DPWS_CASES])
def test_class_lookup(clazz: type[common.ElementBase]) -> None:
    """Ensure DPWS classes can be serialized and deserialized correctly."""
    element, target_tag = _create_dpws_element(clazz)
    xml = lxml.etree.tostring(element)
    parsed_element = lxml.etree.fromstring(xml, parser=clazz.PARSER)
    if target_tag is not None:
        parsed_element = parsed_element.find(target_tag)
    assert isinstance(parsed_element, clazz)


def _create_this_model() -> dpws.ThisModel:
    return dpws.ThisModel(
        dpws.Manufacturer("Acme Corp"),
        dpws.ModelName("Widget"),
    )


def _create_this_device() -> dpws.ThisDevice:
    return dpws.ThisDevice(dpws.FriendlyName("My Device"))


def _create_dpws_element(  # noqa: C901, PLR0911, PLR0912
    clazz: type[common.ElementBase],
) -> tuple[common.ElementBase, str | None]:
    if clazz is dpws.Manufacturer:
        model = _create_this_model()
        return model, dpws.Manufacturer.TAG
    if clazz is dpws.ManufacturerUrl:
        model = dpws.ThisModel(
            dpws.Manufacturer("Acme"),
            dpws.ManufacturerUrl.from_uri("http://example.com"),
            dpws.ModelName("Widget"),
        )
        return model, dpws.ManufacturerUrl.TAG
    if clazz is dpws.ModelName:
        model = _create_this_model()
        return model, dpws.ModelName.TAG
    if clazz is dpws.ModelNumber:
        model = dpws.ThisModel(
            dpws.Manufacturer("Acme"),
            dpws.ModelName("Widget"),
            dpws.ModelNumber("123"),
        )
        return model, dpws.ModelNumber.TAG
    if clazz is dpws.ModelUrl:
        model = dpws.ThisModel(
            dpws.Manufacturer("Acme"),
            dpws.ModelName("Widget"),
            dpws.ModelUrl.from_uri("http://example.com/model"),
        )
        return model, dpws.ModelUrl.TAG
    if clazz is dpws.PresentationUrl:
        model = dpws.ThisModel(
            dpws.Manufacturer("Acme"),
            dpws.ModelName("Widget"),
            dpws.PresentationUrl.from_uri("http://example.com/ui"),
        )
        return model, dpws.PresentationUrl.TAG
    if clazz is dpws.ThisModel:
        return _create_this_model(), None
    if clazz is dpws.FriendlyName:
        device = _create_this_device()
        return device, dpws.FriendlyName.TAG
    if clazz is dpws.FirmwareVersion:
        device = dpws.ThisDevice(
            dpws.FriendlyName("My Device"),
            dpws.FirmwareVersion("1.0.0"),
        )
        return device, dpws.FirmwareVersion.TAG
    if clazz is dpws.SerialNumber:
        device = dpws.ThisDevice(
            dpws.FriendlyName("My Device"),
            dpws.SerialNumber("SN-001"),
        )
        return device, dpws.SerialNumber.TAG
    if clazz is dpws.ThisDevice:
        return _create_this_device(), None
    if clazz is dpws.Relationship:
        return dpws.Relationship(Type=f"{dpws.NAMESPACE}/host"), None
    if clazz is dpws.Types:
        hosted = dpws.Hosted(
            addressing.EndpointReference.with_address("http://example.com"),
            dpws.Types(),
            dpws.ServiceId.from_uri("http://example.com/service"),
        )
        return hosted, dpws.Types.TAG
    if clazz is dpws.ServiceId:
        hosted = dpws.Hosted(
            addressing.EndpointReference.with_address("http://example.com"),
            dpws.Types(),
            dpws.ServiceId.from_uri("http://example.com/service"),
        )
        return hosted, dpws.ServiceId.TAG
    if clazz is dpws.Host:
        return dpws.Host(addressing.EndpointReference.with_address("http://example.com")), None
    if clazz is dpws.Hosted:
        return dpws.Hosted(
            addressing.EndpointReference.with_address("http://example.com"),
            dpws.Types(),
            dpws.ServiceId.from_uri("http://example.com/service"),
        ), None
    if clazz is dpws.Profile:
        return dpws.Profile(), None
    msg = f"Unexpected class: {clazz}"
    raise ValueError(msg)
