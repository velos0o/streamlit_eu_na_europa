import streamlit as st

# Configuração da página - DEVE vir primeiro
st.set_page_config(
    page_title="Dashboard CRM Bitrix24",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para verificar se o streamlit está em modo execução
def is_streamlit_running():
    try:
        # Testa se o session_state está disponível
        test = st.session_state
        return True
    except:
        return False

# Só inicializa session_state se o Streamlit estiver rodando
if is_streamlit_running():
    # Inicializar estado da sessão de forma segura
    if 'pagina_atual' not in st.session_state:
        st.session_state['pagina_atual'] = 'Ficha da Família'

# Resto do código apenas depois das verificações
st.title("Dashboard CRM Bitrix24")
st.write("Aplicação funcionando corretamente!")

if is_streamlit_running():
    st.write(f"Página atual: {st.session_state.get('pagina_atual', 'Não definida')}")
else:
    st.write("Session state não disponível - modo de desenvolvimento") 