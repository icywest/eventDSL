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

# Campos que SIEMPRE deben existir en cada event_form
MANDATORY_FIELDS = {
    "event_name",
    "campus_id",
    "event_date",
    "start_time",
    "end_time",
    "location",
}

ALWAYS_REQUIRED_FIELDS = MANDATORY_FIELDS  # por ahora los mismos

ALLOWED_OPTION_FIELDS = {
    "location",
}

REQUIRED_REQUESTER_TYPES = {"Academics", "Students"}


def validate_model(model):
    """
    Reglas semánticas sobre el modelo ya parseado.
    Lanza TextXError si hay inconsistencias.
    """

    # 1) initialize_runtime debe ser yes
    if model.init.status != "yes":
        raise TextXError(
            "initialize_runtime must be 'yes' to enable rules. "
            "Set: initialize_runtime = yes"
        )

    seen_requesters = set()

    for form in model.forms:
        requester = form.requester_type

        # 2) No permitir más de un event_form por requester_type
        if requester in seen_requesters:
            raise TextXError(
                f"Duplicate event_form for requester_type '{requester}'. "
                f"Each requester_type must be defined only once."
            )
        seen_requesters.add(requester)

        # 3) Revisar campos del formulario
        field_map = {}

        for field in form.fields:
            name = field.field_name

            # 3.1) No duplicar campo en el mismo form
            if name in field_map:
                raise TextXError(
                    f"Duplicate field '{name}' in event_form {requester}. "
                    f"Remove the duplicate definition."
                )
            field_map[name] = field

            # 3.2) Solo location puede tener options
            has_options = hasattr(field, "options") and bool(
                getattr(field, "options", [])
            )
            if has_options and name not in ALLOWED_OPTION_FIELDS:
                allowed_str = ", ".join(sorted(ALLOWED_OPTION_FIELDS))
                raise TextXError(
                    f"Field '{name}' in event_form {requester} defines 'options', "
                    f"but only these fields can define options: {allowed_str}."
                )

            # 3.3) Campos mandatory deben ser required = yes
            if name in ALWAYS_REQUIRED_FIELDS:
                if field.required != "yes":
                    raise TextXError(
                        f"Field '{name}' in event_form {requester} must have "
                        f"'required = yes' because it is a mandatory field."
                    )

        # 3.4) Verificar mandatory fields existen
        missing = MANDATORY_FIELDS - set(field_map.keys())
        if missing:
            missing_str = ", ".join(sorted(missing))
            raise TextXError(
                f"event_form {requester} is missing mandatory fields: {missing_str}. "
                f"All of them must be defined in the form."
            )

    # 4) Formularios para todos los requester_types requeridos
    missing_forms = REQUIRED_REQUESTER_TYPES - seen_requesters
    if missing_forms:
        miss_str = ", ".join(sorted(missing_forms))
        raise TextXError(
            f"Missing event_form definitions for: {miss_str}. "
            f"Define a form for each requester_type."
        )


def parse_rules_from_text(dsl_text: str) -> int:
    """
    Parsea DSL de reglas, valida semántica y guarda en BD.
    Devuelve cuántos event_form se procesaron.
    """
    init_db()

    model = event_rules_mm.model_from_str(dsl_text)

    # Validación semántica
    validate_model(model)

    # Si pasa, limpiamos reglas anteriores y guardamos nuevas
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
