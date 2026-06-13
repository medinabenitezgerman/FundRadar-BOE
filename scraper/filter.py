SECCIONES_VALIDAS = ["5B", "3"]

KEYWORDS = [
    "subvención", "subvenciones", "convocatoria", "ayuda", "ayudas",
    "beca", "becas", "financiación", "sin ánimo de lucro", "ong",
    "asociación", "asociaciones", "fundación", "fundaciones",
    "tercer sector", "acción social", "cooperación", "voluntariado",
    "inclusión", "discapacidad", "mayores", "infancia", "juventud",
    "igualdad", "violencia de género", "inserción laboral",
    "empleo social", "servicios sociales", "dependencia",
    "refugiados", "migrantes", "cultura", "deporte", "medioambiente",
    "educación", "formación", "investigación", "desarrollo rural",
    "pobreza", "exclusión social", "vulnerab", "colectivo", "extracto",
]

def es_relevante(titulo: str, materia: str, seccion: str = "") -> bool:
    if seccion and seccion not in SECCIONES_VALIDAS:
        return False
    titulo_lower = titulo.lower()
    return any(k in titulo_lower for k in KEYWORDS)
