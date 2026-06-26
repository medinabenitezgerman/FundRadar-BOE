import os
import requests
from datetime import date
from lxml import etree
from supabase import create_client
from filter import es_relevante

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/xml, text/xml, */*",
}

def descargar_boe(fecha):
    url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"
    print(f"Descargando BOE del {fecha}...")
    r = requests.get(url, headers=HEADERS, timeout=60)
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
                    "fuente":  "BOE",
                })
    return encontradas

def guardar(subvenciones):
    if not subvenciones:
        print("No hay convocatorias nuevas del BOE.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = (
        client.table("subvenciones")
        .upsert(subvenciones, on_conflict="id_boe")
        .execute()
    )
    print(f"Guardadas {len(result.data)} convocatorias del BOE.")

if __name__ == "__main__":
    hoy       = date.today().strftime("%Y%m%d")
    fecha_iso = date.today().strftime("%Y-%m-%d")
    try:
        xml   = descargar_boe(hoy)
        items = extraer_subvenciones(xml, fecha_iso)
        print(f"{hoy}: {len(items)} convocatorias relevantes.")
        guardar(items)
    except Exception as e:
        print(f"{hoy}: error — {e}")
