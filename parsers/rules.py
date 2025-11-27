# event_dsl/parsers/rules.py
import os
from textx import metamodel_from_file, TextXError

from db import (
    init_db,
    clear_form_rules,
    save_form_field_rule,
    list_form_rules,
)

GRAMMAR_RULES_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "grammar",
    "event_rules_dsl.tx",
)

event_rules_mm = metamodel_from_file(GRAMMAR_RULES_PATH)


def parse_rules_from_text(dsl_text: str) -> int:
    init_db()
    model = event_rules_mm.model_from_str(dsl_text)

    if model.init.status != "yes":
        raise TextXError("initialize_runtime must be 'yes' to enable rules.")

    clear_form_rules()

    for form in model.forms:
        requester_type = form.requester_type

        for field in form.fields:
            field_name = field.field_name
            visible = field.visible == "yes"
            required = field.required == "yes"
            label = getattr(field, "label", None)

            options = None
            if hasattr(field, "options") and field.options:
                options = [opt for opt in field.options]

            save_form_field_rule(
                requester_type=requester_type,
                field_name=field_name,
                visible=visible,
                required=required,
                label=label,
                options=options,
            )

    return len(model.forms)


def debug_print_rules():
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
