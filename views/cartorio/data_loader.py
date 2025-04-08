import streamlit as st
import pandas as pd
from api.bitrix_connector import load_bitrix_data, get_credentials
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def load_data():
    """
    Carrega dados do cartório
    """
    # Obter token do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # URL para acessar a tabela crm_dynamic_items_1052
    url_items = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1052"
    
    # Carregar os dados
    df_items = load_bitrix_data(url_items)
    
    # Se o DataFrame estiver vazio, retornar DataFrame vazio
    if df_items is None or df_items.empty:
        st.error("Não foi possível carregar os dados dos cartórios. Verifique a conexão com o Bitrix24.")
        return pd.DataFrame()
    
    # Filtrar apenas os cartórios Casa Verde (16) e Tatuápe (34)
    df_filtrado = df_items[df_items['CATEGORY_ID'].isin([16, 34])].copy()  # Usar .copy() para evitar SettingWithCopyWarning
    
    # Adicionar o nome do cartório para melhor visualização
    df_filtrado.loc[:, 'NOME_CARTORIO'] = df_filtrado['CATEGORY_ID'].map({
        16: 'CARTÓRIO CASA VERDE',
        34: 'CARTÓRIO TATUÁPE'
    })
    
    return df_filtrado

def carregar_dados_negocios():
    """
    Carrega os dados dos negócios da categoria 32 e seus campos personalizados
    
    Returns:
        tuple: (DataFrame com negócios, DataFrame com campos personalizados)
    """
    # Obter token do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # URLs para acessar as tabelas
    url_deal = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
    url_deal_uf = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
    
    # Preparar filtro para a categoria 32
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["32"], 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    # Carregar dados principais dos negócios com filtro de categoria
    df_deal = load_bitrix_data(url_deal, filters=category_filter)
    
    # Verificar se conseguiu carregar os dados
    if df_deal.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    # Simplificar: selecionar apenas as colunas necessárias
    df_deal = df_deal[['ID', 'TITLE', 'ASSIGNED_BY_NAME']]
    
    # Obter lista de IDs dos deals para filtrar a tabela crm_deal_uf
    deal_ids = df_deal['ID'].astype(str).tolist()
    
    # Limitar a quantidade de IDs para evitar sobrecarga (se houverem muitos)
    if len(deal_ids) > 1000:
        deal_ids = deal_ids[:1000]
    
    # Filtro para crm_deal_uf baseado nos IDs dos deals da categoria 32
    deal_filter = {"dimensionsFilters": [[]]}
    deal_filter["dimensionsFilters"][0].append({
        "fieldName": "DEAL_ID", 
        "values": deal_ids, 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    # Carregar dados da tabela crm_deal_uf (onde estão os campos personalizados do funil de negócios)
    df_deal_uf = load_bitrix_data(url_deal_uf, filters=deal_filter)
    
    # Verificar se conseguiu carregar os dados
    if df_deal_uf.empty:
        return df_deal, pd.DataFrame()
    
    # Verificar se a coluna UF_CRM_HIGILIZACAO_STATUS existe
    colunas_obrigatorias = ['DEAL_ID', 'UF_CRM_1722605592778']
    colunas_selecionadas = colunas_obrigatorias.copy()
    
    # Adicionar UF_CRM_HIGILIZACAO_STATUS se existir
    if 'UF_CRM_HIGILIZACAO_STATUS' in df_deal_uf.columns:
        colunas_selecionadas.append('UF_CRM_HIGILIZACAO_STATUS')
    
    # Simplificar: manter apenas as colunas necessárias
    df_deal_uf = df_deal_uf[colunas_selecionadas]
    
    return df_deal, df_deal_uf

def carregar_estagios_bitrix():
    """
    Carrega os estágios dos funis do Bitrix24
    
    Returns:
        pandas.DataFrame: DataFrame com os estágios
    """
    # Obter token e URL do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # Obter estágios únicos do pipeline
    url_stages = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_status"
    df_stages = load_bitrix_data(url_stages)
    
    return df_stages

def carregar_dados_crm_deal_com_uf():
    """
    Carrega dados de CRM_DEAL e CRM_DEAL_UF com foco no campo UF_CRM_1722605592778
    e filtrando por categoria = 0
    
    Returns:
        pandas.DataFrame: DataFrame com os dados mesclados entre CRM_DEAL e CRM_DEAL_UF
    """
    # Obter token do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # URLs para acessar as tabelas
    url_deal = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
    url_deal_uf = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
    
    # Preparar filtro para a categoria 0
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["0"], 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    # Carregar dados principais dos negócios com filtro de categoria
    df_deal = load_bitrix_data(url_deal, filters=category_filter)
    
    # Verificar se conseguiu carregar os dados
    if df_deal.empty:
        st.warning("Não foi possível carregar os dados da tabela crm_deal para a categoria 0.")
        return pd.DataFrame()
    
    # Incluir mais colunas necessárias, especialmente DATE_CREATE para o filtro de data
    colunas_necessarias = ['ID', 'TITLE', 'CATEGORY_ID', 'ASSIGNED_BY_NAME', 'DATE_CREATE']
    colunas_presentes = [col for col in colunas_necessarias if col in df_deal.columns]
    
    # Verificar se temos a coluna de data
    if 'DATE_CREATE' not in colunas_presentes:
        st.warning("Campo DATE_CREATE não encontrado na tabela crm_deal. A filtragem por data pode não funcionar corretamente.")
    
    # Selecionar apenas as colunas necessárias que existem no DataFrame
    df_deal = df_deal[colunas_presentes]
    
    # Obter lista de IDs dos deals para filtrar a tabela crm_deal_uf
    deal_ids = df_deal['ID'].astype(str).tolist()
    
    # Limitar a quantidade de IDs para evitar sobrecarga (se houverem muitos)
    if len(deal_ids) > 1000:
        deal_ids = deal_ids[:1000]
    
    # Filtro para crm_deal_uf baseado nos IDs dos deals da categoria 0
    deal_filter = {"dimensionsFilters": [[]]}
    deal_filter["dimensionsFilters"][0].append({
        "fieldName": "DEAL_ID", 
        "values": deal_ids, 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    # Carregar dados da tabela crm_deal_uf (onde estão os campos personalizados)
    df_deal_uf = load_bitrix_data(url_deal_uf, filters=deal_filter)
    
    # Verificar se conseguiu carregar os dados
    if df_deal_uf.empty:
        st.warning("Não foi possível carregar os dados da tabela crm_deal_uf para a categoria 0.")
        return df_deal
    
    # Verificar se a coluna UF_CRM_1722605592778 existe (antigo: UF_CRM_1725397957843)
    colunas_obrigatorias = ['DEAL_ID', 'UF_CRM_1722605592778']
    colunas_existentes = [col for col in colunas_obrigatorias if col in df_deal_uf.columns]
    
    if 'UF_CRM_1722605592778' not in df_deal_uf.columns:
        st.warning("Campo UF_CRM_1722605592778 não encontrado na tabela crm_deal_uf.")
    
    # Selecionando colunas relevantes (incluindo UF_CRM_1722605592778 se existir)
    df_deal_uf_filtrado = df_deal_uf[colunas_existentes]
    
    # Mesclar os dados de deal e deal_uf
    df_mesclado = pd.merge(
        df_deal,
        df_deal_uf_filtrado,
        left_on='ID',
        right_on='DEAL_ID',
        how='inner'
    )
    
    # Converter DATE_CREATE para datetime se existir
    if 'DATE_CREATE' in df_mesclado.columns:
        try:
            df_mesclado['DATE_CREATE'] = pd.to_datetime(df_mesclado['DATE_CREATE'], errors='coerce')
        except Exception as e:
            print(f"Erro ao converter DATE_CREATE para formato de data: {str(e)}")
    
    # Renomear colunas para nomes mais amigáveis
    df_mesclado = df_mesclado.rename(columns={
        'UF_CRM_1722605592778': 'UF_CRM_CAMPO_COMPARACAO'
    })
    
    return df_mesclado

def carregar_dados_cartorio():
    """
    Função específica para o modo apresentação que garante 
    compatibilidade com a chamada em apresentacao_conclusoes.py
    """
    try:
        df = load_data()
        print(f"Dados do cartório carregados com sucesso: {len(df)} registros")
        return df
    except Exception as e:
        import traceback
        print(f"Erro ao carregar dados do cartório: {str(e)}")
        print(traceback.format_exc())
        return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro 