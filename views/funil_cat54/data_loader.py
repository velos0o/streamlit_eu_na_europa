import pandas as pd
import streamlit as st
import sys
from pathlib import Path

# Adicionar o caminho da API ao sys.path
api_path = Path(__file__).parents[2] / 'api'
sys.path.append(str(api_path))

from bitrix_connector import load_merged_data

def carregar_dados_negociacao(force_reload=False):
    """
    Carrega os dados de negócios para a categoria 'Negociação' (ID 54).

    Args:
        force_reload (bool): Se True, força o recarregamento dos dados do Bitrix.

    Returns:
        pandas.DataFrame: DataFrame com os dados mesclados.
    """
    try:
        # Chama a função genérica para carregar dados com a category_id específica
        df_negociacao = load_merged_data(category_id='54', force_reload=force_reload, debug=False)
        
        if df_negociacao.empty:
            st.warning("Não foram encontrados dados de Negociação (Categoria 54) ou ocorreu um erro ao carregar.")
            return pd.DataFrame()
            
        return df_negociacao
        
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados de Negociação: {e}")
        return pd.DataFrame() 