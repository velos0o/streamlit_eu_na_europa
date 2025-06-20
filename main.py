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
from views.funil_cat54.funil_cat54_main import show_negociacao
from views.protocolado.protocolado_main import show_protocolados
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
    "funil_cat54": "Negociação",
    "protocolados": "Protocolados",
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

# Mapeamento de sub-rotas para Protocolados
SUB_ROTAS_PROTOCOLADOS = {
    "dados_macros": "Dados Macros",
    "funil_etapas": "Funil - Etapas",
    "pendencias_liberadas": "Pendências Liberadas",
    "pendencias_futuras": "Pendências Futuras",
    "produtividade": "Produtividade"
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

    # Novos estados para o submenu Protocolados
    if 'protocolado_submenu_expanded' not in st.session_state:
        st.session_state.protocolado_submenu_expanded = False
    if 'protocolado_subpagina' not in st.session_state:
        st.session_state.protocolado_subpagina = 'Dados Macros'

# Processar parâmetros da URL
def processar_parametros_url():
    """Processa parâmetros da URL para navegação direta"""
    query_params = st.query_params
    if 'pagina_atual_via_url_processada' not in st.session_state and 'page' in query_params:
        rota = query_params['page'].lower()
        if rota in ROTAS:
            st.session_state['pagina_atual'] = ROTAS[rota]
            st.session_state['pagina_atual_via_url_processada'] = True

            if rota == 'cartorio_new':
                st.session_state.emissao_submenu_expanded = True
                if 'sub' in query_params and query_params['sub'] in SUB_ROTAS_EMISSOES:
                    st.session_state.emissao_subpagina = SUB_ROTAS_EMISSOES[query_params['sub']]
                else:
                    st.session_state.emissao_subpagina = "Funil Certidões"
            elif rota == 'higienizacoes':
                st.session_state.higienizacao_submenu_expanded = True
                if 'sub' in query_params and query_params['sub'] in SUB_ROTAS_HIGIENIZACOES:
                    st.session_state.higienizacao_subpagina = SUB_ROTAS_HIGIENIZACOES[query_params['sub']]
                else:
                    st.session_state.higienizacao_subpagina = "Checklist"
            elif rota == 'comune':
                st.session_state.comune_submenu_expanded = True
                if 'sub' in query_params and query_params['sub'] in SUB_ROTAS_COMUNE:
                    st.session_state.comune_subpagina = SUB_ROTAS_COMUNE[query_params['sub']]
                else:
                    st.session_state.comune_subpagina = "Produção Comune"
            elif rota == 'protocolados':
                st.session_state.protocolado_submenu_expanded = True
                if 'sub' in query_params and query_params['sub'] in SUB_ROTAS_PROTOCOLADOS:
                    st.session_state.protocolado_subpagina = SUB_ROTAS_PROTOCOLADOS[query_params['sub']]
                else:
                    st.session_state.protocolado_subpagina = "Dados Macros"
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


# Funções de navegação e controle de estado
def reset_submenu():
    """Reseta os estados dos submenus"""
    st.session_state.emissao_submenu_expanded = False
    st.session_state.higienizacao_submenu_expanded = False
    st.session_state.comune_submenu_expanded = False
    st.session_state.protocolado_submenu_expanded = False

def ir_para_ficha_familia():
    """Navega para a Ficha da Família e reseta submenus."""
    st.session_state['pagina_atual'] = 'Ficha da Família'
    reset_submenu()
    st.query_params['page'] = 'ficha_familia'

def toggle_emissao_submenu():
    st.session_state.emissao_submenu_expanded = not st.session_state.get('emissao_submenu_expanded', False)
    if st.session_state.emissao_submenu_expanded:
        st.session_state['pagina_atual'] = 'Emissões Brasileiras'
        # Atualiza a URL para refletir a navegação
        sub_rota = next((key for key, value in SUB_ROTAS_EMISSOES.items() if value == st.session_state.emissao_subpagina), 'funil_certidoes')
        st.query_params = {'page': 'cartorio_new', 'sub': sub_rota}

def toggle_higienizacao_submenu():
    st.session_state.higienizacao_submenu_expanded = not st.session_state.get('higienizacao_submenu_expanded', False)
    if st.session_state.higienizacao_submenu_expanded:
        st.session_state['pagina_atual'] = 'Higienizações'
        sub_rota = next((key for key, value in SUB_ROTAS_HIGIENIZACOES.items() if value == st.session_state.higienizacao_subpagina), 'checklist')
        st.query_params = {'page': 'higienizacoes', 'sub': sub_rota}


# --- Funções de Navegação para Sub-páginas ---
def ir_para_emissao_funil_certidoes():
    st.session_state.emissao_subpagina = 'Funil Certidões'
    st.query_params['sub'] = 'funil_certidoes'
    
def ir_para_emissao_emissoes_por_familia():
    st.session_state.emissao_subpagina = 'Emissões Por Família'
    st.query_params['sub'] = 'emissoes_por_familia'

def ir_para_emissao_certidoes_pendentes():
    st.session_state.emissao_subpagina = 'Certidões Pendentes por responsável'
    st.query_params['sub'] = 'certidoes_pendentes_responsavel'

def ir_para_emissao_desempenho_conclusao():
    st.session_state.emissao_subpagina = 'Desempenho Conclusão de Pasta'
    st.query_params['sub'] = 'desempenho_conclusao_pasta'
    
def ir_para_emissao_adm():
    st.session_state.adm_submenu_expanded = not st.session_state.get('adm_submenu_expanded', False)

def ir_para_emissao_producao_time_doutora():
    st.session_state.emissao_subpagina = 'Produção Time Doutora'
    st.query_params['sub'] = 'producao_time_doutora'
    
def ir_para_emissao_pesquisa_br():
    st.session_state.emissao_subpagina = 'Pesquisa BR'
    st.query_params['sub'] = 'pesquisa_br'

def ir_para_higienizacao_checklist():
    st.session_state.higienizacao_subpagina = 'Checklist'
    st.query_params['sub'] = 'checklist'

def ir_para_adm_producao():
    st.session_state.adm_subpagina = 'Produção ADM'
    st.query_params['sub'] = 'producao_adm'

def ir_para_adm_pendencias():
    st.session_state.adm_subpagina = 'Certidões Pendentes por ADM'
    st.query_params['sub'] = 'certidoes_pendentes_adm'

def ir_para_negociacao():
    """Navega para a página de Negociação."""
    st.session_state['pagina_atual'] = 'Negociação'
    st.query_params['page'] = 'funil_cat54' # Mantém a rota para a nova estrutura
    reset_submenu()

def ir_para_protocolados():
    """Navega para a página de Protocolados."""
    st.session_state['pagina_atual'] = 'Protocolados'
    st.session_state.protocolado_submenu_expanded = True
    sub_rota = next((key for key, value in SUB_ROTAS_PROTOCOLADOS.items() if value == st.session_state.protocolado_subpagina), 'dados_macros')
    st.query_params = {'page': 'protocolados', 'sub': sub_rota}

def toggle_comune_submenu():
    st.session_state.comune_submenu_expanded = not st.session_state.get('comune_submenu_expanded', False)
    if st.session_state.comune_submenu_expanded:
        st.session_state['pagina_atual'] = 'Comune'
        sub_rota = next((key for key, value in SUB_ROTAS_COMUNE.items() if value == st.session_state.comune_subpagina), 'producao_comune')
        st.query_params = {'page': 'comune', 'sub': sub_rota}
        
def ir_para_comune_producao():
    st.session_state.comune_subpagina = 'Produção Comune'
    st.query_params['sub'] = 'producao_comune'

def ir_para_comune_funil_certidoes():
    st.session_state.comune_subpagina = 'Funil Certidões Italianas'
    st.query_params['sub'] = 'funil_certidoes_italianas'
    
def ir_para_comune_status_certidao():
    st.session_state.comune_subpagina = 'Status Certidão'
    st.query_params['sub'] = 'status_certidao'

def toggle_protocolado_submenu():
    st.session_state.protocolado_submenu_expanded = not st.session_state.get('protocolado_submenu_expanded', False)

def ir_para_protocolado_subpagina(sub_pagina_nome):
    def navigate():
        st.session_state.protocolado_subpagina = sub_pagina_nome
        st.query_params['sub'] = next(key for key, value in SUB_ROTAS_PROTOCOLADOS.items() if value == sub_pagina_nome)
    return navigate

def ir_para_extracoes():
    """Navega para a página de Extrações de Dados."""
    st.session_state['pagina_atual'] = 'Extrações de Dados'
    reset_submenu()
    st.query_params['page'] = 'extracoes'


def main():
    """Função principal que organiza o layout e a navegação."""
    
    with st.sidebar:
        st.image("assets/LOGO-EU.NA.EUROPA-MAIO.24-COLORIDO-VERTICAL.svg", use_column_width=True)
        st.markdown("---")
        
        # --- Botões de Navegação ---
        botoes_principais = {
            "Ficha da Família": ir_para_ficha_familia,
            "Emissões Brasileiras": toggle_emissao_submenu,
            "Higienizações": toggle_higienizacao_submenu,
            "Comune": toggle_comune_submenu,
            "Negociação": ir_para_negociacao,
            "Protocolados": ir_para_protocolados,
            "Extrações de Dados": ir_para_extracoes
        }

        for nome, acao in botoes_principais.items():
            is_active = st.session_state.pagina_atual == nome
            st.button(nome, on_click=acao, use_container_width=True, type="primary" if is_active else "secondary")

            # Lógica para exibir submenus
            if nome == "Emissões Brasileiras" and st.session_state.get('emissao_submenu_expanded'):
                def sub_button(label, key, on_click):
                    st.button(label, key=f"subbtn_emissao_{key}", on_click=on_click, use_container_width=True,
                              type="primary" if st.session_state.emissao_subpagina == label else "secondary")

                sub_button("Funil Certidões", "funil", ir_para_emissao_funil_certidoes)
                sub_button("Emissões Por Família", "familia", ir_para_emissao_emissoes_por_familia)
                sub_button("Certidões Pendentes por responsável", "pendentes", ir_para_emissao_certidoes_pendentes)
                sub_button("Desempenho Conclusão de Pasta", "desempenho", ir_para_emissao_desempenho_conclusao)
                sub_button("Produção Time Doutora", "doutora", ir_para_emissao_producao_time_doutora)
                sub_button("Pesquisa BR", "pesquisa", ir_para_emissao_pesquisa_br)
                st.button("ADM", on_click=ir_para_emissao_adm, use_container_width=True,
                          type="primary" if st.session_state.get('adm_submenu_expanded') else "secondary")
                if st.session_state.get('adm_submenu_expanded'):
                    st.button("Produção ADM", key="subbtn_adm_prod", on_click=ir_para_adm_producao, use_container_width=True,
                              type="primary" if st.session_state.adm_subpagina == "Produção ADM" else "secondary")
                    st.button("Certidões Pendentes por ADM", key="subbtn_adm_pend", on_click=ir_para_adm_pendencias, use_container_width=True,
                              type="primary" if st.session_state.adm_subpagina == "Certidões Pendentes por ADM" else "secondary")

            elif nome == "Higienizações" and st.session_state.get('higienizacao_submenu_expanded'):
                st.button("Checklist", key="subbtn_hig_check", on_click=ir_para_higienizacao_checklist, use_container_width=True,
                          type="primary" if st.session_state.higienizacao_subpagina == 'Checklist' else "secondary")
            
            elif nome == "Comune" and st.session_state.get('comune_submenu_expanded'):
                st.button("Produção Comune", key="subbtn_comune_prod", on_click=ir_para_comune_producao, use_container_width=True,
                          type="primary" if st.session_state.comune_subpagina == 'Produção Comune' else "secondary")
                st.button("Funil Certidões Italianas", key="subbtn_comune_funil", on_click=ir_para_comune_funil_certidoes, use_container_width=True,
                          type="primary" if st.session_state.comune_subpagina == 'Funil Certidões Italianas' else "secondary")
                st.button("Status Certidão", key="subbtn_comune_status", on_click=ir_para_comune_status_certidao, use_container_width=True,
                          type="primary" if st.session_state.comune_subpagina == 'Status Certidão' else "secondary")

            elif nome == "Protocolados" and st.session_state.get('protocolado_submenu_expanded'):
                for sub_nome in SUB_ROTAS_PROTOCOLADOS.values():
                    st.button(sub_nome, key=f"subbtn_prot_{sub_nome.replace(' ', '_')}", on_click=ir_para_protocolado_subpagina(sub_nome),
                              use_container_width=True, type="primary" if st.session_state.protocolado_subpagina == sub_nome else "secondary")

        st.markdown("---")
        show_guide_sidebar()
        render_sidebar_refresh_button()

    # --- Conteúdo Principal ---
    main_content = st.container()
    with main_content:
        current_page = st.session_state.get('pagina_atual', 'Ficha da Família')

        if current_page == 'Ficha da Família':
            show_ficha_familia()
        elif current_page == 'Higienizações':
            show_higienizacoes(st.session_state.get('higienizacao_subpagina'))
        elif current_page == 'Emissões Brasileiras':
            show_cartorio_new(st.session_state.get('emissao_subpagina'))
        elif current_page == 'Comune':
            views.comune.comune_main.show_comune()
        elif current_page == 'Negociação':
            show_negociacao()
        elif current_page == 'Protocolados':
            show_protocolados()
        elif current_page == 'Extrações de Dados':
            show_extracoes()
        else:
            show_ficha_familia() # Fallback

if __name__ == "__main__":
    main() 