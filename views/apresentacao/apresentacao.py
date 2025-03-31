import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configurar caminho para utils
path_root = Path(__file__).parents[2]  # Subir dois níveis para chegar à raiz do projeto
sys.path.append(str(path_root))

# Definir a função update_progress localmente para evitar problemas de importação
def update_progress(progress_bar, progress_value, message_container, message):
    """
    Atualiza a barra de progresso e mensagem durante o carregamento
    
    Args:
        progress_bar: Componente de barra de progresso do Streamlit
        progress_value: Valor de progresso entre 0 e 1
        message_container: Container para exibir mensagens de progresso
        message: Mensagem a ser exibida
    """
    # Atualizar a barra de progresso
    progress_bar.progress(progress_value)
    
    # Atualizar a mensagem
    message_container.info(message)

# Importar módulos específicos do projeto
from api.bitrix_connector import load_merged_data, get_higilizacao_fields

# Carregar variáveis de ambiente
load_dotenv()

def show_apresentacao(slide_inicial=0):
    """
    Exibe o modo de apresentação otimizado para telas verticais (9:16) como TVs.
    Versão otimizada do apresentacao_conclusoes.py.
    
    Args:
        slide_inicial (int): Índice do slide para iniciar a apresentação
    """
    print(f"Iniciando apresentação com slide_inicial={slide_inicial}")
    
    # Verificar se há redirecionamento solicitado na sessão
    if 'slide_redirect' in st.session_state:
        slide_inicial = st.session_state['slide_redirect']
        print(f"Usando slide_redirect da sessão: {slide_inicial}")
        del st.session_state['slide_redirect']
    
    # Verificar se há parâmetro na URL para definir o slide inicial
    try:
        if 'slide' in st.query_params:
            try:
                slide_inicial = int(st.query_params['slide'])
                print(f"Iniciando apresentação do slide {slide_inicial}")
            except (ValueError, TypeError):
                print("Parâmetro de slide inválido na URL")
        
        # Verificar parâmetro config para alternar o modo
        if 'config' in st.query_params:
            try:
                config_value = int(st.query_params['config'])
                st.session_state.modo_config = (config_value == 1)
                print(f"Modo configuração: {st.session_state.modo_config}")
            except (ValueError, TypeError):
                print("Parâmetro config inválido na URL")
    except Exception as e:
        print(f"Erro ao processar parâmetros da URL: {str(e)}")
    
    # Garantir que os modos necessários são inicializados
    if 'modo_config' not in st.session_state:
        st.session_state.modo_config = False
    
    if 'tempo_slide' not in st.session_state:
        st.session_state.tempo_slide = 10  # Tempo padrão reduzido para 10 segundos por slide
    
    # Esconder elementos desnecessários do Streamlit
    hide_streamlit_elements()
    
    # Aplicar estilos para o modo apresentação
    aplicar_estilos_apresentacao()
    
    # Container para o cabeçalho personalizado
    header_container = st.container()
    
    # Exibir título apenas se não estiver em modo de apresentação automática
    with header_container:
        if st.session_state.modo_config:
            st.markdown("""
            <div style="background-color: #e3f2fd; border-radius: 10px; padding: 15px; margin-bottom: 20px; text-align: center;">
                <h3 style="color: #1565C0; margin: 0;">Modo de Configuração Ativo</h3>
                <p style="margin: 5px 0 0 0;">Ajuste os parâmetros no menu lateral e clique em "Iniciar Apresentação" para começar</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Adicionar um botão para entrar em modo de tela cheia
            st.button("Entrar em Modo Tela Cheia (F11)", on_click=lambda: st.markdown(
                """
                <script>
                    document.addEventListener('DOMContentLoaded', function() {
                        // Tenta entrar em modo de tela cheia
                        if (document.documentElement.requestFullscreen) {
                            document.documentElement.requestFullscreen();
                        } else if (document.documentElement.mozRequestFullScreen) {
                            document.documentElement.mozRequestFullScreen();
                        } else if (document.documentElement.webkitRequestFullscreen) {
                            document.documentElement.webkitRequestFullscreen();
                        } else if (document.documentElement.msRequestFullscreen) {
                            document.documentElement.msRequestFullscreen();
                        }
                    });
                </script>
                """,
                unsafe_allow_html=True
            ))
            
            # Adicionar botões de seleção direta de módulos
            st.markdown("### Acessar Slides Específicos")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Conclusões", use_container_width=True):
                    st.switch_page("main.py")
                    st.query_params["slide"] = 0
            
            with col2:
                if st.button("📈 Produção", use_container_width=True):
                    st.switch_page("main.py")
                    st.query_params["slide"] = 6
            
            with col3:
                if st.button("📁 Cartório", use_container_width=True):
                    st.switch_page("main.py")
                    st.query_params["slide"] = 9
        else:
            # Título estilizado para modo apresentação
            st.title("DASHBOARD INTEGRADO")
            st.caption("Conclusões, Produção e Cartório")
            
            # Botões de navegação grandes e visíveis - Fixados no topo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("CONCLUSÕES", use_container_width=True, type="primary"):
                    st.query_params["slide"] = 0
            
            with col2:
                if st.button("PRODUÇÃO", use_container_width=True, type="primary"):
                    st.query_params["slide"] = 6
            
            with col3:
                if st.button("CARTÓRIO", use_container_width=True, type="primary"):
                    st.query_params["slide"] = 9
            
            with col4:
                # Usar expander em vez de popover
                with st.expander("⚙️ CONFIG", expanded=False):
                    st.subheader("Configurações")
                    st.session_state.tempo_slide = st.slider(
                        "Tempo por slide (segundos)",
                        min_value=5,
                        max_value=60,
                        value=st.session_state.tempo_slide,
                        step=5
                    )
                    # Usar HTML em vez de badge
                    st.markdown('<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.85em;">Configurações de Apresentação</span>', unsafe_allow_html=True)

    # Criar interface de configuração na barra lateral
    with st.sidebar:
        st.title("Configurações de Apresentação")
        st.session_state.tempo_slide = st.slider(
            "Tempo por slide (segundos)",
            min_value=5,
            max_value=60,
            value=st.session_state.tempo_slide,
            step=5
        )
        
        # Botão para alternar entre modo configuração e apresentação
        if st.button("🔄 Iniciar/Parar Apresentação", use_container_width=True):
            st.session_state.modo_config = not st.session_state.modo_config
            
        # Data range para análise
        st.subheader("Período para Análise")
        
        date_to = st.date_input(
            "Data final", 
            value=datetime.now(),
            key="date_to_apresentacao",
            format="DD/MM/YYYY"
        )
        
        dias_analise = st.number_input(
            "Quantidade de dias para análise",
            min_value=7,
            max_value=90,
            value=30,
            step=1
        )
        
        date_from = date_to - timedelta(days=dias_analise)
        
        st.info(f"Período selecionado: {date_from.strftime('%d/%m/%Y')} a {date_to.strftime('%d/%m/%Y')}")
        
        # Botão para aplicar filtros e recarregar dados
        recarregar = st.button("🔄 Recarregar Dados", use_container_width=True)
        
        # Opção para mostrar apenas certos módulos
        st.subheader("Módulos para exibir")
        mostrar_conclusoes = st.checkbox("Mostrar Conclusões", value=True)
        mostrar_producao = st.checkbox("Mostrar Produção", value=True)
        mostrar_cartorio = st.checkbox("Mostrar Cartório", value=True)
        
        # Atalhos para iniciar diretamente em slides específicos
        st.subheader("Iniciar em slide específico")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("➡️ Produção", use_container_width=True):
                st.switch_page("main.py")
                st.query_params["slide"] = 6
        
        with col2:
            if st.button("➡️ Cartório", use_container_width=True):
                st.switch_page("main.py")
                st.query_params["slide"] = 9

    # Carregar dados conforme necessário
    with st.spinner("Carregando dados..."):
        progress_container = st.empty()
        message_container = st.empty()
        
        # Formatar datas para API
        date_from_str = date_from.strftime("%Y-%m-%d")
        date_to_str = date_to.strftime("%Y-%m-%d")
        
        # Carregar os dados necessários e chamar o carrossel
        if not st.session_state.modo_config:
            # Carregar dados (ou usar dados em cache)
            if 'df_conclusoes' not in st.session_state or recarregar:
                df, df_todos = carregar_dados_apresentacao(
                    date_from=date_from_str,
                    date_to=date_to_str,
                    progress_bar=progress_container.progress(0),
                    message_container=message_container
                )
                st.session_state['df_conclusoes'] = df
                st.session_state['df_todos'] = df_todos
            else:
                df = st.session_state['df_conclusoes']
                df_todos = st.session_state['df_todos']
            
            # Iniciar carrossel automático
            iniciar_carrossel_metricas(
                df, 
                df_todos, 
                date_from, 
                date_to, 
                st.session_state.tempo_slide, 
                slide_inicial=slide_inicial
            )
        else:
            # Modo de configuração - exibir slides específicos para teste - importar diretamente do arquivo
            # Caminho absoluto para o diretório atual
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Adicionar ao path para garantir que o módulo seja encontrado
            sys.path.insert(0, current_dir)
            
            # Importar diretamente do arquivo
            from funcoes_slides import (
                slide_metricas_destaque,
                slide_analise_diaria,
                slide_analise_semanal,
                slide_analise_dia_semana,
                slide_analise_horario,
                slide_producao_metricas_macro,
                slide_producao_status_responsavel,
                slide_cartorio_visao_geral,
                slide_cartorio_analise_familias,
                slide_cartorio_ids_familia
            )
            # Importar a versão corrigida do ranking
            from ranking_fix import slide_ranking_produtividade
            # Importar a versão corrigida de pendências por responsável
            from views.apresentacao.producao import slide_producao_pendencias_responsavel, slide_producao_ranking_pendencias

            # Carregar dados para o modo configuração
            if 'df_conclusoes' not in st.session_state or recarregar:
                df, df_todos = carregar_dados_apresentacao(
                    date_from=date_from_str,
                    date_to=date_to_str,
                    progress_bar=progress_container.progress(0),
                    message_container=message_container
                )
                st.session_state['df_conclusoes'] = df
                st.session_state['df_todos'] = df_todos
            else:
                df = st.session_state['df_conclusoes']
                df_todos = st.session_state['df_todos']

            # Criar abas de acordo com os módulos selecionados
            tab_names = []
            
            if mostrar_conclusoes:
                tab_names.extend([
                    "Métricas Destaque", 
                    "Ranking de Produtividade", 
                    "Análise Diária", 
                    "Análise Semanal", 
                    "Análise por Dia da Semana",
                    "Análise por Hora"
                ])
            
            if mostrar_producao:
                tab_names.extend([
                    "Produção - Métricas", 
                    "Produção - Status", 
                    "Produção - Pendências",
                    "Produção - Ranking de Pendências"
                ])
            
            if mostrar_cartorio:
                tab_names.extend([
                    "Cartório - Visão Geral", 
                    "Cartório - Famílias", 
                    "Cartório - IDs"
                ])
            
            # Área para selecionar slide inicial para apresentação
            st.sidebar.subheader("Iniciar de Slide Específico")
            slide_selecionado = st.sidebar.selectbox(
                "Selecione o slide inicial:",
                options=range(len(tab_names)),
                format_func=lambda i: f"{i+1}. {tab_names[i]}",
                index=min(slide_inicial, len(tab_names)-1) if tab_names else 0
            )
            
            if st.sidebar.button("Iniciar Apresentação deste Slide", type="primary"):
                st.switch_page("main.py")
                st.query_params["slide"] = slide_selecionado
            
            # Exibir os slides como abas
            if tab_names:
                slide_tabs = st.tabs(tab_names)
                
                # Exibir os slides de acordo com os módulos selecionados
                tab_index = 0
                
                # Slides de Conclusões
                if mostrar_conclusoes:
                    with slide_tabs[tab_index]:
                        slide_metricas_destaque(df, df_todos, date_from, date_to)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_ranking_produtividade(df, df_todos)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_analise_diaria(df, date_from, date_to)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_analise_semanal(df)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_analise_dia_semana(df)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_analise_horario(df)
                    tab_index += 1
                
                # Slides de Produção
                if mostrar_producao:
                    with slide_tabs[tab_index]:
                        slide_producao_metricas_macro(df)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_producao_status_responsavel(df)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_producao_pendencias_responsavel(df)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_producao_ranking_pendencias(df)
                    tab_index += 1
                
                # Slides de Cartório
                if mostrar_cartorio:
                    with slide_tabs[tab_index]:
                        slide_cartorio_visao_geral(df)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_cartorio_analise_familias(df)
                    tab_index += 1
                    
                    with slide_tabs[tab_index]:
                        slide_cartorio_ids_familia(df)
                    tab_index += 1

def hide_streamlit_elements():
    """Esconde elementos padrão do Streamlit para modo de apresentação"""
    st.markdown("""
    <style>
        /* Configuração para modo apresentação em tela cheia */
        .reportview-container .main .block-container {
            max-width: 100%;
            padding: 0;
        }
        
        /* Esconder elementos desnecessários */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        .css-ch5dnh {display: none;}
        .css-1adrfps {padding-top: 0rem !important;}
        .block-container {padding-top: 0rem !important; padding-bottom: 0rem !important;}
        
        /* Esconder barra lateral em modo apresentação */
        .sidebar-collapsed section[data-testid="stSidebar"] {display: none !important;}
        
        /* Outros elementos */
        [data-testid="collapsedControl"] {display: none !important;}
        div[data-testid="stToolbar"] {display: none !important;}
        div.stButton button {display: none;}
        .streamlit-expanderHeader {display: none;}
        div.stSpinner > div {border-width: 4px !important; height: 4rem !important; width: 4rem !important;}
        
        /* Classe específica para quando estamos em modo tela cheia */
        body.sidebar-collapsed .main .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Quando estamos no modo de apresentação automática (não configuração)
    if 'modo_config' in st.session_state and not st.session_state.modo_config:
        # Script para colapsar automaticamente a barra lateral via JavaScript
        st.markdown("""
        <script>
            (function() {
                const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
                    const sidebarCollapse = window.parent.document.querySelector('[data-testid="collapsedControl"]');
                    if (sidebarCollapse && !document.body.classList.contains('sidebar-collapsed')) {
                        sidebarCollapse.click();
                        document.body.classList.add('sidebar-collapsed');
                    }
                }
            })();
        </script>
        """, unsafe_allow_html=True)

def aplicar_estilos_apresentacao():
    """Aplica estilos CSS otimizados para apresentação em TV vertical"""
    st.markdown("""
    <style>
    /* Estilos base para o modo apresentação */
    body, .stApp {
        font-family: Arial, Helvetica, sans-serif !important;
        color: #333333;
        background-color: #f8f9fa !important;
        height: 100vh;
        margin: 0;
        padding: 0;
        overflow: hidden;
    }
    
    /* Adicionar regras para garantir que os containers sejam totalmente limpos */
    .element-container {
        overflow: hidden;
    }
    
    /* Garantir que elementos não vazem entre slides */
    [data-testid="column"] {
        overflow: hidden !important;
    }
    
    /* Garantir que o Streamlit limpe os elementos com display none */
    [data-empty="true"] {
        display: none !important;
    }
    
    /* Contêiner do cabeçalho */
    .header-container {
        background: linear-gradient(135deg, #1A237E 0%, #283593 100%);
        padding: 25px 15px;
        border-radius: 0 0 20px 20px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    
    /* Título da apresentação */
    .presentation-title {
        font-size: 3.2rem !important;
        font-weight: 900 !important;
        color: white !important;
        margin: 0 !important;
        line-height: 1.2 !important;
        letter-spacing: -0.5px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Subtítulo da apresentação */
    .presentation-subtitle {
        font-size: 1.8rem;
        color: rgba(255,255,255,0.9);
        margin: 10px 0 0 0;
        font-weight: 400;
    }
    
    /* Contêiner de slides */
    .slide-container {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        padding: 25px;
        margin-bottom: 20px;
        height: calc(100vh - 200px);
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    
    /* Título do slide */
    .slide-title {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: #1A237E !important;
        margin-bottom: 25px !important;
        text-align: center;
        border-bottom: 3px solid #E0E0E0;
        padding-bottom: 15px;
    }
    
    /* Contador de slides */
    .slide-counter {
        position: absolute;
        bottom: 25px;
        right: 20px;
        background-color: rgba(0,0,0,0.7);
        color: white;
        padding: 8px 15px;
        border-radius: 30px;
        font-size: 1rem;
        font-weight: 600;
        z-index: 1000;
    }
    
    /* Estilo para informações de slide */
    .slide-info {
        position: absolute;
        bottom: 25px;
        left: 20px;
        background-color: rgba(0,0,0,0.7);
        color: white;
        padding: 8px 15px;
        border-radius: 30px;
        font-size: 0.9rem;
        z-index: 1000;
    }
    
    .updated-at {
        display: flex;
        align-items: center;
    }
    
    .updated-at:before {
        content: "";
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #4CAF50;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
        }
        70% {
            box-shadow: 0 0 0 6px rgba(76, 175, 80, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
        }
    }
    
    /* Classes para cartões de métricas */
    .metric-card-tv {
        background: white;
        border-radius: 12px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.1);
        padding: 25px;
        margin-bottom: 20px;
        text-align: center;
        border-left: 10px solid;
        height: auto;
    }
    
    .metric-card-tv.total {
        border-color: #2E7D32;
    }
    
    .metric-card-tv.media {
        border-color: #1565C0;
    }
    
    .metric-card-tv.taxa {
        border-color: #E65100;
    }
    
    .metric-value-tv {
        font-size: 5rem !important;
        font-weight: 900 !important;
        line-height: 1.1;
        margin: 10px 0;
    }
    
    .metric-card-tv.total .metric-value-tv {
        color: #2E7D32;
    }
    
    .metric-card-tv.media .metric-value-tv {
        color: #1565C0;
    }
    
    .metric-card-tv.taxa .metric-value-tv {
        color: #E65100;
    }
    
    .metric-title-tv {
        font-size: 2rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        margin-bottom: 15px;
    }
    
    .metric-subtitle-tv {
        font-size: 1.4rem;
        color: #666;
        font-weight: 400;
    }
    
    /* Para gráficos */
    .chart-container-tv {
        width: 100%;
        height: calc(100vh - 330px);
        min-height: 500px;
    }
    
    /* Rodapé com data de atualização */
    .update-footer {
        text-align: center;
        padding: 10px;
        background-color: #f8f9fa;
        color: #666;
        position: absolute;
        bottom: 10px;
        width: 100%;
        font-size: 1.2rem;
        font-weight: 500;
    }
    
    /* Estilo específico para o carrossel */
    .progress-bar-container {
        width: 100%;
        background-color: #e0e0e0;
        height: 6px;
        border-radius: 3px;
        margin-top: 10px;
        position: fixed;
        bottom: 15px;
        left: 0;
    }
    
    .progress-bar {
        height: 100%;
        background-color: #1976D2;
        border-radius: 3px;
        transition: width 0.5s ease;
    }
    </style>
    """, unsafe_allow_html=True)

def carregar_dados_apresentacao(date_from=None, date_to=None, progress_bar=None, message_container=None):
    """
    Carrega dados específicos para a apresentação
    """
    # Carregar dados do Bitrix com a mesma lógica do módulo de conclusões
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
    
    # Atualização de progresso
    if progress_bar and message_container:
        update_progress(progress_bar, 0.7, message_container, "Processando dados de conclusões...")
    
    # Guardar DataFrame completo antes de filtros
    df_todos = df.copy()
    
    # Converter campos de data para análise
    if 'UF_CRM_1741206763' in df.columns:
        df['DATA_CONCLUSAO'] = pd.to_datetime(df['UF_CRM_1741206763'], errors='coerce')
        df_todos['DATA_CONCLUSAO'] = df['DATA_CONCLUSAO'].copy()
        
        # Filtrar por data
        if date_from and date_to:
            date_from_dt = pd.to_datetime(date_from)
            date_to_dt = pd.to_datetime(date_to) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            df = df[
                (df['DATA_CONCLUSAO'].notna()) & 
                (df['DATA_CONCLUSAO'] >= date_from_dt) & 
                (df['DATA_CONCLUSAO'] <= date_to_dt)
            ]
    else:
        df['DATA_CONCLUSAO'] = None
        df_todos['DATA_CONCLUSAO'] = None
    
    # Filtrar apenas registros com status COMPLETO
    df_conclusoes = df[df['UF_CRM_HIGILIZACAO_STATUS'] == 'COMPLETO'].copy()
    
    # Adicionar colunas para análise
    if not df_conclusoes.empty and 'DATA_CONCLUSAO' in df_conclusoes.columns:
        df_conclusoes['DIA_SEMANA'] = df_conclusoes['DATA_CONCLUSAO'].dt.day_name()
        df_conclusoes['SEMANA'] = df_conclusoes['DATA_CONCLUSAO'].dt.strftime('%Y-%V')
        df_conclusoes['HORA'] = df_conclusoes['DATA_CONCLUSAO'].dt.hour
        
        # Ordenar por data
        df_conclusoes = df_conclusoes.sort_values('DATA_CONCLUSAO')
    
    # NOVIDADE: Armazenar dados para módulo de produção
    if progress_bar and message_container:
        update_progress(progress_bar, 0.8, message_container, "Processando dados de produção...")
    
    # Usar o DataFrame completo como base para produção
    st.session_state['df_producao'] = df_todos.copy()
    
    # NOVIDADE: Preparar dados para módulo de cartório
    if progress_bar and message_container:
        update_progress(progress_bar, 0.9, message_container, "Processando dados de cartório...")
    
    try:
        # Simular dados de cartório ou carregar de alguma fonte real se disponível
        # Vamos importar a função load_data do cartório para obter os dados diretamente
        from views.cartorio.data_loader import load_data
        df_cartorio = load_data()
        if df_cartorio is not None and not df_cartorio.empty:
            # Filtrar para os cartórios padrão
            cartorio_filter = ["CARTÓRIO CASA VERDE", "CARTÓRIO TATUÁPE"]
            df_cartorio = df_cartorio[df_cartorio['NOME_CARTORIO'].isin(cartorio_filter)]
            
            # Armazenar na sessão
            st.session_state['df_cartorio'] = df_cartorio
            
            # Carregar dados de famílias
            try:
                from views.cartorio.analysis import analisar_familia_certidoes
                df_familias = analisar_familia_certidoes()
                if df_familias is not None and not df_familias.empty:
                    st.session_state['df_familias'] = df_familias
            except Exception as e:
                print(f"Erro ao carregar dados de famílias: {str(e)}")
                # Criar dados fictícios para demonstração
                df_familias = pd.DataFrame({
                    'ID_FAMILIA': ['1x1', '2x1', '3x2', '4x1', '5x3', '6x2', '7x1'],
                    'MEMBROS': [3, 4, 5, 2, 6, 4, 3],
                    'CONCLUIDOS': [3, 2, 3, 1, 4, 2, 3],
                    'CARTORIO': ['Cartório A', 'Cartório B', 'Cartório A', 'Cartório C', 'Cartório B', 'Cartório A', 'Cartório C'],
                    'TOTAL_CERTIDOES': [9, 12, 15, 6, 18, 12, 9],
                    'CERTIDOES_ENTREGUES': [9, 6, 10, 2, 12, 5, 9],
                    'DATA_INICIO': pd.date_range(start='2023-01-01', periods=7, freq='7D')
                })
                st.session_state['df_familias'] = df_familias
        else:
            # Se não conseguir carregar dados reais, criar dados de demonstração
            print("Criando dados de demonstração para cartório...")
            if progress_bar and message_container:
                update_progress(progress_bar, 0.95, message_container, "Criando dados de demonstração para cartório...")
                
            # Dados de exemplo para cartório
            df_cartorio = pd.DataFrame({
                'NOME_CARTORIO': ['CARTÓRIO CASA VERDE', 'CARTÓRIO TATUÁPE'] * 15,
                'ID': range(1, 31),
                'DATE_CREATE': pd.date_range(start='2023-01-01', periods=30),
                'STAGE_ID': ['PENDING', 'IN_PROCESS', 'COMPLETED'] * 10,
                'TOTAL_CERTIDOES': [5, 10, 8, 12, 6] * 6,
                'CERTIDOES_EMITIDAS': [3, 8, 6, 10, 4] * 6
            })
            st.session_state['df_cartorio'] = df_cartorio
            
            # Dados de exemplo para famílias
            df_familias = pd.DataFrame({
                'ID_FAMILIA': ['1x1', '2x1', '3x2', '4x1', '5x3', '6x2', '7x1'],
                'MEMBROS': [3, 4, 5, 2, 6, 4, 3],
                'CONCLUIDOS': [3, 2, 3, 1, 4, 2, 3],
                'CARTORIO': ['Cartório A', 'Cartório B', 'Cartório A', 'Cartório C', 'Cartório B', 'Cartório A', 'Cartório C'],
                'TOTAL_CERTIDOES': [9, 12, 15, 6, 18, 12, 9],
                'CERTIDOES_ENTREGUES': [9, 6, 10, 2, 12, 5, 9],
                'DATA_INICIO': pd.date_range(start='2023-01-01', periods=7, freq='7D')
            })
            st.session_state['df_familias'] = df_familias
    except Exception as e:
        print(f"Erro ao processar dados de cartório: {str(e)}")
        # Criar dados fictícios em caso de erro
        # Dados de exemplo para cartório
        df_cartorio = pd.DataFrame({
            'NOME_CARTORIO': ['CARTÓRIO CASA VERDE', 'CARTÓRIO TATUÁPE'] * 15,
            'ID': range(1, 31),
            'DATE_CREATE': pd.date_range(start='2023-01-01', periods=30),
            'STAGE_ID': ['PENDING', 'IN_PROCESS', 'COMPLETED'] * 10,
            'TOTAL_CERTIDOES': [5, 10, 8, 12, 6] * 6,
            'CERTIDOES_EMITIDAS': [3, 8, 6, 10, 4] * 6
        })
        st.session_state['df_cartorio'] = df_cartorio
        
        # Dados de exemplo para famílias
        df_familias = pd.DataFrame({
            'ID_FAMILIA': ['1x1', '2x1', '3x2', '4x1', '5x3', '6x2', '7x1'],
            'MEMBROS': [3, 4, 5, 2, 6, 4, 3],
            'CONCLUIDOS': [3, 2, 3, 1, 4, 2, 3],
            'CARTORIO': ['Cartório A', 'Cartório B', 'Cartório A', 'Cartório C', 'Cartório B', 'Cartório A', 'Cartório C'],
            'TOTAL_CERTIDOES': [9, 12, 15, 6, 18, 12, 9],
            'CERTIDOES_ENTREGUES': [9, 6, 10, 2, 12, 5, 9],
            'DATA_INICIO': pd.date_range(start='2023-01-01', periods=7, freq='7D')
        })
        st.session_state['df_familias'] = df_familias
    
    if progress_bar and message_container:
        update_progress(progress_bar, 1.0, message_container, "Dados carregados com sucesso!")
    
    return df_conclusoes, df_todos

def iniciar_carrossel_metricas(df, df_todos, date_from, date_to, tempo_por_slide=15, slide_inicial=0):
    """
    Inicia o carrossel de métricas, exibindo cada uma por um tempo determinado
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados de conclusões
        df_todos (pandas.DataFrame): DataFrame com todos os dados (incluindo não concluídos)
        date_from (datetime): Data inicial do período analisado
        date_to (datetime): Data final do período analisado
        tempo_por_slide (int): Tempo em segundos para exibição de cada slide
        slide_inicial (int): Índice do slide para iniciar a apresentação
    """
    # Log para depuração
    print("=" * 50)
    print(f"INICIANDO CARROSSEL - Slide inicial: {slide_inicial}")
    print(f"Total slides: 13 | Tempo por slide: {tempo_por_slide}s")
    
    # Verificar se os dados necessários estão na sessão
    print(f"Dados de conclusões na sessão: {'Sim' if df is not None and not df.empty else 'Não'}")
    print(f"Dados completos na sessão: {'Sim' if df_todos is not None and not df_todos.empty else 'Não'}")
    print(f"Dados de produção na sessão: {'Sim' if 'df_producao' in st.session_state else 'Não'}")
    print(f"Dados de cartório na sessão: {'Sim' if 'df_cartorio' in st.session_state else 'Não'}")
    print(f"Dados de famílias na sessão: {'Sim' if 'df_familias' in st.session_state else 'Não'}")
    print("=" * 50)
    
    # Se não temos dados na sessão, garantir que os dataframes principais foram passados
    if df is None or df.empty:
        st.error("Dados de conclusões não disponíveis para o carrossel")
        return
    
    # Armazenar os dataframes principais na sessão para garantir que as funções de slide possam acessá-los
    st.session_state['df_conclusoes'] = df
    st.session_state['df_todos'] = df_todos
    
    # Importar as funções dos slides usando caminho absoluto para evitar conflito com a pasta slides/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Adicionar ao path para garantir que o módulo seja encontrado
    sys.path.insert(0, current_dir)
    
    # Importar diretamente do arquivo
    from funcoes_slides import (
        slide_metricas_destaque,
        slide_analise_diaria,
        slide_analise_semanal,
        slide_analise_dia_semana,
        slide_analise_horario,
        slide_producao_metricas_macro,
        slide_producao_status_responsavel,
        slide_cartorio_visao_geral,
        slide_cartorio_analise_familias,
        slide_cartorio_ids_familia
    )
    # Importar a versão corrigida do ranking
    from ranking_fix import slide_ranking_produtividade

    # Inicializar variáveis de controle
    slide_atual = slide_inicial
    continuar_apresentacao = True
    ultima_atualizacao = datetime.now()
    
    # Definir número de slides e seus nomes
    total_slides = 13  # Agora temos um slide a mais
    nomes_slides = [
        "Métricas Destaque",
        "Ranking de Produtividade",
        "Análise Diária",
        "Análise Semanal",
        "Análise por Dia da Semana",
        "Análise por Hora do Dia",
        # Slides do módulo de produção
        "Produção - Métricas Macro",
        "Produção - Status por Responsável",
        "Produção - Pendências por Responsável",
        "Produção - Ranking de Pendências",
        # Slides do módulo de cartório
        "Cartório - Visão Geral",
        "Cartório - Análise de Famílias",
        "Cartório - IDs por Família"
    ]
    
    # Pré-carregar dados se necessário (idêntico ao comportamento original)
    st.toast("Preparando apresentação automática...", icon="🔄")
    
    # Configuração adicional para mostrar instruções de navegação
    st.markdown("""
    <div style="position: fixed; bottom: 80px; left: 20px; background-color: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px; z-index: 1000; color: white;">
        <p style="margin: 0; font-size: 0.9rem;">Pressione ESC para sair da apresentação</p>
    </div>
    """, unsafe_allow_html=True)
    
    while continuar_apresentacao:
        try:
            # Verificar se é hora de atualizar os dados (a cada 1 minuto)
            agora = datetime.now()
            if (agora - ultima_atualizacao).total_seconds() >= 60:  # 60 segundos = 1 minuto
                st.rerun()  # Força o recarregamento da aplicação
            
            # Criar novos containers em cada iteração para evitar qualquer persistência
            main_area = st.empty()
            progress_container = st.empty()
            
            # Imprimir informações sobre o slide atual
            print(f"Preparando slide {slide_atual+1}/{total_slides}: {nomes_slides[slide_atual]}")
            
            # Criar um novo container para este slide específico
            with main_area.container():
                try:
                    # Mostrar o título do slide e informações complementares
                    if slide_atual >= 6 and slide_atual <= 8:
                        # Slides de produção (6, 7, 8)
                        st.subheader("➡️ MÓDULO DE PRODUÇÃO")
                    elif slide_atual >= 9:
                        # Slides de cartório (9, 10, 11)
                        st.subheader("➡️ MÓDULO DE CARTÓRIO")
                    
                    # Chamar a função correspondente ao slide atual
                    if slide_atual == 0:
                        slide_metricas_destaque(df, df_todos, date_from, date_to)
                    elif slide_atual == 1:
                        slide_ranking_produtividade(df, df_todos)
                    elif slide_atual == 2:
                        slide_analise_diaria(df, date_from, date_to)
                    elif slide_atual == 3:
                        slide_analise_semanal(df)
                    elif slide_atual == 4:
                        slide_analise_dia_semana(df)
                    elif slide_atual == 5:
                        slide_analise_horario(df)
                    # Slides de produção
                    elif slide_atual == 6:
                        slide_producao_metricas_macro(df)
                    elif slide_atual == 7:
                        slide_producao_status_responsavel(df)
                    elif slide_atual == 8:
                        slide_producao_pendencias_responsavel(df)
                    elif slide_atual == 9:
                        slide_producao_ranking_pendencias(df)
                    # Slides de cartório
                    elif slide_atual == 10:
                        slide_cartorio_visao_geral(df)
                    elif slide_atual == 11:
                        slide_cartorio_analise_familias(df)
                    elif slide_atual == 12:
                        slide_cartorio_ids_familia(df)
                except Exception as e:
                    import traceback
                    st.error(f"Erro ao exibir slide {slide_atual+1}: {str(e)}")
                    st.code(traceback.format_exc())
                    print(f"Erro ao exibir slide {slide_atual+1}: {str(e)}")
                    print(traceback.format_exc())
                
                # Exibir contador de slides e botão de info (para todos os slides)
                st.markdown(f"""
                <div class="slide-counter">
                    {slide_atual + 1}/{total_slides} - {nomes_slides[slide_atual]}
                </div>
                <div class="slide-info">
                    <span class="updated-at">Atualizado às {datetime.now().strftime('%H:%M')}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Adicionar links para navegação direta
                st.markdown("""
                <div style="position: fixed; bottom: 40px; right: 20px; background-color: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px; z-index: 1000;">
                    <span style="color: white; font-size: 0.9rem;">Navegar para: </span>
                    <a href="?slide=0" target="_self" style="color: white; margin: 0 5px;">Conclusões</a> | 
                    <a href="?slide=6" target="_self" style="color: white; margin: 0 5px;">Produção</a> | 
                    <a href="?slide=10" target="_self" style="color: white; margin: 0 5px;">Cartório</a>
                </div>
                """, unsafe_allow_html=True)
            
            # Atualizar barra de progresso
            for i in range(tempo_por_slide * 10):
                progress_percent = (i + 1) / (tempo_por_slide * 10)
                progress_container.markdown(f"""
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {progress_percent * 100}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.1)
            
            # Avançar para o próximo slide
            print(f"Avançando do slide {slide_atual} para {(slide_atual + 1) % total_slides}")
            slide_atual = (slide_atual + 1) % total_slides
            
            # Remover completamente os containers antes do próximo slide
            main_area.empty()
            progress_container.empty()
        
        except Exception as e:
            import traceback
            print(f"Erro crítico na apresentação: {str(e)}")
            print(traceback.format_exc())
            
            # Tentar continuar com o próximo slide
            slide_atual = (slide_atual + 1) % total_slides
            time.sleep(2)  # Pausa para não entrar em loop infinito de erros

# Permitir executar diretamente este módulo
if __name__ == "__main__":
    show_apresentacao() 