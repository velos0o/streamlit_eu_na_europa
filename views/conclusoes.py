import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import numpy as np
import matplotlib.pyplot as plt
import requests
import io
import base64
from PIL import Image
from api.bitrix_connector import load_merged_data, get_higilizacao_fields, get_status_color
import time
import os
from dotenv import load_dotenv
from utils.animation_utils import update_progress

# Carregar variáveis de ambiente
load_dotenv()

# Obter credenciais do ambiente ou Streamlit Secrets
def get_credentials():
    try:
        # Verificar se estamos em ambiente Streamlit Cloud
        if hasattr(st, 'secrets') and 'BITRIX_REST_TOKEN' in st.secrets:
            token = st.secrets.BITRIX_REST_TOKEN
            base_url = st.secrets.BITRIX_REST_URL
        else:
            # Usar variáveis de ambiente locais
            token = os.getenv('BITRIX_REST_TOKEN')
            base_url = os.getenv('BITRIX_REST_URL')
    except Exception as e:
        # Em caso de erro, usar variáveis de ambiente
        token = os.getenv('BITRIX_REST_TOKEN')
        base_url = os.getenv('BITRIX_REST_URL')
    
    # Valor padrão se não encontrado
    if not base_url:
        base_url = "https://eunaeuropacidadania.bitrix24.com.br/rest"
    
    return base_url

# URL base do Bitrix24 para API REST
BITRIX_URL = get_credentials()

def show_conclusoes():
    """
    Exibe a página de conclusões com métricas de produtividade e análises
    relacionadas às conclusões de processos de higienização.
    """
    st.title("Relatório de Conclusões")
    
    # Aplicar estilos
    aplicar_estilos_conclusoes()
    
    # Container de filtros
    with st.expander("Filtros", expanded=True):
        # Primeira linha de filtros
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtro de data (início)
            date_from = st.date_input(
                "Data inicial", 
                value=datetime.now() - timedelta(days=30),
                format="DD/MM/YYYY"
            )
        
        with col2:
            # Filtro de data (fim)
            date_to = st.date_input(
                "Data final", 
                value=datetime.now(),
                format="DD/MM/YYYY"
            )
        
        # Segunda linha de filtros
        col3, col4 = st.columns(2)
        
        with col3:
            # Filtro de usuário/responsável
            responsavel_selecionado = st.multiselect(
                "Responsável",
                options=obter_lista_responsaveis(),
                help="Deixe vazio para ver todos"
            )
    
        with col4:
            # Dia da semana
            dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", 
                        "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
            dia_semana_selecionado = st.multiselect(
                "Dia da semana",
                options=dias_semana,
                help="Deixe vazio para ver todos"
            )
        
        # Botão para aplicar filtros
        col_button = st.columns(1)[0]
        with col_button:
            aplicar_filtros_button = st.button("Aplicar Filtros", type="primary", use_container_width=True)
    
    # Container para progresso e mensagem
    progress_container = st.empty()
    message_container = st.empty()
    
    # Inicialização de sessão para armazenar dados entre recarregamentos
    if 'df_conclusoes' not in st.session_state:
        st.session_state.df_conclusoes = None
        st.session_state.df_todos_conclusoes = None
        st.session_state.last_date_from = None
        st.session_state.last_date_to = None
    
    # Verificar se deve carregar novos dados
    load_data = aplicar_filtros_button or st.session_state.df_conclusoes is None
    
    # Carregar dados quando necessário
    if load_data:
        with st.spinner("Carregando dados..."):
            message_container.text("Conectando à API do Bitrix24...")
            progress_bar = progress_container.progress(0)
            
            # Converter para formato string YYYY-MM-DD
            date_from_str = date_from.strftime("%Y-%m-%d") if date_from else None
            date_to_str = date_to.strftime("%Y-%m-%d") if date_to else None
            
            df, df_todos = carregar_dados_conclusoes(
                date_from=date_from_str,
                date_to=date_to_str,
                progress_bar=progress_bar,
                message_container=message_container
            )
            
            # Armazenar na sessão
            st.session_state.df_conclusoes = df
            st.session_state.df_todos_conclusoes = df_todos
            st.session_state.last_date_from = date_from_str
            st.session_state.last_date_to = date_to_str
            
            # Limpar containers de progresso
            progress_container.empty()
            message_container.empty()
    else:
        df = st.session_state.df_conclusoes
        df_todos = st.session_state.df_todos_conclusoes
    
    if df.empty:
        st.warning("Não foram encontrados dados para os filtros selecionados.")
        return
    
    # Aplicar filtros adicionais
    df_filtrado = aplicar_filtros(df, responsavel_selecionado, dia_semana_selecionado)
    
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado após aplicação dos filtros.")
        return
    
    # Separador
    st.markdown("---")
    
    # 1. Métricas de Destaque
    st.subheader("Métricas de Destaque")
    mostrar_metricas_destaque(df_filtrado, df_todos, date_from, date_to)
    
    # Separador
    st.markdown("---")
    
    # 2. Ranking de Produtividade
    st.subheader("Ranking de Produtividade")
    mostrar_ranking_produtividade(df_filtrado, df_todos)
    
    # Separador
    st.markdown("---")
    
    # 3. Análises Temporais
    st.subheader("Análises Temporais")
    mostrar_analises_temporais(df_filtrado)
    
    # Rodapé discreto
    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%H:%M')}")

def aplicar_estilos_conclusoes():
    """
    Aplica estilos CSS para a página de conclusões
    """
    st.markdown("""
    <style>
    .metric-card {
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        background: white;
        margin: 10px 0;
        transition: transform 0.2s;
        border: 2px solid;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-card.total {
        border-color: #2E7D32;
        border-left: 5px solid #2E7D32;
    }
    .metric-card.media-diaria {
        border-color: #388E3C;
        border-left: 5px solid #388E3C;
    }
    .metric-card.media-hora {
        border-color: #43A047;
        border-left: 5px solid #43A047;
    }
    .metric-card.taxa {
        border-color: #4CAF50;
        border-left: 5px solid #4CAF50;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #1B5E20;
        margin-bottom: 5px;
    }
    .metric-title {
        font-size: 16px;
        color: #2E7D32;
        font-weight: 500;
    }
    .stPlotlyChart {
        background-color: white !important;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .js-plotly-plot .plotly .modebar {
        display: block !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #FFFFFF;
        border-radius: 4px;
        color: #1976D2;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1976D2 !important;
        color: white !important;
    }
    .metrics-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        border: 1px solid #e9ecef;
    }
    .metric-box {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #1976D2;
        margin: 5px 0;
    }
    .metric-box h3 {
        color: #1976D2;
        font-size: 16px;
        margin: 0;
        font-weight: 500;
    }
    .metric-box p {
        color: #333;
        font-size: 24px;
        margin: 5px 0;
        font-weight: bold;
    }
    .metric-box small {
        color: #666;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

def mostrar_metricas_analise(titulo, metricas):
    """
    Exibe métricas em um container estilizado
    """
    st.markdown(f"""
    <div class="metrics-container">
        <h3 style="color: #1976D2; margin-bottom: 15px;">{titulo}</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
    """, unsafe_allow_html=True)
    
    for metrica in metricas:
        st.markdown(f"""
        <div class="metric-box">
            <h3>{metrica['titulo']}</h3>
            <p>{metrica['valor']}</p>
            <small>{metrica['subtitulo']}</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def carregar_dados_conclusoes(date_from=None, date_to=None, progress_bar=None, message_container=None):
    """
    Carrega dados específicos de conclusões da API do Bitrix24
    """
    # Carregar dados do Bitrix
    df = load_merged_data(
        category_id=32,
        date_from=date_from,
        date_to=date_to,
        debug=False,
        progress_bar=progress_bar,
        message_container=message_container
    )
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Guardar o DataFrame completo antes de qualquer filtro
    df_todos = df.copy()
    
    # Converter campo de data/hora para datetime antes de qualquer filtro
    if 'UF_CRM_1741206763' in df.columns:
        # Converter para datetime e tratar valores inválidos
        df['DATA_CONCLUSAO'] = pd.to_datetime(df['UF_CRM_1741206763'], errors='coerce')
        df_todos['DATA_CONCLUSAO'] = df['DATA_CONCLUSAO'].copy()
        
        # Filtrar por data
        if date_from and date_to:
            date_from_dt = pd.to_datetime(date_from)
            date_to_dt = pd.to_datetime(date_to) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            # Aplicar filtro de data apenas aos registros com data válida
            df = df[
                (df['DATA_CONCLUSAO'].notna()) & 
                (df['DATA_CONCLUSAO'] >= date_from_dt) & 
                (df['DATA_CONCLUSAO'] <= date_to_dt)
            ]
    else:
        df['DATA_CONCLUSAO'] = None
        df_todos['DATA_CONCLUSAO'] = None
    
    # Filtrar apenas registros com status COMPLETO depois do filtro de data
    df_conclusoes = df[df['UF_CRM_HIGILIZACAO_STATUS'] == 'COMPLETO'].copy()
    
    # Adicionar colunas de dia da semana, semana e hora
    if not df_conclusoes.empty and 'DATA_CONCLUSAO' in df_conclusoes.columns:
        df_conclusoes['DIA_SEMANA'] = df_conclusoes['DATA_CONCLUSAO'].dt.day_name()
        df_conclusoes['SEMANA'] = df_conclusoes['DATA_CONCLUSAO'].dt.strftime('%Y-%V')
        df_conclusoes['HORA'] = df_conclusoes['DATA_CONCLUSAO'].dt.hour
        
        # Ordenar por data para garantir consistência nas análises temporais
        df_conclusoes = df_conclusoes.sort_values('DATA_CONCLUSAO')
    
    return df_conclusoes, df_todos

def obter_lista_responsaveis():
    """
    Obtém a lista de responsáveis disponíveis no Bitrix24
    """
    try:
        # Carregar dados do Bitrix
        df = load_merged_data(category_id=32)
        if not df.empty and 'ASSIGNED_BY_NAME' in df.columns:
            responsaveis = sorted(df['ASSIGNED_BY_NAME'].unique().tolist())
            return responsaveis if responsaveis else ["Ana Clara", "Leonardo Reis", "Leticia", "Pamela"]
    except Exception as e:
        st.error(f"Erro ao obter lista de responsáveis: {str(e)}")
    
    return ["Ana Clara", "Leonardo Reis", "Leticia", "Pamela"]

def aplicar_filtros(df, responsavel_selecionado, dia_semana_selecionado):
    """
    Aplica filtros adicionais ao DataFrame
    
    Args:
        df (pandas.DataFrame): DataFrame original
        responsavel_selecionado (list): Lista de responsáveis selecionados
        dia_semana_selecionado (list): Lista de dias da semana selecionados
        
    Returns:
        pandas.DataFrame: DataFrame filtrado
    """
    df_filtrado = df.copy()
    
    # Filtrar por responsável
    if responsavel_selecionado:
        if 'ASSIGNED_BY_NAME' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['ASSIGNED_BY_NAME'].isin(responsavel_selecionado)]
            st.sidebar.info(f"Filtro aplicado: Responsável = {', '.join(responsavel_selecionado)}")
        else:
            st.sidebar.warning("Não foi possível aplicar o filtro de responsável (coluna ASSIGNED_BY_NAME não encontrada)")
    
    # Filtrar por dia da semana
    if dia_semana_selecionado:
        # Converter nomes em português para inglês para comparação
        dias_semana_ingles = {
            "Segunda-feira": "Monday",
            "Terça-feira": "Tuesday",
            "Quarta-feira": "Wednesday",
            "Quinta-feira": "Thursday",
            "Sexta-feira": "Friday",
            "Sábado": "Saturday",
            "Domingo": "Sunday"
        }
        
        if 'DIA_SEMANA' in df_filtrado.columns:
            dias_ingles = [dias_semana_ingles[dia] for dia in dia_semana_selecionado]
            df_filtrado = df_filtrado[df_filtrado['DIA_SEMANA'].isin(dias_ingles)]
            st.sidebar.info(f"Filtro aplicado: Dias da semana = {', '.join(dia_semana_selecionado)}")
        else:
            st.sidebar.warning("Não foi possível aplicar o filtro de dia da semana (coluna DIA_SEMANA não encontrada)")
    
    # Log do número de registros após filtragem
    if len(df_filtrado) < len(df):
        st.sidebar.success(f"Filtros aplicados: {len(df_filtrado)} de {len(df)} registros selecionados")
    
    return df_filtrado

def mostrar_metricas_destaque(df, df_todos, date_from, date_to):
    """
    Exibe as métricas de destaque em cards
    """
    st.subheader("Métricas de Destaque")
    
    # Calcular métricas apenas com dados filtrados por data
    total_conclusoes = len(df)
    
    # Carregar dados totais da página inicial
    try:
        df_inicio = load_merged_data(category_id=32)
        if not df_inicio.empty:
            # Total de negócios (todos os registros)
            total_negocios = len(df_inicio)
            
            # Total de concluídos
            concluidos = len(df)
            
            # Calcular taxa de conclusão
            taxa_conclusao = round((concluidos / max(1, total_negocios)) * 100, 1)
            
            # Adicionar informações detalhadas
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.info(f"Total de Negócios: {total_negocios}")
            with col_info2:
                st.info(f"Total de Conclusões: {concluidos}")
            with col_info3:
                pendentes = total_negocios - concluidos
                st.warning(f"Pendentes/Incompletos: {pendentes}")
        else:
            taxa_conclusao = 0
            st.warning("Não foi possível carregar os dados totais")
    except Exception as e:
        st.warning(f"Erro ao calcular taxa de conclusão: {str(e)}")
        taxa_conclusao = 0
    
    # Calcular médias
    dias_uteis = calcular_dias_uteis(date_from, date_to)
    media_diaria = round(total_conclusoes / max(1, dias_uteis), 1)
    media_horaria = round(media_diaria / 8, 1)
    
    # Exibir métricas em cards
    col1, col2, col3, col4 = st.columns(4)
    
    metricas = [
        ("Total de Conclusões", total_conclusoes, "total"),
        ("Média Diária", media_diaria, "media-diaria"),
        ("Média por Hora", media_horaria, "media-hora"),
        ("Taxa de Conclusão", f"{taxa_conclusao}%", "taxa")
    ]
    
    for col, (titulo, valor, classe) in zip([col1, col2, col3, col4], metricas):
        with col:
            st.markdown(f"""
            <div class="metric-card {classe}">
                <div class="metric-value">{valor}</div>
                <div class="metric-title">{titulo}</div>
            </div>
            """, unsafe_allow_html=True)

def calcular_dias_uteis(data_inicio, data_fim):
    """
    Calcula o número de dias úteis entre duas datas (considerando 6 dias por semana)
    
    Args:
        data_inicio (datetime): Data inicial
        data_fim (datetime): Data final
        
    Returns:
        int: Número de dias úteis
    """
    # Converter para datetime se não for
    if not isinstance(data_inicio, datetime):
        data_inicio = datetime.combine(data_inicio, datetime.min.time())
    if not isinstance(data_fim, datetime):
        data_fim = datetime.combine(data_fim, datetime.min.time())
    
    # Diferença em dias
    delta = (data_fim - data_inicio).days + 1
    
    # Calcular número de semanas completas
    semanas = delta // 7
    dias_uteis = semanas * 6  # 6 dias úteis por semana
    
    # Calcular dias restantes
    dias_restantes = delta % 7
    
    # Início da semana (0 = segunda, 6 = domingo)
    dia_semana_inicio = data_inicio.weekday()
    
    # Contar dias restantes
    for i in range(dias_restantes):
        dia = (dia_semana_inicio + i) % 7
        if dia < 6:  # Se não for domingo
            dias_uteis += 1
            
    return max(1, dias_uteis)  # Retorna pelo menos 1 para evitar divisão por zero

def mostrar_ranking_produtividade(df, df_todos):
    """
    Exibe um ranking de produtividade dos responsáveis
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados concluídos
        df_todos (pandas.DataFrame): DataFrame com todos os dados (incluindo não concluídos)
    """
    try:
        # Verificar se a coluna de responsáveis existe em df_todos
        if 'ASSIGNED_BY_NAME' not in df_todos.columns:
            st.error("Não foi possível gerar o ranking: coluna de responsáveis não encontrada.")
            return
        
        # Agrupar por responsável e contar o número de conclusões para os que concluíram
        if not df.empty and 'ASSIGNED_BY_NAME' in df.columns:
            ranking_conclusoes = df.groupby('ASSIGNED_BY_NAME').size().reset_index(name='TOTAL_CONCLUSOES')
        else:
            # Se não há conclusões, criar DataFrame vazio com as colunas necessárias
            ranking_conclusoes = pd.DataFrame(columns=['ASSIGNED_BY_NAME', 'TOTAL_CONCLUSOES'])
        
        # Calcular a taxa de conclusão por responsável
        total_por_responsavel = df_todos.groupby('ASSIGNED_BY_NAME').size().reset_index(name='TOTAL_ATRIBUIDOS')
        
        # Fazer merge outer para incluir todos os responsáveis, mesmo os que não tiveram conclusões
        ranking = pd.merge(total_por_responsavel, ranking_conclusoes, on='ASSIGNED_BY_NAME', how='left')
        
        # Preencher valores NaN de conclusões com 0
        ranking['TOTAL_CONCLUSOES'] = ranking['TOTAL_CONCLUSOES'].fillna(0)
        
        # Converter para inteiro
        ranking['TOTAL_CONCLUSOES'] = ranking['TOTAL_CONCLUSOES'].astype(int)
        
        # Calcular taxa de conclusão
        ranking['TAXA_CONCLUSAO'] = (ranking['TOTAL_CONCLUSOES'] / ranking['TOTAL_ATRIBUIDOS'] * 100).round(1)
        
        # Calcular média de conclusões por dia útil (dias que o responsável trabalhou)
        if not df.empty and 'DATA_CONCLUSAO' in df.columns:
            dias_trabalhados = df.groupby(['ASSIGNED_BY_NAME', df['DATA_CONCLUSAO'].dt.date]).size().reset_index()
            dias_por_responsavel = dias_trabalhados.groupby('ASSIGNED_BY_NAME').size().reset_index(name='DIAS_TRABALHADOS')
            ranking = pd.merge(ranking, dias_por_responsavel, on='ASSIGNED_BY_NAME', how='left')
        else:
            ranking['DIAS_TRABALHADOS'] = 0
        
        # Preencher NaN em dias trabalhados com 0
        ranking['DIAS_TRABALHADOS'] = ranking['DIAS_TRABALHADOS'].fillna(0)
        
        # Calcular média diária (evitando divisão por zero)
        ranking['MEDIA_DIARIA'] = 0.0  # Valor padrão
        mask = ranking['DIAS_TRABALHADOS'] > 0
        ranking.loc[mask, 'MEDIA_DIARIA'] = (ranking.loc[mask, 'TOTAL_CONCLUSOES'] / ranking.loc[mask, 'DIAS_TRABALHADOS']).round(1)
        
        # Ordenar pelo total de conclusões em ordem decrescente
        ranking = ranking.sort_values('TOTAL_CONCLUSOES', ascending=False).reset_index(drop=True)
        
        # Adicionar coluna de posição
        ranking.insert(0, 'POSICAO', ranking.index + 1)
        
        # Configuração das colunas para exibição com st.column_config
        colunas = {
            "POSICAO": st.column_config.NumberColumn(
                "Posição",
                help="Ranking de produtividade",
                format="%d",
                width="small"
            ),
            "ASSIGNED_BY_NAME": st.column_config.TextColumn(
                "Responsável",
                width="medium"
            ),
            "TOTAL_CONCLUSOES": st.column_config.NumberColumn(
                "Conclusões",
                help="Total de demandas concluídas",
                format="%d",
                width="small"
            ),
            "MEDIA_DIARIA": st.column_config.NumberColumn(
                "Média Diária",
                help="Média de conclusões por dia trabalhado",
                format="%.1f",
                width="small"
            ),
            "TAXA_CONCLUSAO": st.column_config.ProgressColumn(
                "Taxa de Conclusão",
                help="Percentual de demandas concluídas em relação ao total atribuído",
                format="%.1f%%",
                min_value=0,
                max_value=100,
                width="medium"
            )
        }
        
        # Exibir o ranking usando o st.dataframe com column_config
        st.dataframe(
            ranking,
            column_config=colunas,
            use_container_width=True,
            hide_index=True
        )
    except Exception as e:
        st.error(f"Erro ao gerar ranking de produtividade: {str(e)}")

def mostrar_analises_temporais(df):
    """
    Exibe análises temporais de dados de conclusão de tarefas.
    """
    try:
        if df.empty:
            st.warning("Não há dados disponíveis para exibir análises temporais.")
            return

        if 'DATA_CONCLUSAO' not in df.columns:
            st.error("A coluna 'DATA_CONCLUSAO' não foi encontrada nos dados.")
            return

        # Preparar dados
        df_valido = df.dropna(subset=['DATA_CONCLUSAO']).copy()
        df_valido['DATA_CONCLUSAO'] = pd.to_datetime(df_valido['DATA_CONCLUSAO'])

        # Definir cores para melhor contraste
        cores = {
            'principal': '#000000',  # Preto para linha principal
            'media': '#FF5722',      # Laranja para média
            'tendencia': '#1976D2',  # Azul para tendência
            'grid': '#E0E0E0',       # Cinza claro para grid
            'texto': '#212121',      # Cinza escuro para texto
            'area': 'rgba(33, 150, 243, 0.1)'  # Azul claro transparente para área
        }

        # Criar seletor de visualização
        tipo_analise = st.radio(
            "Selecione o tipo de análise:",
            ["Análise por Dia", "Análise por Dia da Semana", "Análise por Hora", "Análise por Semana"],
            horizontal=True
        )

        # 1. Análise por Dia
        if tipo_analise == "Análise por Dia":
            df_diario = df_valido.groupby(df_valido['DATA_CONCLUSAO'].dt.date).size().reset_index(name='CONCLUSOES')
            media_diaria = df_diario['CONCLUSOES'].mean()
            
            # Calcular linha de tendência
            x = np.arange(len(df_diario))
            z = np.polyfit(x, df_diario['CONCLUSOES'], 1)
            p = np.poly1d(z)
            tendencia = p(x)
            
            fig = go.Figure()
            
            # Adicionar linha de média
            fig.add_trace(go.Scatter(
                x=df_diario['DATA_CONCLUSAO'],
                y=[media_diaria] * len(df_diario),
                fill=None,
                mode='lines',
                line=dict(color=cores['media'], width=3, dash='dash'),
                name='Média Diária'
            ))
            
            # Adicionar linha de tendência
            fig.add_trace(go.Scatter(
                x=df_diario['DATA_CONCLUSAO'],
                y=tendencia,
                mode='lines',
                line=dict(color=cores['tendencia'], width=3),
                name='Tendência'
            ))
            
            # Adicionar linha principal com área
            fig.add_trace(go.Scatter(
                x=df_diario['DATA_CONCLUSAO'],
                y=df_diario['CONCLUSOES'],
                fill='tonexty',
                mode='lines+markers+text',
                line=dict(color=cores['principal'], width=4),
                marker=dict(
                    size=12,
                    symbol='circle',
                    line=dict(width=3, color=cores['tendencia'])
                ),
                text=df_diario['CONCLUSOES'],
                textposition='top center',
                name='Conclusões',
                fillcolor=cores['area']
            ))
            
            # Atualizar layout
            fig.update_layout(
                title={
                    'text': 'Conclusões por Dia',
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=24, color=cores['texto'])
                },
                xaxis_title='Data',
                yaxis_title='Número de Conclusões',
                height=500,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white',
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    bordercolor=cores['tendencia'],
                    borderwidth=2
                )
            )
            
            # Melhorar grid e eixos
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor=cores['grid'],
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor=cores['grid'],
                showline=True,
                linewidth=2,
                linecolor=cores['texto']
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor=cores['grid'],
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor=cores['grid'],
                showline=True,
                linewidth=2,
                linecolor=cores['texto']
            )
            
            st.plotly_chart(fig, use_container_width=True)

        # 2. Análise por Dia da Semana
        elif tipo_analise == "Análise por Dia da Semana":
            dias_semana_pt = {
                'Monday': 'Segunda-feira',
                'Tuesday': 'Terça-feira',
                'Wednesday': 'Quarta-feira',
                'Thursday': 'Quinta-feira',
                'Friday': 'Sexta-feira',
                'Saturday': 'Sábado',
                'Sunday': 'Domingo'
            }
            df_valido['DIA_SEMANA'] = df_valido['DATA_CONCLUSAO'].dt.day_name().map(dias_semana_pt)
            df_dia_semana = df_valido.groupby('DIA_SEMANA').agg({
                'DATA_CONCLUSAO': 'count',
                'ID': 'nunique'
            }).reset_index()
            df_dia_semana.columns = ['DIA_SEMANA', 'CONCLUSOES', 'PROCESSOS_UNICOS']
            
            ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
            df_dia_semana['DIA_ORDEM'] = pd.Categorical(df_dia_semana['DIA_SEMANA'], categories=ordem_dias, ordered=True)
            df_dia_semana = df_dia_semana.sort_values('DIA_ORDEM')
            
            media_semanal = df_dia_semana['CONCLUSOES'].mean()
            max_valor = df_dia_semana['CONCLUSOES'].max()
            min_valor = df_dia_semana['CONCLUSOES'].min()
            
            # Calcular linha de tendência
            x = np.arange(len(df_dia_semana))
            z = np.polyfit(x, df_dia_semana['CONCLUSOES'], 1)
            p = np.poly1d(z)
            tendencia = p(x)
            
            fig = go.Figure()
            
            # Adicionar barras em azul
            fig.add_trace(go.Bar(
                x=df_dia_semana['DIA_SEMANA'],
                y=df_dia_semana['CONCLUSOES'],
                text=df_dia_semana['CONCLUSOES'],
                textposition='auto',
                name='Conclusões',
                marker=dict(
                    color='#1976D2',
                    line=dict(color='#0D47A1', width=3)
                )
            ))
            
            # Adicionar linha de média
            fig.add_trace(go.Scatter(
                x=df_dia_semana['DIA_SEMANA'],
                y=[media_semanal] * len(df_dia_semana),
                mode='lines',
                name='Média',
                line=dict(color='#FF5722', width=3, dash='dash')
            ))
            
            # Adicionar linha de tendência
            fig.add_trace(go.Scatter(
                x=df_dia_semana['DIA_SEMANA'],
                y=tendencia,
                mode='lines',
                name='Tendência',
                line=dict(color='#4CAF50', width=3)
            ))
            
            # Adicionar linha de máximo
            fig.add_trace(go.Scatter(
                x=df_dia_semana['DIA_SEMANA'],
                y=[max_valor] * len(df_dia_semana),
                mode='lines',
                name='Máximo',
                line=dict(color='#2196F3', width=2, dash='dot')
            ))
            
            # Adicionar linha de mínimo
            fig.add_trace(go.Scatter(
                x=df_dia_semana['DIA_SEMANA'],
                y=[min_valor] * len(df_dia_semana),
                mode='lines',
                name='Mínimo',
                line=dict(color='#F44336', width=2, dash='dot')
            ))
            
            # Atualizar layout
            fig.update_layout(
                title={
                    'text': 'Conclusões por Dia da Semana',
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=24, color='#212121')
                },
                xaxis_title='Dia da Semana',
                yaxis_title='Número de Conclusões',
                height=500,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white',
                hovermode='x unified',
                bargap=0.3,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    bordercolor='#1976D2',
                    borderwidth=2
                )
            )
            
            # Melhorar grid e eixos
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E0E0E0',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='#E0E0E0',
                showline=True,
                linewidth=2,
                linecolor='#212121'
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E0E0E0',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='#E0E0E0',
                showline=True,
                linewidth=2,
                linecolor='#212121'
            )
            
            st.plotly_chart(fig, use_container_width=True)

        # 3. Análise por Hora
        elif tipo_analise == "Análise por Hora":
            df_valido['HORA'] = df_valido['DATA_CONCLUSAO'].dt.hour
            df_hora = df_valido.groupby('HORA').size().reset_index(name='CONCLUSOES')
            media_hora = df_hora['CONCLUSOES'].mean()
            max_valor = df_hora['CONCLUSOES'].max()
            min_valor = df_hora['CONCLUSOES'].min()
            
            # Calcular linha de tendência
            x = np.arange(len(df_hora))
            z = np.polyfit(x, df_hora['CONCLUSOES'], 1)
            p = np.poly1d(z)
            tendencia = p(x)
            
            fig = go.Figure()
            
            # Adicionar barras em azul
            fig.add_trace(go.Bar(
                x=df_hora['HORA'],
                y=df_hora['CONCLUSOES'],
                text=df_hora['CONCLUSOES'],
                textposition='auto',
                name='Conclusões',
                marker=dict(
                    color='#1976D2',
                    line=dict(color='#0D47A1', width=3)
                )
            ))
            
            # Adicionar linha de média
            fig.add_trace(go.Scatter(
                x=df_hora['HORA'],
                y=[media_hora] * len(df_hora),
                mode='lines',
                name='Média',
                line=dict(color='#FF5722', width=3, dash='dash')
            ))
            
            # Adicionar linha de tendência
            fig.add_trace(go.Scatter(
                x=df_hora['HORA'],
                y=tendencia,
                mode='lines',
                name='Tendência',
                line=dict(color='#4CAF50', width=3)
            ))
            
            # Adicionar linha de máximo
            fig.add_trace(go.Scatter(
                x=df_hora['HORA'],
                y=[max_valor] * len(df_hora),
                mode='lines',
                name='Máximo',
                line=dict(color='#2196F3', width=2, dash='dot')
            ))
            
            # Adicionar linha de mínimo
            fig.add_trace(go.Scatter(
                x=df_hora['HORA'],
                y=[min_valor] * len(df_hora),
                mode='lines',
                name='Mínimo',
                line=dict(color='#F44336', width=2, dash='dot')
            ))
            
            # Atualizar layout
            fig.update_layout(
                title={
                    'text': 'Conclusões por Hora do Dia',
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=24, color='#212121')
                },
                xaxis_title='Hora',
                yaxis_title='Número de Conclusões',
                height=500,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white',
                hovermode='x unified',
                bargap=0.3,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    bordercolor='#1976D2',
                    borderwidth=2
                )
            )
            
            # Configurar eixo X para mostrar todas as horas
            fig.update_xaxes(
                ticktext=[f'{i:02d}:00' for i in range(24)],
                tickvals=list(range(24)),
                showgrid=True,
                gridwidth=1,
                gridcolor='#E0E0E0',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='#E0E0E0',
                showline=True,
                linewidth=2,
                linecolor='#212121'
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E0E0E0',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='#E0E0E0',
                showline=True,
                linewidth=2,
                linecolor='#212121'
            )
            
            st.plotly_chart(fig, use_container_width=True)

        # 4. Análise por Semana
        else:
            df_valido['SEMANA'] = df_valido['DATA_CONCLUSAO'].dt.strftime('%Y-%V')
            df_semanal = df_valido.groupby('SEMANA').size().reset_index(name='CONCLUSOES')
            media_semanal = df_semanal['CONCLUSOES'].mean()
            max_valor = df_semanal['CONCLUSOES'].max()
            min_valor = df_semanal['CONCLUSOES'].min()
            
            # Calcular linha de tendência
            x = np.arange(len(df_semanal))
            z = np.polyfit(x, df_semanal['CONCLUSOES'], 1)
            p = np.poly1d(z)
            tendencia = p(x)
            
            fig = go.Figure()
            
            # Adicionar barras em azul
            fig.add_trace(go.Bar(
                x=df_semanal['SEMANA'],
                y=df_semanal['CONCLUSOES'],
                text=df_semanal['CONCLUSOES'],
                textposition='auto',
                name='Conclusões',
                marker=dict(
                    color='#1976D2',
                    line=dict(color='#0D47A1', width=3)
                )
            ))
            
            # Adicionar linha de média
            fig.add_trace(go.Scatter(
                x=df_semanal['SEMANA'],
                y=[media_semanal] * len(df_semanal),
                mode='lines',
                name='Média',
                line=dict(color='#FF5722', width=3, dash='dash')
            ))
            
            # Adicionar linha de tendência
            fig.add_trace(go.Scatter(
                x=df_semanal['SEMANA'],
                y=tendencia,
                mode='lines',
                name='Tendência',
                line=dict(color='#4CAF50', width=3)
            ))
            
            # Adicionar linha de máximo
            fig.add_trace(go.Scatter(
                x=df_semanal['SEMANA'],
                y=[max_valor] * len(df_semanal),
                mode='lines',
                name='Máximo',
                line=dict(color='#2196F3', width=2, dash='dot')
            ))
            
            # Adicionar linha de mínimo
            fig.add_trace(go.Scatter(
                x=df_semanal['SEMANA'],
                y=[min_valor] * len(df_semanal),
                mode='lines',
                name='Mínimo',
                line=dict(color='#F44336', width=2, dash='dot')
            ))
            
            # Atualizar layout
            fig.update_layout(
                title={
                    'text': 'Conclusões por Semana',
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=24, color='#212121')
                },
                xaxis_title='Semana',
                yaxis_title='Número de Conclusões',
                height=500,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white',
                hovermode='x unified',
                bargap=0.3,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    bordercolor='#1976D2',
                    borderwidth=2
                )
            )
            
            # Melhorar grid e eixos
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E0E0E0',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='#E0E0E0',
                showline=True,
                linewidth=2,
                linecolor='#212121'
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='#E0E0E0',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='#E0E0E0',
                showline=True,
                linewidth=2,
                linecolor='#212121'
            )
            
            st.plotly_chart(fig, use_container_width=True)

        # Mostrar métricas abaixo do gráfico
        if tipo_analise == "Análise por Dia":
            dia_maior_prod = df_diario.loc[df_diario['CONCLUSOES'].idxmax()]
            tendencia = df_diario['CONCLUSOES'].iloc[-1] - df_diario['CONCLUSOES'].iloc[0]
            
            metricas = [
                {
                    "titulo": "Dia de Maior Produção",
                    "valor": f"{dia_maior_prod['DATA_CONCLUSAO'].strftime('%d/%m/%Y')}",
                    "subtitulo": f"{int(dia_maior_prod['CONCLUSOES'])} conclusões"
                },
                {
                    "titulo": "Média Diária",
                    "valor": f"{media_diaria:.1f}",
                    "subtitulo": "conclusões/dia"
                },
                {
                    "titulo": "Tendência",
                    "valor": "↑ Crescente" if tendencia > 0 else "↓ Decrescente",
                    "subtitulo": f"Diferença de {abs(tendencia):.1f} conclusões"
                }
            ]
            
            mostrar_metricas_analise("Métricas da Análise Diária", metricas)
            
        elif tipo_analise == "Análise por Dia da Semana":
            dia_mais_produtivo = df_dia_semana.loc[df_dia_semana['CONCLUSOES'].idxmax()]
            
            metricas = [
                {
                    "titulo": "Dia Mais Produtivo",
                    "valor": dia_mais_produtivo['DIA_SEMANA'],
                    "subtitulo": f"{int(dia_mais_produtivo['CONCLUSOES'])} conclusões"
                },
                {
                    "titulo": "Média por Dia da Semana",
                    "valor": f"{media_semanal:.1f}",
                    "subtitulo": "conclusões/dia"
                },
                {
                    "titulo": "Processos Únicos",
                    "valor": f"{int(dia_mais_produtivo['PROCESSOS_UNICOS'])}",
                    "subtitulo": "no dia mais produtivo"
                }
            ]
            
            mostrar_metricas_analise("Métricas da Análise por Dia da Semana", metricas)
            
        elif tipo_analise == "Análise por Hora":
            hora_mais_produtiva = df_hora.loc[df_hora['CONCLUSOES'].idxmax()]
            
            # Categorizar períodos do dia
            manha = df_hora[df_hora['HORA'].between(6, 11)]['CONCLUSOES'].sum()
            tarde = df_hora[df_hora['HORA'].between(12, 17)]['CONCLUSOES'].sum()
            noite = df_hora[df_hora['HORA'].between(18, 23)]['CONCLUSOES'].sum()
            madrugada = df_hora[df_hora['HORA'].between(0, 5)]['CONCLUSOES'].sum()
            
            periodo_mais_produtivo = max(
                [("Manhã", manha), ("Tarde", tarde), 
                 ("Noite", noite), ("Madrugada", madrugada)],
                key=lambda x: x[1]
            )
            
            metricas = [
                {
                    "titulo": "Horário Mais Produtivo",
                    "valor": f"{hora_mais_produtiva['HORA']:02d}:00",
                    "subtitulo": f"{int(hora_mais_produtiva['CONCLUSOES'])} conclusões"
                },
                {
                    "titulo": "Período Mais Produtivo",
                    "valor": periodo_mais_produtivo[0],
                    "subtitulo": f"{int(periodo_mais_produtivo[1])} conclusões"
                },
                {
                    "titulo": "Média por Hora",
                    "valor": f"{media_hora:.1f}",
                    "subtitulo": "conclusões/hora"
                },
                {
                    "titulo": "Horas Produtivas",
                    "valor": f"{len(df_hora[df_hora['CONCLUSOES'] > media_hora])}",
                    "subtitulo": "acima da média"
                }
            ]
            
            mostrar_metricas_analise("Métricas da Análise por Hora", metricas)
            
        else:
            semana_mais_produtiva = df_semanal.loc[df_semanal['CONCLUSOES'].idxmax()]
            
            metricas = [
                {
                    "titulo": "Semana Mais Produtiva",
                    "valor": semana_mais_produtiva['SEMANA'],
                    "subtitulo": f"{int(semana_mais_produtiva['CONCLUSOES'])} conclusões"
                },
                {
                    "titulo": "Média por Semana",
                    "valor": f"{media_semanal:.1f}",
                    "subtitulo": "conclusões/semana"
                }
            ]
            
            mostrar_metricas_analise("Métricas da Análise Semanal", metricas)

    except Exception as e:
        st.error(f"Erro ao gerar análises temporais: {str(e)}")
        st.write("Detalhes do erro para debug:", str(e))