import os
import unittest
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.services.case_service import create_demo_case, reset_store
from app.services.document_service import reset_document_store
from app.services.pdf_detection_service import detect_pdf


class DocumentExtractionHardeningTest(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["DOCUMENT_EXTRACTION_MODE"] = "AUTO"
        os.environ["USE_LLM_EXTRACTION"] = "false"
        os.environ["OPENAI_API_KEY"] = ""
        os.environ["VISION_EXTRACTION_ENABLED"] = "false"
        reset_store()
        reset_document_store()
        self.case = create_demo_case()
        self.client = TestClient(app)

    def upload(self, filename: str, document_type: str, content: bytes, content_type: str = "application/octet-stream") -> dict:
        response = self.client.post(
            f"/api/cases/{self.case['case_id']}/documents/upload",
            data={"document_type": document_type},
            files={"file": (filename, BytesIO(content), content_type)},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def extract(self) -> dict:
        response = self.client.post(f"/api/cases/{self.case['case_id']}/documents/extract")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_txt_document_extracts_through_text_first_without_demo_fallback(self) -> None:
        self.upload("contract.txt", "CONTRACT_PO", b"Buyer: Real Buyer\nSeller: Real Seller\nAmount: USD 900\nCurrency: USD\nIncoterm: CIF\n")
        payload = self.extract()
        values = {field["field_name"]: field["value"] for field in payload["extracted_fields"]}
        self.assertEqual(values["buyer"], "Real Buyer")
        self.assertNotIn("vessel", values)
        self.assertTrue(all(value != "CAPEMOLLINI" for value in values.values()))
        self.assertEqual(payload["status"], "PARTIAL")

    def test_unparseable_document_fails_without_demo_fields(self) -> None:
        self.upload("empty.txt", "CONTRACT_PO", b"not a trade document")
        payload = self.extract()
        self.assertEqual(payload["extracted_fields"], [])
        self.assertEqual(payload["status"], "FAILED")
        diagnostic = payload["document_diagnostics"][0]
        self.assertEqual(diagnostic["status"], "FAILED")
        self.assertEqual(diagnostic["errors"][0]["code"], "NO_RELIABLE_FIELDS_EXTRACTED")

    def test_scanned_like_pdf_returns_needs_vision(self) -> None:
        pdf = b"%PDF-1.4\n1 0 obj<</Type /Page>>endobj\n%%EOF"
        self.upload("scanned.pdf", "LETTER_OF_CREDIT", pdf, "application/pdf")
        payload = self.extract()
        self.assertEqual(payload["status"], "NEEDS_VISION")
        diagnostic = payload["document_diagnostics"][0]
        self.assertEqual(diagnostic["pdf_type"], "SCANNED_PDF")
        self.assertEqual(diagnostic["status"], "NEEDS_VISION")
        self.assertEqual(diagnostic["errors"][0]["code"], "SCANNED_PDF_UNSUPPORTED")

    def test_openai_file_mode_returns_not_implemented(self) -> None:
        os.environ["DOCUMENT_EXTRACTION_MODE"] = "OPENAI_FILE"
        self.upload("contract.txt", "CONTRACT_PO", b"Buyer: Real Buyer")
        payload = self.extract()
        diagnostic = payload["document_diagnostics"][0]
        self.assertEqual(diagnostic["status"], "UNSUPPORTED")
        self.assertEqual(diagnostic["errors"][0]["code"], "OPENAI_FILE_NOT_IMPLEMENTED")

    def test_autofill_failed_when_no_reliable_fields(self) -> None:
        self.upload("empty.txt", "CONTRACT_PO", b"not a trade document")
        self.extract()
        response = self.client.post(f"/api/cases/{self.case['case_id']}/autofill-from-documents")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "FAILED")
        self.assertEqual(payload["autofill"], {})
        self.assertEqual(payload["errors"][0]["code"], "NO_RELIABLE_FIELDS_EXTRACTED")

    def test_text_pdf_detection_for_literal_text_pdf(self) -> None:
        import tempfile
        from pathlib import Path

        content = b"%PDF-1.4\n1 0 obj<</Type /Page>>endobj\n2 0 obj<</Length 260>>stream\nBT (" + (b"Buyer: Real Buyer Seller: Real Seller Amount: USD 900 Currency: USD " * 4) + b") Tj ET\nendstream\nendobj\n%%EOF"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as file:
            file.write(content)
            name = file.name
        detected = detect_pdf(Path(name))
        self.assertEqual(detected["pdf_type"], "TEXT_PDF")


if __name__ == "__main__":
    unittest.main()
