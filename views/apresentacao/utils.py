import streamlit as st

def hide_streamlit_elements():
    """
    Oculta elementos padrão do Streamlit para o modo apresentação
    """
    # Ocultar elementos padrão do Streamlit
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    .viewerBadge_container__1QSob {display: none;}

    /* Remover margens e padding */
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
        padding-left: 0;
        padding-right: 0;
        margin: 0;
    }
    
    /* Remover espaçamento excessivo */
    .stHeader {
        display: none;
    }
    
    /* Ocultar elementos de menu e debug */
    section[data-testid="stSidebar"] {
        display: none;
    }
    
    /* Remover linhas de separação entre elementos */
    hr {
        display: none;
    }
    
    /* Ajustar espaço do título principal */
    h1 {
        margin-top: 0 !important;
    }
    
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
        padding: 0 !important;
    }
    
    /* Remover padding/margin para otimizar espaço vertical */
    div[data-testid="stAppViewContainer"] > div:not([data-testid]) {
        margin: 0;
        padding: 0;
    }
    </style>
    """, unsafe_allow_html=True)

def check_id_pattern(id_str):
    """
    Verifica se uma string segue o padrão de ID de família
    
    Args:
        id_str (str): String a ser verificada
        
    Returns:
        bool: True se segue o padrão, False caso contrário
    """
    try:
        # Verificar se é uma string
        if not isinstance(id_str, str):
            return False
        
        # Remover espaços
        id_str = id_str.strip()
        
        # Verificar se tem tamanho adequado
        if len(id_str) < 3:
            return False
        
        # Verificar se inicia com letra
        if not id_str[0].isalpha():
            return False
        
        # Verificar se os demais caracteres são dígitos
        if not id_str[1:].isdigit():
            return False
        
        return True
    except Exception:
        return False
