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
    "persona física",
    "ciudadanos",
    "trabajadores",
    "empleados",
    "funcionarios",
    "estudiantes",
    "investigadores",
    "becarios",
    "digitalización",
    "transformación digital",
    "sectores productivos",
    "next generation",
    "plan de recuperación",
    "máster universitario",
    "contratos predoctorales",
    "contratos postdoctorales",
    "erasmus",
    "autónomos",
    "concesión administrativa",
    "aprovechamiento",
    "dominio público",
    "canon",
    "obra",
    "licitación",
    "concurso de acceso",
    "proveer plaza",
    "proveer puesto",
    "oposición",
    "movilidad educativa",
    "movilidad del personal",
    "retorno voluntario",
    "ayudas individuales",
    "ayuda individual",
    "subvenciones individuales",
    "subvención individual",
    "familias",
    "propietarios",
    "inquilinos",
    "agricultores",
    "ganaderos",
    "pescadores",
    "armadores",
    "relación de subvenciones concedidas",
    "subvenciones concedidas",
    "se hace pública la relación",
    "se acuerda modificar la resolución",
    "corrección de errores",
    "corrección de errata",
    "corrección de error",
]

def es_relevante(titulo: str, materia: str, seccion: str = "") -> bool:
    if seccion not in SECCIONES_VALIDAS:
        return False
    titulo_lower = titulo.lower()
    if any(k in titulo_lower for k in KEYWORDS_EXCLUIR):
        return False
    return any(k in titulo_lower for k in KEYWORDS_POSITIVAS)
