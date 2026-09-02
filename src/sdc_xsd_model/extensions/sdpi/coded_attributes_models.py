"""SDPi CodedAttributes extension classes for BICEPS extensions."""

from __future__ import annotations

import pathlib
import typing

from sdc_xsd_model import converter
from sdc_xsd_model.core import biceps_pm, common

if typing.TYPE_CHECKING:
    import decimal
    from collections.abc import Sequence

PREFIX: typing.Final[str] = "sdpi"
NAMESPACE: typing.Final[str] = "urn:oid:1.3.6.1.4.1.19376.1.6.2.10.1.1.1"
SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.joinpath("coded_attributes_schema.xsd").absolute()
)


class CodedAttributes(common.ElementBase):
    """Container for coded attribute children."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CodedAttributes"

    @property
    def coded_string_attributes(self) -> Sequence[CodedStringAttribute]:
        """Return all CodedStringAttribute children."""
        return self.findall_by_element(CodedStringAttribute)

    @property
    def coded_integer_attributes(self) -> Sequence[CodedIntegerAttribute]:
        """Return all CodedIntegerAttribute children."""
        return self.findall_by_element(CodedIntegerAttribute)

    @property
    def coded_decimal_attributes(self) -> Sequence[CodedDecimalAttribute]:
        """Return all CodedDecimalAttribute children."""
        return self.findall_by_element(CodedDecimalAttribute)


class CodedStringAttribute(common.ElementBase):
    """A key value pair to include string attributes of the IEEE 11073 classic domain information model that are not available from the BICEPS participant model."""  # noqa: E501, W505

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CodedStringAttribute"

    @property
    def mdc_attribute(self) -> MdcAttribute:
        """Key of the key value pair. Describes the meaning of Value."""
        node = self.find_by_element(MdcAttribute)
        assert node is not None
        return node

    @property
    def value(self) -> str:
        """Value (user data) of the key value pair."""
        node = self.find(f"{{{NAMESPACE}}}Value")
        assert node is not None
        assert node.text is not None
        return node.text


class CodedIntegerAttribute(common.ElementBase):
    """A key value pair to include integer attributes of the IEEE 11073 classic domain information model that are not available from the BICEPS participant model."""  # noqa: E501, W505

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CodedIntegerAttribute"

    @property
    def mdc_attribute(self) -> MdcAttribute:
        """Key of the key value pair. Describes the meaning of Value."""
        node = self.find_by_element(MdcAttribute)
        assert node is not None
        return node

    @property
    def value(self) -> int:
        """Value (user data) of the key value pair."""
        elem = self.find(f"{{{NAMESPACE}}}Value")
        assert elem is not None
        value = converter.to_int(elem.text)
        assert value is not None
        return value


class CodedDecimalAttribute(common.ElementBase):
    """A key value pair to include decimal attributes of the IEEE 11073 classic domain information model that are not available from the BICEPS participant model."""  # noqa: E501, W505

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}CodedDecimalAttribute"

    @property
    def mdc_attribute(self) -> MdcAttribute:
        """Key of the key value pair. Describes the meaning of Value."""
        elem = self.find(MdcAttribute.TAG)
        assert isinstance(elem, MdcAttribute)
        return elem

    @property
    def value(self) -> decimal.Decimal:
        """Value (user data) of the key value pair."""
        elem = self.find(f"{{{NAMESPACE}}}Value")
        assert elem is not None
        value = converter.to_decimal(elem.text)
        assert value is not None
        return value


class MdcAttribute(common.ElementBase):
    """Specifies the concept of the key in a key value pair as laid out by coded attributes."""

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}MdcAttribute"

    @property
    def code(self) -> biceps_pm.CodeIdentifier:
        """Return the required Code attribute."""
        val = self.get("Code")
        assert val is not None
        return biceps_pm.CodeIdentifier(val)

    @property
    def coding_system(self) -> str | None:
        """The coding system of this coded attribute. The implied value is "urn:oid:1.3.111.2.11073.10101.1"."""
        return self.get("CodingSystem")

    @property
    def coding_system_version(self) -> str | None:
        """CodingSystemVersion can be used to discriminate between different versions of a coding system.

        CodingSystemVersion is an optional value and can be omitted in cases where a coding system is backwards
        compatible or CodingSystem includes versioning information.
        """
        return self.get("CodingSystemVersion")

    @property
    def symbolic_code_name(self) -> biceps_pm.SymbolicCodeName | None:
        """If present, SymbolicCodeName is an alternative representation that can be used to perform a plausibility check against Code."""  # noqa: E501, W505
        val = self.get("SymbolicCodeName")
        return biceps_pm.SymbolicCodeName(val) if val is not None else None
