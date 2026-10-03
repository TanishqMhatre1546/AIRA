# AIRA: Clinical Guidelines Assistant

AIRA is a clinical guideline navigator for adults in India. It provides official Indian government health guideline information for everyday symptoms, determines urgency levels, and outlines what warning signs to monitor.

## Safety Invariants

1. AIRA is not a doctor. It does not provide medical diagnoses, medication dosages, or drug interaction advice.
2. Emergency triage symptoms trigger immediate static helpline guidance without calling generative models.
3. Triage classification and safety boundaries run deterministically in Python before any model invocation.
4. User queries and messages are never persisted to storage or written to log files.
5. All guideline citations are constructed from indexed chunk metadata by code.

## Architecture

- **Backend**: Python 3.11, FastAPI, Pydantic v2, LangGraph, langchain-google-genai, rank-bm25, NumPy.
- **Frontend**: React 18, Vite, plain CSS, Font Awesome.
- **Data**: Curated guideline JSON files and rule tables in `backend/data/curated/`.

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:create_app --factory --reload --port 8000
```

### Tooling Commands

```bash
make lint       # Run ruff checks
make typecheck  # Run mypy validation
make test       # Run pytest test suite
```
