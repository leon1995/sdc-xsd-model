"""Converters from XML Schema lexical representations to Python values.

Every converter passes ``None`` through unchanged so that an absent attribute or element stays absent,
and raises :class:`ValueError` for input outside the lexical space of the corresponding XSD type.
The lexical spaces follow https://www.w3.org/TR/xmlschema11-2/ (XML Schema 1.1 Part 2: Datatypes).

``boolean``, ``integer``, ``decimal`` and ``QName`` all carry a fixed ``whiteSpace="collapse"``
facet, so surrounding whitespace is collapsed away before validation. Enumeration facets are checked
against the *value space* rather than the lexical space; for the ``xsd:string`` based enumerations of this
model that amounts to a verbatim comparison -- see :func:`to_enum`.
"""

from __future__ import annotations

import datetime
import decimal
import re
import typing

import lxml.etree

if typing.TYPE_CHECKING:
    import enum
    from collections.abc import Mapping

TRUE_LEXICAL_VALUES: typing.Final[frozenset[str]] = frozenset({"true", "1"})
FALSE_LEXICAL_VALUES: typing.Final[frozenset[str]] = frozenset({"false", "0"})

# Lexical spaces of the numeric types; Python's own parsers are more permissive
# (they accept underscores, "infinity", non-ASCII digits, ...), hence the explicit patterns.
_INTEGER_PATTERN: typing.Final[re.Pattern[str]] = re.compile(r"[+-]?[0-9]+")
# The regular expression the specification itself gives as equivalent to the decimalLexicalRep grammar.
_DECIMAL_PATTERN: typing.Final[re.Pattern[str]] = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)")


def _collapse(value: str) -> str:
    """Apply the ``whiteSpace="collapse"`` facet: trim and fold internal whitespace runs into single spaces."""
    return " ".join(value.split())


def to_bool(value: str | None) -> bool | None:
    """Convert an ``xsd:boolean`` lexical value to a Python ``bool``.

    ``booleanRep ::= 'true' | 'false' | '1' | '0'``, so ``1``/``0`` are accepted as well. The comparison is
    case-sensitive -- ``"True"`` is not a valid literal.
    See https://www.w3.org/TR/xmlschema11-2/#boolean.

    Raises:
        ValueError: if ``value`` is not a valid ``xsd:boolean`` literal.

    """
    if value is None:
        return None
    collapsed = _collapse(value)
    if collapsed in TRUE_LEXICAL_VALUES:
        return True
    if collapsed in FALSE_LEXICAL_VALUES:
        return False
    msg = f"{value!r} is not a valid xsd:boolean literal, expected one of: true, false, 1, 0"
    raise ValueError(msg)


def to_int(value: str | None) -> int | None:
    """Convert an ``xsd:integer`` derived lexical value to a Python ``int``.

    Covers ``xsd:integer``, ``xsd:int``, ``xsd:long``, ``xsd:short``, ``xsd:byte`` and their unsigned
    counterparts: the shared lexical space is one or more digits with an optional leading sign, and no
    trailing decimal point. Leading zeros are permitted -- only the *canonical* representation prohibits
    them and the redundant ``"+"``, so ``"+007"`` is 7. The value range facets that distinguish those types
    are *not* checked here -- schema validation covers them.
    See https://www.w3.org/TR/xmlschema11-2/#integer.

    Raises:
        ValueError: if ``value`` is not a valid integer literal.

    """
    if value is None:
        return None
    collapsed = _collapse(value)
    if _INTEGER_PATTERN.fullmatch(collapsed) is None:
        msg = f"{value!r} is not a valid xsd:integer literal, expected an optionally signed sequence of digits"
        raise ValueError(msg)
    return int(collapsed)


def to_decimal(value: str | None) -> decimal.Decimal | None:
    """Convert an ``xsd:decimal`` lexical value to a :class:`decimal.Decimal`.

    ``xsd:decimal`` allows an optional sign and a decimal point, but -- unlike :class:`decimal.Decimal`
    itself -- neither exponents (``"1E5"``) nor the special values ``Infinity``/``NaN``.
    See https://www.w3.org/TR/xmlschema11-2/#decimal.

    Raises:
        ValueError: if ``value`` is not a valid ``xsd:decimal`` literal.

    """
    if value is None:
        return None
    collapsed = _collapse(value)
    if _DECIMAL_PATTERN.fullmatch(collapsed) is None:
        msg = f"{value!r} is not a valid xsd:decimal literal, exponents and Infinity/NaN are not permitted"
        raise ValueError(msg)
    return decimal.Decimal(collapsed)


def to_qname(value: str | None, nsmap: Mapping[str | None, str]) -> lxml.etree.QName | None:
    """Convert an ``xsd:QName`` lexical value to an :class:`lxml.etree.QName`.

    The value space of ``xsd:QName`` is the set of ``(namespace name, local part)`` tuples, which is what
    :class:`lxml.etree.QName` models. A prefixed name is resolved against *nsmap*, an unprefixed one against
    the default namespace (``nsmap[None]``) if one is in scope. Clark notation (``"{namespace}localName"``)
    is passed through, so a value produced by lxml itself round-trips.
    See https://www.w3.org/TR/xmlschema11-2/#QName.

    Args:
        value: the lexical value, typically from ``element.get(...)`` or ``element.text``.
        nsmap: the namespace declarations in scope, typically ``element.nsmap``.

    Raises:
        ValueError: if *value* is malformed or uses a prefix that is not declared in *nsmap*.

    """
    if value is None:
        return None
    collapsed = _collapse(value)
    if collapsed.startswith("{"):
        try:
            return lxml.etree.QName(collapsed)
        except ValueError as error:
            msg = f"{value!r} is not a valid QName in Clark notation"
            raise ValueError(msg) from error
    prefix, colon, local_name = collapsed.rpartition(":")
    if not local_name or ":" in prefix or (colon and not prefix):
        msg = f"{value!r} is not a valid xsd:QName literal, expected 'localName' or 'prefix:localName'"
        raise ValueError(msg)
    namespace = nsmap.get(prefix or None)
    if prefix and namespace is None:
        msg = f"prefix {prefix!r} of QName {value!r} is not declared in the given namespace map"
        raise ValueError(msg)
    return lxml.etree.QName(namespace, local_name)


def to_enum[E: enum.Enum](value: str | None, enum_type: type[E]) -> E | None:
    """Convert a lexical value constrained by ``xsd:enumeration`` facets to a member of *enum_type*.

    The ``enumeration`` facet constrains the *value space*, not the lexical space, so a literal is mapped
    to a value first and that value is compared for equality. Every enumeration in these schemas restricts
    ``xsd:string``, whose lexical mapping is the identity, so here value equality is verbatim string
    equality. That would no longer hold for an enumeration over a numeric type, where ``"+2"``, ``"2"`` and
    ``"2.0"`` all denote the same value. See https://www.w3.org/TR/xmlschema11-2/#rf-enumeration.

    Raises:
        ValueError: if *value* is not one of the values of *enum_type*.

    """
    if value is None:
        return None
    try:
        return enum_type(value)
    except ValueError as error:
        permitted = ", ".join(str(member.value) for member in enum_type)
        msg = f"{value!r} is not a valid {enum_type.__name__} value, expected one of: {permitted}"
        raise ValueError(msg) from error


class DurationConverter:
    """Converter for xsd:duration values."""

    # https://profiles.ihe.net/DEV/SDPi/#r1018
    SDPI_REGEX_DURATION: typing.Final[re.Pattern[str]] = re.compile(
        r"^(?P<sign>-)?PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?"
        r"(?:(?P<seconds>\d+)(?:\.(?P<fraction>\d+))?S)?(?<!PT)$",
    )

    @staticmethod
    def deserialize(date_string: str, *, allow_negative: bool = False) -> datetime.timedelta:
        """XML Schema duration, constrained to hours, minutes and seconds.

        SDPi explicitly requires this constraint for the Expires attributes. However, we apply it to all
        xsd:duration elements. See https://profiles.ihe.net/DEV/SDPi/#r1018 for more details

        A leading ``"-"`` is rejected unless *allow_negative* is set. xsd:duration itself permits a negative
        duration, and only wse:Expires is bounded by its schema (wse:NonNegativeDurationType, via a
        minInclusive facet), but every duration in the core models is a period, delay, timeout or resolution
        for which a negative value is meaningless. sdpi:Epoch/@Offset is the one signed duration here.

        Raises:
            ValueError: if *date_string* is outside the supported lexical space, or is negative while
                *allow_negative* is not set.

        """
        match = DurationConverter.SDPI_REGEX_DURATION.match(date_string)
        if match is None:
            msg = f"xsd:duration string {date_string} not matching SDPI 1018 regex for durations"
            raise ValueError(msg)
        groups = match.groupdict()
        if groups["sign"] and not allow_negative:
            msg = f"negative xsd:duration {date_string} is not supported here"
            raise ValueError(msg)
        seconds = groups["seconds"] or "0"
        fraction = groups["fraction"] or "0"
        delta = datetime.timedelta(
            hours=int(groups["hours"] or 0),
            minutes=int(groups["minutes"] or 0),
            seconds=float(f"{seconds}.{fraction}"),
        )
        return -delta if groups["sign"] else delta

    @staticmethod
    def serialize(delta: datetime.timedelta, *, allow_negative: bool = False) -> str:
        """Create an ISO 8601 durations value containing seconds.

        A negative *delta* is rejected unless *allow_negative* is set, mirroring :meth:`deserialize`; when
        it is set, the value is emitted with a leading ``"-"``.

        Note: Smaller fractions than microseconds are rounded based in the seventh digit.
              The referenced ISO8601 from 1988 in XML 1.1 does not restrict the precision, but in part 2 5.4 the minimal
              supported fraction-second duration is set to
              milliseconds https://www.w3.org/TR/xmlschema11-2/#partial-implementation, so microseconds should be safe
        """
        if delta < datetime.timedelta(0) and not allow_negative:
            msg = f"negative xsd:duration {delta} is not supported here"
            raise ValueError(msg)
        if not delta:
            return "PT0S"

        sign = "-" if delta < datetime.timedelta(0) else ""
        magnitude = abs(delta)
        total_us = magnitude.days * 86_400_000_000 + magnitude.seconds * 1_000_000 + magnitude.microseconds
        total_secs, us = divmod(total_us, 1_000_000)
        hours, remainder = divmod(total_secs, 3600)
        minutes, secs = divmod(remainder, 60)

        parts: list[str] = [f"{sign}PT"]
        if hours:
            parts.append(f"{hours}H")
        if minutes:
            parts.append(f"{minutes}M")
        if secs or us:
            if us:
                frac = str(us).zfill(6).rstrip("0")
                parts.append(f"{secs}.{frac}S")
            else:
                parts.append(f"{secs}S")

        return "".join(parts)
