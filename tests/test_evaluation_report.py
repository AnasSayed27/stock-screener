"""
Automated Verification Suite for Prediction Performance Evaluation Report.
Verifies completeness, coverage of all 29 target stocks, 10 qualitative lenses,
5-pillar methodology, 2x2 matrix quadrants, benchmark alpha calculations, and StockLens data integration.
"""

import os
import unittest

REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "reports", "prediction_performance_evaluation.md")

ALL_29_STOCKS = [
    ("AZAD", "Azad Engineering"),
    ("PTCIL", "PTC Industries"),
    ("GEESHIP", "Great Eastern Shipping"),
    ("KIRLPNU", "Kirloskar Pneumatic"),
    ("KPRMILL", "K.P.R. Mill"),
    ("TIMETECHNO", "Time Technoplast"),
    ("GUJGASLTD", "Gujarat Gas"),
    ("543678", "Ambo Agritec"),
    ("WABAG", "VA Tech Wabag"),
    ("DYNAMATECH", "Dynamatic Technologies"),
    ("515008", "Modern Insulators"),
    ("511509", "Vivo Bio Tech"),
    ("AMBIKCO", "Ambika Cotton"),
    ("GENUSPOWER", "Genus Power"),
    ("GFL", "Gujarat Fluorochemicals"),
    ("HPL", "HPL Electric"),
    ("HSCL", "Himadri Speciality"),
    ("JKPAPER", "JK Paper"),
    ("KALYANIINV", "Kalyani Investment"),
    ("KAYNES", "Kaynes Technology"),
    ("NAVINFLUOR", "Navin Fluorine"),
    ("NEOGEN", "Neogen Chemicals"),
    ("PEL", "Piramal Enterprises"),
    ("SEAMECLTD", "Seamec"),
    ("SESHAPAPER", "Seshasayee Paper"),
    ("TIMKEN", "Timken India"),
    ("TITAGARH", "Titagarh Rail"),
    ("VEDL", "Vedanta"),
    ("WAAREEENER", "Waaree Energies"),
]

QUALITATIVE_LENSES = [
    "Free-form Discovery",
    "Anomaly Discovery",
    "Hidden Monopoly",
    "Import Substitution",
    "Capital Cycle",
    "Hidden Earnings",
    "Corporate Restructuring",
    "Smart Money",
    "Government Policy",
    "Supply Chain Dependency",
]

QUADRANTS = [
    "High Signal Winner",
    "Noise Dislocation",
    "False Positive",
    "Structural Loser",
]

REQUIRED_SECTIONS = [
    "Executive Summary",
    "Evaluation Framework & Methodology",
    "Master Synthesis",
    "Honorable Mentions",
    "Lens-by-Lens Performance & Attribution",
    "Pattern Extraction",
]


class TestEvaluationReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report_abs_path = os.path.abspath(REPORT_PATH)
        assert os.path.exists(cls.report_abs_path), f"Report not found at {cls.report_abs_path}"
        with open(cls.report_abs_path, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_report_file_exists_and_substantial(self):
        """Report must exist and contain substantial analytical content (>20,000 chars, >500 lines)."""
        self.assertTrue(os.path.exists(self.report_abs_path))
        self.assertGreater(len(self.content), 20000, "Report content is too short.")
        lines = self.content.splitlines()
        self.assertGreater(len(lines), 500, f"Report should have at least 500 lines, found {len(lines)}")

    def test_all_required_sections_present(self):
        """All 6 structural sections must be clearly identifiable."""
        for section in REQUIRED_SECTIONS:
            self.assertIn(section.lower(), self.content.lower(), f"Missing required section: {section}")

    def test_all_29_target_stocks_covered(self):
        """All 29 target corporate entities / tickers must be explicitly evaluated."""
        missing = []
        for ticker, name in ALL_29_STOCKS:
            if ticker not in self.content and name not in self.content:
                missing.append(f"{ticker} ({name})")
        self.assertEqual(missing, [], f"The following target stocks are missing from the report: {missing}")

    def test_all_10_qualitative_lenses_evaluated(self):
        """All 10 analytical lenses must be reviewed in the lens scorecard with audited mathematical consistency."""
        missing = []
        for lens in QUALITATIVE_LENSES:
            if lens.lower() not in self.content.lower():
                missing.append(lens)
        self.assertEqual(missing, [], f"The following qualitative lenses are missing from the report: {missing}")

        # Analytical Lens Scorecard checks
        # Import substitution: 85.7% (6/7) positive alpha, 100% (7/7) thesis validated
        self.assertIn("**85.7% (6/7)** | **100% (7/7)**", self.content, "Import substitution thesis validation must be 100% (7/7)")
        # Supply chain mapper: 50.0% (2/4) positive alpha
        self.assertIn("**50.0% (2/4)** | **100% (4/4)**", self.content, "Supply chain mapper positive alpha must be 50.0% (2/4)")
        # Government policy: 33.3% (1/3) positive alpha, 100% (3/3) thesis validated
        self.assertIn("**33.3% (1/3)** | **100% (3/3)**", self.content, "Government policy must have 33.3% (1/3) positive alpha and 100% (3/3)")
        # Capital cycle: -9.63% average alpha
        self.assertIn("**-9.63%**", self.content, "Capital cycle average alpha must be -9.63%")
        # Free-form discovery: 33.3% (1/3) positive alpha and 33.3% (1/3) thesis validated
        self.assertIn("**33.3% (1/3)** | **33.3% (1/3)**", self.content, "Free-form discovery hit rates must be 33.3% (1/3)")

    def test_2x2_matrix_quadrants_present(self):
        """All four 2x2 Signal vs Noise quadrants must be defined and populated."""
        for quad in QUADRANTS:
            self.assertIn(quad.lower(), self.content.lower(), f"Missing quadrant: {quad}")

    def test_macro_benchmarks_and_alpha_included(self):
        """Report must compare performance against Nifty 50 and Mid/Small cap benchmarks and maintain arithmetic consistency."""
        self.assertIn("Nifty 50", self.content)
        self.assertTrue("Midcap" in self.content or "Midcap 150" in self.content)
        self.assertTrue("Smallcap" in self.content or "Smallcap 250" in self.content)
        self.assertIn("Alpha", self.content)

        # Executive Dashboard metric checks
        self.assertIn("12 / 29 (41.4%)", self.content, "Positive return stock count must be 12 / 29 (41.4%)")
        self.assertIn("18 / 29 (62.1%)", self.content, "Positive alpha stock count must be 18 / 29 (62.1%)")
        self.assertIn("+1.75% (+6.73% ex-Gujarat Gas)", self.content, "Top 7 average alpha must be +1.75% (+6.73% ex-Gujarat Gas)")
        self.assertIn("+215.5% (+14.4% ex-Ambo Agritec)", self.content, "Honorable mentions alpha must be +215.5% (+14.4% ex-Ambo Agritec)")

        # KIRLPNU baseline and outcome consistency
        self.assertIn("₹667.80", self.content)
        self.assertIn("₹780.95", self.content)
        self.assertIn("+16.95%", self.content)
        self.assertIn("+22.19%", self.content)

    def test_stocklens_integration(self):
        """Report must reference StockLens valuation/financial engine and fundamental metrics."""
        self.assertIn("StockLens", self.content)
        self.assertTrue("Quality Score" in self.content or "quality score" in self.content.lower())
        self.assertTrue("EBITDA" in self.content)
        self.assertTrue("PAT" in self.content or "Net Profit" in self.content)


if __name__ == "__main__":
    unittest.main()
