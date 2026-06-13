SECCIONES_VALIDAS = ["5B"]

KEYWORDS_POSITIVAS = [
    "extracto de resolución",
    "extracto de la resolución",
    "extracto de orden",
    "extracto de la orden",
    "subvención", "subvenciones",
    "ayuda", "ayudas",
    "convocatoria de subvenciones",
    "convocatoria de ayudas",
]

KEYWORDS_ENTIDADES = [
    "entidad", "entidades", "asociación", "asociaciones",
    "fundación", "fundaciones", "ong", "ongd",
    "organización no gubernamental", "organizaciones no gubernamentales",
    "sin ánimo de lucro", "tercer sector", "cooperativa",
    "corporación", "federación", "confederación",
    "organizaciones", "instituciones", "colectivo",
    "sector pesquero", "sector agrario", "sector social",
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
    "emprendedores",
    "startups",
    "pymes",
    "empresas",
    "autónomos",
]

def es_relevante(titulo: str, materia: str, seccion: str = "") -> bool:
    if seccion not in SECCIONES_VALIDAS:
        return False

    titulo_lower = titulo.lower()

    if any(k in titulo_lower for k in KEYWORDS_EXCLUIR):
        return False

    if not any(k in titulo_lower for k in KEYWORDS_POSITIVAS):
        return False

    return True
