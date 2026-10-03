"""Offline index builder and verification script for the AIRA retrieval layer.

Generates and commits BM25/Dense chunks, float32 normalized embeddings matrix,
and manifest verification metadata.
"""

import argparse
import hashlib
import json
import logging
import math
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.config import settings  # noqa: E402
from app.data.corpus_loader import load_corpus, load_provenance_statuses  # noqa: E402
from app.data.models import GuidelineChunk  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 768


def compute_provenance_hash(provenance_csv_path: Path, allow_unverified: bool = False) -> str:
    """Compute deterministic SHA-256 hash of item IDs."""
    if not provenance_csv_path.exists():
        return hashlib.sha256(b"").hexdigest()

    statuses = load_provenance_statuses(provenance_csv_path)
    if allow_unverified:
        target_ids = sorted(statuses.keys())
    else:
        target_ids = sorted([k for k, v in statuses.items() if v == "verified"])

    return hashlib.sha256("\n".join(target_ids).encode("utf-8")).hexdigest()


def generate_deterministic_vector(
    chunk_id: str, dimension: int = EMBEDDING_DIMENSION
) -> list[float]:
    """Generate a reproducible, non-zero unit vector from a chunk ID for offline builds."""
    seed_int = int(hashlib.sha256(chunk_id.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed_int)  # noqa: S311
    raw = [rng.gauss(0.0, 1.0) for _ in range(dimension)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]


def load_cache(cache_path: Path) -> dict[str, list[float]]:
    """Load previously computed chunk embeddings from cache file."""
    if cache_path.exists():
        try:
            with open(cache_path, encoding="utf-8") as f:
                raw_data = json.load(f)
            if isinstance(raw_data, dict):
                return {
                    str(k): [float(x) for x in v]
                    for k, v in raw_data.items()
                    if isinstance(v, list)
                }
        except Exception as e:
            logger.warning("Failed to load embeddings cache (%s); starting fresh", e)
    return {}


def save_cache(cache_path: Path, cache: dict[str, list[float]]) -> None:
    """Save embeddings cache to temporary file and rename atomically."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = cache_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    temp_path.replace(cache_path)


def embed_chunks_with_backoff(
    chunks: list[GuidelineChunk],
    cache_path: Path,
    mock_mode: bool = False,
) -> tuple[np.ndarray, int]:
    """Embed chunks using Google Generative AI with batching, backoff, and caching."""
    cache = load_cache(cache_path)
    vectors: list[list[float]] = []
    missing_indices: list[int] = []

    for idx, c in enumerate(chunks):
        if c.chunk_id in cache:
            vectors.append(cache[c.chunk_id])
        else:
            vectors.append([])
            missing_indices.append(idx)

    if missing_indices:
        logger.info(
            "Found %d cached embeddings, %d need computation",
            len(chunks) - len(missing_indices),
            len(missing_indices),
        )

        if mock_mode or not settings.gemini_api_key:
            logger.info("Computing deterministic offline vectors without API calls")
            for idx in missing_indices:
                c = chunks[idx]
                vec = generate_deterministic_vector(c.chunk_id, EMBEDDING_DIMENSION)
                cache[c.chunk_id] = vec
                vectors[idx] = vec
            save_cache(cache_path, cache)
        else:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            embedder = GoogleGenerativeAIEmbeddings(  # type: ignore[call-arg]
                model=settings.embedding_model,
                google_api_key=settings.gemini_api_key.get_secret_value(),
                task_type="retrieval_document",
            )

            batch_size = 10
            for b_start in range(0, len(missing_indices), batch_size):
                b_indices = missing_indices[b_start : b_start + batch_size]
                batch_texts = [chunks[i].text for i in b_indices]

                max_retries = 5
                delay = 1.0
                for attempt in range(max_retries):
                    try:
                        logger.info(
                            "Embedding batch %d-%d of %d",
                            b_start + 1,
                            min(b_start + batch_size, len(missing_indices)),
                            len(missing_indices),
                        )
                        batch_embeddings = embedder.embed_documents(batch_texts)
                        for local_idx, emb in enumerate(batch_embeddings):
                            orig_idx = b_indices[local_idx]
                            c_id = chunks[orig_idx].chunk_id
                            cache[c_id] = emb
                            vectors[orig_idx] = emb
                        save_cache(cache_path, cache)
                        time.sleep(0.5)  # Rate-limit spacing
                        break
                    except Exception as err:
                        if attempt == max_retries - 1:
                            logger.error(
                                "Failed to embed batch after %d retries: %s", max_retries, err
                            )
                            raise
                        jitter = random.uniform(0.1, 0.5)  # noqa: S311
                        sleep_time = delay + jitter
                        logger.warning(
                            "Embeddings API error (%s); retrying in %.2fs (attempt %d/%d)",
                            err,
                            sleep_time,
                            attempt + 1,
                            max_retries,
                        )
                        time.sleep(sleep_time)
                        delay *= 2.0

    raw_matrix = np.array(vectors, dtype=np.float32)
    norms = np.linalg.norm(raw_matrix, axis=1, keepdims=True)
    # Avoid zero division
    norms[norms == 0.0] = 1.0
    normalized_matrix = raw_matrix / norms
    dimension = (
        int(normalized_matrix.shape[1]) if normalized_matrix.ndim == 2 else EMBEDDING_DIMENSION
    )
    return normalized_matrix, dimension


def verify_index(data_dir: Path) -> bool:
    """Verify that committed index files match current corpus and provenance hashes."""
    curated_dir = data_dir / "curated"
    index_dir = data_dir / "index"

    curated_manifest_path = curated_dir / "manifest.json"
    provenance_path = curated_dir / "provenance.csv"
    index_manifest_path = index_dir / "manifest.json"
    chunks_path = index_dir / "chunks.jsonl"
    embeddings_path = index_dir / "embeddings.npy"

    errors: list[str] = []

    if not curated_manifest_path.exists():
        errors.append(f"Missing curated manifest: {curated_manifest_path}")
    if not index_manifest_path.exists():
        errors.append(f"Missing index manifest: {index_manifest_path}")
    if not chunks_path.exists():
        errors.append(f"Missing chunks file: {chunks_path}")
    if not embeddings_path.exists():
        errors.append(f"Missing embeddings matrix: {embeddings_path}")

    if errors:
        for err in errors:
            logger.error("Verification failed: %s", err)
        return False

    with open(curated_manifest_path, encoding="utf-8") as f:
        curated_manifest = json.load(f)
    with open(index_manifest_path, encoding="utf-8") as f:
        index_manifest = json.load(f)

    expected_corpus_hash = curated_manifest.get("overall_corpus_hash")
    indexed_corpus_hash = index_manifest.get("corpus_hash")
    if expected_corpus_hash != indexed_corpus_hash:
        errors.append(
            f"Corpus hash mismatch: index has {indexed_corpus_hash}, "
            f"curated has {expected_corpus_hash}"
        )

    allow_unverified = index_manifest.get("include_unverified", False)
    expected_prov_hash = compute_provenance_hash(provenance_path, allow_unverified=allow_unverified)
    indexed_prov_hash = index_manifest.get("provenance_hash")
    if expected_prov_hash != indexed_prov_hash:
        errors.append(
            f"Provenance hash mismatch: index has {indexed_prov_hash}, "
            f"computed {expected_prov_hash}"
        )

    # Check file contents and dimensions
    chunks_count = 0
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks_count += 1

    matrix = np.load(embeddings_path)
    if matrix.ndim != 2:
        errors.append(f"Embeddings matrix is not 2-dimensional: shape={matrix.shape}")
    else:
        if matrix.shape[0] != chunks_count:
            errors.append(
                f"Matrix rows ({matrix.shape[0]}) do not match chunks.jsonl lines ({chunks_count})"
            )
        if matrix.shape[0] != index_manifest.get("chunk_count"):
            errors.append(
                f"Matrix rows ({matrix.shape[0]}) do not match manifest chunk_count "
                f"({index_manifest.get('chunk_count')})"
            )
        if matrix.shape[1] != index_manifest.get("dimension"):
            errors.append(
                f"Matrix columns ({matrix.shape[1]}) do not match manifest dimension "
                f"({index_manifest.get('dimension')})"
            )

    if errors:
        logger.error("Verification failed with %d error(s):", len(errors))
        for err in errors:
            logger.error("  x %s", err)
        return False

    logger.info("SUCCESS: Index verification passed! All hashes, shapes, and counts match.")
    return True


def build_index(data_dir: Path, include_unverified: bool, mock_mode: bool) -> None:
    """Build index chunks, matrix, and manifest atomically."""
    curated_dir = data_dir / "curated"
    index_dir = data_dir / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    curated_manifest_path = curated_dir / "manifest.json"
    if not curated_manifest_path.exists():
        raise FileNotFoundError(f"Curated manifest not found: {curated_manifest_path}")

    with open(curated_manifest_path, encoding="utf-8") as f:
        curated_manifest = json.load(f)
    corpus_hash = curated_manifest["overall_corpus_hash"]

    provenance_path = curated_dir / "provenance.csv"
    provenance_hash = compute_provenance_hash(provenance_path, allow_unverified=include_unverified)

    logger.info(
        "Loading corpus (include_unverified=%s)...",
        include_unverified,
    )
    chunks = load_corpus(data_dir=data_dir, allow_unverified=include_unverified)
    logger.info("Loaded %d guideline chunks from corpus", len(chunks))

    cache_path = index_dir / ".embeddings_cache.json"
    matrix, dimension = embed_chunks_with_backoff(chunks, cache_path, mock_mode=mock_mode)

    built_at_iso = datetime.now(UTC).isoformat()
    manifest_data = {
        "corpus_hash": corpus_hash,
        "provenance_hash": provenance_hash,
        "embedding_model": settings.embedding_model,
        "dimension": dimension,
        "chunk_count": len(chunks),
        "built_at": built_at_iso,
        "include_unverified": include_unverified,
    }

    # Write files atomically
    tmp_npy = index_dir / "embeddings_tmp.npy"
    tmp_jsonl = index_dir / "chunks_tmp.jsonl"
    tmp_manifest = index_dir / "manifest_tmp.json"

    np.save(tmp_npy, matrix)

    with open(tmp_jsonl, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(c.model_dump_json())
            f.write("\n")

    with open(tmp_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
        f.write("\n")

    # Atomic rename
    tmp_npy.replace(index_dir / "embeddings.npy")
    tmp_jsonl.replace(index_dir / "chunks.jsonl")
    tmp_manifest.replace(index_dir / "manifest.json")

    logger.info(
        "Successfully wrote index to %s (%d chunks, dim=%d)",
        index_dir,
        len(chunks),
        dimension,
    )


def main() -> None:
    """Main CLI entry point for build_index script."""
    parser = argparse.ArgumentParser(
        description="Build or verify the committed AIRA guideline retrieval index."
    )
    parser.add_argument(
        "--include-unverified",
        action="store_true",
        help="Include unverified guideline chunks (development mode only).",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify committed index hashes and shapes without calling embedding API.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Generate synthetic reproducible vectors offline without calling external API.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=backend_root / "data",
        help="Path to data directory containing curated and index subdirectories.",
    )

    args = parser.parse_args()

    if args.verify:
        is_valid = verify_index(args.data_dir)
        sys.exit(0 if is_valid else 1)

    build_index(
        data_dir=args.data_dir,
        include_unverified=args.include_unverified,
        mock_mode=args.mock,
    )


if __name__ == "__main__":
    main()
