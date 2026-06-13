import os
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

ODS_KEYWORDS = {
    "1":  ["pobreza", "exclusión social", "vulnerable"],
    "2":  ["alimentación", "hambre", "agricultura", "pesca"],
    "3":  ["salud", "sanitario", "adicciones", "drogas", "mental"],
    "4":  ["educación", "formación", "escolar", "universitario", "becas"],
    "5":  ["igualdad", "mujer", "género", "violencia de género", "feminismo"],
    "6":  ["agua", "saneamiento", "hidráulico"],
    "7":  ["energía", "renovable", "solar", "eólico"],
    "8":  ["empleo", "trabajo", "inserción laboral", "economía social"],
    "9":  ["innovación", "investigación", "tecnología", "digital"],
    "10": ["desigualdad", "migrantes", "refugiados", "inclusión", "discapacidad"],
    "11": ["vivienda", "urbanismo", "desarrollo urbano", "transporte"],
    "12": ["consumo", "residuos", "reciclaje"],
    "13": ["clima", "medioambiente", "cambio climático", "emisiones"],
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
    "Galicia": ["galicia", "galleg", "coruña", "vigo", "pontevedra", "lugo", "ourense"],
    "País Vasco": ["euskadi", "vasco", "bilbao", "donostia", "vitoria", "bizkaia", "gipuzkoa", "araba"],
    "Castilla y León": ["castilla y león", "burgos", "salamanca", "valladolid", "zamora", "soria", "segovia", "ávila", "palencia", "león"],
    "Aragón": ["aragón", "zaragoza", "huesca", "teruel"],
    "Canarias": ["canarias", "canario", "tenerife", "palmas", "lanzarote", "fuerteventura"],
    "Murcia": ["murcia"],
    "Navarra": ["navarra", "navarro"],
    "Extremadura": ["extremadura", "badajoz", "cáceres"],
    "Asturias": ["asturias", "asturiano"],
    "Baleares": ["baleares", "mallorca", "menorca", "ibiza"],
    "Cantabria": ["cantabria", "cantábrico"],
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
    ods = []
    for num, keywords in ODS_KEYWORDS.items():
        if any(k in texto for k in keywords):
            ods.append(num)
    return ",".join(ods) if ods else "17"

def detectar_ccaa(texto):
    texto = texto.lower()
    for ccaa, keywords in CCAA_KEYWORDS.items():
        if any(k in texto for k in keywords):
            return ccaa
    return "Nacional"

def detectar_ambito(texto):
    texto = texto.lower()
    for ambito, keywords in AMBITO_KEYWORDS.items():
        if any(k in texto for k in keywords):
            return ambito
    return "General"

def detectar_organismo(materia):
    if not materia:
        return "Administración General del Estado"
    return materia

def enriquecer(titulo, materia):
    texto = f"{titulo} {materia or ''}".lower()
    return {
        "organismo":    detectar_organismo(materia),
        "ambito":       detectar_ambito(texto),
        "ccaa":         detectar_ccaa(texto),
        "importe":      "No especificado",
        "fecha_cierre": None,
        "ods":          detectar_ods(texto),
        "descripcion":  titulo[:200],
    }

def main():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    registros = (
        client.table("subvenciones")
        .select("id, titulo, materia")
        .is_("organismo", "null")
        .execute()
    )

    print(f"Enriqueciendo {len(registros.data)} registros...")

    for r in registros.data:
        try:
            datos = enriquecer(r["titulo"], r["materia"] or "")
            client.table("subvenciones").update(datos).eq("id", r["id"]).execute()
            print(f"✓ {r['id']} — {r['titulo'][:60]}")
        except Exception as e:
            print(f"✗ {r['id']} — Error: {e}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
