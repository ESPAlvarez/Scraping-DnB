import os
from setuptools import setup, find_packages

# Leemos el README para la descripción larga
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="dnb_scraper",
    version="0.1.0",
    author="Eder Samuel Pineda Alvarez",
    author_email="espineda0616@gmail.com",
    description="Scraper modular para la extracción de compañías desde dnb.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ESPAlvarez/dnb_scraper",
    packages=find_packages(exclude=["tests", "app"]),
    include_package_data=True,
    install_requires=[
        "selenium>=4.0.0",
        "chromedriver-autoinstaller",
        "fake-useragent",
        "beautifulsoup4",
        "lxml",
        "selenium-stealth",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "flake8",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
        "dnb-step0 = scripts.prepare.scraper_step0:main",  # Solo si scraper_step0.py define un main()
        "dnb-step1 = scraper.tasks:main",  # Correcto: tasks.py gestiona Step 1
        ],
    },
)
