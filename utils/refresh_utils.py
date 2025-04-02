import streamlit as st

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