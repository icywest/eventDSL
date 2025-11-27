# event_dsl/parsers/events.py
import os
from textx import metamodel_from_file

from db import init_db, save_event

GRAMMAR_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "grammar",
    "event_dsl.tx",
)


event_mm = metamodel_from_file(GRAMMAR_PATH)


def parse_and_save_events(dsl_file_path: str):
    init_db()
    model = event_mm.model_from_file(dsl_file_path)

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
