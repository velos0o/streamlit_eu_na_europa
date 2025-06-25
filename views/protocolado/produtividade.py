import streamlit as st
import pandas as pd
import altair as alt

def safe_pandas_df(df):
    """
    Função ultra-defensiva para garantir DataFrame pandas nativo.
    Recria completamente o DataFrame para evitar qualquer vestígio de narwhals.
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Converter para dict e recriar - método mais agressivo
    try:
        return pd.DataFrame(df.to_dict('records'))
    except:
        # Fallback: usar valores e colunas
        try:
            return pd.DataFrame(df.values, columns=df.columns)
        except:
            # Último fallback: tentar conversão direta
            return pd.DataFrame(df)

def show_produtividade(df_protocolados):
    """
    Exibe a análise de produtividade, mostrando tarefas concluídas por responsável e por data.
    VERSÃO RECONSTRUÍDA para evitar problemas com narwhals.
    """
    st.header("Análise de Produtividade", divider='rainbow')
    st.write("Acompanhe o número de tarefas concluídas pelos consultores ao longo do tempo.")

    # Conversão defensiva inicial
    df_protocolados = safe_pandas_df(df_protocolados)
    
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

    # --- Preparação dos Dados (RECONSTRUÍDA) ---
    lista_tarefas = []
    
    for etapa, data_col in mapeamento_etapas.items():
        if data_col not in df_protocolados.columns:
            continue
            
        # Seleção de colunas com conversão defensiva
        try:
            df_etapa = df_protocolados[['ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', data_col]].copy()
            df_etapa = safe_pandas_df(df_etapa)
            
            # Limpeza de dados
            df_etapa = df_etapa.dropna(subset=[data_col, 'CONSULTOR RESPONSÁVEL'])
            df_etapa = df_etapa[df_etapa['CONSULTOR RESPONSÁVEL'].str.strip() != '']
            
            if df_etapa.empty:
                continue

            # Conversão de datas com tratamento de erro
            try:
                df_etapa[data_col] = pd.to_datetime(
                    df_etapa[data_col], 
                    format='%d/%m/%Y', 
                    dayfirst=True, 
                    errors='coerce'
                )
                df_etapa = df_etapa.dropna(subset=[data_col])
            except Exception as e:
                st.warning(f"Erro ao processar datas para {etapa}: {e}")
                continue
            
            if df_etapa.empty:
                continue
                
            # Renomear e adicionar etapa
            df_etapa = df_etapa.rename(columns={data_col: 'Data Conclusão'})
            df_etapa['Etapa'] = etapa
            
            # Conversão defensiva final
            df_etapa = safe_pandas_df(df_etapa)
            lista_tarefas.append(df_etapa)
            
        except Exception as e:
            st.warning(f"Erro ao processar etapa {etapa}: {e}")
            continue
    
    if not lista_tarefas:
        st.info("Nenhuma tarefa concluída foi encontrada.")
        return
    
    # Concatenação com conversão defensiva
    try:
        df_produtividade = pd.concat(lista_tarefas, ignore_index=True)
        df_produtividade = safe_pandas_df(df_produtividade)
    except Exception as e:
        st.error(f"Erro ao consolidar dados de produtividade: {e}")
        return

    # --- Filtros ---
    st.subheader("Filtros", divider='blue')
    col1, col2 = st.columns(2)

    with col1:
        try:
            consultores_unicos = sorted(df_produtividade['CONSULTOR RESPONSÁVEL'].unique())
            consultores_selecionados = st.multiselect(
                "Selecione o(s) Consultor(es)",
                options=consultores_unicos,
                default=consultores_unicos
            )
        except Exception as e:
            st.error(f"Erro ao carregar consultores: {e}")
            return
    
    with col2:
        try:
            # Filtrar para obter intervalo de datas
            df_para_datas = df_produtividade[
                df_produtividade['CONSULTOR RESPONSÁVEL'].isin(consultores_selecionados)
            ]
            df_para_datas = safe_pandas_df(df_para_datas)
            
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
        except Exception as e:
            st.error(f"Erro ao configurar filtro de data: {e}")
            return

    # Validação do filtro de data
    if len(data_selecionada) != 2:
        st.warning("Por favor, selecione um período de início e fim no filtro de data para continuar.")
        st.stop()
        
    start_date, end_date = pd.to_datetime(data_selecionada[0]), pd.to_datetime(data_selecionada[1])

    # --- Aplicação dos Filtros ---
    try:
        df_filtrado_prod = df_produtividade[
            (df_produtividade['CONSULTOR RESPONSÁVEL'].isin(consultores_selecionados)) &
            (df_produtividade['Data Conclusão'] >= start_date) &
            (df_produtividade['Data Conclusão'] <= end_date)
        ]
        df_filtrado_prod = safe_pandas_df(df_filtrado_prod)
    except Exception as e:
        st.error(f"Erro ao aplicar filtros: {e}")
        return

    if df_filtrado_prod.empty:
        st.warning("Nenhuma tarefa concluída encontrada para os filtros selecionados.")
        return

    # --- Métricas Gerais ---
    try:
        total_tarefas = len(df_filtrado_prod)
        dias_no_periodo = (end_date - start_date).days + 1
        media_diaria = total_tarefas / dias_no_periodo if dias_no_periodo > 0 else 0
        
        m_col1, m_col2 = st.columns(2)
        m_col1.metric("Total de Tarefas Concluídas", f"{total_tarefas}")
        m_col2.metric("Média Diária de Conclusão", f"{media_diaria:.2f}")
    except Exception as e:
        st.error(f"Erro ao calcular métricas: {e}")

    # --- Gráficos (RECONSTRUÍDO COM MÁXIMA PROTEÇÃO) ---
    st.subheader("Visualização da Produtividade", divider='blue')
    
    try:
        # Agrupamento com conversão defensiva
        produtividade_diaria = df_filtrado_prod.groupby(
            df_filtrado_prod['Data Conclusão'].dt.date
        ).size().reset_index(name='Contagem')
        
        # Conversão ultra-defensiva para o DataFrame
        produtividade_diaria = safe_pandas_df(produtividade_diaria)
        produtividade_diaria = produtividade_diaria.rename(columns={'Data Conclusão': 'Data'})
        
        # CRIAÇÃO DE DATAFRAME COMPLETAMENTE NOVO PARA ALTAIR
        # Método mais agressivo possível
        chart_data = []
        for _, row in produtividade_diaria.iterrows():
            chart_data.append({
                'Data': row['Data'],
                'Contagem': int(row['Contagem'])
            })
        
        # DataFrame completamente novo, sem qualquer vestígio anterior
        df_chart = pd.DataFrame(chart_data)
        
        # Verificação final de tipos
        st.write(f"🔍 Tipo do DataFrame para gráfico: {type(df_chart)}")
        st.write(f"🔍 Colunas: {list(df_chart.columns)}")
        st.write(f"🔍 Shape: {df_chart.shape}")
        
        # Criação do gráfico Altair
        base = alt.Chart(df_chart).encode(
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
        
    except Exception as e:
        st.error(f"❌ Erro ao criar gráfico: {e}")
        st.write("Tentando exibir dados em formato tabular...")
        try:
            st.dataframe(produtividade_diaria)
        except:
            st.write("Não foi possível exibir os dados.")

    # --- Tabela de Produtividade ---
    st.subheader("Detalhamento por Consultor e Etapa", divider='blue')
    
    try:
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
        
        # Conversão defensiva da tabela
        tabela_produtividade = safe_pandas_df(tabela_produtividade)
        st.dataframe(tabela_produtividade, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao criar tabela de produtividade: {e}") 