"""Calibration script to determine optimal retrieval_min_cosine threshold.

Runs 30 in-scope clinical queries and 30 out-of-scope non-clinical queries,
measures cosine similarity distributions, and recommends a threshold.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.config import settings  # noqa: E402
from app.core.retriever import Retriever  # noqa: E402
from scripts.build_index import generate_deterministic_vector  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

IN_SCOPE_QUERIES = [
    # Acute diarrhea
    "watery stools loose motion and dehydration",
    "frequent watery diarrhea with stomach cramps",
    # Acute respiratory infections
    "cough runny nose sore throat and mild fever",
    "nasal congestion sneezing and cold symptoms",
    # Acute rhinosinusitis
    "facial pressure pain and thick nasal discharge",
    "sinus headache with blocked nose and green mucus",
    # Bacterial skin infections
    "painful red swollen boil on leg with pus",
    "warm tender red skin spreading on arm cellulitis",
    # Dengue fever
    "high fever retro-orbital headache and joint pain",
    "sudden high fever body aches and skin rash",
    # Dermatophytosis (Ringworm / Tinea)
    "circular itchy red ring rash on groin",
    "itchy fungal patch on feet ringworm",
    # Diabetes Type 2
    "increased thirst frequent urination and fatigue",
    "high blood sugar symptoms and lifestyle management",
    # Eczema / Dermatitis
    "dry itchy inflamed skin patches on hands",
    "eczema flare up with flaky red skin and itching",
    # Epistaxis (Nosebleed)
    "nose bleeding from one side how to pinch nose",
    "active nosebleed first aid pressure technique",
    # Headache
    "throbbing tension headache on both sides of head",
    "mild migraine headache with sensitivity to sound",
    # Hypertension
    "high blood pressure readings and salt reduction",
    "elevated blood pressure lifestyle advice and monitoring",
    # Pharyngitis / Sore throat
    "pain when swallowing and scratchy throat",
    "red inflamed throat with difficulty eating solids",
    # Scabies
    "severe itching between fingers and wrists at night",
    "burrows on skin with intense nocturnal itching",
    # Urinary tract infection
    "burning sensation when passing urine and urgency",
    "frequent urination burning pain in lower abdomen",
    # Urticaria / Angioedema
    "raised itchy red hives on skin with wheals",
    "sudden allergic hives with itchy raised welts",
]

OUT_OF_SCOPE_QUERIES = [
    # Programming & Tech
    "how to write a binary search tree in python",
    "what is docker containerization and kubernetes",
    "best practices for git merge conflicts",
    "how does a transformer neural network work",
    # Mathematics & Physics
    "explain quantum mechanics and wave particle duality",
    "how to solve quadratic equations with quadratic formula",
    "what is the theory of general relativity",
    "calculate the area of a trapezoid formula",
    # Cooking & Food Recipes
    "recipe for chocolate chip cookies with butter",
    "how to bake sourdough bread at home",
    "best pasta carbonara authentic italian recipe",
    "how to make homemade chicken noodle soup",
    # Geography & History
    "what is the capital city of australia",
    "who was the first emperor of the roman empire",
    "list the seven wonders of the ancient world",
    "major historical events of the industrial revolution",
    # Finance & Economics
    "how to invest in index funds and mutual funds",
    "what causes inflation in modern macroeconomics",
    "mortgage interest rates calculation formula",
    "cryptocurrency blockchain ledger technology",
    # Sports & Entertainment
    "rules of cricket and how many players on team",
    "who won the football world cup in 2022",
    "plot summary of hamlet by william shakespeare",
    "how to play the acoustic guitar for beginners",
    # Travel & Everyday Tasks
    "how to fix a leaky faucet in bathroom sink",
    "best tourist attractions to visit in tokyo",
    "how to change a flat tire on a bicycle",
    "cheap hotels and flight booking tips in europe",
    # Philosophy & Literature
    "what is the philosophical meaning of stoicism",
    "analysis of themes in the great gatsby",
]


class MockOfflineEmbedder:
    """Deterministic offline embedder for calibration without live API."""

    def embed_query(self, query: str) -> list[float]:
        # Generate vector seeded by query tokens
        return generate_deterministic_vector(query, dimension=768)


def get_embedder(mock_mode: bool) -> Any:
    """Initialize live or mock embedder."""
    if mock_mode or not settings.gemini_api_key:
        logger.info("Using mock offline embedder for calibration")
        return MockOfflineEmbedder()

    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(  # type: ignore[call-arg]
        model=settings.embedding_model,
        google_api_key=settings.gemini_api_key.get_secret_value(),
        task_type="retrieval_query",
    )


def compute_distribution_stats(scores: list[float]) -> dict[str, float]:
    """Calculate summary statistics for a set of cosine scores."""
    if not scores:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0, "p10": 0.0, "p90": 0.0}

    arr = np.array(scores)
    return {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p90": float(np.percentile(arr, 90)),
        "std": float(np.std(arr)),
    }


def run_calibration(data_dir: Path, mock_mode: bool) -> None:
    """Run calibration experiment across 30 in-scope and 30 out-of-scope queries."""
    embedder = get_embedder(mock_mode)
    retriever = Retriever.from_disk(
        index_dir=data_dir / "index",
        curated_dir=data_dir / "curated",
        embedder=embedder,
        settings=settings,
    )

    logger.info("Running calibration with %d in-scope queries...", len(IN_SCOPE_QUERIES))
    in_scope_cosines: list[float] = []
    for q in IN_SCOPE_QUERIES:
        # Run search with high min_cosine to record raw cosine without floor drop
        orig_min = retriever.settings.retrieval_min_cosine
        retriever.settings.retrieval_min_cosine = -1.0
        res = retriever.search(q, conditions=None, top_k=5)
        retriever.settings.retrieval_min_cosine = orig_min
        in_scope_cosines.append(res.best_cosine)

    logger.info("Running calibration with %d out-of-scope queries...", len(OUT_OF_SCOPE_QUERIES))
    out_scope_cosines: list[float] = []
    for q in OUT_OF_SCOPE_QUERIES:
        orig_min = retriever.settings.retrieval_min_cosine
        retriever.settings.retrieval_min_cosine = -1.0
        res = retriever.search(q, conditions=None, top_k=5)
        retriever.settings.retrieval_min_cosine = orig_min
        out_scope_cosines.append(res.best_cosine)

    in_stats = compute_distribution_stats(in_scope_cosines)
    out_stats = compute_distribution_stats(out_scope_cosines)

    print("\n===========================================================")
    print("           AIRA RETRIEVAL CALIBRATION REPORT               ")
    print("===========================================================")
    print(f"Total In-Scope Queries:     {len(IN_SCOPE_QUERIES)}")
    print(f"Total Out-of-Scope Queries: {len(OUT_OF_SCOPE_QUERIES)}")
    print("-----------------------------------------------------------")
    print("IN-SCOPE COSINE DISTRIBUTION:")
    print(f"  Mean:   {in_stats['mean']:.4f} (+/- {in_stats['std']:.4f})")
    print(f"  Median: {in_stats['median']:.4f}")
    print(f"  Min:    {in_stats['min']:.4f}")
    print(f"  Max:    {in_stats['max']:.4f}")
    print(f"  10th %: {in_stats['p10']:.4f}")
    print(f"  90th %: {in_stats['p90']:.4f}")
    print("-----------------------------------------------------------")
    print("OUT-OF-SCOPE COSINE DISTRIBUTION:")
    print(f"  Mean:   {out_stats['mean']:.4f} (+/- {out_stats['std']:.4f})")
    print(f"  Median: {out_stats['median']:.4f}")
    print(f"  Min:    {out_stats['min']:.4f}")
    print(f"  Max:    {out_stats['max']:.4f}")
    print(f"  10th %: {out_stats['p10']:.4f}")
    print(f"  90th %: {out_stats['p90']:.4f}")
    print("-----------------------------------------------------------")

    # Separation analysis
    midpoint = (in_stats["median"] + out_stats["median"]) / 2.0
    recommended_threshold = round(max(0.60, min(0.75, midpoint)), 2)

    print(f"Current Configured Threshold: {settings.retrieval_min_cosine:.2f}")
    print(f"Recommended Threshold:        {recommended_threshold:.2f}")
    print("===========================================================\n")


def main() -> None:
    """CLI entry point for calibrate_retrieval."""
    parser = argparse.ArgumentParser(
        description="Calibrate retrieval_min_cosine threshold on 60 benchmark queries."
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock deterministic embedder instead of live API.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=backend_root / "data",
        help="Path to data directory.",
    )

    args = parser.parse_args()
    run_calibration(data_dir=args.data_dir, mock_mode=args.mock)


if __name__ == "__main__":
    main()
