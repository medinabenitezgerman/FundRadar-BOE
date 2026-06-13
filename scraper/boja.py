import os
import re
import requests
from datetime import date
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

KEYWORDS_POSITIVAS = [
    "subvención", "subvenciones", "ayuda", "ayudas",
    "convocatoria de subvenciones", "convocatoria de ayudas",
    "concesión de subvenciones", "concesión de ayudas",
]

KEYWORDS_EXCLUIR = [
    "modificación", "nombramiento", "cese", "oposición",
    "concurso", "licitación", "contrato", "adjudicación",
    "plaza", "puesto", "funcionario", "personal",
    "becas de formación", "máster", "investigador",
    "autónomo", "personas físicas", "ciudadanos",
]

SECCIONES_VALIDAS = ["1", "3", "5.2"]

def numero_boja_hoy():
    hoy = date.today()
    url = f"https://www.juntadeandalucia.es/eboja/{hoy.year}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    enlaces = soup.find_all('a', href=re.compile(r'/eboja/\d{4}/\d+/index\.html'))
    if not enlaces:
        return None
    ultimo = enlaces[-1]['href']
    m = re.search(r'/eboja/\d{4}/(\d+)/index\.html', ultimo)
    return int(m.group(1)) if m else None

def obtener_numero_boja(fecha_str):
    anyo = fecha_str[:4]
    url = f"https://www.juntadeandalucia.es/eboja/{anyo}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    enlaces = soup.find_all('a', href=re.compile(r'/eboja/\d{4}/\d+/index\.html'))
    for e in reversed(enlaces):
        if fecha_str.replace('-', '/')[5:] in e.text or fecha_str in e.get('href', ''):
            m = re.search(r'/eboja/\d{4}/(\d+)/index\.html', e['href'])
            if m:
                return int(m.group(1))
    return None

def scrape_boja(numero, anyo):
    url_index = f"https://www.juntadeandalucia.es/eboja/{anyo}/{numero}/index.html"
    print(f"Descargando BOJA {numero} de {anyo}...")
    r = requests.get(url_index, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    convocatorias = []
    seccion_actual = None

    for elem in soup.find_all(['h2', 'h3', 'p', 'li']):
        texto = elem.get_text(strip=True)

        if elem.name in ['h2', 'h3']:
            for s in SECCIONES_VALIDAS:
                if texto.startswith(s + '.') or texto.startswith(s + ' '):
                    seccion_actual = s
                    break
            if texto.startswith('2.') or texto.startswith('4.') or texto.startswith('5.1'):
                seccion_actual = None
            continue

        if not seccion_actual:
            continue

        titulo_lower = texto.lower()
        if not any(k in titulo_lower for k in KEYWORDS_POSITIVAS):
            continue
        if any(k in titulo_lower for k in KEYWORDS_EXCLUIR):
            continue

        enlace = elem.find('a')
        url_html = None
        if enlace and enlace.get('href'):
            href = enlace['href']
            if href.startswith('/boja/'):
                url_html = f"https://www.juntadeandalucia.es{href}"
            elif href.startswith('http'):
                url_html = href

        num_disp = None
        if url_html:
            m = re.search(r'/boja/\d{4}/\d+/(\d+)', url_html)
            if m:
                num_disp = m.group(1)

        id_boja = f"BOJA-{anyo}-{numero}-{num_disp or len(convocatorias)+1}"

        convocatorias.append({
            "id_boe":   id_boja,
            "titulo":   texto[:500],
            "fecha":    f"{anyo}-{str(numero).zfill(3)}",
            "url_pdf":  url_html,
            "materia":  seccion_actual,
            "fuente":   "BOJA",
        })

    return convocatorias

def guardar(items):
    if not items:
        print("No hay convocatorias nuevas del BOJA.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = (
        client.table("subvenciones")
        .upsert(items, on_conflict="id_boe")
        .execute()
    )
    print(f"Guardadas {len(result.data)} convocatorias del BOJA.")

if __name__ == "__main__":
    anyo = date.today().year
    numero = numero_boja_hoy()
    if not numero:
        print("No se encontró el número del BOJA de hoy.")
    else:
        items = scrape_boja(numero, anyo)
        print(f"Encontradas {len(items)} convocatorias relevantes en BOJA {numero}.")
        guardar(items)
