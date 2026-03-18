import streamlit as st
import google_connector as gc
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Importador Masivo", page_icon="🚀", layout="wide")
SPREADSHEET_ID = "1YLwfQE1u_4d8UNoDG8eC1ysb2QEApxqtwoKTBGNUW6g"

# 1. Verificar Seguridad
if "logeado" not in st.session_state or not st.session_state["logeado"]:
    st.warning("🔒 Por favor, inicia sesión en la página principal (Home).")
    st.stop()

st.title("🚀 Importador Masivo de Proyectos")
st.markdown("Sube múltiples proyectos a la vez usando un archivo de Excel o CSV. El sistema validará los datos antes de guardarlos.")

pestanas = gc.get_all_sheet_names(SPREADSHEET_ID)

if not pestanas:
    st.info("Aún no hay energías creadas en la base de datos.")
    st.stop()

# --- 1. SELECCIÓN DE ENERGÍA ---
st.markdown("### Paso 1: Selecciona la Matriz Destino")
energia_seleccionada = st.selectbox("⚡ ¿A qué energía pertenecen los proyectos que vas a subir?", pestanas)

# Leer columnas actuales
columnas_brutas = gc.get_columnas(SPREADSHEET_ID, energia_seleccionada)
cols_sistema = ["Usuario", "Última_Modificación", "Última_Modificacion"]

# Columnas que el usuario realmente debe llenar (sin las de sistema)
cols_requeridas = [str(c).strip().title() for c in columnas_brutas if str(c).strip().title() not in cols_sistema and str(c).strip() != ""]

if not cols_requeridas:
    st.warning(f"⚠️ La matriz {energia_seleccionada} no tiene indicadores configurados. Ve al Panel Maestro a crearlos primero.")
    st.stop()

st.markdown("---")

# --- 2. DESCARGA DE PLANTILLA ---
st.markdown("### Paso 2: Descarga la Plantilla Oficial")
st.write("Para evitar errores, descarga este archivo, llénalo con tus proyectos y guárdalo.")

# Generamos un DataFrame vacío solo con los encabezados requeridos
df_plantilla = pd.DataFrame(columns=cols_requeridas)

# Convertimos a Excel en memoria para que lo puedan descargar
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_plantilla.to_excel(writer, index=False, sheet_name='Plantilla_FNCE')
    
st.download_button(
    label=f"📥 Descargar Plantilla Excel ({energia_seleccionada.replace('Proyectos_', '')})",
    data=buffer.getvalue(),
    file_name=f"Plantilla_{energia_seleccionada}.xlsx",
    mime="application/vnd.ms-excel"
)

st.markdown("---")

# --- 3. SUBIDA Y VALIDACIÓN DEL ARCHIVO ---
st.markdown("### Paso 3: Sube tus Datos")
st.info("💡 Asegúrate de no cambiar el nombre de las columnas en el archivo de Excel.")

archivo_subido = st.file_uploader("Arrastra aquí tu archivo lleno (.xlsx o .csv)", type=["xlsx", "csv"])

if archivo_subido is not None:
    try:
        # Leer el archivo dependiendo de su tipo
        if archivo_subido.name.endswith('.csv'):
            df_nuevo = pd.read_csv(archivo_subido)
        else:
            df_nuevo = pd.read_excel(archivo_subido)
            
        # Limpiar nombres de columnas del archivo subido
        df_nuevo.columns = df_nuevo.columns.str.strip().str.title()
        
        # Validar si las columnas coinciden exactamente
        columnas_archivo = list(df_nuevo.columns)
        
        # Revisamos si falta alguna columna requerida
        columnas_faltantes = [c for c in cols_requeridas if c not in columnas_archivo]
        
        if columnas_faltantes:
            st.error("❌ **Error de Formato:** Tu archivo no coincide con la estructura de la base de datos.")
            st.write("Te faltan estas columnas en tu archivo:")
            st.write(columnas_faltantes)
            st.stop()
            
        # Revisamos si el archivo está vacío
        if df_nuevo.empty:
            st.warning("⚠️ El archivo que subiste está vacío. No hay proyectos para importar.")
            st.stop()
            
        st.success(f"✅ Archivo válido. Se detectaron **{len(df_nuevo)}** proyectos listos para importar.")
        st.dataframe(df_nuevo, use_container_width=True)
        
        # --- 4. INYECCIÓN A LA BASE DE DATOS ---
        if st.button("💾 Confirmar e Importar a la Base de Datos"):
            with st.spinner("Sincronizando con la matriz central..."):
                
                # Le inyectamos los datos del sistema automáticamente
                fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                usuario_actual = st.session_state.get('rol', 'Usuario_Masivo')
                
                df_nuevo["Usuario"] = usuario_actual
                df_nuevo["Última_Modificación"] = fecha_ahora
                
                # Traemos los datos viejos para no borrarlos
                datos_actuales = gc.get_all_records(SPREADSHEET_ID, energia_seleccionada)
                df_actual = pd.DataFrame(datos_actuales)
                
                # Unificamos columnas para que peguen perfecto
                if not df_actual.empty:
                    df_actual.columns = df_actual.columns.str.strip().str.title()
                
                # Concatenamos (Pegamos los nuevos debajo de los viejos)
                df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
                
                # Aseguramos el orden final de las columnas
                todas_columnas_finales = cols_requeridas + ["Usuario", "Última_Modificación"]
                for c in todas_columnas_finales:
                    if c not in df_final.columns:
                        df_final[c] = ""
                
                df_final = df_final[todas_columnas_finales]
                
                # Subimos todo el bloque a Google Sheets usando nuestra función maestra
                if gc.update_all_data(SPREADSHEET_ID, energia_seleccionada, df_final.astype(str), todas_columnas_finales):
                    st.success(f"🎉 ¡Éxito! {len(df_nuevo)} proyectos fueron añadidos a {energia_seleccionada}.")
                    st.balloons() # Una pequeña animación de éxito
                    
    except Exception as e:
        st.error(f"❌ Ocurrió un error al leer el archivo: {e}")