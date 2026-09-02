"""SDPi EquipmentIdentifier extension class for BICEPS extensions."""

from __future__ import annotations

import pathlib
import typing

from sdc_xsd_model import converter
from sdc_xsd_model.core import common, extension

PREFIX: typing.Final[str] = "sdpi"
NAMESPACE: typing.Final[str] = "urn:oid:1.3.6.1.4.1.19376.1.6.2.10.1.1.1"
SCHEMA_PATH: typing.Final[pathlib.Path] = (
    pathlib.Path(__file__).parent.joinpath("equipment_identifier_schema.xsd").absolute()
)


class EquipmentIdentifier(common.AnyUri):
    """Equipment identifier for SOMDS Provider descriptors.

    Attaches to pm:MdsDescriptor/ext:Extension or pm:VmdDescriptor/ext:Extension.
    """

    TAG: typing.Final[str] = f"{{{NAMESPACE}}}EquipmentIdentifier"

    @property
    def uri(self) -> str:
        """Return the anyURI text content."""
        assert self.text is not None
        return self.text

    @property
    def must_understand(self) -> bool:
        """Return the ext:MustUnderstand attribute, which defaults to false when absent."""
        value = converter.to_bool(self.get(extension.MUST_UNDERSTAND_ATTR_TAG, "false"))
        assert value is not None
        return value
