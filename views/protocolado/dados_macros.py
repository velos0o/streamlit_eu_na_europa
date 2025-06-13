import streamlit as st
import pandas as pd

def show_dados_macros(df_filtrado):
    """Exibe as métricas macro e de pendências."""
    st.subheader("Visão Geral", divider='blue')
    
    col1, col2 = st.columns(2)
    with col1:
        total_familias = df_filtrado['ID FAMÍLIA'].nunique()
        st.metric("TOTAL DE FAMÍLIAS", total_familias)

    # Contagem total de cada tipo de pendência
    pendencias_gerais = df_filtrado[df_filtrado['PENDENCIAS'] != 'SEM PENDENCIAS']['PENDENCIAS']
    if not pendencias_gerais.empty:
        lista_tags = [
            'Emissão', 'Comune', 'Analise Documental', 
            'Tradução', 'Apostilamento', 'Drive', 'Procuração'
        ]
        
        contagem_tags = pd.Series(dtype=int)
        if not pendencias_gerais.empty:
            contagem_tags = pendencias_gerais.str.split(',').explode().str.strip().value_counts()
            
        st.write("Totais por Tipo de Pendência:")
        
        # Exibir métricas em colunas
        num_cols = 4 
        cols = st.columns(num_cols)
        
        for i, tag in enumerate(lista_tags):
            with cols[i % num_cols]:
                st.metric(label=tag, value=contagem_tags.get(tag, 0))

    # --- Análise 2: Pendências por Responsável ---
    st.subheader("Pendências por Responsável", divider='blue')

    pendencias_df = df_filtrado[['CONSULTOR RESPONSÁVEL', 'PENDENCIAS']].copy()
    pendencias_df = pendencias_df[pendencias_df['PENDENCIAS'] != 'SEM PENDENCIAS']

    if pendencias_df.empty:
        st.info("Nenhuma pendência encontrada para os filtros selecionados.")
    else:
        # Processar as pendências
        pendencias_df['PENDENCIAS_LIST'] = pendencias_df['PENDENCIAS'].str.split(',')
        pendencias_exploded = pendencias_df.explode('PENDENCIAS_LIST')
        pendencias_exploded['PENDENCIA_TIPO'] = pendencias_exploded['PENDENCIAS_LIST'].str.strip()

        # Tabela: Detalhamento de pendências por consultor e tipo
        st.write("Contagem de Pendências por Tipo e Consultor")
        crosstab_pendencias = pd.crosstab(
            index=pendencias_exploded['CONSULTOR RESPONSÁVEL'],
            columns=pendencias_exploded['PENDENCIA_TIPO']
        )
        
        # Garantir que todas as colunas de pendências possíveis existam
        lista_tags = [
            'Emissão', 'Comune', 'Analise Documental', 
            'Tradução', 'Apostilamento', 'Drive', 'Procuração'
        ]
        for tag in lista_tags:
            if tag not in crosstab_pendencias.columns:
                crosstab_pendencias[tag] = 0
        
        # Reordenar colunas e adicionar total
        crosstab_pendencias = crosstab_pendencias[lista_tags]
        crosstab_pendencias['Total de Pendências'] = crosstab_pendencias.sum(axis=1)

        st.dataframe(crosstab_pendencias.sort_values(by='Total de Pendências', ascending=False), use_container_width=True)

        # Gráfico: Detalhamento de pendências por tipo e consultor
        st.write("Gráfico de Detalhamento das Pendências")
        st.bar_chart(crosstab_pendencias.drop(columns=['Total de Pendências']))

    # --- Exibição dos Dados Brutos Filtrados ---
    with st.expander("Ver dados brutos filtrados"):
        colunas_para_exibir = [
            'ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', 'STATUS GERAL', 'PENDENCIAS',
            'PROCURAÇÃO - STATUS', 'ANALISE - STATUS', 'TRADUÇÃO - STATUS', 
            'APOSTILA - STATUS', 'DRIVE - STATUS'
        ]
        colunas_existentes = [col for col in colunas_para_exibir if col in df_filtrado.columns]
        st.dataframe(df_filtrado[colunas_existentes], use_container_width=True) 