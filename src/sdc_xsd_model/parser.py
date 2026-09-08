"""XML parser with registered SDC XSD models."""

from __future__ import annotations

import io
import pathlib
from typing import TYPE_CHECKING

import lxml.etree

from sdc_xsd_model import element_class_lookup
from sdc_xsd_model.core import (
    addressing,
    biceps_msg,
    biceps_pm,
    discovery,
    dpws,
    eventing,
    extension,
    mdpws,
    metadata_exchange,
    soap_envelope,
)

if TYPE_CHECKING:
    from sdc_xsd_model.extension_registry import ExtensionRegistry

# Every module whose elements a BICEPS message can contain. ``sdc_lookup`` registers all of them, so no
# caller has to know the list.
_MODULES = (
    addressing,
    discovery,
    eventing,
    soap_envelope,
    extension,
    biceps_pm,
    biceps_msg,
    metadata_exchange,
    dpws,
    mdpws,
)


def sdc_schema(registry: ExtensionRegistry) -> lxml.etree.XMLSchema:
    """Get an XML schema with all SDC XSD models relevant for BICEPS messages included.

    Compiling this is the expensive part of building a validating parser, so a caller that creates parsers
    repeatedly should compile it once and hand it to :func:`sdc_parser`.
    """
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
            f'<xsd:import namespace="{metadata_exchange.NAMESPACE}" schemaLocation="{metadata_exchange.SCHEMA_PATH.as_uri()}"/>\n',  # noqa: E501
            f'<xsd:import namespace="{dpws.NAMESPACE}" schemaLocation="{dpws.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="{mdpws.NAMESPACE}" schemaLocation="{mdpws.SCHEMA_PATH.as_uri()}"/>\n',
            f'<xsd:import namespace="http://www.w3.org/XML/1998/namespace" schemaLocation="{xsd_dir.joinpath("xml.xsd").as_uri()}"/>\n',  # noqa: E501
        ]
    )
    tmp.writelines([f"{line}\n" for line in registry.get_schema_lines()])
    tmp.write("</xsd:schema>")
    all_included = tmp.getvalue().encode("utf-8")
    schema_parser = lxml.etree.XMLParser()
    registry.install_resolvers(schema_parser)
    elem_tree = lxml.etree.fromstring(all_included, parser=schema_parser)
    return lxml.etree.XMLSchema(etree=elem_tree)


def sdc_lookup(registry: ExtensionRegistry) -> lxml.etree.ElementClassLookup:
    """Get the element class lookup that resolves every SDC namespace to its typed classes.

    Useful on its own to a caller that needs an XML parser configured differently from the one
    :func:`sdc_parser` builds: the set of modules to register lives here rather than in every caller.
    """
    ns_lookup = lxml.etree.ElementNamespaceClassLookup()
    for module in _MODULES:
        module.set_lookup(ns_lookup)
    registry.set_lookup(ns_lookup)
    return element_class_lookup.BicepsElementClassLookup(ns_lookup)


def sdc_parser(
    registry: ExtensionRegistry,
    *,
    validate: bool = True,
    schema: lxml.etree.XMLSchema | None = None,
) -> lxml.etree.XMLParser:
    """Get an XML parser with registered SDC XSD models relevant for BICEPS messages.

    :param registry: the extension registry whose namespaces the parser knows about
    :param validate: whether the parser rejects a document that does not satisfy the schemas. Devices do send
        documents that do not, so a reader that has to tolerate them wants False. Elements come back typed
        either way: the class lookup does not depend on validation.
    :param schema: an already compiled schema to validate against, so that a caller building parsers
        repeatedly - one per thread, say - need not recompile it each time. Ignored when validate is False.

    Comments and processing instructions are dropped, because they carry no meaning in an SDC message and
    keeping them would put them among an element's children for every caller to skip. Entities are not
    resolved.
    """
    if validate and schema is None:
        schema = sdc_schema(registry)
    xml_parser = lxml.etree.XMLParser(
        schema=schema if validate else None,
        resolve_entities=False,
        remove_comments=True,
        remove_pis=True,
    )
    xml_parser.set_element_class_lookup(sdc_lookup(registry))
    return xml_parser


class SoapEnvelopeParser:
    """Parse a Soap envelope XML file."""

    def __init__(
        self,
        registry: ExtensionRegistry,
        *,
        validate: bool = True,
        schema: lxml.etree.XMLSchema | None = None,
    ) -> None:
        """Create a parser for SOAP envelopes.

        :param registry: the extension registry whose namespaces the parser knows about
        :param validate: whether to reject an envelope that does not satisfy the schemas
        :param schema: an already compiled schema, so a caller creating one of these per thread does not
            recompile it each time. Ignored when validate is False.
        """
        self._parser = sdc_parser(registry, validate=validate, schema=schema)

    def from_string(self, raw_envelope: str | bytes) -> soap_envelope.Envelope:
        """Parse an XML string and return an Envelope object."""
        envelope = lxml.etree.fromstring(raw_envelope, parser=self._parser)
        if not isinstance(envelope, soap_envelope.Envelope):
            msg = f"Expected a {soap_envelope.Envelope.TAG} element, got: {envelope.tag}"
            raise TypeError(msg)
        return envelope
