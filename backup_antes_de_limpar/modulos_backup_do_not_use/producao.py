import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Importações internas
from api.bitrix_connector import load_merged_data, get_higilizacao_fields
from components.metrics import render_metrics_section
from components.tables import render_styled_table, create_pendencias_table, create_production_table
from components.filters import date_filter_section, responsible_filter, status_filter
from utils.data_processor import calculate_status_counts, filter_dataframe_by_date, create_responsible_status_table

def show_producao():
    """
    Exibe a página de produção e análise de higienização
    """
    st.title("Produção e Higienização")
    st.markdown("---")
    
    # Descrição da página
    st.markdown("""
    ## Análise de Status de Higienização
    
    Esta página apresenta métricas e análises detalhadas sobre o status de higienização dos processos no Bitrix24.
    Utilize os filtros para refinar sua visualização e análise.
    """)
    
    # Seção de filtros
    with st.expander("Filtros", expanded=True):
        # Filtro de período
        start_date, end_date = date_filter_section()
        
        # Carregar dados iniciais (com filtro de categoria 32 conforme exemplo)
        with st.spinner("Carregando dados..."):
            try:
                df = load_merged_data(category_id=32)
                
                if df.empty:
                    st.error("Não foi possível carregar dados do Bitrix24. Verifique sua conexão.")
                    return
                
                # Aplicar filtro de data
                filtered_df = filter_dataframe_by_date(df, start_date, end_date)
                
                # Filtros adicionais
                col1, col2 = st.columns(2)
                
                with col1:
                    # Filtro de responsáveis (se aplicável)
                    selected_responsibles = responsible_filter(filtered_df)
                    if selected_responsibles:
                        filtered_df = filtered_df[filtered_df['ASSIGNED_BY_NAME'].isin(selected_responsibles)]
                
                with col2:
                    # Filtro de status
                    selected_status = status_filter()
                    if selected_status:
                        # Tratar status nulos
                        status_filter_condition = (
                            filtered_df['UF_CRM_HIGILIZACAO_STATUS'].fillna('PENDENCIA').isin(selected_status)
                        )
                        filtered_df = filtered_df[status_filter_condition]
                
            except Exception as e:
                st.error(f"Erro ao processar os dados: {str(e)}")
                return
    
    # Exibir número de registros após filtros
    st.markdown(f"**{len(filtered_df)} registros** encontrados após aplicação dos filtros.")
    
    # 1. Métricas Macro
    st.markdown("## Métricas Macro")
    
    if not filtered_df.empty:
        # Calcular contagens de status
        counts = calculate_status_counts(filtered_df)
        
        # Renderizar seção de métricas
        render_metrics_section(counts)
    else:
        st.warning("Não há dados disponíveis para exibir métricas.")
    
    # 2. Tabela de Status por Responsável
    st.markdown("## Status por Responsável")
    
    if not filtered_df.empty:
        # Criar tabela cruzada de responsáveis por status
        cross_tab = create_responsible_status_table(filtered_df)
        
        if not cross_tab.empty:
            render_styled_table(cross_tab)
        else:
            st.info("Não há dados suficientes para criar a tabela de status por responsável.")
    else:
        st.warning("Não há dados disponíveis para exibir a tabela de status por responsável.")
    
    # 3. Tabela de Pendências
    st.markdown("## Pendências por Responsável")
    
    if not filtered_df.empty:
        # Criar tabela de pendências
        pendencias_df = create_pendencias_table(filtered_df)
        
        if not pendencias_df.empty:
            render_styled_table(pendencias_df, height="500px")
        else:
            st.success("Não há pendências! Todos os processos estão completos ou em andamento.")
    else:
        st.warning("Não há dados disponíveis para exibir a tabela de pendências.")
    
    # 4. Tabela de Produção
    st.markdown("## Produção Geral")
    
    if not filtered_df.empty:
        # Criar tabela de produção
        production_df = create_production_table(filtered_df)
        
        if not production_df.empty:
            render_styled_table(production_df, height="500px")
        else:
            st.info("Não há dados suficientes para criar a tabela de produção.")
    else:
        st.warning("Não há dados disponíveis para exibir a tabela de produção.")
    
    # Rodapé com informações adicionais
    st.markdown("---")
    st.markdown(f"*Dados atualizados em: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
    
    # Adicionar informações sobre os campos (expandable)
    with st.expander("Descrição dos Campos de Higienização"):
        fields = get_higilizacao_fields()
        
        for field_id, field_name in fields.items():
            st.markdown(f"**{field_name}**: `{field_id}`") 