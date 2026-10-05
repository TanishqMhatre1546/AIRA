"""Hybrid retrieval layer combining BM25 and dense embeddings with Reciprocal Rank Fusion."""

import json
import logging
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from rank_bm25 import BM25Okapi

from app.config import Settings
from app.config import settings as default_settings
from app.core.text import normalize
from app.data.models import GuidelineChunk

logger = logging.getLogger(__name__)

# Stopwords list for BM25 tokenization
STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "in",
        "on",
        "at",
        "is",
        "are",
        "was",
        "were",
        "to",
        "of",
        "for",
        "with",
        "by",
        "and",
        "or",
        "but",
        "so",
        "if",
        "it",
        "this",
        "that",
    }
)

# Reference query triggers that allow reference section chunks
REFERENCE_TRIGGERS: frozenset[str] = frozenset(
    {
        "screening",
        "screen",
        "prevention",
        "prevent",
        "preventing",
        "preventative",
        "preventive",
        "high risk",
        "risk group",
        "risk groups",
        "dehydration assessment",
        "assessment",
        "scope",
    }
)

# RRF smoothing constant
RRF_K: float = 60.0


def bm25_tokenize(text: str) -> list[str]:
    """Tokenize text for BM25 index and query without stemming."""
    norm = normalize(text)
    clean_text = norm.replace("|", " ")
    return [tok for tok in clean_text.split() if tok not in STOPWORDS and len(tok) > 0]


def is_reference_query(query: str) -> bool:
    """Check if query specifically asks for reference or prevention content."""
    query_lower = query.lower()
    return any(trigger in query_lower for trigger in REFERENCE_TRIGGERS)


@dataclass
class ScoredChunk:
    """A guideline chunk enriched with retrieval and fusion ranking metadata."""

    chunk: GuidelineChunk
    fused_score: float
    bm25_rank: int | None = None
    dense_rank: int | None = None
    cosine: float | None = None
    bm25_score: float | None = None


@dataclass
class RetrievalResult:
    """Result container for hybrid search."""

    chunks: list[ScoredChunk]
    mode: Literal["hybrid", "bm25_only"]
    best_cosine: float
    total_candidates: int


class Retriever:
    """Hybrid BM25 and dense retriever with rank fusion and graceful degradation."""

    def __init__(
        self,
        chunks: Sequence[GuidelineChunk],
        matrix: np.ndarray,
        embedder: Any = None,
        settings: Settings | None = None,
        manifest: dict[str, Any] | None = None,
    ) -> None:
        self.chunks = list(chunks)
        self.matrix = matrix.astype(np.float32)
        self.embedder = embedder
        self.settings = settings or default_settings
        self.manifest = manifest or {}

        # Validate startup matrix invariants
        self._verify_startup_integrity()

        # Build BM25 index on chunk corpus
        tokenized_corpus = [bm25_tokenize(c.text) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def _verify_startup_integrity(self) -> None:
        """Verify dimensional and count invariants at initialization."""
        chunk_count = len(self.chunks)
        matrix_rows = self.matrix.shape[0] if self.matrix.ndim == 2 else 0

        if matrix_rows != chunk_count:
            raise ValueError(
                f"Embedding matrix rows ({matrix_rows}) does not match chunk count ({chunk_count})"
            )

        if self.manifest:
            manifest_count = self.manifest.get("chunk_count")
            if manifest_count is not None and manifest_count != chunk_count:
                raise ValueError(
                    f"Manifest chunk_count ({manifest_count}) does not match chunk count "
                    f"({chunk_count})"
                )
            manifest_dim = self.manifest.get("dimension")
            if (
                manifest_dim is not None
                and self.matrix.ndim == 2
                and self.matrix.shape[1] != manifest_dim
            ):
                raise ValueError(
                    f"Manifest dimension ({manifest_dim}) does not match matrix dimension "
                    f"({self.matrix.shape[1]})"
                )

    @classmethod
    def from_disk(
        cls,
        index_dir: Path | None = None,
        curated_dir: Path | None = None,
        embedder: Any = None,
        settings: Settings | None = None,
    ) -> "Retriever":
        """Load and verify retriever from committed disk index files."""
        app_settings = settings or default_settings
        idx_dir = index_dir or (app_settings.data_dir / "index")
        cur_dir = curated_dir or (app_settings.data_dir / "curated")

        manifest_path = idx_dir / "manifest.json"
        chunks_path = idx_dir / "chunks.jsonl"
        matrix_path = idx_dir / "embeddings.npy"

        if not manifest_path.exists():
            raise FileNotFoundError(f"Index manifest not found: {manifest_path}")
        if not chunks_path.exists():
            raise FileNotFoundError(f"Index chunks file not found: {chunks_path}")
        if not matrix_path.exists():
            raise FileNotFoundError(f"Embeddings matrix not found: {matrix_path}")

        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

        chunks: list[GuidelineChunk] = []
        with open(chunks_path, encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    chunks.append(GuidelineChunk.model_validate_json(line_str))

        matrix = np.load(matrix_path)

        # Cross-check corpus hash against curated manifest if present
        curated_manifest_path = cur_dir / "manifest.json"
        if curated_manifest_path.exists():
            with open(curated_manifest_path, encoding="utf-8") as f:
                curated_manifest = json.load(f)
            expected_corpus_hash = curated_manifest.get("overall_corpus_hash")
            index_corpus_hash = manifest.get("corpus_hash")
            if expected_corpus_hash and index_corpus_hash != expected_corpus_hash:
                raise ValueError(
                    f"Index corpus hash ({index_corpus_hash}) does not match curated corpus hash "
                    f"({expected_corpus_hash})"
                )

        # In production, startup must refuse an index built with include_unverified=True
        if (
            app_settings.environment == "production"
            and manifest.get("include_unverified", False)
        ):
            raise ValueError(
                "Production environment cannot start with an index built with "
                "include_unverified=True"
            )

        return cls(
            chunks=chunks,
            matrix=matrix,
            embedder=embedder,
            settings=app_settings,
            manifest=manifest,
        )

    def _embed_query(self, query: str) -> list[float] | None:
        """Embed query vector using configured embedder with strict timeout."""
        if self.embedder is None:
            return None

        timeout_sec = float(self.settings.retrieval_timeout_seconds)

        def call_embedder() -> list[float]:
            if hasattr(self.embedder, "embed_query"):
                return list(self.embedder.embed_query(query))
            if callable(self.embedder):
                return list(self.embedder(query))
            raise TypeError("Embedder object must provide embed_query method or be callable")

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call_embedder)
                return future.result(timeout=timeout_sec)
        except FuturesTimeoutError:
            logger.warning(
                "Dense query embedding timed out after %.1f seconds; degrading to bm25_only mode",
                timeout_sec,
            )
            return None
        except Exception as err:
            logger.warning(
                "Dense query embedding failed with error (%s); degrading to bm25_only mode",
                err.__class__.__name__,
            )
            return None

    def search(
        self,
        query: str,
        conditions: list[str] | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        """Search the guideline index using hybrid BM25 and dense embedding fusion."""
        effective_top_k = top_k if top_k is not None else self.settings.top_k
        if not self.chunks:
            return RetrievalResult(chunks=[], mode="bm25_only", best_cosine=0.0, total_candidates=0)

        # 1. Section filtering: filter out reference chunks unless query asks for reference
        allow_reference = is_reference_query(query)
        eligible_indices = [
            i for i, c in enumerate(self.chunks) if allow_reference or c.section_type != "reference"
        ]

        # 2. Condition filtering: restrict to detected conditions if at least 2 chunks match
        active_conditions = [c.strip() for c in (conditions or []) if c.strip()]
        if active_conditions:
            from app.data.corpus_loader import to_corpus_condition_id

            target_cids = {
                to_corpus_condition_id(c) for c in active_conditions
            } | set(active_conditions)
            cond_filtered = [
                i for i in eligible_indices if self.chunks[i].condition_id in target_cids
            ]
            if len(cond_filtered) >= 2:
                eligible_indices = cond_filtered

        if not eligible_indices:
            return RetrievalResult(chunks=[], mode="bm25_only", best_cosine=0.0, total_candidates=0)

        # 3. Dense query embedding and similarity calculation
        q_vec = self._embed_query(query)
        mode: Literal["hybrid", "bm25_only"] = "hybrid" if q_vec is not None else "bm25_only"

        cosines: dict[int, float] = {}
        best_cosine = 0.0

        if mode == "hybrid" and q_vec is not None:
            q_arr = np.array(q_vec, dtype=np.float32)
            if len(q_arr) == self.matrix.shape[1]:
                q_norm = np.linalg.norm(q_arr)
                if q_norm > 0:
                    q_unit = q_arr / q_norm
                    sub_matrix = self.matrix[eligible_indices]
                    dot_products = np.dot(sub_matrix, q_unit)
                    for local_idx, orig_idx in enumerate(eligible_indices):
                        cos_val = float(dot_products[local_idx])
                        cosines[orig_idx] = cos_val
                    if cosines:
                        best_cosine = max(cosines.values())
            else:
                logger.warning(
                    "Dense query vector dimension (%d) does not match index matrix dimension (%d); "
                    "falling back to bm25_only mode",
                    len(q_arr),
                    self.matrix.shape[1],
                )
                mode = "bm25_only"

        # 4. Relevance floor check
        if (
            mode == "hybrid"
            and not active_conditions
            and best_cosine < self.settings.retrieval_min_cosine
        ):
            return RetrievalResult(
                chunks=[],
                mode="hybrid",
                best_cosine=best_cosine,
                total_candidates=len(eligible_indices),
            )

        # 5. BM25 Scoring
        q_tokens = bm25_tokenize(query)
        content_words = [t for t in q_tokens if t not in STOPWORDS and len(t) > 1]
        all_bm25_scores = self.bm25.get_scores(q_tokens) if q_tokens else np.zeros(len(self.chunks))
        bm25_scores: dict[int, float] = {i: float(all_bm25_scores[i]) for i in eligible_indices}

        if mode == "bm25_only" and not active_conditions and len(content_words) >= 2:
            # Require that at least 2 content words appear in chunk
            valid_content_indices = []
            for idx in eligible_indices:
                chunk_toks = set(bm25_tokenize(self.chunks[idx].text))
                overlap = sum(1 for w in set(content_words) if w in chunk_toks)
                if overlap >= 2:
                    valid_content_indices.append(idx)
            eligible_indices = valid_content_indices
            bm25_scores = {i: bm25_scores[i] for i in eligible_indices}

        best_bm25 = max(bm25_scores.values()) if bm25_scores else 0.0

        if (
            mode == "bm25_only"
            and not active_conditions
            and (best_bm25 < self.settings.retrieval_min_bm25 or not eligible_indices)
        ):
            return RetrievalResult(
                chunks=[],
                mode="bm25_only",
                best_cosine=0.0,
                total_candidates=len(eligible_indices),
            )

        # 6. Reciprocal Rank Fusion (RRF)
        # Sort indices by BM25 score descending to determine 1-based ranks
        sorted_by_bm25 = sorted(eligible_indices, key=lambda idx: bm25_scores[idx], reverse=True)
        bm25_ranks = {orig_idx: rank + 1 for rank, orig_idx in enumerate(sorted_by_bm25)}

        fused_scored_chunks: list[ScoredChunk] = []

        if mode == "hybrid":
            # Sort indices by dense cosine similarity descending to determine 1-based ranks
            sorted_by_dense = sorted(
                eligible_indices, key=lambda idx: cosines.get(idx, -1.0), reverse=True
            )
            dense_ranks = {orig_idx: rank + 1 for rank, orig_idx in enumerate(sorted_by_dense)}

            for orig_idx in eligible_indices:
                r_bm25 = bm25_ranks[orig_idx]
                r_dense = dense_ranks[orig_idx]
                rrf_score = (1.0 / (RRF_K + r_bm25)) + (1.0 / (RRF_K + r_dense))
                fused_scored_chunks.append(
                    ScoredChunk(
                        chunk=self.chunks[orig_idx],
                        fused_score=rrf_score,
                        bm25_rank=r_bm25,
                        dense_rank=r_dense,
                        cosine=cosines.get(orig_idx),
                        bm25_score=bm25_scores.get(orig_idx),
                    )
                )
        else:
            for orig_idx in eligible_indices:
                r_bm25 = bm25_ranks[orig_idx]
                rrf_score = 1.0 / (RRF_K + r_bm25)
                fused_scored_chunks.append(
                    ScoredChunk(
                        chunk=self.chunks[orig_idx],
                        fused_score=rrf_score,
                        bm25_rank=r_bm25,
                        dense_rank=None,
                        cosine=None,
                        bm25_score=bm25_scores.get(orig_idx),
                    )
                )

        # 7. Sort by fused score descending
        fused_scored_chunks.sort(key=lambda sc: sc.fused_score, reverse=True)

        return RetrievalResult(
            chunks=fused_scored_chunks[:effective_top_k],
            mode=mode,
            best_cosine=best_cosine,
            total_candidates=len(eligible_indices),
        )
