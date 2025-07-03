import streamlit as st
import pandas as pd
# O caminho do data_loader agora precisa de um nível a mais
from ..data_loader import get_criacao_adendo_data
from utils.dataframe_utils import ensure_pandas_df

def show_tipo_contrato():
    """
    Exibe um relatório consolidado com as principais métricas de Adendos e Distratos
    em formato de cartões.
    """
    st.header("Relatório por Tipo de Contrato")

    # CSS para os cartões de métricas
    st.markdown("""
    <style>
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        height: 100%;
    }
    .metric-card h3 {
        font-size: 1.1rem;
        color: #616161;
        margin-bottom: 10px;
        font-weight: 500;
    }
    .metric-card p {
        font-size: 2.5rem;
        font-weight: 600;
        margin: 0;
    }
    .metric-card .concluido { color: #2E7D32; } /* Verde */
    .metric-card .pendente { color: #C62828; } /* Vermelho */
    .metric-card .neutro { color: #37474F; } /* Cor padrão */
    </style>
    """, unsafe_allow_html=True)

    df = get_criacao_adendo_data()
    df = ensure_pandas_df(df)

    if df.empty:
        st.warning("Não foram encontrados dados para Adendos ou Distratos.")
        return

    # Define o ID da etapa de sucesso
    SUCCESS_STAGE_ID = 'DT1118_126:SUCCESS'
    
    tipos_relevantes = ["ADENDO", "DISTRATO"]
    df_filtrado = df[df['UF_CRM_42_TIPO_DE_DOCUMENTO'].isin(tipos_relevantes)].copy()

    if df_filtrado.empty:
        st.info("Nenhum registro de 'ADENDO' ou 'DISTRATO' encontrado no funil.")
        return

    # Cálculos das métricas
    adendo_count = (df_filtrado['UF_CRM_42_TIPO_DE_DOCUMENTO'] == 'ADENDO').sum()
    distrato_count = (df_filtrado['UF_CRM_42_TIPO_DE_DOCUMENTO'] == 'DISTRATO').sum()
    total_count = len(df_filtrado)
    concluido_count = (df_filtrado['STAGE_ID'] == SUCCESS_STAGE_ID).sum()
    pendente_count = total_count - concluido_count

    # Exibição em colunas com cartões
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f'<div class="metric-card"><h3>ADENDOS</h3><p class="neutro">{adendo_count}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>DISTRATOS</h3><p class="neutro">{distrato_count}</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3>TOTAL</h3><p class="neutro">{total_count}</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><h3>CONCLUÍDOS</h3><p class="concluido">{concluido_count}</p></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><h3>PENDENTES</h3><p class="pendente">{pendente_count}</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # --- Tabela de Resumo por Responsável ---
    st.subheader("Desempenho por Responsável")

    # Garante que a coluna de responsável não tenha valores nulos para o groupby
    df_filtrado['ASSIGNED_BY_NAME'].fillna('Não Atribuído', inplace=True)

    responsible_summary = df_filtrado.groupby('ASSIGNED_BY_NAME').apply(lambda x: pd.Series({
        'Adendos': (x['UF_CRM_42_TIPO_DE_DOCUMENTO'] == 'ADENDO').sum(),
        'Distratos': (x['UF_CRM_42_TIPO_DE_DOCUMENTO'] == 'DISTRATO').sum(),
        'Total Geral': len(x),
        'Concluídos': (x['STAGE_ID'] == SUCCESS_STAGE_ID).sum()
    })).reset_index()

    responsible_summary['Pendentes'] = responsible_summary['Total Geral'] - responsible_summary['Concluídos']

    responsible_summary.rename(columns={'ASSIGNED_BY_NAME': 'Responsável'}, inplace=True)
    
    # Reordena as colunas para a exibição final
    final_columns = ['Responsável', 'Adendos', 'Distratos', 'Total Geral', 'Concluídos', 'Pendentes']
    st.dataframe(responsible_summary[final_columns], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.write("### Detalhamento dos Dados Brutos")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True) 