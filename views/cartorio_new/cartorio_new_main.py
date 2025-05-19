import streamlit as st
import pandas as pd

# Importar funções do novo data_loader
from .data_loader import carregar_dados_cartorio

# Importar funções das novas seções/abas
from .visao_geral import exibir_visao_geral
from .acompanhamento import exibir_acompanhamento
# from .producao import exibir_producao # REMOVIDO
from .pendencias import exibir_pendencias
from .pendencias_adm import exibir_pendencias_adm
from .higienizacao_desempenho import exibir_higienizacao_desempenho

# Importar componente TOC - REMOVIDO
# from components.table_of_contents import render_toc 

def show_cartorio_new():
    """
    Função principal para exibir a página refatorada de Emissões Brasileiras.
    Renderiza a subpágina correta com base em st.session_state.emissao_subpagina.
    """
    # Título com estilo BI (mais profissional e vibrante)
    st.markdown("""
    <style>
    .bi-title {
        color: #1E40AF; /* Azul mais vibrante */
        font-size: 2.25rem; /* Tamanho maior */
        font-weight: 800; /* Extra negrito */
        margin-bottom: 1.25rem; /* Mais espaçamento inferior */
        padding-bottom: 0.75rem; /* Mais espaço antes da borda */
        border-bottom: 4px solid #3B82F6; /* Borda inferior mais grossa e vibrante */
        text-align: left;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1); /* Sutil sombra para profundidade */
    }
    </style>
    <h1 class='bi-title'>EMISSÕES BRASILEIRAS</h1>
    """, unsafe_allow_html=True)
    
    # --- Carregar Dados ---
    def load_data_cached():
        return carregar_dados_cartorio()
        
    with st.spinner("Carregando dados dos cartórios..."):
        df_cartorio = load_data_cached()
    
    if df_cartorio is None or df_cartorio.empty:
        st.warning("Não foi possível carregar os dados dos cartórios ou não há dados para exibir.")
        return
        
    # --- Renderização Condicional da View baseada no Estado da Sessão de main.py ---
    subpagina_selecionada = st.session_state.get('emissao_subpagina', 'Funil Certidões')
    
    if subpagina_selecionada == "Funil Certidões":
        exibir_visao_geral(df_cartorio)
    elif subpagina_selecionada == "Emissões Por Família":
        exibir_acompanhamento(df_cartorio)
    elif subpagina_selecionada == "Certidões Pendentes por responsável":
        exibir_pendencias(df_cartorio)
    elif subpagina_selecionada == "Certidões Pendentes Por ADM":
        exibir_pendencias_adm(df_cartorio)
    elif subpagina_selecionada == "Desempenho Conclusão de Pasta":
        exibir_higienizacao_desempenho()
    else:
        st.warning(f"Subpágina desconhecida: {subpagina_selecionada}")

    # --- Navegação Rápida (TOC) - REMOVIDA ---
    # st.markdown("---") 
    # sections = [...] 
    # render_toc(sections, ...) 
    # st.caption(...)

    # st.markdown("---") # Removido divisor extra
    # st.write("Fim da página Emissões Brasileiras.") # Removido texto final redundante 