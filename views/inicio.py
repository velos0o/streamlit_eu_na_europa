import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
from api.bitrix_connector import load_merged_data
from components.metrics import render_metrics_section, render_conclusion_item
from components.tables import create_responsible_status_table, create_pendencias_table, create_production_table
from components.table_of_contents import create_section_anchor, create_section_header

# Obter o caminho absoluto para a pasta utils
utils_path = os.path.join(Path(__file__).parents[1], 'utils')
sys.path.insert(0, str(utils_path))

# Agora importa diretamente dos arquivos na pasta utils
from data_processor import calculate_status_counts
from animation_utils import display_loading_animation, clear_loading_animation

def format_date_br(date):
    """
    Formata a data no padrão brasileiro, ajustando o fuso horário para corresponder ao Bitrix24
    """
    if pd.isna(date):
        return 'N/A'
    
    # Converter para datetime se for string
    if isinstance(date, str):
        date = pd.to_datetime(date)
    
    # Ajustar -6 horas para corresponder ao horário do Bitrix24
    date = date - pd.Timedelta(hours=6)
    
    # Formatar no padrão brasileiro
    return date.strftime('%d/%m/%Y %H:%M')

# Função para carregar dados - será chamada automaticamente
def load_data():
    if 'home_data' not in st.session_state or st.session_state.get('force_reload', False):
        st.session_state['force_reload'] = False
        
        with st.spinner("Carregando dados..."):
            try:
                # Carregar dados sem filtro de data
                df = load_merged_data(
                    category_id=32,
                    debug=False,
                    progress_bar=None,
                    message_container=None
                )
                
                if not df.empty:
                    st.session_state['home_data'] = df
                else:
                    st.session_state['home_data'] = pd.DataFrame()
                    
            except Exception as e:
                st.error(f"Erro ao carregar dados: {str(e)}")
                st.session_state['home_data'] = pd.DataFrame()

def show_inicio():
    """
    Exibe a página inicial do dashboard
    """
    # Verificar se está no modo de demonstração
    demo_mode = st.session_state.get('demo_mode', False)
    
    # Verificar se foi acionado atualização via botão flutuante
    if st.session_state.get('reload_trigger', False):
        # Limpar dados em cache para forçar recarregamento
        for key in ['df_inicio', 'macro_counts', 'conclusoes_recentes']:
            if key in st.session_state:
                del st.session_state[key]
        
        # Resetar flag de recarregamento
        st.session_state['reload_trigger'] = False
        st.rerun()
    
    st.title("Dashboard CRM Bitrix24")
    st.markdown("---")
    
    # Resumo do projeto
    st.markdown("""
    ## Bem-vindo ao Dashboard Analítico
    
    Este dashboard foi desenvolvido para análise de dados do CRM Bitrix24, 
    com foco na visualização e análise do status de higienização de processos.
    """)
    
    # Carregar dados automaticamente na inicialização
    load_data()
    
    # Botão para recarregar dados manualmente
    if st.button("Atualizar Dados"):
        st.session_state['force_reload'] = True
        st.experimental_rerun()
    
    # Exibir as informações se houver dados
    if 'home_data' in st.session_state and not st.session_state['home_data'].empty:
        df = st.session_state['home_data']
        
        # Criar âncora e cabeçalho para a seção de métricas gerais
        create_section_anchor("metricas_gerais")
        st.subheader("Métricas Gerais")
        
        # Exibir métricas
        counts = calculate_status_counts(df)
        render_metrics_section(counts)
        
        # Criar âncora e cabeçalho para a seção de últimas conclusões
        create_section_anchor("ultimas_conclusoes")
        st.subheader("Últimas Conclusões")
        
        # Últimas conclusões
        if 'DATE_MODIFY' in df.columns:
            completed_df = df[df['UF_CRM_HIGILIZACAO_STATUS'] == 'COMPLETO']
            if not completed_df.empty:
                recent_df = completed_df.sort_values('DATE_MODIFY', ascending=False).head(5)
                for _, row in recent_df.iterrows():
                    render_conclusion_item(
                        id=row.get('ID', 'N/A'),
                        title=row.get('TITLE', 'N/A'),
                        responsible=row.get('ASSIGNED_BY_NAME', 'N/A'),
                        date=format_date_br(row.get('DATE_MODIFY'))
                    )
            else:
                st.info("Nenhum processo concluído encontrado.")
    else:
        st.info("Nenhum dado encontrado para o período selecionado.")
    
    # Rodapé
    st.markdown("---")
    st.markdown("*Dashboard em desenvolvimento. Última atualização: Agosto 2024*")

# Adiciona código de inicialização para executar no início do script
if __name__ == "__main__":
    show_inicio() 