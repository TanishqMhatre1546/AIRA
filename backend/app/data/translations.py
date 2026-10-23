"""Translation sidecar loader and registry for curated guideline items."""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.config import settings

logger = logging.getLogger(__name__)

TranslationStatus = Literal["draft", "reviewed", "rejected"]


@dataclass(frozen=True)
class TranslationItem:
    """Individual translation item matching an extracted provenance item_id."""

    item_id: str
    text: str
    status: TranslationStatus
    reviewer: str | None = None
    reviewed_on: str | None = None
    source_hash: str | None = None


def compute_source_hash(text: str) -> str:
    """Compute normalized 12-char SHA-1 hash of source English text."""
    clean = " ".join(text.strip().rstrip(".!?").lower().split())
    return hashlib.sha1(clean.encode("utf-8")).hexdigest()[:12]  # noqa: S324


class TranslationRegistry:
    """In-memory cache of curated guideline translations."""

    def __init__(self, i18n_dir: Path | None = None) -> None:
        if i18n_dir:
            self.i18n_dir = i18n_dir
        else:
            p1 = Path(settings.data_dir) / "curated" / "i18n"
            p2 = Path(__file__).resolve().parent.parent.parent / "data" / "curated" / "i18n"
            self.i18n_dir = p1 if p1.exists() else p2
        self._cache: dict[tuple[str, str], dict[str, TranslationItem]] = {}
        self._loaded: bool = False

    def load(self, force_reload: bool = False) -> None:
        """Load all sidecar translation files from i18n directory."""
        if self._loaded and not force_reload:
            return

        self._cache.clear()
        if not self.i18n_dir.exists():
            self._loaded = True
            return

        for path in self.i18n_dir.glob("*.*.json"):
            # Expected file format: <condition_stem>.<lang>.json (e.g. acute_diarrhea.hi.json)
            parts = path.name.split(".")
            if len(parts) < 3:
                continue
            lang = parts[-2]
            cond_key = ".".join(parts[:-2])

            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning("Failed to parse translation file %s: %s", path, e)
                continue

            # Support either a dict keyed by item_id or a list of items
            items_dict: dict[str, TranslationItem] = {}
            raw_items = data.get("translations", data) if isinstance(data, dict) else data

            if isinstance(raw_items, dict):
                for item_id, item_val in raw_items.items():
                    if isinstance(item_val, dict):
                        status = item_val.get("status", "draft")
                        if status not in ("draft", "reviewed", "rejected"):
                            status = "draft"
                        items_dict[item_id] = TranslationItem(
                            item_id=item_id,
                            text=str(item_val.get("text", "")).strip(),
                            status=status,
                            reviewer=item_val.get("reviewer"),
                            reviewed_on=item_val.get("reviewed_on"),
                            source_hash=item_val.get("source_hash"),
                        )
            elif isinstance(raw_items, list):
                for item_val in raw_items:
                    if isinstance(item_val, dict) and "item_id" in item_val:
                        i_id = str(item_val["item_id"])
                        status = item_val.get("status", "draft")
                        if status not in ("draft", "reviewed", "rejected"):
                            status = "draft"
                        items_dict[i_id] = TranslationItem(
                            item_id=i_id,
                            text=str(item_val.get("text", "")).strip(),
                            status=status,
                            reviewer=item_val.get("reviewer"),
                            reviewed_on=item_val.get("reviewed_on"),
                            source_hash=item_val.get("source_hash"),
                        )

            # Register under both the condition key in file name and doc id if present
            self._cache[(cond_key, lang)] = items_dict
            doc_id = data.get("condition_id") if isinstance(data, dict) else None
            if doc_id and doc_id != cond_key:
                self._cache[(doc_id, lang)] = items_dict

        self._loaded = True

    def get_translation(
        self,
        condition_id: str,
        lang: str,
        item_id: str,
        allow_unreviewed: bool = False,
        current_source_text: str | None = None,
    ) -> tuple[str | None, str | None]:
        """Retrieve reviewed translated text for an item, or draft if allowed."""
        self.load()
        items = self._cache.get((condition_id, lang))
        if not items:
            # Fallback check stripping 'icmr-stw-' prefix or replacing dashes with underscores
            alt_key = condition_id.replace("icmr-stw-", "").replace("-", "_")
            items = self._cache.get((alt_key, lang))

        if not items or item_id not in items:
            return None, None

        item = items[item_id]
        if not item.text.strip():
            return None, None

        # A changed English item resets its translation to draft
        status = item.status
        if current_source_text and item.source_hash:
            curr_hash = compute_source_hash(current_source_text)
            if curr_hash != item.source_hash:
                status = "draft"

        if status == "reviewed":
            return item.text, "reviewed"
        if status == "draft" and allow_unreviewed:
            return item.text, "draft"

        return None, None


# Global translation registry instance
translation_registry = TranslationRegistry()
