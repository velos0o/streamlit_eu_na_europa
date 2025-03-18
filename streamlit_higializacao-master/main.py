import streamlit as st

# Configuração geral da página
st.set_page_config(
    page_title="Dashboard CRM Bitrix24",
    page_icon="logo..svg",
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
from views.producao import show_producao
from views.conclusoes import show_conclusoes
from views.cartorio.cartorio_main import show_cartorio
from views.extracoes.extracoes_main import show_extracoes

# Carregando CSS
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Removendo todos os elementos padrão do Streamlit
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    .css-ch5dnh {display: none;}
    .css-1adrfps {padding-top: 1rem;}
    .block-container {padding-top: 1rem;}
    section[data-testid="stSidebar"] div.block-container {padding-top: 2rem;}
    [data-testid="collapsedControl"] {display: none;}
    div[data-testid="stToolbar"] {display: none !important;}
    
    /* Estilo específico para limpar qualquer navegação extra */
    .main .block-container {padding-top: 20px !important;}
    
    /* Esconder todos os outros widgets não utilizados */
    div.stTabs {display: none;}
    
    /* Melhorar o estilo dos botões de navegação */
    .menu-button {
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Variável de estado para controlar a navegação
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'Início'

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
</style>
""", unsafe_allow_html=True)

# Adicionar logo no sidebar centralizado
st.sidebar.image("logo..svg", width=180)

# Menu de navegação simplificado
st.sidebar.title("Dashboard CRM Bitrix24")
st.sidebar.markdown("---")

# Criar uma seção para os botões de navegação
st.sidebar.markdown("### Navegação")

# Funções simples para alterar a página
def ir_para_inicio(): st.session_state['pagina_atual'] = 'Início'
def ir_para_producao(): st.session_state['pagina_atual'] = 'Produção'
def ir_para_conclusoes(): st.session_state['pagina_atual'] = 'Conclusões'
def ir_para_cartorio(): st.session_state['pagina_atual'] = 'Cartório'
def ir_para_extracoes(): st.session_state['pagina_atual'] = 'Extrações de Dados'

# Botões individuais para navegação
st.sidebar.button("Início", key="btn_inicio", 
            on_click=ir_para_inicio,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Início" else "secondary")

st.sidebar.button("Produção", key="btn_producao", 
            on_click=ir_para_producao,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Produção" else "secondary")

st.sidebar.button("Conclusões", key="btn_conclusoes", 
            on_click=ir_para_conclusoes,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Conclusões" else "secondary")

st.sidebar.button("Cartório", key="btn_cartorio", 
            on_click=ir_para_cartorio,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Cartório" else "secondary")

st.sidebar.button("Extrações", key="btn_extracoes", 
            on_click=ir_para_extracoes,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Extrações de Dados" else "secondary")

# Exibição da página selecionada com base na variável de sessão
pagina = st.session_state['pagina_atual']

try:
    if pagina == "Início":
        show_inicio()
    elif pagina == "Produção Higienização":
        show_producao()
    elif pagina == "Conclusões Higienização":
        show_conclusoes()
    elif pagina == "Emissões Brasileiras":
        show_cartorio()
    elif pagina == "Extrações de Dados Bitrix24":
        show_extracoes()
except Exception as e:
    st.error(f"Erro ao carregar a página: {str(e)}")
    # Mostrar detalhes do erro para facilitar a depuração
    st.exception(e)

# Rodapé do sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("Dashboard desenvolvido para análise de dados do CRM Bitrix24") 
