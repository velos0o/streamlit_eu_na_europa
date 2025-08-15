import streamlit as st
import pandas as pd
from utils.dataframe_utils import ensure_pandas_df

def show_dados_macros(df_filtrado):
    """
    Exibe as métricas macro de tarefas cumpridas.
    """
    st.subheader("Visão Geral - Tarefas Cumpridas", divider='green')
    
    # Garante que o dataframe de entrada seja pandas nativo
    df_filtrado = ensure_pandas_df(df_filtrado)
    
    if df_filtrado.empty:
        st.warning("Não há dados para exibir.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        try:
            total_familias = df_filtrado['ID FAMÍLIA'].nunique()
            st.metric("TOTAL DE FAMÍLIAS", total_familias)
        except Exception as e:
            st.error(f"Erro ao calcular total de famílias: {e}")

    # Contagem total de cada tipo de tarefa cumprida
    try:
        lista_tags = [
            'Emissão', 'Comune', 'Analise Documental', 
            'Tradução', 'Apostilamento', 'Drive', 'Procuração'
        ]

        def get_cumpridas_list(pendencias_str):
            if pd.isna(pendencias_str) or pendencias_str.strip() == 'SEM PENDENCIAS':
                return lista_tags
            if not isinstance(pendencias_str, str):
                 return []
            pendencias_list = [p.strip() for p in pendencias_str.split(',')]
            return [tag for tag in lista_tags if tag not in pendencias_list]

        # Aplicar a função para obter listas de tarefas cumpridas
        cumpridas_gerais_list = df_filtrado['PENDENCIAS'].apply(get_cumpridas_list)

        # Explodir a lista para contar cada tarefa cumprida
        contagem_tags = cumpridas_gerais_list.explode().value_counts()
        
        st.write("Totais por Tipo de Tarefa Cumprida:")
        
        # Exibir métricas em colunas
        num_cols = 4 
        cols = st.columns(num_cols)
        
        for i, tag in enumerate(lista_tags):
            with cols[i % num_cols]:
                valor = contagem_tags.get(tag, 0)
                st.metric(label=tag, value=int(valor))
                
    except Exception as e:
        st.error(f"Erro ao processar tarefas cumpridas: {e}")

    # --- Análise 2: Tarefas Cumpridas por Responsável ---
    st.subheader("Tarefas Cumpridas por Responsável", divider='green')

    try:
        cumpridas_df = df_filtrado[['CONSULTOR RESPONSÁVEL', 'PENDENCIAS']].copy()

        if cumpridas_df.empty:
            st.info("Nenhum dado encontrado para os filtros selecionados.")
        else:
            cumpridas_df['CUMPRIDAS_LIST'] = cumpridas_df['PENDENCIAS'].apply(get_cumpridas_list)
            cumpridas_exploded = cumpridas_df.explode('CUMPRIDAS_LIST')
            cumpridas_exploded['CUMPRIDA_TIPO'] = cumpridas_exploded['CUMPRIDAS_LIST']

            # Tabela: Detalhamento de tarefas cumpridas por consultor e tipo
            st.write("Contagem de Tarefas Cumprridas por Tipo e Consultor")
            
            try:
                crosstab_cumpridas = pd.crosstab(
                    index=cumpridas_exploded['CONSULTOR RESPONSÁVEL'],
                    columns=cumpridas_exploded['CUMPRIDA_TIPO']
                )
                
                # Garantir que todas as colunas de tarefas possíveis existam
                for tag in lista_tags:
                    if tag not in crosstab_cumpridas.columns:
                        crosstab_cumpridas[tag] = 0
                
                # Reordenar colunas e adicionar total
                crosstab_cumpridas = crosstab_cumpridas[lista_tags]
                crosstab_cumpridas['Total de Tarefas Cumpridas'] = crosstab_cumpridas.sum(axis=1)

                crosstab_sorted = crosstab_cumpridas.sort_values(by='Total de Tarefas Cumpridas', ascending=False)
                
                st.dataframe(ensure_pandas_df(crosstab_sorted), use_container_width=True)

                # Gráfico: Detalhamento de tarefas cumpridas por tipo e consultor
                st.write("Gráfico de Detalhamento das Tarefas Cumpridas")
                
                chart_data = crosstab_cumpridas[lista_tags].copy()
                st.bar_chart(chart_data)
                
            except Exception as e:
                st.error(f"Erro ao criar a tabela de tarefas cumpridas: {e}")
                
    except Exception as e:
        st.error(f"Erro ao processar tarefas cumpridas por responsável: {e}")

    # --- Exibição dos Dados Brutos Filtrados ---
    try:
        with st.expander("Ver dados brutos filtrados"):
            colunas_para_exibir = [
                'ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', 'STATUS GERAL', 'PENDENCIAS',
                'PROCURAÇÃO - STATUS', 'ANALISE - STATUS', 'TRADUÇÃO - STATUS', 
                'APOSTILA - STATUS', 'DRIVE - STATUS'
            ]
            colunas_existentes = [col for col in colunas_para_exibir if col in df_filtrado.columns]
            
            dados_brutos = df_filtrado[colunas_existentes]
            
            st.dataframe(ensure_pandas_df(dados_brutos), use_container_width=True)
            
    except Exception as e:
        st.error(f"Erro ao exibir dados brutos: {e}")