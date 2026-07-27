from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from urllib.parse import quote_plus
import hashlib
import math
import re

import folium
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation


st.set_page_config(
    page_title="VACUNACION PLATAFORMA DIGITAL",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_NAME = "VACUNACION PLATAFORMA DIGITAL"
DEVELOPER = "EGS | Estudio de Gestión de Sistemas"
AUTO_REFRESH_SECONDS = 21600
LAST_CONTENT_REVIEW = "27/07/2026"

if "section" not in st.session_state:
    st.session_state.section = "Inicio"
if "selected_stage" not in st.session_state:
    st.session_state.selected_stage = "Embarazo"
if "selected_vaccine" not in st.session_state:
    st.session_state.selected_vaccine = None
if "user_location" not in st.session_state:
    st.session_state.user_location = None


OFFICIAL_SOURCES = [
    {
        "name": "Calendario Nacional de Vacunación",
        "institution": "Ministerio de Salud de la Nación",
        "url": "https://www.argentina.gob.ar/salud/vacunas",
        "type": "Calendario",
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
    {"name": "Asistencia Pública", "address": "Colón 165", "phone": "03564 439154", "lat": -31.42715, "lon": -62.08388, "schedule": "Lunes a viernes. Confirmar horario de vacunación."},
    {"name": "CAPS Cottolengo", "address": "José Hernández 3049", "phone": "03564 434726 / 3564 213014", "lat": -31.41485, "lon": -62.10592, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS 2 Hermanos", "address": "Colombia 234", "phone": "03564 310030", "lat": -31.43275, "lon": -62.09612, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS Roque Sáenz Peña", "address": "Falucho esq. Gerónimo del Barco", "phone": "3564 370400", "lat": -31.42272, "lon": -62.09140, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS Jardín", "address": "Rioja 2653", "phone": "3564 333456", "lat": -31.41860, "lon": -62.10440, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS Bouchard", "address": "Rioja esq. General Paz", "phone": "03564 498404", "lat": -31.42790, "lon": -62.10040, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS La Milka", "address": "Madre Marcilla 407", "phone": "3564 237775", "lat": -31.44342, "lon": -62.10010, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS Sarmiento", "address": "Olegario Andrade 707", "phone": "03564 498116 / 3564 333452", "lat": -31.42022, "lon": -62.09275, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS Parque", "address": "Resistencia 578", "phone": "03564 434725 / 3564 595398", "lat": -31.43462, "lon": -62.07382, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS San Cayetano", "address": "Pascual Bailón Sosa 1759", "phone": "03564 435274", "lat": -31.43825, "lon": -62.11125, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS Prado", "address": "Los Robles 1193", "phone": "3564 237319", "lat": -31.40720, "lon": -62.08955, "schedule": "Consultar telefónicamente."},
    {"name": "CAPS Plaza", "address": "Víctor Angelli 4136", "phone": "3564 684355", "lat": -31.39870, "lon": -62.11030, "schedule": "Lunes a viernes de 8 a 12. Confirmar vacunación."},
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
            headers={"User-Agent": "VACUNACION-PLATAFORMA-DIGITAL/1.0"},
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
        --navy:#15314A; --green:#2C8F78; --muted:#667989; --line:#DCE6ED;
        --soft:#F7FAFC; --white:#FFFFFF; --shadow:0 18px 50px rgba(20,49,74,.08);
    }
    .stApp{background:#fff;color:var(--navy)}
    .block-container{max-width:1260px;padding-top:.7rem;padding-bottom:3rem}
    #MainMenu,footer,header{visibility:hidden}
    h1,h2,h3{color:var(--navy);letter-spacing:-.03em}
    .brandbar{display:flex;justify-content:space-between;align-items:center;padding:1rem 0 1.3rem;border-bottom:1px solid var(--line);margin-bottom:1rem}
    .brandtitle{font-size:1.28rem;font-weight:950;color:var(--navy)}
    .brandmeta{font-size:.8rem;color:var(--muted);font-weight:700}
    .hero{padding:4.2rem 3.2rem;border-radius:32px;border:1px solid var(--line);background:radial-gradient(circle at 85% 12%,#EAF7FB 0,transparent 28%),radial-gradient(circle at 95% 88%,#EEF9F5 0,transparent 25%),linear-gradient(135deg,#FAFCFD,#FFFFFF);box-shadow:var(--shadow);margin-bottom:2rem}
    .hero h1{font-size:clamp(3rem,6vw,5.6rem);line-height:.95;margin:0 0 1.2rem;max-width:980px}
    .hero p{font-size:1.12rem;color:var(--muted);max-width:760px;line-height:1.7;margin:0}
    .section-label{font-size:.74rem;letter-spacing:.11em;text-transform:uppercase;font-weight:900;color:var(--green);margin-top:2.4rem}
    .section-title{font-size:2.1rem;font-weight:900;margin:.2rem 0 .3rem}
    .section-copy{color:var(--muted);margin-bottom:1.3rem}
    .stage-card{padding:1.35rem;border-radius:22px;border:1px solid rgba(21,49,74,.08);min-height:165px;margin-bottom:.8rem}
    .stage-card h3{margin:.15rem 0 .4rem}
    .stage-card p{color:#506273;font-size:.92rem}
    .detail-card{padding:1.7rem;border-radius:26px;border:1px solid var(--line);background:#fff;box-shadow:var(--shadow);margin:1rem 0}
    .detail-header{display:block;margin-bottom:1rem}
    .dose-row{padding:.9rem 1rem;border-radius:14px;background:#F7FAFC;margin:.55rem 0;border:1px solid #E7EEF3}
    .vaccine-card{padding:1.25rem;border-radius:20px;border:1px solid var(--line);background:#fff;margin-bottom:1rem;min-height:220px}
    .vaccine-card p{color:var(--muted)}
    .source-chip{display:inline-block;padding:.35rem .6rem;border-radius:999px;background:#EDF7F4;color:#267563;font-size:.74rem;font-weight:800}
    .notice{padding:1rem 1.1rem;border-left:4px solid var(--green);background:#F1F9F6;border-radius:12px;margin:1rem 0}
    .footerx{margin-top:3rem;padding-top:1.2rem;border-top:1px solid var(--line);font-size:.85rem;color:var(--muted)}
    .stButton>button{border-radius:12px}
    @media(max-width:850px){.brandbar{align-items:flex-start;flex-direction:column}.hero{padding:2.4rem 1.4rem;border-radius:24px}.detail-header{align-items:flex-start}}
    </style>
    """,
    unsafe_allow_html=True,
)


def nav() -> None:
    labels = ["Inicio", "Calendario", "Vacunas", "Dónde vacunarme", "Información", "Novedades", "Fuentes oficiales"]
    cols = st.columns(4)
    for i, label in enumerate(labels):
        with cols[i % 4]:
            if st.button(label, use_container_width=True, key=f"nav_{label}"):
                st.session_state.section = label
                st.rerun()


def heading(label: str, title: str, copy: str = "") -> None:
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if copy:
        st.markdown(f'<div class="section-copy">{copy}</div>', unsafe_allow_html=True)


def render_home() -> None:
    st.markdown(
        """
        <<section class="hero">
    <h1>VACUNACIÓN PLATAFORMA DIGITAL</h1>

    
        Información oficial sobre vacunación para todas las etapas de la vida.
    
</section>
        """,
        unsafe_allow_html=True,
    )
    heading("Accesos", "Consultá la plataforma")
    cards = [
        ("Calendario", "Vacunas organizadas por cada etapa de la vida.", "#E9A8C4"),
        ("Vacunas", "Biblioteca de vacunas con esquema y fuente.", "#78C6E7"),
        ("Dónde vacunarme", "Mapa interactivo de San Francisco.", "#73D3C6"),
        ("Información", "Preguntas frecuentes y cuidados del carnet.", "#F3C65D"),
        ("Novedades", "Campañas y avisos oficiales.", "#A997E7"),
        ("Fuentes oficiales", "Origen y actualización de cada contenido.", "#8CCB85"),
    ]
    cols = st.columns(3)
    for i, (title, desc, accent) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(
                f'<div class="vaccine-card" style="border-top:5px solid {accent}"><h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Abrir {title}", key=f"home_{title}", use_container_width=True):
                st.session_state.section = title
                st.rerun()


def render_calendar() -> None:
    heading(
        "Calendario",
        "Calendario por etapas de la vida",
        "Seleccioná una etapa para consultar toda la información dentro de la plataforma.",
    )

    stage_names = list(STAGES.keys())

    cols = st.columns(4)
    for index, (name, data) in enumerate(STAGES.items()):
        with cols[index % 4]:
            st.markdown(
                f"""
                <div class="stage-card" style="background:{data['soft']};border-top:5px solid {data['color']}">
                    <h3>{name}</h3>
                    <p>{data['subtitle']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    selected_stage = st.selectbox(
        "Etapa de la vida",
        stage_names,
        index=stage_names.index(st.session_state.selected_stage),
        key="calendar_stage_selector",
    )
    st.session_state.selected_stage = selected_stage

    data = STAGES[selected_stage]
    st.markdown(
        f"""
        <div class="detail-card" style="border-top:6px solid {data['color']}">
            <div class="detail-header">
                <div class="source-chip">Etapa seleccionada</div>
                <h2 style="margin:.45rem 0">{selected_stage}</h2>
                <div style="color:#6A7B8B">{data['subtitle']}</div>
            </div>
            <p>{data['intro']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for label, item_text in data["items"]:
        st.markdown(
            f'<div class="dose-row"><strong>{label}</strong><br>{item_text}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="notice">{data["note"]}</div>',
        unsafe_allow_html=True,
    )
    st.link_button(
        "Abrir fuente oficial de esta etapa",
        data["source"],
        use_container_width=True,
    )


def render_vaccines() -> None:
    heading(
        "Biblioteca",
        "Vacunas",
        "Abrí cada ficha directamente dentro de la plataforma.",
    )

    search_col, filter_col = st.columns([2, 1])

    with search_col:
        query = st.text_input(
            "Buscar vacuna o enfermedad",
            placeholder="Ej.: VPH, gripe, sarampión...",
            key="vaccine_query_final",
        )

    with filter_col:
        stage_filter = st.selectbox(
            "Filtrar por etapa",
            ["Todas"] + sorted({vaccine["stage"] for vaccine in VACCINES}),
            key="vaccine_stage_filter_final",
        )

    filtered_vaccines = VACCINES

    if query:
        term = query.lower().strip()
        filtered_vaccines = [
            vaccine
            for vaccine in filtered_vaccines
            if term
            in (
                vaccine["name"]
                + " "
                + vaccine["protects"]
                + " "
                + vaccine["stage"]
                + " "
                + vaccine["who"]
                + " "
                + vaccine["details"]
            ).lower()
        ]

    if stage_filter != "Todas":
        filtered_vaccines = [
            vaccine
            for vaccine in filtered_vaccines
            if vaccine["stage"] == stage_filter
        ]

    if not filtered_vaccines:
        st.warning("No se encontraron vacunas con esos criterios.")
        return

    st.caption(
        f"Se muestran {len(filtered_vaccines)} fichas. "
        "Tocá el nombre de una vacuna para abrir o cerrar su contenido."
    )

    for vaccine in filtered_vaccines:
        with st.expander(
            f"{vaccine['name']} — {vaccine['stage']}",
            expanded=False,
        ):
            st.markdown(f"## {vaccine['name']}")
            st.write(f"**Protege contra:** {vaccine['protects']}")
            st.write(f"**Población objetivo:** {vaccine['who']}")
            st.write(f"**Esquema:** {vaccine['scheme']}")
            st.write(f"**Vía de administración:** {vaccine['route']}")

            st.markdown("### Información principal")
            st.write(vaccine["details"])

            st.markdown("### Efectos esperables")
            st.write(vaccine["expected"])

            st.markdown("### Precauciones")
            st.write(vaccine["precautions"])

            st.info(
                "La ficha es informativa. La evaluación individual corresponde "
                "al equipo de salud."
            )

            st.link_button(
                "Abrir fuente oficial",
                vaccine["source"],
                use_container_width=True,
                key=f"official_source_{vaccine['name']}",
            )


def render_centers() -> None:
    heading(
        "Territorio",
        "Dónde vacunarme",
        "Permití el acceso a tu ubicación para ver primero los centros más cercanos.",
    )

    st.markdown(
        '<div class="notice">La ubicación se utiliza únicamente durante esta sesión. '
        'No se guarda ni se incorpora a ningún registro.</div>',
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

    search = st.text_input(
        "Buscar centro o dirección",
        placeholder="Ej.: La Milka, Resistencia, Asistencia Pública...",
        key="center_search_final",
    )

    filtered_centers = CENTERS
    if search:
        term = search.lower().strip()
        filtered_centers = [
            center
            for center in CENTERS
            if term in (center["name"] + " " + center["address"]).lower()
        ]

    if not filtered_centers:
        st.warning("No se encontraron centros con ese criterio.")
        return

    user_location = st.session_state.user_location

    if user_location:
        ranked_centers = nearest_centers(
            user_location["lat"],
            user_location["lon"],
            filtered_centers,
        )
        map_center = [user_location["lat"], user_location["lon"]]
        map_zoom = 15
        nearest = ranked_centers[0]
    else:
        ranked_centers = filtered_centers
        map_center = [-31.427, -62.086]
        map_zoom = 13
        nearest = None
        st.info(
            "Para centrar el mapa en tu posición, presioná el botón de ubicación "
            "y aceptá el permiso del navegador."
        )

    map_object = folium.Map(
        location=map_center,
        zoom_start=map_zoom,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    if user_location:
        folium.CircleMarker(
            location=[user_location["lat"], user_location["lon"]],
            radius=10,
            tooltip="Tu ubicación",
            color="#15314A",
            weight=3,
            fill=True,
            fill_color="#15314A",
            fill_opacity=1,
        ).add_to(map_object)

        folium.PolyLine(
            [
                [user_location["lat"], user_location["lon"]],
                [nearest["lat"], nearest["lon"]],
            ],
            color="#15314A",
            weight=3,
            opacity=0.75,
        ).add_to(map_object)

    for center in ranked_centers:
        distance_text = ""
        if user_location:
            distance_text = (
                f"<br>Distancia aproximada: {center['distance_km']:.2f} km"
            )

        popup = folium.Popup(
            f"<b>{center['name']}</b><br>"
            f"{center['address']}<br>"
            f"Tel.: {center['phone']}<br>"
            f"{center['schedule']}"
            f"{distance_text}<br>"
            f"<a href='https://www.google.com/maps/dir/?api=1&destination="
            f"{center['lat']},{center['lon']}' target='_blank'>Cómo llegar</a>",
            max_width=340,
        )

        folium.CircleMarker(
            location=[center["lat"], center["lon"]],
            radius=8,
            popup=popup,
            tooltip=center["name"],
            color="#2C8F78",
            weight=2,
            fill=True,
            fill_color="#2C8F78",
            fill_opacity=0.9,
        ).add_to(map_object)

    st_folium(
        map_object,
        width=None,
        height=560,
        returned_objects=[],
        key="final_centers_map",
    )

    if nearest:
        st.markdown("### Centro más cercano")
        st.success(
            f"{nearest['name']} — {nearest['distance_km']:.2f} km aproximadamente."
        )
        st.caption(
            "La distancia se calcula en línea recta. El recorrido real puede variar."
        )
        st.markdown(
            f"[Abrir recorrido al centro más cercano]"
            f"(https://www.google.com/maps/dir/?api=1&destination="
            f"{nearest['lat']},{nearest['lon']})"
        )

    st.markdown(
        "### Centros ordenados por cercanía"
        if user_location
        else "### Centros disponibles"
    )

    for center in ranked_centers:
        distance_label = ""
        if user_location:
            distance_label = f" · {center['distance_km']:.2f} km"

        with st.expander(
            f"{center['name']} · {center['address']}{distance_label}"
        ):
            st.write(f"**Teléfono:** {center['phone']}")
            st.write(f"**Horario:** {center['schedule']}")
            st.markdown(
                f"[Abrir recorrido en Google Maps]"
                f"(https://www.google.com/maps/dir/?api=1&destination="
                f"{center['lat']},{center['lon']})"
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
    heading("Novedades", "Novedades oficiales", "Campañas y avisos con enlace a la publicación original.")
    st.markdown(
        """
        <div class="detail-card">
            <span class="source-chip">Campaña 2026</span>
            <h3>Campaña de vacunación antigripal en San Francisco</h3>
            <p>
                La Municipalidad informó vacunación en Asistencia Pública y CAPS seleccionados.
                La disponibilidad y los horarios deben confirmarse antes de asistir.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "Abrir anuncio municipal",
        "https://www.sanfrancisco.gov.ar/noticia/municipio-comienza-con-la-campana-de-vacunacion-antigripal-2026-6732",
        use_container_width=True,
    )


def render_sources() -> None:
    heading("Transparencia", "Fuentes oficiales", "La plataforma verifica automáticamente la disponibilidad y detecta cambios en las páginas fuente.")
    if st.button("Actualizar fuentes ahora", use_container_width=True):
        source_snapshot.clear()
        st.rerun()
    for source in OFFICIAL_SOURCES:
        snap = source_snapshot(source["url"])
        with st.expander(f"{source['name']} · {source['institution']}"):
            st.write(f"**Tipo:** {source['type']}")
            st.write(f"**Estado:** {'Disponible' if snap['ok'] else 'Sin respuesta'}")
            st.write(f"**Última consulta automática:** {snap['checked_at']}")
            st.write(f"**Huella de contenido:** {snap['hash']}")
            st.link_button("Abrir fuente", source["url"], key=f"source_{source['name']}")


PAGES = {
    "Inicio": render_home,
    "Calendario": render_calendar,
    "Vacunas": render_vaccines,
    "Dónde vacunarme": render_centers,
    "Información": render_information,
    "Novedades": render_news,
    "Fuentes oficiales": render_sources,
}

st.markdown(
    f"""
    <div class="brandbar">
        <div class="brandtitle">{APP_NAME}</div>
        <div class="brandmeta">San Francisco · Córdoba</div>
    </div>
    """,
    unsafe_allow_html=True,
)

nav()
st.divider()
PAGES[st.session_state.section]()
st.markdown(f'<div class="footerx"><strong>{DEVELOPER}</strong><br>Última revisión de contenidos: {LAST_CONTENT_REVIEW}</div>', unsafe_allow_html=True)
