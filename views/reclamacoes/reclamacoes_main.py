import streamlit as st
import pandas as pd
import time
import sys
from pathlib import Path

# --- Configuração Inicial e Importações --- 

# Controle de depuração - definir como False em produção
# Pode ser controlado por st.session_state se necessário
DEBUG_MODE = False 

# Adicionar caminhos para importação (ajustado para nova estrutura)
# O __file__ agora está em views/reclamacoes/reclamacoes_main.py
# Precisamos subir dois níveis para chegar à raiz do projeto
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root / 'api'))
sys.path.insert(0, str(project_root / 'utils'))
sys.path.insert(0, str(project_root / 'components')) # Adicionar components

# Importar funções dos módulos separados
from .data_loader import carregar_dados_reclamacoes
from .styles import apply_tailwind_styles, THEME
from .metrics_cards import display_metrics_cards
from .charts import display_main_charts, display_distribution_charts
from .details import display_details_section

# Importar funções necessárias para refresh global (se existir)
try:
    from refresh_utils import handle_refresh_trigger, get_force_reload_status, clear_force_reload_flag
except ImportError:
    # Funções substitutas caso o módulo não seja encontrado
    print("WARN: Módulo 'refresh_utils' não encontrado. Funções de refresh global desativadas.")
    def get_force_reload_status(): return False
    def handle_refresh_trigger(): return False
    def clear_force_reload_flag(): pass

# --- Funções Auxiliares (UI) ---

def display_header_and_controls():
    """Exibe o cabeçalho da página e os controles de tema/atualização."""
    st.markdown('<h1 class="tw-heading tw-fade-in">Gestão de Reclamações</h1>', unsafe_allow_html=True)
    
    col_theme, col_refresh = st.columns([1, 9])
    
    # Botão de Tema
    with col_theme:
        theme_icon = "🌓" if st.session_state.get("dark_mode", False) else "☀️"
        theme_tooltip = "Alternar para tema claro" if st.session_state.get("dark_mode", False) else "Alternar para tema escuro"
        
        # Estilo inline para o botão de tema (simplificado)
        st.markdown("""
        <style>
        button[data-testid="baseButton-secondary"][title*="Alternar para tema"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0.5em !important;
            font-size: 1.2em !important;
            transition: transform 0.3s !important;
        }
        button[data-testid="baseButton-secondary"][title*="Alternar para tema"]:hover {
            transform: rotate(30deg) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button(theme_icon, key="btn_toggle_theme_reclamacoes", help=theme_tooltip):
            st.session_state.dark_mode = not st.session_state.get("dark_mode", False)
            st.rerun()
    
    # Botão de Atualizar Dados
    with col_refresh:
        col_blank, col_btn = st.columns([0.7, 0.3]) # Ajuste para alinhar à direita
        with col_btn:
            # Estilo inline para o botão de atualização
            st.markdown(f"""
            <style>
            div[data-testid="stButton"] > button[kind="primary"][id*="btn_atualizar_reclamacoes"] {{
                background-color: {THEME[st.session_state.get("dark_mode", False) and 'dark' or 'light']["success"]} !important;
                color: white !important;
                font-weight: bold !important;
                transition: all 0.3s !important;
            }}
            div[data-testid="stButton"] > button[kind="primary"][id*="btn_atualizar_reclamacoes"]:hover {{
                background-color: {THEME[st.session_state.get("dark_mode", False) and 'dark' or 'light']["success"]}dd !important; /* Levemente mais escuro */
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Atualizar Dados", key="btn_atualizar_reclamacoes", help="Força a atualização dos dados do Bitrix24", type="primary", use_container_width=True):
                with st.spinner("Atualizando dados e limpando cache..."):
                    st.info("Limpando cache e recarregando dados em tempo real...")
                    st.cache_data.clear() # Limpa todos os caches @st.cache_data
                    st.session_state['force_reload'] = True # Sinaliza para recarregar
                    time.sleep(0.5)
                    st.success("Cache limpo! Recarregando página...")
                    time.sleep(0.5)
                    st.rerun()
    
    st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)

def display_debug_options():
    """Exibe o expansor com opções de desenvolvimento/depuração."""
    with st.expander("⚙️ Opções de Desenvolvimento", expanded=False):
        # Checkbox para ativar/desativar o modo de depuração
        current_debug_mode = st.session_state.get("debug_mode_reclamacoes", DEBUG_MODE)
        new_debug_mode = st.checkbox("Modo de Depuração", value=current_debug_mode, 
                       help="Exibe informações adicionais para diagnóstico", key="debug_toggle_reclamacoes")
        
        if new_debug_mode != current_debug_mode:
            st.session_state.debug_mode_reclamacoes = new_debug_mode
            st.rerun()
        
        st.markdown("---")
        st.write("Caminhos do Sistema:")
        st.code(f"Project Root: {project_root}")
        st.code(f"API Path: {project_root / 'api'}")
        st.code(f"Utils Path: {project_root / 'utils'}")
        st.markdown("---")
        
        # Botão para testar conexão direta com Bitrix (simplificado)
        if st.button("Testar Conexão Bitrix (dados)", key="btn_test_bitrix_reclamacoes"):
            st.info("Iniciando teste de carregamento de dados...")
            with st.spinner("Tentando carregar dados..."):
                # Chama a função de carregar com modo debug ativado temporariamente
                df_test = carregar_dados_reclamacoes(force_reload=True, debug=True)
                if df_test is not None and not df_test.empty:
                    if "WARNING" not in df_test.iloc[0].astype(str).str.cat(): # Verifica se não são dados simulados
                        st.success(f"Conexão bem-sucedida! {len(df_test)} registros carregados.")
                        st.dataframe(df_test.head(3))
                    else:
                        st.warning("Dados simulados foram retornados.")
                else:
                    st.error("Falha ao carregar dados do Bitrix.")

# --- Função Principal da Página ---

def show_reclamacoes():
    """
    Função principal que renderiza a página de Reclamações.
    """
    # Inicializar estados da sessão se não existirem
    if "dark_mode" not in st.session_state: st.session_state.dark_mode = False
    if "debug_mode_reclamacoes" not in st.session_state: st.session_state.debug_mode_reclamacoes = DEBUG_MODE
    if "force_reload" not in st.session_state: st.session_state.force_reload = False

    # Aplicar estilos CSS
    apply_tailwind_styles()
    
    # Exibir cabeçalho e controles
    display_header_and_controls()
    
    # Lógica de atualização global e forçada
    if handle_refresh_trigger():
        st.info("⏳ Atualizando dados como parte de uma atualização global...")
        time.sleep(0.5)
        st.rerun()
    
    force_reload = st.session_state.get('force_reload', False)
    if force_reload:
        st.info("⏳ Dados sendo atualizados diretamente da API (ignorando cache)...", icon="🔄")
        st.session_state.force_reload = False # Resetar a flag
        clear_force_reload_flag() # Limpar flag global também
    
    # Carregar os dados
    debug_active = st.session_state.get("debug_mode_reclamacoes", DEBUG_MODE)
    df_reclamacoes = carregar_dados_reclamacoes(force_reload=force_reload, debug=debug_active)
    
    # Verificar se o DataFrame está vazio ou é None (após tentativa de carga)
    if df_reclamacoes is None or df_reclamacoes.empty:
        st.error("Não foi possível carregar os dados das reclamações. Verifique a conexão ou tente atualizar.")
        display_debug_options() # Mostrar opções de debug em caso de falha
        return # Interrompe a execução se não há dados

    # --- Renderização do Conteúdo --- 
    
    st.markdown('<h2 class="tw-heading">Visão Geral</h2>', unsafe_allow_html=True)
    display_metrics_cards(df_reclamacoes)
    
    st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)
    
    display_main_charts(df_reclamacoes)
    
    st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)
    
    display_distribution_charts(df_reclamacoes)
    
    st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)
    
    display_details_section(df_reclamacoes)
    
    # --- Rodapé e Opções de Debug --- 
    st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; opacity: 0.7; font-size: 0.85rem; margin-top: 2rem; margin-bottom: 1rem;">Desenvolvido com 💙 usando Streamlit.</div>', unsafe_allow_html=True)
    
    display_debug_options()

# --- Execução (se chamado diretamente) ---
if __name__ == "__main__":
    # Simular ambiente Streamlit para teste local
    if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False
    show_reclamacoes() 