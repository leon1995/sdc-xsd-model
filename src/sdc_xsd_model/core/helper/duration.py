"""Handle XML durations."""

import datetime
import re


def _parse_integer(value: str | None) -> int | None:
    return int(value) if value is not None else None


# By the time of implementation, the sdpi regex has a bug, see https://github.com/IHE/DEV.SDPi/issues/516
# This bug has already been fixed here.
__SDPI_REGEX_DURATION__ = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+)(?:\.(?P<fraction>\d+))?S)?(?<!PT)$",
)


def parse_duration(date_string: str) -> datetime.timedelta:
    """XML Schema duration, constrained to hours, minutes and seconds.

    SDPi explicitly requires this constraint for the Expires attributes. However, we apply it to all
    xsd:duration elements. See https://github.com/IHE/DEV.SDPi/issues/517 for more details
    """
    match = __SDPI_REGEX_DURATION__.match(date_string)
    if match is None:
        msg = f"Date string {date_string} not matching SDPI regex for durations"
        raise ValueError(msg)
    groups = match.groupdict()
    seconds = groups["seconds"] or "0"
    fraction = groups["fraction"] or "0"
    return datetime.timedelta(
        hours=_parse_integer(groups["hours"]) or 0,
        minutes=_parse_integer(groups["minutes"]) or 0,
        seconds=float(f"{seconds}.{fraction}"),
    )


def duration_string(delta: datetime.timedelta) -> str:
    r"""Create an ISO 8601 durations value containing seconds.

    Note: Smaller fractions than microseconds are rounded based in the seventh digit.
          The referenced ISO8601 from 1988 in XML 1.1 does not
    restrict the precision, but in part 2 5.4 the minimal supported fraction-second duration is set to milliseconds
    https://www.w3.org/TR/xmlschema11-2/#partial-implementation, so microseconds should be safe
    Days are not allowed by SDPi and has to follow the regex ^PT(\d+H)?(\d+M)?(\d+(.\d+)?S)?(?<!PT)$.
    """
    if delta < datetime.timedelta(0):
        msg = "Negative durations are not supported"
        raise ValueError(msg)
    if not delta:
        return "PT0S"

    total_us = delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds
    total_secs, us = divmod(total_us, 1_000_000)
    hours, remainder = divmod(total_secs, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = ["PT"]
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
