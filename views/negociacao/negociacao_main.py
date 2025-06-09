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
    """Cria um gráfico de funil e retorna a figura e os dados da tabela."""
    if df.empty or 'STAGE_ID' not in df.columns:
        return None, None

    stage_counts = df['STAGE_ID'].value_counts().reset_index()
    stage_counts.columns = ['STAGE_ID', 'count']

    stage_counts['stage_name'] = stage_counts['STAGE_ID'].apply(lambda x: STATUS_NEGOCIACAO.get(x, {}).get('nome', 'Desconhecido'))
    stage_counts['order'] = stage_counts['STAGE_ID'].apply(lambda x: STATUS_NEGOCIACAO.get(x, {}).get('ordem', 999))
    
    stage_counts = stage_counts[stage_counts['stage_name'] != 'Desconhecido'].sort_values('order')

    if stage_counts.empty:
        return None, None

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
    return fig, stage_counts

def show_negociacao():
    st.title("Funil de Negociação - Famílias")

    with st.spinner("Carregando dados de negociação..."):
        df_negociacao = carregar_dados_negociacao()

    if df_negociacao.empty:
        st.info("Não há dados de negociação para exibir.")
        return

    # Funil Geral
    st.header("Funil Geral de Negociação")
    fig_geral, _ = create_funnel_chart(df_negociacao, "Distribuição Geral de Negócios por Estágio")
    
    if fig_geral:
        st.plotly_chart(fig_geral, use_container_width=True)
    else:
        st.error("A coluna 'STAGE_ID' não foi encontrada nos dados. Não é possível gerar o funil geral.")

    st.markdown("---")

    # Análise por Responsável
    st.header("Análise por Responsável")

    if 'ASSIGNED_BY_NAME' not in df_negociacao.columns or 'STAGE_ID' not in df_negociacao.columns:
        st.warning("As colunas necessárias ('ASSIGNED_BY_NAME', 'STAGE_ID') não foram encontradas para gerar a análise.")
        return

    # Tabela de contagem geral por responsável
    st.subheader("Contagem Total de Famílias por Responsável")
    contagem_responsaveis = df_negociacao['ASSIGNED_BY_NAME'].value_counts().reset_index()
    contagem_responsaveis.columns = ['Responsável', 'Nº de Famílias']
    st.dataframe(contagem_responsaveis, use_container_width=True)

    # Tabela pivotada com responsáveis nas linhas e etapas nas colunas
    st.subheader("Visão Detalhada por Etapa e Responsável")
    
    # Mapear STAGE_ID para nomes de etapas
    df_negociacao['stage_name'] = df_negociacao['STAGE_ID'].apply(lambda x: STATUS_NEGOCIACAO.get(x, {}).get('nome', 'Desconhecido'))
    
    # Filtrar etapas desconhecidas
    df_pivot_data = df_negociacao[df_negociacao['stage_name'] != 'Desconhecido']

    # Criar tabela pivotada
    pivot_table = pd.pivot_table(
        df_pivot_data,
        index='ASSIGNED_BY_NAME',
        columns='stage_name',
        aggfunc='size',
        fill_value=0
    )

    # Ordenar as colunas da tabela pivotada de acordo com a ordem do funil
    ordered_stages = sorted(STATUS_NEGOCIACAO.values(), key=lambda x: x['ordem'])
    ordered_stage_names = [stage['nome'] for stage in ordered_stages]
    
    # Garantir que apenas as colunas existentes na pivot_table sejam usadas para reordenar
    final_ordered_columns = [name for name in ordered_stage_names if name in pivot_table.columns]
    
    pivot_table_ordered = pivot_table[final_ordered_columns]

    st.dataframe(pivot_table_ordered, use_container_width=True) 