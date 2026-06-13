# filter.py — detecta si una convocatoria es relevante para el tercer sector

KEYWORDS = [
    "subvención", "convocatoria", "ayuda", "beca",
    "sin ánimo de lucro", "ong", "asociación", "fundación",
    "tercer sector", "acción social", "cooperación",
    "voluntariado", "inclusión social", "discapacidad",
    "mayores", "infancia", "juventud", "igualdad",
    "violencia de género", "inserción laboral", "empleo social",
    "servicios sociales", "dependencia", "refugiados", "migrantes",
]

MATERIAS = [
    "asistencia social", "cooperación internacional",
    "educación", "empleo", "igualdad", "juventud",
    "sanidad", "servicios sociales", "derechos sociales",
]

def es_relevante(titulo: str, materia: str) -> bool:
    titulo_lower  = titulo.lower()
    materia_lower = materia.lower()
    return (
        any(k in titulo_lower  for k in KEYWORDS) or
        any(m in materia_lower for m in MATERIAS)
    )
