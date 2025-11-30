import os
import sys

BASE_DIR = os.path.dirname(__file__)
CODE_DIR = os.path.join(BASE_DIR, "eventdsl")

if CODE_DIR not in sys.path:
    sys.path.append(CODE_DIR)

from gui.rules_ide import run_ide
if __name__ == "__main__":
    run_ide()
