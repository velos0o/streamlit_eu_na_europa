import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def date_filter_section():
    """
    Renderiza seção de filtro por data
    
    Returns:
        tuple: (data_inicial, data_final) selecionadas
    """
    st.markdown("### Filtro de Período")
    
    col1, col2 = st.columns(2)
    
    # Data padrão: 30 dias atrás até hoje
    default_start = datetime.now() - timedelta(days=30)
    default_end = datetime.now()
    
    with col1:
        start_date = st.date_input(
            "Data Inicial",
            value=default_start,
            format="DD/MM/YYYY"
        )
    
    with col2:
        end_date = st.date_input(
            "Data Final",
            value=default_end,
            format="DD/MM/YYYY"
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