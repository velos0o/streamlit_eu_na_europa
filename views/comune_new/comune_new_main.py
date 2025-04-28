import streamlit as st
import pandas as pd

# Importar funções do data_loader de comune_new
from .data_loader import load_comune_data

# Importar a função da sub-página de Visão Geral
from .visao_geral import exibir_visao_geral_comune
# --- NOVO: Importar a função da sub-página de Tempo de Solicitação ---
from .tempo_solicitacao import exibir_tempo_solicitacao
# --- NOVO: Importar a futura função da sub-página de Mapa ---
from .mapa_comunes import exibir_mapa_comune # Criaremos este arquivo/função

def show_comune_new():
    """
    Função principal para exibir a nova página de Comune.
    Renderiza a subpágina correta com base em st.session_state.comune_subpagina
    (definida na sidebar de main.py).
    """
    # Título da seção (pode ser personalizado)
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
    <h1 class='bi-title'>COMUNE (NOVO)</h1>
    """, unsafe_allow_html=True)

    # --- Carregar Dados ---
    @st.cache_data(ttl=3600) # Cache por 1 hora
    def load_data_cached():
        return load_comune_data()

    with st.spinner("Carregando dados de Comune..."):
        df_comune = load_data_cached()

    if df_comune is None or df_comune.empty:
        # A mensagem de aviso já é mostrada pelo data_loader placeholder
        # st.warning("Não foi possível carregar os dados de Comune ou não há dados para exibir.")
        return

    # --- Renderização Condicional da View baseada no Estado da Sessão ---
    # A subpágina será definida pela navegação na sidebar em main.py
    subpagina_selecionada = st.session_state.get('comune_subpagina', 'Visão Geral') # Default para Visão Geral

    if subpagina_selecionada == "Visão Geral":
        exibir_visao_geral_comune(df_comune)
    elif subpagina_selecionada == "Tempo de Solicitação":
        exibir_tempo_solicitacao(df_comune)
        
    # --- NOVA LÓGICA PARA RENDERIZAR MAPAS ---
    elif subpagina_selecionada.startswith("Mapa Comune"): # Verifica se a subpágina é um mapa
        # Mapear nome da subpágina para CATEGORY_ID
        mapa_ids = {
            "Mapa Comune 1": "22",
            "Mapa Comune 2": "58",
            "Mapa Comune 3": "60"
        }
        category_id_selecionado = mapa_ids.get(subpagina_selecionada)
        
        if category_id_selecionado:
            if 'CATEGORY_ID' in df_comune.columns:
                df_comune['CATEGORY_ID'] = df_comune['CATEGORY_ID'].astype(str)
                df_mapa = df_comune[df_comune['CATEGORY_ID'] == category_id_selecionado].copy()
                if not df_mapa.empty:
                    exibir_mapa_comune(df_mapa, category_id_selecionado)
                else:
                    st.warning(f"Nenhum dado encontrado para {subpagina_selecionada} (CATEGORY_ID {category_id_selecionado}).")
            else:
                st.error("Coluna 'CATEGORY_ID' não encontrada nos dados carregados. Não é possível filtrar para o mapa.")
        else:
            st.error(f"Subpágina de mapa inválida: {subpagina_selecionada}")
    # --- FIM NOVA LÓGICA PARA MAPAS ---
    
    else:
        st.warning(f"Subpágina desconhecida para Comune (Novo): {subpagina_selecionada}")
        st.info("Selecione uma opção no menu lateral.") 