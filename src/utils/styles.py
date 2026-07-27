import streamlit as st

def inject_global_styles() -> None:
    st.markdown(
        '''
        <style>
        :root {
            --green:#2C8F78; --green-dark:#1F6D5D; --blue:#DDF2FA;
            --navy:#12304A; --muted:#617486; --soft:#F4F8FB;
            --line:#DDE7EE; --white:#FFFFFF;
        }
        .stApp { background:var(--white); color:var(--navy); }
        .block-container { max-width:1240px; padding-top:1.2rem; padding-bottom:3rem; }
        #MainMenu, footer, header { visibility:hidden; }
        h1,h2,h3 { color:var(--navy); letter-spacing:-.03em; }
        .topbar { display:flex; justify-content:space-between; gap:1rem; padding:.8rem 0 1.2rem; border-bottom:1px solid var(--line); margin-bottom:1.8rem; }
        .brand { font-weight:800; color:var(--navy); text-decoration:none; }
        .brand span { color:var(--green); }
        .nav-links { display:flex; flex-wrap:wrap; gap:.35rem; justify-content:flex-end; }
        .nav-link { text-decoration:none; color:var(--muted); font-size:.9rem; font-weight:650; padding:.55rem .7rem; border-radius:999px; }
        .nav-link:hover,.nav-link.active { color:var(--navy); background:var(--soft); }
        .hero { padding:3.5rem 2.8rem; border-radius:28px; background:radial-gradient(circle at top right, rgba(221,242,250,.95), transparent 34%), linear-gradient(135deg,#F7FCFD 0%,#FFFFFF 58%); border:1px solid var(--line); box-shadow:0 18px 50px rgba(18,48,74,.07); margin-bottom:2rem; }
        .hero-badge { display:inline-flex; padding:.45rem .72rem; border-radius:999px; background:rgba(44,143,120,.10); color:var(--green-dark); font-weight:750; font-size:.82rem; margin-bottom:1rem; }
        .hero h1 { max-width:780px; font-size:clamp(2.3rem,5vw,4.6rem); line-height:.98; margin:0 0 1rem; }
        .hero-copy { max-width:720px; color:var(--muted); font-size:1.15rem; line-height:1.7; }
        .hero-actions { display:flex; flex-wrap:wrap; gap:.8rem; margin-top:1.5rem; }
        .btn { text-decoration:none !important; border-radius:14px; padding:.85rem 1.1rem; font-weight:800; display:inline-block; }
        .btn-primary { background:var(--green); color:white !important; }
        .btn-secondary { background:var(--navy); color:white !important; }
        .btn-ghost { border:1px solid var(--line); color:var(--navy) !important; background:white; }
        .feature-card { min-height:220px; padding:1.35rem; border-radius:20px; border:1px solid var(--line); background:white; margin-bottom:1.1rem; }
        .feature-icon { width:46px; height:46px; border-radius:14px; display:grid; place-items:center; background:var(--blue); font-size:1.35rem; margin-bottom:1rem; }
        .feature-card h3 { margin:0 0 .55rem; font-size:1.15rem; }
        .feature-card p { color:var(--muted); line-height:1.55; min-height:70px; }
        .feature-card a { color:var(--green-dark); text-decoration:none; font-weight:800; }
        .page-intro { background:var(--soft); border:1px solid var(--line); border-radius:22px; padding:2rem; margin-bottom:1.4rem; }
        .notice { border-left:4px solid var(--green); background:#F5FBF9; padding:1rem 1.1rem; border-radius:12px; color:var(--navy); margin:1rem 0; }
        .site-footer { margin-top:3rem; border-top:1px solid var(--line); padding-top:1.5rem; color:var(--muted); font-size:.85rem; display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap; }
        @media (max-width:850px) {
            .topbar { align-items:flex-start; flex-direction:column; }
            .nav-links { justify-content:flex-start; }
            .hero { padding:2.2rem 1.35rem; border-radius:22px; }
        }
        </style>
        ''',
        unsafe_allow_html=True,
    )
