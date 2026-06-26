import os
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services.case_service import reset_store
from app.services.document_service import reset_document_store


class TreatmentPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["USE_LLM_SUMMARY"] = "false"
        os.environ["REQUIRE_LLM_AGENT"] = "false"
        os.environ["OPENAI_API_KEY"] = ""
        reset_store()
        reset_document_store()
        self.client = TestClient(app)

    def create_clean_confirmed_case(self) -> str:
        case_id = self.client.post("/api/cases/demo/clean").json()["case_id"]
        self.approve_all_fields(case_id)
        response = self.client.post(f"/api/cases/{case_id}/confirm-fields")
        self.assertEqual(response.status_code, 200, response.text)
        return case_id

    def approve_all_fields(self, case_id: str) -> None:
        fields = self.client.get(f"/api/cases/{case_id}/extracted-fields").json()
        self.assertTrue(fields)
        for field in fields:
            response = self.client.post(f"/api/cases/{case_id}/extracted-fields/{field['field_id']}/approve")
            self.assertEqual(response.status_code, 200, response.text)

    def generate(self, case_id: str) -> dict:
        response = self.client.post(f"/api/cases/{case_id}/treatment-plans/generate")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_confirmed_case_can_generate_treatment_plans(self) -> None:
        case_id = self.create_clean_confirmed_case()
        result = self.generate(case_id)
        self.assertEqual(len(result["plans"]), 3)
        self.assertFalse(result["conflict_safe_mode"])
        self.assertEqual(result["allowed_plan_types"], ["LOW_COST", "BALANCED", "MAX_PROTECTION"])
        self.assertTrue(result["recommended_plan_id"])

    def test_blank_case_without_confirmed_facts_cannot_generate_treatment_plans(self) -> None:
        case_id = self.client.post("/api/cases", json={"case_name": "Blank Review Case"}).json()["case_id"]
        response = self.client.post(f"/api/cases/{case_id}/treatment-plans/generate")
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json()["error"], "CONFIRMED_FACTS_REQUIRED")
        self.assertEqual(response.json()["message"], "Confirmed case facts are required before generating treatment plans.")

    def test_treatment_plans_are_isolated_by_case(self) -> None:
        first = self.create_clean_confirmed_case()
        second = self.client.post("/api/cases/demo/clean").json()["case_id"]
        self.generate(first)
        self.assertGreater(len(self.client.get(f"/api/cases/{first}/treatment-plans").json()), 0)
        self.assertEqual(self.client.get(f"/api/cases/{second}/treatment-plans").json(), [])

    def test_recommended_plan_and_residual_risks_exist(self) -> None:
        case_id = self.create_clean_confirmed_case()
        result = self.generate(case_id)
        recommended = [plan for plan in result["plans"] if plan["status"] == "RECOMMENDED"]
        self.assertEqual(len(recommended), 1)
        for plan in result["plans"]:
            self.assertIn("residual_risks", plan)
            self.assertIsInstance(plan["residual_risks"], list)

    def test_select_and_archive_plan(self) -> None:
        case_id = self.create_clean_confirmed_case()
        plans = self.generate(case_id)["plans"]
        plan_id = plans[0]["plan_id"]
        selected = self.client.post(f"/api/cases/{case_id}/treatment-plans/{plan_id}/select")
        self.assertEqual(selected.status_code, 200, selected.text)
        self.assertEqual(selected.json()["status"], "SELECTED")

        archived = self.client.post(f"/api/cases/{case_id}/treatment-plans/{plan_id}/archive")
        self.assertEqual(archived.status_code, 200, archived.text)
        self.assertEqual(archived.json()["status"], "ARCHIVED")

    def test_approval_package_and_status_updates(self) -> None:
        case_id = self.create_clean_confirmed_case()
        plan_id = self.generate(case_id)["recommended_plan_id"]
        package = self.client.post(f"/api/cases/{case_id}/treatment-plans/{plan_id}/approval-package")
        self.assertEqual(package.status_code, 200, package.text)
        self.assertEqual(package.json()["plan_id"], plan_id)
        package_id = package.json()["approval_package_id"]

        for status in ["SUBMITTED", "APPROVED", "REJECTED", "NEEDS_MORE_INFO", "ARCHIVED"]:
            response = self.client.post(
                f"/api/cases/{case_id}/approval-packages/{package_id}/status",
                json={"status": status, "decision_note": f"{status} for test"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["approval_status"], status)

    def test_unresolved_high_conflict_still_generates_low_cost_plan(self) -> None:
        case_id = self.client.post("/api/cases/demo/conflict").json()["case_id"]
        result = self.generate(case_id)
        self.assertTrue(result["conflict_safe_mode"])
        self.assertEqual(result["allowed_plan_types"], ["LOW_COST"])
        self.assertEqual(len(result["plans"]), 1)
        low_cost = result["plans"][0]
        self.assertEqual(result["recommended_plan_id"], low_cost["plan_id"])
        self.assertEqual(low_cost["plan_type"], "LOW_COST")
        self.assertEqual(low_cost["status"], "RECOMMENDED")
        self.assertTrue(low_cost["conflict_safe_mode"])
        self.assertIn("Unresolved high-severity conflicts", low_cost["rationale"])

    def test_conflict_safe_approval_package_is_marked_not_execution_approval(self) -> None:
        case_id = self.client.post("/api/cases/demo/conflict").json()["case_id"]
        plan_id = self.generate(case_id)["recommended_plan_id"]
        package = self.client.post(f"/api/cases/{case_id}/treatment-plans/{plan_id}/approval-package")
        self.assertEqual(package.status_code, 200, package.text)
        self.assertEqual(package.json()["plan_id"], plan_id)
        self.assertTrue(package.json()["conflict_safe_mode"])
        self.assertEqual(package.json()["approval_scope"], "CONFLICT_RESOLUTION_ONLY")

    def test_agent_run_trace_contains_treatment_steps(self) -> None:
        case_id = self.create_clean_confirmed_case()
        response = self.client.post(f"/api/cases/{case_id}/agent-run")
        self.assertEqual(response.status_code, 200, response.text)
        step_names = {step["name"] for step in response.json()["trace"]}
        self.assertIn("Generate Treatment Plans", step_names)
        self.assertIn("Generate Residual Risk Summary", step_names)
        self.assertIn("Generate Approval Summary Draft", step_names)
        self.assertIn("Persist Treatment Outputs", step_names)


if __name__ == "__main__":
    unittest.main()
