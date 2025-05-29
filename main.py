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
import views.comune.comune_main
import views.comune.producao_comune
import views.comune.funil_certidoes_italianas
import views.comune.status_certidao

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
    "comune": "Comune",
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

# Mapeamento de sub-rotas para Comune
SUB_ROTAS_COMUNE = {
    "producao_comune": "Produção Comune",
    "funil_certidoes_italianas": "Funil Certidões Italianas",
    "status_certidao": "Status Certidão"
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

    # Novos estados para o submenu Comune
    if 'comune_submenu_expanded' not in st.session_state:
        st.session_state.comune_submenu_expanded = False
    if 'comune_subpagina' not in st.session_state:
        st.session_state.comune_subpagina = 'Produção Comune'

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
            elif rota == 'comune':
                st.session_state.comune_submenu_expanded = True
                if 'sub' in st.query_params and st.query_params['sub'] in SUB_ROTAS_COMUNE:
                    st.session_state.comune_subpagina = SUB_ROTAS_COMUNE[st.query_params['sub']]
                else:
                    st.session_state.comune_subpagina = "Produção Comune"
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

/* CSS específico para submenu ADM - caixa azul destacada */
.adm-submenu-container {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(37, 99, 235, 0.04)) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 8px !important;
    padding: 8px 12px 8px 12px !important;
    margin: 6px 0 6px 20px !important;
    box-shadow: 0 1px 3px rgba(59, 130, 246, 0.1) !important;
}

.adm-submenu-title {
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.75rem !important;
    margin-bottom: 6px !important;
    padding-bottom: 4px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-bottom: 1px solid rgba(59, 130, 246, 0.15) !important;
}

/* CSS para criar container visual dos botões ADM */
[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_adm_producao"] {
    position: relative !important;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(37, 99, 235, 0.04)) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 8px 12px 4px 12px !important;
    margin: 6px 0 0 20px !important;
    box-shadow: 0 1px 3px rgba(59, 130, 246, 0.1) !important;
}

[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_adm_producao"]::before {
    content: "ADM" !important;
    display: block !important;
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.75rem !important;
    margin-bottom: 6px !important;
    padding-bottom: 4px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-bottom: 1px solid rgba(59, 130, 246, 0.15) !important;
}

[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_adm_pendencias"] {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(37, 99, 235, 0.04)) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
    padding: 4px 12px 8px 12px !important;
    margin: 0 0 6px 20px !important;
    box-shadow: 0 1px 3px rgba(59, 130, 246, 0.1) !important;
}

/* CSS para botões dentro do container ADM */
[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_adm_"] [data-testid="stButton"] {
    margin: 2px 0 !important;
}

[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_adm_"] [data-testid="stButton"] button:not([data-testid="stIconButton"]) {
    background: rgba(248, 250, 252, 0.9) !important;
    border: 1px solid rgba(59, 130, 246, 0.15) !important;
    border-radius: 6px !important;
    padding: 6px 12px !important;
    font-size: 0.875rem !important;
    color: #4B5563 !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_adm_"] [data-testid="stButton"] button:not([data-testid="stIconButton"]):hover {
    background: rgba(59, 130, 246, 0.08) !important;
    border-color: rgba(59, 130, 246, 0.25) !important;
    color: #1F2937 !important;
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1) !important;
}

[data-testid="stSidebar"] .stElementContainer[class*="st-key-subbtn_adm_"] [data-testid="stButton"] button[kind="primary"]:not([data-testid="stIconButton"]) {
    background: rgba(59, 130, 246, 0.12) !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
    color: #1E40AF !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.15) !important;
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
    st.session_state.comune_submenu_expanded = False

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

def ir_para_emissao_certidoes_pendentes():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Certidões Pendentes por responsável'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'certidoes_pendentes_responsavel'

def ir_para_emissao_desempenho_conclusao():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Desempenho Conclusão de Pasta'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'desempenho_conclusao_pasta'

def ir_para_emissao_adm():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'ADM'
    st.session_state.adm_submenu_expanded = True
    st.session_state.adm_subpagina = 'Produção ADM'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'adm'

def ir_para_emissao_producao_time_doutora():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Produção Time Doutora'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'producao_time_doutora'

def ir_para_emissao_pesquisa_br():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Pesquisa BR'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'pesquisa_br'

def ir_para_higienizacao_checklist():
    st.session_state['pagina_atual'] = 'Higienizações'
    st.session_state.higienizacao_subpagina = 'Checklist'
    st.query_params['page'] = 'higienizacoes'
    st.query_params['sub'] = 'checklist'

def ir_para_adm_producao():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'ADM'
    st.session_state.adm_submenu_expanded = True
    st.session_state.adm_subpagina = 'Produção ADM'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'adm'

def ir_para_adm_pendencias():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'ADM'
    st.session_state.adm_submenu_expanded = True
    st.session_state.adm_subpagina = 'Certidões Pendentes por ADM'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'adm'

# Nova função para toggle do submenu Comune
def toggle_comune_submenu():
    st.session_state.comune_submenu_expanded = not st.session_state.get('comune_submenu_expanded', False)
    st.session_state.emissao_submenu_expanded = False
    st.session_state.higienizacao_submenu_expanded = False
    st.session_state.adm_submenu_expanded = False
    
    if st.session_state.comune_submenu_expanded:
        st.session_state['pagina_atual'] = 'Comune'
        st.query_params['page'] = 'comune'
        current_subpage = st.session_state.get('comune_subpagina')
        if current_subpage not in SUB_ROTAS_COMUNE.values():
            st.session_state.comune_subpagina = 'Produção Comune'
            st.query_params['sub'] = 'producao_comune'

# Nova função para navegação da sub-aba Produção Comune
def ir_para_comune_producao():
    st.session_state['pagina_atual'] = 'Comune'
    st.session_state.comune_subpagina = 'Produção Comune'
    st.query_params['page'] = 'comune'
    st.query_params['sub'] = 'producao_comune'

# Nova função para navegação da sub-aba Funil Certidões Italianas
def ir_para_comune_funil_certidoes():
    st.session_state['pagina_atual'] = 'Comune'
    st.session_state.comune_subpagina = 'Funil Certidões Italianas'
    st.query_params['page'] = 'comune'
    st.query_params['sub'] = 'funil_certidoes_italianas'

# Nova função para navegação da sub-aba Status Certidão
def ir_para_comune_status_certidao():
    """Navega para a página de Status de Certidão"""
    st.session_state.pagina_atual = 'Comune'
    st.session_state.comune_submenu_expanded = True
    st.session_state.comune_subpagina = 'Status Certidão'
    st.query_params['page'] = 'comune'
    st.query_params['sub'] = 'status_certidao'

# Botões de navegação
st.sidebar.button(
    "Ficha da Família", 
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

# Submenu Emissões Brasileiras (deve aparecer IMEDIATAMENTE após o botão)
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
        st.button(
            "Certidões Pendentes por responsável", 
            key="subbtn_emissao_certidoes_pendentes",
            on_click=ir_para_emissao_certidoes_pendentes,
            use_container_width=True,
            type="primary" if st.session_state.get('emissao_subpagina') == "Certidões Pendentes por responsável" else "secondary"
        )
        st.button(
            "Desempenho Conclusão de Pasta", 
            key="subbtn_emissao_desempenho_conclusao",
            on_click=ir_para_emissao_desempenho_conclusao,
            use_container_width=True,
            type="primary" if st.session_state.get('emissao_subpagina') == "Desempenho Conclusão de Pasta" else "secondary"
        )
        st.button(
            "ADM", 
            key="subbtn_emissao_adm",
            on_click=ir_para_emissao_adm,
            use_container_width=True,
            type="primary" if st.session_state.get('emissao_subpagina') == "ADM" else "secondary"
        )
        
        # Submenu ADM aparece imediatamente após o botão ADM
        if (st.session_state.get('emissao_subpagina') == "ADM" and 
            st.session_state.get('adm_submenu_expanded', False)):
            
            # Botões ADM com estilo visual unificado via CSS
            st.button(
                "Produção ADM", 
                key="subbtn_adm_producao",
                on_click=ir_para_adm_producao,
                use_container_width=True,
                type="primary" if st.session_state.get('adm_subpagina') == "Produção ADM" else "secondary"
            )
            st.button(
                "Certidões Pendentes por ADM", 
                key="subbtn_adm_pendencias",
                on_click=ir_para_adm_pendencias,
                use_container_width=True,
                type="primary" if st.session_state.get('adm_subpagina') == "Certidões Pendentes por ADM" else "secondary"
            )
        
        st.button(
            "Produção Time Doutora", 
            key="subbtn_emissao_producao_time_doutora",
            on_click=ir_para_emissao_producao_time_doutora,
            use_container_width=True,
            type="primary" if st.session_state.get('emissao_subpagina') == "Produção Time Doutora" else "secondary"
        )
        st.button(
            "Pesquisa BR", 
            key="subbtn_emissao_pesquisa_br",
            on_click=ir_para_emissao_pesquisa_br,
            use_container_width=True,
            type="primary" if st.session_state.get('emissao_subpagina') == "Pesquisa BR" else "secondary"
        )

# Novo botão para a aba Comune (DEPOIS do submenu de Emissões Brasileiras)
st.sidebar.button(
    "Comune",
    key="btn_comune",
    on_click=toggle_comune_submenu,
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Comune" else "secondary",
    help="Dashboard de Métricas do Comune via Planilha Google"
)

# Novo submenu para Comune (IMEDIATAMENTE após o botão Comune)
if st.session_state.get('comune_submenu_expanded', False):
    with st.sidebar.container():
        st.button(
            "Produção Comune",
            key="subbtn_comune_producao",
            on_click=ir_para_comune_producao,
            use_container_width=True,
            type="primary" if st.session_state.get('comune_subpagina') == "Produção Comune" else "secondary"
        )
        st.button(
            "Funil Certidões Italianas",
            key="subbtn_comune_funil_certidoes",
            on_click=ir_para_comune_funil_certidoes,
            use_container_width=True,
            type="primary" if st.session_state.get('comune_subpagina') == "Funil Certidões Italianas" else "secondary"
        )
        st.button(
            "Status Certidão",
            key="subbtn_comune_status_certidao",
            on_click=ir_para_comune_status_certidao,
            use_container_width=True,
            type="primary" if st.session_state.get('comune_subpagina') == "Status Certidão" else "secondary"
        )

st.sidebar.button(
    "Extrações de Dados", 
    key="btn_extracoes", 
    on_click=lambda: setattr(st.session_state, 'pagina_atual', 'Extrações de Dados') or st.query_params.update({'page': 'extracoes'}),
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Extrações de Dados" else "secondary",
    help="Módulo de extrações e relatórios"
)

# Exibição da página selecionada
current_page = st.session_state.get('pagina_atual', 'Ficha da Família')

try:
    if current_page == "Ficha da Família":
        show_ficha_familia()
    elif current_page == "Higienizações":
        if st.session_state.get('higienizacao_subpagina') == "Checklist":
            show_higienizacoes(sub_page="checklist")
        else:
            show_higienizacoes()
    elif current_page == "Emissões Brasileiras":
        show_cartorio_new()  # Remover os parâmetros que a função não aceita
    elif current_page == "Comune":
        if st.session_state.get('comune_subpagina') == "Produção Comune":
            views.comune.producao_comune.show_producao_comune()
        elif st.session_state.get('comune_subpagina') == "Funil Certidões Italianas":
            views.comune.funil_certidoes_italianas.show_funil_certidoes_italianas()
        elif st.session_state.get('comune_subpagina') == "Status Certidão":
            views.comune.status_certidao.show_status_certidao()
        else:
            views.comune.comune_main.show_comune_main()
    elif current_page == "Extrações de Dados":
        show_extracoes()
    else:
        st.error(f"Página '{current_page}' não encontrada!")
        
except Exception as e:
    st.error(f"Erro ao carregar a página: {str(e)}")
    st.error("Verifique se todos os arquivos necessários estão disponíveis.") 