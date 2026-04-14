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

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Costeador B2B | Fika Group", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# --- CSS MINIMALISTA Y ESTÉTICA DE MARCA FIKA ---
# Colores del logo: Magenta (#E10078), Morado (#8E24AA), Cyan (#00B0FF)
st.markdown("""
<style>
/* Ocultar barra superior por defecto de Streamlit */
header[data-testid="stHeader"] { display: none; }

/* Título estilo Logo Fika */
.fika-logo {
    font-size: 2.8rem;
    font-weight: 900;
    margin-bottom: -15px;
    letter-spacing: -1px;
}
.fika-sub {
    font-size: 1.1rem;
    font-weight: 300;
    opacity: 0.8;
    margin-top: 0;
    margin-bottom: 2rem;
}

/* Mejora de Métricas */
[data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 1rem !important;
    font-weight: 600 !important;
    opacity: 0.85;
}

/* Botones Primarios con los colores institucionales (Gradient) */
div.stButton > button[kind="primary"] {
    font-weight: bold;
    border-radius: 8px;
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
    background: linear-gradient(90deg, #E80373, #9C27B0, #00B0FF);
    color: white;
    border: none;
    transition: all 0.3s ease;
}
div.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 15px rgba(156, 39, 176, 0.4);
    transform: translateY(-2px);
}

/* DataFrames styling headers */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

/* Bordes redondeados sutiles en los inputs */
.stTextInput input, .stNumberInput input {
    border-radius: 6px;
}

/* Quitar padding innecesario de la parte superior */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

ARCHIVO_BD = "cotizaciones_fika.json"

# --- FUNCIONES DE BASE DE DATOS (INTACTAS) ---
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

def del_materia_prima(index):
    st.session_state.materia_prima.pop(index)

def del_empaque(index):
    st.session_state.empaque.pop(index)

def main():
    # --- CONFIGURACIÓN ESTRATÉGICA EN SIDEBAR (ESTILO SAAS) ---
    with st.sidebar:
        st.markdown("### ⚙️ Panel Comercial")
        st.caption("Configura los márgenes globales y costos operativos.")
        
        with st.container(border=True):
            st.markdown("<p style='font-size:0.9rem;font-weight:bold;'><span style='color: #E80373;'>●</span> Márgenes de Rentabilidad</p>", unsafe_allow_html=True)
            margen_fika_pct = st.slider("Margen Neto Fika (%)", 0, 99, 35, help="Ganancia bruta sobre precio para FIKA")
            margen_pdv_pct = st.slider("Margen Punto de Venta (%)", 0, 99, 20, help="Ganancia reservada para el Cliente/Distribuidor")
            impuestos_pct = st.slider("Impuestos IVA/IT (%)", 0, 99, 13, help="Carga tributaria obligatoria")
        
        with st.container(border=True):
            st.markdown("<p style='font-size:0.9rem;font-weight:bold;'><span style='color: #00B0FF;'>●</span> Costos Fijos Estructurales</p>", unsafe_allow_html=True)
            st.session_state.costos_operativos['mano_obra'] = st.number_input("👷 Mano de Obra (Bs)", min_value=0.0, value=float(st.session_state.costos_operativos['mano_obra']), step=1.0)
            st.session_state.costos_operativos['prorrateo'] = st.number_input("🏭 Prorrateo Fábrica (Bs)", min_value=0.0, value=float(st.session_state.costos_operativos['prorrateo']), step=1.0)

    # --- PANTALLA PRINCIPAL ---
    st.markdown("<div class='fika-logo'>FIKA<span style='font-weight:300;'>B2B</span></div>", unsafe_allow_html=True)
    st.markdown("<p class='fika-sub'>distribución simplificada</p>", unsafe_allow_html=True)

    tab_cotizador, tab_historial = st.tabs(["📝 Construir Receta y Dashboard Financiero", "🗂️ Base de Datos Histórica"])

    # --- PESTAÑA 1: COTIZADOR PRINCIPAL ---
    with tab_cotizador:
        col_datos, padding, col_resultados = st.columns([1.5, 0.05, 1.4])

        with col_datos:
            # 1. MATERIA PRIMA
            with st.container(border=True):
                st.markdown("<h3 style='margin-bottom:0;'>🌾 1. Materia Prima e Insumos</h3>", unsafe_allow_html=True)
                st.caption("Añade cada ingrediente, cuánta cantidad requiere y su costo exacto.")
                st.write("") # Spacing
                
                for i, item in enumerate(st.session_state.materia_prima):
                    c1, c2, c3, c4, c5 = st.columns([3.5, 1.4, 1.4, 1.6, 0.5])
                    
                    # Labels en la parte superior solo para la primera fila
                    visibility = "visible" if i == 0 else "collapsed"
                    
                    item['nombre'] = c1.text_input("Ingrediente / Descripción", item['nombre'], key=f"mp_nom_{i}", label_visibility=visibility, placeholder="Ej. Azúcar")
                    item['cantidad'] = c2.number_input("Cant.", min_value=0.0, value=float(item['cantidad']), key=f"mp_cant_{i}", step=1.0, label_visibility=visibility)
                    item['rendimiento'] = c3.number_input("Rend %", min_value=0.1, value=float(item['rendimiento']), key=f"mp_rend_{i}", step=1.0, label_visibility=visibility)
                    item['costo'] = c4.number_input("Costo (Bs)", min_value=0.0, value=float(item['costo']), key=f"mp_costo_{i}", step=1.0, label_visibility=visibility)
                    
                    # Alinear el botón de eliminar asegurando que coincida con los inputs
                    if i == 0:
                        c5.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if c5.button("✕", key=f"del_mp_{i}", use_container_width=True, help="Eliminar fila"):
                        del_materia_prima(i)
                        st.rerun()

                if st.button("➕ Añadir Nuevo Ingrediente"):
                     add_materia_prima()
                     st.rerun()

            # 2. EMPAQUES
            with st.container(border=True):
                st.markdown("<h3 style='margin-bottom:0;'>📦 2. Empaquetado y Materiales</h3>", unsafe_allow_html=True)
                st.caption("Sobres, cajas corporativas, botellas, pegatinas, etc.")
                st.write("")
                
                for i, item in enumerate(st.session_state.empaque):
                    c1, c2, c3, c5 = st.columns([4, 1.5, 2, 0.5])
                    visibility = "visible" if i == 0 else "collapsed"
                    
                    item['nombre'] = c1.text_input("Tipo de Empaque", item['nombre'], key=f"emp_nom_{i}", label_visibility=visibility, placeholder="Ej. Envase Vidrio")
                    item['cantidad'] = c2.number_input("Cant.", min_value=0.0, value=float(item['cantidad']), key=f"emp_cant_{i}", step=1.0, label_visibility=visibility)
                    item['costo'] = c3.number_input("Costo Unit. (Bs)", min_value=0.0, value=float(item['costo']), key=f"emp_costo_{i}", step=1.0, label_visibility=visibility)
                    
                    if i == 0:
                        c5.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if c5.button("✕", key=f"del_emp_{i}", use_container_width=True, help="Eliminar empaque"):
                        del_empaque(i)
                        st.rerun()

                if st.button("➕ Añadir Material"):
                    add_empaque()
                    st.rerun()

            if st.button("🚀 Procesar Dashboard Financiero", type="primary", use_container_width=True):
                st.session_state.mostrar_resultados = True

        with col_resultados:
            # DASHBOARD PROFESIONAL
            with st.container(border=True):
                st.markdown("### 📊 Dashboard de Rentabilidad Fika")

                # CÁLCULOS MATEMÁTICOS INQUEBRANTABLES
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

                if mf >= 1.0 or mpdv >= 1.0 or mimp >= 1.0:
                    st.error("⚠️ Alerta: Los márgenes o impuestos no pueden ser 100% o superar ese límite numérico.")
                elif st.session_state.get('mostrar_resultados', False):
                    res = st.session_state.resultados

                    # MÉTRICAS TIPO DASHBOARD (Respetando colores institucionales semánticos)
                    c_met1, c_met2 = st.columns(2)
                    c_met1.metric("🟣 Salida Fábrica (Fika)", f"Bs {res['precio_fika']:.2f}", f"+ Bs {res['utilidad_fika']:.2f} V. Bruto")
                    c_met2.metric("🔵 PvP Final Recomendado", f"Bs {res['precio_final']:.2f}", f"Impuestos: Bs {res['monto_impuestos']:.2f}", delta_color="off")
                    
                    st.divider()
                    
                    # TABLA RESUMEN PROFESIONAL
                    st.markdown("#### 📋 Estructura de Costos y Cascada de Valor")
                    
                    df_resumen = pd.DataFrame([
                        {"ID": 1, "Concepto": "Costo Producción Raíz", "Monto (Bs)": f"{res['costo_total']:.2f}", "Peso %": f"{(res['costo_total']/res['precio_final'])*100:.1f}%" if res['precio_final']>0 else "0%"},
                        {"ID": 2, "Concepto": "🏆 Utilidad Bruta Fika", "Monto (Bs)": f"{res['utilidad_fika']:.2f}", "Peso %": f"{(res['utilidad_fika']/res['precio_final'])*100:.1f}%"  if res['precio_final']>0 else "0%"},
                        {"ID": 3, "Concepto": "🤝 Margen Canal / PDV", "Monto (Bs)": f"{res['utilidad_pdv']:.2f}", "Peso %": f"{(res['utilidad_pdv']/res['precio_final'])*100:.1f}%"  if res['precio_final']>0 else "0%"},
                        {"ID": 4, "Concepto": "⚖️ Carga Impositiva", "Monto (Bs)": f"{res['monto_impuestos']:.2f}", "Peso %": f"{(res['monto_impuestos']/res['precio_final'])*100:.1f}%"  if res['precio_final']>0 else "0%"}
                    ])
                    # Mostrando tabla nativa, muy profesional y limpia
                    st.dataframe(df_resumen, use_container_width=True, hide_index=True)

            # ZONA DE EXPORTACIÓN Y BASE DE DATOS
            with st.container(border=True):
                st.markdown("#### 💾 Guardar y Emitir Cotización")
                
                nombre_coti = st.text_input("ID Comercial / Producto", placeholder="Ej: Salsa Picante 250g - Supermercado X", label_visibility="collapsed")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Respaldar BD", use_container_width=True):
                        if nombre_coti:
                            def save_coti(data):
                                data[nombre_coti] = {
                                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                            st.success("✅ Guardado.")
                        else:
                            st.warning("⚠️ Ingresa un identificador.")
                
                with col_btn2:
                    if nombre_coti and st.session_state.get('mostrar_resultados', False):
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Helvetica", size=18, style="B")
                        pdf.cell(0, 10, "Ficha Tecnica de Factibilidad Comercial - Fika B2B", new_x="LMARGIN", new_y="NEXT", align="C")
                        pdf.ln(10)
                        
                        pdf.set_font("Helvetica", size=12)
                        pdf.cell(0, 10, f"Producto: {nombre_coti}", new_x="LMARGIN", new_y="NEXT")
                        pdf.cell(0, 10, f"Fecha de Analisis: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(5)
                        
                        pdf.set_font("Helvetica", size=12, style="B")
                        pdf.cell(0, 10, "-- DESGLOSE FINANCIERO --", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("Helvetica", size=12)
                        pdf.cell(0, 10, f"Costo Raiz de Produccion: {res['costo_total']:.2f} Bs.", new_x="LMARGIN", new_y="NEXT")
                        pdf.cell(0, 10, f"Precio Salida Fika: {res['precio_fika']:.2f} Bs. (Margen {margen_fika_pct}%)", new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.ln(5)
                        pdf.set_font("Helvetica", size=14, style="B")
                        pdf.cell(0, 10, f">> PRECIO VENTA PUBLICO (PvP) SUGERIDO: {res['precio_final']:.2f} Bs.", new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.ln(15)
                        pdf.set_font("Helvetica", size=10, style="I")
                        pdf.cell(0, 10, "Aprobacion Ejecutiva: _______________________", new_x="LMARGIN", new_y="NEXT")

                        pdf_bytes = pdf.output()
                        st.download_button(
                            label="📄 Descargar PDF Oficial",
                            data=pdf_bytes,
                            file_name=f"Fika_{nombre_coti.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.button("📄 Descargar PDF Oficial", disabled=True, use_container_width=True)


    # --- PESTAÑA 2: HISTORIAL ---
    with tab_historial:
        st.subheader("🗄️ Auditoría de Costeos Almacenados")
        st.write("Consulta la rentabilidad histórica.")
        bd = st.session_state.db_cotizaciones

        if not bd:
            st.info("ℹ️ Banco de datos vacío. Construye y guarda una cotización primero.")
        else:
            with st.container(border=True):
                coti_seleccionada = st.selectbox("🔎 Filtrar cotización registrada:", ['Selecciona un proyecto...'] + list(bd.keys()))

                if coti_seleccionada and coti_seleccionada != 'Selecciona un proyecto...':
                    datos = bd[coti_seleccionada]
                    st.caption(f"Registro Temporal: {datos['fecha']}")
                    st.divider()

                    hc1, hc2 = st.columns(2)
                    with hc1:
                        st.markdown("**Finanzas Rápidas**")
                        st.metric("Costo Producción", f"{datos['resultados']['costo_total']:.2f} Bs")
                        st.metric("Precio Salida de Fábrica", f"{datos['resultados']['precio_fika']:.2f} Bs")
                        st.metric("Precio Final Etiqueta", f"{datos['resultados']['precio_final']:.2f} Bs")

                    with hc2:
                        st.markdown("**Matriz Estratégica Usada**")
                        try:
                            margen_fika_v = f"{datos['parametros']['margen_fika']}%"
                            margen_pdv_v = f"{datos['parametros']['margen_pdv']}%"
                            impuestos_v = f"{datos['parametros']['impuestos']}%"
                        except KeyError:
                            margen_fika_v = "No Info"
                            margen_pdv_v = "No Info"
                            impuestos_v = "No Info"

                        df_params = pd.DataFrame({
                            "Parámetro": ["Rentabilidad Fika", "Rentabilidad Retail (PDV)", "Deducción de Impuestos"],
                            "Valor Registrado": [margen_fika_v, margen_pdv_v, impuestos_v]
                        })
                        st.dataframe(df_params, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()
