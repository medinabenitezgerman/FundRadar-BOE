-- schema.sql
-- Ejecuta esto UNA SOLA VEZ en el SQL Editor de tu proyecto Supabase
-- (supabase.com → tu proyecto → SQL Editor → New query → pega esto → Run)

create table if not exists subvenciones (
  id         bigint generated always as identity primary key,
  id_boe     text unique not null,          -- evita duplicados
  titulo     text not null,
  fecha      date not null,
  url_pdf    text,
  materia    text,
  created_at timestamptz default now()
);

-- Índice para búsquedas rápidas por texto
create index if not exists idx_subvenciones_texto
  on subvenciones using gin(to_tsvector('spanish', titulo));

-- Índice para filtrar por fecha
create index if not exists idx_subvenciones_fecha
  on subvenciones (fecha desc);

-- Seguridad: cualquier persona puede leer (para el frontend de Fundradar)
alter table subvenciones enable row level security;

create policy "Lectura pública"
  on subvenciones for select
  using (true);
