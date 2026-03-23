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

import lxml.etree

if typing.TYPE_CHECKING:
    import os
    from collections.abc import Sequence

    from sdc_xsd_model.core import common

_TAG_RE = re.compile(r"\{(?P<ns>[^}]+)\}(?P<local>.+)")


@dataclasses.dataclass
class _NamespaceInfo:
    prefix: str | None = None
    schemas: set[pathlib.Path] = dataclasses.field(default_factory=set)
    classes: dict[str, type[common.ElementBase]] = dataclasses.field(default_factory=dict)


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
        """Return lines of XML schema declarations of registered extensions referencing a schema."""
        return [
            f'<xsd:import namespace="{ns}" schemaLocation="{schema.as_uri()}"/>'
            for ns, info in self._namespaces.items()
            for schema in info.schemas
        ]
