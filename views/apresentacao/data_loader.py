import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import traceback
from api.bitrix_connector import load_merged_data, get_higilizacao_fields

# Definir a função update_progress localmente para evitar problemas de importação
def update_progress(progress_bar, progress_value, message_container, message):
    """
    Atualiza a barra de progresso e mensagem durante o carregamento
    
    Args:
        progress_bar: Componente de barra de progresso do Streamlit
        progress_value: Valor de progresso entre 0 e 1
        message_container: Container para exibir mensagens de progresso
        message: Mensagem a ser exibida
    """
    # Atualizar a barra de progresso
    progress_bar.progress(progress_value)
    
    # Atualizar a mensagem
    message_container.info(message)

def carregar_dados_apresentacao(date_from=None, date_to=None, progress_bar=None, message_container=None):
    """
    Carrega dados específicos para a apresentação de conclusões
    """
    # Carregar dados do Bitrix com a mesma lógica do módulo de conclusões
    df = load_merged_data(
        category_id=32,
        date_from=date_from,
        date_to=date_to,
        debug=False,
        progress_bar=progress_bar,
        message_container=message_container
    )
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Guardar DataFrame completo antes de filtros
    df_todos = df.copy()
    
    # Converter campos de data para análise
    if 'UF_CRM_1741206763' in df.columns:
        df['DATA_CONCLUSAO'] = pd.to_datetime(df['UF_CRM_1741206763'], errors='coerce')
        df_todos['DATA_CONCLUSAO'] = df['DATA_CONCLUSAO'].copy()
        
        # Filtrar por data
        if date_from and date_to:
            date_from_dt = pd.to_datetime(date_from)
            date_to_dt = pd.to_datetime(date_to) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            df = df[
                (df['DATA_CONCLUSAO'].notna()) & 
                (df['DATA_CONCLUSAO'] >= date_from_dt) & 
                (df['DATA_CONCLUSAO'] <= date_to_dt)
            ]
    else:
        df['DATA_CONCLUSAO'] = None
        df_todos['DATA_CONCLUSAO'] = None
    
    # Filtrar apenas registros com status COMPLETO
    df_conclusoes = df[df['UF_CRM_HIGILIZACAO_STATUS'] == 'COMPLETO'].copy()
    
    # Adicionar colunas para análise
    if not df_conclusoes.empty and 'DATA_CONCLUSAO' in df_conclusoes.columns:
        df_conclusoes['DIA_SEMANA'] = df_conclusoes['DATA_CONCLUSAO'].dt.day_name()
        df_conclusoes['SEMANA'] = df_conclusoes['DATA_CONCLUSAO'].dt.strftime('%Y-%V')
        df_conclusoes['HORA'] = df_conclusoes['DATA_CONCLUSAO'].dt.hour
        
        # Ordenar por data
        df_conclusoes = df_conclusoes.sort_values('DATA_CONCLUSAO')
    
    return df_conclusoes, df_todos

def carregar_dados_producao(date_from=None, date_to=None, progress_bar=None, message_container=None):
    """
    Carrega dados específicos para a apresentação de produção
    """
    try:
        # Formatar datas para a API
        date_from_str = date_from if isinstance(date_from, str) else date_from.strftime("%Y-%m-%d") if isinstance(date_from, datetime) else None
        date_to_str = date_to if isinstance(date_to, str) else date_to.strftime("%Y-%m-%d") if isinstance(date_to, datetime) else None
        
        # Carregar dados de produção
        df = load_merged_data(
            category_id=32,  # Mesma categoria usada no módulo de produção
            date_from=date_from_str,
            date_to=date_to_str,
            debug=False,
            progress_bar=progress_bar,
            message_container=message_container
        )
        
        if df.empty:
            if message_container:
                message_container.warning("Não foram encontrados dados de produção. Tentando usar dados de demonstração...")
            
            try:
                # Usar dados de demonstração como fallback
                from views.producao import generate_demo_data
                df = generate_demo_data()
                if message_container:
                    message_container.success("Usando dados de demonstração de produção")
                print("Usando dados de demonstração para produção")
            except Exception as e:
                print(f"Erro ao gerar dados de demonstração: {str(e)}")
                if message_container:
                    message_container.error(f"Erro ao gerar dados de demonstração: {str(e)}")
                return pd.DataFrame()
        
        # Verificar e corrigir colunas necessárias de higienização
        fields = get_higilizacao_fields()
        for field in fields:
            # Garantir que todas as colunas necessárias existam
            field_id = field.get('FIELD_ID', '')
            if field_id and field_id not in df.columns:
                df[field_id] = np.nan
        
        # Adicionar campo de status se não existir
        if 'UF_CRM_HIGILIZACAO_STATUS' not in df.columns:
            df['UF_CRM_HIGILIZACAO_STATUS'] = 'PENDENCIA'
            
        # Calcular campos adicionais para análise
        df['PENDENTE'] = ~df['UF_CRM_HIGILIZACAO_STATUS'].isin(['COMPLETO', 'INCOMPLETO'])
        
        return df
        
    except Exception as e:
        print(f"Erro ao carregar dados de produção: {str(e)}")
        print(traceback.format_exc())
        
        if progress_bar:
            update_progress(progress_bar, 1.0, message_container, f"Erro ao carregar dados de produção: {str(e)}")
        if message_container:
            message_container.error(f"Erro ao carregar dados de produção: {str(e)}")
        
        return pd.DataFrame()

def carregar_dados_cartorio(progress_bar=None, message_container=None):
    """
    Carrega dados específicos para a apresentação de cartório
    """
    try:
        # Importar diretamente a função load_data que sabemos que existe
        from views.cartorio.data_loader import load_data
        
        # Carregar dados usando a função importada
        df_cartorio = load_data()
        
        if progress_bar:
            update_progress(progress_bar, 0.9, message_container, "Dados do cartório carregados com sucesso")
        
        if df_cartorio is None or df_cartorio.empty:
            print("Dados do cartório estão vazios!")
            if message_container:
                message_container.warning("Dados do cartório estão vazios!")
            return pd.DataFrame()
        
        print(f"Dados do cartório carregados com sucesso: {len(df_cartorio)} registros")
        
        # Filtro padrão para cartórios
        cartorio_filter = ["CARTÓRIO CASA VERDE", "CARTÓRIO TATUÁPE"]
        df_cartorio = df_cartorio[df_cartorio['NOME_CARTORIO'].isin(cartorio_filter)]
        
        return df_cartorio
        
    except Exception as e:
        print(f"Erro ao carregar dados de cartório: {str(e)}")
        print(traceback.format_exc())
        
        if progress_bar:
            update_progress(progress_bar, 1.0, message_container, f"Erro ao carregar dados de cartório: {str(e)}")
        if message_container:
            message_container.error(f"Erro ao carregar dados de cartório: {str(e)}")
        
        return pd.DataFrame()
