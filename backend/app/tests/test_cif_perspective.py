import os
import unittest
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.services.case_service import reset_store
from app.services.document_service import reset_document_store


class CifPerspectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["EVENT_SOURCE_MODE"] = "MOCK"
        os.environ["USE_LLM_SUMMARY"] = "false"
        os.environ["REQUIRE_LLM_AGENT"] = "false"
        os.environ["OPENAI_API_KEY"] = ""
        os.environ["DOCUMENT_EXTRACTION_MODE"] = "AUTO"
        os.environ["USE_LLM_EXTRACTION"] = "false"
        reset_store()
        reset_document_store()
        self.client = TestClient(app)

    def create_confirmed_case(self) -> str:
        case_id = self.client.post("/api/cases/demo/clean").json()["case_id"]
        fields = self.client.get(f"/api/cases/{case_id}/extracted-fields").json()
        self.assertTrue(fields)
        for field in fields:
            response = self.client.post(f"/api/cases/{case_id}/extracted-fields/{field['field_id']}/approve")
            self.assertEqual(response.status_code, 200, response.text)
        response = self.client.post(f"/api/cases/{case_id}/confirm-fields")
        self.assertEqual(response.status_code, 200, response.text)
        return case_id

    def test_cif_responsibility_matrix(self) -> None:
        case_id = self.create_confirmed_case()
        response = self.client.get(f"/api/cases/{case_id}/cif-responsibility")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()

        self.assertEqual(payload["incoterm"], "CIF")
        self.assertEqual(payload["named_destination_port"], "Chittagong")
        self.assertEqual(payload["risk_transfer_point"], "Loaded on board at port of loading")
        self.assertIn("arrange insurance", payload["seller_responsibilities"])
        self.assertIn("import clearance", payload["buyer_responsibilities"])
        self.assertEqual(payload["cost_responsibility"]["cargo_insurance"], "SELLER")
        self.assertEqual(payload["cost_responsibility"]["main_carriage"], "SELLER")
        self.assertEqual(payload["cost_responsibility"]["import_clearance"], "BUYER")

    def test_both_perspective_is_rejected(self) -> None:
        case_id = self.create_confirmed_case()
        response = self.client.get(f"/api/cases/{case_id}/perspective-analysis?perspective=BOTH")
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["error"], "UNSUPPORTED_PERSPECTIVE")

    def test_buyer_and_seller_outputs_differ_under_cif(self) -> None:
        case_id = self.create_confirmed_case()
        agent_response = self.client.post(f"/api/cases/{case_id}/agent-run")
        self.assertEqual(agent_response.status_code, 200, agent_response.text)

        buyer = self.client.get(f"/api/cases/{case_id}/perspective-analysis?perspective=BUYER").json()
        seller = self.client.get(f"/api/cases/{case_id}/perspective-analysis?perspective=SELLER").json()

        buyer_exposures = buyer["risk_summary"]["exposures"]
        seller_exposures = seller["risk_summary"]["exposures"]
        self.assertTrue(any(item["cif_scenario"] == "destination_port_congestion" and item["severity"] == "High" for item in buyer_exposures))
        self.assertTrue(any(item["category"] == "LC Deadline" and item["severity"] == "High" for item in seller_exposures))
        self.assertTrue(any(action["title"] == "Coordinate customs broker / port agent" for action in buyer["actions"]))
        self.assertTrue(any(action["title"] == "Prepare or verify insurance certificate" for action in seller["actions"]))
        self.assertTrue(all(action["party_perspective"] == "BUYER" for action in buyer["actions"]))
        self.assertTrue(all(action["incoterm_basis"] == "CIF" for action in seller["actions"]))

        self.assertTrue(seller["treatment_plans"])
        self.assertEqual(seller["treatment_plans"][0]["perspective"], "SELLER")
        self.assertEqual(seller["treatment_plans"][0]["incoterm_basis"], "CIF")

        step_names = {step["name"] for step in agent_response.json()["trace"]}
        self.assertIn("Resolve CIF Responsibilities", step_names)
        self.assertIn("Apply Buyer/Seller Perspective", step_names)
        self.assertIn("Generate CIF-specific Actions", step_names)
        self.assertIn("Generate CIF-specific Treatment Plan Summary", step_names)

    def test_missing_cif_named_place_returns_warning(self) -> None:
        case_id = self.client.post("/api/cases", json={"case_name": "Missing Named Place"}).json()["case_id"]
        upload = self.client.post(
            f"/api/cases/{case_id}/documents/upload",
            data={"document_type": "CONTRACT_PO"},
            files={"file": ("contract.txt", BytesIO(b"Buyer: A\nSeller: B\nAmount: USD 900\nCurrency: USD\nIncoterm: CIF\nPayment Method: LC at sight\n"), "text/plain")},
        )
        self.assertEqual(upload.status_code, 200, upload.text)
        extracted = self.client.post(f"/api/cases/{case_id}/documents/extract")
        self.assertEqual(extracted.status_code, 200, extracted.text)
        warnings = extracted.json()["document_diagnostics"][0]["warnings"]
        self.assertIn("CIF_NAMED_DESTINATION_PORT_MISSING", warnings)


if __name__ == "__main__":
    unittest.main()
