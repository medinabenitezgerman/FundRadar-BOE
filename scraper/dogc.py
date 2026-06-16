import os
import re
import requests
from datetime import date
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

BASE_URL = "https://dogc.gencat.cat"

SECCIONES_VALIDAS = ["Disposicions generals", "Altres disposicions", "Anuncis"]

KEYWORDS_POSITIVAS = [
    "subvenci", "ajut", "ajuts", "convocatoria", "concessio",
    "subvención", "subvenciones", "ayuda", "ayudas",
    "convocatoria de subvencions",
]

KEYWORDS_EXCLUIR = [
    "modificacio", "nomenament", "cessament", "oposici",
    "licitaci", "contracte", "adjudicaci",
    "formacio professional", "compromis de contractaci",
    "persones fisiques", "ciutadans",
    "correccio d'errades", "correccio d'error",
    "sindicat", "sindicats",
    "accio concertada", "prorrog",
    "relacio de subvencions concedides",
    "persones fisiques",
    "empresa", "autonoms",
]

def get_numero_dogc():
    url = f"{BASE_URL}/ca/inici/"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        m = re.search(r'DOGC\s+n[uú]m\.?\s*(\d+)', soup.get_text())
        if m:
            return int(m.group(1))
    except Exception as e:
        print(f"Error obteniendo número DOGC: {e}")
    return None

def scrape_dogc(numero):
    url = f"{BASE_URL}/ca/pdogc_canals_interns/pdogc_sumari_del_dogc/?numDOGC={numero}"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"Error descargando DOGC {numero}: {e}")
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    fecha = date.today().strftime("%Y-%m-%d")
    convocatorias = []

    m = re.search(r'(\d{2}/\d{2}/\d{4})', soup.get_text())
    if m:
        parts = m.group(1).split('/')
        fecha = f"{parts[2]}-{parts[1]}-{parts[0]}"

    items = soup.find_all(['p', 'div'], string=re.compile(r'.{20,}'))

    for item in soup.find_all('a', href=re.compile(r'/ca/document-del-dogc/')):
        titulo = item.get_text(strip=True)
        if not titulo or len(titulo) < 20:
            continue

        titulo_norm = titulo.lower().encode('ascii', 'ignore').decode()
        if not any(k in titulo_norm for k in KEYWORDS_POSITIVAS):
            continue
        if any(k in titulo_norm for k in KEYWORDS_EXCLUIR):
            continue

        href = item.get('href', '')
        url_doc = f"{BASE_URL}{href}" if href.startswith('/') else href
        doc_id = re.search(r'documentId=(\d+)', href)
        id_dogc = f"DOGC-{numero}-{doc_id.group(1) if doc_id else len(convocatorias)+1}"

        convocatorias.append({
            "id_boe":  id_dogc,
            "titulo":  titulo[:500],
            "fecha":   fecha,
            "url_pdf": url_doc,
            "materia": "DOGC",
            "fuente":  "DOGC",
            "ccaa":    "Cataluña",
        })

    return convocatorias

def guardar(items):
    if not items:
        print("No hay convocatorias nuevas del DOGC.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = (
        client.table("subvenciones")
        .upsert(items, on_conflict="id_boe")
        .execute()
    )
    print(f"Guardadas {len(result.data)} convocatorias del DOGC.")

if __name__ == "__main__":
    numero = get_numero_dogc()
    if not numero:
        print("No se encontró el número del DOGC de hoy.")
    else:
        print(f"Scrapeando DOGC {numero}...")
        items = scrape_dogc(numero)
        print(f"DOGC {numero}: {len(items)} convocatorias relevantes.")
        guardar(items)
