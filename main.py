import streamlit as st

# Configuração geral da página com temas avançados (novo na 1.44)
st.set_page_config(
    page_title="Dashboard CRM Bitrix24",
    page_icon="assets/LOGO-EU.NA.EUROPA-MAIO.24-COLORIDO-VERTICAL.svg",
    layout="wide",
    initial_sidebar_state="expanded" if "pagina_atual" not in st.session_state or st.session_state.get("pagina_atual") != "Apresentação Conclusões" else "collapsed"
)

import os
import sys
from pathlib import Path

# Configuração do ambiente
path_root = Path(__file__).parents[0]
sys.path.append(str(path_root))

# Importações das páginas - usando a pasta views
from views.inicio import show_inicio
from views.producao import show_producao
from views.conclusoes import show_conclusoes
from views.extracoes.extracoes_main import show_extracoes
# Importar nova página de apresentação de conclusões
from views.apresentacao import show_apresentacao
# Importar nova página de COMUNE
from views.comune.comune_main import show_comune
# Importar nova página de Tickets
from views.tickets import show_tickets
# Importar nova página de Reclamações (caminho atualizado)
from views.reclamacoes.reclamacoes_main import show_reclamacoes
# Importar nova página de Emissões Brasileiras
from views.cartorio_new.cartorio_new_main import show_cartorio_new

# Importar os novos componentes do guia de relatório
from components.report_guide import show_guide_sidebar, show_page_guide, show_contextual_help
from components.search_component import show_search_box
from components.table_of_contents import render_toc
# Importar o componente de botão de atualização
from components.refresh_button import render_refresh_button, render_sidebar_refresh_button

# Carregando CSS ainda necessário
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# CSS adicional para o botão de atualização gigante
st.markdown("""
<style>
/* CSS específico para o botão de atualização na barra lateral usando ID */
div.stButton > button#btn_sidebar_refresh_all {
    height: 120px !important;
    font-size: 24px !important;
    font-weight: 900 !important;
    letter-spacing: 1px !important;
    border-radius: 12px !important;
    margin: 15px 0 !important;
    padding: 10px !important;
    background-color: #FF5722 !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
    transition: all 0.3s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div.stButton > button#btn_sidebar_refresh_all:hover {
    background-color: #E64A19 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 15px rgba(0,0,0,0.3) !important;
}

/* Adicionar animação pulsante para chamar mais atenção */
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.03); }
    100% { transform: scale(1); }
}

div.stButton > button#btn_sidebar_refresh_all {
    animation: pulse 2s infinite;
}
</style>
""", unsafe_allow_html=True)

# Adicionar CSS para centralizar imagens no sidebar
st.markdown("""
<style>
    [data-testid="stSidebar"] [data-testid="stImage"] {
        text-align: center;
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 80%;
    }
    
    /* Melhor centralização da logo */
    [data-testid="stSidebar"] [data-testid="stImage"] > img {
        margin: 0 auto;
        display: block;
        max-width: 100%;
    }
    
    /* Container da imagem centralizado */
    [data-testid="stSidebar"] [data-testid="stImage"] > div {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* Espaçamento extra acima e abaixo da logo */
    [data-testid="stSidebar"] [data-testid="stImage"] {
        padding: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Adicionar logo no sidebar (método tradicional)
st.sidebar.image("assets/LOGO-EU.NA.EUROPA-MAIO.24-COLORIDO-VERTICAL.svg", width=500)

# Menu de navegação simplificado
st.sidebar.title("Dashboard CRM Bitrix24")

# Adicionar o botão grande de atualização na barra lateral
render_sidebar_refresh_button()

st.sidebar.markdown("---")

# Adicionar barra de pesquisa no topo do sidebar
show_search_box()
st.sidebar.markdown("---")

# Criar uma seção para os botões de navegação
st.sidebar.subheader("Navegação")

# Variáveis de estado para controlar a navegação
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'Macro Higienização'
# --- NOVO: Estado para submenu Emissões --- 
if 'emissao_submenu_expanded' not in st.session_state:
    st.session_state.emissao_submenu_expanded = False
if 'emissao_subpagina' not in st.session_state:
    st.session_state.emissao_subpagina = 'Visão Geral' # Subpágina padrão
# --- FIM NOVO ---

# Funções para alterar a página e controlar submenu
def reset_submenu():
    st.session_state.emissao_submenu_expanded = False

def ir_para_inicio(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Macro Higienização'
def ir_para_producao(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Produção Higienização'
def ir_para_conclusoes(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Conclusões Higienização'
def ir_para_comune(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Comune'
def ir_para_extracoes(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Extrações de Dados'
def ir_para_apresentacao(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Apresentação Conclusões'
def ir_para_tickets(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Tickets'
def ir_para_reclamacoes(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Reclamações'

# --- NOVO: Função para toggle e navegação do submenu Emissões ---
def toggle_emissao_submenu():
    st.session_state.emissao_submenu_expanded = not st.session_state.get('emissao_submenu_expanded', False)
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    # Define uma subpágina padrão ao abrir ou se já estiver aberto e clicar de novo
    st.session_state.emissao_subpagina = 'Visão Geral' 
# --- FIM NOVO ---

# --- NOVO: Funções on_click para sub-botões Emissões ---
def ir_para_emissao_visao_geral():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Visão Geral'
    # Não mexe em emissao_submenu_expanded

def ir_para_emissao_acompanhamento():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Acompanhamento'

def ir_para_emissao_producao():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Produção'

def ir_para_emissao_pendencias():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Pendências'
# --- FIM NOVO ---

# Botões individuais para navegação
st.sidebar.button("Macro Higienização", key="btn_inicio", 
            on_click=ir_para_inicio, 
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Macro Higienização" else "secondary")

st.sidebar.button("Produção Higienização", key="btn_producao", 
            on_click=ir_para_producao,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Produção Higienização" else "secondary",
            help="Visualização de produção de processos")

st.sidebar.button("Conclusões Higienização", key="btn_conclusoes", 
            on_click=ir_para_conclusoes,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Conclusões Higienização" else "secondary")

# --- ATUALIZADO: Botão para Emissões Brasileiras agora usa toggle_emissao_submenu ---
st.sidebar.button("Emissões Brasileiras", key="btn_cartorio_new", 
            on_click=toggle_emissao_submenu, 
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Emissões Brasileiras" else "secondary",
            help="Módulo refatorado de emissões de cartórios brasileiros")
# --- FIM ATUALIZADO ---

# --- ATUALIZADO: Bloco condicional para o submenu com funcionalidade ---
if st.session_state.get('emissao_submenu_expanded', False):
    with st.sidebar.container(): 
        # --- CSS Injetado para Estilo Persistente dos Sub-botões ---
        st.markdown("""
        <style>
        /* Base style para TODOS os sub-botões */
        [data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] [data-testid="stButton"] button:not([data-testid="stIconButton"]) {
            background: none !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0.25rem 0.5rem !important;
            margin: 0 !important;
            border-radius: 4px !important;
            font-size: 0.9em !important;
            text-align: left !important;
            width: 100% !important;
            display: block !important;
            line-height: 1.4 !important;
            font-weight: 400 !important;
            color: #333 !important;
            transition: background-color 0.1s ease, color 0.1s ease !important;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
        }
        /* Efeito Hover (para todos) */
        [data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] [data-testid="stButton"] button:not([data-testid="stIconButton"]):hover:not(:focus) {
            /* Usando cores fixas aqui, pois não temos variáveis SCSS */
            color: #2563EB !important; /* Cor primária aproximada */
            background-color: rgba(59, 130, 246, 0.08) !important; /* Cor primária clara aproximada */
        }
        /* Estilo ATIVO (primary) - apenas muda peso e cor */
        [data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] [data-testid="stButton"] button[kind="primary"]:not([data-testid="stIconButton"]) {
            font-weight: 600 !important;
            color: #2563EB !important; /* Cor primária aproximada */
            /* Garante que fundo e borda não voltem */
            background: none !important; 
            border: none !important;
        }
        /* Garante que o foco não estrague o visual */
        [data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] [data-testid="stButton"] button:not([data-testid="stIconButton"]):focus {
            background: none !important;
            border: none !important;
            box-shadow: none !important;
            /* outline: 2px solid rgba(59, 130, 246, 0.3) !important; */ /* Outline opcional */
        }
        /* Recuo do container do botão */
        [data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] {
            margin-left: 15px !important;
            padding: 0 !important;
            margin-bottom: 2px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        # --- Fim CSS Injetado ---

        # Botões diretamente dentro do container da sidebar
        st.button("Visão Geral", key="subbtn_visao_geral", 
                    on_click=ir_para_emissao_visao_geral,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Visão Geral" else "secondary")
        st.button("Acompanhamento", key="subbtn_acompanhamento", 
                    on_click=ir_para_emissao_acompanhamento,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Acompanhamento" else "secondary")
        st.button("Produção", key="subbtn_producao", 
                    on_click=ir_para_emissao_producao,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Produção" else "secondary")
        st.button("Pendências", key="subbtn_pendencias", 
                    on_click=ir_para_emissao_pendencias,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Pendências" else "secondary")
# --- FIM ATUALIZADO ---

st.sidebar.button("Comune Bitrix24", key="btn_comune", 
            on_click=ir_para_comune,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Comune" else "secondary")

st.sidebar.button("Extrações", key="btn_extracoes", 
            on_click=ir_para_extracoes,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Extrações de Dados" else "secondary")

st.sidebar.button("Tickets de Suporte", key="btn_tickets", 
            on_click=ir_para_tickets,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Tickets" else "secondary")

st.sidebar.button("Reclamações", key="btn_reclamacoes", 
            on_click=ir_para_reclamacoes,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Reclamações" else "secondary")

# Adicionar separador para seção de apresentação
st.sidebar.markdown("---")
st.sidebar.subheader("Modo Apresentação")

# Botão destacado para o modo de apresentação
st.sidebar.button("📺 Apresentação em TV (9:16)", key="btn_apresentacao", 
            on_click=ir_para_apresentacao,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Apresentação Conclusões" else "secondary")

# Adicionar o guia de relatório na barra lateral
show_guide_sidebar()

# Exibição da página selecionada com base na variável de sessão
pagina = st.session_state['pagina_atual']

try:
    # Adicionar guia de página contextual para cada página
    if pagina != "Apresentação Conclusões":  # Não mostrar na apresentação
        show_page_guide(pagina)
    
    if pagina == "Macro Higienização":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Métricas Gerais", "anchor": "metricas_gerais", "icon": "📊"},
            {"label": "Últimas Conclusões", "anchor": "ultimas_conclusoes", "icon": "✅"}
        ]
        show_inicio()
        
    elif pagina == "Produção Higienização":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Métricas de Produção", "anchor": "metricas_producao", "icon": "📊"},
            {"label": "Produção por Responsável", "anchor": "producao_responsavel", "icon": "👤"},
            {"label": "Tendências Temporais", "anchor": "tendencias_temporais", "icon": "📈"},
            {"label": "Pendências", "anchor": "pendencias", "icon": "⚠️"}
        ]
        show_producao()
        
    elif pagina == "Conclusões Higienização":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Métricas de Conclusão", "anchor": "metricas_conclusao", "icon": "📊"},
            {"label": "Análise de Qualidade", "anchor": "analise_qualidade", "icon": "🔍"},
            {"label": "Tendências de Conclusão", "anchor": "tendencias_conclusao", "icon": "📈"}
        ]
        show_conclusoes()
        
    elif pagina == "Comune":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Análise de Comunidades", "anchor": "analise_comunidades", "icon": "👥"},
            {"label": "Interações", "anchor": "interacoes", "icon": "🔄"},
            {"label": "Métricas de Engajamento", "anchor": "metricas_engajamento", "icon": "📊"}
        ]
        show_comune()
        
    elif pagina == "Extrações de Dados":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Extração Personalizada", "anchor": "extracao_personalizada", "icon": "🔍"},
            {"label": "Relatórios Prontos", "anchor": "relatorios_prontos", "icon": "📋"},
            {"label": "Exportação", "anchor": "exportacao", "icon": "📤"}
        ]
        show_extracoes()
        
    elif pagina == "Tickets":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Visão Geral", "anchor": "visao_geral", "icon": "📊"},
            {"label": "Por Tempo", "anchor": "por_tempo", "icon": "🕒"},
            {"label": "Detalhes", "anchor": "detalhes", "icon": "🔍"}
        ]
        show_tickets()
        
    elif pagina == "Reclamações":
        # Definir as seções para o sumário da página (atualizado)
        sections = [
            {"label": "Visão Geral", "anchor": "visao_geral", "icon": "📊"}, # O anchor pode ser o próprio subheader se não houver um explícito
            {"label": "Tendência", "anchor": "tendencia", "icon": "📈"},
            {"label": "Detalhes", "anchor": "detalhes_das_reclamacoes", "icon": "🔍"} # Usar o anchor do subheader em details.py
        ]
        show_reclamacoes() # Função importada do novo local
        
    elif pagina == "Apresentação Conclusões":
        # Verificar se há parâmetro 'slide' na URL
        slide_inicial = 0
        try:
            if 'slide' in st.query_params:
                slide_inicial = int(st.query_params['slide'])
                print(f"Iniciando apresentação a partir do slide: {slide_inicial}")
        except Exception as e:
            print(f"Erro ao processar parâmetro de slide: {str(e)}")
            
        # Chamar a função com o parâmetro de slide inicial
        show_apresentacao(slide_inicial=slide_inicial)
        
    # Nova lógica para a página refatorada
    elif pagina == "Emissões Brasileiras":
        # Define as seções para o sumário da página (precisa ser dinâmico ou removido)
        # sections = [...] 
        
        # Chama a função principal, que agora deve rotear internamente
        show_cartorio_new() # Assumindo que show_cartorio_new agora usa st.session_state.emissao_subpagina para rotear
        
except Exception as e:
    st.error(f"Erro ao carregar a página: {str(e)}")
    # Mostrar detalhes do erro para facilitar a depuração
    st.exception(e)

# Rodapé do sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("Dashboard desenvolvido para análise de dados do CRM Bitrix24") 
