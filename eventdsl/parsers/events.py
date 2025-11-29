import os
from textx import metamodel_from_file

from db import init_db, save_event
from validators.scheduling import (
    validate_event_scheduling,
    SchedulingValidationError,
)

GRAMMAR_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "grammar",
    "event_dsl.tx",
)

event_mm = metamodel_from_file(GRAMMAR_PATH)


def parse_and_save_events(dsl_file_path: str):
    """
    Parsea un .evdsl con eventos, valida scheduling y guarda.
    Si algún evento viola reglas, se lanza excepción y no se guarda ninguno.
    """
    init_db()
    model = event_mm.model_from_file(dsl_file_path)

    # Validar todos primero
    for ev in model.events:
        name = ev.name
        requester_type = ev.requester_type
        campus_id = int(ev.campus_id)
        date = ev.date
        start_time = ev.start
        end_time = ev.end
        location = ev.location

        try:
            validate_event_scheduling(
                name=name,
                requester_type=requester_type,
                campus_id=campus_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                location=location,
            )
        except SchedulingValidationError as e:
            raise SchedulingValidationError(
                f"Error in event '{name}' on {date} {start_time}-{end_time} "
                f"({requester_type}, Campus {campus_id} @ {location}):\n{e}"
            )

    # Si todos son válidos, guardar
    for ev in model.events:
        save_event(
            name=ev.name,
            requester_type=ev.requester_type,
            campus_id=int(ev.campus_id),
            date=ev.date,
            start_time=ev.start,
            end_time=ev.end,
            location=ev.location,
        )

    print(f"✅ Se guardaron {len(model.events)} evento(s) desde {dsl_file_path}")
