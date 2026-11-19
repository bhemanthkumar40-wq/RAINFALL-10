"""
Unit tests for data pipeline and dataset validation.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.data_pipeline import (
    load_india_dataset,
    get_india_dataset_summary,
    prepare_india_train_test_split,
    INDIA_SUBDIVISION_COORDINATES
)

class TestDataPipeline(unittest.TestCase):
    def test_india_dataset_loading(self):
        df = load_india_dataset()
        self.assertFalse(df.empty, "Dataset should not be empty")
        self.assertGreaterEqual(len(df), 4000, "Dataset should contain over 4,000 annual records")
        self.assertIn("SUBDIVISION", df.columns)
        self.assertIn("YEAR", df.columns)
        self.assertIn("ANNUAL", df.columns)
        self.assertEqual(df["SUBDIVISION"].nunique(), 36, "Dataset must contain exactly 36 subdivisions")

    def test_subdivision_summary_and_coordinates(self):
        summary = get_india_dataset_summary()
        self.assertEqual(summary["total_subdivisions"], 36)
        self.assertIn("subdivisions", summary)
        
        for sub in summary["subdivisions"]:
            self.assertIn("latitude", sub)
            self.assertIn("longitude", sub)
            self.assertIn("annual_rainfall_mean_mm", sub)
            self.assertGreater(sub["annual_rainfall_mean_mm"], 0)
            self.assertIn("monthly_medians", sub)

    def test_train_test_split_stratification(self):
        X_train, X_test, y_train, y_test, preproc = prepare_india_train_test_split(test_size=0.2, random_state=42)
        self.assertEqual(len(X_train) + len(X_test), 49392)
        self.assertGreater(len(y_train), 39000)
        self.assertGreater(len(y_test), 9800)
        # Class balance should be consistent across train and test
        train_pos_ratio = sum(y_train) / len(y_train)
        test_pos_ratio = sum(y_test) / len(y_test)
        self.assertAlmostEqual(train_pos_ratio, test_pos_ratio, places=2)

if __name__ == "__main__":
    unittest.main()
