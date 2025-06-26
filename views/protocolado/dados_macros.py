import streamlit as st
import pandas as pd

def safe_pandas_df(df):
    """
    Função ultra-defensiva para garantir DataFrame pandas nativo.
    Recria completamente o DataFrame para evitar qualquer vestígio de narwhals.
    """
    if df is None:
        return pd.DataFrame()
    
    # Se tiver to_native, é a forma preferencial
    if hasattr(df, 'to_native'):
        try:
            native_df = df.to_native()
            # Certificar-se de que é realmente um DataFrame do pandas
            if isinstance(native_df, pd.DataFrame):
                return native_df
        except Exception:
            pass # Tentar outros métodos
    
    # Se for um DataFrame do pandas, retornar
    if isinstance(df, pd.DataFrame) and not hasattr(df, '__narwhals_df__'):
         return df

    # Converter para dict e recriar - método agressivo
    try:
        return pd.DataFrame(df.to_dict('records'))
    except:
        # Fallback: usar valores e colunas
        try:
            return pd.DataFrame(df.values, columns=df.columns)
        except:
            # Último fallback: tentar conversão direta, que pode falhar
            return pd.DataFrame(df)

def show_dados_macros(df_filtrado):
    """
    Exibe as métricas macro e de pendências.
    VERSÃO RECONSTRUÍDA para evitar problemas com narwhals.
    """
    st.subheader("Visão Geral", divider='blue')
    
    # Conversão defensiva inicial
    df_filtrado = safe_pandas_df(df_filtrado)
    
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
        # Filtrar pendências e garantir que seja uma Series
        mask = df_filtrado['PENDENCIAS'] != 'SEM PENDENCIAS'
        pendencias_gerais = df_filtrado.loc[mask, 'PENDENCIAS']
        
        if not pendencias_gerais.empty:
            lista_tags = [
                'Emissão', 'Comune', 'Analise Documental', 
                'Tradução', 'Apostilamento', 'Drive', 'Procuração'
            ]
            
            try:
                # Garantir que pendencias_gerais seja uma Series pandas nativa
                if hasattr(pendencias_gerais, 'to_pandas'):
                    pendencias_gerais = pendencias_gerais.to_pandas()
                
                # Processar as tags
                contagem_tags = pendencias_gerais.str.split(',').explode().str.strip().value_counts()
                
                # Converter para Series nativa se necessário
                if hasattr(contagem_tags, 'to_pandas'):
                    contagem_tags = contagem_tags.to_pandas()
                    
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
        pendencias_df = safe_pandas_df(pendencias_df)
        pendencias_df = pendencias_df[pendencias_df['PENDENCIAS'] != 'SEM PENDENCIAS']
        pendencias_df = safe_pandas_df(pendencias_df)

        if pendencias_df.empty:
            st.info("Nenhuma pendência encontrada para os filtros selecionados.")
        else:
            # Processar as pendências
            try:
                pendencias_df['PENDENCIAS_LIST'] = pendencias_df['PENDENCIAS'].str.split(',')
                pendencias_exploded = pendencias_df.explode('PENDENCIAS_LIST')
                pendencias_exploded = safe_pandas_df(pendencias_exploded)
                pendencias_exploded['PENDENCIA_TIPO'] = pendencias_exploded['PENDENCIAS_LIST'].str.strip()

                # Tabela: Detalhamento de pendências por consultor e tipo
                st.write("Contagem de Pendências por Tipo e Consultor")
                
                try:
                    crosstab_pendencias = pd.crosstab(
                        index=pendencias_exploded['CONSULTOR RESPONSÁVEL'],
                        columns=pendencias_exploded['PENDENCIA_TIPO']
                    )
                    crosstab_pendencias = safe_pandas_df(crosstab_pendencias)
                    
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
                    crosstab_pendencias = safe_pandas_df(crosstab_pendencias)
                    crosstab_pendencias['Total de Pendências'] = crosstab_pendencias.sum(axis=1)

                    crosstab_sorted = crosstab_pendencias.sort_values(by='Total de Pendências', ascending=False)
                    crosstab_sorted = safe_pandas_df(crosstab_sorted)
                    
                    st.dataframe(crosstab_sorted, use_container_width=True)

                    # Gráfico: Detalhamento de pendências por tipo e consultor
                    st.write("Gráfico de Detalhamento das Pendências")
                    
                    try:
                        chart_data = crosstab_pendencias.drop(columns=['Total de Pendências'])
                        final_chart_data = safe_pandas_df(chart_data)
                        
                        st.bar_chart(final_chart_data)
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao criar gráfico de barras: {e}")
                        st.write("Exibindo dados em formato tabular:")
                        try:
                            # Criar tabela simples com dados básicos
                            chart_data_fallback = safe_pandas_df(chart_data)
                            dados_tabela = []
                            for consultor in chart_data_fallback.index:
                                linha_dict = {'Consultor': consultor}
                                for coluna in chart_data_fallback.columns:
                                    linha_dict[coluna] = int(chart_data_fallback.loc[consultor, coluna])
                                dados_tabela.append(linha_dict)
                            
                            df_tabela = pd.DataFrame(dados_tabela)
                            st.dataframe(df_tabela)
                        except Exception as e2:
                            st.write(f"Não foi possível exibir os dados: {e2}")
                    
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
            dados_brutos = safe_pandas_df(dados_brutos)
            
            st.dataframe(dados_brutos, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erro ao exibir dados brutos: {e}") 