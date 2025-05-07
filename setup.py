import os
from setuptools import setup, find_packages

setup(
    name="dnb_scraper",
    version="0.1.0",
    author="Eder Samuel Pineda Alvarez",
    author_email="espineda0616@gmail.com",
    description="Scraper modular para la extracción de compañías desde dnb.com",
    long_description=(
        open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else ""
    ),
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
        "dev": ["pytest", "black", "flake8"],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "dnb-step0=scripts.prepare.scraper_step0:main",  # Ajusta la ruta si es necesario
            "dnb-step1=scripts.run_step1:main",  # Ajusta la ruta si es necesario
        ]
    },
)
