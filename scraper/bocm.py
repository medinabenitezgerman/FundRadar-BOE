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
    "subvenci", "convocatoria de ayuda", "convocatoria de subvenci",
    "bases reguladoras", "fondo social", "programa de ayuda",
]

KEYWORDS_EXCLUIR = [
    "proceso selectivo", "pruebas selectivas", "plazas convocadas",
    "oferta de empleo", "oposici",
    "nombramiento", "cese",
    "licitaci", "contrato", "adjudicaci",
    "modificaci",
    "corrección de errores", "correccion de errores",
    "subvenciones concedidas", "relacion de subvenciones",
    "prorrog",
    "autonomo", "autónomo", "persona fisica", "personas fisicas",
    "empresas", "pymes", "emprendedor",
    "agricultor", "ganadero",
    "sindicato",
    "formacion profesional para el empleo",
    "personas trabajadoras desempleadas",
    "accion concertada",
]

def normalizar(texto):
    t = texto.lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ü","u"),("ñ","n")]:
        t = t.replace(a, b)
    return t

def es_relevante(titulo):
    n = normalizar(titulo)
    if not any(k in n for k in KEYWORDS_POSITIVAS):
        return False
    if any(k in n for k in KEYWORDS_EXCLUIR):
        return False
    return True

def descargar(url):
    if SCRAPER_KEY:
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_KEY}&url={requests.utils.quote(url, safe='')}"
        r = requests.get(proxy_url, timeout=60)
    else:
        r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r

def get_numero_bocm(fecha_str):
    hoy = date.today()
    dia_anio = hoy.timetuple().tm_yday
    anio, mes, dia = fecha_str[:4], fecha_str[4:6], fecha_str[6:8]
    for offset in range(-3, 4):
        numero = str(dia_anio + offset).zfill(3)
        url = f"{BASE_URL}/boletin/CM_Boletin_BOCM/{anio}/{mes}/{dia}/BOCM-{fecha_str}{numero}.xml"
        try:
            r = descargar(url)
            if r.status_code == 200 and b"<sumario>" in r.content[:500]:
                print(f"[BOCM] Boletín número {numero} encontrado.")
                return numero
        except:
            pass
    return None

def scrape_bocm(fecha_str, numero, fecha_iso):
    anio, mes, dia = fecha_str[:4], fecha_str[4:6], fecha_str[6:8]
    xml_url = f"{BASE_URL}/boletin/CM_Boletin_BOCM/{anio}/{mes}/{dia}/BOCM-{fecha_str}{numero}.xml"
    print(f"[BOCM] Descargando: {xml_url}")

    try:
        r = descargar(xml_url)
        root = etree.fromstring(r.content)
    except Exception as e:
        print(f"[BOCM] Error: {e}")
        return []

    convocatorias = []

    for disp in root.findall(".//disposicion"):
        titulo_el = disp.find("titulo")
        if titulo_el is None or not titulo_el.text:
            continue

        titulo = titulo_el.text.strip()
        if not es_relevante(titulo):
            continue

        identificador_el = disp.find("identificador")
        id_bocm = identificador_el.text.strip() if identificador_el is not None else f"BOCM-{fecha_str}-{disp.get('numero','?')}"

        url_pdf_el = disp.find("url_pdf")
        url_pdf = url_pdf_el.text.strip() if url_pdf_el is not None else xml_url

        organismo = ""
        padre = disp.getparent()
        while padre is not None:
            if padre.tag == "organismo":
                organismo = padre.get("nombre", "")
                break
            padre = padre.getparent()

        convocatorias.append({
            "id_boe":    id_bocm,
            "titulo":    titulo[:500],
            "fecha":     fecha_iso,
            "url_pdf":   url_pdf,
            "fuente":    "BOCM",
            "ccaa":      "Madrid",
            "organismo": organismo,
            "ambito":    "autonómico",
        })

    print(f"[BOCM] {len(convocatorias)} convocatorias relevantes.")
    return convocatorias

def guardar(items):
    if not items:
        print("[BOCM] Nada que guardar.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.table("subvenciones").upsert(items, on_conflict="id_boe").execute()
    print(f"[BOCM] Guardadas {len(result.data)} filas.")

if __name__ == "__main__":
    hoy = date.today()
    fecha_str = hoy.strftime("%Y%m%d")
    fecha_iso = hoy.strftime("%Y-%m-%d")
    numero = get_numero_bocm(fecha_str)
    if not numero:
        print("[BOCM] No se encontró el boletín de hoy.")
    else:
        items = scrape_bocm(fecha_str, numero, fecha_iso)
        guardar(items)
