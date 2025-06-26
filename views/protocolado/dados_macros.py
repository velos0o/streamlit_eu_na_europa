import streamlit as st
import pandas as pd
from utils.dataframe_utils import ensure_pandas_df

def show_dados_macros(df_filtrado):
    """
    Exibe as métricas macro e de pendências.
    """
    st.subheader("Visão Geral", divider='blue')
    
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

    # Contagem total de cada tipo de pendência
    try:
        # Filtrar pendências
        mask = df_filtrado['PENDENCIAS'] != 'SEM PENDENCIAS'
        pendencias_gerais = df_filtrado.loc[mask, 'PENDENCIAS']
        
        if not pendencias_gerais.empty:
            lista_tags = [
                'Emissão', 'Comune', 'Analise Documental', 
                'Tradução', 'Apostilamento', 'Drive', 'Procuração'
            ]
            
            try:
                # Processar as tags
                contagem_tags = pendencias_gerais.str.split(',').explode().str.strip().value_counts()
                
            except Exception as e:
                st.warning(f"Erro ao processar contagem de tags: {e}")
                contagem_tags = pd.Series(dtype=int)
                
            st.write("Totais por Tipo de Pendência:")
            
            # Exibir métricas em colunas
            num_cols = 4 
            cols = st.columns(num_cols)
            
            for i, tag in enumerate(lista_tags):
                with cols[i % num_cols]:
                    try:
                        valor = contagem_tags.get(tag, 0)
                        st.metric(label=tag, value=valor)
                    except Exception as e:
                        st.metric(label=tag, value=0)
                        
    except Exception as e:
        st.error(f"Erro ao processar pendências gerais: {e}")

    # --- Análise 2: Pendências por Responsável ---
    st.subheader("Pendências por Responsável", divider='blue')

    try:
        pendencias_df = df_filtrado[['CONSULTOR RESPONSÁVEL', 'PENDENCIAS']].copy()
        pendencias_df = pendencias_df[pendencias_df['PENDENCIAS'] != 'SEM PENDENCIAS']

        if pendencias_df.empty:
            st.info("Nenhuma pendência encontrada para os filtros selecionados.")
        else:
            # Processar as pendências
            try:
                pendencias_df['PENDENCIAS_LIST'] = pendencias_df['PENDENCIAS'].str.split(',')
                pendencias_exploded = pendencias_df.explode('PENDENCIAS_LIST')
                pendencias_exploded['PENDENCIA_TIPO'] = pendencias_exploded['PENDENCIAS_LIST'].str.strip()

                # Tabela: Detalhamento de pendências por consultor e tipo
                st.write("Contagem de Pendências por Tipo e Consultor")
                
                try:
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

                    crosstab_sorted = crosstab_pendencias.sort_values(by='Total de Pendências', ascending=False)
                    
                    st.dataframe(ensure_pandas_df(crosstab_sorted), use_container_width=True)

                    # Gráfico: Detalhamento de pendências por tipo e consultor
                    st.write("Gráfico de Detalhamento das Pendências")
                    
                    try:
                        # CORREÇÃO: Garantir que chart_data seja um pandas DataFrame nativo
                        chart_data = crosstab_pendencias.drop(columns=['Total de Pendências'])
                        
                        # Converter explicitamente para pandas DataFrame nativo
                        if hasattr(chart_data, 'to_native'):
                            chart_data = chart_data.to_native()
                        elif not isinstance(chart_data, pd.DataFrame):
                            chart_data = pd.DataFrame(chart_data)
                        
                        # Alternativa: usar o método nativo do pandas para garantir o tipo correto
                        chart_data = pd.DataFrame(chart_data.values, 
                                                index=chart_data.index, 
                                                columns=chart_data.columns)
                        
                        st.bar_chart(chart_data)
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao criar gráfico de barras: {e}")
                        # Adicionar debug para entender melhor o erro
                        st.write(f"Tipo do chart_data: {type(chart_data)}")
                    
                except Exception as e:
                    st.error(f"Erro ao criar crosstab: {e}")
                    
            except Exception as e:
                st.error(f"Erro ao processar pendências explodidas: {e}")
                
    except Exception as e:
        st.error(f"Erro ao processar pendências por responsável: {e}")

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