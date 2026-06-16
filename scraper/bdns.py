import os
import json
import subprocess
from datetime import date
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

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

NIVEL1_A_CCAA = {
    "AUTONOMICA": None,
    "ESTATAL": "Nacional",
    "LOCAL": None,
    "OTROS": None,
    "UE": "Nacional",
}

def es_relevante(titulo):
    t = titulo.lower()
    if any(k in t for k in KEYWORDS_EXCLUIR):
        return False
    return any(k in t for k in KEYWORDS_POSITIVAS)

def main():
    hoy = date.today()

    print("Instalando bdns-fetch...")
    subprocess.run(["pip", "install", "bdns-fetch", "--break-system-packages", "-q"], check=True)

    print("Descargando últimas convocatorias BDNS...")
    result = subprocess.run(
        ["bdns-fetch", "--output-file", "/tmp/bdns_convocatorias.jsonl", "convocatorias-ultimas"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error bdns-fetch: {result.stderr}")
        return

    convocatorias = []
    try:
        with open("/tmp/bdns_convocatorias.jsonl", "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    convocatorias.append(json.loads(line))
    except FileNotFoundError:
        print("No se generó el archivo.")
        return

    print(f"Total descargadas: {len(convocatorias)}")

    items = []
    for c in convocatorias:
        titulo = c.get("descripcion", "")
        if not titulo or not es_relevante(titulo):
            continue

        bdns_id = str(c.get("numeroConvocatoria", c.get("id", "")))
        id_boe = f"BDNS-{bdns_id}"
        fecha = str(c.get("fechaRecepcion", hoy.strftime("%Y-%m-%d")))[:10]
        organismo = c.get("nivel2", c.get("nivel1", ""))
        nivel1 = c.get("nivel1", "")
        ccaa = NIVEL1_A_CCAA.get(nivel1, nivel1)
        url_pdf = f"https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{bdns_id}"

        items.append({
            "id_boe":  id_boe,
            "titulo":  titulo[:500],
            "fecha":   fecha,
            "url_pdf": url_pdf,
            "materia": str(organismo)[:200] if organismo else "",
            "fuente":  "BDNS",
            "bdns_id": bdns_id,
            "ccaa":    str(ccaa) if ccaa else "Nacional",
        })

    print(f"Convocatorias relevantes: {len(items)}")

    if not items:
        print("Ninguna pasó el filtro.")
        return

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.table("subvenciones").upsert(items, on_conflict="id_boe").execute()
    print(f"Guardadas {len(result.data)} convocatorias de la BDNS.")

if __name__ == "__main__":
    main()
"actividades deportivas",
    "deporte de base",
    "cheque",
    "bono",
    "voucher",
    "ticket",
    "empresas",
    "pymes",
    "autónomos",
    "emprendedores",
    "agricultores",
    "ganaderos",
    "pescadores",
    "personas físicas",
    "persona física",
    "estudiantes",
    "becas",
    "investigadores",
