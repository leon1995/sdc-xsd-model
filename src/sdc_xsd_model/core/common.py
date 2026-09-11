"""Common XML Schema Definition (XSD) elements and types."""

from __future__ import annotations

import types
import typing
import uuid

import lxml.etree

from sdc_xsd_model import converter

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def element_classes(element: type[ElementBase] | typing.TypeAliasType) -> tuple[type, ...]:
    """Flatten *element* into the concrete classes it stands for, as ``isinstance`` needs them.

    ``isinstance`` rejects a PEP 695 ``type`` alias outright -- "arg 2 must be a type, a tuple of types, or a
    union" -- and it rejects a union that *contains* one just as firmly. That second case is the one that
    matters here: ``ABSTRACT_STATE`` is a union of ``ABSTRACT_CONTEXT_STATE``, ``ABSTRACT_ALERT_STATE`` and
    three more aliases, so unwrapping a single level yields a union of aliases and fails the same way. Hence
    the recursion.
    """
    if isinstance(element, typing.TypeAliasType):
        return element_classes(element.__value__)
    if isinstance(element, types.UnionType):
        return tuple(one for member in typing.get_args(element) for one in element_classes(member))
    return (typing.cast("type", element),)


def _mismatch_message(name: str, element: type[ElementBase] | typing.TypeAliasType, found: object) -> str:
    """Describe a child that is not the class its accessor promises.

    Two causes wear the same exception. A *different* registered class is about the document; an element
    with no class attached at all means nothing is wrong with the document -- the class was never
    registered, or the caller used a module-local parser -- so say which one it is.
    """
    expected = element.__name__
    if not isinstance(found, ElementBase):
        return (
            f"{name} did not deserialize to {expected}: it is a plain lxml.etree._Element. Either "
            f"{expected} is missing from its module's set_lookup, or this document was parsed by a "
            f"module-local get_parser() that does not register the namespace of {name} -- "
            f"parser.sdc_parser registers every module."
        )
    return f"{name} is a {type(found).__name__}, not a {expected}"


def _checked(
    found: lxml.etree._Element | None,
    element: type[ElementBase] | typing.TypeAliasType,
    name: str,
) -> typing.Any:  # noqa: ANN401
    """Return *found* when it is an *element*, else raise.

    An absent child is not a mismatch: an optional element is absent on the wire all the time, and the
    accessors that require one guard that themselves.
    """
    if found is None or isinstance(found, element_classes(element)):
        return found
    raise TypeError(_mismatch_message(name, element, found))


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

        @property
        def nsmap(self) -> Mapping[str | None, str]:
            """https://lxml.de/api/lxml.etree._Element-class.html#nsmap."""

    @typing.overload
    def find_child[E: ElementBase](self, name: str, element: type[E]) -> E | None: ...

    @typing.overload
    # ``object`` rather than ``typing.TypeAliasType``: a ``type`` alias in argument position is a type
    # form, not a value of that class, so a type checker rejects the precise annotation. The class
    # overload above still binds ``E`` exactly, so only the alias case widens.
    def find_child(self, name: str, element: object) -> typing.Any: ...  # noqa: ANN401

    def find_child[E: ElementBase](self, name: str, element: type[E] | typing.TypeAliasType) -> E | None:
        """Return the child named *name*, verified to be an *element*.

        *name* is a fully qualified ``{namespace}local`` tag rather than a local name, because a child does
        not always share its parent's namespace -- the message model is full of ``pm:`` children inside
        ``msg:`` elements, and deriving the namespace from the caller would put a silent
        wrong-namespace failure back where one has already shipped once.

        *element* may be a class or a ``type`` alias for a union of classes, which is what the abstract
        state and descriptor accessors need; a union cannot be a ``TAG``, so those reach this method rather
        than :meth:`find_by_element`.

        :raises TypeError: the child is present but is not an *element*. This is the check the
            ``typing.cast`` these accessors used to perform did not do: an unregistered class or a
            module-local parser fails here, naming the class, instead of reaching the caller as a plain
            ``_Element`` that raises ``AttributeError`` on the first property read.
        """
        return _checked(self.find(name), element, name)

    @typing.overload
    def findall_child[E: ElementBase](self, name: str, element: type[E]) -> Sequence[E]: ...

    @typing.overload
    # ``object`` rather than ``typing.TypeAliasType``: a ``type`` alias in argument position is a type
    # form, not a value of that class, so a type checker rejects the precise annotation. The class
    # overload above still binds ``E`` exactly, so only the alias case widens.
    def findall_child(self, name: str, element: object) -> typing.Any: ...  # noqa: ANN401

    def findall_child[E: ElementBase](self, name: str, element: type[E] | typing.TypeAliasType) -> Sequence[E]:
        """Return every child named *name*, each verified to be an *element*.

        Raises on the *first* child that is not an *element* rather than filtering: a mismatch means a
        registration or parser problem that affects every sibling, so returning the ones that happen to be
        typed would hide it. A caller that must tolerate junk still has ``findall``.

        :raises TypeError: some child is present but is not an *element*.
        """
        return [_checked(found, element, name) for found in self.findall(name)]

    def find_by_element[E: ElementBase](self, element: type[E]) -> E | None:
        """Return the child whose tag is *element*'s own ``TAG``, verified to be an *element*.

        The terse form of :meth:`find_child` for a class that has exactly one element name. A class
        registered under several names -- ``pm:CodedValue`` appears under 19 -- has no ``TAG`` and must name
        the child at the call site instead.
        """
        return self.find_child(element.TAG, element)

    def findall_by_element[E: ElementBase](self, element: type[E]) -> Sequence[E]:
        """Return every child whose tag is *element*'s own ``TAG``, each verified to be an *element*."""
        return self.findall_child(element.TAG, element)

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
