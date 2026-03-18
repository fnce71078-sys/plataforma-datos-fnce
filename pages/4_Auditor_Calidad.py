import streamlit as st
import google_connector as gc
import pandas as pd
import numpy as np

st.set_page_config(page_title="Auditor de Calidad", page_icon="🕵️‍♂️", layout="wide")
SPREADSHEET_ID = "1YLwfQE1u_4d8UNoDG8eC1ysb2QEApxqtwoKTBGNUW6g"

# 1. Verificar Seguridad
if "logeado" not in st.session_state or not st.session_state["logeado"]:
    st.warning("🔒 Por favor, inicia sesión en la página principal (Home).")
    st.stop()

st.title("🕵️‍♂️ Auditor de Calidad de Datos (Data Scanner)")
st.markdown("Módulo de **solo lectura** para detectar inconsistencias, datos faltantes y medir la salud de la matriz.")

pestanas = gc.get_all_sheet_names(SPREADSHEET_ID)

if not pestanas:
    st.info("Aún no hay energías creadas en la base de datos.")
    st.stop()

# --- SELECCIÓN DE ENERGÍA ---
st.markdown("### 1. Selecciona la Matriz a Auditar")
energia_seleccionada = st.selectbox("⚡ Energía:", pestanas)

with st.spinner('Escaneando base de datos...'):
    datos = gc.get_all_records(SPREADSHEET_ID, energia_seleccionada)

if not datos:
    st.warning(f"No hay proyectos registrados en {energia_seleccionada.replace('Proyectos_', '')} para auditar.")
    st.stop()

df = pd.DataFrame(datos)

# --- MOTOR DE AUDITORÍA ---
# Limpiamos los nombres de las columnas para evitar errores
df.columns = df.columns.str.strip().str.title()

# Ignoramos las columnas del sistema porque esas se llenan solas
columnas_sistema = ["Usuario", "Última_Modificación", "Última_Modificacion"]
cols_a_evaluar = [c for c in df.columns if c not in columnas_sistema]

# Convertimos los espacios en blanco y cadenas vacías a valores nulos (NaN) reales de Python para poder contarlos
df_eval = df[cols_a_evaluar].replace(r'^\s*$', np.nan, regex=True)

# Cálculos de salud
total_celdas = df_eval.size
celdas_vacias = df_eval.isna().sum().sum()
celdas_llenas = total_celdas - celdas_vacias
porcentaje_salud = (celdas_llenas / total_celdas) * 100 if total_celdas > 0 else 0

st.markdown("---")
st.markdown(f"### 🩺 Diagnóstico General: {energia_seleccionada.replace('Proyectos_', '')}")

# --- TARJETAS DE MÉTRICAS ---
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Proyectos Evaluados", len(df_eval))
col_m2.metric("Total de Datos Esperados", total_celdas)
col_m3.metric("Datos Faltantes (Huecos)", celdas_vacias, delta_color="inverse")

# --- BARRA DE SALUD ---
st.write("**Nivel de Completitud de la Matriz:**")
barra_color = "green" if porcentaje_salud == 100 else "orange" if porcentaje_salud > 70 else "red"

# Usamos HTML para hacer una barra de progreso que cambie de color
st.markdown(f"""
    <div style="background-color: #e6e6e6; border-radius: 10px; height: 25px; width: 100%;">
        <div style="background-color: {barra_color}; width: {porcentaje_salud}%; height: 100%; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
            {porcentaje_salud:.1f}%
        </div>
    </div>
    <br>
""", unsafe_allow_html=True)

if porcentaje_salud == 100.0:
    st.success("🌟 ¡Excelente! La matriz está al 100%. No falta ningún dato en los proyectos registrados.")
else:
    st.warning("⚠️ Se han detectado datos en blanco. Revisa los detalles a continuación para corregirlos en la pestaña de 'Ingreso Datos'.")

    st.markdown("---")
    st.markdown("### 🚨 Detalle de Alertas")
    
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        st.write("**📌 Columnas con más datos faltantes:**")
        # Contar nulos por columna
        nulos_por_columna = df_eval.isna().sum()
        nulos_por_columna = nulos_por_columna[nulos_por_columna > 0].sort_values(ascending=False)
        
        df_nulos_col = pd.DataFrame({
            "Indicador": nulos_por_columna.index,
            "Celdas Vacías": nulos_por_columna.values
        })
        st.dataframe(df_nulos_col, hide_index=True, use_container_width=True)

    with col_a2:
        st.write("**📌 Proyectos incompletos:**")
        # Asumimos que la primera columna es el nombre del proyecto
        col_nombre_proyecto = cols_a_evaluar[0]
        
        # Contar nulos por fila (proyecto)
        nulos_por_fila = df_eval.isna().sum(axis=1)
        filas_con_nulos = nulos_por_fila[nulos_por_fila > 0].index
        
        # Armamos una tablita que diga "El proyecto X le faltan Y datos"
        proyectos_incompletos = df_eval.loc[filas_con_nulos, col_nombre_proyecto].values
        cantidad_faltante = nulos_por_fila[nulos_por_fila > 0].values
        
        df_nulos_fila = pd.DataFrame({
            "Proyecto": proyectos_incompletos,
            "Datos Faltantes": cantidad_faltante
        }).sort_values(by="Datos Faltantes", ascending=False)
        
        st.dataframe(df_nulos_fila, hide_index=True, use_container_width=True)
        
    st.info("💡 **Instrucción:** Copia el nombre del proyecto incompleto, ve a la pestaña '1_Ingreso_Datos', búscalo en la tabla dinámica y llena las celdas vacías.")