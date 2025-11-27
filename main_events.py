# main_events.py
import sys
import os

from parsers.events import parse_and_save_events
from db import list_events, init_db


def print_all_events():
    events = list_events()
    if not events:
        print("No hay eventos guardados todavía.")
        return

    print("\nEventos en la base de datos:")
    print("-" * 60)
    for ev in events:
        ev_id, name, requester_type, campus_id, date, start, end, location = ev
        print(
            f"[{ev_id}] {date} {start}-{end} | {name} "
            f"({requester_type}, Campus {campus_id}) @ {location}"
        )


def main():
    if len(sys.argv) < 2:
        print("Uso: python main_events.py examples/events/demo.evdsl")
        sys.exit(1)

    dsl_path = sys.argv[1]

    if not os.path.exists(dsl_path):
        print(f"Error: No existe el archivo '{dsl_path}'")
        sys.exit(1)

    parse_and_save_events(dsl_path)
    print_all_events()


if __name__ == "__main__":
    init_db()
    main()
