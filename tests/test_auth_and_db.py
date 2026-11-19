"""
Unit tests for authentication security, password hashing, and user ownership isolation.
"""

import os
import sys
import unittest
import tempfile
import gc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import db
from services.auth_service import register_user, authenticate_user

class TestAuthAndDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)
        os.environ["DATABASE_PATH"] = self.temp_db_path
        db.init_db()

    def tearDown(self):
        gc.collect()
        try:
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except PermissionError:
            pass

    def test_user_registration_and_password_hashing(self):
        plain = "SuperSecurePassword123"
        success, msg, user = register_user("scientist@imd.gov.in", plain, "Dr. Scientist")
        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "scientist@imd.gov.in")
        
        raw_user = db.get_user_by_email("scientist@imd.gov.in")
        self.assertNotEqual(raw_user["password_hash"], plain)
        self.assertTrue(raw_user["password_hash"].startswith("scrypt:") or raw_user["password_hash"].startswith("pbkdf2:"))

    def test_duplicate_email_rejection(self):
        register_user("unique@imd.gov.in", "Password123", "User One")
        success, msg, user = register_user("unique@imd.gov.in", "AnotherPass456", "User Two")
        self.assertFalse(success)
        self.assertIn("already exists", msg)

    def test_authentication_verification(self):
        register_user("auth@imd.gov.in", "ValidPassword88", "Auth Test")
        
        ok, msg, user = authenticate_user("auth@imd.gov.in", "ValidPassword88")
        self.assertTrue(ok)
        self.assertEqual(user["email"], "auth@imd.gov.in")
        
        fail, fmsg, fuser = authenticate_user("auth@imd.gov.in", "WrongPassword")
        self.assertFalse(fail)
        self.assertIsNone(fuser)

    def test_strict_user_ownership_isolation(self):
        _, _, user_a = register_user("usera@imd.gov.in", "Password123", "User A")
        _, _, user_b = register_user("userb@imd.gov.in", "Password123", "User B")
        
        pred_data = {
            "region": "KERALA",
            "season": "JUL",
            "model_used": "Gradient Boosting",
            "predicted_rain": 1,
            "rain_probability": 0.98,
            "rainfall_category": "Heavy / Excess Rain"
        }
        pred_id = db.save_prediction(user_a["id"], pred_data)
        
        preds_a = db.get_user_predictions(user_a["id"])
        self.assertEqual(len(preds_a), 1)
        self.assertEqual(preds_a[0]["region"], "KERALA")
        
        preds_b = db.get_user_predictions(user_b["id"])
        self.assertEqual(len(preds_b), 0)
        
        deleted_by_b = db.delete_user_prediction(user_b["id"], pred_id)
        self.assertFalse(deleted_by_b)
        
        self.assertEqual(len(db.get_user_predictions(user_a["id"])), 1)
        
        deleted_by_a = db.delete_user_prediction(user_a["id"], pred_id)
        self.assertTrue(deleted_by_a)
        self.assertEqual(len(db.get_user_predictions(user_a["id"])), 0)

if __name__ == "__main__":
    unittest.main()
