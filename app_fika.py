import streamlit as st
import pandas as pd
import json
import os
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
                    st.session_state.db_cotizaciones[nombre_coti] = {
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "parametros": {
                            "mp": mp, "empaque": empaque, "mo": mo, "otros": otros_costos,
                            "margen_fika": margen_fika, "margen_dist": margen_distribuidor,
                            "margen_pdv": margen_pdv, "impuestos": impuestos
                        },
                        "resultados": {
                            "costo_total": costo_total, "precio_fika": precio_fika,
                            "precio_final": precio_final_cliente
                        }
                    }
                    guardar_bd(st.session_state.db_cotizaciones)
                    st.success("¡Cotización guardada con éxito!")
                else:
                    st.error("Ponle un nombre para guardarla.")

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
