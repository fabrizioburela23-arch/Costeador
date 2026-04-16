import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from formulas import FinancialCalculator
from db import CosteosDB


st.set_page_config(
    page_title="Costeador Atelier",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        :root {
            --bg: #fff8f8;
            --surface: #ffffff;
            --surface-soft: #fff0f2;
            --surface-mid: #ffe8ed;
            --surface-strong: #f9dbe2;
            --text: #27171c;
            --muted: #5a3f47;
            --primary: #b90064;
            --primary-2: #e6007e;
            --secondary: #83449a;
            --tertiary: #006688;
            --outline: #e2bdc7;
            --danger: #ba1a1a;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(230, 0, 126, 0.08), transparent 28%),
                radial-gradient(circle at top left, rgba(131, 68, 154, 0.06), transparent 24%),
                var(--bg);
            color: var(--text);
            font-family: "Inter", "Segoe UI", sans-serif;
        }

        [data-testid="stHeader"] {
            background: rgba(255, 248, 248, 0.75);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #fff7f8 0%, #fff0f2 100%);
            border-right: 1px solid rgba(226, 189, 199, 0.5);
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        .brand-shell {
            background: rgba(255, 248, 248, 0.82);
            backdrop-filter: blur(18px);
            border: 1px solid rgba(226, 189, 199, 0.35);
            border-radius: 24px;
            padding: 1rem 1.25rem;
            box-shadow: 0 20px 40px rgba(39, 23, 28, 0.05);
            margin-bottom: 1.25rem;
        }

        .brand-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .brand-kicker {
            color: var(--secondary);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 800;
            font-size: 0.76rem;
            margin-bottom: 0.35rem;
        }

        .brand-title {
            font-size: 2.3rem;
            line-height: 1;
            font-weight: 900;
            letter-spacing: -0.04em;
            color: var(--text);
            margin: 0;
        }

        .brand-title span {
            background: linear-gradient(135deg, var(--primary), var(--primary-2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-copy {
            color: var(--muted);
            max-width: 760px;
            font-size: 1rem;
            margin-top: 0.5rem;
        }

        .nav-pill-row {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            justify-content: flex-end;
        }

        .nav-pill {
            background: #fff;
            border: 1px solid rgba(226, 189, 199, 0.75);
            color: var(--muted);
            border-radius: 999px;
            padding: 0.55rem 0.95rem;
            font-size: 0.88rem;
            font-weight: 700;
        }

        .nav-pill.active {
            color: white;
            border-color: transparent;
            background: linear-gradient(135deg, var(--primary), var(--primary-2));
            box-shadow: 0 10px 24px rgba(185, 0, 100, 0.18);
        }

        .section-card {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(226, 189, 199, 0.45);
            border-radius: 24px;
            padding: 1.2rem 1.2rem 1rem 1.2rem;
            box-shadow: 0 20px 40px rgba(39, 23, 28, 0.04);
            margin-bottom: 1rem;
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
            font-weight: 850;
            letter-spacing: -0.02em;
            color: var(--text);
        }

        .section-title p {
            margin: 0.25rem 0 0 0;
            color: var(--muted);
            font-size: 0.9rem;
        }

        .summary-hero {
            background: linear-gradient(145deg, rgba(255,255,255,0.92), rgba(255,240,242,0.92));
            border: 1px solid rgba(226, 189, 199, 0.5);
            border-radius: 28px;
            padding: 1.5rem;
            box-shadow: 0 22px 50px rgba(39, 23, 28, 0.06);
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }

        .summary-hero:after {
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(185,0,100,0.14) 0%, rgba(185,0,100,0) 70%);
            top: -80px;
            right: -40px;
        }

        .summary-kicker {
            position: relative;
            z-index: 1;
            color: var(--secondary);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.74rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }

        .summary-headline {
            position: relative;
            z-index: 1;
            color: var(--text);
            font-size: 2.5rem;
            letter-spacing: -0.05em;
            line-height: 1;
            font-weight: 900;
            margin: 0.2rem 0 0.5rem 0;
        }

        .summary-copy {
            position: relative;
            z-index: 1;
            color: var(--muted);
            margin: 0;
            max-width: 520px;
        }

        .mini-card {
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(226, 189, 199, 0.5);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin-bottom: 0.8rem;
        }

        .mini-label {
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.72rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }

        .mini-value {
            color: var(--text);
            font-size: 1.35rem;
            font-weight: 850;
            letter-spacing: -0.03em;
        }

        .mini-note {
            color: var(--muted);
            font-size: 0.86rem;
            margin-top: 0.25rem;
        }

        .gradient-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.35rem 0.65rem;
            border-radius: 999px;
            color: white;
            font-size: 0.78rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--primary-2));
            box-shadow: 0 8px 20px rgba(185, 0, 100, 0.18);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            background: rgba(255,255,255,0.7);
            border: 1px solid rgba(226, 189, 199, 0.6);
            color: var(--muted);
            font-weight: 800;
            padding: 0.45rem 0.9rem;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--primary), var(--primary-2)) !important;
            color: white !important;
            border-color: transparent !important;
        }

        div.stButton > button {
            border-radius: 14px;
            border: 1px solid rgba(226, 189, 199, 0.75);
            background: rgba(255,255,255,0.88);
            color: var(--text);
            font-weight: 800;
            padding-top: 0.55rem;
            padding-bottom: 0.55rem;
        }

        div.stButton > button[kind="primary"] {
            border: 0;
            color: white;
            background: linear-gradient(135deg, var(--primary), var(--primary-2));
            box-shadow: 0 12px 30px rgba(185, 0, 100, 0.2);
        }

        div.stButton > button:hover {
            border-color: rgba(185, 0, 100, 0.55);
            color: var(--primary);
        }

        div.stButton > button[kind="primary"]:hover {
            color: white;
        }

        .stTextInput input, .stNumberInput input, .stSelectbox select, textarea {
            border-radius: 14px !important;
            border: 1px solid rgba(226, 189, 199, 0.8) !important;
            background: rgba(255, 255, 255, 0.9) !important;
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(226, 189, 199, 0.55);
            border-radius: 18px;
            padding: 0.85rem 1rem;
            box-shadow: 0 12px 24px rgba(39, 23, 28, 0.04);
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted);
            font-weight: 700;
        }

        [data-testid="stMetricValue"] {
            color: var(--text);
            font-weight: 900;
            letter-spacing: -0.03em;
        }

        .history-card {
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(226, 189, 199, 0.55);
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }

        .sidebar-card {
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(226, 189, 199, 0.55);
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 12px 24px rgba(39, 23, 28, 0.04);
        }

        .sidebar-title {
            margin: 0 0 0.25rem 0;
            font-size: 0.95rem;
            font-weight: 850;
            color: var(--text);
        }

        .sidebar-copy {
            margin: 0;
            font-size: 0.84rem;
            color: var(--muted);
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
            <p class="sidebar-title">Pricing Studio</p>
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
            <p class="sidebar-title">Márgenes y carga fiscal</p>
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
            <p class="sidebar-title">Lectura del escenario</p>
            <p class="sidebar-copy">Fika: <strong>{margen_fika_pct*100:.0f}%</strong> · PDV: <strong>{margen_pdv_pct*100:.0f}%</strong> · Impuestos: <strong>{impuestos_pct*100:.0f}%</strong></p>
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
                <p class="brand-copy">Rediseño visual inspirado en Stitch para una experiencia más editorial, clara y premium en la construcción, análisis y cotización de productos agroindustriales.</p>
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
    ["Recipe Builder", "Pricing Studio", "Costeos guardados"]
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
            submitted_mpd = st.form_submit_button("Agregar ingrediente", type="primary", use_container_width=True)
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
            if st.button("Eliminar ingrediente seleccionado", use_container_width=True):
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
        if st.button("Agregar empaque", use_container_width=True):
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
        if st.button("Agregar CIF", use_container_width=True):
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
                    <p class="summary-copy">Precio público final por unidad para <strong>{st.session_state.producto_nombre}</strong>. La interfaz replica la lógica visual premium del diseño Stitch con foco en lectura comercial.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<span class="gradient-chip">Pricing recommendation activa</span>', unsafe_allow_html=True)
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
                        <p>Vista inspirada en el layout de Pricing de Stitch, enfocada en desglose, estrategia y precio objetivo.</p>
                    </div>
                    <div class="gradient-chip">{st.session_state.producto_nombre}</div>
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
                    "Ingredientes": "#b90064",
                    "Empaque": "#e6007e",
                    "Labor": "#83449a",
                    "Overhead": "#006688",
                },
            )
            fig_donut.update_layout(
                title="Participación del costo unitario",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend_title_text="",
                margin=dict(l=10, r=10, t=60, b=10),
                font=dict(color="#27171c"),
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
                    connector={"line": {"color": "rgba(39,23,28,0.3)"}},
                    increasing={"marker": {"color": "#b90064"}},
                    decreasing={"marker": {"color": "#83449a"}},
                    totals={"marker": {"color": "#006688"}},
                )
            )
            fig_waterfall.update_layout(
                title="Construcción del precio final",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=60, b=10),
                font=dict(color="#27171c"),
                showlegend=False,
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
            if st.button("Guardar en base de datos", type="primary", use_container_width=True):
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
                    st.success(f"Costeo guardado exitosamente con ID: {doc_id}")
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
                    <h3>Costeos Históricos Guardados</h3>
                    <p>Visualiza los escenarios persistidos y consulta su precio final, fecha y estructura general.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Refrescar lista", use_container_width=False):
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
