import logging
from fake_useragent import UserAgent
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth

BASE_URL = "https://www.dnb.com"

logger = logging.getLogger(__name__)


def init_driver(proxy=None, headless=False):
    """
    Inicializa un webDriver con configuración anti-bot, proxy opcional
    y user-agent aleatorio.
    """
    chromedir = chromedriver_autoinstaller.install()

    ua = UserAgent().random
    logger.debug(f"User-Agent: {ua}")

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument(f"--user-agent={ua}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--window-position=-2000,0")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")

    if proxy:
        opts.add_argument(f"--proxy-server=http://{proxy}")
        logger.debug(f"Proxy usado: {proxy}")

    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_experimental_option(
        "prefs",
        {
            "intl.accept_languages": "en-US,en",
        },
    )

    driver = webdriver.Chrome(service=Service(chromedir), options=opts)

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
