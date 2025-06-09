import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from .data_loader import carregar_dados_negociacao

STATUS_NEGOCIACAO = {
    "C34:NEW": {"nome": "REUNIÃO AGENDADA", "ordem": 10, "resultado": "-"},
    "C34:PREPARATION": {"nome": "REUNIÃO REALIZADA", "ordem": 20, "resultado": "-"},
    "C34:PREPAYMENT_INVOICE": {"nome": "EM NEGOCIAÇÃO", "ordem": 30, "resultado": "-"},
    "C34:UC_N0J7C7": {"nome": "CRIAR ADENDO", "ordem": 40, "resultado": "-"},
    "C34:UC_10YYOU": {"nome": "VALIDANDO", "ordem": 50, "resultado": "-"},
    "C34:UC_8CS5R3": {"nome": "EM ASSINATURA", "ordem": 60, "resultado": "-"},
    "C34:FINAL_INVOICE": {"nome": "ASSINADO", "ordem": 70, "resultado": "-"},
    "C34:WON": {"nome": "VALIDADO ENVIAR FINANCEIRO", "ordem": 80, "resultado": "✅ SUCESSO"},
    "C34:LOSE": {"nome": "DISTRATO(VALIDAR)", "ordem": 90, "resultado": "❌ FALHA"},
    "C34:UC_D5LB1N": {"nome": "DISTRATO APROVADO", "ordem": 100, "resultado": "❌ FALHA"}
}

def create_funnel_chart(df, title):
    """Cria um gráfico de funil com base no DataFrame fornecido."""
    if df.empty or 'STAGE_ID' not in df.columns:
        return None

    stage_counts = df['STAGE_ID'].value_counts().reset_index()
    stage_counts.columns = ['STAGE_ID', 'count']

    stage_counts['stage_name'] = stage_counts['STAGE_ID'].apply(lambda x: STATUS_NEGOCIACAO.get(x, {}).get('nome', 'Desconhecido'))
    stage_counts['order'] = stage_counts['STAGE_ID'].apply(lambda x: STATUS_NEGOCIACAO.get(x, {}).get('ordem', 999))
    
    stage_counts = stage_counts[stage_counts['stage_name'] != 'Desconhecido'].sort_values('order')

    if stage_counts.empty:
        return None

    fig = go.Figure(go.Funnel(
        y=stage_counts['stage_name'],
        x=stage_counts['count'],
        textposition="inside",
        textinfo="value+percent initial",
        opacity=0.7,
        marker={"color": ["#004c99", "#005a9e", "#0069a3", "#0078a8", "#0087ad", "#0096b2", "#00a5b7", "#00b4bb", "#00c3bf", "#00d2c3"],
                "line": {"width": [4, 3, 2, 2, 2, 2, 2, 2, 1, 1], "color": "white"}},
        connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}}
    ))

    fig.update_layout(
        title=title,
        title_font_size=20,
        height=500,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig

def show_negociacao():
    st.title("Funil de Negociação - Famílias")

    with st.spinner("Carregando dados de negociação..."):
        df_negociacao = carregar_dados_negociacao()

    if df_negociacao.empty:
        st.info("Não há dados de negociação para exibir.")
        return

    # Funil Geral
    st.header("Funil Geral de Negociação")
    fig_geral = create_funnel_chart(df_negociacao, "Distribuição Geral de Negócios por Estágio")
    
    if fig_geral:
        st.plotly_chart(fig_geral, use_container_width=True)
    else:
        st.error("A coluna 'STAGE_ID' não foi encontrada nos dados. Não é possível gerar o funil geral.")

    st.markdown("---")

    # Análise por Responsável
    st.header("Análise por Responsável")

    if 'ASSIGNED_BY_NAME' not in df_negociacao.columns:
        st.warning("A coluna de responsáveis ('ASSIGNED_BY_NAME') não foi encontrada.")
        return

    # Tabela de contagem por responsável
    st.subheader("Contagem de Famílias por Responsável")
    contagem_responsaveis = df_negociacao['ASSIGNED_BY_NAME'].value_counts().reset_index()
    contagem_responsaveis.columns = ['Responsável', 'Nº de Famílias']
    st.dataframe(contagem_responsaveis, use_container_width=True)

    # Funil por responsável
    st.subheader("Funil de Negociação por Responsável")
    lista_responsaveis = sorted(df_negociacao['ASSIGNED_BY_NAME'].unique())
    
    responsavel_selecionado = st.selectbox(
        "Selecione um responsável para ver seu funil:",
        options=lista_responsaveis
    )

    if responsavel_selecionado:
        df_filtrado = df_negociacao[df_negociacao['ASSIGNED_BY_NAME'] == responsavel_selecionado]
        fig_responsavel = create_funnel_chart(df_filtrado, f"Funil de {responsavel_selecionado}")
        
        if fig_responsavel:
            st.plotly_chart(fig_responsavel, use_container_width=True)
        else:
            st.info(f"Não há dados de funil para exibir para {responsavel_selecionado}.") 