import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from fpdf import FPDF

try:
    import fcntl
except ImportError:
    fcntl = None

try:
    import msvcrt
except ImportError:
    msvcrt = None

# --- CONFIGURACIÓN DE LA PÁGINA (DEBE SER LA PRIMERA LÍNEA) ---
st.set_page_config(page_title="Costeador Profesional Fika", page_icon="⚙️", layout="wide")

# --- INYECCIÓN CSS AVANZADA (PREMIUM SAAS UI) ---
st.markdown("""
<style>
/* Main Background */
.stApp {
    background-color: #F8FAFC;
}

/* Hide default top header */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Styling for Card Containers */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border-radius: 16px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    padding: 1.5rem !important;
    transition: all 0.3s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* Typography Enhancements */
h1, h2, h3 {
    color: #0F172A;
    font-family: 'Inter', sans-serif;
    font-weight: 700;
}

/* Metrics Styling (Big bold numbers) */
[data-testid="stMetricValue"] {
    font-size: 2.8rem !important;
    font-weight: 800 !important;
    color: #1E293B !important;
}
[data-testid="stMetricLabel"] {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #64748B !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetricDelta"] {
    font-size: 1rem !important;
    font-weight: 600 !important;
}

/* Base Buttons */
div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease-in-out;
    border: 1px solid #CBD5E1;
    color: #334155;
    background: #FFFFFF;
}
div.stButton > button:hover {
    border-color: #94A3B8;
    background: #F1F5F9;
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

/* Primary Buttons (Calcular, Guardar, Descargar) */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%);
    color: white;
    border: none;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4338ca 0%, #1d4ed8 100%);
    transform: translateY(-2px) scale(1.01);
    box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
}

/* Inputs & text area styling */
.stTextInput input, .stNumberInput input {
    border-radius: 8px;
    border: 1px solid #CBD5E1;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #3B82F6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}
</style>
""", unsafe_allow_html=True)

ARCHIVO_BD = "cotizaciones_fika.json"

# --- FUNCIONES DE BASE DE DATOS (SEGURAS Y UNIFICADAS) ---
def _lock_file(f):
    if fcntl:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    elif msvcrt:
        try:
            current_pos = f.tell()
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            f.seek(current_pos)
        except (OSError, AttributeError):
            pass

def _unlock_file(f):
    if fcntl:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    elif msvcrt:
        try:
            current_pos = f.tell()
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            f.seek(current_pos)
        except (OSError, AttributeError):
            pass

def cargar_bd():
    if not os.path.exists(ARCHIVO_BD):
        return {}
    try:
        with open(ARCHIVO_BD, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def update_bd(updater_func):
    if not os.path.exists(ARCHIVO_BD):
        with open(ARCHIVO_BD, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(ARCHIVO_BD, "a+", encoding="utf-8") as f:
        _lock_file(f)
        try:
            f.seek(0)
            try:
                content = f.read()
                data = json.loads(content) if content else {}
            except json.JSONDecodeError:
                data = {}

            updated_data = updater_func(data)

            f.seek(0)
            f.truncate()
            json.dump(updated_data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
            return updated_data
        finally:
            _unlock_file(f)

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'db_cotizaciones' not in st.session_state:
    st.session_state.db_cotizaciones = cargar_bd()

if 'materia_prima' not in st.session_state:
    st.session_state.materia_prima = [{"id": 0, "nombre": "", "cantidad": 0.0, "rendimiento": 100.0, "costo": 0.0}]

if 'empaque' not in st.session_state:
    st.session_state.empaque = [
        {"id": 0, "nombre": "Envases", "cantidad": 0.0, "costo": 0.0},
        {"id": 1, "nombre": "Etiquetas", "cantidad": 0.0, "costo": 0.0},
        {"id": 2, "nombre": "Cajas", "cantidad": 0.0, "costo": 0.0}
    ]

if 'costos_operativos' not in st.session_state:
    st.session_state.costos_operativos = {"mano_obra": 0.0, "prorrateo": 0.0}

# --- CALLBACKS PARA LISTAS DINÁMICAS ---
def add_materia_prima():
    new_id = len(st.session_state.materia_prima)
    st.session_state.materia_prima.append({"id": new_id, "nombre": "", "cantidad": 0.0, "rendimiento": 100.0, "costo": 0.0})

def add_empaque():
    new_id = len(st.session_state.empaque)
    st.session_state.empaque.append({"id": new_id, "nombre": "", "cantidad": 0.0, "costo": 0.0})

def main():
    st.title("💼 Costeador Profesional Fika")
    st.markdown("<p style='color: #64748B; font-size: 1.1rem; margin-bottom: 2rem;'>Herramienta técnica de cotización B2B con cálculo dinámico sobre margen de precio.</p>", unsafe_allow_html=True)

    tabs = st.tabs(["📝 Generar Cotización", "🗂️ Historial Fika"])

    # --- PESTAÑA 1: NUEVO COSTEO ---
    with tabs[0]:
        col1, padding, col2 = st.columns([1.5, 0.1, 1.8])

        with col1:
            # TARJETA: MATERIA PRIMA
            with st.container(border=True):
                st.subheader("🌾 1. Materia Prima")
                st.caption("Detalla todos los ingredientes y su porcentaje de rendimiento.")
                
                for i, item in enumerate(st.session_state.materia_prima):
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
                    item['nombre'] = c1.text_input("Ingrediente", item['nombre'], key=f"mp_nom_{i}")
                    item['cantidad'] = c2.number_input("Cant.", min_value=0.0, value=float(item['cantidad']), key=f"mp_cant_{i}", step=1.0)
                    item['rendimiento'] = c3.number_input("Rend %", min_value=0.1, value=float(item['rendimiento']), key=f"mp_rend_{i}", step=1.0)
                    item['costo'] = c4.number_input("Costo (Bs)", min_value=0.0, value=float(item['costo']), key=f"mp_costo_{i}", step=1.0)

                st.button("➕ Añadir Ingrediente", on_click=add_materia_prima)

            # TARJETA: EMPAQUE
            with st.container(border=True):
                st.subheader("📦 2. Costos de Empaque")
                st.caption("Envases, etiquetas, cajas logísticas, flejes, etc.")
                
                for i, item in enumerate(st.session_state.empaque):
                    c1, c2, c3 = st.columns([2, 1, 1.2])
                    item['nombre'] = c1.text_input("Tipo de Empaque", item['nombre'], key=f"emp_nom_{i}")
                    item['cantidad'] = c2.number_input("Cant.", min_value=0.0, value=float(item['cantidad']), key=f"emp_cant_{i}", step=1.0)
                    item['costo'] = c3.number_input("Costo Unit. (Bs)", min_value=0.0, value=float(item['costo']), key=f"emp_costo_{i}", step=1.0)

                st.button("➕ Añadir Empaque", on_click=add_empaque)

            # TARJETA: COSTOS FIJOS
            with st.container(border=True):
                st.subheader("⚙️ 3. Operativos y Fijos")
                c1, c2 = st.columns(2)
                st.session_state.costos_operativos['mano_obra'] = c1.number_input("👷 Mano de Obra (Bs)", min_value=0.0, value=float(st.session_state.costos_operativos['mano_obra']), step=1.0)
                st.session_state.costos_operativos['prorrateo'] = c2.number_input("🏭 Prorrateo Fábrica (Bs)", min_value=0.0, value=float(st.session_state.costos_operativos['prorrateo']), step=1.0)

            # TARJETA: MÁRGENES
            with st.container(border=True):
                st.subheader("📈 4. Márgenes de Negocio")
                margen_fika_pct = st.slider("🎯 Margen Bruto Fika (%)", 0, 99, 35)
                margen_pdv_pct = st.slider("🏪 Margen Punto de Venta (%)", 0, 99, 20)
                impuestos_pct = st.slider("⚖️ Retenciones e Impuestos (%)", 0, 99, 13)

            if st.button("🚀 Calcular Panel Financiero", type="primary", use_container_width=True):
                st.session_state.mostrar_resultados = True

        with col2:
            # TARJETA DE RESULTADOS PRINCIPAL
            with st.container(border=True):
                st.subheader("📊 Análisis de Rentabilidad")

                # --- CÁLCULO REACTIVO (ESTRICTO: MARGEN SOBRE PRECIO) ---
                costo_mp = sum([(item['cantidad'] * item['costo']) / (item['rendimiento']/100) if item['rendimiento'] > 0 else 0 for item in st.session_state.materia_prima])
                costo_empaque = sum([item['cantidad'] * item['costo'] for item in st.session_state.empaque])
                costo_op = st.session_state.costos_operativos['mano_obra'] + st.session_state.costos_operativos['prorrateo']

                costo_total = costo_mp + costo_empaque + costo_op

                mf = margen_fika_pct / 100.0
                mpdv = margen_pdv_pct / 100.0
                mimp = impuestos_pct / 100.0

                precio_fika = costo_total / (1 - mf) if mf < 1.0 else 0
                precio_pdv = precio_fika / (1 - mpdv) if mpdv < 1.0 else 0
                precio_final = precio_pdv / (1 - mimp) if mimp < 1.0 else 0

                st.session_state.resultados = {
                    "costo_total": costo_total,
                    "precio_fika": precio_fika,
                    "precio_pdv": precio_pdv,
                    "precio_final": precio_final,
                    "utilidad_fika": precio_fika - costo_total,
                    "utilidad_pdv": precio_pdv - precio_fika,
                    "monto_impuestos": precio_final - precio_pdv
                }

                # --- MOSTRAR RESULTADOS ---
                if mf >= 1.0 or mpdv >= 1.0 or mimp >= 1.0:
                    st.error("❌ Alerta financiera: Los márgenes o impuestos no pueden sumar o ser del 100%.")
                elif st.session_state.get('mostrar_resultados', False):
                    res = st.session_state.resultados

                    # Metricas Destacadas
                    m1, m2 = st.columns(2)
                    m1.metric("🔵 SALIDA FIKA (Bs)", f"{res['precio_fika']:.2f}", f"Utilidad Neta: {res['utilidad_fika']:.2f} Bs")
                    m2.metric("🟢 FINAL CLIENTE (Bs)", f"{res['precio_final']:.2f}", f"Impuestos: {res['monto_impuestos']:.2f} Bs", delta_color="off")
                    
                    st.divider()

                    st.markdown("<p style='font-weight: 600; color: #475569;'>Composición de la Cascada de Valor</p>", unsafe_allow_html=True)
                    chart_data = [
                        {"Eslabón": "1. Costo Base de Producción", "Monto (Bs)": res['costo_total']},
                        {"Eslabón": "2. Margen Operativo Fika", "Monto (Bs)": res['utilidad_fika']},
                        {"Eslabón": "3. Margen Distribuidor/PDV", "Monto (Bs)": res['utilidad_pdv']},
                        {"Eslabón": "4. Carga Impositiva", "Monto (Bs)": res['monto_impuestos']}
                    ]
                    # Chart without the ugly borders
                    st.bar_chart(pd.DataFrame(chart_data).set_index("Eslabón"), use_container_width=True)

            # TARJETA DE ACCIONES (Guardar y Descargar)
            with st.container(border=True):
                st.subheader("💾 Exportación de Cotización")
                
                nombre_coti = st.text_input("Identificador / Producto Cotizado", placeholder="Ej: Salsa de Ajo Doypack 500g - Cliente X")

                col_btn_guardar, col_btn_pdf = st.columns(2)

                with col_btn_guardar:
                    if st.button("💾 Guardar en Base de Datos", type="primary", use_container_width=True):
                        if nombre_coti:
                            def save_coti(data):
                                data[nombre_coti] = {
                                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "resultados": res,
                                    "parametros": {
                                        "mp": st.session_state.materia_prima,
                                        "empaque": st.session_state.empaque,
                                        "op": st.session_state.costos_operativos,
                                        "margen_fika": margen_fika_pct,
                                        "margen_pdv": margen_pdv_pct,
                                        "impuestos": impuestos_pct
                                    }
                                }
                                return data

                            st.session_state.db_cotizaciones = update_bd(save_coti)
                            st.success("✅ ¡Registro respaldado exitosamente!")
                        else:
                            st.warning("⚠️ Debes asignar un identificador para guardar.")

                with col_btn_pdf:
                    if nombre_coti and st.session_state.get('mostrar_resultados', False):
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Helvetica", size=18, style="B")
                        pdf.cell(0, 10, "Factibilidad Técnica Comercial - Fika Group", new_x="LMARGIN", new_y="NEXT", align="C")
                        pdf.ln(10)
                        
                        pdf.set_font("Helvetica", size=12)
                        pdf.cell(0, 10, f"Producto de Referencia: {nombre_coti}", new_x="LMARGIN", new_y="NEXT")
                        pdf.cell(0, 10, f"Fecha de Emisión: {datetime.now().strftime('%Y-%m-%d')}", new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(5)
                        
                        pdf.set_font("Helvetica", size=12, style="B")
                        pdf.cell(0, 10, "-- ESTRUCTURA FINANCIERA --", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("Helvetica", size=12)
                        pdf.cell(0, 10, f"Costo Total Base Produccion: {res['costo_total']:.2f} Bs.", new_x="LMARGIN", new_y="NEXT")
                        pdf.cell(0, 10, f"Precio Salida Fika: {res['precio_fika']:.2f} Bs. (Margen {margen_fika_pct}%)", new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.ln(5)
                        pdf.set_font("Helvetica", size=14, style="B")
                        pdf.cell(0, 10, f"> PRECIO SUGERIDO CLIENTE FINAL: {res['precio_final']:.2f} Bs.", new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.ln(20)
                        pdf.set_font("Helvetica", size=10, style="I")
                        pdf.cell(0, 10, "Validación Administrativa: _______________________", new_x="LMARGIN", new_y="NEXT")

                        pdf_bytes = pdf.output()
                        st.download_button(
                            label="📄 Imprimir Informe PDF",
                            data=pdf_bytes,
                            file_name=f"Cotizacion_{nombre_coti.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                    else:
                        st.button("📄 Imprimir Informe PDF", disabled=True, use_container_width=True, help="Calcula e ingresa un nombre para generar.")

    # --- PESTAÑA 2: HISTORIAL ---
    with tabs[1]:
        st.subheader("🗂️ Registro de Inteligencia de Negocios")
        st.caption("Auditoría y consulta de esquemas de precios anteriores.")
        bd = st.session_state.db_cotizaciones

        if not bd:
            st.info("Aún no tienes esquemas comerciales registrados en el sistema.")
        else:
            with st.container(border=True):
                coti_seleccionada = st.selectbox("🔎 Seleccione un modelo almacenado:", list(bd.keys()))

                if coti_seleccionada:
                    datos = bd[coti_seleccionada]
                    st.caption(f"📅 Fecha de Generación: {datos['fecha']}")
                    st.divider()

                    hc1, hc2 = st.columns(2)
                    with hc1:
                        st.markdown("<p style='font-weight: 600; color: #475569;'>Retrato Financiero</p>", unsafe_allow_html=True)
                        st.metric("Costo Total Raíz", f"{datos['resultados']['costo_total']:.2f} Bs")
                        st.metric("Precio Salida de Fábrica", f"{datos['resultados']['precio_fika']:.2f} Bs")
                        st.metric("Precio Etiqueta Cliente", f"{datos['resultados']['precio_final']:.2f} Bs")

                    with hc2:
                        st.markdown("<p style='font-weight: 600; color: #475569;'>Huella de Parámetros</p>", unsafe_allow_html=True)
                        try:
                            margen_fika_v = f"{datos['parametros']['margen_fika']}%"
                            margen_pdv_v = f"{datos['parametros']['margen_pdv']}%"
                            impuestos_v = f"{datos['parametros']['impuestos']}%"
                        except KeyError:
                            margen_fika_v = "N/A"
                            margen_pdv_v = "N/A"
                            impuestos_v = "N/A"

                        df_params = pd.DataFrame({
                            "Parámetro Estratégico": ["Margen Fika", "Margen Punto Venta", "Carga Tributaria"],
                            "Valor Registrado": [margen_fika_v, margen_pdv_v, impuestos_v]
                        })
                        st.dataframe(df_params, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()
