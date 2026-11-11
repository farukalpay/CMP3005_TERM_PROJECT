"""Hardware description for the report (thin wrapper around experiments/common.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "experiments"))
from common import hardware  # noqa: E402


def hw():
    return hardware()
