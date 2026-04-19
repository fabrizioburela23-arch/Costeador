import os

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx
from formulas import FinancialCalculator
from db import CosteosDB


if __name__ == "__main__" and get_script_run_ctx(suppress_warning=True) is None:
    os.execvp(
        "streamlit",
        [
            "streamlit",
            "run",
            __file__,
            "--server.port",
            os.environ.get("PORT", "8501"),
            "--server.address",
            "0.0.0.0",
            "--server.headless",
            "true",
        ],
    )


st.set_page_config(
    page_title="Costeador Atelier",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────
# PREMIUM DARK THEME — High-contrast, glassmorphism, animations
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        /* ── COLOR TOKENS ── */
        :root {
            --bg-base: #0b0f19;
            --bg-surface: rgba(17, 22, 36, 0.85);
            --bg-elevated: rgba(25, 32, 52, 0.88);
            --bg-card: rgba(30, 38, 60, 0.65);
            --bg-input: rgba(20, 26, 44, 0.9);

            --text-primary: #f0f2f8;
            --text-secondary: #a0a8c0;
            --text-muted: #6b7394;

            --accent: #a855f7;
            --accent-light: #c084fc;
            --accent-glow: rgba(168, 85, 247, 0.25);
            --accent-2: #6366f1;
            --accent-2-glow: rgba(99, 102, 241, 0.2);

            --success: #34d399;
            --warning: #fbbf24;
            --danger: #f87171;

            --border: rgba(148, 163, 210, 0.12);
            --border-hover: rgba(168, 85, 247, 0.35);
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.25);
            --shadow-md: 0 8px 28px rgba(0, 0, 0, 0.35);
            --shadow-lg: 0 16px 48px rgba(0, 0, 0, 0.45);
            --shadow-glow: 0 0 40px var(--accent-glow);

            --radius-sm: 10px;
            --radius-md: 16px;
            --radius-lg: 24px;
            --radius-pill: 999px;
        }

        /* ── BASE ── */
        *, *::before, *::after { box-sizing: border-box; }

        .stApp {
            background:
                radial-gradient(ellipse 80% 50% at 20% -10%, rgba(99, 102, 241, 0.15), transparent),
                radial-gradient(ellipse 60% 40% at 80% 10%, rgba(168, 85, 247, 0.12), transparent),
                radial-gradient(ellipse 50% 50% at 50% 100%, rgba(99, 102, 241, 0.06), transparent),
                var(--bg-base) !important;
            color: var(--text-primary) !important;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        /* ── SCROLLBAR ── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(168, 85, 247, 0.3); border-radius: 8px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(168, 85, 247, 0.5); }

        /* ── HEADER ── */
        [data-testid="stHeader"] {
            background: rgba(11, 15, 25, 0.7) !important;
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
        }

        /* ── SIDEBAR ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(17, 22, 38, 0.97) 0%, rgba(11, 15, 25, 0.98) 100%) !important;
            border-right: 1px solid var(--border) !important;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stSlider label,
        [data-testid="stSidebar"] span {
            color: var(--text-secondary) !important;
        }

        /* ── MAIN CONTENT ── */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        /* ── BRAND HEADER ── */
        .brand-shell {
            background: var(--bg-card);
            backdrop-filter: blur(24px) saturate(1.4);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.5rem 1.75rem;
            box-shadow: var(--shadow-md), var(--shadow-glow);
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }

        .brand-shell::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--accent-2), var(--accent), var(--accent-2));
            opacity: 0.8;
        }

        .brand-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .brand-kicker {
            color: var(--accent-light);
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-weight: 800;
            font-size: 0.72rem;
            margin-bottom: 0.4rem;
        }

        .brand-title {
            font-size: 2.4rem;
            line-height: 1.05;
            font-weight: 900;
            letter-spacing: -0.04em;
            color: var(--text-primary);
            margin: 0;
        }

        .brand-title span {
            background: linear-gradient(135deg, var(--accent), var(--accent-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-copy {
            color: var(--text-secondary);
            max-width: 760px;
            font-size: 0.95rem;
            margin-top: 0.5rem;
            line-height: 1.55;
        }

        .nav-pill-row {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            justify-content: flex-end;
        }

        .nav-pill {
            background: var(--bg-input);
            border: 1px solid var(--border);
            color: var(--text-muted);
            border-radius: var(--radius-pill);
            padding: 0.5rem 0.9rem;
            font-size: 0.82rem;
            font-weight: 700;
            transition: all 0.25s ease;
        }

        .nav-pill:hover {
            color: var(--text-primary);
            border-color: var(--border-hover);
        }

        .nav-pill.active {
            color: white;
            border-color: transparent;
            background: linear-gradient(135deg, var(--accent-2), var(--accent));
            box-shadow: 0 6px 20px var(--accent-glow);
        }

        /* ── SECTION CARDS ── */
        .section-card {
            background: var(--bg-card);
            backdrop-filter: blur(16px) saturate(1.3);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.4rem;
            box-shadow: var(--shadow-sm);
            margin-bottom: 1rem;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }

        .section-card:hover {
            border-color: var(--border-hover);
            box-shadow: var(--shadow-md);
        }

        .section-title {
            display: flex;
            justify-content: space-between;
            align-items: end;
            gap: 1rem;
            margin-bottom: 0.8rem;
        }

        .section-title h3 {
            margin: 0;
            font-size: 1.15rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-primary);
        }

        .section-title p {
            margin: 0.25rem 0 0 0;
            color: var(--text-secondary);
            font-size: 0.88rem;
            line-height: 1.5;
        }

        /* ── SUMMARY HERO ── */
        .summary-hero {
            background: linear-gradient(145deg, var(--bg-elevated), var(--bg-card));
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.75rem;
            box-shadow: var(--shadow-lg), var(--shadow-glow);
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }

        .summary-hero::before {
            content: "";
            position: absolute;
            width: 260px;
            height: 260px;
            border-radius: 50%;
            background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
            top: -100px;
            right: -60px;
            animation: pulse-glow 4s ease-in-out infinite;
        }

        @keyframes pulse-glow {
            0%, 100% { opacity: 0.4; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }

        .summary-kicker {
            position: relative;
            z-index: 1;
            color: var(--accent-light);
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-size: 0.72rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }

        .summary-headline {
            position: relative;
            z-index: 1;
            background: linear-gradient(135deg, var(--text-primary), var(--accent-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.6rem;
            letter-spacing: -0.05em;
            line-height: 1;
            font-weight: 900;
            margin: 0.2rem 0 0.6rem 0;
        }

        .summary-copy {
            position: relative;
            z-index: 1;
            color: var(--text-secondary);
            margin: 0;
            max-width: 520px;
            line-height: 1.55;
        }

        /* ── MINI CARDS ── */
        .mini-card {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 1rem 1.1rem;
            margin-bottom: 0.75rem;
            transition: all 0.3s ease;
        }

        .mini-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow-sm);
        }

        .mini-label {
            color: var(--accent-light);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 0.7rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .mini-value {
            color: var(--text-primary);
            font-size: 1.4rem;
            font-weight: 850;
            letter-spacing: -0.03em;
        }

        .mini-note {
            color: var(--text-muted);
            font-size: 0.84rem;
            margin-top: 0.3rem;
            line-height: 1.5;
        }

        /* ── GRADIENT CHIP ── */
        .gradient-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.35rem 0.75rem;
            border-radius: var(--radius-pill);
            color: white;
            font-size: 0.76rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-2), var(--accent));
            box-shadow: 0 4px 16px var(--accent-glow);
            letter-spacing: 0.02em;
        }

        /* ── TABS ── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            margin-bottom: 1rem;
            background: transparent !important;
            border-bottom: 1px solid var(--border) !important;
            padding-bottom: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: var(--radius-pill);
            background: var(--bg-input) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-muted) !important;
            font-weight: 700 !important;
            padding: 0.45rem 1rem !important;
            transition: all 0.25s ease !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: var(--text-primary) !important;
            border-color: var(--border-hover) !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--accent-2), var(--accent)) !important;
            color: white !important;
            border-color: transparent !important;
            box-shadow: 0 4px 16px var(--accent-glow) !important;
        }

        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] {
            display: none !important;
        }

        /* ── BUTTONS ── */
        div.stButton > button {
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border) !important;
            background: var(--bg-elevated) !important;
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            font-family: "Inter", sans-serif !important;
            padding: 0.55rem 1rem !important;
            transition: all 0.25s ease !important;
            letter-spacing: 0.01em;
        }

        div.stButton > button:hover {
            border-color: var(--accent) !important;
            color: var(--accent-light) !important;
            box-shadow: 0 4px 16px var(--accent-glow) !important;
            transform: translateY(-1px);
        }

        div.stButton > button:active {
            transform: translateY(0);
        }

        div.stButton > button[kind="primary"],
        div.stButton > button[data-testid="stFormSubmitButton"] {
            border: none !important;
            color: white !important;
            background: linear-gradient(135deg, var(--accent-2), var(--accent)) !important;
            box-shadow: 0 8px 24px var(--accent-glow) !important;
        }

        div.stButton > button[kind="primary"]:hover,
        div.stButton > button[data-testid="stFormSubmitButton"]:hover {
            color: white !important;
            box-shadow: 0 10px 32px rgba(168, 85, 247, 0.4) !important;
            transform: translateY(-2px);
        }

        /* Form submit button */
        [data-testid="stFormSubmitButton"] > button {
            border: none !important;
            color: white !important;
            background: linear-gradient(135deg, var(--accent-2), var(--accent)) !important;
            box-shadow: 0 6px 20px var(--accent-glow) !important;
            font-weight: 800 !important;
            border-radius: var(--radius-sm) !important;
            transition: all 0.25s ease !important;
        }

        [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(168, 85, 247, 0.4) !important;
        }

        /* ── INPUTS ── */
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox [data-baseweb="select"],
        .stTextArea textarea {
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border) !important;
            background: var(--bg-input) !important;
            color: var(--text-primary) !important;
            font-family: "Inter", sans-serif !important;
            transition: all 0.2s ease !important;
        }

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 2px var(--accent-glow) !important;
        }

        /* Input labels */
        .stTextInput label,
        .stNumberInput label,
        .stSelectbox label,
        .stTextArea label,
        .stSlider label,
        .stRadio label,
        .stCheckbox label {
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
        }

        /* Selectbox dropdown */
        [data-baseweb="select"] > div {
            background: var(--bg-input) !important;
            border-color: var(--border) !important;
        }

        [data-baseweb="popover"] {
            background: var(--bg-elevated) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-md) !important;
        }

        [data-baseweb="menu"] {
            background: var(--bg-elevated) !important;
        }

        [data-baseweb="menu"] li {
            color: var(--text-primary) !important;
        }

        [data-baseweb="menu"] li:hover {
            background: var(--accent-glow) !important;
        }

        /* Slider */
        .stSlider [data-baseweb="slider"] [role="slider"] {
            background: var(--accent) !important;
            border: 2px solid var(--accent-light) !important;
        }

        .stSlider [data-testid="stTickBar"] {
            display: none;
        }

        /* ── METRICS ── */
        [data-testid="stMetric"] {
            background: var(--bg-card) !important;
            backdrop-filter: blur(12px);
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-md) !important;
            padding: 0.9rem 1rem !important;
            box-shadow: var(--shadow-sm) !important;
            transition: all 0.3s ease;
        }

        [data-testid="stMetric"]:hover {
            border-color: var(--border-hover) !important;
            box-shadow: var(--shadow-md) !important;
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-muted) !important;
            font-weight: 700 !important;
        }

        [data-testid="stMetricValue"] {
            color: var(--text-primary) !important;
            font-weight: 900 !important;
            letter-spacing: -0.03em !important;
        }

        [data-testid="stMetricDelta"] {
            color: var(--accent-light) !important;
        }

        /* ── DATAFRAME ── */
        [data-testid="stDataFrame"],
        .stDataFrame {
            border-radius: var(--radius-md) !important;
            overflow: hidden;
        }

        /* ── ALERTS ── */
        .stAlert {
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border) !important;
            background: var(--bg-elevated) !important;
        }

        [data-testid="stNotification"] {
            background: var(--bg-elevated) !important;
            color: var(--text-primary) !important;
            border-radius: var(--radius-sm) !important;
        }

        /* ── HISTORY CARDS ── */
        .history-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 1.1rem 1.2rem;
            margin-bottom: 0.75rem;
            transition: all 0.3s ease;
        }

        .history-card:hover {
            border-color: var(--border-hover);
            box-shadow: var(--shadow-sm);
            transform: translateY(-1px);
        }

        /* ── SIDEBAR CARDS ── */
        .sidebar-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow-sm);
        }

        .sidebar-title {
            margin: 0 0 0.3rem 0;
            font-size: 0.95rem;
            font-weight: 800;
            color: var(--text-primary);
        }

        .sidebar-copy {
            margin: 0;
            font-size: 0.84rem;
            color: var(--text-muted);
            line-height: 1.5;
        }

        /* ── EXPANDER ── */
        [data-testid="stExpander"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-md) !important;
        }

        [data-testid="stExpander"] summary {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
        }

        /* ── MISC TEXT ── */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
        }

        p, span, div, label {
            color: var(--text-secondary);
        }

        a {
            color: var(--accent-light) !important;
        }

        /* ── DIVIDER ── */
        hr {
            border-color: var(--border) !important;
        }

        /* ── ANIMATIONS ── */
        @keyframes fade-in-up {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .section-card, .summary-hero, .brand-shell, .mini-card, .history-card {
            animation: fade-in-up 0.5s ease both;
        }

        .mini-card:nth-child(2) { animation-delay: 0.05s; }
        .mini-card:nth-child(3) { animation-delay: 0.1s; }
        .mini-card:nth-child(4) { animation-delay: 0.15s; }

        /* ── SLIDER COLORS ── */
        .stSlider > div > div > div {
            color: var(--text-secondary) !important;
        }

        /* Number input stepper */
        .stNumberInput button {
            color: var(--text-secondary) !important;
            background: var(--bg-elevated) !important;
            border-color: var(--border) !important;
        }

        .stNumberInput button:hover {
            color: var(--accent-light) !important;
            border-color: var(--accent) !important;
        }

        /* Form borders */
        [data-testid="stForm"] {
            border-color: var(--border) !important;
            border-radius: var(--radius-md) !important;
            padding: 1rem !important;
            background: var(--bg-elevated) !important;
        }

        /* JSON viewer */
        .stJson {
            background: var(--bg-input) !important;
            border-radius: var(--radius-sm) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


if "mpd_items" not in st.session_state:
    st.session_state.mpd_items = []
if "empaque_items" not in st.session_state:
    st.session_state.empaque_items = []
if "cif_items" not in st.session_state:
    st.session_state.cif_items = []
if "mostrar_resultados" not in st.session_state:
    st.session_state.mostrar_resultados = True
if "producto_nombre" not in st.session_state:
    st.session_state.producto_nombre = "Producto Agroindustrial"
if "producto_categoria" not in st.session_state:
    st.session_state.producto_categoria = "Deshidratado"
if "desperdicio_esperado" not in st.session_state:
    st.session_state.desperdicio_esperado = 5.0


with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-card">
            <p class="sidebar-title">⚙️ Pricing Studio</p>
            <p class="sidebar-copy">Ajusta el lote, los márgenes y las simulaciones para visualizar escenarios comerciales en tiempo real.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    lote_produccion = st.number_input(
        "Tamaño del lote (unidades finales)", min_value=1, value=1000, step=1
    )
    costo_mpd_simulado_bs = st.slider(
        "Simulación de MPD base (Bs.)",
        min_value=0.0,
        max_value=50000.0,
        value=0.0,
        step=100.0,
        help="Si es mayor a cero, reemplaza el costo calculado de materias primas para un escenario rápido.",
    )

    st.markdown(
        """
        <div class="sidebar-card">
            <p class="sidebar-title">📊 Márgenes y carga fiscal</p>
            <p class="sidebar-copy">La fórmula aplicada mantiene el enfoque de margen sobre precio solicitado en el proyecto.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    margen_fika_pct = st.slider("Margen Fika (%)", 0.0, 99.0, 30.0, 1.0) / 100.0
    margen_pdv_pct = st.slider("Margen PDV (%)", 0.0, 99.0, 20.0, 1.0) / 100.0
    impuestos_pct = st.slider("Impuestos (%)", 0.0, 99.0, 16.0, 1.0) / 100.0

    st.markdown(
        f"""
        <div class="sidebar-card">
            <p class="sidebar-title">📌 Lectura del escenario</p>
            <p class="sidebar-copy">Fika: <strong style="color: var(--accent-light)">{margen_fika_pct*100:.0f}%</strong> · PDV: <strong style="color: var(--accent-light)">{margen_pdv_pct*100:.0f}%</strong> · Impuestos: <strong style="color: var(--accent-light)">{impuestos_pct*100:.0f}%</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="brand-shell">
        <div class="brand-bar">
            <div>
                <div class="brand-kicker">Atelier Financial Interface</div>
                <h1 class="brand-title">Costeador <span>Atelier</span></h1>
                <p class="brand-copy">Herramienta premium para la construcción, análisis y cotización de productos agroindustriales. Diseño editorial con foco en claridad y eficiencia operativa.</p>
            </div>
            <div class="nav-pill-row">
                <span class="nav-pill">Overview</span>
                <span class="nav-pill">Inventory</span>
                <span class="nav-pill active">Builder</span>
                <span class="nav-pill">Pricing</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.session_state.producto_nombre = st.session_state.get("producto_nombre", "Producto Agroindustrial")


def render_card_start(title: str, description: str):
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">
                <div>
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )


def render_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def compute_totals():
    total_mpd_calculado = 0.0
    for item in st.session_state.mpd_items:
        try:
            calc = FinancialCalculator.calculate_mpd_cost(
                float(item["cantidad_inicial_kg"]),
                float(item["costo_unitario_bs"]),
                float(item["porcentaje_merma"]),
            )
            item["cantidad_final_kg"] = calc["cantidad_final_kg"]
            item["costo_total_bs"] = calc["costo_total_bs"]
            total_mpd_calculado += calc["costo_total_bs"]
        except Exception:
            item["cantidad_final_kg"] = 0.0
            item["costo_total_bs"] = 0.0

    total_mpd = costo_mpd_simulado_bs if costo_mpd_simulado_bs > 0 else total_mpd_calculado
    total_empaque = sum(float(i.get("costo_total_bs", 0.0)) for i in st.session_state.empaque_items)
    total_cif = sum(float(i.get("costo_total_bs", 0.0)) for i in st.session_state.cif_items)
    return total_mpd_calculado, total_mpd, total_empaque, total_cif


def safe_currency(value: float) -> str:
    return f"Bs. {value:,.2f}"


def add_mpd_item(nombre, cantidad, costo_unit, merma):
    if not nombre:
        st.warning("Debes asignar un nombre a la materia prima.")
        return
    calc = FinancialCalculator.calculate_mpd_cost(cantidad, costo_unit, merma / 100.0)
    st.session_state.mpd_items.append(
        {
            "nombre": nombre,
            "cantidad_inicial_kg": cantidad,
            "costo_unitario_bs": costo_unit,
            "porcentaje_merma": merma / 100.0,
            "cantidad_final_kg": calc["cantidad_final_kg"],
            "costo_total_bs": calc["costo_total_bs"],
        }
    )


def add_empaque_item(nombre, cantidad, costo_unit):
    if not nombre:
        st.warning("Debes asignar un nombre al ítem de empaque.")
        return
    st.session_state.empaque_items.append(
        {
            "item": nombre,
            "cantidad": cantidad,
            "costo_unitario_bs": costo_unit,
            "costo_total_bs": cantidad * costo_unit,
        }
    )


def add_cif_item(nombre, costo):
    if not nombre:
        st.warning("Debes asignar un nombre al concepto CIF.")
        return
    st.session_state.cif_items.append(
        {"concepto": nombre, "costo_total_bs": costo}
    )


builder_tab, pricing_tab, history_tab = st.tabs(
    ["🔧 Recipe Builder", "💰 Pricing Studio", "📁 Costeos guardados"]
)


with builder_tab:
    left_col, right_col = st.columns([1.65, 1.0], gap="large")

    with left_col:
        render_card_start(
            "Product Details",
            "Configura el producto base antes de cargar ingredientes, empaques y costos operativos.",
        )
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.producto_nombre = st.text_input(
                "Nombre del producto",
                value=st.session_state.producto_nombre,
                placeholder="Ej. Mango deshidratado premium",
            )
            lote_produccion = st.number_input(
                "Batch Yield / Lote final",
                min_value=1,
                value=int(lote_produccion),
                step=1,
                key="lote_builder",
            )
        with c2:
            st.session_state.producto_categoria = st.selectbox(
                "Categoría",
                ["Deshidratado", "Molienda", "Bebida", "Otro"],
                index=["Deshidratado", "Molienda", "Bebida", "Otro"].index(st.session_state.producto_categoria)
                if st.session_state.producto_categoria in ["Deshidratado", "Molienda", "Bebida", "Otro"]
                else 0,
            )
            st.session_state.desperdicio_esperado = st.number_input(
                "Merma esperada global (%)",
                min_value=0.0,
                max_value=99.0,
                value=float(st.session_state.desperdicio_esperado),
                step=1.0,
            )
        render_card_end()

        render_card_start(
            "Ingredients List",
            "Carga materia prima directa con cantidad inicial, costo unitario y merma específica.",
        )
        with st.form("form_mpd", clear_on_submit=True):
            a1, a2, a3, a4 = st.columns([2.4, 1.2, 1.2, 1.0])
            mpd_nombre = a1.text_input("Ingrediente", placeholder="Ej. Mango fresco")
            mpd_cantidad = a2.number_input("Cant. inicial (Kg)", min_value=0.0, value=100.0, step=1.0)
            mpd_costo_unit = a3.number_input("Costo unit. (Bs/Kg)", min_value=0.0, value=5.0, step=0.5)
            mpd_merma = a4.number_input("Merma (%)", min_value=0.0, max_value=99.0, value=15.0, step=1.0)
            submitted_mpd = st.form_submit_button("✚ Agregar ingrediente", type="primary", use_container_width=True)
            if submitted_mpd:
                add_mpd_item(mpd_nombre, mpd_cantidad, mpd_costo_unit, mpd_merma)

        if st.session_state.mpd_items:
            df_mpd = pd.DataFrame(st.session_state.mpd_items)
            df_mpd_display = df_mpd.copy()
            df_mpd_display["porcentaje_merma"] = df_mpd_display["porcentaje_merma"] * 100
            st.dataframe(
                df_mpd_display.rename(
                    columns={
                        "nombre": "Ingrediente",
                        "cantidad_inicial_kg": "Cantidad inicial (Kg)",
                        "costo_unitario_bs": "Costo unitario (Bs/Kg)",
                        "porcentaje_merma": "Merma (%)",
                        "cantidad_final_kg": "Cantidad final (Kg)",
                        "costo_total_bs": "Costo total (Bs)",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            delete_idx = st.selectbox(
                "Eliminar ingrediente",
                options=list(range(len(st.session_state.mpd_items))),
                format_func=lambda x: st.session_state.mpd_items[x]["nombre"],
                key="delete_mpd_select",
            )
            if st.button("🗑 Eliminar ingrediente seleccionado", use_container_width=True):
                st.session_state.mpd_items.pop(delete_idx)
                st.rerun()
        else:
            st.info("Aún no hay ingredientes cargados.")
        render_card_end()

        render_card_start(
            "Packaging & Indirect Costs",
            "Agrupa empaque, mano de obra directa y costos indirectos dentro del mismo flujo de construcción.",
        )
        em1, em2, em3 = st.columns([2.2, 1.1, 1.1])
        emp_nombre = em1.text_input("Ítem de empaque", placeholder="Ej. Bolsa trilaminada")
        emp_cantidad = em2.number_input("Cantidad", min_value=0.0, value=1000.0, step=1.0)
        emp_costo_unit = em3.number_input("Costo unitario (Bs)", min_value=0.0, value=1.5, step=0.1)
        if st.button("✚ Agregar empaque", use_container_width=True):
            add_empaque_item(emp_nombre, emp_cantidad, emp_costo_unit)

        if st.session_state.empaque_items:
            st.dataframe(
                pd.DataFrame(st.session_state.empaque_items).rename(
                    columns={
                        "item": "Empaque",
                        "cantidad": "Cantidad",
                        "costo_unitario_bs": "Costo unitario (Bs)",
                        "costo_total_bs": "Costo total (Bs)",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        mo1, mo2 = st.columns(2)
        mod_horas = mo1.number_input("Horas totales del lote", min_value=0.0, value=40.0, step=1.0)
        mod_costo_hora = mo2.number_input("Costo por hora (Bs)", min_value=0.0, value=15.0, step=1.0)
        total_mod = mod_horas * mod_costo_hora

        ci1, ci2 = st.columns([2.2, 1.2])
        cif_nombre = ci1.text_input("Concepto CIF", placeholder="Ej. Energía eléctrica")
        cif_costo = ci2.number_input("Costo CIF total (Bs)", min_value=0.0, value=300.0, step=10.0)
        if st.button("✚ Agregar CIF", use_container_width=True):
            add_cif_item(cif_nombre, cif_costo)

        if st.session_state.cif_items:
            st.dataframe(
                pd.DataFrame(st.session_state.cif_items).rename(
                    columns={"concepto": "Concepto", "costo_total_bs": "Costo total (Bs)"}
                ),
                use_container_width=True,
                hide_index=True,
            )
        render_card_end()

    total_mpd_calculado, total_mpd, total_empaque, total_cif = compute_totals()

    try:
        resultados = FinancialCalculator.calculate_full_costing(
            total_mpd_bs=total_mpd,
            total_empaque_bs=total_empaque,
            total_mod_bs=total_mod,
            total_cif_bs=total_cif,
            lote_produccion_unidades=lote_produccion,
            margen_fika_porcentaje=margen_fika_pct,
            margen_pdv_porcentaje=margen_pdv_pct,
            impuestos_porcentaje=impuestos_pct,
        )
        calculo_exitoso = True
    except Exception as e:
        calculo_exitoso = False
        resultados = None
        st.error(f"Error en los cálculos: {e}")

    with right_col:
        if calculo_exitoso:
            ru = resultados["rentabilidad_unitaria"]
            cu = resultados["costos_unitarios"]
            st.markdown(
                f"""
                <div class="summary-hero">
                    <div class="summary-kicker">Atelier Summary</div>
                    <div class="summary-headline">{safe_currency(ru['precio_venta_publico_bs'])}</div>
                    <p class="summary-copy">Precio público final por unidad para <strong style="color: var(--accent-light)">{st.session_state.producto_nombre}</strong>. Cálculo en tiempo real basado en costos, márgenes y carga fiscal configurada.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<span class="gradient-chip">✦ Pricing recommendation activa</span>', unsafe_allow_html=True)
            st.write("")
            st.metric("Costo total de producción / unidad", safe_currency(cu["costo_produccion"]))
            st.metric(
                "Precio fábrica",
                safe_currency(ru["precio_venta_fabrica_bs"]),
                f"Margen Fika {margen_fika_pct*100:.0f}%",
                delta_color="off",
            )
            st.metric(
                "Precio público sin impuestos",
                safe_currency(ru["precio_venta_publico_sin_impuestos_bs"]),
                f"Margen PDV {margen_pdv_pct*100:.0f}%",
                delta_color="off",
            )

            st.markdown(
                f"""
                <div class="mini-card">
                    <div class="mini-label">Materia prima aplicada</div>
                    <div class="mini-value">{safe_currency(total_mpd)}</div>
                    <div class="mini-note">Costo calculado: {safe_currency(total_mpd_calculado)} {'· simulado' if costo_mpd_simulado_bs > 0 else '· cálculo real'}.</div>
                </div>
                <div class="mini-card">
                    <div class="mini-label">Costos operativos del lote</div>
                    <div class="mini-value">{safe_currency(total_mod + total_cif + total_empaque)}</div>
                    <div class="mini-note">Empaque, MOD y CIF consolidados en el constructor.</div>
                </div>
                <div class="mini-card">
                    <div class="mini-label">Lectura estratégica</div>
                    <div class="mini-note">Si el precio objetivo del mercado es sensible, puedes ajustar lote, merma o empaques desde el panel izquierdo y recalcular al instante.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.warning("No fue posible renderizar el resumen porque los parámetros actuales generan un error de cálculo.")


with pricing_tab:
    total_mpd_calculado, total_mpd, total_empaque, total_cif = compute_totals()
    total_mod = mod_horas * mod_costo_hora

    try:
        resultados = FinancialCalculator.calculate_full_costing(
            total_mpd_bs=total_mpd,
            total_empaque_bs=total_empaque,
            total_mod_bs=total_mod,
            total_cif_bs=total_cif,
            lote_produccion_unidades=lote_produccion,
            margen_fika_porcentaje=margen_fika_pct,
            margen_pdv_porcentaje=margen_pdv_pct,
            impuestos_porcentaje=impuestos_pct,
        )
        calculo_exitoso = True
    except Exception as e:
        calculo_exitoso = False
        resultados = None
        st.error(f"Error en los cálculos: {e}")

    if calculo_exitoso:
        ru = resultados["rentabilidad_unitaria"]
        cu = resultados["costos_unitarios"]
        breakdown = pd.DataFrame(
            {
                "Componente": [
                    "MPD",
                    "Empaque",
                    "MOD",
                    "CIF",
                    "Margen Fika",
                    "Margen PDV",
                    "Impuestos",
                ],
                "Monto (Bs.)": [
                    cu["mpd"],
                    cu["empaque"],
                    cu["mod"],
                    cu["cif"],
                    ru["monto_margen_fika_bs"],
                    ru["monto_margen_pdv_bs"],
                    ru["monto_impuestos_bs"],
                ],
            }
        )
        cost_only = pd.DataFrame(
            {
                "Componente": ["Ingredientes", "Empaque", "Labor", "Overhead"],
                "Monto": [cu["mpd"], cu["empaque"], cu["mod"], cu["cif"]],
            }
        )

        st.markdown(
            f"""
            <div class="section-card">
                <div class="section-title">
                    <div>
                        <h3>Cost Analysis & Pricing</h3>
                        <p>Desglose completo del costeo unitario, márgenes y precio final objetivo.</p>
                    </div>
                    <div class="gradient-chip">✦ {st.session_state.producto_nombre}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        met1, met2, met3, met4 = st.columns(4)
        met1.metric("Costo unitario", safe_currency(cu["costo_produccion"]))
        met2.metric("Precio fábrica", safe_currency(ru["precio_venta_fabrica_bs"]))
        met3.metric("Precio público", safe_currency(ru["precio_venta_publico_bs"]))
        met4.metric("Margen bruto visible", f"{((ru['precio_venta_publico_bs']-cu['costo_produccion'])/ru['precio_venta_publico_bs'])*100:.1f}%")

        c_chart1, c_chart2 = st.columns([1.05, 1.0], gap="large")
        with c_chart1:
            fig_donut = px.pie(
                cost_only,
                values="Monto",
                names="Componente",
                hole=0.68,
                color="Componente",
                color_discrete_map={
                    "Ingredientes": "#a855f7",
                    "Empaque": "#c084fc",
                    "Labor": "#6366f1",
                    "Overhead": "#38bdf8",
                },
            )
            fig_donut.update_layout(
                title=dict(text="Participación del costo unitario", font=dict(color="#f0f2f8", size=14)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend_title_text="",
                margin=dict(l=10, r=10, t=60, b=10),
                font=dict(color="#a0a8c0", family="Inter"),
                legend=dict(font=dict(color="#a0a8c0")),
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with c_chart2:
            fig_waterfall = go.Figure(
                go.Waterfall(
                    name="Precio",
                    orientation="v",
                    measure=["relative"] * 7 + ["total"],
                    x=breakdown["Componente"].tolist() + ["PVP Final"],
                    y=breakdown["Monto (Bs.)"].tolist() + [ru["precio_venta_publico_bs"]],
                    connector={"line": {"color": "rgba(160,168,192,0.3)"}},
                    increasing={"marker": {"color": "#a855f7"}},
                    decreasing={"marker": {"color": "#6366f1"}},
                    totals={"marker": {"color": "#38bdf8"}},
                )
            )
            fig_waterfall.update_layout(
                title=dict(text="Construcción del precio final", font=dict(color="#f0f2f8", size=14)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=60, b=10),
                font=dict(color="#a0a8c0", family="Inter"),
                showlegend=False,
                xaxis=dict(gridcolor="rgba(148,163,210,0.08)", color="#a0a8c0"),
                yaxis=dict(gridcolor="rgba(148,163,210,0.08)", color="#a0a8c0"),
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)

        left_save, right_save = st.columns([1.2, 1.0], gap="large")
        with left_save:
            render_card_start(
                "Scenario Analysis",
                "Guarda el escenario de pricing con nombre y conserva su estructura para revisiones futuras.",
            )
            nombre_costeo = st.text_input(
                "Nombre del escenario",
                placeholder="Ej. Mango deshidratado 100Kg",
            )
            if st.button("💾 Guardar en base de datos", type="primary", use_container_width=True):
                if not nombre_costeo:
                    st.warning("Debes asignar un nombre al costeo antes de guardar.")
                else:
                    doc_data = {
                        "nombre_costeo": nombre_costeo,
                        "categoria": st.session_state.producto_categoria,
                        "lote_produccion_kg": lote_produccion,
                        "mpd": st.session_state.mpd_items,
                        "empaque": st.session_state.empaque_items,
                        "mod": {
                            "horas_totales": mod_horas,
                            "costo_por_hora_bs": mod_costo_hora,
                            "costo_total_bs": total_mod,
                        },
                        "cif": st.session_state.cif_items,
                        "parametros_financieros": {
                            "margen_fika_porcentaje": margen_fika_pct,
                            "margen_pdv_porcentaje": margen_pdv_pct,
                            "impuestos_porcentaje": impuestos_pct,
                        },
                        "resultados": resultados,
                    }
                    doc_id = CosteosDB.save_costeo(doc_data)
                    st.success(f"✅ Costeo guardado exitosamente con ID: {doc_id}")
            render_card_end()

        with right_save:
            st.markdown(
                f"""
                <div class="section-card">
                    <div class="section-title">
                        <div>
                            <h3>Pricing Controls</h3>
                            <p>Lectura ejecutiva del escenario actual con foco comercial y financiero.</p>
                        </div>
                    </div>
                    <div class="mini-card">
                        <div class="mini-label">Target Margin Slider</div>
                        <div class="mini-value">{margen_fika_pct*100:.0f}% / {margen_pdv_pct*100:.0f}%</div>
                        <div class="mini-note">Margen Fika y PDV en el escenario activo.</div>
                    </div>
                    <div class="mini-card">
                        <div class="mini-label">Benchmark operativo</div>
                        <div class="mini-note">Lote: {lote_produccion:,.0f} unidades · Impuestos: {impuestos_pct*100:.0f}% · MOD total: {safe_currency(total_mod)}</div>
                    </div>
                    <div class="mini-card">
                        <div class="mini-label">PVP recomendado</div>
                        <div class="mini-value">{safe_currency(ru['precio_venta_publico_bs'])}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_card_start(
            "Desglose numérico",
            "Tabla analítica por componente para respaldo de decisiones comerciales.",
        )
        st.dataframe(breakdown, use_container_width=True, hide_index=True)
        render_card_end()


with history_tab:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">
                <div>
                    <h3>📁 Costeos Históricos Guardados</h3>
                    <p>Visualiza los escenarios persistidos y consulta su precio final, fecha y estructura general.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Refrescar lista", use_container_width=False):
        st.rerun()

    try:
        costeos_guardados = CosteosDB.get_all_costeos()
        if costeos_guardados:
            for idx, c in enumerate(costeos_guardados):
                nombre = c.get("nombre_costeo", f"Costeo {idx + 1}")
                fecha = c.get("fecha_actualizacion", "Sin fecha")
                try:
                    precio_final = c.get("resultados", {}).get("rentabilidad_unitaria", {}).get("precio_venta_publico_bs", 0.0)
                except Exception:
                    precio_final = 0.0

                st.markdown(
                    f"""
                    <div class="history-card">
                        <div class="mini-label">{fecha}</div>
                        <div class="mini-value">{nombre}</div>
                        <div class="mini-note">Precio público final estimado: {safe_currency(float(precio_final))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.expander(f"Ver detalle · {nombre}"):
                    st.json(c)
        else:
            st.info("No hay costeos guardados todavía.")
    except Exception as e:
        st.error(f"Error cargando costeos guardados: {str(e)}")
