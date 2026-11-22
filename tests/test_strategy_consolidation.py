# -*- coding: utf-8 -*-
"""
TDD Verification Suite for DiscoveryLens Strategy Consolidation (11 -> 6 Core + 1 Custom).

Validates:
1. Active strategy registry: exactly 6 core strategies + 1 separated custom ('freeform') strategy.
2. Retired/merged legacy IDs are removed from active registry.
3. Core prompt integrity is preserved on untouched strategies and cleanly unified
   (without forced sub-strategy output quotas) on the 2 merged strategies, aligned with
   NotebookLM safety principles (e.g., CFO/PAT cash conversion, promoter pledge guardrails,
   tariff/escrow checks, liquidity gate).
4. Evaluator coverage checklists in discovery_phases.py match every active strategy ID
   and enforce multi-angle Phase 1 breadth without retired checklists.
5. Master Synthesis minimum threshold lowered from 7 -> 5 in backend and frontend.
6. Frontend separates Custom Research (freeform) from the 6-strategy core selector
   and removes Scuttlebutt experimental badges.
"""

import os
import re
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DISCOVERY_JS = ROOT_DIR / "frontend" / "js" / "discovery.js"
BACKEND_SYNTHESIS_PY = BACKEND_DIR / "synthesis.py"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from discovery_prompts import DISCOVERY_STRATEGIES, SYNTHESIS_SYSTEM_PROMPT
from discovery_phases import STRATEGY_COVERAGE_CHECKLISTS


EXPECTED_CORE_IDS = [
    "policy_import_substitution",
    "supply_chain",
    "hidden_monopoly",
    "forensic_anomalies",
    "capital_cycle",
    "corporate_restructuring",
]

EXPECTED_CUSTOM_IDS = ["freeform"]

RETIRED_IDS = [
    "scuttlebutt",
    "government_policy",
    "import_substitution",
    "hidden_earnings",
    "anomaly_discovery",
    "smart_money",
]


class TestStrategyConsolidation(unittest.TestCase):
    """Expected-to-fail TDD tests prior to implementing the 11 -> 6 consolidation."""

    def setUp(self):
        self.strategies_by_id = {s["id"]: s for s in DISCOVERY_STRATEGIES}

    # --- 1. Registry Schema & Counts ---

    def test_exact_strategy_count_and_categories(self):
        """Registry must contain exactly 6 core strategies and 1 custom ('freeform') strategy."""
        self.assertEqual(
            len(DISCOVERY_STRATEGIES),
            7,
            f"Expected 7 total entries (6 core + 1 custom), found {len(DISCOVERY_STRATEGIES)}: "
            f"{list(self.strategies_by_id.keys())}",
        )

        for strat in DISCOVERY_STRATEGIES:
            self.assertIn(
                "category",
                strat,
                f"Strategy '{strat['id']}' is missing required 'category' field ('core' or 'custom').",
            )
            self.assertIn(strat["category"], {"core", "custom"})

        core_ids = [s["id"] for s in DISCOVERY_STRATEGIES if s.get("category") == "core"]
        custom_ids = [s["id"] for s in DISCOVERY_STRATEGIES if s.get("category") == "custom"]

        self.assertEqual(set(core_ids), set(EXPECTED_CORE_IDS))
        self.assertEqual(custom_ids, EXPECTED_CUSTOM_IDS)

    def test_retired_and_merged_legacy_ids_removed(self):
        """Retired Scuttlebutt and pre-merge legacy IDs must not appear as active strategies."""
        active_ids = set(self.strategies_by_id.keys())
        for legacy_id in RETIRED_IDS:
            self.assertNotIn(
                legacy_id,
                active_ids,
                f"Legacy/retired strategy '{legacy_id}' is still present in DISCOVERY_STRATEGIES.",
            )

    def test_freeform_remains_required_custom_tool(self):
        """Free-form must remain available as a required custom research strategy."""
        self.assertIn("freeform", self.strategies_by_id.keys())
        ff = self.strategies_by_id["freeform"]
        self.assertEqual(ff.get("category"), "custom")
        self.assertTrue(ff.get("required"))

    # --- 2. Prompt Integrity & Clean Unification (No Forced Sub-Strategy Quotas) ---

    def test_untouched_core_prompts_preserve_domain_gates(self):
        """The 4 untouched strategies must preserve their core logic and Category A gates."""
        active_ids = set(self.strategies_by_id.keys())
        for kept_id in ["hidden_monopoly", "supply_chain", "capital_cycle", "corporate_restructuring"]:
            self.assertIn(kept_id, active_ids)

        cap_prompt = self.strategies_by_id["capital_cycle"]["prompt_template"]
        self.assertIn("MANDATORY DOMAIN GATE — IMPORT DUMPING & VERTICAL INSULATION", cap_prompt)

        restruct_prompt = self.strategies_by_id["corporate_restructuring"]["prompt_template"]
        self.assertIn("MANDATORY DOMAIN GATE — STATUTORY TIMELINE & CATALYST AUTHORITY", restruct_prompt)

        mono_prompt = self.strategies_by_id["hidden_monopoly"]["prompt_template"]
        self.assertIn("TOLL ROAD", mono_prompt.upper())
        self.assertIn("HIDDEN BRAND LOYALTY", mono_prompt.upper())

        sc_prompt = self.strategies_by_id["supply_chain"]["prompt_template"]
        self.assertIn("CHOKEPOINT", sc_prompt.upper())

    def test_policy_import_substitution_unified_prompt_accuracy(self):
        """Merged policy/import prompt preserves both cores cleanly without forced sub-strategy quotas."""
        self.assertIn("policy_import_substitution", self.strategies_by_id.keys())
        prompt = self.strategies_by_id["policy_import_substitution"]["prompt_template"]
        lower = prompt.lower()

        # Core elements preserved from government_policy + import_substitution
        self.assertIn("escrow", lower)
        self.assertIn("import", lower)
        self.assertIn("tariff", lower)
        self.assertIn("pli", lower)
        self.assertIn("certification", lower)
        self.assertIn("wrong market assumption", lower)
        self.assertIn("leading indicators", lower)

        # Must NOT contain robotic forced sub-strategy output quotas
        self.assertNotIn("sub-strategy a", lower)
        self.assertNotIn("sub-strategy b", lower)
        self.assertNotIn("at least 1 candidate from each sub-strategy", lower)

    def test_forensic_anomalies_unified_prompt_accuracy_and_notebooklm_gates(self):
        """Merged forensic prompt preserves accounting/anomaly/insider cores + NotebookLM safety checks."""
        self.assertIn("forensic_anomalies", self.strategies_by_id.keys())
        prompt = self.strategies_by_id["forensic_anomalies"]["prompt_template"]
        lower = prompt.lower()

        # Core elements preserved from hidden_earnings + anomaly_discovery + filtered smart_money
        self.assertIn("capex", lower)
        self.assertIn("depreciation", lower)
        self.assertIn("customer advances", lower)
        self.assertIn("promoter", lower)
        self.assertIn("pledge", lower)
        self.assertIn("cash flow", lower)
        self.assertIn("wrong market assumption", lower)

        # NotebookLM-verified safety alignment: cash conversion + high pledge warning
        self.assertTrue(
            "0.8" in lower or "cfo" in lower,
            "Forensic prompt must reference CFO/cash-flow verification to block fake-growth/penny traps.",
        )
        self.assertIn(
            "20%",
            lower,
            "Forensic prompt must include the NotebookLM >20% promoter pledge disqualifier.",
        )

        # Global liquidity gate must remain intact in synthesis prompt
        self.assertIn("300 crore", SYNTHESIS_SYSTEM_PROMPT.lower())

        # Must NOT contain forced sub-strategy output quotas
        self.assertNotIn("sub-strategy a", lower)
        self.assertNotIn("sub-strategy b", lower)

    # --- 3. Evaluator Coverage Checklists Alignment ---

    def test_evaluator_checklists_match_active_strategies_exactly(self):
        """Every active strategy (6 core + freeform) must have a checklist, and retired ones removed."""
        expected_all = set(EXPECTED_CORE_IDS + EXPECTED_CUSTOM_IDS)
        actual_keys = set(STRATEGY_COVERAGE_CHECKLISTS.keys())
        self.assertEqual(
            actual_keys,
            expected_all,
            f"Checklist keys mismatch.\nExpected: {sorted(expected_all)}\nActual:   {sorted(actual_keys)}",
        )

        # Merged checklists must audit breadth across the unified angles during Phase 1
        pol_chk = STRATEGY_COVERAGE_CHECKLISTS["policy_import_substitution"].lower()
        self.assertIn("breadth gate", pol_chk)
        self.assertIn("escrow", pol_chk)
        self.assertIn("import", pol_chk)
        self.assertIn("tariff", pol_chk)

        for_chk = STRATEGY_COVERAGE_CHECKLISTS["forensic_anomalies"].lower()
        self.assertIn("breadth gate", for_chk)
        self.assertIn("cfo", for_chk)
        self.assertIn("anomaly", for_chk)
        self.assertIn("promoter", for_chk)
        self.assertIn("pledge", for_chk)

    # --- 4. Master Synthesis Minimum Lowered (7 -> 5) ---

    def test_backend_synthesis_minimum_is_five(self):
        """backend/synthesis.py must enforce minimum 5 discoveries (not 7)."""
        src = BACKEND_SYNTHESIS_PY.read_text(encoding="utf-8")
        self.assertIn(
            "len(discoveries) < 5",
            src,
            "backend/synthesis.py should enforce `len(discoveries) < 5`.",
        )
        self.assertNotIn(
            "len(discoveries) < 7",
            src,
            "backend/synthesis.py still contains hardcoded `len(discoveries) < 7`.",
        )

    def test_frontend_synthesis_minimum_and_custom_research_separation(self):
        """frontend/js/discovery.js must enforce Min 5, default to valid core ID, and separate Custom Research."""
        js = FRONTEND_DISCOVERY_JS.read_text(encoding="utf-8")

        # Min 5 threshold in UI copy & logic
        self.assertNotIn("Min 7 required", js)
        self.assertNotIn("at least 7 strategy", js)
        self.assertNotIn("selectedCount >= 7", js)
        self.assertNotIn("selectedIds.length < 7", js)
        self.assertIn("Min 5 required", js)
        self.assertIn("selectedCount >= 5", js)
        self.assertIn("selectedIds.length < 5", js)

        # Default selected strategy must not point to removed 'government_policy'
        self.assertNotIn("_selectedStrategyId = 'government_policy'", js)

        # Scuttlebutt badge removed & Custom Research section introduced
        self.assertNotIn("s.id === 'scuttlebutt'", js)
        self.assertIn("custom-research", js.lower())


if __name__ == "__main__":
    unittest.main()
