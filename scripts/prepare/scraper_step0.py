import os
import time
import random
import logging
from scraper.driver_factory import init_driver
from scraper.extractor import (
    extract_subindustries,
    bypass_challenge,
    is_access_denied,
    is_error_500,
    is_connection_lost,
)
from scraper.utils import (
    cargar_proxies,
    cargar_links,
    save_json
)
from scraper.progress import read_progress, save_progress
from scraper.config import (
    MAX_RETRIES,
    INITIAL_BACKOFF,
    BACKOFF_FACTOR,
    PROXY_LIST_FILE
)

# configuración de logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("logs/scraper_step0.log"),
              logging.StreamHandler()],
)

# Constantes especificas
LINKS_FILE = "links.txt"
PROGRESS_FILE = "progress_step0.json"
OUTPUT_FILE = "data/raw/subindustries_by_country.json"
os.makedirs("logs", exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)


def main():
    proxies = cargar_proxies(PROXY_LIST_FILE)
    urls = cargar_links(LINKS_FILE)
    completed, blocked = read_progress(PROGRESS_FILE)
    results = []

    for url in urls:
        if url in completed:
            logger.info(f"[SKIP] {url}")
            continue

        backoff, success = INITIAL_BACKOFF, False
        for attempt in range(1, MAX_RETRIES + 1):
            logger.info(f"[{attempt}/{MAX_RETRIES}] Scraping {url}...")
            proxy = random.choice(proxies) if proxies else None
            driver = init_driver(proxy, headless=True)
            try:
                driver.get(url)
                time.sleep(random.uniform(2, 4))
                html = driver.page_source

                # Detectar bloqueos
                if (
                    bypass_challenge(driver)
                    or is_access_denied(driver)
                    or is_error_500(driver)
                    or is_connection_lost(driver)
                ):
                    raise Exception("Bloqueo detectado")

                subs = extract_subindustries(html)
                if subs:
                    for name, href in subs:
                        results.append({"page": url, "sub_industry": name, "link": href})

                completed.add(url)
                logger.info(f"  ✅ Extraídos {len(subs)} enlaces de {url}")
                success = True
                break

            except Exception as e:
                logger.warning(f"  ⚠️ Error en {url}: {e}, retrying en {backoff}s")
                time.sleep(backoff)
                backoff *= BACKOFF_FACTOR

            finally:
                driver.quit()

        if not success:
            logger.error(f"❌ Falló tras {MAX_RETRIES} intentos: {url}")
            blocked.add(url)

        save_progress(PROGRESS_FILE, completed, blocked)
        save_json(OUTPUT_FILE, results)
        time.sleep(random.uniform(1, 3))

    logger.info(f"Scrape step0 completado. Total de enlaces: {len(results)}")


if __name__ == "__main__":
    main()
