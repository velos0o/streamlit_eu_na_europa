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

    lista_tags = [
        'Emissão', 'Comune', 'Analise Documental', 
        'Tradução', 'Apostilamento', 'Drive', 'Procuração'
    ]

    mapeamento_conclusao = {
        'Procuração': ('PROCURAÇÃO - STATUS', 'Concluida'),
        'Analise Documental': ('ANALISE - STATUS', 'Positiva'),
        'Tradução': ('TRADUÇÃO - STATUS', 'Concluido'),
        'Apostilamento': ('APOSTILA - STATUS', 'Concluido'),
        'Drive': ('DRIVE - STATUS', 'Concluido')
    }
    
    col1, col2 = st.columns(2)
    with col1:
        try:
            total_familias = df_filtrado['ID FAMÍLIA'].nunique()
            st.metric("TOTAL DE FAMÍLIAS", total_familias)
        except Exception as e:
            st.error(f"Erro ao calcular total de famílias: {e}")

    # Contagem total de cada tipo de tarefa cumprida
    try:
        contagem_tags = {}
        for etapa in lista_tags:
            count = 0
            if etapa in mapeamento_conclusao:
                coluna, valor_sucesso = mapeamento_conclusao[etapa]
                if coluna in df_filtrado.columns:
                    # Conta famílias únicas onde o status é o de sucesso (ignorando case e espaços)
                    condicao = df_filtrado[coluna].str.strip().str.lower() == valor_sucesso.lower()
                    count = df_filtrado.loc[condicao.fillna(False)]['ID FAMÍLIA'].nunique()
            else:
                # Lógica antiga para etapas não mapeadas (Emissão, Comune)
                count = df_filtrado.loc[~df_filtrado['PENDENCIAS'].str.contains(etapa, case=False, na=False), 'ID FAMÍLIA'].nunique()
            contagem_tags[etapa] = count
        
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
        lista_cumpridas_por_responsavel = []

        # Iterar sobre as etapas para construir a lista de cumpridas
        for etapa in lista_tags:
            df_temp = pd.DataFrame()
            if etapa in mapeamento_conclusao:
                coluna, valor_sucesso = mapeamento_conclusao[etapa]
                if coluna in df_filtrado.columns and not df_filtrado[coluna].isnull().all():
                    condicao = df_filtrado[coluna].str.strip().str.lower() == valor_sucesso.lower()
                    df_etapa_cumprida = df_filtrado.loc[condicao.fillna(False)]
                    # Seleciona as colunas necessárias e adiciona o tipo de tarefa
                    df_temp = df_etapa_cumprida[['CONSULTOR RESPONSÁVEL', 'ID FAMÍLIA']].copy()
                    df_temp['CUMPRIDA_TIPO'] = etapa
            else: # Lógica antiga para Emissão e Comune
                df_etapa_cumprida = df_filtrado.loc[~df_filtrado['PENDENCIAS'].str.contains(etapa, case=False, na=False)]
                df_temp = df_etapa_cumprida[['CONSULTOR RESPONSÁVEL', 'ID FAMÍLIA']].copy()
                df_temp['CUMPRIDA_TIPO'] = etapa
            
            if not df_temp.empty:
                lista_cumpridas_por_responsavel.append(df_temp)

        if not lista_cumpridas_por_responsavel:
            st.info("Nenhum dado encontrado para os filtros selecionados.")
        else:
            # Concatena os dataframes e remove duplicatas para não contar a mesma família/tarefa/consultor mais de uma vez
            cumpridas_df = pd.concat(lista_cumpridas_por_responsavel, ignore_index=True)
            cumpridas_df.drop_duplicates(inplace=True)

            # Tabela: Detalhamento de tarefas cumpridas por consultor e tipo
            st.write("Contagem de Tarefas Cumpridas por Tipo e Consultor")
            
            try:
                crosstab_cumpridas = pd.crosstab(
                    index=cumpridas_df['CONSULTOR RESPONSÁVEL'],
                    columns=cumpridas_df['CUMPRIDA_TIPO']
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