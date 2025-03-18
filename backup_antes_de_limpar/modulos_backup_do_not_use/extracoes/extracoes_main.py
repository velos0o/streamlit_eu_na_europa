import streamlit as st

def show_extracoes():
    """
    Exibe a página principal de Extrações de Dados
    """
    st.title("Extrações de Dados")
    st.markdown("---")
    
    st.markdown("""
    ## Visualização e Exportação de Dados
    
    Esta seção do dashboard permite a visualização e exportação de dados do Bitrix24 para análises específicas.
    
    ### Submódulos Planejados:
    
    1. **Extrator de Processos**: Exportação de dados de processos em formato CSV/Excel
    2. **Consulta Personalizada**: Criação de consultas personalizadas
    3. **Histórico de Alterações**: Visualização do histórico de alterações
    4. **Relatórios Periódicos**: Agendamento de relatórios automáticos
    
    Seleções futuras estarão disponíveis aqui.
    """)
    
    # Menu para os submódulos (a ser implementado)
    menu_options = ["Aguardando Implementação"]
    selected = st.selectbox("Selecione uma opção:", menu_options)
    
    st.info("Esta seção está em desenvolvimento e será implementada nas próximas atualizações.")
    
    # Rodapé
    st.markdown("---")
    st.markdown("*Desenvolvimento em andamento. Última atualização: Agosto 2024*") 