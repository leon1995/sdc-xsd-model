"""Lxml models for Extension Point elements from IEEE 11073-10207-2017."""

from __future__ import annotations

import pathlib
import typing

import lxml.etree

PREFIX: typing.Final[str] = "mdpws"
NAMESPACE: typing.Final[str] = "http://standards.ieee.org/downloads/11073/11073-20702-2016"

lxml.etree.register_namespace(PREFIX, NAMESPACE)

SCHEMA_PATH: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent.parent.joinpath("xsd", "MDPWS.xsd").absolute()
SCHEMA: typing.Final[lxml.etree.XMLSchema] = lxml.etree.XMLSchema(file=SCHEMA_PATH)
