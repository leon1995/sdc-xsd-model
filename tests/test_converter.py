"""Tests for the XML Schema lexical value converters."""

import datetime
import decimal
import enum

import lxml.etree
import pytest

from sdc_xsd_model import converter


class _Colour(enum.StrEnum):
    RED = "Red"
    GREEN = "Green"


_NSMAP = {None: "urn:default", "pm": "urn:participant"}


# ── xsd:boolean ────────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("raw", ["true", "1", " true ", "\n1\t"])
def test_to_bool_true(raw: str) -> None:
    """Every lexical representation of true converts to True."""
    assert converter.to_bool(raw) is True


@pytest.mark.parametrize("raw", ["false", "0", " false ", "\n0\t"])
def test_to_bool_false(raw: str) -> None:
    """Every lexical representation of false converts to False."""
    assert converter.to_bool(raw) is False


@pytest.mark.parametrize("raw", ["True", "FALSE", "yes", "no", "", "2", "-1", "true false"])
def test_to_bool_invalid(raw: str) -> None:
    """Values outside the xsd:boolean lexical space are rejected."""
    with pytest.raises(ValueError, match="xsd:boolean"):
        converter.to_bool(raw)


# ── xsd:integer ────────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("0", 0), ("42", 42), ("-42", -42), ("+42", 42), ("007", 7), (" 42\n", 42), ("4294967296", 4294967296)],
)
def test_to_int(raw: str, expected: int) -> None:
    """Signed, zero-padded and out-of-int32-range digit sequences convert to int."""
    assert converter.to_int(raw) == expected


@pytest.mark.parametrize("raw", ["", "4.0", "1e5", "1_0", "0x10", "٤٢", "42 42", "- 42"])
def test_to_int_invalid(raw: str) -> None:
    """Values outside the xsd:integer lexical space are rejected."""
    with pytest.raises(ValueError, match="xsd:integer"):
        converter.to_int(raw)


# ── xsd:decimal ────────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1.5", "1.5"), ("-1.5", "-1.5"), ("+1.5", "1.5"), ("42", "42"), ("1.", "1"), (".5", "0.5"), (" 1.50 ", "1.50")],
)
def test_to_decimal(raw: str, expected: str) -> None:
    """Optionally signed fixed-point literals convert to Decimal, preserving precision."""
    assert converter.to_decimal(raw) == decimal.Decimal(expected)


def test_to_decimal_keeps_trailing_zeros() -> None:
    """The Decimal is built from the literal, so the written precision survives."""
    assert str(converter.to_decimal("1.50")) == "1.50"


@pytest.mark.parametrize("raw", ["", "1e5", "1E5", "NaN", "Infinity", "INF", "1_0", "."])
def test_to_decimal_invalid(raw: str) -> None:
    """Exponents and the special values that decimal.Decimal would accept are rejected."""
    with pytest.raises(ValueError, match="xsd:decimal"):
        converter.to_decimal(raw)


# ── xsd:QName ──────────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("pm:Mds", "{urn:participant}Mds"),
        ("Mds", "{urn:default}Mds"),
        ("{urn:participant}Mds", "{urn:participant}Mds"),
        (" pm:Mds ", "{urn:participant}Mds"),
    ],
)
def test_to_qname(raw: str, expected: str) -> None:
    """Prefixed, unprefixed and Clark notation names all resolve against the namespace map."""
    assert converter.to_qname(raw, _NSMAP) == lxml.etree.QName(expected)


def test_to_qname_without_default_namespace() -> None:
    """An unprefixed name stays namespace-less when no default namespace is in scope."""
    q_name = converter.to_qname("Mds", {"pm": "urn:participant"})
    assert q_name is not None
    assert q_name.namespace is None
    assert q_name.localname == "Mds"


def test_to_qname_undeclared_prefix() -> None:
    """An undeclared prefix is an error rather than a silently namespace-less name."""
    with pytest.raises(ValueError, match="not declared"):
        converter.to_qname("msg:Mds", _NSMAP)


@pytest.mark.parametrize("raw", ["", ":Mds", "pm:", "a:b:c"])
def test_to_qname_invalid(raw: str) -> None:
    """Malformed QName literals are rejected."""
    with pytest.raises(ValueError, match="QName"):
        converter.to_qname(raw, _NSMAP)


# ── xsd:enumeration ────────────────────────────────────────────────────────────────────────────────


def test_to_enum() -> None:
    """A permitted value converts to the corresponding enum member."""
    assert converter.to_enum("Red", _Colour) is _Colour.RED


@pytest.mark.parametrize("raw", ["red", "RED", "Blue", "", " Red "])
def test_to_enum_invalid(raw: str) -> None:
    """Enum values are matched verbatim, since the enumerations restrict xsd:string."""
    with pytest.raises(ValueError, match="_Colour"):
        converter.to_enum(raw, _Colour)


def test_to_enum_error_lists_permitted_values() -> None:
    """The error message names the permitted values."""
    with pytest.raises(ValueError, match="Red, Green"):
        converter.to_enum("Blue", _Colour)


# ── xsd:duration ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("PT0S", datetime.timedelta(0)),
        ("PT1H", datetime.timedelta(hours=1)),
        ("PT30M", datetime.timedelta(minutes=30)),
        ("PT45S", datetime.timedelta(seconds=45)),
        ("PT1H30M45S", datetime.timedelta(hours=1, minutes=30, seconds=45)),
        ("PT0.5S", datetime.timedelta(milliseconds=500)),
        ("PT1H0.25S", datetime.timedelta(hours=1, milliseconds=250)),
    ],
)
def test_duration_deserialize(raw: str, expected: datetime.timedelta) -> None:
    """The hour/minute/second forms convert to timedelta."""
    assert converter.DurationConverter.deserialize(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["", "PT", "-PT", "P1D", "P1Y", "P1M", "P0Y0M0DT0H0M0S", "PT1D", "1H", "pt1h", "PT1H ", "+PT1H"],
)
def test_duration_deserialize_invalid(raw: str) -> None:
    """SDPi R1018 admits only the PT hour/minute/second form, so the date designators are rejected."""
    with pytest.raises(ValueError, match="not matching SDPI 1018 regex"):
        converter.DurationConverter.deserialize(raw)


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (datetime.timedelta(0), "PT0S"),
        (datetime.timedelta(hours=1), "PT1H"),
        (datetime.timedelta(hours=1, minutes=30, seconds=45), "PT1H30M45S"),
        (datetime.timedelta(milliseconds=500), "PT0.5S"),
        (datetime.timedelta(days=1), "PT24H"),
    ],
)
def test_duration_serialize(delta: datetime.timedelta, expected: str) -> None:
    """A non-negative timedelta serializes to the PT form."""
    assert converter.DurationConverter.serialize(delta) == expected


@pytest.mark.parametrize("raw", ["PT0S", "PT1H", "PT1H30M45S", "PT0.5S"])
def test_duration_round_trip(raw: str) -> None:
    """Round-tripping a canonical form through deserialize and serialize returns it unchanged."""
    assert converter.DurationConverter.serialize(converter.DurationConverter.deserialize(raw)) == raw


# ── negative durations ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("raw", ["-PT3H", "-PT1H30M", "-PT0.5S"])
def test_negative_duration_rejected_by_default(raw: str) -> None:
    """Every duration in the core models is a period, delay or timeout, so a negative is an error."""
    with pytest.raises(ValueError, match="negative xsd:duration"):
        converter.DurationConverter.deserialize(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("-PT3H", datetime.timedelta(hours=-3)),
        ("-PT1H30M", -datetime.timedelta(hours=1, minutes=30)),
        ("-PT0.5S", -datetime.timedelta(milliseconds=500)),
    ],
)
def test_negative_duration_allowed_when_opted_in(raw: str, expected: datetime.timedelta) -> None:
    """sdpi:Epoch/@Offset is signed, so the caller can opt in."""
    assert converter.DurationConverter.deserialize(raw, allow_negative=True) == expected


@pytest.mark.parametrize(
    "delta",
    [datetime.timedelta(hours=-3), -datetime.timedelta(hours=1, minutes=30), -datetime.timedelta(milliseconds=500)],
)
def test_negative_duration_serialize_rejected_by_default(delta: datetime.timedelta) -> None:
    """Serializing mirrors deserializing: a negative delta needs the same opt-in."""
    with pytest.raises(ValueError, match="negative xsd:duration"):
        converter.DurationConverter.serialize(delta)


@pytest.mark.parametrize("raw", ["-PT3H", "-PT1H30M", "-PT0.5S"])
def test_negative_duration_round_trip(raw: str) -> None:
    """A signed duration round-trips, sign included, once opted in on both sides."""
    delta = converter.DurationConverter.deserialize(raw, allow_negative=True)
    assert converter.DurationConverter.serialize(delta, allow_negative=True) == raw


# ── xsd:dateTime and its truncated forms ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2020", converter.XsdDateTime(2020)),
        ("2020-05", converter.XsdDateTime(2020, 5)),
        ("2020-05-17", converter.XsdDateTime(2020, 5, 17)),
        ("2020-05-17T10:20:30", converter.XsdDateTime(2020, 5, 17, datetime.time(10, 20, 30))),
        ("-0045", converter.XsdDateTime(-45)),
        ("12020", converter.XsdDateTime(12020)),
        ("20200517", converter.XsdDateTime(20200517)),
        ("2020-02-29", converter.XsdDateTime(2020, 2, 29)),
        ("2020-05-17T10:20:30.5", converter.XsdDateTime(2020, 5, 17, datetime.time(10, 20, 30, 500000))),
        (" 2020 ", converter.XsdDateTime(2020)),
        ("\n2020-05-17\t", converter.XsdDateTime(2020, 5, 17)),
    ],
)
def test_xsd_date_time_deserialize(raw: str, expected: converter.XsdDateTime) -> None:
    """Each of the four union member types parses to the components it states.

    A year of any digit count and a negative year are both valid, which is why the components are kept as
    integers rather than as a datetime.date.
    """
    assert converter.XsdDateTime.deserialize(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2020", converter.DateTimePrecision.YEAR),
        ("2020-05", converter.DateTimePrecision.YEAR_MONTH),
        ("2020-05-17", converter.DateTimePrecision.DATE),
        ("2020-05-17T10:20:30", converter.DateTimePrecision.DATE_TIME),
    ],
)
def test_xsd_date_time_precision(raw: str, expected: converter.DateTimePrecision) -> None:
    """The precision reports which member type of the union the literal was written in."""
    assert converter.XsdDateTime.deserialize(raw).precision is expected


@pytest.mark.parametrize(
    ("raw", "offset"),
    [
        ("2020Z", datetime.timedelta(0)),
        ("2020-05+02:00", datetime.timedelta(hours=2)),
        ("2020-05-17-14:00", datetime.timedelta(hours=-14)),
        ("2020-05-17T10:20:30+05:30", datetime.timedelta(hours=5, minutes=30)),
    ],
)
def test_xsd_date_time_timezone(raw: str, offset: datetime.timedelta) -> None:
    """Every precision may carry a timezone, so the offset is kept apart from the time of day."""
    parsed = converter.XsdDateTime.deserialize(raw)
    assert parsed.tzinfo == datetime.timezone(offset)
    assert parsed.time is None or parsed.time.tzinfo is None


def test_xsd_date_time_truncates_sub_microsecond_fraction() -> None:
    """Fractional seconds are truncated rather than rounded, so they can never carry into the second."""
    parsed = converter.XsdDateTime.deserialize("2020-05-17T10:20:30.9999999")
    assert parsed.time == datetime.time(10, 20, 30, 999999)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2020-05-17T24:00:00", converter.XsdDateTime(2020, 5, 18, datetime.time())),
        ("2020-05-31T24:00:00", converter.XsdDateTime(2020, 6, 1, datetime.time())),
        ("2020-12-31T24:00:00", converter.XsdDateTime(2021, 1, 1, datetime.time())),
    ],
)
def test_xsd_date_time_midnight_rolls_over(raw: str, expected: converter.XsdDateTime) -> None:
    """The hour 24 denotes midnight of the following day and is normalized to it."""
    assert converter.XsdDateTime.deserialize(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "+2020",
        "2020-00",
        "2020-13-01",
        "2020-01-32",
        "2020-5-17",
        "2020-05-17T10:20",
        "2020-05-17T23:59:60",
        "2020-05-17+15:00",
        "2020-05-17T10:20:30+02",
        "2020-05-17 10:20:30",
        "17.05.2020",
    ],
)
def test_xsd_date_time_invalid_lexical(raw: str) -> None:
    """Literals outside the lexical space of all four types are rejected."""
    with pytest.raises(ValueError, match="not a valid xsd:dateTime"):
        converter.XsdDateTime.deserialize(raw)


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ("0000", "year zero"),
        ("2001-02-30", "out of range"),
        ("2021-02-29", "out of range"),
        ("2020-04-31", "out of range"),
        ("2020-05-17T24:00:01", "denotes midnight"),
    ],
)
def test_xsd_date_time_invalid_value(raw: str, message: str) -> None:
    """Literals inside the lexical space but outside the value space are rejected as well."""
    with pytest.raises(ValueError, match=message):
        converter.XsdDateTime.deserialize(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "2020",
        "-0045",
        "12020",
        "2020Z",
        "2020+02:00",
        "2020-05",
        "2020-05-17",
        "2020-05-17-14:00",
        "2020-05-17T10:20:30",
        "2020-05-17T10:20:30.5",
        "2020-05-17T10:20:30Z",
    ],
)
def test_xsd_date_time_round_trip(raw: str) -> None:
    """A canonical literal of any precision survives deserialize followed by serialize unchanged."""
    assert converter.XsdDateTime.deserialize(raw).serialize() == raw


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("2020-05-17T24:00:00", "2020-05-18T00:00:00"), ("2020-05-17+00:00", "2020-05-17Z")],
)
def test_xsd_date_time_canonicalizes(raw: str, expected: str) -> None:
    """Where two lexical forms denote one value, serialize returns the canonical one."""
    assert converter.XsdDateTime.deserialize(raw).serialize() == expected


def test_xsd_date_time_str_is_the_lexical_form() -> None:
    """str() gives the lexical form, so a value can be written straight into an element."""
    assert str(converter.XsdDateTime(2020, 5)) == "2020-05"


def test_xsd_date_time_rejects_year_zero() -> None:
    """Direct construction enforces the same invariants as parsing; XML Schema 1.0 has no year zero."""
    with pytest.raises(ValueError, match="year zero"):
        converter.XsdDateTime(0)


def test_xsd_date_time_rejects_day_without_month() -> None:
    """No lexical form states a day without the month it refines."""
    with pytest.raises(ValueError, match="without a month"):
        converter.XsdDateTime(2020, day=17)


def test_xsd_date_time_rejects_time_without_date() -> None:
    """No lexical form states a time of day without a full date."""
    with pytest.raises(ValueError, match="without a full date"):
        converter.XsdDateTime(2020, 5, time=datetime.time(10))


def test_xsd_date_time_rejects_month_out_of_range() -> None:
    """A month outside 1 to 12 has no lexical form."""
    with pytest.raises(ValueError, match="out of range"):
        converter.XsdDateTime(2020, 13)


def test_xsd_date_time_rejects_day_out_of_range_for_month() -> None:
    """The value space rejects a day the month does not have, February 29th of a common year included."""
    with pytest.raises(ValueError, match="out of range"):
        converter.XsdDateTime(2021, 2, 29)


def test_xsd_date_time_rejects_aware_time() -> None:
    """The offset lives in tzinfo, so that it survives at a precision that has no time of day."""
    with pytest.raises(ValueError, match="belongs in the tzinfo"):
        converter.XsdDateTime(2020, 5, 17, datetime.time(10, tzinfo=datetime.UTC))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2020", "2020-01-01T00:00:00"),
        ("2020-05", "2020-05-01T00:00:00"),
        ("2020-05-17", "2020-05-17T00:00:00"),
        ("2020-05-17T10:20:30", "2020-05-17T10:20:30"),
        ("2020-05-17T10:20:30+02:00", "2020-05-17T10:20:30+02:00"),
        ("2020-05Z", "2020-05-01T00:00:00+00:00"),
    ],
)
def test_xsd_date_time_to_datetime(raw: str, expected: str) -> None:
    """An absent month or day defaults to 1 and an absent time to midnight; the offset is kept."""
    assert converter.XsdDateTime.deserialize(raw).to_datetime() == datetime.datetime.fromisoformat(expected)


def test_xsd_date_time_to_datetime_rejects_unrepresentable_year() -> None:
    """A year datetime cannot hold is an error only once a concrete instant is asked for."""
    parsed = converter.XsdDateTime.deserialize("12020")
    with pytest.raises(ValueError, match="year"):
        parsed.to_datetime()


def test_date_time_converter_deserialize() -> None:
    """A full xsd:dateTime literal converts straight to a datetime."""
    converted = converter.DateTimeConverter.deserialize("2020-05-17T10:20:30Z")
    assert converted == datetime.datetime.fromisoformat("2020-05-17T10:20:30+00:00")


@pytest.mark.parametrize(("raw", "precision"), [("2020", "gYear"), ("2020-05", "gYearMonth"), ("2020-05-17", "date")])
def test_date_time_converter_rejects_shorter_forms(raw: str, precision: str) -> None:
    """The shorter forms are valid literals of their own types, but not of xsd:dateTime."""
    with pytest.raises(ValueError, match=f"xsd:{precision} literal"):
        converter.DateTimeConverter.deserialize(raw)


@pytest.mark.parametrize("raw", ["2020-05-17T10:20:30", "2020-05-17T10:20:30+02:00", "2020-05-17T10:20:30.5Z"])
def test_date_time_converter_round_trip(raw: str) -> None:
    """A naive or aware datetime round-trips through deserialize and serialize."""
    assert converter.DateTimeConverter.serialize(converter.DateTimeConverter.deserialize(raw)) == raw


# ── absent values ──────────────────────────────────────────────────────────────────────────────────


def test_none_passes_through() -> None:
    """An absent attribute stays absent for every converter."""
    assert converter.to_bool(None) is None
    assert converter.to_int(None) is None
    assert converter.to_decimal(None) is None
    assert converter.to_qname(None, _NSMAP) is None
    assert converter.to_enum(None, _Colour) is None
