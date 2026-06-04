"""Stage 1: validate the manifest, write the calibration/held-out splits.

Frozen output: `data/corpus/splits.json`. After this point the held-out
set is the held-out set; figures cannot migrate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import hydra
from omegaconf import DictConfig

from stem_alt.corpus import DatasetFactory
from stem_alt.corpus.fetch import FetchConfig, fetch_corpus_images
from stem_alt.corpus.stratification import save_splits, stratified_split
from stem_alt.utils import get_logger, set_seed

LOGGER = get_logger(__name__)


def _to_cell_dict(raw: dict) -> Dict[Tuple[str, str], int]:
    """Parse `"domain:eth_category": count` config keys into tuple-keyed cells."""
    cells: Dict[Tuple[str, str], int] = {}
    for key, value in raw.items():
        # rpartition: the eth_category is the leaf, robust to any colon that
        # might appear earlier in a domain name.
        domain, sep, category = str(key).rpartition(":")
        if not sep or not domain or not category:
            raise ValueError(
                f"held_out_target_per_cell key {key!r} must be 'domain:eth_category'"
            )
        cells[(domain, category)] = int(value)
    return cells


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    set_seed(cfg.seed)
    dataset_cls = DatasetFactory(cfg.corpus.name)
    dataset = dataset_cls(manifest_path=cfg.corpus.manifest_path)
    LOGGER.info("Loaded %d figures from %s", len(dataset), cfg.corpus.manifest_path)

    target = _to_cell_dict(cfg.corpus.held_out_target_per_cell)
    calibration, held_out = stratified_split(
        dataset.figures, held_out_target_per_cell=target, seed=cfg.seed
    )
    LOGGER.info("Calibration n=%d  Held-out n=%d", len(calibration), len(held_out))

    splits_path = Path(cfg.corpus.splits_path)
    save_splits(calibration=calibration, held_out=held_out, out_path=splits_path)
    LOGGER.info("Splits written to %s", splits_path)

    # Acquire the licence-preserving figure files named in the manifest. Set
    # corpus.fetch_images=false to (re)write splits without touching the network.
    if cfg.corpus.get("fetch_images", False):
        LOGGER.info("Fetching corpus images from manifest sources ...")
        fetch_cfg = FetchConfig(
            width=int(cfg.corpus.get("fetch_width", 1400)),
            skip_existing=bool(cfg.corpus.get("fetch_skip_existing", True)),
        )
        result = fetch_corpus_images(Path(cfg.corpus.manifest_path), cfg=fetch_cfg)
        if not result.ok:
            LOGGER.warning(
                "%d image(s) could not be fetched: %s",
                len(result.failed),
                [figure_id for figure_id, _ in result.failed],
            )


if __name__ == "__main__":
    main()
