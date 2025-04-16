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
from views.cartorio.cartorio_main import show_cartorio
from views.extracoes.extracoes_main import show_extracoes
# Importar nova página de apresentação de conclusões
from views.apresentacao import show_apresentacao
# Importar nova página de COMUNE
from views.comune.comune_main import show_comune
# Importar nova página de Tickets
from views.tickets import show_tickets
# Importar nova página de Reclamações
from views.reclamacoes import show_reclamacoes

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

# Variável de estado para controlar a navegação
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'Macro Higienização'

# Funções simples para alterar a página
def ir_para_inicio(): st.session_state['pagina_atual'] = 'Macro Higienização'
def ir_para_producao(): st.session_state['pagina_atual'] = 'Produção Higienização'
def ir_para_conclusoes(): st.session_state['pagina_atual'] = 'Conclusões Higienização'
def ir_para_cartorio(): st.session_state['pagina_atual'] = 'Cartório'
def ir_para_comune(): st.session_state['pagina_atual'] = 'Comune'
def ir_para_extracoes(): st.session_state['pagina_atual'] = 'Extrações de Dados'
def ir_para_apresentacao(): st.session_state['pagina_atual'] = 'Apresentação Conclusões'
def ir_para_tickets(): st.session_state['pagina_atual'] = 'Tickets'
def ir_para_reclamacoes(): st.session_state['pagina_atual'] = 'Reclamações'

# Botões individuais para navegação (usando método tradicional)
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

st.sidebar.button("Funil Emissões Bitrix", key="btn_cartorio", 
            on_click=ir_para_cartorio,
            use_container_width=True,
            type="primary" if st.session_state['pagina_atual'] == "Cartório" else "secondary")

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
        render_toc(sections, "Navegação Rápida", horizontal=True)
        show_inicio()
        
    elif pagina == "Produção Higienização":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Métricas de Produção", "anchor": "metricas_producao", "icon": "📊"},
            {"label": "Produção por Responsável", "anchor": "producao_responsavel", "icon": "👤"},
            {"label": "Tendências Temporais", "anchor": "tendencias_temporais", "icon": "📈"},
            {"label": "Pendências", "anchor": "pendencias", "icon": "⚠️"}
        ]
        render_toc(sections, "Navegação Rápida", horizontal=True)
        show_producao()
        
    elif pagina == "Conclusões Higienização":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Métricas de Conclusão", "anchor": "metricas_conclusao", "icon": "📊"},
            {"label": "Análise de Qualidade", "anchor": "analise_qualidade", "icon": "🔍"},
            {"label": "Tendências de Conclusão", "anchor": "tendencias_conclusao", "icon": "📈"}
        ]
        render_toc(sections, "Navegação Rápida", horizontal=True)
        show_conclusoes()
        
    elif pagina == "Cartório":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Visão do Funil", "anchor": "visao_funil", "icon": "📋"},
            {"label": "Conversão Entre Etapas", "anchor": "conversao_etapas", "icon": "🔄"},
            {"label": "Previsão de Conclusões", "anchor": "previsao_conclusoes", "icon": "🔮"}
        ]
        render_toc(sections, "Navegação Rápida", horizontal=True)
        show_cartorio()
        
    elif pagina == "Comune":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Análise de Comunidades", "anchor": "analise_comunidades", "icon": "👥"},
            {"label": "Interações", "anchor": "interacoes", "icon": "🔄"},
            {"label": "Métricas de Engajamento", "anchor": "metricas_engajamento", "icon": "📊"}
        ]
        render_toc(sections, "Navegação Rápida", horizontal=True)
        show_comune()
        
    elif pagina == "Extrações de Dados":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Extração Personalizada", "anchor": "extracao_personalizada", "icon": "🔍"},
            {"label": "Relatórios Prontos", "anchor": "relatorios_prontos", "icon": "📋"},
            {"label": "Exportação", "anchor": "exportacao", "icon": "📤"}
        ]
        render_toc(sections, "Navegação Rápida", horizontal=True)
        show_extracoes()
        
    elif pagina == "Tickets":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Visão Geral", "anchor": "visao_geral", "icon": "📊"},
            {"label": "Por Tempo", "anchor": "por_tempo", "icon": "🕒"},
            {"label": "Detalhes", "anchor": "detalhes", "icon": "🔍"}
        ]
        render_toc(sections, "Navegação Rápida", horizontal=True)
        show_tickets()
        
    elif pagina == "Reclamações":
        # Definir as seções para o sumário da página
        sections = [
            {"label": "Visão Geral", "anchor": "visao_geral", "icon": "📊"},
            {"label": "Tendência", "anchor": "tendencia", "icon": "📈"},
            {"label": "Detalhes", "anchor": "detalhes", "icon": "🔍"}
        ]
        render_toc(sections, "Navegação Rápida", horizontal=True)
        show_reclamacoes()
        
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
