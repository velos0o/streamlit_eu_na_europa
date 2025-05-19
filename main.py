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
from views.extracoes.extracoes_main import show_extracoes
# Importar nova página de apresentação de conclusões
# from views.apresentacao import show_apresentacao
# Importar nova página de COMUNE
# from views.comune.comune_main import show_comune
# Importar nova página de Tickets
# from views.tickets import show_tickets
# Importar nova página de Reclamações (caminho atualizado)
# from views.reclamacoes.reclamacoes_main import show_reclamacoes
# Importar nova página de Emissões Brasileiras
from views.cartorio_new.cartorio_new_main import show_cartorio_new
# --- NOVO: Importar Ficha da Família (anteriormente Página Inicial) ---
from views.ficha_familia import show_ficha_familia
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
    "ficha_familia": "Ficha da Família",
    "higienizacoes": "Higienizações",
    "cartorio_new": "Emissões Brasileiras",
    "extracoes": "Extrações de Dados"
}

# Mapeamento de sub-rotas para Emissões Brasileiras
SUB_ROTAS_EMISSOES = {
    "funil_certidoes": "Funil Certidões",
    "emissoes_por_familia": "Emissões Por Família",
    "certidoes_pendentes_responsavel": "Certidões Pendentes por responsável",
    "certidoes_pendentes_adm": "Certidões Pendentes Por ADM",
    "desempenho_conclusao_pasta": "Desempenho Conclusão de Pasta"
}

# Mapeamento de sub-rotas para Comune (Novo) - REMOVIDO
# SUB_ROTAS_COMUNE = {
#     "visao_geral": "Visão Geral",
#     "tempo_solicitacao": "Tempo de Solicitação",
#     "mapa_comune_1": "Mapa Comune 1",
#     "mapa_comune_2": "Mapa Comune 2",
#     "mapa_comune_3": "Mapa Comune 3"
# }

# Mapeamento de sub-rotas para Higienizações
SUB_ROTAS_HIGIENIZACOES = {
    # "producao": "Produção", # REMOVIDO
    # "conclusoes": "Conclusões", # REMOVIDO
    "checklist": "Checklist"
}

# Processar parâmetros da URL
def processar_parametros_url():
    # Processar a URL apenas se 'pagina_atual_via_url_processada' ainda não foi definida 
    # (ou seja, na primeira carga ou se o estado foi perdido)
    if 'pagina_atual_via_url_processada' not in st.session_state and 'page' in st.query_params:
        rota = st.query_params['page'].lower()
        if rota in ROTAS:
            st.session_state['pagina_atual'] = ROTAS[rota]
            st.session_state['pagina_atual_via_url_processada'] = True # Marcar que processamos

            # Lógica de subrotas como antes
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
        # Se a rota na URL não for válida, não faz nada, deixa o default do session_state
    elif 'pagina_atual_via_url_processada' not in st.session_state:
        st.session_state['pagina_atual_via_url_processada'] = True
                    
# Inicializar estado da sessão
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'Ficha da Família'
    if 'pagina_atual_via_url_processada' in st.session_state: # Adicionado para resetar o flag
        del st.session_state['pagina_atual_via_url_processada']
# --- Estado para submenu Emissões --- 
if 'emissao_submenu_expanded' not in st.session_state:
    st.session_state.emissao_submenu_expanded = False
if 'emissao_subpagina' not in st.session_state:
    st.session_state.emissao_subpagina = 'Funil Certidões' # Subpágina padrão ATUALIZADO
# --- Estado para submenu Comune (Novo) --- REMOVIDO
# if 'comune_submenu_expanded' not in st.session_state:
#     st.session_state.comune_submenu_expanded = False
# if 'comune_subpagina' not in st.session_state:
#     st.session_state.comune_subpagina = 'Visão Geral' # Subpágina padrão
# --- Estado para submenu Higienizações ---
if 'higienizacao_submenu_expanded' not in st.session_state:
    st.session_state.higienizacao_submenu_expanded = False
if 'higienizacao_subpagina' not in st.session_state:
    st.session_state.higienizacao_subpagina = 'Checklist' # Subpágina padrão ATUALIZADO para Checklist

# Processar os parâmetros da URL
processar_parametros_url()
# ----- FIM DA ADIÇÃO: PROCESSAMENTO DE URLs PERSONALIZADAS -----

# Carregando CSS ainda necessário
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# CSS simplificado para o botão de atualização
st.markdown("""
<style>
/* CSS para botão de atualização mais simples */
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

# Adicionar o guia de relatório na barra lateral
# show_guide_sidebar()

# Adicionar barra de pesquisa no topo do sidebar
show_search_box()
st.sidebar.markdown("---")

# Criar uma seção para os botões de navegação
st.sidebar.subheader("Navegação")

# Variáveis de estado para controlar a navegação
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'Ficha da Família'
# --- NOVO: Estado para submenu Emissões --- 
if 'emissao_submenu_expanded' not in st.session_state:
    st.session_state.emissao_submenu_expanded = False
if 'emissao_subpagina' not in st.session_state:
    st.session_state.emissao_subpagina = 'Funil Certidões' # Subpágina padrão ATUALIZADO

# --- NOVO: Funções de Navegação COM ATUALIZAÇÃO DE URL ---
def ir_para_ficha_familia():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Ficha da Família'
    st.query_params['page'] = 'ficha_familia'
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
        
def ir_para_extracoes(): 
    reset_submenu()
    st.session_state['pagina_atual'] = 'Extrações de Dados'
    st.query_params['page'] = 'extracoes'
    if 'sub' in st.query_params:
        del st.query_params['sub']
        
# Funções para alterar a página e controlar submenu
def reset_submenu():
    st.session_state.emissao_submenu_expanded = False
    # st.session_state.comune_submenu_expanded = False # Resetar submenu Comune também - REMOVIDO
    st.session_state.higienizacao_submenu_expanded = False # Resetar submenu Higienizações também

# --- NOVO: Função para toggle e navegação do submenu Emissões ---
def toggle_emissao_submenu():
    print(f"DEBUG: toggle_emissao_submenu chamada. Expandido antes: {st.session_state.get('emissao_submenu_expanded')}") # DEBUG
    st.session_state.emissao_submenu_expanded = not st.session_state.get('emissao_submenu_expanded', False)
    st.session_state.higienizacao_submenu_expanded = False # Fecha submenu Higienizações
    
    print(f"DEBUG: toggle_emissao_submenu - Expandido depois: {st.session_state.emissao_submenu_expanded}") # DEBUG
    if st.session_state.emissao_submenu_expanded:
        print(f"DEBUG: toggle_emissao_submenu - Página atual ANTES: {st.session_state.get('pagina_atual')}") # DEBUG
        st.session_state['pagina_atual'] = 'Emissões Brasileiras'
        print(f"DEBUG: toggle_emissao_submenu - Página atual DEPOIS: {st.session_state.get('pagina_atual')}") # DEBUG
        st.query_params['page'] = 'cartorio_new'
        current_subpage = st.session_state.get('emissao_subpagina')
        if current_subpage not in SUB_ROTAS_EMISSOES.values():
             st.session_state.emissao_subpagina = 'Funil Certidões'
             st.query_params['sub'] = 'funil_certidoes' 
        print(f"DEBUG: toggle_emissao_submenu - Subpágina definida para: {st.session_state.get('emissao_subpagina')}") # DEBUG

# --- NOVO: Funções on_click para sub-botões Emissões ---
def ir_para_emissao_funil_certidoes():
    print(f"DEBUG: ir_para_emissao_funil_certidoes chamada. Página atual ANTES: {st.session_state.get('pagina_atual')}") # DEBUG
    st.session_state['pagina_atual'] = 'Emissões Brasileiras' 
    print(f"DEBUG: ir_para_emissao_funil_certidoes - Página atual DEPOIS: {st.session_state.get('pagina_atual')}") # DEBUG
    st.session_state.emissao_subpagina = 'Funil Certidões'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'funil_certidoes'
    print(f"DEBUG: ir_para_emissao_funil_certidoes - Subpágina definida para: {st.session_state.get('emissao_subpagina')}") # DEBUG

def ir_para_emissao_emissoes_por_familia():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras' 
    st.session_state.emissao_subpagina = 'Emissões Por Família'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'emissoes_por_familia'

def ir_para_emissao_certidoes_pendentes_responsavel():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras' # Garante que a página principal está correta
    st.session_state.emissao_subpagina = 'Certidões Pendentes por responsável'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'certidoes_pendentes_responsavel'

# --- Função on_click para sub-botão Certidões Pendentes Por ADM ---
def ir_para_emissao_certidoes_pendentes_adm():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras'
    st.session_state.emissao_subpagina = 'Certidões Pendentes Por ADM'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'certidoes_pendentes_adm'

# --- Função on_click para sub-botão Desempenho Conclusão de Pasta ---
def ir_para_emissao_desempenho_conclusao_pasta():
    st.session_state['pagina_atual'] = 'Emissões Brasileiras' # Garante que a página principal está correta
    st.session_state.emissao_subpagina = 'Desempenho Conclusão de Pasta'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'desempenho_conclusao_pasta'

# --- NOVO: Função para toggle e navegação do submenu Comune (Novo) --- REMOVIDO
# def toggle_comune_submenu():
#     st.session_state.comune_submenu_expanded = not st.session_state.get('comune_submenu_expanded', False)
#     st.session_state.emissao_submenu_expanded = False # Fecha outro submenu
#     st.session_state.higienizacao_submenu_expanded = False # Fecha submenu Higienizações
#     # Define a página principal e subpágina padrão ao abrir/fechar
#     if st.session_state.comune_submenu_expanded:
#         st.session_state['pagina_atual'] = 'Comune (Novo)'
#         st.query_params['page'] = 'comune_new'
#         # Mantém a subpágina atual se já estiver em uma subpágina do Comune
#         if st.session_state.get('pagina_atual') != 'Comune (Novo)':
#             st.session_state.comune_subpagina = 'Visão Geral'
#             st.query_params['sub'] = 'visao_geral'
#     # Se fechar, mantém a URL atual

# --- NOVO: Função para toggle e navegação do submenu Higienizações ---
def toggle_higienizacao_submenu():
    st.session_state.higienizacao_submenu_expanded = not st.session_state.get('higienizacao_submenu_expanded', False)
    st.session_state.emissao_submenu_expanded = False # Fecha submenu Emissões
    # st.session_state.comune_submenu_expanded = False # Fecha submenu Comune - REMOVIDO
    # Define a página principal e subpágina padrão ao abrir/fechar
    if st.session_state.higienizacao_submenu_expanded:
        st.session_state['pagina_atual'] = 'Higienizações'
        st.query_params['page'] = 'higienizacoes'
        # Mantém a subpágina atual se já estiver em uma subpágina de Higienizações
        if st.session_state.get('pagina_atual') != 'Higienizações':
            st.session_state.higienizacao_subpagina = 'Checklist' # ATUALIZADO
            st.query_params['sub'] = 'checklist' # ATUALIZADO
    # Se fechar, mantém a URL atual

# --- NOVO: Funções on_click para sub-botões de Higienizações ---
def ir_para_higienizacao_checklist():
    st.session_state['pagina_atual'] = 'Higienizações'
    st.session_state.higienizacao_subpagina = 'Checklist'
    st.query_params['page'] = 'higienizacoes'
    st.query_params['sub'] = 'checklist'

# Funções on_click para sub-botões Comune (Novo) - REMOVIDO
# def ir_para_comune_visao_geral():
#     st.session_state['pagina_atual'] = 'Comune (Novo)'
#     st.session_state.comune_subpagina = 'Visão Geral'
#     st.query_params['page'] = 'comune_new'
#     st.query_params['sub'] = 'visao_geral'

# def ir_para_comune_tempo_solicitacao():
#     st.session_state['pagina_atual'] = 'Comune (Novo)'
#     st.session_state.comune_subpagina = 'Tempo de Solicitação'
#     st.query_params['page'] = 'comune_new'
#     st.query_params['sub'] = 'tempo_solicitacao'

# Funções on_click para sub-botões do MAPA (dentro de Comune Novo) - REMOVIDO
# def ir_para_mapa_comune_1():
#     st.session_state['pagina_atual'] = 'Comune (Novo)' # Permanece na página principal
#     st.session_state.comune_subpagina = 'Mapa Comune 1' # Define a subpágina para o mapa 1
#     st.query_params['page'] = 'comune_new'
#     st.query_params['sub'] = 'mapa_comune_1'

# def ir_para_mapa_comune_2():
#     st.session_state['pagina_atual'] = 'Comune (Novo)'
#     st.session_state.comune_subpagina = 'Mapa Comune 2'
#     st.query_params['page'] = 'comune_new'
#     st.query_params['sub'] = 'mapa_comune_2'

# def ir_para_mapa_comune_3():
#     st.session_state['pagina_atual'] = 'Comune (Novo)'
#     st.session_state.comune_subpagina = 'Mapa Comune 3'
#     st.query_params['page'] = 'comune_new'
#     st.query_params['sub'] = 'mapa_comune_3'

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
st.sidebar.button("🏠 Ficha da Família", key="btn_ficha_familia",
            on_click=ir_para_ficha_familia,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Ficha da Família" else "secondary")

# --- NOVO: Botão para Higienizações agora usa toggle_higienizacao_submenu ---
st.sidebar.button("Higienizações", key="btn_higienizacoes", 
            on_click=toggle_higienizacao_submenu, 
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Higienizações" else "secondary",
            help="Módulo unificado de Higienizações (Produção, Conclusões e Checklist)")

# --- NOVO: Bloco condicional para o submenu Higienizações ---
if st.session_state.get('higienizacao_submenu_expanded', False):
    with st.sidebar.container():
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
        st.button("Funil Certidões", key="subbtn_emissao_funil_certidoes",
                    on_click=ir_para_emissao_funil_certidoes,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Funil Certidões" else "secondary")
        st.button("Emissões Por Família", key="subbtn_emissao_emissoes_por_familia",
                    on_click=ir_para_emissao_emissoes_por_familia,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Emissões Por Família" else "secondary")
        st.button("Certidões Pendentes por responsável", key="subbtn_emissao_certidoes_pendentes_responsavel",
                    on_click=ir_para_emissao_certidoes_pendentes_responsavel,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Certidões Pendentes por responsável" else "secondary")
        st.button("Certidões Pendentes Por ADM", key="subbtn_emissao_certidoes_pendentes_adm",
                    on_click=ir_para_emissao_certidoes_pendentes_adm,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Certidões Pendentes Por ADM" else "secondary")
        st.button("Desempenho Conclusão de Pasta", key="subbtn_emissao_desempenho_conclusao_pasta",
                    on_click=ir_para_emissao_desempenho_conclusao_pasta,
                    use_container_width=True,
                    type="primary" if st.session_state.get('emissao_subpagina') == "Desempenho Conclusão de Pasta" else "secondary")

# st.sidebar.button("Extrações", key="btn_extracoes", 
#             on_click=ir_para_extracoes,
#             use_container_width=True,
#             type="primary" if st.session_state['pagina_atual'] == "Extrações de Dados" else "secondary")

# Adicionar o componente de links rápidos na barra lateral
# show_page_links_sidebar()

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
            
            elif pagina == "Higienizações":
                # Mapeamento reverso para subpáginas de Higienizações
                subpagina_para_rota = {v: k for k, v in SUB_ROTAS_HIGIENIZACOES.items()}
                if subpagina in subpagina_para_rota:
                    url += f"&sub={subpagina_para_rota[subpagina]}"
        
        return url
    
    # Se a página não for encontrada, retorna link para página inicial (agora Ficha da Família)
    return f"{base_url}page=ficha_familia"

# Exibição da página selecionada com base na variável de sessão
pagina = st.session_state.get('pagina_atual', 'Ficha da Família') # Adicionado .get com default para segurança
print(f"DEBUG: main.py - VALOR DE 'pagina' ANTES DO TRY: {pagina}") # DEBUG ADICIONAL

try:
    # Adicionar guia de página contextual para cada página
    # if pagina != "Apresentação Conclusões":  # Comentado temporariamente
    #     if pagina != "Extrações de Dados": # Adiciona esta condição
    #         show_page_guide(pagina)
    
    if pagina == "Ficha da Família":
        print("DEBUG: main.py - Renderizando Ficha da Família") # DEBUG
        show_ficha_familia()
    # Comentar outras páginas temporariamente
    # elif pagina == "Macro Higienização":
    #     # Definir as seções para o sumário da página
    #     sections = [
    #         {"label": "Métricas Gerais", "anchor": "metricas_gerais", "icon": "📊"},
    #         {"label": "Últimas Conclusões", "anchor": "ultimas_conclusoes", "icon": "✅"}
    #     ]
    #     show_inicio()
        
    # elif pagina == "Produção Higienização":
    #     # Definir as seções para o sumário da página
    #     sections = [
    #         {"label": "Métricas de Produção", "anchor": "metricas_producao", "icon": "📊"},
    #         {"label": "Produção por Responsável", "anchor": "producao_responsavel", "icon": "👤"},
    #         {"label": "Tendências Temporais", "anchor": "tendencias_temporais", "icon": "📈"},
    #         {"label": "Pendências", "anchor": "pendencias", "icon": "⚠️"}
    #     ]
    #     show_producao()
        
    # elif pagina == "Conclusões Higienização":
    #     # Definir as seções para o sumário da página
    #     sections = [
    #         {"label": "Métricas de Conclusão", "anchor": "metricas_conclusao", "icon": "📊"},
    #         {"label": "Análise de Qualidade", "anchor": "analise_qualidade", "icon": "🔍"},
    #         {"label": "Tendências de Conclusão", "anchor": "tendencias_conclusao", "icon": "📈"}
    #     ]
    #     show_conclusoes()
        
    elif pagina == "Higienizações":
        print("DEBUG: main.py - Renderizando Higienizações") # DEBUG
        show_higienizacoes()
        
    elif pagina == "Extrações de Dados":
        print("DEBUG: main.py - Renderizando Extrações de Dados") # DEBUG
        show_extracoes()
        
    elif pagina == "Emissões Brasileiras":
        print(f"DEBUG: main.py - Renderizando Emissões Brasileiras. Subpágina: {st.session_state.get('emissao_subpagina')}") # DEBUG
        st.write(f"Debug: main.py - Entrou no bloco para exibir Emissões Brasileiras. Subpágina atual: {st.session_state.get('emissao_subpagina')}") 
        show_cartorio_new() # CHAMADA DA FUNÇÃO DEVE ESTAR AQUI
    else:
        print(f"DEBUG: main.py - Página desconhecida na renderização: {pagina}. Voltando para Ficha da Família.") # DEBUG
        st.warning(f"Página '{pagina}' não reconhecida. Exibindo Ficha da Família.")
        show_ficha_familia() # Fallback mais explícito

    # Adicionar seção de links rápidos no rodapé (apenas para páginas que não são de apresentação)
    # Condição original era if pagina != "Apresentação Conclusões":
    # Como Apresentação foi removida, podemos chamar diretamente ou adicionar nova condição se necessário.
    st.markdown("---")
    if pagina != "Extrações de Dados": # Adiciona esta condição
        show_quick_links()

except Exception as e:
    st.error(f"Erro ao carregar a página: {str(e)}")
    # Mostrar detalhes do erro para facilitar a depuração
    st.exception(e)

# Rodapé do sidebar
st.sidebar.markdown("---")
render_sidebar_refresh_button()
st.sidebar.markdown("Dashboard desenvolvido para análise de dados do CRM Bitrix24") 
