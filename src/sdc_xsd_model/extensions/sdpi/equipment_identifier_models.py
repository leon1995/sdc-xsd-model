"""SDPi EquipmentIdentifier extension class for BICEPS extensions."""

from __future__ import annotations

import pathlib
import typing

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
    def must_understand(self) -> bool | None:
        """``ext:MustUnderstand`` as written, or None when absent; see :attr:`must_understand_or_implied`."""
        return extension.must_understand_of(self)

    @property
    def must_understand_or_implied(self) -> bool:
        """``ext:MustUnderstand``; the schema states an absent attribute means ``false``."""
        return common.with_implied(self.must_understand, extension.IMPLIED_MUST_UNDERSTAND)
