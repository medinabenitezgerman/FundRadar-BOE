import os
import re
import requests
from datetime import date
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

BASE_URL = "https://www.juntadeandalucia.es"

SECCIONES_VALIDAS = ["s51", "s54"]

KEYWORDS_POSITIVAS = [
    "subvención", "subvenciones", "ayuda", "ayudas",
    "convocatoria de subvenciones", "convocatoria de ayudas",
    "concesión de subvenciones", "concesión de ayudas",
]

KEYWORDS_EXCLUIR = [
    "modificación del extracto",
    "extracto de modificación",
    "segunda modificación",
    "tercera modificación",
    "modificación de la convocatoria",
    "nombramiento", "cese", "oposición",
    "concurso de", "licitación", "contrato", "adjudicación",
    "plaza", "puesto de trabajo", "funcionario", "personal",
    "becas de formación", "máster", "investigador",
    "autónomo", "personas físicas", "ciudadanos",
    "certamen", "premio", "galardón",
    "relación de subvenciones concedidas",
    "subvenciones concedidas",
    "se hace pública la relación",
    "se acuerda modificar la resolución",
    "corrección de errores",
    "corrección de errata",
    "corrección de error",
    "sindicato",
    "sindicatos",
    "organizaciones sindicales",
    "representación sindical",
    "acción sindical",
    "federación sindical",
    "confederación sindical",
    "formación profesional para el empleo",
    "compromiso de contratación",
    "personas trabajadoras desempleadas",
    "programas formativos",
    "acción concertada",
    "prórroga",
    "prorroga",
    "autorización para la prestación",
]

FECHAS_BOJA = {
    63: "2026-04-01", 64: "2026-04-02", 65: "2026-04-03",
    66: "2026-04-04", 67: "2026-04-07", 68: "2026-04-08",
    69: "2026-04-09", 70: "2026-04-10", 71: "2026-04-11",
    72: "2026-04-14", 73: "2026-04-15", 74: "2026-04-16",
    75: "2026-04-17", 76: "2026-04-22", 77: "2026-04-23",
    78: "2026-04-24", 79: "2026-04-25", 80: "2026-04-28",
    81: "2026-04-29", 82: "2026-04-30",
    83: "2026-05-04", 84: "2026-05-05", 85: "2026-05-06",
    86: "2026-05-07", 87: "2026-05-08", 88: "2026-05-12",
    89: "2026-05-13", 90: "2026-05-14", 91: "2026-05-15",
    92: "2026-05-19", 93: "2026-05-20", 94: "2026-05-21",
    95: "2026-05-22", 96: "2026-05-26", 97: "2026-05-27",
    98: "2026-05-28", 99: "2026-05-29",
    100: "2026-06-02", 101: "2026-06-03", 102: "2026-06-04",
    103: "2026-06-05", 104: "2026-06-09", 105: "2026-06-10",
    106: "2026-06-11", 107: "2026-06-12", 108: "2026-06-12",
    109: "2026-06-12", 110: "2026-06-12", 111: "2026-06-12",
    112: "2026-06-12",
}

def scrape_seccion(anyo, numero, seccion_href, fecha):
    url = f"{BASE_URL}/eboja/{anyo}/{numero}/{seccion_href}"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except:
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    items = soup.find_all('div', class_='item')
    convocatorias = []

    for item in items:
        p = item.find('p')
        if not p:
            continue
        titulo = p.get_text(strip=True)
        titulo_lower = titulo.lower()

        if not any(k in titulo_lower for k in KEYWORDS_POSITIVAS):
            continue
        if any(k in titulo_lower for k in KEYWORDS_EXCLUIR):
            continue

        enlace_html = item.find('a', class_='item_html')
        url_html = None
        num_disp = None
        if enlace_html:
            href = enlace_html.get('href', '')
            if href.startswith('/boja/'):
                url_html = f"{BASE_URL}{href}"
                m = re.search(r'/boja/\d{4}/\d+/(\d+)', href)
                if m:
                    num_disp = m.group(1)

        enlace_pdf = item.find('a', class_='item_pdf_grupo')
        url_pdf = None
        if enlace_pdf:
            href = enlace_pdf.get('href', '')
            if href.startswith('http'):
                url_pdf = href
            elif href:
                url_pdf = f"{BASE_URL}/eboja/{anyo}/{numero}/{href}"

        id_boja = f"BOJA-{anyo}-{numero}-{num_disp or len(convocatorias)+1}"

        convocatorias.append({
            "id_boe":  id_boja,
            "titulo":  titulo[:500],
            "fecha":   fecha,
            "url_pdf": url_html or url_pdf,
            "materia": seccion_href,
            "fuente":  "BOJA",
        })

    return convocatorias

def scrape_boja(numero, anyo):
    fecha = FECHAS_BOJA.get(numero, f"{anyo}-01-01")
    print(f"Scrapeando BOJA {numero} de {anyo} ({fecha})...")
    todas = []
    for seccion in SECCIONES_VALIDAS:
        items = scrape_seccion(anyo, numero, seccion, fecha)
        todas.extend(items)
        print(f"  Sección {seccion}: {len(items)} convocatorias")
    return todas

def guardar(items):
    if not items:
        print("No hay convocatorias nuevas del BOJA.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = (
        client.table("subvenciones")
        .upsert(items, on_conflict="id_boe")
        .execute()
    )
    print(f"Guardadas {len(result.data)} convocatorias del BOJA.")

if __name__ == "__main__":
    anyo = 2026
    for numero in range(63, 113):
        try:
            items = scrape_boja(numero, anyo)
            print(f"BOJA {numero}: {len(items)} convocatorias relevantes.")
            guardar(items)
        except Exception as e:
            print(f"Error en BOJA {numero}: {e}")
