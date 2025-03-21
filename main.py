import streamlit as st

# Configuração geral da página
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
from views.cartorio.cartorio_main import show_cartorio
from views.extracoes.extracoes_main import show_extracoes
# Importar nova página de apresentação de conclusões
from views.apresentacao import show_apresentacao

# Carregando CSS
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Adicionando CSS da fonte Montserrat
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Montserrat', sans-serif !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600;
}

p, span, div {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)

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
    
    /* Removida a regra que escondia as abas */
    /* div.stTabs {display: none;} */
    
    /* Melhorar o estilo dos botões de navegação */
    .menu-button {
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Variável de estado para controlar a navegação
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'Macro Higienização'

# Adicionar CSS especial para o modo de apresentação
if 'pagina_atual' in st.session_state and st.session_state['pagina_atual'] == 'Apresentação Conclusões':
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            width: 15rem !important;
        }
        
        /* Quando em modo apresentação automática, esconder completamente a barra lateral */
        body.sidebar-collapsed section[data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
        }
        
        /* Configuração específica para o modo apresentação */
        .modoapresentacao .stApp {
            background-color: #f8f9fa !important;
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
</style>
""", unsafe_allow_html=True)

# Adicionar logo no sidebar centralizado
st.sidebar.image("assets/LOGO-EU.NA.EUROPA-MAIO.24-COLORIDO-VERTICAL.svg", width=250)

# Menu de navegação simplificado
st.sidebar.title("Dashboard CRM Bitrix24")
st.sidebar.markdown("---")

# Criar uma seção para os botões de navegação
st.sidebar.markdown("### Navegação")

# Funções simples para alterar a página
def ir_para_inicio(): st.session_state['pagina_atual'] = 'Macro Higienização'
def ir_para_producao(): st.session_state['pagina_atual'] = 'Produção Higienização'
def ir_para_conclusoes(): st.session_state['pagina_atual'] = 'Conclusões Higienização'
def ir_para_cartorio(): st.session_state['pagina_atual'] = 'Cartório'
def ir_para_extracoes(): st.session_state['pagina_atual'] = 'Extrações de Dados'
def ir_para_apresentacao(): st.session_state['pagina_atual'] = 'Apresentação Conclusões'

# Botões individuais para navegação
st.sidebar.button("Macro Higienização", key="btn_inicio", 
            on_click=ir_para_inicio,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Macro Higienização" else "secondary")

st.sidebar.button("Produção Higienização", key="btn_producao", 
            on_click=ir_para_producao,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Produção Higienização" else "secondary")

st.sidebar.button("Conclusões Higienização", key="btn_conclusoes", 
            on_click=ir_para_conclusoes,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Conclusões Higienização" else "secondary")

st.sidebar.button("Funil Emissões Bitrix", key="btn_cartorio", 
            on_click=ir_para_cartorio,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Cartório" else "secondary")

st.sidebar.button("Extrações", key="btn_extracoes", 
            on_click=ir_para_extracoes,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Extrações de Dados" else "secondary")

# Adicionar separador para seção de apresentação
st.sidebar.markdown("---")
st.sidebar.markdown("### Modo Apresentação")

# Botão destacado para o modo de apresentação
st.sidebar.button("📊 Apresentação em TV (9:16)", key="btn_apresentacao", 
            on_click=ir_para_apresentacao,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Apresentação Conclusões" else "secondary")

# Exibição da página selecionada com base na variável de sessão
pagina = st.session_state['pagina_atual']

try:
    if pagina == "Macro Higienização":
        show_inicio()
    elif pagina == "Produção Higienização":
        show_producao()
    elif pagina == "Conclusões Higienização":
        show_conclusoes()
    elif pagina == "Cartório":
        show_cartorio()
    elif pagina == "Extrações de Dados":
        show_extracoes()
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
except Exception as e:
    st.error(f"Erro ao carregar a página: {str(e)}")
    # Mostrar detalhes do erro para facilitar a depuração
    st.exception(e)

# Rodapé do sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("Dashboard desenvolvido para análise de dados do CRM Bitrix24") 
