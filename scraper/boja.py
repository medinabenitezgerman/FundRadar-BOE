import os
import re
import requests
from datetime import date
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

BASE_URL = "https://www.juntadeandalucia.es"

SECCIONES_VALIDAS = ["s51", "s54", "s57"]  # Disposiciones generales, Otras disposiciones, Otros anuncios

KEYWORDS_POSITIVAS = [
    "subvención", "subvenciones", "ayuda", "ayudas",
    "convocatoria de subvenciones", "convocatoria de ayudas",
    "concesión de subvenciones", "concesión de ayudas",
]

KEYWORDS_EXCLUIR = [
    "modificación", "nombramiento", "cese", "oposición",
    "concurso de", "licitación", "contrato", "adjudicación",
    "plaza", "puesto de trabajo", "funcionario", "personal",
    "becas de formación", "máster", "investigador",
    "autónomo", "personas físicas", "ciudadanos",
    "certamen", "premio", "galardón",
]

def get_numero_boja(anyo):
    """Obtiene el número del último BOJA publicado para un año dado."""
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
    except:
        return None

def scrape_seccion(anyo, numero, seccion_href):
    """Scrape una sección concreta del BOJA."""
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
        fecha_str = f"{anyo}-{str(numero).zfill(3)}-01"

        convocatorias.append({
            "id_boe":   id_boja,
            "titulo":   titulo[:500],
            "fecha":    f"{anyo}-01-01",
            "url_pdf":  url_html or url_pdf,
            "materia":  seccion_href,
            "fuente":   "BOJA",
        })

    return convocatorias

def scrape_boja(numero, anyo):
    print(f"Scrapeando BOJA {numero} de {anyo}...")
    todas = []
    for seccion in SECCIONES_VALIDAS:
        items = scrape_seccion(anyo, numero, seccion)
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

def scrape_historico_boja(fechas):
    """Scrape múltiples boletines por número."""
    for anyo, numero in fechas:
        try:
            items = scrape_boja(numero, anyo)
            print(f"BOJA {numero}/{anyo}: {len(items)} convocatorias relevantes.")
            guardar(items)
        except Exception as e:
            print(f"Error en BOJA {numero}/{anyo}: {e}")

if __name__ == "__main__":
    anyo = date.today().year
    numero = get_numero_boja(anyo)
    if not numero:
        print("No se encontró el número del BOJA de hoy.")
    else:
        items = scrape_boja(numero, anyo)
        print(f"Encontradas {len(items)} convocatorias relevantes en BOJA {numero}.")
        guardar(items)
