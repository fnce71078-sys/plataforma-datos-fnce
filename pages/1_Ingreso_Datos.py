import streamlit as st
import google_connector as gc
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gestión de Proyectos", page_icon="📝", layout="wide")
SPREADSHEET_ID = "1YLwfQE1u_4d8UNoDG8eC1ysb2QEApxqtwoKTBGNUW6g"

if "logeado" not in st.session_state or not st.session_state["logeado"]:
    st.warning("🔒 Por favor, inicia sesión en la página principal (Home).")
    st.stop()

st.title("📝 Gestión de Proyectos FNCE")
pestanas = gc.get_all_sheet_names(SPREADSHEET_ID)

if not pestanas:
    st.info("Aún no hay energías creadas. Ve al 'Panel de Administración' en el Home.")
    st.stop()

energia_seleccionada = st.selectbox("⚡ Selecciona la matriz de energía a gestionar:", pestanas)
tab_ingreso, tab_vista = st.tabs(["➕ Registrar Nuevo Proyecto", "📊 Base de Datos Activa (Editar/Eliminar)"])

# Usamos la nueva función con memoria caché
columnas_brutas = gc.get_columnas(SPREADSHEET_ID, energia_seleccionada)

columnas_fijas = ["Usuario", "Última_Modificación"]

if columnas_brutas: 
    for col_fija in columnas_fijas:
        if col_fija not in columnas_brutas:
            gc.add_column_with_batch(SPREADSHEET_ID, energia_seleccionada, col_fija)
            columnas_brutas.append(col_fija)

cols_normales = [c for c in columnas_brutas if c not in columnas_fijas]
columnas_ordenadas = cols_normales + columnas_fijas

with tab_ingreso:
    st.subheader(f"Formulario de {energia_seleccionada.replace('Proyectos_', '')}")
    cols_formulario = [c for c in columnas_ordenadas if c != "Última_Modificación"]

    if not cols_normales:
        st.warning("⚠️ Esta energía no tiene indicadores creados aún.")
    else:
        with st.form("form_nuevo_proyecto", clear_on_submit=True):
            valores_ingresados = {}
            for col in cols_formulario:
                valores_ingresados[col] = st.text_input(f"{col}:")
            
            if st.form_submit_button("Guardar Proyecto"):
                fila_a_insertar = []
                fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for col in columnas_ordenadas:
                    if col == "Última_Modificación":
                        fila_a_insertar.append(fecha_ahora)
                    else:
                        fila_a_insertar.append(valores_ingresados.get(col, ""))
                
                datos_actuales = gc.get_all_records(SPREADSHEET_ID, energia_seleccionada)
                df_temp = pd.DataFrame(datos_actuales)
                if df_temp.empty:
                    df_temp = pd.DataFrame(columns=columnas_ordenadas)
                else:
                    for c in columnas_ordenadas:
                        if c not in df_temp.columns: df_temp[c] = ""
                            
                nueva_fila_dict = {col: fila_a_insertar[i] for i, col in enumerate(columnas_ordenadas)}
                df_temp = pd.concat([df_temp, pd.DataFrame([nueva_fila_dict])], ignore_index=True)
                df_temp = df_temp[columnas_ordenadas]
                
                if gc.update_all_data(SPREADSHEET_ID, energia_seleccionada, df_temp, columnas_ordenadas):
                    st.success("✅ Proyecto registrado exitosamente.")
                    st.rerun()

with tab_vista:
    st.subheader("Registros Actuales")
    datos = gc.get_all_records(SPREADSHEET_ID, energia_seleccionada)
    if datos:
        df = pd.DataFrame(datos)
        for c in columnas_ordenadas:
            if c not in df.columns: df[c] = ""
        df = df[columnas_ordenadas]
        
        df_para_editar = df.astype(str)
        df_original_str = df_para_editar.copy()
        
        df_editado = st.data_editor(
            df_para_editar, num_rows="dynamic", use_container_width=True,
            disabled=["Última_Modificación"], key="tabla_editor"
        )
        
        if st.button("💾 Guardar Cambios de la Tabla"):
            df_editado_str = df_editado.astype(str)
            cols_a_comparar = [c for c in columnas_ordenadas if c != "Última_Modificación"]
            
            for i in df_editado_str.index:
                necesita_actualizar_fecha = False
                if i in df_original_str.index:
                    if list(df_original_str.loc[i, cols_a_comparar]) != list(df_editado_str.loc[i, cols_a_comparar]):
                        necesita_actualizar_fecha = True
                else: necesita_actualizar_fecha = True
                if necesita_actualizar_fecha:
                    df_editado_str.at[i, "Última_Modificación"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            df_editado_str = df_editado_str[columnas_ordenadas]
            if gc.update_all_data(SPREADSHEET_ID, energia_seleccionada, df_editado_str, columnas_ordenadas):
                st.success("✅ Base de datos sincronizada.")
                st.rerun()
    else:
        st.write("Aún no hay proyectos registrados en esta matriz.")