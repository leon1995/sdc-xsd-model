"""SDPi Gender extension class for BICEPS extensions."""

from __future__ import annotations

import enum
import typing

from sdc_xsd_model.core import common, extension
from sdc_xsd_model.extension_registry import register_extension

NAMESPACE: typing.Final[str] = "urn:oid:1.3.6.1.4.1.19376.1.6.2.10.1.1.1"


class GenderType(enum.StrEnum):
    """Type defining the gender information of a patient.

    This allows the differentiation between Sex and Gender in a pm:PatientDemographicsCoreData as in
    HL7 FHIR (https://hl7.org/fhir/valueset-administrative-gender.html).
    """

    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    UNKNOWN = "Unknown"


@register_extension
class Gender(common.ElementBase):
    """Administrative gender for patients in BICEPS.

    Attaches to pm:PatientDemographicsCoreData/ext:Extension.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}Gender"

    @property
    def type(self) -> str:
        """Return the gender text content (Male / Female / Other / Unknown)."""
        assert self.text is not None
        return GenderType(self.text)

    @property
    def must_understand(self) -> bool | None:
        """Return the optional ext:MustUnderstand attribute."""
        raw = self.get(extension.MUST_UNDERSTAND_ATTR_TAG)
        return raw.lower() == "true" if raw is not None else None
