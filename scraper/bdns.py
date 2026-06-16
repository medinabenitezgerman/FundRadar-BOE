import os
import requests
from datetime import date, timedelta
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

BASE_URL = "https://www.infosubvenciones.es/bdnstrans/api"

KEYWORDS_POSITIVAS = [
    "subvención", "subvenciones", "ayuda", "ayudas",
    "convocatoria de subvenciones", "convocatoria de ayudas",
    "concesión de subvenciones", "concesión de ayudas",
]

KEYWORDS_EXCLUIR = [
    "modificación", "nombramiento", "cese", "oposición",
    "licitación", "contrato", "adjudicación",
    "becas de formación", "máster", "investigador",
    "autónomo", "personas físicas", "ciudadanos",
    "corrección de errores", "corrección de errata",
    "sindicato", "sindicatos", "organizaciones sindicales",
    "formación profesional para el empleo",
    "compromiso de contratación",
    "personas trabajadoras desempleadas",
    "acción concertada", "prórroga", "prorroga",
    "autorización para la prestación",
    "relación de subvenciones concedidas",
    "subvenciones concedidas",
    "se hace pública la relación",
]

def es_relevante(titulo):
    titulo_lower = titulo.lower()
    if any(k in titulo_lower for k in KEYWORDS_EXCLUIR):
        return False
    return any(k in titulo_lower for k in KEYWORDS_POSITIVAS)

def descargar_convocatorias(fecha_desde, fecha_hasta, page=0, page_size=100):
    url = f"{BASE_URL}/convocatorias"
    params = {
        "fechaDesde": fecha_desde,
        "fechaHasta": fecha_hasta,
        "page": page,
        "pageSize": page_size,
    }
    headers = {"Accept": "application/json"}
    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def guardar(items):
    if not items:
        print("No hay convocatorias nuevas de la BDNS.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = (
        client.table("subvenciones")
        .upsert(items, on_conflict="id_boe")
        .execute()
    )
    print(f"Guardadas {len(result.data)} convocatorias de la BDNS.")

def main():
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    fecha_desde = ayer.strftime("%d/%m/%Y")
    fecha_hasta = hoy.strftime("%d/%m/%Y")

    print(f"Descargando convocatorias BDNS del {fecha_desde} al {fecha_hasta}...")

    try:
        data = descargar_convocatorias(fecha_desde, fecha_hasta)
        print(f"Respuesta BDNS: {type(data)}")
        print(f"Primeros datos: {str(data)[:500]}")

        if isinstance(data, list):
            convocatorias = data
        elif isinstance(data, dict):
            convocatorias = data.get("content", data.get("data", data.get("items", [])))
        else:
            print("Formato desconocido")
            return

        print(f"Total encontradas: {len(convocatorias)}")

        items = []
        for c in convocatorias:
            titulo = c.get("titulo", c.get("descripcion", c.get("title", "")))
            if not titulo or not es_relevante(titulo):
                continue

            bdns_id = str(c.get("id", c.get("codigo", c.get("bdns", ""))))
            id_boe = f"BDNS-{bdns_id}"
            fecha = c.get("fechaRegistro", c.get("fecha", hoy.strftime("%Y-%m-%d")))
            if fecha and "/" in str(fecha):
                partes = str(fecha).split("/")
                if len(partes) == 3:
                    fecha = f"{partes[2]}-{partes[1].zfill(2)}-{partes[0].zfill(2)}"

            organismo = c.get("organo", c.get("organismo", c.get("departamento", "")))
            ccaa = c.get("administracion", c.get("ccaa", "Nacional"))
            url_pdf = f"https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{bdns_id}"

            items.append({
                "id_boe":   id_boe,
                "titulo":   titulo[:500],
                "fecha":    fecha[:10] if fecha else hoy.strftime("%Y-%m-%d"),
                "url_pdf":  url_pdf,
                "materia":  organismo[:200] if organismo else "",
                "fuente":   "BDNS",
                "bdns_id":  bdns_id,
                "ccaa":     ccaa,
            })

        print(f"Convocatorias relevantes: {len(items)}")
        if items:
            guardar(items)
        else:
            print("Ninguna pasó el filtro.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
