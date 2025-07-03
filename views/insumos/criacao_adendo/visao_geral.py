import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ..data_loader import get_criacao_adendo_data
from utils.dataframe_utils import ensure_pandas_df

def show_visao_geral():
    """
    Exibe a visão geral do funil de Criação de Adendo com um gráfico de funil.
    """
    st.header("Visão Geral do Funil de Criação de Adendo")
    
    df = get_criacao_adendo_data()
    df = ensure_pandas_df(df)

    if df.empty:
        st.warning("Nenhum dado encontrado para o funil de Criação de Adendo.")
        return

    # Mapeamento de IDs de estágio para nomes, ordem e cores corretas
    stage_map = {
        'DT1118_126:NEW': ('Fila', 1, '#FBC02D'),                           # Amarelo
        'DT1118_126:PREPARATION': ('Em Andamento', 2, '#FFA726'),          # Laranja
        'DT1118_126:UC_OESN94': ('Enviado para Conferência', 3, '#FBC02D'), # Amarelo
        'DT1118_126:UC_6MUBF9': ('Enviado para Assinatura', 4, '#4CAF50'),  # Verde
        'DT1118_126:SUCCESS': ('Assinatura Completa', 5, '#4CAF50'),       # Verde
        'DT1118_126:UC_XK5D9A': ('Corrigir Adendo', 6, '#D32F2F'),          # Vermelho
        'DT1118_126:FAIL': ('Cancelado', 7, '#BDBDBD') # Cinza para cancelados
    }
    
    # Processa os dados do funil
    df['stage_name'] = df['STAGE_ID'].map(lambda x: stage_map.get(x, ('Desconhecido', 99, '#CCCCCC'))[0])
    
    stage_counts = df['stage_name'].value_counts().reset_index()
    stage_counts.columns = ['stage_name', 'count']
    
    # Garante que todas as etapas do mapa estejam presentes para o gráfico
    all_stages = pd.DataFrame(list(stage_map.values()), columns=['stage_name', 'stage_order', 'color'])
    
    # Junta os dados para ter contagens e cores
    stage_counts = pd.merge(all_stages, stage_counts, on='stage_name', how='left').fillna(0)
    stage_counts = stage_counts.sort_values('stage_order')

    # Criação do gráfico de funil com as cores corretas
    fig = go.Figure(go.Funnel(
        y=stage_counts['stage_name'],
        x=stage_counts['count'],
        textposition="inside",
        textinfo="value+percent total",
        marker={"color": stage_counts['color']}, # Usa a coluna de cores
        connector={"line": {"color": "grey", "dash": "dot", "width": 2}}
    ))

    fig.update_layout(
        title="Distribuição por Etapa do Funil",
        title_font_size=20,
        height=600 # Aumenta a altura para melhor visualização
    )
    
    st.plotly_chart(fig, use_container_width=True) 