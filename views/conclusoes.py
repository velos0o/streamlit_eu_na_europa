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
import sys
from pathlib import Path
from dotenv import load_dotenv

# Obter o caminho absoluto para a pasta utils
utils_path = os.path.join(Path(__file__).parents[1], 'utils')
sys.path.insert(0, str(utils_path))

# Agora importa diretamente do arquivo animation_utils
from animation_utils import update_progress

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
    # Título com destaque extra
    st.markdown("""
    <h1 style="font-size: 3.2rem; font-weight: 900; color: #1A237E; text-align: center; 
    margin-bottom: 1.8rem; padding-bottom: 10px; border-bottom: 4px solid #1976D2;
    font-family: Arial, Helvetica, sans-serif;">
    RELATÓRIO DE CONCLUSÕES</h1>
    """, unsafe_allow_html=True)
    
    # Aplicar estilos
    aplicar_estilos_conclusoes()
    
    # Container de filtros
    with st.expander("Filtros", expanded=True):
        # Informações sobre o cálculo de médias
        st.markdown("""
        <div style="background-color: #e6f7ff; padding: 10px; border-radius: 5px; border-left: 5px solid #1976D2; margin-bottom: 15px; font-family: Arial, Helvetica, sans-serif;">
            <strong>⚠️ IMPORTANTE:</strong> As médias são calculadas considerando apenas os dias em que houve trabalho:<br>
            • Segunda a Sexta: considerados dias úteis<br>
            • Sábado: considerado dia útil<br>
            • Domingo: não contado nas médias
        </div>
        """, unsafe_allow_html=True)
        
        # Primeira linha de filtros
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtro de data (início)
            date_from = st.date_input(
                "Data inicial", 
                value=datetime.now() - timedelta(days=30),
                format="DD/MM/YYYY",
                key="conclusoes_date_from"
            )
        
        with col2:
            # Filtro de data (fim)
            date_to = st.date_input(
                "Data final", 
                value=datetime.now(),
                format="DD/MM/YYYY",
                key="conclusoes_date_to"
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
     
    # 1. Métricas de Destaque
    st.subheader("Métricas de Destaque")
    mostrar_metricas_destaque(df_filtrado, df_todos, date_from, date_to)
    
    # 2. Ranking de Produtividade
    st.subheader("Ranking de Produtividade")
    mostrar_ranking_produtividade(df_filtrado, df_todos)
    
    # Separador
    st.markdown("---")
 
    # 3. Análises Temporais
    st.subheader("Análises Temporais")
    mostrar_analises_temporais(df_filtrado, date_from, date_to)
    
    # Rodapé discreto
    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%H:%M')}")

def aplicar_estilos_conclusoes():
    """
    Aplica estilos CSS para a página de conclusões
    """
    st.markdown("""
    <style>
    /* Estilos globais de tipografia */
    body, .stApp {
        font-family: Arial, Helvetica, sans-serif !important;
        font-size: 18px;
        color: #333333;
    }
    
    /* Estilos para títulos */
    h1, h2, h3, h4, h5, h6 {
        font-family: Arial, Helvetica, sans-serif !important;
        font-weight: 900 !important;
        color: #1A237E !important;
        letter-spacing: -0.5px;
    }
    
    h1 {
        font-size: 3rem !important;
        margin-bottom: 1.5rem !important;
        font-weight: 900 !important;
    }
    
    h2, .stSubheader {
        font-size: 2.3rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #E0E0E0;
        font-weight: 800 !important;
    }
    
    h3 {
        font-size: 1.8rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
        font-weight: 700 !important;
    }
    
    /* Estilos para informações e avisos */
    .stInfo, .stWarning, .stSuccess, .stError {
        font-size: 1.2rem !important;
        font-weight: 600;
        padding: 1rem !important;
    }
    
    /* Estilos para legendas */
    .stCaption {
        font-size: 1rem !important;
        opacity: 0.8;
        font-style: italic;
    }
    
    /* Estilos para cards de métricas */
    .metric-card {
        border-radius: 12px;
        padding: 28px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        text-align: center;
        background: white;
        margin: 15px 0;
        transition: transform 0.3s, box-shadow 0.3s;
        border: 3px solid;
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 16px rgba(0,0,0,0.15);
    }
    
    .metric-card.total {
        border-color: #2E7D32;
        border-left: 8px solid #2E7D32;
    }
    
    .metric-card.media-diaria {
        border-color: #1565C0;
        border-left: 8px solid #1565C0;
    }
    
    .metric-card.media-hora {
        border-color: #6A1B9A;
        border-left: 8px solid #6A1B9A;
    }
    
    .metric-card.taxa {
        border-color: #E65100;
        border-left: 8px solid #E65100;
    }
    
    .metric-value {
        font-size: 56px !important;
        font-weight: 900 !important;
        line-height: 1.2;
        margin-bottom: 10px;
    }
    
    .metric-card.total .metric-value {
        color: #2E7D32;
    }
    
    .metric-card.media-diaria .metric-value {
        color: #1565C0;
    }
    
    .metric-card.media-hora .metric-value {
        color: #6A1B9A;
    }
    
    .metric-card.taxa .metric-value {
        color: #E65100;
    }
    
    .metric-title {
        font-size: 20px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card.total .metric-title {
        color: #2E7D32;
    }
    
    .metric-card.media-diaria .metric-title {
        color: #1565C0;
    }
    
    .metric-card.media-hora .metric-title {
        color: #6A1B9A;
    }
    
    .metric-card.taxa .metric-title {
        color: #E65100;
    }
    
    /* Estilos para gráficos */
    .stPlotlyChart {
        background-color: white !important;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
        margin: 15px 0;
    }
    
    .js-plotly-plot .plotly .modebar {
        display: block !important;
    }
    
    /* Estilos para tabelas */
    [data-testid="stDataFrame"] table {
        font-size: 18px !important;
    }
    
    [data-testid="stDataFrame"] th {
        font-weight: 800 !important;
        background-color: #F5F5F5 !important;
        color: #1A237E !important;
        text-transform: uppercase;
        font-size: 16px !important;
        padding: 14px !important;
    }
    
    [data-testid="stDataFrame"] td {
        font-size: 17px !important;
        padding: 12px !important;
        font-weight: 600;
    }
    
    [data-testid="stDataFrame"] tr:hover td {
        background-color: rgba(25, 118, 210, 0.05) !important;
    }
    
    /* Estilos para tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        white-space: pre-wrap;
        background-color: #FFFFFF;
        border-radius: 8px;
        color: #1976D2;
        font-weight: 700;
        font-size: 18px !important;
        border: 2px solid #E0E0E0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1976D2 !important;
        color: white !important;
        border: 2px solid #1976D2 !important;
    }
    
    /* Estilos para containers de métricas */
    .metrics-container {
        background-color: #f8f9fa;
        padding: 25px;
        border-radius: 12px;
        margin-top: 25px;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    
    .metric-box {
        background-color: white;
        padding: 22px;
        border-radius: 10px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.08);
        border-left: 6px solid #1976D2;
        margin: 10px 0;
        transition: transform 0.2s;
    }
    
    .metric-box:hover {
        transform: translateY(-3px);
    }
    
    .metric-box h3 {
        color: #1976D2;
        font-size: 20px !important;
        margin: 0;
        font-weight: 700 !important;
    }
    
    .metric-box p {
        color: #333;
        font-size: 36px !important;
        margin: 8px 0;
        font-weight: 900 !important;
    }
    
    .metric-box small {
        color: #666;
        font-size: 16px !important;
        font-style: italic;
    }
    
    /* Estilo para labels dos controles */
    label.css-109ww5y {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #333333 !important;
    }
    
    /* Estilo para expandir/colapsar */
    details {
        margin: 1rem 0;
    }
    
    details summary {
        font-weight: 700;
        cursor: pointer;
        padding: 12px;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    
    /* Estilo para informações adicionais */
    .info-text {
        font-size: 18px;
        line-height: 1.6;
        background-color: #f8f9fa;
        padding: 18px;
        border-radius: 8px;
        border-left: 5px solid #1976D2;
        margin: 16px 0;
        font-weight: 600;
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
    # Adicionar mensagem de verificação
    st.success("RECALCULADO: Médias baseadas em dias úteis a partir da primeira conclusão registrada v4.0")
    
    # Usar dados originais sem filtro
    df_filtrado = df
    
    # Calcular métricas com dados originais
    total_conclusoes = len(df_filtrado)
    
    # Carregar dados totais da página inicial
    try:
        df_inicio = load_merged_data(category_id=32)
        if not df_inicio.empty:
            # Total de negócios (todos os registros)
            total_negocios = len(df_inicio)
            
            # Total de concluídos
            concluidos = len(df_filtrado)
            
            # Calcular taxa de conclusão
            taxa_conclusao = round((concluidos / max(1, total_negocios)) * 100, 1)
            
            # Adicionar informações detalhadas com mais destaque
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.markdown("""
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; box-shadow: 0 3px 8px rgba(0,0,0,0.1); border-left: 5px solid #1976D2;">
                    <p style="font-size: 17px; margin: 0; font-weight: 600; color: #1565C0;">Total de Negócios:</p>
                    <p style="font-size: 24px; margin: 5px 0 0 0; font-weight: 800; color: #0D47A1;">{}</p>
                </div>
                """.format(f"{total_negocios:,}".replace(",", ".")), unsafe_allow_html=True)
            with col_info2:
                st.markdown("""
                <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; box-shadow: 0 3px 8px rgba(0,0,0,0.1); border-left: 5px solid #4CAF50;">
                    <p style="font-size: 17px; margin: 0; font-weight: 600; color: #2E7D32;">Total de Conclusões:</p>
                    <p style="font-size: 24px; margin: 5px 0 0 0; font-weight: 800; color: #1B5E20;">{}</p>
                </div>
                """.format(f"{concluidos:,}".replace(",", ".")), unsafe_allow_html=True)
            with col_info3:
                pendentes = total_negocios - concluidos
                st.markdown("""
                <div style="background-color: #fff8e1; padding: 15px; border-radius: 8px; box-shadow: 0 3px 8px rgba(0,0,0,0.1); border-left: 5px solid #FFC107;">
                    <p style="font-size: 17px; margin: 0; font-weight: 600; color: #F57F17;">Pendentes/Incompletos:</p>
                    <p style="font-size: 24px; margin: 5px 0 0 0; font-weight: 800; color: #E65100;">{}</p>
                </div>
                """.format(f"{pendentes:,}".replace(",", ".")), unsafe_allow_html=True)
        else:
            taxa_conclusao = 0
            st.warning("Não foi possível carregar os dados totais")
    except Exception as e:
        st.warning(f"Erro ao calcular taxa de conclusão: {str(e)}")
        taxa_conclusao = 0
    
    # Converter para datetime se não for
    if not isinstance(date_from, datetime):
        date_from = datetime.combine(date_from, datetime.min.time())
    if not isinstance(date_to, datetime):
        date_to = datetime.combine(date_to, datetime.min.time())
    
    # Encontrar a data da primeira conclusão (se houver registros)
    data_primeira_conclusao = None
    if not df_filtrado.empty and 'DATA_CONCLUSAO' in df_filtrado.columns:
        df_com_data = df_filtrado.dropna(subset=['DATA_CONCLUSAO'])
        if not df_com_data.empty:
            data_primeira_conclusao = df_com_data['DATA_CONCLUSAO'].min().date()
    
    # Se não houver conclusões, usar a data inicial
    if data_primeira_conclusao is None:
        data_primeira_conclusao = date_from.date()
    
    # Ajustar a data inicial para ser a data da primeira conclusão
    data_inicio_efetiva = max(date_from.date(), data_primeira_conclusao)
    
    # SIMPLIFICAR: Contar dias úteis naturais (dias em que houve trabalho)
    dias_uteis_naturais = 0
    horas_uteis = 0
    
    # Criar uma lista para debug com detalhes de cada dia
    dias_debug = []
    
    # Calcular dia a dia a partir da primeira conclusão
    data_atual = datetime.combine(data_inicio_efetiva, datetime.min.time())
    while data_atual.date() <= date_to.date():
        # Dia da semana: 0 = segunda, 6 = domingo
        dia_semana = data_atual.weekday()
        
        # Segunda a sábado são considerados dias úteis
        if 0 <= dia_semana <= 5:  # Segunda a sábado
            dias_uteis_naturais += 1
            
            # Registrar horas para média horária
            if 0 <= dia_semana <= 4:  # Segunda a sexta
                horas_uteis += 12  # 7h - 19h (12 horas)
                dias_debug.append(f"{data_atual.strftime('%d/%m/%Y')} ({['Seg', 'Ter', 'Qua', 'Qui', 'Sex'][dia_semana]}): +1 dia, +12h")
            else:  # Sábado
                horas_uteis += 3   # 9h - 12h (3 horas)
                dias_debug.append(f"{data_atual.strftime('%d/%m/%Y')} (Sáb): +1 dia, +3h")
        else:  # Domingo
            dias_debug.append(f"{data_atual.strftime('%d/%m/%Y')} (Dom): +0 dias, +0h")
        
        # Avançar para o próximo dia
        data_atual += timedelta(days=1)
    
    # Calcular médias
    # Média diária baseada em dias naturais (dias em que houve trabalho)
    media_diaria = round(total_conclusoes / max(1, dias_uteis_naturais), 2)
    
    # Média horária
    media_horaria = round(total_conclusoes / max(1, horas_uteis), 2)
    
    # Exibir métricas em cards com destaque extra
    col1, col2, col3, col4 = st.columns(4)
    
    metricas = [
        ("Total de Conclusões", f"{total_conclusoes:,}".replace(",", "."), "total", "#2E7D32"),
        ("Média Diária", f"{media_diaria:,.2f}".replace(",", "."), "media-diaria", "#1565C0"),
        ("Média por Hora", f"{media_horaria:,.2f}".replace(",", "."), "media-hora", "#6A1B9A"),
        ("Taxa de Conclusão", f"{taxa_conclusao}%", "taxa", "#E65100")
    ]
    
    for col, (titulo, valor, classe, cor) in zip([col1, col2, col3, col4], metricas):
        with col:
            st.markdown(f"""
            <div class="metric-card {classe}" style="background: linear-gradient(to bottom, white, #f8f9fa); border-width: 3px; border-color: {cor}; border-left-width: 10px; box-shadow: 0 8px 16px rgba(0,0,0,0.12); font-family: Arial, Helvetica, sans-serif;">
                <div class="metric-value" style="font-size: 58px; font-weight: 900; color: {cor}; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">{valor}</div>
                <div class="metric-title" style="font-size: 20px; font-weight: 800; color: {cor}; text-transform: uppercase; letter-spacing: 0.5px;">{titulo}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Destacar a data inicial efetiva (primeira conclusão)
    if data_inicio_efetiva > date_from.date():
        st.warning(f"⚠️ **Primeira conclusão registrada em {data_inicio_efetiva.strftime('%d/%m/%Y')}**. Médias calculadas a partir desta data.")
    
    # Informações sobre o cálculo com mais destaque
    st.markdown(f"""
    <div class="info-text" style="background-color: #f3e5f5; border-left: 6px solid #7B1FA2; padding: 20px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.08); font-family: Arial, Helvetica, sans-serif;">
        <div style="font-size: 18px; margin-bottom: 10px;">
            <strong style="font-size: 19px; color: #4A148C;">Período considerado:</strong> 
            <span style="font-weight: 700;">{data_inicio_efetiva.strftime('%d/%m/%Y')} a {date_to.strftime('%d/%m/%Y')}</span>
        </div>
        <div style="font-size: 18px; margin-bottom: 10px;">
            <strong style="color: #4A148C;">Dias úteis (seg-sáb):</strong> 
            <span style="font-weight: 800; font-size: 20px;">{dias_uteis_naturais}</span> dias | 
            <strong style="color: #4A148C;">Horas úteis:</strong> 
            <span style="font-weight: 800; font-size: 20px;">{horas_uteis}h</span>
        </div>
        <div style="font-size: 18px;">
            <strong style="color: #4A148C;">Cálculo da média:</strong> 
            <span style="font-weight: 700;">{total_conclusoes:,} conclusões ÷ {dias_uteis_naturais} dias = 
            <span style="font-weight: 900; font-size: 20px; color: #1565C0;">{media_diaria:,.2f}</span> conclusões/dia</span>
        </div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

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
        # Usar os dados originais sem filtragem
        df_filtrado = df
        
        # Verificar se a coluna de responsáveis existe em df_todos
        if 'ASSIGNED_BY_NAME' not in df_todos.columns:
            st.error("Não foi possível gerar o ranking: coluna de responsáveis não encontrada.")
            return
        
        # Agrupar por responsável e contar o número de conclusões para os que concluíram
        if not df_filtrado.empty and 'ASSIGNED_BY_NAME' in df_filtrado.columns:
            ranking_conclusoes = df_filtrado.groupby('ASSIGNED_BY_NAME').size().reset_index(name='TOTAL_CONCLUSOES')
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
        
        # Calcular pendentes
        ranking['PENDENTES'] = ranking['TOTAL_ATRIBUIDOS'] - ranking['TOTAL_CONCLUSOES']
        
        # Calcular taxa de conclusão
        ranking['TAXA_CONCLUSAO'] = (ranking['TOTAL_CONCLUSOES'] / ranking['TOTAL_ATRIBUIDOS'] * 100).round(1)
        
        # Calcular dias trabalhados (dias em que cada responsável teve pelo menos uma conclusão)
        if not df_filtrado.empty and 'DATA_CONCLUSAO' in df_filtrado.columns:
            # Criar colunas auxiliares
            df_temp = df_filtrado.copy()
            df_temp['DATA'] = df_temp['DATA_CONCLUSAO'].dt.date
            df_temp['DIA_SEMANA'] = df_temp['DATA_CONCLUSAO'].dt.weekday
            
            # Lista para armazenar os dados de dias trabalhados com primeira conclusão
            dados_dias_trabalhados = []
            
            # Para cada responsável, calcular dias úteis a partir da primeira conclusão
            for responsavel in df_temp['ASSIGNED_BY_NAME'].unique():
                # Filtrar dados do responsável
                df_resp = df_temp[df_temp['ASSIGNED_BY_NAME'] == responsavel]
                
                # Encontrar data da primeira conclusão
                primeira_conclusao = df_resp['DATA'].min()
                
                # Encontrar data da última conclusão
                ultima_conclusao = df_resp['DATA'].max()
                
                # Calcular dias úteis entre a primeira e a última conclusão
                dias_uteis = 0
                data_atual = datetime.combine(primeira_conclusao, datetime.min.time())
                
                while data_atual.date() <= ultima_conclusao:
                    dia_semana = data_atual.weekday()
                    if dia_semana <= 5:  # Segunda a sábado
                        dias_uteis += 1
                    data_atual += timedelta(days=1)
                
                # Dias em que o responsável realmente trabalhou (com conclusões)
                dias_com_conclusao = df_resp['DATA'].nunique()
                
                # Adicionar à lista de dados
                dados_dias_trabalhados.append({
                    'ASSIGNED_BY_NAME': responsavel,
                    'PRIMEIRA_CONCLUSAO': primeira_conclusao,
                    'ULTIMA_CONCLUSAO': ultima_conclusao,
                    'DIAS_UTEIS_PERIODO': dias_uteis,
                    'DIAS_COM_CONCLUSAO': dias_com_conclusao
                })
            
            # Converter para DataFrame
            df_dias = pd.DataFrame(dados_dias_trabalhados)
            
            # Mesclar com o ranking
            if not df_dias.empty:
                ranking = pd.merge(ranking, df_dias, on='ASSIGNED_BY_NAME', how='left')
                
                # Usar os dias úteis do período como dias trabalhados
                ranking['DIAS_TRABALHADOS'] = ranking['DIAS_UTEIS_PERIODO']
            else:
                ranking['DIAS_TRABALHADOS'] = 0
        else:
            ranking['DIAS_TRABALHADOS'] = 0
        
        # Preencher NaN em dias trabalhados com 0
        ranking['DIAS_TRABALHADOS'] = ranking['DIAS_TRABALHADOS'].fillna(0)
        
        # Calcular média diária (evitando divisão por zero)
        ranking['MEDIA_DIARIA'] = 0.0  # Valor padrão
        mask = ranking['DIAS_TRABALHADOS'] > 0
        ranking.loc[mask, 'MEDIA_DIARIA'] = (ranking.loc[mask, 'TOTAL_CONCLUSOES'] / ranking.loc[mask, 'DIAS_TRABALHADOS']).round(2)
        
        # Determinar o melhor valor para destaque (maior média diária)
        if not ranking.empty and 'MEDIA_DIARIA' in ranking.columns:
            melhor_media = ranking['MEDIA_DIARIA'].max()
            
            # Criar coluna de status para destacar
            ranking['STATUS'] = ''
            ranking.loc[ranking['MEDIA_DIARIA'] == melhor_media, 'STATUS'] = '🏆'
        
        # Ordenar pelo total de conclusões em ordem decrescente
        ranking = ranking.sort_values('TOTAL_CONCLUSOES', ascending=False).reset_index(drop=True)
        
        # Adicionar coluna de posição
        ranking.insert(0, 'POSICAO', ranking.index + 1)
        
        # Formatação dos valores numéricos para exibição
        ranking['POSICAO_FORMATADA'] = ranking['POSICAO'].apply(lambda x: f"{x}º")
        ranking['MEDIA_DIARIA_FORMATADA'] = ranking['MEDIA_DIARIA'].apply(lambda x: f"{x:.2f}".replace('.', ','))
        
        # Configuração das colunas para exibição com st.column_config
        colunas = {
            "POSICAO_FORMATADA": st.column_config.TextColumn(
                "Posição",
                help="Ranking de produtividade",
                width="small"
            ),
            "STATUS": st.column_config.TextColumn(
                " ",
                help="Destaque",
                width="small"
            ),
            "ASSIGNED_BY_NAME": st.column_config.TextColumn(
                "Responsável",
                width="medium"
            ),
            "PENDENTES": st.column_config.NumberColumn(
                "Pendentes",
                help="Demandas ainda não concluídas",
                format="%d",
                width="small"
            ),
            "TOTAL_CONCLUSOES": st.column_config.NumberColumn(
                "Conclusões",
                help="Total de demandas concluídas",
                format="%d",
                width="small"
            ),
            "MEDIA_DIARIA_FORMATADA": st.column_config.TextColumn(
                "Média Diária",
                help="Média de conclusões por dia útil do período (seg-sáb)",
                width="small"
            ),
            "DIAS_TRABALHADOS": st.column_config.NumberColumn(
                "Dias Úteis",
                help="Quantidade de dias úteis (seg-sáb) entre a primeira e última conclusão",
                format="%d",
                width="small"
            ),
            "DIAS_COM_CONCLUSAO": st.column_config.NumberColumn(
                "Dias c/ Conclusão",
                help="Quantidade de dias em que houve pelo menos uma conclusão",
                format="%d",
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
        
        # Colunas a exibir - invertendo a ordem de Pendentes e Conclusões
        colunas_exibir = ['POSICAO_FORMATADA', 'STATUS', 'ASSIGNED_BY_NAME', 'PENDENTES', 
                          'TOTAL_CONCLUSOES', 'MEDIA_DIARIA_FORMATADA', 'DIAS_TRABALHADOS', 'DIAS_COM_CONCLUSAO', 'TAXA_CONCLUSAO']
        
        # Exibir o ranking usando o st.dataframe com column_config
        st.dataframe(
            ranking[colunas_exibir],
            column_config=colunas,
            use_container_width=True,
            hide_index=True,
            height=min(400, len(ranking) * 50 + 60)  # Ajusta a altura com base no número de linhas
        )
        
        # Informação sobre o cálculo
        st.markdown("""
        <div class="info-text">
          <strong>📊 Cálculo das médias:</strong> As médias são calculadas considerando os dias úteis (seg-sáb) entre a primeira e a última conclusão de cada responsável.<br>
          <strong>🏆 Destaque:</strong> Indica o responsável com a melhor média diária.
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar métricas dos 3 melhores (em um grid de métricas)
        if len(ranking) >= 3:
            # Usar o ranking já ordenado por total de conclusões (ranking principal)
            top3 = ranking.head(3).copy()
            
            # Calcular percentual em relação ao melhor (primeiro = 100%)
            melhor_total = top3['TOTAL_CONCLUSOES'].iloc[0]
            top3['PERCENTUAL'] = (top3['TOTAL_CONCLUSOES'] / melhor_total * 100).round(1)
            
            st.markdown("""
            <h3 style="font-size: 20px; margin-top: 30px; margin-bottom: 15px; color: #1A237E; font-weight: 800; font-family: Arial, Helvetica, sans-serif;">Top 3 - Maiores Totais de Conclusão</h3>
            <p style="color: #616161; font-size: 16px; margin-bottom: 20px; font-family: Arial, Helvetica, sans-serif;">
            Este ranking considera o <strong>total de conclusões</strong>, mantendo a mesma ordem da tabela acima.
            </p>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            for i, (idx, row) in enumerate(top3.iterrows()):
                col = [col1, col2, col3][i]
                with col:
                    media = row['MEDIA_DIARIA']
                    nome = row['ASSIGNED_BY_NAME']
                    total = row['TOTAL_CONCLUSOES']
                    dias = row['DIAS_TRABALHADOS']
                    percentual = row['PERCENTUAL']
                    percentual_texto = f"{percentual:.1f}%" if i > 0 else "100%"
                    # A posição no ranking já é a correta, pois estamos usando o mesmo ranking
                    posicao_ranking = int(row['POSICAO'])
                    
                    st.markdown(f"""
                    <div style="background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); height: 100%; border-top: 5px solid {'#FFD700' if i == 0 else '#C0C0C0' if i == 1 else '#CD7F32'}; font-family: Arial, Helvetica, sans-serif;">
                        <div style="font-size: 24px; text-align: center; margin-bottom: 10px;">{"🥇" if i == 0 else "🥈" if i == 1 else "🥉"}</div>
                        <div style="font-size: 18px; font-weight: 600; text-align: center; margin-bottom: 10px; color: #1A237E;">{nome}</div>
                        <div style="position: absolute; top: 10px; right: 10px; background-color: #f0f0f0; border-radius: 50%; width: 24px; height: 24px; display: flex; justify-content: center; align-items: center; font-size: 12px; font-weight: bold; color: #333;">{posicao_ranking}º</div>
                        <div style="font-size: 32px; font-weight: 800; text-align: center; margin-bottom: 5px; color: {'#FF6F00' if i == 0 else '#455A64' if i == 1 else '#6D4C41'};">{total}</div>
                        <div style="font-size: 14px; text-align: center; color: #757575;">conclusões</div>
                        <div style="font-size: 24px; font-weight: 800; text-align: center; margin-top: 15px; color: {'#FF6F00' if i == 0 else '#455A64' if i == 1 else '#6D4C41'};">{percentual_texto}</div>
                        <div style="font-size: 14px; text-align: center; color: #757575; margin-bottom: 10px;">produtividade</div>
                        <div style="font-size: 14px; text-align: center; margin-top: 15px; color: #616161;">média de {media:.2f} por dia em {dias} dias úteis</div>
                    </div>
                    """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao gerar ranking de produtividade: {str(e)}")

def mostrar_analises_temporais(df, date_from, date_to):
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
        
        if df_valido.empty:
            st.warning("Não há dados disponíveis para análises temporais.")
            return

        # Encontrar a data da primeira conclusão
        data_primeira_conclusao = df_valido['DATA_CONCLUSAO'].min().date()
        
        # Ajustar a data inicial para ser a data da primeira conclusão
        if isinstance(date_from, datetime):
            data_inicio_efetiva = max(date_from.date(), data_primeira_conclusao)
        else:
            data_inicio_efetiva = max(date_from, data_primeira_conclusao)
        
        # Garantir que date_from e date_to sejam datetime
        if not isinstance(date_from, datetime):
            date_from = datetime.combine(date_from, datetime.min.time())
        if not isinstance(date_to, datetime):
            date_to = datetime.combine(date_to, datetime.min.time())
        
        # Calcular dias úteis (dias em que houve trabalho) a partir da primeira conclusão
        dias_uteis_naturais = 0
        horas_uteis = 0
        
        # Calcular dias úteis e horas úteis
        data_atual = datetime.combine(data_inicio_efetiva, datetime.min.time())
        while data_atual.date() <= date_to.date():
            dia_semana = data_atual.weekday()
            if dia_semana <= 5:  # Segunda a sábado
                dias_uteis_naturais += 1
                if dia_semana <= 4:  # Segunda a sexta
                    horas_uteis += 12
                else:  # Sábado
                    horas_uteis += 3
            # Domingo não conta
            data_atual += timedelta(days=1)
        
        # Mostrar informações sobre o período com destaque
        st.markdown(f"""
        <div class="info-text" style="background-color: #f1f8e9; border-color: #558B2F; font-family: Arial, Helvetica, sans-serif;">
            <strong style="font-size: 20px; color: #33691E;">Análise do período:</strong> 
            <span style="font-weight: 700; font-size: 19px;">{data_inicio_efetiva.strftime('%d/%m/%Y')} a {date_to.strftime('%d/%m/%Y')}</span> | 
            <strong style="color: #33691E;">Dias úteis:</strong> 
            <span style="font-weight: 800; font-size: 20px;">{dias_uteis_naturais}</span> | 
            <strong style="color: #33691E;">Horas úteis:</strong> 
            <span style="font-weight: 800; font-size: 20px;">{horas_uteis}h</span>
        </div>
        """, unsafe_allow_html=True)

        # Destacar a data inicial efetiva (primeira conclusão)
        if isinstance(date_from, datetime) and data_inicio_efetiva > date_from.date():
            st.info(f"ℹ️ **Análises temporais consideram dados a partir da primeira conclusão** ({data_inicio_efetiva.strftime('%d/%m/%Y')}).")
        elif not isinstance(date_from, datetime) and data_inicio_efetiva > date_from:
            st.info(f"ℹ️ **Análises temporais consideram dados a partir da primeira conclusão** ({data_inicio_efetiva.strftime('%d/%m/%Y')}).")

        # Definir cores para melhor contraste
        cores = {
            'principal': '#000000',  # Preto para linha principal
            'media': '#FF5722',      # Laranja para média
            'media_ajustada': '#9C27B0',  # Roxo para média ajustada
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

        # Fonte nativa para todos os gráficos
        fonte_nativa = "Arial, Helvetica, sans-serif"

        # 1. Análise por Dia
        if tipo_analise == "Análise por Dia":
            # Agrupar dados por dia para contar conclusões
            df_diario_original = df_valido.groupby(df_valido['DATA_CONCLUSAO'].dt.date).size().reset_index(name='CONCLUSOES')
            
            # Criar um DataFrame com todos os dias do período (incluindo dias sem conclusões)
            # Converter para datetime se não for
            if not isinstance(date_from, datetime):
                date_from_dt = datetime.combine(date_from, datetime.min.time())
            else:
                date_from_dt = date_from
                
            if not isinstance(date_to, datetime):
                date_to_dt = datetime.combine(date_to, datetime.min.time())
            else:
                date_to_dt = date_to
            
            # Definir data mínima fixa (04/03 do ano atual)
            data_minima = datetime(date_to_dt.year, 3, 4)
            if data_minima > date_to_dt:  # Se 04/03 deste ano for futuro, usa ano anterior
                data_minima = datetime(date_to_dt.year - 1, 3, 4)
            
            # Usar a data máxima entre a data mínima fixa e a data escolhida pelo usuário
            date_from_efetiva = max(date_from_dt, data_minima)
            
            # Gerar lista de todos os dias no período
            todas_datas = pd.date_range(start=date_from_efetiva, end=date_to_dt, freq='D')
            df_todos_dias = pd.DataFrame({'DATA_CONCLUSAO': todas_datas.date})
            
            # Mesclar com dados originais (preservando todos os dias)
            df_diario = pd.merge(df_todos_dias, df_diario_original, how='left', on='DATA_CONCLUSAO')
            
            # Preencher NaN com 0 (dias sem conclusões)
            df_diario['CONCLUSOES'] = df_diario['CONCLUSOES'].fillna(0).astype(int)
            
            # Média simples (média aritmética diária)
            media_diaria_simples = df_diario['CONCLUSOES'].mean()
            
            # Média ajustada (por dia útil natural a partir da primeira conclusão)
            total_conclusoes = df_diario['CONCLUSOES'].sum()
            media_diaria_ajustada = round(total_conclusoes / dias_uteis_naturais, 2)
            
            # Calcular linha de tendência
            x = np.arange(len(df_diario))
            z = np.polyfit(x, df_diario['CONCLUSOES'], 1)
            p = np.poly1d(z)
            tendencia = p(x)
            
            fig = go.Figure()
            
            # Adicionar linha de média simples
            fig.add_trace(go.Scatter(
                x=df_diario['DATA_CONCLUSAO'],
                y=[media_diaria_simples] * len(df_diario),
                fill=None,
                mode='lines',
                line=dict(color=cores['media'], width=3, dash='dash'),
                name='Média Simples'
            ))
            
            # Adicionar linha de média ajustada por dias úteis
            fig.add_trace(go.Scatter(
                x=df_diario['DATA_CONCLUSAO'],
                y=[media_diaria_ajustada] * len(df_diario),
                fill=None,
                mode='lines',
                line=dict(color=cores['media_ajustada'], width=3, dash='dot'),
                name='Média por Dia Útil'
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
                    size=16,
                    symbol='circle',
                    line=dict(width=3, color=cores['tendencia'])
                ),
                text=df_diario['CONCLUSOES'],
                textposition='top center',
                textfont=dict(size=16, color='black', family=fonte_nativa),
                name='Conclusões',
                fillcolor=cores['area']
            ))
            
            # Atualizar layout com fontes nativas
            fig.update_layout(
                title={
                    'text': 'Conclusões por Dia',
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=28, color=cores['texto'], family=fonte_nativa)
                },
                xaxis_title={
                    'text': 'Data',
                    'font': dict(size=18, family=fonte_nativa)
                },
                yaxis_title={
                    'text': 'Número de Conclusões',
                    'font': dict(size=18, family=fonte_nativa)
                },
                height=550,
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
                    borderwidth=2,
                    font=dict(size=16, family=fonte_nativa)
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
                linecolor=cores['texto'],
                tickfont=dict(size=16, family=fonte_nativa),
                tickmode='array',  # Forçar exibição de todos os valores
                tickvals=df_diario['DATA_CONCLUSAO'].tolist(),  # Usar todos os dias como valores de ticks
                ticktext=[d.strftime('%d/%m') for d in df_diario['DATA_CONCLUSAO']],  # Formatar datas como DD/MM
                tickangle=45  # Rotacionar rótulos para evitar sobreposição
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
                linecolor=cores['texto'],
                tickfont=dict(size=16, family=fonte_nativa)
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
                textfont=dict(family=fonte_nativa, size=16),
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
                    'font': dict(size=28, color='#212121', family=fonte_nativa)
                },
                xaxis_title={
                    'text': 'Dia da Semana',
                    'font': dict(size=18, family=fonte_nativa)
                },
                yaxis_title={
                    'text': 'Número de Conclusões',
                    'font': dict(size=18, family=fonte_nativa)
                },
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
                    borderwidth=2,
                    font=dict(size=16, family=fonte_nativa)
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
                linecolor='#212121',
                tickfont=dict(size=16, family=fonte_nativa)
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
                linecolor='#212121',
                tickfont=dict(size=16, family=fonte_nativa)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar métricas sobre dia da semana
            dia_mais_produtivo = df_dia_semana.loc[df_dia_semana['CONCLUSOES'].idxmax()]
            
            st.markdown(f"""
            <div class="metrics-container" style="background-color: #f5f5f5; border: 2px solid #e0e0e0; box-shadow: 0 6px 15px rgba(0,0,0,0.1); font-family: Arial, Helvetica, sans-serif;">
                <h3 style="font-size: 24px; margin-bottom: 18px; color: #1A237E; font-weight: 800; text-transform: uppercase;">Métricas por Dia da Semana</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px;">
                    <div class="metric-box" style="border-left: 8px solid #1976D2; box-shadow: 0 5px 12px rgba(25, 118, 210, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800;">Dia Mais Produtivo</h3>
                        <p style="font-size: 28px; font-weight: 900; color: #1976D2;">{dia_mais_produtivo['DIA_SEMANA']}</p>
                        <small style="font-size: 17px; font-weight: 600;">{int(dia_mais_produtivo['CONCLUSOES'])} conclusões</small>
                    </div>
                    <div class="metric-box" style="border-left: 8px solid #FF5722; box-shadow: 0 5px 12px rgba(255, 87, 34, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800; color: #E64A19;">Média por Dia</h3>
                        <p style="font-size: 38px; font-weight: 900; color: #FF5722;">{media_semanal:.2f}</p>
                        <small style="font-size: 17px; font-weight: 600;">conclusões/dia</small>
                    </div>
                    <div class="metric-box" style="border-left: 8px solid #4CAF50; box-shadow: 0 5px 12px rgba(76, 175, 80, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800; color: #2E7D32;">Processos Únicos</h3>
                        <p style="font-size: 38px; font-weight: 900; color: #4CAF50;">{int(dia_mais_produtivo['PROCESSOS_UNICOS'])}</p>
                        <small style="font-size: 17px; font-weight: 600;">no dia mais produtivo</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

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
                textfont=dict(family=fonte_nativa, size=16),
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
                    'font': dict(size=28, color='#212121', family=fonte_nativa)
                },
                xaxis_title={
                    'text': 'Hora',
                    'font': dict(size=18, family=fonte_nativa)
                },
                yaxis_title={
                    'text': 'Número de Conclusões',
                    'font': dict(size=18, family=fonte_nativa)
                },
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
                    borderwidth=2,
                    font=dict(size=16, family=fonte_nativa)
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
                linecolor='#212121',
                tickfont=dict(size=16, family=fonte_nativa)
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
                linecolor='#212121',
                tickfont=dict(size=16, family=fonte_nativa)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar métricas sobre horários
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
            
            st.markdown(f"""
            <div class="metrics-container" style="background-color: #f5f5f5; border: 2px solid #e0e0e0; box-shadow: 0 6px 15px rgba(0,0,0,0.1); font-family: Arial, Helvetica, sans-serif;">
                <h3 style="font-size: 24px; margin-bottom: 18px; color: #1A237E; font-weight: 800; text-transform: uppercase;">Métricas por Hora</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px;">
                    <div class="metric-box" style="border-left: 8px solid #1976D2; box-shadow: 0 5px 12px rgba(25, 118, 210, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800;">Horário Mais Produtivo</h3>
                        <p style="font-size: 38px; font-weight: 900; color: #1976D2;">{hora_mais_produtiva['HORA']:02d}:00</p>
                        <small style="font-size: 17px; font-weight: 600;">{int(hora_mais_produtiva['CONCLUSOES'])} conclusões</small>
                    </div>
                    <div class="metric-box" style="border-left: 8px solid #FF5722; box-shadow: 0 5px 12px rgba(255, 87, 34, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800; color: #E64A19;">Período Mais Produtivo</h3>
                        <p style="font-size: 38px; font-weight: 900; color: #FF5722;">{periodo_mais_produtivo[0]}</p>
                        <small style="font-size: 17px; font-weight: 600;">{int(periodo_mais_produtivo[1])} conclusões</small>
                    </div>
                    <div class="metric-box" style="border-left: 8px solid #4CAF50; box-shadow: 0 5px 12px rgba(76, 175, 80, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800; color: #2E7D32;">Média por Hora</h3>
                        <p style="font-size: 38px; font-weight: 900; color: #4CAF50;">{media_hora:.2f}</p>
                        <small style="font-size: 17px; font-weight: 600;">conclusões/hora</small>
                    </div>
                    <div class="metric-box" style="border-left: 8px solid #9C27B0; box-shadow: 0 5px 12px rgba(156, 39, 176, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800; color: #7B1FA2;">Horas Produtivas</h3>
                        <p style="font-size: 38px; font-weight: 900; color: #9C27B0;">{len(df_hora[df_hora['CONCLUSOES'] > media_hora])}</p>
                        <small style="font-size: 17px; font-weight: 600;">acima da média</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
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
                textfont=dict(family=fonte_nativa, size=16),
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
                    'font': dict(size=28, color='#212121', family=fonte_nativa)
                },
                xaxis_title={
                    'text': 'Semana',
                    'font': dict(size=18, family=fonte_nativa)
                },
                yaxis_title={
                    'text': 'Número de Conclusões',
                    'font': dict(size=18, family=fonte_nativa)
                },
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
                    borderwidth=2,
                    font=dict(size=16, family=fonte_nativa)
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
                linecolor='#212121',
                tickfont=dict(size=16, family=fonte_nativa)
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
                linecolor='#212121',
                tickfont=dict(size=16, family=fonte_nativa)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar métricas por semana
            semana_mais_produtiva = df_semanal.loc[df_semanal['CONCLUSOES'].idxmax()]
            
            st.markdown(f"""
            <div class="metrics-container" style="background-color: #f5f5f5; border: 2px solid #e0e0e0; box-shadow: 0 6px 15px rgba(0,0,0,0.1); font-family: Arial, Helvetica, sans-serif;">
                <h3 style="font-size: 24px; margin-bottom: 18px; color: #1A237E; font-weight: 800; text-transform: uppercase;">Métricas por Semana</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px;">
                    <div class="metric-box" style="border-left: 8px solid #1976D2; box-shadow: 0 5px 12px rgba(25, 118, 210, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800;">Semana Mais Produtiva</h3>
                        <p style="font-size: 28px; font-weight: 900; color: #1976D2;">{semana_mais_produtiva['SEMANA']}</p>
                        <small style="font-size: 17px; font-weight: 600;">{int(semana_mais_produtiva['CONCLUSOES'])} conclusões</small>
                    </div>
                    <div class="metric-box" style="border-left: 8px solid #FF5722; box-shadow: 0 5px 12px rgba(255, 87, 34, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800; color: #E64A19;">Média por Semana</h3>
                        <p style="font-size: 38px; font-weight: 900; color: #FF5722;">{media_semanal:.2f}</p>
                        <small style="font-size: 17px; font-weight: 600;">conclusões/semana</small>
                    </div>
                    <div class="metric-box" style="border-left: 8px solid #4CAF50; box-shadow: 0 5px 12px rgba(76, 175, 80, 0.1); font-family: Arial, Helvetica, sans-serif;">
                        <h3 style="font-size: 21px; font-weight: 800; color: #2E7D32;">Total de Semanas</h3>
                        <p style="font-size: 38px; font-weight: 900; color: #4CAF50;">{len(df_semanal)}</p>
                        <small style="font-size: 17px; font-weight: 600;">com registros</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao exibir análises temporais: {str(e)}")
        import traceback
        st.error(traceback.format_exc())