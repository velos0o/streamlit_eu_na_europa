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
# --- NOVO: Importar nova página de Comune (Novo) ---
from views.comune_new.comune_new_main import show_comune_new
# --- NOVO: Importar Página Inicial ---
from views.pagina_inicial import show_pagina_inicial
# --- NOVO: Importar nova página unificada de Higienizações ---
from views.higienizacoes import show_higienizacoes

# Importar os novos componentes do guia de relatório
from components.report_guide import show_guide_sidebar, show_page_guide, show_contextual_help
from components.search_component import show_search_box
from components.table_of_contents import render_toc
# Importar o componente de botão de atualização
from components.refresh_button import render_refresh_button, render_sidebar_refresh_button
# --- NOVO: Importar componente de links rápidos ---
from components.quick_links import show_quick_links, show_page_links_sidebar

# ----- INÍCIO DA ADIÇÃO: PROCESSAMENTO DE URLs PERSONALIZADAS -----
# Mapeamento de rotas para páginas
ROTAS = {
    "pagina_inicial": "Página Inicial",
    "higienizacoes": "Higienizações",
    "cartorio_new": "Emissões Brasileiras",
    "comune_new": "Comune (Novo)",
    "comune": "Comune",
    "extracoes": "Extrações de Dados",
    "tickets": "Tickets",
    "reclamacoes": "Reclamações",
    "apresentacao": "Apresentação Conclusões"
}

# Mapeamento de sub-rotas para Emissões Brasileiras
SUB_ROTAS_EMISSOES = {
    "visao_geral": "Visão Geral",
    "acompanhamento": "Acompanhamento",
    "producao": "Produção",
    "pendencias": "Pendências",
    "higienizacao_desempenho": "Higienização Desempenho"
}

# Mapeamento de sub-rotas para Comune (Novo)
SUB_ROTAS_COMUNE = {
    "visao_geral": "Visão Geral",
    "tempo_solicitacao": "Tempo de Solicitação",
    "mapa_comune_1": "Mapa Comune 1",
    "mapa_comune_2": "Mapa Comune 2",
    "mapa_comune_3": "Mapa Comune 3"
}

# Mapeamento de sub-rotas para Higienizações
SUB_ROTAS_HIGIENIZACOES = {
    "producao": "Produção",
    "conclusoes": "Conclusões",
    "checklist": "Checklist"
}

# Processar parâmetros da URL
def processar_parametros_url():
    # Verificar se existe o parâmetro 'page' na URL
    if 'page' in st.query_params:
        rota = st.query_params['page'].lower()
        
        # Verificar se a rota existe no nosso mapeamento
        if rota in ROTAS:
            st.session_state['pagina_atual'] = ROTAS[rota]
            
            # Expandir submenu apropriado com base na página selecionada
            if rota == 'cartorio_new':
                st.session_state.emissao_submenu_expanded = True
                # Verificar se há subrota
                if 'sub' in st.query_params and st.query_params['sub'] in SUB_ROTAS_EMISSOES:
                    st.session_state.emissao_subpagina = SUB_ROTAS_EMISSOES[st.query_params['sub']]
                else:
                    st.session_state.emissao_subpagina = "Visão Geral"  # Valor padrão
                    
            elif rota == 'comune_new':
                st.session_state.comune_submenu_expanded = True
                # Verificar se há subrota
                if 'sub' in st.query_params and st.query_params['sub'] in SUB_ROTAS_COMUNE:
                    st.session_state.comune_subpagina = SUB_ROTAS_COMUNE[st.query_params['sub']]
                else:
                    st.session_state.comune_subpagina = "Visão Geral"  # Valor padrão
                    
            elif rota == 'higienizacoes':
                st.session_state.higienizacao_submenu_expanded = True
                # Verificar se há subrota
                if 'sub' in st.query_params and st.query_params['sub'] in SUB_ROTAS_HIGIENIZACOES:
                    st.session_state.higienizacao_subpagina = SUB_ROTAS_HIGIENIZACOES[st.query_params['sub']]
                else:
                    st.session_state.higienizacao_subpagina = "Produção"  # Valor padrão
                    
# Inicializar estado da sessão
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'Página Inicial'
# --- Estado para submenu Emissões --- 
if 'emissao_submenu_expanded' not in st.session_state:
    st.session_state.emissao_submenu_expanded = False
if 'emissao_subpagina' not in st.session_state:
    st.session_state.emissao_subpagina = 'Visão Geral' # Subpágina padrão
# --- Estado para submenu Comune (Novo) ---
if 'comune_submenu_expanded' not in st.session_state:
    st.session_state.comune_submenu_expanded = False
if 'comune_subpagina' not in st.session_state:
    st.session_state.comune_subpagina = 'Visão Geral' # Subpágina padrão
# --- Estado para submenu Higienizações ---
if 'higienizacao_submenu_expanded' not in st.session_state:
    st.session_state.higienizacao_submenu_expanded = False
if 'higienizacao_subpagina' not in st.session_state:
    st.session_state.higienizacao_subpagina = 'Produção' # Subpágina padrão

# Processar os parâmetros da URL
processar_parametros_url()
# ----- FIM DA ADIÇÃO: PROCESSAMENTO DE URLs PERSONALIZADAS -----

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
    st.session_state['pagina_atual'] = 'Página Inicial'
# --- NOVO: Estado para submenu Emissões --- 
if 'emissao_submenu_expanded' not in st.session_state:
    st.session_state.emissao_submenu_expanded = False
if 'emissao_subpagina' not in st.session_state:
    st.session_state.emissao_subpagina = 'Visão Geral' # Subpágina padrão

# --- NOVO: Estado para submenu Comune (Novo) ---
if 'comune_submenu_expanded' not in st.session_state:
    st.session_state.comune_submenu_expanded = False
if 'comune_subpagina' not in st.session_state:
    st.session_state.comune_subpagina = 'Visão Geral' # Subpágina padrão

# --- NOVO: Estado para submenu Higienizações ---
if 'higienizacao_submenu_expanded' not in st.session_state:
    st.session_state.higienizacao_submenu_expanded = False
if 'higienizacao_subpagina' not in st.session_state:
    st.session_state.higienizacao_subpagina = 'Produção' # Subpágina padrão

# Funções para alterar a página e controlar submenu
def reset_submenu():
    st.session_state.emissao_submenu_expanded = False
    st.session_state.comune_submenu_expanded = False # Resetar submenu Comune também
    st.session_state.higienizacao_submenu_expanded = False # Resetar submenu Higienizações também

# --- FUNÇÕES DE NAVEGAÇÃO COM ATUALIZAÇÃO DE URL ---
def ir_para_pagina_inicial():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Página Inicial'
    st.query_params['page'] = 'pagina_inicial'
    # Remover parâmetro 'sub' se existir
    if 'sub' in st.query_params:
        del st.query_params['sub']

def ir_para_inicio(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Macro Higienização'
    st.query_params['page'] = 'macro_higienizacao'
    if 'sub' in st.query_params:
        del st.query_params['sub']
        
def ir_para_producao(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Produção Higienização'
    st.query_params['page'] = 'producao_higienizacao'
    if 'sub' in st.query_params:
        del st.query_params['sub']
        
def ir_para_conclusoes(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Conclusões Higienização'
    st.query_params['page'] = 'conclusoes_higienizacao'
    if 'sub' in st.query_params:
        del st.query_params['sub']
        
def ir_para_comune(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Comune'
    st.query_params['page'] = 'comune'
    if 'sub' in st.query_params:
        del st.query_params['sub']
        
def ir_para_extracoes(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Extrações de Dados'
    st.query_params['page'] = 'extracoes'
    if 'sub' in st.query_params:
        del st.query_params['sub']
        
def ir_para_apresentacao(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Apresentação Conclusões'
    st.query_params['page'] = 'apresentacao'
    if 'sub' in st.query_params:
        del st.query_params['sub']
        
def ir_para_tickets(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Tickets'
    st.query_params['page'] = 'tickets'
    if 'sub' in st.query_params:
        del st.query_params['sub']
        
def ir_para_reclamacoes(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Reclamações'
    st.query_params['page'] = 'reclamacoes'
    if 'sub' in st.query_params:
        del st.query_params['sub']

# --- NOVO: Função para toggle e navegação do submenu Emissões ---
def toggle_emissao_submenu():
    st.session_state.emissao_submenu_expanded = not st.session_state.get('emissao_submenu_expanded', False)
    st.session_state.comune_submenu_expanded = False # Fecha outro submenu
    st.session_state.higienizacao_submenu_expanded = False # Fecha submenu Higienizações
    # Define a página principal e subpágina padrão ao abrir/fechar
    if st.session_state.emissao_submenu_expanded:
        st.session_state['pagina_atual'] = 'Emissões Brasileiras'
        st.query_params['page'] = 'cartorio_new'
        # Mantém a subpágina atual se já estiver em uma subpágina de Emissões
        if st.session_state.get('pagina_atual') != 'Emissões Brasileiras':
             st.session_state.emissao_subpagina = 'Visão Geral'
             st.query_params['sub'] = 'visao_geral'
    # Se fechar, mantém a URL atual

# --- NOVO: Funções on_click para sub-botões Emissões ---
def ir_para_emissao_visao_geral():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Visão Geral'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'visao_geral'

def ir_para_emissao_acompanhamento():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Acompanhamento'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'acompanhamento'

def ir_para_emissao_producao():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Produção'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'producao'

def ir_para_emissao_pendencias():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Pendências'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'pendencias'

# --- NOVO: Função on_click para sub-botão Higienização Desempenho ---
def ir_para_emissao_higienizacao_desempenho():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Higienização Desempenho'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'higienizacao_desempenho'

# --- NOVO: Função para toggle e navegação do submenu Comune (Novo) ---
def toggle_comune_submenu():
    st.session_state.comune_submenu_expanded = not st.session_state.get('comune_submenu_expanded', False)
    st.session_state.emissao_submenu_expanded = False # Fecha outro submenu
    st.session_state.higienizacao_submenu_expanded = False # Fecha submenu Higienizações
    # Define a página principal e subpágina padrão ao abrir/fechar
    if st.session_state.comune_submenu_expanded:
        st.session_state['pagina_atual'] = 'Comune (Novo)'
        st.query_params['page'] = 'comune_new'
        # Mantém a subpágina atual se já estiver em uma subpágina do Comune
        if st.session_state.get('pagina_atual') != 'Comune (Novo)':
            st.session_state.comune_subpagina = 'Visão Geral'
            st.query_params['sub'] = 'visao_geral'
    # Se fechar, mantém a URL atual

# --- NOVO: Função para toggle e navegação do submenu Higienizações ---
def toggle_higienizacao_submenu():
    st.session_state.higienizacao_submenu_expanded = not st.session_state.get('higienizacao_submenu_expanded', False)
    st.session_state.emissao_submenu_expanded = False # Fecha submenu Emissões
    st.session_state.comune_submenu_expanded = False # Fecha submenu Comune
    # Define a página principal e subpágina padrão ao abrir/fechar
    if st.session_state.higienizacao_submenu_expanded:
        st.session_state['pagina_atual'] = 'Higienizações'
        st.query_params['page'] = 'higienizacoes'
        # Mantém a subpágina atual se já estiver em uma subpágina de Higienizações
        if st.session_state.get('pagina_atual') != 'Higienizações':
            st.session_state.higienizacao_subpagina = 'Produção'
            st.query_params['sub'] = 'producao'
    # Se fechar, mantém a URL atual

# --- NOVO: Funções on_click para sub-botões de Higienizações ---
def ir_para_higienizacao_producao():
    st.session_state['pagina_atual'] = 'Higienizações'
    st.session_state.higienizacao_subpagina = 'Produção'
    st.query_params['page'] = 'higienizacoes'
    st.query_params['sub'] = 'producao'

def ir_para_higienizacao_conclusoes():
    st.session_state['pagina_atual'] = 'Higienizações'
    st.session_state.higienizacao_subpagina = 'Conclusões'
    st.query_params['page'] = 'higienizacoes'
    st.query_params['sub'] = 'conclusoes'

def ir_para_higienizacao_checklist():
    st.session_state['pagina_atual'] = 'Higienizações'
    st.session_state.higienizacao_subpagina = 'Checklist'
    st.query_params['page'] = 'higienizacoes'
    st.query_params['sub'] = 'checklist'

# Funções on_click para sub-botões Comune (Novo)
def ir_para_comune_visao_geral():
    st.session_state['pagina_atual'] = 'Comune (Novo)'
    st.session_state.comune_subpagina = 'Visão Geral'
    st.query_params['page'] = 'comune_new'
    st.query_params['sub'] = 'visao_geral'

def ir_para_comune_tempo_solicitacao():
    st.session_state['pagina_atual'] = 'Comune (Novo)'
    st.session_state.comune_subpagina = 'Tempo de Solicitação'
    st.query_params['page'] = 'comune_new'
    st.query_params['sub'] = 'tempo_solicitacao'

# Funções on_click para sub-botões do MAPA (dentro de Comune Novo)
def ir_para_mapa_comune_1():
    st.session_state['pagina_atual'] = 'Comune (Novo)' # Permanece na página principal
    st.session_state.comune_subpagina = 'Mapa Comune 1' # Define a subpágina para o mapa 1
    st.query_params['page'] = 'comune_new'
    st.query_params['sub'] = 'mapa_comune_1'

def ir_para_mapa_comune_2():
    st.session_state['pagina_atual'] = 'Comune (Novo)'
    st.session_state.comune_subpagina = 'Mapa Comune 2'
    st.query_params['page'] = 'comune_new'
    st.query_params['sub'] = 'mapa_comune_2'

def ir_para_mapa_comune_3():
    st.session_state['pagina_atual'] = 'Comune (Novo)'
    st.session_state.comune_subpagina = 'Mapa Comune 3'
    st.query_params['page'] = 'comune_new'
    st.query_params['sub'] = 'mapa_comune_3'

# --- NOVO: CSS ÚNICO para TODOS os sub-botões (movido de dentro dos ifs) ---
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
    color: #2563EB !important; /* Cor primária aproximada */
    background-color: rgba(59, 130, 246, 0.08) !important; /* Cor primária clara aproximada */
}
/* Estilo ATIVO (primary) - apenas muda peso e cor */
[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] [data-testid="stButton"] button[kind="primary"]:not([data-testid="stIconButton"]) {
    font-weight: 600 !important;
    color: #2563EB !important; /* Cor primária aproximada */
    background: none !important;
    border: none !important;
}
/* Garante que o foco não estrague o visual */
[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] [data-testid="stButton"] button:not([data-testid="stIconButton"]):focus {
    background: none !important;
    border: none !important;
    box-shadow: none !important;
}
/* Recuo do container do botão */
[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] {
    margin-left: 15px !important;
    padding: 0 !important;
    margin-bottom: 2px !important;
}
</style>
""", unsafe_allow_html=True)

# Botões individuais para navegação
st.sidebar.button("🏠 Página Inicial", key="btn_pagina_inicial",
            on_click=ir_para_pagina_inicial,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Página Inicial" else "secondary")

# --- NOVO: Botão para Higienizações agora usa toggle_higienizacao_submenu ---
st.sidebar.button("Higienizações", key="btn_higienizacoes", 
            on_click=toggle_higienizacao_submenu, 
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Higienizações" else "secondary",
            help="Módulo unificado de Higienizações (Produção, Conclusões e Checklist)")

# --- NOVO: Bloco condicional para o submenu Higienizações ---
if st.session_state.get('higienizacao_submenu_expanded', False):
    with st.sidebar.container():
        st.button("Produção", key="subbtn_higienizacao_producao",
                  on_click=ir_para_higienizacao_producao,
                  use_container_width=True,
                  type="primary" if st.session_state.get('higienizacao_subpagina') == "Produção" else "secondary")
        st.button("Conclusões", key="subbtn_higienizacao_conclusoes",
                  on_click=ir_para_higienizacao_conclusoes,
                  use_container_width=True,
                  type="primary" if st.session_state.get('higienizacao_subpagina') == "Conclusões" else "secondary")
        st.button("Checklist", key="subbtn_higienizacao_checklist",
                  on_click=ir_para_higienizacao_checklist,
                  use_container_width=True,
                  type="primary" if st.session_state.get('higienizacao_subpagina') == "Checklist" else "secondary")

# --- REMOVIDOS: Botões individuais para Macro, Produção e Conclusões (Agora estão no submenu) ---
# st.sidebar.button("Macro Higienização", key="btn_inicio"...)
# st.sidebar.button("Produção Higienização", key="btn_producao"...)
# st.sidebar.button("Conclusões Higienização", key="btn_conclusoes"...)

# --- ATUALIZADO: Botão para Emissões Brasileiras agora usa toggle_emissao_submenu ---
st.sidebar.button("Emissões Brasileiras", key="btn_cartorio_new", 
            on_click=toggle_emissao_submenu, 
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Emissões Brasileiras" else "secondary",
            help="Módulo refatorado de emissões de cartórios brasileiros")

# Bloco condicional para o submenu Emissões Brasileiras
if st.session_state.get('emissao_submenu_expanded', False):
    with st.sidebar.container():
        st.button("Visão Geral", key="subbtn_emissao_visao_geral",
                    on_click=ir_para_emissao_visao_geral,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Visão Geral" else "secondary")
        st.button("Acompanhamento", key="subbtn_emissao_acompanhamento",
                    on_click=ir_para_emissao_acompanhamento,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Acompanhamento" else "secondary")
        st.button("Produção", key="subbtn_emissao_producao",
                    on_click=ir_para_emissao_producao,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Produção" else "secondary")
        st.button("Pendências", key="subbtn_emissao_pendencias",
                    on_click=ir_para_emissao_pendencias,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Pendências" else "secondary")
        st.button("Higienização Desempenho", key="subbtn_emissao_higienizacao",
                    on_click=ir_para_emissao_higienizacao_desempenho,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Higienização Desempenho" else "secondary")

st.sidebar.button("Comune Bitrix24", key="btn_comune", 
            on_click=ir_para_comune,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Comune" else "secondary")

# --- NOVO: Botão para Comune (Novo) com toggle ---
st.sidebar.button("Comune (Novo)", key="btn_comune_new",
            on_click=toggle_comune_submenu,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Comune (Novo)" else "secondary",
            help="Módulo refatorado de Comune")

# --- NOVO: Bloco condicional para o submenu Comune (Novo) ---
if st.session_state.get('comune_submenu_expanded', False):
    with st.sidebar.container():
        # Botões diretamente dentro do container da sidebar
        st.button("Visão Geral", key="subbtn_comune_visao_geral",
                    on_click=ir_para_comune_visao_geral,
                    use_container_width=True,
                    type="primary" if st.session_state.get('comune_subpagina') == "Visão Geral" else "secondary")
        st.button("Tempo de Solicitação", key="subbtn_comune_tempo",
                    on_click=ir_para_comune_tempo_solicitacao,
                    use_container_width=True,
                    type="primary" if st.session_state.get('comune_subpagina') == "Tempo de Solicitação" else "secondary")
        
        # Adicionar Separador e Botões do Mapa
        st.markdown("<hr style='margin: 5px 0; border-top: 1px solid #ddd;'/>", unsafe_allow_html=True)
        st.markdown("<span style='font-size: 0.8em; color: #666; margin-left: 15px; font-weight: bold;'>Mapas</span>", unsafe_allow_html=True)
        
        st.button("Mapa Comune 1 (Cat 22)", key="subbtn_mapa_c1",
                    on_click=ir_para_mapa_comune_1,
                    use_container_width=True,
                    type="primary" if st.session_state.get('comune_subpagina') == "Mapa Comune 1" else "secondary")
        st.button("Mapa Comune 2 (Cat 58)", key="subbtn_mapa_c2",
                    on_click=ir_para_mapa_comune_2,
                    use_container_width=True,
                    type="primary" if st.session_state.get('comune_subpagina') == "Mapa Comune 2" else "secondary")
        st.button("Mapa Comune 3 (Cat 60)", key="subbtn_mapa_c3",
                    on_click=ir_para_mapa_comune_3,
                    use_container_width=True,
                    type="primary" if st.session_state.get('comune_subpagina') == "Mapa Comune 3" else "secondary")

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

# Adicionar o componente de links rápidos na barra lateral
show_page_links_sidebar()

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

# Função utilitária para gerar URLs de navegação
def gerar_url_navegacao(pagina, subpagina=None):
    """
    Gera URLs para navegação direta entre páginas do relatório.
    
    Args:
        pagina (str): Identificador da página (ex: 'pagina_inicial', 'cartorio_new')
        subpagina (str, optional): Identificador da subpágina quando aplicável
        
    Returns:
        str: URL formatada para navegação direta
    """
    base_url = "?"
    
    # Mapeamento reverso para encontrar as chaves (rotas) a partir dos nomes de páginas
    pagina_para_rota = {v: k for k, v in ROTAS.items()}
    
    if pagina in pagina_para_rota:
        rota = pagina_para_rota[pagina]
        url = f"{base_url}page={rota}"
        
        # Adicionar subpágina se especificada e relevante
        if subpagina:
            # Identificar o tipo de página para selecionar o mapeamento correto
            if pagina == "Emissões Brasileiras":
                # Mapeamento reverso para subpáginas de Emissões
                subpagina_para_rota = {v: k for k, v in SUB_ROTAS_EMISSOES.items()}
                if subpagina in subpagina_para_rota:
                    url += f"&sub={subpagina_para_rota[subpagina]}"
            
            elif pagina == "Comune (Novo)":
                # Mapeamento reverso para subpáginas de Comune
                subpagina_para_rota = {v: k for k, v in SUB_ROTAS_COMUNE.items()}
                if subpagina in subpagina_para_rota:
                    url += f"&sub={subpagina_para_rota[subpagina]}"
            
            elif pagina == "Higienizações":
                # Mapeamento reverso para subpáginas de Higienizações
                subpagina_para_rota = {v: k for k, v in SUB_ROTAS_HIGIENIZACOES.items()}
                if subpagina in subpagina_para_rota:
                    url += f"&sub={subpagina_para_rota[subpagina]}"
        
        return url
    
    # Se a página não for encontrada, retorna link para página inicial
    return f"{base_url}page=pagina_inicial"

# Exibição da página selecionada com base na variável de sessão
pagina = st.session_state['pagina_atual']

try:
    # Adicionar guia de página contextual para cada página
    if pagina != "Apresentação Conclusões":  # Não mostrar na apresentação
        show_page_guide(pagina)
    
    if pagina == "Página Inicial":
        show_pagina_inicial()
    elif pagina == "Macro Higienização":
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
        
    # --- NOVO: Roteamento para página de Higienizações ---
    elif pagina == "Higienizações":
        # Mostrar a página unificada de Higienizações, que irá rotear internamente
        # com base no valor de st.session_state.higienizacao_subpagina
        show_higienizacoes()
    # --- FIM NOVO ---
        
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
        
    # --- NOVO: Lógica para a página Comune (Novo) ---
    elif pagina == "Comune (Novo)":
        # Não precisa mais diferenciar 'Mapa Comunes' aqui
        show_comune_new() # A função interna agora roteia a subpágina
    # --- FIM NOVO ---
    
    # Adicionar seção de links rápidos no rodapé (apenas para páginas que não são de apresentação)
    if pagina != "Apresentação Conclusões":
        st.markdown("---")
        show_quick_links()

except Exception as e:
    st.error(f"Erro ao carregar a página: {str(e)}")
    # Mostrar detalhes do erro para facilitar a depuração
    st.exception(e)

# Rodapé do sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("Dashboard desenvolvido para análise de dados do CRM Bitrix24") 
