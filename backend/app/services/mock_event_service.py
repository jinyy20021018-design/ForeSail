import copy
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def get_mock_events() -> list[dict]:
    with (DATA_DIR / "mock_events.json").open("r", encoding="utf-8") as file:
        return copy.deepcopy(json.load(file))
