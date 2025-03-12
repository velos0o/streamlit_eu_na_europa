import streamlit as st
import pandas as pd

def render_metric_card(title, value, comparison_value=None, description=None):
    """
    Renderiza um card de métrica com opção de comparação
    
    Args:
        title (str): Título da métrica
        value (any): Valor principal da métrica
        comparison_value (float, optional): Valor de comparação/porcentagem
        description (str, optional): Descrição adicional
    """
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-comparison">{comparison_value}</div>' if comparison_value else ''}
            {f'<div class="metric-description">{description}</div>' if description else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_metrics_section(counts):
    """
    Renderiza a seção de métricas com os valores calculados
    
    Args:
        counts (dict): Dicionário com as contagens de status
    """
    # Criar colunas para as métricas
    col1, col2, col3, col4 = st.columns(4)
    
    # Total de processos (agora chamado de "Total de Negócios")
    with col1:
        st.markdown("""
        <div class="metric-container total">
            <div class="metric-title">Total de Negócios</div>
            <div class="metric-value">{}</div>
            <div class="metric-description">Total de IDs no funil</div>
        </div>
        """.format(counts['total']), unsafe_allow_html=True)
    
    # Processos pendentes
    with col2:
        st.markdown("""
        <div class="metric-container pendente">
            <div class="metric-title">Pendentes</div>
            <div class="metric-value">{}</div>
            <div class="metric-percentage">{:.1f}%</div>
            <div class="metric-description">Status vazio ou PENDENTE</div>
        </div>
        """.format(counts['pendente'], counts['pendente_pct']), unsafe_allow_html=True)
    
    # Processos incompletos
    with col3:
        st.markdown("""
        <div class="metric-container incompleto">
            <div class="metric-title">Incompletos</div>
            <div class="metric-value">{}</div>
            <div class="metric-percentage">{:.1f}%</div>
        </div>
        """.format(counts['incompleto'], counts['incompleto_pct']), unsafe_allow_html=True)
    
    # Processos completos
    with col4:
        st.markdown("""
        <div class="metric-container completo">
            <div class="metric-title">Completos</div>
            <div class="metric-value">{}</div>
            <div class="metric-percentage">{:.1f}%</div>
        </div>
        """.format(counts['completo'], counts['completo_pct']), unsafe_allow_html=True)

def render_status_indicator(status):
    """
    Renderiza um indicador visual de status
    
    Args:
        status (str): Status a ser exibido
    """
    from api.bitrix_connector import get_status_color
    from utils.data_processor import format_status_text
    
    color_class = get_status_color(status)
    status_text = format_status_text(status)
    
    st.markdown(
        f"""
        <span class="{color_class}">{status_text}</span>
        """,
        unsafe_allow_html=True
    )

def render_conclusion_item(id, title, responsible, date):
    """
    Renderiza um item da lista de conclusões
    
    Args:
        id (str): ID do processo
        title (str): Título do processo
        responsible (str): Nome do responsável
        date (str): Data de conclusão
    """
    st.markdown(f"""
    <div class="conclusion-item">
        <div class="conclusion-title">
            <span class="status-completo">Concluído</span>
        </div>
        <div class="conclusion-info">
            <strong>ID:</strong> {id}<br>
            <strong>Nome:</strong> {title}<br>
            <strong>Responsável:</strong> {responsible}<br>
            <strong>Concluído em:</strong> {date}
        </div>
    </div>
    """, unsafe_allow_html=True) 