"""SDPi Gender extension class for BICEPS extensions."""

from __future__ import annotations

import enum
import pathlib
import typing

from sdc_xsd_model import converter
from sdc_xsd_model.core import common, extension

PREFIX: typing.Final[str] = "sdpi"
NAMESPACE: typing.Final[str] = "urn:oid:1.3.6.1.4.1.19376.1.6.2.10.1.1.1"
SCHEMA_PATH: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent.joinpath("gender_schema.xsd").absolute()


class GenderType(enum.StrEnum):
    """Type defining the gender information of a patient.

    This allows the differentiation between Sex and Gender in a pm:PatientDemographicsCoreData as in
    HL7 FHIR (https://hl7.org/fhir/valueset-administrative-gender.html).
    """

    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class Gender(common.ElementBase):
    """Administrative gender for patients in BICEPS.

    Attaches to pm:PatientDemographicsCoreData/ext:Extension.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Gender"

    @property
    def type(self) -> GenderType:
        """Return the gender text content (Male / Female / Other / Unknown)."""
        value = converter.to_enum(self.text, GenderType)
        assert value is not None
        return value

    @property
    def must_understand(self) -> bool | None:
        """``ext:MustUnderstand`` as written, or None when absent; see :attr:`must_understand_or_implied`."""
        return extension.must_understand_of(self)

    @property
    def must_understand_or_implied(self) -> bool:
        """``ext:MustUnderstand``; the schema states an absent attribute means ``false``."""
        return common.with_implied(self.must_understand, extension.IMPLIED_MUST_UNDERSTAND)
