import streamlit as st

def show_cartorio():
    """
    Exibe a página principal do Cartório
    """
    st.title("Gestão de Cartório")
    st.markdown("---")
    
    st.markdown("""
    ## Gestão de Documentação
    
    Esta seção do dashboard é dedicada à gestão de documentação e processos de cartório.
    
    ### Submódulos Planejados:
    
    1. **Controle de Documentos**: Monitoramento de documentos pendentes e completos
    2. **Acompanhamento de Processos**: Status de processos em cartório
    3. **Métricas de Cartório**: Estatísticas e tempos médios de processamento
    
    Seleções futuras estarão disponíveis aqui.
    """)
    
    # Menu para os submódulos (a ser implementado)
    menu_options = ["Aguardando Implementação"]
    selected = st.selectbox("Selecione uma opção:", menu_options)
    
    st.info("Esta seção está em desenvolvimento e será implementada nas próximas atualizações.")
    
    # Rodapé
    st.markdown("---")
    st.markdown("*Desenvolvimento em andamento. Última atualização: Agosto 2024*") 