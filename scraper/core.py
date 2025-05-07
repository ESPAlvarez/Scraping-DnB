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


def main():
    # preparar carpetas y logger
    os.makedirs(OUTPUT_DIR_1, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    proxies = cargar_proxies(PROXY_LIST_FILE)

    for fname in os.listdir(INPUT_DIR_1):
        if not fname.endswith(".json"):
            continue
        country = os.path.splitext(fname)[0]
        country_cfg = os.path.join(CONFIG_DIR, f"{country}.json")
        config = load_json(country_cfg, {"enlaces": {}, "base_links_completados": []})
        config.setdefault("enlaces", {})
        config.setdefault("base_links_completados", [])

        entries = load_json(os.path.join(INPUT_DIR_1, fname), [])
        out_file = os.path.join(OUTPUT_DIR_1, f"{country}.json")
        results = load_json(out_file, [])

        for rec in entries:
            base_link = rec["link"]
            # saltar si ya lo terminamos
            if base_link in config["base_links_completados"]:
                logger.info(f"[{country}] {base_link} ya completado, salto...")
                continue

            full_base = BASE_URL + base_link
            # obtener "verticales" A-Z
            drv0 = init_driver(random.choice(proxies) if proxies else None)
            try:
                drv0.get(full_base)
                time.sleep(random.uniform(2, 4))
                verticals = [
                    a.get_atribute("href")
                    for a in drv0.find_elements(By.CSS_SELECTOR, ".alpha-pagination a[href]")
                ]

            except Exception:
                verticals = []
            finally:
                drv0.quit()

            verticals = [
                v if v.startswith("http") else BASE_URL + v for v in verticals] or [
                full_base]
            errores = False
            # iterar cada "vertical"
            for vlink in verticals:
                entry_cfg = init_link_cfg(vlink, config)
                save_json(country_cfg, config)

                # preparar firma de la página 1
                start_page = entry_cfg["start_page"]
                page = get_next_page(entry_cfg)
                first_signature = None

                while page:
                    paged_url = f"{vlink}? page={page}"
                    logger.info(f"[{country}] GET {paged_url}...")
                    success = False
                    backoff = INITIAL_BACKOFF

                    for attempt in range(1, MAX_RETRIES + 1):
                        drv = init_driver(
                            random.choice(proxies) if proxies else None
                        )
                        try:
                            drv.get(paged_url)
                            time.sleep(random.uniform(2, 4))

                            # sin empresas -> ajustar end_page
                            if is_no_companies_message(drv):
                                new_end = max(page - 1, 1)
                                entry_cfg["end_page"] = new_end
                                entry_cfg["current_page"] = new_end + 1
                                save_json(country_cfg, config)
                                success = True
                                break

                            # detectar bloqueos
                            if any(
                                [
                                    bypass_challenge(drv),
                                    is_access_denied(drv),
                                    is_error_500(drv),
                                    is_connection_lost(drv),
                                ]
                            ):
                                raise Exception("Bloqueo")

                            comps = extract_companies_detailed(
                                drv.page_source, rec["sub_industry"]
                            )
                            # capturar firma de la página 1
                            if page == start_page:
                                first_signature = {
                                    c["company_link"] for c in comps
                                }
                            # Si firma se repite corta paginación
                            elif (
                                first_signature is not None
                                and {
                                    c["company_link"] for c in comps
                                } == first_signature
                            ):
                                new_end = max(page - 1, start_page)
                                entry_cfg["end_page"] = new_end
                                entry_cfg["current_page"] = new_end + 1
                                save_json(country_cfg, config)
                                logger.info(
                                    f"[{country}] página repetida en "
                                    f"{paged_url}, ajustado end_page a {new_end}"
                                )
                                success = True
                                break

                            if not comps:
                                success = True
                                break

                            # guardar datos
                            for c in comps:
                                results.append({**rec, **c, "page": page})
                            save_json(out_file, results)

                            # avanzar puntero
                            entry_cfg["current_page"] += 1
                            save_json(country_cfg, config)
                            success = True
                            break

                        except Exception as e:
                            logger.warning(
                                f"[{country}] error {paged_url}: {e}, "
                                f"retry {attempt}/{MAX_RETRIES}"
                            )
                            time.sleep(backoff + random.random())
                            backoff *= BACKOFF_FACTOR

                        finally:
                            drv.quit()

                    if not success:
                        logger.error(
                            f"[{country}] fallo persistente en {paged_url}, "
                            f"dejo pendiente vertical"
                        )
                        errores = True
                        break

                    page = get_next_page(entry_cfg)

            all_done = not errores and all(
                get_next_page(config["enlaces"].get(v, {})) is None
                for v in verticals
            )
            if all_done:
                config["base_links_completados"].append(base_link)
                save_json(country_cfg, config)
                logger.info(f"[{country}] completado: {base_link}")

            save_json(country_cfg, config)

    logger.info("Scraping Step 1 completado.")


if __name__ == "__main__":
    main()
