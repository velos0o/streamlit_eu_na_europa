# Arquivo para centralizar estilos e temas

import streamlit as st

# Definir cores Tailwind CSS para tema claro e escuro
THEME = {
    "light": {
        "primary": "#3B82F6",          # blue-500
        "secondary": "#6366F1",        # indigo-500
        "accent": "#F59E0B",           # amber-500
        "background": "#F9FAFB",       # gray-50
        "card_bg": "#FFFFFF",          # Fundo do card claro
        "input_bg": "#FFFFFF",         # Fundo do input claro
        "text": "#1F2937",             # gray-800
        "subtle_text": "#6B7280",      # gray-500
        "border": "#E5E7EB",           # gray-200
        "success": "#10B981",          # emerald-500
        "warning": "#F59E0B",          # amber-500 
        "error": "#EF4444",            # red-500
        "info": "#3B82F6",             # blue-500
        "sidebar_bg": "#FFFFFF",       # Fundo da sidebar claro
        "sidebar_text": "#374151",    # Texto da sidebar claro
    },
    "dark": {
        "primary": "#60A5FA",          # blue-400
        "secondary": "#818CF8",        # indigo-400
        "accent": "#FBBF24",           # amber-400
        "background": "#111827",       # gray-900
        "card_bg": "#1F2937",          # Fundo do card escuro (gray-800)
        "input_bg": "#374151",         # Fundo do input escuro (gray-700)
        "text": "#F9FAFB",             # gray-50
        "subtle_text": "#9CA3AF",      # gray-400
        "border": "#374151",           # gray-700
        "success": "#34D399",          # emerald-400
        "warning": "#FBBF24",          # amber-400
        "error": "#F87171",            # red-400
        "info": "#60A5FA",             # blue-400
        "sidebar_bg": "#1F2937",       # Fundo da sidebar escuro (gray-800)
        "sidebar_text": "#D1D5DB",    # Texto da sidebar escuro (gray-300)
    }
}

# Função para criar containers no estilo Tailwind usando componentes nativos do Streamlit
def tailwind_container(container_type="default"):
    """
    Cria um container estilizado com Tailwind CSS usando componentes nativos do Streamlit
    
    Args:
        container_type: Tipo de container (default, info, success, warning, error)
    
    Returns:
        Um objeto container do Streamlit com estilo do Tailwind
    """
    # Determinar o tema com base no session_state
    theme_mode = "dark" if st.session_state.get("dark_mode", False) else "light"
    theme = THEME[theme_mode]
    
    # Mapear tipos para cores
    color_map = {
        "default": theme["primary"],
        "info": theme["info"],
        "success": theme["success"],
        "warning": theme["warning"],
        "error": theme["error"],
        "secondary": theme["secondary"]
    }
    
    border_color = color_map.get(container_type, theme["primary"])
    
    # Criar CSS para o container (Expander)
    container_css = f"""
    <style>
    /* Estilo para o container do Expander */
    div[data-testid="stExpander"] > details {{
        border-left: 4px solid {border_color} !important;
        border-radius: 0.375rem !important; 
        background-color: {theme.get("card_bg", theme["background"]) } !important; /* Usa card_bg */
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
        overflow: hidden; 
    }}
    /* Estilo para o cabeçalho do Expander */
    div[data-testid="stExpander"] > details > summary {{
        color: {border_color} !important;
        font-weight: 600;
        background-color: transparent !important; /* Fundo do summary transparente */
        border-bottom: none !important; 
        padding: 0.75rem 1rem; 
    }}
    /* Remove o ícone de seta padrão se desejar substituir por um ícone CSS */
    div[data-testid="stExpander"] > details > summary::before {{
        display: none; 
    }}
    /* Estilo para o conteúdo dentro do Expander */
    div[data-testid="stExpander"] > details > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {{
        padding: 1rem; 
        background-color: {theme.get("card_bg", theme["background"])} !important; /* Usa card_bg */
        border-top: 1px solid {theme.get("border", "#EEEEEE")} !important; /* Linha separadora sutil */
    }}
    /* Força cor de texto dentro do expander */
    div[data-testid="stExpander"] > details > div * {{
        color: {theme["text"]} !important;
    }}
    </style>
    """
    
    st.markdown(container_css, unsafe_allow_html=True)
    
    # Retorna st para encadear chamadas (ex: tw.expander(...))
    return st

# Adicionar CSS global para o tema claro e escuro inspirado no Tailwind
def apply_tailwind_styles():
    """Aplica estilos globais inspirados no Tailwind CSS para a página."""
    # Determinar o tema com base no session_state
    theme_mode = "dark" if st.session_state.get("dark_mode", False) else "light"
    theme = THEME[theme_mode]
    
    # Gerar CSS baseado no tema
    css = f"""
    <style>
    /* ===== ESTILOS GLOBAIS BASE ===== */
    body {{
        background-color: {theme["background"]} !important;
        color: {theme["text"]} !important;
    }}
    .stApp {{
        background-color: {theme["background"]} !important;
        color: {theme["text"]} !important; 
    }}
    /* Cor do texto padrão (assegurar herança) */
    div, p, span, li, label {{
        color: inherit !important; 
    }}
    
    /* Cabeçalhos */
    h1, h2, h3 {{
        color: {theme["primary"]} !important;
        font-weight: 600 !important;
    }}
    h1 {{
        font-size: 2.25rem !important; line-height: 2.5rem !important;
        margin-bottom: 1.5rem !important; border-bottom: 2px solid {theme.get("border", "#EEEEEE")} !important; padding-bottom: 0.5rem !important;
    }}
    h2 {{
        font-size: 1.5rem !important; line-height: 2rem !important;
        margin-top: 1.5rem !important; margin-bottom: 1rem !important;
    }}
    h3 {{
        font-size: 1.25rem !important; line-height: 1.75rem !important;
        margin-top: 1rem !important; margin-bottom: 0.75rem !important;
        color: {theme.get("subtle_text", theme["text"]) } !important; /* Subheaders um pouco mais sutis */
    }}

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {{
        background-color: {theme.get("sidebar_bg", theme["background"])};
        border-right: 1px solid {theme.get("border", "#EEEEEE")} !important; /* Borda sutil */
    }}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
         gap: 0.5rem; 
    }}
    /* Texto geral na sidebar */
    [data-testid="stSidebar"] * {{
        color: {theme.get("sidebar_text", theme["text"])}; 
    }}
    /* Cabeçalhos na Sidebar */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4 {{
        color: {theme.get("sidebar_text", theme["text"])}; 
        opacity: 0.9;
    }}
     /* Ajuste específico para st.title e st.header na sidebar */
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h2 {{
         color: {theme.get("sidebar_text", theme["text"])}; 
         font-weight: 700;
         margin-bottom: 0.5rem;
    }}
     [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h3 {{
         color: {theme.get("sidebar_text", theme["text"])}; 
         font-weight: 600;
         opacity: 0.8;
         font-size: 1rem !important;
         margin-top: 1rem;
         margin-bottom: 0.25rem;
    }}
    /* Botões na Sidebar */
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:not(:disabled) {{
        background-color: {theme["primary"]} !important;
        color: white !important;
        border-color: {theme["primary"]} !important;
    }}
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"]:not(:disabled) {{
        background-color: {theme.get("sidebar_bg", theme["background"])} !important;
        color: {theme["primary"]} !important;
        border: 1px solid {theme["primary"]}50 !important;
    }}
     [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"]:not(:disabled):hover {{
        background-color: {theme["primary"]}10 !important;
        border-color: {theme["primary"]} !important;
        color: {theme["secondary"]} !important;
    }}

    /* ===== COMPONENTES STREAMLIT (Conteúdo Principal) ===== */

    /* Inputs e Text Area */
    .stTextInput > div > div > input,
    .stTextArea > div > textarea,
    .stNumberInput > div > div > input {{
        background-color: {theme.get("input_bg", theme["background"]) } !important;
        color: {theme["text"]} !important;
        border: 1px solid {theme.get("border", "#EEEEEE")} !important;
        border-radius: 0.375rem !important;
        transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > textarea:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: {theme["primary"]} !important;
        box-shadow: 0 0 0 2px {theme["primary"]}30 !important;
    }}
    .stTextInput > label,
    .stTextArea > label,
    .stNumberInput > label {{
        color: {theme.get("subtle_text", theme["text"])} !important;
        font-size: 0.875rem; /* Label um pouco menor */
    }}

    /* Selectbox e Multiselect */
    .stSelectbox > div[data-baseweb="select"] > div,
    .stMultiSelect > div[data-baseweb="select"] > div {{
        background-color: {theme.get("input_bg", theme["background"]) } !important;
        border: 1px solid {theme.get("border", "#EEEEEE")} !important;
        border-radius: 0.375rem !important;
        color: {theme["text"]} !important;
    }}
    /* Indicador de dropdown */
    .stSelectbox div[data-baseweb="select"] svg,
    .stMultiSelect div[data-baseweb="select"] svg {{
        fill: {theme.get("subtle_text", theme["text"]) } !important;
    }}
    /* Cor do texto dentro do select/multiselect */
    .stSelectbox div[data-baseweb="select"] [data-baseweb="tag"],
    .stMultiSelect div[data-baseweb="select"] [data-baseweb="tag"],
    .stSelectbox div[data-baseweb="select"] div[class*="placeholder"],
    .stSelectbox div[data-baseweb="select"] span[class*="singleValue"],
    .stMultiSelect div[data-baseweb="select"] div[class*="placeholder"],
    .stMultiSelect div[data-baseweb="select"] input {{
        color: {theme["text"]} !important;
    }}
    /* Tags selecionadas no Multiselect */
     .stMultiSelect span[data-baseweb="tag"] {{
         background-color: {theme["primary"]}20 !important; 
         border: 1px solid {theme["primary"]}30 !important;
         padding: 0.1rem 0.4rem;
         border-radius: 0.25rem;
         color: {theme["text"]} !important;
         margin: 0.1rem;
     }}
     .stMultiSelect span[data-baseweb="tag"] > span {{ /* Texto dentro da tag */
         color: {theme["text"]} !important; 
     }}
     .stMultiSelect span[data-baseweb="tag"] > div[role="button"] svg {{ /* Ícone 'x' na tag */
         fill: {theme["text"]} !important; 
         opacity: 0.7;
     }}
    .stSelectbox > label,
    .stMultiSelect > label {{
        color: {theme.get("subtle_text", theme["text"]) } !important;
        font-size: 0.875rem;
    }}
    /* Dropdown do Select/Multiselect */
    div[data-baseweb="popover"] ul[role="listbox"] {{
        background-color: {theme.get("card_bg", theme["background"]) } !important; /* Usa card_bg */
        border: 1px solid {theme.get("border", "#EEEEEE")} !important;
        border-radius: 0.375rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    div[data-baseweb="popover"] ul[role="listbox"] li {{
        color: {theme["text"]} !important;
        transition: background-color 0.2s ease;
        padding: 0.5rem 0.75rem;
    }}
    div[data-baseweb="popover"] ul[role="listbox"] li:hover,
    div[data-baseweb="popover"] ul[role="listbox"] li[aria-selected="true"] {{
        background-color: {theme["primary"]}20 !important;
    }}

    /* Botões (Conteúdo Principal) */
    div[data-testid="stButton"]:not([data-testid="stSidebar"] div[data-testid="stButton"]) > button:not(:disabled) {{
        transition: all 0.3s ease;
        border-radius: 0.375rem; 
        padding: 0.5rem 1rem; 
        font-weight: 500;
    }}
    /* Botão Primário */
    div[data-testid="stButton"]:not([data-testid="stSidebar"] div[data-testid="stButton"]) > button[kind="primary"]:not(:disabled) {{
        background-color: {theme["primary"]};
        color: white; 
        border: 1px solid {theme["primary"]};
    }}
    div[data-testid="stButton"]:not([data-testid="stSidebar"] div[data-testid="stButton"]) > button[kind="primary"]:not(:disabled):hover {{
        background-color: {theme["secondary"]};
        border-color: {theme["secondary"]};
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }}
    /* Botão Secundário */
    div[data-testid="stButton"]:not([data-testid="stSidebar"] div[data-testid="stButton"]) > button[kind="secondary"]:not(:disabled) {{
        background-color: {theme.get("input_bg", theme["background"]) };
        color: {theme["primary"]};
        border: 1px solid {theme.get("border", "#EEEEEE")};
    }}
    div[data-testid="stButton"]:not([data-testid="stSidebar"] div[data-testid="stButton"]) > button[kind="secondary"]:not(:disabled):hover {{
        background-color: {theme["primary"]}10; 
        border-color: {theme["primary"]}50;
        color: {theme["secondary"]};
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }}

    /* Dataframe */
    .dataframe {{
        color: {theme["text"]} !important;
        background-color: {theme.get("card_bg", theme["background"]) } !important; 
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border-radius: 0.5rem !important;
        overflow: hidden !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid {theme.get("border", "#EEEEEE")} !important;
    }}
    .dataframe th {{
        background-color: {theme.get("card_bg", theme["background"]) } !important;
        color: {theme.get("subtle_text", theme["text"]) } !important; 
        padding: 0.75rem 1rem !important;
        text-align: left !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important; /* Header menor */
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        border-bottom: 2px solid {theme.get("border", "#EEEEEE")} !important;
    }}
    .dataframe td {{
        background-color: {theme.get("card_bg", theme["background"]) } !important; 
        color: {theme["text"]} !important;
        padding: 0.75rem 1rem !important;
        border-top: 1px solid {theme.get("border", "#EEEEEE")} !important;
        transition: background-color 0.2s !important;
    }}
    .dataframe tr:hover td {{
        background-color: {theme["primary"]}10 !important;
    }}

    /* Metric */
    [data-testid="stMetric"] {{
        background-color: {theme.get("card_bg", theme["background"]) };
        border: 1px solid {theme.get("border", "#EEEEEE")};
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    [data-testid="stMetricValue"] {{
        color: {theme["primary"]} !important;
        font-size: 1.75rem !important; /* Leve redução */
    }}
    [data-testid="stMetricLabel"] {{
        color: {theme.get("subtle_text", theme["text"]) } !important;
        font-size: 0.875rem !important;
        opacity: 1;
    }}
    [data-testid="stMetricDelta"] > div {{
        color: inherit !important; 
        font-size: 0.875rem !important;
    }}
    
    /* Expander (estilo base movido para tailwind_container) */
    /* Garantir cor de texto dentro do expander */
    div[data-testid="stExpander"] > details > div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"],
    div[data-testid="stExpander"] > details > div[data-testid="stVerticalBlock"] div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stExpander"] > details > div[data-testid="stVerticalBlock"] div[data-testid="stMarkdownContainer"] li {{
         color: {theme["text"]} !important;
    }}
    
    /* Checkbox e Radio */
    .stCheckbox > label, .stRadio > label {{
        color: {theme["text"]} !important;
    }}
    .stCheckbox input[type="checkbox"], .stRadio input[type="radio"] {{
        filter: brightness(90%) contrast(110%); 
    }}

    /* Alertas (st.info, st.warning, etc.) */
    .stAlert {{
        border-radius: 0.375rem !important;
        border-left-width: 4px !important;
        padding: 0.75rem 1rem !important;
        color: inherit !important; 
    }}
    .stAlert * {{ /* Força cor do texto herdada para filhos */
         color: inherit !important; 
    }}
    .stAlert[data-baseweb="alert"][kind="info"] {{
        background-color: {theme["info"]}15 !important;
        border-left-color: {theme["info"]} !important;
        color: {theme["info"]}dd !important;
    }}
    .stAlert[data-baseweb="alert"][kind="success"] {{
        background-color: {theme["success"]}15 !important;
        border-left-color: {theme["success"]} !important;
        color: {theme["success"]}dd !important;
    }}
    .stAlert[data-baseweb="alert"][kind="warning"] {{
        background-color: {theme["warning"]}15 !important;
        border-left-color: {theme["warning"]} !important;
        color: {theme["warning"]}dd !important;
    }}
    .stAlert[data-baseweb="alert"][kind="error"] {{
        background-color: {theme["error"]}15 !important;
        border-left-color: {theme["error"]} !important;
        color: {theme["error"]}dd !important;
    }}

    /* ===== CLASSES CUSTOMIZADAS (Tailwind-like) ===== */

    .tw-heading {{
        color: {theme["primary"]};
        font-weight: 600;
        margin-bottom: 1rem;
        position: relative;
        display: inline-block;
    }}
    .tw-heading::after {{
        content: ''; position: absolute; bottom: -5px; left: 0;
        width: 40%; height: 3px; background: linear-gradient(90deg, {theme["primary"]}, transparent);
    }}
    
    .tw-card {{
        background-color: {theme.get("card_bg", theme["background"]) };
        border-radius: 0.5rem; padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 1rem; border: 1px solid {theme.get("border", "#EEEEEE")};
        transition: transform 0.2s, box-shadow 0.2s;
        color: {theme["text"]} !important; 
    }}
    /* Cor do texto dentro do card customizado */
    .tw-card > div, .tw-card > h3, .tw-card p, .tw-card span, .tw-card li {{
        color: {theme["text"]} !important;
    }}
    .tw-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }}
    .tw-card-primary {{ border-left: 4px solid {theme["primary"]}; }}
    .tw-card-secondary {{ border-left: 4px solid {theme["secondary"]}; }}
    .tw-card-success {{ border-left: 4px solid {theme["success"]}; }}
    .tw-card-error {{ border-left: 4px solid {theme["error"]}; }}
    
    .tw-badge {{
        display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px;
        font-size: 0.75rem; font-weight: 500; text-transform: uppercase;
        letter-spacing: 0.05em; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .tw-badge:hover {{ transform: scale(1.05); box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }}
    .tw-badge-primary {{ background-color: {theme["primary"]}20; color: {theme["primary"]}; border: 1px solid {theme["primary"]}30; }}
    .tw-badge-success {{ background-color: {theme["success"]}20; color: {theme["success"]}; border: 1px solid {theme["success"]}30; }}
    .tw-badge-warning {{ background-color: {theme["warning"]}20; color: {'#A15C07' if theme_mode == 'dark' else theme["warning"]}; border: 1px solid {theme["warning"]}30; }}
    .tw-badge-error {{ background-color: {theme["error"]}20; color: {theme["error"]}; border: 1px solid {theme["error"]}30; }}
    .tw-badge-info {{ background-color: {theme["info"]}20; color: {theme["info"]}; border: 1px solid {theme["info"]}30; }}

    .tw-divider {{
        height: 1px; width: 100%;
        background: linear-gradient(90deg, {theme["primary"]}10, {theme["primary"]}40, {theme["primary"]}10);
        margin: 1.5rem 0;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .tw-fade-in {{ animation: fadeIn 0.5s ease-out forwards; }}
    
    .tw-tooltip {{ position: relative; display: inline-block; }}
    .tw-tooltip::after {{
        content: attr(data-tooltip); position: absolute; bottom: 125%; left: 50%;
        transform: translateX(-50%); background-color: {theme["secondary"]}; color: white;
        text-align: center; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;
        white-space: nowrap; opacity: 0; visibility: hidden;
        transition: opacity 0.3s, visibility 0.3s; z-index: 1000;
    }}
    .tw-tooltip:hover::after {{ opacity: 1; visibility: visible; }}
    
    /* ===== AJUSTES ESPECÍFICOS TEMA ESCURO (Sobrescritas) ===== */
    {f'''
    /* Estilo específico para tema escuro para garantir cobertura */
    body, .stApp {{
        background-color: {theme["background"]} !important;
        color: {theme["text"]} !important;
    }}
    div, p, span, li, label {{
        color: inherit !important; 
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {theme["primary"]} !important; 
    }}
    h3 {{
         color: {theme.get("subtle_text", theme["text"]) } !important;
    }}
    
    /* Sidebar Escura */
    [data-testid="stSidebar"] {{
        background-color: {theme.get("sidebar_bg", theme["background"])};
        border-right: 1px solid {theme.get("border", "#EEEEEE")} !important;
    }}
     [data-testid="stSidebar"] * {{
        color: {theme.get("sidebar_text", theme["text"])}; 
    }}
     [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {{
        color: {theme.get("sidebar_text", theme["text"])}; 
        opacity: 0.9;
    }}
     [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] h3 {{
         color: {theme.get("sidebar_text", theme["text"])}; 
         font-weight: 600;
         opacity: 0.8;
         font-size: 1rem !important;
         margin-top: 1rem;
         margin-bottom: 0.25rem;
    }}
     [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:not(:disabled) {{
        background-color: {theme["primary"]} !important;
        color: white !important;
        border-color: {theme["primary"]} !important;
    }}
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"]:not(:disabled) {{
        background-color: {theme.get("sidebar_bg", theme["background"])} !important;
        color: {theme["primary"]} !important;
        border: 1px solid {theme["primary"]}50 !important;
    }}
     [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"]:not(:disabled):hover {{
        background-color: {theme["primary"]}10 !important;
        border-color: {theme["primary"]} !important;
        color: {theme["secondary"]} !important;
    }}

    /* Inputs mais escuros */
    .stTextInput > div > div > input,
    .stTextArea > div > textarea,
    .stNumberInput > div > div > input {{
        background-color: {theme.get("input_bg", theme["background"]) } !important; 
        color: {theme["text"]} !important;
        border: 1px solid {theme.get("border", "#EEEEEE")} !important; 
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > textarea:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: {theme["primary"]} !important;
        box-shadow: 0 0 0 2px {theme["primary"]}30 !important;
    }}
     .stTextInput > label,
    .stTextArea > label,
    .stNumberInput > label {{
        color: {theme.get("subtle_text", theme["text"]) } !important;
    }}
    
    /* Selects/Multiselects mais escuros */
    .stSelectbox > div[data-baseweb="select"] > div,
    .stMultiSelect > div[data-baseweb="select"] > div {{
        background-color: {theme.get("input_bg", theme["background"]) } !important;
        border: 1px solid {theme.get("border", "#EEEEEE")} !important;
        color: {theme["text"]} !important;
    }}
    .stSelectbox div[data-baseweb="select"] [data-baseweb="tag"],
    .stMultiSelect div[data-baseweb="select"] [data-baseweb="tag"],
    .stSelectbox div[data-baseweb="select"] div[class*="placeholder"],
    .stSelectbox div[data-baseweb="select"] span[class*="singleValue"],
    .stMultiSelect div[data-baseweb="select"] div[class*="placeholder"],
    .stMultiSelect div[data-baseweb="select"] input {{
        color: {theme["text"]} !important; 
    }}
     .stSelectbox div[data-baseweb="select"] svg,
    .stMultiSelect div[data-baseweb="select"] svg {{
        fill: {theme.get("subtle_text", theme["text"]) } !important;
    }}
    .stMultiSelect span[data-baseweb="tag"] {{
         background-color: {theme["secondary"]}30 !important; 
         border: 1px solid {theme["secondary"]}50 !important;
         color: {theme["text"]} !important;
     }}
     .stMultiSelect span[data-baseweb="tag"] > span {{
         color: {theme["text"]} !important; 
     }}
     .stMultiSelect span[data-baseweb="tag"] > div[role="button"] svg {{
         fill: {theme["text"]} !important; 
         opacity: 0.7;
     }}
     .stSelectbox > label,
    .stMultiSelect > label {{
        color: {theme.get("subtle_text", theme["text"]) } !important;
    }}
    div[data-baseweb="popover"] ul[role="listbox"] {{
        background-color: {theme.get("card_bg", theme["background"]) } !important;
        border: 1px solid {theme.get("border", "#EEEEEE")} !important;
    }}
    div[data-baseweb="popover"] ul[role="listbox"] li:hover,
    div[data-baseweb="popover"] ul[role="listbox"] li[aria-selected="true"] {{
        background-color: {theme["primary"]}30 !important;
    }}

    /* Dataframe Escuro */
    .dataframe {{
        background-color: {theme.get("card_bg", theme["background"]) } !important;
        border: 1px solid {theme.get("border", "#EEEEEE")} !important;
    }}
    .dataframe th {{
        background-color: {theme.get("card_bg", theme["background"]) } !important;
        color: {theme.get("subtle_text", theme["text"]) } !important; 
        border-bottom: 2px solid {theme.get("border", "#EEEEEE")} !important;
    }}
    .dataframe td {{
        background-color: {theme.get("card_bg", theme["background"]) } !important;
        color: {theme["text"]} !important;
        border-top: 1px solid {theme.get("border", "#EEEEEE")} !important;
    }}
    .dataframe tr:hover td {{
        background-color: {theme["primary"]}20 !important;
    }}
    
    /* Metric Escuro */
    [data-testid="stMetric"] {{
        background-color: {theme.get("card_bg", theme["background"]) } !important;
        border: 1px solid {theme.get("border", "#EEEEEE")} !important;
    }}
    [data-testid="stMetricValue"] {{ color: {theme["primary"]} !important; }}
    [data-testid="stMetricLabel"] {{ color: {theme.get("subtle_text", theme["text"]) } !important; opacity: 1;}}
    [data-testid="stMetricDelta"] > div {{ color: inherit !important; }}
    
    /* Expander Escuro */
    div[data-testid="stExpander"] > details,
    div[data-testid="stExpander"] > details > summary,
    div[data-testid="stExpander"] > details > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {{
        background-color: {theme.get("card_bg", theme["background"]) } !important;
        border-color: {theme.get("border", "#EEEEEE")} !important; /* Garante borda escura */
    }}
    div[data-testid="stExpander"] > details > div * {{ 
        color: {theme["text"]} !important;
    }}
    div[data-testid="stExpander"] > details > summary {{ 
        color: {theme["secondary"]} !important; 
        border-bottom: 1px solid {theme.get("border", "#EEEEEE")} !important; /* Separador para summary */
    }}
    div[data-testid="stExpander"] > details {{
        border-left-color: {theme["secondary"]} !important;
    }}
    
    /* Alertas Escuros */
    .stAlert[data-baseweb="alert"] {{
         color: inherit !important;
         border-radius: 0.375rem !important;
         border-left-width: 4px !important;
         padding: 0.75rem 1rem !important;
    }}
    .stAlert[data-baseweb="alert"] * {{ color: inherit !important; }}

    .stAlert[data-baseweb="alert"][kind="info"] {{
        background-color: {theme["info"]}20 !important;
        border-left-color: {theme["info"]} !important;
        color: {theme["info"]} !important;
    }}
    .stAlert[data-baseweb="alert"][kind="success"] {{
        background-color: {theme["success"]}20 !important;
        border-left-color: {theme["success"]} !important;
        color: {theme["success"]} !important;
    }}
    .stAlert[data-baseweb="alert"][kind="warning"] {{
        background-color: {theme["warning"]}20 !important;
        border-left-color: {theme["warning"]} !important;
        color: {theme["warning"]} !important;
    }}
    .stAlert[data-baseweb="alert"][kind="error"] {{
        background-color: {theme["error"]}20 !important;
        border-left-color: {theme["error"]} !important;
        color: {theme["error"]} !important;
    }}

    /* Card customizado no escuro */
    .tw-card {{
        background-color: {theme.get("card_bg", theme["background"]) } !important;
        border: 1px solid {theme.get("border", "#EEEEEE")} !important;
        color: {theme["text"]} !important;
    }}
    .tw-card > div, .tw-card > h3, .tw-card p, .tw-card span, .tw-card li {{
        color: {theme["text"]} !important;
    }}
    
    ''' if theme_mode == "dark" else ''}

    </style>
    """
    
    # Aplicar o CSS
    st.markdown(css, unsafe_allow_html=True) 