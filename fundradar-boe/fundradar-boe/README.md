# Fundradar — Scraper del BOE

Recoge subvenciones del BOE cada mañana, filtra las relevantes para el tercer sector y las guarda en Supabase. Todo gratis, sin instalar nada en tu ordenador.

---

## Cómo ponerlo en marcha (30 minutos, paso a paso)

### Paso 1 — Crear la base de datos en Supabase

1. Ve a **supabase.com** y crea una cuenta gratuita
2. Crea un nuevo proyecto (elige región "West EU")
3. Una vez creado, ve al menú lateral → **SQL Editor** → **New query**
4. Copia y pega todo el contenido del archivo `supabase/schema.sql`
5. Haz clic en **Run** — verás que aparece la tabla `subvenciones`

### Paso 2 — Copiar las credenciales de Supabase

1. En Supabase, ve a **Settings** (engranaje) → **API**
2. Copia estos dos valores y guárdalos en algún sitio:
   - **Project URL** (algo como `https://xxxx.supabase.co`)
   - **anon public key** (una cadena larga de letras y números)

### Paso 3 — Subir el código a GitHub

1. Ve a **github.com** y crea una cuenta si no tienes
2. Crea un repositorio nuevo: **New repository** → ponle nombre `fundradar-boe` → **Create**
3. Sube todos estos archivos tal cual están (puedes usar el botón "uploading an existing file")

### Paso 4 — Añadir las credenciales a GitHub (de forma segura)

1. En tu repositorio de GitHub, ve a **Settings** → **Secrets and variables** → **Actions**
2. Haz clic en **New repository secret** y añade estos dos:
   - Nombre: `SUPABASE_URL` → Valor: la Project URL del paso 2
   - Nombre: `SUPABASE_KEY` → Valor: la anon public key del paso 2

### Paso 5 — Ejecutar por primera vez

1. Ve a la pestaña **Actions** de tu repositorio
2. Verás el workflow "Scraper BOE - Fundradar"
3. Haz clic en **Run workflow** → **Run workflow** (botón verde)
4. En un minuto verás si ha funcionado (tick verde) o ha fallado (cruz roja)

### Paso 6 — Verificar que hay datos

1. Vuelve a Supabase → **Table Editor** → `subvenciones`
2. Deberías ver filas con convocatorias del BOE de hoy

A partir de aquí el scraper corre solo cada mañana a las 10:00 (España). Los logs están siempre disponibles en la pestaña Actions de GitHub.

---

## Estructura de archivos

```
fundradar-boe/
├── .github/
│   └── workflows/
│       └── scraper.yml     ← el cron job (no tocar)
├── scraper/
│   ├── main.py             ← script principal
│   └── filter.py           ← keywords del tercer sector (personalizable)
└── supabase/
    └── schema.sql          ← estructura de la base de datos
```

---

## Personalizar el filtro

Edita el archivo `scraper/filter.py` para añadir o quitar keywords según los tipos de entidades que quieras detectar en Fundradar.
