import streamlit as st
import pandas as pd
import json
import os
try:
    import fcntl
except ImportError:
    fcntl = None
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Cotizador Comercial FikaGroup", layout="wide")
ARCHIVO_BD = "cotizaciones_fika.json"

# --- FUNCIONES DE BASE DE DATOS ---
def _lock_file(f):
    if fcntl:
        fcntl.flock(f, fcntl.LOCK_EX)
    else:
        try:
            import msvcrt
            # Lock the first byte of the file to ensure mutual exclusion
            # We seek to 0 before locking to ensure all processes lock the same byte
            current_pos = f.tell()
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            f.seek(current_pos)
        except (ImportError, AttributeError, OSError):
            pass

def _unlock_file(f):
    if fcntl:
        fcntl.flock(f, fcntl.LOCK_UN)
    else:
        try:
            import msvcrt
            current_pos = f.tell()
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            f.seek(current_pos)
        except (ImportError, AttributeError, OSError):
            pass

def cargar_bd():
    if not os.path.exists(ARCHIVO_BD):
        return {}
    # Use "a+" to ensure compatibility with msvcrt.locking on Windows,
    # as it requires write access even for shared-like locks.
    with open(ARCHIVO_BD, "a+") as f:
        try:
            # Always lock before seeking/reading to ensure consistency
            _lock_file(f)
            f.seek(0)
            return json.load(f)
        except (json.JSONDecodeError, EOFError):
            return {}
        finally:
            _unlock_file(f)

def guardar_bd(datos):
    """Note: Prefer using update_bd to avoid lost updates."""
    # Using 'a+' ensures the file is created if it doesn't exist and doesn't truncate on open
    with open(ARCHIVO_BD, "a+") as f:
        try:
            _lock_file(f)
            f.seek(0)
            f.truncate()
            json.dump(datos, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        finally:
            _unlock_file(f)

def update_bd(update_func):
    """
    Safely update the database using a Read-Modify-Write cycle.
    update_func: a function that takes the current dict and returns the updated dict.
    """
    with open(ARCHIVO_BD, "a+") as f:
        try:
            _lock_file(f)
            f.seek(0)
            try:
                content = f.read()
                if content:
                    datos = json.loads(content)
                else:
                    datos = {}
            except (json.JSONDecodeError, EOFError):
                datos = {}

            nuevos_datos = update_func(datos)

            f.seek(0)
            f.truncate()
            json.dump(nuevos_datos, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
            return nuevos_datos
        finally:
            _unlock_file(f)

# Initialize session state with the current data
if 'db_cotizaciones' not in st.session_state:
    st.session_state.db_cotizaciones = cargar_bd()

# --- ENCABEZADO ---
st.title("📊 Cotizador Comercial FikaGroup")
st.markdown("Calculadora estratégica B2B/B2C basada en **margen sobre precio**.")

tabs = st.tabs(["📝 Nueva Cotización", "🗂️ Historial Guardado"])

# --- PESTAÑA 1: NUEVA COTIZACIÓN ---
with tabs[0]:
    from datetime import datetime

ARCHIVO_BD = "cotizaciones_fika.json"

# --- FUNCIONES DE BASE DE DATOS ---
def cargar_bd():
    if os.path.exists(ARCHIVO_BD):
        with open(ARCHIVO_BD, "r") as f:
            return json.load(f)
    return {}

def guardar_bd(datos):
    with open(ARCHIVO_BD, "w") as f:
        json.dump(datos, f, indent=4)

def render_nueva_cotizacion():
    col1, col2 = st.columns([1.2, 2])

    with col1:
        st.header("1. Estructura de Costos (Bs)")
        mp = st.number_input("Costo Materia Prima", min_value=0.0, value=15.0, step=1.0)
        empaque = st.number_input("Costo de Empaque", min_value=0.0, value=4.0, step=0.5)
        mo = st.number_input("Costo Mano de Obra", min_value=0.0, value=5.0, step=1.0)
        otros_costos = st.number_input("Otros Costos Asociados", min_value=0.0, value=2.0, step=0.5)

        costo_total = mp + empaque + mo + otros_costos
        st.info(f"**COSTO TOTAL DE PRODUCCIÓN:** {costo_total:.2f} Bs")

        st.header("2. Márgenes e Impuestos")
        margen_fika = st.slider("Margen Fika (%)", 0, 90, 35) / 100

        st.markdown("##### Canales de Distribución")
        usar_distribuidor = st.checkbox("Incluir Distribuidor Mayorista")
        margen_distribuidor = st.slider("Margen Distribuidor (%)", 0, 50, 15) / 100 if usar_distribuidor else 0.0

        usar_pdv = st.checkbox("Incluir Punto de Venta (PDV)", value=True)
        margen_pdv = st.slider("Margen PDV (%)", 0, 50, 20) / 100 if usar_pdv else 0.0

        st.markdown("##### Carga Impositiva")
        impuestos = st.slider("Impuestos (%)", 0, 30, 13) / 100

    with col2:
        st.header("3. Proyección de Precios")

        # --- CÁLCULO ESTRICTO ---
        precio_fika = costo_total / (1 - margen_fika)
        utilidad_fika = precio_fika - costo_total

        precio_distribuidor = precio_fika / (1 - margen_distribuidor) if usar_distribuidor else precio_fika
        utilidad_distribuidor = precio_distribuidor - precio_fika

        precio_pdv = precio_distribuidor / (1 - margen_pdv) if usar_pdv else precio_distribuidor
        utilidad_pdv = precio_pdv - precio_distribuidor

        precio_final_cliente = precio_pdv / (1 - impuestos)
        monto_impuestos = precio_final_cliente - precio_pdv

        # --- MÉTRICAS ---
        m1, m2 = st.columns(2)
        m1.metric("PRECIO SALIDA FIKA", f"{precio_fika:.2f} Bs", f"Utilidad Neta: {utilidad_fika:.2f} Bs")
        m2.metric("PRECIO FINAL CLIENTE", f"{precio_final_cliente:.2f} Bs", f"Impuestos: {monto_impuestos:.2f} Bs", delta_color="off")

        # --- TABLA RESUMEN ---
        st.subheader("Desglose de la Cadena")
        datos_tabla = [
            {"Concepto": "Costo de Producción", "Monto (Bs)": costo_total},
            {"Concepto": "Utilidad Fika", "Monto (Bs)": utilidad_fika},
        ]
        if usar_distribuidor: datos_tabla.append({"Concepto": "Margen Distribuidor", "Monto (Bs)": utilidad_distribuidor})
        if usar_pdv: datos_tabla.append({"Concepto": "Margen PDV", "Monto (Bs)": utilidad_pdv})
        datos_tabla.append({"Concepto": "Impuestos", "Monto (Bs)": monto_impuestos})

        df_desglose = pd.DataFrame(datos_tabla)
        st.bar_chart(df_desglose.set_index("Concepto")["Monto (Bs)"])

        # --- GUARDAR COTIZACIÓN ---
        st.markdown("---")
        st.subheader("💾 Guardar esta Cotización")
        col_nombre, col_btn = st.columns([3, 1])
        with col_nombre:
            nombre_coti = st.text_input("Nombre del Producto / Escenario (ej: Ya!Jua 50g Supermercados)")
        with col_btn:
            st.write("") # Espaciador
            if st.button("Guardar", type="primary", use_container_width=True):
                if nombre_coti:
                    nueva_coti = {
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "parametros": {
                            "mp": mp, "empaque": empaque, "mo": mo, "otros": otros_costos,
                            "margen_fika": margen_fika, "margen_dist": margen_distribuidor,
                            "margen_pdv": margen_pdv, "impuestos": impuestos
                        },
                        "resultados": {
                            "costo_total": costo_total, 
                            "precio_fika": precio_fika,
                            "precio_final": precio_final_cliente
                        }
                    }
                    
                    def perform_save(db):
                        db[nombre_coti] = nueva_coti
                        return db
                    
                    st.session_state.db_cotizaciones = update_bd(perform_save)
                    guardar_bd(st.session_state.db_cotizaciones)
                    st.success("¡Cotización guardada con éxito!")
            else:
                st.warning("Por favor, ingresa un nombre para la cotización.")

# --- PESTAÑA 2: HISTORIAL ---
with tabs[1]:
    def render_historial():
        st.header("🗂️ Historial de Cotizaciones Guardadas")
    
        if not st.session_state.db_cotizaciones:
            st.info("Aún no tienes cotizaciones guardadas.")
        else:
            nombres_guardados = list(st.session_state.db_cotizaciones.keys())
            coti_seleccionada = st.selectbox("Selecciona una cotización para revisar:", nombres_guardados)
    
            if coti_seleccionada:
                datos = st.session_state.db_cotizaciones[coti_seleccionada]
                st.caption(f"📅 Fecha de creación/actualización: {datos['fecha']}")
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
    st.set_page_config(page_title="Costeador Profesional Fika", layout="wide")
    ARCHIVO_BD = "cotizaciones_fika.json"
    
    # --- FUNCIONES DE BASE DE DATOS ---
    def update_bd(updater_func):
        if not os.path.exists(ARCHIVO_BD):
            with open(ARCHIVO_BD, "w") as f:
                json.dump({}, f)
    
        with open(ARCHIVO_BD, "a+") as f:
            if fcntl:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            elif msvcrt:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
    
            try:
                f.seek(0)
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
    
                updated_data = updater_func(data)
    
                f.seek(0)
                f.truncate()
                json.dump(updated_data, f, indent=4)
            finally:
                if fcntl:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                elif msvcrt:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    
    def cargar_bd():
        if os.path.exists(ARCHIVO_BD):
            with open(ARCHIVO_BD, "r") as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}
    
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
    
    def add_materia_prima():
        new_id = len(st.session_state.materia_prima)
        st.session_state.materia_prima.append({"id": new_id, "nombre": "", "cantidad": 0.0, "rendimiento": 100.0, "costo": 0.0})
    
    def add_empaque():
        new_id = len(st.session_state.empaque)
        st.session_state.empaque.append({"id": new_id, "nombre": "", "cantidad": 0.0, "costo": 0.0})
    
    st.title("📊 Costeador Profesional")
    
    tabs = st.tabs(["📝 Nuevo Costeo", "🗂️ Historial"])
    
    with tabs[0]:
        col1, col2 = st.columns([1.2, 2])
    
        with col1:
            st.header("1. Materia Prima")
            for i, item in enumerate(st.session_state.materia_prima):
                c1, c2, c3, c4 = st.columns(4)
                item['nombre'] = c1.text_input("Nombre", item['nombre'], key=f"mp_nom_{i}")
                item['cantidad'] = c2.number_input("Cantidad", min_value=0.0, value=float(item['cantidad']), key=f"mp_cant_{i}")
                item['rendimiento'] = c3.number_input("Rendimiento (%)", min_value=0.1, value=float(item['rendimiento']), key=f"mp_rend_{i}")
                item['costo'] = c4.number_input("Costo (Bs.)", min_value=0.0, value=float(item['costo']), key=f"mp_costo_{i}")
    
            st.button("[ + Añadir Ítem ] Materia Prima", on_click=add_materia_prima)
    
            st.header("2. Costos de Empaque")
            st.caption("Envases, etiquetas, cajas, etc.")
            for i, item in enumerate(st.session_state.empaque):
                c1, c2, c3 = st.columns(3)
                item['nombre'] = c1.text_input("Nombre de Empaque", item['nombre'], key=f"emp_nom_{i}")
                item['cantidad'] = c2.number_input("Cantidad", min_value=0.0, value=float(item['cantidad']), key=f"emp_cant_{i}")
                item['costo'] = c3.number_input("Costo (Bs.)", min_value=0.0, value=float(item['costo']), key=f"emp_costo_{i}")
    
            st.button("[ + Añadir Ítem ] Empaque", on_click=add_empaque)
    
            st.header("3. Costos Operativos/Fijos")
            c1, c2 = st.columns(2)
            st.session_state.costos_operativos['mano_obra'] = c1.number_input("Mano de Obra (Bs.)", min_value=0.0, value=float(st.session_state.costos_operativos['mano_obra']))
            st.session_state.costos_operativos['prorrateo'] = c2.number_input("Prorrateo de Fabricación (Bs.)", min_value=0.0, value=float(st.session_state.costos_operativos['prorrateo']))
    
            st.header("4. Márgenes e Impuestos")
            margen_fika_pct = st.slider("Margen Fika (%)", 0, 99, 35)
            margen_pdv_pct = st.slider("Margen PDV (%)", 0, 99, 20)
            impuestos_pct = st.slider("Impuestos (%)", 0, 99, 13)
    
            if st.button("[ Calcular Precio Final ]", type="primary", use_container_width=True):
                st.session_state.mostrar_resultados = True
    
        with col2:
            st.header("Proyección de Precios")
    
            # --- CÁLCULO REACTIVO (SIEMPRE SE EJECUTA) ---
            costo_mp = sum([(item['cantidad'] * item['costo']) / (item['rendimiento']/100) if item['rendimiento'] > 0 else 0 for item in st.session_state.materia_prima])
            costo_empaque = sum([item['cantidad'] * item['costo'] for item in st.session_state.empaque])
            costo_op = st.session_state.costos_operativos['mano_obra'] + st.session_state.costos_operativos['prorrateo']
    
            costo_total = costo_mp + costo_empaque + costo_op
    
            mf = margen_fika_pct / 100.0
            mpdv = margen_pdv_pct / 100.0
            mimp = impuestos_pct / 100.0
    
            # Manejo seguro de la división
            precio_fika = costo_total / (1 - mf) if mf < 1.0 else 0
            precio_pdv = precio_fika / (1 - mpdv) if mpdv < 1.0 else 0
            precio_final = precio_pdv / (1 - mimp) if mimp < 1.0 else 0
    
            # Actualizar siempre el estado con los valores más recientes
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
                m1.metric("PRECIO SALIDA FIKA (Bs.)", f"{res['precio_fika']:.2f}", f"Utilidad Fika: {res['utilidad_fika']:.2f} Bs.")
                m2.metric("PRECIO FINAL CLIENTE (Bs.)", f"{res['precio_final']:.2f}", f"Impuestos: {res['monto_impuestos']:.2f} Bs.", delta_color="off")
    
                st.subheader("Desglose de la Cadena")
                chart_data = [
                    {"Concepto": "Costo de Producción", "Monto (Bs.)": res['costo_total']},
                    {"Concepto": "Margen Fika", "Monto (Bs.)": res['utilidad_fika']},
                    {"Concepto": "Margen PDV", "Monto (Bs.)": res['utilidad_pdv']},
                    {"Concepto": "Impuestos", "Monto (Bs.)": res['monto_impuestos']}
                ]
                st.bar_chart(chart_data, x="Concepto", y="Monto (Bs.)")
    
                st.markdown("---")
                st.subheader("Acciones")
    
                nombre_coti = st.text_input("Nombre del Producto / Escenario")
    
                if st.button("[ Guardar Costeo ]", type="primary"):
                    if nombre_coti:
                        def save_coti(data):
                            data[nombre_coti] = {
                                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "resultados": res,
                                "parametros": {
                                    "mp": st.session_state.materia_prima,
                                    "empaque": st.session_state.empaque,
                                    "op": st.session_state.costos_operativos
                                }
                            }
                            return data
                        update_bd(save_coti)
                        st.success("¡Costeo guardado con éxito!")
                    else:
                        st.error("Ponle un nombre para guardar el costeo.")
    
                if nombre_coti:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Helvetica", size=16, style="B")
                    pdf.cell(0, 10, "Cotización Comercial", new_x="LMARGIN", new_y="NEXT", align="C")
                    pdf.ln(10)
                    pdf.set_font("Helvetica", size=12)
                    pdf.cell(0, 10, f"Producto: {nombre_coti}", new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 10, f"Precio de Venta Sugerido: {res['precio_final']:.2f} Bs.", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(20)
                    pdf.cell(0, 10, "Aprobado por el cliente: _______________________", new_x="LMARGIN", new_y="NEXT")
    
                    pdf_bytes = pdf.output()
                    st.download_button(
                        label="[ Generar Cotización PDF ]",
                        data=pdf_bytes,
                        file_name=f"Cotizacion_{nombre_coti}.pdf",
                        mime="application/pdf"
                    )
    
    with tabs[1]:
        st.header("🗂️ Historial Guardado")
        bd = cargar_bd()
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
                    st.markdown("### Parámetros Usados")
                    p = datos['parametros']
                    df_params = pd.DataFrame({
                        "Variable": ["Materia Prima", "Empaque", "Mano de Obra", "Otros Costos", "Margen Fika", "Margen Dist.", "Margen PDV", "Impuestos"],
                        "Valor": [f"{p['mp']} Bs", f"{p['empaque']} Bs", f"{p['mo']} Bs", f"{p['otros']} Bs",
                                  f"{p['margen_fika']*100:.1f}%", f"{p['margen_dist']*100:.1f}%",
                                  f"{p['margen_pdv']*100:.1f}%", f"{p['impuestos']*100:.1f}%"]
                    })
                    st.table(df_params)
    
                if st.button("Eliminar esta cotización", type="secondary"):
                    def perform_delete(db):
                        if coti_seleccionada in db:
                            del db[coti_seleccionada]
                        return db
    
                    st.session_state.db_cotizaciones = update_bd(perform_delete)
                    st.rerun()
                    del st.session_state.db_cotizaciones[coti_seleccionada]
                    guardar_bd(st.session_state.db_cotizaciones)
                    st.rerun()
    
    def main():
        # --- CONFIGURACIÓN DE LA PÁGINA ---
        st.set_page_config(page_title="Cotizador Comercial FikaGroup", layout="wide")
    
        if 'db_cotizaciones' not in st.session_state:
            st.session_state.db_cotizaciones = cargar_bd()
    
        # --- ENCABEZADO ---
        st.title("📊 Cotizador Comercial FikaGroup")
        st.markdown("Calculadora estratégica B2B/B2C basada en **margen sobre precio**.")
    
        tabs = st.tabs(["📝 Nueva Cotización", "🗂️ Historial Guardado"])
    
        # --- PESTAÑA 1: NUEVA COTIZACIÓN ---
        with tabs[0]:
            render_nueva_cotizacion()
    
        # --- PESTAÑA 2: HISTORIAL ---
        with tabs[1]:
            render_historial()
    
    if __name__ == '__main__':
        main()
                    st.metric("Costo Total", f"{datos['resultados']['costo_total']:.2f} Bs.")
                    st.metric("Precio Salida Fika", f"{datos['resultados']['precio_fika']:.2f} Bs.")
                    st.metric("Precio Final Cliente", f"{datos['resultados']['precio_final']:.2f} Bs.")
    
                if st.button("Eliminar esta cotización", type="secondary"):
                    def delete_coti(data):
                        if coti_seleccionada in data:
                            del data[coti_seleccionada]
                        return data
                    update_bd(delete_coti)
                    st.rerun()
