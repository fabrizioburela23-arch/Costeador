import streamlit as st
import pandas as pd
import json
import os
import tempfile
import traceback
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
st.set_page_config(page_title="Fika Costeador | B2B", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# --- CSS MINIMALISTA Y ESTÉTICA DE MARCA FIKA ---
st.markdown("""
<style>
header[data-testid="stHeader"] { display: none; }
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
[data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 1rem !important;
    font-weight: 600 !important;
    opacity: 0.85;
}
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
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.stTextInput input, .stNumberInput input {
    border-radius: 6px;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

ARCHIVO_BD = "cotizaciones_fika.json"

def _lock_file(f):
    if fcntl: fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    elif msvcrt:
        try:
            p = f.tell()
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            f.seek(p)
        except (OSError, AttributeError): pass

def _unlock_file(f):
    if fcntl: fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    elif msvcrt:
        try:
            p = f.tell()
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            f.seek(p)
        except (OSError, AttributeError): pass

def cargar_bd():
    if not os.path.exists(ARCHIVO_BD): return {}
    try:
        with open(ARCHIVO_BD, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception: return {}

def update_bd(updater_func):
    if not os.path.exists(ARCHIVO_BD):
        with open(ARCHIVO_BD, "w", encoding="utf-8") as f: json.dump({}, f)
    with open(ARCHIVO_BD, "a+", encoding="utf-8") as f:
        _lock_file(f)
        try:
            f.seek(0)
            try:
                content = f.read()
                data = json.loads(content) if content else {}
            except Exception: data = {}
            updated_data = updater_func(data)
            f.seek(0)
            f.truncate()
            json.dump(updated_data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
            return updated_data
        finally:
            _unlock_file(f)

# --- NORMALIZADOR DE ESTADO SEGURO ---
if 'db_cotizaciones' not in st.session_state:
    st.session_state.db_cotizaciones = cargar_bd()

if 'materia_prima' not in st.session_state:
    st.session_state.materia_prima = [{"id": 0, "nombre": "", "u_m": "kg", "lote": "", "cantidad": 0.0, "rendimiento": 100.0, "costo": 0.0}]
else:
    for item in st.session_state.materia_prima:
        if 'u_m' not in item: item['u_m'] = 'kg'
        if 'lote' not in item: item['lote'] = ''

if 'empaque' not in st.session_state:
    st.session_state.empaque = [
        {"id": 0, "nombre": "Envases", "cantidad": 0.0, "costo": 0.0},
        {"id": 1, "nombre": "Etiquetas", "cantidad": 0.0, "costo": 0.0},
        {"id": 2, "nombre": "Cajas", "cantidad": 0.0, "costo": 0.0}
    ]

if 'costos_operativos' not in st.session_state:
    st.session_state.costos_operativos = {"mano_obra": 0.0, "prorrateo": 0.0, "transporte": 0.0}
else:
    if 'transporte' not in st.session_state.costos_operativos:
        st.session_state.costos_operativos['transporte'] = 0.0

def cargar_receta_a_estado(receta_id):
    datos = st.session_state.db_cotizaciones.get(receta_id, None)
    if datos:
        params = datos.get('parametros', {})
        mp_recuperada = []
        for i, item in enumerate(params.get('mp', [])):
            mp_recuperada.append({
                "id": i,
                "nombre": item.get('nombre', ''),
                "u_m": item.get('u_m', 'kg'),
                "lote": item.get('lote', ''),
                "cantidad": item.get('cantidad', 0.0),
                "rendimiento": item.get('rendimiento', 100.0),
                "costo": item.get('costo', 0.0)
            })
        st.session_state.materia_prima = mp_recuperada if mp_recuperada else [{"id": 0, "nombre": "", "u_m": "kg", "lote": "", "cantidad": 0.0, "rendimiento": 100.0, "costo": 0.0}]
        
        st.session_state.empaque = params.get('empaque', st.session_state.empaque)
        
        ops_antiguos = params.get('op', {})
        st.session_state.costos_operativos = {
            "mano_obra": ops_antiguos.get('mano_obra', 0.0),
            "prorrateo": ops_antiguos.get('prorrateo', 0.0),
            "transporte": ops_antiguos.get('transporte', 0.0) 
        }
        
        st.session_state.t_margen_fika = params.get('margen_fika', 35)
        st.session_state.t_margen_pdv = params.get('margen_pdv', 20)
        st.session_state.t_impuestos = params.get('impuestos', 13)

def refrescar_interfaz():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def add_materia_prima():
    st.session_state.materia_prima.append({"id": len(st.session_state.materia_prima), "nombre": "", "u_m": "kg", "lote": "", "cantidad": 0.0, "rendimiento": 100.0, "costo": 0.0})

def add_empaque():
    st.session_state.empaque.append({"id": len(st.session_state.empaque), "nombre": "", "cantidad": 0.0, "costo": 0.0})

def del_materia_prima(index):
    if len(st.session_state.materia_prima) > 1:
        st.session_state.materia_prima.pop(index)

def del_empaque(index):
    if len(st.session_state.empaque) > 1:
        st.session_state.empaque.pop(index)

def main():
    st.markdown("<div class='fika-logo'>FIKA <span style='font-weight:300;'>COSTEADOR</span></div>", unsafe_allow_html=True)
    st.markdown("<p class='fika-sub'>Inteligencia de Producción B2B 🚀</p>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Panel Comercial")
        
        opciones_bd = ['-- Crear Nueva Receta --'] + list(st.session_state.db_cotizaciones.keys())
        receta_seleccionada = st.selectbox("📂 Cargar Receta", opciones_bd)
        
        if st.button("⬇️ Restaurar Receta", use_container_width=True):
            if receta_seleccionada != '-- Crear Nueva Receta --':
                cargar_receta_a_estado(receta_seleccionada)
                refrescar_interfaz()

        st.divider()
        
        with st.container(border=True):
            st.markdown("<p style='font-size:0.9rem;font-weight:bold;'><span style='color: #E80373;'>●</span> Configuración de Márgenes</p>", unsafe_allow_html=True)
            v_fika = st.session_state.get('t_margen_fika', 35)
            v_pdv = st.session_state.get('t_margen_pdv', 20)
            v_imp = st.session_state.get('t_impuestos', 13)
            
            margen_fika_pct = st.slider("Margen Neto Fika (%)", 0, 99, int(v_fika), key="slider_fika")
            margen_pdv_pct = st.slider("Margen Punto Venta (%)", 0, 99, int(v_pdv), key="slider_pdv")
            impuestos_pct = st.slider("Impuestos IVA/IT (%)", 0, 99, int(v_imp), key="slider_imp")
        
        with st.container(border=True):
            st.markdown("<p style='font-size:0.9rem;font-weight:bold;'><span style='color: #00B0FF;'>●</span> Costos Estructurales / Lote</p>", unsafe_allow_html=True)
            try:
                mo = float(st.session_state.costos_operativos.get('mano_obra', 0.0))
                pr = float(st.session_state.costos_operativos.get('prorrateo', 0.0))
                tr = float(st.session_state.costos_operativos.get('transporte', 0.0))
            except:
                mo, pr, tr = 0.0, 0.0, 0.0
                
            st.session_state.costos_operativos['mano_obra'] = st.number_input("👷 Mano de Obra (Bs)", min_value=0.0, value=mo, step=1.0)
            st.session_state.costos_operativos['prorrateo'] = st.number_input("🏭 Prorrateo Fábrica (Bs)", min_value=0.0, value=pr, step=1.0)
            st.session_state.costos_operativos['transporte'] = st.number_input("🚚 Transporte (Bs)", min_value=0.0, value=tr, step=1.0)

    tab_cotizador, tab_historial = st.tabs(["📝 Formular y Costear", "🗂️ Historial Fika"])

    with tab_cotizador:
        col_datos, padding, col_resultados = st.columns([1.7, 0.05, 1.3])

        with col_datos:
            with st.container(border=True):
                st.markdown("<h3 style='margin-bottom:0;'>🌾 1. Materia Prima</h3>", unsafe_allow_html=True)
                st.write("") 
                
                for i, item in enumerate(st.session_state.materia_prima):
                    c1, c_um, c_lt, c2, c3, c4, c5 = st.columns([2.5, 0.8, 1.4, 1.0, 1.0, 1.3, 0.4])
                    visibility = "visible" if i == 0 else "collapsed"
                    
                    item['nombre'] = c1.text_input("Ingrediente", str(item.get('nombre', '')), key=f"mp_n_{i}", label_visibility=visibility)
                    item['u_m'] = c_um.text_input("U.M", str(item.get('u_m', 'kg')), key=f"mp_um_{i}", label_visibility=visibility)
                    item['lote'] = c_lt.text_input("Lote", str(item.get('lote', '')), key=f"mp_lt_{i}", label_visibility=visibility, placeholder="Opc.")
                    
                    try:
                        cant_val = float(item.get('cantidad', 0.0))
                        rend_val = float(item.get('rendimiento', 100.0))
                        cos_val = float(item.get('costo', 0.0))
                    except:
                        cant_val, rend_val, cos_val = 0.0, 100.0, 0.0
                        
                    item['cantidad'] = c2.number_input("Cant.", min_value=0.0, value=cant_val, key=f"mp_c_{i}", step=0.1, label_visibility=visibility)
                    item['rendimiento'] = c3.number_input("Rend%", min_value=0.1, value=rend_val, key=f"mp_r_{i}", step=1.0, label_visibility=visibility)
                    item['costo'] = c4.number_input("Costo", min_value=0.0, value=cos_val, key=f"mp_co_{i}", step=1.0, label_visibility=visibility)
                    
                    if i == 0:
                        c5.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if c5.button("✕", key=f"del_m_{i}", use_container_width=True):
                        del_materia_prima(i)
                        refrescar_interfaz()

                if st.button("➕ Adicionar Ingrediente"):
                     add_materia_prima()
                     refrescar_interfaz()

            with st.container(border=True):
                st.markdown("<h3 style='margin-bottom:0;'>📦 2. Material de Empaque</h3>", unsafe_allow_html=True)
                st.write("")
                
                for i, item in enumerate(st.session_state.empaque):
                    c1, c2, c3, c5 = st.columns([4, 1.5, 2, 0.4])
                    visibility = "visible" if i == 0 else "collapsed"
                    
                    item['nombre'] = c1.text_input("Empaque", str(item.get('nombre', '')), key=f"ep_n_{i}", label_visibility=visibility)
                    
                    try:
                        cant_e = float(item.get('cantidad', 0.0))
                        cos_e = float(item.get('costo', 0.0))
                    except:
                        cant_e, cos_e = 0.0, 0.0
                        
                    item['cantidad'] = c2.number_input("Unids", min_value=0.0, value=cant_e, key=f"ep_c_{i}", step=1.0, label_visibility=visibility)
                    item['costo'] = c3.number_input("Unitario(Bs)", min_value=0.0, value=cos_e, key=f"ep_co_{i}", step=1.0, label_visibility=visibility)
                    
                    if i == 0:
                        c5.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if c5.button("✕", key=f"del_e_{i}", use_container_width=True):
                        del_empaque(i)
                        refrescar_interfaz()

                if st.button("➕ Adicionar Empaque"):
                    add_empaque()
                    refrescar_interfaz()

            if st.button("🚀 Calcular Inteligencia Financiera", type="primary", use_container_width=True):
                st.session_state.mostrar_resultados = True

        with col_resultados:
            with st.container(border=True):
                st.markdown("### 📊 Tablero de Rentabilidad")

                costo_mp = sum([(float(item['cantidad']) * float(item['costo'])) / (float(item['rendimiento'])/100.0) if float(item['rendimiento']) > 0 else 0 for item in st.session_state.materia_prima])
                costo_empaque = sum([float(item['cantidad']) * float(item['costo']) for item in st.session_state.empaque])
                c_op = st.session_state.costos_operativos
                costo_op_total = float(c_op.get('mano_obra', 0.0)) + float(c_op.get('prorrateo', 0.0)) + float(c_op.get('transporte', 0.0))

                costo_total = costo_mp + costo_empaque + costo_op_total

                mf = float(margen_fika_pct) / 100.0
                mpdv = float(margen_pdv_pct) / 100.0
                mimp = float(impuestos_pct) / 100.0

                precio_fika = costo_total / (1.0 - mf) if mf < 1.0 else 0
                precio_pdv = precio_fika / (1.0 - mpdv) if mpdv < 1.0 else 0
                precio_final = precio_pdv / (1.0 - mimp) if mimp < 1.0 else 0

                st.session_state.resultados = {
                    "costo_total": costo_total, "precio_fika": precio_fika, "precio_pdv": precio_pdv,
                    "precio_final": precio_final, "utilidad_fika": precio_fika - costo_total,
                    "utilidad_pdv": precio_pdv - precio_fika, "monto_impuestos": precio_final - precio_pdv
                }

                if mf >= 1.0 or mpdv >= 1.0 or mimp >= 1.0:
                    st.error("⚠️ Alerta: Los márgenes no pueden ser 100%.")
                elif st.session_state.get('mostrar_resultados', False):
                    res = st.session_state.resultados

                    c_met1, c_met2 = st.columns(2)
                    c_met1.metric("🟣 B2B Fábrica", f"Bs {res['precio_fika']:.2f}")
                    c_met2.metric("🔵 B2C Cliente Final", f"Bs {res['precio_final']:.2f}", delta_color="off")
                    
                    st.divider()
                    
                    df_resumen = pd.DataFrame([
                        {"Elemento": "Costos Raíz", "Bs": f"{res['costo_total']:.2f}", "Margen %": f"{(res['costo_total']/res['precio_final'])*100:.1f}%" if res['precio_final']>0 else "0%"},
                        {"Elemento": "Ganancia Fika", "Bs": f"{res['utilidad_fika']:.2f}", "Margen %": f"{(res['utilidad_fika']/res['precio_final'])*100:.1f}%"  if res['precio_final']>0 else "0%"},
                        {"Elemento": "Ganancia Distr.", "Bs": f"{res['utilidad_pdv']:.2f}", "Margen %": f"{(res['utilidad_pdv']/res['precio_final'])*100:.1f}%"  if res['precio_final']>0 else "0%"},
                        {"Elemento": "Impuestos", "Bs": f"{res['monto_impuestos']:.2f}", "Margen %": f"{(res['monto_impuestos']/res['precio_final'])*100:.1f}%"  if res['precio_final']>0 else "0%"}
                    ])
                    st.dataframe(df_resumen, use_container_width=True, hide_index=True)

            with st.container(border=True):
                st.markdown("#### 📄 Proforma / Guardar")
                nombre_coti = st.text_input("ID Proforma", placeholder="Salsa Tomate", label_visibility="collapsed")
                logo_file = st.file_uploader("Logo (Opcional)", type=['png', 'jpg', 'jpeg'])

                c_g1, c_g2 = st.columns(2)
                with c_g1:
                    if st.button("💾 Guardar BD", use_container_width=True):
                        if nombre_coti:
                            def save_coti(data):
                                data[nombre_coti] = {
                                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "resultados": res,
                                    "parametros": {"mp": st.session_state.materia_prima, "empaque": st.session_state.empaque, "op": st.session_state.costos_operativos, "margen_fika": margen_fika_pct, "margen_pdv": margen_pdv_pct, "impuestos": impuestos_pct}
                                }
                                return data
                            st.session_state.db_cotizaciones = update_bd(save_coti)
                            st.success("✅ Ok")
                        else: st.error("⚠️ Nombre")
                
                with c_g2:
                    if nombre_coti and st.session_state.get('mostrar_resultados', False):
                        pdf = FPDF()
                        pdf.add_page()
                        
                        if logo_file is not None:
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                                    tmp.write(logo_file.getvalue())
                                    tmp_path = tmp.name
                                pdf.image(tmp_path, x=10, y=10, w=40)
                                pdf.ln(15)
                                os.remove(tmp_path)
                            except Exception: pass
                            
                        pdf.set_font("Helvetica", size=18, style="B")
                        pdf.cell(0, 10, "PROFORMA COMERCIAL", new_x="LMARGIN", new_y="NEXT", align="C")
                        pdf.ln(5)
                        
                        pdf.set_font("Helvetica", size=12)
                        pdf.cell(0, 10, f"Cliente: {nombre_coti}", new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
                        pdf.ln(10)
                        
                        pdf.set_font("Helvetica", size=11, style="B")
                        pdf.cell(70, 10, "Detalle Financiero", border=0)
                        pdf.cell(40, 10, "Monto", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.set_font("Helvetica", size=11)
                        pdf.cell(70, 8, "Costo de Produccion:")
                        pdf.cell(40, 8, f"{res['costo_total']:.2f} Bs.", align="R", new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.cell(70, 8, "Precio Fabrica:")
                        pdf.cell(40, 8, f"{res['precio_fika']:.2f} Bs.", align="R", new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.ln(3)
                        pdf.set_font("Helvetica", size=15, style="B")
                        pdf.cell(70, 10, "TOTAL CLIENTE FINAL:")
                        pdf.cell(40, 10, f"{res['precio_final']:.2f} Bs.", align="R", new_x="LMARGIN", new_y="NEXT")

                        pdf_bytes = pdf.output()
                        st.download_button(label="📄 PDF", data=pdf_bytes, file_name=f"{nombre_coti.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
                    else: st.button("📄 PDF", disabled=True, use_container_width=True)

    with tab_historial:
        st.subheader("🗄️ Historial Fika")
        bd = st.session_state.db_cotizaciones
        if not bd:
            st.info("Vacío.")
        else:
            with st.container(border=True):
                coti_seleccionada = st.selectbox("Buscar:", ['-- Vacio --'] + list(bd.keys()))
                if coti_seleccionada and coti_seleccionada != '-- Vacio --':
                    datos = bd[coti_seleccionada]
                    st.caption(f"Registro: {datos['fecha']}")
                    st.metric("Venta Público", f"{datos['resultados']['precio_final']:.2f} Bs")

try:
    main()
except Exception as e:
    st.error(f"⚠️ ERROR FATAL BLOQUEADO: {str(e)}")
    st.code(traceback.format_exc())
