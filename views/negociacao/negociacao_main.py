import streamlit as st
import pandas as pd
import plotly.express as px
from .data_loader import carregar_dados_negociacao
from datetime import datetime, timedelta
import re
import numpy as np

def parse_custom_date(date_str):
    """
    Converte uma string de data customizada (incluindo 'hoje', 'ontem', 'amanhã')
    para um objeto de data.
    """
    if not isinstance(date_str, str):
        return None

    today = datetime.now().date()
    date_str_lower = date_str.lower()

    if 'hoje' in date_str_lower:
        return today
    elif 'ontem' in date_str_lower:
        return today - timedelta(days=1)
    elif 'amanhã' in date_str_lower:
        return today + timedelta(days=1)
    else:
        match = re.search(r'(\d{2}/\d{2}/\d{4})', date_str_lower)
        if match:
            try:
                return pd.to_datetime(match.group(1), format='%d/%m/%Y', errors='coerce').date()
            except (ValueError, TypeError):
                return None
    return None

def show_negociacao():
    st.title("Negociação - Famílias")

    with st.spinner("Carregando dados de negociação..."):
        df_negociacao = carregar_dados_negociacao()

    if df_negociacao.empty:
        st.info("Não há dados de negociação para exibir.")
        return

    # --- Filtros Principais ---
    st.header("Filtros")
    col1, col2 = st.columns(2)

    all_responsaveis = sorted(df_negociacao['ASSIGNED_BY_NAME'].dropna().unique())

    with col1:
        selected_responsaveis = st.multiselect(
            "Responsável",
            options=all_responsaveis,
            default=all_responsaveis,
            key="main_responsavel_filter"
        )

    with col2:
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        next_month_start = (start_of_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_of_month = next_month_start - timedelta(days=1)
        
        selected_date_range = st.date_input(
            "Período da Reunião",
            value=(start_of_month, end_of_month),
            min_value=datetime(2023, 1, 1).date(),
            max_value=today + timedelta(days=365),
            key="main_date_filter"
        )
    
    if len(selected_date_range) != 2:
        st.warning("Por favor, selecione um intervalo de datas válido.")
        return
        
    start_date, end_date = selected_date_range

    # --- Aplicação dos Filtros ---
    df_filtrado = df_negociacao[df_negociacao['ASSIGNED_BY_NAME'].isin(selected_responsaveis)]

    # Indicador: Total de Famílias em Negociação Ativa (baseado no filtro de responsável)
    final_stages = ["C34:WON", "C34:LOSE", "C34:UC_D5LB1N"]
    df_active_negociacao = df_filtrado[~df_filtrado['STAGE_ID'].isin(final_stages)]
    total_active = len(df_active_negociacao)
    st.metric(label="Total de Famílias em Negociação Ativa", value=total_active)

    st.markdown("---")

    # Análise de Reuniões Agendadas
    st.header("Análise de Reuniões Agendadas")

    campo_data_reuniao = 'UF_CRM_1737689240946'

    if campo_data_reuniao not in df_filtrado.columns:
        st.warning(f"A coluna '{campo_data_reuniao}' (data da reunião) não foi encontrada nos dados.")
        return

    df_reunioes = df_filtrado.copy()
    df_reunioes['data_reuniao'] = df_reunioes[campo_data_reuniao].apply(parse_custom_date)
    
    df_reunioes.dropna(subset=['data_reuniao'], inplace=True)
    df_reunioes = df_reunioes[(df_reunioes['data_reuniao'] >= start_date) & (df_reunioes['data_reuniao'] <= end_date)]

    if df_reunioes.empty:
        st.info("Não há reuniões com datas válidas para o período e responsável selecionado.")
    else:
        contagem_reunioes_por_dia = df_reunioes.groupby('data_reuniao').size().reset_index(name='numero_de_reunioes')
        
        all_days_df = pd.DataFrame(pd.date_range(start=start_date, end=end_date), columns=['data_reuniao'])
        all_days_df['data_reuniao'] = all_days_df['data_reuniao'].dt.date

        contagem_completa = pd.merge(all_days_df, contagem_reunioes_por_dia, on='data_reuniao', how='left').fillna(0)
        contagem_completa['numero_de_reunioes'] = contagem_completa['numero_de_reunioes'].astype(int)

        fig = px.line(
            contagem_completa,
            x='data_reuniao',
            y='numero_de_reunioes',
            title='Número de Reuniões Agendadas por Dia',
            labels={'data_reuniao': 'Data da Reunião', 'numero_de_reunioes': 'Nº de Reuniões'},
            markers=True,
            text='numero_de_reunioes'
        )
        fig.update_traces(textposition="top center")
        fig.update_xaxes(dtick='D1', tickformat='%d/%m')
        st.plotly_chart(fig, use_container_width=True)

        df_display = contagem_completa[contagem_completa['numero_de_reunioes'] > 0].copy()
        df_display['data_reuniao'] = df_display['data_reuniao'].apply(lambda d: d.strftime('%d-%m-%Y'))
        st.dataframe(df_display.rename(columns={
            'data_reuniao': 'Data da Reunião',
            'numero_de_reunioes': 'Número de Reuniões'
        }), use_container_width=True)

    st.markdown("---")
    
    # --- Tabela de Resumo por Responsável (Filtros Independentes) ---
    st.header("Resumo por Responsável")

    resumo_col1, resumo_col2 = st.columns(2)
    with resumo_col1:
        resumo_responsaveis = st.multiselect(
            "Responsável (para resumo)",
            options=all_responsaveis,
            default=all_responsaveis,
            key="summary_responsavel_filter"
        )
    
    with resumo_col2:
        resumo_date_range = st.date_input(
            "Período (para resumo)",
            value=(start_of_month, end_of_month),
            min_value=datetime(2023, 1, 1).date(),
            max_value=today + timedelta(days=365),
            key="summary_date_filter"
        )

    if len(resumo_date_range) == 2:
        resumo_start_date, resumo_end_date = resumo_date_range
        
        df_resumo_base = df_negociacao[df_negociacao['ASSIGNED_BY_NAME'].isin(resumo_responsaveis)]
        df_resumo_base['data_reuniao'] = df_resumo_base[campo_data_reuniao].apply(parse_custom_date)
        df_resumo_base.dropna(subset=['data_reuniao'], inplace=True)
        df_resumo_base = df_resumo_base[(df_resumo_base['data_reuniao'] >= resumo_start_date) & (df_resumo_base['data_reuniao'] <= resumo_end_date)]

        if not df_resumo_base.empty:
            dias_uteis = np.busday_count(resumo_start_date, resumo_end_date + timedelta(days=1))
            dias_filtrados = (resumo_end_date - resumo_start_date).days + 1

            resumo_reunioes = df_resumo_base.groupby('ASSIGNED_BY_NAME').size().reset_index(name='reuniao_total')

            if dias_uteis > 0:
                resumo_reunioes['media_dia_util'] = (resumo_reunioes['reuniao_total'] / dias_uteis)
            else:
                resumo_reunioes['media_dia_util'] = 0
            
            resumo_reunioes['dias_filtrados'] = dias_filtrados

            resumo_display = resumo_reunioes[['ASSIGNED_BY_NAME', 'reuniao_total', 'media_dia_util', 'dias_filtrados']]
            resumo_display = resumo_display.rename(columns={
                'ASSIGNED_BY_NAME': 'Responsável',
                'reuniao_total': 'Reuniões no Período',
                'media_dia_util': 'Média Diária (dias úteis)',
                'dias_filtrados': 'Dias no Filtro'
            })
            
            resumo_display['Média Diária (dias úteis)'] = resumo_display['Média Diária (dias úteis)'].map('{:.2f}'.format)
            
            st.dataframe(resumo_display, use_container_width=True)
        else:
            st.info("Não há dados de reuniões no período selecionado para gerar o resumo.")
    else:
        st.warning("Por favor, selecione um intervalo de datas válido para o resumo.") 