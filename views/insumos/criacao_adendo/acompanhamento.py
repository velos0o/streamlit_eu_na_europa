import streamlit as st
import pandas as pd
from ..data_loader import get_criacao_adendo_data
from utils.dataframe_utils import ensure_pandas_df

def show_acompanhamento():
    """
    Exibe um painel de acompanhamento operacional com um funil simplificado
    e uma análise de carga de trabalho por responsável (Negociador).
    """
    st.header("Acompanhamento Operacional de Adendos e Distratos")

    # Injetando CSS para os cartões de métrica
    st.markdown("""
    <style>
    .metric-card-grey {
        background-color: #F5F5F5;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-card-grey h3 {
        font-size: 1.1rem;
        color: #616161;
        margin-bottom: 8px;
        font-weight: 500;
    }
    .metric-card-grey p {
        font-size: 2.5rem;
        font-weight: 600;
        margin: 0;
        color: #212121;
    }
    </style>
    """, unsafe_allow_html=True)

    df = get_criacao_adendo_data()
    df = ensure_pandas_df(df)

    if df.empty:
        st.warning("Não foram encontrados dados para análise.")
        return

    # Mapeamento dos estágios para o funil simplificado
    stages = {
        'EM_ANDAMENTO': ['DT1118_126:PREPARATION'],
        'AGUARDANDO_CONFERENCIA': ['DT1118_126:UC_OESN94'],
        'CONCLUIDO': ['DT1118_126:SUCCESS']
    }

    # Cálculos para o funil simplificado
    em_andamento_count = df[df['STAGE_ID'].isin(stages['EM_ANDAMENTO'])].shape[0]
    aguardando_conferencia_count = df[df['STAGE_ID'].isin(stages['AGUARDANDO_CONFERENCIA'])].shape[0]
    concluido_count = df[df['STAGE_ID'].isin(stages['CONCLUIDO'])].shape[0]
    
    # Exibe os status macro no topo
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card-grey"><h3>Em Andamento</h3><p>{em_andamento_count}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card-grey"><h3>Aguardando Conferência</h3><p>{aguardando_conferencia_count}</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card-grey"><h3>Concluído</h3><p>{concluido_count}</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Exibe as tabelas abaixo
    st.subheader("Carga por Negociador")
    
    responsavel_col = 'UF_CRM_42_NEGOCIADOR'
    if responsavel_col not in df.columns:
        st.error(f"A coluna '{responsavel_col}' não foi encontrada.")
        return

    df_workload = df.copy()
    df_workload[responsavel_col].fillna('Não Atribuído', inplace=True)
    
    # Define os estágios para os cálculos
    concluido_stages = ['DT1118_126:SUCCESS']
    fail_stages = ['DT1118_126:FAIL']
    
    # Agrupa e calcula as métricas de uma vez
    summary = df_workload.groupby(responsavel_col).agg(
        Adendos=('UF_CRM_42_TIPO_DE_DOCUMENTO', lambda x: (x == 'ADENDO').sum()),
        Distratos=('UF_CRM_42_TIPO_DE_DOCUMENTO', lambda x: (x == 'DISTRATO').sum()),
        Total_Geral=('ID', 'count'),
        Concluído=('STAGE_ID', lambda x: x.isin(concluido_stages).sum())
    ).reset_index()

    # Calcula 'Em Andamento'
    # Contamos quantos não estão nem concluídos nem falhados
    em_andamento_counts = df_workload[~df_workload['STAGE_ID'].isin(concluido_stages + fail_stages)].groupby(responsavel_col).size()
    summary = summary.merge(em_andamento_counts.rename('Em Andamento'), left_on=responsavel_col, right_index=True, how='left').fillna(0)

    summary.rename(columns={responsavel_col: 'Negociador'}, inplace=True)
    
    # Converte colunas para inteiro para garantir a formatação correta
    int_cols = ['Adendos', 'Distratos', 'Total_Geral', 'Concluído', 'Em Andamento']
    for col in int_cols:
        if col in summary.columns:
            summary[col] = summary[col].astype(int)

    final_columns = ['Negociador', 'Adendos', 'Distratos', 'Total_Geral', 'Em Andamento', 'Concluído']
    st.dataframe(summary[final_columns], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Detalhamento Completo")
    st.dataframe(df, use_container_width=True) 