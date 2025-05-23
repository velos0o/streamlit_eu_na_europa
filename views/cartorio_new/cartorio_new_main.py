import streamlit as st
import pandas as pd

# Importar funções do novo data_loader
from .data_loader import carregar_dados_cartorio

# Importar funções das novas seções/abas
from .visao_geral import exibir_visao_geral
from .acompanhamento import exibir_acompanhamento
# OCULTO DA VISÃO DO USUÁRIO - PRODUÇÃO
# from .producao import exibir_producao
from .pendencias import exibir_pendencias
from .pendencias_adm import exibir_pendencias_adm
from .higienizacao_desempenho import exibir_higienizacao_desempenho
from .producao_adm import exibir_producao_adm
from .producao_time_doutora import exibir_producao_time_doutora
from .pesquisa_br import exibir_pesquisa_br

# Importar componente TOC - REMOVIDO
# from components.table_of_contents import render_toc 

def show_cartorio_new():
    """
    Função principal para exibir a página refatorada de Emissões Brasileiras.
    Renderiza a subpágina correta com base em st.session_state.emissao_subpagina.
    """
    # --- Carregar CSS Compilado ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")
    # --- Fim Carregar CSS ---

    # Título com classe SCSS (substituindo CSS inline)
    st.markdown('<h1 class="bi-title">EMISSÕES BRASILEIRAS</h1>', unsafe_allow_html=True)
    
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
    elif subpagina_selecionada == "Desempenho Conclusão de Pasta":
        exibir_higienizacao_desempenho()
    elif subpagina_selecionada == "ADM":
        # Submenu ADM
        adm_subpagina = st.session_state.get('adm_subpagina', 'Produção ADM')
        
        if adm_subpagina == "Produção ADM":
            exibir_producao_adm(df_cartorio)
        elif adm_subpagina == "Certidões Pendentes por ADM":
            exibir_pendencias_adm(df_cartorio)
        else:
            st.warning(f"Subpágina ADM desconhecida: {adm_subpagina}")
    elif subpagina_selecionada == "Produção Time Doutora":
        exibir_producao_time_doutora(df_cartorio)
    elif subpagina_selecionada == "Pesquisa BR":
        exibir_pesquisa_br(df_cartorio)
    else:
        st.warning(f"Subpágina desconhecida: {subpagina_selecionada}")

    # --- Navegação Rápida (TOC) - REMOVIDA ---
    # st.markdown("---") 
    # sections = [...] 
    # render_toc(sections, ...) 
    # st.caption(...)

    # st.markdown("---") # Removido divisor extra
    # st.write("Fim da página Emissões Brasileiras.") # Removido texto final redundante 