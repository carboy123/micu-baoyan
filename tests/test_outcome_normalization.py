"""Regression checks for reviewed destination abbreviations and cohort metadata."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("studio_import", ROOT / "scripts/import-studio-data.py")
studio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(studio)


class OutcomeNormalizationTests(unittest.TestCase):
    def test_reviewed_destination_rows_are_recognized(self):
        cases = [(2025, 29, "湖大", "湖南大学"), (2025, 53, "电科直博", "电子科技大学"),
                 (2025, 55, "湖大人机院", "湖南大学"), (2027, 6, "控制工程", "中国地质大学"),
                 (2027, 21, "电科深", "电子科技大学"), (2027, 54, "电科", "电子科技大学"),
                 (2027, 67, "南京邮电大大学集成电路", "南京邮电大学"), (2027, 69, "北理珠", "北京理工大学")]
        for year, row, text, expected in cases:
            with self.subTest(year=year, row=row):
                self.assertEqual(studio.outcome_school(year, row, text), expected)

    def test_contextual_correction_does_not_reclassify_other_records(self):
        self.assertEqual(studio.outcome_school(2027, 999, "控制工程"), studio.UNKNOWN_SCHOOL)
        self.assertEqual(studio.outcome_school(2027, 999, "湖大"), studio.UNKNOWN_SCHOOL)
        self.assertEqual(studio.outcome_school(2027, 999, "南京邮电大学集成电路"), "南京邮电大学")

    def test_changed_source_requires_recheck(self):
        with self.assertRaisesRegex(ValueError, "须重新核对"):
            studio.outcome_school(2027, 6, "其他大学控制工程")

    def test_published_cohorts_remain_separate_from_application_year(self):
        periods = json.loads((ROOT / "data/outcomes.json").read_text(encoding="utf-8"))["periods"]
        by_id = {period["id"]: period for period in periods}
        self.assertEqual(by_id["cohort-2026"]["graduationYear"], 2026)
        self.assertEqual(by_id["cohort-2026"]["applicationYear"], 2025)
        self.assertEqual(by_id["cohort-2027"]["graduationYear"], 2027)


if __name__ == "__main__":
    unittest.main()
