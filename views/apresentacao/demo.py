import streamlit as st
from views.apresentacao import show_apresentacao

def main():
    """
    Demonstração do uso do módulo de apresentação modular
    """
    st.title("Demonstração da Apresentação Modular")
    
    st.write("""
    Este é um exemplo de como usar o novo módulo de apresentação modular 
    que substituiu o arquivo `apresentacao_conclusoes.py` original.
    """)
    
    st.info("""
    A nova implementação é mais fácil de manter, com cada componente separado
    em seu próprio arquivo, facilitando a adição de novos slides ou funcionalidades.
    """)
    
    # Botão para iniciar a apresentação
    if st.button("Iniciar Apresentação", type="primary"):
        show_apresentacao(slide_inicial=0)
    
    # Parâmetros adicionais
    st.subheader("Opções Avançadas")
    
    slide_inicial = st.number_input(
        "Slide Inicial", 
        min_value=0, 
        max_value=11, 
        value=0, 
        help="Número do slide para iniciar a apresentação"
    )
    
    modo_config = st.checkbox(
        "Modo de Configuração", 
        value=False,
        help="Ativa o modo de configuração que permite ajustar parâmetros"
    )
    
    # Botão para iniciar com opções avançadas
    if st.button("Iniciar com Opções Avançadas"):
        # Definir parâmetros na sessão
        st.session_state.modo_config = modo_config
        
        # Iniciar apresentação
        show_apresentacao(slide_inicial=slide_inicial)
    
    # Informações sobre os slides
    st.subheader("Módulos Disponíveis")
    
    st.markdown("""
    | Índice | Módulo | Descrição |
    | ------ | ------ | --------- |
    | 0-5    | Conclusões | Métricas e análises de conclusões |
    | 6-8    | Produção | Métricas e status de produção |
    | 9-11   | Cartório | Análises de cartório e famílias |
    """)
    
    st.caption("© 2024 - Implementação modular otimizada para visualização em tela 9:16")

if __name__ == "__main__":
    main() 