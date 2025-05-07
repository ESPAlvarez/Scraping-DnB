import os
import json
from typing import Tuple, Set


def read_progress(filepath: str) -> Tuple[Set[str], Set[str]]:
    """
    Lee un fichero JSON de progreso y devuelve dos conjuntos:
    completed y blocked. Si el fichero no existe, devuelve conjuntos vacíos.
    """
    if not os.path.exists(filepath):
        return set(), set()
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    completed = set(data.get("completed", []))
    blocked = set(data.get("blocked", []))
    return completed, blocked


def save_progress(
    filepath: str, completed: Set[str], blocked: Set[str]
) -> None:
    """
    Guarda el estado de progreso en un fichero JSON con las claves
    'completed' y 'blocked'. Crea directorio si es necesario.
    """
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    payload = {
        "completed": list(completed),
        "blocked": list(blocked),
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
