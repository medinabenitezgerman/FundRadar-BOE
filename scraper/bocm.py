import os
import re
import requests
from datetime import date
from lxml import etree
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SCRAPER_KEY  = os.environ.get("SCRAPER_API_KEY", "")

BASE_URL = "https://www.bocm.es"

KEYWORDS_POSITIVAS = [
    "subvenci", "ayuda", "ayudas",
    "convocatoria de subvenciones", "convocatoria de ayudas",
    "concesi",
]

KEYWORDS_EXCLUIR = [
    "modificaci", "nombramiento", "cese", "oposici",
    "licitaci", "contrato", "adjudicaci",
    "becas de formaci", "master", "investigador",
    "autonomo", "personas fisicas", "persona fisica",
    "ciudadanos", "estudiantes",
    "correccion de errores", "correccion de errata",
    "sindicato", "sindicatos",
    "formacion profesional para el empleo",
    "compromiso de contratacion",
    "personas trabajadoras desempleadas",
    "accion concertada", "prorrog",
    "relacion de subvenciones concedidas",
    "subvenciones concedidas",
    "empresas", "pymes", "emprendedores",
    "agricultores", "ganaderos",
    "pruebas selectivas", "proceso selectivo",
    "plazas convocadas", "oferta de empleo",
]

def descargar(url):
    if SCRAPER_KEY:
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_KEY}&url={requests.utils.quote(url, safe='')}"
        r = requests.get(proxy_url, timeout=60)
    else:
        r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r

def get_bocm_info():
    hoy = date.today()
    fecha_str = hoy.strftime("%Y%m%d")
    try:
        r = descargar(f"{BASE_URL}/ultimo-bocm")
        m = re.search(r'bocm-(\d{8})-(\d+)', r.url + r.text.lower())
        if m:
            return m.group(1), m.group(2), hoy.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error obteniendo info BOCM: {e}")
    return fecha_str, None, hoy.strftime("%Y-%m-%d")

def get_numero_bocm(fecha_str, fecha_iso):
    try:
        r = descargar(f"{BASE_URL}/boletin/bocm-{fecha_str.lower()}-141")
        m = re.search(r'bocm-\d{8}-(\d+)', r.url)
        if m:
            return m.group(1)
    except:
        pass
    try:
        r = descargar(f"{BASE_URL}/ultimo-bocm")
        m = re.search(r'bocm-\d{8}-(\d+)', r.text.lower())
        if m:
            return m.group(1)
    except:
        pass
    return None

def scrape_bocm(fecha_str, numero, fecha_iso):
    xml_url = f"{BASE_URL}/boletin/CM_Boletin_BOCM/{fecha_str[:4]}/{fecha_str[4:6]}/{fecha_str[6:8]}/BOCM-{fecha_str}{numero}.xml"
    print(f"Descargando XML BOCM: {xml_url}")
    try:
        r = descargar(xml_url)
    except Exception as e:
        print(f"Error descargando XML BOCM: {e}")
        return []

    try:
        root = etree.fromstring(r.content)
    except Exception as e:
        print(f"Error parseando XML BOCM: {e}")
        return []

    convocatorias = []
    for elem in root.iter():
        titulo = (elem.text or "").strip()
        if not titulo or len(titulo) < 20:
            continue

        titulo_norm = titulo.lower().encode('ascii', 'ignore').decode()
        if not any(k in titulo_norm for k in KEYWORDS_POSITIVAS):
            continue
        if any(k in titulo_norm for k in KEYWORDS_EXCLUIR):
            continue

        cve = elem.get('cve', elem.get('id', ''))
        id_bocm = f"BOCM-{fecha_str}-{cve or len(convocatorias)+1}"
        url_doc = f"{BASE_URL}/boletin-completo/{cve}" if cve else xml_url

        convocatorias.append({
            "id_boe":  id_bocm,
            "titulo":  titulo[:500],
            "fecha":   fecha_iso,
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
    result = client.table("subvenciones").upsert(items, on_conflict="id_boe").execute()
    print(f"Guardadas {len(result.data)} convocatorias del BOCM.")

if __name__ == "__main__":
    hoy = date.today()
    fecha_str = hoy.strftime("%Y%m%d")
    fecha_iso = hoy.strftime("%Y-%m-%d")
    fecha_str2, numero, _ = get_bocm_info()
    if not numero:
        numero = get_numero_bocm(fecha_str, fecha_iso)
    if not numero:
        print("No se pudo determinar el número del BOCM.")
    else:
        print(f"Scrapeando BOCM {numero} de {fecha_iso}...")
        items = scrape_bocm(fecha_str, numero, fecha_iso)
        print(f"BOCM: {len(items)} convocatorias.")
        guardar(items)
