"""SDPi EquipmentIdentifier extension class for BICEPS extensions."""

from __future__ import annotations

import typing

from sdc_xsd_model.core import common, extension
from sdc_xsd_model.extension_registry import register_extension

NAMESPACE: typing.Final[str] = "urn:oid:1.3.6.1.4.1.19376.1.6.2.10.1.1.1"


@register_extension
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
        """Return the optional ext:MustUnderstand attribute."""
        value = self.get(extension.MUST_UNDERSTAND_ATTR_TAG)
        return value.lower() == "true" if value is not None else None
