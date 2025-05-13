import streamlit as st

def show_quick_links():
    """
    Exibe uma seção de links rápidos para navegação direta entre páginas do relatório.
    Esta função mostra uma caixa expansível com URLs que podem ser copiadas para acesso direto.
    """
    with st.expander("🔗 Links Rápidos", expanded=False):
        st.markdown("""
        ### Links para Navegação Direta
        
        Copie os links abaixo para acessar diretamente cada seção do relatório ou compartilhar com outros usuários.
        """)
        
        # Container para os links organizados em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Páginas Principais")
            st.markdown("🏠 [Página Inicial](?page=pagina_inicial)")
            st.markdown("📊 [Higienizações](?page=higienizacoes)")
            st.markdown("📝 [Emissões Brasileiras](?page=cartorio_new)")
            st.markdown("🗺️ [Comune (Novo)](?page=comune_new)")
            st.markdown("🏛️ [Comune](?page=comune)")
            
        with col2:
            st.subheader("Subpáginas")
            
            # Emissões Brasileiras
            st.markdown("**Emissões Brasileiras:**")
            st.markdown("📈 [Visão Geral](?page=cartorio_new&sub=visao_geral)")
            st.markdown("👁️ [Acompanhamento](?page=cartorio_new&sub=acompanhamento)")
            st.markdown("⚙️ [Produção](?page=cartorio_new&sub=producao)")
            st.markdown("⚠️ [Pendências](?page=cartorio_new&sub=pendencias)")
            
            # Comune (Novo)
            st.markdown("**Comune (Novo):**")
            st.markdown("📊 [Visão Geral](?page=comune_new&sub=visao_geral)")
            st.markdown("⏱️ [Tempo de Solicitação](?page=comune_new&sub=tempo_solicitacao)")
            st.markdown("🗺️ [Mapa Comune 1](?page=comune_new&sub=mapa_comune_1)")
            
            # Higienizações
            st.markdown("**Higienizações:**")
            st.markdown("🏭 [Produção](?page=higienizacoes&sub=producao)")
            st.markdown("✅ [Conclusões](?page=higienizacoes&sub=conclusoes)")
            st.markdown("📋 [Checklist](?page=higienizacoes&sub=checklist)")
        
        st.markdown("""
        ### Como usar os links
        
        1. Clique no link desejado para navegar diretamente para a página
        2. Copie o link e compartilhe por e-mail, mensagem ou bookmark
        3. Use estes links para criar atalhos personalizados
        
        > **Dica:** Os links mantêm os parâmetros de URL, então você pode adicionar seus próprios parâmetros como filtros ou configurações.
        """)

def show_page_links_sidebar():
    """
    Exibe links rápidos na barra lateral para navegação direta.
    """
    with st.sidebar.expander("🔗 Links Diretos", expanded=False):
        st.markdown("**Acesso Rápido:**")
        st.markdown("🏠 [Página Inicial](?page=pagina_inicial)")
        st.markdown("📝 [Emissões](?page=cartorio_new)")
        st.markdown("🗺️ [Comune](?page=comune_new)")
        st.markdown("📊 [Higienizações](?page=higienizacoes)") 