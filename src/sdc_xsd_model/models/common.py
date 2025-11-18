"""Common XML Schema Definition (XSD) elements and types."""

import typing
from collections.abc import Mapping, Sequence

import lxml.etree


class ElementBase(lxml.etree.ElementBase):
    """https://lxml.de/api/lxml.etree.ElementBase-class.html."""

    TAG: str

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
        return lxml.etree.tostring(self).decode()

    def __repr__(self) -> str:
        return self.__str__()


class AnyUri(ElementBase):
    pass


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
