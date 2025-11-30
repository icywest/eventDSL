import sqlite3
import os
import json
from typing import Optional, List

DB_PATH = os.path.join(os.path.dirname(__file__), "events.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            requester_type TEXT NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            location TEXT NOT NULL,
            requester_unit TEXT
        )
        """
    )

    # Tabla de reglas de formulario
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS form_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_type TEXT NOT NULL,
            field_name TEXT NOT NULL,
            visible INTEGER NOT NULL,
            required INTEGER NOT NULL,
            label TEXT,
            options_json TEXT
        )
        """
    )

    conn.commit()
    conn.close()


# ---------- Eventos ----------

def save_event(
    name: str,
    requester_type: str,
    date: str,
    start_time: str,
    end_time: str,
    location: str,
    requester_unit: Optional[str] = None,
):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO events (name, requester_type, date, start_time, end_time, location, requester_unit)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, requester_type, date, start_time, end_time, location, requester_unit),
    )
    conn.commit()
    conn.close()


def list_events():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, requester_type, date, start_time, end_time, location, requester_unit
        FROM events
        ORDER BY date, start_time
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_events_for_date_location(date: str, location: str):
    """
    Eventos ya agendados para una fecha/location.
    Se usa para validar conflictos.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, requester_type, date, start_time, end_time, location, requester_unit
        FROM events
        WHERE date = ?
          AND location = ?
        ORDER BY start_time
        """,
        (date, location),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------- Reglas de formulario ----------

def clear_form_rules():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM form_fields")
    conn.commit()
    conn.close()


def save_form_field_rule(
    requester_type: str,
    field_name: str,
    visible: bool,
    required: bool,
    label: Optional[str],
    options: Optional[List[str]],
):
    conn = get_conn()
    cursor = conn.cursor()
    options_json = json.dumps(options) if options is not None else None

    cursor.execute(
        """
        INSERT INTO form_fields (requester_type, field_name, visible, required, label, options_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            requester_type,
            field_name,
            1 if visible else 0,
            1 if required else 0,
            label,
            options_json,
        ),
    )
    conn.commit()
    conn.close()


def list_form_rules():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT requester_type, field_name, visible, required, label, options_json
        FROM form_fields
        ORDER BY requester_type, field_name
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_form_rules_for_requester(requester_type: str):
    """
    Reglas de campos visibles para un requester_type (Academics/Students).
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT field_name, visible, required, label, options_json
        FROM form_fields
        WHERE requester_type = ?
        ORDER BY id
        """,
        (requester_type,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
