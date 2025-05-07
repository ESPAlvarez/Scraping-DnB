import os
import json
import random
import time
import logging
import re

import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from lxml import etree
from fake_useragent import UserAgent

# ---------------------------- Configuración ----------------------------
BASE_URL = "https://www.dnb.com"
PROXY_LIST_FILE = "proxies.txt"
INPUT_DIR = "data/by_country"
OUTPUT_DIR = "data/companies_by_country"
CONFIG_DIR = "config_companies"
LOG_FILE = "logs/scraper_step1.log"
MAX_RETRIES = 3
INITIAL_BACKOFF = 5
BACKOFF_FACTOR = 2
DEFAULT_END_PAGE = 20

# Asegurar directorios
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE, level=logging.DEBUG, format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger()


# ---------------------------- Utils: Configuración ----------------------------
def load_json(path, default):
    return json.load(open(path, "r", encoding="utf-8")) if os.path.exists(path) else default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def init_link_cfg(link, config):
    if link not in config["enlaces"]:
        config["enlaces"][link] = {"start_page": 1, "end_page": DEFAULT_END_PAGE, "current_page": 1}
    entry = config["enlaces"][link]

    if entry.get("end_page", 0) < 1:
        entry["end_page"] = DEFAULT_END_PAGE

    # solo asegurar current_page no sea menor a start_page
    entry["current_page"] = max(entry["start_page"], entry["current_page"])
    return entry


def get_next_page(entry):
    return entry["current_page"] if entry["current_page"] <= entry["end_page"] else None


# ---------------------------- Proxy Pool ----------------------------
def load_proxies(filepath=PROXY_LIST_FILE):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


# ---------------------------- WebDriver Setup ----------------------------
def init_driver(proxy=None):
    chromedir = chromedriver_autoinstaller.install()
    ua = UserAgent().random
    opts = Options()
    opts.add_argument(f"--user-agent={ua}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--disable-dev-shm-usage")
    if proxy:
        opts.add_argument(f"--proxy-server=http://{proxy}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_experimental_option("prefs", {"intl.accept_languages": ["en-US", "en"]})
    driver = webdriver.Chrome(service=Service(chromedir), options=opts)
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.setExtraHTTPHeaders",
        {"headers": {"Referer": BASE_URL, "Accept-Language": "en-US,en;q=0.9"}},
    )
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        safe_context=True,
    )
    return driver


# ---------------------------- Bloqueos y errores ----------------------------
def bypass_challenge(driver):
    try:
        driver.find_element(By.ID, "sec-cpt-if")
        return True
    except NoSuchElementException:
        return False


def is_error_500(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '//h2[contains(text(),"500 Error")]'))
        )
        return True
    except TimeoutException:
        return False


def is_access_denied(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout=3).until(
            EC.presence_of_element_located((By.XPATH, '//h1[contains(text(),"Access Denied")]'))
        )
        return True
    except TimeoutException:
        return False


def is_connection_lost(driver):
    txt = driver.page_source.lower()
    return any(msg in txt for msg in ["connection lost", "404 error", "http error 502"])


def is_no_companies_message(driver):
    try:
        driver.find_element(By.CLASS_NAME, "candidatesMatchedQuantityIsNullOrZeroWrapper")
        return True
    except NoSuchElementException:
        return False


# ---------------------------- Extracción ----------------------------
def extract_companies_detailed(html, sub_industry):
    soup = BeautifulSoup(html, "html.parser")
    data = []
    for blk in soup.find_all("div", class_=re.compile(r"col-md-12 data")):
        try:
            root = etree.HTML(str(blk))
            name_el = root.xpath('.//div[@class="col-md-6"]/a')
            comp = name_el[0].text.strip() if name_el else "N/A"
            href = name_el[0].get("href") if name_el else ""
            locs = [
                l.strip().replace("\xa0", " ")
                for l in root.xpath('.//div[@class="col-md-4"]/text()')
                if l.strip()
            ]
            locs = locs[-2:] if len(locs) >= 2 else locs
            rev_el = root.xpath('.//div[@class="col-md-2 last"]/text()') or []
            rev = rev_el[-1].strip() if rev_el else "N/A"
            data.append(
                {
                    "company_name": comp,
                    "company_link": BASE_URL + href,
                    "location": locs,
                    "revenue": rev,
                    "sub_industry": sub_industry,
                }
            )
        except Exception as e:
            logger.warning(f"Error extrayendo bloque: {e}")
    return data


# ---------------------------- Main ----------------------------
def main():
    proxies = load_proxies()

    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith(".json"):
            continue
        country = os.path.splitext(fname)[0]
        country_cfg_path = os.path.join(CONFIG_DIR, f"{country}.json")
        config = load_json(country_cfg_path, {"enlaces": {}})
        config.setdefault("base_links_completados", [])

        entries = load_json(os.path.join(INPUT_DIR, fname), [])
        out_file = os.path.join(OUTPUT_DIR, f"{country}.json")
        results = load_json(out_file, [])

        for rec in entries:
            base_link = rec["link"]
            if base_link in config.get("base_links_completados", []):
                logger.info(f"[{country}] {base_link} ya marcado como completado, saltando…")
                continue

            full_base = f"{BASE_URL}{base_link}"

            # Obtener verticals (A-Z) normalizados absolutos
            drv0 = init_driver(random.choice(proxies) if proxies else None)
            try:
                drv0.get(full_base)
                time.sleep(random.uniform(2, 4))
                verticals = [
                    a.get_attribute("href")
                    for a in drv0.find_elements(By.CSS_SELECTOR, ".alpha-pagination a[href]")
                ]
            except Exception:
                verticals = []
            finally:
                drv0.quit()

            verticals = [v if v.startswith("http") else f"{BASE_URL}{v}" for v in verticals]
            if not verticals:
                verticals = [full_base]

            errores_en_verticales = False  # 🚩 bandera para errores

            for vlink in verticals:
                entry_cfg = init_link_cfg(vlink, config)
                next_page = get_next_page(entry_cfg)
                while next_page:
                    paged_url = f"{vlink}?page={next_page}"
                    logger.info(f"[{country}] GET {paged_url}")
                    success = False
                    backoff = INITIAL_BACKOFF
                    for attempt in range(1, MAX_RETRIES + 1):
                        drv = init_driver(random.choice(proxies) if proxies else None)
                        try:
                            drv.get(paged_url)
                            time.sleep(random.uniform(2, 4))

                            if is_no_companies_message(drv):
                                new_end = max(next_page - 1, 1)
                                entry_cfg["end_page"] = new_end
                                entry_cfg["current_page"] = new_end + 1
                                save_json(country_cfg_path, config)
                                logger.info(
                                    f"[{country}] sin empresas en {paged_url}, ajustado end_page a {new_end}, avanzando current_page"
                                )
                                success = True
                                break

                            if (
                                bypass_challenge(drv)
                                or is_access_denied(drv)
                                or is_error_500(drv)
                                or is_connection_lost(drv)
                            ):
                                raise Exception("Bloqueado")

                            comps = extract_companies_detailed(drv.page_source, rec["sub_industry"])
                            if not comps:
                                success = True
                                break

                            for c in comps:
                                results.append({**rec, **c, "page": next_page})
                            save_json(out_file, results)

                            entry_cfg["current_page"] += 1
                            save_json(country_cfg_path, config)
                            success = True
                            break

                        except Exception as e:
                            logger.warning(
                                f"[{country}] error en {paged_url}: {e}, retry {attempt}/{MAX_RETRIES}"
                            )
                            time.sleep(backoff + random.random())
                            backoff *= BACKOFF_FACTOR
                        finally:
                            drv.quit()

                    if not success:
                        logger.error(
                            f"[{country}] fallo persistente en {paged_url}, dejando vertical pendiente"
                        )
                        errores_en_verticales = True
                        break

                    next_page = get_next_page(entry_cfg)

            # ✅ Solo marcar como completado si TODO se procesó sin errores
            all_done = not errores_en_verticales and all(
                get_next_page(config["enlaces"].get(v, {})) is None for v in verticals
            )
            if all_done and base_link not in config["base_links_completados"]:
                config["base_links_completados"].append(base_link)
                save_json(country_cfg_path, config)
                logger.info(f"[{country}] Marcado como completado: {base_link}")

            save_json(country_cfg_path, config)

    logger.info("Scraping compañías completado.")


if __name__ == "__main__":
    main()
