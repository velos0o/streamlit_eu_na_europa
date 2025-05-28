import streamlit as st
import gspread
from utils.secrets_helper import get_google_credentials

@st.cache_resource(ttl=3600)
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

@st.cache_data(ttl=300)
def fetch_data_from_sheet(_client, spreadsheet_url, sheet_name):
    """Busca dados de uma planilha específica, tentando pelo GID 0 primeiro."""
    if not _client:
        print("[WARN] fetch_data_from_sheet chamado sem um cliente gspread válido.")
        return None
    try:
        spreadsheet = _client.open_by_url(spreadsheet_url)
        # Tentar abrir pela GID 0 (primeira aba)
        try:
            print(f"[INFO] Tentando abrir a planilha '{spreadsheet_url}' pela GID 0 (índice 0).")
            sheet = spreadsheet.get_worksheet(0) # 0 para a primeira aba (gid=0)
            print(f"[INFO] Aba com índice 0 aberta com sucesso. Nome real da aba: '{sheet.title}'")
        except Exception as e_gid:
            print(f"[WARN] Falha ao abrir planilha pelo índice 0 (GID 0): {e_gid}. Tentando pelo nome '{sheet_name}'.")
            # Fallback: tentar abrir pelo nome fornecido se pelo GID falhar
            sheet = spreadsheet.worksheet(sheet_name)
            print(f"[INFO] Aba '{sheet_name}' aberta com sucesso pelo nome.")
            
        data = sheet.get_all_records() # Retorna uma lista de dicionários
        return data
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Planilha não encontrada: {spreadsheet_url}")
        print(f"[ERROR] SpreadsheetNotFound: {spreadsheet_url}")
        return None
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Aba '{sheet_name}' não encontrada na planilha.")
        print(f"[ERROR] WorksheetNotFound: Aba '{sheet_name}' não encontrada em {spreadsheet_url}")
        return None
    except gspread.exceptions.APIError as api_e:
        st.error(f"Erro na API do Google Sheets ao acessar '{sheet_name}': {api_e}")
        print(f"[ERROR] APIError: {type(api_e).__name__} - {api_e} ao acessar '{sheet_name}' em {spreadsheet_url}")
        return None
    except Exception as e:
        st.error(f"Erro ao buscar dados da planilha '{sheet_name}' ({type(e).__name__}): {e}")
        print(f"[ERROR] Falha em fetch_data_from_sheet: {type(e).__name__} - {e} para aba '{sheet_name}' em {spreadsheet_url}")
        return None

# Exemplo de como usar (remover ou comentar em produção)
# if __name__ == '__main__':
#     st.info("Tentando conectar ao Google Sheets para teste...")
#     client = get_google_sheets_client()
#     if client:
#         st.success("Cliente Google Sheets obtido com sucesso!")
#         SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1pB3HTFsaHyqAt3bhxzWG3RjfAxAzl97ydGqT35uYb-w/edit?gid=0#gid=0'
#         SHEET_NAME = 'Página1' # Substitua pelo nome correto da sua aba
#         st.write(f"Buscando dados da aba: {SHEET_NAME}")
#         data = fetch_data_from_sheet(client, SPREADSHEET_URL, SHEET_NAME)
#         if data:
#             st.dataframe(data)
#         else:
#             st.warning("Não foram retornados dados da planilha.")
#     else:
#         st.error("Falha ao obter cliente Google Sheets para teste.") 