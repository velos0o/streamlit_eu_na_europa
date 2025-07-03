import streamlit as st
import pandas as pd
import plotly.express as px
from ..data_loader import get_criacao_adendo_data
from utils.dataframe_utils import ensure_pandas_df

def create_donut_chart_with_legend(df, column_name, chart_title, color_sequence, key, chart_type='pie'):
    """Cria um gráfico de pizza/donut com uma legenda detalhada ao lado."""
    if df.empty or column_name not in df or df[column_name].isnull().all():
        st.info(f"Não há dados disponíveis para a análise de '{column_name}'.")
        return

    counts = df[column_name].value_counts().reset_index()
    counts.columns = [column_name, 'Quantidade']
    total = counts['Quantidade'].sum()
    counts['Percentual'] = (counts['Quantidade'] / total) * 100 if total > 0 else 0

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.pie(
            counts,
            names=column_name,
            values='Quantidade',
            title=" ",
            color_discrete_sequence=color_sequence,
            hole=0.4 if chart_type == 'donut' else 0
        )
        fig.update_traces(
            textposition='inside',
            textinfo='percent',
            hoverinfo='label+percent+value',
            insidetextfont={'size': 16, 'color': 'white'},
            marker=dict(line=dict(color='#000000', width=1))
        )
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True, key=key)

    with col2:
        st.markdown(f"<div style='height: 40px;'></div>", unsafe_allow_html=True)
        st.markdown(f"##### {chart_title}")
        for index, row in counts.iterrows():
            color = color_sequence[index % len(color_sequence)]
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 12px; font-size: 14px;">
                <span style="width: 18px; height: 18px; background-color: {color}; border-radius: 5px; margin-right: 12px; display: inline-block; flex-shrink: 0;"></span>
                <div style="line-height: 1.2;">
                    <strong>{row[column_name]}</strong><br>
                    <small style="color: #666;">{row['Quantidade']} casos ({row['Percentual']:.1f}%)</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_analise_motivos():
    """Exibe um relatório detalhado e conectado sobre os motivos dos adendos e distratos."""
    st.header("Análise Detalhada dos Motivos")

    # Injetando CSS para estilizar as abas como botões
    st.markdown("""
    <style>
    div[data-baseweb="tab-list"] {
        gap: 8px;
    }
    div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
        background-color: #F5F5F5;
        color: #424242;
        border-radius: 8px !important;
        border: 1px solid #E0E0E0;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
        padding: 10px 18px !important;
    }
    div[data-baseweb="tab-list"] button[data-baseweb="tab"]:hover {
        background-color: #EEEEEE;
        border-color: #BDBDBD;
    }
    div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #212121;
        color: white;
        border: 1px solid #000000;
    }
    div[data-baseweb="tab-list"] {
        border-bottom: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    df = get_criacao_adendo_data()
    df = ensure_pandas_df(df)

    if df.empty:
        st.warning("Não foram encontrados dados para análise.")
        return

    # --- NOVO GRÁFICO DE ROSCA ---
    st.subheader("Distribuição Geral de Documentos")
    df_docs = df.copy()
    df_docs['UF_CRM_42_TIPO_DE_DOCUMENTO'].fillna('Não Preenchido', inplace=True)
    create_donut_chart_with_legend(df_docs, 'UF_CRM_42_TIPO_DE_DOCUMENTO', 'Tipos de Documento', px.colors.qualitative.Vivid, key="tipo_documento_donut", chart_type='donut')
    st.markdown("---")
    # --- FIM DO NOVO GRÁFICO ---
    
    required_cols = ['UF_CRM_42_TIPO_DE_DOCUMENTO', 'UF_CRM_42_SITUACAO', 'UF_CRM_42_TIPO_DE_PASTA', 'UF_CRM_42_PARCELA', 'UF_CRM_42_TIPO_DE_DEVOLUCAO']
    if not all(col in df.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in df.columns]
        st.error(f"As seguintes colunas necessárias não foram encontradas: {', '.join(missing_cols)}")
        return

    tipos_relevantes = ["ADENDO", "DISTRATO"]
    df_filtrado = df[df['UF_CRM_42_TIPO_DE_DOCUMENTO'].isin(tipos_relevantes)].copy()
    df_filtrado['UF_CRM_42_SITUACAO'].fillna('Não Preenchido', inplace=True)
    df_filtrado['UF_CRM_42_TIPO_DE_PASTA'].fillna('Não Preenchido', inplace=True)
    df_filtrado['UF_CRM_42_PARCELA'] = pd.to_numeric(df_filtrado['UF_CRM_42_PARCELA'], errors='coerce').fillna(0)
    df_filtrado['UF_CRM_42_TIPO_DE_DEVOLUCAO'].fillna('Não Preenchido', inplace=True)

    st.subheader("Visão Geral das Situações")
    create_donut_chart_with_legend(df_filtrado, 'UF_CRM_42_SITUACAO', 'Distribuição por Situação', px.colors.qualitative.Pastel, key="situacao_geral_donut", chart_type='donut')

    st.markdown("---")
    st.subheader("Análise Geral de Parcelas Mais Selecionadas")

    # Filtra parcelas maiores que 0 para a análise
    df_parcelas = df_filtrado[df_filtrado['UF_CRM_42_PARCELA'] > 0].copy()

    if df_parcelas.empty:
        st.info("Não há dados de parcelas para analisar.")
    else:
        # Lógica do gráfico de barras de parcelas movida para cá
        df_parcelas['UF_CRM_42_PARCELA'] = df_parcelas['UF_CRM_42_PARCELA'].astype(int)
        parcela_counts = df_parcelas['UF_CRM_42_PARCELA'].value_counts().reset_index()
        parcela_counts.columns = ['Parcela', 'Quantidade']
        top_parcelas = parcela_counts.head(15)
        top_parcelas['Parcela'] = top_parcelas['Parcela'].astype(str) + 'x'
        top_parcelas = top_parcelas.sort_values(by='Quantidade', ascending=True)

        fig = px.bar(
            top_parcelas,
            x='Quantidade', y='Parcela', orientation='h',
            title='Top 15 Quantidade de Parcelas Mais Utilizadas',
            labels={'Quantidade': 'Número de Contratos', 'Parcela': 'Nº de Parcelas'},
            text='Quantidade'
        )
        fig.update_traces(
            marker_color='#3498db', marker_line_color='rgb(8,48,107)',
            marker_line_width=1.5, opacity=0.8,
            textposition='outside', cliponaxis=False
        )
        fig.update_layout(
            height=500, plot_bgcolor='rgba(240, 240, 240, 0.95)',
            title_x=0.5, xaxis=dict(showgrid=True, gridwidth=1, gridcolor='White'),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True, key="geral_parcelas_bar")

    st.markdown("---")
    st.subheader("Análise Específica por Situação")

    tabs = st.tabs(["Congelamento", "Condição Especial", "Devolução e Distrato"])

    with tabs[0]:
        st.markdown("#### Detalhes dos Casos de Congelamento")
        df_congelamento = df_filtrado[df_filtrado['UF_CRM_42_SITUACAO'] == 'CONGELAMENTO']
        
        if df_congelamento.empty:
            st.info("Não há dados de 'Congelamento' para analisar.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                create_donut_chart_with_legend(df_congelamento, 'UF_CRM_42_TIPO_DE_PASTA', 'Tipo de Pasta', px.colors.qualitative.Set2, key="congelamento_pasta_donut", chart_type='donut')
            with col2:
                st.markdown("###### Parcelas em Casos de Congelamento")
                parcela_counts = df_congelamento[df_congelamento['UF_CRM_42_PARCELA'] > 0]['UF_CRM_42_PARCELA'].value_counts().reset_index()
                parcela_counts.columns = ['Parcela', 'Quantidade']
                
                fig_bar = px.bar(parcela_counts.head(10), x='Parcela', y='Quantidade', text_auto=True, title='Top 10 Parcelas')
                fig_bar.update_layout(xaxis={'type': 'category'}, height=350, title_x=0.5)
                st.plotly_chart(fig_bar, use_container_width=True, key="congelamento_parcela_bar")

    with tabs[1]:
        st.markdown("#### Detalhes dos Casos de Condição Especial")
        df_condicao = df_filtrado[df_filtrado['UF_CRM_42_SITUACAO'] == 'CONDIÇÃO ESPECIAL']

        if df_condicao.empty:
            st.info("Não há dados de 'Condição Especial' para analisar.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                create_donut_chart_with_legend(df_condicao, 'UF_CRM_42_TIPO_DE_PASTA', 'Tipo de Pasta', px.colors.qualitative.Antique, key="condicao_pasta_donut", chart_type='donut')
            with col2:
                st.markdown("###### Parcelas em Casos de Condição Especial")
                parcela_counts = df_condicao[df_condicao['UF_CRM_42_PARCELA'] > 0]['UF_CRM_42_PARCELA'].value_counts().reset_index()
                parcela_counts.columns = ['Parcela', 'Quantidade']

                fig_bar = px.bar(parcela_counts.head(10), x='Parcela', y='Quantidade', text_auto=True, title='Top 10 Parcelas')
                fig_bar.update_layout(xaxis={'type': 'category'}, height=350, title_x=0.5)
                st.plotly_chart(fig_bar, use_container_width=True, key="condicao_parcela_bar")

    with tabs[2]:
        st.markdown("#### Detalhes dos Casos de Devolução e Distrato")
        df_devolucao = df_filtrado[df_filtrado['UF_CRM_42_SITUACAO'].isin(['DEVOLUÇÃO', 'DISTRATO'])]

        if df_devolucao.empty:
            st.info("Não há dados de 'Devolução' ou 'Distrato' para analisar.")
        else:
            create_donut_chart_with_legend(df_devolucao, 'UF_CRM_42_TIPO_DE_DEVOLUCAO', 'Análise de Devoluções', px.colors.qualitative.Bold, key="devolucao_donut", chart_type='donut') 