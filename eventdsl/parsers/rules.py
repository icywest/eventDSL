# parsers/rules.py
"""
Parser and validator for the EVENT RULES DSL (event_rules_dsl.tx).

Responsibilities:
- Load the textX metamodel for event_rules_dsl.tx.
- Apply semantic validation rules on the parsed model.
- Persist the resulting form configuration into the database.
"""

import os
import sys
from textx import metamodel_from_file, TextXError

CODE_ROOT = os.path.dirname(os.path.dirname(__file__))
if CODE_ROOT not in sys.path:
    sys.path.append(CODE_ROOT)

from db import (
    init_db,
    clear_form_rules,
    save_form_field_rule,
    list_form_rules,
)

# Path to the rules grammar
GRAMMAR_RULES_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "grammar",
    "event_rules_dsl.tx",
)

# Global metamodel for event_rules_dsl
event_rules_mm = metamodel_from_file(GRAMMAR_RULES_PATH)

# Fields that must exist in every event_form
MANDATORY_FIELDS = {
    "event_name",
    "event_date",
    "start_time",
    "end_time",
    "location",
}

# Fields that must always be required in every event_form
ALWAYS_REQUIRED_FIELDS = MANDATORY_FIELDS

# Fields allowed to define options = [...]
ALLOWED_OPTION_FIELDS = {
    "location",
    "requester_unit",
}

# Requester types that must have an event_form defined
REQUIRED_REQUESTER_TYPES = {"Academics", "Students"}


def validate_model(model):
    """
    Apply semantic validation rules to an already parsed model.

    Raises TextXError if any inconsistency is found:
    - initialize_runtime must be "yes".
    - Only one event_form per requester_type.
    - No duplicate fields within the same form.
    - Only specific fields can define options.
    - Mandatory fields must exist and be required.
    - Forms must exist for all required requester types.
    """
    # 1) Runtime must be enabled explicitly
    if model.init.status != "yes":
        raise TextXError(
            "initialize_runtime must be 'yes' to enable rules. "
            "Set: initialize_runtime = yes"
        )

    seen_requesters = set()

    for form in model.forms:
        requester = form.requester_type

        # 2) No more than one form per requester_type
        if requester in seen_requesters:
            raise TextXError(
                f"Duplicate event_form for requester_type '{requester}'. "
                f"Each requester_type must be defined only once."
            )
        seen_requesters.add(requester)

        # 3) Per-form field inspection
        field_map = {}

        for field in form.fields:
            name = field.field_name

            # 3.1) No duplicate fields within the same form
            if name in field_map:
                raise TextXError(
                    f"Duplicate field '{name}' in event_form {requester}. "
                    f"Remove the duplicate definition."
                )
            field_map[name] = field

            # 3.2) Only specific fields are allowed to have 'options'
            has_options = hasattr(field, "options") and bool(
                getattr(field, "options", [])
            )
            if has_options and name not in ALLOWED_OPTION_FIELDS:
                allowed_str = ", ".join(sorted(ALLOWED_OPTION_FIELDS))
                raise TextXError(
                    f"Field '{name}' in event_form {requester} defines 'options', "
                    f"but only these fields can define options: {allowed_str}."
                )

            # 3.3) Mandatory fields must be required = yes
            if name in ALWAYS_REQUIRED_FIELDS:
                if field.required != "yes":
                    raise TextXError(
                        f"Field '{name}' in event_form {requester} must have "
                        f"'required = yes' because it is a mandatory field."
                    )

        # 3.4) All mandatory fields must be present
        missing = MANDATORY_FIELDS - set(field_map.keys())
        if missing:
            missing_str = ", ".join(sorted(missing))
            raise TextXError(
                f"event_form {requester} is missing mandatory fields: {missing_str}. "
                f"All of them must be defined in the form."
            )

    # 4) There must be forms for all required requester types
    missing_forms = REQUIRED_REQUESTER_TYPES - seen_requesters
    if missing_forms:
        miss_str = ", ".join(sorted(missing_forms))
        raise TextXError(
            f"Missing event_form definitions for: {miss_str}. "
            f"Define a form for each requester_type."
        )


def parse_rules_from_text(dsl_text: str) -> int:
    """
    Parse rules from a raw DSL string, validate the model,
    and persist the resulting form configuration into the database.

    Returns:
        int: Number of event_form blocks processed.
    """
    init_db()

    model = event_rules_mm.model_from_str(dsl_text)

    # Semantic validation over the parsed model
    validate_model(model)

    # If validation succeeds, existing rules are cleared and new ones are stored
    clear_form_rules()

    for form in model.forms:
        requester_type = form.requester_type

        for field in form.fields:
            name = field.field_name
            visible = field.visible == "yes"
            required = field.required == "yes"
            label = getattr(field, "label", None)

            options = None
            if hasattr(field, "options") and field.options:
                options = [opt for opt in field.options]

            save_form_field_rule(
                requester_type=requester_type,
                field_name=name,
                visible=visible,
                required=required,
                label=label,
                options=options,
            )

    return len(model.forms)


def debug_print_rules():
    """
    Helper to print all form rules currently stored in the database.
    Useful for manual inspection during development.
    """
    rules = list_form_rules()
    print("\nForm rules in DB:")
    print("-" * 60)
    for r in rules:
        requester_type, field_name, visible, required, label, options_json = r
        print(
            f"{requester_type} | {field_name} | "
            f"visible={bool(visible)} required={bool(required)} "
            f"label={label!r} options={options_json}"
        )
