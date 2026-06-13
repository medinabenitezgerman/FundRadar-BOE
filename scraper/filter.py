SECCIONES_VALIDAS = ["5B"]

KEYWORDS_POSITIVAS = [
    "subvención", "subvenciones",
    "ayuda", "ayudas",
    "beca", "becas",
    "convocatoria",
    "concesión",
    "financiación",
]

KEYWORDS_EXCLUIR = [
    "modificación del extracto",
    "extracto de modificación",
    "segunda modificación",
    "tercera modificación",
    "modificación de la convocatoria",
    "jóvenes con titulación",
    "titulados universitarios",
    "personas físicas",
    "digitalización",
    "transformación digital",
    "sectores productivos",
    "next generation",
    "plan de recuperación",
    "becas de formación",
    "máster universitario",
    "investigadores",
    "estancias de investigación",
    "contratos predoctorales",
    "contratos postdoctorales",
    "erasmus",
    "startups",
    "pymes",
    "autónomos",
]

def es_relevante(titulo: str, materia: str, seccion: str = "") -> bool:
    if seccion not in SECCIONES_VALIDAS:
        return False
    titulo_lower = titulo.lower()
    if any(k in titulo_lower for k in KEYWORDS_EXCLUIR):
        return False
    return any(k in titulo_lower for k in KEYWORDS_POSITIVAS)
