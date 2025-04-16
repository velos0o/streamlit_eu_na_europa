import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random
import json
import os
from pathlib import Path
import sys

# Adicionar caminhos para importação
api_path = Path(__file__).parents[1] / 'api'
utils_path = Path(__file__).parents[1] / 'utils'
sys.path.insert(0, str(api_path))
sys.path.insert(0, str(utils_path))

# Importar funções necessárias para refresh global
try:
    from refresh_utils import handle_refresh_trigger, get_force_reload_status, clear_force_reload_flag
except ImportError:
    # Função substituta caso o módulo não seja encontrado
    def get_force_reload_status(): return False
    def handle_refresh_trigger(): return False
    def clear_force_reload_flag(): pass

# Definir cores Tailwind CSS para tema claro e escuro
THEME = {
    "light": {
        "primary": "#3B82F6",          # blue-500
        "secondary": "#6366F1",        # indigo-500
        "accent": "#F59E0B",           # amber-500
        "background": "#F9FAFB",       # gray-50
        "text": "#1F2937",             # gray-800
        "success": "#10B981",          # emerald-500
        "warning": "#F59E0B",          # amber-500 
        "error": "#EF4444",            # red-500
        "info": "#3B82F6",             # blue-500
    },
    "dark": {
        "primary": "#60A5FA",          # blue-400
        "secondary": "#818CF8",        # indigo-400
        "accent": "#FBBF24",           # amber-400
        "background": "#111827",       # gray-900
        "text": "#F9FAFB",             # gray-50
        "success": "#34D399",          # emerald-400
        "warning": "#FBBF24",          # amber-400
        "error": "#F87171",            # red-400
        "info": "#60A5FA",             # blue-400
    }
}

# Controle de depuração - definir como False em produção
DEBUG_MODE = False

# Função para carregar dados da entidade 1086
def carregar_dados_reclamacoes(force_reload=False, debug=DEBUG_MODE):
    """
    Carrega os dados da entidade 1086 (Reclamações) do Bitrix24
    
    Args:
        force_reload (bool): Se True, força o recarregamento dos dados ignorando o cache
        debug (bool): Se True, exibe informações de depuração
    
    Returns:
        pandas.DataFrame: DataFrame com os dados de reclamações
    """
    try:
        # Limpar mensagens de depuração anteriores se não estiver em modo debug
        if not debug:
            limpar_mensagens_debug = st.empty()
        
        # Importar as funções necessárias do bi_connector
        try:
            from bitrix_connector import load_bitrix_data, get_credentials
        except ImportError as e:
            if debug:
                st.error(f"Erro ao importar módulo bitrix_connector: {str(e)}")
                st.info("Tentando importar de outro caminho...")
            
            try:
                # Tentar diretamente com caminho completo
                sys.path.insert(0, str(Path(__file__).parents[1]))
                from api.bitrix_connector import load_bitrix_data, get_credentials
                if debug:
                    st.success("Importação bem-sucedida via api.bitrix_connector")
            except ImportError as e2:
                if debug:
                    st.error(f"Erro ao importar após ajuste de caminho: {str(e2)}")
                # Caso falhe, usamos dados simulados
                return _gerar_dados_simulados_reclamacoes()
        
        # Obter credenciais do Bitrix24
        BITRIX_TOKEN, BITRIX_URL = get_credentials()
        
        # Exibir informação sobre as credenciais para diagnóstico (ocultando o token completo)
        if debug:
            token_display = BITRIX_TOKEN[:5] + "*****" if BITRIX_TOKEN and len(BITRIX_TOKEN) > 5 else "Token não encontrado"
            st.info(f"Tentando conectar ao Bitrix: {BITRIX_URL} com token: {token_display}")
        
        # URL para a entidade 1086 no Bitrix24
        # Tente primeiro com a estrutura padrão
        url_reclamacoes = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1086"
        
        with st.spinner("Carregando dados de reclamações do Bitrix24..."):
            # Ver se há filtro específico para essa entidade
            # Se não há um filtro de categoria específico, podemos ver se existe alguma configuração que ajude
            filters = {"dimensionsFilters": [[]]}
            
            # Exibir a URL para diagnóstico (ocultando o token completo)
            if debug:
                url_display = url_reclamacoes.replace(BITRIX_TOKEN, token_display)
                st.info(f"Tentando acessar: {url_display}")
            
            # Tentar primeiro com filtro
            df_reclamacoes = load_bitrix_data(url_reclamacoes, filters=filters, show_logs=debug, force_reload=force_reload)
            
            # Se falhar, tentar sem filtro
            if df_reclamacoes is None or df_reclamacoes.empty:
                if debug:
                    st.warning("Primeira tentativa falhou. Tentando sem filtros...")
                df_reclamacoes = load_bitrix_data(url_reclamacoes, filters=None, show_logs=debug, force_reload=force_reload)
            
            # Se ainda falhar, tentar com formato de tabela alternativo (algumas instalações do Bitrix têm nomes diferentes)
            if df_reclamacoes is None or df_reclamacoes.empty:
                if debug:
                    st.warning("Segunda tentativa falhou. Tentando formato de tabela alternativo...")
                # Tentar com diferentes variações do nome da tabela
                alternate_urls = [
                    f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_1086",
                    f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_item_1086",
                    f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=b_crm_dynamic_items_1086"
                ]
                
                for url in alternate_urls:
                    if debug:
                        url_display = url.replace(BITRIX_TOKEN, token_display)
                        st.info(f"Tentando URL alternativa: {url_display}")
                    df_reclamacoes = load_bitrix_data(url, filters=None, show_logs=debug, force_reload=force_reload)
                    if df_reclamacoes is not None and not df_reclamacoes.empty:
                        if debug:
                            st.success(f"Conexão bem-sucedida com URL alternativa!")
                        break
            
            # Verificar se os dados foram carregados corretamente
            if df_reclamacoes is None or df_reclamacoes.empty:
                st.error("Não foi possível conectar à API Bitrix24 para carregar dados de reclamações.")
                # Mostrar um botão para tentar novamente
                if st.button("Tentar novamente", key="btn_retry_reclamacoes"):
                    st.rerun()
                return _gerar_dados_simulados_reclamacoes()
            
            # Exibir amostra dos dados para diagnóstico
            if debug:
                st.success(f"Dados carregados com sucesso: {len(df_reclamacoes)} registros.")
                st.write("Amostra dos dados recebidos:")
                st.write(f"Colunas disponíveis: {list(df_reclamacoes.columns)}")
                if len(df_reclamacoes) > 0:
                    st.write("Primeiro registro:")
                    st.write(df_reclamacoes.iloc[0])
            
            # Processar os dados recebidos
            # Renomear colunas para nomes mais amigáveis
            colunas_mapeamento = {
                'ID': 'ID',
                'TITLE': 'TITULO',
                'DATE_CREATE': 'DATA_CRIACAO',
                'STAGE_ID': 'ID_ESTAGIO',
                'ASSIGNED_BY_ID': 'ID_RESPONSAVEL',
                'ASSIGNED_BY_NAME': 'ADM_RESPONSAVEL',
                'UF_CRM_28_CPF': 'CPF',
                'UF_CRM_28_DEPARTAMENTO': 'DEPARTAMENTO',
                'UF_CRM_28_DESCRICAO_RECLAMACAO': 'DESCRICAO_RECLAMACAO',
                'UF_CRM_28_EMAIL': 'EMAIL',
                'UF_CRM_28_ORIGEM': 'ORIGEM',
                'UF_CRM_28_TELEFONE': 'TELEFONE',
                'STAGE_NAME': 'STATUS'
            }
            
            # Criar cópia para evitar SettingWithCopyWarning
            df_processado = df_reclamacoes.copy()
            
            # Renomear colunas que existem no DataFrame
            for col_original, col_novo in colunas_mapeamento.items():
                if col_original in df_processado.columns:
                    df_processado.rename(columns={col_original: col_novo}, inplace=True)
            
            # Garantir que todas as colunas necessárias existam
            for col_novo in colunas_mapeamento.values():
                if col_novo not in df_processado.columns:
                    df_processado[col_novo] = None
            
            # Converter coluna de data para datetime
            if 'DATA_CRIACAO' in df_processado.columns:
                df_processado['DATA_CRIACAO'] = pd.to_datetime(df_processado['DATA_CRIACAO'], errors='coerce')
            
            # Ordenar por data de criação (mais recentes primeiro)
            if 'DATA_CRIACAO' in df_processado.columns:
                df_processado = df_processado.sort_values(by="DATA_CRIACAO", ascending=False)
            
            # Exibir informações sobre os dados carregados
            st.success(f"Dados processados com sucesso: {len(df_processado)} reclamações.")
            
            # Limpar as mensagens de depuração se não estiver em modo debug
            if not debug:
                limpar_mensagens_debug.empty()
            
            return df_processado
    
    except Exception as e:
        st.error(f"Erro ao carregar dados de reclamações: {str(e)}")
        # Exibir o traceback para diagnóstico
        if debug:
            import traceback
            st.code(traceback.format_exc(), language="python")
        return _gerar_dados_simulados_reclamacoes()

# Função auxiliar para gerar dados simulados de reclamações
def _gerar_dados_simulados_reclamacoes():
    """
    Gera dados simulados para demonstração quando a API não está disponível
    """
    st.warning("Usando dados simulados para demonstração.")
    
    # Simular um atraso na carga para mostrar o spinner
    time.sleep(1)
    
    # Criar dados simulados
    data = {
        "ID": list(range(1, 51)),
        "DATA_CRIACAO": [(datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d") for _ in range(50)],
        "ADM_RESPONSAVEL": random.choices(["Ana Silva", "Carlos Santos", "Luciana Oliveira", "Pedro Almeida", "Maria Souza"], k=50),
        "CPF": [f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}" for _ in range(50)],
        "DEPARTAMENTO": random.choices(["Atendimento", "Financeiro", "Técnico", "Jurídico", "Comercial"], k=50),
        "DESCRICAO_RECLAMACAO": [
            "Problemas com processo de emissão",
            "Atraso na entrega de documentos",
            "Informações incorretas",
            "Valores cobrados indevidamente",
            "Falta de retorno do atendente",
            "Documentação recusada sem justificativa",
            "Sistema fora do ar durante processo",
            "Documento emitido com erro",
            "Cobrança em duplicidade",
            "Não recebi confirmação do pedido"
        ] * 5,
        "EMAIL": [f"cliente{i}@exemplo.com" for i in range(1, 51)],
        "ORIGEM": random.choices(["Site", "Telefone", "Email", "WhatsApp", "Presencial"], k=50),
        "TELEFONE": [f"({random.randint(11, 99)}) {random.randint(90000, 99999)}-{random.randint(1000, 9999)}" for _ in range(50)],
        "STATUS": random.choices(["Nova", "Em análise", "Respondida", "Resolvida", "Cancelada"], weights=[10, 30, 25, 25, 10], k=50)
    }
    
    df = pd.DataFrame(data)
    
    # Converter coluna de data para datetime
    df["DATA_CRIACAO"] = pd.to_datetime(df["DATA_CRIACAO"])
    
    # Ordenar por data de criação (mais recentes primeiro)
    df = df.sort_values(by="DATA_CRIACAO", ascending=False)
    
    return df

# Função para aplicar estilo TailwindCSS baseado no tema
def tailwind_card(title, content, theme_mode="light", accent_color=None):
    """Cria um card estilizado com TailwindCSS"""
    theme = THEME[theme_mode]
    accent = theme[accent_color] if accent_color else theme["primary"]
    
    bg_color = theme["background"]
    text_color = theme["text"]
    border_color = accent
    
    card_html = f"""
    <div style="
        background-color: {bg_color};
        color: {text_color};
        border-left: 4px solid {border_color};
        border-radius: 0.375rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <h3 style="
            color: {accent};
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        ">{title}</h3>
        <div>{content}</div>
    </div>
    """
    return card_html

# Função para criar um stat card com valor e título
def stat_card(value, title, change=None, is_positive=True, theme_mode="light"):
    """Cria um card de estatística estilizado com TailwindCSS"""
    theme = THEME[theme_mode]
    
    # Formatar valor para exibição
    formatted_value = value
    if isinstance(value, (int, float)):
        formatted_value = f"{value:,}".replace(",", ".")
    
    # Definir cores para o indicador de mudança
    change_color = theme["success"] if is_positive else theme["error"]
    change_arrow = "↑" if is_positive else "↓"
    
    # Construir HTML para o indicador de mudança
    change_html = ""
    if change is not None:
        change_html = f"""
        <div style="
            color: {change_color};
            font-size: 0.875rem;
            font-weight: 500;
            display: flex;
            align-items: center;
        ">
            {change_arrow} {change}%
        </div>
        """
    
    # Construir o card completo
    card_html = f"""
    <div style="
        background-color: {theme['background']};
        color: {theme['text']};
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        padding: 1.25rem;
        height: 100%;
    ">
        <div style="
            font-size: 2rem;
            font-weight: 700;
            color: {theme['primary']};
            margin-bottom: 0.5rem;
        ">{formatted_value}</div>
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div style="
                font-size: 1rem;
                color: {theme['text']};
                opacity: 0.8;
            ">{title}</div>
            {change_html}
        </div>
    </div>
    """
    return card_html

# Função alternativa usando componentes nativos do Streamlit
def show_metric_card(col, value, title, change=None, is_positive=True, theme_mode="light"):
    """Exibe um cartão de métrica usando componentes nativos do Streamlit"""
    theme = THEME[theme_mode]
    
    # Cria uma div estilizada
    with col:
        # Aplicar estilo personalizado à coluna
        if theme_mode == "dark":
            col.markdown(f"""
            <style>
            [data-testid="stMetricValue"] {{
                color: {theme["primary"]} !important;
                font-size: 2rem !important;
            }}
            [data-testid="stMetricLabel"] {{
                color: {theme["text"]} !important;
            }}
            [data-testid="stMetricDelta"] {{
                color: {theme["success"] if is_positive else theme["error"]} !important;
            }}
            </style>
            """, unsafe_allow_html=True)
            
        # Exibir o valor usando o componente nativo
        delta = change if change is not None else None
        col.metric(
            label=title,
            value=value,
            delta=f"{change}%" if delta is not None else None,
            delta_color="normal" if is_positive else "inverse"
        )

# Função para criar containers no estilo Tailwind usando componentes nativos do Streamlit
def tailwind_container(container_type="default"):
    """
    Cria um container estilizado com Tailwind CSS usando componentes nativos do Streamlit
    
    Args:
        container_type: Tipo de container (default, info, success, warning, error)
    
    Returns:
        Um objeto container do Streamlit com estilo do Tailwind
    """
    theme_mode = "dark" if st.session_state.dark_mode else "light"
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
    
    # Criar CSS para o container
    container_css = f"""
    <style>
    div[data-testid="stExpander"] > details > summary {{
        color: {border_color} !important;
        font-weight: 600;
    }}
    div[data-testid="stExpander"] {{
        border-left: 4px solid {border_color} !important;
        background-color: {theme["background"]} !important;
    }}
    </style>
    """
    
    # Adicionar o CSS
    st.markdown(container_css, unsafe_allow_html=True)
    
    # Retornar um expander normal
    return st

# Adicionar CSS global para o tema claro e escuro inspirado no Tailwind
def apply_tailwind_styles(theme_mode="light"):
    """Aplica estilos globais inspirados no Tailwind CSS"""
    theme = THEME[theme_mode]
    
    # Gerar CSS baseado no tema
    css = f"""
    <style>
    /* Estilos globais inspirados no Tailwind */
    .tw-heading {{
        color: {theme["primary"]};
        font-weight: 600;
        margin-bottom: 1rem;
        position: relative;
        display: inline-block;
    }}
    
    .tw-heading::after {{
        content: '';
        position: absolute;
        bottom: -5px;
        left: 0;
        width: 40%;
        height: 3px;
        background: linear-gradient(90deg, {theme["primary"]}, transparent);
    }}
    
    /* Cards com bordas arredondadas */
    .tw-card {{
        background-color: {theme["background"]};
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 1rem;
        border: 1px solid {theme["primary"]}20;
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    
    .tw-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }}
    
    /* Cards com bordas coloridas */
    .tw-card-primary {{
        border-left: 4px solid {theme["primary"]};
    }}
    
    .tw-card-secondary {{
        border-left: 4px solid {theme["secondary"]};
    }}
    
    .tw-card-success {{
        border-left: 4px solid {theme["success"]};
    }}
    
    .tw-card-error {{
        border-left: 4px solid {theme["error"]};
    }}
    
    /* Botões estilizados */
    div.stButton > button {{
        background-color: {theme["primary"]};
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.3s;
    }}
    
    div.stButton > button:hover {{
        background-color: {theme["secondary"]};
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
    }}
    
    /* Cabeçalhos */
    h1, h2, h3 {{
        color: {theme["primary"]} !important;
        font-weight: 600 !important;
    }}
    
    h1 {{
        font-size: 2.25rem !important;
        line-height: 2.5rem !important;
        margin-bottom: 1.5rem !important;
        border-bottom: 2px solid {theme["primary"]}30 !important;
        padding-bottom: 0.5rem !important;
    }}
    
    h2 {{
        font-size: 1.5rem !important;
        line-height: 2rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }}
    
    h3 {{
        font-size: 1.25rem !important;
        line-height: 1.75rem !important;
        margin-top: 1rem !important;
        margin-bottom: 0.75rem !important;
    }}
    
    /* Badges/tags */
    .tw-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    
    .tw-badge:hover {{
        transform: scale(1.05);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    .tw-badge-primary {{
        background-color: {theme["primary"]}20;
        color: {theme["primary"]};
        border: 1px solid {theme["primary"]}30;
    }}
    
    .tw-badge-success {{
        background-color: {theme["success"]}20;
        color: {theme["success"]};
        border: 1px solid {theme["success"]}30;
    }}
    
    .tw-badge-warning {{
        background-color: {theme["warning"]}20;
        color: {theme["warning"]};
        border: 1px solid {theme["warning"]}30;
    }}
    
    .tw-badge-error {{
        background-color: {theme["error"]}20;
        color: {theme["error"]};
        border: 1px solid {theme["error"]}30;
    }}
    
    /* Separadores */
    .tw-divider {{
        height: 1px;
        width: 100%;
        background: linear-gradient(90deg, {theme["primary"]}10, {theme["primary"]}40, {theme["primary"]}10);
        margin: 1.5rem 0;
    }}
    
    /* Animação fade-in para elementos */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .tw-fade-in {{
        animation: fadeIn 0.5s ease-out;
    }}
    
    /* Tooltip personalizado */
    .tw-tooltip {{
        position: relative;
        display: inline-block;
    }}
    
    .tw-tooltip::after {{
        content: attr(data-tooltip);
        position: absolute;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        background-color: {theme["secondary"]};
        color: white;
        text-align: center;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        white-space: nowrap;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s, visibility 0.3s;
        z-index: 1000;
    }}
    
    .tw-tooltip:hover::after {{
        opacity: 1;
        visibility: visible;
    }}
    
    /* Elemento de toggle para tema */
    .tw-theme-toggle {{
        cursor: pointer;
        padding: 8px;
        border-radius: 50%;
        background-color: {theme["background"]};
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
    }}
    
    .tw-theme-toggle:hover {{
        transform: rotate(30deg);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
    }}
    
    /* Ajuste nas tabelas para tema escuro */
    {f'''
    .dataframe {{
        color: {theme["text"]} !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border-radius: 0.5rem !important;
        overflow: hidden !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }}
    
    .dataframe th {{
        background-color: {theme["secondary"]}30 !important;
        color: {theme["text"]} !important;
        padding: 0.75rem 1rem !important;
        text-align: left !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}
    
    .dataframe td {{
        background-color: {theme["background"]} !important;
        color: {theme["text"]} !important;
        padding: 0.75rem 1rem !important;
        border-top: 1px solid {theme["secondary"]}20 !important;
        transition: background-color 0.2s !important;
    }}
    
    .dataframe tr:hover td {{
        background-color: {theme["secondary"]}15 !important;
    }}
    ''' if theme_mode == "dark" else f'''
    .dataframe {{
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border-radius: 0.5rem !important;
        overflow: hidden !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05) !important;
    }}
    
    .dataframe th {{
        background-color: {theme["primary"]}10 !important;
        padding: 0.75rem 1rem !important;
        text-align: left !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}
    
    .dataframe td {{
        padding: 0.75rem 1rem !important;
        border-top: 1px solid {theme["primary"]}10 !important;
        transition: background-color 0.2s !important;
    }}
    
    .dataframe tr:hover td {{
        background-color: {theme["primary"]}10 !important;
    }}
    '''}
    </style>
    """
    
    # Aplicar o CSS
    st.markdown(css, unsafe_allow_html=True)

# Função principal para mostrar a página de reclamações
def show_reclamacoes():
    """
    Exibe a página de reclamações do cliente
    """
    # Verificar se o tema escuro está ativado
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
        
    # Obter o tema atual
    theme_mode = "dark" if st.session_state.dark_mode else "light"
    
    # Aplicar estilos globais baseados no Tailwind CSS
    apply_tailwind_styles(theme_mode)
    
    # Adicionar CSS específico para o tema escuro
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
        /* Estilo para o tema escuro */
        .stApp {
            background-color: #111827 !important;
            color: #F9FAFB !important;
        }
        
        /* Ajustar cores de texto */
        p, span, div {
            color: #F9FAFB !important;
        }
        
        /* Personalizações de cabeçalhos */
        h1, h2, h3, h4, h5, h6 {
            color: #60A5FA !important;
        }
        
        /* Ajustar cores de widgets do Streamlit */
        .stSelectbox label, .stMultiselect label {
            color: #F9FAFB !important;
        }
        
        /* Ajustar cores dos cards e containers */
        .stAlert, .stInfoAlert {
            background-color: #1F2937 !important;
            color: #F9FAFB !important;
        }
        
        /* Ajustar cores de tabelas */
        .dataframe {
            color: #F9FAFB !important;
        }
        
        /* Ajustar cores de elementos da tabela */
        .dataframe th {
            background-color: #374151 !important;
            color: #F9FAFB !important;
        }
        
        .dataframe td {
            background-color: #1F2937 !important;
            color: #F9FAFB !important;
        }
        
        /* Ajustar cores de entrada */
        .stTextInput > div > div > input {
            background-color: #374151 !important;
            color: #F9FAFB !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Layout principal com estilo Tailwind e animação
    st.markdown('<h1 class="tw-heading tw-fade-in">Gestão de Reclamações</h1>', unsafe_allow_html=True)
    
    # Toggle para alterar entre tema claro e escuro com estilo personalizado
    col_theme, col_refresh = st.columns([1, 9])
    with col_theme:
        # Usar apenas o botão nativo do Streamlit com o ícone apropriado
        theme_icon = "🌓" if st.session_state.dark_mode else "☀️"
        theme_tooltip = "Alternar para tema claro" if st.session_state.dark_mode else "Alternar para tema escuro"
        
        # Aplicar um pouco de personalização ao botão nativo
        st.markdown("""
        <style>
        /* Personalizar botão de tema */
        [data-testid="baseButton-secondary"][id*="btn_toggle_theme"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0.5em !important;
            font-size: 1.2em !important;
            transition: transform 0.3s !important;
        }
        
        [data-testid="baseButton-secondary"][id*="btn_toggle_theme"]:hover {
            transform: rotate(30deg) !important;
        }

        /* Estilo para o botão de atualização */
        div[data-testid="baseButton-secondaryFormSubmit"][id*="btn_atualizar_reclamacoes"] {
            background-color: #10B981 !important;
            color: white !important;
            font-weight: bold !important;
            padding: 0.5em 1em !important;
            transition: all 0.3s !important;
        }
        
        div[data-testid="baseButton-secondaryFormSubmit"][id*="btn_atualizar_reclamacoes"]:hover {
            background-color: #047857 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Botão simples com o emoji apropriado
        if st.button(theme_icon, key="btn_toggle_theme", help=theme_tooltip):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    with col_refresh:
        col_blank, col_btn = st.columns([2, 1])
        with col_btn:
            if st.button("🔄 Atualizar Dados", key="btn_atualizar_reclamacoes", help="Força a atualização dos dados do Bitrix24", type="primary", use_container_width=True):
                with st.spinner("Atualizando dados e limpando cache..."):
                    # Mostrar mensagem de feedback
                    st.info("Limpando cache e recarregando dados em tempo real...")
                    
                    # Limpar todos os caches antes de recarregar
                    st.cache_data.clear()
                    
                    # Definir flags no estado da sessão para consistência com o resto do projeto
                    st.session_state['full_refresh'] = True
                    st.session_state['force_reload'] = True
                    st.session_state['loading_state'] = 'loading'
                    
                    # Pequena pausa para garantir que o cache seja completamente limpo
                    time.sleep(0.5)
                    st.success("Cache limpo! Recarregando página...")
                    time.sleep(0.5)
                    st.rerun()
    
    # Adicionar um separador estilizado
    st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)

    # Verificar se a página está em modo de depuração
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = DEBUG_MODE
    
    # Verificar se há atualização global acionada por outro botão do sistema
    if handle_refresh_trigger():
        # Indicar que estamos atualizando
        st.info("⏳ Atualizando dados como parte de uma atualização global...")
        time.sleep(0.5)
        st.rerun()
    
    # Se estiver forçando recarregamento, exibir indicador
    force_reload = get_force_reload_status()
    if force_reload:
        st.info("⏳ Dados sendo atualizados diretamente da API (ignorando cache)...")
        # Limpar a flag após seu uso
        clear_force_reload_flag()
    
    # Carregar dados com opção de force_reload e depuração conforme configurado
    with st.spinner("Carregando dados de reclamações..."):
        df = carregar_dados_reclamacoes(force_reload=force_reload, debug=st.session_state.debug_mode)
    
    # Dashboard principal
    st.markdown('<h2 class="tw-heading tw-fade-in">Visão Geral</h2>', unsafe_allow_html=True)
    
    # Adicionar cards para métricas em uma div com animação
    st.markdown('<div class="tw-fade-in">', unsafe_allow_html=True)
    
    # Métricas principais em cards
    col1, col2, col3, col4 = st.columns(4)
    
    # Total de reclamações
    total_reclamacoes = len(df)
    show_metric_card(
        col1,
        total_reclamacoes, 
        "Total de Reclamações", 
        change=12, 
        is_positive=False,
        theme_mode=theme_mode
    )

    # Reclamações em aberto
    reclamacoes_em_aberto = len(df[df["STATUS"].isin(["Nova", "Em análise"])])
    show_metric_card(
        col2,
        reclamacoes_em_aberto, 
        "Em Aberto", 
        change=5, 
        is_positive=False,
        theme_mode=theme_mode
    )

    # Reclamações resolvidas
    reclamacoes_resolvidas = len(df[df["STATUS"] == "Resolvida"])
    show_metric_card(
        col3,
        reclamacoes_resolvidas, 
        "Resolvidas", 
        change=8, 
        is_positive=True,
        theme_mode=theme_mode
    )
    
    # Taxa de resolução
    taxa_resolucao = int((reclamacoes_resolvidas / total_reclamacoes) * 100)
    show_metric_card(
        col4,
        f"{taxa_resolucao}%", 
        "Taxa de Resolução", 
        change=3, 
        is_positive=True,
        theme_mode=theme_mode
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Gráficos principais com animação
    st.markdown('<div class="tw-fade-in" style="animation-delay: 0.1s;">', unsafe_allow_html=True)
    
    # Criar dois gráficos principais
    col_grafico1, col_grafico2 = st.columns(2)
    
    with col_grafico1:
        st.subheader("Status das Reclamações")
        
        # Contagem de status
        status_counts = df["STATUS"].value_counts().reset_index()
        status_counts.columns = ["Status", "Quantidade"]
        
        # Criar gráfico de pizza com Plotly
        fig_status = px.pie(
            status_counts, 
            values="Quantidade", 
            names="Status",
            color="Status",
            color_discrete_map={
                "Nova": THEME[theme_mode]["primary"],
                "Em análise": THEME[theme_mode]["info"],
                "Respondida": THEME[theme_mode]["warning"],
                "Resolvida": THEME[theme_mode]["success"],
                "Cancelada": THEME[theme_mode]["error"]
            },
            hole=0.4
        )
        
        # Atualizar layout para tema escuro, se necessário
        if theme_mode == "dark":
            fig_status.update_layout(
                paper_bgcolor="#1F2937",
                plot_bgcolor="#1F2937",
                font=dict(color="#F9FAFB")
            )
        
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col_grafico2:
        st.subheader("Reclamações por Origem")
        
        # Contagem de origem
        origem_counts = df["ORIGEM"].value_counts().reset_index()
        origem_counts.columns = ["Origem", "Quantidade"]
        
        # Criar gráfico de barras com Plotly
        fig_origem = px.bar(
            origem_counts, 
            x="Origem", 
            y="Quantidade",
            color="Origem",
            text="Quantidade"
        )
        
        # Atualizar layout para tema escuro, se necessário
        if theme_mode == "dark":
            fig_origem.update_layout(
                paper_bgcolor="#1F2937",
                plot_bgcolor="#1F2937",
                font=dict(color="#F9FAFB")
            )
            
            # Atualizar eixos
            fig_origem.update_xaxes(color="#F9FAFB")
            fig_origem.update_yaxes(color="#F9FAFB")
        
        st.plotly_chart(fig_origem, use_container_width=True)
    
    # Gráfico de tendência no tempo
    st.subheader("Tendência de Reclamações", anchor="tendencia")
    
    # Agrupar por data de criação
    df_trend = df.groupby(df["DATA_CRIACAO"].dt.strftime("%Y-%m-%d")).size().reset_index()
    df_trend.columns = ["Data", "Quantidade"]
    df_trend["Data"] = pd.to_datetime(df_trend["Data"])
    df_trend = df_trend.sort_values("Data")
    
    # Criar gráfico de linha com Plotly
    fig_trend = px.line(
        df_trend, 
        x="Data", 
        y="Quantidade",
        markers=True
    )
    
    # Atualizar layout para tema escuro, se necessário
    if theme_mode == "dark":
        fig_trend.update_layout(
            paper_bgcolor="#1F2937",
            plot_bgcolor="#1F2937",
            font=dict(color="#F9FAFB")
        )
        
        # Atualizar eixos
        fig_trend.update_xaxes(color="#F9FAFB")
        fig_trend.update_yaxes(color="#F9FAFB")
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Distribuição por departamento e responsável
    col_dept, col_resp = st.columns(2)
    
    with col_dept:
        st.subheader("Por Departamento")
        
        # Contagem por departamento
        dept_counts = df["DEPARTAMENTO"].value_counts().reset_index()
        dept_counts.columns = ["Departamento", "Quantidade"]
        
        # Criar gráfico de barras horizontais com Plotly
        fig_dept = px.bar(
            dept_counts, 
            y="Departamento", 
            x="Quantidade",
            orientation="h",
            color="Quantidade",
            color_continuous_scale=["#60A5FA", "#3B82F6"] if theme_mode == "dark" else ["#93C5FD", "#2563EB"],
            text="Quantidade"
        )
        
        # Atualizar layout para tema escuro, se necessário
        if theme_mode == "dark":
            fig_dept.update_layout(
                paper_bgcolor="#1F2937",
                plot_bgcolor="#1F2937",
                font=dict(color="#F9FAFB")
            )
            
            # Atualizar eixos
            fig_dept.update_xaxes(color="#F9FAFB")
            fig_dept.update_yaxes(color="#F9FAFB")
        
        st.plotly_chart(fig_dept, use_container_width=True)
    
    with col_resp:
        st.subheader("Por Responsável")
        
        # Contagem por responsável
        resp_counts = df["ADM_RESPONSAVEL"].value_counts().reset_index()
        resp_counts.columns = ["Responsável", "Quantidade"]
        
        # Criar gráfico de barras horizontais com Plotly
        fig_resp = px.bar(
            resp_counts, 
            y="Responsável", 
            x="Quantidade",
            orientation="h",
            color="Quantidade",
            color_continuous_scale=["#A78BFA", "#7C3AED"] if theme_mode == "dark" else ["#C4B5FD", "#6D28D9"],
            text="Quantidade"
        )
        
        # Atualizar layout para tema escuro, se necessário
        if theme_mode == "dark":
            fig_resp.update_layout(
                paper_bgcolor="#1F2937",
                plot_bgcolor="#1F2937",
                font=dict(color="#F9FAFB")
            )
            
            # Atualizar eixos
            fig_resp.update_xaxes(color="#F9FAFB")
            fig_resp.update_yaxes(color="#F9FAFB")
        
        st.plotly_chart(fig_resp, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de detalhes/filtros com animação
    st.markdown('<div class="tw-fade-in" style="animation-delay: 0.2s;">', unsafe_allow_html=True)
    st.markdown('<h2 class="tw-heading">Detalhes das Reclamações</h2>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="tw-card tw-card-primary">', unsafe_allow_html=True)
        
        # Adicionar filtros
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            status_filter = st.multiselect(
                "Status",
                options=df["STATUS"].unique(),
                default=df["STATUS"].unique()
            )
            
        with col_filtro2:
            departamento_filter = st.multiselect(
                "Departamento",
                options=df["DEPARTAMENTO"].unique(),
                default=df["DEPARTAMENTO"].unique()
            )
            
        with col_filtro3:
            origem_filter = st.multiselect(
                "Origem",
                options=df["ORIGEM"].unique(),
                default=df["ORIGEM"].unique()
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Aplicar filtros
    df_filtered = df[
        df["STATUS"].isin(status_filter) &
        df["DEPARTAMENTO"].isin(departamento_filter) &
        df["ORIGEM"].isin(origem_filter)
    ]
    
    # Mostrar tabela filtrada com badges para status
    df_display = df_filtered[["DATA_CRIACAO", "ADM_RESPONSAVEL", "DEPARTAMENTO", "ORIGEM", "STATUS", "DESCRICAO_RECLAMACAO"]].copy()
    
    # Converter o status para HTML com badges
    # Como não podemos alterar diretamente a tabela com HTML, mostraremos uma versão sem formatação
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "DATA_CRIACAO": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "ADM_RESPONSAVEL": st.column_config.TextColumn("Responsável"),
            "DEPARTAMENTO": st.column_config.TextColumn("Departamento"),
            "ORIGEM": st.column_config.TextColumn("Origem"),
            "STATUS": st.column_config.TextColumn("Status"),
            "DESCRICAO_RECLAMACAO": st.column_config.TextColumn("Descrição"),
        }
    )
    
    # Adicionar expansor para ver detalhes de uma reclamação específica
    tw = tailwind_container("secondary")
    with tw.expander("Ver detalhes de uma reclamação específica"):
        col_id, col_btn = st.columns([3, 1])
        
        with col_id:
            reclamacao_id = st.number_input("ID da Reclamação", min_value=1, max_value=max(df["ID"]), value=1)
            
        with col_btn:
            st.write("")  # Espaço para alinhar com o input
            buscar = st.button("Buscar")
            
        if buscar:
            reclamacao = df[df["ID"] == reclamacao_id]
            
            if not reclamacao.empty:
                reclamacao = reclamacao.iloc[0]
                
                # Card com os detalhes da reclamação usando componentes estilizados
                st.markdown(f'<div class="tw-card tw-card-secondary">', unsafe_allow_html=True)
                st.subheader(f"Detalhes da Reclamação #{reclamacao_id}")
                
                # Adicionar badge do status
                status = reclamacao["STATUS"]
                st.markdown(f'<span class="tw-badge tw-badge-{"success" if status == "Resolvida" else "warning" if status in ["Em análise", "Respondida"] else "error" if status == "Cancelada" else "primary"}">{status}</span>', unsafe_allow_html=True)
                
                st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)
                
                # Primeira coluna com informações básicas
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**ID:** {reclamacao['ID']}")
                    st.markdown(f"**Data:** {reclamacao['DATA_CRIACAO'].strftime('%d/%m/%Y')}")
                    st.markdown(f"**Responsável:** {reclamacao['ADM_RESPONSAVEL']}")
                    st.markdown(f"**Departamento:** {reclamacao['DEPARTAMENTO']}")
                
                with col2:
                    st.markdown(f"**Origem:** {reclamacao['ORIGEM']}")
                    st.markdown(f"**CPF:** {reclamacao['CPF']}")
                    st.markdown(f"**Email:** {reclamacao['EMAIL']}")
                    st.markdown(f"**Telefone:** {reclamacao['TELEFONE']}")
                
                # Descrição completa
                st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)
                st.markdown("### Descrição")
                st.markdown(reclamacao["DESCRICAO_RECLAMACAO"])
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(f"Reclamação com ID {reclamacao_id} não encontrada.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer com informações adicionais
    st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; opacity: 0.7; font-size: 0.85rem; margin-top: 2rem; margin-bottom: 1rem;">Desenvolvido com 💙 usando Streamlit e design inspirado no Tailwind CSS</div>', unsafe_allow_html=True)
    
    # Toggle para debug - mostrar apenas em desenvolvimento
    with st.expander("⚙️ Opções de Desenvolvimento", expanded=False):
        # Checkbox para ativar/desativar o modo de depuração
        if st.checkbox("Modo de Depuração", value=st.session_state.debug_mode, 
                       help="Exibe informações adicionais para diagnóstico", key="debug_toggle"):
            st.session_state.debug_mode = not st.session_state.debug_mode
            st.rerun()
        
        st.markdown("---")
        st.write("Caminhos do Sistema:")
        st.code(f"API Path: {api_path}")
        st.code(f"Utils Path: {utils_path}")
        st.markdown("---")
        
        # Nome da entidade Bitrix
        entity_name = st.text_input("Nome da Entidade Bitrix", value="crm_dynamic_items_1086", 
                                   help="Altere para testar diferentes nomes de tabela")
        
        # Botão para testar conexão direta com Bitrix
        if st.button("Testar Conexão Bitrix", key="btn_test_bitrix"):
            try:
                # Importar as funções necessárias do bi_connector
                try:
                    from bitrix_connector import load_bitrix_data, get_credentials
                    st.success("Importação bem-sucedida via bitrix_connector")
                except ImportError as e:
                    st.error(f"Erro ao importar módulo bitrix_connector: {str(e)}")
                    try:
                        # Tentar diretamente com caminho completo
                        from api.bitrix_connector import load_bitrix_data, get_credentials
                        st.success("Importação bem-sucedida via api.bitrix_connector")
                    except ImportError as e2:
                        st.error(f"Erro ao importar após ajuste de caminho: {str(e2)}")
                
                # Obter credenciais do Bitrix24
                BITRIX_TOKEN, BITRIX_URL = get_credentials()
                token_display = BITRIX_TOKEN[:5] + "*****" if BITRIX_TOKEN and len(BITRIX_TOKEN) > 5 else "Token não encontrado"
                st.success(f"Credenciais obtidas: {BITRIX_URL} / {token_display}")
                
                # Tentar carregar dados da entidade especificada
                url_test = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table={entity_name}"
                st.info(f"Testando conexão com: {url_test.replace(BITRIX_TOKEN, token_display)}")
                
                with st.spinner("Testando conexão..."):
                    df_test = load_bitrix_data(url_test, show_logs=True)
                    
                if df_test is not None and not df_test.empty:
                    st.success(f"Conexão bem-sucedida! Recebidos {len(df_test)} registros com {len(df_test.columns)} colunas.")
                    st.write("Colunas disponíveis:")
                    st.write(list(df_test.columns))
                    
                    # Mostrar primeiros registros
                    if len(df_test) > 0:
                        st.write("Primeiros registros:")
                        st.dataframe(df_test.head(3))
                else:
                    st.error("Conexão falhou ou não retornou dados. Verifique o nome da entidade e as credenciais.")
            except Exception as e:
                st.error(f"Erro ao testar conexão: {str(e)}")
                import traceback
                st.code(traceback.format_exc(), language="python") 