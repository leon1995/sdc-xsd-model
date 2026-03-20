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

import lxml.etree

if typing.TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence

    from sdc_xsd_model.core import common

_TAG_RE = re.compile(r"\{(?P<ns>[^}]+)\}(?P<local>.+)")


@dataclasses.dataclass
class _NamespaceInfo:
    prefix: str | None = None
    schema_path: pathlib.Path | None = None
    classes: dict[str, type[common.ElementBase]] = dataclasses.field(default_factory=dict)


__REGISTRY__: dict[str, _NamespaceInfo] = {}


def _parse_tag(tag: str) -> tuple[str, str]:
    """Extract ``(namespace, local_name)`` from a Clark-notation TAG string."""
    m = _TAG_RE.match(tag)
    if not m:
        msg = f"TAG must be in Clark notation '{{namespace}}localname', got: {tag!r}"
        raise ValueError(msg)
    return m.group("ns"), m.group("local")


def _register_class[T: common.ElementBase](
    cls: type[T],
    prefix: str | None = None,
    schema_path: pathlib.Path | None = None,
) -> type[T]:
    ns, local_name = _parse_tag(cls.TAG)

    if ns not in __REGISTRY__:
        __REGISTRY__[ns] = _NamespaceInfo()
    info = __REGISTRY__[ns]

    if prefix is not None:
        if info.prefix:
            msg = f"Namespace {ns} already has a registered prefix: {info.prefix}"
            raise ValueError(msg)
        info.prefix = prefix
        lxml.etree.register_namespace(prefix, ns)
    if schema_path is not None:
        info.schema_path = schema_path.absolute() if not schema_path.is_absolute() else schema_path

    if local_name in info.classes:
        msg = f"{cls.TAG} already registered"
        raise RuntimeError(msg)
    info.classes[local_name] = cls
    return cls


@typing.overload
def register_extension[T: common.ElementBase](cls: type[T], /) -> type[T]: ...


@typing.overload
def register_extension[T: common.ElementBase](
    *,
    prefix: str | None = None,
    schema_path: pathlib.Path | None = None,
) -> typing.Callable[[type[T]], type[T]]: ...


def register_extension[T: common.ElementBase](
    cls: type[T] | None = None,
    /,
    *,
    prefix: str | None = None,
    schema_path: pathlib.Path | None = None,
) -> type[T] | typing.Callable[[type[T]], type[T]]:
    """Register an ``ElementBase`` subclass for automatic namespace class lookup.

    Can be used as a bare decorator (``@register_extension``) or with arguments
    (``@register_extension(prefix="myext", schema_path=Path("custom.xsd"))``).
    """
    if cls is not None:
        # Bare @register_extension (no parentheses)
        return _register_class(cls, prefix=prefix, schema_path=schema_path)

    # Called with arguments — return the real decorator
    def decorator(cls: type[T]) -> type[T]:
        return _register_class(cls, prefix=prefix, schema_path=schema_path)

    return decorator


def set_lookup(lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
    """Register all custom extension classes from the registry into *lookup*."""
    for ns, info in __REGISTRY__.items():
        ns_registry = lookup.get_namespace(ns)
        for local_name, cls in info.classes.items():
            ns_registry[local_name] = cls


def get_schema_lines() -> Sequence[str]:
    """Return a lines of XML schema declarations of registered extensions referencing a schema."""
    return [
        f'<xsd:import namespace="{ns}" schemaLocation="{info.schema_path.as_uri()}"/>'
        for ns, info in __REGISTRY__.items()
        if info.schema_path is not None
    ]
