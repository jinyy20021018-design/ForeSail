import unittest

from app.services.action_board_service import generate_actions


class ActionBoardTest(unittest.TestCase):
    def test_generates_deduplicated_actions_from_exposures(self) -> None:
        risk_summary = {
            "exposures": [
                {"category": "Shipping"},
                {"category": "Shipping"},
                {"category": "LC Deadline"},
                {"category": "Payment Timeline"},
            ]
        }
        actions = generate_actions(risk_summary)
        titles = [action["title"] for action in actions]

        self.assertEqual(len(titles), len(set(titles)))
        self.assertIn("Contact carrier to confirm latest ETA and delay reason", titles)
        self.assertIn("Prepare LC amendment request if shipment timing becomes non-compliant", titles)
        self.assertIn("Update expected payment and cashflow timeline", titles)


if __name__ == "__main__":
    unittest.main()
