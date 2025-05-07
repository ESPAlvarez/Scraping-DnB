# scraper/config.py

"""
Constantes de configuración global para el scraper:
- MAX_RETRIES: número máximo de reintentos ante fallo de scrapping.
- INITIAL_BACKOFF: tiempo inicial de espera antes del siguiente intento (en segundos).
- BACKOFF_FACTOR: factor de multiplicación del backoff tras cada intento.
- OUTPUT_DIR: directorio base donde se escriben los JSON por país (step0).
"""
import os

PROXY_LIST_FILE = "proxies.txt"
OUTPUT_DIR_0 = os.path.join("data", "by_country")
OUTPUT_DIR_1 = os.path.join("data", "companies_by_sub_industry")
INPUT_DIR_1 = os.path.join("data", "by_country")
CONFIG_DIR = "config_companies"
LOG_FILE = os.path.join("logs", "scraper_step1.log")

# parámetros de reintento y paginación
MAX_RETRIES = 3
INITIAL_BACKOFF = 5  # segundos
BACKOFF_FACTOR = 2
DEFAULT_END_PAGE = 20
