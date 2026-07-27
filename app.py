import streamlit as st
import pandas as pd

st.set_page_config(page_title='VACUNACION Plataforma Digital', page_icon='💉', layout='wide', initial_sidebar_state='collapsed')

DEVELOPER = 'EGS | Estudio de Gestión de Sistemas'

if 'section' not in st.session_state:
    st.session_state.section = 'Inicio'
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

CALENDAR_STAGES = {
    'Embarazo': ('🤰', 'Antes y durante el embarazo', 'Espacio preparado para información oficial validada durante el embarazo, con lenguaje claro, alertas y referencias visibles.'),
    'Recién nacido': ('👶', 'Desde el nacimiento', 'Información organizada para acompañar los primeros controles y facilitar la lectura del calendario oficial.'),
    'Infancia': ('🧒', 'Primeros años', 'Navegación por edades, fichas verificables y explicaciones para familias.'),
    'Edad escolar': ('🎒', 'Etapa escolar', 'Contenidos vinculados a la edad escolar, campañas y recuperación de esquemas.'),
    'Adolescencia': ('🧑', 'Adolescencia', 'Información directa para adolescentes, familias y equipos educativos.'),
    'Adultez': ('👩', 'Vida adulta', 'Orientación general por etapa de vida, trabajo, viajes y situaciones especiales.'),
    'Personas mayores': ('👵', 'Personas mayores', 'Acceso legible, simple y accesible a información relevante y campañas.'),
}

VACCINES = [
    {'name':'Ficha demostrativa 01','protects':'Contenido sanitario pendiente de validación','audience':'Población objetivo pendiente de validación','stage':'Infancia','summary':'La ficha definitiva incluirá resumen de un minuto, enfermedad, población objetivo, esquema, dosis, situaciones especiales, contraindicaciones, efectos adversos, mitos, preguntas frecuentes y referencias oficiales.','status':'Borrador'},
    {'name':'Ficha demostrativa 02','protects':'Contenido sanitario pendiente de validación','audience':'Población objetivo pendiente de validación','stage':'Adolescencia','summary':'El contenido se publicará únicamente después de revisión humana, trazabilidad de fuente y fecha de actualización.','status':'Borrador'},
    {'name':'Ficha demostrativa 03','protects':'Contenido sanitario pendiente de validación','audience':'Población objetivo pendiente de validación','stage':'Adultez','summary':'La plataforma no determina vacunas faltantes ni reemplaza el carnet o la consulta profesional.','status':'Borrador'},
]

INFO_TOPICS = [
    ('🛡️','Seguridad de las vacunas','Cómo se controlan, qué se evalúa y dónde consultar.'),
    ('🤰','Embarazo','Información específica y contenidos revisados.'),
    ('👶','Vacunación infantil','Explicaciones claras para madres, padres y cuidadores.'),
    ('🧑','Adolescencia','Información adaptada a esta etapa de vida.'),
    ('👵','Personas mayores','Contenidos accesibles y situaciones frecuentes.'),
    ('❤️','Enfermedades crónicas','Orientación general y consulta con el equipo de salud.'),
    ('✈️','Viajes','Qué revisar antes de viajar y dónde buscar información oficial.'),
    ('🕒','Esquemas atrasados','Qué hacer cuando un esquema no está completo.'),
    ('📄','Pérdida del carnet','Opciones para recuperar o verificar antecedentes.'),
    ('💬','Mitos y desinformación','Respuestas basadas en fuentes oficiales.'),
]

CENTERS = pd.DataFrame([{'Centro':'Centro pendiente de verificación','Localidad':'San Francisco','Provincia':'Córdoba','Dirección':'Pendiente','Horarios':'Pendiente','Accesibilidad':'Pendiente','Estado':'Borrador'}])

st.markdown('''
<style>
:root{--green:#2C8F78;--green-dark:#1F6D5D;--green-soft:#EAF7F3;--navy:#12304A;--blue:#DDF2FA;--soft:#F6F9FB;--muted:#617486;--line:#DDE7EE;--white:#FFFFFF;--warning:#FFF7DF;--shadow:0 18px 50px rgba(18,48,74,.08)}
.stApp{background:var(--white);color:var(--navy)}
.block-container{max-width:1240px;padding-top:1rem;padding-bottom:3rem}
#MainMenu,footer,header{visibility:hidden}
h1,h2,h3{color:var(--navy);letter-spacing:-.03em} p{line-height:1.65}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.9rem 0 1.2rem;border-bottom:1px solid var(--line);margin-bottom:1.25rem}
.brand{font-weight:900;font-size:1.05rem;color:var(--navy);letter-spacing:-.02em}.brand span{color:var(--green)}
.top-meta{color:var(--muted);font-size:.82rem;font-weight:700}
.hero{padding:3.8rem 3rem;border-radius:30px;background:radial-gradient(circle at 82% 12%,rgba(221,242,250,.95),transparent 28%),radial-gradient(circle at 96% 88%,rgba(234,247,243,.9),transparent 26%),linear-gradient(135deg,#F9FCFD 0%,#FFFFFF 60%);border:1px solid var(--line);box-shadow:var(--shadow);margin-bottom:1.8rem;overflow:hidden}
.hero-badge{display:inline-flex;padding:.48rem .78rem;border-radius:999px;background:var(--green-soft);color:var(--green-dark);font-weight:850;font-size:.8rem;margin-bottom:1.1rem}
.hero h1{max-width:820px;font-size:clamp(2.5rem,5.4vw,5rem);line-height:.98;margin:0 0 1rem}.hero p{max-width:760px;color:var(--muted);font-size:1.14rem;margin-bottom:0}
.section-header{margin:2.3rem 0 1rem}.section-header span{color:var(--green-dark);font-size:.76rem;font-weight:900;text-transform:uppercase;letter-spacing:.1em}.section-header h2{margin:.35rem 0 .4rem;font-size:2rem}.section-header p{color:var(--muted);margin:0}
.module-card{min-height:220px;padding:1.4rem;border-radius:22px;border:1px solid var(--line);background:var(--white);margin-bottom:1rem;transition:transform .18s ease,box-shadow .18s ease}.module-card:hover{transform:translateY(-4px);box-shadow:0 16px 36px rgba(18,48,74,.09)}
.module-icon{width:48px;height:48px;border-radius:15px;display:grid;place-items:center;background:var(--blue);font-size:1.4rem;margin-bottom:1rem}.module-card p{color:var(--muted);min-height:70px}
.stage-card{display:grid;grid-template-columns:74px 1fr;gap:1.25rem;align-items:center;padding:1.6rem;border:1px solid var(--line);border-radius:24px;background:linear-gradient(135deg,#FFFFFF 0%,#F5FBFD 100%);margin:1.2rem 0}.stage-icon{width:70px;height:70px;border-radius:20px;background:var(--blue);display:grid;place-items:center;font-size:2.15rem}.stage-kicker{color:var(--green-dark);font-size:.72rem;font-weight:900;text-transform:uppercase;letter-spacing:.09em}.stage-card h2{margin:.25rem 0 .45rem}.stage-card p{margin:0;color:var(--muted)}
.timeline{border-left:2px solid var(--line);margin:1.5rem 0 0 1rem;padding-left:1.6rem}.timeline-item{position:relative;padding:0 0 1.5rem}.timeline-item:before{content:'';position:absolute;width:12px;height:12px;border-radius:50%;left:-1.98rem;top:.35rem;background:var(--green);box-shadow:0 0 0 5px rgba(44,143,120,.12)}.timeline-item h3{margin:0 0 .35rem;font-size:1.05rem}.timeline-item p{margin:0;color:var(--muted)}
.notice{border-left:4px solid var(--green);background:#F4FBF8;padding:1rem 1.1rem;border-radius:12px;margin:1rem 0}.warning-box{border-left:4px solid #D6A800;background:var(--warning);padding:1rem 1.1rem;border-radius:12px;margin:1rem 0}
.topic-card{padding:1.15rem;border:1px solid var(--line);border-radius:18px;background:var(--white);min-height:180px;margin-bottom:1rem}.topic-card .icon{font-size:1.45rem;margin-bottom:.7rem}.topic-card p{color:var(--muted);font-size:.92rem}
.metric-card{padding:1.2rem;border:1px solid var(--line);border-radius:18px;background:var(--soft)}.metric-card strong{display:block;font-size:1.8rem;color:var(--navy)}.metric-card span{color:var(--muted);font-size:.85rem}
.footer{margin-top:3rem;border-top:1px solid var(--line);padding-top:1.4rem;color:var(--muted);font-size:.85rem}
@media(max-width:850px){.topbar{align-items:flex-start;flex-direction:column}.hero{padding:2.3rem 1.4rem;border-radius:24px}.stage-card{grid-template-columns:1fr}}
</style>
''', unsafe_allow_html=True)


def render_header():
    st.markdown("<div class='topbar'><div class='brand'>VACUNACION <span>Plataforma Digital</span></div><div class='top-meta'>Información pública · Accesible · Territorial</div></div>", unsafe_allow_html=True)


def render_footer():
    st.markdown(f"<div class='footer'><strong>{DEVELOPER}</strong></div>", unsafe_allow_html=True)


def render_navigation():
    sections=[('Inicio','🏠'),('Calendario','📅'),('Orientación','🧭'),('Vacunas','💉'),('Información','📘'),('Dónde vacunarme','📍'),('Novedades','🔔'),('Administración','⚙️')]
    cols=st.columns(4)
    for i,(label,icon) in enumerate(sections):
        with cols[i%4]:
            if st.button(f'{icon} {label}',use_container_width=True,key=f'nav_{label}'):
                st.session_state.section=label
                st.rerun()


def section_header(kicker,title,description):
    st.markdown(f"<div class='section-header'><span>{kicker}</span><h2>{title}</h2><p>{description}</p></div>", unsafe_allow_html=True)


def render_home():
    st.markdown("""
    <section class='hero'>
      <div class='hero-badge'>Información pública clara y confiable</div>
      <h1>Todo sobre vacunación, en un solo lugar.</h1>
      <p>Consultá el calendario, recibí orientación general, conocé cada vacuna, encontrá información útil y accedé a los puntos de vacunación.</p>
    </section>
    """, unsafe_allow_html=True)
    query=st.text_input('Buscar',placeholder='Ej.: vacuna contra la gripe, perdí el carnet, estoy embarazada...',key='home_search')
    if query:
        st.session_state.search_history.append(query)
        st.info(f'Consulta recibida: “{query}”. El buscador definitivo funcionará solo sobre contenido aprobado.')
    section_header('Accesos principales','Elegí qué necesitás consultar','La plataforma organiza la información por necesidad ciudadana.')
    modules=[('📅','Calendario','Recorré la vacunación por etapa de vida.'),('🧭','Orientación','Recibí orientación general basada en reglas.'),('💉','Vacunas','Consultá fichas claras, trazables y verificables.'),('📘','Información','Embarazo, viajes, carnet, mitos y más.'),('📍','Dónde vacunarme','Accedé a centros y datos territoriales.'),('🔔','Novedades','Campañas, operativos y alertas vigentes.')]
    cols=st.columns(3,gap='large')
    for i,(icon,title,description) in enumerate(modules):
        with cols[i%3]:
            st.markdown(f"<article class='module-card'><div class='module-icon'>{icon}</div><h3>{title}</h3><p>{description}</p></article>", unsafe_allow_html=True)
            if st.button(f'Abrir {title}',key=f'open_{title}',use_container_width=True):
                st.session_state.section=title
                st.rerun()
    section_header('Confianza','Información preparada para ser verificable','Cada contenido tendrá fuente, fecha de revisión y estado editorial.')
    c1,c2,c3=st.columns(3)
    with c1: st.markdown("<div class='metric-card'><strong>100%</strong><span>Contenido con fuente visible</span></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='metric-card'><strong>0</strong><span>Datos personales requeridos en V1</span></div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='metric-card'><strong>WCAG</strong><span>Objetivo de accesibilidad 2.2 AA</span></div>", unsafe_allow_html=True)


def render_calendar():
    section_header('Calendario','Calendario de vacunación por etapa de vida','Explorá la información de forma cronológica y comprensible.')
    stage=st.segmented_control('Etapa de vida',options=list(CALENDAR_STAGES.keys()),default='Embarazo',label_visibility='collapsed')
    icon,kicker,description=CALENDAR_STAGES[stage]
    st.markdown(f"<div class='stage-card'><div class='stage-icon'>{icon}</div><div><span class='stage-kicker'>{kicker}</span><h2>{stage}</h2><p>{description}</p></div></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='timeline'>
      <div class='timeline-item'><h3>Información principal</h3><p>Espacio preparado para el esquema oficial, edades y dosis.</p></div>
      <div class='timeline-item'><h3>Situaciones especiales</h3><p>Se incorporarán condiciones, viajes, embarazo y otras situaciones.</p></div>
      <div class='timeline-item'><h3>Fuentes y revisión</h3><p>Cada recomendación mostrará fuente oficial y fecha de actualización.</p></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='warning-box'><strong>BORRADOR — NO PUBLICAR.</strong><br>Esta versión prueba la arquitectura y la experiencia de usuario. Todavía no contiene un calendario sanitario oficial.</div>", unsafe_allow_html=True)


def render_orientation():
    section_header('Orientación','¿Qué vacunas podrían corresponderme?','Respondé unas preguntas breves para recibir orientación general.')
    st.markdown("<div class='notice'>La plataforma no determina vacunas faltantes. La orientación se construye únicamente a partir de la información ingresada y siempre recomienda verificar el carnet o consultar en un vacunatorio.</div>", unsafe_allow_html=True)
    with st.form('orientation_form'):
        c1,c2=st.columns(2)
        with c1:
            age=st.number_input('Edad',min_value=0,max_value=120,step=1)
            pregnancy=st.selectbox('¿Cursa un embarazo?',['No corresponde','No','Sí'])
            chronic=st.selectbox('¿Tiene alguna enfermedad crónica?',['No sé','No','Sí'])
        with c2:
            travel=st.selectbox('¿Tiene un viaje próximo?',['No','Sí'])
            card=st.selectbox('¿Tiene disponible su carnet?',['Sí','No','No sé'])
            special=st.selectbox('¿Existe alguna situación especial?',['No sé','No','Sí'])
        submitted=st.form_submit_button('Obtener orientación general',use_container_width=True)
    if submitted:
        st.markdown(f"<div class='notice'><strong>Según la información ingresada</strong>, podrían ser relevantes contenidos para una persona de {age} años. Verificá tu carnet o consultá en un vacunatorio.</div>", unsafe_allow_html=True)
        results=[]
        if pregnancy=='Sí': results.append('Información aprobada relacionada con embarazo.')
        if chronic=='Sí': results.append('Información aprobada sobre enfermedades crónicas.')
        if travel=='Sí': results.append('Información aprobada vinculada a viajes.')
        if card!='Sí': results.append('Cómo recuperar o verificar antecedentes de vacunación.')
        if special=='Sí': results.append('Consulta profesional por situación especial.')
        for item in results or ['La plataforma mostrará información general para la etapa de vida ingresada.']:
            st.info(item)


def render_vaccines():
    section_header('Vacunas','Biblioteca de vacunas','Buscá por vacuna, enfermedad, etapa de vida o situación.')
    c1,c2=st.columns([2,1])
    with c1: query=st.text_input('Buscar vacuna, enfermedad o etapa',key='vaccine_search',placeholder='Ej.: gripe, VPH, tétanos, embarazo...')
    with c2: stage_filter=st.selectbox('Filtrar por etapa',['Todas']+sorted({x['stage'] for x in VACCINES}))
    results=VACCINES
    if query:
        q=query.lower(); results=[x for x in results if q in x['name'].lower() or q in x['protects'].lower() or q in x['audience'].lower() or q in x['stage'].lower() or q in x['summary'].lower()]
    if stage_filter!='Todas': results=[x for x in results if x['stage']==stage_filter]
    if not results: st.warning('No se encontraron resultados.')
    for item in results:
        with st.expander(f"{item['name']} · {item['stage']}"):
            st.markdown('### Resumen en un minuto'); st.write(item['summary'])
            st.markdown('### Protege contra'); st.write(item['protects'])
            st.markdown('### Población objetivo'); st.write(item['audience'])
            st.caption(f"Estado editorial: {item['status']} · Fuente: pendiente · Revisión: pendiente")


def render_information():
    section_header('Información','Información clara para situaciones reales','Explorá temas frecuentes con lenguaje directo y fuentes oficiales.')
    cols=st.columns(3,gap='large')
    for i,(icon,title,description) in enumerate(INFO_TOPICS):
        with cols[i%3]:
            st.markdown(f"<article class='topic-card'><div class='icon'>{icon}</div><h3>{title}</h3><p>{description}</p></article>", unsafe_allow_html=True)
            with st.expander('Ver contenido'):
                st.write('Contenido pendiente de revisión y publicación. La ficha final incluirá explicación, preguntas frecuentes, mitos, fuentes y fecha de actualización.')


def render_centers():
    section_header('Territorio','Dónde vacunarme','Encontrá centros, horarios, accesibilidad y rutas en San Francisco.')
    st.markdown("<div class='warning-box'>Los centros, horarios y coordenadas todavía no fueron verificados. No se publicarán ubicaciones hasta completar la validación institucional.</div>", unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1: st.selectbox('Tipo de centro',['Todos','Hospital','Centro de salud','Operativo'])
    with c2: st.selectbox('Accesibilidad',['Todas','Acceso adaptado','Información pendiente'])
    with c3: st.selectbox('Servicio',['Todos','Vacunación general','Campaña','Información pendiente'])
    st.dataframe(CENTERS,use_container_width=True,hide_index=True)
    st.markdown("<div class='section-box'><h3>Mapa inteligente</h3><p>Esta sección incorporará geolocalización, centro más cercano, rutas, filtros, clustering y fecha de verificación.</p></div>", unsafe_allow_html=True)


def render_news():
    section_header('Novedades','Campañas y anuncios oficiales','Información temporal separada del calendario permanente.')
    st.markdown("<div class='section-box'><span class='stage-kicker'>Estado actual</span><h3>Sin novedades publicadas</h3><p>El módulo está preparado para campañas, operativos, cambios de horarios y avisos institucionales.</p></div>", unsafe_allow_html=True)
    with st.expander('Flujo editorial'): st.code('Borrador → Revisión → Aprobación → Publicación → Archivo')


def render_admin():
    section_header('Administración','Panel de gestión','Control editorial, territorial y analítico de la plataforma.')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Contenidos en borrador',len(VACCINES)); c2.metric('Fuentes verificadas',0); c3.metric('Centros verificados',0); c4.metric('Búsquedas de prueba',len(st.session_state.search_history))
    st.markdown('### Módulos administrativos')
    modules=['Dashboard','Contenidos','Vacunatorios','Fuentes oficiales','Inteligencia','Versionado','Configuración','Backup y seguridad']
    cols=st.columns(4)
    for i,item in enumerate(modules):
        with cols[i%4]: st.markdown(f"<div class='topic-card'><h3>{item}</h3><p>Sección preparada para la siguiente etapa de desarrollo.</p></div>", unsafe_allow_html=True)
    st.markdown('### Búsquedas registradas en esta sesión')
    if st.session_state.search_history: st.write(st.session_state.search_history[-10:])
    else: st.info('Todavía no se registraron búsquedas.')

PAGES={'Inicio':render_home,'Calendario':render_calendar,'Orientación':render_orientation,'Vacunas':render_vaccines,'Información':render_information,'Dónde vacunarme':render_centers,'Novedades':render_news,'Administración':render_admin}
render_header(); render_navigation(); st.divider(); PAGES.get(st.session_state.section,render_home)(); render_footer()
