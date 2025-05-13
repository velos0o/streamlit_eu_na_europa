import streamlit as st
from views.producao import show_producao
from views.conclusoes import show_conclusoes
from views.higienizacoes.checklist import show_higienizacao_checklist

def show_higienizacoes():
    """
    Função principal que controla a exibição das subpáginas de Higienizações
    baseada no estado da sessão.
    """
    # Título principal da página
    st.title("Higienizações")
    
    # Verificar qual subpágina exibir com base no estado da sessão
    subpagina = st.session_state.get('higienizacao_subpagina', 'Produção')
    
    # Exibir a subpágina selecionada
    if subpagina == 'Produção':
        # Exibir a página de produção atual
        show_producao()
    elif subpagina == 'Conclusões':
        # Exibir a página de conclusões atual
        show_conclusoes()
    elif subpagina == 'Checklist':
        # Exibir a nova página de checklist
        show_higienizacao_checklist()
    else:
        # Fallback para a subpágina padrão se não for encontrada
        st.warning(f"Subpágina '{subpagina}' não encontrada. Exibindo página de Produção.")
        show_producao() 