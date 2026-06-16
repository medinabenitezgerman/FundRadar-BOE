import os
import re
import requests
from datetime import datetime, timedelta
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

MESES = {
    'enero':'01','febrero':'02','marzo':'03','abril':'04',
    'mayo':'05','junio':'06','julio':'07','agosto':'08',
    'septiembre':'09','octubre':'10','noviembre':'11','diciembre':'12'
}

ODS_KEYWORDS = {
    "1":  ["pobreza", "exclusion social", "vulnerable"],
    "2":  ["alimentacion", "hambre", "agricultura", "pesca"],
    "3":  ["salud", "sanitario", "adicciones", "drogas", "mental"],
    "4":  ["educacion", "formacion", "escolar", "universitario"],
    "5":  ["igualdad", "mujer", "genero", "violencia de genero"],
    "6":  ["agua", "saneamiento"],
    "7":  ["energia", "renovable", "solar", "eolico"],
    "8":  ["empleo", "trabajo", "insercion laboral", "economia social"],
    "9":  ["innovacion", "investigacion", "tecnologia"],
    "10": ["desigualdad", "migrantes", "refugiados", "inclusion", "discapacidad"],
    "11": ["vivienda", "urbanismo", "desarrollo urbano"],
    "12": ["consumo", "residuos", "reciclaje"],
    "13": ["clima", "medioambiente", "cambio climatico"],
    "14": ["marino", "oceano", "costas", "pesca maritima"],
    "15": ["biodiversidad", "bosques", "fauna", "flora", "rural"],
    "16": ["paz", "justicia", "derechos humanos", "cooperacion", "democracia"],
    "17": ["alianzas", "cooperacion internacional"],
}

AMBITO_KEYWORDS = {
    "Social": ["social", "inclusion", "discapacidad", "mayores", "infancia", "juventud", "dependencia", "pobreza"],
    "Educacion": ["educacion", "formacion", "escolar", "universitario", "ensenanza"],
    "Cultura": ["cultura", "cultural", "patrimonio", "arte", "cine", "audiovisual"],
    "Cooperacion internacional": ["cooperacion internacional", "humanitaria", "desarrollo", "aecid"],
    "Medioambiente": ["medioambiente", "medio ambiente", "clima", "biodiversidad", "rural"],
    "Deporte": ["deporte", "deportivo", "actividad fisica"],
    "Salud": ["salud", "sanitario", "adicciones", "drogas"],
    "Empleo": ["empleo", "trabajo", "insercion laboral", "economia social"],
    "Investigacion": ["investigacion", "innovacion", "ciencia", "tecnologia"],
    "Igualdad": ["igualdad", "mujer", "genero", "violencia de genero"],
}

REGION_A_CCAA = {
    "ES11": "Galicia", "ES12": "Asturias", "ES13": "Cantabria",
    "ES21": "Pais Vasco", "ES22": "Navarra", "ES23": "La Rioja", "ES24": "Aragon",
    "ES30": "Madrid", "ES41": "Castilla y Leon", "ES42": "Castilla-La Mancha",
    "ES43": "Extremadura", "ES51": "Cataluna", "ES52": "Valencia", "ES53": "Baleares",
    "ES61": "Andalucia", "ES62": "Murcia", "ES63": "Ceuta", "ES64": "Melilla",
    "ES70": "Canarias",
}

def detectar_ods(texto):
    norm = texto.lower().encode('ascii', 'ignore').decode()
    ods = [n for n, kws in ODS_KEYWORDS.items() if any(k in norm for k in kws)]
    return ",".join(ods) if ods else "17"

def detectar_ambito(texto):
    norm = texto.lower().encode('ascii', 'ignore').decode()
    for ambito, kws in AMBITO_KEYWORDS.items():
        if any(k in norm for k in kws):
            return ambito
    return "General"

def region_a_ccaa(codigo):
    prefijo = codigo[:4].upper()
    return REGION_A_CCAA.get(prefijo, None)

def fecha_a_iso(texto):
    texto = texto.strip().lower()
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', texto)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    partes = texto.split()
    if len(partes) >= 5 and partes[1] == 'de' and partes[3] == 'de':
        mes = MESES.get(partes[2])
        if mes:
            return f"{partes[4]}-{mes}-{partes[0].zfill(2)}"
    return None

def fecha_valida(fecha_iso, fecha_pub):
    if not fecha_iso or not fecha_pub:
        return False
    try:
        return datetime.strptime(fecha_iso, "%Y-%m-%d") >= datetime.strptime(fecha_pub, "%Y-%m-%d")
    except:
        return False

def calcular_dias_habiles(fecha_pub, dias):
    try:
        actual = datetime.strptime(fecha_pub, "%Y-%m-%d") + timedelta(days=1)
        habiles = 0
        while habiles < dias:
            if actual.weekday() < 5:
                habiles += 1
            actual += timedelta(days=1)
        return actual.strftime("%Y-%m-%d")
    except:
        return None

def extraer_datos_bdns(bdns_id, fecha_pub):
    url = f"https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{bdns_id}"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        html = r.text
    except:
        return {}, fecha_pub, None, None

    texto = html.lower()
    datos = {}

    m = re.search(r'presupuesto total[^<]{0,50}?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\s*[€e]', texto)
    if m:
        try:
            valor = float(m.group(1).replace('.', '').replace(',', '.'))
            if valor > 0:
                datos['importe'] = f"{valor:,.0f} euros".replace(',', '.')
        except:
            pass

    m = re.search(r'regi[oó]n de impacto[^<]{0,50}?(es\d+)', texto)
    if m:
        ccaa = region_a_ccaa(m.group(1).upper())
        if ccaa:
            datos['ccaa'] = ccaa

    if 'ccaa' not in datos:
        if 'estatal' in texto[:2000]:
            datos['ccaa'] = 'Nacional'

    fecha_fin = None
    m = re.search(r'(\d+)\s+d[ií]as?\s+h[áa]biles?\s+(?:a partir|contados?|desde|a contar)', texto)
    if m:
        fecha_fin = calcular_dias_habiles(fecha_pub, int(m.group(1)))

    patrones_fin = [
        r'hasta el\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'(\d{2}/\d{2}/\d{4})',
    ]
    if not fecha_fin:
        for p in patrones_fin:
            m = re.search(p, texto)
            if m:
                f = fecha_a_iso(m.group(1))
                if fecha_valida(f, fecha_pub):
                    fecha_fin = f
                    break

    fecha_ejec = None
    m = re.search(r'31\s+de\s+diciembre\s+de\s+(\d{4})', texto)
    if m:
        f = f"{m.group(1)}-12-31"
        if fecha_valida(f, fecha_pub):
            fecha_ejec = f

    organismo_parts = []
    for nivel in ['nivel1', 'nivel2', 'nivel3']:
        m = re.search(rf'{nivel}["\s:]+([^"<,\n]+)', html)
        if m:
            organismo_parts.append(m.group(1).strip())
    if not organismo_parts:
        m = re.search(r'ayuntamiento[^<"]{0,80}', texto)
        if m:
            organismo_parts.append(m.group(0).strip().title())
    if organismo_parts:
        datos['organismo'] = ' - '.join(organismo_parts)[:200]

    return datos, fecha_pub, fecha_fin, fecha_ejec

def main():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    registros = client.table("subvenciones").select(
        "id, id_boe, titulo, materia, fecha, bdns_id, organismo, ccaa"
    ).execute()

    sin_enriquecer = [r for r in registros.data if not r.get("organismo")]
    print(f"Enriqueciendo {len(sin_enriquecer)} registros...")

    for r in sin_enriquecer:
        try:
            texto_base = f"{r['titulo']} {r['materia'] or ''}"
            fecha_pub = r.get("fecha") or ""

            datos_base = {
                "organismo":           r.get("materia") or "—",
                "ambito":              detectar_ambito(texto_base),
                "ccaa":                r.get("ccaa") or "Nacional",
                "ods":                 detectar_ods(texto_base),
                "descripcion":         r["titulo"][:200],
                "importe":             "Ver convocatoria",
                "fecha_inicio":        fecha_pub,
                "fecha_fin_solicitud": None,
                "fecha_fin_ejecucion": None,
            }

            bdns_id = r.get("bdns_id")
            if bdns_id:
                datos_bdns, f_ini, f_fin, f_ejec = extraer_datos_bdns(bdns_id, fecha_pub)
                if datos_bdns.get("organismo"):
                    datos_base["organismo"] = datos_bdns["organismo"]
                if datos_bdns.get("importe"):
                    datos_base["importe"] = datos_bdns["importe"]
                if datos_bdns.get("ccaa"):
                    datos_base["ccaa"] = datos_bdns["ccaa"]
                if f_fin:
                    datos_base["fecha_fin_solicitud"] = f_fin
                if f_ejec:
                    datos_base["fecha_fin_ejecucion"] = f_ejec
                print(f"OK {r['id_boe']} ccaa:{datos_base['ccaa']} imp:{datos_base['importe'][:20]}")

            client.table("subvenciones").update(datos_base).eq("id", r["id"]).execute()

        except Exception as e:
            print(f"ERROR {r.get('id_boe')}: {e}")

if __name__ == "__main__":
    main()
