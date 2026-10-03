# AIRA Operations and Runbook

This document outlines standard operating procedures for managing, deploying, and maintaining AIRA in production.

---

## 1. Rebuilding the Corpus Index

Whenever clinical guidelines in `backend/data/curated/` or rule tables in `backend/data/curated/rules/` are added or updated, the search index and manifests must be rebuilt and validated.

### Step 1: Validate Corpus Structure
Verify that all guideline markdown files adhere to schema, page numbers, and condition identifiers:
```bash
cd backend
python scripts/validate_corpus.py
```

### Step 2: Build Embeddings and BM25 Index
Rebuild the dense embeddings and sparse BM25 index. Make sure `GEMINI_API_KEY` is set in your environment:
```bash
python scripts/build_index.py
```
This generates:
- `backend/data/index/corpus_chunks.json` (chunk metadata and text)
- `backend/data/index/embeddings.npy` (3072-dimensional vector embeddings)
- `backend/data/index/bm25_params.json` (sparse keyword index parameters)
- `backend/data/index/manifest.json` (SHA-256 integrity checksums)

### Step 3: Verify Index Integrity
Validate that chunk hashes match the generated manifest:
```bash
python scripts/build_index.py --verify
```

### Step 4: Run Evaluation Harness
Run the offline safety and triage regression test suite:
```bash
python -m eval.run --suite all
```

---

## 2. Rotating the Gemini API Key

AIRA uses Google Gemini models for live answer generation and embeddings. API keys must be rotated without exposing secrets in source control.

### On Render Dashboard:
1. Navigate to the **aira-backend** web service on the Render Dashboard.
2. Open the **Environment** tab.
3. Locate `GEMINI_API_KEY`.
4. Replace the existing value with the newly generated API key.
5. Click **Save Changes**. Render will automatically trigger a zero-downtime rolling restart.

### Verification:
Check `/api/ready` on the live backend service:
```bash
curl -i https://aira-backend.onrender.com/api/ready
```
Expected response: HTTP 200 with `{"status": "ready"}`.

---

## 3. Switching to Extractive Fallback Mode (`LLM_ENABLED=false`)

In the event of an upstream Gemini API outage, rate limiting, or for air-gapped / cost-constrained environments, AIRA can operate in 100% deterministic extractive mode.

In extractive mode:
- Safety gates and triage scoring run deterministically as normal.
- Retrieved ICMR guideline passages are copied verbatim into structured sections.
- Zero external LLM calls are made.

### How to Activate:
1. In `render.yaml` or on the Render Dashboard under **Environment**:
   - Set `LLM_ENABLED=false`
2. Save changes to deploy.

### Local Testing:
```bash
cd backend
LLM_ENABLED=false python -m uvicorn app.main:create_app --factory --port 8000
```

---

## 4. Rolling Back a Deployment

If a production deployment exhibits regressions or operational errors, roll back immediately using Render's deployment history.

### On Render:
1. Open the **aira-backend** (or **aira-frontend**) service in the Render Dashboard.
2. Navigate to the **Events** or **Deploys** tab.
3. Locate the last known healthy deployment commit/build.
4. Click the three dots menu next to that deployment and select **Rollback to this deploy**.
5. Verify liveness and readiness probes:
   - `GET /api/health` -> HTTP 200 `{"status": "ok"}`
   - `GET /api/ready` -> HTTP 200 `{"status": "ready"}`

### In Git:
To revert a breaking commit on the `main` branch:
```bash
git revert <commit-hash>
git push origin main
```
Render will automatically detect the new commit and deploy the clean build.
