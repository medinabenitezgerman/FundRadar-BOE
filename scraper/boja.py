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
    "sindicato", "sindicatos",
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
    "prórroga", "prorroga",
    "autorización para la prestación",
]

def get_ultimo_numero_boja(anyo):
    url = f"{BASE_URL}/eboja/{anyo}.html"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        enlaces = soup.find_all('a', href=re.compile(rf'/eboja/{anyo}/\d+/index\.html'))
        if not enlaces:
            return None
        ultimo = enlaces[-1]['href']
        m = re.search(rf'/eboja/{anyo}/(\d+)/index\.html', ultimo)
        return int(m.group(1)) if m else None
    except Exception as e:
        print(f"Error obteniendo número BOJA: {e}")
        return None

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

def scrape_boja(numero, anyo, fecha):
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
    anyo = date.today().year
    fecha = date.today().strftime("%Y-%m-%d")
    numero = get_ultimo_numero_boja(anyo)
    if not numero:
        print("No se encontró el número del BOJA de hoy.")
    else:
        items = scrape_boja(numero, anyo, fecha)
        print(f"BOJA {numero}: {len(items)} convocatorias relevantes.")
        guardar(items)
