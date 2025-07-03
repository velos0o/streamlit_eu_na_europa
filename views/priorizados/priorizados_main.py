import streamlit as st
import pandas as pd
import gspread
from ..cartorio_new.data_loader import carregar_dados_cartorio

def safe_pandas_df(df):
    """
    Função ultra-defensiva para garantir DataFrame pandas nativo.
    Recria completamente o DataFrame para evitar qualquer vestígio de narwhals.
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Converter para dict e recriar - método mais agressivo
    try:
        return pd.DataFrame(df.to_dict('records'))
    except:
        # Fallback: usar valores e colunas
        try:
            return pd.DataFrame(df.values, columns=df.columns)
        except:
            # Último fallback: tentar conversão direta
            return pd.DataFrame(df)

from .dados_macros import show_dados_macros
from .funil_etapas import show_funil_etapas
from .pendencias_liberadas import show_pendencias_liberadas
from .pendencias_futuras import show_pendencias_futuras
from .produtividade import show_produtividade
from .tempo_etapas import show_tempo_etapas
# from .produtividade_debug import show_produtividade_debug

@st.cache_data(ttl=300)
def carregar_dados_priorizados():
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

        return safe_pandas_df(df)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Planilha não encontrada. Verifique o ID e se a conta de serviço tem permissão de 'Leitor'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha: {e}")
        return pd.DataFrame()

def show_priorizados(subpagina):
    st.title(f"Priorizados: {subpagina}")
    
    # Carregar dados das duas fontes
    with st.spinner("Carregando dados de Priorizados..."):
        df_raw = carregar_dados_priorizados()
    
    with st.spinner("Carregando dados de Emissões Brasileiras..."):
        df_cartorio = carregar_dados_cartorio()

    if df_raw.empty:
        st.warning("Não foi possível carregar os dados de priorizados ou a planilha está vazia.")
        return

    mapeamento_colunas = {
        'B': 'ID FAMÍLIA', 'C': 'CONSULTOR RESPONSÁVEL', 
        'D': 'Data de Inicio das Tratativas',
        'E': 'STATUS GERAL', 'F': 'PENDENCIAS',
        'G': 'PROCURAÇÃO - STATUS', 'H': 'PROCURAÇÃO - ADM RESPONSAVEL', 'I': 'PROCURAÇÃO - DATA ENVIO', 'J': 'PROCURAÇÃO - DATA CONCLUSÃO',
        'K': 'ANALISE - RESPONSÁVEL', 'L': 'ANALISE - DATA DE ENVIO', 'M': 'ANALISE - STATUS', 'N': 'ANALISE - DATA CONCLUSÃO',
        'O': 'TRADUÇÃO - DATA DE INICIO', 'P': 'TRADUÇÃO - STATUS', 'Q': 'TRADUÇÃO - DATA DE ENTREGA',
        'R': 'APOSTILA - DATA DE INICIO', 'S': 'APOSTILA - STATUS', 'T': 'APOSTILA - DATA DE ENTREGA',
        'U': 'DRIVE - DATA DE INICIO', 'V': 'DRIVE - STATUS', 'W': 'DRIVE - DATA DE ENTREGA',
        'X': 'DATA DE FINALIZAÇÃO DA PASTA',
    }
    
    df = safe_pandas_df(df_raw.rename(columns=mapeamento_colunas))
    if 'PENDENCIAS' in df.columns:
        df['PENDENCIAS'] = df['PENDENCIAS'].fillna('SEM PENDENCIAS').replace('', 'SEM PENDENCIAS')

    # A página de Produtividade tem seus próprios filtros internos e não usa a sidebar.
    if subpagina == "Produtividade":
        show_produtividade()
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

    df_filtrado = safe_pandas_df(df[
        df['CONSULTOR RESPONSÁVEL'].isin(consultores_selecionados) &
        df['STATUS GERAL'].isin(status_selecionado)
    ])

    if subpagina == "Dados Macros":
        show_dados_macros(safe_pandas_df(df_filtrado))
    elif subpagina == "Funil - Etapas":
        show_funil_etapas(safe_pandas_df(df_filtrado))
    elif subpagina == "Pendências Liberadas":
        show_pendencias_liberadas(safe_pandas_df(df_filtrado))
    elif subpagina == "Pendências Futuras":
        show_pendencias_futuras(safe_pandas_df(df_filtrado))
    elif subpagina == "Tempo por Etapa":
        show_tempo_etapas(safe_pandas_df(df_filtrado), safe_pandas_df(df_cartorio))
    else:
        st.error(f"Sub-página '{subpagina}' não encontrada.")
        show_dados_macros(safe_pandas_df(df_filtrado)) 