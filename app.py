import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from formulas import FinancialCalculator
from db import CosteosDB

# Configuración de página
st.set_page_config(
    page_title="App Costeador Agroindustrial",
    page_icon="🥭",
    layout="wide"
)

st.title("📊 App Costeador Agroindustrial")
st.markdown("Plataforma de costeo avanzado para deshidratación y molienda de alimentos.")

# --- INICIALIZAR ESTADO DE SESIÓN ---
if 'mpd_items' not in st.session_state:
    st.session_state.mpd_items = []
if 'empaque_items' not in st.session_state:
    st.session_state.empaque_items = []
if 'cif_items' not in st.session_state:
    st.session_state.cif_items = []

# --- SIDEBAR: SIMULADOR WHAT-IF ---
st.sidebar.header("🎛️ Simulador de Escenarios (What-If)")
st.sidebar.markdown("Ajusta los parámetros financieros en tiempo real.")

st.sidebar.subheader("Materia Prima Principal (Simulación)")
costo_mpd_simulado_bs = st.sidebar.slider("Ajuste Costo MPD Base (Bs.)", min_value=0.0, max_value=50000.0, value=0.0, step=100.0, help="Si es mayor a 0, este valor reemplazará el cálculo de materias primas ingresadas manualmente para evaluar un escenario rápido.")

st.sidebar.divider()
margen_fika_pct = st.sidebar.slider("Margen Fika (%)", min_value=0.0, max_value=99.0, value=30.0, step=1.0) / 100.0
margen_pdv_pct = st.sidebar.slider("Margen PDV (%)", min_value=0.0, max_value=99.0, value=20.0, step=1.0) / 100.0
impuestos_pct = st.sidebar.slider("Impuestos (%)", min_value=0.0, max_value=99.0, value=16.0, step=1.0) / 100.0

st.sidebar.divider()
lote_produccion = st.sidebar.number_input("Tamaño del Lote de Producción (Unidades finales)", min_value=1, value=1000)

# --- PESTAÑAS PRINCIPALES ---
tab_ingreso, tab_resultados, tab_guardados = st.tabs(["📝 Ingreso de Datos", "📈 Reporte de Rentabilidad", "📂 Costeos Guardados"])

with tab_ingreso:
    st.header("1. Materia Prima Directa (MPD)")
    st.caption("Añade las materias primas. Define la merma para procesos de deshidratación.")

    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
    with col1: mpd_nombre = st.text_input("Nombre MPD", key="mpd_n")
    with col2: mpd_cantidad = st.number_input("Cant. Inicial (Kg)", min_value=0.0, value=100.0, key="mpd_c")
    with col3: mpd_costo_unit = st.number_input("Costo Unit. (Bs/Kg)", min_value=0.0, value=5.0, key="mpd_cu")
    with col4: mpd_merma = st.number_input("Merma (%)", min_value=0.0, max_value=99.0, value=90.0, key="mpd_m")
    with col5:
        st.write("")
        st.write("")
        if st.button("➕ Add", key="add_mpd"):
            if mpd_nombre:
                # Calcular impacto de la merma
                calc = FinancialCalculator.calculate_mpd_cost(mpd_cantidad, mpd_costo_unit, mpd_merma/100.0)
                st.session_state.mpd_items.append({
                    "nombre": mpd_nombre,
                    "cantidad_inicial_kg": mpd_cantidad,
                    "costo_unitario_bs": mpd_costo_unit,
                    "porcentaje_merma": mpd_merma/100.0,
                    "cantidad_final_kg": calc["cantidad_final_kg"],
                    "costo_total_bs": calc["costo_total_bs"]
                })

    if st.session_state.mpd_items:
        df_mpd = pd.DataFrame(st.session_state.mpd_items)
        st.dataframe(df_mpd, use_container_width=True)
        total_mpd_calculado = df_mpd['costo_total_bs'].sum()
        st.write(f"**Total MPD Calculado: Bs. {total_mpd_calculado:,.2f}**")
    else:
        total_mpd_calculado = 0.0

    # Lógica de simulación de costo de materia prima
    if costo_mpd_simulado_bs > 0:
        total_mpd = costo_mpd_simulado_bs
        st.info(f"🔮 Simulando con Costo MPD Base de la barra lateral: **Bs. {total_mpd:,.2f}**")
    else:
        total_mpd = total_mpd_calculado

    st.divider()

    st.header("2. Costos de Empaque")
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    with col1: emp_nombre = st.text_input("Ítem de Empaque", key="emp_n")
    with col2: emp_cantidad = st.number_input("Cantidad", min_value=0.0, value=1000.0, key="emp_c")
    with col3: emp_costo_unit = st.number_input("Costo Unit. (Bs)", min_value=0.0, value=1.5, key="emp_cu")
    with col4:
        st.write("")
        st.write("")
        if st.button("➕ Add", key="add_emp"):
            if emp_nombre:
                st.session_state.empaque_items.append({
                    "item": emp_nombre,
                    "cantidad": emp_cantidad,
                    "costo_unitario_bs": emp_costo_unit,
                    "costo_total_bs": emp_cantidad * emp_costo_unit
                })

    if st.session_state.empaque_items:
        df_emp = pd.DataFrame(st.session_state.empaque_items)
        st.dataframe(df_emp, use_container_width=True)
        total_empaque = df_emp['costo_total_bs'].sum()
        st.write(f"**Total Empaque: Bs. {total_empaque:,.2f}**")
    else:
        total_empaque = 0.0

    st.divider()

    st.header("3. Mano de Obra Directa (MOD)")
    col1, col2 = st.columns(2)
    with col1: mod_horas = st.number_input("Horas Totales del Lote", min_value=0.0, value=40.0)
    with col2: mod_costo_hora = st.number_input("Costo por Hora (Bs)", min_value=0.0, value=15.0)
    total_mod = mod_horas * mod_costo_hora
    st.write(f"**Total MOD: Bs. {total_mod:,.2f}**")

    st.divider()

    st.header("4. Costos Indirectos de Fabricación (CIF)")
    col1, col2, col3 = st.columns([4, 3, 1])
    with col1: cif_nombre = st.text_input("Concepto CIF", key="cif_n")
    with col2: cif_costo = st.number_input("Costo Total (Bs)", min_value=0.0, value=300.0, key="cif_c")
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Add", key="add_cif"):
            if cif_nombre:
                st.session_state.cif_items.append({
                    "concepto": cif_nombre,
                    "costo_total_bs": cif_costo
                })

    if st.session_state.cif_items:
        df_cif = pd.DataFrame(st.session_state.cif_items)
        st.dataframe(df_cif, use_container_width=True)
        total_cif = df_cif['costo_total_bs'].sum()
        st.write(f"**Total CIF: Bs. {total_cif:,.2f}**")
    else:
        total_cif = 0.0

# --- CÁLCULO GENERAL ---
try:
    resultados = FinancialCalculator.calculate_full_costing(
        total_mpd_bs=total_mpd,
        total_empaque_bs=total_empaque,
        total_mod_bs=total_mod,
        total_cif_bs=total_cif,
        lote_produccion_unidades=lote_produccion,
        margen_fika_porcentaje=margen_fika_pct,
        margen_pdv_porcentaje=margen_pdv_pct,
        impuestos_porcentaje=impuestos_pct
    )
    calculo_exitoso = True
except Exception as e:
    st.error(f"Error en los cálculos: {str(e)}")
    calculo_exitoso = False

with tab_resultados:
    if calculo_exitoso:
        st.header("Resumen Financiero por Unidad")

        ru = resultados['rentabilidad_unitaria']
        cu = resultados['costos_unitarios']

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Costo Total Producción", f"Bs. {cu['costo_produccion']:.2f}")
        col2.metric("Precio Fábrica", f"Bs. {ru['precio_venta_fabrica_bs']:.2f}", f"Margen Fika: {margen_fika_pct*100}%")
        col3.metric("Precio Público (sin imp)", f"Bs. {ru['precio_venta_publico_sin_impuestos_bs']:.2f}", f"Margen PDV: {margen_pdv_pct*100}%")
        col4.metric("PVP Final", f"Bs. {ru['precio_venta_publico_bs']:.2f}", f"Impuestos: {impuestos_pct*100}%")

        st.divider()

        st.subheader("Desglose del Precio de Venta al Público (PVP)")

        # Datos para Gráfico de Cascada o Torta
        datos_desglose = {
            "Componente": ["MPD", "Empaque", "MOD", "CIF", "Margen Fika", "Margen PDV", "Impuestos"],
            "Monto (Bs.)": [
                cu['mpd'],
                cu['empaque'],
                cu['mod'],
                cu['cif'],
                ru['monto_margen_fika_bs'],
                ru['monto_margen_pdv_bs'],
                ru['monto_impuestos_bs']
            ]
        }
        df_plot = pd.DataFrame(datos_desglose)

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            fig_pie = px.pie(df_plot, values="Monto (Bs.)", names="Componente", title="Participación en el PVP")
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_chart2:
            fig_waterfall = go.Figure(go.Waterfall(
                name = "20", orientation = "v",
                measure = ["relative"] * 7 + ["total"],
                x = df_plot["Componente"].tolist() + ["PVP Final"],
                textposition = "outside",
                y = df_plot["Monto (Bs.)"].tolist() + [ru['precio_venta_publico_bs']],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            fig_waterfall.update_layout(title="Construcción del Precio (Cascada)")
            st.plotly_chart(fig_waterfall, use_container_width=True)

        st.divider()
        st.subheader("Guardar Costeo")
        nombre_costeo = st.text_input("Nombre de este escenario (Ej: Mango Deshidratado 100Kg)")
        if st.button("💾 Guardar en Base de Datos"):
            if not nombre_costeo:
                st.warning("Debes asignar un nombre al costeo antes de guardar.")
            else:
                doc_data = {
                    "nombre_costeo": nombre_costeo,
                    "lote_produccion_kg": lote_produccion,
                    "mpd": st.session_state.mpd_items,
                    "empaque": st.session_state.empaque_items,
                    "mod": {
                        "horas_totales": mod_horas,
                        "costo_por_hora_bs": mod_costo_hora,
                        "costo_total_bs": total_mod
                    },
                    "cif": st.session_state.cif_items,
                    "parametros_financieros": {
                        "margen_fika_porcentaje": margen_fika_pct,
                        "margen_pdv_porcentaje": margen_pdv_pct,
                        "impuestos_porcentaje": impuestos_pct
                    },
                    "resultados": resultados
                }
                doc_id = CosteosDB.save_costeo(doc_data)
                st.success(f"Costeo '{nombre_costeo}' guardado exitosamente (ID: {doc_id})!")

with tab_guardados:
    st.header("Costeos Históricos Guardados")
    if st.button("🔄 Refrescar Lista"):
        st.rerun()

    try:
        costeos_guardados = CosteosDB.get_all_costeos()
        if costeos_guardados:
            for c in costeos_guardados:
                with st.expander(f"{c.get('nombre_costeo', 'Sin nombre')} - {c.get('fecha_actualizacion', '')}"):
                    st.json(c)
        else:
            st.info("No hay costeos guardados todavía.")
    except Exception as e:
        st.error(f"Error cargando costeos de la base de datos: {str(e)}")
