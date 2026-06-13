SECCIONES_VALIDAS = ["5B"]

KEYWORDS_POSITIVAS = [
    "extracto", "subvención", "subvenciones",
    "ayuda económica", "ayudas económicas",
    "beca", "becas", "financiación",
    "convocatoria de subvenciones", "convocatoria de ayudas",
    "concesión de subvenciones", "concesión de ayudas",
]

KEYWORDS_NEGATIVAS = [
    "regantes", "junta general", "junta ordinaria", "junta extraordinaria",
    "asamblea", "licitación", "formalización de contratos",
    "enajenación", "subasta", "concesión administrativa",
    "información pública", "extravío", "título universitario",
]

def es_relevante(titulo: str, materia: str, seccion: str = "") -> bool:
    if seccion not in SECCIONES_VALIDAS:
        return False
    titulo_lower = titulo.lower()
    if any(k in titulo_lower for k in KEYWORDS_NEGATIVAS):
        return False
    return any(k in titulo_lower for k in KEYWORDS_POSITIVAS)
