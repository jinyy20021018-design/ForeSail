import os
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services.case_service import reset_store
from app.services.document_service import reset_document_store


class CaseDetailAutofillTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["USE_LLM_EXTRACTION"] = "false"
        os.environ["OPENAI_API_KEY"] = ""
        reset_store()
        reset_document_store()
        self.client = TestClient(app)

    def test_autofill_from_demo_documents_returns_draft_details_and_sources(self) -> None:
        case_id = self.client.post("/api/cases/demo/clean").json()["case_id"]
        response = self.client.post(f"/api/cases/{case_id}/autofill-from-documents")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["case_id"], case_id)
        self.assertEqual(payload["extraction_mode"], "AUTO")
        self.assertTrue(payload["fallback_used"])
        self.assertIn("case_name", payload["autofill"])
        self.assertEqual(payload["autofill"]["owner"], "Trade Ops")
        self.assertIn("vessel", payload["extra_facts"])
        self.assertIn("vessel", payload["field_sources"])
        self.assertIn("evidence", payload["field_sources"]["vessel"])

        confirmed = self.client.get(f"/api/cases/{case_id}/confirmed-facts")
        self.assertEqual(confirmed.status_code, 404)

    def test_update_case_details_updates_shell_only(self) -> None:
        case_id = self.client.post("/api/cases", json={"case_name": "Draft"}).json()["case_id"]
        response = self.client.post(
            f"/api/cases/{case_id}/details",
            json={"case_name": "Updated Draft", "buyer": "Buyer A", "port_of_loading": "Shanghai", "port_of_discharge": "Chittagong"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["case_name"], "Updated Draft")
        self.assertEqual(payload["buyer"], "Buyer A")
        self.assertEqual(payload["route"], "Shanghai -> Chittagong")


if __name__ == "__main__":
    unittest.main()
