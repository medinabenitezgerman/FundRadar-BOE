SECCIONES_VALIDAS = ["5B"]

KEYWORDS = [
    "extracto", "convocatoria", "convoca", "subvención", "subvenciones",
    "ayuda", "ayudas", "beca", "becas", "financiación",
]

def es_relevante(titulo: str, materia: str, seccion: str = "") -> bool:
    if seccion not in SECCIONES_VALIDAS:
        return False
    titulo_lower = titulo.lower()
    return any(k in titulo_lower for k in KEYWORDS)
