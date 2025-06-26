import streamlit as st
import pandas as pd
import altair as alt
from utils.dataframe_utils import ensure_pandas_df

def show_produtividade(df_protocolados):
    """
    Exibe a análise de produtividade, mostrando tarefas concluídas por responsável e por data.
    """
    st.header("Análise de Produtividade", divider='rainbow')
    st.write("Acompanhe o número de tarefas concluídas pelos consultores ao longo do tempo.")

    # Garante que o dataframe de entrada seja pandas nativo
    df_protocolados = ensure_pandas_df(df_protocolados)
    
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
        if data_col not in df_protocolados.columns:
            continue
            
        try:
            df_etapa = df_protocolados[['ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', data_col]].copy()
            
            # Limpeza de dados
            df_etapa = df_etapa.dropna(subset=[data_col, 'CONSULTOR RESPONSÁVEL'])
            df_etapa = df_etapa[df_etapa['CONSULTOR RESPONSÁVEL'].str.strip() != '']
            
            if df_etapa.empty:
                continue

            # Conversão de datas com tratamento de erro
            df_etapa[data_col] = pd.to_datetime(
                df_etapa[data_col], 
                format='%d/%m/%Y', 
                dayfirst=True, 
                errors='coerce'
            )
            df_etapa = df_etapa.dropna(subset=[data_col])
            
            if df_etapa.empty:
                continue
                
            # Renomear e adicionar etapa
            df_etapa = df_etapa.rename(columns={data_col: 'Data Conclusão'})
            df_etapa['Etapa'] = etapa
            
            lista_tarefas.append(df_etapa)
            
        except Exception as e:
            st.warning(f"Erro ao processar etapa {etapa}: {e}")
            continue
    
    if not lista_tarefas:
        st.info("Nenhuma tarefa concluída foi encontrada.")
        return
    
    try:
        df_produtividade = pd.concat(lista_tarefas, ignore_index=True)
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
            df_para_datas = df_produtividade[
                df_produtividade['CONSULTOR RESPONSÁVEL'].isin(consultores_selecionados)
            ]
            
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

    # --- Gráficos ---
    st.subheader("Visualização da Produtividade", divider='blue')
    
    try:
        # Agrupamento
        produtividade_diaria = df_filtrado_prod.groupby(
            df_filtrado_prod['Data Conclusão'].dt.date
        ).size().reset_index(name='Contagem')
        
        produtividade_diaria = produtividade_diaria.rename(columns={'Data Conclusão': 'Data'})
        
        # Garante que os dados para o gráfico são um dataframe pandas nativo
        df_chart = ensure_pandas_df(produtividade_diaria)
        
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
            st.dataframe(ensure_pandas_df(produtividade_diaria))
        except:
            st.write("Não foi possível exibir os dados.")

    # --- Tabela de Produtividade ---
    st.subheader("Detalhamento por Consultor e Etapa", divider='blue')
    
    try:
        # Criar pivot table
        tabela_produtividade = pd.pivot_table(
            df_filtrado_prod,
            values='ID FAMÍLIA',
            index='CONSULTOR RESPONSÁVEL',
            columns='Etapa',
            aggfunc='count',
            fill_value=0,
            margins=True,
            margins_name='Total'
        )
        
        st.dataframe(ensure_pandas_df(tabela_produtividade), use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao criar tabela de produtividade: {e}")
        # Fallback: mostrar dados básicos
        try:
            st.write("Dados básicos de produtividade:")
            resumo = df_filtrado_prod.groupby(['CONSULTOR RESPONSÁVEL', 'Etapa']).size().reset_index(name='Quantidade')
            st.dataframe(ensure_pandas_df(resumo), use_container_width=True)
        except Exception as e2:
            st.error(f"Erro no fallback: {e2}") 