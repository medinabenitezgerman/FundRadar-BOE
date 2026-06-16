import os
import re
import requests
from datetime import date
from lxml import etree
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
    "pruebas selectivas", "proceso selectivo",
    "plazas convocadas", "oferta de empleo",
]

def get_bocm_url():
    hoy = date.today()
    fecha_str = hoy.strftime("%Y%m%d")
    url_main = f"{BASE_URL}/boletin/bocm-{fecha_str.lower()}-"
    try:
        r = requests.get(f"{BASE_URL}/ultimo-bocm", timeout=20)
        r.raise_for_status()
        m = re.search(r'bocm-(\d{8})-(\d+)', r.url + r.text.lower())
        if m:
            fecha = m.group(1)
            numero = m.group(2)
            xml_url = f"{BASE_URL}/boletin/CM_Boletin_BOCM/{fecha[:4]}/{fecha[4:6]}/{fecha[6:8]}/BOCM-{fecha}{numero}.xml"
            return xml_url, hoy.strftime("%Y-%m-%d"), numero
    except Exception as e:
        print(f"Error obteniendo BOCM: {e}")
    return None, None, None

def scrape_bocm_xml(xml_url, fecha, numero):
    try:
        r = requests.get(xml_url, timeout=30)
        r.raise_for_status()
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
        titulo = elem.text or ""
        if not titulo or len(titulo) < 20:
            continue

        titulo_lower = titulo.lower()
        if not any(k in titulo_lower for k in KEYWORDS_POSITIVAS):
            continue
        if any(k in titulo_lower for k in KEYWORDS_EXCLUIR):
            continue

        cve = elem.get('cve', elem.get('id', f"BOCM-{fecha.replace('-','')}-{len(convocatorias)+1}"))
        id_bocm = f"BOCM-{cve}" if not cve.startswith('BOCM') else cve
        url_doc = f"{BASE_URL}/boletin-completo/{cve}" if cve else xml_url

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
    xml_url, fecha, numero = get_bocm_url()
    if not xml_url:
        fecha = date.today().strftime("%Y-%m-%d")
        fecha_str = fecha.replace("-", "")
        xml_url = f"{BASE_URL}/boletin/CM_Boletin_BOCM/{fecha[:4]}/{fecha[5:7]}/{fecha[8:10]}/BOCM-{fecha_str}141.xml"
        numero = "141"
        print(f"Usando URL directa: {xml_url}")

    print(f"Scrapeando BOCM {numero} de {fecha}...")
    items = scrape_bocm_xml(xml_url, fecha, numero)
    print(f"BOCM: {len(items)} convocatorias relevantes.")
    guardar(items)
