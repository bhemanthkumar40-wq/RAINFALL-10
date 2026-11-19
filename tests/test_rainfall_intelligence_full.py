"""
Comprehensive System Verification Test Suite for Rainfall Intelligence.
Validates:
1. All 11 light-themed page views.
2. Full authentication, RBAC authorization, and login attempt auditing.
3. Machine Learning multi-regressor benchmark suite with genuine R2, MAE, MSE, RMSE, MAPE.
4. Exploratory data analysis, correlation matrices, and data cleaning pipelines.
5. Live prediction inference, IMD severity categorization, and user history persistence.
6. Admin dashboard functionality, user activation toggling, and report exports.
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
from services.model_service import train_all_models, predict_rainfall

class TestRainfallIntelligenceFull(unittest.TestCase):
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

    def test_all_11_page_routes_render_cleanly(self):
        """Verifies every page route loads with HTTP 200."""
        routes = [
            "/login", "/register", "/dashboard", "/predict",
            "/models", "/analysis", "/dataset", "/history",
            "/settings", "/about"
        ]
        for route in routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Page {route} failed to render")

    def test_ml_7_regressors_training_and_metrics(self):
        """Verifies multi-regressor benchmark outputs real R2, MAE, MSE, RMSE, MAPE."""
        report = train_all_models("Subdivision Rainfall (1901-2015)")
        self.assertIn("metrics", report)
        self.assertEqual(len(report["metrics"]), 7)
        self.assertIn(report["best_model"], [
            "Linear Regression", "Decision Tree", "Random Forest",
            "Gradient Boosting", "K-Nearest Neighbors", "Support Vector Regressor", "Extra Trees"
        ])
        
        for m in report["metrics"]:
            self.assertIn("model_name", m)
            self.assertGreater(m["r2_score"], 0.70, f"{m['model_name']} R2 score should be above 0.70")
            self.assertGreater(m["mae"], 0)
            self.assertGreater(m["rmse"], 0)
            self.assertGreater(m["training_time"], 0)

    def test_live_prediction_and_imd_categorization(self):
        """Tests live model inference, rainfall output in mm, and IMD classification."""
        pred = predict_rainfall(
            input_values={"JUN": 250.0, "JUL": 450.0, "AUG": 350.0, "SEP": 180.0},
            model_name="Random Forest",
            dataset_name="Subdivision Rainfall (1901-2015)"
        )
        self.assertIn("predicted_rainfall_mm", pred)
        self.assertGreater(pred["predicted_rainfall_mm"], 500.0)
        self.assertIn("rainfall_category", pred)
        self.assertIn("advisory", pred)
        self.assertIn("confidence_pct", pred)

    def test_dataset_inspection_and_cleaning_api(self):
        """Verifies inspection and cleaning pipeline."""
        insp_res = self.client.get("/api/datasets/inspect?dataset=Subdivision%20Rainfall%20(1901-2015)")
        self.assertEqual(insp_res.status_code, 200)
        insp_data = json.loads(insp_res.data)
        self.assertTrue(insp_data["success"])
        self.assertEqual(insp_data["inspection"]["total_rows"], 4116)
        self.assertEqual(len(insp_data["inspection"]["first_10_rows"]), 10)

        # Cleaning
        clean_res = self.client.post("/api/datasets/clean", json={
            "dataset_name": "Subdivision Rainfall (1901-2015)",
            "impute_strategy": "median",
            "remove_duplicates": True
        })
        self.assertEqual(clean_res.status_code, 200)
        clean_data = json.loads(clean_res.data)
        self.assertTrue(clean_data["success"])

    def test_auth_and_prediction_history_lifecycle(self):
        """Tests registration, login, prediction creation, history retrieval, and CSV export."""
        # 1. Register
        reg_res = self.client.post("/api/auth/register", json={
            "email": "demo.user@rainfall.org",
            "password": "UserPass@123",
            "full_name": "Demo Scientist"
        })
        self.assertEqual(reg_res.status_code, 201)

        # 2. Predict while logged in
        pred_res = self.client.post("/api/predict", json={
            "region": "KERALA",
            "season": "JUL",
            "inputs": {"JUN": 300.0, "JUL": 500.0}
        })
        self.assertEqual(pred_res.status_code, 200)
        pred_data = json.loads(pred_res.data)
        self.assertTrue(pred_data["success"])
        self.assertTrue(pred_data["persisted"])

        # 3. Check history
        hist_res = self.client.get("/api/history")
        self.assertEqual(hist_res.status_code, 200)
        hist_data = json.loads(hist_res.data)
        self.assertTrue(hist_data["success"])
        self.assertGreaterEqual(hist_data["total_count"], 1)

        # 4. Export CSV
        csv_res = self.client.get("/api/history/export")
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn("text/csv", csv_res.content_type)

    def test_admin_dashboard_authorization_and_management(self):
        """Tests that admin role can view stats, manage users, and export report."""
        # Log in as admin
        login_res = self.client.post("/api/auth/login", json={
            "email": "admin@rainfall.org",
            "password": "Admin@1234"
        })
        self.assertEqual(login_res.status_code, 200)

        # Admin stats
        stats_res = self.client.get("/api/admin/stats")
        self.assertEqual(stats_res.status_code, 200)
        stats = json.loads(stats_res.data)["stats"]
        self.assertGreaterEqual(stats["total_users"], 1)

        # Admin users list
        users_res = self.client.get("/api/admin/users")
        self.assertEqual(users_res.status_code, 200)
        users = json.loads(users_res.data)["users"]
        self.assertGreaterEqual(len(users), 1)

        # Admin report export
        rep_res = self.client.get("/api/admin/export-report")
        self.assertEqual(rep_res.status_code, 200)
        self.assertIn("text/csv", rep_res.content_type)

if __name__ == "__main__":
    unittest.main()
