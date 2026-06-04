"""Acquire third-party corpus figures from the manifest's Commons sources.

Shared by the ``code/scripts/fetch_corpus_images.py`` CLI and by
``pipeline/01_build_corpus.py`` so that building the corpus from the manifest
also materialises the licence-preserving figure files, exactly as the
manuscript Data-availability section and ``data/corpus/README.md`` describe.

Wikimedia Commons renders SVG sources to PNG server-side; raster sources are
converted to the manifest's target format with Pillow; GIF animation is kept.
Rows with a ``local://`` source are skipped — those figures are produced by
``code/scripts/render_local_figures.py``.

This module is import-safe (it is auto-imported by ``stem_alt.corpus``): it
performs no network or filesystem work at import time, and Pillow is imported
lazily inside the functions that need it.
"""

from __future__ import annotations

import csv
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from stem_alt.utils import get_logger

LOGGER = get_logger(__name__)

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "STEM-Alt-corpus-builder/1.0 (academic course project; arvidg@mit.edu)"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class FetchConfig:
    """Immutable fetch configuration."""

    width: int = 1400
    skip_existing: bool = False
    only: Optional[str] = None
    timeout: int = 60
    retries: int = 3
    delay: float = 0.7  # polite pause between downloads (Commons rate limits)


@dataclass
class FetchResult:
    """Outcome of a fetch run."""

    fetched: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    failed: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when every requested figure was fetched (no failures)."""
        return not self.failed


def commons_title(source_url: str) -> Optional[str]:
    """Return the ``File:...`` title from a Commons /wiki/ URL, else None."""
    if "commons.wikimedia.org/wiki/" not in source_url:
        return None
    return urllib.parse.unquote(source_url.split("/wiki/", 1)[1])


def _api_get(params: Dict[str, object], timeout: int) -> dict:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _chunks(seq: List[str], size: int) -> Iterator[List[str]]:
    for start in range(0, len(seq), size):
        yield seq[start : start + size]


def resolve_titles(titles: List[str], cfg: FetchConfig) -> Dict[str, Optional[dict]]:
    """Batch-resolve File titles to imageinfo, following redirects.

    Returns a mapping from the original title to its imageinfo dict, or to
    ``None`` when the file is missing on Commons.
    """
    info_by_resolved: Dict[str, dict] = {}
    normalized: Dict[str, str] = {}
    redirected: Dict[str, str] = {}

    for batch in _chunks(titles, 40):
        data = _api_get(
            {
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "iiprop": "url|mime|size",
                "iiurlwidth": cfg.width,
                "redirects": 1,
                "titles": "|".join(batch),
            },
            cfg.timeout,
        )
        query = data.get("query", {})
        for item in query.get("normalized", []):
            normalized[item["from"]] = item["to"]
        for item in query.get("redirects", []):
            redirected[item["from"]] = item["to"]
        for page in query.get("pages", {}).values():
            if "missing" in page:
                continue
            info = page.get("imageinfo")
            if info:
                info_by_resolved[page["title"]] = info[0]

    resolved: Dict[str, Optional[dict]] = {}
    for title in titles:
        step = normalized.get(title, title)
        canonical = redirected.get(step, step)
        resolved[title] = info_by_resolved.get(canonical)
    return resolved


def _download(url: str, cfg: FetchConfig) -> bytes:
    """Download bytes with a retry loop; back off harder on HTTP 429."""
    last_error: Optional[Exception] = None
    for attempt in range(1, cfg.retries + 2):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=cfg.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            last_error = error
            backoff = 10.0 * attempt if error.code == 429 else 1.5 * attempt
            LOGGER.warning(
                "download attempt %d failed (HTTP %s); backing off %.0fs",
                attempt, error.code, backoff,
            )
            time.sleep(backoff)
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            LOGGER.warning("download attempt %d failed: %s", attempt, error)
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"failed to download {url}: {last_error}")


def _to_target_bytes(raw: bytes, target_ext: str) -> bytes:
    """Return bytes in the manifest's target format (lazy Pillow import)."""
    if target_ext == ".gif":
        return raw  # keep original (preserves animation)
    if target_ext == ".png" and raw[:8] == PNG_MAGIC:
        return raw  # already PNG (e.g. a Commons SVG->PNG render)

    from PIL import Image

    with Image.open(io.BytesIO(raw)) as image:
        if image.mode == "CMYK":
            image = image.convert("RGB")
        elif image.mode in ("P", "LA"):
            image = image.convert("RGBA")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()


def _validate(path: Path) -> Tuple[Tuple[int, int], str]:
    """Confirm the written file is a decodable image; return size and format."""
    from PIL import Image

    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.size, (image.format or "?")


def _pick_url(info: dict, target_ext: str) -> str:
    """Choose the best source URL for the target format."""
    if target_ext == ".gif":
        return info["url"]  # original preserves animation
    return info.get("thumburl") or info["url"]


def fetch_corpus_images(
    manifest_path: Path,
    project_root: Optional[Path] = None,
    cfg: Optional[FetchConfig] = None,
) -> FetchResult:
    """Fetch every third-party figure named in the manifest into its image_path.

    ``image_path`` values are resolved relative to ``project_root`` (defaults
    to the manifest's ``<root>/data/corpus/manifest.csv`` grandparent).
    """
    manifest_path = Path(manifest_path)
    cfg = cfg or FetchConfig()
    if project_root is None:
        project_root = manifest_path.resolve().parents[2]

    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    result = FetchResult()

    # Decide which rows need fetching before any network call, so a re-run on a
    # populated corpus (skip_existing) resolves nothing and stays offline.
    pending: List[dict] = []
    for row in rows:
        figure_id = row["figure_id"]
        if cfg.only and figure_id != cfg.only:
            continue
        dest = project_root / row["image_path"]
        if row["source_url"].startswith("local://"):
            LOGGER.info(
                "skip  %-34s local figure (%s)",
                figure_id, "present" if dest.exists() else "MISSING",
            )
            result.skipped.append(figure_id)
            continue
        if cfg.skip_existing and dest.exists():
            LOGGER.info("skip  %-34s exists", figure_id)
            result.skipped.append(figure_id)
            continue
        pending.append(row)

    titles = [t for row in pending for t in [commons_title(row["source_url"])] if t]
    resolved = resolve_titles(titles, cfg) if titles else {}

    for row in pending:
        figure_id = row["figure_id"]
        source_url = row["source_url"]
        dest = project_root / row["image_path"]
        target_ext = dest.suffix.lower()

        title = commons_title(source_url)
        info = resolved.get(title) if title else None
        if info is None:
            LOGGER.error("FAIL  %-34s unresolved source: %s", figure_id, source_url)
            result.failed.append((figure_id, "unresolved source"))
            continue

        try:
            time.sleep(cfg.delay)  # throttle to stay under Commons rate limits
            raw = _download(_pick_url(info, target_ext), cfg)
            data = _to_target_bytes(raw, target_ext)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            (width, height), fmt = _validate(dest)
            LOGGER.info(
                "ok    %-34s %5d x %-5d %-4s %6.0f KB  <- %s",
                figure_id, width, height, fmt, len(data) / 1024, title,
            )
            result.fetched.append(figure_id)
        except (RuntimeError, OSError, ValueError) as error:
            LOGGER.error("FAIL  %-34s %s", figure_id, error)
            result.failed.append((figure_id, str(error)))

    LOGGER.info(
        "done: %d fetched, %d skipped, %d failed",
        len(result.fetched), len(result.skipped), len(result.failed),
    )
    for figure_id, why in result.failed:
        LOGGER.error("  failed: %s (%s)", figure_id, why)
    return result
