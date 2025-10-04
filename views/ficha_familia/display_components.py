"""
Componentes de exibição visual para Ficha da Família
"""
import streamlit as st
import html


def inject_all_ficha_css():
    """
    Injeta TODO o CSS necessário para a Ficha da Família de uma vez.
    Chame esta função no INÍCIO da página para garantir que o CSS sempre carregue.
    """
    css_completo = """
    <style>
    /* === ALERTAS FLUTUANTES === */
    @keyframes ficha-alert-pulse {
      0% { transform: translateY(0); box-shadow: 0 18px 34px rgba(16,33,61,0.20); }
      50% { transform: translateY(-3px); box-shadow: 0 24px 42px rgba(16,33,61,0.28); }
      100% { transform: translateY(0); box-shadow: 0 18px 34px rgba(16,33,61,0.20); }
    }
    .ficha-alert-base {
       position: fixed; right: 24px; width: 260px; min-height: 120px;
       border-radius: 16px; display: flex; align-items: center; gap: 12px;
       padding: 18px 22px; border: 1px solid var(--alert-border, rgba(0,0,0,0.25));
       background: var(--alert-bg, #FFC107); color: var(--alert-color, #1c1c1c);
       box-shadow: 0 14px 28px rgba(16,33,61,0.20); opacity: 0.99; z-index: 9999;
    }
    .ficha-alert-base.no-icon { padding-left: 26px; }
    .ficha-alert-text { display: flex; flex-direction: column; gap: 6px; }
    .ficha-alert-title {
       font-weight: 800; letter-spacing: 0.045em; text-transform: uppercase;
       font-size: 1rem; line-height: 1.3;
    }
    .ficha-alert-subtitle {
       font-size: 0.9rem; line-height: 1.45; font-weight: 600; opacity: 0.98;
    }
    
    /* === MAPA INICIAL === */
    @keyframes pulse-border {
      0% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.8); }
      70% { box-shadow: 0 0 0 12px rgba(255, 193, 7, 0); }
      100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
    }
    .mapa-inicial-notification {
      position: fixed; top: 65px; right: 0; width: 150px; height: 150px;
      background-color: #FFC107; color: #1c1c1c; border-radius: 8px 0 0 8px;
      display: flex; justify-content: center; align-items: center;
      font-weight: bold; font-size: 1.1em; text-align: center; z-index: 9999;
      box-shadow: 0 4px 12px rgba(0,0,0,0.25); animation: pulse-border 2s infinite;
      padding: 10px; border: 2px solid #FFA000; border-right: none;
    }
    
    /* === TABELA DE EMISSÕES - DESIGN MINIMALISTA === */
    .cert-status-wrapper {
        display: flex; flex-direction: column; gap: 8px;
    }
    .cert-status-wrapper.duplicado {
        position: relative; border-left: 2px solid #E0E0E0; padding-left: 12px;
    }
    .cert-status-wrapper.duplicado::before {
        content: "Duplicado"; position: absolute; top: -8px; left: 0;
        transform: translate(-6px, -50%);
        background: #F5F5F5; color: #666;
        font-size: 0.65rem; font-weight: 600;
        letter-spacing: 0.03em; padding: 2px 8px;
        border-radius: 4px; border: 1px solid #E0E0E0;
        text-transform: uppercase;
    }
    .cert-card {
        background: #FAFAFA; border: 1px solid #E0E0E0;
        border-radius: 4px; padding: 10px 12px;
        display: flex; flex-direction: column; gap: 6px; text-align: left;
        box-shadow: none;
    }
    .cert-card.default-status {
        background: #F9F9F9; border: 1px dashed #D0D0D0;
        color: #666;
    }
    .cert-card-header {
        display: flex; align-items: flex-start; justify-content: space-between; gap: 8px;
    }
    .cert-status-title {
        font-size: 0.85rem; font-weight: 600; color: #333; line-height: 1.3;
    }
    .cert-status-meta {
        display: flex; flex-wrap: wrap; gap: 4px; align-items: center;
    }
    .cert-chip {
        background: #F0F0F0; color: #555;
        font-size: 0.65rem; font-weight: 500; padding: 2px 8px;
        border-radius: 3px; text-transform: uppercase; letter-spacing: 0.03em;
        display: inline-flex; align-items: center; gap: 4px;
        border: 1px solid #E0E0E0;
    }
    .cert-note {
        font-size: 0.75rem; color: #777; line-height: 1.3;
    }
    .cert-status-links {
        display: flex; flex-wrap: wrap; gap: 6px;
    }
    .cert-link-button {
        display: inline-flex; align-items: center; gap: 3px;
        padding: 3px 8px; border-radius: 3px; text-decoration: none;
        background: #FFF; border: 1px solid #D0D0D0;
        color: #555 !important; font-size: 0.7rem; font-weight: 500;
        transition: all 0.15s ease;
    }
    .cert-link-button:hover {
        background-color: #F5F5F5; border-color: #999;
        color: #333 !important;
    }
    .cert-link-icon { font-size: 0.8em; line-height: 1; }
    .ficha-download-bar {
        display: flex; justify-content: flex-start; align-items: center;
        gap: 10px; margin: 10px 0 6px 0;
    }
    
    /* === LARGURA COMPLETA === */
    .ficha-familia-container {
        width: 100% !important; max-width: 100% !important;
        box-sizing: border-box !important; padding: 20px !important;
    }
    div[data-testid="stMarkdownContainer"] {
        width: 100% !important; max-width: 100% !important; flex: 0 1 100% !important;
    }
    
    /* === PÁGINA DE BUSCA === */
    .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .search-results-table {
        width: 100%; border-collapse: collapse;
        margin-bottom: 15px; font-size: 14px;
    }
    .search-results-table th {
        background-color: #f0f0f0; padding: 8px 12px;
        text-align: left; border: 1px solid #ddd; font-weight: 600;
    }
    .search-results-table td {
        padding: 8px 12px; border: 1px solid #ddd; vertical-align: top;
    }
    .search-results-table tr:hover {
        background-color: #f9f9f9; cursor: pointer;
    }
    .search-results-table tr.selected { background-color: #e0f0ff; }
    .results-count {
        font-size: 0.9em; color: #555;
        margin-bottom: 10px; font-style: italic;
    }
    </style>
    """
    st.markdown(css_completo, unsafe_allow_html=True)


def render_alert_box(titulo_texto, subtitulo_texto, background_color, border_color, text_color, top_position):
    """Renderiza caixa de alerta flutuante"""
    # CSS é injetado sempre para garantir que carregue
    alert_css_base = """
    <style>
    @keyframes ficha-alert-pulse {
      0% {
        transform: translateY(0);
        box-shadow: 0 18px 34px rgba(16,33,61,0.20);
      }
      50% {
        transform: translateY(-3px);
        box-shadow: 0 24px 42px rgba(16,33,61,0.28);
      }
      100% {
        transform: translateY(0);
        box-shadow: 0 18px 34px rgba(16,33,61,0.20);
      }
    }
    .ficha-alert-base {
       position: fixed;
       right: 24px;
       width: 260px;
       min-height: 120px;
       border-radius: 16px;
       display: flex;
       align-items: center;
       gap: 12px;
       padding: 18px 22px;
       border: 1px solid var(--alert-border, rgba(0,0,0,0.25));
       background: var(--alert-bg, #FFC107);
       color: var(--alert-color, #1c1c1c);
       box-shadow: 0 14px 28px rgba(16,33,61,0.20);
       opacity: 0.99;
       z-index: 9999;
     }
     .ficha-alert-base.no-icon {
       padding-left: 26px;
     }
     .ficha-alert-text {
       display: flex;
       flex-direction: column;
       gap: 6px;
     }
     .ficha-alert-title {
       font-weight: 800;
       letter-spacing: 0.045em;
       text-transform: uppercase;
       font-size: 1rem;
       line-height: 1.3;
     }
     .ficha-alert-subtitle {
       font-size: 0.9rem;
       line-height: 1.45;
       font-weight: 600;
       opacity: 0.98;
     }
     </style>
     """
    
    # Sempre injeta CSS (Streamlit evita duplicação automáticamente)
    st.markdown(alert_css_base, unsafe_allow_html=True)

    titulo_html = f"<div class='ficha-alert-title'>{html.escape(str(titulo_texto))}</div>" if titulo_texto else ""
    subtitulo_html = f"<div class='ficha-alert-subtitle'>{html.escape(str(subtitulo_texto))}</div>" if subtitulo_texto else ""

    style_parts = [
        f"top:{int(top_position)}px",
        f"--alert-bg:{background_color}",
        f"--alert-border:{border_color}",
        f"--alert-color:{text_color}"
    ]
    style_attr = '; '.join(style_parts)

    alert_html = (
        f"<div class='ficha-alert-base no-icon' style='{style_attr}'>"
        f"<div class='ficha-alert-text'>{titulo_html}{subtitulo_html}</div>"
        "</div>"
    )
    st.markdown(alert_html, unsafe_allow_html=True)


def render_mapa_inicial_notification():
    """Renderiza notificação de Mapa Inicial"""
    mapa_inicial_css = """
    <style>
    @keyframes pulse-border {
      0% {
        box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.8);
      }
      70% {
        box-shadow: 0 0 0 12px rgba(255, 193, 7, 0);
      }
      100% {
        box-shadow: 0 0 0 0 rgba(255, 193, 7, 0);
      }
    }

    .mapa-inicial-notification {
      position: fixed;
      top: 65px;
      right: 0;
      width: 150px;
      height: 150px;
      background-color: #FFC107;
      color: #1c1c1c;
      border-radius: 8px 0 0 8px;
      display: flex;
      justify-content: center;
      align-items: center;
      font-weight: bold;
      font-size: 1.1em;
      text-align: center;
      z-index: 9999;
      box-shadow: 0 4px 12px rgba(0,0,0,0.25);
      animation: pulse-border 2s infinite;
      padding: 10px;
      border: 2px solid #FFA000;
      border-right: none;
    }
    </style>
    """
    mapa_inicial_html = "<div class='mapa-inicial-notification'>MAPA INICIAL</div>"
    st.markdown(mapa_inicial_html + mapa_inicial_css, unsafe_allow_html=True)


def inject_table_emissoes_css():
    """Injeta CSS para tabela de emissões"""
    tabela_emissoes_css = '''
    <style>
    .cert-status-wrapper {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .cert-status-wrapper.duplicado {
        position: relative;
        border-left: 4px solid #FF9800;
        padding-left: 16px;
    }
    .cert-status-wrapper.duplicado::before {
        content: "Duplicado";
        position: absolute;
        top: -10px;
        left: 0;
        transform: translate(-6px, -50%);
        background: linear-gradient(135deg, #FF9800 0%, #FB8C00 100%);
        color: #FFFFFF;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        padding: 3px 9px;
        border-radius: 999px;
        box-shadow: 0 4px 10px rgba(255, 152, 0, 0.35);
        text-transform: uppercase;
    }
    .cert-card {
        background: #FFFFFF;
        border: 1px solid rgba(13, 110, 253, 0.18);
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 14px 28px rgba(16, 33, 61, 0.12);
        display: flex;
        flex-direction: column;
        gap: 10px;
        text-align: left;
    }
    .cert-card.default-status {
        background: linear-gradient(135deg, #F8FAFF 0%, #EEF3FF 100%);
        border: 1px dashed rgba(13, 110, 253, 0.35);
        color: #4A5663;
        box-shadow: none;
    }
    .cert-card-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
    }
    .cert-status-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #10213D;
        line-height: 1.35;
    }
    .cert-status-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }
    .cert-chip {
        --chip-bg: rgba(13, 110, 253, 0.14);
        --chip-color: #0D47A1;
        background: var(--chip-bg);
        color: var(--chip-color);
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 999px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .cert-chip svg {
        width: 12px;
        height: 12px;
    }
    .cert-note {
        font-size: 0.80rem;
        color: #617089;
        line-height: 1.45;
    }
    .cert-status-links {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .cert-link-button {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        border-radius: 6px;
        text-decoration: none;
        background: transparent;
        border: 1px solid rgba(13, 110, 253, 0.35);
        color: #0D6EFD !important;
        font-size: 0.76rem;
        font-weight: 600;
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        box-shadow: none;
    }
    .cert-link-button:hover {
        background-color: rgba(13, 110, 253, 0.08);
        border-color: rgba(13, 110, 253, 0.55);
        color: #0B5ED7 !important;
    }
    .cert-link-icon {
        font-size: 0.85em;
        line-height: 1;
    }
    .ficha-download-bar {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 12px;
        margin: 14px 0 8px 0;
    }
    </style>
    '''
    # Sempre injeta CSS (Streamlit evita duplicação automáticamente)
    st.markdown(tabela_emissoes_css, unsafe_allow_html=True)


def inject_fullwidth_css():
    """Injeta CSS para largura completa"""
    css_fullwidth = '''
    <style>
    .ficha-familia-container {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        padding: 20px !important;
    }
    div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        flex: 0 1 100% !important;
    }
    </style>
    '''
    st.markdown(css_fullwidth, unsafe_allow_html=True)


def inject_search_page_css():
    """Injeta CSS para página de busca"""
    st.markdown('''
    <style>
    .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    .search-results-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 15px;
        font-size: 14px;
    }
    .search-results-table th {
        background-color: #f0f0f0;
        padding: 8px 12px;
        text-align: left;
        border: 1px solid #ddd;
        font-weight: 600;
    }
    .search-results-table td {
        padding: 8px 12px;
        border: 1px solid #ddd;
        vertical-align: top;
    }
    .search-results-table tr:hover {
        background-color: #f9f9f9;
        cursor: pointer;
    }
    .search-results-table tr.selected {
        background-color: #e0f0ff;
    }
    .results-count {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 10px;
        font-style: italic;
    }
    </style>
    ''', unsafe_allow_html=True)


# Configurações de canais especiais para alertas
CANAIS_ESPECIAIS_CONFIG = {
    'RECLAME AQUI': {
        'bg': 'linear-gradient(135deg, #FF6B6B 0%, #F44336 100%)',
        'border': 'rgba(255,255,255,0.35)',
        'color': '#FFFFFF',
        'label': 'Reclame Aqui',
    },
    'EXTRAJUDICIAL': {
        'bg': '#5E35B1',
        'border': 'rgba(255,255,255,0.28)',
        'color': '#FFFFFF',
        'label': 'Extrajudicial'
    },
    'PROCON': {
        'bg': '#FFB300',
        'border': 'rgba(0,0,0,0.15)',
        'color': '#1C1C1C',
        'label': 'PROCON'
    },
    'PROCESSO JUDICIAL': {
        'bg': '#1E88E5',
        'border': 'rgba(255,255,255,0.3)',
        'color': '#FFFFFF',
        'label': 'Processo Judicial'
    }
}


