import streamlit as st

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
            
            # Registrar no log
            print("Botão de atualização acionado - recarregando dados")
            
            # Recarregar a página
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

def render_sidebar_refresh_button():
    """
    Renderiza um botão grande de atualização na barra lateral esquerda
    
    Este botão permite atualizar todos os dados do relatório de uma só vez
    """
    # Criar seção visualmente destacada
    st.sidebar.markdown("""
    <div style="
        background-color: #f8f9fa; 
        padding: 15px; 
        border-radius: 8px; 
        margin: 15px 0; 
        border-left: 5px solid #FF5722;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        color: #FF5722;
    ">
        ⚡ ATUALIZAÇÃO RÁPIDA
    </div>
    """, unsafe_allow_html=True)
    
    # Botão grande nativo do Streamlit
    if st.sidebar.button("🔄 ATUALIZAR DADOS", key="btn_sidebar_refresh_all", type="primary", use_container_width=True):
        # Definir estados para forçar o recarregamento em todas as páginas
        st.session_state['reload_trigger'] = True
        st.session_state['loading_state'] = 'loading'
        
        # Registrar no log
        print("Botão de atualização acionado na sidebar - recarregando dados")
        
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