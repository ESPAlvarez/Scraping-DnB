import os
import re
from scraper.utils import load_json, save_json
from scraper.config import OUTPUT_DIR_0

# Constants
INPUT_FILE = os.path.join("data/raw", "subindustries_by_country.json")
# Regex to extract sub_industry and country code from link
PATTERN = re.compile(r"company-information\.(?P<sub>.+?)\.(?P<code>[^./]+)\.html$")


def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR_0, exist_ok=True)

    # Load flat list of subindustry records
    records = load_json(INPUT_FILE, [])

    # Group by country
    by_country = {}
    for rec in records:
        country = rec.get("sub_industry", "").strip()
        link = rec.get("link", "")

        # Extract real sub_industry and code
        m = PATTERN.search(link)
        if not m:
            print(f"Warning: enlace no parseable, omitiendo --> {link}")
            continue
        sub_ind = m.group("sub")
        code = m.group("code")

        # Build new record
        new_rec = {
            "page": rec.get("page"),
            "link": link,
            "country": country,
            "sub_industry": sub_ind,
            "code": code,
        }

        by_country.setdefault(country, []).append(new_rec)

    # Write per-country JSON files
    for country, items in by_country.items():
        safe_name = country.replace(" ", "_")
        path = os.path.join(OUTPUT_DIR_0, f"{safe_name}.json")
        save_json(path, items)
        print(f"Escritos {len(items)} registros en {path}")


if __name__ == "__main__":
    main()
