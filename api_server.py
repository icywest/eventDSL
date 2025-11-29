# api_server.py
import os
import sys
from typing import List, Optional

from fastapi import FastAPI, HTTPException # type: ignore
from starlette.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel, Field # type: ignore

# ---------------------------------------------------------
# Añadir la carpeta de código "eventdsl" al sys.path
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)              # carpeta externa eventdsl
CODE_DIR = os.path.join(BASE_DIR, "eventdsl")     # carpeta interna eventdsl\

if CODE_DIR not in sys.path:
    sys.path.append(CODE_DIR)

# Ahora podemos importar módulos dentro de eventdsl/
from eventdsl.db import (
    init_db,
    get_form_rules_for_requester,
    list_events,
    save_event,
)
from eventdsl.validators.scheduling import (
    validate_event_scheduling,
    SchedulingValidationError,
)

app = FastAPI(title="EventDSL API Server")

# CORS para permitir React en localhost
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


class FormField(BaseModel):
    field_name: str
    label: str
    visible: bool
    required: bool
    options: Optional[List[str]] = None


class EventCreate(BaseModel):
    requester_type: str = Field(..., pattern="^(Academics|Students)$")
    name: str
    campus_id: int
    date: str        # yyyy-mm-dd
    start_time: str  # HH:MM
    end_time: str    # HH:MM
    location: str    # LocationOption permitido


class EventOut(BaseModel):
    id: int
    name: str
    requester_type: str
    campus_id: int
    date: str
    start_time: str
    end_time: str
    location: str


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Event Scheduler DSL API is running",
    }


@app.get("/form-config", response_model=List[FormField])
def get_form_config(requester_type: str):
    if requester_type not in ("Academics", "Students"):
        raise HTTPException(status_code=400, detail="Invalid requester_type")

    rules = get_form_rules_for_requester(requester_type)

    if not rules:
        raise HTTPException(
            status_code=404,
            detail=f"No form rules found for requester_type '{requester_type}'. "
                   f"Ask the admin to configure rules via DSL.",
        )

    fields: List[FormField] = []
    import json

    for field_name, visible, required, label, options_json in rules:
        if not visible:
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


@app.get("/events", response_model=List[EventOut])
def get_events():
    rows = list_events()
    events: List[EventOut] = []
    for ev in rows:
        ev_id, name, requester_type, campus_id, date, start, end, location = ev
        events.append(
            EventOut(
                id=ev_id,
                name=name,
                requester_type=requester_type,
                campus_id=campus_id,
                date=date,
                start_time=start,
                end_time=end,
                location=location,
            )
        )
    return events


@app.post("/events", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate):
    try:
        validate_event_scheduling(
            name=payload.name,
            requester_type=payload.requester_type,
            campus_id=payload.campus_id,
            date=payload.date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location=payload.location,
        )
    except SchedulingValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        save_event(
            name=payload.name,
            requester_type=payload.requester_type,
            campus_id=payload.campus_id,
            date=payload.date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location=payload.location,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )

    rows = list_events()
    last = rows[-1]
    ev_id, name, requester_type, campus_id, date, start, end, location = last

    return EventOut(
        id=ev_id,
        name=name,
        requester_type=requester_type,
        campus_id=campus_id,
        date=date,
        start_time=start,
        end_time=end,
        location=location,
    )
