# scraper/tasks.py
import argparse
import logging
import os

from .core import scrape_country, scrape_countries
from .diff import compute_diff
from .config import INPUT_DIR_1, CONFIG_DIR

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="DNB Scraper: batch, subset or single‑country modes"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--country",
        type=str,
        help="Force scraper and diff for a single country"
    )
    group.add_argument(
        "--countries",
        nargs="+",
        metavar="COUNTRY",
        help="List of countries to process (subset mode)"
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Generate change report after scraping"
    )
    args = parser.parse_args()

    # Asegurarnos de que exista la carpeta de configs
    os.makedirs(CONFIG_DIR, exist_ok=True)

    if args.country:
        # ─── Single‑country mode ─────────────────────────────────────────────────
        country = args.country
        logger.info(f"[*] Single‑country mode: force re‑scrape {country}")
        scrape_country(country, reset=True)

        if args.diff:
            logger.info(f"[*] Generating diff for {country}")
            compute_diff(country)

    else:
        # ─── Batch / Subset mode ────────────────────────────────────────────────
        if args.countries:
            targets = args.countries
            logger.info(f"[*] Subset mode: processing {targets}")
        else:
            # Batch A→Z: todos los países que falten por completar
            files = sorted(f for f in os.listdir(INPUT_DIR_1) if f.endswith(".json"))
            targets = [os.path.splitext(f)[0] for f in files]
            logger.info(f"[*] Batch mode: processing all countries → {targets}")

        # Ejecutar scraping de todos los targets (va saltando los completados)
        scrape_countries(targets)

        if args.diff:
            for country in targets:
                logger.info(f"[*] Generating diff for {country}")
                compute_diff(country)


if __name__ == '__main__':
    # Configurar logging
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler('logs/tasks.log'),
            logging.StreamHandler(),
        ],
    )
    main()
