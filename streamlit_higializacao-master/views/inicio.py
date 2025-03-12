import streamlit as st
import pandas as pd
from api.bitrix_connector import load_merged_data
from components.metrics import render_metrics_section, render_conclusion_item
from components.tables import create_responsible_status_table, create_pendencias_table, create_production_table
from utils.data_processor import calculate_status_counts
from utils.animation_utils import display_loading_animation, clear_loading_animation

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

def show_inicio():
    """
    Exibe a página inicial do dashboard
    """
    st.title("Dashboard CRM Bitrix24")
    st.markdown("---")
    
    # Resumo do projeto
    st.markdown("""
    ## Bem-vindo ao Dashboard Analítico
    
    Este dashboard foi desenvolvido para análise de dados do CRM Bitrix24, 
    com foco na visualização e análise do status de higienização de processos.
    """)
    
    # Inicializar as variáveis de sessão se não existirem
    if 'home_data_loaded' not in st.session_state:
        st.session_state['home_data_loaded'] = False
    
    # Adicionar botão para carregar dados
    load_button = st.button("Carregar Dados do Bitrix24", key="load_data_button", type="primary")
    
    if load_button or st.session_state['home_data_loaded']:
        if not st.session_state['home_data_loaded']:
            with st.container():
                progress_bar, animation_container, message_container = display_loading_animation(
                    "Carregando dados...",
                    min_display_time=3
                )
                
                try:
                    # Carregar dados sem filtro de data
                    df = load_merged_data(
                        category_id=32,
                        debug=False,
                        progress_bar=progress_bar,
                        message_container=message_container
                    )
                    
                    clear_loading_animation(progress_bar, animation_container, message_container)
                    
                    if not df.empty:
                        st.session_state['home_data_loaded'] = True
                        st.session_state['home_data'] = df
                        
                        # Exibir as métricas e visualizações
                        _show_dashboard_content(df)
                    else:
                        st.info("Nenhum dado encontrado para o período selecionado.")
                        
                except Exception as e:
                    clear_loading_animation(progress_bar, animation_container, message_container)
                    st.error(f"Erro ao carregar dados: {str(e)}")
        else:
            # Usar dados em cache
            df = st.session_state['home_data']
            _show_dashboard_content(df)
    else:
        # Informações iniciais quando os dados não foram carregados
        st.info("Clique no botão acima para carregar os dados do Bitrix24.")
        
        # Exibir informações de amostra ou estatísticas pré-calculadas
        st.markdown("### Estatísticas de Exemplo")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pendências", "--")
        with col2:
            st.metric("Incompletos", "--")
        with col3:
            st.metric("Concluídos", "--")

def _show_dashboard_content(df):
    """
    Função auxiliar para exibir o conteúdo do dashboard após o carregamento dos dados
    """
    # Exibir métricas
    counts = calculate_status_counts(df)
    st.subheader("Resumo de Métricas")
    render_metrics_section(counts)
    
    # Criar tabs para as diferentes visualizações
    tab1, tab2, tab3 = st.tabs([
        "Status por Responsável",
        "Pendências por Responsável",
        "Produção Geral"
    ])
    
    # Tab de Status por Responsável
    with tab1:
        st.markdown("""
        <style>
        .dataframe {
            width: 100% !important;
            max-height: 600px !important;
            overflow: auto !important;
        }
        </style>
        """, unsafe_allow_html=True)
        status_table = create_responsible_status_table(df)
        st.dataframe(
            status_table,
            use_container_width=True,
            height=500
        )
    
    # Tab de Pendências
    with tab2:
        pendencias_table = create_pendencias_table(df)
        st.dataframe(
            pendencias_table,
            use_container_width=True,
            height=500
        )
    
    # Tab de Produção Geral
    with tab3:
        production_table = create_production_table(df)
        st.dataframe(
            production_table,
            use_container_width=True,
            height=500
        )
    
    # Últimas conclusões
    st.markdown("### Últimas Conclusões")
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
    
    # Rodapé
    st.markdown("---")
    st.markdown("*Dashboard em desenvolvimento. Última atualização: Agosto 2024*") 