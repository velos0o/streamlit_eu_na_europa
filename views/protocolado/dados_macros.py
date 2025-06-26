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
                        # CORREÇÃO: Criar um novo DataFrame completamente independente
                        # Usar apenas as colunas de tags (sem a coluna Total)
                        chart_data = crosstab_pendencias[lista_tags].copy()
                        
                        # Converter para dicionário e depois para DataFrame para garantir tipo correto
                        chart_dict = chart_data.to_dict()
                        chart_data_clean = pd.DataFrame(chart_dict)
                        
                        # Alternativa 1: Usar st.bar_chart com dados convertidos
                        st.bar_chart(chart_data_clean)
                        
                    except Exception as e:
                        # Se ainda houver erro, tentar com plotly ou altair
                        try:
                            st.warning("Tentando método alternativo de visualização...")
                            
                            # Alternativa 2: Usar st.dataframe com style
                            chart_data_styled = chart_data.style.background_gradient(cmap='Blues')
                            st.dataframe(chart_data_styled, use_container_width=True)
                            
                        except:
                            # Alternativa 3: Usar st.columns com métricas
                            st.error(f"❌ Erro ao criar gráfico de barras: {e}")
                            st.info("Exibindo dados em formato alternativo:")
                            
                            for consultor in chart_data.index:
                                st.write(f"**{consultor}**")
                                cols = st.columns(len(lista_tags))
                                for i, tag in enumerate(lista_tags):
                                    with cols[i]:
                                        st.metric(tag, chart_data.loc[consultor, tag])
                    
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