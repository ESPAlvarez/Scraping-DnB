import os
import json
from typing import Any, Dict, List, Tuple


def load_results(
    country: str,
    input_dir: str = "data/companies_by_country",
) -> List[Dict[str, Any]]:
    """
    Carga el snapshot JSON para un país dado desde el directorio especificado.
    """
    path = os.path.join(input_dir, f"{country}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_diff(
    country: str,
    old_dir: str = "data/companies_by_country_old",
    new_dir: str = "data/companies_by_country",
    report_dir: str = "reports",
) -> Dict[str, Any]:
    """
    Compara el snapshot "old" y "new" de un país, y genera un dict con:
      - added: empresas nuevas
      - removed: empresas que desaparecieron
      - updated: empresas existentes cuyo "revenue" o "location" cambiaron
    Escribe el informe completo en reports/{country}_changes.json.
    """
    old_snapshot = load_results(country, old_dir)
    new_snapshot = load_results(country, new_dir)

    # Indexar por company_link
    old_map = {c["company_link"]: c for c in old_snapshot}
    new_map = {c["company_link"]: c for c in new_snapshot}

    # Detectar añadidos y eliminados
    added = [new_map[link] for link in new_map if link not in old_map]
    removed = [old_map[link] for link in old_map if link not in new_map]

    # Detectar actualizados
    updated: List[Dict[str, Any]] = []
    for link, new_c in new_map.items():
        if link in old_map:
            old_c = old_map[link]
            changes: Dict[str, Tuple[Any, Any]] = {}
            for field in {"revenue", "location"}:
                if old_c.get(field) != new_c.get(field):
                    changes[field] = (old_c.get(field), new_c.get(field))
            if changes:
                updated.append(
                    {
                        "company_link": link,
                        "changes": changes,
                        "old": old_c,
                        "new": new_c,
                    }
                )

    report = {
        "country": country,
        "added": added,
        "removed": removed,
        "updated": updated,
    }

    # Asegurar directorio de reportes
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{country}_changes.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report
