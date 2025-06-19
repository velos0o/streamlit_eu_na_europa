import streamlit as st
import pandas as pd
import gspread

from .dados_macros import show_dados_macros
from .funil_etapas import show_funil_etapas
from .pendencias_liberadas import show_pendencias_liberadas
from .pendencias_futuras import show_pendencias_futuras
from .produtividade import show_produtividade

@st.cache_data(ttl=300)
def carregar_dados_protocolados():
    """
    Carrega dados da planilha Google Sheets de forma segura usando uma Conta de Serviço.
    """
    try:
        creds = st.secrets["google"]["sheets"]
        sa = gspread.service_account_from_dict(creds)
        sheet_id = "15L7SdGgbF3nhiE3ptk7WFmuTwbxSY3rA1hfCnYmMFMM"
        sh = sa.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)
        
        data = worksheet.get_all_values()
        if len(data) < 3:
            return pd.DataFrame()

        data_rows = data[2:]
        cleaned_rows = [row for row in data_rows if any(cell for cell in row)]

        if not cleaned_rows:
            st.warning("Nenhum dado válido encontrado após o cabeçalho.")
            return pd.DataFrame()
            
        df = pd.DataFrame(cleaned_rows)
        
        num_cols = len(df.columns)
        col_names = [chr(ord('A') + i) for i in range(num_cols)]
        df.columns = col_names[:num_cols]

        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Planilha não encontrada. Verifique o ID e se a conta de serviço tem permissão de 'Leitor'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha: {e}")
        return pd.DataFrame()

def show_protocolados(subpagina):
    st.header("Relatório de Protocolados", divider='rainbow')
    
    df_raw = carregar_dados_protocolados()
    
    if df_raw.empty:
        st.warning("Não foi possível carregar os dados ou a planilha está vazia.")
        return

    mapeamento_colunas = {
        'B': 'ID FAMÍLIA', 'C': 'CONSULTOR RESPONSÁVEL', 'D': 'STATUS GERAL', 'E': 'PENDENCIAS',
        'F': 'PROCURAÇÃO - STATUS', 'G': 'PROCURAÇÃO - ADM RESPONSAVEL', 'H': 'PROCURAÇÃO - DATA ENVIO', 'I': 'PROCURAÇÃO - DATA CONCLUSÃO',
        'J': 'ANALISE - RESPONSÁVEL', 'K': 'ANALISE - DATA DE ENVIO', 'L': 'ANALISE - STATUS', 'M': 'ANALISE - DATA CONCLUSÃO',
        'N': 'TRADUÇÃO - DATA DE INICIO', 'O': 'TRADUÇÃO - STATUS', 'P': 'TRADUÇÃO - DATA DE ENTREGA',
        'Q': 'APOSTILA - DATA DE INICIO', 'R': 'APOSTILA - STATUS', 'S': 'APOSTILA - DATA DE ENTREGA',
        'T': 'DRIVE - DATA DE INICIO', 'U': 'DRIVE - STATUS', 'V': 'DRIVE - DATA DE ENTREGA',
    }
    
    df = df_raw.rename(columns=mapeamento_colunas)
    if 'PENDENCIAS' in df.columns:
        df['PENDENCIAS'] = df['PENDENCIAS'].fillna('SEM PENDENCIAS').replace('', 'SEM PENDENCIAS')

    # A página de Produtividade tem seus próprios filtros internos e não usa a sidebar.
    if subpagina == "Produtividade":
        show_produtividade(df)  # Passa o DataFrame não filtrado
        return  # Impede a renderização dos filtros da sidebar

    # Filtros na sidebar para todas as outras páginas
    st.sidebar.header("Filtros de Análise")
    
    consultores_unicos = sorted(df['CONSULTOR RESPONSÁVEL'].dropna().unique())
    status_unicos = sorted(df['STATUS GERAL'].dropna().unique())
    
    consultores_selecionados = st.sidebar.multiselect(
        "Consultor Responsável", options=consultores_unicos, default=consultores_unicos
    )
    status_selecionado = st.sidebar.multiselect(
        "Status Geral", options=status_unicos, default=status_unicos
    )

    df_filtrado = df[
        df['CONSULTOR RESPONSÁVEL'].isin(consultores_selecionados) &
        df['STATUS GERAL'].isin(status_selecionado)
    ]

    if subpagina == "Dados Macros":
        show_dados_macros(df_filtrado)
    elif subpagina == "Funil - Etapas":
        show_funil_etapas(df_filtrado)
    elif subpagina == "Pendências Liberadas":
        show_pendencias_liberadas(df_filtrado)
    elif subpagina == "Pendências Futuras":
        show_pendencias_futuras(df_filtrado)
    else:
        st.error(f"Sub-página '{subpagina}' não encontrada.")
        show_dados_macros(df_filtrado) 