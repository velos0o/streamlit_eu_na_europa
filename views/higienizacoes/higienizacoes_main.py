import streamlit as st
# from views.producao import show_producao # REMOVIDO
# from views.conclusoes import show_conclusoes # REMOVIDO
from views.higienizacoes.checklist.higienizacao_checklist import show_higienizacao_checklist

def show_higienizacoes():
    """
    Função principal que controla a exibição das subpáginas de Higienizações
    baseada no estado da sessão.
    """
    # Título principal da página
    st.title("Higienizações")
    
    # Verificar qual subpágina exibir com base no estado da sessão
    subpagina = st.session_state.get('higienizacao_subpagina', 'Checklist') # PADRÃO ATUALIZADO
    
    # Exibir a subpágina selecionada
    # REMOVIDO IF PARA PRODUÇÃO
    # if subpagina == 'Produção':
    #     # Exibir a página de produção atual
    #     show_producao()
    # REMOVIDO ELIF PARA CONCLUSÕES
    # elif subpagina == 'Conclusões':
    #     # Exibir a página de conclusões atual
    #     show_conclusoes()
    if subpagina == 'Checklist': # Alterado para if, já que é a única opção principal agora
        # Exibir a nova página de checklist
        show_higienizacao_checklist()
    else:
        # Fallback para a subpágina padrão se não for encontrada
        st.warning(f"Subpágina '{subpagina}' não encontrada. Exibindo Checklist.")
        show_higienizacao_checklist() # Exibe Checklist como fallback 