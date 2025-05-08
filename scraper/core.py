import os
import time
import random
import logging
from selenium.webdriver.common.by import By

from .config import (
    DEFAULT_END_PAGE,
    OUTPUT_DIR_1,
    INPUT_DIR_1,
    CONFIG_DIR,
    PROXY_LIST_FILE,
    INITIAL_BACKOFF,
    MAX_RETRIES,
    BACKOFF_FACTOR,
)
from .driver_factory import init_driver, BASE_URL
from .extractor import (
    bypass_challenge,
    is_access_denied,
    is_error_500,
    is_connection_lost,
    extract_companies_detailed,
    is_no_companies_message,
)
from .utils import cargar_proxies, load_json, save_json

logger = logging.getLogger(__name__)


def init_link_cfg(link: str, config: dict) -> dict:
    """
    Inicializa la configuración del enlace para el scrapping.
    """
    entry = config["enlaces"].setdefault(
        link,
        {
            "start_page": 1,
            "end_page": DEFAULT_END_PAGE,
            "current_page": 1,
        },
    )
    # Asegurar valores válidos
    entry["start_page"] = 1
    if entry["end_page"] < 1:
        entry["end_page"] = DEFAULT_END_PAGE
    entry["current_page"] = max(
        entry["start_page"],
        min(entry.get("current_page", entry["start_page"]), entry["end_page"]),
    )
    return entry


def get_next_page(entry: dict) -> int:
    return (
        entry["current_page"]
        if entry["current_page"] <= entry["end_page"]
        else None
    )


def scrape_country(country: str, reset: bool = False):
    """
    Hace scraping completo (o re‑scrape si reset=True) para un país.
    - Carga/crea CONFIG_DIR/{country}.json
    - Itera cada base_link, vertical y página
    - Persiste progreso y resultados en OUTPUT_DIR_1/{country}.json
    """
    # directorios
    os.makedirs(OUTPUT_DIR_1, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)

    cfg_path = os.path.join(CONFIG_DIR, f"{country}.json")
    if reset and os.path.exists(cfg_path):
        os.remove(cfg_path)  # fuerza re‑inicio
    config = load_json(cfg_path, {"enlaces": {}, "base_links_completados": []})
    config.setdefault("enlaces", {})
    config.setdefault("base_links_completados", [])

    # proxies y lista de sub‑industrias
    proxies = cargar_proxies(PROXY_LIST_FILE)
    entries = load_json(os.path.join(INPUT_DIR_1, f"{country}.json"), [])
    out_file = os.path.join(OUTPUT_DIR_1, f"{country}.json")
    results = load_json(out_file, [])

    for rec in entries:
        base_link = rec["link"]
        if base_link in config["base_links_completados"]:
            logger.info(f"[{country}] {base_link} ya completado, salto…")
            continue

        full_base = BASE_URL + base_link
        # obtener A→Z verticales
        drv0 = init_driver(random.choice(proxies) if proxies else None)
        try:
            drv0.get(full_base)
            time.sleep(random.uniform(2, 4))
            verticals = [
                e.get_attribute("href")
                for e in drv0.find_elements(By.CSS_SELECTOR, ".alpha-pagination a[href]")
            ]
        except Exception:
            verticals = []
        finally:
            drv0.quit()

        verticals = [
            v if v.startswith("http") else BASE_URL + v for v in verticals
        ] or [full_base]
        errores = False

        # loop verticales → páginas
        for vlink in verticals:
            entry_cfg = init_link_cfg(vlink, config)
            save_json(cfg_path, config)

            start_page = entry_cfg["start_page"]
            page = get_next_page(entry_cfg)
            first_sig = None

            while page:
                paged = f"{vlink}?page={page}"
                logger.info(f"[{country}] GET {paged}…")
                success = False
                backoff = INITIAL_BACKOFF

                for attempt in range(1, MAX_RETRIES + 1):
                    drv = init_driver(random.choice(proxies) if proxies else None)
                    try:
                        drv.get(paged)
                        time.sleep(random.uniform(2, 4))

                        # sin empresas?
                        if is_no_companies_message(drv):
                            new_end = max(page - 1, 1)
                            entry_cfg.update({"end_page": new_end, "current_page": new_end + 1})
                            save_json(cfg_path, config)
                            success = True
                            break

                        # bloqueos?
                        if any([bypass_challenge(drv),
                                is_access_denied(drv),
                                is_error_500(drv),
                                is_connection_lost(drv)]):
                            raise Exception("Bloqueo")

                        comps = extract_companies_detailed(drv.page_source, rec["sub_industry"])

                        # firma de la página 1
                        if page == start_page:
                            first_sig = {c["company_link"] for c in comps}
                        # si repite la firma, cortamos
                        elif first_sig is not None and {
                            c["company_link"] for c in comps
                        } == first_sig:
                            new_end = max(page - 1, start_page)
                            entry_cfg.update({"end_page": new_end, "current_page": new_end + 1})
                            save_json(cfg_path, config)
                            logger.info(f"[{country}] firma repetida en {paged}, ajustado end_page={new_end}")
                            success = True
                            break

                        if not comps:
                            success = True
                            break

                        # guardar resultados
                        for c in comps:
                            results.append({**rec, **c, "page": page})
                        save_json(out_file, results)

                        # avanzar
                        entry_cfg["current_page"] += 1
                        save_json(cfg_path, config)
                        success = True
                        break

                    except Exception as e:
                        logger.warning(f"[{country}] error {paged}: {e}, retry {attempt}/{MAX_RETRIES}")
                        time.sleep(backoff + random.random())
                        backoff *= BACKOFF_FACTOR
                    finally:
                        drv.quit()

                if not success:
                    logger.error(f"[{country}] fallo persistente en {paged}, dejo pendiente.")
                    errores = True
                    break

                page = get_next_page(entry_cfg)

        # si no hubo errores y todo paginado terminó:
        if not errores and all(get_next_page(
            config["enlaces"].get(v, {})
        ) is None for v in verticals):
            config["base_links_completados"].append(base_link)
            save_json(cfg_path, config)
            logger.info(f"[{country}] base_link completado: {base_link}")

    logger.info(f"[{country}] Scraping completado.")


def scrape_countries(countries: list[str], reset: bool = False):
    """
    Para un listado de países:
     - si reset=True, borra su cfg individual antes de scrapear
     - llama a scrape_country por cada uno
    """
    for c in countries:
        scrape_country(c, reset=reset)


# Modo standalone: batch A→Z
if __name__ == "__main__":
    # lista de todos los países
    files = sorted(f for f in os.listdir(INPUT_DIR_1) if f.endswith(".json"))
    all_c = [os.path.splitext(f)[0] for f in files]
    logging.basicConfig(level=logging.INFO)
    scrape_countries(all_c)
