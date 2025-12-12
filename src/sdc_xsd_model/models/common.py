"""Common XML Schema Definition (XSD) elements and types."""

import typing
import uuid
from collections.abc import Mapping, Sequence

import lxml.etree


class ElementBase(lxml.etree.ElementBase):
    """https://lxml.de/api/lxml.etree.ElementBase-class.html."""

    TAG: str
    PARSER: lxml.etree.XMLParser | None

    if typing.TYPE_CHECKING:

        def __init__(
            self,
            *children: "str | ElementBase",
            attrib: Mapping[str, str | bytes] | None = None,
            nsmap: Mapping[None | str, str] | None = None,
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
        return typing.cast("type[E] | None", self.find(element.TAG))

    def findall_by_element[E: ElementBase](self, element: type[E]) -> Sequence[E]:
        return typing.cast("Sequence[E]", self.findall(element.TAG))

    def __str__(self) -> str:
        return lxml.etree.tostring(self).decode()

    def __repr__(self) -> str:
        return self.__str__()


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
        if self.text is None:
            return None
        if "{" in self.text and "}" in self.text:
            return lxml.etree.QName(self.text)
        if ":" in self.text:
            prefix, tag = self.text.split(":", 1)
            namespace = self.nsmap.get(prefix)
            return lxml.etree.QName(namespace, tag)
        return lxml.etree.QName(self.text)
