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
