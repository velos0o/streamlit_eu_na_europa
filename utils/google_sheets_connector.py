import streamlit as st
import gspread
from utils.secrets_helper import get_google_credentials
from utils.dataframe_utils import ensure_pandas_df

@st.cache_resource
def get_google_sheets_client():
    """Retorna um cliente gspread autenticado."""
    try:
        credentials = get_google_credentials()
        if credentials is None:
            st.error("Não foi possível obter as credenciais do Google a partir do secrets_helper.")
            return None
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets ({type(e).__name__}): {e}")
        print(f"[ERROR] Falha em get_google_sheets_client: {type(e).__name__} - {e}")
        return None

@st.cache_data
def fetch_data_from_sheet(_client, spreadsheet_url, sheet_name=None, gid=None):
    """Busca dados de uma planilha específica, com prioridade para o GID."""
    if not _client:
        print("[WARN] fetch_data_from_sheet chamado sem um cliente gspread válido.")
        return None
    try:
        spreadsheet = _client.open_by_url(spreadsheet_url)
        sheet = None

        if gid is not None:
            try:
                gid = int(gid)
                print(f"[INFO] Tentando abrir a planilha '{spreadsheet_url}' pelo GID {gid}.")
                sheet = spreadsheet.get_worksheet_by_id(gid)
                print(f"[INFO] Aba com GID {gid} aberta com sucesso. Nome da aba: '{sheet.title}'")
            except Exception as e_gid:
                print(f"[WARN] Falha ao abrir planilha pelo GID {gid}: {e_gid}. Tentando outras opções.")
        
        if sheet is None and sheet_name is not None:
            try:
                print(f"[INFO] Tentando abrir a aba pelo nome '{sheet_name}'.")
                sheet = spreadsheet.worksheet(sheet_name)
                print(f"[INFO] Aba '{sheet_name}' aberta com sucesso pelo nome.")
            except gspread.exceptions.WorksheetNotFound:
                print(f"[WARN] Aba com nome '{sheet_name}' não encontrada. Tentando a primeira aba.")
                pass # Continua para tentar a primeira aba

        if sheet is None:
            try:
                print("[INFO] Tentando abrir a primeira aba (índice 0).")
                sheet = spreadsheet.get_worksheet(0)
                print(f"[INFO] Primeira aba aberta com sucesso. Nome: '{sheet.title}'")
            except Exception as e_first:
                st.error(f"Não foi possível abrir a aba pelo GID, nome ou como primeira aba. Erro: {e_first}")
                print(f"[ERROR] Falha total ao tentar abrir uma aba em '{spreadsheet_url}': {e_first}")
                return None

        data = sheet.get_all_records()
        return data
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Planilha não encontrada: {spreadsheet_url}")
        print(f"[ERROR] SpreadsheetNotFound: {spreadsheet_url}")
        return None
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Aba '{sheet_name or 'especificada'}' não encontrada na planilha.")
        print(f"[ERROR] WorksheetNotFound: Aba '{sheet_name or 'especificada'}' não encontrada em {spreadsheet_url}")
        return None
    except gspread.exceptions.APIError as api_e:
        st.error(f"Erro na API do Google Sheets ao acessar a planilha: {api_e}")
        print(f"[ERROR] APIError: {type(api_e).__name__} - {api_e} ao acessar '{spreadsheet_url}'")
        return None
    except Exception as e:
        st.error(f"Erro ao buscar dados da planilha ({type(e).__name__}): {e}")
        print(f"[ERROR] Falha em fetch_data_from_sheet: {type(e).__name__} - {e} para '{spreadsheet_url}'")
        return None

# Exemplo de como usar (remover ou comentar em produção)
# if __name__ == '__main__':
#     st.info("Tentando conectar ao Google Sheets para teste...")
#     client = get_google_sheets_client()
#     if client:
#         st.success("Cliente Google Sheets obtido com sucesso!")
#         SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/15L7SdGgbF3nhiE3ptk7WFmuTwbxSY3rA1hfCnYmMFMM/edit#gid=170972868'
#         GID = 170972868 # GID da aba de produtividade
#         st.write(f"Buscando dados da planilha com GID: {GID}")
#         data = fetch_data_from_sheet(client, SPREADSHEET_URL, gid=GID)
#         if data:
#             st.dataframe(data)
#         else:
#             st.warning("Não foram retornados dados da planilha.")
#     else:
#         st.error("Falha ao obter cliente Google Sheets para teste.") 