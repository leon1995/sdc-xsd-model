"""Custom element class lookup for BICEPS models."""

import typing
from collections.abc import Mapping

import lxml.etree

from sdc_xsd_model import converter
from sdc_xsd_model.core import common

_XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"


class BicepsElementClassLookup(lxml.etree.PythonElementClassLookup):
    """Element class lookup that dispatches on ``xsi:type`` or parent context.

    Wraps an ``ElementNamespaceClassLookup`` as fallback.  When an element
    carries an ``xsi:type`` attribute, the QName is resolved against the
    namespace lookup registry.  Additionally, parent-context dispatch allows
    resolving polymorphic children (e.g. ``MetricValue``) based on the parent
    element's tag.  If neither mechanism matches, the fallback namespace-based
    lookup is used.
    """

    def __init__(self, ns_lookup: lxml.etree.ElementNamespaceClassLookup) -> None:
        super().__init__(fallback=ns_lookup)
        self._ns_lookup = ns_lookup
        self._parent_dispatch: Mapping[tuple[str, str], str] = self._create_parent_dispatch()

    @staticmethod
    def _create_parent_dispatch() -> Mapping[tuple[str, str], str]:
        """Register parent-context dispatch for polymorphic MetricValue elements.

        In BICEPS, the ``MetricValue`` child element has a different schema type depending on its parent state element.
        Since all variants share the same element name, the namespace class lookup cannot distinguish them.
        This function registers parent->child type mappings so the lookup resolves the concrete class.
        """
        dispatcher: dict[tuple[str, str], str] = {}
        for parent_type, type_name in (
            ("NumericMetricState", "NumericMetricValue"),
            ("StringMetricState", "StringMetricValue"),
            ("EnumStringMetricState", "StringMetricValue"),
            ("RealTimeSampleArrayMetricState", "SampleArrayValue"),
            ("DistributionSampleArrayMetricState", "SampleArrayValue"),
        ):
            dispatcher[(parent_type, "MetricValue")] = type_name

        return dispatcher

    def _resolve_xsi_type(self, element: lxml.etree._Element) -> tuple[str | None, str | None]:
        """Extract (namespace, local_name) from an element's ``xsi:type``, or *(None, None)*."""
        try:
            q_name = converter.to_qname(element.get(_XSI_TYPE), element.nsmap)
        except ValueError:
            # A malformed or undeclared-prefix xsi:type cannot name a class; defer to the fallback
            # lookup rather than raising out of the parser.
            return None, None
        if q_name is None:
            return None, None
        return q_name.namespace, q_name.localname

    def _resolve_parent_type(
        self, parent: lxml.etree._Element, child: lxml.etree._Element
    ) -> tuple[str | None, str | None]:
        """Resolve a parent-context class.

        When a child element with *child_local_name* appears inside a parent whose resolved type is *parent_type*
        (the local part of the parent's ``xsi:type`` or, if absent, the parent's tag local name), resolve it
        via *type_name* in the child's namespace registry instead of the default tag-based lookup.
        """
        # Determine parent's effective type: xsi:type local name, or tag local name.
        _, parent_type = self._resolve_xsi_type(parent)
        if parent_type is None:
            parent_type = lxml.etree.QName(parent.tag).localname
        child_local = lxml.etree.QName(child.tag).localname
        type_name = self._parent_dispatch.get((parent_type, child_local))
        child_ns = lxml.etree.QName(child.tag).namespace if type_name is not None else None
        return child_ns, type_name

    def lookup(self, _: typing.Any, element: lxml.etree._Element) -> type[common.ElementBase] | None:  # noqa: ANN401
        """Return the element class based on ``xsi:type``, parent context, or *None* for fallback."""
        # Comments and processing instructions are also passed here, but their read-only proxy
        # exposes neither ``get`` nor a string ``tag``.  Delegate them to the fallback lookup.
        if not isinstance(element.tag, str):
            return None

        ns, local = self._resolve_xsi_type(element)
        if ns is not None and local is not None:
            try:
                return self._ns_lookup.get_namespace(ns)[local]
            except KeyError:
                pass

        parent = element.getparent()
        if parent is not None and self._parent_dispatch:
            child_ns, type_name = self._resolve_parent_type(parent, element)
            if child_ns is not None and type_name is not None:
                try:
                    return self._ns_lookup.get_namespace(child_ns)[type_name]
                except KeyError:
                    pass

        return None
