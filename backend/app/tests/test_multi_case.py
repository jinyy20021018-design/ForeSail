import os
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services.case_service import reset_store
from app.services.document_service import reset_document_store
from app.services.persistence_service import save_item


class MultiCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["USE_LLM_SUMMARY"] = "false"
        os.environ["REQUIRE_LLM_AGENT"] = "false"
        os.environ["OPENAI_API_KEY"] = ""
        reset_store()
        reset_document_store()
        self.client = TestClient(app)

    def create_case(self, name: str = "Manual Case") -> dict:
        response = self.client.post("/api/cases", json={"case_name": name, "owner": "Trade Ops"})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def approve_all_fields(self, case_id: str) -> None:
        fields = self.client.get(f"/api/cases/{case_id}/extracted-fields").json()
        self.assertTrue(fields)
        for field in fields:
            response = self.client.post(f"/api/cases/{case_id}/extracted-fields/{field['field_id']}/approve")
            self.assertEqual(response.status_code, 200, response.text)

    def test_empty_database_first_case_is_case_001(self) -> None:
        case = self.create_case()
        self.assertEqual(case["case_id"], "CASE-001")
        self.assertEqual(case["status"], "DRAFT")

    def test_consecutive_manual_cases_have_unique_ids(self) -> None:
        ids = [self.create_case(f"Manual Case {index}")["case_id"] for index in range(3)]
        self.assertEqual(ids, ["CASE-001", "CASE-002", "CASE-003"])
        cases = self.client.get("/api/cases").json()["cases"]
        self.assertEqual([case["case_id"] for case in cases], ids)

    def test_clean_demo_cases_do_not_overwrite_each_other(self) -> None:
        first = self.client.post("/api/cases/demo/clean").json()
        second = self.client.post("/api/cases/demo/clean").json()
        self.assertNotEqual(first["case_id"], second["case_id"])
        cases = self.client.get("/api/cases").json()["cases"]
        self.assertEqual(len(cases), 2)

    def test_conflict_demo_cases_do_not_overwrite_each_other(self) -> None:
        first = self.client.post("/api/cases/demo/conflict").json()
        second = self.client.post("/api/cases/demo/conflict").json()
        self.assertNotEqual(first["case_id"], second["case_id"])
        cases = self.client.get("/api/cases").json()["cases"]
        self.assertEqual(len(cases), 2)
        self.assertTrue(all(case["high_conflicts_count"] > 0 for case in cases))

    def test_clean_and_conflict_demo_can_coexist(self) -> None:
        clean = self.client.post("/api/cases/demo/clean").json()
        conflict = self.client.post("/api/cases/demo/conflict").json()
        summaries = {case["case_id"]: case for case in self.client.get("/api/cases").json()["cases"]}
        self.assertEqual(len(summaries), 2)
        self.assertEqual(summaries[clean["case_id"]]["high_conflicts_count"], 0)
        self.assertGreater(summaries[conflict["case_id"]]["high_conflicts_count"], 0)

    def test_documents_fields_conflicts_are_isolated_by_case(self) -> None:
        clean = self.client.post("/api/cases/demo/clean").json()["case_id"]
        conflict = self.client.post("/api/cases/demo/conflict").json()["case_id"]

        clean_documents = self.client.get(f"/api/cases/{clean}/documents").json()
        conflict_documents = self.client.get(f"/api/cases/{conflict}/documents").json()
        clean_fields = self.client.get(f"/api/cases/{clean}/extracted-fields").json()
        conflict_fields = self.client.get(f"/api/cases/{conflict}/extracted-fields").json()
        clean_conflicts = self.client.get(f"/api/cases/{clean}/field-conflicts").json()
        conflict_conflicts = self.client.get(f"/api/cases/{conflict}/field-conflicts").json()

        self.assertTrue(all(document["case_id"] == clean for document in clean_documents))
        self.assertTrue(all(document["case_id"] == conflict for document in conflict_documents))
        self.assertTrue(all(field["case_id"] == clean for field in clean_fields))
        self.assertTrue(all(field["case_id"] == conflict for field in conflict_fields))
        self.assertFalse(any(conflict_item["severity"] == "High" for conflict_item in clean_conflicts))
        self.assertTrue(any(conflict_item["severity"] == "High" for conflict_item in conflict_conflicts))

    def test_agent_runs_are_isolated_by_case(self) -> None:
        first = self.client.post("/api/cases/demo/clean").json()["case_id"]
        second = self.client.post("/api/cases/demo/clean").json()["case_id"]
        self.approve_all_fields(first)
        self.client.post(f"/api/cases/{first}/confirm-fields")

        run = self.client.post(f"/api/cases/{first}/agent-run")
        self.assertEqual(run.status_code, 200, run.text)

        first_runs = self.client.get(f"/api/cases/{first}/agent-runs").json()
        second_runs = self.client.get(f"/api/cases/{second}/agent-runs").json()
        self.assertEqual(len(first_runs), 1)
        self.assertEqual(first_runs[0]["case_id"], first)
        self.assertEqual(second_runs, [])

    def test_non_standard_case_id_does_not_break_generation(self) -> None:
        save_item("case", "DEMO-ABC", {"case_id": "DEMO-ABC", "status": "DRAFT"}, "DEMO-ABC")
        case = self.create_case()
        self.assertEqual(case["case_id"], "CASE-001")


if __name__ == "__main__":
    unittest.main()
