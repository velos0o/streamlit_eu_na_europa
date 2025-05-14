import streamlit as st
from utils.refresh_utils import clear_file_cache

def render_refresh_button():
    """
    Renderiza um botão grande de atualização flutuante no canto da tela
    
    Este botão permite atualizar todos os dados do relatório de uma só vez
    """
    # Estilo CSS para o botão flutuante
    st.markdown("""
    <style>
    /* Container do botão fixo no canto */
    div.refresh-button-fixed {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 999;
    }
    
    /* Estilo do botão grande circular */
    div.refresh-button-fixed button {
        width: 75px !important;
        height: 75px !important;
        border-radius: 50% !important;
        font-size: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #0066cc !important;
        color: white !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Efeito hover */
    div.refresh-button-fixed button:hover {
        background-color: #0052a3 !important;
        transform: scale(1.05) !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Criando um container para posicionar o botão
    button_container = st.container()
    with button_container:
        # Hack: Usar uma coluna para posicionar o botão no canto
        st.markdown('<div class="refresh-button-fixed">', unsafe_allow_html=True)
        
        # Botão de atualização
        if st.button("↻", key="btn_refresh_all", type="primary"):
            # Definir estados para forçar o recarregamento em todas as páginas
            st.session_state['reload_trigger'] = True
            st.session_state['loading_state'] = 'loading'
            
            # Limpar cache de arquivos
            clear_file_cache()
            
            # Registrar no log
            print("Botão de atualização acionado - recarregando dados")
            
            # Recarregar a página
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

def render_sidebar_refresh_button():
    """
    Renderiza um botão de atualização na barra lateral esquerda
    
    Este botão permite atualizar todos os dados do relatório de uma só vez
    """
    # Verificar se tem mensagem de sucesso para mostrar (de uma atualização anterior)
    if 'refresh_success' in st.session_state and st.session_state['refresh_success']:
        st.sidebar.success("✅ Dados atualizados com sucesso!", icon="✅")
        # Limpar flag após mostrar
        st.session_state['refresh_success'] = False
    
    # Botão nativo do Streamlit (sem o cabeçalho "ATUALIZAÇÃO RÁPIDA")
    if st.sidebar.button("🔄 ATUALIZAR DADOS", key="btn_sidebar_refresh_all", type="primary", use_container_width=True):
        # Limpar TODOS os dados em cache para forçar nova chamada à API
        chaves_para_limpar = [
            # Estados de carregamento
            'loading_state',
            'reload_trigger',
            
            # Dados da página inicial
            'df_inicio', 
            'macro_counts', 
            'conclusoes_recentes',
            
            # Dados da página de produção
            'filtered_df',
            'filtered_df_cat34',
            
            # Dados de páginas principais
            'df_conclusoes',
            'df_cartorio',
            'df_comune',
            'df_extracoes',
            'df_ficha_familia',
            'df_higienizacoes',
            'df_cartorio_new',
            
            # Novos dados de checklist
            'df_checklist',
            'df_higienizacoes_checklist',
            
            # Dados das novas sub-páginas de Emissões
            'df_funil_certidoes',
            'df_emissoes_por_familia',
            'df_certidoes_pendentes',
            'df_desempenho_conclusao',
            
            # Filtros e configurações para reiniciar
            'start_date',
            'end_date',
            'selected_status',
            'selected_responsibles',
            
            # Chaves específicas para planilhas
            'data_planilha',
            'df_planilha',
            'df_planilha_raw',
            'planilha_time',
            'planilha_ultima_atualizacao',
            'planilha_cache_key',
            
            # Limpeza de todos os caches relacionados a DataFrames
            'df_',
            'data_',
            'cached_',
            'excel_',
            'csv_',
            'sheet_',
        ]
        
        # Limpar cada chave se existir no estado da sessão
        for chave in chaves_para_limpar:
            # Limpar chaves exatas
            if chave in st.session_state:
                del st.session_state[chave]
            
            # Limpar todas as chaves que começam com determinados prefixos
            if chave.endswith('_'):
                prefixo = chave
                chaves_com_prefixo = [k for k in st.session_state.keys() if k.startswith(prefixo)]
                for k in chaves_com_prefixo:
                    del st.session_state[k]
        
        # Definir explicitamente o estado de carregamento como 'not_started' 
        # para forçar recarregamento completo
        st.session_state['loading_state'] = 'not_started'
        
        # Flag para indicar que estamos fazendo uma atualização completa
        st.session_state['full_refresh'] = True
        
        # Flag para forçar releitura de arquivos externos
        st.session_state['force_reload_files'] = True
        
        # Timestamp atual para invalidar caches
        import time
        st.session_state['last_refresh_timestamp'] = time.time()
        
        # Limpar cache de arquivos usando a função dedicada
        clear_file_cache()
        
        # Definir flag de sucesso para mostrar mensagem após recarregar
        st.session_state['refresh_success'] = True
        
        # Registrar no log
        print("Atualizando todos os dados - limpeza completa do cache")
        
        # Recarregar a página
        st.rerun()
    
    # Adicionar espaço após o botão
    st.sidebar.markdown("---")

def render_refresh_button_streamlit():
    """
    Renderiza um botão de atualização usando componentes nativos do Streamlit
    
    Esta versão é uma alternativa que usa o st.button e lógica de estado do Streamlit
    """
    # Estilo CSS para posicionar o contêiner do botão
    st.markdown("""
    <style>
    [data-testid="stButton"] {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 999;
    }
    
    /* Estilo personalizado para o botão grande */
    .big-refresh-button button {
        width: 75px !important;
        height: 75px !important;
        border-radius: 50% !important;
        font-size: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Contêiner com classe personalizada para o botão
    with st.container():
        st.markdown('<div class="big-refresh-button">', unsafe_allow_html=True)
        if st.button("↻", key="refresh_button", type="primary"):
            # Limpar estado de carregamento
            if 'loading_state' in st.session_state:
                st.session_state['loading_state'] = 'loading'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Manter a versão antiga como referência, mas não usar
def render_refresh_button_js():
    """
    Renderiza um botão de atualização usando JavaScript puro
    
    Nota: Esta implementação é uma alternativa que usa JavaScript e localStorage
    """
    # Estilo CSS para o botão flutuante
    st.markdown("""
    <style>
    .refresh-button-container {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 999;
    }
    
    .refresh-button {
        background-color: #0066cc;
        color: white;
        border: none;
        border-radius: 50%;
        width: 75px;
        height: 75px;
        font-size: 32px;
        cursor: pointer;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
    }
    
    .refresh-button:hover {
        background-color: #0052a3;
        transform: scale(1.05);
        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
    }
    
    .refresh-button span {
        line-height: 0;
    }
    
    /* Texto que aparece ao passar o mouse */
    .refresh-button-tooltip {
        position: absolute;
        bottom: 85px;
        right: 0;
        background-color: #333;
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 14px;
        opacity: 0;
        transition: opacity 0.3s;
        white-space: nowrap;
    }
    
    .refresh-button-container:hover .refresh-button-tooltip {
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # HTML para o botão flutuante
    refresh_button_html = """
    <div class="refresh-button-container">
        <div class="refresh-button-tooltip">Atualizar todos os dados</div>
        <button class="refresh-button" onclick="reloadPage()">
            <span>↻</span>
        </button>
    </div>
    
    <script>
    function reloadPage() {
        // Limpar estados persistentes se necessário
        localStorage.setItem('reload_trigger', 'true');
        // Recarregar a página
        window.location.reload();
    }
    
    // Verificar se a página foi recarregada pelo botão
    document.addEventListener('DOMContentLoaded', function() {
        if (localStorage.getItem('reload_trigger') === 'true') {
            localStorage.removeItem('reload_trigger');
            // Aqui podemos adicionar alguma lógica quando a página recarregar
        }
    });
    </script>
    """
    
    # Renderizar o botão
    st.markdown(refresh_button_html, unsafe_allow_html=True) 