#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
from scraper.core import main as run_step1

if __name__ == "__main__":
    # Ir a la raíz del proyecto para que 'import scraper' funcione
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    os.chdir(BASE_DIR)

    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/scraper_step1.log"),
            logging.StreamHandler(),
        ],
    )
    run_step1()
