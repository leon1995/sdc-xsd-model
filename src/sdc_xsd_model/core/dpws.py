"""Lxml models for DPWS elements from https://docs.oasis-open.org/ws-dd/dpws/1.1/os/wsdd-dpws-1.1-spec-os.html."""

from __future__ import annotations

import enum
import functools
import pathlib
import typing

import lxml.etree

from sdc_xsd_model.core import addressing, common

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

PREFIX: typing.Final[str] = "dpws"
NAMESPACE: typing.Final[str] = "http://docs.oasis-open.org/ws-dd/ns/dpws/2009/01"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.parent.joinpath("xsd", "wsdd-dpws-1.1-schema-os.xsd").absolute()
)
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


class DeviceRelationshipTypeURIs(enum.StrEnum):
    HOST = f"{NAMESPACE}/host"


class DeviceMetadataDialectURIs(enum.StrEnum):
    THIS_MODEL = f"{NAMESPACE}/ThisModel"
    THIS_DEVICE = f"{NAMESPACE}/ThisDevice"
    RELATIONSHIP = f"{NAMESPACE}/Relationship"


class DeviceEventingFilterDialectURIs(enum.StrEnum):
    ACTION = f"{NAMESPACE}/Action"


class DeviceActionURIs(enum.StrEnum):
    FAULT = f"{NAMESPACE}/fault"


class DeviceSoapFaultSubcodeQNames(enum.StrEnum):
    FILTER_ACTION_NOT_SUPPORTED = f"{{{NAMESPACE}}}FilterActionNotSupported"


class DiscoveryTypeValues(enum.StrEnum):
    DEVICE = f"{{{NAMESPACE}}}Device"


class LocalizedStringType(common.ElementBase):
    """A string with optional xml:lang attribute."""

    @property
    def lang(self) -> str | None:
        """``xml:lang`` of this string, or None when absent.

        DPWS repeats these elements once per language, so a consumer picking a display string has to read the
        tag to choose between them. Mirrors ``eventing.LanguageSpecificStringType.lang``.
        """
        return self.get("{http://www.w3.org/XML/1998/namespace}lang")


class Manufacturer(LocalizedStringType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Manufacturer"


class ModelName(LocalizedStringType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ModelName"


class ManufacturerUrl(common.AnyUri):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ManufacturerUrl"


class ModelNumber(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ModelNumber"


class ModelUrl(common.AnyUri):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ModelUrl"


class PresentationUrl(common.AnyUri):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}PresentationUrl"


class ThisModel(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ThisModel"

    @property
    def manufacturers(self) -> Sequence[Manufacturer]:
        return self.findall_by_element(Manufacturer)

    @property
    def manufacturer_url(self) -> ManufacturerUrl | None:
        return self.find_by_element(ManufacturerUrl)

    @property
    def model_names(self) -> Sequence[ModelName]:
        return self.findall_by_element(ModelName)

    @property
    def model_number(self) -> ModelNumber | None:
        return self.find_by_element(ModelNumber)

    @property
    def model_url(self) -> ModelUrl | None:
        return self.find_by_element(ModelUrl)

    @property
    def presentation_url(self) -> PresentationUrl | None:
        return self.find_by_element(PresentationUrl)


class FriendlyName(LocalizedStringType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}FriendlyName"


class FirmwareVersion(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}FirmwareVersion"


class SerialNumber(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SerialNumber"


class ThisDevice(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ThisDevice"

    @property
    def friendly_names(self) -> Sequence[FriendlyName]:
        return self.findall_by_element(FriendlyName)

    @property
    def firmware_version(self) -> FirmwareVersion | None:
        return self.find_by_element(FirmwareVersion)

    @property
    def serial_number(self) -> SerialNumber | None:
        return self.find_by_element(SerialNumber)


class Types(common.QNameListType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Types"


class ServiceId(common.AnyUri):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ServiceId"


class Host(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Host"

    @property
    def endpoint_reference(self) -> addressing.EndpointReference:
        value = self.find_by_element(addressing.EndpointReference)
        # schema enforces presence
        assert value is not None
        return value

    @property
    def types(self) -> Types | None:
        return self.find_by_element(Types)


class Hosted(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Hosted"

    @property
    def endpoint_references(self) -> Sequence[addressing.EndpointReference]:
        return self.findall_by_element(addressing.EndpointReference)

    @property
    def types(self) -> Types:
        value = self.find_by_element(Types)
        # schema enforces presence
        assert value is not None
        return value

    @property
    def service_id(self) -> str:
        node = self.find_by_element(ServiceId)
        # schema enforces presence
        assert node is not None
        text = node.text
        assert text is not None
        return text


class Relationship(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Relationship"

    @property
    def type(self) -> str:
        value = self.get("Type")
        # schema enforces presence (use="required")
        assert value is not None
        return value

    @property
    def host(self) -> Host | None:
        return self.find_by_element(Host)

    @property
    def hosted(self) -> Sequence[Hosted]:
        return self.findall_by_element(Hosted)


class Profile(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Profile"


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register DPWS elements in the given lookup."""
    dpws_namespace = lookup.get_namespace(NAMESPACE)
    dpws_namespace["ThisModel"] = ThisModel
    dpws_namespace["Manufacturer"] = Manufacturer
    dpws_namespace["ManufacturerUrl"] = ManufacturerUrl
    dpws_namespace["ModelName"] = ModelName
    dpws_namespace["ModelNumber"] = ModelNumber
    dpws_namespace["ModelUrl"] = ModelUrl
    dpws_namespace["PresentationUrl"] = PresentationUrl
    dpws_namespace["ThisDevice"] = ThisDevice
    dpws_namespace["FriendlyName"] = FriendlyName
    dpws_namespace["FirmwareVersion"] = FirmwareVersion
    dpws_namespace["SerialNumber"] = SerialNumber
    dpws_namespace["Relationship"] = Relationship
    dpws_namespace["Host"] = Host
    dpws_namespace["Hosted"] = Hosted
    dpws_namespace["Types"] = Types
    dpws_namespace["ServiceId"] = ServiceId
    dpws_namespace["Profile"] = Profile


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get DPWS parser."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    addressing.set_lookup(lookup)
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, get_parser())
