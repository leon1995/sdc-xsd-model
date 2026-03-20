"""SDPi extensions."""

from sdc_xsd_model import extension_registry
from sdc_xsd_model.extensions.sdpi import (
    coded_attributes_models,
    equipment_identifier_models,
    gender_models,
    timestamp_epoch_version_models,
)


def register_all() -> None:
    """Register all SDPi extensions."""
    register_coded_attributes()
    register_equipment_identifier()
    register_gender()
    register_timestamp_epoch_version()


def register_coded_attributes() -> None:
    """Register the SDPi Coded Attributes extension and its element classes."""
    coded_attributes_extension = extension_registry.register_extension(
        namespace=coded_attributes_models.NAMESPACE,
        prefix=coded_attributes_models.PREFIX,
        schema=coded_attributes_models.SCHEMA_PATH,
    )
    coded_attributes_extension.register_classes(
        coded_attributes_models.CodedAttributes,
        coded_attributes_models.CodedStringAttribute,
        coded_attributes_models.CodedIntegerAttribute,
        coded_attributes_models.CodedDecimalAttribute,
        coded_attributes_models.MdcAttribute,
    )


def register_equipment_identifier() -> None:
    """Register the SDPi Equipment Identifier extension and its element classes."""
    equipment_identifier_extension = extension_registry.register_extension(
        namespace=equipment_identifier_models.NAMESPACE,
        prefix=equipment_identifier_models.PREFIX,
        schema=equipment_identifier_models.SCHEMA_PATH,
    )
    equipment_identifier_extension.register_classes(
        equipment_identifier_models.EquipmentIdentifier,
    )


def register_gender() -> None:
    """Register the SDPi Gender extension and its element classes."""
    gender_extension = extension_registry.register_extension(
        namespace=gender_models.NAMESPACE,
        prefix=gender_models.PREFIX,
        schema=gender_models.SCHEMA_PATH,
    )
    gender_extension.register_classes(
        gender_models.Gender,
    )


def register_timestamp_epoch_version() -> None:
    """Register the SDPi Timestamp Epoch Version extension and its element classes."""
    timestamp_epoch_version_extension = extension_registry.register_extension(
        namespace=timestamp_epoch_version_models.NAMESPACE,
        prefix=timestamp_epoch_version_models.PREFIX,
        schema=timestamp_epoch_version_models.SCHEMA_PATH,
    )
    timestamp_epoch_version_extension.register_classes(
        timestamp_epoch_version_models.EpochSupport,
        timestamp_epoch_version_models.Epoch,
        timestamp_epoch_version_models.Epochs,
        timestamp_epoch_version_models.MetricEpoch,
        timestamp_epoch_version_models.CalibrationInfoEpoch,
        timestamp_epoch_version_models.AlertSystemStateEpoch,
        timestamp_epoch_version_models.AlertConditionStateEpoch,
        timestamp_epoch_version_models.AbstractContextStateEpoch,
    )
