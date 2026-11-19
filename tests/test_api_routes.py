"""
Integration tests for Flask web routes and API endpoints.
"""

import os
import sys
import unittest
import tempfile
import json
import gc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from services import db

class TestApiRoutes(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)
        os.environ["DATABASE_PATH"] = self.temp_db_path
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        gc.collect()
        try:
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except PermissionError:
            pass

    def test_page_renders(self):
        for path in ["/", "/dashboard", "/models", "/about", "/login", "/register"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Page {path} failed to load")

    def test_subdivisions_api(self):
        res = self.client.get("/api/subdivisions")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["subdivisions"]), 36)

    def test_map_data_api(self):
        res = self.client.get("/api/map-data?month=JUL")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["regions"]), 36)
        first = data["regions"][0]
        self.assertIn("latitude", first)
        self.assertIn("longitude", first)
        self.assertIn("current_model_prediction", first)

    def test_predict_api(self):
        payload = {
            "subdivision": "KERALA",
            "month": "JUL",
            "prev_month_rain_mm": 600.0,
            "model_name": "Gradient Boosting"
        }
        res = self.client.post("/api/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        pred = data["prediction"]
        self.assertIn("rain_probability_pct", pred)
        self.assertIn("prediction_label", pred)
        self.assertIn("estimated_amount_mm", pred)
        self.assertGreater(pred["rain_probability_pct"], 80)

    def test_models_benchmark_api(self):
        res = self.client.get("/api/models")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        rep = data["report"]
        self.assertIn("metrics", rep)
        self.assertGreaterEqual(len(rep["metrics"]), 6)
        self.assertIn("unavailable_models", rep)

if __name__ == "__main__":
    unittest.main()
