import streamlit as st
import pandas as pd
from .metrics import display_metrics
from .calendar_view import display_reuniao_schedule

def show_fluxo_financeiro(df_page: pd.DataFrame):
    """
    Renderiza a página Fluxo Financeiro (ID 116) usando os componentes
    de métricas e calendário.
    """
    st.title("Fluxo Financeiro")
    st.markdown("Visão geral dos registros e agendamentos da categoria Fluxo Financeiro.")
    
    st.markdown("---")
    
    # Exibir métricas
    display_metrics(df_page)
    
    st.markdown("---")
    
    # Exibir calendário de reuniões
    display_reuniao_schedule(df_page)
    
    st.markdown("---")
    
    # Exibir tabela de dados brutos da página
    st.subheader("Dados Completos da Categoria")
    if df_page.empty:
        st.warning("Nenhum dado encontrado para a categoria (ID 116).")
    else:
        st.dataframe(df_page) 