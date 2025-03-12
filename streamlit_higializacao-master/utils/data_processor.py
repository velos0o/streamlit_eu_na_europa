import pandas as pd
import numpy as np
import streamlit as st

def format_status_text(value):
    """
    Formata o texto de status para exibição
    
    Args:
        value: Valor do status
        
    Returns:
        str: Texto formatado do status
    """
    if not value or pd.isna(value):
        return "Pendente"
    
    value = str(value).strip().upper()
    
    if value == "SIM":
        return "Completo"
    elif value in ["COMPLETO", "COMPLETE"]:
        return "Completo"
    elif value == "INCOMPLETO":
        return "Incompleto"
    elif value == "PENDENCIA" or value == "PENDÊNCIA":
        return "Pendência"
    else:
        return value

def calculate_status_counts(df):
    """
    Calcula as contagens de status de higienização
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        
    Returns:
        dict: Dicionário com as contagens
    """
    # Verificar se o DataFrame está vazio
    if df.empty:
        return {
            'total': 0,
            'pendente': 0,
            'pendente_pct': 0,
            'incompleto': 0,
            'incompleto_pct': 0,
            'completo': 0,
            'completo_pct': 0
        }
    
    # Campos necessários
    status_field = 'UF_CRM_HIGILIZACAO_STATUS'
    deal_id = 'ID'  # ID na tabela crm_deal
    uf_deal_id = 'DEAL_ID'  # ID na tabela crm_deal_uf
    
    # Verificar se temos os campos necessários
    if not all(field in df.columns for field in [deal_id, status_field]):
        print("Campos necessários não encontrados!")
        print(f"Colunas disponíveis: {df.columns.tolist()}")
        return {
            'total': len(df),
            'pendente': len(df),
            'pendente_pct': 100,
            'incompleto': 0,
            'incompleto_pct': 0,
            'completo': 0,
            'completo_pct': 0
        }
    
    # Garantir que estamos usando apenas registros únicos
    if uf_deal_id in df.columns:
        # Se temos ambos os IDs, usar o DEAL_ID para remover duplicatas
        df = df.drop_duplicates(subset=[uf_deal_id])
    else:
        # Caso contrário, usar o ID da tabela principal
        df = df.drop_duplicates(subset=[deal_id])
    
    # Total de negócios é o total de IDs únicos no funil 32 (sem filtragem)
    total = len(df)
    
    # Tratar valores nulos/vazios no status
    # Consideramos valores nulos ou vazios como PENDENTE
    pendentes = df[df[status_field].isna() | (df[status_field] == '')].shape[0]
    pendentes += df[df[status_field].str.upper() == 'PENDENCIA'].shape[0] if not df[status_field].isna().all() else 0
    
    # Contagem para status explícitos
    completos = df[df[status_field].str.upper() == 'COMPLETO'].shape[0] if not df[status_field].isna().all() else 0
    incompletos = df[df[status_field].str.upper() == 'INCOMPLETO'].shape[0] if not df[status_field].isna().all() else 0
    
    # Verificar se há algum status não reconhecido
    outros = total - (completos + incompletos + pendentes)
    if outros > 0:
        print(f"\nAVISO: {outros} registros com status não reconhecido")
        outros_status = df[~df[status_field].isin(['COMPLETO', 'INCOMPLETO', 'PENDENCIA']) & ~df[status_field].isna() & (df[status_field] != '')][status_field].unique()
        print(f"Status não reconhecidos: {outros_status}")
        # Adicionar registros não reconhecidos aos pendentes
        pendentes += outros
    
    # Calcular percentuais
    completos_pct = (completos / total * 100) if total > 0 else 0
    incompletos_pct = (incompletos / total * 100) if total > 0 else 0
    pendentes_pct = (pendentes / total * 100) if total > 0 else 0
    
    # Debug: imprimir distribuição detalhada
    print("\nDistribuição detalhada de status:")
    print(f"Total de registros: {total}")
    print(f"Pendências (PENDENCIA + vazios): {pendentes} ({pendentes_pct:.1f}%)")
    print(f"Incompletos: {incompletos} ({incompletos_pct:.1f}%)")
    print(f"Concluídos: {completos} ({completos_pct:.1f}%)")
    
    if uf_deal_id in df.columns:
        print("\nVerificação de IDs:")
        print(f"Total de IDs únicos em crm_deal: {df[deal_id].nunique()}")
        print(f"Total de IDs únicos em crm_deal_uf: {df[uf_deal_id].nunique()}")
    
    return {
        'total': total,
        'pendente': pendentes,
        'pendente_pct': round(pendentes_pct, 1),
        'incompleto': incompletos,
        'incompleto_pct': round(incompletos_pct, 1),
        'completo': completos,
        'completo_pct': round(completos_pct, 1)
    }

def filter_dataframe_by_date(df, start_date, end_date, date_column='UF_CRM_1741206763'):
    """
    Filtra DataFrame por intervalo de datas
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        start_date (datetime): Data inicial
        end_date (datetime): Data final
        date_column (str): Nome da coluna de data
        
    Returns:
        pandas.DataFrame: DataFrame filtrado
    """
    if df.empty or date_column not in df.columns:
        return df
    
    # Converter a coluna para datetime
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    
    # Aplicar filtro de data
    return df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]

def get_completion_status(row, higilizacao_fields):
    """
    Determina o status de conclusão com base nos campos de higienização
    
    Args:
        row (pandas.Series): Linha do DataFrame
        higilizacao_fields (list): Lista de campos de higienização
        
    Returns:
        str: Status de conclusão
    """
    # Remover UF_CRM_HIGILIZACAO_STATUS da lista de verificação
    fields_to_check = [f for f in higilizacao_fields if f != 'UF_CRM_HIGILIZACAO_STATUS']
    
    # Contar quantos campos estão preenchidos com 'sim'
    completed = sum(1 for field in fields_to_check if str(row.get(field, '')).upper() == 'SIM')
    total = len(fields_to_check)
    
    if completed == 0:
        return 'PENDENCIA'
    elif completed < total:
        return 'INCOMPLETO'
    else:
        return 'COMPLETO'

def create_responsible_status_table(df, responsible_column='ASSIGNED_BY_NAME'):
    """
    Cria tabela de status por responsável
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        responsible_column (str): Nome da coluna de responsável
        
    Returns:
        pandas.DataFrame: Tabela cruzada de responsáveis por status
    """
    if df.empty or responsible_column not in df.columns or 'UF_CRM_HIGILIZACAO_STATUS' not in df.columns:
        return pd.DataFrame()
    
    # Substituir valores nulos no status por 'PENDENCIA'
    df['UF_CRM_HIGILIZACAO_STATUS'] = df['UF_CRM_HIGILIZACAO_STATUS'].fillna('PENDENCIA')
    
    # Criar tabela cruzada
    cross_tab = pd.crosstab(
        index=df[responsible_column], 
        columns=df['UF_CRM_HIGILIZACAO_STATUS'].str.upper(), 
        margins=True,
        margins_name='Total'
    )
    
    # Certificar que todas as colunas de status existem
    for status in ['COMPLETO', 'INCOMPLETO', 'PENDENCIA']:
        if status not in cross_tab.columns:
            cross_tab[status] = 0
    
    # Reordenar as colunas
    ordered_columns = [col for col in ['COMPLETO', 'INCOMPLETO', 'PENDENCIA', 'Total'] if col in cross_tab.columns]
    return cross_tab[ordered_columns] 