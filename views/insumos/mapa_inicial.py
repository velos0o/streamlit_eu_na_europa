import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from .metrics import display_metrics
from .calendar_view import display_reuniao_schedule

def show_mapa_inicial(df_page: pd.DataFrame):
    """
    Renderiza a página Mapa Inicial (ID 114) usando os componentes
    de métricas e calendário.
    """
    st.title("Mapa Inicial")
    st.markdown("Visão geral dos registros e agendamentos da categoria Mapa Inicial.")
    
    st.markdown("---")
    
    # Exibir métricas
    display_metrics(df_page)
    
    st.markdown("---")
    
    # Exibir calendário de reuniões
    display_reuniao_schedule(df_page)
    
    st.markdown("---")

    # --- Análise Detalhada ---
    st.subheader("Análise Detalhada por Responsável e Etapa")
    
    # Fazer uma cópia para as manipulações
    df_analysis = df_page.copy()

    # --- Filtros ---
    col1, col2 = st.columns(2)
    
    # Filtro por Responsável
    with col1:
        if 'ASSIGNED_BY_NAME' in df_analysis.columns:
            responsaveis = sorted(df_analysis['ASSIGNED_BY_NAME'].unique())
            selected_responsaveis = st.multiselect(
                "Filtrar por Responsável:",
                options=responsaveis,
                default=responsaveis # Padrão: todos selecionados
            )
        else:
            selected_responsaveis = []
            st.info("Coluna de responsável não encontrada.")

    # Filtro por Data de Reunião
    with col2:
        date_col = 'UF_CRM_42_DATA_REUNIAO'
        if date_col in df_analysis.columns:
            df_analysis[date_col] = pd.to_datetime(df_analysis[date_col], errors='coerce')
            
            valid_dates = df_analysis.dropna(subset=[date_col])
            
            if not valid_dates.empty:
                min_date = valid_dates[date_col].min().date()
                max_date = valid_dates[date_col].max().date()
                
                # Define a semana atual como padrão
                today = datetime.now().date()
                start_of_week = today - timedelta(days=today.weekday())
                end_of_week = start_of_week + timedelta(days=6)

                selected_date_range = st.date_input(
                    "Filtrar por Data de Reunião:",
                    value=(start_of_week, end_of_week),
                    min_value=min_date,
                    max_value=max_date
                )
            else:
                selected_date_range = None
                st.info("Não há datas de reunião válidas para filtrar.")
        else:
            selected_date_range = None
            st.info("Coluna de data de reunião não encontrada.")

    # Aplicar filtros
    if selected_responsaveis:
        df_analysis = df_analysis[df_analysis['ASSIGNED_BY_NAME'].isin(selected_responsaveis)]
    
    if selected_date_range and len(selected_date_range) == 2:
        start_date = pd.to_datetime(selected_date_range[0])
        end_date = pd.to_datetime(selected_date_range[1])
        # Filtra o intervalo, ignorando NaT
        df_analysis = df_analysis[df_analysis[date_col].between(start_date, end_date)]

    # Criar e exibir a tabela de resumo pivotada
    if not df_analysis.empty and 'ASSIGNED_BY_NAME' in df_analysis.columns and 'STAGE_NAME' in df_analysis.columns:
        # Usar groupby().unstack() para mais robustez
        summary_df = df_analysis.groupby(['ASSIGNED_BY_NAME', 'STAGE_NAME'])['ID'].count().unstack(fill_value=0)
        
        # Garante que as colunas 'FILA' e 'PRONTO' existam
        for stage in ['FILA', 'PRONTO']:
            if stage not in summary_df.columns:
                summary_df[stage] = 0
        
        # Adiciona a coluna Total somando apenas FILA e PRONTO
        summary_df['Total'] = summary_df['FILA'] + summary_df['PRONTO']
        
        # Selecionar as colunas desejadas e resetar o índice
        final_df = summary_df[['FILA', 'PRONTO', 'Total']].reset_index()
        
        # Renomear a coluna de responsável
        final_df.rename(columns={'ASSIGNED_BY_NAME': 'Responsável'}, inplace=True)
        
        st.dataframe(final_df, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    
    st.markdown("---")
    
    # Exibir tabela de dados brutos da página
    st.subheader("Dados Completos da Categoria")
    if df_page.empty:
        st.warning("Nenhum dado encontrado para a categoria (ID 114).")
    else:
        st.dataframe(df_page) 