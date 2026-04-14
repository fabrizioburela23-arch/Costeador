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
st.set_page_config(page_title="Costeador Profesional Fika", layout="wide")

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
        with open(ARCHIVO_BD, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def update_bd(updater_func):
    if not os.path.exists(ARCHIVO_BD):
        with open(ARCHIVO_BD, "w") as f:
            json.dump({}, f)
    
    with open(ARCHIVO_BD, "a+") as f:
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

# --- INTERFAZ PRINCIPAL ---
def main():
    st.title("📊 Costeador Profesional B2B - Fika Group")
    st.markdown("Calculadora estratégica basada en **margen sobre precio** y listas dinámicas.")

    tabs = st.tabs(["📝 Nuevo Costeo", "🗂️ Historial"])

    # --- PESTAÑA 1: NUEVO COSTEO ---
    with tabs[0]:
        col1, col2 = st.columns([1.2, 2])

        with col1:
            st.header("1. Materia Prima")
            for i, item in enumerate(st.session_state.materia_prima):
                c1, c2, c3, c4 = st.columns(4)
                item['nombre'] = c1.text_input("Nombre", item['nombre'], key=f"mp_nom_{i}")
                item['cantidad'] = c2.number_input("Cantidad", min_value=0.0, value=float(item['cantidad']), key=f"mp_cant_{i}", step=1.0)
                item['rendimiento'] = c3.number_input("Rend (%)", min_value=0.1, value=float(item['rendimiento']), key=f"mp_rend_{i}", step=1.0)
                item['costo'] = c4.number_input("Costo (Bs)", min_value=0.0, value=float(item['costo']), key=f"mp_costo_{i}", step=1.0)

            st.button("[ + Añadir Ítem ] Materia Prima", on_click=add_materia_prima)

            st.header("2. Costos de Empaque")
            st.caption("Envases, etiquetas, cajas, etc.")
            for i, item in enumerate(st.session_state.empaque):
                c1, c2, c3 = st.columns(3)
                item['nombre'] = c1.text_input("Nombre Empaque", item['nombre'], key=f"emp_nom_{i}")
                item['cantidad'] = c2.number_input("Cantidad", min_value=0.0, value=float(item['cantidad']), key=f"emp_cant_{i}", step=1.0)
                item['costo'] = c3.number_input("Costo (Bs)", min_value=0.0, value=float(item['costo']), key=f"emp_costo_{i}", step=1.0)

            st.button("[ + Añadir Ítem ] Empaque", on_click=add_empaque)

            st.header("3. Costos Operativos/Fijos")
            c1, c2 = st.columns(2)
            st.session_state.costos_operativos['mano_obra'] = c1.number_input("Mano de Obra (Bs)", min_value=0.0, value=float(st.session_state.costos_operativos['mano_obra']), step=1.0)
            st.session_state.costos_operativos['prorrateo'] = c2.number_input("Prorrateo Fábrica (Bs)", min_value=0.0, value=float(st.session_state.costos_operativos['prorrateo']), step=1.0)

            st.header("4. Márgenes e Impuestos")
            margen_fika_pct = st.slider("Margen Fika (%)", 0, 99, 35)
            margen_pdv_pct = st.slider("Margen PDV (%)", 0, 99, 20)
            impuestos_pct = st.slider("Impuestos (%)", 0, 99, 13)

            if st.button("[ Calcular Precio Final ]", type="primary", use_container_width=True):
                st.session_state.mostrar_resultados = True

        with col2:
            st.header("Proyección de Precios")

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
                st.error("Los márgenes o impuestos no pueden ser 100% o mayores.")
            elif st.session_state.get('mostrar_resultados', False):
                res = st.session_state.resultados

                m1, m2 = st.columns(2)
                m1.metric("PRECIO SALIDA FIKA (Bs)", f"{res['precio_fika']:.2f}", f"Utilidad Fika: {res['utilidad_fika']:.2f} Bs")
                m2.metric("PRECIO FINAL CLIENTE (Bs)", f"{res['precio_final']:.2f}", f"Impuestos: {res['monto_impuestos']:.2f} Bs", delta_color="off")

                st.subheader("Desglose de la Cadena")
                chart_data = [
                    {"Concepto": "Costo de Producción", "Monto (Bs)": res['costo_total']},
                    {"Concepto": "Margen Fika", "Monto (Bs)": res['utilidad_fika']},
                    {"Concepto": "Margen PDV", "Monto (Bs)": res['utilidad_pdv']},
                    {"Concepto": "Impuestos", "Monto (Bs)": res['monto_impuestos']}
                ]
                st.bar_chart(pd.DataFrame(chart_data).set_index("Concepto"))

                st.markdown("---")
                st.subheader("Acciones")

                nombre_coti = st.text_input("Nombre del Producto / Escenario")

                col_btn_guardar, col_btn_pdf = st.columns(2)

                with col_btn_guardar:
                    if st.button("[ Guardar Costeo ]", type="primary", use_container_width=True):
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
                            st.success("¡Costeo guardado con éxito!")
                        else:
                            st.error("Ponle un nombre para guardar el costeo.")

                with col_btn_pdf:
                    if nombre_coti:
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Helvetica", size=16, style="B")
                        pdf.cell(0, 10, "Cotizacion Comercial - Fika Group", new_x="LMARGIN", new_y="NEXT", align="C")
                        pdf.ln(10)
                        pdf.set_font("Helvetica", size=12)
                        pdf.cell(0, 10, f"Producto: {nombre_coti}", new_x="LMARGIN", new_y="NEXT")
                        pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d')}", new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(5)
                        pdf.cell(0, 10, f"Costo Total Produccion: {res['costo_total']:.2f} Bs.", new_x="LMARGIN", new_y="NEXT")
                        pdf.cell(0, 10, f"Precio Salida Fika: {res['precio_fika']:.2f} Bs.", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("Helvetica", size=14, style="B")
                        pdf.cell(0, 10, f"Precio Final al Cliente: {res['precio_final']:.2f} Bs.", new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(20)
                        pdf.set_font("Helvetica", size=12)
                        pdf.cell(0, 10, "Aprobado por el cliente: _______________________", new_x="LMARGIN", new_y="NEXT")

                        pdf_bytes = pdf.output()
                        st.download_button(
                            label="[ 📄 Descargar PDF ]",
                            data=pdf_bytes,
                            file_name=f"Cotizacion_{nombre_coti.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.button("[ 📄 Descargar PDF ]", disabled=True, use_container_width=True, help="Ingresa un nombre y calcula primero.")

    # --- PESTAÑA 2: HISTORIAL ---
    with tabs[1]:
        st.header("🗂️ Historial Guardado")
        bd = st.session_state.db_cotizaciones
        
        if not bd:
            st.info("Aún no tienes cotizaciones guardadas.")
        else:
            coti_seleccionada = st.selectbox("Selecciona un costeo para revisar:", list(bd.keys()))
            if coti_seleccionada:
                datos = bd[coti_seleccionada]
                st.caption(f"📅 Fecha: {datos['fecha']}")

                hc1, hc2 = st.columns(2)
                with hc1:
                    st.markdown("### Resumen Financiero")
                    st.metric("Costo Total", f"{datos['resultados']['costo_total']:.2f} Bs")
                    st.metric("Precio Salida Fika", f"{datos['resultados']['precio_fika']:.2f} Bs")
                    st.metric("Precio Final Cliente", f"{datos['resultados']['precio_final']:.2f} Bs")

                with hc2:
                    st.markdown("### Parámetros Globales Usados")
                    try:
                        margen_fika_v = f"{datos['parametros']['margen_fika']}%"
                        margen_pdv_v = f"{datos['parametros']['margen_pdv']}%"
                        impuestos_v = f"{datos['parametros']['impuestos']}%"
                    except KeyError:
                        margen_fika_v = "N/A"
                        margen_pdv_v = "N/A"
                        impuestos_v = "N/A"

                    df_params = pd.DataFrame({
                        "Variable": ["Margen Fika", "Margen PDV", "Impuestos"],
                        "Valor": [margen_fika_v, margen_pdv_v, impuestos_v
