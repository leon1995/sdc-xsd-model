"""Configure shared lxml element class lookup for generated models."""

import lxml.etree

from sdc_xsd_model.models import addressing, discovery, eventing, soap_envelope

__LOOKUP__ = lxml.etree.ElementNamespaceClassLookup()
addressing.set_lookup(__LOOKUP__)
discovery.set_lookup(__LOOKUP__)
eventing.set_lookup(__LOOKUP__)
soap_envelope.set_lookup(__LOOKUP__)
# ensure that that the namespace -> class lookup is initialized
lxml.etree.set_element_class_lookup(__LOOKUP__)
