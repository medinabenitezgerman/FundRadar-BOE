import os
import requests
from datetime import date
from lxml import etree
from supabase import create_client
from filter import es_relevante

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

def descargar_boe(fecha):
    url = f"https://www.boe.es/diario_boe/xml.php?id=BOE-S-{fecha}"
    print(f"Descargando BOE del {fecha}...")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def extraer_subvenciones(xml_bytes, fecha):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml_bytes, parser=parser)
    encontradas = []
    for item in root.findall(".//item"):
        titulo  = item.findtext("titulo",        default="")
        id_boe  = item.findtext("identificador", default="")
        url_pdf = item.findtext("urlPdf",        default="")
        materia = item.findtext("materia",       default="")
        if not id_boe:
            continue
        if es_relevante(titulo, materia):
            encontradas.append({
                "id_boe":  id_boe,
                "titulo":  titulo,
                "fecha":   fecha,
                "url_pdf": f"https://www.boe.es{url_pdf}" if url_pdf else None,
                "materia": materia,
            })
    return encontradas

def guardar(subvenciones):
    if not subvenciones:
        print("No hay convocatorias nuevas hoy.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = (
        client.table("subvenciones")
        .upsert(subvenciones, on_conflict="id_boe")
        .execute()
    )
    print(f"Guardadas {len(result.data)} convocatorias.")

if __name__ == "__main__":
    hoy = date.today().strftime("%Y%m%d")
    xml   = descargar_boe(hoy)
    items = extraer_subvenciones(xml, hoy)
    print(f"Encontradas {len(items)} convocatorias relevantes.")
    guardar(items)
