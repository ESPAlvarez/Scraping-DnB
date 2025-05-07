import os
import json
import random
import re
import time
import logging

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
from fake_useragent import UserAgent

# ---------------------------- Configuración inicial ----------------------------

PROXY_LIST_FILE = "proxies.txt"
LINKS_FILE = "links.txt"
PROGRESS_FILE = "progress_step0.json"
OUTPUT_FILE = "data/subindustries_by_country.json"
LOG_FILE = "logs/scraper_blocking.log"
BASE_URL = "https://www.dnb.com"

MAX_RETRIES = 3
INITIAL_BACKOFF = 5  # segundos
BACKOFF_FACTOR = 2

# Asegurar directorios
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# Logger
logging.basicConfig(
    filename=LOG_FILE,
    filemode="w",
    format="[%(asctime)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger()

# ---------------------------- Detección de bloqueos ----------------------------


def bypass_challenge(driver):
    """Detecta iframe de challenge (captcha/sec)."""
    try:
        driver.find_element(By.ID, "sec-cpt-if")
        return True
    except NoSuchElementException:
        return False


def is_error_500(driver, timeout=3):
    """Detecta página con Error 500."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '//h2[contains(text(),"500 Error")]'))
        )
        return True
    except TimeoutException:
        return False


def is_access_denied(driver, timeout=3):
    """Detecta página con Access Denied."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '//h1[contains(text(),"Access Denied")]'))
        )
        return True
    except TimeoutException:
        return False


def is_connection_lost(driver):
    """Detecta errores de conexión perdida, 404, 502, etc."""
    text = driver.page_source.lower()
    for msg in ["connection lost", "not found", "404 error", "http error 502", "no puede procesar"]:
        if msg in text:
            return True
    return False


# ---------------------------- Driver & Stealth setup ----------------------------


# Modifica init_driver para aceptar un proxy opcional
def init_driver(proxy=None):
    chromedir = chromedriver_autoinstaller.install()
    ua = UserAgent().random
    logger.debug(f"  → New UA: {ua}")
    opts = Options()
    opts.headless = False
    opts.add_argument(f"--user-agent={ua}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--disable-dev-shm-usage")

    if proxy:
        opts.add_argument(f"--proxy-server=http://{proxy}")
        logger.debug(f"  → Proxy usado: {proxy}")

    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_experimental_option(
        "prefs",
        {
            "intl.accept_languages": "en-US,en",
        },
    )

    service = Service(chromedir)
    driver = webdriver.Chrome(service=service, options=opts)

    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.setExtraHTTPHeaders",
        {
            "headers": {
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": BASE_URL,
            }
        },
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


# ---------------------------- Utilidades de scraping ----------------------------


def cargar_proxies(filepath):
    with open(filepath, "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
    logger.info(f"{len(proxies)} proxies cargados.")
    return proxies


def cargar_links(filepath):
    enlaces = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            p = line.strip()
            if not p:
                continue
            if not p.startswith("http"):
                p = BASE_URL + (p if p.startswith("/") else f"/{p}")
            enlaces.append(p)
    logger.info(f"Cargadas {len(enlaces)} URLs")
    return enlaces


def leer_progreso(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            d = json.load(f)
        return set(d.get("completed", [])), set(d.get("blocked", []))
    return set(), set()


def guardar_progreso(filepath, completed, blocked):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {"completed": list(completed), "blocked": list(blocked)},
            f,
            indent=2,
            ensure_ascii=False,
        )
    logger.debug("Progreso guardado")


def extract_subindustries(html):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    selectors = [
        "div.col-md-6.col-xs-6.data a[href]",  # Estilo original
        "div.data a[href]",  # Cualquier contenedor .data
        "div.row a[href*='/business-directory/company-information.']",  # Dentro de fila
        "a[href*='/business-directory/company-information.']",  # Cualquier enlace relevante
    ]
    for sel in selectors:
        for a in soup.select(sel):
            name = a.get_text(strip=True).split("(")[0].strip()
            href = a["href"]
            out.append((name, href))
        if out:
            return out
    # Fallback regex por si cambian clases
    for a in soup.find_all(
        "a", href=re.compile(r"/business-directory/company-information\.[^.]+\.[^/]+\.html")
    ):
        name = a.get_text(strip=True).split("(")[0].strip()
        out.append((name, a["href"]))
    return out


# ---------------------------- Main ----------------------------


def main():
    proxies = cargar_proxies(PROXY_LIST_FILE)
    urls = cargar_links(LINKS_FILE)
    completed, blocked = leer_progreso(PROGRESS_FILE)
    results = []

    for url in urls:
        if url in completed:
            logger.info(f"[SKIP] {url}")
            continue
        backoff, success = INITIAL_BACKOFF, False
        for attempt in range(1, MAX_RETRIES + 1):
            logger.info(f"[{attempt}/{MAX_RETRIES}] GET {url}")
            proxy = random.choice(proxies) if proxies else None
            driver = init_driver(proxy)
            try:
                driver.get(url)
                time.sleep(random.uniform(2, 4))
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(random.uniform(1, 2))

                html = driver.page_source
                subs = extract_subindustries(html)
                if subs:
                    for name, href in subs:
                        results.append({"page": url, "sub_industry": name, "link": href})
                    completed.add(url)
                    logger.info(f"  ✅ Extraídos {len(subs)} enlaces de {url}")
                    success = True
                    break
                # Si no extrajo, marcar completado sin bloqueos
                completed.add(url)
                logger.warning(f"  ⚠️ Sin sub‑industrias en {url}, marcado completo")
                success = True
                break

            except Exception as e:
                if not subs:
                    if (
                        bypass_challenge(driver)
                        or is_access_denied(driver)
                        or is_error_500(driver)
                        or is_connection_lost(driver)
                    ):
                        logger.warning(f"Bloqueo en {url}: {e}")
                logger.info(f"  Retrying en {backoff:.1f}s (error: {e})")
                time.sleep(backoff + random.uniform(0, 2))
                backoff *= BACKOFF_FACTOR

            finally:
                try:
                    driver.delete_all_cookies()
                    driver.quit()
                except:
                    pass

        if not success:
            logger.error(f"❌ Falló tras {MAX_RETRIES} intentos: {url}")
            blocked.add(url)
        guardar_progreso(PROGRESS_FILE, completed, blocked)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        time.sleep(random.uniform(3, 6))

    logger.info(f"Scrape terminado. {len(results)} enlaces guardados.")


if __name__ == "__main__":
    main()
