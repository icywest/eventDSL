import os
import sys

BASE_DIR = os.path.dirname(__file__)
CODE_DIR = os.path.join(BASE_DIR, "eventdsl")

if CODE_DIR not in sys.path:
    sys.path.append(CODE_DIR)

from gui.add_event_view import run_add_event_app
if __name__ == "__main__":
    run_add_event_app()
