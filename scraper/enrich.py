import os
import re
import requests
from datetime import date, timedelta, datetime
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SCRAPER_KEY  = os.environ["SCRAPER_API_KEY"]

MESES = {
    'enero':'01','febrero':'02','marzo':'03','abril':'04',
    'mayo':'05','junio':'06','julio':'07','agosto':'08',
    'septiembre':'09','octubre':'10','noviembre':'11','diciembre':'12'
}

ODS_KEYWORDS = {
    "1":  ["pobreza", "exclusión social", "vulnerable"],
    "2":  ["alimentación", "hambre", "agricultura", "pesca"],
    "3":  ["salud", "sanitario", "adicciones", "drogas", "mental"],
    "4":  ["educación", "formación", "escolar", "universitario", "becas"],
    "5":  ["igualdad", "mujer", "género", "violencia de género"],
    "6":  ["agua", "saneamiento", "hidráulico"],
    "7":  ["energía", "renovable", "solar", "eólico"],
    "8":  ["empleo", "trabajo", "inserción laboral", "economía social"],
    "9":  ["innovación", "investigación", "tecnología", "digital"],
    "10": ["desigualdad", "migrantes", "refugiados", "inclusión", "discapacidad"],
    "11": ["vivienda", "urbanismo", "desarrollo urbano", "transporte"],
    "12": ["consumo", "residuos", "reciclaje"],
    "13": ["clima", "medioambiente", "cambio climático"],
    "14": ["marino", "océano", "costas", "pesca marítima"],
    "15": ["biodiversidad", "bosques", "fauna", "flora", "rural"],
    "16": ["paz", "justicia", "derechos humanos", "cooperación", "democracia"],
    "17": ["alianzas", "cooperación internacional", "desarrollo sostenible"],
}

CCAA_KEYWORDS = {
    "Andalucía": ["andaluc", "sevilla", "málaga", "granada", "córdoba", "huelva", "jaén", "almería", "cádiz"],
    "Madrid": ["madrid"],
    "Cataluña": ["cataluña", "catalunya", "barcelona", "girona", "lleida", "tarragona"],
    "Valencia": ["valencia", "valenciana", "alicante", "castellón"],
    "Galicia": ["galicia", "coruña", "vigo", "pontevedra", "lugo", "ourense"],
    "País Vasco": ["euskadi", "vasco", "bilbao", "donostia", "vitoria", "bizkaia", "gipuzkoa"],
    "Castilla y León": ["castilla y león", "burgos", "salamanca", "valladolid", "zamora", "soria", "segovia", "ávila", "palencia", "león"],
    "Aragón": ["aragón", "zaragoza", "huesca", "teruel"],
    "Canarias": ["canarias", "tenerife", "palmas", "lanzarote"],
    "Murcia": ["murcia"],
    "Navarra": ["navarra"],
    "Extremadura": ["extremadura", "badajoz", "cáceres"],
    "Asturias": ["asturias"],
    "Baleares": ["baleares", "mallorca", "menorca", "ibiza"],
    "Cantabria": ["cantabria"],
    "La Rioja": ["rioja"],
    "Ceuta": ["ceuta"],
    "Melilla": ["melilla"],
}

AMBITO_KEYWORDS = {
    "Social": ["social", "inclusión", "discapacidad", "mayores", "infancia", "juventud", "dependencia", "pobreza"],
    "Educación": ["educación", "formación", "escolar", "universitario", "becas", "enseñanza"],
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
    if '/' in texto:
        partes = texto.split('/')
        if len(partes) == 3:
            return f"{partes[2].strip()}-{partes[1].strip().zfill(2)}-{partes[0].strip().zfill(2)}"
    partes = texto.split()
    if len(partes) >= 5 and partes[1] == 'de' and partes[3] == 'de':
        mes = MESES.get(partes[2])
        if mes:
            return f"{partes[4]}-{mes}-{partes[0].zfill(2)}"
    return None

def fecha_valida(fecha_iso, fecha_publicacion):
    if not fecha_iso or not fecha_publicacion:
        return False
    try:
        f = datetime.strptime(fecha_iso, "%Y-%m-%d")
        p = datetime.strptime(fecha_publicacion, "%Y-%m-%d")
        return f >= p
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

def extraer_fechas(html, fecha_publicacion):
    texto = html.lower()
    bdns_id = None
    fecha_inicio = fecha_publicacion
    fecha_fin_solicitud = None
    fecha_fin_ejecucion = None

    m = re.search(r'bdns\s*\(?identif\.?\)?\s*:?\s*(\d+)', texto)
    if m:
        bdns_id = m.group(1)

    patrones_fin = [
        r'hasta el\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'fecha l[íi]mite[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'plazo[^.]*?finaliza[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'terminar[áa]\s+el\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
    ]
    for p in patrones_fin:
        m = re.search(p, texto)
        if m:
            f = fecha_a_iso(m.group(1))
            if fecha_valida(f, fecha_publicacion):
                fecha_fin_solicitud = f
                break

    if not fecha_fin_solicitud:
        m = re.search(r'(\d+)\s+d[íi]as?\s+h[áa]biles?\s+(?:a partir|contados?|desde)', texto)
        if not m:
            m = re.search(r'plazo\s+de\s+(\d+)\s+d[íi]as?\s+h[áa]biles?', texto)
        if m:
            dias = int(m.group(1))
            fecha_fin_solicitud = calcular_dias_habiles(fecha_publicacion, dias)

    patrones_ejecucion = [
        r'ejecuci[oó]n[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'31\s+de\s+diciembre\s+de\s+(\d{4})',
        r'hasta el\s+31\s+de\s+diciembre\s+de\s+(\d{4})',
        r'justificaci[oó]n[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
    ]
    for p in patrones_ejecucion:
        m = re.search(p, texto)
        if m:
            g = m.group(1)
            if len(g) == 4:
                f = f"{g}-12-31"
            else:
                f = fecha_a_iso(g)
            if fecha_valida(f, fecha_publicacion):
                fecha_fin_ejecucion = f
                break

    return bdns_id, fecha_inicio, fecha_fin_solicitud, fecha_fin_ejecucion

def extraer_importe(html):
    patrones = [
        r'importe[^.]*?([\d.,]+)\s*euros',
        r'dotaci[oó]n[^.]*?([\d.,]+)\s*euros',
        r'cuant[íi]a[^.]*?([\d.,]+)\s*euros',
        r'presupuesto[^.]*?([\d.,]+)\s*euros',
        r'([\d.,]+)\s*euros',
    ]
    for p in patrones:
        m = re.search(p, html.lower())
        if m:
            try:
                valor = float(m.group(1).replace('.', '').replace(',', '.'))
                if valor > 100:
                    return f"Dotación total: {valor:,.0f} €".replace(',', '.')
            except:
                pass
    return "Ver PDF para más información"

def descargar_html(id_boe):
    url = f"https://www.boe.es/diario_boe/txt.php?id={id_boe}"
    proxy = f"http://api.scraperapi.com?api_key={SCRAPER_KEY}&url={requests.utils.quote(url, safe='')}"
    r = requests.get(proxy, timeout=30)
    r.raise_for_status()
    return r.text

def main():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    registros = client.table("subvenciones").select("id, id_boe, titulo, materia, fecha").execute()
    print(f"Enriqueciendo {len(registros.data)} registros...")

    for r in registros.data:
        try:
            texto_base = f"{r['titulo']} {r['materia'] or ''}".lower()
            fecha_pub = r.get("fecha") or ""

            datos = {
                "organismo":           r.get("materia") or "Administración General del Estado",
                "ambito":              detectar_ambito(texto_base),
                "ccaa":                detectar_ccaa(texto_base),
                "ods":                 detectar_ods(texto_base),
                "descripcion":         r["titulo"][:200],
                "importe":             "Ver PDF para más información",
                "fecha_inicio":        fecha_pub,
                "fecha_fin_solicitud": None,
                "fecha_fin_ejecucion": None,
                "bdns_id":             None,
            }

            try:
                html = descargar_html(r["id_boe"])
                bdns, f_ini, f_fin, f_ejec = extraer_fechas(html, fecha_pub)
                importe = extraer_importe(html)
                datos.update({
                    "bdns_id":             bdns,
                    "fecha_inicio":        f_ini or fecha_pub,
                    "fecha_fin_solicitud": f_fin,
                    "fecha_fin_ejecucion": f_ejec,
                    "importe":             importe,
                })
                print(f"✓ {r['id_boe']} — fin: {f_fin} ejec: {f_ejec}")
            except Exception as e:
                print(f"  Sin HTML para {r['id_boe']}: {e}")

            client.table("subvenciones").update(datos).eq("id", r["id"]).execute()

        except Exception as e:
            print(f"✗ Error {r.get('id_boe')}: {e}")

if __name__ == "__main__":
    main()
