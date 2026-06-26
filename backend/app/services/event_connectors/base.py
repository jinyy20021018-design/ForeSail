from typing import Protocol


class EventConnector(Protocol):
    name: str

    def fetch_events(self, watch_profile: dict, case_id: str) -> list[dict]:
        ...
