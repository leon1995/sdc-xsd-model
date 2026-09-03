"""Simplified registration API for custom BICEPS extension classes.

Provides a factory-based API to register custom ``ElementBase`` subclasses
for arbitrary XML namespaces and obtain a composite parser that includes both
built-in SDC modules and user-defined extensions.

Example::

    from sdc_xsd_model.extension_registry import ExtensionRegistry

    registry = ExtensionRegistry()
    sdpi = registry.register_extension(
        namespace="urn:oid:1.3.6.1.4.1.19376.1.6.2.10.1.1.1",
        prefix="sdpi",
        schema=Path("custom.xsd"),
    )

    @sdpi
    class MyData(common.ElementBase):
        TAG = "{urn:oid:1.3.6.1.4.1.19376.1.6.2.10.1.1.1}MyData"
        ...

    # Classes can also be registered at runtime:
    sdpi.register_classes(MyDynamicClass)
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import typing
import urllib.parse

import lxml.etree

if typing.TYPE_CHECKING:
    import os
    from collections.abc import Iterable, Sequence

    from sdc_xsd_model.core import common

_TAG_RE = re.compile(r"\{(?P<ns>[^}]+)\}(?P<local>.+)")

_UNION_URI_PREFIX = "urn:sdc-xsd-model:extension-union:"


@dataclasses.dataclass
class _NamespaceInfo:
    prefix: str | None = None
    schemas: set[pathlib.Path] = dataclasses.field(default_factory=set)
    classes: dict[str, type[common.ElementBase]] = dataclasses.field(default_factory=dict)


def _union_uri(namespace: str) -> str:
    """Return the synthetic location under which *namespace*'s union schema is served.

    The namespace is percent-encoded because a nested URI such as ``urn:oid:1.3.6...`` is not a
    valid ``xsd:anyURI`` when embedded verbatim, and libxml2 rejects the ``xsd:import`` outright.
    """
    return _UNION_URI_PREFIX + urllib.parse.quote(namespace, safe="")


def _union_document(namespace: str, schemas: Iterable[pathlib.Path]) -> str:
    """Return a schema document for *namespace* that includes every one of *schemas*.

    A namespace may be described by several schema documents, but ``xsd:import`` binds a namespace
    to exactly one location -- libxml2 honours the first import and silently ignores the rest. The
    documents therefore have to be combined with ``xsd:include`` into a single document, which is
    what gets imported. Schemas are sorted so the result does not depend on set iteration order.
    """
    includes = "".join(f'<xsd:include schemaLocation="{schema.as_uri()}"/>' for schema in sorted(schemas))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" targetNamespace="{namespace}">'
        f"{includes}</xsd:schema>"
    )


def _parse_tag(tag: str) -> tuple[str, str]:
    """Extract ``(namespace, local_name)`` from a Clark-notation TAG string."""
    m = _TAG_RE.match(tag)
    if not m:
        msg = f"TAG must be in Clark notation '{{namespace}}localname', got: {tag!r}"
        raise ValueError(msg)
    return m.group("ns"), m.group("local")


class _NamespaceDecorator:
    """Reusable decorator returned by :meth:`ExtensionRegistry.register_extension`."""

    __slots__ = ("_info", "_namespace")

    def __init__(self, namespace: str, info: _NamespaceInfo) -> None:
        self._namespace = namespace
        self._info = info

    @typing.overload
    def __call__[T: common.ElementBase](self, cls: type[T], /) -> type[T]: ...

    @typing.overload
    def __call__[T: common.ElementBase](self) -> typing.Callable[[type[T]], type[T]]: ...

    def __call__[T: common.ElementBase](
        self,
        cls: type[T] | None = None,
    ) -> type[T] | typing.Callable[[type[T]], type[T]]:
        if cls is not None:
            return self._register(cls)

        def decorator(cls: type[T]) -> type[T]:
            return self._register(cls)

        return decorator

    def _register[T: common.ElementBase](self, cls: type[T]) -> type[T]:
        ns, local_name = _parse_tag(cls.TAG)

        if ns != self._namespace:
            msg = f"TAG namespace {ns!r} does not match factory namespace {self._namespace!r}"
            raise ValueError(msg)

        if local_name in self._info.classes:
            msg = f"{cls.TAG} already registered"
            raise RuntimeError(msg)

        self._info.classes[local_name] = cls
        return cls

    def register_classes(self, *classes: type[common.ElementBase]) -> None:
        """Register multiple classes at once."""
        for cls in classes:
            self._register(cls)


class ExtensionRegistry:
    """Injectable registry for custom BICEPS extension classes.

    Each instance maintains its own isolated namespace->class mapping,
    enabling test isolation without global-state mutation.
    """

    def __init__(self) -> None:
        self._namespaces: dict[str, _NamespaceInfo] = {}

    def register_extension(
        self,
        namespace: str,
        *,
        prefix: str | None = None,
        schema: str | os.PathLike[str] | None = None,
    ) -> _NamespaceDecorator:
        """Create a decorator that registers ``ElementBase`` subclasses under *namespace*."""
        if namespace not in self._namespaces:
            self._namespaces[namespace] = _NamespaceInfo()
        info = self._namespaces[namespace]

        if prefix is not None:
            if info.prefix is not None and info.prefix != prefix:
                msg = (
                    f"Namespace {namespace!r} already registered with prefix {info.prefix!r}, "
                    f"cannot re-register with {prefix!r}"
                )
                raise ValueError(msg)
            info.prefix = prefix
            lxml.etree.register_namespace(prefix, namespace)
        if schema is not None:
            info.schemas.add(pathlib.Path(schema).absolute())

        return _NamespaceDecorator(namespace, info)

    def set_lookup(self, lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
        """Register all custom extension classes from the registry into *lookup*."""
        for ns, info in self._namespaces.items():
            ns_registry = lookup.get_namespace(ns)
            for local_name, cls in info.classes.items():
                ns_registry[local_name] = cls

    def get_schema_lines(self) -> Sequence[str]:
        """Return lines of XML schema declarations of registered extensions referencing a schema.

        Exactly one ``xsd:import`` is emitted per namespace. A namespace described by several schema
        documents is imported through a synthetic union document, which
        :meth:`install_resolvers` serves to the parser building the schema.
        """
        lines = []
        for ns, info in self._namespaces.items():
            if not info.schemas:
                continue
            location = next(iter(info.schemas)).as_uri() if len(info.schemas) == 1 else _union_uri(ns)
            lines.append(f'<xsd:import namespace="{ns}" schemaLocation="{location}"/>')
        return lines

    def install_resolvers(self, parser: lxml.etree.XMLParser) -> None:
        """Teach *parser* to resolve the union schema of every namespace with multiple schemas.

        Must be called on the parser that reads the aggregate schema document, so that the
        synthetic locations emitted by :meth:`get_schema_lines` can be resolved from memory.
        """
        unions = {
            _union_uri(ns): _union_document(ns, info.schemas)
            for ns, info in self._namespaces.items()
            if len(info.schemas) > 1
        }

        class _UnionResolver(lxml.etree.Resolver):
            """Serve the in-memory union schema documents by their synthetic location."""

            def resolve(self, system_url: str, public_id: str | None, context: object) -> object:  # noqa: ARG002
                document = unions.get(system_url)
                if document is None:
                    return None
                return self.resolve_string(document, context)

        parser.resolvers.add(_UnionResolver())
