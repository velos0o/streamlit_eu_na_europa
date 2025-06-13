import streamlit as st
import pandas as pd
import altair as alt

def show_produtividade(df_filtrado):
    """
    Exibe a análise de produtividade, mostrando tarefas concluídas por responsável e por data.
    """
    st.header("Análise de Produtividade", divider='rainbow')
    st.write("Acompanhe o número de tarefas concluídas pelos consultores ao longo do tempo.")

    if df_filtrado.empty:
        st.warning("Não há dados para exibir com os filtros selecionados.")
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
    # Transforma o DataFrame de formato largo para longo, criando uma linha para cada tarefa concluída
    lista_tarefas = []
    for etapa, data_col in mapeamento_etapas.items():
        if data_col in df_filtrado.columns:
            df_etapa = df_filtrado[['ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', data_col]].copy()
            df_etapa.dropna(subset=[data_col], inplace=True)
            df_etapa[data_col] = pd.to_datetime(df_etapa[data_col], errors='coerce')
            df_etapa.rename(columns={data_col: 'Data Conclusão'}, inplace=True)
            df_etapa['Etapa'] = etapa
            lista_tarefas.append(df_etapa)
    
    if not lista_tarefas:
        st.error("Nenhuma das colunas de data de conclusão foi encontrada. Verifique os nomes das colunas na planilha.")
        return
        
    df_produtividade = pd.concat(lista_tarefas, ignore_index=True).dropna(subset=['Data Conclusão'])

    # --- Filtros ---
    col1, col2 = st.columns([2, 1])
    with col1:
        consultores_selecionados = st.multiselect(
            "Selecione o(s) Consultor(es)",
            options=sorted(df_produtividade['CONSULTOR RESPONSÁVEL'].unique()),
            default=sorted(df_produtividade['CONSULTOR RESPONSÁVEL'].unique())
        )
    with col2:
        min_date = df_produtividade['Data Conclusão'].min().date()
        max_date = df_produtividade['Data Conclusão'].max().date()
        
        data_selecionada = st.date_input(
            "Selecione o Período",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )

    # Garante que o filtro de data tenha um início e um fim
    if len(data_selecionada) != 2:
        st.info("Por favor, selecione um período de início e fim no filtro de data.")
        return
        
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
    
    # Prepara os dados para o gráfico
    produtividade_diaria = df_filtrado_prod.groupby(df_filtrado_prod['Data Conclusão'].dt.date).size().reset_index(name='Contagem')
    produtividade_diaria.rename(columns={'Data Conclusão': 'Data'}, inplace=True)
    
    # Cria o gráfico base com a linha e os pontos
    base = alt.Chart(produtividade_diaria).encode(
        x=alt.X('Data:T', title='Data da Conclusão'),
        y=alt.Y('Contagem:Q', title='Nº de Tarefas Concluídas'),
        tooltip=['Data:T', 'Contagem:Q']
    )

    linha = base.mark_line(color='#1E88E5', point=True)
    pontos = base.mark_point(size=80, filled=True, color='#1E88E5')
    
    # Cria os rótulos de texto acima dos pontos
    texto = base.mark_text(
        align='center',
        baseline='bottom',
        dy=-10  # Deslocamento vertical para ficar acima do ponto
    ).encode(
        text='Contagem:Q'
    )

    # Combina as camadas do gráfico
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