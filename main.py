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
from views.congelado import show_congelado
from views.fechamento_pasta import show_fechamento_pasta
from views.higienizacoes.higienizacoes_main import show_higienizacoes
from views.negociacao.negociacao_main import show_negociacao
from views.priorizados.priorizados_main import show_priorizados
from views.insumos.insumo_main import show_insumos
from views.scaner.scaner_main import show_scaner
import views.traducao.traducao_main
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
    "congelado": "Congelado",
    "fechamento_pasta": "Fechamento de Pasta",
    "higienizacoes": "Higienizações", 
    "cartorio_new": "Emissões Brasileiras",
    "comune": "Comune",
    "negociacao": "Negociação",
    "priorizados": "Priorizados",
    "insumos": "Insumos",
    "extracoes": "Extrações de Dados",
    "scaner": "Scaner",
    "traducao": "Tradução"
}

# Mapeamento reverso para facilitar a busca de chaves
ROTAS_INVERSO = {v: k for k, v in ROTAS.items()}

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

# Mapeamento de sub-rotas para Priorizados
SUB_ROTAS_PRIORIZADOS = {
    "dados_macros": "Dados Macros",
    "funil_etapas": "Funil - Etapas",
    "pendencias_liberadas": "Pendências Liberadas",
    "pendencias_futuras": "Pendências Futuras",
    "tempo_por_etapa": "Tempo por Etapa",
    "produtividade": "Produtividade"
}

# Mapeamento de sub-rotas para Insumos
SUB_ROTAS_INSUMOS = {
    "consulta_familia": "CONSULTA DE FAMÍLIAS",
    "mapa_inicial": "MAPA INICIAL",
    "fluxo_financeiro": "FLUXO FINANCEIRO",
    "ia": "IA",
    "criacao_adendo": "CRIAÇÃO DE ADENDO"
}

# Mapeamento para o novo submenu de Adendo
SUB_ROTAS_ADENDO = {
    "visao_geral": "Visão Geral",
    "tipo_contrato": "Tipo de Contrato",
    "analise_adendos_distratos": "Análise Adendos e Distratos",
    "acompanhamento": "Acompanhamento Operacional"
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

    # Novos estados para o submenu Priorizados
    if 'priorizado_submenu_expanded' not in st.session_state:
        st.session_state.priorizado_submenu_expanded = False
    if 'priorizado_subpagina' not in st.session_state:
        st.session_state.priorizado_subpagina = 'Dados Macros'

    # Novos estados para o submenu Insumos
    if 'insumo_submenu_expanded' not in st.session_state:
        st.session_state.insumo_submenu_expanded = False
    if 'insumo_subpagina' not in st.session_state:
        st.session_state.insumo_subpagina = 'CONSULTA DE FAMÍLIAS'

    # Novos estados para o submenu de Adendo
    if 'adendo_submenu_expanded' not in st.session_state:
        st.session_state.adendo_submenu_expanded = False
    if 'adendo_subpagina' not in st.session_state:
        st.session_state.adendo_subpagina = "Visão Geral" # Padrão

# Processar parâmetros da URL
def sincronizar_estado_e_url():
    """
    Sincroniza o estado da sessão com os parâmetros da URL para garantir consistência.
    Se a URL tiver um parâmetro 'page' válido, o estado da sessão será atualizado
    para refletir a página solicitada. Isso garante que os links diretos funcionem.
    """
    try:
        query_params = st.query_params
    except AttributeError:
        # Fallback para a API experimental (< 1.30.0)
        query_params_experimental = st.experimental_get_query_params()
        query_params = {k: v[0] if v else '' for k, v in query_params_experimental.items()}

    pagina_na_url = query_params.get("page")

    # Bloqueio explícito de acesso à página Higienizações via URL
    if pagina_na_url == 'higienizacoes':
        st.session_state['pagina_atual'] = 'Ficha da Família'
        st.query_params['page'] = 'ficha_familia'
        if 'sub' in st.query_params:
            del st.query_params['sub']
        st.rerun()

    if pagina_na_url and pagina_na_url in ROTAS:
        pagina_desejada_pela_url = ROTAS[pagina_na_url]
        
        # Apenas atualiza o estado se for diferente, para evitar reruns desnecessários
        if st.session_state.get('pagina_atual') != pagina_desejada_pela_url:
            st.session_state['pagina_atual'] = pagina_desejada_pela_url
            
            # Lógica para restaurar o estado dos submenus com base na URL
            if pagina_na_url == 'cartorio_new':
                st.session_state.emissao_submenu_expanded = True
                sub_rota = query_params.get('sub')
                if sub_rota and sub_rota in SUB_ROTAS_EMISSOES:
                    st.session_state.emissao_subpagina = SUB_ROTAS_EMISSOES[sub_rota]
            elif pagina_na_url == 'higienizacoes':
                st.session_state.higienizacao_submenu_expanded = True
                sub_rota = query_params.get('sub')
                if sub_rota and sub_rota in SUB_ROTAS_HIGIENIZACOES:
                    st.session_state.higienizacao_subpagina = SUB_ROTAS_HIGIENIZACOES[sub_rota]
            elif pagina_na_url == 'comune':
                st.session_state.comune_submenu_expanded = True
                sub_rota = query_params.get('sub')
                if sub_rota and sub_rota in SUB_ROTAS_COMUNE:
                    st.session_state.comune_subpagina = SUB_ROTAS_COMUNE[sub_rota]
            elif pagina_na_url == 'priorizados':
                st.session_state.priorizado_submenu_expanded = True
                sub_rota = query_params.get('sub')
                if sub_rota and sub_rota in SUB_ROTAS_PRIORIZADOS:
                    st.session_state.priorizado_subpagina = SUB_ROTAS_PRIORIZADOS[sub_rota]
            elif pagina_na_url == 'insumos':
                st.session_state.insumo_submenu_expanded = True
                sub_rota = query_params.get('sub')
                if sub_rota and sub_rota in SUB_ROTAS_INSUMOS:
                    st.session_state.insumo_subpagina = SUB_ROTAS_INSUMOS[sub_rota]

                    # Sincronizar sub-submenu de Adendo
                    if st.session_state.insumo_subpagina == 'CRIAÇÃO DE ADENDO':
                        st.session_state.adendo_submenu_expanded = True
                        sub2_rota = query_params.get("sub2")
                        if sub2_rota and sub2_rota in SUB_ROTAS_ADENDO:
                            st.session_state.adendo_subpagina = SUB_ROTAS_ADENDO[sub2_rota]
            
            # Força um rerun para garantir que a página correta seja exibida imediatamente
            st.rerun()

# Inicializar estados da sessão PRIMEIRO
inicializar_estados_sessao()

# Sincronizar com a URL DEPOIS da inicialização
sincronizar_estado_e_url()

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
    """Reseta todos os submenus para o estado fechado"""
    st.session_state.emissao_submenu_expanded = False
    st.session_state.adm_submenu_expanded = False
    st.session_state.higienizacao_submenu_expanded = False
    st.session_state.comune_submenu_expanded = False
    st.session_state.priorizado_submenu_expanded = False
    st.session_state.insumo_submenu_expanded = False

def ir_para_ficha_familia():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Ficha da Família'
    st.query_params['page'] = 'ficha_familia'
    if 'sub' in st.query_params:
        del st.query_params['sub']

def ir_para_congelado():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Congelado'
    st.query_params['page'] = 'congelado'
    if 'sub' in st.query_params:
        del st.query_params['sub']

def ir_para_fechamento_pasta():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Fechamento de Pasta'
    st.query_params['page'] = 'fechamento_pasta'
    if 'sub' in st.query_params:
        del st.query_params['sub']

def toggle_emissao_submenu():
    st.session_state.emissao_submenu_expanded = not st.session_state.get('emissao_submenu_expanded', False)
    st.session_state.higienizacao_submenu_expanded = False
    st.session_state.adm_submenu_expanded = False
    
    if st.session_state.emissao_submenu_expanded:
        st.session_state['pagina_atual'] = 'Emissões Brasileiras'
        current_subpage = st.session_state.get('emissao_subpagina')
        st.query_params['page'] = 'cartorio_new'
        if current_subpage not in SUB_ROTAS_EMISSOES.values():
            st.session_state.emissao_subpagina = 'Funil Certidões'
            st.query_params['sub'] = 'funil_certidoes'
        else:
            sub_route = [k for k, v in SUB_ROTAS_EMISSOES.items() if v == current_subpage][0]
            st.query_params['sub'] = sub_route

def toggle_higienizacao_submenu():
    st.session_state.higienizacao_submenu_expanded = not st.session_state.get('higienizacao_submenu_expanded', False)
    st.session_state.emissao_submenu_expanded = False
    
    if st.session_state.higienizacao_submenu_expanded:
        st.session_state['pagina_atual'] = 'Higienizações'
        st.query_params['page'] = 'higienizacoes'
        if st.session_state.get('pagina_atual') != 'Higienizações':
            st.session_state.higienizacao_subpagina = 'Checklist'
            st.query_params['sub'] = 'checklist'
        elif 'sub' in st.query_params:
            del st.query_params['sub']

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
    st.session_state.emissao_submenu_expanded = True
    st.session_state.adm_submenu_expanded = True
    st.session_state.adm_subpagina = 'Certidões Pendentes por ADM'
    st.query_params['page'] = 'cartorio_new'
    st.query_params['sub'] = 'certidoes_pendentes_adm'

def ir_para_negociacao():
    st.session_state['pagina_atual'] = 'Negociação'
    st.session_state.emissao_submenu_expanded = False
    st.session_state.higienizacao_submenu_expanded = False
    st.session_state.comune_submenu_expanded = False
    st.query_params['page'] = 'negociacao'
    
def ir_para_priorizados():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Priorizados'
    st.session_state.priorizado_submenu_expanded = True
    # Mantém a subpágina atual ou vai para o padrão
    sub_rota = next((key for key, value in SUB_ROTAS_PRIORIZADOS.items() if value == st.session_state.priorizado_subpagina), 'dados_macros')
    st.query_params = {'page': 'priorizados', 'sub': sub_rota}

# Nova função para toggle do submenu Comune
def toggle_comune_submenu():
    st.session_state.comune_submenu_expanded = not st.session_state.get('comune_submenu_expanded', False)
    st.session_state.emissao_submenu_expanded = False
    st.session_state.higienizacao_submenu_expanded = False
    st.session_state.adm_submenu_expanded = False
    
    if st.session_state.comune_submenu_expanded:
        st.session_state['pagina_atual'] = 'Comune'
        current_subpage = st.session_state.get('comune_subpagina')
        st.query_params['page'] = 'comune'
        if current_subpage not in SUB_ROTAS_COMUNE.values():
            st.session_state.comune_subpagina = 'Produção Comune'
            st.query_params['sub'] = 'producao_comune'
        else:
            sub_route = [k for k, v in SUB_ROTAS_COMUNE.items() if v == current_subpage][0]
            st.query_params['sub'] = sub_route

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
    reset_submenu()
    st.session_state['pagina_atual'] = 'Comune'
    st.session_state.comune_submenu_expanded = True
    st.session_state.comune_subpagina = 'Status Certidão'
    st.query_params = {'page': 'comune', 'sub': 'status_certidao'}

def toggle_priorizado_submenu():
    reset_submenu()
    st.session_state.pagina_atual = 'Priorizados'
    st.session_state.priorizado_submenu_expanded = not st.session_state.get('priorizado_submenu_expanded', False)
    sub_rota = next((key for key, value in SUB_ROTAS_PRIORIZADOS.items() if value == st.session_state.priorizado_subpagina), 'dados_macros')
    st.query_params = {'page': 'priorizados', 'sub': sub_rota}

def ir_para_priorizado_subpagina(sub_pagina_nome):
    def navigate():
        reset_submenu()
        st.session_state.pagina_atual = 'Priorizados'
        st.session_state.priorizado_submenu_expanded = True
        st.session_state.priorizado_subpagina = sub_pagina_nome
        sub_rota_key = next((k for k, v in SUB_ROTAS_PRIORIZADOS.items() if v == sub_pagina_nome), 'dados_macros')
        st.query_params = {'page': 'priorizados', 'sub': sub_rota_key}
    return navigate

def ir_para_extracoes():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Extrações de Dados'
    st.query_params['page'] = 'extracoes'
    if 'sub' in st.query_params:
        del st.query_params['sub']

def ir_para_scaner():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Scaner'
    st.query_params['page'] = 'scaner'
    if 'sub' in st.query_params:
        del st.query_params['sub']

def ir_para_traducao():
    reset_submenu()
    st.session_state['pagina_atual'] = 'Tradução'
    st.query_params['page'] = 'traducao'
    if 'sub' in st.query_params:
        del st.query_params['sub']

# Funções para o novo menu Insumos
def toggle_insumo_submenu():
    reset_submenu()
    st.session_state.pagina_atual = 'Insumos'
    st.session_state.insumo_submenu_expanded = not st.session_state.get('insumo_submenu_expanded', False)
    # Define a subpágina atual ou padrão e atualiza a URL
    sub_rota = next((key for key, value in SUB_ROTAS_INSUMOS.items() if value == st.session_state.insumo_subpagina), 'consulta_familia')
    st.query_params = {'page': 'insumos', 'sub': sub_rota}

def ir_para_insumo_subpagina(sub_pagina_nome):
    """Função de fábrica para criar callbacks de navegação para Insumos."""
    def navigate():
        st.session_state.pagina_atual = 'Insumos'
        st.session_state.insumo_submenu_expanded = True
        st.session_state.insumo_subpagina = sub_pagina_nome
        
        query_params = {'page': 'insumos', 'sub': next((k for k, v in SUB_ROTAS_INSUMOS.items() if v == sub_pagina_nome), 'consulta_familia')}

        # Gerencia o estado do submenu aninhado
        if sub_pagina_nome == "CRIAÇÃO DE ADENDO":
            st.session_state.adendo_submenu_expanded = True # Abre
            # Garante que a sub-página de adendo seja incluída na URL
            sub2_rota_key = next((k for k, v in SUB_ROTAS_ADENDO.items() if v == st.session_state.adendo_subpagina), 'visao_geral')
            query_params['sub2'] = sub2_rota_key
        else:
            st.session_state.adendo_submenu_expanded = False # Fecha
        
        st.query_params = query_params
    return navigate

def ir_para_adendo_subpagina(sub_pagina_nome):
    """Função de fábrica para criar callbacks para o submenu Adendo."""
    def navigate():
        st.session_state.adendo_subpagina = sub_pagina_nome
        st.query_params['sub2'] = next((k for k, v in SUB_ROTAS_ADENDO.items() if v == sub_pagina_nome), 'visao_geral')
    return navigate

# A DEFINIÇÃO DA FUNÇÃO VEM AQUI, ANTES DE SER USADA
def sub_button(label, key, is_active, on_click):
    """Cria um botão de submenu estilizado."""
    st.button(
        label, 
        key=f"subbtn_{key}", 
        on_click=on_click, 
        use_container_width=True, 
        type="primary" if is_active else "secondary"
    )

# Botões de navegação
st.sidebar.button(
    "Ficha da Família", 
    key="btn_ficha_familia",
    on_click=ir_para_ficha_familia,
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Ficha da Família" else "secondary"
)

st.sidebar.button(
    "Congelado", 
    key="btn_congelado",
    on_click=ir_para_congelado,
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Congelado" else "secondary"
)

st.sidebar.button(
    "Fechamento de Pasta",
    key="btn_fechamento_pasta",
    on_click=ir_para_fechamento_pasta,
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Fechamento de Pasta" else "secondary"
)

_ocultar_hig = True or st.session_state.get('ocultar_higienizacoes', False)
_relatorios_ocultos_hig = st.session_state.get('relatorios_ocultos', [])
_relatorios_ocultos_map_hig = st.session_state.get('relatorios_ocultos_map', {})
_hig_oculto = (
    _ocultar_hig
    or ('Higienizações' in _relatorios_ocultos_hig)
    or (_relatorios_ocultos_map_hig.get('Higienizações') is True)
)
if not _hig_oculto:
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
    "Negociação", 
    key="btn_negociacao",
    on_click=ir_para_negociacao,
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Negociação" else "secondary",
    help="Módulo de Negociação"
)

st.sidebar.button(
    "Priorizados", 
    key="btn_priorizados",
    on_click=toggle_priorizado_submenu,
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Priorizados" else "secondary",
    help="Módulo de Priorizados"
)

if st.session_state.get('priorizado_submenu_expanded', False):
    with st.sidebar.container():
        for sub_key, sub_value in SUB_ROTAS_PRIORIZADOS.items():
            is_active = st.session_state.get('priorizado_subpagina') == sub_value
            sub_button(sub_value, f"priorizado_{sub_key}", is_active, ir_para_priorizado_subpagina(sub_value))

# Botão para Insumos
st.sidebar.button(
    "Insumos",
    key="btn_insumos",
    on_click=toggle_insumo_submenu,
    use_container_width=True,
    type="primary" if st.session_state['pagina_atual'] == "Insumos" else "secondary",
    help="Relatórios de Insumos"
)

# Submenu Insumos
if st.session_state.get('insumo_submenu_expanded', False):
    with st.sidebar.container():
        for key, nome_subpagina in SUB_ROTAS_INSUMOS.items():
            is_active = st.session_state.get('insumo_subpagina') == nome_subpagina
            sub_button(nome_subpagina, key, is_active, ir_para_insumo_subpagina(nome_subpagina))
            
            # Lógica para o submenu de Adendo
            if nome_subpagina == "CRIAÇÃO DE ADENDO" and is_active:
                if st.session_state.get('adendo_submenu_expanded', False):
                    with st.container():
                        st.markdown("<div class='sub-button-container-level2'>", unsafe_allow_html=True)
                        for key_adendo, nome_adendo_sub in SUB_ROTAS_ADENDO.items():
                            is_active_adendo = st.session_state.get('adendo_subpagina') == nome_adendo_sub
                            sub_button(nome_adendo_sub, f"adendo_{key_adendo}", is_active_adendo, ir_para_adendo_subpagina(nome_adendo_sub))
                        st.markdown("</div>", unsafe_allow_html=True)

st.sidebar.button(
    "Scaner", 
    key="btn_scaner", 
    on_click=ir_para_scaner,
    use_container_width=True,
    type="primary" if st.session_state.get('pagina_atual') == "SCANER" else "secondary",
    help="Módulo de scaner de documentos"
)

st.sidebar.button(
    "Tradução",
    key="btn_traducao",
    on_click=ir_para_traducao,
    use_container_width=True,
    type="primary" if st.session_state.get('pagina_atual') == "Tradução" else "secondary",
    help="Módulo de tradução de documentos"
)

# Ocultar botão de Extrações de Dados se marcado como oculto
_ocultar_extracoes = st.session_state.get('ocultar_extracoes', False)
_relatorios_ocultos = st.session_state.get('relatorios_ocultos', [])
_relatorios_ocultos_map = st.session_state.get('relatorios_ocultos_map', {})
_extracoes_oculto = (
    _ocultar_extracoes
    or ('Extrações de Dados' in _relatorios_ocultos)
    or (_relatorios_ocultos_map.get('Extrações de Dados') is True)
)
if not _extracoes_oculto:
    st.sidebar.button(
        "Extrações de Dados", 
        key="btn_extracoes", 
        on_click=ir_para_extracoes,
        use_container_width=True,
        type="primary" if st.session_state['pagina_atual'] == "Extrações de Dados" else "secondary",
        help="Módulo de extrações e relatórios"
    )

# Exibição da página selecionada
current_page = st.session_state.get('pagina_atual', 'Ficha da Família')

try:
    if current_page == "Ficha da Família":
        show_ficha_familia()
    elif current_page == "Congelado":
        show_congelado()
    elif current_page == "Fechamento de Pasta":
        show_fechamento_pasta()
    elif current_page == "Higienizações":
        # Se oculto, redireciona para Ficha da Família e não renderiza
        if _hig_oculto:
            st.session_state['pagina_atual'] = 'Ficha da Família'
            st.query_params['page'] = 'ficha_familia'
            st.rerun()
        if st.session_state.get('higienizacao_subpagina') == "Checklist":
            show_higienizacoes(sub_page="checklist")
        else:
            show_higienizacoes()
    elif current_page == "Emissões Brasileiras":
        show_cartorio_new(st.session_state.emissao_subpagina, st.session_state.adm_subpagina)
    elif current_page == "Comune":
        if st.session_state.get('comune_subpagina') == "Produção Comune":
            views.comune.producao_comune.show_producao_comune()
        elif st.session_state.get('comune_subpagina') == "Funil Certidões Italianas":
            views.comune.funil_certidoes_italianas.show_funil_certidoes_italianas()
        elif st.session_state.get('comune_subpagina') == "Status Certidão":
            views.comune.status_certidao.show_status_certidao()
        else:
            views.comune.comune_main.show_comune_main()
    elif current_page == "Negociação":
        show_negociacao()
    elif current_page == "Priorizados":
        show_priorizados(st.session_state.get('priorizado_subpagina'))
    elif current_page == "Extrações de Dados":
        show_extracoes()
    elif current_page == "Insumos":
        show_insumos(st.session_state.get('insumo_subpagina'), st.session_state.get('adendo_subpagina'))
    elif current_page == "Scaner":
        show_scaner()
    elif current_page == "Tradução":
        views.traducao.traducao_main.show_traducao()
    else:
        st.error(f"Página '{current_page}' não encontrada!")
        
except Exception as e:
    st.error(f"Erro ao carregar a página: {str(e)}")
    st.error("Verifique se todos os arquivos necessários estão disponíveis.")

# Função principal
def main():
    """Função principal que renderiza a aplicação Streamlit."""
    # ... código existente ...

if __name__ == "__main__":
    main()