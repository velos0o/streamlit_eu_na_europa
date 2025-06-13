import streamlit as st
import pandas as pd
import altair as alt

def _create_section(title, df, end_date_col, start_date_col, status_col, other_cols=None):
    """
    Cria uma seção de análise compacta, focada em métricas de desempenho.
    """
    if other_cols is None:
        other_cols = []
        
    st.header(title, divider='blue')

    required_cols = [end_date_col, start_date_col, status_col]
    if not all(col in df.columns for col in required_cols):
        st.warning(f"Dados insuficientes para a seção '{title}'.")
        return

    df_section = df.copy()
    df_section[end_date_col] = pd.to_datetime(df_section[end_date_col], errors='coerce')
    df_section[start_date_col] = pd.to_datetime(df_section[start_date_col], errors='coerce')

    df_concluido = df_section[df_section[end_date_col].notna()].copy()
    
    if df_concluido.empty:
        st.info(f"Nenhuma tarefa concluída para '{title}' encontrada.")
        return

    # --- Métricas de Desempenho e Status ---
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.subheader("Desempenho")
        total_concluidas = len(df_concluido)
        df_concluido['TEMPO_PROCESSAMENTO'] = (df_concluido[end_date_col] - df_concluido[start_date_col]).dt.days
        tempo_medio_dias = f"{int(df_concluido['TEMPO_PROCESSAMENTO'].mean())} dias" if pd.notna(df_concluido['TEMPO_PROCESSAMENTO'].mean()) else 'N/A'

        st.metric(f"Total Concluído", total_concluidas)
        st.metric("Tempo Médio", tempo_medio_dias)

    with col2:
        st.subheader("Resumo dos Status")
        status_counts = df_concluido[status_col].value_counts().reset_index()
        status_counts.columns = ['Status', 'Total']
        st.dataframe(status_counts, use_container_width=True, hide_index=True)

    # --- Tabela de Detalhes ---
    with st.expander(f"Ver todos os dados de '{title}'"):
        cols_to_show = ['ID FAMÍLIA', start_date_col, end_date_col, status_col, 'TEMPO_PROCESSAMENTO'] + other_cols
        cols_existentes = [col for col in cols_to_show if col in df_concluido.columns]
        st.dataframe(df_concluido[cols_existentes].sort_values(by=end_date_col, ascending=False), use_container_width=True)


def show_pendencias_liberadas(df_filtrado):
    """
    Exibe a análise de pendências liberadas, organizadas por etapa do processo.
    """
    st.subheader("Análise de Pendências Liberadas", divider='rainbow')
    st.write("Visão consolidada e detalhada das tarefas finalizadas em cada etapa do processo.")

    if df_filtrado.empty:
        st.warning("Não há dados para exibir com os filtros selecionados.")
        return

    secoes = {
        "Procuração": {"end_date_col": 'PROCURAÇÃO - DATA CONCLUSÃO', "start_date_col": 'PROCURAÇÃO - DATA ENVIO', "status_col": 'PROCURAÇÃO - STATUS', "other_cols": ['PROCURAÇÃO - ADM RESPONSAVEL']},
        "Análise Documental": {"end_date_col": 'ANALISE - DATA CONCLUSÃO', "start_date_col": 'ANALISE - DATA DE ENVIO', "status_col": 'ANALISE - STATUS', "other_cols": ['ANALISE - RESPONSÁVEL']},
        "Tradução": {"end_date_col": 'TRADUÇÃO - DATA DE ENTREGA', "start_date_col": 'TRADUÇÃO - DATA DE INICIO', "status_col": 'TRADUÇÃO - STATUS'},
        "Apostila": {"end_date_col": 'APOSTILA - DATA DE ENTREGA', "start_date_col": 'APOSTILA - DATA DE INICIO', "status_col": 'APOSTILA - STATUS'},
        "Drive": {"end_date_col": 'DRIVE - DATA DE ENTREGA', "start_date_col": 'DRIVE - DATA DE INICIO', "status_col": 'DRIVE - STATUS'}
    }

    # --- Tabela Consolidada de Status ---
    st.header("Distribuição Geral de Status", divider='blue')
    all_status_data = []
    for title, params in secoes.items():
        if all(col in df_filtrado.columns for col in [params['end_date_col'], params['status_col']]):
            df_concluido = df_filtrado[df_filtrado[params['end_date_col']].notna() & (df_filtrado[params['end_date_col']] != '')]
            if not df_concluido.empty:
                status_counts = df_concluido[params['status_col']].value_counts().reset_index()
                status_counts.columns = ['Status', 'Contagem']
                status_counts['Etapa'] = title
                all_status_data.append(status_counts)

    if all_status_data:
        df_summary = pd.concat(all_status_data)
        
        # Cria a tabela dinâmica com etapas como linhas e status como colunas
        pivot_table = pd.pivot_table(
            df_summary,
            values='Contagem',
            index='Etapa',
            columns='Status',
            aggfunc='sum',
            fill_value=0
        )
        
        # Adiciona uma coluna de total e reordena para clareza
        pivot_table['Total Geral'] = pivot_table.sum(axis=1)
        ordem_etapas = [etapa for etapa in secoes.keys() if etapa in pivot_table.index]
        pivot_table = pivot_table.reindex(ordem_etapas)

        st.dataframe(pivot_table.astype(int), use_container_width=True)
    else:
        st.info("Não há dados de status de conclusão para exibir na tabela.")
    
    st.markdown("---")

    # --- Seções Individuais ---
    for title, params in secoes.items():
        _create_section(title=title, df=df_filtrado, **params) 