"""
Módulo de carregamento de dados para Ficha da Família
"""
import streamlit as st
import pandas as pd
from api.bitrix_connector import load_merged_data


def load_crm_deal_data(category_id):
    """Carrega dados do CRM Deal (Funil/Categoria especificado) usando a função central load_merged_data."""
    print(f"[INFO] Solicitando dados CRM para category_id: {category_id} via load_merged_data")
    try:
        df_crm_merged = load_merged_data(category_id=category_id, debug=False, force_reload=False)

        if df_crm_merged is None or df_crm_merged.empty:
            st.warning(f"Nenhum dado encontrado ou erro ao carregar dados para a categoria {category_id}.")
            print(f"[AVISO] load_merged_data retornou vazio para category_id {category_id}")
            return pd.DataFrame()
        else:
            print(f"[INFO] Dados para category_id {category_id} carregados com sucesso via load_merged_data ({len(df_crm_merged)} linhas).")
            # Verificar se as colunas essenciais existem
            colunas_necessarias = ['ID', 'UF_CRM_1722883482527', 'UF_CRM_1722605592778']
            colunas_faltantes = [col for col in colunas_necessarias if col not in df_crm_merged.columns]
            if colunas_faltantes:
                st.error(f"Erro Crítico: As seguintes colunas essenciais estão faltando nos dados carregados: {colunas_faltantes}")
                print(f"[ERRO] Colunas essenciais ausentes após merge: {colunas_faltantes}. Colunas presentes: {list(df_crm_merged.columns)}")
                return pd.DataFrame()
            return df_crm_merged

    except ImportError:
        st.error("Erro Crítico: Não foi possível importar 'load_merged_data' de 'api.bitrix_connector'. Verifique a estrutura do projeto.")
        print("[ERRO CRÍTICO] Falha ao importar load_merged_data")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro inesperado ao chamar load_merged_data: {e}")
        print(f"[ERRO CRÍTICO] Erro inesperado em load_crm_deal_data ao chamar load_merged_data: {e}")
        return pd.DataFrame()


