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
    "1":  ["pobreza", "exclusión social", "vulnerable"],
    "2":  ["alimentación", "hambre", "agricultura", "pesca"],
    "3":  ["salud", "sanitario", "adicciones", "drogas", "mental"],
    "4":  ["educación", "formación", "escolar", "universitario"],
    "5":  ["igualdad", "mujer", "género", "violencia de género"],
    "6":  ["agua", "saneamiento"],
    "7":  ["energía", "renovable", "solar", "eólico"],
    "8":  ["empleo", "trabajo", "inserción laboral", "economía social"],
    "9":  ["innovación", "investigación", "tecnología"],
    "10": ["desigualdad", "migrantes", "refugiados", "inclusión", "discapacidad"],
    "11": ["vivienda", "urbanismo", "desarrollo urbano"],
    "12": ["consumo", "residuos", "reciclaje"],
    "13": ["clima", "medioambiente", "cambio climático"],
    "14": ["marino", "océano", "costas", "pesca marítima"],
    "15": ["biodiversidad", "bosques", "fauna", "flora", "rural"],
    "16": ["paz", "justicia", "derechos humanos", "cooperación", "democracia"],
    "17": ["alianzas", "cooperación internacional"],
}

CCAA_KEYWORDS = {
    "Andalucía": ["andaluc", "sevilla", "málaga", "granada", "córdoba", "huelva", "jaén", "almería", "cádiz"],
    "Madrid": ["madrid"],
    "Cataluña": ["cataluña", "catalunya", "barcelona", "girona", "lleida", "tarragona"],
    "Valencia": ["valencia", "valenciana", "alicante", "castellón"],
    "Galicia": ["galicia", "coruña", "vigo", "pontevedra", "lugo", "ourense"],
    "País Vasco": ["euskadi", "vasco", "bilbao", "donostia", "vitoria"],
    "Castilla y León": ["castilla y león", "burgos", "salamanca", "valladolid"],
    "Aragón": ["aragón", "zaragoza", "huesca", "teruel"],
    "Canarias": ["canarias", "tenerife", "palmas"],
    "Murcia": ["murcia"],
    "Navarra": ["navarra"],
    "Extremadura": ["extremadura", "badajoz", "cáceres"],
    "Asturias": ["asturias"],
    "Baleares": ["baleares", "mallorca"],
    "Cantabria": ["cantabria"],
    "La Rioja": ["rioja"],
    "Ceuta": ["ceuta"],
    "Melilla": ["melilla"],
}

AMBITO_KEYWORDS = {
    "Social": ["social", "inclusión", "discapacidad", "mayores", "infancia", "juventud", "dependencia", "pobreza"],
    "Educación": ["educación", "formación", "escolar", "universitario", "enseñanza"],
    "Cultura": ["cultura", "cultural", "patrimonio", "arte", "cine", "audiovisual"],
    "Cooperación internacional": ["cooperación internacional", "humanitaria", "desarrollo", "aecid"],
    "Medioambiente": ["medioambiente", "medio ambiente", "clima", "biodiversidad", "rural"],
    "Deporte": ["deporte", "deportivo", "actividad física"],
    "Salud": ["salud", "sanitario", "adicciones", "drogas"],
    "Empleo": ["empleo", "trabajo", "inserción laboral", "economía social"],
    "Investigación": ["investigación", "innovación", "ciencia", "tecnología"],
    "Igualdad": ["igualdad", "mujer", "género", "violencia de género"],
}

def detectar_ods(texto):
    texto = texto.lower()
    ods = [n for n, kws in ODS_KEYWORDS.items() if any(k in texto for k in kws)]
    return ",".join(ods) if ods else "17"

def detectar_ccaa(texto):
    texto = texto.lower()
    for ccaa, kws in CCAA_KEYWORDS.items():
        if any(k in texto for k in kws):
            return ccaa
    return "Nacional"

def detectar_ambito(texto):
    texto = texto.lower()
    for ambito, kws in AMBITO_KEYWORDS.items():
        if any(k in texto for k in kws):
            return ambito
    return "General"

def fecha_a_iso(texto):
    texto = texto.strip().lower()
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
        return None, None, None, None

    texto = html.lower()
    fecha_fin = None
    fecha_ejec = None
    importe = None
    organismo = None

    m = re.search(r'órgano[^<]*</th>\s*<td[^>]*>([^<]+)</td>', texto)
    if m:
        organismo = m.group(1).strip()

    patrones_importe = [
        r'importe[^<]*?(\d[\d.,]+)\s*euros',
        r'dotaci[oó]n[^<]*?(\d[\d.,]+)\s*euros',
        r'cuant[íi]a[^<]*?(\d[\d.,]+)\s*euros',
        r'(\d[\d.,]+)\s*euros',
    ]
    for p in patrones_importe:
        m = re.search(p, texto)
        if m:
            try:
                valor = float(m.group(1).replace('.', '').replace(',', '.'))
                if valor > 100:
                    importe = f"Dotación total: {valor:,.0f} €".replace(',', '.')
                    break
            except:
                pass

    patrones_fin = [
        r'hasta el\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'fecha l[íi]mite[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'plazo[^.]*?finaliza[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
    ]
    for p in patrones_fin:
        m = re.search(p, texto)
        if m:
            f = fecha_a_iso(m.group(1))
            if fecha_valida(f, fecha_pub):
                fecha_fin = f
                break

    if not fecha_fin:
        m = re.search(r'(\d+)\s+d[íi]as?\s+h[áa]biles?\s+(?:a partir|contados?|desde)', texto)
        if m:
            fecha_fin = calcular_dias_habiles(fecha_pub, int(m.group(1)))

    patrones_ejec = [
        r'31\s+de\s+diciembre\s+de\s+(\d{4})',
        r'ejecuci[oó]n[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
    ]
    for p in patrones_ejec:
        m = re.search(p, texto)
        if m:
            g = m.group(1)
            f = f"{g}-12-31" if len(g) == 4 else fecha_a_iso(g)
            if fecha_valida(f, fecha_pub):
                fecha_ejec = f
                break

    return organismo, importe, fecha_fin, fecha_ejec

def main():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    registros = client.table("subvenciones").select(
        "id, id_boe, titulo, materia, fecha, fuente, url_pdf, bdns_id, organismo, ccaa"
    ).execute()

    sin_enriquecer = [r for r in registros.data if not r.get("organismo")]
    print(f"Enriqueciendo {len(sin_enriquecer)} registros...")

    for r in sin_enriquecer:
        try:
            texto_base = f"{r['titulo']} {r['materia'] or ''}".lower()
            fecha_pub = r.get("fecha") or ""

            datos = {
                "organismo":           r.get("materia") or "—",
                "ambito":              detectar_ambito(texto_base),
                "ccaa":                r.get("ccaa") or detectar_ccaa(texto_base),
                "ods":                 detectar_ods(texto_base),
                "descripcion":         r["titulo"][:200],
                "importe":             "Ver convocatoria para más información",
                "fecha_inicio":        fecha_pub,
                "fecha_fin_solicitud": None,
                "fecha_fin_ejecucion": None,
            }

            bdns_id = r.get("bdns_id")
            if bdns_id:
                organismo, importe, f_fin, f_ejec = extraer_datos_bdns(bdns_id, fecha_pub)
                if organismo:
                    datos["organismo"] = organismo
                if importe:
                    datos["importe"] = importe
                if f_fin:
                    datos["fecha_fin_solicitud"] = f_fin
                if f_ejec:
                    datos["fecha_fin_ejecucion"] = f_ejec
                print(f"✓ {r['id_boe']} — fin: {f_fin} ejec: {f_ejec}")

            client.table("subvenciones").update(datos).eq("id", r["id"]).execute()

        except Exception as e:
            print(f"✗ Error {r.get('id_boe')}: {e}")

if __name__ == "__main__":
    main()
