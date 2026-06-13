SECCIONES_VALIDAS = ["5B"]

KEYWORDS_POSITIVAS = [
    "subvención", "subvenciones",
    "ayuda", "ayudas",
    "convocatoria de subvenciones",
    "convocatoria de ayudas",
    "concesión de subvenciones",
    "concesión de ayudas",
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
    "máster universitario",
    "investigadores",
    "contratos predoctorales",
    "contratos postdoctorales",
    "erasmus",
    "autónomos",
    "concesión administrativa",
    "aprovechamiento",
    "dominio público",
    "canon",
    "tarifa",
    "obra",
    "licitación",
    "contrato",
    "concurso de acceso",
    "proveer",
    "plaza",
    "puesto de trabajo",
    "oposicion",
    "oposición",
]

def es_relevante(titulo: str, materia: str, seccion: str = "") -> bool:
    if seccion not in SECCIONES_VALIDAS:
        return False
    titulo_lower = titulo.lower()
    if any(k in titulo_lower for k in KEYWORDS_EXCLUIR):
        return False
    return any(k in titulo_lower for k in KEYWORDS_POSITIVAS)
