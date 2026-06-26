from app.services.mock_event_service import get_mock_events


class MockEventConnector:
    name = "mock_event_connector"

    def fetch_events(self, watch_profile: dict, case_id: str) -> list[dict]:
        return get_mock_events()
