import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def date_filter_section(title="Filtro de Período", on_change=None):
    """
    Renderiza seção de filtro por data
    
    Args:
        title (str): Título personalizado para a seção de filtro
        on_change (callable, optional): Função para chamar quando as datas são alteradas
    
    Returns:
        tuple: (data_inicial, data_final) selecionadas ou (None, None) se sem filtro
    """
    st.markdown(f"### {title}")
    
    # Opção para desativar o filtro de data
    sem_filtro_data = st.checkbox("Sem filtro de data", value=False, key=f"sem_filtro_{title.replace(' ', '_').lower()}")
    
    if sem_filtro_data:
        return None, None
    
    col1, col2 = st.columns(2)
    
    # Data padrão: 30 dias atrás até hoje
    default_start = datetime.now() - timedelta(days=30)
    default_end = datetime.now()
    
    with col1:
        start_date = st.date_input(
            "Data Inicial",
            value=default_start,
            format="DD/MM/YYYY",
            on_change=on_change if on_change else None
        )
    
    with col2:
        end_date = st.date_input(
            "Data Final",
            value=default_end,
            format="DD/MM/YYYY",
            on_change=on_change if on_change else None
        )
    
    # Converter para datetime para comparações
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    return start_datetime, end_datetime

def responsible_filter(df, responsible_column='ASSIGNED_BY_NAME'):
    """
    Renderiza filtro de responsáveis
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        responsible_column (str): Nome da coluna de responsável
        
    Returns:
        list: Lista de responsáveis selecionados
    """
    if df.empty or responsible_column not in df.columns:
        return []
    
    # Obter lista única de responsáveis
    responsibles = sorted(df[responsible_column].unique().tolist())
    
    # Adicionar opção "Todos"
    all_option = "Todos"
    options = [all_option] + responsibles
    
    # Criar o seletor
    selected = st.multiselect(
        "Filtrar por Responsável",
        options=options,
        default=[all_option]
    )
    
    # Se "Todos" estiver selecionado, retorna todos os responsáveis
    if all_option in selected:
        return responsibles
    
    return selected

def status_filter():
    """
    Renderiza filtro de status de higienização
    
    Returns:
        list: Lista de status selecionados
    """
    # Opções de status
    status_options = ["Todos", "Completo", "Incompleto", "Pendente"]
    
    # Criar o seletor
    selected = st.multiselect(
        "Filtrar por Status",
        options=status_options,
        default=["Todos"]
    )
    
    # Mapear para valores internos do sistema
    status_map = {
        "Completo": "COMPLETO",
        "Incompleto": "INCOMPLETO",
        "Pendente": "PENDENCIA"
    }
    
    # Se "Todos" estiver selecionado, retorna todos os status
    if "Todos" in selected:
        return list(status_map.values())
    
    # Converter para valores internos
    return [status_map[s] for s in selected if s in status_map]

def create_filter_section(df, include_date=True, include_responsible=True, include_status=True, date_title="Filtro de Período"):
    """
    Cria uma seção completa de filtros combinando os diferentes tipos de filtro disponíveis.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        include_date (bool): Se deve incluir filtro de data
        include_responsible (bool): Se deve incluir filtro de responsável
        include_status (bool): Se deve incluir filtro de status
        date_title (str): Título personalizado para a seção de filtro de data
    
    Returns:
        dict: Dicionário com os filtros aplicados
        {
            'date_range': (data_inicial, data_final),
            'responsibles': [lista_de_responsaveis],
            'status': [lista_de_status]
        }
    """
    filters = {}
    
    with st.expander("📊 Filtros", expanded=True):
        if include_date:
            filters['date_range'] = date_filter_section(title=date_title)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if include_responsible and not df.empty:
                filters['responsibles'] = responsible_filter(df)
        
        with col2:
            if include_status:
                filters['status'] = status_filter()
                
        # Botão para aplicar os filtros
        if st.button("Aplicar Filtros", use_container_width=True):
            st.rerun()
    
    return filters 