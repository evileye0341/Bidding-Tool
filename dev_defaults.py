from datetime import date
from pathlib import Path


DEV_DEFAULT_BID_LABEL = "June 2026"
DEV_DEFAULT_START_DATE = date(2026, 6, 2)
DEV_DEFAULT_END_DATE = date(2026, 7, 1)
DEV_REQUIREMENTS_PATH = (
    Path(__file__).parent / "dev_data" / "reserve_requirements_june_2026.txt"
)


def load_dev_requirements_text():
    if not DEV_REQUIREMENTS_PATH.exists():
        return ""

    return DEV_REQUIREMENTS_PATH.read_text(encoding="utf-8").strip()
