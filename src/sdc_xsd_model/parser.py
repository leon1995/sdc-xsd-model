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
