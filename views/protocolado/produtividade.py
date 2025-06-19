import streamlit as st
import pandas as pd
import altair as alt

def show_produtividade(df_protocolados):
    """
    Exibe a análise de produtividade, mostrando tarefas concluídas por responsável e por data.
    Esta página gerencia seus próprios filtros.
    """
    st.header("Análise de Produtividade", divider='rainbow')
    st.write("Acompanhe o número de tarefas concluídas pelos consultores ao longo do tempo.")

    if df_protocolados.empty:
        st.warning("Não há dados de protocolados para exibir.")
        return

    # --- Mapeamento de Etapas e Colunas de Conclusão ---
    mapeamento_etapas = {
        'Procuração': 'PROCURAÇÃO - DATA CONCLUSÃO',
        'Análise Documental': 'ANALISE - DATA CONCLUSÃO',
        'Tradução': 'TRADUÇÃO - DATA DE ENTREGA',
        'Apostila': 'APOSTILA - DATA DE ENTREGA',
        'Drive': 'DRIVE - DATA DE ENTREGA'
    }

    # --- Preparação dos Dados ---
    lista_tarefas = []
    for etapa, data_col in mapeamento_etapas.items():
        if data_col in df_protocolados.columns:
            df_etapa = df_protocolados[['ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', data_col]].copy()
            df_etapa.dropna(subset=[data_col, 'CONSULTOR RESPONSÁVEL'], inplace=True)
            df_etapa = df_etapa[df_etapa['CONSULTOR RESPONSÁVEL'].str.strip() != '']

            if df_etapa.empty:
                continue

            df_etapa[data_col] = pd.to_datetime(df_etapa[data_col], errors='coerce')
            df_etapa.dropna(subset=[data_col], inplace=True)
            
            df_etapa.rename(columns={data_col: 'Data Conclusão'}, inplace=True)
            df_etapa['Etapa'] = etapa
            lista_tarefas.append(df_etapa)
    
    if not lista_tarefas:
        st.info("Nenhuma tarefa concluída foi encontrada.")
        return
        
    df_produtividade = pd.concat(lista_tarefas, ignore_index=True)

    # --- Filtros ---
    st.subheader("Filtros", divider='blue')
    col1, col2 = st.columns(2)

    with col1:
        consultores_unicos = sorted(df_produtividade['CONSULTOR RESPONSÁVEL'].unique())
        consultores_selecionados = st.multiselect(
            "Selecione o(s) Consultor(es)",
            options=consultores_unicos,
            default=consultores_unicos
        )
    
    with col2:
        # Filtra o dataframe de produtividade para obter o intervalo de datas correto
        df_para_datas = df_produtividade[df_produtividade['CONSULTOR RESPONSÁVEL'].isin(consultores_selecionados)]
        
        if not df_para_datas.empty:
            min_date = df_para_datas['Data Conclusão'].min().date()
            max_date = df_para_datas['Data Conclusão'].max().date()
        else:
            min_date = pd.Timestamp('today').date()
            max_date = pd.Timestamp('today').date()
            
        data_selecionada = st.date_input(
            "Selecione o Período",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )

    # Garante que o filtro de data tenha um início e um fim
    if len(data_selecionada) != 2:
        st.warning("Por favor, selecione um período de início e fim no filtro de data para continuar.")
        st.stop()
        
    start_date, end_date = pd.to_datetime(data_selecionada[0]), pd.to_datetime(data_selecionada[1])

    # --- Aplicação dos Filtros ---
    df_filtrado_prod = df_produtividade[
        (df_produtividade['CONSULTOR RESPONSÁVEL'].isin(consultores_selecionados)) &
        (df_produtividade['Data Conclusão'] >= start_date) &
        (df_produtividade['Data Conclusão'] <= end_date)
    ]

    if df_filtrado_prod.empty:
        st.warning("Nenhuma tarefa concluída encontrada para os filtros selecionados.")
        return

    # --- Métricas Gerais ---
    total_tarefas = len(df_filtrado_prod)
    dias_no_periodo = (end_date - start_date).days + 1
    media_diaria = total_tarefas / dias_no_periodo if dias_no_periodo > 0 else 0
    
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("Total de Tarefas Concluídas", f"{total_tarefas}")
    m_col2.metric("Média Diária de Conclusão", f"{media_diaria:.2f}")

    # --- Gráficos ---
    st.subheader("Visualização da Produtividade", divider='blue')
    
    produtividade_diaria = df_filtrado_prod.groupby(df_filtrado_prod['Data Conclusão'].dt.date).size().reset_index(name='Contagem')
    produtividade_diaria.rename(columns={'Data Conclusão': 'Data'}, inplace=True)
    
    base = alt.Chart(produtividade_diaria).encode(
        x=alt.X('Data:T', title='Data da Conclusão'),
        y=alt.Y('Contagem:Q', title='Nº de Tarefas Concluídas'),
        tooltip=['Data:T', 'Contagem:Q']
    )

    linha = base.mark_line(color='#1E88E5', point=True)
    pontos = base.mark_point(size=80, filled=True, color='#1E88E5')
    
    texto = base.mark_text(
        align='center',
        baseline='bottom',
        dy=-10
    ).encode(
        text='Contagem:Q'
    )

    chart = (linha + pontos + texto).interactive().properties(
        title='Produtividade Diária (Tarefas Concluídas)'
    )
    
    st.altair_chart(chart, use_container_width=True)

    # --- Tabela de Produtividade ---
    st.subheader("Detalhamento por Consultor e Etapa", divider='blue')
    
    tabela_produtividade = pd.pivot_table(
        df_filtrado_prod,
        values='ID FAMÍLIA',
        index='CONSULTOR RESPONSÁVEL',
        columns='Etapa',
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='Total Geral'
    )
    
    st.dataframe(tabela_produtividade, use_container_width=True) 