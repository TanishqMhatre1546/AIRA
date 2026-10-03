"""Comprehensive test suite for the hybrid retrieval layer (BM25, dense vectors, RRF, filters)."""

import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from app.config import Settings
from app.core.retriever import (
    RRF_K,
    Retriever,
    bm25_tokenize,
    is_reference_query,
)
from app.data.models import GuidelineChunk


def create_sample_chunk(
    chunk_id: str,
    condition_id: str = "dengue_fever",
    section_type: str = "danger_signs",
    label: str = "Danger Signs",
    text: str = "Sample chunk text for testing.",
) -> GuidelineChunk:
    """Helper to create a valid GuidelineChunk model."""
    return GuidelineChunk(
        chunk_id=chunk_id,
        condition_id=condition_id,
        condition=condition_id.replace("_", " ").title(),
        section_type=section_type,
        label=label,
        text=text,
        item_ids=[chunk_id[:12]],
        source_title="Standard Guidelines",
        source_publisher="MOHFW",
        source_year="2024",
        source_url="https://example.gov/guide",
        page=1,
    )


class MockDeterministicEmbedder:
    """Mock embedder returning deterministic vectors for test queries."""

    def __init__(self, vectors: dict[str, list[float]] | None = None, default_dim: int = 4) -> None:
        self.vectors = vectors or {}
        self.default_dim = default_dim

    def embed_query(self, query: str) -> list[float]:
        if query in self.vectors:
            return self.vectors[query]
        # Return simple orthogonal vector
        vec = [1.0] + [0.0] * (self.default_dim - 1)
        return vec


class MockFailingEmbedder:
    """Embedder that always raises an exception."""

    def embed_query(self, query: str) -> list[float]:
        raise RuntimeError("External Embeddings API service unavailable")


class MockTimeoutEmbedder:
    """Embedder that simulates a long hanging network request."""

    def embed_query(self, query: str) -> list[float]:
        time.sleep(2.0)
        return [1.0, 0.0, 0.0, 0.0]


# ---------------------------------------------------------------------------
# 1. BM25 Tokenization and Reference Trigger Unit Tests
# ---------------------------------------------------------------------------
def test_bm25_tokenization_removes_stopwords_and_punctuation() -> None:
    """BM25 tokenizer must remove stopwords and pipe tokens without stemming."""
    text = "The patient has a severe fever and chest pain | coughing heavily"
    tokens = bm25_tokenize(text)

    assert "the" not in tokens
    assert "a" not in tokens
    assert "and" not in tokens
    assert "|" not in tokens
    assert "fever" in tokens
    assert "chest" in tokens
    assert "pain" in tokens
    assert "coughing" in tokens


def test_reference_query_detection() -> None:
    """is_reference_query must return True only when reference keywords are present."""
    assert is_reference_query("What are the screening guidelines for diabetes?") is True
    assert is_reference_query("How to prevent dengue fever at home?") is True
    assert is_reference_query("High risk groups for respiratory infection") is True
    assert is_reference_query("I have high fever and vomiting") is False


# ---------------------------------------------------------------------------
# 2. Startup Integrity and Validation Tests
# ---------------------------------------------------------------------------
def test_retriever_startup_integrity_validation() -> None:
    """Retriever must fail fast if matrix rows or manifest dimensions mismatch chunks."""
    chunks = [
        create_sample_chunk("c1", text="chunk one"),
        create_sample_chunk("c2", text="chunk two"),
    ]
    valid_matrix = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)

    # 1. Matching matrix -> success
    retriever = Retriever(chunks=chunks, matrix=valid_matrix)
    assert len(retriever.chunks) == 2

    # 2. Matrix row mismatch -> ValueError
    invalid_row_matrix = np.array([[1.0, 0.0]], dtype=np.float32)
    with pytest.raises(ValueError, match="Embedding matrix rows"):
        Retriever(chunks=chunks, matrix=invalid_row_matrix)

    # 3. Manifest chunk_count mismatch -> ValueError
    with pytest.raises(ValueError, match="Manifest chunk_count"):
        Retriever(
            chunks=chunks,
            matrix=valid_matrix,
            manifest={"chunk_count": 5, "dimension": 2},
        )

    # 4. Manifest dimension mismatch -> ValueError
    with pytest.raises(ValueError, match="Manifest dimension"):
        Retriever(
            chunks=chunks,
            matrix=valid_matrix,
            manifest={"chunk_count": 2, "dimension": 128},
        )


# ---------------------------------------------------------------------------
# 3. Reciprocal Rank Fusion (RRF) and Ranking Tests
# ---------------------------------------------------------------------------
def test_rrf_scoring_calculation() -> None:
    """RRF score must equal 1/(60 + r_bm25) + 1/(60 + r_dense)."""
    chunks = [
        create_sample_chunk("c1", text="dengue fever with high fever and rash"),
        create_sample_chunk("c2", text="watery diarrhea and dehydration in cholera"),
    ]
    # c1 is aligned with [1, 0], c2 with [0, 1]
    matrix = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    embedder = MockDeterministicEmbedder(vectors={"dengue": [1.0, 0.0]}, default_dim=2)

    retriever = Retriever(chunks=chunks, matrix=matrix, embedder=embedder)
    res = retriever.search("dengue", top_k=2)

    assert res.mode == "hybrid"
    assert len(res.chunks) == 2

    top_result = res.chunks[0]
    assert top_result.chunk.chunk_id == "c1"
    assert top_result.bm25_rank == 1
    assert top_result.dense_rank == 1

    expected_rrf = (1.0 / (RRF_K + 1)) + (1.0 / (RRF_K + 1))
    assert pytest.approx(top_result.fused_score, rel=1e-5) == expected_rrf


# ---------------------------------------------------------------------------
# 4. Section and Reference Filtering Tests
# ---------------------------------------------------------------------------
def test_reference_section_filtering() -> None:
    """Reference chunks must be filtered out unless query explicitly asks for reference."""
    chunks = [
        create_sample_chunk("c1", section_type="danger_signs", text="danger signs of fever"),
        create_sample_chunk(
            "c2", section_type="reference", text="prevention and screening note for fever"
        ),
    ]
    matrix = np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32)
    embedder = MockDeterministicEmbedder(default_dim=2)

    retriever = Retriever(chunks=chunks, matrix=matrix, embedder=embedder)

    # Standard query -> drops reference chunk c2
    res1 = retriever.search("fever symptoms", top_k=5)
    chunk_ids1 = [sc.chunk.chunk_id for sc in res1.chunks]
    assert "c1" in chunk_ids1
    assert "c2" not in chunk_ids1

    # Prevention query -> includes reference chunk c2
    res2 = retriever.search("how to prevent fever", top_k=5)
    chunk_ids2 = [sc.chunk.chunk_id for sc in res2.chunks]
    assert "c2" in chunk_ids2


# ---------------------------------------------------------------------------
# 5. Condition Filtering and Fallback Tests
# ---------------------------------------------------------------------------
def test_condition_filter_and_global_fallback() -> None:
    """Condition filter restricts candidates, but falls back to global if < 2 chunks match."""
    chunks = [
        create_sample_chunk("c1", condition_id="dengue_fever", text="dengue symptom one"),
        create_sample_chunk("c2", condition_id="dengue_fever", text="dengue symptom two"),
        create_sample_chunk("c3", condition_id="acute_diarrhea", text="diarrhea symptom one"),
        create_sample_chunk("c4", condition_id="hypertension", text="hypertension symptom one"),
    ]
    matrix = np.eye(4, dtype=np.float32)
    embedder = MockDeterministicEmbedder(default_dim=4)

    retriever = Retriever(chunks=chunks, matrix=matrix, embedder=embedder)

    # 1. 2 matching dengue chunks -> filter active
    res_dengue = retriever.search("fever", conditions=["dengue_fever"], top_k=5)
    assert res_dengue.total_candidates == 2
    for sc in res_dengue.chunks:
        assert sc.chunk.condition_id == "dengue_fever"

    # 2. Only 1 hypertension chunk (< 2) -> fallback to global search (all 4 chunks)
    res_ht = retriever.search("fever", conditions=["hypertension"], top_k=5)
    assert res_ht.total_candidates == 4


# ---------------------------------------------------------------------------
# 6. Graceful Degradation on Embedder Error and Timeout Tests
# ---------------------------------------------------------------------------
def test_graceful_degradation_on_embedder_exception(caplog: pytest.LogCaptureFixture) -> None:
    """Retriever must degrade to bm25_only and log warning without leaking query text."""
    chunks = [
        create_sample_chunk("c1", text="high fever with chills"),
        create_sample_chunk("c2", text="stomach pain and vomiting"),
    ]
    matrix = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    retriever = Retriever(chunks=chunks, matrix=matrix, embedder=MockFailingEmbedder())

    private_query = "super confidential symptom query"
    with caplog.at_level(logging.WARNING):
        res = retriever.search(private_query, top_k=2)

    assert res.mode == "bm25_only"
    assert res.best_cosine == 0.0
    # Ensure query string was not logged
    for record in caplog.records:
        assert private_query not in record.message
        assert "degrading to bm25_only mode" in record.message


def test_graceful_degradation_on_timeout() -> None:
    """Retriever must timeout and degrade to bm25_only when embedder exceeds timeout."""
    chunks = [
        create_sample_chunk("c1", text="high fever with chills"),
        create_sample_chunk("c2", text="stomach pain and vomiting"),
    ]
    matrix = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    fast_settings = Settings(retrieval_timeout_seconds=0.1)

    retriever = Retriever(
        chunks=chunks,
        matrix=matrix,
        embedder=MockTimeoutEmbedder(),
        settings=fast_settings,
    )

    res = retriever.search("fever", top_k=2)
    assert res.mode == "bm25_only"


# ---------------------------------------------------------------------------
# 7. Relevance Floor Tests
# ---------------------------------------------------------------------------
def test_relevance_floor_drops_unrelated_queries() -> None:
    """When best_cosine is below retrieval_min_cosine and no condition detected, return empty."""
    chunks = [
        create_sample_chunk("c1", text="dengue fever management guidelines"),
    ]
    matrix = np.array([[1.0, 0.0]], dtype=np.float32)
    # Query vector orthogonal to chunk matrix -> cosine = 0.0
    embedder = MockDeterministicEmbedder(vectors={"random text": [0.0, 1.0]}, default_dim=2)

    settings_floor = Settings(retrieval_min_cosine=0.65)
    retriever = Retriever(chunks=chunks, matrix=matrix, embedder=embedder, settings=settings_floor)

    # No condition detected + low cosine -> empty results
    res = retriever.search("random text", conditions=None)
    assert res.chunks == []
    assert res.best_cosine == 0.0

    # With detected condition -> condition chunk is returned even with low cosine
    res_cond = retriever.search("random text", conditions=["dengue_fever"])
    assert len(res_cond.chunks) == 1


# ---------------------------------------------------------------------------
# 8. Disk Loading and Hash Mismatch Tests
# ---------------------------------------------------------------------------
def test_retriever_from_disk(tmp_path: Any) -> None:
    """Retriever.from_disk must successfully load committed files and verify corpus hash."""
    from scripts.build_index import build_index

    # Build index in temp directory
    data_dir = tmp_path / "data"
    curated_dir = data_dir / "curated"
    curated_dir.mkdir(parents=True)

    # Copy manifest from real backend curated
    real_curated = Path(__file__).resolve().parent.parent / "data" / "curated"
    import shutil

    for json_file in real_curated.glob("*.json"):
        shutil.copy(json_file, curated_dir / json_file.name)
    shutil.copy(real_curated / "provenance.csv", curated_dir / "provenance.csv")

    build_index(data_dir=data_dir, include_unverified=True, mock_mode=True)

    # Load from disk
    retriever = Retriever.from_disk(
        index_dir=data_dir / "index",
        curated_dir=data_dir / "curated",
        embedder=MockDeterministicEmbedder(default_dim=768),
    )
    assert len(retriever.chunks) > 0
    assert retriever.matrix.shape[0] == len(retriever.chunks)

    # Corrupt curated manifest hash and verify from_disk fails
    curated_manifest_path = curated_dir / "manifest.json"
    import json

    with open(curated_manifest_path, encoding="utf-8") as fh_in:
        cur_mf = json.load(fh_in)
    cur_mf["overall_corpus_hash"] = "corrupted_hash_12345"
    with open(curated_manifest_path, "w", encoding="utf-8") as fh_out:
        json.dump(cur_mf, fh_out)

    with pytest.raises(ValueError, match="Index corpus hash"):
        Retriever.from_disk(
            index_dir=data_dir / "index",
            curated_dir=data_dir / "curated",
        )
