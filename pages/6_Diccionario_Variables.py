import streamlit as st
import google_connector as gc
import pandas as pd

st.set_page_config(page_title="Glosario Institucional", page_icon="📖", layout="wide")
SPREADSHEET_ID = "1YLwfQE1u_4d8UNoDG8eC1ysb2QEApxqtwoKTBGNUW6g"
HOJA_DICCIONARIO = "Config_Diccionario"

# 1. Verificar Seguridad
if "logeado" not in st.session_state or not st.session_state["logeado"]:
    st.warning("🔒 Por favor, inicia sesión en la página principal (Home).")
    st.stop()

st.title("📖 Diccionario Central de Variables")
st.markdown("Define y estandariza las instrucciones para cada indicador. Esto asegurará la calidad de los datos ingresados por otras instituciones.")

pestanas = gc.get_all_sheet_names(SPREADSHEET_ID)

# --- 2. CONFIGURACIÓN INVISIBLE DE LA HOJA MAESTRA ---
if HOJA_DICCIONARIO not in pestanas:
    with st.spinner("Creando matriz central de configuraciones..."):
        gc.create_new_sheet(SPREADSHEET_ID, HOJA_DICCIONARIO)
        df_init = pd.DataFrame(columns=["Energía", "Indicador", "Descripción"])
        gc.update_all_data(SPREADSHEET_ID, HOJA_DICCIONARIO, df_init, ["Energía", "Indicador", "Descripción"])
        st.success("✅ Motor de Diccionario inicializado correctamente.")
        st.rerun()

# Filtramos para que el diccionario no se audite a sí mismo
energias_reales = [p for p in pestanas if p != HOJA_DICCIONARIO]

if not energias_reales:
    st.info("Aún no hay energías creadas en la base de datos.")
    st.stop()

col_izq, col_der = st.columns([1, 1.5])

# --- 3. PANEL DE ADMINISTRACIÓN (IZQUIERDA) ---
with col_izq:
    st.markdown("### ✍️ Registrar Instrucción")
    
    energia_seleccionada = st.selectbox("⚡ 1. Selecciona la Matriz:", energias_reales)
    
    # Leemos las columnas reales de esa energía
    columnas_brutas = gc.get_columnas(SPREADSHEET_ID, energia_seleccionada)
    cols_sistema = ["Usuario", "Última_Modificación", "Última_Modificacion", ""]
    indicadores_limpios = [str(c).strip().title() for c in columnas_brutas if str(c).strip().title() not in cols_sistema]
    
    if not indicadores_limpios:
        st.warning("Esta energía no tiene indicadores configurados.")
    else:
        indicador_seleccionado = st.selectbox("📌 2. Selecciona el Indicador:", indicadores_limpios)
        
        # Leemos el diccionario actual para ver si este indicador ya tiene una descripción y mostrarla
        datos_diccionario = gc.get_all_records(SPREADSHEET_ID, HOJA_DICCIONARIO)
        df_dicc = pd.DataFrame(datos_diccionario)
        
        descripcion_actual = ""
        if not df_dicc.empty:
            # Filtramos buscando si ya existe
            filtro = (df_dicc["Energía"] == energia_seleccionada) & (df_dicc["Indicador"] == indicador_seleccionado)
            if filtro.any():
                descripcion_actual = str(df_dicc.loc[filtro, "Descripción"].values[0])
                
        # Área de texto para la instrucción
        nueva_descripcion = st.text_area(
            "📝 3. Escribe la definición o instrucción (Ej: 'Ingresar valor en Megavatios MW'):",
            value=descripcion_actual,
            height=150
        )
        
        if st.button("💾 Guardar en el Glosario"):
            with st.spinner("Sincronizando diccionario..."):
                if df_dicc.empty:
                    df_dicc = pd.DataFrame(columns=["Energía", "Indicador", "Descripción"])
                
                # Buscamos de nuevo por si acaso
                filtro = (df_dicc["Energía"] == energia_seleccionada) & (df_dicc["Indicador"] == indicador_seleccionado)
                
                if filtro.any():
                    # Si existe, actualizamos
                    idx = df_dicc.index[filtro].tolist()[0]
                    df_dicc.at[idx, "Descripción"] = nueva_descripcion
                else:
                    # Si no existe, agregamos fila nueva
                    nueva_fila = pd.DataFrame([{
                        "Energía": energia_seleccionada, 
                        "Indicador": indicador_seleccionado, 
                        "Descripción": nueva_descripcion
                    }])
                    df_dicc = pd.concat([df_dicc, nueva_fila], ignore_index=True)
                
                # Sincronizamos con Google Sheets
                if gc.update_all_data(SPREADSHEET_ID, HOJA_DICCIONARIO, df_dicc.astype(str), ["Energía", "Indicador", "Descripción"]):
                    st.success("✅ ¡Instrucción guardada exitosamente!")
                    st.rerun()

# --- 4. VISUALIZADOR DEL DICCIONARIO (DERECHA) ---
with col_der:
    st.markdown(f"### 📖 Glosario Actual: {energia_seleccionada.replace('Proyectos_', '')}")
    
    if not df_dicc.empty:
        # Mostramos solo las descripciones de la energía que el usuario está viendo
        df_vista = df_dicc[df_dicc["Energía"] == energia_seleccionada][["Indicador", "Descripción"]]
        
        if df_vista.empty:
            st.info("Aún no has registrado definiciones para esta energía.")
        else:
            st.dataframe(df_vista, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.info("💡 **Consejo:** Estos textos son los que guiarán a los investigadores para evitar que suban datos erróneos en la base de datos.")
    else:
        st.info("El diccionario central está vacío.")