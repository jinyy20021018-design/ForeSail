import unittest

from app.services.case_service import create_demo_case, reset_store
from app.services.mock_event_service import get_mock_events
from app.services.relevance_engine import classify_events
from app.services.risk_mapper import summarize_exposures


class RiskMapperTest(unittest.TestCase):
    def setUp(self) -> None:
        reset_store()
        self.case = create_demo_case()
        self.events = get_mock_events()
        self.results = classify_events(self.case, self.events)

    def test_expected_exposure_categories(self) -> None:
        result_by_id = {result["event_id"]: result for result in self.results}
        self.assertEqual(
            set(result_by_id["EVT-001"]["mapped_exposures"]),
            {"Shipping", "Payment Timeline", "LC Deadline"},
        )
        self.assertEqual(
            set(result_by_id["EVT-002"]["mapped_exposures"]),
            {"Port Operation", "Shipping", "Payment Timeline"},
        )
        self.assertEqual(set(result_by_id["EVT-003"]["mapped_exposures"]), {"Shipping", "LC Deadline"})
        self.assertEqual(result_by_id["EVT-004"]["mapped_exposures"], [])
        self.assertEqual(result_by_id["EVT-005"]["mapped_exposures"], [])

    def test_summary_is_triggered_by_relevant_events(self) -> None:
        summary = summarize_exposures(self.case, self.events, self.results)
        self.assertTrue(summary["triggered"])
        self.assertEqual(set(summary["trigger_events"]), {"EVT-001", "EVT-002"})
        self.assertEqual(summary["watch_events_considered"], ["EVT-003"])

    def test_trigger_and_watch_evidence_are_separated(self) -> None:
        summary = summarize_exposures(self.case, self.events, self.results)
        exposure_by_category = {exposure["category"]: exposure for exposure in summary["exposures"]}

        self.assertIn("EVT-001", exposure_by_category["LC Deadline"]["trigger_event_ids"])
        self.assertIn("EVT-003", exposure_by_category["LC Deadline"]["watch_event_ids"])


if __name__ == "__main__":
    unittest.main()
