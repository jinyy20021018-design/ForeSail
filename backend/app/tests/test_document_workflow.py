import os
import unittest
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.services.case_service import create_demo_case, reset_store
from app.services.document_service import reset_document_store


class DocumentWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["USE_LLM_SUMMARY"] = "false"
        os.environ["REQUIRE_LLM_AGENT"] = "false"
        os.environ["OPENAI_API_KEY"] = ""
        os.environ.pop("USE_LLM_EXTRACTION", None)
        os.environ.pop("LLM_EXTRACTION_TEST_INVALID_JSON", None)
        reset_store()
        reset_document_store()
        self.case = create_demo_case()
        self.client = TestClient(app)

    def upload_text(self, filename: str, document_type: str, text: str) -> dict:
        response = self.client.post(
            f"/api/cases/{self.case['case_id']}/documents/upload",
            data={"document_type": document_type},
            files={"file": (filename, BytesIO(text.encode("utf-8")), "text/plain")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def seed_documents(self) -> None:
        self.upload_text(
            "contract.txt",
            "CONTRACT_PO",
            "\n".join([
                "Commodity: Cotton Yarn",
                "Quantity: 100 MT",
                "Amount: USD 1250000",
                "Currency: USD",
                "Buyer: Demo Buyer",
                "Seller: Demo Seller",
                "Incoterm: CIF",
                "Payment Method: LC at sight",
                "Final Destination: Dhaka",
            ]),
        )
        self.upload_text(
            "booking.txt",
            "BOOKING_CONFIRMATION",
            "\n".join([
                "Booking Reference: BKG-7788",
                "Vessel: CAPEMOLLINI",
                "Route: Shanghai -> Chittagong -> Dhaka",
                "Port of Loading: Shanghai",
                "Port of Discharge: Chittagong",
                "Final Destination: Dhaka",
                "ETD: 2026-11-25",
                "ETA: 2026-12-08",
            ]),
        )
        self.upload_text(
            "lc.txt",
            "LETTER_OF_CREDIT",
            "\n".join([
                "LC Number: LC-001",
                "Issuing Bank: Demo Bank",
                "Applicant: Demo Buyer",
                "Beneficiary: Demo Seller",
                "Amount: USD 1250000",
                "Currency: USD",
                "Latest Shipment: 2026-11-30",
                "LC Expiry: 2026-12-31",
                "Presentation Period: 21",
                "Payment Method: LC at sight",
            ]),
        )

    def extract(self) -> list[dict]:
        response = self.client.post(f"/api/cases/{self.case['case_id']}/documents/extract")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["extracted_fields"]

    def approve_all_fields(self, fields: list[dict]) -> None:
        for field in fields:
            response = self.client.post(f"/api/cases/{self.case['case_id']}/extracted-fields/{field['field_id']}/approve")
            self.assertEqual(response.status_code, 200, response.text)

    def test_document_upload_endpoint_works(self) -> None:
        document = self.upload_text("contract.txt", "CONTRACT_PO", "Incoterm: CIF")
        self.assertEqual(document["parse_status"], "UPLOADED")

    def test_extraction_returns_fields_with_evidence_and_confidence(self) -> None:
        self.seed_documents()
        fields = self.extract()
        self.assertTrue(fields)
        self.assertTrue(all("evidence_text" in field for field in fields))
        self.assertTrue(all("confidence" in field for field in fields))

    def test_approve_edit_reject_field_works(self) -> None:
        self.seed_documents()
        fields = self.extract()
        field_id = fields[0]["field_id"]
        self.assertEqual(self.client.post(f"/api/cases/{self.case['case_id']}/extracted-fields/{field_id}/approve").status_code, 200)
        edit = self.client.post(
            f"/api/cases/{self.case['case_id']}/extracted-fields/{field_id}/edit",
            json={"value": "Edited Value"},
        )
        self.assertEqual(edit.status_code, 200)
        self.assertEqual(edit.json()["review_status"], "EDITED")
        reject = self.client.post(f"/api/cases/{self.case['case_id']}/extracted-fields/{field_id}/reject")
        self.assertEqual(reject.status_code, 200)
        self.assertEqual(reject.json()["review_status"], "REJECTED")

    def test_confirm_fields_generates_confirmed_facts(self) -> None:
        self.seed_documents()
        fields = self.extract()
        self.approve_all_fields(fields)
        response = self.client.post(f"/api/cases/{self.case['case_id']}/confirm-fields")
        self.assertEqual(response.status_code, 200, response.text)
        facts = response.json()
        self.assertEqual(facts["vessel"], "CAPEMOLLINI")
        self.assertEqual(facts["currency"], "USD")

    def test_missing_critical_fields_block_confirmation(self) -> None:
        self.seed_documents()
        fields = self.extract()
        for field in fields:
            if field["field_name"] != "vessel":
                self.client.post(f"/api/cases/{self.case['case_id']}/extracted-fields/{field['field_id']}/approve")
        response = self.client.post(f"/api/cases/{self.case['case_id']}/confirm-fields")
        self.assertEqual(response.status_code, 400)

    def test_agent_run_returns_obligations_gaps_and_drafts(self) -> None:
        self.seed_documents()
        fields = self.extract()
        self.approve_all_fields(fields)
        self.client.post(f"/api/cases/{self.case['case_id']}/confirm-fields")
        response = self.client.post(f"/api/cases/{self.case['case_id']}/agent-run")
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertGreaterEqual(len(result["trace"]), 12)
        self.assertTrue(result["obligations"])
        self.assertTrue(result["information_gaps"])
        self.assertTrue(result["action_drafts"])
        obligation_names = {obligation["name"] for obligation in result["obligations"]}
        self.assertIn("Latest Shipment Date", obligation_names)
        latest = next(obligation for obligation in result["obligations"] if obligation["name"] == "Latest Shipment Date")
        self.assertEqual(latest["current_assessment"], "At risk due to vessel delay")

    def test_no_llm_api_key_extraction_fallback_works(self) -> None:
        os.environ["USE_LLM_EXTRACTION"] = "true"
        os.environ["OPENAI_API_KEY"] = ""
        self.seed_documents()
        fields = self.extract()
        self.assertTrue(fields)

    def test_invalid_llm_json_fallback_works(self) -> None:
        os.environ["USE_LLM_EXTRACTION"] = "true"
        os.environ["LLM_EXTRACTION_TEST_INVALID_JSON"] = "true"
        self.seed_documents()
        fields = self.extract()
        self.assertTrue(fields)


if __name__ == "__main__":
    unittest.main()
