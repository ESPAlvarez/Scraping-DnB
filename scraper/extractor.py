import re
from typing import List, Tuple, Dict
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from lxml import etree
from .driver_factory import BASE_URL


def bypass_challenge(driver) -> bool:
    """Detecta iframe de challenge (captcha/sec)."""
    try:
        driver.find_element(By.ID, "sec-cpt-if")
        return True
    except NoSuchElementException:
        return False


def is_error_500(driver, timeout: int = 3) -> bool:
    """
    Detecta página con Error HTTP 500 usando WebDriverWait, 
    con fallback en page_source.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//h2[contains(text(),'500 Error') or "
                    "contains(text(),'500 error')]",
                )
            )
        )
        return True
    except (TimeoutException, NoSuchElementException, Exception):
        return "500 error" in driver.page_source.lower()


def is_access_denied(driver, timeout: int = 3) -> bool:
    """
    Detecta página con mensaje de Access Denied usando WebDriverWait,
    con fallback.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//h1[contains(text(),'Access Denied') or "
                    "contains(text(),'access denied')]",
                )
            )
        )
        return True
    except (TimeoutException, NoSuchElementException, Exception):
        return "access denied" in driver.page_source.lower()


def is_connection_lost(driver) -> bool:
    """Detecta errores de conexión (404, 502, connection lost, etc.)."""
    text = driver.page_source.lower()
    for msg in [
        "connection lost",
        "not found",
        "404 error",
        "http error 502",
        "no found",
        "no puede procesar",
    ]:
        if msg in text:
            return True
    return False


def is_no_companies_message(driver) -> bool:
    """Detecta cuando la página indica que no hay empresas listadas."""
    try:
        driver.find_element(
            By.CLASS_NAME,
            "candidatesMatchedQuantityIsNullOrZeroWrapper",
        )
        return True
    except NoSuchElementException:
        return False


def extract_subindustries(html: str) -> List[Tuple[str, str]]:
    """
    Extrae enlaces de subindustrias a partir de HTML.
    Devuelve una lista de tuplas (nombre, href).
    """
    soup = BeautifulSoup(html, "html.parser")
    out: List[Tuple[str, str]] = []
    selectors = [
        "div.col-md-6.col-xs-6.data a[href]",
        "div.data a[href]",
        "div.row a[href*='/business-directory/company-information.']",
        "a[href*='/business-directory/company-information.']",
    ]
    for sel in selectors:
        for a in soup.select(sel):
            name = a.get_text(strip=True).split("(")[0].strip()
            href = a.get("href")
            out.append((name, href))
        if out:
            return out
    # fallback regex
    for a in soup.find_all(
        "a",
        href=re.compile(
            r"/business-directory/company-information\.[^.]+\.[^/]+\.html"
        ),
    ):
        name = a.get_text(strip=True).split("(")[0].strip()
        out.append((name, a["href"]))
    return out


def extract_companies_detailed(
    html: str, sub_industry: str
) -> List[Dict[str, str]]:
    """
    Extrae datos detallados de empresas de una página de resultados.
    Cada dict contiene company_name, company_link, location,
    revenue, sub_industry.
    """
    soup = BeautifulSoup(html, "html.parser")
    data: List[Dict] = []
    for blk in soup.find_all("div", class_=re.compile(r"col-md-12 data")):
        try:
            root = etree.HTML(str(blk))
            name_el = root.xpath('.//div[@class="col-md-6"]/a')
            comp = name_el[0].text.strip() if name_el else "N/A"
            href = name_el[0].get("href") if name_el else ""
            locs = [
                text.strip().replace("\xa0", " ")
                for text in root.xpath('.//div[@class="col-md-4"]/text()')
            ]
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
        except Exception:
            continue
    return data
