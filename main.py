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

# Função para verificar se o streamlit está em modo execução
def is_streamlit_running():
    """Verifica se o Streamlit está rodando adequadamente para usar session_state"""
    try:
        # Testa se o session_state está disponível
        test = st.session_state
        return True
    except:
        return False

# Só faz imports condicionais e configurações se o Streamlit estiver rodando
if is_streamlit_running():
    # Importações das páginas - usando a pasta views
    from views.inicio import show_inicio
    from views.extracoes.extracoes_main import show_extracoes
    from views.cartorio_new.cartorio_new_main import show_cartorio_new
    from views.ficha_familia import show_ficha_familia
    from views.higienizacoes.higienizacoes_main import show_higienizacoes

    # Importar os novos componentes
    from components.report_guide import show_guide_sidebar
    from components.search_component import show_search_box
    from components.table_of_contents import render_toc
    from components.refresh_button import render_sidebar_refresh_button

    # CSS personalizado
    with open("assets/styles/css/main.css", "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    # Função para inicializar estados da sessão
    def inicializar_estados_sessao():
        """Inicializa todos os estados da sessão necessários para a aplicação"""
        # Estados básicos de navegação
        if 'pagina_atual' not in st.session_state:
            st.session_state['pagina_atual'] = 'Ficha da Família'
        
        if 'sub_pagina_atual' not in st.session_state:
            st.session_state['sub_pagina_atual'] = None
            
        if 'mostrar_guia' not in st.session_state:
            st.session_state['mostrar_guia'] = False
            
        if 'mostrar_busca' not in st.session_state:
            st.session_state['mostrar_busca'] = False
            
        # Estados de dados
        if 'dados_carregados' not in st.session_state:
            st.session_state['dados_carregados'] = False
            
        if 'force_reload' not in st.session_state:
            st.session_state['force_reload'] = False

    # Inicializar estados da sessão
    inicializar_estados_sessao()

    # Funções auxiliares de navegação
    def reset_submenu():
        """Reseta o submenu atual"""
        st.session_state['sub_pagina_atual'] = None

    def ir_para_ficha_familia():
        reset_submenu()
        st.session_state['pagina_atual'] = 'Ficha da Família'
        st.query_params['page'] = 'ficha_familia'
        if 'sub' in st.query_params:
            del st.query_params['sub']

    def ir_para_higienizacoes():
        reset_submenu()
        st.session_state['pagina_atual'] = 'Higienizações'
        st.query_params['page'] = 'higienizacoes'
        if 'sub' in st.query_params:
            del st.query_params['sub']

    def ir_para_cartorio():
        reset_submenu()
        st.session_state['pagina_atual'] = 'Cartório'
        st.query_params['page'] = 'cartorio'
        if 'sub' in st.query_params:
            del st.query_params['sub']

    def ir_para_extracoes():
        reset_submenu()
        st.session_state['pagina_atual'] = 'Extrações'
        st.query_params['page'] = 'extracoes'
        if 'sub' in st.query_params:
            del st.query_params['sub']

    # Interface principal
    with st.sidebar:
        # Logo e título principal
        st.image("assets/LOGO-EU.NA.EUROPA-MAIO.24-COLORIDO-VERTICAL.svg", width=200)
        st.markdown("---")
        
        # Navegação principal
        st.subheader("📊 Dashboard Principal")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 Ficha da Família", use_container_width=True):
                ir_para_ficha_familia()
                st.rerun()
                
        with col2:
            if st.button("🧹 Higienizações", use_container_width=True):
                ir_para_higienizacoes()
                st.rerun()
                
        col3, col4 = st.columns(2)
        with col3:
            if st.button("📋 Cartório", use_container_width=True):
                ir_para_cartorio()
                st.rerun()
                
        with col4:
            if st.button("📊 Extrações", use_container_width=True):
                ir_para_extracoes()
                st.rerun()

        st.markdown("---")
        
        # Componentes auxiliares
        show_guide_sidebar()
        show_search_box()
        render_sidebar_refresh_button()

    # Renderização da página principal
    pagina_atual = st.session_state.get('pagina_atual', 'Ficha da Família')
    
    if pagina_atual == 'Ficha da Família':
        show_ficha_familia()
    elif pagina_atual == 'Higienizações':
        show_higienizacoes()
    elif pagina_atual == 'Cartório':
        show_cartorio_new()
    elif pagina_atual == 'Extrações':
        show_extracoes()
    else:
        st.error(f"Página '{pagina_atual}' não encontrada")

else:
    # Modo de desenvolvimento/import - só mostra informações básicas
    st.title("Dashboard CRM Bitrix24")
    st.info("⚠️ Aplicação em modo de desenvolvimento. Execute com `streamlit run main.py` para funcionalidade completa.") 