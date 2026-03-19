"""Tests for the SDPi Gender extension model."""

from __future__ import annotations

import pathlib
import typing

import lxml.etree
import pytest

from sdc_xsd_model import extension_registry
from sdc_xsd_model.core import biceps_msg, biceps_pm, extension
from sdc_xsd_model.extensions.sdpi.gender_models import (
    NAMESPACE,
    Gender,
    GenderType,
)

if typing.TYPE_CHECKING:
    from sdc_xsd_model.core import common

GENDER_CASES = [
    (Gender, "Gender"),
]

EXAMPLE_XML = pathlib.Path(__file__).parent / "gender_example.xml"


@pytest.fixture
def parser() -> lxml.etree.XMLParser:
    """Build a parser with the sdpi namespace class lookup."""
    lookup = lxml.etree.ElementNamespaceClassLookup()
    extension_registry.set_lookup(lookup)
    xml_parser = lxml.etree.XMLParser()
    xml_parser.set_element_class_lookup(lookup)
    return xml_parser


@pytest.fixture
def biceps_parser() -> lxml.etree.XMLParser:
    """Build a full BICEPS parser with schema validation and all namespace lookups."""
    from sdc_xsd_model.parser import biceps_parser  # noqa: PLC0415

    return biceps_parser()


@pytest.mark.parametrize(("clazz", "local_name"), GENDER_CASES)
def test_default_tag(clazz: type[common.ElementBase], local_name: str) -> None:
    """Verify TAG follows the Clark notation {namespace}LocalName."""
    assert f"{{{NAMESPACE}}}{local_name}" == clazz.TAG


@pytest.mark.parametrize("clazz", [case[0] for case in GENDER_CASES])
def test_default_namespace(clazz: type[common.ElementBase]) -> None:
    """Verify that the sdpi namespace is registered in nsmap when constructing an element."""
    assert clazz(nsmap={"sdpi": NAMESPACE}).nsmap["sdpi"] == NAMESPACE


@pytest.mark.parametrize("clazz", [case[0] for case in GENDER_CASES])
def test_class_lookup(clazz: type[common.ElementBase], parser: lxml.etree.XMLParser) -> None:
    """Verify serialize-then-parse roundtrip resolves to the correct Python class."""
    element = clazz()
    xml = lxml.etree.tostring(element)
    parsed = lxml.etree.fromstring(xml, parser=parser)
    assert isinstance(parsed, clazz)


class TestExampleXml:
    """Tests that parse the gender_example.xml and verify its structure and values."""

    @pytest.fixture
    def tree(self, biceps_parser: lxml.etree.XMLParser) -> biceps_msg.GetMdibResponse:
        """Get the GetMdibResponse as fixture."""
        response = lxml.etree.parse(str(EXAMPLE_XML), parser=biceps_parser).getroot()
        assert isinstance(response, biceps_msg.GetMdibResponse)
        return response

    @pytest.fixture
    def patient_state(self, tree: biceps_msg.GetMdibResponse) -> biceps_pm.PatientContextState:
        """Get the patient context state as fixture."""
        patient_state = tree[0][1][0]
        assert isinstance(patient_state, biceps_pm.PatientContextState)
        return patient_state

    def test_biceps_tree_structure(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify the BICEPS tree structure down to MdDescription with one Mds."""
        mdib = tree.mdib
        assert isinstance(mdib, biceps_pm.Mdib)
        md_description = mdib.md_description
        assert isinstance(md_description, biceps_pm.MdDescription)
        assert len(md_description.mds) == 1

    def test_patient_context_state_type(self, tree: biceps_msg.GetMdibResponse) -> None:
        """Verify xsi:type dispatch resolves pm:State to PatientContextState."""
        md_state = tree.mdib.md_state
        assert isinstance(md_state, biceps_pm.MdState)
        states = md_state.states
        assert len(states) == 1
        patient_state = states[0]
        assert isinstance(patient_state, biceps_pm.PatientContextState)

    def test_patient_context_state_attributes(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify PatientContextState attributes from the example."""
        assert patient_state.context_association == biceps_pm.ContextAssociation.PRE

    def test_patient_identification(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify the patient Identification element root and extension values."""
        identifications = patient_state.identification
        assert len(identifications) == 1
        assert identifications[0].root == "http://www.sdpi.org"
        assert identifications[0].extension_attr == "SamplePatientId123"

    def test_core_data_type(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify the CoreData child resolves to PatientDemographicsCoreData."""
        core_data = patient_state.core_data
        assert isinstance(core_data, biceps_pm.PatientDemographicsCoreData)

    def test_core_data_extension_type(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify the ext:Extension inside CoreData resolves to the correct class."""
        core_data = patient_state.core_data
        assert core_data is not None
        ext = core_data.extension
        assert isinstance(ext, extension.Extension)

    def test_gender_value(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify the Gender extension value equals 'Other'."""
        core_data = patient_state.core_data
        assert core_data is not None
        ext = core_data.extension
        assert ext is not None
        gender = ext.find_by_element(Gender)
        assert isinstance(gender, Gender)
        assert gender.type == GenderType.OTHER

    def test_gender_must_understand_absent(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify ext:MustUnderstand is None when not present in the example."""
        core_data = patient_state.core_data
        assert core_data is not None
        ext = core_data.extension
        assert ext is not None
        gender = ext.find_by_element(Gender)
        assert isinstance(gender, Gender)
        assert gender.must_understand is None

    def test_core_data_given_name(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify CoreData given name equals 'John'."""
        core_data = patient_state.core_data
        assert core_data is not None
        assert core_data.given_name == "John"

    def test_core_data_middle_name(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify CoreData middle name equals 'Donnelly'."""
        core_data = patient_state.core_data
        assert core_data is not None
        assert core_data.middle_names == ["Donnelly"]

    def test_core_data_family_name(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify CoreData family name equals 'Doe'."""
        core_data = patient_state.core_data
        assert core_data is not None
        assert core_data.family_name == "Doe"

    def test_core_data_sex(self, patient_state: biceps_pm.PatientContextState) -> None:
        """Verify CoreData Sex equals 'M'."""
        core_data = patient_state.core_data
        assert core_data is not None
        assert core_data.sex == biceps_pm.Sex.M
