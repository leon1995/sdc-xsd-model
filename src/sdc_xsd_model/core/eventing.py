"""Lxml models for WS-Eventing elements from https://www.w3.org/submissions/2006/SUBM-WS-Eventing-20060315/."""

from __future__ import annotations
import datetime
from sdc_xsd_model.core.helper import duration

import enum
import functools
import pathlib
import typing

import lxml.etree

from sdc_xsd_model.core import addressing, common

if typing.TYPE_CHECKING:
    from collections.abc import Sequence


PREFIX: typing.Final[str] = "wse"
NAMESPACE: typing.Final[str] = "http://schemas.xmlsoap.org/ws/2004/08/eventing"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.parent.joinpath("xsd", "eventing.xsd").absolute()
)
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


class NotifyTo(addressing.EndpointReference):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}NotifyTo"


class EndTo(addressing.EndpointReference):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EndTo"


class SubscriptionManager(addressing.EndpointReference):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SubscriptionManager"


class DeliveryType(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Delivery"

    @property
    def mode(self) -> str | None:
        return self.get("Mode")


class FilterType(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Filter"

    @property
    def dialect(self) -> str | None:
        return self.get("Dialect")


class Identifier(addressing.AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Identifier"


class SupportedDeliveryMode(addressing.AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SupportedDeliveryMode"


class SupportedDialect(addressing.AttributedURIType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SupportedDialect"


class LanguageSpecificStringType(common.ElementBase):
    @property
    def lang(self) -> str | None:
        return self.get("{http://www.w3.org/XML/1998/namespace}lang")


class Reason(LanguageSpecificStringType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Reason"


class Expires(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Expires"

    @property
    def expiration(self) -> datetime.datetime | datetime.timedelta:
        text = self.text
        assert text is not None
        if text.startswith("P"):
            return duration.parse_duration(text)
        return datetime.datetime.fromisoformat(text)


class GetStatus(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetStatus"


class GetStatusResponse(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}GetStatusResponse"

    @property
    def expires(self) -> Expires | None:
        return self.find_by_element(Expires)


class Renew(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Renew"

    @property
    def expires(self) -> Expires | None:
        return self.find_by_element(Expires)


class RenewResponse(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}RenewResponse"

    @property
    def expires(self) -> Expires | None:
        return self.find_by_element(Expires)


class Unsubscribe(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Unsubscribe"


class Subscribe(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Subscribe"

    @property
    def end_to(self) -> EndTo | None:
        return self.find_by_element(EndTo)

    @property
    def delivery(self) -> DeliveryType | None:
        return self.find_by_element(DeliveryType)

    @property
    def expires(self) -> Expires | None:
        return self.find_by_element(Expires)

    @property
    def filter(self) -> FilterType | None:
        return self.find_by_element(FilterType)


class SubscribeResponse(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SubscribeResponse"

    @property
    def subscription_manager(self) -> SubscriptionManager:
        value = self.find_by_element(SubscriptionManager)
        # schema enforces presence
        assert value is not None
        return value

    @property
    def expires(self) -> Expires:
        node = self.find_by_element(Expires)
        assert node is not None
        return node


class SubscriptionEndCodeType(enum.StrEnum):
    DELIVERY_FAILURE = "http://schemas.xmlsoap.org/ws/2004/08/eventing/DeliveryFailure"
    SOURCE_SHUTTING_DOWN = "http://schemas.xmlsoap.org/ws/2004/08/eventing/SourceShuttingDown"
    SOURCE_CANCELLING = "http://schemas.xmlsoap.org/ws/2004/08/eventing/SourceCancelling"


class OpenSubscriptionEndCodeType(common.ElementBase):
    def code_type(self) -> SubscriptionEndCodeType | None:
        return SubscriptionEndCodeType(super().text) if super().text is not None else None


class Status(OpenSubscriptionEndCodeType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Status"


class SubscriptionEnd(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}SubscriptionEnd"

    @property
    def subscription_manager(self) -> SubscriptionManager:
        value = self.find_by_element(SubscriptionManager)
        # schema enforces presence
        assert value is not None
        return value

    @property
    def status(self) -> Status | None:
        return self.find_by_element(Status)

    @property
    def reason(self) -> Sequence[Reason]:
        return self.findall_by_element(Reason)


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register all Eventing elements in the given lookup."""
    eventing_namespace = lookup.get_namespace(NAMESPACE)
    eventing_namespace["NotifyTo"] = NotifyTo
    eventing_namespace["EndTo"] = EndTo
    eventing_namespace["SubscriptionManager"] = SubscriptionManager
    eventing_namespace["Delivery"] = DeliveryType
    eventing_namespace["Filter"] = FilterType
    eventing_namespace["Identifier"] = Identifier
    eventing_namespace["SupportedDeliveryMode"] = SupportedDeliveryMode
    eventing_namespace["SupportedDialect"] = SupportedDialect
    eventing_namespace["LanguageSpecificString"] = LanguageSpecificStringType
    eventing_namespace["OpenSubscriptionEndCodeType"] = OpenSubscriptionEndCodeType
    eventing_namespace["Status"] = Status
    eventing_namespace["SubscriptionEnd"] = SubscriptionEnd
    eventing_namespace["SubscribeResponse"] = SubscribeResponse
    eventing_namespace["Subscribe"] = Subscribe
    eventing_namespace["Unsubscribe"] = Unsubscribe
    eventing_namespace["RenewResponse"] = RenewResponse
    eventing_namespace["Renew"] = Renew
    eventing_namespace["GetStatusResponse"] = GetStatusResponse
    eventing_namespace["GetStatus"] = GetStatus
    eventing_namespace["Expires"] = Expires
    eventing_namespace["Reason"] = Reason


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get eventing parser."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


common.set_parser_on_subclasses(__name__, get_parser())
