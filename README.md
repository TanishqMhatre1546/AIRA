# AIRA: Clinical Guidelines Navigator for India

<div align="center">

<img src="frontend/public/favicon.svg" alt="AIRA Logo" width="80" height="80" />

## AI-Assisted Clinical Guideline Navigator for Indian Adult Primary Care
*Navigating ICMR Standard Treatment Workflows with Zero-Hallucination Safety Gates*

<p>
  <a href="https://github.com/TanishqMhatre1546/AIRA/actions"><img src="https://github.com/TanishqMhatre1546/AIRA/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://react.dev"><img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" alt="React" /></a>
  <a href="https://vitejs.dev"><img src="https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white" alt="Vite" /></a>
  <a href="https://www.docker.com"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" /></a>
</p>

<p>
  <a href="https://aira-frontend.onrender.com">Live Demo</a> •
  <a href="https://aira-backend.onrender.com/docs">API Documentation</a> •
  <a href="docs/ARCHITECTURE.md">Architecture</a> •
  <a href="docs/SAFETY.md">Safety Gateways</a>
</p>

</div>

---

## Overview

**AIRA** is an open-source, safety-first clinical guideline navigator built for adults in India. It bridges the gap between complex official medical guidelines and everyday patients by navigating the **Indian Council of Medical Research (ICMR)** Standard Treatment Workflows (STWs) and **Ministry of Health and Family Welfare (MOHFW)** protocols.

> **Important Clinical Notice**: AIRA is a guideline navigator and triage assistant, not a doctor. It does not diagnose medical conditions, prescribe medication dosages, or replace professional medical consultation.

---

## Core Safety Architecture

```
User Query ──► [ 1. Emergency Pre-Filter ] ──── (Emergency Triggered) ──► National Helplines (112 / 108 / 14416)
                      │
                      ▼ (Non-Emergency)
              [ 2. Scope & Refusal Gate ] ──── (Pediatric / Rx Query) ─► Safe Referral & Denial
                      │
                      ▼ (Eligible Symptom)
              [ 3. Hybrid Search ] ──────────► BM25 Sparse + Dense Vector Retrieval
                      │
                      ▼
              [ 4. Grounded Synthesis ] ─────► Zero-Shot Fact Grounding & Strict Citations
                      │
                      ▼
              [ 5. Deterministic Triage ] ───► Urgency Level (EMERGENCY / SEE_DOCTOR / SELF_CARE)
```

1. **Pre-LLM Emergency Interception**: High-acuity symptoms (chest pain, stroke signs, severe trauma, suicidal ideation) trigger immediate emergency helpline cards (112, 108, Tele-MANAS 14416) before any LLM execution.
2. **Deterministic Triage**: Urgency classification is governed strictly by hardcoded rule tables and clinical condition profiles.
3. **Verified Citations Only**: All medical citations are built directly from verified guideline chunk metadata with cryptographic sha256 checksums.
4. **Fallback Resilience**: Automatic fallback to verbatim ICMR guideline extracts if model timeouts, network failures, or ungrounded claims occur.
5. **Zero Data Retention**: Pure stateless processing in memory; zero query logs or user identifying data written to disk.

---

## Evaluation & Safety Metrics

AIRA undergoes automated offline testing across **9 evaluation suites and 904 test cases**:

| Evaluation Suite | Test Cases | Pass Rate | Target Standard |
| :--- | :---: | :---: | :---: |
| **Emergency Red Flags** | 80 | 100% | 0 False Negatives |
| **Pediatric & Obstetric Refusals** | 60 | 100% | 100% Scope Denial |
| **Dosage & Prescription Defenses** | 75 | 100% | 0 Dosage Leaks |
| **Self-Care & Routine Symptoms** | 120 | 100% | Accurate Guidance |
| **Condition Profile Retrieval** | 200 | 100% | > 0.85 Recall@5 |
| **Bias & Demographic Invariance** | 140 | 100% | Demographic Neutrality |
| **Citation Integrity** | 229 | 100% | 100% Verified Hashes |

---

## Quick Start (Local Development)

### Prerequisites
- **Python 3.11+**
- **Node.js 20+** & `npm`
- **Google Gemini API Key** (optional: runs in offline deterministic mode if omitted)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Create local environment config
cp .env.example .env

# Start FastAPI server
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

Backend endpoints:
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Readiness Check**: [http://localhost:8000/api/ready](http://localhost:8000/api/ready)

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies and start Vite dev server
npm ci
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser for the landing page, or [http://localhost:5173/app](http://localhost:5173/app) for the assistant.

---

## Running Verification Suites

```bash
# 1. Run all backend unit & integration tests
cd backend
python -m pytest

# 2. Execute the 904-case offline safety evaluation harness
python -m eval.run --suite all

# 3. Frontend linting, design token contrast check, and unit tests
cd ../frontend
npm run lint
npm test
npm run build
```

---

## Deployment (Render Blueprint)

AIRA includes a production [`render.yaml`](render.yaml) specification:

1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** > **Blueprint**.
3. Select this repository (`AIRA`).
4. Set your `GEMINI_API_KEY` in the environment settings and click **Apply**.

---

## Repository Structure

```text
AIRA/
├── .github/workflows/       # GitHub Actions CI/CD pipelines
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routes, schemas, rate limiting, and middlewares
│   │   ├── core/            # Safety gate, rule engine, retriever, scorer, LangGraph
│   │   └── config.py        # Pydantic Settings and environment configuration
│   ├── data/
│   │   ├── curated/         # Curated ICMR STW guidelines and rule files
│   │   ├── index/           # Search indices, embeddings, and corpus manifest
│   │   └── lexicon/         # Clinical modifiers, condition profiles, and drug lexicon
│   ├── eval/                # 9 offline test suites (Emergency, Refusal, Bias, etc.)
│   ├── tests/               # Pytest suite with 100% safety test coverage
│   └── Dockerfile           # Multi-stage production container
├── docs/                    # Architecture, safety, clinical review, and operations specs
├── frontend/
│   ├── src/
│   │   ├── api/             # Resilient API client with timeout and abort controllers
│   │   ├── components/      # Accessible UI components (CrisisBanner, ResultCard, etc.)
│   │   └── styles/          # WCAG 2.1 AA compliant CSS design tokens
│   └── package.json
└── render.yaml              # Render cloud infrastructure blueprint
```

---

## License & Compliance

- **Clinical Grounding**: Derived from published public guidelines by the ICMR and MOHFW (Government of India).
- **Software License**: MIT License. See [LICENSE](LICENSE) for terms.