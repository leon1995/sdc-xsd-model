"""Configure shared lxml element class lookup for generated models."""

import lxml.etree

from sdc_xsd_model.models import addressing, discovery, eventing, soap_envelope

__LOOKUP__ = lxml.etree.ElementNamespaceClassLookup()
addressing.set_lookup(__LOOKUP__)
discovery.set_lookup(__LOOKUP__)
eventing.set_lookup(__LOOKUP__)
soap_envelope.set_lookup(__LOOKUP__)
# Ensure that the namespace -> class lookup is initialized.
#   Otherwise, when using e.g. .append() the appended element would lose its type information,
#   because it gets serialized and parsed without the class lookup set.
#   One could define a parser within the element class itself,
#   but setting up the lookup would result in a circular import.
lxml.etree.set_element_class_lookup(__LOOKUP__)
