"""Converters from XML Schema lexical representations to Python values.

Every converter passes ``None`` through unchanged so that an absent attribute or element stays absent,
and raises :class:`ValueError` for input outside the lexical space of the corresponding XSD type.
The lexical spaces follow https://www.w3.org/TR/xmlschema11-2/ (XML Schema 1.1 Part 2: Datatypes).

``boolean``, ``integer``, ``decimal``, ``QName`` and the date and time types all carry a fixed
``whiteSpace="collapse"``
facet, so surrounding whitespace is collapsed away before validation. Enumeration facets are checked
against the *value space* rather than the lexical space; for the ``xsd:string`` based enumerations of this
model that amounts to a verbatim comparison -- see :func:`to_enum`.
"""

from __future__ import annotations

import calendar
import dataclasses
import datetime
import decimal
import enum
import re
import typing

import lxml.etree

if typing.TYPE_CHECKING:
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


# ── xsd:dateTime and its truncated forms ───────────────────────────────────────────────────────────

_MONTHS_PER_YEAR: typing.Final[int] = 12
_MIDNIGHT_HOUR: typing.Final[int] = 24
_MICROSECOND_DIGITS: typing.Final[int] = 6

# Lexical space of xsd:dateTime and of the three shorter forms that omit a trailing part of it. Written
# out rather than delegated to datetime.fromisoformat, which accepts the basic format ("20200517") and
# rejects the years outside 1..9999 that these types allow.
_DATE_TIME_PATTERN: typing.Final[re.Pattern[str]] = re.compile(
    r"(?P<year>-?(?:[1-9][0-9]{3,}|0[0-9]{3}))"
    r"(?:-(?P<month>0[1-9]|1[0-2])"
    r"(?:-(?P<day>0[1-9]|[12][0-9]|3[01])"
    r"(?:T(?P<hour>[01][0-9]|2[0-4]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])"
    r"(?:\.(?P<fraction>[0-9]+))?)?)?)?"
    r"(?P<tz>Z|[+-](?:(?:0[0-9]|1[0-3]):[0-5][0-9]|14:00))?",
)


class DateTimePrecision(enum.StrEnum):
    """How much of a date and time a value states; the member value is the name of the XSD type."""

    YEAR = "gYear"
    YEAR_MONTH = "gYearMonth"
    DATE = "date"
    DATE_TIME = "dateTime"


def _parse_timezone(value: str | None) -> datetime.timezone | None:
    """Convert the optional timezone suffix that every date and time type may carry to a fixed offset."""
    if value is None:
        return None
    if value == "Z":
        return datetime.UTC
    hours, _, minutes = value[1:].partition(":")
    offset = datetime.timedelta(hours=int(hours), minutes=int(minutes))
    return datetime.timezone(-offset if value.startswith("-") else offset)


def _next_day(year: int, month: int, day: int) -> tuple[int, int, int]:
    """Advance a date by one day, without the 1..9999 year range that datetime arithmetic imposes."""
    if day < calendar.monthrange(year, month)[1]:
        return year, month, day + 1
    if month < _MONTHS_PER_YEAR:
        return year, month + 1, 1
    # XML Schema 1.0 has no year zero, so year -1 is followed by year 1.
    return (year + 2 if year == -1 else year + 1), 1, 1


def _serialize_timezone(tzinfo: datetime.timezone) -> str:
    """Return the lexical form of a timezone offset, using the canonical ``Z`` for UTC."""
    offset = tzinfo.utcoffset(None)
    assert offset is not None
    if not offset:
        return "Z"
    hours, minutes = divmod(abs(offset) // datetime.timedelta(minutes=1), 60)
    return f"{'-' if offset < datetime.timedelta(0) else '+'}{hours:02d}:{minutes:02d}"


@dataclasses.dataclass(frozen=True, slots=True)
class XsdDateTime:
    """A point in time stated as a year, a year and month, a full date, or a full timestamp.

    ``pm:PatientDemographicsCoreData/DateOfBirth`` is declared as a union of ``xsd:dateTime``,
    ``xsd:date``, ``xsd:gYearMonth`` and ``xsd:gYear``, so a conforming document may state any of those
    four precisions in the same element. Their lexical spaces are disjoint, so the form a value was
    written in is unambiguous, and :attr:`precision` reports it.

    The components are kept as plain integers rather than as a :class:`datetime.date`, because these
    types admit any number of year digits and a negative year -- both ``"-0045"`` and ``"12020"`` are
    valid -- while :class:`datetime.datetime` covers only the years 1 to 9999. Use :meth:`to_datetime`
    where a concrete point in time is needed.

    ``time`` is always naive: the timezone offset, which each of the four types may carry, lives in
    ``tzinfo`` so that it survives at a precision that has no time of day.
    """

    year: int
    month: int | None = None
    day: int | None = None
    time: datetime.time | None = None
    tzinfo: datetime.timezone | None = None

    def __post_init__(self) -> None:
        """Reject the states that no lexical form denotes.

        Raises:
            ValueError: if the year is zero, a component is out of range, a component is stated without
                the coarser one it refines, or ``time`` carries a timezone of its own.

        """
        if self.year == 0:
            msg = "year zero does not exist in XML Schema 1.0"
            raise ValueError(msg)
        if self.day is not None and self.month is None:
            msg = "a day of month cannot be stated without a month"
            raise ValueError(msg)
        if self.time is not None and self.day is None:
            msg = "a time of day cannot be stated without a full date"
            raise ValueError(msg)
        if self.time is not None and self.time.tzinfo is not None:
            msg = "the timezone offset belongs in the tzinfo field, not in time"
            raise ValueError(msg)
        if self.month is not None:
            if not 1 <= self.month <= _MONTHS_PER_YEAR:
                msg = f"month {self.month} is out of range"
                raise ValueError(msg)
            # The lexical space allows any day from 1 to 31; the value space does not.
            if self.day is not None and not 1 <= self.day <= calendar.monthrange(self.year, self.month)[1]:
                msg = f"day {self.day} is out of range for month {self.month} of year {self.year}"
                raise ValueError(msg)

    @property
    def precision(self) -> DateTimePrecision:
        """Return the union member type whose lexical form this value was written in."""
        if self.time is not None:
            return DateTimePrecision.DATE_TIME
        if self.day is not None:
            return DateTimePrecision.DATE
        if self.month is not None:
            return DateTimePrecision.YEAR_MONTH
        return DateTimePrecision.YEAR

    @classmethod
    def deserialize(cls, value: str) -> typing.Self:
        """Convert an ``xsd:dateTime``, ``xsd:date``, ``xsd:gYearMonth`` or ``xsd:gYear`` literal.

        The hour ``24`` denotes midnight of the following day and is normalized to it, since both
        lexical forms map to the same value.

        Fractional seconds are truncated to the microseconds :class:`datetime.time` can hold; XML Schema
        requires only milliseconds to be supported, see
        https://www.w3.org/TR/xmlschema11-2/#partial-implementation.

        Raises:
            ValueError: if *value* is outside the lexical space of all four types.

        """
        match = _DATE_TIME_PATTERN.fullmatch(_collapse(value))
        if match is None:
            msg = (
                f"{value!r} is not a valid xsd:dateTime, xsd:date, xsd:gYearMonth or xsd:gYear literal, "
                f"expected CCYY[-MM[-DD[Thh:mm:ss[.sss]]]] with an optional timezone"
            )
            raise ValueError(msg)
        groups = match.groupdict()
        year = int(groups["year"])
        month = int(groups["month"]) if groups["month"] is not None else None
        day = int(groups["day"]) if groups["day"] is not None else None
        tzinfo = _parse_timezone(groups["tz"])
        if groups["hour"] is None:
            return cls(year=year, month=month, day=day, tzinfo=tzinfo)

        hour = int(groups["hour"])
        minute = int(groups["minute"])
        second = int(groups["second"])
        fraction = groups["fraction"] or ""
        microsecond = int(fraction[:_MICROSECOND_DIGITS].ljust(_MICROSECOND_DIGITS, "0")) if fraction else 0
        if hour == _MIDNIGHT_HOUR:
            if minute or second or microsecond:
                msg = f"the hour 24 in {value!r} denotes midnight, so it admits no minutes or seconds"
                raise ValueError(msg)
            # The nesting of the pattern guarantees a full date once an hour has matched.
            assert month is not None
            assert day is not None
            year, month, day = _next_day(year, month, day)
            hour = 0
        return cls(
            year=year,
            month=month,
            day=day,
            time=datetime.time(hour, minute, second, microsecond),
            tzinfo=tzinfo,
        )

    @classmethod
    def from_datetime(cls, value: datetime.datetime) -> typing.Self:
        """Create a full-precision value from a :class:`datetime.datetime`.

        An aware *value* keeps the UTC offset it had at that instant, since a fixed offset is all the XSD
        types can express -- a named timezone is therefore reduced to one.
        """
        offset = value.utcoffset()
        return cls(
            year=value.year,
            month=value.month,
            day=value.day,
            time=value.time(),
            tzinfo=datetime.timezone(offset) if offset is not None else None,
        )

    def serialize(self) -> str:
        """Return the canonical lexical form of the type named by :attr:`precision`.

        Two literals do not come back verbatim, because in each case both forms denote the same value:
        an hour of ``24`` comes back as midnight of the following day, and a ``+00:00`` offset as ``Z``.
        """
        parts = [f"-{abs(self.year):04d}" if self.year < 0 else f"{self.year:04d}"]
        if self.month is not None:
            parts.append(f"-{self.month:02d}")
        if self.day is not None:
            parts.append(f"-{self.day:02d}")
        if self.time is not None:
            # isoformat() pads the fraction to six digits; the canonical form has no trailing zeros.
            formatted = self.time.isoformat()
            parts.append(f"T{formatted.rstrip('0') if self.time.microsecond else formatted}")
        if self.tzinfo is not None:
            parts.append(_serialize_timezone(self.tzinfo))
        return "".join(parts)

    def to_datetime(self) -> datetime.datetime:
        """Return this value as a :class:`datetime.datetime`, defaulting the components it omits.

        An absent month or day becomes 1 and an absent time becomes midnight, so ``"2020-05"`` becomes
        2020-05-01T00:00:00. The timezone offset, where there is one, is kept.

        Raises:
            ValueError: if the year is outside the 1 to 9999 range that :class:`datetime.date` supports.

        """
        return datetime.datetime.combine(
            datetime.date(self.year, self.month or 1, self.day or 1),
            self.time or datetime.time(),
            tzinfo=self.tzinfo,
        )

    def __str__(self) -> str:
        return self.serialize()


class DateTimeConverter:
    """Converter for xsd:dateTime values."""

    @staticmethod
    def deserialize(value: str) -> datetime.datetime:
        """Convert an ``xsd:dateTime`` literal to a :class:`datetime.datetime`.

        Raises:
            ValueError: if *value* is not a valid ``xsd:dateTime`` literal. That includes the shorter
                ``xsd:date``, ``xsd:gYearMonth`` and ``xsd:gYear`` forms, which are valid literals of
                their own types but not of this one, and a year that :class:`datetime.datetime` cannot
                represent.

        """
        parsed = XsdDateTime.deserialize(value)
        if parsed.precision is not DateTimePrecision.DATE_TIME:
            msg = f"{value!r} is an xsd:{parsed.precision} literal, not the xsd:dateTime that is required here"
            raise ValueError(msg)
        return parsed.to_datetime()

    @staticmethod
    def serialize(value: datetime.datetime) -> str:
        """Return the canonical ``xsd:dateTime`` lexical form of *value*."""
        return XsdDateTime.from_datetime(value).serialize()
