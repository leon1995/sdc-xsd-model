"""Structural tests over the namespace registrations each model module installs.

Two failure modes here are invisible at runtime. A class can carry a ``TAG`` that its module never registers,
and a ``set_lookup`` key can name something no schema declares. In both cases the element still parses -- it
just comes back as a plain ``lxml.etree._Element``, and because ``find_by_element`` is an unchecked
``typing.cast`` the caller is handed an object that only claims to be the typed class. The failure surfaces as
an ``AttributeError`` far from its cause, or as a property that silently returns ``None`` forever. See the
"Parser scope" note in CLAUDE.md.

These tests are cheap insurance against a rename: a case-insensitive search-and-replace once turned the
registration keys for ``Voltage`` and ``VoltageSpecified`` into ``VolTAGe`` and ``VolTAGeSpecified``, which
nothing detected because a missing registration is not an error.
"""

from __future__ import annotations

import inspect
import typing

import lxml.etree
import pytest

from sdc_xsd_model.core import (
    addressing,
    biceps_msg,
    biceps_pm,
    common,
    discovery,
    dpws,
    eventing,
    extension,
    mdpws,
    metadata_exchange,
    soap_envelope,
)

if typing.TYPE_CHECKING:
    import pathlib
    import types

XSD_NAMESPACE: typing.Final[str] = "http://www.w3.org/2001/XMLSchema"

# The same set ``parser.sdc_parser`` wires up.
CORE_MODULES: typing.Final[tuple[types.ModuleType, ...]] = (
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


class _RecordingLookup:
    """Stand-in for ``ElementNamespaceClassLookup`` that records what ``set_lookup`` writes.

    ``lxml``'s ``_ClassNamespaceRegistry`` offers no way to read its keys back, and ``set_lookup`` only ever
    calls ``get_namespace(...)`` and then ``ns[name] = cls``, so a plain dict per namespace is enough.
    """

    def __init__(self) -> None:
        self.entries: dict[str, dict[str, type]] = {}

    def get_namespace(self, namespace: str) -> dict[str, type]:
        return self.entries.setdefault(namespace, {})


def _recorded_entries(module: types.ModuleType) -> dict[str, dict[str, type]]:
    lookup = _RecordingLookup()
    module.set_lookup(lookup)  # ty:ignore[invalid-argument-type]
    return lookup.entries


def _declared_names(schema_path: pathlib.Path, seen: set[pathlib.Path] | None = None) -> set[str]:
    """Return every name a lookup key may legitimately use, following ``xsd:import``/``xsd:include``.

    Element names cover the normal case. Complex type names are included because the biceps registries double
    as the ``xsi:type`` resolver and as parent-context dispatch targets, both of which look a *type* name up in
    a namespace registry (see ``biceps_pm.set_lookup`` and ``element_class_lookup``). Imported schemas count
    because such a dispatch target may name a type from an imported namespace -- ``biceps_msg`` registers
    ``SampleArrayValue`` that way, since ``BICEPS_MessageModel.xsd`` imports the participant namespace and uses
    ``pm:SampleArrayValue`` for ``msg:ObservedValueStream/msg:Value/msg:Value``.

    Simple types are deliberately excluded: a simple type has no children, so no element class can ever be
    selected for one and a key naming a simple type is dead.
    """
    seen = set() if seen is None else seen
    schema_path = schema_path.resolve()
    if schema_path in seen or not schema_path.is_file():
        return set()
    seen.add(schema_path)
    tree = lxml.etree.parse(str(schema_path))
    names: set[str] = set()
    for kind in ("element", "complexType"):
        names.update(name for node in tree.iter(f"{{{XSD_NAMESPACE}}}{kind}") if (name := node.get("name")) is not None)
    for kind in ("import", "include"):
        for node in tree.iter(f"{{{XSD_NAMESPACE}}}{kind}"):
            location = node.get("schemaLocation")
            # Remote locations are not fetched; every schema this project validates against is vendored.
            if location is None or "://" in location:
                continue
            names |= _declared_names(schema_path.parent / location, seen)
    return names


def _own_tag_classes() -> list[tuple[str, type[common.ElementBase]]]:
    """Return every element class that declares its own ``TAG``, paired with its module name.

    A class that *inherits* its ``TAG`` shares an element name with its base -- ``LimitAlertConditionDescriptor``
    and ``AlertConditionDescriptor`` are both ``pm:AlertCondition``. There the base is registered for the
    element name and the subtype is reached through ``xsi:type``, so the subtype resolving to its base is
    correct rather than a defect. Keying on ``"TAG" in cls.__dict__`` expresses that without a hand-maintained
    exemption list.
    """
    found: list[tuple[str, type[common.ElementBase]]] = []
    for module in CORE_MODULES:
        for cls in vars(module).values():
            if not (inspect.isclass(cls) and issubclass(cls, common.ElementBase)):
                continue
            if cls.__module__ != module.__name__ or "TAG" not in cls.__dict__:
                continue
            found.append((module.__name__.rpartition(".")[2], cls))
    return found


OWN_TAG_CLASSES: typing.Final[list[tuple[str, type[common.ElementBase]]]] = _own_tag_classes()

LOOKUP_KEYS: typing.Final[list[tuple[str, str, str]]] = [
    (module.__name__.rpartition(".")[2], namespace, key)
    for module in CORE_MODULES
    for namespace, entries in _recorded_entries(module).items()
    for key in entries
]


@pytest.fixture(scope="module")
def composite_parser() -> lxml.etree.XMLParser:
    """Build a non-validating parser knowing every core namespace.

    Validation is deliberately off: most classes model elements that are only declared inside a complex type,
    so a bare instance of their tag is not a valid document. Registration is what is under test here.
    """
    lookup = lxml.etree.ElementNamespaceClassLookup()
    for module in CORE_MODULES:
        module.set_lookup(lookup)
    parser = lxml.etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    return parser


@pytest.mark.parametrize(
    ("module_name", "clazz"),
    OWN_TAG_CLASSES,
    ids=[f"{module_name}.{clazz.__name__}" for module_name, clazz in OWN_TAG_CLASSES],
)
def test_class_declaring_a_tag_deserializes_to_itself(
    module_name: str,
    clazz: type[common.ElementBase],
    composite_parser: lxml.etree.XMLParser,
) -> None:
    """A class that declares a TAG must be registered for it, or it can never deserialize."""
    namespace, _, local_name = clazz.TAG[1:].partition("}")
    xml = f'<p:{local_name} xmlns:p="{namespace}"/>'.encode()
    element = lxml.etree.fromstring(xml, parser=composite_parser)
    assert isinstance(element, clazz), (
        f"{module_name}.{clazz.__name__} declares TAG {clazz.TAG} but <{local_name}> deserialized to "
        f"{type(element).__name__}; add it to {module_name}.set_lookup"
    )


@pytest.mark.parametrize(
    ("module_name", "namespace", "key"),
    LOOKUP_KEYS,
    ids=[f"{module_name}:{key}" for module_name, _, key in LOOKUP_KEYS],
)
def test_lookup_key_names_something_the_schema_declares(module_name: str, namespace: str, key: str) -> None:
    """A registration key that matches no schema name is dead: nothing on the wire will ever hit it."""
    declared = {
        name for module in CORE_MODULES if namespace == module.NAMESPACE for name in _declared_names(module.SCHEMA_PATH)
    }
    assert key in declared, (
        f"{module_name}.set_lookup registers {key!r} in {namespace}, which declares no element or type of "
        f"that name -- the entry is unreachable"
    )
