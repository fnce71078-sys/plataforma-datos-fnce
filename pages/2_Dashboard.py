import streamlit as st
import google_connector as gc
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Analítico", page_icon="📊", layout="wide")
SPREADSHEET_ID = "1YLwfQE1u_4d8UNoDG8eC1ysb2QEApxqtwoKTBGNUW6g"

if "logeado" not in st.session_state or not st.session_state["logeado"]:
    st.warning("🔒 Por favor, inicia sesión en la página principal (Home).")
    st.stop()

st.title("📊 Panel de Inteligencia Corporativa - FNCE")
st.markdown("Análisis avanzado y comparativo de viabilidad de proyectos.")

pestanas = gc.get_all_sheet_names(SPREADSHEET_ID)

# --- FILTRO MÁGICO APLICADO AQUÍ ---
energias_reales = [p for p in pestanas if p != "Config_Diccionario"]

if not energias_reales:
    st.info("Aún no hay energías creadas.")
    st.stop()

datos_maestros = {}
columnas_por_energia = {}
df_consolidado_lista = []

# --- MOTOR DE LIMPIEZA Y ESTANDARIZACIÓN ---
with st.spinner('Procesando y unificando datos...'):
    # Usamos energias_reales para que ignore el diccionario
    for p in energias_reales: 
        nombre_energia = p.replace("Proyectos_", "")
        datos_hoja = gc.get_all_records(SPREADSHEET_ID, p)
        
        if datos_hoja:
            df_temp = pd.DataFrame(datos_hoja)
            
            # 1. LA MAGIA: Limpiamos espacios y capitalizamos todo para que "valor" y "Valor" sean iguales
            df_temp.columns = df_temp.columns.str.strip().str.title()
            
            # Identificamos columnas de sistema y las sacamos de la lista de indicadores
            cols_sistema = ["Usuario", "Última_Modificación", "Última_modificación"]
            cols_limpias = [c for c in df_temp.columns if c not in cols_sistema]
            
            columnas_por_energia[nombre_energia] = cols_limpias
            datos_maestros[nombre_energia] = df_temp
            
            # Etiquetamos para el global
            df_temp["Tipo_Energía"] = nombre_energia 
            df_consolidado_lista.append(df_temp)

if df_consolidado_lista:
    df_global = pd.concat(df_consolidado_lista, ignore_index=True)
else:
    df_global = pd.DataFrame()

# Extraemos una lista de columnas maestras (ya unificadas)
if not df_global.empty:
    todas_las_columnas_globales = [c for c in df_global.columns if c not in ["Tipo_Energía", "Usuario", "Última_Modificación", "Última_modificación"]]
else:
    todas_las_columnas_globales = []

tab_tablas, tab_graficas = st.tabs(["📋 VISIÓN GENERAL Y TABLAS", "📈 INTELIGENCIA GRÁFICA (Plotly)"])

# ==========================================
# PESTAÑA 1: VISIÓN GENERAL Y TABLAS
# ==========================================
with tab_tablas:
    st.markdown("### 🌐 Resumen Automático de Proyectos")
    
    # Ajustamos la cantidad de columnas visuales a las energías reales
    cols_resumen = st.columns(len(energias_reales)) 
    for i, nombre_energia in enumerate(columnas_por_energia.keys()):
        cantidad_proyectos = len(datos_maestros.get(nombre_energia, []))
        cantidad_indicadores = len(columnas_por_energia[nombre_energia])
        
        with cols_resumen[i]:
            st.success(f"**{nombre_energia}**\n\n📂 Proyectos: {cantidad_proyectos} | 📐 Indicadores: {cantidad_indicadores}")

    st.markdown("---")
    
    st.markdown("### 🔍 Explorador por Energía (Automático)")
    energia_explorar = st.selectbox("Selecciona la matriz a detallar:", list(datos_maestros.keys()) if datos_maestros else ["Ninguna"])
    
    if energia_explorar in datos_maestros:
        st.dataframe(datos_maestros[energia_explorar].drop(columns=["Tipo_Energía", "Usuario", "Última_Modificación", "Última_modificación"], errors='ignore'), use_container_width=True)

    st.markdown("---")
    
    # --- TABLA COMPARATIVA TEXTUAL / GENERAL ---
    st.markdown("### ⚖️ Tabla Comparativa de Variables")
    st.write("Selecciona una columna que identifique al proyecto y otra variable para cruzar la información entre distintas energías.")
    
    if len(todas_las_columnas_globales) >= 2:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            col_proyecto_general = st.selectbox("Columna Identificadora (Ej: Nombre Proyecto):", todas_las_columnas_globales, index=0)
        with col_c2:
            col_a_comparar = st.selectbox("Variable a comparar:", todas_las_columnas_globales, index=1)
        
        # Filtramos la tabla para mostrar solo lo que el usuario quiere comparar
        df_comparativo = df_global[[col_proyecto_general, "Tipo_Energía", col_a_comparar]].dropna()
        st.dataframe(df_comparativo, use_container_width=True, hide_index=True)
    else:
        st.info("Registra más indicadores para habilitar la tabla comparativa.")

# ==========================================
# PESTAÑA 2: GRÁFICAS PRO (PLOTLY)
# ==========================================
with tab_graficas:
    if df_global.empty:
        st.warning("No hay datos suficientes para graficar.")
    else:
        st.markdown("### 🌍 Distribución General (Automática)")
        conteo_energias = df_global["Tipo_Energía"].value_counts().reset_index()
        conteo_energias.columns = ["Tipo_Energía", "Cantidad"]
        
        fig_pie = px.pie(
            conteo_energias, values='Cantidad', names='Tipo_Energía', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")

        # --- 1. GRÁFICA INDIVIDUAL (LA QUE HABÍAMOS QUITADO) ---
        st.markdown("### 🎯 Análisis Específico por Energía")
        st.write("Selecciona una energía y cruza sus variables libremente.")
        col_g1, col_g2, col_g3 = st.columns(3)
        
        with col_g1:
            energia_graficar = st.selectbox("1. Energía:", list(datos_maestros.keys()), key="ind_energia")
        
        if energia_graficar in datos_maestros:
            df_ind = datos_maestros[energia_graficar].copy()
            cols_ind = [c for c in df_ind.columns if c not in ["Tipo_Energía", "Usuario", "Última_Modificación", "Última_modificación"]]
            
            with col_g2:
                eje_x_ind = st.selectbox("2. Eje X (Proyectos / Categoría):", cols_ind, key="ind_x")
            with col_g3:
                eje_y_ind = st.selectbox("3. Eje Y (Variable a medir):", cols_ind, key="ind_y")
            
            if eje_x_ind and eje_y_ind:
                # Intentamos forzar el Eje Y a numérico para que la gráfica tenga sentido
                df_ind[eje_y_ind] = pd.to_numeric(df_ind[eje_y_ind], errors='coerce')
                
                if df_ind[eje_y_ind].notna().any():
                    fig_ind = px.bar(
                        df_ind, x=eje_x_ind, y=eje_y_ind, text_auto='.2s',
                        color=eje_x_ind, color_discrete_sequence=px.colors.qualitative.Bold,
                        title=f"{eje_y_ind} por {eje_x_ind} en {energia_graficar}"
                    )
                    fig_ind.update_layout(showlegend=False)
                    st.plotly_chart(fig_ind, use_container_width=True)
                else:
                    st.warning(f"⚠️ La columna '{eje_y_ind}' no contiene números. Selecciona una variable numérica para el Eje Y.")

        st.markdown("---")
        
        # --- 2. GRÁFICA COMPARATIVA NUMÉRICA (CON UNIFICACIÓN DE NOMBRES) ---
        st.markdown("### 📈 Comparativa Numérica Global")
        st.write("El sistema detecta automáticamente las columnas numéricas que comparten el mismo nombre en diferentes energías.")
        
        cols_numericas_global = []
        df_global_grafica = df_global.copy()
        
        for col in todas_las_columnas_globales:
            df_temp = pd.to_numeric(df_global_grafica[col], errors='coerce')
            if df_temp.notna().any():
                cols_numericas_global.append(col)
                df_global_grafica[col] = df_temp
                
        if len(cols_numericas_global) > 0:
            col_comp1, col_comp2 = st.columns(2)
            with col_comp1:
                eje_y_global = st.selectbox("Indicador Numérico a comparar:", cols_numericas_global)
            with col_comp2:
                eje_x_global = st.selectbox("Agrupar por:", todas_las_columnas_globales)
            
            fig_global = px.bar(
                df_global_grafica, 
                x=eje_x_global, 
                y=eje_y_global, 
                color="Tipo_Energía",
                barmode="group",
                title=f"Comparativa de {eje_y_global} entre energías",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            st.plotly_chart(fig_global, use_container_width=True)
            
            # Gráfico de Cajas Estadístico (Opcional pero muy útil para informes)
            with st.expander("Ver Análisis Estadístico de Dispersión (Box Plot)"):
                fig_box = px.box(
                    df_global_grafica, x="Tipo_Energía", y=eje_y_global, color="Tipo_Energía",
                    points="all", title=f"Distribución Estadística de {eje_y_global}"
                )
                st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("💡 Asegúrate de registrar números en indicadores con el mismo nombre en varias energías para habilitar la comparativa global.")
