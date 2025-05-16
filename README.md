# 📊 DNB Web Scraper – Versión 1

Este proyecto es un scraper automatizado orientado a la recolección de información empresarial desde el sitio web de Dun & Bradstreet ([https://www.dnb.com/](https://www.dnb.com/)). A través de un flujo estructurado en Python, este sistema extrae nombres de empresas, subindustrias, ingresos aproximados y ubicaciones, con el objetivo de facilitar el análisis exploratorio y el enriquecimiento de una futura base de datos.

⚠️ Disclaimer legal
Este scraper fue desarrollado con fines estrictamente educativos y de investigación. No somos propietarios ni estamos afiliados a Dun & Bradstreet. El uso de esta herramienta debe respetar los términos y condiciones del sitio web objetivo. No promovemos ni autorizamos su uso con fines comerciales o automatizaciones masivas sin consentimiento.

---

## ✅ ¿Qué se logró en esta primera versión (v1)?

* Extracción completa por país, subindustria y vertical A–Z.
* Implementación de control de paginación, detección de bloqueos (Access Denied, CAPTCHA, errores 500).
* Soporte para proxies gratuitos rotativos mediante ProxyScrape.
* Guardado de resultados en formato JSON.
* Comparación entre snapshots antiguos y nuevos para detectar cambios.
* Orquestación por CLI (consola) con varios modos de ejecución.
* Código modular, con lógica dividida en etapas (preparación, extracción, orquestación).
* Tests unitarios (extractores, progreso, utilidades).
* Compatible con Python 3.10+ y sin dependencias comerciales.

---

## 🧠 Motivación

Scrapear datos públicos puede ser una herramienta poderosa para estudios de mercado, validaciones cruzadas y análisis competitivos. Sin embargo, también implica retos técnicos (rotación de IPs, bloqueo por tráfico, detección de patrones) que esta versión aborda parcialmente.

Este proyecto nació como un reto técnico sin fines de lucro y fue realizado desde cero sin frameworks pesados ni plataformas externas.

---

## 🛠 Tecnologías utilizadas

* Python 3.10
* Selenium (con Chrome Headless)
* BeautifulSoup4 + lxml
* Streamlit (para futuras interfaces)
* pytest / flake8 / black (estilo y tests)
* Documentación: Notion
* Gestión de dependencias: pip + requirements.txt

---

## 🚀 ¿Qué viene para la Versión 2?

El siguiente paso del proyecto no se enfoca en scraping, sino en transformar esta herramienta en una plataforma completa de análisis de datos con interfaz web.

Se plantea:

* Uso de PostgreSQL como base de datos centralizada.
* Incorporación de nuevos campos en el scraper (dirección, doing business as, sitio web).
* Revisión manual y enriquecimiento de datos por parte de analistas (ej. LinkedIn, teléfonos).
* Construcción de una capa de negocio con:

  * Streamlit como dashboard interactivo para analistas y usuarios finales.
  * GraphQL (con Graphene) para exponer los datos de forma estructurada.
  * Streamlit-Authenticator para login y control de acceso.
* Orquestación interna sin .bat, desde el backend.
* Posible integración con React (solo si fuera requerido).

Todo esto se hará sin costos de hosting ni dominio (presupuesto = 0), priorizando el entorno local de desarrollo.

---

📘 Documentación completa del proyecto (v1):
[https://www.notion.so/DOCUMENTACION-SCRAPING-DNB-V1-1edbbe7bad088035b4f9cb5785b4bd7c?pvs=4](https://www.notion.so/DOCUMENTACION-SCRAPING-DNB-V1-1edbbe7bad088035b4f9cb5785b4bd7c?pvs=4)

---

🤝 Colaboración y créditos

Este proyecto fue diseñado, desarrollado y documentado con enfoque modular, claridad técnica y profesionalismo. ¡Cualquier mejora o recomendación es bienvenida siempre que se respete el carácter no comercial del mismo!

¿Quieres usar este código como base para tus pruebas educativas o aprendizaje? Adelante. ¿Planeas automatizar scraping masivo? Te recomendamos revisar las políticas del sitio objetivo.

---
