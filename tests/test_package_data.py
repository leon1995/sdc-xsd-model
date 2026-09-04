"""Tests that the schema files and the PEP 561 marker ship with the package.

Every core model module builds an :class:`lxml.etree.XMLSchema` from ``SCHEMA_PATH`` **at module scope**, so a
distribution that omits an ``.xsd`` fails at *import* time rather than on first use. Nothing else in the suite
reaches that path: the working tree always has the files, so a packaging regression only shows up once someone
installs the wheel. These tests assert the files are reachable through :mod:`importlib.resources` -- the API
that behaves the same for a source checkout, a wheel and a zipimport -- rather than through the ``__file__``
arithmetic the modules themselves use.

Note the schema documents are checked for being well-formed XSD *documents*, not compiled with
:class:`lxml.etree.XMLSchema`. Compiling requires resolving ``xsd:import`` relative to the document's base URL,
which reading bytes through ``importlib.resources`` deliberately discards; ``test_schema_compiled_at_import``
covers compilation instead, since that is what the modules do.
"""

from __future__ import annotations

import importlib
import importlib.resources
import pathlib
import pkgutil
import typing

import lxml.etree
import pytest

import sdc_xsd_model

XSD_NAMESPACE: typing.Final[str] = "http://www.w3.org/2001/XMLSchema"


def _modules_with(attribute: str) -> list[str]:
    """Return every importable module in the package exposing *attribute*.

    Discovered rather than hard-coded so a new model module is covered the moment it is added, instead of
    silently escaping these tests.
    """
    return sorted(
        module.name
        for module in pkgutil.walk_packages(sdc_xsd_model.__path__, prefix=f"{sdc_xsd_model.__name__}.")
        if hasattr(importlib.import_module(module.name), attribute)
    )


# Modules declaring a schema path. The SDPi extension modules expose SCHEMA_PATH only -- their schemas are
# compiled by ExtensionRegistry, not at module scope -- so the two lists differ and are collected separately.
SCHEMA_PATH_MODULES: typing.Final[list[str]] = _modules_with("SCHEMA_PATH")
SCHEMA_MODULES: typing.Final[list[str]] = _modules_with("SCHEMA")


def test_schema_modules_discovered() -> None:
    """Guard the discovery itself: empty lists would make every parametrised test below vacuous."""
    assert SCHEMA_PATH_MODULES, "no module exposing SCHEMA_PATH was found"
    assert SCHEMA_MODULES, "no module exposing SCHEMA was found"
    # Anything compiling a schema must also say where it came from.
    assert not set(SCHEMA_MODULES) - set(SCHEMA_PATH_MODULES)


@pytest.mark.parametrize("module_name", SCHEMA_PATH_MODULES)
def test_schema_path_exists(module_name: str) -> None:
    """``SCHEMA_PATH`` points at a file that is actually present."""
    schema_path = importlib.import_module(module_name).SCHEMA_PATH
    assert isinstance(schema_path, pathlib.Path)
    assert schema_path.is_file(), f"{module_name}.SCHEMA_PATH does not exist: {schema_path}"


@pytest.mark.parametrize("module_name", SCHEMA_PATH_MODULES)
def test_schema_is_reachable_as_package_data(module_name: str) -> None:
    """The schema resolves through ``importlib.resources``, i.e. it is package data and not a stray file."""
    schema_path = importlib.import_module(module_name).SCHEMA_PATH
    anchor = importlib.resources.files(sdc_xsd_model)
    # Core schemas live in the shared xsd/ directory; each SDPi extension ships its schema beside its module.
    if schema_path.parent.name == "xsd":
        resource = anchor.joinpath("xsd", schema_path.name)
    else:
        relative = schema_path.parent.relative_to(pathlib.Path(str(anchor)))
        resource = anchor.joinpath(*relative.parts, schema_path.name)
    assert resource.is_file(), f"{schema_path.name} is not package data ({resource})"
    # Parsing proves the shipped bytes are an XSD document, not merely a file of the right name.
    root = lxml.etree.fromstring(resource.read_bytes())
    assert root.tag == f"{{{XSD_NAMESPACE}}}schema"


@pytest.mark.parametrize("module_name", SCHEMA_MODULES)
def test_schema_compiled_at_import(module_name: str) -> None:
    """``SCHEMA`` is compiled at module scope, which is what makes a missing schema an import-time failure."""
    assert isinstance(importlib.import_module(module_name).SCHEMA, lxml.etree.XMLSchema)


def test_py_typed_marker_ships() -> None:
    """PEP 561: without this marker a type checker ignores the package's annotations entirely."""
    assert importlib.resources.files(sdc_xsd_model).joinpath("py.typed").is_file()
