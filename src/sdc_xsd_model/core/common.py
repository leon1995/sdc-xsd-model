"""Common XML Schema Definition (XSD) elements and types."""

from __future__ import annotations

import typing
import uuid

import lxml.etree

from sdc_xsd_model import converter

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class ElementBase(lxml.etree.ElementBase):
    """https://lxml.de/api/lxml.etree.ElementBase-class.html."""

    TAG: str
    PARSER: lxml.etree.XMLParser | None

    if typing.TYPE_CHECKING:

        def __init__(
            self,
            *children: str | ElementBase,
            attrib: Mapping[str, str | bytes] | None = None,
            nsmap: Mapping[None | str, str] | Mapping[str, str] | None = None,
            **_extra: str | bytes,
        ) -> None: ...

    @property
    def text(self) -> str | None:
        """https://lxml.de/api/lxml.etree._Element-class.html#text."""
        return super().text

    @property
    def nsmap(self) -> Mapping[str | None, str]:
        """https://lxml.de/api/lxml.etree._Element-class.html#nsmap."""
        return super().nsmap

    def find_by_element[E: ElementBase](self, element: type[E]) -> E | None:
        return typing.cast("E | None", self.find(element.TAG))

    def findall_by_element[E: ElementBase](self, element: type[E]) -> Sequence[E]:
        return typing.cast("Sequence[E]", self.findall(element.TAG))

    def __str__(self) -> str:
        return bytes(self).decode()

    def __repr__(self) -> str:
        return self.__str__()

    def __bytes__(self) -> bytes:
        return lxml.etree.tostring(self)


class AnyUri(ElementBase):
    @classmethod
    def from_uri(cls, uri: str | uuid.UUID) -> typing.Self:
        """Create an AttributedURIType from a URI string or UUID."""
        return cls(uri.urn if isinstance(uri, uuid.UUID) else uri)

    @classmethod
    def from_random_uri(cls) -> typing.Self:
        """Create an AttributedURIType with a random UUID URN."""
        return cls.from_uri(uuid.uuid4())


class QNameType(ElementBase):
    @property
    def q_name(self) -> lxml.etree.QName | None:
        return converter.to_qname(self.text, self.nsmap)


class QNameListType(ElementBase):
    @property
    def q_names(self) -> Sequence[lxml.etree.QName]:
        if self.text is None:
            return []
        return [
            q_name
            for raw_qname in self.text.split()
            if (q_name := converter.to_qname(raw_qname, self.nsmap)) is not None
        ]


def with_implied[T](value: T | None, implied: T) -> T:
    """Return *value*, or *implied* when the attribute it came from was absent.

    BICEPS states defaults in ``xsd:documentation`` prose ("The implied value SHALL be ...") rather than as an
    XSD ``default``, so an absent optional attribute does **not** mean "unknown" -- it means the stated value.
    Accessors that apply one are named ``<name>_or_implied`` and sit beside the literal reading, so a caller can
    still tell whether the attribute was on the wire.
    """
    return implied if value is None else value


def _all_subclasses(cls: type[ElementBase]) -> set[type[ElementBase]]:
    """Recursively collect all subclasses of *cls*."""
    result: set[type[ElementBase]] = set()
    for sub in cls.__subclasses__():
        result.add(sub)
        result.update(_all_subclasses(sub))
    return result


def set_parser_on_subclasses(module_name: str, parser: lxml.etree.XMLParser) -> None:
    """Set ``PARSER`` on every ``ElementBase`` subclass defined in *module_name*."""
    for cls in _all_subclasses(ElementBase):
        if cls.__module__ == module_name:
            cls.PARSER = parser
