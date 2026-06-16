import os
import re
import requests
from datetime import date
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

BASE_URL = "https://www.bocm.es"

KEYWORDS_POSITIVAS = [
    "subvención", "subvenciones", "ayuda", "ayudas",
    "convocatoria de subvenciones", "convocatoria de ayudas",
    "concesión de subvenciones", "concesión de ayudas",
]

KEYWORDS_EXCLUIR = [
    "modificación", "nombramiento", "cese", "oposición",
    "licitación", "contrato", "adjudicación",
    "becas de formación", "máster", "investigador",
    "autónomo", "autónomos", "personas físicas", "persona física",
    "ciudadanos", "estudiantes",
    "corrección de errores", "corrección de errata",
    "sindicato", "sindicatos",
    "formación profesional para el empleo",
    "compromiso de contratación",
    "personas trabajadoras desempleadas",
    "acción concertada", "prórroga", "prorroga",
    "relación de subvenciones concedidas",
    "subvenciones concedidas",
    "se acuerda modificar",
    "empresas", "pymes", "emprendedores",
    "agricultores", "ganaderos",
]

def get_bocm_hoy():
    hoy = date.today()
    url = f"{BASE_URL}/BOCM/Boletin/Paginas/bocm-{hoy.strftime('%Y%m%d')}.aspx"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return url, hoy.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error accediendo al BOCM: {e}")
    return None, None

def scrape_bocm(url_boletin, fecha):
    try:
        r = requests.get(url_boletin, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"Error descargando BOCM: {e}")
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    convocatorias = []

    for enlace in soup.find_all('a', href=True):
        titulo = enlace.get_text(strip=True)
        if not titulo or len(titulo) < 20:
            continue

        titulo_lower = titulo.lower()
        if not any(k in titulo_lower for k in KEYWORDS_POSITIVAS):
            continue
        if any(k in titulo_lower for k in KEYWORDS_EXCLUIR):
            continue

        href = enlace.get('href', '')
        url_doc = f"{BASE_URL}{href}" if href.startswith('/') else href

        doc_id = re.search(r'(\d{6,})', href)
        id_bocm = f"BOCM-{fecha.replace('-','')}-{doc_id.group(1) if doc_id else len(convocatorias)+1}"

        convocatorias.append({
            "id_boe":  id_bocm,
            "titulo":  titulo[:500],
            "fecha":   fecha,
            "url_pdf": url_doc,
            "materia": "BOCM",
            "fuente":  "BOCM",
            "ccaa":    "Madrid",
        })

    return convocatorias

def guardar(items):
    if not items:
        print("No hay convocatorias nuevas del BOCM.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = (
        client.table("subvenciones")
        .upsert(items, on_conflict="id_boe")
        .execute()
    )
    print(f"Guardadas {len(result.data)} convocatorias del BOCM.")

if __name__ == "__main__":
    url_boletin, fecha = get_bocm_hoy()
    if not url_boletin:
        print("No hay BOCM hoy o no se pudo acceder.")
    else:
        print(f"Scrapeando BOCM de {fecha}...")
        items = scrape_bocm(url_boletin, fecha)
        print(f"BOCM: {len(items)} convocatorias relevantes.")
        guardar(items)
