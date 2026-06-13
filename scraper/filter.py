KEYWORDS = [
    "subvención", "subvenciones", "convocatoria", "ayuda", "ayudas",
    "beca", "becas", "grant", "financiación", "financiamiento",
    "sin ánimo de lucro", "ong", "asociación", "asociaciones",
    "fundación", "fundaciones", "tercer sector", "entidad sin ánimo",
    "acción social", "cooperación", "voluntariado", "inclusión",
    "discapacidad", "mayores", "infancia", "juventud", "igualdad",
    "violencia de género", "inserción laboral", "empleo social",
    "servicios sociales", "dependencia", "refugiados", "migrantes",
    "cultura", "deporte", "medioambiente", "medio ambiente",
    "educación", "formación", "investigación", "innovación social",
    "desarrollo rural", "comunidad", "vecinal", "barrio",
    "sanitario", "salud", "mental", "adicciones", "pobreza",
    "exclusión social", "vulnerab", "colectivo", "minorías",
]

MATERIAS = [
    "subvenciones", "ayudas", "asistencia social",
    "cooperación internacional", "educación", "empleo",
    "igualdad", "juventud", "sanidad", "servicios sociales",
    "derechos sociales", "cultura", "deporte", "medio ambiente",
    "desarrollo rural", "vivienda", "investigación",
]

def es_relevante(titulo: str, materia: str) -> bool:
    titulo_lower  = titulo.lower()
    materia_lower = materia.lower()
    return (
        any(k in titulo_lower  for k in KEYWORDS) or
        any(m in materia_lower for m in MATERIAS)
    )
