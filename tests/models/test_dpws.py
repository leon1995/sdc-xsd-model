"""Tests for the DPWS model classes."""

import lxml.etree
import pytest

from sdc_xsd_model.models import addressing, common, dpws

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


def test_this_model_properties() -> None:
    """Ensure ThisModel exposes typed child element properties."""
    model = dpws.ThisModel(
        dpws.Manufacturer("Acme Corp"),
        dpws.ManufacturerUrl.from_uri("http://acme.example.com"),
        dpws.ModelName("Widget"),
        dpws.ModelNumber("X-100"),
        dpws.ModelUrl.from_uri("http://acme.example.com/widget"),
        dpws.PresentationUrl.from_uri("http://acme.example.com/ui"),
    )
    assert len(model.manufacturers) == 1
    assert model.manufacturers[0].text == "Acme Corp"
    assert model.manufacturer_url is not None
    assert model.manufacturer_url.text == "http://acme.example.com"
    assert len(model.model_names) == 1
    assert model.model_names[0].text == "Widget"
    assert model.model_number is not None
    assert model.model_number.text == "X-100"
    assert model.model_url is not None
    assert model.presentation_url is not None


def test_this_device_properties() -> None:
    """Ensure ThisDevice exposes typed child element properties."""
    device = dpws.ThisDevice(
        dpws.FriendlyName("My Device"),
        dpws.FirmwareVersion("2.0"),
        dpws.SerialNumber("SN-42"),
    )
    assert len(device.friendly_names) == 1
    assert device.friendly_names[0].text == "My Device"
    assert device.firmware_version is not None
    assert device.firmware_version.text == "2.0"
    assert device.serial_number is not None
    assert device.serial_number.text == "SN-42"


def test_host_properties() -> None:
    """Ensure Host exposes endpoint_reference and types properties."""
    host = dpws.Host(
        addressing.EndpointReference.with_address("http://example.com/host"),
        dpws.Types(),
    )
    assert isinstance(host.endpoint_reference, addressing.EndpointReference)
    assert host.types is not None


def test_hosted_properties() -> None:
    """Ensure Hosted exposes endpoint_references, types, and service_id properties."""
    hosted = dpws.Hosted(
        addressing.EndpointReference.with_address("http://example.com/svc1"),
        addressing.EndpointReference.with_address("http://example.com/svc2"),
        dpws.Types(),
        dpws.ServiceId.from_uri("http://example.com/service"),
    )
    assert len(hosted.endpoint_references) == 2  # noqa: PLR2004
    assert isinstance(hosted.types, dpws.Types)
    assert isinstance(hosted.service_id, dpws.ServiceId)


def test_relationship_type_attribute() -> None:
    """Ensure Relationship exposes the Type attribute."""
    rel = dpws.Relationship(Type=f"{dpws.NAMESPACE}/host")
    assert rel.type == f"{dpws.NAMESPACE}/host"
