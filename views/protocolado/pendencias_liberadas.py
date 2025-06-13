import streamlit as st
import pandas as pd
import altair as alt

def _create_section(title, df, end_date_col, start_date_col, status_col, completion_statuses, other_cols=None):
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

    # Substitui status vazios/com espaços por NA e depois remove essas linhas
    df_section[status_col] = df_section[status_col].replace(r'^\s*$', pd.NA, regex=True)
    df_section = df_section.dropna(subset=[status_col])

    if df_section.empty:
        st.info(f"Nenhuma tarefa com status definido para '{title}'.")
        return

    df_section[end_date_col] = pd.to_datetime(df_section[end_date_col], errors='coerce')
    df_section[start_date_col] = pd.to_datetime(df_section[start_date_col], errors='coerce')

    # --- Lógica de Dados ---
    # DataFrame para calcular o resumo de TODOS os status (em andamento e concluídos)
    df_status = df_section # df_section já está filtrado para status não nulos

    # DataFrame APENAS com tarefas concluídas para calcular o desempenho
    df_concluido = df_section[df_section[end_date_col].notna()].copy()
    
    # --- Métricas de Desempenho e Status ---
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.subheader("Desempenho")
        
        # Os status de conclusão agora são configuráveis
        completion_statuses_lower = [s.lower() for s in completion_statuses]
        df_com_status_concluido = df_status[df_status[status_col].str.strip().str.lower().isin(completion_statuses_lower)]
        
        # A métrica deve contar o total de TAREFAS, para corresponder à tabela.
        total_tarefas_concluidas = len(df_com_status_concluido)
        
        # O tempo médio, no entanto, só pode ser calculado com as datas.
        df_com_datas = df_section[df_section[end_date_col].notna()].copy()
        if not df_com_datas.empty:
            df_com_datas['TEMPO_PROCESSAMENTO'] = (df_com_datas[end_date_col] - df_com_datas[start_date_col]).dt.days
            tempo_medio_dias = f"{int(df_com_datas['TEMPO_PROCESSAMENTO'].mean())} dias" if pd.notna(df_com_datas['TEMPO_PROCESSAMENTO'].mean()) else 'N/A'
        else:
            tempo_medio_dias = 'N/A'

        st.metric(f"Total de Tarefas Concluídas", total_tarefas_concluidas)
        st.metric("Tempo Médio de Conclusão", tempo_medio_dias)

    with col2:
        st.subheader("Resumo dos Status")
        if not df_status.empty:
            status_counts = df_status[status_col].value_counts().reset_index()
            status_counts.columns = ['Status', 'Total']
            st.dataframe(status_counts, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum status encontrado para esta etapa.")

    # --- Tabela de Detalhes ---
    if not df_com_datas.empty:
        with st.expander(f"Ver detalhes das tarefas concluídas"):
            cols_to_show = ['ID FAMÍLIA', start_date_col, end_date_col, status_col, 'TEMPO_PROCESSAMENTO'] + other_cols
            cols_existentes = [col for col in cols_to_show if col in df_com_datas.columns]
            st.dataframe(df_com_datas[cols_existentes].sort_values(by=end_date_col, ascending=False), use_container_width=True)


def show_pendencias_liberadas(df_filtrado):
    """
    Exibe a análise de pendências liberadas, organizadas por etapa do processo.
    """
    st.title("Análise de Pendências Liberadas")

    if df_filtrado.empty:
        st.warning("Não há dados para exibir com os filtros selecionados.")
        return

    secoes = {
        "Procuração": {
            "start_date_col": "PROCURAÇÃO - DATA ENVIO",
            "end_date_col": "PROCURAÇÃO - DATA CONCLUSÃO",
            "status_col": "PROCURAÇÃO - STATUS",
            "completion_statuses": ["Concluido"],
            "other_cols": ["PROCURAÇÃO - ADM RESPONSAVEL"]
        },
        "Análise Documental": {
            "start_date_col": "ANALISE - DATA DE ENVIO",
            "end_date_col": "ANALISE - DATA CONCLUSÃO",
            "status_col": "ANALISE - STATUS",
            "completion_statuses": ["Positiva", "Negativa"], # Ambos os status finalizam a análise
            "other_cols": ["ANALISE - RESPONSÁVEL"]
        },
        "Tradução": {
            "start_date_col": "TRADUÇÃO - DATA DE INICIO",
            "end_date_col": "TRADUÇÃO - DATA DE ENTREGA",
            "status_col": "TRADUÇÃO - STATUS",
            "completion_statuses": ["Concluido"],
            "other_cols": []
        },
        "Apostila": {
            "start_date_col": "APOSTILA - DATA DE INICIO",
            "end_date_col": "APOSTILA - DATA DE ENTREGA",
            "status_col": "APOSTILA - STATUS",
            "completion_statuses": ["Concluido"],
            "other_cols": []
        },
        "Drive": {
            "start_date_col": "DRIVE - DATA DE INICIO",
            "end_date_col": "DRIVE - DATA DE ENTREGA",
            "status_col": "DRIVE - STATUS",
            "completion_statuses": ["Concluido"],
            "other_cols": []
        }
    }

    # --- Tabela Consolidada de Status ---
    st.header("Distribuição Geral de Status", divider='blue')
    all_status_data = []
    for title, params in secoes.items():
        if all(col in df_filtrado.columns for col in [params['status_col'], 'ID FAMÍLIA']):
            df_etapa = df_filtrado.copy()
            # Substitui status vazios/com espaços por NA e depois remove essas linhas
            df_etapa[params['status_col']] = df_etapa[params['status_col']].replace(r'^\s*$', pd.NA, regex=True)
            df_etapa = df_etapa.dropna(subset=[params['status_col']])

            if not df_etapa.empty:
                status_counts = df_etapa.groupby(params['status_col'])['ID FAMÍLIA'].nunique().reset_index()
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