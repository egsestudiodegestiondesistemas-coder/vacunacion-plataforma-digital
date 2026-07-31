from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Dict, List
from urllib.parse import quote_plus
import hashlib
import math
import re
import secrets
import string

import folium
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation


st.set_page_config(
    page_title="VACUNACIÓN | Plataforma Oficial",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_NAME = "VACUNACIÓN"
APP_SUBTITLE = "Plataforma Oficial"
APP_SLOGAN = "Información oficial para una vacunación en cada etapa de la vida."
DEVELOPER = "EGS | Estudio de Gestión de Sistemas"
AUTO_REFRESH_SECONDS = 21600
LAST_CONTENT_REVIEW = "28/07/2026"

CORDOBA_VACCINATION_URL = "https://vacunacion.cba.gov.ar/Vacunas"
MI_ARGENTINA_URL = "https://www.argentina.gob.ar/miargentina"
SIGIPSA_URL = "https://www.sigipsa.com.ar/"
NOMIVAC_URL = "https://sisa.msal.gov.ar/"
SUPABASE_REQUESTS_TABLE = "access_requests"
SUPABASE_USERS_TABLE = "institutional_users"
SUPABASE_AUDIT_TABLE = "audit_log"
SUPABASE_CITIZENS_TABLE = "citizens"
SUPABASE_VACCINATION_RECORDS_TABLE = "vaccination_records"

if "section" not in st.session_state:
    st.session_state.section = "Inicio"
if "selected_stage" not in st.session_state:
    st.session_state.selected_stage = "Embarazo"
if "selected_vaccine" not in st.session_state:
    st.session_state.selected_vaccine = None
if "user_location" not in st.session_state:
    st.session_state.user_location = None
if "library_vaccine" not in st.session_state:
    st.session_state.library_vaccine = None
if "library_letter" not in st.session_state:
    st.session_state.library_letter = "Todas"
if "professional_module" not in st.session_state:
    st.session_state.professional_module = "Centro técnico"
if "intelligence_module" not in st.session_state:
    st.session_state.intelligence_module = "Tablero ejecutivo"
if "professional_access_view" not in st.session_state:
    st.session_state.professional_access_view = "Bienvenida"
if "professional_workspace" not in st.session_state:
    st.session_state.professional_workspace = "Área técnica"
if "institutional_authenticated" not in st.session_state:
    st.session_state.institutional_authenticated = False
if "institutional_role" not in st.session_state:
    st.session_state.institutional_role = None
if "institutional_user" not in st.session_state:
    st.session_state.institutional_user = None
if "access_requests" not in st.session_state:
    st.session_state.access_requests = []
if "created_user_credentials" not in st.session_state:
    st.session_state.created_user_credentials = None
if "nominal_selected_citizen" not in st.session_state:
    st.session_state.nominal_selected_citizen = None
if "nominal_last_document" not in st.session_state:
    st.session_state.nominal_last_document = ""


OFFICIAL_SOURCES = [
    {
        "name": "Calendario Nacional de Vacunación",
        "institution": "Ministerio de Salud de la Nación",
        "url": "https://www.argentina.gob.ar/salud/vacunas",
        "type": "Esquemas de vacunación",
    },
    {
        "name": "Preguntas frecuentes sobre vacunas",
        "institution": "Ministerio de Salud de la Nación",
        "url": "https://www.argentina.gob.ar/salud/vacunas/preguntas-frecuentes",
        "type": "Información",
    },
    {
        "name": "Centros de vacunación de Córdoba",
        "institution": "Gobierno de la Provincia de Córdoba",
        "url": "https://datosgestionabierta.cba.gov.ar/dataset/centros-de-vacunacion-de-la-provincia-de-cordoba",
        "type": "Territorio",
    },
    {
        "name": "CAPS de San Francisco",
        "institution": "Municipalidad de San Francisco",
        "url": "https://www.sanfrancisco.gov.ar/contenidos/centro-de-atencion-primaria-de-salud-caps-282",
        "type": "Territorio",
    },
    {
        "name": "Campaña antigripal 2026",
        "institution": "Municipalidad de San Francisco",
        "url": "https://www.sanfrancisco.gov.ar/noticia/municipio-comienza-con-la-campana-de-vacunacion-antigripal-2026-6732",
        "type": "Novedades",
    },
    {
        "name": "Mi Argentina",
        "institution": "Gobierno de la República Argentina",
        "url": MI_ARGENTINA_URL,
        "type": "Consulta ciudadana",
    },
]


PROFESSIONAL_SYSTEMS = [
    {
        "name": "SIGIPSA",
        "institution": "Sistema Integral para la Gestión de la Información en Programas de Salud",
        "url": SIGIPSA_URL,
        "purpose": "Gestión institucional de programas de salud y acceso con credenciales habilitadas.",
    },
    {
        "name": "NOMIVAC / SISA",
        "institution": "Ministerio de Salud de la Nación",
        "url": NOMIVAC_URL,
        "purpose": "Registro nominal y consulta institucional dentro del Sistema Integrado de Información Sanitaria Argentino.",
    },
]


NEWS_ITEMS = [
    {
        "category": "Esquemas de vacunación",
        "date": "2026",
        "title": "Calendario Nacional de Vacunación 2026",
        "summary": (
            "Consulta el calendario vigente, los carnets unificados y las recomendaciones "
            "organizadas por etapa de la vida."
        ),
        "institution": "Ministerio de Salud de la Nación",
        "url": "https://www.argentina.gob.ar/salud/vacunas",
        "priority": 1,
        "status": "Vigente",
        "featured": True,
    },
    {
        "category": "Campaña vigente",
        "date": "2026",
        "title": "Vacunación antigripal anual",
        "summary": (
            "Información oficial sobre los grupos priorizados, la aplicación gratuita "
            "y las recomendaciones de la campaña antigripal."
        ),
        "institution": "Ministerio de Salud de la Nación",
        "url": "https://www.argentina.gob.ar/salud/vacunas/novedadantigripal",
        "priority": 2,
        "status": "Vigente",
        "featured": False,
    },
    {
        "category": "Actualización técnica",
        "date": "3 de junio de 2026",
        "title": "Recomendaciones sobre vacunas antimeningocócicas ACWY",
        "summary": (
            "Lineamientos técnicos vigentes para la utilización de vacunas "
            "antimeningocócicas conjugadas tetravalentes durante 2026."
        ),
        "institution": "Ministerio de Salud de la Nación",
        "url": "https://www.argentina.gob.ar/salud/inmunoprevenibles/recomendaciones-manuales-y-lineamientos",
        "priority": 3,
        "status": "Actualizado",
        "featured": False,
    },
    {
        "category": "Prevención",
        "date": "18 de febrero de 2026",
        "title": "Vacunación antes del inicio escolar",
        "summary": (
            "Recordatorio oficial para completar los esquemas correspondientes "
            "a niños y niñas que cumplen 5 años durante 2026."
        ),
        "institution": "Ministerio de Salud de la Nación",
        "url": "https://www.argentina.gob.ar/noticias/salud-refuerza-la-importancia-de-completar-los-esquemas-de-vacunacion-antes-del-inicio-de",
        "priority": 4,
        "status": "Información",
        "featured": False,
    },
    {
        "category": "Vigilancia",
        "date": "12 de febrero de 2026",
        "title": "Información oficial sobre sarampión",
        "summary": (
            "Consulta las medidas de prevención, la vacunación indicada y la información "
            "actualizada ante casos importados en la región."
        ),
        "institution": "Ministerio de Salud de la Nación",
        "url": "https://www.argentina.gob.ar/salud/sarampion",
        "priority": 5,
        "status": "Importante",
        "featured": False,
    },
    {
        "category": "Información local",
        "date": "2026",
        "title": "Campaña antigripal en San Francisco",
        "summary": (
            "Acceso al anuncio municipal sobre la campaña local. Antes de asistir, "
            "conviene confirmar disponibilidad, lugar y horario con el establecimiento."
        ),
        "institution": "Municipalidad de San Francisco",
        "url": "https://www.sanfrancisco.gov.ar/noticia/municipio-comienza-con-la-campana-de-vacunacion-antigripal-2026-6732",
        "priority": 6,
        "status": "Local",
        "featured": False,
    },
]


STAGES: Dict[str, dict] = {
    "Embarazo": {
        "color": "#E9A8C4",
        "soft": "#FFF3F8",
        "subtitle": "Protección para la persona gestante y el bebé",
        "intro": (
            "La vacunación durante el embarazo protege a la persona gestante y al bebé "
            "durante sus primeros meses de vida."
        ),
        "items": [
            ("Antigripal", "Una dosis en cualquier trimestre del embarazo."),
            ("Triple bacteriana acelular", "Una dosis en cada embarazo a partir de la semana 20."),
            ("Virus Sincicial Respiratorio", "Una dosis entre las semanas 32 y 36,6 de gestación."),
        ],
        "note": (
            "Si la vacuna antigripal no se recibió durante el embarazo, puede aplicarse "
            "en el puerperio dentro de los 10 días posteriores al parto."
        ),
        "source": "https://www.argentina.gob.ar/salud/vacunas/embarazadas",
    },
    "Recién nacido": {
        "color": "#78C6E7",
        "soft": "#EFFAFF",
        "subtitle": "Protección desde las primeras horas de vida",
        "intro": "Las primeras vacunas se aplican durante la internación o antes del egreso de la maternidad.",
        "items": [
            ("Hepatitis B", "Una dosis dentro de las primeras 12 horas de vida."),
            ("BCG", "Una dosis antes de egresar de la maternidad."),
        ],
        "note": "Conservá el carnet y verificá que cada aplicación quede registrada.",
        "source": "https://www.argentina.gob.ar/salud/crecerconsalud/primermes/vacunas",
    },
    "Hasta 1 año": {
        "color": "#73D3C6",
        "soft": "#EEFBF8",
        "subtitle": "Inicio de los principales esquemas",
        "intro": "Durante el primer año se aplican dosis iniciales y refuerzos fundamentales.",
        "items": [
            ("2 meses", "Neumococo conjugada, Polio, Quíntuple y Rotavirus: primeras dosis."),
            ("3 meses", "Meningococo: primera dosis."),
            ("4 meses", "Neumococo, Polio, Quíntuple y Rotavirus: segundas dosis."),
            ("5 meses", "Meningococo: segunda dosis."),
            ("6 meses", "Polio y Quíntuple: terceras dosis."),
            ("6 a 24 meses", "Antigripal según antecedentes de vacunación."),
            ("12 meses", "Neumococo refuerzo, Hepatitis A y Triple viral primera dosis."),
        ],
        "note": "Verificá el esquema exacto en el carnet y en el vacunatorio.",
        "source": "https://www.argentina.gob.ar/salud/vacunas",
    },
    "Hasta 2 años": {
        "color": "#F3C65D",
        "soft": "#FFF9EA",
        "subtitle": "Refuerzos y continuidad de esquemas",
        "intro": "Entre el primer y el segundo año se aplican refuerzos y nuevas vacunas.",
        "items": [
            ("15 meses", "Meningococo refuerzo y Varicela primera dosis."),
            ("15 a 18 meses", "Triple viral segunda dosis y Quíntuple refuerzo."),
            ("18 meses", "Fiebre amarilla para residentes en zonas de riesgo."),
            ("6 a 24 meses", "Antigripal según antecedentes."),
        ],
        "note": "No reinicies esquemas. Consultá para completarlos según antecedentes.",
        "source": "https://www.argentina.gob.ar/salud/vacunas",
    },
    "5 años": {
        "color": "#F39B68",
        "soft": "#FFF3EC",
        "subtitle": "Vacunas del ingreso escolar",
        "intro": "El ingreso escolar es una oportunidad para revisar y completar el carnet.",
        "items": [
            ("Polio", "Una dosis de refuerzo."),
            ("Triple viral", "Dosis correspondiente según esquema vigente."),
            ("Triple bacteriana celular", "Una dosis de refuerzo."),
            ("Varicela", "Revisar y completar el esquema según corresponda."),
        ],
        "note": "Llevá el carnet al control escolar y al vacunatorio.",
        "source": "https://www.argentina.gob.ar/salud/crecerconsalud/seisadiez/vacunas",
    },
    "11 años": {
        "color": "#A997E7",
        "soft": "#F5F2FF",
        "subtitle": "Refuerzos y prevención en la adolescencia",
        "intro": "A los 11 años se refuerzan vacunas de la infancia y se incorporan nuevas protecciones.",
        "items": [
            ("VPH", "Una única dosis."),
            ("Meningococo", "Una única dosis."),
            ("Triple bacteriana acelular", "Una única dosis."),
            ("Fiebre amarilla", "Refuerzo para residentes en zonas de riesgo."),
        ],
        "note": "También se revisan esquemas incompletos de Hepatitis B y Triple viral.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/vacunacion-adolescentes",
    },
    "15 a 64 años": {
        "color": "#68B8D8",
        "soft": "#EFF8FC",
        "subtitle": "Refuerzos y situaciones específicas",
        "intro": "En la adultez corresponde sostener refuerzos y completar esquemas.",
        "items": [
            ("Doble bacteriana", "Completar tres dosis y luego refuerzo cada 10 años."),
            ("Doble o triple viral", "Acreditar dos dosis después del año de vida."),
            ("Antigripal", "Anual para personas con factores de riesgo."),
            ("Fiebre Hemorrágica Argentina", "Desde los 15 años para quienes residan o trabajen en zona endémica."),
        ],
        "note": "La indicación puede variar según antecedentes, ocupación, viaje o condición clínica.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/vacunacion-adultos",
    },
    "65 años o más": {
        "color": "#8CCB85",
        "soft": "#F1FAEF",
        "subtitle": "Protección frente a complicaciones frecuentes",
        "intro": "Las personas de 65 años o más deben continuar refuerzos y protegerse frente a gripe y neumococo.",
        "items": [
            ("Antigripal", "Una dosis anual."),
            ("Neumococo", "Esquema vigente según antecedentes."),
            ("Doble bacteriana", "Completar esquema y refuerzo cada 10 años."),
        ],
        "note": "Consultá para revisar antecedentes y oportunidades de vacunación.",
        "source": "https://www.argentina.gob.ar/salud/vacunas",
    },
}


VACCINES: List[dict] = [
    {
        "name": "BCG",
        "protects": "Formas graves de tuberculosis.",
        "stage": "Recién nacido",
        "scheme": "Una dosis antes de egresar de la maternidad.",
        "route": "Intradérmica.",
        "who": "Personas recién nacidas.",
        "details": "Es habitual que deje una pequeña cicatriz en el brazo.",
        "expected": "Puede aparecer una reacción local que evoluciona de forma gradual.",
        "precautions": "La evaluación individual corresponde al equipo de salud.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/bcg",
    },
    {
        "name": "Hepatitis B",
        "protects": "Hepatitis B y sus complicaciones.",
        "stage": "Recién nacido / Todas las edades",
        "scheme": "Dosis neonatal dentro de las primeras 12 horas y esquema según antecedentes.",
        "route": "Intramuscular.",
        "who": "Recién nacidos y personas con esquema incompleto.",
        "details": "La dosis neonatal es prioritaria por su oportunidad de prevención.",
        "expected": "Dolor o enrojecimiento local; ocasionalmente fiebre.",
        "precautions": "La indicación individual debe revisarse en el vacunatorio.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/hepatitisb",
    },
    {
        "name": "Neumococo",
        "protects": "Enfermedades invasivas y neumonía por neumococo.",
        "stage": "Infancia / Personas mayores / Riesgo",
        "scheme": "Esquema según edad, antecedentes y condición clínica.",
        "route": "Intramuscular.",
        "who": "Lactantes, personas mayores y grupos con indicación específica.",
        "details": "Previene formas graves de enfermedad neumocócica.",
        "expected": "Dolor local, fiebre o malestar transitorio.",
        "precautions": "Consultar antecedentes y esquemas previos.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/neumococo",
    },
    {
        "name": "Polio",
        "protects": "Poliomielitis.",
        "stage": "Infancia",
        "scheme": "Dosis a los 2, 4 y 6 meses, con refuerzo escolar según calendario.",
        "route": "Intramuscular.",
        "who": "Niños y niñas según calendario.",
        "details": "El calendario utiliza vacuna antipoliomielítica inactivada.",
        "expected": "Dolor o inflamación leve en el sitio de aplicación.",
        "precautions": "Revisar esquema y edad en el vacunatorio.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/polio",
    },
    {
        "name": "Rotavirus",
        "protects": "Gastroenteritis grave por rotavirus.",
        "stage": "Lactantes",
        "scheme": "Dos dosis durante los primeros meses de vida.",
        "route": "Oral.",
        "who": "Lactantes dentro de las edades previstas por calendario.",
        "details": "Tiene edades máximas de aplicación que deben respetarse.",
        "expected": "Puede presentarse irritabilidad o síntomas digestivos leves.",
        "precautions": "Confirmar la edad antes de la aplicación.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/rotavirus",
    },
    {
        "name": "Quíntuple",
        "protects": "Difteria, tétanos, tos convulsa, Haemophilus influenzae tipo b y hepatitis B.",
        "stage": "Infancia",
        "scheme": "Dosis a los 2, 4 y 6 meses y refuerzo según calendario.",
        "route": "Intramuscular.",
        "who": "Lactantes y niños pequeños.",
        "details": "Integra varias protecciones en una misma aplicación.",
        "expected": "Dolor local, fiebre o irritabilidad.",
        "precautions": "Consultar antecedentes de reacciones previas.",
        "source": "https://www.argentina.gob.ar/salud/vacunas",
    },
    {
        "name": "Meningococo",
        "protects": "Enfermedad meningocócica invasiva.",
        "stage": "Infancia / Adolescencia",
        "scheme": "Dosis durante el primer año, refuerzo a los 15 meses y dosis a los 11 años.",
        "route": "Intramuscular.",
        "who": "Niños, niñas y adolescentes según calendario.",
        "details": "Previene cuadros graves como meningitis y sepsis.",
        "expected": "Dolor local, fiebre o malestar transitorio.",
        "precautions": "Revisar esquema según edad.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/meningococo",
    },
    {
        "name": "Antigripal",
        "protects": "Influenza y sus complicaciones.",
        "stage": "Embarazo / Infancia / Riesgo / Personas mayores",
        "scheme": "Una dosis anual; algunos niños pueden requerir dos dosis según antecedentes.",
        "route": "Intramuscular.",
        "who": "Grupos incluidos en el Calendario Nacional.",
        "details": "Debe aplicarse oportunamente, idealmente antes del invierno.",
        "expected": "Dolor local, fiebre baja o malestar.",
        "precautions": "Verificar indicación anual y antecedentes.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/antigripal",
    },
    {
        "name": "Hepatitis A",
        "protects": "Hepatitis A.",
        "stage": "12 meses",
        "scheme": "Una única dosis a los 12 meses.",
        "route": "Intramuscular.",
        "who": "Niños y niñas según calendario.",
        "details": "Forma parte del esquema de la primera infancia.",
        "expected": "Dolor local o febrícula.",
        "precautions": "Confirmar edad y antecedentes.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/hepatitisa",
    },
    {
        "name": "Triple viral",
        "protects": "Sarampión, rubéola y paperas.",
        "stage": "Infancia / Recupero",
        "scheme": "Primera dosis a los 12 meses y segunda entre los 15 y 18 meses.",
        "route": "Subcutánea.",
        "who": "Niños y personas con esquemas incompletos según normativa.",
        "details": "Las dosis requeridas dependen de edad, cohorte y antecedentes.",
        "expected": "Puede presentarse fiebre o exantema leve días después.",
        "precautions": "Consultar en embarazo, inmunocompromiso o ante dudas.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/tripleviral",
    },
    {
        "name": "Varicela",
        "protects": "Varicela y sus complicaciones.",
        "stage": "Infancia",
        "scheme": "Dosis a los 15 meses y revisión del esquema en edad escolar.",
        "route": "Subcutánea.",
        "who": "Niños y niñas según calendario.",
        "details": "La indicación exacta se verifica según cohorte y antecedentes.",
        "expected": "Dolor local, fiebre o erupción leve.",
        "precautions": "Consultar en embarazo o inmunocompromiso.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/varicela",
    },
    {
        "name": "VPH",
        "protects": "Infecciones y cánceres relacionados con el Virus del Papiloma Humano.",
        "stage": "11 años",
        "scheme": "Una única dosis a los 11 años.",
        "route": "Intramuscular.",
        "who": "Niños y niñas según calendario.",
        "details": "La vacunación temprana mejora la protección antes de la exposición.",
        "expected": "Dolor local, cefalea o malestar transitorio.",
        "precautions": "Permanecer sentado unos minutos después de la aplicación.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/vph",
    },
    {
        "name": "Triple bacteriana acelular",
        "protects": "Difteria, tétanos y tos convulsa.",
        "stage": "Embarazo / 11 años / Personal de salud",
        "scheme": "Según etapa: embarazo desde semana 20, dosis a los 11 años y situaciones especiales.",
        "route": "Intramuscular.",
        "who": "Personas incluidas en calendario y situaciones especiales.",
        "details": "Durante el embarazo protege también al recién nacido frente a tos convulsa.",
        "expected": "Dolor local, fiebre o malestar.",
        "precautions": "Revisar antecedentes y etapa de vida.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/triplebacterianaacelular",
    },
    {
        "name": "Doble bacteriana",
        "protects": "Difteria y tétanos.",
        "stage": "Adultez",
        "scheme": "Completar tres dosis y luego refuerzo cada 10 años.",
        "route": "Intramuscular.",
        "who": "Personas adultas según antecedentes.",
        "details": "El refuerzo periódico mantiene la protección.",
        "expected": "Dolor local o febrícula.",
        "precautions": "Revisar fecha del último refuerzo.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/doblebacteriana",
    },
    {
        "name": "Fiebre amarilla",
        "protects": "Fiebre amarilla.",
        "stage": "Zonas de riesgo / Viajes",
        "scheme": "Según residencia, riesgo epidemiológico o requerimientos de viaje.",
        "route": "Subcutánea.",
        "who": "Personas con indicación por residencia o viaje.",
        "details": "El certificado internacional conserva validez de por vida.",
        "expected": "Dolor local, fiebre o cefalea.",
        "precautions": "Requiere evaluación en algunas edades y condiciones clínicas.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/fiebreamarilla",
    },
    {
        "name": "Virus Sincicial Respiratorio",
        "protects": "Enfermedad respiratoria grave por VSR en lactantes.",
        "stage": "Embarazo",
        "scheme": "Una dosis entre las semanas 32 y 36,6 de gestación.",
        "route": "Intramuscular.",
        "who": "Personas embarazadas según calendario.",
        "details": "La protección se transfiere al bebé mediante anticuerpos maternos.",
        "expected": "Dolor local, cefalea o malestar.",
        "precautions": "Confirmar edad gestacional.",
        "source": "https://www.argentina.gob.ar/salud/vacunas/vsr",
    },
]


CENTERS = [
    {
        "name": "Asistencia Pública",
        "type": "Asistencia Pública",
        "address": "Colón 165",
        "phone": "03564 439154",
        "lat": -31.42715,
        "lon": -62.08388,
        "schedule": "Lunes a viernes. Confirmar horario de vacunación.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS Cottolengo",
        "type": "CAPS",
        "address": "José Hernández 3049",
        "phone": "03564 434726 / 3564 213014",
        "lat": -31.41485,
        "lon": -62.10592,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS 2 Hermanos",
        "type": "CAPS",
        "address": "Colombia 234",
        "phone": "03564 310030",
        "lat": -31.43275,
        "lon": -62.09612,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS Roque Sáenz Peña",
        "type": "CAPS",
        "address": "Falucho esq. Gerónimo del Barco",
        "phone": "3564 370400",
        "lat": -31.42272,
        "lon": -62.09140,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS Jardín",
        "type": "CAPS",
        "address": "Rioja 2653",
        "phone": "3564 333456",
        "lat": -31.41860,
        "lon": -62.10440,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS Bouchard",
        "type": "CAPS",
        "address": "Rioja esq. General Paz",
        "phone": "03564 498404",
        "lat": -31.42790,
        "lon": -62.10040,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS La Milka",
        "type": "CAPS",
        "address": "Madre Marcilla 407",
        "phone": "3564 237775",
        "lat": -31.44342,
        "lon": -62.10010,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS Sarmiento",
        "type": "CAPS",
        "address": "Olegario Andrade 707",
        "phone": "03564 498116 / 3564 333452",
        "lat": -31.42022,
        "lon": -62.09275,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS Parque",
        "type": "CAPS",
        "address": "Resistencia 578",
        "phone": "03564 434725 / 3564 595398",
        "lat": -31.43462,
        "lon": -62.07382,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS San Cayetano",
        "type": "CAPS",
        "address": "Pascual Bailón Sosa 1759",
        "phone": "03564 435274",
        "lat": -31.43825,
        "lon": -62.11125,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS Prado",
        "type": "CAPS",
        "address": "Los Robles 1193",
        "phone": "3564 237319",
        "lat": -31.40720,
        "lon": -62.08955,
        "schedule": "Consultar telefónicamente.",
        "availability": "Confirmar antes de concurrir",
    },
    {
        "name": "CAPS Plaza",
        "type": "CAPS",
        "address": "Víctor Angelli 4136",
        "phone": "3564 684355",
        "lat": -31.39870,
        "lon": -62.11030,
        "schedule": "Lunes a viernes de 8 a 12. Confirmar vacunación.",
        "availability": "Confirmar antes de concurrir",
    },
]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


@st.cache_data(ttl=AUTO_REFRESH_SECONDS, show_spinner=False)
def source_snapshot(url: str) -> dict:
    checked_at = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")
    try:
        response = requests.get(
            url,
            timeout=12,
            headers={"User-Agent": "VACUNACIÓN-PLATAFORMA-DIGITAL/1.0"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        main = soup.find("main") or soup.find("article") or soup.body
        text = clean_text(main.get_text(" ", strip=True) if main else "")
        return {
            "ok": True,
            "checked_at": checked_at,
            "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
        }
    except Exception as exc:
        return {"ok": False, "checked_at": checked_at, "hash": "-", "error": str(exc)}



def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_centers(latitude: float, longitude: float, centers: List[dict]) -> List[dict]:
    ranked = []
    for center in centers:
        enriched = dict(center)
        enriched["distance_km"] = haversine_km(
            latitude,
            longitude,
            center["lat"],
            center["lon"],
        )
        ranked.append(enriched)
    return sorted(ranked, key=lambda item: item["distance_km"])


st.markdown(
    """
    <style>
    :root{
        --ink:#102A43;
        --ink-soft:#334E68;
        --accent:#176B5B;
        --accent-strong:#0F5B4D;
        --accent-soft:#EEF7F4;
        --surface:#FFFFFF;
        --surface-soft:#F6F8FA;
        --line:#D9E2E8;
        --focus:#1C7C6B;
        --shadow:0 14px 38px rgba(16,42,67,.08);
        --shadow-soft:0 6px 20px rgba(16,42,67,.06);
        --radius-lg:24px;
        --radius-md:16px;
        --radius-sm:10px;
    }

    html{scroll-behavior:smooth}
    .stApp{
        background:var(--surface);
        color:var(--ink);
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    }
    .block-container{
        max-width:1240px;
        padding-top:1rem;
        padding-bottom:4rem;
    }
    #MainMenu, footer, header{visibility:hidden}
    h1,h2,h3,h4{
        color:var(--ink);
        letter-spacing:-.025em;
        line-height:1.15;
    }
    p, li, label, .stCaption{line-height:1.6}

    .brandbar{
        display:flex;
        justify-content:space-between;
        align-items:flex-end;
        gap:2rem;
        padding:1.1rem 0 1.35rem;
        border-bottom:1px solid var(--line);
        margin-bottom:1rem;
    }
    .brandidentity{display:flex;flex-direction:column;gap:.18rem}
    .brandtitle{
        font-size:1.55rem;
        line-height:1;
        font-weight:850;
        letter-spacing:-.035em;
        color:var(--ink);
    }
    .brandsubtitle{
        font-size:.92rem;
        font-weight:650;
        color:var(--ink-soft);
    }
    .brandmeta{
        font-size:.84rem;
        color:var(--ink-soft);
        font-weight:600;
        text-align:right;
    }

    .hero{
        padding:4.6rem 3.5rem;
        border-radius:var(--radius-lg);
        border:1px solid var(--line);
        background:linear-gradient(145deg,#FBFCFD 0%,#F5FAF8 100%);
        box-shadow:var(--shadow);
        margin:1.5rem 0 2.4rem;
    }
    .hero-eyebrow{
        margin:0 0 1.1rem;
        font-size:.82rem;
        font-weight:750;
        letter-spacing:.08em;
        text-transform:uppercase;
        color:var(--accent);
    }
    .hero h1{
        font-size:clamp(3.2rem,7vw,6.1rem);
        line-height:.92;
        margin:0;
        max-width:920px;
        font-weight:880;
        letter-spacing:-.06em;
    }
    .hero h2{
        font-size:clamp(1.2rem,2vw,1.65rem);
        margin:.9rem 0 1.4rem;
        color:var(--ink-soft);
        font-weight:600;
        letter-spacing:-.02em;
    }
    .hero p{
        font-size:clamp(1rem,1.4vw,1.16rem);
        color:var(--ink-soft);
        max-width:760px;
        line-height:1.7;
        margin:0;
    }

    .section-label{
        font-size:.74rem;
        letter-spacing:.1em;
        text-transform:uppercase;
        font-weight:800;
        color:var(--accent);
        margin-top:2.7rem;
    }
    .section-title{
        font-size:clamp(1.8rem,3vw,2.45rem);
        font-weight:820;
        margin:.25rem 0 .45rem;
    }
    .section-copy{
        color:var(--ink-soft);
        margin-bottom:1.4rem;
        max-width:840px;
        font-size:1rem;
    }

    .stage-card{
        padding:1.35rem;
        border-radius:var(--radius-md);
        border:1px solid rgba(16,42,67,.10);
        min-height:155px;
        margin-bottom:.85rem;
        transition:transform .18s ease,box-shadow .18s ease;
    }
    .stage-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-soft)}
    .stage-card h3{margin:.1rem 0 .45rem;font-size:1.08rem}
    .stage-card p{color:var(--ink-soft);font-size:.92rem;margin-bottom:0}

    .detail-card{
        padding:1.8rem;
        border-radius:var(--radius-lg);
        border:1px solid var(--line);
        background:var(--surface);
        box-shadow:var(--shadow-soft);
        margin:1rem 0;
    }
    .detail-header{display:block;margin-bottom:1rem}
    .dose-row{
        padding:1rem 1.05rem;
        border-radius:var(--radius-sm);
        background:var(--surface-soft);
        margin:.6rem 0;
        border:1px solid #E6EBEF;
    }
    .vaccine-card{
        padding:1.45rem;
        border-radius:var(--radius-md);
        border:1px solid var(--line);
        background:var(--surface);
        margin-bottom:1rem;
        min-height:205px;
        box-shadow:0 2px 0 rgba(16,42,67,.02);
        transition:transform .18s ease,box-shadow .18s ease;
    }
    .vaccine-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-soft)}
    .vaccine-card p{color:var(--ink-soft)}
    .source-chip{
        display:inline-block;
        padding:.34rem .68rem;
        border-radius:999px;
        background:var(--accent-soft);
        color:var(--accent-strong);
        font-size:.74rem;
        font-weight:760;
    }
    .notice{
        padding:1rem 1.15rem;
        border-left:4px solid var(--accent);
        background:var(--accent-soft);
        border-radius:var(--radius-sm);
        margin:1rem 0;
        color:var(--ink-soft);
    }
    .footerx{
        margin-top:3.5rem;
        padding-top:1.4rem;
        border-top:1px solid var(--line);
        font-size:.84rem;
        color:var(--ink-soft);
        line-height:1.7;
    }

    .stButton>button,
    .stLinkButton>a{
        min-height:44px;
        border-radius:var(--radius-sm)!important;
        border:1px solid var(--line)!important;
        background:var(--surface)!important;
        color:var(--ink)!important;
        font-weight:680!important;
        box-shadow:none!important;
        transition:background .16s ease,border-color .16s ease,transform .16s ease!important;
    }
    .stButton>button:hover,
    .stLinkButton>a:hover{
        background:var(--surface-soft)!important;
        border-color:#B7C4CD!important;
        transform:translateY(-1px);
    }
    .stButton>button:focus,
    .stLinkButton>a:focus,
    input:focus,
    textarea:focus{
        outline:3px solid rgba(28,124,107,.22)!important;
        outline-offset:2px!important;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"]>div>div{
        border-radius:var(--radius-sm)!important;
        min-height:44px;
    }
    [data-testid="stExpander"]{
        border:1px solid var(--line)!important;
        border-radius:var(--radius-sm)!important;
        overflow:hidden;
    }
    [data-testid="stExpander"] summary{font-weight:680}
    [data-testid="stHorizontalBlock"]{row-gap:.65rem}

    @media(max-width:900px){
        .block-container{padding-left:1rem;padding-right:1rem;padding-top:.55rem}
        .brandbar{align-items:flex-start;flex-direction:column;gap:.65rem}
        .brandmeta{text-align:left}
        .hero{padding:3rem 1.7rem;border-radius:20px;margin-top:1rem}
    }
    /* El selector móvil permanece oculto en escritorio. */
    .st-key-mobile_navigation{display:none}

    @media(max-width:600px){
        .block-container{
            padding-left:.82rem!important;
            padding-right:.82rem!important;
            padding-top:.35rem!important;
            padding-bottom:7rem!important;
        }
        .brandbar{
            gap:.3rem!important;
            padding:.7rem 0 .85rem!important;
            margin-bottom:.35rem!important;
        }
        .brandtitle{font-size:1.12rem!important;line-height:1.15!important}
        .brandsubtitle{font-size:.78rem!important}
        .brandmeta{font-size:.76rem!important}

        /* En móvil se ocultan los botones extensos y se utiliza un único selector. */
        .st-key-desktop_citizen_navigation,
        .st-key-desktop_professional_navigation,
        .desktop-nav-label{display:none!important}
        .st-key-mobile_navigation{display:block!important;margin:.2rem 0 .75rem!important}
        .st-key-mobile_navigation label{
            font-size:.76rem!important;
            font-weight:760!important;
            color:var(--ink-soft)!important;
        }
        .st-key-mobile_navigation [data-baseweb="select"]>div{
            min-height:46px!important;
            border-radius:12px!important;
        }

        .hero{
            padding:1.35rem 1rem!important;
            border-radius:16px!important;
            margin:.55rem 0 1rem!important;
            box-shadow:none!important;
        }
        .hero h1{font-size:2.08rem!important;line-height:1!important;letter-spacing:-.045em!important}
        .hero h2{font-size:1rem!important;margin:.65rem 0 .8rem!important}
        .hero p{font-size:.92rem!important;line-height:1.5!important}
        .hero-eyebrow{font-size:.68rem!important;margin-bottom:.65rem!important}
        .section-label{margin-top:1.15rem!important;font-size:.67rem!important}
        .section-title{font-size:1.55rem!important;margin:.18rem 0 .25rem!important}
        .section-copy{font-size:.9rem!important;line-height:1.48!important;margin-bottom:.8rem!important}

        .stage-card,.vaccine-card,.detail-card{
            min-height:0!important;
            border-radius:14px!important;
            box-shadow:none!important;
        }
        .vaccine-card{
            padding:.88rem .92rem!important;
            margin:.25rem 0 .35rem!important;
        }
        .vaccine-card h3{font-size:1rem!important;margin:0 0 .28rem!important}
        .vaccine-card p{font-size:.84rem!important;line-height:1.42!important;margin:0!important}
        .stage-card{padding:.9rem!important;margin-bottom:.4rem!important}
        .detail-card{padding:1rem!important;margin:.65rem 0!important}
        .dose-row{padding:.8rem .85rem!important;margin:.42rem 0!important}
        .notice{margin:.65rem 0!important;font-size:.88rem!important}
        .footerx{margin-top:1.5rem!important;padding-top:1rem!important;font-size:.78rem!important}

        .stButton>button,.stLinkButton>a{
            min-height:42px!important;
            font-size:.86rem!important;
            padding:.55rem .75rem!important;
        }
        [data-testid="stVerticalBlock"]{gap:.45rem!important}
        [data-testid="stHorizontalBlock"]{gap:.55rem!important;row-gap:.55rem!important}
        [data-testid="stExpander"]{margin-bottom:.35rem!important}
        [data-testid="stExpander"] summary{padding:.72rem .8rem!important}
        [data-testid="stForm"]{padding:.2rem 0!important}
        [data-testid="stDataFrame"],iframe{max-width:100%!important}

        /* Adaptación exclusiva del entorno profesional e institucional. */
        .portal-hero{padding:1.35rem 1rem!important;border-radius:16px!important}
        .portal-hero h1{font-size:1.8rem!important;line-height:1.15!important}
        .portal-hero p{font-size:.94rem!important;line-height:1.55!important}
        .portal-band{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:.55rem!important}
        .portal-metric{padding:.8rem!important;min-height:auto!important}
        .portal-metric span{font-size:.68rem!important}
        .portal-metric strong{font-size:.88rem!important}
        .technical-grid{grid-template-columns:1fr!important}
        .technical-sheet{padding:1rem!important;border-radius:14px!important}
        .module-card{min-height:auto!important;padding:1rem!important}
        .module-card p{font-size:.88rem!important}
        [data-testid="stExpander"] summary{font-size:.95rem!important}
        [data-testid="stForm"]{padding:.2rem 0!important}
        .data-quality,.decision-panel,.notice{padding:1rem!important;border-radius:14px!important}
    }
    @media(prefers-reduced-motion:reduce){
        *{scroll-behavior:auto!important;transition:none!important;animation:none!important}
    }
    
    .news-featured {
        margin-top: 1.1rem;
        padding: 2rem;
        border: 1px solid #DCE5EC;
        border-radius: 22px;
        background: linear-gradient(135deg, #F7FAFC 0%, #EEF5F3 100%);
        box-shadow: 0 12px 30px rgba(21, 49, 74, 0.07);
    }

    .news-featured-label,
    .news-status {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        padding: 0.34rem 0.65rem;
        border-radius: 999px;
        background: #E4F1ED;
        color: #1E6A58;
        font-size: 0.76rem;
        font-weight: 750;
        letter-spacing: 0.02em;
    }

    .news-featured-meta {
        margin-top: 1rem;
        color: #667685;
        font-size: 0.88rem;
    }

    .news-featured h2 {
        margin: 0.55rem 0 0.65rem;
        color: #15314A;
        font-size: clamp(1.55rem, 3vw, 2.2rem);
        line-height: 1.16;
    }

    .news-featured p {
        max-width: 820px;
        margin: 0;
        color: #4F6070;
        font-size: 1rem;
        line-height: 1.65;
    }

    .news-card {
        min-height: 270px;
        margin-top: 0.45rem;
        padding: 1.35rem;
        border: 1px solid #DCE5EC;
        border-radius: 18px;
        background: #FFFFFF;
        box-shadow: 0 8px 22px rgba(21, 49, 74, 0.055);
    }

    .news-card-topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .news-category {
        color: #71808E;
        font-size: 0.78rem;
        text-align: right;
    }

    .news-card h3 {
        margin: 0 0 0.7rem;
        color: #15314A;
        font-size: 1.14rem;
        line-height: 1.34;
    }

    .news-card p {
        margin: 0;
        color: #536473;
        line-height: 1.58;
    }

    .news-meta {
        margin-top: 1.1rem;
        padding-top: 0.85rem;
        border-top: 1px solid #ECF0F3;
        color: #687785;
        font-size: 0.82rem;
        line-height: 1.4;
    }

    .news-local-note {
        margin-top: 1.4rem;
        padding: 1rem 1.1rem;
        border-radius: 14px;
        background: #F6F8FA;
        color: #5C6B78;
        font-size: 0.88rem;
        line-height: 1.55;
    }

    @media (max-width: 760px) {
        .news-featured {
            padding: 1.35rem;
            border-radius: 18px;
        }

        .news-card {
            min-height: auto;
        }
    }


    .centers-intro {
        margin: 0.9rem 0 1.2rem;
        padding: 1rem 1.1rem;
        border: 1px solid #DDE7E3;
        border-radius: 15px;
        background: #F4F9F7;
        color: #4E625C;
        font-size: 0.91rem;
        line-height: 1.55;
    }

    .center-summary-card {
        min-height: 116px;
        margin: 0.55rem 0 0.85rem;
        padding: 1.05rem 1.15rem;
        border: 1px solid #DCE5EC;
        border-radius: 16px;
        background: #FFFFFF;
        box-shadow: 0 7px 20px rgba(21, 49, 74, 0.05);
    }

    .center-summary-card strong,
    .center-summary-card span {
        display: block;
    }

    .center-summary-card strong {
        margin: 0.28rem 0 0.18rem;
        color: #15314A;
        font-size: 1rem;
        line-height: 1.35;
    }

    .center-summary-card span:last-child {
        color: #6B7985;
        font-size: 0.84rem;
    }

    .center-summary-label {
        color: #2C8F78;
        font-size: 0.73rem;
        font-weight: 750;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .center-card {
        min-height: 325px;
        margin: 0.45rem 0 0.15rem;
        padding: 1.3rem;
        border: 1px solid #DCE5EC;
        border-radius: 18px;
        background: #FFFFFF;
        box-shadow: 0 8px 22px rgba(21, 49, 74, 0.055);
    }

    .center-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.95rem;
    }

    .center-type {
        display: inline-flex;
        width: fit-content;
        padding: 0.31rem 0.62rem;
        border-radius: 999px;
        background: #E6F2EE;
        color: #176B59;
        font-size: 0.74rem;
        font-weight: 750;
    }

    .center-distance {
        color: #61717E;
        font-size: 0.78rem;
        font-weight: 650;
    }

    .center-card h3 {
        margin: 0 0 0.42rem;
        color: #15314A;
        font-size: 1.18rem;
        line-height: 1.3;
    }

    .center-address {
        min-height: 42px;
        margin-bottom: 1rem;
        color: #5C6D7A;
        line-height: 1.5;
    }

    .center-detail {
        margin-top: 0.78rem;
        padding-top: 0.78rem;
        border-top: 1px solid #ECF0F3;
    }

    .center-detail span,
    .center-detail strong {
        display: block;
    }

    .center-detail span {
        margin-bottom: 0.22rem;
        color: #77848E;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.035em;
        text-transform: uppercase;
    }

    .center-detail strong {
        color: #415363;
        font-size: 0.89rem;
        line-height: 1.45;
    }

    .center-verification {
        margin-top: 0.95rem;
        color: #6A786F;
        font-size: 0.8rem;
        font-weight: 650;
    }

    @media (max-width: 760px) {
        .center-card {
            min-height: auto;
        }

        .center-summary-card {
            min-height: auto;
        }
    }


    .scheme-intro {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin: 0.9rem 0 1.35rem;
        padding: 1rem 1.15rem;
        border: 1px solid #DDE7E3;
        border-radius: 16px;
        background: #F5F9F8;
    }

    .scheme-intro div,
    .scheme-intro strong,
    .scheme-intro span {
        display: block;
    }

    .scheme-intro strong {
        margin-top: 0.18rem;
        color: #15314A;
        font-size: 0.98rem;
    }

    .scheme-kicker,
    .scheme-source {
        color: #2C8F78;
        font-size: 0.72rem;
        font-weight: 780;
        letter-spacing: 0.055em;
        text-transform: uppercase;
    }

    .scheme-source {
        text-align: right;
        color: #687884;
    }

    .scheme-step {
        margin: 1.55rem 0 0.75rem;
        color: #15314A;
        font-size: 0.84rem;
        font-weight: 800;
        letter-spacing: 0.035em;
        text-transform: uppercase;
    }

    .stage-option {
        min-height: 152px;
        margin: 0 0 0.35rem;
        padding: 1.15rem;
        border: 1px solid #DDE5EA;
        border-top: 5px solid var(--stage-color);
        border-radius: 17px;
        background: #FFFFFF;
        box-shadow: 0 5px 16px rgba(21, 49, 74, 0.04);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }

    .stage-option:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(21, 49, 74, 0.08);
    }

    .stage-option-active {
        border-color: var(--stage-color);
        background: var(--stage-soft);
        box-shadow: 0 10px 26px rgba(21, 49, 74, 0.09);
    }

    .stage-option-status {
        display: block;
        margin-bottom: 0.75rem;
        color: #657783;
        font-size: 0.69rem;
        font-weight: 770;
        letter-spacing: 0.052em;
        text-transform: uppercase;
    }

    .stage-option-active .stage-option-status {
        color: #15314A;
    }

    .stage-option h3 {
        margin: 0 0 0.38rem;
        color: #15314A;
        font-size: 1.03rem;
        line-height: 1.25;
    }

    .stage-option p {
        margin: 0;
        color: #667784;
        font-size: 0.84rem;
        line-height: 1.45;
    }

    .scheme-hero {
        position: relative;
        min-height: 300px;
        margin: 0.3rem 0 1rem;
        padding: 2rem;
        overflow: hidden;
        border: 1px solid color-mix(in srgb, var(--stage-color) 48%, #DCE5EA);
        border-radius: 22px;
        background:
            radial-gradient(circle at 92% 16%, var(--stage-soft), transparent 42%),
            #FFFFFF;
        box-shadow: 0 12px 34px rgba(21, 49, 74, 0.07);
    }

    .scheme-hero::after {
        content: "";
        position: absolute;
        right: -45px;
        bottom: -65px;
        width: 190px;
        height: 190px;
        border: 28px solid var(--stage-color);
        border-radius: 50%;
        opacity: 0.12;
    }

    .scheme-hero-label {
        display: inline-flex;
        padding: 0.32rem 0.62rem;
        border-radius: 999px;
        background: var(--stage-soft);
        color: #15314A;
        font-size: 0.71rem;
        font-weight: 780;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .scheme-hero h2 {
        position: relative;
        z-index: 1;
        margin: 0.8rem 0 0.3rem;
        color: #15314A;
        font-size: clamp(2rem, 4vw, 3.25rem);
        letter-spacing: -0.045em;
    }

    .scheme-hero-subtitle {
        position: relative;
        z-index: 1;
        margin: 0;
        color: #415A6D;
        font-size: 1.03rem;
        font-weight: 650;
    }

    .scheme-hero-copy {
        position: relative;
        z-index: 1;
        max-width: 700px;
        margin: 1rem 0 1.4rem;
        color: #60717E;
        line-height: 1.65;
    }

    .scheme-metric {
        position: relative;
        z-index: 1;
        display: inline-flex;
        align-items: baseline;
        gap: 0.48rem;
        color: #15314A;
    }

    .scheme-metric strong {
        font-size: 1.65rem;
    }

    .scheme-metric span {
        color: #647580;
        font-size: 0.84rem;
        font-weight: 650;
    }

    .scheme-validation {
        min-height: 210px;
        margin: 0.3rem 0 0.7rem;
        padding: 1.45rem;
        border: 1px solid #DCE5EA;
        border-radius: 18px;
        background: #F7F9FA;
    }

    .scheme-validation span,
    .scheme-validation strong {
        display: block;
    }

    .scheme-validation span {
        color: #2C8F78;
        font-size: 0.72rem;
        font-weight: 780;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .scheme-validation strong {
        margin: 0.45rem 0 0.7rem;
        color: #15314A;
        font-size: 1.05rem;
    }

    .scheme-validation p {
        color: #657681;
        font-size: 0.88rem;
        line-height: 1.55;
    }

    .scheme-results {
        margin: 0.65rem 0 0.85rem;
        color: #687986;
        font-size: 0.83rem;
        font-weight: 650;
    }

    .scheme-vaccine-card {
        min-height: 215px;
        margin: 0.35rem 0 0.2rem;
        padding: 1.4rem;
        border: 1px solid #DCE5EA;
        border-top: 5px solid var(--stage-color);
        border-radius: 18px;
        background: #FFFFFF;
        box-shadow: 0 7px 20px rgba(21, 49, 74, 0.05);
    }

    .scheme-vaccine-top {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .scheme-vaccine-top span {
        color: #657681;
        font-size: 0.69rem;
        font-weight: 760;
        letter-spacing: 0.045em;
        text-transform: uppercase;
    }

    .scheme-vaccine-card h3 {
        margin: 0 0 1rem;
        color: #15314A;
        font-size: 1.22rem;
        line-height: 1.3;
    }

    .scheme-dose-label {
        margin-bottom: 0.25rem;
        color: #2C8F78;
        font-size: 0.7rem;
        font-weight: 780;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .scheme-vaccine-card p {
        margin: 0;
        color: #526674;
        line-height: 1.58;
    }

    .scheme-detail-panel {
        margin: 0.45rem 0 0.8rem;
        padding: 1.25rem;
        border: 1px solid #DDE6EA;
        border-radius: 16px;
        background: #F7F9FA;
    }

    .scheme-detail-label {
        color: #2C8F78;
        font-size: 0.69rem;
        font-weight: 780;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .scheme-detail-panel h4 {
        margin: 0.45rem 0 0.9rem;
        color: #15314A;
        font-size: 1.08rem;
    }

    .scheme-detail-panel p {
        color: #596B78;
        font-size: 0.88rem;
        line-height: 1.55;
    }

    .scheme-detail-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .scheme-detail-grid div {
        padding: 0.82rem;
        border: 1px solid #E2E8EC;
        border-radius: 12px;
        background: #FFFFFF;
    }

    .scheme-detail-grid span,
    .scheme-detail-grid strong {
        display: block;
    }

    .scheme-detail-grid span {
        margin-bottom: 0.28rem;
        color: #78858F;
        font-size: 0.66rem;
        font-weight: 760;
        text-transform: uppercase;
    }

    .scheme-detail-grid strong {
        color: #405361;
        font-size: 0.82rem;
        line-height: 1.4;
    }

    .scheme-note {
        margin: 1.25rem 0 0.9rem;
        padding: 1.15rem;
        border-left: 5px solid var(--stage-color);
        border-radius: 0 14px 14px 0;
        background: #F7F9FA;
    }

    .scheme-note span {
        display: block;
        margin-bottom: 0.28rem;
        color: #15314A;
        font-size: 0.75rem;
        font-weight: 780;
        text-transform: uppercase;
    }

    .scheme-note p {
        margin: 0;
        color: #596B78;
        line-height: 1.55;
    }

    .scheme-footer {
        margin-top: 1rem;
        padding: 1.2rem;
        border: 1px solid #DCE5EA;
        border-radius: 16px;
        background: #FFFFFF;
    }

    .scheme-footer strong,
    .scheme-footer span {
        display: block;
    }

    .scheme-footer strong {
        color: #15314A;
    }

    .scheme-footer span {
        margin-top: 0.2rem;
        color: #6A7984;
        font-size: 0.86rem;
    }

    @media (max-width: 760px) {
        .scheme-intro {
            display: block;
        }

        .scheme-source {
            margin-top: 0.65rem;
            text-align: left;
        }

        .stage-option,
        .scheme-vaccine-card,
        .scheme-validation,
        .scheme-hero {
            min-height: auto;
        }

        .scheme-hero {
            padding: 1.45rem;
            border-radius: 18px;
        }

        .scheme-detail-grid {
            grid-template-columns: 1fr;
        }
    }


    .library-title-block {
        margin: 0.3rem 0 1.15rem;
    }

    .library-title-block span {
        display: block;
        margin-bottom: 0.3rem;
        color: #2C8F78;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .library-title-block h1 {
        margin: 0;
        color: #15314A;
        font-size: clamp(2.1rem, 5vw, 3.7rem);
        letter-spacing: -0.05em;
        line-height: 1;
    }

    .library-result-count {
        display: flex;
        align-items: baseline;
        gap: 0.42rem;
        margin: 1rem 0 0.85rem;
        color: #15314A;
    }

    .library-result-count strong {
        font-size: 1.35rem;
    }

    .library-result-count span {
        color: #6D7B85;
        font-size: 0.84rem;
        font-weight: 650;
    }

    .library-index-heading {
        margin: 0 0 0.9rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #DCE5EA;
    }

    .library-index-heading span,
    .library-index-heading strong {
        display: block;
    }

    .library-index-heading span {
        margin-bottom: 0.18rem;
        color: #2C8F78;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.055em;
        text-transform: uppercase;
    }

    .library-index-heading strong {
        color: #15314A;
        font-size: 1rem;
    }

    .library-letter-heading {
        margin: 1.1rem 0 0.45rem;
        color: #2C8F78;
        font-size: 1.55rem;
        font-weight: 800;
        line-height: 1;
    }

    .library-list-item {
        margin-top: 0.38rem;
        padding: 0.92rem 0.95rem;
        border: 1px solid #DFE7EB;
        border-radius: 14px;
        background: #FFFFFF;
    }

    .library-list-item-active {
        border-color: #2C8F78;
        background: #F0F8F5;
    }

    .library-list-item strong,
    .library-list-item span {
        display: block;
    }

    .library-list-item strong {
        color: #15314A;
        font-size: 0.94rem;
    }

    .library-list-item span {
        margin-top: 0.28rem;
        color: #667782;
        font-size: 0.78rem;
        line-height: 1.42;
    }

    .library-empty-state {
        min-height: 540px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 2.3rem;
        border: 1px dashed #C8D4DB;
        border-radius: 22px;
        background: #F8FAFB;
        text-align: center;
    }

    .library-empty-state span {
        color: #2C8F78;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .library-empty-state h2 {
        margin: 0.55rem 0 0.35rem;
        color: #15314A;
        font-size: 1.65rem;
    }

    .library-empty-state p {
        margin: 0;
        color: #6B7983;
    }

    .vaccine-record {
        margin-bottom: 0.95rem;
        padding: 1.7rem;
        border: 1px solid #DCE5EA;
        border-radius: 22px;
        background:
            radial-gradient(circle at 95% 8%, rgba(44, 143, 120, 0.12), transparent 32%),
            #FFFFFF;
        box-shadow: 0 12px 34px rgba(21, 49, 74, 0.07);
    }

    .vaccine-record-top {
        display: flex;
        justify-content: space-between;
        gap: 1.2rem;
        align-items: flex-start;
    }

    .vaccine-record-kicker {
        color: #2C8F78;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.055em;
        text-transform: uppercase;
    }

    .vaccine-record h2 {
        margin: 0.35rem 0 0;
        color: #15314A;
        font-size: clamp(2rem, 4.5vw, 3.15rem);
        letter-spacing: -0.045em;
        line-height: 1.04;
    }

    .vaccine-record-status {
        min-width: 132px;
        padding: 0.82rem;
        border: 1px solid #DCE5EA;
        border-radius: 14px;
        background: rgba(255,255,255,0.86);
        text-align: right;
    }

    .vaccine-record-status span,
    .vaccine-record-status strong {
        display: block;
    }

    .vaccine-record-status span {
        color: #6C7A84;
        font-size: 0.66rem;
        font-weight: 760;
        text-transform: uppercase;
    }

    .vaccine-record-status strong {
        margin-top: 0.2rem;
        color: #15314A;
        font-size: 1.4rem;
    }

    .vaccine-record-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 1.2rem 0;
    }

    .vaccine-record-meta span {
        display: inline-flex;
        padding: 0.34rem 0.62rem;
        border-radius: 999px;
        background: #EEF4F2;
        color: #496459;
        font-size: 0.71rem;
        font-weight: 720;
    }

    .vaccine-record-protection {
        padding-top: 1rem;
        border-top: 1px solid #DFE7EA;
    }

    .vaccine-record-protection span,
    .vaccine-record-protection strong {
        display: block;
    }

    .vaccine-record-protection span {
        margin-bottom: 0.28rem;
        color: #2C8F78;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .vaccine-record-protection strong {
        color: #15314A;
        font-size: 1.06rem;
        line-height: 1.45;
    }

    .vaccine-record-section {
        margin-top: 0.7rem;
        padding: 1.12rem 1.2rem;
        border: 1px solid #DFE7EB;
        border-radius: 16px;
        background: #FFFFFF;
    }

    .vaccine-record-section-accent {
        border-left: 5px solid #2C8F78;
    }

    .vaccine-record-label {
        display: block;
        margin-bottom: 0.35rem;
        color: #2C8F78;
        font-size: 0.69rem;
        font-weight: 800;
        letter-spacing: 0.052em;
        text-transform: uppercase;
    }

    .vaccine-record-section p {
        margin: 0;
        color: #4E6170;
        line-height: 1.58;
    }

    .vaccine-record-split {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.75rem;
        margin-top: 0.75rem;
    }

    .vaccine-record-split div {
        padding: 1.15rem;
        border: 1px solid #DFE7EB;
        border-radius: 16px;
        background: #F7F9FA;
    }

    .vaccine-record-split p {
        margin: 0;
        color: #536674;
        font-size: 0.88rem;
        line-height: 1.55;
    }

    .vaccine-documentation {
        margin: 1rem 0 0.65rem;
        padding: 1.15rem;
        border: 1px solid #DDE7E3;
        border-radius: 16px;
        background: #F3F8F6;
    }

    .vaccine-documentation span,
    .vaccine-documentation strong {
        display: block;
    }

    .vaccine-documentation span {
        color: #2C8F78;
        font-size: 0.69rem;
        font-weight: 800;
        letter-spacing: 0.052em;
        text-transform: uppercase;
    }

    .vaccine-documentation strong {
        margin: 0.35rem 0 0.3rem;
        color: #15314A;
    }

    .vaccine-documentation p {
        margin: 0;
        color: #61717B;
        font-size: 0.84rem;
        line-height: 1.5;
    }

    @media (max-width: 760px) {
        .vaccine-record-top {
            display: block;
        }

        .vaccine-record-status {
            margin-top: 1rem;
            text-align: left;
        }

        .vaccine-record-split {
            grid-template-columns: 1fr;
        }

        .library-empty-state {
            min-height: 300px;
        }
    }


    .library-page-title {
        margin: 0.25rem 0 1.2rem;
    }

    .library-page-title span {
        display: block;
        margin-bottom: 0.32rem;
        color: #2C8F78;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .library-page-title h1 {
        margin: 0;
        color: #15314A;
        font-size: clamp(2.15rem, 5vw, 3.7rem);
        letter-spacing: -0.05em;
        line-height: 1;
    }

    .library-navigator-head {
        margin: 0.35rem 0 1rem;
        padding-bottom: 0.85rem;
        border-bottom: 1px solid #DCE5EA;
    }

    .library-navigator-head span,
    .library-navigator-head strong {
        display: block;
    }

    .library-navigator-head span {
        color: #2C8F78;
        font-size: 0.69rem;
        font-weight: 800;
        letter-spacing: 0.055em;
        text-transform: uppercase;
    }

    .library-navigator-head strong {
        margin-top: 0.22rem;
        color: #15314A;
        font-size: 1rem;
    }

    .library-group-letter {
        margin: 1rem 0 0.42rem;
        color: #2C8F78;
        font-size: 1.45rem;
        font-weight: 800;
    }

    .library-nav-row {
        padding: 0.82rem 0.9rem;
        border-left: 3px solid transparent;
        border-bottom: 1px solid #E7ECEF;
        background: transparent;
    }

    .library-nav-row-active {
        border-left-color: #2C8F78;
        background: #F2F8F6;
    }

    .library-nav-row strong,
    .library-nav-row span {
        display: block;
    }

    .library-nav-row strong {
        color: #15314A;
        font-size: 0.92rem;
    }

    .library-nav-row span {
        margin-top: 0.24rem;
        color: #6A7984;
        font-size: 0.76rem;
        line-height: 1.4;
    }

    .vaccine-dossier {
        margin-bottom: 0;
        padding: 0 0 1.15rem;
        border-bottom: 2px solid #15314A;
    }

    .vaccine-dossier-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1.2rem;
    }

    .vaccine-dossier-kicker {
        display: block;
        color: #2C8F78;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.055em;
        text-transform: uppercase;
    }

    .vaccine-dossier h2 {
        margin: 0.38rem 0 0;
        color: #15314A;
        font-size: clamp(2.2rem, 5vw, 3.85rem);
        letter-spacing: -0.05em;
        line-height: 1;
    }

    .vaccine-dossier-complete {
        min-width: 145px;
        padding: 0.8rem 0 0.8rem 1rem;
        border-left: 1px solid #DCE5EA;
        text-align: right;
    }

    .vaccine-dossier-complete span,
    .vaccine-dossier-complete strong {
        display: block;
    }

    .vaccine-dossier-complete span {
        color: #6C7A84;
        font-size: 0.66rem;
        font-weight: 760;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .vaccine-dossier-complete strong {
        margin-top: 0.22rem;
        color: #15314A;
        font-size: 1.45rem;
    }

    .vaccine-dossier-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.8rem 1.2rem;
        margin-top: 1.2rem;
        color: #5B6E7A;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .vaccine-dossier-section {
        padding: 1.2rem 0;
        border-bottom: 1px solid #DCE5EA;
    }

    .vaccine-dossier-section span {
        display: block;
        margin-bottom: 0.42rem;
        color: #2C8F78;
        font-size: 0.69rem;
        font-weight: 800;
        letter-spacing: 0.055em;
        text-transform: uppercase;
    }

    .vaccine-dossier-section p {
        margin: 0;
        color: #445968;
        font-size: 0.98rem;
        line-height: 1.66;
    }

    .vaccine-dossier-documentation {
        margin: 1.1rem 0 0.7rem;
        padding: 1rem 0;
        border-top: 2px solid #15314A;
        border-bottom: 1px solid #DCE5EA;
    }

    .vaccine-dossier-documentation span,
    .vaccine-dossier-documentation strong {
        display: block;
    }

    .vaccine-dossier-documentation span {
        color: #2C8F78;
        font-size: 0.69rem;
        font-weight: 800;
        letter-spacing: 0.055em;
        text-transform: uppercase;
    }

    .vaccine-dossier-documentation strong {
        margin: 0.35rem 0 0.25rem;
        color: #15314A;
        font-size: 1rem;
    }

    .vaccine-dossier-documentation p {
        margin: 0;
        color: #667781;
        font-size: 0.84rem;
        line-height: 1.5;
    }

    @media (max-width: 760px) {
        .vaccine-dossier-header {
            display: block;
        }

        .vaccine-dossier-complete {
            margin-top: 1rem;
            padding-left: 0;
            border-left: 0;
            text-align: left;
        }

        .vaccine-dossier-meta {
            display: block;
        }

        .vaccine-dossier-meta span {
            display: block;
            margin-top: 0.35rem;
        }
    }


    /* Portales Profesional e Inteligencia Sanitaria */
    .portal-hero {
        margin: 0.35rem 0 1.5rem;
        padding: 1.65rem 1.75rem;
        border: 1px solid #D8E3E8;
        border-left: 6px solid #15314A;
        border-radius: 18px;
        background: linear-gradient(135deg, #F8FBFC 0%, #EEF5F4 100%);
    }

    .portal-hero-intelligence {
        border-left-color: #2C8F78;
        background: linear-gradient(135deg, #F7FBFA 0%, #EAF5F1 100%);
    }

    .portal-eyebrow {
        color: #2C8F78;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.065em;
        text-transform: uppercase;
    }

    .portal-hero h1 {
        margin: 0.35rem 0 0.65rem;
        color: #15314A;
        font-size: clamp(2rem, 4.5vw, 3.45rem);
        line-height: 1.02;
        letter-spacing: -0.045em;
    }

    .portal-hero p {
        max-width: 900px;
        margin: 0;
        color: #506675;
        font-size: 1rem;
        line-height: 1.62;
    }

    .portal-band {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0 0 1.35rem;
    }

    .portal-metric {
        padding: 1rem 1.05rem;
        border: 1px solid #DCE5EA;
        border-radius: 14px;
        background: #FFFFFF;
    }

    .portal-metric span,
    .portal-metric strong {
        display: block;
    }

    .portal-metric span {
        color: #6A7B86;
        font-size: 0.68rem;
        font-weight: 780;
        letter-spacing: 0.045em;
        text-transform: uppercase;
    }

    .portal-metric strong {
        margin-top: 0.3rem;
        color: #15314A;
        font-size: 1.2rem;
    }

    .module-card {
        min-height: 180px;
        margin-bottom: 0.55rem;
        padding: 1.15rem;
        border: 1px solid #DCE5EA;
        border-top: 4px solid #2C8F78;
        border-radius: 16px;
        background: #FFFFFF;
        box-shadow: 0 7px 22px rgba(21, 49, 74, 0.055);
    }

    .module-card h3 {
        margin: 0 0 0.55rem;
        color: #15314A;
        font-size: 1.06rem;
    }

    .module-card p {
        margin: 0;
        color: #60727D;
        font-size: 0.88rem;
        line-height: 1.52;
    }

    .technical-sheet {
        padding: 1.35rem 1.4rem;
        border: 1px solid #D8E3E8;
        border-radius: 16px;
        background: #FFFFFF;
    }

    .technical-sheet h3 {
        margin: 0 0 0.35rem;
        color: #15314A;
        font-size: 1.35rem;
    }

    .technical-sheet > p {
        margin: 0 0 1rem;
        color: #647580;
        line-height: 1.55;
    }

    .technical-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0;
        border-top: 1px solid #DCE5EA;
    }

    .technical-field {
        padding: 0.95rem 0;
        border-bottom: 1px solid #DCE5EA;
    }

    .technical-field:nth-child(odd) {
        padding-right: 1.1rem;
        border-right: 1px solid #DCE5EA;
    }

    .technical-field:nth-child(even) {
        padding-left: 1.1rem;
    }

    .technical-field span,
    .technical-field strong {
        display: block;
    }

    .technical-field span {
        color: #2C8F78;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .technical-field strong {
        margin-top: 0.3rem;
        color: #435866;
        font-size: 0.9rem;
        line-height: 1.48;
    }

    .decision-panel {
        padding: 1.15rem 1.2rem;
        border-left: 5px solid #2C8F78;
        border-radius: 12px;
        background: #F0F7F5;
    }

    .decision-panel strong {
        color: #15314A;
    }

    .decision-panel p {
        margin: 0.35rem 0 0;
        color: #536975;
        line-height: 1.55;
    }

    .data-quality {
        padding: 0.9rem 1rem;
        border: 1px solid #E2D6B2;
        border-radius: 12px;
        background: #FFF9E9;
        color: #63552C;
        font-size: 0.86rem;
        line-height: 1.5;
    }

    .analytics-card {
        min-height: 150px;
        padding: 1.1rem;
        border: 1px solid #DCE5EA;
        border-radius: 15px;
        background: #FFFFFF;
    }

    .analytics-card span {
        display: block;
        color: #2C8F78;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .analytics-card h3 {
        margin: 0.38rem 0 0.42rem;
        color: #15314A;
        font-size: 1.12rem;
    }

    .analytics-card p {
        margin: 0;
        color: #61737F;
        font-size: 0.86rem;
        line-height: 1.48;
    }

    @media (max-width: 900px) {
        .portal-band {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 680px) {
        .portal-band,
        .technical-grid {
            grid-template-columns: 1fr;
        }

        .technical-field:nth-child(odd),
        .technical-field:nth-child(even) {
            padding-left: 0;
            padding-right: 0;
            border-right: 0;
        }
    }

</style>
    """,
    unsafe_allow_html=True,
)


def nav() -> None:
    citizen_labels = [
        "Inicio",
        "Esquemas de vacunación",
        "Mi registro oficial",
        "Biblioteca de vacunas",
        "Centros de vacunación",
        "Información",
        "Novedades",
        "Fuentes oficiales",
    ]
    portal_labels = ["Profesionales e instituciones"]
    all_labels = citizen_labels + portal_labels

    if st.session_state.section not in all_labels:
        st.session_state.section = "Inicio"

    if (
        "mobile_navigation" not in st.session_state
        or st.session_state.mobile_navigation not in all_labels
    ):
        st.session_state.mobile_navigation = st.session_state.section

    def change_mobile_section() -> None:
        selected = st.session_state.mobile_navigation
        if selected in all_labels:
            st.session_state.section = selected

    def open_section(label: str) -> None:
        st.session_state.section = label
        st.session_state.mobile_navigation = label

    st.selectbox(
        "Sección",
        all_labels,
        key="mobile_navigation",
        on_change=change_mobile_section,
    )

    st.markdown(
        '<div class="section-label desktop-nav-label">Portal ciudadano</div>',
        unsafe_allow_html=True,
    )
    with st.container(key="desktop_citizen_navigation"):
        citizen_cols = st.columns(4)
        for index, label in enumerate(citizen_labels):
            with citizen_cols[index % 4]:
                st.button(
                    label,
                    use_container_width=True,
                    key=f"nav_{label}",
                    disabled=st.session_state.section == label,
                    on_click=open_section,
                    args=(label,),
                )

    st.markdown(
        '<div class="section-label desktop-nav-label" style="margin-top:0.8rem">Portales especializados</div>',
        unsafe_allow_html=True,
    )
    with st.container(key="desktop_professional_navigation"):
        st.button(
            portal_labels[0],
            use_container_width=True,
            key=f"nav_{portal_labels[0]}",
            disabled=st.session_state.section == portal_labels[0],
            on_click=open_section,
            args=(portal_labels[0],),
        )


def heading(label: str, title: str, copy: str = "") -> None:
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if copy:
        st.markdown(f'<div class="section-copy">{copy}</div>', unsafe_allow_html=True)


def render_home() -> None:
    st.markdown(
        f"""
        <section class="hero">
            <div class="hero-eyebrow">{APP_SUBTITLE}</div>
            <h1>{APP_NAME}</h1>
            <h2>{APP_SUBTITLE}</h2>
            <p>{APP_SLOGAN}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    heading("Accesos", "Consultá la plataforma")
    cards = [
        ("Esquemas de vacunación", "Consulta visual de vacunas, dosis y momentos de aplicación.", "#E9A8C4"),
        ("Biblioteca de vacunas", "Biblioteca de vacunas con esquema y fuente.", "#78C6E7"),
        ("Centros de vacunación", "Buscador territorial, mapa y acceso directo a cada centro.", "#73D3C6"),
        ("Información", "Preguntas frecuentes y cuidados del carnet.", "#F3C65D"),
        ("Novedades", "Campañas y avisos oficiales.", "#A997E7"),
        ("Fuentes oficiales", "Origen y actualización de cada contenido.", "#8CCB85"),
        ("Mi registro oficial", "Acceso seguro a los servicios oficiales de consulta.", "#68B8D8"),
        ("Profesionales e instituciones", "Consulta técnica, capacitación, inteligencia sanitaria y herramientas de gestión con acceso según perfil.", "#15314A"),
    ]
    cols = st.columns(4)
    for i, (title, desc, accent) in enumerate(cards):
        with cols[i % 4]:
            st.markdown(
                f'<div class="vaccine-card" style="border-top:5px solid {accent}"><h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )
            st.button(
                f"Abrir {title}",
                key=f"home_{title}",
                use_container_width=True,
                on_click=lambda destination=title: (
                    st.session_state.__setitem__("section", destination),
                    st.session_state.__setitem__("mobile_navigation", destination),
                ),
            )



def render_calendar() -> None:
    heading(
        "Vacunación",
        "Esquemas de vacunación",
        "Seleccioná una etapa y consultá únicamente las vacunas que corresponden a ese momento.",
    )

    stage_names = list(STAGES.keys())

    if st.session_state.selected_stage not in stage_names:
        st.session_state.selected_stage = stage_names[0]

    st.markdown(
        """
        <div class="scheme-intro">
            <div>
                <span class="scheme-kicker">Consulta guiada</span>
                <strong>Una etapa por vez. Información clara y verificable.</strong>
            </div>
            <span class="scheme-source">Calendario Nacional de Vacunación</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="scheme-step">1. Seleccioná una etapa</div>', unsafe_allow_html=True)

    stage_columns = st.columns(4)

    for index, (name, data) in enumerate(STAGES.items()):
        is_active = name == st.session_state.selected_stage
        state_class = " stage-option-active" if is_active else ""

        with stage_columns[index % 4]:
            st.markdown(
                f"""
                <div class="stage-option{state_class}"
                     style="--stage-color:{data['color']};--stage-soft:{data['soft']}">
                    <span class="stage-option-status">
                        {"Etapa seleccionada" if is_active else "Etapa de vacunación"}
                    </span>
                    <h3>{name}</h3>
                    <p>{data['subtitle']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Seleccionada" if is_active else "Consultar etapa",
                key=f"scheme_stage_{index}",
                use_container_width=True,
                disabled=is_active,
            ):
                st.session_state.selected_stage = name
                st.session_state.selected_vaccine = None
                st.rerun()

    selected_stage = st.session_state.selected_stage
    data = STAGES[selected_stage]

    st.markdown('<div class="scheme-step">2. Consultá el esquema</div>', unsafe_allow_html=True)

    summary_col, source_col = st.columns([1.45, 0.75])

    with summary_col:
        st.markdown(
            f"""
            <section class="scheme-hero"
                     style="--stage-color:{data['color']};--stage-soft:{data['soft']}">
                <span class="scheme-hero-label">Etapa seleccionada</span>
                <h2>{selected_stage}</h2>
                <p class="scheme-hero-subtitle">{data['subtitle']}</p>
                <p class="scheme-hero-copy">{data['intro']}</p>
                <div class="scheme-metric">
                    <strong>{len(data["items"])}</strong>
                    <span>{"vacuna o indicación" if len(data["items"]) == 1 else "vacunas o indicaciones"}</span>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with source_col:
        st.markdown(
            f"""
            <aside class="scheme-validation">
                <span>Contenido institucional</span>
                <strong>Fuente oficial vinculada</strong>
                <p>La información se presenta de forma resumida. La evaluación individual corresponde al equipo de salud.</p>
            </aside>
            """,
            unsafe_allow_html=True,
        )
        st.link_button(
            "Abrir fuente oficial",
            data["source"],
            use_container_width=True,
        )

    search_term = st.text_input(
        "Buscar dentro de esta etapa",
        placeholder="Nombre de vacuna o indicación...",
        key=f"scheme_search_{selected_stage}",
    ).strip().lower()

    visible_items = [
        (label, item_text)
        for label, item_text in data["items"]
        if not search_term
        or search_term in f"{label} {item_text}".lower()
    ]

    if not visible_items:
        st.info("No se encontraron coincidencias dentro de la etapa seleccionada.")
    else:
        st.markdown(
            f'<div class="scheme-results">Se muestran {len(visible_items)} resultados para {selected_stage}.</div>',
            unsafe_allow_html=True,
        )

        for row_start in range(0, len(visible_items), 2):
            columns = st.columns(2)

            for column, (label, item_text) in zip(
                columns,
                visible_items[row_start:row_start + 2],
            ):
                detail_match = next(
                    (
                        vaccine
                        for vaccine in VACCINES
                        if vaccine["name"].lower() == label.lower()
                        or label.lower() in vaccine["name"].lower()
                        or vaccine["name"].lower() in label.lower()
                    ),
                    None,
                )

                with column:
                    st.markdown(
                        f"""
                        <article class="scheme-vaccine-card"
                                 style="--stage-color:{data['color']};--stage-soft:{data['soft']}">
                            <div class="scheme-vaccine-top">
                                <span>Calendario Nacional</span>
                                <span>{selected_stage}</span>
                            </div>
                            <h3>{label}</h3>
                            <div class="scheme-dose-label">Momento o esquema</div>
                            <p>{item_text}</p>
                        </article>
                        """,
                        unsafe_allow_html=True,
                    )

                    detail_key = hashlib.md5(
                        f"{selected_stage}-{label}".encode("utf-8")
                    ).hexdigest()[:10]

                    if st.button(
                        "Cerrar información"
                        if st.session_state.selected_vaccine == detail_key
                        else "Ver información",
                        key=f"scheme_detail_{detail_key}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_vaccine = (
                            None
                            if st.session_state.selected_vaccine == detail_key
                            else detail_key
                        )
                        st.rerun()

                    if st.session_state.selected_vaccine == detail_key:
                        if detail_match:
                            st.markdown(
                                f"""
                                <div class="scheme-detail-panel">
                                    <span class="scheme-detail-label">Información ampliada</span>
                                    <h4>{detail_match["name"]}</h4>
                                    <div class="scheme-detail-grid">
                                        <div>
                                            <span>Protege contra</span>
                                            <strong>{detail_match["protects"]}</strong>
                                        </div>
                                        <div>
                                            <span>Población objetivo</span>
                                            <strong>{detail_match["who"]}</strong>
                                        </div>
                                        <div>
                                            <span>Esquema</span>
                                            <strong>{detail_match["scheme"]}</strong>
                                        </div>
                                        <div>
                                            <span>Vía de administración</span>
                                            <strong>{detail_match["route"]}</strong>
                                        </div>
                                    </div>
                                    <p>{detail_match["details"]}</p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            st.link_button(
                                "Consultar ficha oficial",
                                detail_match["source"],
                                use_container_width=True,
                                key=f"scheme_source_{detail_key}",
                            )
                        else:
                            st.markdown(
                                f"""
                                <div class="scheme-detail-panel">
                                    <span class="scheme-detail-label">Información de la etapa</span>
                                    <h4>{label}</h4>
                                    <p>{item_text}</p>
                                    <p>Para validar antecedentes, intervalos o situaciones particulares, consultá al equipo de vacunación.</p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

    st.markdown(
        f"""
        <div class="scheme-note" style="--stage-color:{data['color']}">
            <span>Información importante</span>
            <p>{data["note"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="scheme-footer">
            <strong>¿Necesitás saber dónde consultar?</strong>
            <span>Accedé al buscador territorial de centros de vacunación.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "Ver centros de vacunación",
        key="scheme_to_centers",
        use_container_width=True,
    ):
        st.session_state.section = "Centros de vacunación"
        st.rerun()





def render_vaccines() -> None:
    st.markdown(
        '<div class="library-page-title">'
        '<span>Repositorio institucional</span>'
        '<h1>Biblioteca de vacunas</h1>'
        '</div>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Buscar",
        placeholder="Buscar por vacuna, enfermedad o población...",
        key="library_search",
        label_visibility="collapsed",
    ).strip().lower()

    ordered_vaccines = sorted(VACCINES, key=lambda item: item["name"].lower())
    available_letters = sorted(
        {item["name"][0].upper() for item in ordered_vaccines if item.get("name")}
    )

    alpha_options = ["Todas"] + available_letters
    alpha_cols = st.columns(min(len(alpha_options), 9))

    for index, letter in enumerate(alpha_options):
        with alpha_cols[index % len(alpha_cols)]:
            active = st.session_state.library_letter == letter

            if st.button(
                "A–Z" if letter == "Todas" else letter,
                key=f"library_alpha_{letter}",
                use_container_width=True,
                disabled=active,
            ):
                st.session_state.library_letter = letter
                st.session_state.library_vaccine = None
                st.rerun()

    filtered = []

    for vaccine in ordered_vaccines:
        searchable = " ".join(
            [
                vaccine.get("name", ""),
                vaccine.get("protects", ""),
                vaccine.get("stage", ""),
                vaccine.get("who", ""),
                vaccine.get("scheme", ""),
                vaccine.get("route", ""),
                vaccine.get("details", ""),
                vaccine.get("expected", ""),
                vaccine.get("precautions", ""),
            ]
        ).lower()

        matches_query = not query or query in searchable
        matches_letter = (
            st.session_state.library_letter == "Todas"
            or vaccine.get("name", "").upper().startswith(
                st.session_state.library_letter
            )
        )

        if matches_query and matches_letter:
            filtered.append(vaccine)

    if not filtered:
        st.info("No se encontraron vacunas con esos criterios.")
        return

    visible_names = {vaccine["name"] for vaccine in filtered}

    if st.session_state.library_vaccine not in visible_names:
        st.session_state.library_vaccine = filtered[0]["name"]

    selected = next(
        vaccine
        for vaccine in filtered
        if vaccine["name"] == st.session_state.library_vaccine
    )

    navigator_col, record_col = st.columns([0.72, 1.78], gap="large")

    with navigator_col:
        result_word = "vacuna" if len(filtered) == 1 else "vacunas"

        st.markdown(
            '<div class="library-navigator-head">'
            '<span>Índice</span>'
            f'<strong>{len(filtered)} {result_word}</strong>'
            '</div>',
            unsafe_allow_html=True,
        )

        grouped: Dict[str, List[dict]] = {}

        for vaccine in filtered:
            initial = vaccine["name"][0].upper()
            grouped.setdefault(initial, []).append(vaccine)

        for letter, vaccines in grouped.items():
            st.markdown(
                f'<div class="library-group-letter">{escape(letter)}</div>',
                unsafe_allow_html=True,
            )

            for vaccine in vaccines:
                vaccine_name = vaccine["name"]
                active = st.session_state.library_vaccine == vaccine_name
                active_class = " library-nav-row-active" if active else ""

                st.markdown(
                    f'<div class="library-nav-row{active_class}">'
                    f'<strong>{escape(vaccine_name)}</strong>'
                    f'<span>{escape(vaccine.get("protects", ""))}</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                button_key = hashlib.md5(
                    vaccine_name.encode("utf-8")
                ).hexdigest()[:10]

                if st.button(
                    "Seleccionada" if active else "Abrir",
                    key=f"library_nav_{button_key}",
                    use_container_width=True,
                    disabled=active,
                ):
                    st.session_state.library_vaccine = vaccine_name
                    st.rerun()

    with record_col:
        completed_fields = sum(
            bool(selected.get(field))
            for field in [
                "protects",
                "who",
                "scheme",
                "route",
                "details",
                "expected",
                "precautions",
                "source",
            ]
        )
        completeness = round(completed_fields / 8 * 100)

        name = escape(selected.get("name", ""))
        stage = escape(selected.get("stage", ""))
        protects = escape(selected.get("protects", ""))
        who = escape(selected.get("who", ""))
        scheme = escape(selected.get("scheme", ""))
        route = escape(selected.get("route", ""))
        details = escape(selected.get("details", ""))
        expected = escape(selected.get("expected", ""))
        precautions = escape(selected.get("precautions", ""))

        st.markdown(
            '<section class="vaccine-dossier">'
            '<div class="vaccine-dossier-header">'
            '<div>'
            '<span class="vaccine-dossier-kicker">Expediente institucional</span>'
            f'<h2>{name}</h2>'
            '</div>'
            '<div class="vaccine-dossier-complete">'
            '<span>Contenido documentado</span>'
            f'<strong>{completeness}%</strong>'
            '</div>'
            '</div>'
            '<div class="vaccine-dossier-meta">'
            '<span>Calendario Nacional</span>'
            '<span>Información vigente</span>'
            f'<span>{stage}</span>'
            '</div>'
            '</section>',
            unsafe_allow_html=True,
        )

        dossier_sections = [
            ("Protección", protects),
            ("Población objetivo", who),
            ("Esquema", scheme),
            ("Administración", route),
            ("Información principal", details),
            ("Efectos esperables", expected),
            ("Precauciones", precautions),
        ]

        for title, text in dossier_sections:
            st.markdown(
                '<section class="vaccine-dossier-section">'
                f'<span>{escape(title)}</span>'
                f'<p>{text or "Información no disponible."}</p>'
                '</section>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<section class="vaccine-dossier-documentation">'
            '<span>Documentación oficial</span>'
            '<strong>Fuente sanitaria vinculada</strong>'
            '<p>La ficha resume información oficial y no reemplaza '
            'la evaluación individual del equipo de salud.</p>'
            '</section>',
            unsafe_allow_html=True,
        )

        source_url = selected.get("source", "")

        if source_url:
            st.link_button(
                "Abrir documentación oficial",
                source_url,
                use_container_width=True,
                key=(
                    "library_source_"
                    + hashlib.md5(
                        selected["name"].encode("utf-8")
                    ).hexdigest()[:10]
                ),
            )
        else:
            st.info("La fuente oficial de esta ficha todavía no está vinculada.")

        action_col_1, action_col_2 = st.columns(2)

        with action_col_1:
            if st.button(
                "Ver esquemas de vacunación",
                key="library_go_schemes",
                use_container_width=True,
            ):
                st.session_state.section = "Esquemas de vacunación"
                st.rerun()

        with action_col_2:
            if st.button(
                "Ver centros de vacunación",
                key="library_go_centers",
                use_container_width=True,
            ):
                st.session_state.section = "Centros de vacunación"
                st.rerun()


def render_centers() -> None:
    heading(
        "Territorio",
        "Centros de vacunación",
        "Buscá establecimientos, consultá su ubicación y accedé al recorrido.",
    )

    st.markdown(
        """
        <div class="centers-intro">
            <strong>Información territorial de San Francisco.</strong>
            Los horarios y la disponibilidad de vacunas pueden cambiar. Confirmá los datos
            con el establecimiento antes de concurrir.
        </div>
        """,
        unsafe_allow_html=True,
    )

    location_result = streamlit_geolocation()

    if isinstance(location_result, dict):
        latitude = location_result.get("latitude")
        longitude = location_result.get("longitude")

        if latitude is not None and longitude is not None:
            st.session_state.user_location = {
                "lat": float(latitude),
                "lon": float(longitude),
            }

    search_col, type_col = st.columns([1.55, 0.85])

    with search_col:
        search = st.text_input(
            "Buscar",
            placeholder="Centro, calle o barrio...",
            key="center_search_professional",
        )

    with type_col:
        selected_type = st.selectbox(
            "Tipo de establecimiento",
            ["Todos"] + sorted({center["type"] for center in CENTERS}),
            key="center_type_filter",
        )

    filtered_centers = []
    normalized_search = search.strip().lower()

    for center in CENTERS:
        matches_search = (
            not normalized_search
            or normalized_search
            in f"{center['name']} {center['address']} {center['type']}".lower()
        )
        matches_type = selected_type == "Todos" or center["type"] == selected_type

        if matches_search and matches_type:
            filtered_centers.append(center)

    if not filtered_centers:
        st.info("No se encontraron centros con los criterios seleccionados.")
        return

    user_location = st.session_state.user_location

    if user_location:
        ranked_centers = nearest_centers(
            user_location["lat"],
            user_location["lon"],
            filtered_centers,
        )
        map_center = [user_location["lat"], user_location["lon"]]
        map_zoom = 14
        nearest = ranked_centers[0]
    else:
        ranked_centers = filtered_centers
        map_center = [-31.427, -62.086]
        map_zoom = 13
        nearest = None

    total_label = (
        "1 centro encontrado"
        if len(ranked_centers) == 1
        else f"{len(ranked_centers)} centros encontrados"
    )

    summary_col, location_col = st.columns([1, 1])

    with summary_col:
        st.markdown(
            f"""
            <div class="center-summary-card">
                <span class="center-summary-label">Resultados</span>
                <strong>{total_label}</strong>
                <span>San Francisco, Córdoba</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with location_col:
        if nearest:
            st.markdown(
                f"""
                <div class="center-summary-card">
                    <span class="center-summary-label">Más cercano</span>
                    <strong>{nearest["name"]}</strong>
                    <span>{nearest["distance_km"]:.2f} km aproximadamente</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="center-summary-card">
                    <span class="center-summary-label">Ubicación</span>
                    <strong>Activá el permiso del navegador</strong>
                    <span>Podrás ordenar los centros por cercanía.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    map_object = folium.Map(
        location=map_center,
        zoom_start=map_zoom,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Mapa",
        control=False,
    ).add_to(map_object)

    if user_location:
        folium.Circle(
            location=[user_location["lat"], user_location["lon"]],
            radius=65,
            tooltip="Ubicación aproximada",
            color="#15314A",
            weight=2,
            fill=True,
            fill_color="#15314A",
            fill_opacity=0.16,
        ).add_to(map_object)

        folium.CircleMarker(
            location=[user_location["lat"], user_location["lon"]],
            radius=6,
            tooltip="Tu ubicación",
            color="#15314A",
            weight=2,
            fill=True,
            fill_color="#15314A",
            fill_opacity=1,
        ).add_to(map_object)

    marker_group = folium.FeatureGroup(name="Centros de vacunación")

    for position, center in enumerate(ranked_centers, start=1):
        distance_html = ""
        if user_location:
            distance_html = (
                f"<div style='margin-top:8px;color:#526472;'>"
                f"Distancia aproximada: <strong>{center['distance_km']:.2f} km</strong>"
                f"</div>"
            )

        maps_url = (
            "https://www.google.com/maps/dir/?api=1&destination="
            f"{center['lat']},{center['lon']}"
        )

        popup_html = f"""
        <div style="font-family:Arial,sans-serif;width:275px;padding:4px 2px;">
            <div style="font-size:11px;font-weight:700;color:#2C8F78;
                        text-transform:uppercase;letter-spacing:.04em;">
                {center["type"]}
            </div>
            <div style="font-size:17px;font-weight:700;color:#15314A;
                        margin:5px 0 8px;">
                {center["name"]}
            </div>
            <div style="font-size:13px;line-height:1.55;color:#4F6070;">
                {center["address"]}<br>
                {center["phone"]}<br>
                {center["schedule"]}
            </div>
            {distance_html}
            <a href="{maps_url}" target="_blank"
               style="display:inline-block;margin-top:12px;color:#176B59;
                      font-weight:700;text-decoration:none;">
                Cómo llegar
            </a>
        </div>
        """

        folium.CircleMarker(
            location=[center["lat"], center["lon"]],
            radius=9 if position == 1 and user_location else 7,
            popup=folium.Popup(popup_html, max_width=330),
            tooltip=center["name"],
            color="#176B59",
            weight=2,
            fill=True,
            fill_color="#2C8F78",
            fill_opacity=0.94,
        ).add_to(marker_group)

    marker_group.add_to(map_object)

    if user_location and nearest:
        folium.PolyLine(
            [
                [user_location["lat"], user_location["lon"]],
                [nearest["lat"], nearest["lon"]],
            ],
            color="#15314A",
            weight=2,
            opacity=0.5,
            dash_array="7, 7",
        ).add_to(map_object)

    st.markdown("### Mapa territorial")
    st_folium(
        map_object,
        width=None,
        height=530,
        returned_objects=[],
        key="professional_centers_map",
    )

    st.caption(
        "La distancia se calcula en línea recta y puede diferir del recorrido real."
        if user_location
        else "Permití el acceso a tu ubicación para ordenar los centros por cercanía."
    )

    st.markdown(
        "### Centros ordenados por cercanía"
        if user_location
        else "### Directorio de centros"
    )

    for index in range(0, len(ranked_centers), 2):
        columns = st.columns(2)

        for column, center in zip(columns, ranked_centers[index:index + 2]):
            distance_label = ""
            if user_location:
                distance_label = (
                    f'<span class="center-distance">'
                    f'{center["distance_km"]:.2f} km aprox.</span>'
                )

            maps_url = (
                "https://www.google.com/maps/dir/?api=1&destination="
                f"{center['lat']},{center['lon']}"
            )
            phone_link = re.sub(r"[^0-9+]", "", center["phone"].split("/")[0])

            with column:
                st.markdown(
                    f"""
                    <article class="center-card">
                        <div class="center-card-header">
                            <span class="center-type">{center["type"]}</span>
                            {distance_label}
                        </div>
                        <h3>{center["name"]}</h3>
                        <div class="center-address">{center["address"]}</div>
                        <div class="center-detail">
                            <span>Horario</span>
                            <strong>{center["schedule"]}</strong>
                        </div>
                        <div class="center-detail">
                            <span>Teléfono</span>
                            <strong>{center["phone"]}</strong>
                        </div>
                        <div class="center-verification">
                            {center["availability"]}
                        </div>
                    </article>
                    """,
                    unsafe_allow_html=True,
                )

                action_col_1, action_col_2 = st.columns(2)

                with action_col_1:
                    st.link_button(
                        "Cómo llegar",
                        maps_url,
                        use_container_width=True,
                        key=f"route_{center['name']}",
                    )

                with action_col_2:
                    st.link_button(
                        "Llamar",
                        f"tel:{phone_link}",
                        use_container_width=True,
                        key=f"call_{center['name']}",
                    )


def render_information() -> None:
    heading("Información", "Información útil")
    st.markdown(
        '<div class="notice">La plataforma no registra datos personales, no gestiona turnos, '
        'no reemplaza el carnet y no emite indicaciones clínicas individuales.</div>',
        unsafe_allow_html=True,
    )
    topics = {
        "¿Dónde están disponibles las vacunas?": "Las vacunas del Calendario Nacional están disponibles gratuitamente en vacunatorios, centros de salud y hospitales públicos.",
        "¿Puedo recibir más de una vacuna el mismo día?": "Distintas vacunas pueden administrarse el mismo día. La decisión final corresponde al equipo de salud.",
        "¿Qué síntomas pueden aparecer?": "Puede presentarse dolor, enrojecimiento o inflamación en el lugar de aplicación. Algunas personas presentan fiebre o decaimiento.",
        "¿Qué hago si perdí el carnet?": "Consultá en el vacunatorio o establecimiento donde recibiste las dosis y revisá los registros disponibles.",
        "¿Debo reiniciar un esquema atrasado?": "No. El equipo de salud revisará antecedentes y completará el esquema según corresponda.",
        "¿Qué debo llevar?": "DNI y carnet de vacunación, si lo tenés disponible.",
        "¿La plataforma reemplaza la consulta?": "No. La información es pública y general. La revisión individual corresponde al equipo de salud.",
    }
    for question, answer in topics.items():
        with st.expander(question):
            st.write(answer)
    st.link_button("Ver preguntas frecuentes oficiales", "https://www.argentina.gob.ar/salud/vacunas/preguntas-frecuentes")



def render_news() -> None:
    heading(
        "Actualizaciones",
        "Centro de actualizaciones oficiales",
        "Campañas, noticias y comunicados relevantes sobre vacunación.",
    )

    st.markdown(
        f"""<div class="notice">
            Información revisada el <strong>{LAST_CONTENT_REVIEW}</strong>.
            Consultá siempre la publicación oficial para conocer el detalle completo.
        </div>""",
        unsafe_allow_html=True,
    )

    ordered_items = sorted(NEWS_ITEMS, key=lambda item: item["priority"])
    featured = next(
        (item for item in ordered_items if item.get("featured")),
        ordered_items[0],
    )

    st.markdown(
        f"""
        <section class="news-featured">
            <div class="news-featured-label">{featured.get("status", "Destacado")}</div>
            <div class="news-featured-meta">
                {featured["institution"]} · {featured["date"]}
            </div>
            <h2>{featured["title"]}</h2>
            <p>{featured["summary"]}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "Ver actualización destacada",
        featured["url"],
        use_container_width=True,
        key="featured_news_link",
    )

    st.markdown("### Explorar actualizaciones")

    control_col, search_col = st.columns([1.1, 1.4])
    category_options = ["Todas"] + sorted(
        {item["category"] for item in ordered_items}
    )

    with control_col:
        selected_category = st.selectbox(
            "Categoría",
            category_options,
            index=0,
            key="news_category",
        )

    with search_col:
        search_term = st.text_input(
            "Buscar",
            placeholder="Ej.: gripe, sarampión, calendario...",
            key="news_search",
        )

    normalized_search = search_term.strip().lower()

    filtered_items = []
    for item in ordered_items:
        matches_category = (
            selected_category == "Todas"
            or item["category"] == selected_category
        )
        searchable_text = " ".join(
            [
                item["title"],
                item["summary"],
                item["institution"],
                item["category"],
                item.get("status", ""),
            ]
        ).lower()
        matches_search = (
            not normalized_search
            or normalized_search in searchable_text
        )

        if matches_category and matches_search:
            filtered_items.append(item)

    if not filtered_items:
        st.info("No se encontraron actualizaciones con esos criterios.")
        return

    st.caption(
        f"{len(filtered_items)} "
        f"{'publicación disponible' if len(filtered_items) == 1 else 'publicaciones disponibles'}"
    )

    for index in range(0, len(filtered_items), 2):
        columns = st.columns(2)

        for column, item in zip(columns, filtered_items[index:index + 2]):
            with column:
                st.markdown(
                    f"""
                    <article class="news-card">
                        <div class="news-card-topline">
                            <span class="news-status">{item.get("status", item["category"])}</span>
                            <span class="news-category">{item["category"]}</span>
                        </div>
                        <h3>{item["title"]}</h3>
                        <p>{item["summary"]}</p>
                        <div class="news-meta">
                            {item["institution"]} · {item["date"]}
                        </div>
                    </article>
                    """,
                    unsafe_allow_html=True,
                )
                st.link_button(
                    "Ver publicación oficial",
                    item["url"],
                    use_container_width=True,
                    key=f"news_link_{item['priority']}",
                )

    st.markdown(
        """
        <div class="news-local-note">
            Para campañas, jornadas y horarios en San Francisco, confirmá la información
            con el establecimiento de salud antes de concurrir.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_official_record() -> None:
    heading(
        "Acceso oficial",
        "Mi registro oficial de vacunación",
        "Consultá tus dosis directamente en los portales gubernamentales habilitados.",
    )

    st.markdown(
        """
        <div class="notice">
            Esta plataforma no solicita ni almacena DNI, usuarios, contraseñas,
            credenciales de CiDi, datos clínicos ni antecedentes de vacunación.
            Cada acceso se abre directamente en el sistema oficial correspondiente.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Consulta ciudadana")
    st.write(
        "Usá estos accesos para revisar la información de vacunación disponible "
        "en los servicios oficiales."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.link_button(
            "Consultar mis vacunas en Córdoba",
            CORDOBA_VACCINATION_URL,
            use_container_width=True,
        )
    with col2:
        st.link_button(
            "Ingresar a Mi Argentina",
            MI_ARGENTINA_URL,
            use_container_width=True,
        )




def render_professional_area() -> None:
    st.markdown(
        """
        <section class="portal-hero">
            <div class="portal-eyebrow">Entorno especializado</div>
            <h1>Portal profesional</h1>
            <p>
                Consulta técnica para vacunadores, enfermería, medicina, farmacia,
                epidemiología, docencia y equipos de gestión. La información se organiza
                por práctica, decisión y fuente oficial, sin alterar el Portal Ciudadano.
            </p>
        </section>
        <div class="portal-band">
            <div class="portal-metric"><span>Alcance</span><strong>Práctica clínica</strong></div>
            <div class="portal-metric"><span>Base</span><strong>Fuentes oficiales</strong></div>
            <div class="portal-metric"><span>Control</span><strong>Versionado</strong></div>
            <div class="portal-metric"><span>Uso</span><strong>Formación y consulta</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    modules = [
        ("Centro técnico", "Fichas profesionales, dosis, vía, sitio, intervalos, coadministración y situaciones especiales."),
        ("Manual del vacunador", "Procedimientos, preparación, administración segura, registro y buenas prácticas."),
        ("ESAVI", "Definiciones, clasificación, evaluación inicial, notificación y documentación del evento."),
        ("Cadena de frío", "Conservación, transporte, monitoreo térmico, desvíos y plan de contingencia."),
        ("Normativa", "Leyes, resoluciones, lineamientos nacionales y documentos técnicos vinculados."),
        ("Biblioteca científica", "Documentos de organismos sanitarios, revisiones y referencias seleccionadas."),
        ("Capacitación", "Rutas de aprendizaje, evaluaciones y material de apoyo para equipos de salud."),
        ("Casos clínicos", "Escenarios formativos para recuperación de esquemas y decisiones frecuentes."),
        ("Sistemas institucionales", "Accesos oficiales a SIGIPSA y NOMIVAC/SISA para usuarios con credenciales habilitadas."),
    ]

    module_titles = [title for title, _ in modules]
    current_index = module_titles.index(st.session_state.professional_module) if st.session_state.professional_module in module_titles else 0
    selected_navigation = st.selectbox(
        "Seleccionar módulo profesional",
        module_titles,
        index=current_index,
        key="professional_module_navigation",
        help="En celular, este selector evita recorrer una lista extensa de botones.",
    )
    if selected_navigation != st.session_state.professional_module:
        st.session_state.professional_module = selected_navigation
        st.rerun()

    with st.expander("Conocer todos los módulos", expanded=False):
        for title, description in modules:
            st.markdown(
                f'<article class="module-card"><h3>{escape(title)}</h3><p>{escape(description)}</p></article>',
                unsafe_allow_html=True,
            )

    st.divider()
    selected = st.session_state.professional_module
    heading("Módulo activo", selected)

    if selected == "Centro técnico":
        vaccine_names = sorted(item["name"] for item in VACCINES)
        selected_name = st.selectbox(
            "Seleccionar vacuna",
            vaccine_names,
            key="professional_vaccine_selector",
        )
        vaccine = next(item for item in VACCINES if item["name"] == selected_name)

        technical_fields = [
            ("Protección", vaccine.get("protects", "No documentado")),
            ("Población objetivo", vaccine.get("who", "No documentado")),
            ("Esquema", vaccine.get("scheme", "No documentado")),
            ("Vía y administración", vaccine.get("route", "No documentado")),
            ("Información técnica", vaccine.get("details", "No documentado")),
            ("Efectos esperables", vaccine.get("expected", "No documentado")),
            ("Precauciones", vaccine.get("precautions", "No documentado")),
            ("Etapa asociada", vaccine.get("stage", "No documentado")),
        ]
        fields_html = "".join(
            '<div class="technical-field">'
            f'<span>{escape(label)}</span><strong>{escape(value)}</strong>'
            '</div>'
            for label, value in technical_fields
        )
        st.markdown(
            '<section class="technical-sheet">'
            f'<h3>{escape(vaccine["name"])}</h3>'
            '<p>Vista técnica inicial vinculada a la entidad central de vacuna.</p>'
            f'<div class="technical-grid">{fields_html}</div>'
            '</section>',
            unsafe_allow_html=True,
        )
        st.markdown("#### Campos técnicos programados")
        st.write(
            "Plataforma tecnológica, composición, volumen, presentación, sitio anatómico, "
            "aguja recomendada, intervalos mínimos, coadministración, intercambiabilidad, "
            "embarazo, inmunocompromiso, reconstitución, estabilidad, transporte y bibliografía."
        )
        if vaccine.get("source"):
            st.link_button(
                "Abrir fuente oficial vinculada",
                vaccine["source"],
                use_container_width=True,
            )

    elif selected == "Manual del vacunador":
        chapters = [
            "Preparación del acto vacunal",
            "Evaluación previa y entrevista",
            "Administración segura",
            "Registro nominal y documental",
            "Prevención de errores programáticos",
            "Bioseguridad y descarte",
        ]
        for number, chapter in enumerate(chapters, 1):
            with st.expander(f"{number:02d}. {chapter}"):
                st.write(
                    "Estructura preparada para incorporar procedimiento normalizado, "
                    "lista de verificación, puntos críticos y documentación oficial."
                )

    elif selected == "ESAVI":
        st.markdown(
            '<div class="decision-panel"><strong>Principio operativo</strong>'
            '<p>Ante un evento posterior a la vacunación, priorizar la evaluación clínica, '
            'documentar con precisión y utilizar el circuito oficial de notificación. '
            'La relación temporal no demuestra causalidad.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown("#### Ruta de actuación")
        st.write(
            "1. Evaluación y estabilización. 2. Identificación del producto, lote, fecha y sitio. "
            "3. Clasificación inicial. 4. Notificación por el canal oficial. 5. Seguimiento y cierre."
        )
        st.warning(
            "Este módulo es educativo. La conducta clínica y la notificación deben ajustarse "
            "a los lineamientos oficiales vigentes y a la jurisdicción correspondiente."
        )

    elif selected == "Cadena de frío":
        st.markdown("#### Control operativo")
        chain_items = {
            "Recepción": "Verificar integridad, trazabilidad, temperatura y documentación.",
            "Almacenamiento": "Mantener organización por producto, vencimiento y condiciones específicas.",
            "Monitoreo": "Registrar temperaturas y revisar alarmas o excursiones térmicas.",
            "Contingencia": "Aislar, identificar como no utilizar y consultar antes de descartar.",
        }
        for title, text in chain_items.items():
            st.markdown(f"**{title}.** {text}")
        st.info(
            "Las condiciones concretas dependen del producto y del lineamiento técnico. "
            "No debe inferirse estabilidad sin evaluación oficial."
        )

    elif selected == "Normativa":
        heading("Repositorio", "Normativa y lineamientos")
        for source in OFFICIAL_SOURCES:
            if source["type"] in {"Esquemas de vacunación", "Información", "Sistema institucional", "Registro sanitario"}:
                st.markdown(f"**{source['name']}**  \\n{source['institution']}")
                st.link_button(
                    "Abrir documento o portal",
                    source["url"],
                    key=f"professional_source_{hashlib.md5(source['url'].encode()).hexdigest()[:10]}",
                )

    elif selected == "Biblioteca científica":
        st.info(
            "El repositorio científico queda preparado para indexar título, institución, año, "
            "tipo de documento, vacuna, enfermedad, población y versión."
        )
        st.markdown("#### Criterios de inclusión")
        st.write(
            "Prioridad para organismos sanitarios, guías de práctica, consensos, revisiones "
            "sistemáticas y documentos normativos. Cada registro debe conservar autoría, fecha y enlace."
        )

    elif selected == "Capacitación":
        tracks = [
            "Fundamentos de inmunización",
            "Administración segura",
            "Cadena de frío",
            "ESAVI y farmacovigilancia",
            "Recuperación de esquemas",
        ]
        for index, track in enumerate(tracks, 1):
            st.progress(index / len(tracks), text=f"Ruta {index}: {track}")
        st.caption("La progresión mostrada representa la arquitectura del programa, no avance individual.")

    elif selected == "Sistemas institucionales":
        st.markdown(
            '<div class="decision-panel"><strong>Accesos institucionales oficiales</strong>'
            '<p>Estos sistemas están destinados a personal y establecimientos autorizados. '
            'La plataforma no solicita, almacena ni administra sus credenciales.</p></div>',
            unsafe_allow_html=True,
        )
        for system in PROFESSIONAL_SYSTEMS:
            st.markdown(
                f'<article class="module-card"><h3>{escape(system["name"])}</h3>'
                f'<p>{escape(system["institution"])}</p>'
                f'<p>{escape(system["purpose"])}</p></article>',
                unsafe_allow_html=True,
            )
            st.link_button(
                f'Ingresar a {system["name"]}',
                system["url"],
                use_container_width=True,
                key=f'professional_system_{hashlib.md5(system["url"].encode()).hexdigest()[:10]}',
            )
        st.caption(
            "La integración actual consiste en accesos oficiales de referencia. "
            "No existe conexión directa ni intercambio de datos nominales con estos sistemas."
        )

    elif selected == "Casos clínicos":
        case = st.selectbox(
            "Escenario",
            [
                "Carnet incompleto en ingreso escolar",
                "Adulto sin registro disponible",
                "Embarazo con esquema a revisar",
                "Consulta por dosis atrasada",
            ],
            key="clinical_case_selector",
        )
        st.markdown(
            f'<div class="decision-panel"><strong>{escape(case)}</strong>'
            '<p>El caso se utilizará para practicar recopilación de antecedentes, identificación '
            'de dosis válidas, aplicación de intervalos y consulta del lineamiento vigente.</p></div>',
            unsafe_allow_html=True,
        )
        st.text_area(
            "Análisis profesional",
            placeholder="Registrar antecedentes relevantes, dudas y fuente a consultar...",
            key="clinical_case_notes",
            height=130,
        )
        st.caption("No ingrese datos personales ni información clínica identificable.")


def render_health_intelligence_area() -> None:
    st.markdown(
        """
        <section class="portal-hero portal-hero-intelligence">
            <div class="portal-eyebrow">Planificación y gestión</div>
            <h1>Inteligencia sanitaria</h1>
            <p>
                Entorno para municipios, hospitales, programas de inmunización y equipos de
                análisis. Integra indicadores, territorio, campañas y reportes sin presentar
                datos simulados como si fueran resultados oficiales.
            </p>
        </section>
        <div class="portal-band">
            <div class="portal-metric"><span>Dimensión</span><strong>Cobertura</strong></div>
            <div class="portal-metric"><span>Dimensión</span><strong>Territorio</strong></div>
            <div class="portal-metric"><span>Dimensión</span><strong>Operación</strong></div>
            <div class="portal-metric"><span>Dimensión</span><strong>Calidad de datos</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    modules = [
        ("Tablero ejecutivo", "Indicadores estratégicos, tendencias, alertas y lectura rápida para conducción."),
        ("Coberturas", "Numeradores, denominadores, metas, brechas y seguimiento por vacuna y población."),
        ("GIS sanitario", "Accesibilidad, áreas de influencia, distribución territorial y zonas subatendidas."),
        ("Campañas", "Planificación operativa, metas, recursos, avance y evaluación posterior."),
        ("Calidad de datos", "Completitud, consistencia, oportunidad, duplicados y trazabilidad."),
        ("Reportes", "Salidas ejecutivas, técnicas y territoriales con metodología documentada."),
    ]

    intelligence_titles = [title for title, _ in modules]
    intelligence_index = intelligence_titles.index(st.session_state.intelligence_module) if st.session_state.intelligence_module in intelligence_titles else 0
    intelligence_navigation = st.selectbox(
        "Seleccionar módulo de inteligencia sanitaria",
        intelligence_titles,
        index=intelligence_index,
        key="intelligence_module_navigation",
        help="En celular, este selector concentra la navegación en un único control.",
    )
    if intelligence_navigation != st.session_state.intelligence_module:
        st.session_state.intelligence_module = intelligence_navigation
        st.rerun()

    with st.expander("Conocer todos los módulos de gestión", expanded=False):
        for title, description in modules:
            st.markdown(
                f'<article class="module-card"><h3>{escape(title)}</h3><p>{escape(description)}</p></article>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="data-quality"><strong>Gobernanza de datos:</strong> los indicadores '
        'reales requieren fuente, período, definición, numerador, denominador, nivel geográfico '
        'y fecha de actualización. Esta versión muestra la arquitectura sin inventar resultados.</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    selected = st.session_state.intelligence_module
    heading("Módulo activo", selected)

    if selected == "Tablero ejecutivo":
        analytics = [
            ("Cobertura", "Seguimiento por vacuna, dosis, edad, período y territorio."),
            ("Brecha", "Diferencia entre población objetivo y dosis válidas registradas."),
            ("Oportunidad", "Tiempo entre edad recomendada y aplicación efectiva."),
            ("Acceso", "Distancia, tiempo de viaje y disponibilidad territorial."),
            ("Operación", "Capacidad, turnos, stock informado y desempeño de campaña."),
            ("Calidad", "Completitud, consistencia y actualización de los registros."),
        ]
        cards = st.columns(3)
        for index, (title, description) in enumerate(analytics):
            with cards[index % 3]:
                st.markdown(
                    f'<article class="analytics-card"><span>Indicador</span><h3>{escape(title)}</h3>'
                    f'<p>{escape(description)}</p></article>',
                    unsafe_allow_html=True,
                )
        st.info("Conecte una fuente validada para calcular y visualizar resultados reales.")

    elif selected == "Coberturas":
        st.markdown("#### Definición mínima del indicador")
        definition = pd.DataFrame(
            [
                ["Numerador", "Personas con dosis válida según criterio definido"],
                ["Denominador", "Población objetivo del mismo período y territorio"],
                ["Unidad", "Porcentaje"],
                ["Desagregación", "Vacuna, dosis, edad, sexo registrado, establecimiento y territorio"],
                ["Periodicidad", "Definida según disponibilidad y uso de gestión"],
            ],
            columns=["Componente", "Definición"],
        )
        st.dataframe(definition, use_container_width=True, hide_index=True)
        st.warning("No combine numeradores y denominadores de períodos o territorios incompatibles.")

    elif selected == "GIS sanitario":
        st.markdown("#### Capas previstas")
        layers = [
            "Centros y puestos de vacunación",
            "Población objetivo por unidad territorial",
            "Red vial y tiempos de acceso",
            "Áreas de influencia",
            "Coberturas y brechas",
            "Campañas y operativos móviles",
        ]
        for layer in layers:
            st.markdown(f"- {layer}")
        st.info(
            "El análisis territorial debe documentar proyección, escala, fecha, fuente y limitaciones. "
            "La localización de personas no debe exponerse."
        )
        if st.button("Abrir centros ciudadanos", use_container_width=True, key="gis_open_centers"):
            st.session_state.section = "Centros de vacunación"
            st.rerun()

    elif selected == "Campañas":
        campaign_table = pd.DataFrame(
            [
                ["Diagnóstico", "Población objetivo, brecha, territorio y barreras"],
                ["Diseño", "Meta, estrategia, establecimientos, equipos y cronograma"],
                ["Ejecución", "Dosis, cobertura operativa, incidencias y recursos"],
                ["Evaluación", "Resultados, oportunidad, equidad y lecciones aprendidas"],
            ],
            columns=["Fase", "Contenido mínimo"],
        )
        st.dataframe(campaign_table, use_container_width=True, hide_index=True)

    elif selected == "Calidad de datos":
        quality_dimensions = {
            "Completitud": "Porcentaje de campos obligatorios informados.",
            "Consistencia": "Compatibilidad entre edad, vacuna, dosis, fecha y esquema.",
            "Oportunidad": "Demora entre el evento y su disponibilidad para análisis.",
            "Unicidad": "Detección y gestión de registros potencialmente duplicados.",
            "Trazabilidad": "Fuente, proceso, versión y responsable de cada transformación.",
        }
        for title, description in quality_dimensions.items():
            with st.expander(title):
                st.write(description)

    elif selected == "Reportes":
        report_types = pd.DataFrame(
            [
                ["Ejecutivo", "Síntesis, alertas, brechas y decisiones requeridas"],
                ["Técnico", "Metodología, definiciones, fuentes, resultados y limitaciones"],
                ["Territorial", "Mapas, accesibilidad, distribución y priorización"],
                ["Operativo", "Campaña, establecimientos, recursos, incidencias y avance"],
            ],
            columns=["Reporte", "Contenido"],
        )
        st.dataframe(report_types, use_container_width=True, hide_index=True)
        st.caption("La exportación debe incluir fecha de corte y versión de los datos.")

def render_sources() -> None:
    heading("Transparencia", "Fuentes oficiales", "La plataforma verifica automáticamente la disponibilidad y detecta cambios en las páginas fuente.")
    if st.button("Actualizar fuentes ahora", use_container_width=True):
        source_snapshot.clear()
        st.rerun()
    for source in OFFICIAL_SOURCES:
        snap = source_snapshot(source["url"])
        with st.expander(f"{source['name']}, {source['institution']}"):
            st.write(f"**Tipo:** {source['type']}")
            st.write(f"**Estado:** {'Disponible' if snap['ok'] else 'Sin respuesta'}")
            st.write(f"**Última consulta automática:** {snap['checked_at']}")
            st.write(f"**Huella de contenido:** {snap['hash']}")
            st.link_button("Abrir fuente", source["url"], key=f"source_{source['name']}")



def _supabase_config() -> tuple[str, str]:
    try:
        url = str(st.secrets.get("SUPABASE_URL", "")).strip().rstrip("/")
        key = str(st.secrets.get("SUPABASE_ANON_KEY", "")).strip()
        return url, key
    except Exception:
        return "", ""


def _supabase_admin_config() -> tuple[str, str]:
    try:
        url = str(st.secrets.get("SUPABASE_URL", "")).strip().rstrip("/")
        key = str(st.secrets.get("SUPABASE_SECRET_KEY", "")).strip()
        return url, key
    except Exception:
        return "", ""


def _supabase_enabled() -> bool:
    url, key = _supabase_config()
    return bool(url and key)


def _supabase_admin_enabled() -> bool:
    url, key = _supabase_admin_config()
    return bool(url and key)


def _supabase_rest(
    method: str,
    *,
    table: str = SUPABASE_REQUESTS_TABLE,
    params: dict | None = None,
    payload: dict | None = None,
    admin: bool = False,
) -> tuple[bool, object]:
    url, key = _supabase_admin_config() if admin else _supabase_config()

    if not url or not key:
        missing = "SUPABASE_SECRET_KEY" if admin else "SUPABASE_URL o SUPABASE_ANON_KEY"
        return False, f"Falta configurar {missing} en Streamlit Secrets."

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    try:
        response = requests.request(
            method,
            f"{url}/rest/v1/{table}",
            headers=headers,
            params=params,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        if not response.text:
            return True, None
        return True, response.json()
    except requests.RequestException as exc:
        detail = ""
        if getattr(exc, "response", None) is not None:
            detail = exc.response.text[:900]
        return False, detail or str(exc)


def _record_audit(action: str, entity_type: str, entity_id: str, details: dict | None = None) -> tuple[bool, str]:
    payload = {
        "actor": str(st.session_state.get("institutional_user") or "Administración"),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
    }
    ok, result = _supabase_rest(
        "POST",
        table=SUPABASE_AUDIT_TABLE,
        payload=payload,
        admin=True,
    )
    return (True, "Auditoría registrada.") if ok else (False, str(result))


def _generate_temporary_password(length: int = 14) -> str:
    """Genera una clave temporal robusta para el primer ingreso."""
    alphabet = string.ascii_letters + string.digits + "!@#$%*-_"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
            and any(char in "!@#$%*-_" for char in password)
        ):
            return password


def _create_auth_user(email: str, password: str, metadata: dict) -> tuple[bool, object]:
    url, key = _supabase_admin_config()
    if not url or not key:
        return False, "Falta SUPABASE_SECRET_KEY en Streamlit Secrets."

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": metadata,
    }

    try:
        response = requests.post(
            f"{url}/auth/v1/admin/users",
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as exc:
        detail = ""
        if getattr(exc, "response", None) is not None:
            detail = exc.response.text[:900]
        return False, detail or str(exc)


def _delete_auth_user(user_id: str) -> None:
    """Revierte el alta en Auth si falla el perfil institucional."""
    if not user_id:
        return
    url, key = _supabase_admin_config()
    if not url or not key:
        return
    try:
        requests.delete(
            f"{url}/auth/v1/admin/users/{user_id}",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
            },
            timeout=20,
        )
    except requests.RequestException:
        pass


def _create_institutional_user(request_data: dict) -> tuple[bool, dict | str]:
    email = str(request_data.get("correo", "")).strip().lower()
    if not email or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return False, "La solicitud no contiene un correo válido."

    temporary_password = _generate_temporary_password()
    full_name = str(request_data.get("nombre", "")).strip()
    role = str(request_data.get("perfil", "Profesional")).strip()
    institution = str(request_data.get("institucion", "")).strip()

    auth_ok, auth_result = _create_auth_user(
        email,
        temporary_password,
        {
            "full_name": full_name,
            "role": role,
            "institution": institution,
        },
    )
    if not auth_ok:
        return False, (
            "No se pudo crear la cuenta de acceso en Supabase Auth. "
            f"Detalle: {auth_result}"
        )

    auth_user_id = ""
    if isinstance(auth_result, dict):
        auth_user_id = str(auth_result.get("id", ""))

    profile_payload = {
        "email": email,
        "full_name": full_name,
        "role": role,
        "institution": institution,
        "request_id": str(request_data.get("id", "")) or None,
        "status": "Activo",
    }

    profile_ok, profile_result = _supabase_rest(
        "POST",
        table=SUPABASE_USERS_TABLE,
        params={"on_conflict": "email"},
        payload=profile_payload,
        admin=True,
    )
    if not profile_ok:
        _delete_auth_user(auth_user_id)
        return False, (
            "La cuenta de acceso se creó, pero no pudo guardarse el perfil institucional. "
            "El alta fue revertida. "
            f"Detalle: {profile_result}"
        )

    return True, {
        "email": email,
        "temporary_password": temporary_password,
        "role": role,
        "institution": institution,
        "auth_user_id": auth_user_id,
    }


def _authenticate_institutional_user(email: str, password: str) -> tuple[bool, dict | str]:
    """Valida correo y contraseña en Supabase Auth."""
    url, anon_key = _supabase_config()
    if not url or not anon_key:
        return False, "Supabase no está configurado."

    try:
        response = requests.post(
            f"{url}/auth/v1/token",
            params={"grant_type": "password"},
            headers={
                "apikey": anon_key,
                "Content-Type": "application/json",
            },
            json={
                "email": email.strip().lower(),
                "password": password,
            },
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException:
        return False, "Correo o clave incorrectos."

    profile_ok, profile_result = _supabase_rest(
        "GET",
        table=SUPABASE_USERS_TABLE,
        params={
            "select": "email,full_name,role,institution,status",
            "email": f"eq.{email.strip().lower()}",
            "limit": "1",
        },
        admin=True,
    )
    if not profile_ok:
        return False, "La cuenta existe, pero no se pudo consultar su perfil institucional."

    if not isinstance(profile_result, list) or not profile_result:
        return False, "La cuenta no tiene un perfil institucional habilitado."

    profile = profile_result[0]
    if str(profile.get("status", "")).strip().lower() != "activo":
        return False, "La cuenta institucional no está activa."

    return True, profile

def _load_audit_log(limit: int = 100) -> tuple[bool, list]:
    ok, result = _supabase_rest(
        "GET",
        table=SUPABASE_AUDIT_TABLE,
        params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        admin=True,
    )
    if not ok:
        return False, []
    return True, result if isinstance(result, list) else []


def _tracking_code(email: str) -> str:
    seed = f"{email.strip().lower()}-{datetime.now(timezone.utc).isoformat()}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8].upper()
    return f"VAC-{digest}"


def _save_access_request(request_data: dict) -> tuple[bool, str]:
    ok, result = _supabase_rest("POST", payload=request_data)
    if ok:
        return True, "La solicitud fue registrada y quedó pendiente de revisión."
    return False, f"No fue posible guardar la solicitud en Supabase: {result}"


def _load_access_requests() -> tuple[bool, list]:
    ok, result = _supabase_rest(
        "GET",
        params={
            "select": "*",
            "order": "created_at.desc",
            "limit": "500",
        },
        admin=True,
    )
    if not ok:
        return False, []
    return True, result if isinstance(result, list) else []


def _update_access_request(
    request_id: object,
    status: str,
    review_note: str,
) -> tuple[bool, str]:
    ok, result = _supabase_rest(
        "PATCH",
        params={"id": f"eq.{request_id}"},
        payload={
            "estado": status,
            "nota_revision": review_note.strip(),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        },
        admin=True,
    )
    if ok:
        return True, "Estado actualizado."
    return False, f"No fue posible actualizar la solicitud: {result}"


def _find_access_request(email: str, tracking_code: str) -> tuple[bool, dict | None]:
    ok, result = _supabase_rest(
        "GET",
        params={
            "select": "codigo_seguimiento,estado,perfil,request_type,created_at,nota_revision",
            "correo": f"eq.{email.strip().lower()}",
            "codigo_seguimiento": f"eq.{tracking_code.strip().upper()}",
            "limit": "1",
        },
    )
    if not ok:
        return False, None
    if isinstance(result, list) and result:
        return True, result[0]
    return True, None


def _normalize_document(value: str) -> str:
    """Conserva únicamente caracteres alfanuméricos para búsquedas consistentes."""
    return re.sub(r"[^0-9A-Za-z]", "", value or "").upper()


def _find_citizen(document_type: str, document_number: str) -> tuple[bool, dict | None, str]:
    normalized_document = _normalize_document(document_number)
    if not normalized_document:
        return False, None, "Ingresá un número de documento."

    ok, result = _supabase_rest(
        "GET",
        table=SUPABASE_CITIZENS_TABLE,
        params={
            "select": "*",
            "document_type": f"eq.{document_type}",
            "document_number": f"eq.{normalized_document}",
            "limit": "1",
        },
        admin=True,
    )
    if not ok:
        return False, None, f"No fue posible consultar el registro nominal: {result}"
    if isinstance(result, list) and result:
        return True, result[0], ""
    return True, None, ""


def _create_citizen(payload: dict) -> tuple[bool, dict | str]:
    ok, result = _supabase_rest(
        "POST",
        table=SUPABASE_CITIZENS_TABLE,
        payload=payload,
        admin=True,
    )
    if not ok:
        return False, f"No fue posible crear el ciudadano: {result}"
    if isinstance(result, list) and result:
        return True, result[0]
    return False, "Supabase no devolvió el registro creado."


def _load_vaccination_records(citizen_id: str) -> tuple[bool, list, str]:
    ok, result = _supabase_rest(
        "GET",
        table=SUPABASE_VACCINATION_RECORDS_TABLE,
        params={
            "select": "*",
            "citizen_id": f"eq.{citizen_id}",
            "order": "application_date.desc,created_at.desc",
            "limit": "500",
        },
        admin=True,
    )
    if not ok:
        return False, [], f"No fue posible cargar el historial: {result}"
    return True, result if isinstance(result, list) else [], ""


def _create_vaccination_record(payload: dict) -> tuple[bool, dict | str]:
    ok, result = _supabase_rest(
        "POST",
        table=SUPABASE_VACCINATION_RECORDS_TABLE,
        payload=payload,
        admin=True,
    )
    if not ok:
        return False, f"No fue posible registrar la vacuna: {result}"
    if isinstance(result, list) and result:
        return True, result[0]
    return False, "Supabase no devolvió el registro creado."


def render_nominal_registry() -> None:
    heading(
        "Gestión institucional",
        "Registro nominal de vacunación",
        "Buscá una persona por documento, registrá sus datos y consultá el historial de dosis.",
    )

    st.markdown(
        '<div class="data-quality"><strong>Acceso restringido:</strong> este módulo '
        'maneja datos personales y sanitarios. Utilizalo únicamente con autorización, '
        'finalidad asistencial o institucional legítima y conforme a la normativa aplicable.</div>',
        unsafe_allow_html=True,
    )

    if not _supabase_admin_enabled():
        st.error(
            "Falta SUPABASE_SECRET_KEY en Streamlit Secrets. "
            "El registro nominal requiere acceso seguro desde el servidor."
        )
        return

    st.markdown("### 1. Buscar persona")
    search_col_1, search_col_2, search_col_3 = st.columns([0.7, 1.4, 0.8])
    with search_col_1:
        document_type = st.selectbox(
            "Tipo de documento",
            ["DNI", "Pasaporte", "Otro"],
            key="nominal_document_type",
        )
    with search_col_2:
        document_number = st.text_input(
            "Número de documento",
            value=st.session_state.nominal_last_document,
            placeholder="Ingresá el documento sin puntos",
            key="nominal_document_number",
        )
    with search_col_3:
        st.write("")
        st.write("")
        search_clicked = st.button(
            "Buscar",
            use_container_width=True,
            key="nominal_search_button",
        )

    if search_clicked:
        normalized = _normalize_document(document_number)
        st.session_state.nominal_last_document = normalized
        ok, citizen, error = _find_citizen(document_type, normalized)
        if not ok:
            st.error(error)
        elif citizen:
            st.session_state.nominal_selected_citizen = citizen
            st.success("Persona encontrada.")
            st.rerun()
        else:
            st.session_state.nominal_selected_citizen = {
                "_new": True,
                "document_type": document_type,
                "document_number": normalized,
            }
            st.info("No existe una persona con ese documento. Podés crearla a continuación.")
            st.rerun()

    citizen = st.session_state.get("nominal_selected_citizen")
    if not isinstance(citizen, dict):
        st.info("Ingresá un documento para comenzar.")
        return

    if citizen.get("_new"):
        st.markdown("### 2. Crear persona")
        with st.form("nominal_create_citizen_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                first_name = st.text_input("Nombre")
                birth_date = st.date_input(
                    "Fecha de nacimiento",
                    value=None,
                    min_value=datetime(1900, 1, 1).date(),
                    max_value=datetime.now().date(),
                )
                phone = st.text_input("Teléfono")
                address = st.text_input("Domicilio")
            with c2:
                last_name = st.text_input("Apellido")
                sex_registered = st.selectbox(
                    "Sexo registrado",
                    ["No informado", "Femenino", "Masculino", "X / Otro"],
                )
                email = st.text_input("Correo electrónico")
                locality = st.text_input("Localidad", value="San Francisco")
            observations = st.text_area("Observaciones", height=90)
            create_person = st.form_submit_button(
                "Crear persona",
                use_container_width=True,
            )

        if create_person:
            if not first_name.strip() or not last_name.strip() or birth_date is None:
                st.error("Completá nombre, apellido y fecha de nacimiento.")
            elif email.strip() and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
                st.error("El correo electrónico no tiene un formato válido.")
            else:
                payload = {
                    "document_type": str(citizen.get("document_type", "DNI")),
                    "document_number": _normalize_document(str(citizen.get("document_number", ""))),
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "birth_date": birth_date.isoformat(),
                    "sex_registered": None if sex_registered == "No informado" else sex_registered,
                    "phone": phone.strip() or None,
                    "email": email.strip().lower() or None,
                    "address": address.strip() or None,
                    "locality": locality.strip() or None,
                    "province": "Córdoba",
                    "observations": observations.strip() or None,
                }
                ok, result = _create_citizen(payload)
                if ok and isinstance(result, dict):
                    st.session_state.nominal_selected_citizen = result
                    _record_audit(
                        "Crear ciudadano",
                        "citizen",
                        str(result.get("id", "")),
                        {"document_type": payload["document_type"], "document_number": payload["document_number"]},
                    )
                    st.success("Persona creada correctamente.")
                    st.rerun()
                else:
                    st.error(str(result))
        return

    citizen_id = str(citizen.get("id", ""))
    if not citizen_id:
        st.error("El registro seleccionado no contiene un identificador válido.")
        return

    full_name = f"{citizen.get('last_name', '')}, {citizen.get('first_name', '')}".strip(", ")
    st.markdown("### Persona seleccionada")
    st.markdown(
        '<section class="technical-sheet">'
        f'<h3>{escape(full_name or "Sin nombre")}</h3>'
        '<div class="technical-grid">'
        f'<div class="technical-field"><span>Documento</span><strong>{escape(str(citizen.get("document_type", "")))} {escape(str(citizen.get("document_number", "")))}</strong></div>'
        f'<div class="technical-field"><span>Fecha de nacimiento</span><strong>{escape(str(citizen.get("birth_date", "")))}</strong></div>'
        f'<div class="technical-field"><span>Localidad</span><strong>{escape(str(citizen.get("locality") or "No informada"))}</strong></div>'
        f'<div class="technical-field"><span>Contacto</span><strong>{escape(str(citizen.get("phone") or citizen.get("email") or "No informado"))}</strong></div>'
        '</div></section>',
        unsafe_allow_html=True,
    )

    if st.button("Buscar otra persona", use_container_width=True, key="nominal_clear_selection"):
        st.session_state.nominal_selected_citizen = None
        st.session_state.nominal_last_document = ""
        st.rerun()

    st.markdown("### 2. Registrar aplicación")
    with st.form("nominal_vaccination_form", clear_on_submit=True):
        r1, r2, r3 = st.columns(3)
        with r1:
            vaccine_name = st.selectbox("Vacuna", sorted({item["name"] for item in VACCINES}) + ["Otra"])
            dose_number = st.text_input("Dosis", placeholder="Ej.: 1.ª dosis, refuerzo, dosis anual")
            application_date = st.date_input("Fecha de aplicación", value=datetime.now().date(), max_value=datetime.now().date())
        with r2:
            batch_number = st.text_input("Lote")
            expiration_date = st.date_input("Vencimiento del lote", value=None)
            laboratory = st.text_input("Laboratorio")
        with r3:
            establishment = st.text_input("Establecimiento")
            locality_record = st.text_input("Localidad de aplicación", value=str(citizen.get("locality") or "San Francisco"))
            administration_route = st.selectbox("Vía de administración", ["No informada", "Intramuscular", "Subcutánea", "Intradérmica", "Oral", "Otra"])

        r4, r5 = st.columns(2)
        with r4:
            anatomical_site = st.text_input("Sitio anatómico", placeholder="Ej.: deltoides derecho")
            vaccinator_name = st.text_input("Nombre del vacunador/a", value=str(st.session_state.get("institutional_user") or ""))
        with r5:
            vaccinator_registration = st.text_input("Matrícula")
            record_observations = st.text_area("Observaciones", height=90)

        confirm_record = st.checkbox("Confirmo que verifiqué identidad, vacuna, dosis, lote y fecha antes de registrar.")
        save_record = st.form_submit_button("Registrar vacuna", use_container_width=True)

    if save_record:
        if not dose_number.strip() or not establishment.strip():
            st.error("Completá dosis y establecimiento.")
        elif not batch_number.strip():
            st.error("Ingresá el número de lote.")
        elif not confirm_record:
            st.error("Debés confirmar la verificación previa.")
        else:
            payload = {
                "citizen_id": citizen_id,
                "vaccine_name": vaccine_name,
                "dose_number": dose_number.strip(),
                "application_date": application_date.isoformat(),
                "batch_number": batch_number.strip(),
                "expiration_date": expiration_date.isoformat() if expiration_date else None,
                "laboratory": laboratory.strip() or None,
                "establishment": establishment.strip(),
                "locality": locality_record.strip() or None,
                "province": "Córdoba",
                "administration_route": None if administration_route == "No informada" else administration_route,
                "anatomical_site": anatomical_site.strip() or None,
                "vaccinator_name": vaccinator_name.strip() or None,
                "vaccinator_registration": vaccinator_registration.strip() or None,
                "observations": record_observations.strip() or None,
            }
            ok, result = _create_vaccination_record(payload)
            if ok and isinstance(result, dict):
                _record_audit(
                    "Registrar vacuna",
                    "vaccination_record",
                    str(result.get("id", "")),
                    {"citizen_id": citizen_id, "vaccine_name": vaccine_name, "dose_number": dose_number.strip()},
                )
                st.success("Vacuna registrada correctamente.")
                st.rerun()
            else:
                st.error(str(result))

    st.markdown("### 3. Historial de vacunación")
    history_ok, records, history_error = _load_vaccination_records(citizen_id)
    if not history_ok:
        st.error(history_error)
    elif not records:
        st.info("La persona todavía no tiene aplicaciones registradas.")
    else:
        history_rows = [{
            "Fecha": record.get("application_date", ""),
            "Vacuna": record.get("vaccine_name", ""),
            "Dosis": record.get("dose_number", ""),
            "Lote": record.get("batch_number", ""),
            "Establecimiento": record.get("establishment", ""),
            "Vacunador/a": record.get("vaccinator_name", ""),
        } for record in records]
        st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)

def _institutional_users() -> dict:
    """Lee usuarios institucionales desde .streamlit/secrets.toml sin exponer credenciales."""
    try:
        configured = st.secrets.get("institutional_users", {})
        return {str(email).strip().lower(): dict(data) for email, data in configured.items()}
    except Exception:
        return {}


def _admin_code() -> str:
    try:
        return str(st.secrets.get("ADMIN_ACCESS_CODE", "")).strip()
    except Exception:
        return ""


def render_professional_portal() -> None:
    st.markdown(
        """
        <section class="portal-hero">
            <div class="portal-eyebrow">Acceso especializado</div>
            <h1>Profesionales e instituciones</h1>
            <p>
                Recursos técnicos de consulta abierta y herramientas institucionales
                para análisis, planificación, seguimiento y gestión de la vacunación.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.professional_access_view == "Bienvenida":
        heading("Bienvenida", "Ingresá según el uso que necesitás")
        st.markdown(
            """
            <div class="decision-panel">
                <strong>Cómo utilizar este espacio</strong>
                <p>
                    Podés consultar contenidos profesionales sin registrarte. Para acceder a
                    indicadores, reportes, campañas y funciones institucionales, necesitás una
                    cuenta previamente autorizada por la administración de la plataforma.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                '<article class="module-card"><h3>Contenidos profesionales</h3>'
                '<p>Centro técnico, manual del vacunador, ESAVI, cadena de frío, normativa, biblioteca, capacitación y casos clínicos.</p></article>',
                unsafe_allow_html=True,
            )
            if st.button("Explorar contenidos profesionales", use_container_width=True, key="open_professional_content"):
                st.session_state.professional_access_view = "Contenido abierto"
                st.session_state.professional_workspace = "Área técnica"
                st.rerun()

        with col2:
            st.markdown(
                '<article class="module-card"><h3>Solicitud institucional</h3>'
                '<p>Solicitá autorización para acceder a inteligencia sanitaria, indicadores, reportes y herramientas de gestión.</p></article>',
                unsafe_allow_html=True,
            )
            if st.button("Registrarme", use_container_width=True, key="request_institutional_access"):
                st.session_state.professional_access_view = "Solicitud"
                st.rerun()

        with col3:
            st.markdown(
                '<article class="module-card"><h3>Cuenta autorizada</h3>'
                '<p>Ingresá con el correo y la clave de acceso asignados luego de la aprobación administrativa.</p></article>',
                unsafe_allow_html=True,
            )
            if st.button("Ya tengo una cuenta", use_container_width=True, key="existing_institutional_account"):
                st.session_state.professional_access_view = "Ingreso"
                st.rerun()
        return

    if st.session_state.professional_access_view == "Solicitud":
        heading(
            "Registro",
            "Solicitud de acceso",
            "Profesionales e instituciones pueden registrarse. La cuenta se habilita únicamente después de la revisión administrativa.",
        )

        request_type = st.radio(
            "Tipo de solicitud",
            ["Profesional", "Institución"],
            horizontal=True,
            key="access_request_type",
        )

        with st.form("institutional_request_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Nombre y apellido del responsable")
                email = st.text_input("Correo electrónico")
                phone = st.text_input("Teléfono")
                profession = st.text_input("Profesión, función o cargo")
            with col2:
                institution = st.text_input(
                    "Institución" if request_type == "Profesional"
                    else "Nombre legal de la institución"
                )
                registration = st.text_input(
                    "Matrícula profesional" if request_type == "Profesional"
                    else "CUIT o identificación institucional"
                )
                jurisdiction = st.text_input("Provincia, municipio o jurisdicción")
                requested_role = st.selectbox(
                    "Perfil solicitado",
                    (
                        ["Profesional", "Vacunador/a", "Referente de inmunizaciones"]
                        if request_type == "Profesional"
                        else [
                            "Referente institucional",
                            "Gestor sanitario",
                            "Administrador institucional",
                        ]
                    ),
                )

            sigipsa_interest = st.checkbox(
                "Solicito orientación para el acceso institucional a SIGIPSA."
            )
            reason = st.text_area("Motivo de la solicitud", height=110)
            confirm = st.checkbox(
                "Declaro que la información consignada es correcta y autorizo su revisión administrativa."
            )
            submitted = st.form_submit_button(
                "Enviar solicitud",
                use_container_width=True,
            )

        if submitted:
            required = [
                full_name.strip(),
                email.strip(),
                profession.strip(),
                institution.strip(),
                jurisdiction.strip(),
                reason.strip(),
            ]
            if not all(required):
                st.error("Completá todos los campos obligatorios antes de enviar la solicitud.")
            elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
                st.error("Ingresá un correo electrónico válido.")
            elif not confirm:
                st.error("Debés aceptar la declaración para enviar la solicitud.")
            elif not _supabase_enabled():
                st.error(
                    "Supabase no está configurado. Revisá SUPABASE_URL y "
                    "SUPABASE_ANON_KEY en Streamlit Secrets."
                )
            else:
                tracking_code = _tracking_code(email)
                request_data = {
                    "request_type": request_type,
                    "nombre": full_name.strip(),
                    "correo": email.strip().lower(),
                    "telefono": phone.strip(),
                    "profesion": profession.strip(),
                    "institucion": institution.strip(),
                    "matricula": registration.strip(),
                    "jurisdiccion": jurisdiction.strip(),
                    "perfil": requested_role,
                    "sigipsa_interest": bool(sigipsa_interest),
                    "motivo": reason.strip(),
                    "estado": "Pendiente",
                    "codigo_seguimiento": tracking_code,
                    "fecha": datetime.now().astimezone().strftime("%d/%m/%Y %H:%M"),
                }
                ok, message = _save_access_request(request_data)
                if ok:
                    st.success(message)
                    st.markdown("**Código de seguimiento**")
                    st.code(tracking_code, language=None)
                    st.info(
                        "Guardá este código. Lo necesitarás junto con tu correo "
                        "para consultar el estado."
                    )
                else:
                    st.error(message)

        with st.expander("Consultar el estado de una solicitud", expanded=False):
            status_email = st.text_input(
                "Correo utilizado en el registro",
                key="status_request_email",
            )
            status_code = st.text_input(
                "Código de seguimiento",
                key="status_request_code",
            )
            if st.button(
                "Consultar estado",
                use_container_width=True,
                key="check_request_status",
            ):
                if not status_email.strip() or not status_code.strip():
                    st.warning("Ingresá el correo y el código de seguimiento.")
                else:
                    ok, status_data = _find_access_request(
                        status_email,
                        status_code,
                    )
                    if not ok:
                        st.error("No fue posible consultar el estado.")
                    elif not status_data:
                        st.warning("No se encontró una solicitud con esos datos.")
                    else:
                        st.success(
                            f"Estado: {status_data.get('estado', 'Pendiente')}"
                        )
                        st.write(
                            f"Perfil solicitado: "
                            f"{status_data.get('perfil', 'No informado')}"
                        )
                        note = str(status_data.get("nota_revision") or "").strip()
                        if note:
                            st.info(f"Observación administrativa: {note}")

        if st.button(
            "Volver a la bienvenida",
            use_container_width=True,
            key="request_back",
        ):
            st.session_state.professional_access_view = "Bienvenida"
            st.rerun()
        return

    if st.session_state.professional_access_view == "Ingreso":
        heading("Cuenta institucional", "Ingreso seguro", "Utilizá las credenciales habilitadas por la administración.")
        with st.form("institutional_login_form"):
            email = st.text_input("Correo autorizado")
            access_code = st.text_input("Clave de acceso", type="password")
            login = st.form_submit_button("Ingresar", use_container_width=True)

        if login:
            normalized_email = email.strip().lower()
            valid_admin = bool(_admin_code()) and access_code == _admin_code()

            if valid_admin:
                st.session_state.institutional_authenticated = True
                st.session_state.institutional_user = normalized_email or "Administración"
                st.session_state.institutional_role = "Superadministradora"
                st.session_state.professional_access_view = "Espacio institucional"
                st.rerun()
            elif not normalized_email or not access_code:
                st.error("Ingresá el correo y la clave de acceso.")
            else:
                auth_ok, auth_result = _authenticate_institutional_user(
                    normalized_email,
                    access_code,
                )
                if auth_ok and isinstance(auth_result, dict):
                    st.session_state.institutional_authenticated = True
                    st.session_state.institutional_user = normalized_email
                    st.session_state.institutional_role = str(
                        auth_result.get("role", "Referente institucional")
                    )
                    st.session_state.professional_access_view = "Espacio institucional"
                    st.rerun()
                else:
                    st.error(str(auth_result))

        st.caption(
            "Las cuentas aprobadas ingresan con el correo registrado y la clave temporal "
            "generada por la administración. La clave de Superadministradora permanece "
            "configurada en Streamlit Secrets."
        )
        if st.button("Volver a la bienvenida", use_container_width=True, key="login_back"):
            st.session_state.professional_access_view = "Bienvenida"
            st.rerun()
        return

    if st.session_state.professional_access_view == "Contenido abierto":
        top1, top2 = st.columns([4, 1])
        with top1:
            st.markdown('<div class="section-label">Acceso abierto</div>', unsafe_allow_html=True)
        with top2:
            if st.button("Volver", use_container_width=True, key="professional_open_back"):
                st.session_state.professional_access_view = "Bienvenida"
                st.rerun()
        render_professional_area()
        return

    if st.session_state.professional_access_view == "Espacio institucional":
        if not st.session_state.institutional_authenticated:
            st.session_state.professional_access_view = "Ingreso"
            st.rerun()

        st.markdown(
            f'<div class="data-quality"><strong>Sesión institucional:</strong> '
            f'{escape(str(st.session_state.institutional_user))} · '
            f'{escape(str(st.session_state.institutional_role))}</div>',
            unsafe_allow_html=True,
        )

        workspace_col, logout_col = st.columns([4, 1])
        with workspace_col:
            workspace_options = ["Área técnica", "Registro nominal", "Inteligencia sanitaria"]
            workspace_index = workspace_options.index(st.session_state.professional_workspace)
            workspace_selected = st.selectbox(
                "Espacio de trabajo",
                workspace_options,
                index=workspace_index,
                key="institutional_workspace_navigation",
            )
            if workspace_selected != st.session_state.professional_workspace:
                st.session_state.professional_workspace = workspace_selected
                st.rerun()
        with logout_col:
            st.write("")
            if st.button("Cerrar sesión", use_container_width=True, key="institutional_logout"):
                st.session_state.institutional_authenticated = False
                st.session_state.institutional_role = None
                st.session_state.institutional_user = None
                st.session_state.professional_access_view = "Bienvenida"
                st.rerun()

        if st.session_state.professional_workspace == "Área técnica":
            render_professional_area()
        elif st.session_state.professional_workspace == "Registro nominal":
            render_nominal_registry()
        else:
            render_health_intelligence_area()

        if st.session_state.institutional_role == "Superadministradora":
            st.divider()
            heading(
                "Administración",
                "Gestión de solicitudes",
                "Revisión, decisión, trazabilidad y alta institucional.",
            )

            if not _supabase_admin_enabled():
                st.error(
                    "Falta SUPABASE_SECRET_KEY en Streamlit Secrets. "
                    "El panel administrativo requiere una clave privada del servidor."
                )
                return

            ok, requests_list = _load_access_requests()

            if not ok:
                st.error("No fue posible cargar las solicitudes desde Supabase.")
                return

            counts = {
                "Total": len(requests_list),
                "Pendientes": sum(r.get("estado") == "Pendiente" for r in requests_list),
                "Aprobadas": sum(r.get("estado") == "Aprobada" for r in requests_list),
                "Información": sum(r.get("estado") == "Requiere información" for r in requests_list),
                "Rechazadas": sum(r.get("estado") == "Rechazada" for r in requests_list),
            }

            metric_cols = st.columns(5)
            for column, (label, value) in zip(metric_cols, counts.items()):
                with column:
                    st.metric(label, value)

            f1, f2, f3 = st.columns([1.4, 1, 1])
            with f1:
                search_term = st.text_input(
                    "Buscar",
                    placeholder="Nombre, correo, institución, matrícula o código...",
                    key="admin_request_search",
                ).strip().lower()
            with f2:
                status_options = sorted({str(r.get("estado", "Pendiente")) for r in requests_list})
                selected_status = st.selectbox(
                    "Estado",
                    ["Todos"] + status_options,
                    key="admin_request_status",
                )
            with f3:
                type_options = sorted({str(r.get("request_type", "No informado")) for r in requests_list})
                selected_type = st.selectbox(
                    "Tipo",
                    ["Todos"] + type_options,
                    key="admin_request_type",
                )

            filtered = []
            for request in requests_list:
                searchable = " ".join(
                    [
                        str(request.get("nombre", "")),
                        str(request.get("correo", "")),
                        str(request.get("institucion", "")),
                        str(request.get("matricula", "")),
                        str(request.get("codigo_seguimiento", "")),
                        str(request.get("perfil", "")),
                    ]
                ).lower()
                if (
                    (not search_term or search_term in searchable)
                    and (selected_status == "Todos" or request.get("estado") == selected_status)
                    and (selected_type == "Todos" or request.get("request_type") == selected_type)
                ):
                    filtered.append(request)

            st.caption(f"{len(filtered)} solicitudes visibles.")

            if not filtered:
                st.info("No hay solicitudes que coincidan con los filtros.")
            else:
                rows = [
                    {
                        "Fecha": r.get("fecha") or r.get("created_at", ""),
                        "Nombre": r.get("nombre", ""),
                        "Tipo": r.get("request_type", ""),
                        "Institución": r.get("institucion", ""),
                        "Perfil": r.get("perfil", ""),
                        "Estado": r.get("estado", "Pendiente"),
                        "Código": r.get("codigo_seguimiento", ""),
                    }
                    for r in filtered
                ]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                options = {
                    f"{r.get('nombre', 'Sin nombre')} · {r.get('codigo_seguimiento', '')} · {r.get('estado', 'Pendiente')}": r
                    for r in filtered
                }
                selected_label = st.selectbox(
                    "Abrir solicitud",
                    list(options.keys()),
                    key="admin_request_selector",
                )
                request = options[selected_label]
                request_id = str(request.get("id", ""))
                current_status = str(request.get("estado", "Pendiente"))

                st.markdown("### Detalle de la solicitud")
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Nombre:** {request.get('nombre', '')}")
                    st.write(f"**Correo:** {request.get('correo', '')}")
                    st.write(f"**Teléfono:** {request.get('telefono') or 'No informado'}")
                    st.write(f"**Profesión o cargo:** {request.get('profesion', '')}")
                    st.write(f"**Institución:** {request.get('institucion', '')}")
                with c2:
                    st.write(f"**Matrícula o identificación:** {request.get('matricula') or 'No informada'}")
                    st.write(f"**Jurisdicción:** {request.get('jurisdiccion') or 'No informada'}")
                    st.write(f"**Perfil solicitado:** {request.get('perfil', '')}")
                    st.write(f"**Interés SIGIPSA:** {'Sí' if request.get('sigipsa_interest') else 'No'}")
                    st.write(f"**Código:** {request.get('codigo_seguimiento', '')}")

                st.write(f"**Motivo:** {request.get('motivo', '')}")
                review_note = st.text_area(
                    "Observación administrativa",
                    value=str(request.get("nota_revision") or ""),
                    key=f"admin_review_note_{request_id}",
                    height=110,
                )
                st.info(f"Estado actual: {current_status}")

                a, b, c = st.columns(3)
                with a:
                    approve = st.button(
                        "Aprobar y crear usuario",
                        use_container_width=True,
                        key=f"admin_approve_{request_id}",
                    )
                with b:
                    request_more = st.button(
                        "Solicitar información",
                        use_container_width=True,
                        key=f"admin_more_info_{request_id}",
                    )
                with c:
                    reject = st.button(
                        "Rechazar",
                        use_container_width=True,
                        key=f"admin_reject_{request_id}",
                    )

                if approve:
                    if current_status == "Aprobada":
                        st.warning("Esta solicitud ya figura como aprobada.")
                    else:
                        user_ok, user_result = _create_institutional_user(request)
                        if not user_ok:
                            st.error(str(user_result))
                        elif isinstance(user_result, dict):
                            update_ok, update_message = _update_access_request(
                                request_id, "Aprobada", review_note
                            )
                            if update_ok:
                                st.session_state.created_user_credentials = user_result
                                _record_audit(
                                    "Aprobar solicitud y crear usuario",
                                    "access_request",
                                    request_id,
                                    {
                                        "estado_anterior": current_status,
                                        "estado_nuevo": "Aprobada",
                                        "correo": request.get("correo", ""),
                                        "auth_user_id": user_result.get("auth_user_id", ""),
                                    },
                                )
                                st.success(
                                    "Solicitud aprobada y cuenta institucional creada."
                                )
                            else:
                                st.error(update_message)

                created_credentials = st.session_state.get("created_user_credentials")
                if (
                    isinstance(created_credentials, dict)
                    and created_credentials.get("email") == str(request.get("correo", "")).strip().lower()
                ):
                    st.markdown("### Credenciales iniciales")
                    st.warning(
                        "Copiá estos datos antes de salir de esta solicitud. "
                        "La clave temporal se muestra únicamente durante esta sesión administrativa."
                    )
                    st.text_input(
                        "Correo de acceso",
                        value=str(created_credentials.get("email", "")),
                        disabled=True,
                        key=f"created_email_{request_id}",
                    )
                    st.text_input(
                        "Clave temporal",
                        value=str(created_credentials.get("temporary_password", "")),
                        disabled=True,
                        key=f"created_password_{request_id}",
                    )
                    st.caption(
                        "Entregá estas credenciales por un canal seguro. "
                        "La persona podrá ingresar desde “Ya tengo una cuenta”."
                    )
                    if st.button(
                        "Ocultar credenciales",
                        use_container_width=True,
                        key=f"hide_created_credentials_{request_id}",
                    ):
                        st.session_state.created_user_credentials = None
                        st.rerun()

                if request_more:
                    update_ok, update_message = _update_access_request(
                        request_id, "Requiere información", review_note
                    )
                    if update_ok:
                        _record_audit(
                            "Solicitar información",
                            "access_request",
                            request_id,
                            {"estado_anterior": current_status, "estado_nuevo": "Requiere información"},
                        )
                        st.success(update_message)
                        st.rerun()
                    else:
                        st.error(update_message)

                if reject:
                    update_ok, update_message = _update_access_request(
                        request_id, "Rechazada", review_note
                    )
                    if update_ok:
                        _record_audit(
                            "Rechazar solicitud",
                            "access_request",
                            request_id,
                            {"estado_anterior": current_status, "estado_nuevo": "Rechazada"},
                        )
                        st.success(update_message)
                        st.rerun()
                    else:
                        st.error(update_message)

            st.markdown("### Auditoría reciente")
            audit_ok, audit_rows = _load_audit_log(limit=50)
            if not audit_ok:
                st.warning("No fue posible cargar el registro de auditoría.")
            elif not audit_rows:
                st.info("Todavía no hay acciones administrativas registradas.")
            else:
                audit_df = pd.DataFrame(
                    [
                        {
                            "Fecha": row.get("created_at", ""),
                            "Actor": row.get("actor", ""),
                            "Acción": row.get("action", ""),
                            "Entidad": row.get("entity_type", ""),
                            "Identificador": row.get("entity_id", ""),
                        }
                        for row in audit_rows
                    ]
                )
                st.dataframe(audit_df, use_container_width=True, hide_index=True)
        return

    st.session_state.professional_access_view = "Bienvenida"
    st.rerun()


PAGES = {
    "Inicio": render_home,
    "Esquemas de vacunación": render_calendar,
    "Mi registro oficial": render_official_record,
    "Biblioteca de vacunas": render_vaccines,
    "Centros de vacunación": render_centers,
    "Información": render_information,
    "Novedades": render_news,
    "Fuentes oficiales": render_sources,
    "Profesionales e instituciones": render_professional_portal,
}

st.markdown(
    f"""
    <div class="brandbar">
        <div class="brandidentity">
            <div class="brandtitle">{APP_NAME}</div>
            <div class="brandsubtitle">{APP_SUBTITLE}</div>
        </div>
        <div class="brandmeta">San Francisco, Córdoba</div>
    </div>
    """,
    unsafe_allow_html=True,
)

nav()

if st.session_state.section == "Vacunas":
    st.session_state.section = "Biblioteca de vacunas"

if st.session_state.section not in PAGES:
    st.session_state.section = "Inicio"

PAGES[st.session_state.section]()
st.markdown(
    f"""
    <div class="footerx">
        <strong>{DEVELOPER}</strong><br>
        Última revisión de contenidos: {LAST_CONTENT_REVIEW}<br><br>
        Esta plataforma integra orientación ciudadana, consulta profesional y arquitectura de inteligencia sanitaria basada en fuentes oficiales.
        El Portal Ciudadano no almacena datos clínicos. El Registro Nominal es un módulo institucional
        restringido y no reemplaza la historia clínica ni los sistemas oficiales.
        La plataforma no accede directamente a SIGIPSA, NOMIVAC, CiDi o Mi Argentina.
    </div>
    """,
    unsafe_allow_html=True,
)
