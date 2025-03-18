import streamlit as st
import pandas as pd
from api.bitrix_connector import load_merged_data
from components.metrics import render_metrics_section
from utils.data_processor import calculate_status_counts

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
    
    Utilize o menu lateral para navegar entre as diferentes seções do dashboard.
    """)
    
    st.markdown("---")
    
    # Carregando dados para exibir métricas resumidas
    with st.spinner("Carregando dados gerais..."):
        try:
            # Carregamos dados com categoria 32 (conforme exemplo)
            df = load_merged_data(category_id=32)
            
            if not df.empty:
                # Calcular métricas gerais
                counts = calculate_status_counts(df)
                
                # Exibir seção de métricas
                st.subheader("Resumo de Métricas")
                render_metrics_section(counts)
                
                # Últimas atualizações
                st.markdown("### Últimas Atualizações")
                
                # Ordenar por data de modificação (se existir)
                if 'DATE_MODIFY' in df.columns:
                    recent_df = df.sort_values('DATE_MODIFY', ascending=False).head(5)
                    
                    # Exibir tabela simplificada
                    if not recent_df.empty:
                        recent_table = pd.DataFrame({
                            'Título': recent_df.get('TITLE', ''),
                            'Responsável': recent_df.get('ASSIGNED_BY_NAME', ''),
                            'Status': recent_df.get('UF_CRM_HIGILIZACAO_STATUS', ''),
                            'Atualizado': pd.to_datetime(recent_df['DATE_MODIFY']).dt.strftime('%d/%m/%Y %H:%M')
                        })
                        st.dataframe(recent_table, use_container_width=True)
            else:
                st.warning("Não foi possível carregar os dados. Verifique sua conexão com o Bitrix24.")
                
        except Exception as e:
            st.error(f"Erro ao carregar os dados: {str(e)}")
    
    # Rodapé
    st.markdown("---")
    st.markdown("*Dashboard em desenvolvimento. Última atualização: Agosto 2024*") 