"""SDPi (IHE Service-oriented Device Point-of-care Interoperability) extensions."""


def register_all() -> None:
    """Import all SDPi extension modules so their classes are added to the extension registry.

    Call this before building a parser (e.g. ``biceps_parser()``) to ensure all
    SDPi element classes are available for namespace lookup and schema validation.
    """
    from sdc_xsd_model.extensions.sdpi import (  # noqa: F401, PLC0415
        coded_attributes_models,
        equipment_identifier_models,
        gender_models,
        timestamp_epoch_version_models,
    )
