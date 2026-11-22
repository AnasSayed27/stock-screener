# Additional Repository Files Documentation

This document records the additional documentation, testing, analysis, and discovery data files tracked in this repository:

---

### 1. Root Documentation & Test Files
- **`UPDATE_HISTORY.md`**: Complete decision, architecture change, and empirical evaluation audit log across project updates (including UPD-000 domain fixes and UPD-001 strategy consolidation).
- **`test_api.py`**: Manual testing suite verifying backend API endpoints and response payloads.
- **`test_thesis.py`**: Manual testing script for generating and validating AI investment thesis pipelines.

---

### 2. Strategy & Architecture Documentation (`Misc/`)
- **`Misc/how_it_works.md`**: Architectural breakdown of the StockLens screener, analysis engine, and synthesis pipeline.
- **`Misc/implementation_plan.md`**: Step-by-step implementation milestones and system designs.
- **`Misc/investment_strategy.md`**: Quantitative and fundamental criteria rules, valuation gates, and multi-lens investment strategy.
- **`Misc/walkthrough.md`**: End-to-end user walkthrough of screening, discovery, and report generation workflows.

---

### 3. Historical Analysis, Discovery Runs & Usage Data (`data/`)
*(Note: Ephemeral stock caches `data/cache/` and uploaded temporary PDFs `data/ai_temp/` remain excluded via `.gitignore` to prevent repository bloat).*

- **`data/api_usage.json`**: Cumulative usage tracking for external API services (Gemini, Tavily, etc.).
- **`data/discoveries/`**: Saved autonomous multi-phase DiscoveryLens runs (JSON format) across multiple strategy executions.
- **`data/syntheses/`**: Saved Master Synthesis portfolio outputs and ranking runs.
- **`data/ai_reports/`**: Saved structured AI fundamental analysis reports (business overview, governance, and risks) for analyzed tickers (e.g., BPCL, CHENNPETRO, JAYNECOIND).
