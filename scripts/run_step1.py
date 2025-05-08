#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
from scraper.tasks import main as run_tasks

if __name__ == "__main__":
    # Nos situamos en la raíz del proyecto para que 'import scraper' funcione correctamente
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    os.chdir(BASE_DIR)

    # Aseguramos existencia de carpeta de logs
    os.makedirs("logs", exist_ok=True)

    # Configuración de logging compartida
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/tasks.log"),
            logging.StreamHandler(),
        ],
    )

    # Ejecutamos el entry‑point de la CLI de scraping
    run_tasks()
