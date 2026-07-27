# Arquitectura — VACUNACION Plataforma Digital

## Propósito
Plataforma ciudadana de información, orientación general y acceso territorial a la vacunación.

## Límites
No es historia clínica, carnet digital, sistema de turnos, registro nominal, herramienta diagnóstica ni motor de decisión clínica.

## Principios
- Información clara, verificable y versionada.
- Orientación basada en reglas revisadas por personas.
- Ninguna inferencia sobre vacunas faltantes.
- Privacidad por diseño.
- Objetivo WCAG 2.2 AA.
- Arquitectura modular y API-first.
- Mantener la estética aprobada.

## Capas
- Presentación: Streamlit.
- Componentes: `src/components`.
- Configuración: `src/config`.
- Modelos: `src/models`.
- Datos temporales: `src/data`.
- Persistencia futura: PostgreSQL/PostGIS.
- Interoperabilidad futura: API y preparación FHIR.

## Flujo Git
- `main`: estable.
- `develop`: integración.
- `feature/*`: funcionalidades.
- `fix/*`: correcciones.

## Estados editoriales
`draft -> review -> approved -> published -> archived`
