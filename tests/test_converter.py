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
        ("-PT3H", datetime.timedelta(hours=-3)),
        ("-PT1H30M", -datetime.timedelta(hours=1, minutes=30)),
    ],
)
def test_duration_deserialize(raw: str, expected: datetime.timedelta) -> None:
    """The hour/minute/second forms and a leading sign convert to timedelta."""
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
        (datetime.timedelta(hours=-3), "-PT3H"),
        (-datetime.timedelta(hours=1, minutes=30), "-PT1H30M"),
        (-datetime.timedelta(milliseconds=500), "-PT0.5S"),
    ],
)
def test_duration_serialize(delta: datetime.timedelta, expected: str) -> None:
    """A timedelta serializes to the PT form, with a leading sign when negative."""
    assert converter.DurationConverter.serialize(delta) == expected


@pytest.mark.parametrize(
    "raw",
    ["PT0S", "PT1H", "PT1H30M45S", "PT0.5S", "-PT3H", "-PT1H30M", "-PT0.5S"],
)
def test_duration_round_trip(raw: str) -> None:
    """Round-tripping a canonical form through deserialize and serialize returns it unchanged."""
    assert converter.DurationConverter.serialize(converter.DurationConverter.deserialize(raw)) == raw


# ── absent values ──────────────────────────────────────────────────────────────────────────────────


def test_none_passes_through() -> None:
    """An absent attribute stays absent for every converter."""
    assert converter.to_bool(None) is None
    assert converter.to_int(None) is None
    assert converter.to_decimal(None) is None
    assert converter.to_qname(None, _NSMAP) is None
    assert converter.to_enum(None, _Colour) is None
