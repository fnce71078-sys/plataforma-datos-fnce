import streamlit as st
import google_connector as gc
import os

# 1. Configuración de la página
st.set_page_config(
    page_title="Matriz Transición Energética",
    page_icon="⚡",
    layout="wide"
)

# --- ¡IMPORTANTE! ---
SPREADSHEET_ID = "1YLwfQE1u_4d8UNoDG8eC1ysb2QEApxqtwoKTBGNUW6g"

# 2. Función para cargar los logos en el menú lateral
def cargar_logos():
    st.sidebar.markdown("### Instituciones Aliadas")
    logos = ["anh.png", "upb.png", "usta.png", "minciencia.png", "unal.png", "udem.png"]
    col1, col2 = st.sidebar.columns(2)
    for i, logo in enumerate(logos):
        ruta = os.path.join("assets", logo)
        if os.path.exists(ruta):
            if i % 2 == 0:
                col1.image(ruta, use_container_width=True)
            else:
                col2.image(ruta, use_container_width=True)

# 3. Sistema de Autenticación (Login)
def verificar_login():
    if "logeado" not in st.session_state:
        st.session_state["logeado"] = False

    if not st.session_state["logeado"]:
        st.title("🔐 Acceso al Sistema")
        st.markdown("Plataforma de Matriz de Indicadores de Viabilidad de Proyectos.")
        
        with st.form("formulario_login"):
            usuario_ingresado = st.text_input("Usuario")
            password_ingresado = st.text_input("Contraseña", type="password")
            boton_entrar = st.form_submit_button("Ingresar")

            if boton_entrar:
                try:
                    pass_admin_archivo = st.secrets["accesos"]["clave_maestra"]
                    pass_user_archivo = st.secrets["accesos"]["clave_invitado"]

                    if usuario_ingresado == "admin" and password_ingresado == pass_admin_archivo:
                        st.session_state["logeado"] = True
                        st.session_state["rol"] = "admin"
                        st.rerun()
                    elif usuario_ingresado == "usuario" and password_ingresado == pass_user_archivo:
                        st.session_state["logeado"] = True
                        st.session_state["rol"] = "usuario"
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas. Revisa mayúsculas y minúsculas.")
                except KeyError as e:
                    st.error(f"❌ Error de configuración en secretos: {e}")
        
        st.stop()

# --- EJECUCIÓN PRINCIPAL ---
verificar_login()
cargar_logos()

# --- NUEVA ESTRUCTURA CON PESTAÑAS (TABS) ---
st.title("🌱 Matriz de Viabilidad - Proyectos FNCE")

# Creamos las pestañas. Si es admin, ve ambas. Si es usuario, solo ve la presentación.
if st.session_state["rol"] == "admin":
    tab_intro, tab_admin = st.tabs(["📖 Presentación del Proyecto", "⚙️ Panel de Administración"])
else:
    tab_intro, = st.tabs(["📖 Presentación del Proyecto"])
    tab_admin = None

# --- PESTAÑA 1: PRESENTACIÓN (La ven todos) ---
with tab_intro:
    st.markdown("### Sistema de Registro y Evaluación de Energías")
    st.write("""
    Esta plataforma web está diseñada para centralizar la **Matriz de Indicadores de Viabilidad** de proyectos enfocados en **Fuentes No Convencionales de Energía (FNCE)**.
    
    Su objetivo principal es permitir el ingreso estructurado, almacenamiento y análisis de los 
    datos técnicos, financieros y ambientales de diversas energías, asegurando una base de datos 
    estandarizada para la toma de decisiones.
    """)
    
    st.markdown("---")
    st.markdown("#### 🏛️ Instituciones Aliadas")
    st.write("Este proyecto es un esfuerzo interinstitucional respaldado por:")
    
    # Lista de instituciones
    col_inst1, col_inst2 = st.columns(2)
    with col_inst1:
        st.markdown("- **ANH** (Agencia Nacional de Hidrocarburos)")
        st.markdown("- **USTA** (Universidad Santo Tomás)")
        st.markdown("- **UPB** (Universidad Pontificia Bolivariana)")
    with col_inst2:
        st.markdown("- **MINISTERIO DE CIENCIA**")
        st.markdown("- **UNAL** (Universidad Nacional de Colombia)")
        st.markdown("- **Universidad de Medellín**")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 **Instrucción:** Utiliza el menú lateral izquierdo para navegar a la sección de 'Ingreso Datos' y registrar un nuevo proyecto.")

# --- PESTAÑA 2: ADMINISTRACIÓN (Solo la ve el Admin) ---
if tab_admin is not None:
    with tab_admin:
        st.write(f"Bienvenido, **{st.session_state['rol'].capitalize()}**. Aquí controlas la estructura maestra de la base de datos.")
        
        pestanas_actuales = gc.get_all_sheet_names(SPREADSHEET_ID)
        
        # --- SECCIÓN 1: ENERGÍAS ---
        st.markdown("### ⚡ 1. Gestión de Energías (Pestañas)")
        col_e1, col_e2, col_e3 = st.columns(3)

        with col_e1:
            st.info("➕ Crear Energía")
            nueva_energia = st.text_input("Nombre (Ej: Geotérmica):")
            if st.button("Crear", key="btn_crear_e"):
                if nueva_energia:
                    nombre_formateado = f"Proyectos_{nueva_energia.strip().replace(' ', '_')}"
                    if nombre_formateado in pestanas_actuales:
                        st.warning("⚠️ Esta energía ya existe.")
                    else:
                        if gc.create_new_sheet(SPREADSHEET_ID, nombre_formateado):
                            st.success(f"✅ Pestaña '{nombre_formateado}' creada con éxito.")
                            st.rerun()
                else:
                    st.warning("Escribe un nombre.")

        with col_e2:
            st.warning("✏️ Renombrar Energía")
            if pestanas_actuales:
                energia_ren = st.selectbox("Selecciona:", pestanas_actuales, key="sel_ren_e")
                nuevo_nombre_e = st.text_input("Nuevo nombre (Ej: Solar):")
                if st.button("Renombrar", key="btn_ren_e"):
                    if nuevo_nombre_e:
                        if gc.rename_sheet(SPREADSHEET_ID, energia_ren, nuevo_nombre_e):
                            st.success("✅ Energía renombrada.")
                            st.rerun()
                    else:
                        st.warning("Escribe el nuevo nombre.")

        with col_e3:
            st.error("🗑️ Eliminar Energía")
            if pestanas_actuales:
                energia_del = st.selectbox("Selecciona:", pestanas_actuales, key="sel_del_e")
                if st.button("Eliminar", key="btn_del_e"):
                    if gc.delete_sheet(SPREADSHEET_ID, energia_del):
                        st.success("✅ Energía eliminada.")
                        st.rerun()

        st.markdown("---")
        
        # --- SECCIÓN 2: INDICADORES ---
        st.markdown("### 📊 2. Gestión de Indicadores (Columnas)")
        if not pestanas_actuales:
            st.info("Crea al menos una energía arriba para poder gestionar sus indicadores.")
        else:
            energia_seleccionada = st.selectbox("Selecciona la matriz a editar:", pestanas_actuales)
            
            # --- NUEVO: LECTURA DINÁMICA DE COLUMNAS ---
            try:
                ws = gc.get_worksheet(SPREADSHEET_ID, energia_seleccionada)
                columnas_actuales = ws.row_values(1)
            except Exception:
                columnas_actuales = []
            
            col_i1, col_i2, col_i3 = st.columns(3)
            
            with col_i1:
                st.info("➕ Agregar Indicador")
                nueva_col = st.text_input("Nombre del indicador:")
                if st.button("Agregar", key="btn_add_i"):
                    if nueva_col:
                        if gc.add_column_with_batch(SPREADSHEET_ID, energia_seleccionada, nueva_col.strip()):
                            st.success(f"✅ Columna '{nueva_col}' agregada.")
                            st.rerun()
                    else:
                        st.warning("Escribe el nombre.")

            with col_i2:
                st.warning("✏️ Renombrar Indicador")
                if columnas_actuales:
                    col_vieja = st.selectbox("Selecciona el indicador a renombrar:", columnas_actuales, key="sel_ren_i")
                    col_nueva = st.text_input("Nuevo nombre:")
                    if st.button("Renombrar", key="btn_ren_i"):
                        if col_nueva:
                            if gc.rename_column(SPREADSHEET_ID, energia_seleccionada, col_vieja, col_nueva):
                                st.success(f"✅ '{col_vieja}' cambió a '{col_nueva}'.")
                                st.rerun()
                        else:
                            st.warning("Escribe el nuevo nombre.")
                else:
                    st.info("No hay columnas creadas en esta matriz.")

            with col_i3:
                st.error("🗑️ Eliminar Indicador")
                if columnas_actuales:
                    col_a_borrar = st.selectbox("Selecciona el indicador a borrar:", columnas_actuales, key="sel_del_i")
                    if st.button("Eliminar", key="btn_del_i"):
                        if gc.delete_column(SPREADSHEET_ID, energia_seleccionada, col_a_borrar):
                            st.success(f"✅ Columna '{col_a_borrar}' eliminada.")
                            st.rerun()
                else:
                    st.info("No hay columnas creadas en esta matriz.")