import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# --- CONEXIÓN PRINCIPAL ---
@st.cache_resource(ttl=600) # Refresca la conexión cada 10 min
def init_connection():
    credentials_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    service = build('sheets', 'v4', credentials=creds)
    return client, service

def get_worksheet(spreadsheet_id, worksheet_name):
    client, _ = init_connection()
    sheet = client.open_by_key(spreadsheet_id)
    return sheet.worksheet(worksheet_name)

# --- FUNCIONES DE LECTURA (CON MEMORIA CACHÉ) ---
@st.cache_data(ttl=30, show_spinner=False)
def get_columnas(spreadsheet_id, worksheet_name):
    try:
        ws = get_worksheet(spreadsheet_id, worksheet_name)
        return ws.row_values(1)
    except Exception:
        return []

@st.cache_data(ttl=30, show_spinner=False)
def get_all_records(spreadsheet_id, worksheet_name):
    try:
        ws = get_worksheet(spreadsheet_id, worksheet_name)
        return ws.get_all_records()
    except Exception as e:
        return []

@st.cache_data(ttl=30, show_spinner=False)
def get_all_sheet_names(spreadsheet_id):
    client, _ = init_connection()
    try:
        sheet = client.open_by_key(spreadsheet_id)
        return [ws.title for ws in sheet.worksheets()]
    except Exception:
        return []

# --- FUNCIONES DE ESCRITURA (LIMPIAN LA MEMORIA AL GUARDAR) ---
def insert_row(spreadsheet_id, worksheet_name, row_data):
    try:
        ws = get_worksheet(spreadsheet_id, worksheet_name)
        ws.append_row(row_data)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def update_all_data(spreadsheet_id, worksheet_name, dataframe, headers_originales):
    client, _ = init_connection()
    try:
        sheet = client.open_by_key(spreadsheet_id)
        ws = sheet.worksheet(worksheet_name)
        dataframe = dataframe.fillna("")
        datos_completos = [headers_originales] + dataframe.values.tolist()
        ws.clear()
        ws.update(datos_completos)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al sincronizar: {e}")
        return False

# --- FUNCIONES DE ESTRUCTURA Y PANEL MAESTRO ---
def add_column_with_batch(spreadsheet_id, worksheet_name, new_column_name):
    client, service = init_connection()
    try:
        sheet = client.open_by_key(spreadsheet_id)
        ws = sheet.worksheet(worksheet_name)
        sheet_id = ws.id
        headers = ws.row_values(1)
        next_col_index = len(headers) 
        
        requests = [{"updateCells": {"rows": [{"values": [{"userEnteredValue": {"stringValue": new_column_name}}]}],"fields": "userEnteredValue","start": {"sheetId": sheet_id,"rowIndex": 0, "columnIndex": next_col_index}}}]
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()
        st.cache_data.clear()
        return True
    except Exception:
        return False

def create_new_sheet(spreadsheet_id, sheet_title):
    client, _ = init_connection()
    try:
        sheet = client.open_by_key(spreadsheet_id)
        sheet.add_worksheet(title=sheet_title, rows=100, cols=20)
        st.cache_data.clear()
        return True
    except Exception:
        return False

def rename_sheet(spreadsheet_id, old_name, new_name):
    client, _ = init_connection()
    try:
        sheet = client.open_by_key(spreadsheet_id)
        ws = sheet.worksheet(old_name)
        nombre_limpio = new_name.strip().replace(' ', '_')
        if not nombre_limpio.startswith("Proyectos_"):
             nombre_limpio = f"Proyectos_{nombre_limpio}"
        ws.update_title(nombre_limpio)
        st.cache_data.clear()
        return True
    except Exception:
        return False

def delete_sheet(spreadsheet_id, sheet_name):
    client, _ = init_connection()
    try:
        sheet = client.open_by_key(spreadsheet_id)
        ws = sheet.worksheet(sheet_name)
        sheet.del_worksheet(ws)
        st.cache_data.clear()
        return True
    except Exception:
        return False

def rename_column(spreadsheet_id, worksheet_name, old_col_name, new_col_name):
    client, _ = init_connection()
    try:
        sheet = client.open_by_key(spreadsheet_id)
        ws = sheet.worksheet(worksheet_name)
        headers = ws.row_values(1)
        col_index = headers.index(old_col_name) + 1 
        ws.update_cell(1, col_index, new_col_name.strip())
        st.cache_data.clear()
        return True
    except Exception:
        return False

def delete_column(spreadsheet_id, worksheet_name, col_name):
    client, service = init_connection()
    try:
        sheet = client.open_by_key(spreadsheet_id)
        ws = sheet.worksheet(worksheet_name)
        headers = ws.row_values(1)
        col_index = headers.index(col_name)
        sheet_id = ws.id
        requests = [{"deleteDimension": {"range": {"sheetId": sheet_id,"dimension": "COLUMNS","startIndex": col_index,"endIndex": col_index + 1}}}]
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()
        st.cache_data.clear()
        return True
    except Exception:
        return False

# --- FUNCIÓN DE DISEÑO PROFESIONAL (ACTUALIZADA 3.0) ---
def format_sheet_professional(spreadsheet_id, worksheet_name):
    client, service = init_connection()
    try:
        sheet = client.open_by_key(spreadsheet_id)
        ws = sheet.worksheet(worksheet_name)
        sheet_id = ws.id
        
        # 1. Calculamos inteligentemente el tamaño exacto de la tabla
        encabezados = ws.row_values(1)
        max_cols = len(encabezados)
        col_a = ws.col_values(1)
        max_rows = len(col_a)

        requests = [
            # Congelar la primera fila
            {"updateSheetProperties": {"properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            
            # Pintar los encabezados (Azul institucional)
            {"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": max_cols}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.1, "green": 0.2, "blue": 0.4}, "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"}},
            
            # Centrar y organizar todos los datos nuevos que ingresaste por la app
            {"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": max_rows, "startColumnIndex": 0, "endColumnIndex": max_cols}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}}, "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)"}},
            
            # Dibujar la cuadrícula (Líneas NEGRAS sólidas para seccionar la tabla por completo)
            {"updateBorders": {"range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": max_rows, "startColumnIndex": 0, "endColumnIndex": max_cols}, "top": {"style": "SOLID", "color": {"red": 0.0, "green": 0.0, "blue": 0.0}}, "bottom": {"style": "SOLID", "color": {"red": 0.0, "green": 0.0, "blue": 0.0}}, "left": {"style": "SOLID", "color": {"red": 0.0, "green": 0.0, "blue": 0.0}}, "right": {"style": "SOLID", "color": {"red": 0.0, "green": 0.0, "blue": 0.0}}, "innerHorizontal": {"style": "SOLID", "color": {"red": 0.0, "green": 0.0, "blue": 0.0}}, "innerVertical": {"style": "SOLID", "color": {"red": 0.0, "green": 0.0, "blue": 0.0}}}},
            
            # Ajustar el ancho de las columnas a la medida del texto
            {"autoResizeDimensions": {"dimensions": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": max_cols}}}
        ]
        
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()
        return True
    except Exception as e:
        print(f"Error de formato: {e}")
        return False
