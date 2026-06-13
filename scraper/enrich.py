import os
import json
import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

def enriquecer(titulo, materia):
    prompt = f"""Analiza esta convocatoria del BOE y extrae la información en JSON.

Título: {titulo}
Materia: {materia}

Devuelve SOLO un JSON válido con estos campos (sin texto adicional, sin markdown):
{{
  "organismo": "nombre del organismo convocante",
  "ambito": "tipo de actividad (social, educación, cultura, cooperación, medioambiente, deporte, salud, etc)",
  "ccaa": "comunidad autónoma o 'Nacional' si es para toda España",
  "importe": "importe máximo si aparece, si no 'No especificado'",
  "fecha_cierre": null,
  "ods": "números ODS relacionados separados por comas (ej: 1,3,10)",
  "descripcion": "descripción breve de 1-2 frases de qué financia esta convocatoria"
}}"""

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    r.raise_for_status()
    texto = r.json()["content"][0]["text"].strip()
    return json.loads(texto)

def main():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    registros = (
        client.table("subvenciones")
        .select("id, titulo, materia")
        .is_("organismo", "null")
        .execute()
    )

    print(f"Enriqueciendo {len(registros.data)} registros...")

    for r in registros.data:
        try:
            datos = enriquecer(r["titulo"], r["materia"] or "")
            client.table("subvenciones").update({
                "organismo":    datos.get("organismo"),
                "ambito":       datos.get("ambito"),
                "ccaa":         datos.get("ccaa"),
                "importe":      datos.get("importe"),
                "fecha_cierre": datos.get("fecha_cierre"),
                "ods":          datos.get("ods"),
                "descripcion":  datos.get("descripcion"),
            }).eq("id", r["id"]).execute()
            print(f"✓ {r['id']} — {r['titulo'][:60]}")
        except Exception as e:
            print(f"✗ {r['id']} — Error: {e}")

if __name__ == "__main__":
    main()
