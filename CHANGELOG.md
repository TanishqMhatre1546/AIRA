# Changelog

All notable changes to the AIRA project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-03

### Added
- Multi-stage production `backend/Dockerfile` with non-root user execution, `urllib` healthcheck, and sub-350 MB memory ceiling.
- `render.yaml` deployment blueprint configuring backend Docker web service and frontend static site with strict security headers.
- Comprehensive GitHub Actions CI pipeline in `.github/workflows/ci.yml` covering backend quality, corpus integrity, safety evaluation, frontend build, repo hygiene, and Docker memory benchmarks.
- Operations runbook in `docs/OPERATIONS.md` detailing index rebuilds, key rotation, extractive fallback, and rollbacks.
- Full documentation suite: `docs/ARCHITECTURE.md`, `docs/SAFETY.md`, `docs/CLINICAL_REVIEW.md`, `docs/DATA_SOURCES.md`, `docs/BIAS_TESTING.md`, `docs/EVALUATION.md`, and `docs/DEMO_SCRIPT.md`.

### Verified
- Zero failing test cases across all 9 evaluation suites (904/904 cases passing, 100% emergency recall, 0 bias violations).
- 281/281 passing backend unit tests.
- 15/15 passing frontend component and hook tests.

---

## [0.6.0] - 2026-10-03

### Added
- Accessible, focused clinical tool frontend in `frontend/` using React 18, Vite, and Font Awesome icons.
- Strict design token system (`src/styles/tokens.css`) enforcing 9 WCAG AA compliant colors, 4px border radii, and zero animations/gradients.
- `useTriage` state management hook with 4-second cold-start detection and request cancellation via `AbortController`.
- Static informational pages for `How It Works`, `Sources`, `Privacy Policy`, and `Terms of Service`.
- Custom design linter (`frontend/scripts/design_lint.mjs`) validating WCAG AA contrast ratios and design constraints.

---

## [0.5.0] - 2026-10-03

### Added
- Offline evaluation harness (`backend/eval/run.py`) executing 9 automated safety suites.
- Matrix bias testing harness validating demographic invariance across gender, name, community, and occupation preambles.
- Strict CI thresholds in `eval/thresholds.yaml` requiring 100% emergency recall and zero bias violations.
- Modifier audit and calibration scripts verifying clinical risk escalations against ICMR citations.

---

## [0.4.0] - 2026-10-03

### Added
- LangGraph state machine orchestrating input normalization, safety gating, urgency scoring, hybrid retrieval, answer generation, and output formatting.
- Deterministic output validators scanning for ungrounded claims, prohibited drug dosages, and unauthorized diagnoses.
- Automatic extractive fallback circuit breaker delivering verbatim guideline passages when LLM is disabled or ungrounded.

---

## [0.3.0] - 2026-10-03

### Added
- Hybrid retrieval engine combining sparse BM25 keyword matching with dense 3072-dimensional vector embeddings (`gemini-embedding-001`).
- Startup manifest validation verifying chunk counts, SHA-256 hashes, and index integrity.
- Fast local embedding cache (`.embeddings_cache.json`) for deterministic index rebuilds.

---

## [0.2.0] - 2026-10-03

### Added
- Deterministic Safety Gate (`app/core/safety_gate.py`) intercepting emergency red flags, mental health crises, pediatric queries, and dosage requests before model invocation.
- Rule engine (`app/core/rule_engine.py`) and urgency scorer (`app/core/scorer.py`) evaluating duration thresholds and clinical status modifiers.
- Drug lexicon and negation phrase parser preventing false-positive triggers on negated symptoms.

---

## [0.1.0] - 2026-10-02

### Added
- Initial project scaffolding with FastAPI, Pydantic v2, and Python 3.11+.
- Curated clinical guideline corpus covering 15 adult outpatient conditions derived from ICMR Standard Treatment Workflows.
- Extracted guideline chunks, metadata schema, and provenance mappings.
