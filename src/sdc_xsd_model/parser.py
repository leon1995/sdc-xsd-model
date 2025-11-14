"""XML parser with registered SDC XSD models."""

import io
import pathlib

import lxml.etree

from sdc_xsd_model.models import addressing, discovery, eventing, soap_envelope


def discovery_schema() -> lxml.etree.XMLSchema:
    """Get an XMLSchema with all discovery related XSD models included."""
    xsd_dir = pathlib.Path(__file__).parent.joinpath("xsd").absolute()
    tmp = io.StringIO()
    tmp.writelines(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">\n',
            f'<xsd:import namespace="{addressing.NAMESPACE}" schemaLocation="{xsd_dir.joinpath("ws-addr.xsd").as_uri()}"/>\n',  # noqa: E501
            f'<xsd:import namespace="{discovery.NAMESPACE}" schemaLocation="{xsd_dir.joinpath("wsdd-discovery-1.1-schema-os.xsd").as_uri()}"/>\n',  # noqa: E501
            f'<xsd:import namespace="{eventing.NAMESPACE}" schemaLocation="{xsd_dir.joinpath("eventing.xsd").as_uri()}"/>\n',  # noqa: E501
            f'<xsd:import namespace="{soap_envelope.NAMESPACE}" schemaLocation="{xsd_dir.joinpath("soap-envelope.xsd").as_uri()}"/>\n',  # noqa: E501
            f'<xsd:import namespace="http://www.w3.org/XML/1998/namespace" schemaLocation="{xsd_dir.joinpath("xml.xsd").as_uri()}"/>\n',  # noqa: E501
            "</xsd:schema>",
        ]
    )
    all_included = tmp.getvalue().encode("utf-8")

    elem_tree = lxml.etree.fromstring(all_included)
    return lxml.etree.XMLSchema(etree=elem_tree)


def _set_addressing(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    addressing_namespace = lookup.get_namespace(addressing.NAMESPACE)
    addressing_namespace["Address"] = addressing.Address
    addressing_namespace["EndpointReference"] = addressing.EndpointReference
    addressing_namespace["ReferenceParameters"] = addressing.ReferenceParameters
    addressing_namespace["Metadata"] = addressing.Metadata
    addressing_namespace["To"] = addressing.To
    addressing_namespace["From"] = addressing.From
    addressing_namespace["ReplyTo"] = addressing.ReplyTo
    addressing_namespace["FaultTo"] = addressing.FaultTo
    addressing_namespace["Action"] = addressing.Action
    addressing_namespace["MessageID"] = addressing.MessageID


def _set_eventing(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    eventing_namespace = lookup.get_namespace(eventing.NAMESPACE)
    eventing_namespace["NotifyTo"] = eventing.NotifyTo
    eventing_namespace["EndTo"] = eventing.EndTo
    eventing_namespace["SubscriptionManager"] = eventing.SubscriptionManager
    eventing_namespace["Delivery"] = eventing.DeliveryType
    eventing_namespace["Filter"] = eventing.FilterType
    eventing_namespace["Identifier"] = eventing.Identifier
    eventing_namespace["SupportedDeliveryMode"] = eventing.SupportedDeliveryMode
    eventing_namespace["SupportedDialect"] = eventing.SupportedDialect
    eventing_namespace["LanguageSpecificString"] = eventing.LanguageSpecificStringType
    eventing_namespace["OpenSubscriptionEndCodeType"] = eventing.OpenSubscriptionEndCodeType
    eventing_namespace["Status"] = eventing.Status
    eventing_namespace["SubscriptionEnd"] = eventing.SubscriptionEnd
    eventing_namespace["SubscribeResponse"] = eventing.SubscribeResponse
    eventing_namespace["Subscribe"] = eventing.Subscribe
    eventing_namespace["Unsubscribe"] = eventing.Unsubscribe
    eventing_namespace["RenewResponse"] = eventing.RenewResponse
    eventing_namespace["Renew"] = eventing.Renew
    eventing_namespace["GetStatusResponse"] = eventing.GetStatusResponse
    eventing_namespace["GetStatus"] = eventing.GetStatus
    eventing_namespace["Expires"] = eventing.Expires
    eventing_namespace["Reason"] = eventing.Reason


def _set_discovery(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    discovery_namespace = lookup.get_namespace(discovery.NAMESPACE)
    discovery_namespace["Types"] = discovery.Types
    discovery_namespace["Scopes"] = discovery.Scopes
    discovery_namespace["XAddrs"] = discovery.XAddrs
    discovery_namespace["Hello"] = discovery.Hello
    discovery_namespace["Bye"] = discovery.Bye
    discovery_namespace["Probe"] = discovery.Probe
    discovery_namespace["ProbeMatch"] = discovery.ProbeMatch
    discovery_namespace["ProbeMatches"] = discovery.ProbeMatches
    discovery_namespace["ResolveMatch"] = discovery.ResolveMatch
    discovery_namespace["ResolveMatches"] = discovery.ResolveMatches
    discovery_namespace["AppSequence"] = discovery.AppSequence


def _set_soap_envelope(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    soap_namespace = lookup.get_namespace(soap_envelope.NAMESPACE)
    soap_namespace["Envelope"] = soap_envelope.Envelope
    soap_namespace["Header"] = soap_envelope.Header
    soap_namespace["Body"] = soap_envelope.Body
    soap_namespace["Text"] = soap_envelope.FaultReasonText
    soap_namespace["Reason"] = soap_envelope.FaultReason
    soap_namespace["Subcode"] = soap_envelope.SubCode
    soap_namespace["Code"] = soap_envelope.FaultCode
    soap_namespace["Detail"] = soap_envelope.Detail
    soap_namespace["Fault"] = soap_envelope.Fault
    soap_namespace["Value"] = soap_envelope.Value
    soap_namespace["Node"] = soap_envelope.Node
    soap_namespace["Role"] = soap_envelope.Role


def discovery_parser() -> lxml.etree.XMLParser:
    """Get an XML parser with registered SDC XSD models."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    _set_addressing(lookup)
    _set_eventing(lookup)
    _set_discovery(lookup)
    _set_soap_envelope(lookup)

    parser = lxml.etree.XMLParser(schema=discovery_schema())
    parser.set_element_class_lookup(lookup)
    return parser
