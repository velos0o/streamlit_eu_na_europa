import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime

def handle_refresh_trigger():
    """
    Verifica se foi acionada uma atualização completa e prepara o ambiente
    para recarregar os dados.
    
    Returns:
        bool: True se uma atualização foi acionada, False caso contrário
    """
    refresh_triggered = False
    
    # Verificar se foi acionado atualização completa via botão
    if st.session_state.get('full_refresh', False):
        # Exibir indicador de atualização completa
        st.info("⏳ Realizando atualização completa dos dados...")
        
        # Limpar todos os dados em cache para forçar recarregamento
        chaves_comuns = [
            # Estados de carregamento
            'loading_state',
            'reload_trigger',
            
            # Dados comuns
            'df_inicio', 
            'filtered_df',
            'filtered_df_cat34',
            'macro_counts', 
            'conclusoes_recentes',
            'df_conclusoes',
            'df_cartorio',
            'df_comune',
            'df_extracoes',
            
            # Filtros e configurações
            'start_date',
            'end_date',
            'selected_status',
            'selected_responsibles'
        ]
        
        # Limpar cada chave se existir no estado da sessão
        for chave in chaves_comuns:
            if chave in st.session_state:
                del st.session_state[chave]
        
        # Ativar flag para forçar recarregamento ignorando cache
        st.session_state['force_reload'] = True
        
        # Limpar flag de atualização completa
        st.session_state['full_refresh'] = False
        
        refresh_triggered = True
    
    # Verificar se foi acionado atualização normal via botão
    elif st.session_state.get('reload_trigger', False):
        # Limpar alguns dados em cache
        if 'loading_state' in st.session_state:
            st.session_state['loading_state'] = 'loading'
            
        # Resetar flag de recarregamento
        st.session_state['reload_trigger'] = False
        
        refresh_triggered = True
    
    return refresh_triggered


def get_force_reload_status():
    """
    Verifica se o modo de recarregamento forçado está ativo
    
    Returns:
        bool: True se o modo de recarregamento forçado está ativo
    """
    return st.session_state.get('force_reload', False)


def clear_force_reload_flag():
    """
    Limpa a flag de recarregamento forçado após seu uso
    """
    if 'force_reload' in st.session_state:
        del st.session_state['force_reload']

def load_csv_with_refresh(filepath, **kwargs):
    """
    Carrega um arquivo CSV com suporte a atualização forçada
    
    Args:
        filepath (str): Caminho para o arquivo CSV
        **kwargs: Argumentos adicionais para pd.read_csv
        
    Returns:
        pandas.DataFrame: DataFrame com os dados do CSV
    """
    # Verificar se o arquivo existe
    if not os.path.exists(filepath):
        st.error(f"Arquivo não encontrado: {filepath}")
        return pd.DataFrame()
    
    # Obter a hora de modificação do arquivo
    file_modified_time = os.path.getmtime(filepath)
    
    # Criar uma chave única para este arquivo
    cache_key = f"csv_{filepath.replace('/', '_')}"
    
    # Verificar se precisa recarregar com base na força ou modificação
    force_reload = st.session_state.get('force_reload_files', False)
    last_refresh = st.session_state.get('last_refresh_timestamp', 0)
    
    # Se temos metadados do arquivo em cache
    if cache_key + "_time" in st.session_state:
        cached_time = st.session_state[cache_key + "_time"]
        
        # Carregar do cache se o arquivo não foi modificado e não estamos forçando recarregamento
        if cached_time >= file_modified_time and not force_reload and last_refresh < cached_time:
            if cache_key + "_data" in st.session_state:
                print(f"Usando dados em cache para {filepath}")
                return st.session_state[cache_key + "_data"]
    
    # Se chegamos aqui, precisamos recarregar o arquivo
    print(f"Carregando dados frescos de {filepath}")
    
    try:
        # Carregar arquivo com pandas
        df = pd.read_csv(filepath, **kwargs)
        
        # Armazenar no cache
        st.session_state[cache_key + "_data"] = df
        st.session_state[cache_key + "_time"] = time.time()
        
        # Debug
        print(f"Arquivo {filepath} carregado com sucesso: {len(df)} linhas.")
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo {filepath}: {str(e)}")
        return pd.DataFrame()

def load_excel_with_refresh(filepath, sheet_name=0, **kwargs):
    """
    Carrega um arquivo Excel com suporte a atualização forçada
    
    Args:
        filepath (str): Caminho para o arquivo Excel
        sheet_name: Nome ou índice da planilha a carregar
        **kwargs: Argumentos adicionais para pd.read_excel
        
    Returns:
        pandas.DataFrame: DataFrame com os dados do Excel
    """
    # Verificar se o arquivo existe
    if not os.path.exists(filepath):
        st.error(f"Arquivo não encontrado: {filepath}")
        return pd.DataFrame()
    
    # Obter a hora de modificação do arquivo
    file_modified_time = os.path.getmtime(filepath)
    
    # Criar uma chave única para este arquivo e planilha
    sheet_identifier = sheet_name if isinstance(sheet_name, str) else f"sheet_{sheet_name}"
    cache_key = f"excel_{filepath.replace('/', '_')}_{sheet_identifier}"
    
    # Verificar se precisa recarregar com base na força ou modificação
    force_reload = st.session_state.get('force_reload_files', False)
    last_refresh = st.session_state.get('last_refresh_timestamp', 0)
    
    # Se temos metadados do arquivo em cache
    if cache_key + "_time" in st.session_state:
        cached_time = st.session_state[cache_key + "_time"]
        
        # Carregar do cache se o arquivo não foi modificado e não estamos forçando recarregamento
        if cached_time >= file_modified_time and not force_reload and last_refresh < cached_time:
            if cache_key + "_data" in st.session_state:
                print(f"Usando dados em cache para {filepath} (sheet: {sheet_name})")
                return st.session_state[cache_key + "_data"]
    
    # Se chegamos aqui, precisamos recarregar o arquivo
    print(f"Carregando dados frescos de {filepath} (sheet: {sheet_name})")
    
    try:
        # Carregar arquivo com pandas
        df = pd.read_excel(filepath, sheet_name=sheet_name, **kwargs)
        
        # Armazenar no cache
        st.session_state[cache_key + "_data"] = df
        st.session_state[cache_key + "_time"] = time.time()
        
        # Debug
        print(f"Arquivo {filepath} (sheet: {sheet_name}) carregado com sucesso: {len(df)} linhas.")
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo {filepath}: {str(e)}")
        return pd.DataFrame()

def clear_file_cache():
    """
    Limpa o cache de todos os arquivos carregados
    """
    # Identificar todas as chaves de cache de arquivos
    file_cache_keys = [k for k in st.session_state.keys() 
                       if k.startswith("csv_") or k.startswith("excel_")]
    
    # Remover todas as chaves
    for key in file_cache_keys:
        del st.session_state[key]
    
    # Definir flag para forçar recarregamento
    st.session_state['force_reload_files'] = True
    
    # Atualizar timestamp
    st.session_state['last_refresh_timestamp'] = time.time()
    
    print(f"Cache de arquivos limpo: {len(file_cache_keys)} entradas removidas") 