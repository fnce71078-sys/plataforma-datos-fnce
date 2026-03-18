import streamlit as st
import google_connector as gc
import pandas as pd
import io

st.set_page_config(page_title="Exportación y Formato", page_icon="✨", layout="wide")
SPREADSHEET_ID = "1YLwfQE1u_4d8UNoDG8eC1ysb2QEApxqtwoKTBGNUW6g"

# 1. Verificar Seguridad
if "logeado" not in st.session_state or not st.session_state["logeado"]:
    st.warning("🔒 Por favor, inicia sesión en la página principal (Home).")
    st.stop()

st.title("✨ Exportación y Formato de Datos")
st.markdown("Revisa el estado final de las matrices, aplica formato profesional en Google Sheets y descarga los consolidados.")

pestanas = gc.get_all_sheet_names(SPREADSHEET_ID)
# Excluimos el diccionario para no exportarlo como si fuera una energía
energias_reales = [p for p in pestanas if p != "Config_Diccionario"]

if not energias_reales:
    st.info("Aún no hay energías creadas.")
    st.stop()

# --- 1. SELECCIÓN ---
energia_seleccionada = st.selectbox("⚡ Selecciona la matriz a finalizar:", energias_reales)

with st.spinner("Cargando datos..."):
    datos = gc.get_all_records(SPREADSHEET_ID, energia_seleccionada)

if not datos:
    st.warning("Esta matriz no tiene proyectos registrados para exportar.")
    st.stop()

df_export = pd.DataFrame(datos)

# --- 2. VISTA PREVIA ---
st.markdown(f"### 👁️ Vista Previa: {energia_seleccionada.replace('Proyectos_', '')}")
st.write(f"Total de proyectos listos: **{len(df_export)}**")
st.dataframe(df_export, use_container_width=True)

st.markdown("---")

col_izq, col_der = st.columns(2)

# --- 3. FORMATO EN LA NUBE (GOOGLE SHEETS) ---
with col_izq:
    st.markdown("### 🎨 Estética en Google Sheets")
    st.write("Aplica colores institucionales, congela la barra superior y ajusta las columnas en el archivo original de la nube.")
    
    if st.button("✨ Dar Formato Profesional a la Hoja"):
        with st.spinner("Aplicando diseño en Google Sheets..."):
            exito = gc.format_sheet_professional(SPREADSHEET_ID, energia_seleccionada)
            if exito:
                st.success("✅ ¡Formato aplicado con éxito! Si abres tu Google Sheets, verás la tabla perfectamente organizada.")
                st.balloons()
            else:
                st.error("❌ Hubo un error al intentar aplicar el formato.")

# --- 4. EXPORTACIÓN LOCAL ---
with col_der:
    st.markdown("### 📥 Descarga Local")
    st.write("Obtén una copia física de la base de datos terminada para enviarla a los ingenieros de software o a la ANH.")
    
    col_btn1, col_btn2 = st.columns(2)
    
    # --- NUEVA MAGIA PARA EXCEL PROFESIONAL ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        
        # Nombre de la hoja (Excel solo permite máximo 31 caracteres en el nombre de una pestaña)
        nombre_hoja = energia_seleccionada[:31]
        
        # Escribimos los datos empezando en la fila 2 para dejarle el control de los títulos a Excel
        df_export.to_excel(writer, index=False, sheet_name=nombre_hoja, startrow=1, header=False)
        
        workbook = writer.book
        worksheet = writer.sheets[nombre_hoja]
        (max_row, max_col) = df_export.shape
        
        # Configuramos los encabezados oficiales para la tabla
        column_settings = [{'header': str(column)} for column in df_export.columns] 
        
        # Si hay datos, creamos la tabla formal dinámica
        if max_row > 0:
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': column_settings,
                'style': 'Table Style Medium 9' # Estilo azul corporativo con filas intercaladas
            })
            
            # Ajustamos el ancho de cada columna automáticamente al contenido
            for i, col in enumerate(df_export.columns):
                ancho = max(df_export[col].astype(str).map(len).max(), len(str(col))) + 4
                worksheet.set_column(i, i, ancho)
        else:
            # Si está vacío por alguna razón, solo ponemos los encabezados normales
            df_export.to_excel(writer, index=False, sheet_name=nombre_hoja)

    with col_btn1:
        st.download_button(
            label="📊 Descargar en Excel",
            data=buffer.getvalue(),
            file_name=f"Consolidado_{energia_seleccionada}.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )
        
    # Botón CSV (Se mantiene texto plano ideal para migraciones de bases de datos)
    csv_data = df_export.to_csv(index=False).encode('utf-8')
    with col_btn2:
        st.download_button(
            label="📝 Descargar en CSV",
            data=csv_data,
            file_name=f"Consolidado_{energia_seleccionada}.csv",
            mime="text/csv",
            use_container_width=True
        )