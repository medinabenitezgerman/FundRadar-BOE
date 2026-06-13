import os
import requests
from datetime import date
from lxml import etree
from supabase import create_client
from filter import es_relevante

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SCRAPER_KEY  = os.environ["SCRAPER_API_KEY"]

HISTORICO = [
    "20260401","20260402","20260403","20260404",
    "20260407","20260408","20260409","20260410","20260411",
    "20260414","20260415","20260416","20260417","20260418",
    "20260421","20260422","20260423","20260424","20260425",
    "20260428","20260429","20260430",
    "20260504","20260505","20260506","20260507","20260508",
    "20260511","20260512","20260513","20260514","20260515",
    "20260518","20260519","20260520","20260521","20260522",
    "20260526","20260527","20260528","20260529",
    "20260602","20260603","20260604","20260605","20260606",
    "20260609","20260610","20260611","20260612",
]

def descargar_boe(fecha):
    url_boe = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"
    url = f"http://api.scraperapi.com?api_key={SCRAPER_KEY}&url={requests.utils.quote(url_boe, safe='')}"
    print(f"Descargando BOE del {fecha}...")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content

def extraer_subvenciones(xml_bytes, fecha):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml_bytes, parser=parser)
    encontradas = []
    for seccion in root.findall(".//seccion"):
        codigo = seccion.get("codigo", "")
        for item in seccion.findall(".//item"):
            titulo   = item.findtext("titulo",        default="")
            id_boe   = item.findtext("identificador", default="")
            url_pdf  = item.findtext("url_pdf",       default="")
            epigrafe = item.getparent()
            materia  = epigrafe.get("nombre", "") if epigrafe is not None else ""
            if not id_boe:
                continue
            if es_relevante(titulo, materia, codigo):
                encontradas.append({
                    "id_boe":  id_boe,
                    "titulo":  titulo,
                    "fecha":   fecha,
                    "url_pdf": url_pdf if url_pdf else None,
                    "materia": materia,
                })
    return encontradas

def guardar(subvenciones):
    if not subvenciones:
        print("No hay convocatorias nuevas.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = (
        client.table("subvenciones")
        .upsert(subvenciones, on_conflict="id_boe")
        .execute()
    )
    print(f"Guardadas {len(result.data)} convocatorias.")

if __name__ == "__main__":
    for hoy in HISTORICO:
        try:
            xml   = descargar_boe(hoy)
            items = extraer_subvenciones(xml, hoy)
            print(f"{hoy}: {len(items)} convocatorias relevantes.")
            guardar(items)
        except Exception as e:
            print(f"{hoy}: error — {e}")
