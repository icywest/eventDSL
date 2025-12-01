# parsers/events.py
"""
Parser for the EVENTS DSL (event_dsl.tx).

Responsible for:
- Loading the textX metamodel for event_dsl.tx.
- Parsing .evdsl files containing event instances.
- Validating scheduling constraints for each event.
- Persisting valid events into the database.
"""

import os
import sys
from textx import metamodel_from_file

CODE_ROOT = os.path.dirname(os.path.dirname(__file__))
if CODE_ROOT not in sys.path:
    sys.path.append(CODE_ROOT)

from db import init_db, save_event
from validators.scheduling import (
    validate_event_scheduling,
    SchedulingValidationError,
)

# Path to the events grammar
GRAMMAR_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "grammar",
    "event_dsl.tx",
)

# Global metamodel for event_dsl
event_mm = metamodel_from_file(GRAMMAR_PATH)


def parse_and_save_events(dsl_file_path: str):
    """
    Parse a .evdsl file, validate each event according to scheduling rules,
    and store all of them into the database if and only if every event is valid.

    If any event violates scheduling rules, a SchedulingValidationError is raised
    and no events are stored (all-or-nothing behavior).
    """
    init_db()
    model = event_mm.model_from_file(dsl_file_path)

    # First pass: validate all events
    for ev in model.events:
        name = ev.name
        requester_type = ev.requester_type
        date = ev.date
        start_time = ev.start
        end_time = ev.end
        location = ev.location

        try:
            validate_event_scheduling(
                name=name,
                requester_type=requester_type,
                date=date,
                start_time=start_time,
                end_time=end_time,
                location=location,
            )
        except SchedulingValidationError as e:
            raise SchedulingValidationError(
                f"Error in event '{name}' on {date} {start_time}-{end_time} "
                f"({requester_type} @ {location}):\n{e}"
            )

    # Second pass: if all are valid, store them
    for ev in model.events:
        save_event(
            name=ev.name,
            requester_type=ev.requester_type,
            date=ev.date,
            start_time=ev.start,
            end_time=ev.end,
            location=ev.location,
        )

    print(f"✅ Se guardaron {len(model.events)} evento(s) desde {dsl_file_path}")
