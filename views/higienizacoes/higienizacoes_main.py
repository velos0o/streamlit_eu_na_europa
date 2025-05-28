import streamlit as st
# from views.producao import show_producao # REMOVIDO
# from views.conclusoes import show_conclusoes # REMOVIDO
from views.higienizacoes.checklist.higienizacao_checklist import show_higienizacao_checklist

def show_higienizacoes(sub_page=None):
    """
    Função principal que controla a exibição das subpáginas de Higienizações
    baseada no parâmetro sub_page ou no estado da sessão.
    """
    # Título principal da página
    st.title("Higienizações")
    
    # Determinar qual subpágina exibir
    # Priorizar o parâmetro sub_page se fornecido, senão usar o estado da sessão
    if sub_page is not None:
        subpagina = sub_page
    else:
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