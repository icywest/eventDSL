from db import get_events_for_date_location


class SchedulingValidationError(Exception):
    """Error de validación de reglas de agendado."""
    pass


def _parse_time_to_minutes(time_str: str) -> int:
    """
    Convierte 'HH:MM' a minutos desde 00:00.
    Lanza SchedulingValidationError si el formato es incorrecto.
    """
    try:
        parts = time_str.strip().split(":")
        if len(parts) != 2:
            raise ValueError
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError
        return hour * 60 + minute
    except Exception:
        raise SchedulingValidationError(
            f"Invalid time format '{time_str}'. Expected HH:MM in 24-hour format."
        )


def validate_event_scheduling(
    name: str,
    requester_type: str,
    date: str,
    start_time: str,
    end_time: str,
    location: str,
):
    """
    Reglas de negocio de agendado:

    - start_time < end_time
    - duración mínima 60 minutos
    - no traslape con otros eventos en misma fecha/location
    """

    # 1) Formato y orden de horas
    start_min = _parse_time_to_minutes(start_time)
    end_min = _parse_time_to_minutes(end_time)

    if start_min >= end_min:
        raise SchedulingValidationError(
            f"Start time '{start_time}' must be earlier than end time '{end_time}'."
        )

    # 2) Duración mínima 1 hora
    duration = end_min - start_min
    if duration < 60:
        raise SchedulingValidationError(
            f"Event duration must be at least 60 minutes. "
            f"Current duration: {duration} minutes."
        )

    # 3) Conflictos con otros eventos en misma fecha/location
    existing_events = get_events_for_date_location(date, location)

    conflicts = []
    for ev in existing_events:
        (
            ev_id,
            ev_name,
            ev_requester,
            ev_date,
            ev_start,
            ev_end,
            ev_location,
            ev_requester_unit,
        ) = ev

        ev_start_min = _parse_time_to_minutes(ev_start)
        ev_end_min = _parse_time_to_minutes(ev_end)

        # traslape si NO se cumple: new_end <= ev_start OR new_start >= ev_end
        overlap = not (end_min <= ev_start_min or start_min >= ev_end_min)
        if overlap:
            extra = f", {ev_requester_unit}" if ev_requester_unit else ""
            conflicts.append(
                f"- [{ev_id}] {ev_date} {ev_start}-{ev_end} | {ev_name} "
                f"({ev_requester}{extra} @ {ev_location})"
            )

    if conflicts:
        conflict_msg = "\n".join(conflicts)
        raise SchedulingValidationError(
            "Cannot schedule event due to time conflict with existing events:\n"
            + conflict_msg
        )
