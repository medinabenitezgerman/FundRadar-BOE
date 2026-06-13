import os
import requests
from datetime import date
from lxml import etree
from supabase import create_client
from filter import es_relevante

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

def descargar_boe(fecha):
    # API oficial del BOE
    url = f"https://boe.es/datosabiertos/api/boletines/diarios/{fecha[:4]}/{fecha[4:6]}/{fecha[6:]}"
    print(f"Descargando BOE del {fecha}...")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()

def extraer_subvenciones(datos, fecha):
    encontradas = []
    items = datos.get("data", {}).get("sumario", {}).get("diario", {}).get("seccion", [])
    if not isinstance(items, list):
        items = [items]
    for seccion in items:
        departamentos = seccion.get("departamento", [])
        if not isinstance(departamentos, list):
            departamentos = [departamentos]
        for dep in departamentos:
            epigrafe = dep.get("epigrafe", [])
            if not isinstance(epigrafe, list):
                epigrafe = [epigrafe]
            for ep in epigrafe:
                items_ep = ep.get("item", [])
                if not isinstance(items_ep, list):
                    items_ep = [items_ep]
                for item in items_ep:
                    titulo  = item.get("titulo", "")
                    id_boe  = item.get("id", "")
                    url_pdf = item.get("url_pdf", "")
                    materia = ep.get("nombre", "")
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
    hoy = "20260612"
    datos = descargar_boe(hoy)
    items = extraer_subvenciones(datos, hoy)
    print(f"Encontradas {len(items)} convocatorias relevantes.")
    guardar(items)
