import os
import re
import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SCRAPER_KEY  = os.environ["SCRAPER_API_KEY"]

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

def extraer_fecha_cierre(html):
    patrones = [
        r'plazo[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'hasta el\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'fecha l[íi]mite[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'presentaci[oó]n[^.]*?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
    ]
    MESES = {'enero':'01','febrero':'02','marzo':'03','abril':'04','mayo':'05','junio':'06',
             'julio':'07','agosto':'08','septiembre':'09','octubre':'10','noviembre':'11','diciembre':'12'}
    texto = html.lower()
    for p in patrones:
        m = re.search(p, texto)
        if m:
            fecha_str = m.group(1)
            if '/' in fecha_str:
                partes = fecha_str.split('/')
                if len(partes) == 3:
                    return f"{partes[2]}-{partes[1].zfill(2)}-{partes[0].zfill(2)}"
            else:
                partes = fecha_str.split()
                if len(partes) >= 5:
                    mes = MESES.get(partes[2], None)
                    if mes:
                        return f"{partes[4]}-{mes}-{partes[0].zfill(2)}"
    return None

def extraer_importe(html):
    patrones = [
        r'importe[^.]*?([\d.,]+)\s*euros',
        r'dotaci[oó]n[^.]*?([\d.,]+)\s*euros',
        r'cuant[íi]a[^.]*?([\d.,]+)\s*euros',
        r'presupuesto[^.]*?([\d.,]+)\s*euros',
        r'([\d.,]+)\s*euros',
    ]
    texto = html.lower()
    for p in patrones:
        m = re.search(p, texto)
        if m:
            importe = m.group(1).replace('.', '').replace(',', '.')
            try:
                valor = float(importe)
                if valor > 100:
                    return f"Dotación total: {valor:,.0f} € (ver PDF para máximo por entidad)".replace(',', '.')
            except:
                pass
    return "Ver PDF para más información"

def descargar_html(id_boe):
    url_html = f"https://www.boe.es/diario_boe/txt.php?id={id_boe}"
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_KEY}&url={requests.utils.quote(url_html, safe='')}"
    r = requests.get(proxy_url, timeout=30)
    r.raise_for_status()
    return r.text

def main():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    registros = (
        client.table("subvenciones")
        .select("id, id_boe, titulo, materia, organismo")
        .execute()
    )

    print(f"Enriqueciendo {len(registros.data)} registros...")

    for r in registros.data:
        try:
            texto_base = f"{r['titulo']} {r['materia'] or ''}".lower()
            datos = {
                "organismo":    r.get("organismo") or r.get("materia") or "Administración General del Estado",
                "ambito":       detectar_ambito(texto_base),
                "ccaa":         detectar_ccaa(texto_base),
                "ods":          detectar_ods(texto_base),
                "descripcion":  r["titulo"][:200],
                "importe":      "Ver PDF para más información",
                "fecha_cierre": None,
            }

            try:
                html = descargar_html(r["id_boe"])
                fecha = extraer_fecha_cierre(html)
                importe = extraer_importe(html)
                if fecha:
                    datos["fecha_cierre"] = fecha
                datos["importe"] = importe
                print(f"✓ {r['id_boe']} — fecha: {fecha or 'no encontrada'} — importe: {importe}")
            except Exception as e:
                print(f"  HTML no disponible para {r['id_boe']}: {e}")

            client.table("subvenciones").update(datos).eq("id", r["id"]).execute()

        except Exception as e:
            print(f"✗ Error en {r.get('id_boe')}: {e}")

if __name__ == "__main__":
    main()
