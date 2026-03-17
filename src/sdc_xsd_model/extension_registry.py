"""Simplified registration API for custom BICEPS extension classes.

Provides a decorator-based API to register custom ``ElementBase`` subclasses
for arbitrary XML namespaces and obtain a composite parser that includes both
built-in SDC modules and user-defined extensions.

Example::

    from sdc_xsd_model.registry import register_extension, get_extension_parser

    @register_extension(prefix="myext", schema_path=Path("custom.xsd"))
    class MyData(common.ElementBase):
        TAG = "{http://example.com/myext}MyData"
        ...

    parser = get_extension_parser()
    parsed = lxml.etree.fromstring(xml_bytes, parser=parser)
"""

from __future__ import annotations

import dataclasses
import re
import typing
from collections.abc import Sequence

import lxml.etree

from sdc_xsd_model.models import common

if typing.TYPE_CHECKING:
    import pathlib

_TAG_RE = re.compile(r"\{(?P<ns>[^}]+)\}(?P<local>.+)")


@dataclasses.dataclass
class _NamespaceInfo:
    prefix: str | None = None
    schema_path: pathlib.Path | None = None
    classes: dict[str, type[common.ElementBase]] = dataclasses.field(default_factory=dict)


_registry: dict[str, _NamespaceInfo] = {}


def _parse_tag(tag: str) -> tuple[str, str]:
    """Extract ``(namespace, local_name)`` from a Clark-notation TAG string."""
    m = _TAG_RE.match(tag)
    if not m:
        msg = f"TAG must be in Clark notation '{{namespace}}localname', got: {tag!r}"
        raise ValueError(msg)
    return m.group("ns"), m.group("local")


def _register_class(
    cls: type[common.ElementBase],
    prefix: str | None = None,
    schema_path: pathlib.Path | None = None,
) -> type[common.ElementBase]:
    ns, local_name = _parse_tag(cls.TAG)

    if ns not in _registry:
        _registry[ns] = _NamespaceInfo()
    info = _registry[ns]

    if prefix is not None:
        info.prefix = prefix
        lxml.etree.register_namespace(prefix, ns)
    if schema_path is not None:
        info.schema_path = schema_path.absolute() if not schema_path.is_absolute() else schema_path

    info.classes[local_name] = cls
    return cls


@typing.overload
def register_extension(cls: type[common.ElementBase], /) -> type[common.ElementBase]: ...


@typing.overload
def register_extension(
    *,
    prefix: str | None = None,
    schema_path: pathlib.Path | None = None,
) -> typing.Callable[[type[common.ElementBase]], type[common.ElementBase]]: ...


def register_extension(
    cls: type[common.ElementBase] | None = None,
    /,
    *,
    prefix: str | None = None,
    schema_path: pathlib.Path | None = None,
) -> type[common.ElementBase] | typing.Callable[[type[common.ElementBase]], type[common.ElementBase]]:
    """Register an ``ElementBase`` subclass for automatic namespace class lookup.

    Can be used as a bare decorator (``@register_extension``) or with arguments
    (``@register_extension(prefix="myext", schema_path=Path("custom.xsd"))``).
    """
    if cls is not None:
        # Bare @register_extension (no parentheses)
        return _register_class(cls, prefix=prefix, schema_path=schema_path)

    # Called with arguments — return the real decorator
    def decorator(cls: type[common.ElementBase]) -> type[common.ElementBase]:
        return _register_class(cls, prefix=prefix, schema_path=schema_path)

    return decorator


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register all custom extension classes from the registry into *lookup*."""
    for ns, info in _registry.items():
        ns_registry = lookup.get_namespace(ns)
        for local_name, cls in info.classes.items():
            ns_registry[local_name] = cls


def get_schema_lines() -> Sequence[str]:
    """Return a lines of XML schema declarations of registered extensions referencing a schema."""
    return [
        f'<xsd:import namespace="{ns}" schemaLocation="{info.schema_path.as_uri()}"/>'
        for ns, info in _registry.items()
        if info.schema_path is not None
    ]


def clear_registry() -> None:
    """Remove all registered extension classes. Useful for test isolation."""
    _registry.clear()
