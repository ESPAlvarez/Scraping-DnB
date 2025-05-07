import os
import json
import re

INPUT_FILE = "data/subindustries_by_country.json"
OUTPUT_DIR = "data/by_country"

# Expresión regular para extraer sub_industry y code de la URL
PATTERN = re.compile(r"company-information\.(?P<sub>.+?)\.(?P<code>[^./]+)\.html$")


def main():
    # Crear directorio de salida si no existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Cargar datos planos
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    # Agrupar por país
    by_country = {}
    for rec in records:
        # El campo sub_industry del JSON original es en realidad el país
        country = rec.get("sub_industry", "").strip()
        link = rec.get("link", "")

        # Extraer sub_industry real y código
        m = PATTERN.search(link)
        if not m:
            print(f"Warning: enlace no parseable, omitiendo --> {link}")
            continue
        sub_ind = m.group("sub")
        code = m.group("code")

        # Construir nuevo registro
        new_rec = {
            "page": rec.get("page"),
            "link": link,
            "country": country,
            "sub_industry": sub_ind,
            "code": code,
        }

        # Añadir al grupo del país
        by_country.setdefault(country, []).append(new_rec)

    # Escribir un fichero JSON por país
    for country, items in by_country.items():
        # Sanitizar nombre de fichero
        safe_name = country.replace(" ", "_")
        path = os.path.join(OUTPUT_DIR, f"{safe_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"Escritos {len(items)} registros en {path}")


if __name__ == "__main__":
    main()
