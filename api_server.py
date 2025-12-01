# api_server.py
"""
FastAPI backend for the Event Scheduler DSL project.

Exposes:
- Form configuration endpoint based on DSL rules stored in the DB.
- CRUD-like endpoints for events (create + list).
- AST endpoints for:
    * Rules DSL (event_rules_dsl.tx)
    * Events DSL (event_dsl.tx)
"""

import os
import sys
from typing import List, Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from textx import TextXError

# ------------------------------------------------------------------
# Path configuration
# ------------------------------------------------------------------

BASE_DIR = os.path.dirname(__file__)              # Outer eventDSL folder
CODE_DIR = os.path.join(BASE_DIR, "eventdsl")     # Inner eventdsl\ folder

if CODE_DIR not in sys.path:
    sys.path.append(CODE_DIR)

# ------------------------------------------------------------------
# Internal imports from eventdsl package
# ------------------------------------------------------------------

from db import (
    init_db,
    get_form_rules_for_requester,
    list_events,
    save_event,
)
from validators.scheduling import (
    validate_event_scheduling,
    SchedulingValidationError,
)

# TextX metamodels for both DSLs
from parsers.rules import event_rules_mm   # Grammar: event_rules_dsl.tx
from parsers.events import event_mm          # Grammar: event_dsl.tx

# ------------------------------------------------------------------
# FastAPI app and CORS
# ------------------------------------------------------------------

app = FastAPI(title="Event Scheduler DSL API")

# Allowed frontend origins during development
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Pydantic models
# ------------------------------------------------------------------


class FormField(BaseModel):
    """
    Represents a single field in the event request form configuration
    that is sent to the frontend.
    """
    field_name: str
    label: str
    visible: bool
    required: bool
    options: Optional[List[str]] = None


class EventCreate(BaseModel):
    """
    Payload for creating a new event via the API.
    """
    requester_type: str = Field(..., pattern="^(Academics|Students)$")
    name: str
    date: str        # ISO format: yyyy-mm-dd
    start_time: str  # 24h format: HH:MM
    end_time: str    # 24h format: HH:MM
    location: str    # One of the allowed location options
    requester_unit: Optional[str] = None


class EventOut(BaseModel):
    """
    Representation of an event as returned by the API.
    """
    id: int
    name: str
    requester_type: str
    date: str
    start_time: str
    end_time: str
    location: str
    requester_unit: Optional[str] = None


class AstRequest(BaseModel):
    """
    Generic request body for AST endpoints.
    """
    code: str


# ------------------------------------------------------------------
# Utility: textX model → JSON-serializable tree
# ------------------------------------------------------------------


def model_to_dict(
    obj: Any,
    max_depth: int = 20,
    current_depth: int = 0,
    visited: Optional[set] = None,
):
    """
    Convert a textX model instance into a JSON-serializable tree.

    - Primitive values are returned as-is.
    - Sequences are converted element by element.
    - Objects are represented as:
        {
            "__type__": "<ClassName>",
            "<attr>": <converted value>,
            ...
        }

    To avoid infinite recursion:
    - Structural back-references such as 'parent' are skipped.
    - A 'visited' set of object ids is used to break cycles.
    - 'max_depth' acts as an additional safety limit.
    """
    if visited is None:
        visited = set()

    if obj is None:
        return None

    # Depth guard to prevent very deep or malformed structures
    if current_depth > max_depth:
        return {"__type__": "MaxDepthReached"}

    # Primitive types are left as-is
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # Sequences (lists, tuples) are converted element by element
    if isinstance(obj, (list, tuple)):
        return [
            model_to_dict(
                item,
                max_depth=max_depth,
                current_depth=current_depth + 1,
                visited=visited,
            )
            for item in obj
        ]

    # Objects with attributes
    if hasattr(obj, "__dict__"):
        obj_id = id(obj)

        # Cycle detection: if we have already seen this object, stop here
        if obj_id in visited:
            return {
                "__type__": obj.__class__.__name__,
                "__note__": "circular_reference",
            }

        visited.add(obj_id)

        data = {"__type__": obj.__class__.__name__}

        for attr_name, value in obj.__dict__.items():
            # Skip internal and structural attributes that cause cycles
            if attr_name.startswith("_"):
                continue
            if attr_name in ("parent", "parent_obj", "parent_ref"):
                continue

            data[attr_name] = model_to_dict(
                value,
                max_depth=max_depth,
                current_depth=current_depth + 1,
                visited=visited,
            )

        return data

    # Fallback for unsupported types
    return str(obj)


# ------------------------------------------------------------------
# Lifecycle
# ------------------------------------------------------------------


@app.on_event("startup")
def on_startup():
    """
    Initialize the DB connection / schema when the API starts.
    """
    init_db()


# ------------------------------------------------------------------
# Basic health check
# ------------------------------------------------------------------


@app.get("/")
def root():
    """
    Simple root endpoint to verify that the API is online.
    """
    return {
        "status": "ok",
        "message": "Event Scheduler DSL API is running",
    }


# ------------------------------------------------------------------
# Form configuration endpoint (based on DSL rules stored in DB)
# ------------------------------------------------------------------


@app.get("/form-config", response_model=List[FormField])
def get_form_config(requester_type: str):
    """
    Returns the form configuration for a given requester_type
    (e.g., Academics or Students), based on the rules DSL
    already parsed and stored in the database.
    """
    if requester_type not in ("Academics", "Students"):
        raise HTTPException(status_code=400, detail="Invalid requester_type")

    rules = get_form_rules_for_requester(requester_type)

    if not rules:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No form rules found for requester_type '{requester_type}'. "
                f"Ask the admin to configure rules via DSL."
            ),
        )

    fields: List[FormField] = []
    import json

    for field_name, visible, required, label, options_json in rules:
        if not visible:
            # Fields marked as not visible are not sent to the frontend
            continue

        label_final = label or field_name
        options = None
        if options_json:
            options = json.loads(options_json)

        fields.append(
            FormField(
                field_name=field_name,
                label=label_final,
                visible=bool(visible),
                required=bool(required),
                options=options,
            )
        )

    return fields


# ------------------------------------------------------------------
# Events endpoints
# ------------------------------------------------------------------


@app.get("/events", response_model=List[EventOut])
def get_events():
    """
    Returns the list of all stored events.
    """
    rows = list_events()
    events: List[EventOut] = []
    for ev in rows:
        ev_id, name, requester_type, date, start, end, location, requester_unit = ev
        events.append(
            EventOut(
                id=ev_id,
                name=name,
                requester_type=requester_type,
                date=date,
                start_time=start,
                end_time=end,
                location=location,
                requester_unit=requester_unit,
            )
        )
    return events


@app.post("/events", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate):
    """
    Validates an event using scheduling rules and, if valid,
    stores it in the database and returns the created record.
    """
    # Domain-specific scheduling validation (DSL-based constraints)
    try:
        validate_event_scheduling(
            name=payload.name,
            requester_type=payload.requester_type,
            date=payload.date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location=payload.location,
        )
    except SchedulingValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Persist in DB
    try:
        save_event(
            name=payload.name,
            requester_type=payload.requester_type,
            date=payload.date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location=payload.location,
            requester_unit=payload.requester_unit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )

    # Return the last inserted event (simple approach)
    rows = list_events()
    last = rows[-1]
    ev_id, name, requester_type, date, start, end, location, requester_unit = last

    return EventOut(
        id=ev_id,
        name=name,
        requester_type=requester_type,
        date=date,
        start_time=start,
        end_time=end,
        location=location,
        requester_unit=requester_unit,
    )


# ------------------------------------------------------------------
# AST endpoints (for visualization in the frontend)
# ------------------------------------------------------------------


@app.post("/rules-ast")
def get_rules_ast(payload: AstRequest):
    """
    Parses the EVENT RULES DSL (event_rules_dsl.tx) from raw text and returns
    the corresponding abstract syntax tree (AST) as a JSON structure.

    This is intended to be consumed by the frontend in order to visualize
    how the DSL rules are interpreted by textX.
    """
    try:
        model = event_rules_mm.model_from_str(payload.code)
        ast_dict = model_to_dict(model)
        return {"ok": True, "ast": ast_dict}
    except TextXError as e:
        # Grammar or semantic errors during parsing
        raise HTTPException(
            status_code=400,
            detail=f"Rules DSL parsing error: {e}",
        )
    except Exception as e:
        # Generic unexpected error
        raise HTTPException(
            status_code=500,
            detail=f"Internal error while parsing rules DSL: {e}",
        )


@app.post("/events-ast")
def get_events_ast(payload: AstRequest):
    """
    Parses the EVENTS DSL (event_dsl.tx) from raw text and returns
    the corresponding abstract syntax tree (AST) as a JSON structure.

    This endpoint is useful to inspect batch event definitions
    and how textX instantiates the model.
    """
    try:
        model = event_mm.model_from_str(payload.code)
        ast_dict = model_to_dict(model)
        return {"ok": True, "ast": ast_dict}
    except TextXError as e:
        # Grammar or semantic errors during parsing
        raise HTTPException(
            status_code=400,
            detail=f"Events DSL parsing error: {e}",
        )
    except Exception as e:
        # Generic unexpected error
        raise HTTPException(
            status_code=500,
            detail=f"Internal error while parsing events DSL: {e}",
        )
