"""XML parser with registered SDC XSD models."""

from __future__ import annotations

import io
import pathlib

import lxml.etree

from sdc_xsd_model import element_class_lookup, extension_registry
from sdc_xsd_model.core import addressing, biceps_msg, biceps_pm, discovery, eventing, extension, soap_envelope

_XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"


def discovery_schema() -> lxml.etree.XMLSchema:
    """Get an XMLSchema with all discovery related XSD models included."""
    xsd_dir = pathlib.Path(__file__).parent.joinpath("xsd").absolute()
    tmp = io.StringIO()
    tmp.writelines(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">\n',
            f'<xsd:import namespace="{addressing.NAMESPACE}" schemaLocation="{addressing.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="{discovery.NAMESPACE}" schemaLocation="{discovery.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="{eventing.NAMESPACE}" schemaLocation="{eventing.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="{soap_envelope.NAMESPACE}" schemaLocation="{soap_envelope.SCHEMA_PATH.as_uri()}"/>\n',  # noqa: E501
            f'<xsd:import namespace="http://www.w3.org/XML/1998/namespace" schemaLocation="{xsd_dir.joinpath("xml.xsd").as_uri()}"/>\n',  # noqa: E501
            "</xsd:schema>",
        ]
    )
    all_included = tmp.getvalue().encode("utf-8")

    elem_tree = lxml.etree.fromstring(all_included)
    return lxml.etree.XMLSchema(etree=elem_tree)


def discovery_parser() -> lxml.etree.XMLParser:
    """Get an XML parser with registered SDC XSD models relevant for discovery."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    addressing.set_lookup(lookup)
    discovery.set_lookup(lookup)
    eventing.set_lookup(lookup)
    soap_envelope.set_lookup(lookup)
    parser = lxml.etree.XMLParser(schema=discovery_schema())
    parser.set_element_class_lookup(lookup)
    return parser


def biceps_schema() -> lxml.etree.XMLSchema:
    """Get an XML schema with all SDC XSD models relevant for BICEPS messages included."""
    xsd_dir = pathlib.Path(__file__).parent.joinpath("xsd").absolute()
    tmp = io.StringIO()
    tmp.writelines(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">\n',
            f'<xsd:import namespace="{addressing.NAMESPACE}" schemaLocation="{addressing.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="{discovery.NAMESPACE}" schemaLocation="{discovery.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="{eventing.NAMESPACE}" schemaLocation="{eventing.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="{soap_envelope.NAMESPACE}" schemaLocation="{soap_envelope.SCHEMA_PATH.as_uri()}"/>\n',  # noqa: E501
            f'<xsd:import namespace="{extension.NAMESPACE}" schemaLocation="{extension.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="{biceps_pm.NAMESPACE}" schemaLocation="{biceps_pm.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="{biceps_msg.NAMESPACE}" schemaLocation="{biceps_msg.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="http://www.w3.org/XML/1998/namespace" schemaLocation="{xsd_dir.joinpath("xml.xsd").as_uri()}"/>\n',  # noqa: E501
        ]
    )
    tmp.writelines([f"{line}\n" for line in extension_registry.get_schema_lines()])
    tmp.write("</xsd:schema>")
    all_included = tmp.getvalue().encode("utf-8")

    elem_tree = lxml.etree.fromstring(all_included)
    return lxml.etree.XMLSchema(etree=elem_tree)


def biceps_parser() -> lxml.etree.XMLParser:
    """Get an XML parser with registered SDC XSD models relevant for BICEPS messages."""
    ns_lookup = lxml.etree.ElementNamespaceClassLookup()
    addressing.set_lookup(ns_lookup)
    discovery.set_lookup(ns_lookup)
    eventing.set_lookup(ns_lookup)
    soap_envelope.set_lookup(ns_lookup)
    extension.set_lookup(ns_lookup)
    biceps_pm.set_lookup(ns_lookup)
    biceps_msg.set_lookup(ns_lookup)
    extension_registry.set_lookup(ns_lookup)
    custom_lookup = element_class_lookup.BicepsElementClassLookup(ns_lookup)
    xml_parser = lxml.etree.XMLParser(schema=biceps_schema())
    xml_parser.set_element_class_lookup(custom_lookup)
    return xml_parser
