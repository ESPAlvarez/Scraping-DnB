import os
import json
from typing import List

from scraper.driver_factory import BASE_URL


def cargar_proxies(filepath: str) -> List[str]:
    """
    Carga una lista de proxies desde un fichero de texto, una URL por línea.
    """
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        proxies = [line.strip() for line in f if line.strip()]
    return proxies


def cargar_links(filepath: str) -> List[str]:
    """
    Carga una lista de URLs desde un fichero de texto.
    Cada línea puede ser:
      - absoluta (http://… o https://…)
      - relativa, como "/foo" o "bar"
    Las rutas relativas se normalizan como BASE_URL + "/" + ruta_sin_barra_inicial.
    """
    if not os.path.exists(filepath):
        return []
    links: List[str] = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url:
                continue
            if url.lower().startswith("http"):
                links.append(url)
            else:
                # asegurarnos de que haya una sola "/" de separación
                if not url.startswith("/"):
                    url = "/" + url
                links.append(BASE_URL + url)
    return links


def load_json(path: str, default):
    """
    Carga JSON desde archivo o devuelve valor por defecto si no existe.
    """
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path: str, obj) -> None:
    """
    Guarda un objeto como JSON en el archivo especificado.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
