"""Lxml models for WS-Discovery elements from https://docs.oasis-open.org/ws-dd/discovery/1.1/os/wsdd-discovery-1.1-spec-os.html."""

from __future__ import annotations

import functools
import pathlib
import typing

import lxml.etree

from sdc_xsd_model.core import addressing, common

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

PREFIX: typing.Final[str] = "wsd"
NAMESPACE: typing.Final[str] = "http://docs.oasis-open.org/ws-dd/ns/discovery/2009/01"

lxml.etree.register_namespace(PREFIX, NAMESPACE)
SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.parent.joinpath("xsd", "wsdd-discovery-1.1-schema-os.xsd").absolute()
)
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)


class UriListType(common.ElementBase):
    @property
    def uris(self) -> Sequence[str]:
        if self.text is None:
            return []
        return self.text.split()


class Types(common.QNameListType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Types"


class Scopes(UriListType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Scopes"

    @property
    def match_by(self) -> str | None:
        return self.get("MatchBy")


class XAddrs(UriListType):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}XAddrs"


class MetadataVersion(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MetadataVersion"

    @property
    def version(self) -> int | None:
        return int(self.text) if self.text is not None else None


class Hello(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Hello"

    @property
    def endpoint_reference(self) -> addressing.EndpointReference:
        value = self.find_by_element(addressing.EndpointReference)
        # schema enforces presence
        assert value is not None
        return value

    @property
    def types(self) -> Types | None:
        return self.find_by_element(Types)

    @property
    def scopes(self) -> Scopes | None:
        return self.find_by_element(Scopes)

    @property
    def x_addrs(self) -> XAddrs | None:
        return self.find_by_element(XAddrs)

    @property
    def metadata_version(self) -> MetadataVersion | None:
        return self.find_by_element(MetadataVersion)


class Bye(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Bye"

    @property
    def endpoint_reference(self) -> addressing.EndpointReference:
        value = self.find_by_element(addressing.EndpointReference)
        # schema enforces presence
        assert value is not None
        return value

    @property
    def types(self) -> Types | None:
        return self.find_by_element(Types)

    @property
    def scopes(self) -> Scopes | None:
        return self.find_by_element(Scopes)

    @property
    def x_addrs(self) -> XAddrs | None:
        return self.find_by_element(XAddrs)

    @property
    def metadata_version(self) -> MetadataVersion | None:
        return self.find_by_element(MetadataVersion)


class Probe(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Probe"

    @property
    def types(self) -> Types | None:
        return self.find_by_element(Types)

    @property
    def scopes(self) -> Scopes | None:
        return self.find_by_element(Scopes)


class ProbeMatch(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ProbeMatch"

    @property
    def endpoint_reference(self) -> addressing.EndpointReference | None:
        return self.find_by_element(addressing.EndpointReference)

    @property
    def types(self) -> Types | None:
        return self.find_by_element(Types)

    @property
    def scopes(self) -> Scopes | None:
        return self.find_by_element(Scopes)

    @property
    def x_addrs(self) -> XAddrs | None:
        return self.find_by_element(XAddrs)

    @property
    def metadata_version(self) -> MetadataVersion | None:
        return self.find_by_element(MetadataVersion)


class ProbeMatches(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ProbeMatches"

    @property
    def probe_match(self) -> Sequence[ProbeMatch]:
        return self.findall_by_element(ProbeMatch)


class Resolve(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Resolve"

    @property
    def endpoint_reference(self) -> addressing.EndpointReference:
        value = self.find_by_element(addressing.EndpointReference)
        # schema enforces presence
        assert value is not None
        return value


class ResolveMatch(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ResolveMatch"

    @property
    def endpoint_reference(self) -> addressing.EndpointReference | None:
        return self.find_by_element(addressing.EndpointReference)

    @property
    def types(self) -> Types | None:
        return self.find_by_element(Types)

    @property
    def scopes(self) -> Scopes | None:
        return self.find_by_element(Scopes)

    @property
    def x_addrs(self) -> XAddrs | None:
        return self.find_by_element(XAddrs)

    @property
    def metadata_version(self) -> MetadataVersion | None:
        return self.find_by_element(MetadataVersion)


class ResolveMatches(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}ResolveMatches"

    @property
    def resolve_match(self) -> ResolveMatch | None:
        return self.find_by_element(ResolveMatch)


class AppSequence(common.ElementBase):
    TAG: typing.Final[str] = f"{{{NAMESPACE}}}AppSequence"

    @property
    def instance_id(self) -> int:
        instance_id = self.get("InstanceId")
        # schema enforces presence
        assert instance_id is not None
        return int(instance_id)

    @property
    def sequence_id(self) -> str | None:
        return self.get("SequenceId")

    @property
    def message_number(self) -> int:
        value = self.get("MessageNumber")
        # schema enforces presence
        assert value is not None
        return int(value)


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register discovery types in the given lookup."""
    discovery_namespace = lookup.get_namespace(NAMESPACE)
    discovery_namespace["Types"] = Types
    discovery_namespace["Scopes"] = Scopes
    discovery_namespace["XAddrs"] = XAddrs
    discovery_namespace["Hello"] = Hello
    discovery_namespace["Bye"] = Bye
    discovery_namespace["Probe"] = Probe
    discovery_namespace["ProbeMatch"] = ProbeMatch
    discovery_namespace["ProbeMatches"] = ProbeMatches
    discovery_namespace["Resolve"] = Resolve
    discovery_namespace["ResolveMatch"] = ResolveMatch
    discovery_namespace["ResolveMatches"] = ResolveMatches
    discovery_namespace["AppSequence"] = AppSequence
    discovery_namespace["MetadataVersion"] = MetadataVersion


@functools.cache
def get_parser() -> lxml.etree.XMLParser:
    """Get discovery parser."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser(schema=SCHEMA)
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


for cls in (
    Types,
    Scopes,
    XAddrs,
    Hello,
    Bye,
    Probe,
    ProbeMatch,
    ProbeMatches,
    Resolve,
    ResolveMatch,
    ResolveMatches,
    AppSequence,
    MetadataVersion,
):
    cls.PARSER = get_parser()
