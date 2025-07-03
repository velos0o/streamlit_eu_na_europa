import streamlit as st
import pandas as pd
import plotly.express as px
from utils.google_sheets_connector import get_google_sheets_client, fetch_data_from_sheet
from utils.dataframe_utils import ensure_pandas_df
from datetime import datetime
import numpy as np

# Constantes para a planilha
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/15L7SdGgbF3nhiE3ptk7WFmuTwbxSY3rA1hfCnYmMFMM/edit"
GID = 170972868

@st.cache_data
def load_producao_data():
    """Carrega os dados de produtividade da planilha do Google."""
    try:
        client = get_google_sheets_client()
        if client:
            data = fetch_data_from_sheet(client, SPREADSHEET_URL, gid=GID)
            if data:
                df = pd.DataFrame(data)
                df = ensure_pandas_df(df) # Garante que é um DataFrame pandas
                return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados da produção: {e}")
    return pd.DataFrame()

def preprocess_data(df):
    """Realiza o pré-processamento dos dados."""
    if df.empty:
        return df

    # Converte a coluna de data/hora para datetime
    df['Data/Hora'] = pd.to_datetime(df['Data/Hora'], errors='coerce', format='%d/%m/%Y %H:%M:%S')
    
    # Remove linhas onde a data não pôde ser convertida
    df.dropna(subset=['Data/Hora'], inplace=True)
    
    # Extrai a data para o filtro e para o gráfico diário
    df['Data'] = df['Data/Hora'].dt.date
    
    return df

def display_filters(df):
    """Exibe os filtros na área principal do relatório, dentro de um expander."""
    with st.expander("Filtros de Produtividade", expanded=True):
        # Filtro de data em sua própria linha
        min_date = df['Data'].min()
        max_date = df['Data'].max()
        
        date_range = st.date_input(
            "Período",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="prod_date_range"
        )

        if len(date_range) != 2:
            start_date, end_date = None, None
        else:
            start_date, end_date = date_range

        # Filtros de Responsável e Tipo de Ação em uma nova linha com colunas
        col1, col2 = st.columns(2)
        with col1:
            responsaveis = sorted(df['Responsável'].unique())
            selected_responsaveis = st.multiselect(
                "Responsável",
                options=responsaveis,
                default=responsaveis,
                key="prod_responsaveis"
            )
        with col2:
            tipos_acao = sorted(df['Tipo de Ação'].unique())
            selected_tipos_acao = st.multiselect(
                "Tipo de Ação",
                options=tipos_acao,
                default=tipos_acao,
                key="prod_tipos_acao"
            )

    return (start_date, end_date) if start_date and end_date else None, selected_responsaveis, selected_tipos_acao

def show_produtividade():
    """Exibe o relatório completo de produtividade."""
    st.header("Análise de Produtividade - Protocolado")

    df_raw = load_producao_data()
    
    if df_raw.empty:
        st.warning("Não foi possível carregar os dados de produtividade. Verifique a planilha ou a conexão.")
        return
        
    df = preprocess_data(df_raw.copy())

    if df.empty:
        st.warning("Os dados estão vazios ou em formato incorreto após o pré-processamento.")
        return

    # Exibe filtros e obtém seleções
    date_range, selected_responsaveis, selected_tipos_acao = display_filters(df)

    if not date_range or not selected_responsaveis or not selected_tipos_acao:
        st.info("Ajuste os filtros para visualizar os dados.")
        return

    start_date, end_date = date_range
    start_date_dt = datetime.combine(start_date, datetime.min.time()).date()
    end_date_dt = datetime.combine(end_date, datetime.max.time()).date()

    # Aplica filtros
    filtered_df = df[
        (df['Data'] >= start_date_dt) &
        (df['Data'] <= end_date_dt) &
        (df['Responsável'].isin(selected_responsaveis)) &
        (df['Tipo de Ação'].isin(selected_tipos_acao))
    ]

    if filtered_df.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
        return

    # Métricas de produção
    st.subheader("Métricas Gerais")

    # Cálculos das métricas
    total_dia = filtered_df[filtered_df['Data'] == filtered_df['Data'].max()].shape[0] if not filtered_df.empty else 0
    
    latest_date_dt = pd.to_datetime(filtered_df['Data'].max()) if not filtered_df.empty else pd.to_datetime('today')
    start_of_week = (latest_date_dt - pd.to_timedelta(latest_date_dt.weekday(), unit='d')).date()
    total_semana = filtered_df[filtered_df['Data'] >= start_of_week].shape[0] if not filtered_df.empty else 0
    
    # Média diária baseada em dias úteis
    dias_uteis = np.busday_count(start_date_dt, end_date_dt + pd.Timedelta(days=1))
    media_diaria_uteis = filtered_df.shape[0] / dias_uteis if dias_uteis > 0 else 0
    
    responsavel_ativo = filtered_df['Responsável'].mode()[0] if not filtered_df.empty else "N/A"

    def render_metric_card(title, value, sub_title=""):
        st.markdown(f"""
        <div class="card-visao-geral card-visao-geral--summary">
            <div class="card-visao-geral__title">{title}</div>
            <div class="card-visao-geral__metrics">
                <span class="card-visao-geral__quantity">{value}</span>
            </div>
            <div class="card-visao-geral__subtitle">{sub_title}</div>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Produção no Último Dia", f"{total_dia}")
    with col2:
        render_metric_card("Produção na Última Semana", f"{total_semana}")
    with col3:
        render_metric_card("Média Diária (Dias Úteis)", f"{media_diaria_uteis:.2f}")
    with col4:
        render_metric_card("Responsável Mais Ativo", responsavel_ativo)
        
    st.divider()

    st.subheader("Resumo de Atividades por Responsável")
    
    # Tabela de produtividade
    produtividade_table = filtered_df.groupby('Responsável')['Família ID'].count().reset_index()
    produtividade_table.rename(columns={'Família ID': 'Total de Atividades'}, inplace=True)
    produtividade_table = produtividade_table.sort_values(by='Total de Atividades', ascending=False)
    
    st.dataframe(
        produtividade_table.style.format({"Total de Atividades": "{:}"}).background_gradient(cmap='Greens', subset=['Total de Atividades']),
        use_container_width=True
    )
    
    st.divider()

    st.subheader("Distribuição por Tipo de Ação")
    action_counts = filtered_df['Tipo de Ação'].value_counts().reset_index()
    action_counts.columns = ['Tipo de Ação', 'Quantidade']
    total_actions = action_counts['Quantidade'].sum()
    
    chart_data = action_counts
    small_slices = pd.DataFrame() # Inicializa o dataframe para garantir o escopo

    if total_actions > 0:
        action_counts['Percentual'] = (action_counts['Quantidade'] / total_actions) * 100
        
        # Agrupar fatias pequenas em "Outros"
        threshold = 3.0  # Limite de 3%
        large_slices = action_counts[action_counts['Percentual'] >= threshold]
        small_slices = action_counts[action_counts['Percentual'] < threshold]

        if not small_slices.empty and len(small_slices) > 1:
            outros_sum = small_slices['Quantidade'].sum()
            outros_percent = small_slices['Percentual'].sum()
            outros_row = pd.DataFrame([{'Tipo de Ação': 'Outros', 'Quantidade': outros_sum, 'Percentual': outros_percent}])
            chart_data = pd.concat([large_slices, outros_row], ignore_index=True)
    else:
        action_counts['Percentual'] = 0

    chart_data = chart_data.sort_values(by='Quantidade', ascending=False)
    
    color_sequence = px.colors.qualitative.Pastel

    col1, col2 = st.columns([5, 1.5]) # Proporção ajustada para afastar muito mais a legenda

    with col1:
        fig_pie = px.pie(
            chart_data,
            names='Tipo de Ação',
            values='Quantidade',
            title=" ",
            color_discrete_sequence=color_sequence,
            hole=0.4 # Transforma em Donut Chart
        )
        fig_pie.update_traces(
            textposition='outside',
            texttemplate='%{label}<br>%{value} (%{percent})',
            hoverinfo='label+percent+value',
            outsidetextfont={'size': 18} # Aumenta mais o tamanho da fonte externa
        )
        fig_pie.update_layout(
            legend_title_text='Ações',
            height=500,
            showlegend=False,
            margin=dict(t=40, b=40, l=40, r=40) # Adiciona margem para os textos não cortarem
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True) # Adiciona espaço para alinhar
        st.markdown("##### Legenda Detalhada")
        for index, row in chart_data.iterrows():
            color = color_sequence[index % len(color_sequence)]
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 12px; font-size: 14px;">
                <span style="width: 18px; height: 18px; background-color: {color}; border-radius: 5px; margin-right: 12px; display: inline-block; flex-shrink: 0;"></span>
                <div style="line-height: 1.2;">
                    <strong>{row['Tipo de Ação']}</strong><br>
                    <small style="color: #666;">{row['Quantidade']} atividades ({row['Percentual']:.1f}%)</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Expansor para detalhar a categoria "Outros"
    if not small_slices.empty and len(small_slices) > 1:
        with st.expander("🔍 Ver detalhes da categoria 'Outros'"):
            st.markdown("###### Ações com menos de 3% de representatividade")
            detailed_others = small_slices.sort_values(by='Quantidade', ascending=True)

            fig_others = px.bar(
                detailed_others, x='Quantidade', y='Tipo de Ação', orientation='h',
                text='Quantidade', title=None
            )
            fig_others.update_layout(
                yaxis_title=None, xaxis_title="Quantidade",
                height=len(detailed_others) * 35 + 80,
                margin=dict(l=10, r=10, t=30, b=10)
            )
            fig_others.update_traces(
                textposition='outside', marker=dict(color='rgb(158, 202, 225)')
            )
            st.plotly_chart(fig_others, use_container_width=True)

    st.divider()

    st.subheader("Produtividade Diária")
    daily_prod = filtered_df.groupby('Data')['Família ID'].count().reset_index()
    daily_prod.rename(columns={'Família ID': 'Total de Atividades'}, inplace=True)
    # Garante que a data seja tratada como categoria para mostrar todos os dias
    daily_prod['Data'] = pd.to_datetime(daily_prod['Data']).dt.strftime('%d/%m/%Y')

    fig_bar = px.bar(
        daily_prod,
        x='Data',
        y='Total de Atividades',
        title=" ",
        text_auto=True
    )
    fig_bar.update_traces(
        textposition='outside', marker=dict(color='rgb(34, 139, 34)')
    )
    fig_bar.update_layout(
        xaxis_title="Data", 
        yaxis_title="Nº de Atividades",
        height=500,
        xaxis={'type': 'category'} # Força o eixo X a ser categórico
    )
    # Adiciona a linha de média
    fig_bar.add_hline(
        y=media_diaria_uteis, 
        line_dash="dot", 
        annotation_text=f"Média p/ Dia Útil: {media_diaria_uteis:.2f}", 
        annotation_position="bottom right",
        annotation_font_color="green"
    )
    st.plotly_chart(fig_bar, use_container_width=True) 