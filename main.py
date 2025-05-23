import streamlit as st

# Configuração geral da página com temas avançados (novo na 1.44)
st.set_page_config(
    page_title="Dashboard CRM Bitrix24",
    page_icon="assets/LOGO-EU.NA.EUROPA-MAIO.24-COLORIDO-VERTICAL.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import sys
from pathlib import Path

# Configuração do ambiente
path_root = Path(__file__).parents[0]
sys.path.append(str(path_root))

# Importações das páginas - usando a pasta views
from views.inicio import show_inicio
from views.extracoes.extracoes_main import show_extracoes
from views.cartorio_new.cartorio_new_main import show_cartorio_new
from views.ficha_familia import show_ficha_familia
from views.higienizacoes.higienizacoes_main import show_higienizacoes

# Importar os novos componentes
from components.report_guide import show_guide_sidebar, show_page_guide, show_contextual_help
from components.search_component import show_search_box
from components.table_of_contents import render_toc
from components.refresh_button import render_refresh_button, render_sidebar_refresh_button
from components.quick_links import show_quick_links, show_page_links_sidebar

# Mapeamento de rotas para páginas
ROTAS = {
    "ficha_familia": "Ficha da Família",
    "higienizacoes": "Higienizações", 
    "cartorio_new": "Emissões Brasileiras",
    "extracoes": "Extrações de Dados"
}

# Mapeamento de sub-rotas para Emissões Brasileiras
SUB_ROTAS_EMISSOES = {
    "funil_certidoes": "Funil Certidões",
    "emissoes_por_familia": "Emissões Por Família",
    "producao": "Produção",
    "adm": "ADM",
    "certidoes_pendentes_responsavel": "Certidões Pendentes por responsável",
    "desempenho_conclusao_pasta": "Desempenho Conclusão de Pasta",
    "producao_time_doutora": "Produção Time Doutora",
    "pesquisa_br": "Pesquisa BR"
}

# Mapeamento de sub-rotas para o submenu ADM
SUB_ROTAS_ADM = {
    "producao_adm": "Produção ADM",
    "certidoes_pendentes_adm": "Certidões Pendentes por ADM"
}

# Mapeamento de sub-rotas para Higienizações
SUB_ROTAS_HIGIENIZACOES = {
    "checklist": "Checklist"
}

# Função para inicializar todos os estados da sessão
def inicializar_estados_sessao():
    """Inicializa todos os estados da sessão necessários"""
    if 'pagina_atual' not in st.session_state:
        st.session_state['pagina_atual'] = 'Ficha da Família'
    
    if 'emissao_submenu_expanded' not in st.session_state:
        st.session_state.emissao_submenu_expanded = False
    if 'emissao_subpagina' not in st.session_state:
        st.session_state.emissao_subpagina = 'Funil Certidões'
    
    if 'adm_submenu_expanded' not in st.session_state:
        st.session_state.adm_submenu_expanded = False
    if 'adm_subpagina' not in st.session_state:
        st.session_state.adm_subpagina = 'Produção ADM'
    
    if 'higienizacao_submenu_expanded' not in st.session_state:
        st.session_state.higienizacao_submenu_expanded = False
    if 'higienizacao_subpagina' not in st.session_state:
        st.session_state.higienizacao_subpagina = 'Checklist'

# Processar parâmetros da URL
def processar_parametros_url():
    """Processa parâmetros da URL para navegação direta"""
    if 'pagina_atual_via_url_processada' not in st.session_state and 'page' in st.query_params:
        rota = st.query_params['page'].lower()
        if rota in ROTAS:
            st.session_state['pagina_atual'] = ROTAS[rota]
            st.session_state['pagina_atual_via_url_processada'] = True

            if rota == 'cartorio_new':
                st.session_state.emissao_submenu_expanded = True
                if 'sub' in st.query_params and st.query_params['sub'] in SUB_ROTAS_EMISSOES:
                    st.session_state.emissao_subpagina = SUB_ROTAS_EMISSOES[st.query_params['sub']]
                else:
                    st.session_state.emissao_subpagina = "Funil Certidões"
            elif rota == 'higienizacoes':
                st.session_state.higienizacao_submenu_expanded = True
                if 'sub' in st.query_params and st.query_params['sub'] in SUB_ROTAS_HIGIENIZACOES:
                    st.session_state.higienizacao_subpagina = SUB_ROTAS_HIGIENIZACOES[st.query_params['sub']]
                else:
                    st.session_state.higienizacao_subpagina = "Checklist"
    elif 'pagina_atual_via_url_processada' not in st.session_state:
        st.session_state['pagina_atual_via_url_processada'] = True

# Inicializar estados da sessão PRIMEIRO
inicializar_estados_sessao()

# Processar parâmetros da URL DEPOIS da inicialização
processar_parametros_url()

# Carregando CSS
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# CSS para botões e interface
st.markdown("""
<style>
/* CSS para botão de atualização */
div.stButton > button#btn_sidebar_refresh_all {
    font-size: 18px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    margin: 10px 0 !important;
    background-color: #2196F3 !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    transition: all 0.2s ease !important;
}

div.stButton > button#btn_sidebar_refresh_all:hover {
    background-color: #1976D2 !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
}

/* CSS para centralizar imagens no sidebar */
[data-testid="stSidebar"] [data-testid="stImage"] {
    text-align: center;
    display: block;
    margin-left: auto;
    margin-right: auto;
    width: 80%;
}

[data-testid="stSidebar"] [data-testid="stImage"] > img {
    margin: 0 auto;
    display: block;
    max-width: 100%;
}

[data-testid="stSidebar"] [data-testid="stImage"] > div {
    display: flex;
    justify-content: center;
    align-items: center;
}

[data-testid="stSidebar"] [data-testid="stImage"] {
    padding: 10px 0;
}

/* CSS para sub-botões */
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
}

[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] [data-testid="stButton"] button:not([data-testid="stIconButton"]):hover:not(:focus) {
    color: #2563EB !important;
    background-color: rgba(59, 130, 246, 0.08) !important;
}

[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] [data-testid="stButton"] button[kind="primary"]:not([data-testid="stIconButton"]) {
    font-weight: 600 !important;
    color: #2563EB !important;
    background: none !important;
    border: none !important;
}

[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_"] {
    margin-left: 15px !important;
    padding: 0 !important;
    margin-bottom: 2px !important;
}
</style>
""", unsafe_allow_html=True)

# Adicionar logo no sidebar
st.sidebar.image("assets/LOGO-EU.NA.EUROPA-MAIO.24-COLORIDO-VERTICAL.svg", width=500)

# Menu de navegação
st.sidebar.title("Dashboard CRM Bitrix24")
show_search_box()
st.sidebar.markdown("---")
st.sidebar.subheader("Navegação")

# Funções de navegação
def reset_submenu():
    st.session_state.emissao_submenu_expanded = False
    st.session_state.higienizacao_submenu_expanded = False
    st.session_state.adm_submenu_expanded = False

def ir_para_ficha_familia():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Ficha da Família'
    st.query_params['page'] = 'ficha_familia'
    if 'sub' in st.query_params:
        del st.query_params['sub']

def toggle_emissao_submenu():
    st.session_state.emissao_submenu_expanded = not st.session_state.get('emissao_submenu_expanded', False)
    st.session_state.higienizacao_submenu_expanded = False
    st.session_state.adm_submenu_expanded = False
    
    if st.session_state.emissao_submenu_expanded:
        st.session_state['pagina_atual'] = 'Emissões Brasileiras'
        st.query_params['page'] = 'cartorio_new'
        current_subpage = st.session_state.get('emissao_subpagina')
        if current_subpage not in SUB_ROTAS_EMISSOES.values():
            st.session_state.emissao_subpagina = 'Funil Certidões'
            st.query_params['sub'] = 'funil_certidoes'

def toggle_higienizacao_submenu():
    st.session_state.higienizacao_submenu_expanded = not st.session_state.get('higienizacao_submenu_expanded', False)
    st.session_state.emissao_submenu_expanded = False
    
    if st.session_state.higienizacao_submenu_expanded:
        st.session_state['pagina_atual'] = 'Higienizações'
        st.query_params['page'] = 'higienizacoes'
        if st.session_state.get('pagina_atual') != 'Higienizações':
            st.session_state.higienizacao_subpagina = 'Checklist'
            st.query_params['sub'] = 'checklist'

def ir_para_emissao_funil_certidoes():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Funil Certidões'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'funil_certidoes'

def ir_para_emissao_emissoes_por_familia():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Emissões Por Família'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'emissoes_por_familia'

def ir_para_higienizacao_checklist():
    st.session_state['pagina_atual'] = 'Higienizações'
    st.session_state.higienizacao_subpagina = 'Checklist'
    st.query_params['page'] = 'higienizacoes'
    st.query_params['sub'] = 'checklist'

# Botões de navegação
st.sidebar.button(
    "🏠 Ficha da Família", 
    key="btn_ficha_familia",
    on_click=ir_para_ficha_familia,
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Ficha da Família" else "secondary"
)

st.sidebar.button(
    "Higienizações", 
    key="btn_higienizacoes", 
    on_click=toggle_higienizacao_submenu, 
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Higienizações" else "secondary",
    help="Módulo unificado de Higienizações"
)

# Submenu Higienizações
if st.session_state.get('higienizacao_submenu_expanded', False):
    with st.sidebar.container():
        st.button(
            "Checklist", 
            key="subbtn_higienizacao_checklist",
            on_click=ir_para_higienizacao_checklist,
            use_container_width=True,
            type="primary" if st.session_state.get('higienizacao_subpagina') == "Checklist" else "secondary"
        )

st.sidebar.button(
    "Emissões Brasileiras", 
    key="btn_cartorio_new", 
    on_click=toggle_emissao_submenu, 
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Emissões Brasileiras" else "secondary",
    help="Módulo de emissões de cartórios brasileiros"
)

# Submenu Emissões Brasileiras
if st.session_state.get('emissao_submenu_expanded', False):
    with st.sidebar.container():
        st.button(
            "Funil Certidões", 
            key="subbtn_emissao_funil_certidoes",
            on_click=ir_para_emissao_funil_certidoes,
            use_container_width=True,
            type="primary" if st.session_state.get('emissao_subpagina') == "Funil Certidões" else "secondary"
        )
        st.button(
            "Emissões Por Família", 
            key="subbtn_emissao_emissoes_por_familia",
            on_click=ir_para_emissao_emissoes_por_familia,
            use_container_width=True,
            type="primary" if st.session_state.get('emissao_subpagina') == "Emissões Por Família" else "secondary"
        )

# Exibição da página selecionada
pagina = st.session_state.get('pagina_atual', 'Ficha da Família')

try:
    if pagina == "Ficha da Família":
        show_ficha_familia()
    elif pagina == "Higienizações":
        show_higienizacoes()
    elif pagina == "Emissões Brasileiras":
        show_cartorio_new()
    elif pagina == "Extrações de Dados":
        show_extracoes()
    else:
        st.error(f"Página '{pagina}' não encontrada!")
        
except Exception as e:
    st.error(f"Erro ao carregar a página: {str(e)}")
    st.error("Verifique se todos os arquivos necessários estão disponíveis.") 