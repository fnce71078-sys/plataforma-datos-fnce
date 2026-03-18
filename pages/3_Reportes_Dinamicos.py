import streamlit as st
import google_connector as gc
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Constructor de Reportes", page_icon="📑", layout="wide")
SPREADSHEET_ID = "1YLwfQE1u_4d8UNoDG8eC1ysb2QEApxqtwoKTBGNUW6g"

# 1. Verificar Seguridad
if "logeado" not in st.session_state or not st.session_state["logeado"]:
    st.warning("🔒 Por favor, inicia sesión en la página principal (Home).")
    st.stop()

st.title("📑 Constructor de Reportes a la Medida")
st.markdown("Crea tablas personalizadas combinando variables de diferentes fuentes de energía FNCE.")

pestanas = gc.get_all_sheet_names(SPREADSHEET_ID)

if not pestanas:
    st.info("Aún no hay energías creadas.")
    st.stop()

# --- EXTRACCIÓN Y LIMPIEZA DE DATOS ---
df_consolidado_lista = []
conteo_indicadores = [] # Lista para guardar cuántos indicadores tiene cada energía

with st.spinner('Cargando toda la base de datos y calculando indicadores...'):
    for p in pestanas:
        nombre_energia = p.replace("Proyectos_", "")
        
        # Leemos las columnas para la gráfica superior
        columnas_totales = gc.get_columnas(SPREADSHEET_ID, p)
        # Limpiamos y no contamos las columnas del sistema
        cols_limpias = [str(c).strip().title() for c in columnas_totales if str(c).strip().title() not in ["Usuario", "Última_Modificación", "Última_Modificacion", ""]]
        conteo_indicadores.append({"Tipo_Energía": nombre_energia, "Cantidad_Indicadores": len(cols_limpias)})

        # Leemos los datos para la tabla dinámica
        datos_hoja = gc.get_all_records(SPREADSHEET_ID, p)
        if datos_hoja:
            df_temp = pd.DataFrame(datos_hoja)
            df_temp.columns = df_temp.columns.str.strip().str.title()
            df_temp["Tipo_Energía"] = nombre_energia 
            df_consolidado_lista.append(df_temp)

# --- SECCIÓN 1: GRÁFICA COMPARATIVA DE INDICADORES ---
st.markdown("### 📊 Densidad de Evaluación por Energía")
st.write("Compara cuántos indicadores o variables se están midiendo en cada tipo de fuente.")

df_conteo_ind = pd.DataFrame(conteo_indicadores)

if not df_conteo_ind.empty:
    fig_indicadores = px.bar(
        df_conteo_ind, 
        x="Tipo_Energía", 
        y="Cantidad_Indicadores",
        text="Cantidad_Indicadores", # Pone el numerito encima de la barra
        color="Tipo_Energía",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_indicadores.update_traces(textposition='outside')
    fig_indicadores.update_layout(showlegend=False, yaxis_title="N° de Indicadores", xaxis_title="Energía")
    st.plotly_chart(fig_indicadores, use_container_width=True)

st.markdown("---")

# --- SECCIÓN 2: CONSTRUCTOR DE LA TABLA ---
if df_consolidado_lista:
    df_global = pd.concat(df_consolidado_lista, ignore_index=True)
else:
    df_global = pd.DataFrame()
    st.warning("No hay proyectos registrados en la base de datos para armar el reporte.")
    st.stop()

st.markdown("### 🛠️ Configura tu Reporte")

# Obtenemos todas las columnas limpias
todas_las_columnas = [c for c in df_global.columns if c not in ["Usuario", "Última_Modificación", "Última_Modificacion"]]

if len(todas_las_columnas) > 0:
    # El usuario elige cuál es la columna "Ancla"
    col_ancla = st.selectbox("📌 Selecciona la columna fija que identifica a tus proyectos (Ej: Nombre Proyecto):", todas_las_columnas, index=0)

    # Quitamos la columna ancla y el Tipo de Energía de las opciones restantes
    opciones_variables = [c for c in todas_las_columnas if c not in [col_ancla, "Tipo_Energía"]]

    # El usuario elige qué más quiere ver
    variables_seleccionadas = st.multiselect(
        "➕ Selecciona los indicadores que deseas agregar a la tabla (puedes elegir varios):",
        options=opciones_variables,
        default=opciones_variables[:3] if len(opciones_variables) >= 3 else opciones_variables
    )

    st.markdown("---")
    st.markdown("### 📑 Tu Reporte Generado")

    # Armamos la tabla final
    columnas_finales = [col_ancla, "Tipo_Energía"] + variables_seleccionadas
    df_reporte = df_global[columnas_finales].dropna(subset=[col_ancla])

    # Mostramos la tabla interactiva
    st.dataframe(df_reporte, use_container_width=True, hide_index=True)

    # Botón para descargar
    if not df_reporte.empty:
        csv = df_reporte.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar este Reporte (CSV)",
            data=csv,
            file_name='reporte_personalizado_fnce.csv',
            mime='text/csv',
        )
else:
    st.info("No se encontraron indicadores válidos para construir el reporte.")