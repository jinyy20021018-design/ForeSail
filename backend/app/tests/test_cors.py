import unittest

from fastapi.testclient import TestClient

from app.main import app, allowed_origins


class CorsMiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_configured_origins_include_local_defaults(self) -> None:
        self.assertIn("http://localhost:5173", allowed_origins)
        self.assertIn("http://127.0.0.1:5173", allowed_origins)

    def test_production_origin_is_allowed(self) -> None:
        response = self.client.get("/api/cases", headers={"Origin": "https://fore-sail.vercel.app"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "https://fore-sail.vercel.app")

    def test_preview_origin_is_allowed(self) -> None:
        origin = "https://fore-sail-git-preview-team.vercel.app"
        response = self.client.get("/api/cases", headers={"Origin": origin})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("access-control-allow-origin"), origin)

    def test_localhost_origin_is_allowed(self) -> None:
        origin = "http://localhost:5173"
        response = self.client.get("/api/cases", headers={"Origin": origin})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("access-control-allow-origin"), origin)

    def test_unrelated_origin_is_rejected(self) -> None:
        response = self.client.get("/api/cases", headers={"Origin": "https://evil.vercel.app"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.headers.get("access-control-allow-origin"))

    def test_cases_preflight_allows_production_origin(self) -> None:
        origin = "https://fore-sail.vercel.app"
        response = self.client.options(
            "/api/cases",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("access-control-allow-origin"), origin)
