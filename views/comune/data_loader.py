import streamlit as st
import pandas as pd
from api.bitrix_connector import load_bitrix_data, get_credentials
from datetime import datetime
from dotenv import load_dotenv
import os # Adicionado para construir caminho do arquivo

# Carregar variáveis de ambiente
load_dotenv()

def carregar_datas_solicitacao():
    """
    Carrega as datas de solicitação originais do arquivo CSV.
    """
    # Construir o caminho relativo para o arquivo CSV
    script_dir = os.path.dirname(__file__) # Diretório atual do script
    csv_path = os.path.join(script_dir, 'Planilhas', 'Emissões Italiana, Antes de movimentação geral - comune.csv')

    try:
        df_datas = pd.read_csv(csv_path, usecols=['ID', 'Movido em'], dtype={'ID': str})
        # Renomear colunas
        df_datas = df_datas.rename(columns={'Movido em': 'DATA_SOLICITACAO_ORIGINAL'})
        # Converter para datetime, tratando erros
        df_datas['DATA_SOLICITACAO_ORIGINAL'] = pd.to_datetime(df_datas['DATA_SOLICITACAO_ORIGINAL'], errors='coerce')
        # Remover linhas onde a data não pôde ser convertida ou o ID é nulo
        df_datas.dropna(subset=['ID', 'DATA_SOLICITACAO_ORIGINAL'], inplace=True)
        # Remover IDs duplicados, mantendo o primeiro (ou último, dependendo da lógica desejada)
        df_datas.drop_duplicates(subset=['ID'], keep='first', inplace=True)
        return df_datas
    except FileNotFoundError:
        st.error(f"Arquivo CSV não encontrado em: {csv_path}")
        return pd.DataFrame({'ID': [], 'DATA_SOLICITACAO_ORIGINAL': []})
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        return pd.DataFrame({'ID': [], 'DATA_SOLICITACAO_ORIGINAL': []})

def carregar_dados_comune():
    """
    Carrega dados da entidade CRM_DYNAMIC_1052 com CATEGORY_ID = 22
    e junta com as datas de solicitação do CSV.
    """
    # Obter token do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # URL para acessar a tabela crm_dynamic_items_1052
    url_items = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1052"
    
    # Preparar filtro para a categoria 22
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["22"], 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    # Carregar os dados do Bitrix
    df_items = load_bitrix_data(url_items, filters=category_filter)
    
    # Se o DataFrame estiver vazio, retornar DataFrame vazio
    if df_items is None or df_items.empty:
        st.error("Não foi possível carregar os dados de COMUNE do Bitrix24. Verifique a conexão.")
        return pd.DataFrame()

    # Garantir que a coluna ID do Bitrix seja string para o merge
    if 'ID' in df_items.columns:
        df_items['ID'] = df_items['ID'].astype(str)
    else:
        st.error("Coluna 'ID' não encontrada nos dados do Bitrix. Não é possível juntar as datas de solicitação.")
        # Adicionar o nome mesmo sem o merge
        df_items.loc[:, 'NOME_SEGMENTO'] = "COMUNE BITRIX24"
        return df_items

    # Carregar as datas de solicitação do CSV
    df_datas_solicitacao = carregar_datas_solicitacao()

    # Juntar (merge) os dados do Bitrix com as datas do CSV
    if not df_datas_solicitacao.empty:
        df_items = pd.merge(df_items, df_datas_solicitacao, on='ID', how='left')
        print(f"Merge realizado. Colunas após merge: {df_items.columns.tolist()}")
        # Verificar quantas linhas tiveram correspondência
        matched_rows = df_items['DATA_SOLICITACAO_ORIGINAL'].notna().sum()
        print(f"{matched_rows} de {len(df_items)} registros tiveram data de solicitação encontrada no CSV.")
    else:
        print("Não foi possível carregar ou processar as datas de solicitação do CSV. A coluna DATA_SOLICITACAO_ORIGINAL não será adicionada.")
        # Adicionar coluna vazia para consistência, se necessário
        df_items['DATA_SOLICITACAO_ORIGINAL'] = pd.NaT

    # Adicionar o nome para melhor visualização
    df_items.loc[:, 'NOME_SEGMENTO'] = "COMUNE BITRIX24"
    
    return df_items

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
    
    # Log do filtro aplicado
    print(f"Aplicando filtro para CRM_DEAL: {category_filter}")
    
    # Carregar dados principais dos negócios com filtro de categoria
    df_deal = load_bitrix_data(url_deal, filters=category_filter)
    
    # Verificar se conseguiu carregar os dados
    if df_deal.empty:
        print("Nenhum dado encontrado para CRM_DEAL com CATEGORY_ID=32")
        return pd.DataFrame(), pd.DataFrame()
    else:
        print(f"Carregados {len(df_deal)} registros de CRM_DEAL com CATEGORY_ID=32")
        
    # Verificar se a coluna CATEGORY_ID existe e tem valores esperados
    if 'CATEGORY_ID' in df_deal.columns:
        categorias_encontradas = df_deal['CATEGORY_ID'].unique()
        print(f"Categorias encontradas nos dados: {categorias_encontradas}")
    
    # Simplificar: selecionar apenas as colunas necessárias
    colunas_deal = ['ID', 'TITLE', 'ASSIGNED_BY_NAME']
    
    # Verificar se todas as colunas existem
    colunas_existentes = [col for col in colunas_deal if col in df_deal.columns]
    if len(colunas_existentes) < len(colunas_deal):
        print(f"Aviso: Nem todas as colunas desejadas existem. Colunas disponíveis: {df_deal.columns.tolist()}")
    
    # Selecionar apenas as colunas que existem
    df_deal = df_deal[colunas_existentes]
    
    # Obter lista de IDs dos deals para filtrar a tabela crm_deal_uf
    deal_ids = df_deal['ID'].astype(str).tolist()
    
    # Mostrar alguns IDs para debug
    print(f"Exemplos de IDs de deals que serão usados: {deal_ids[:5] if len(deal_ids) > 5 else deal_ids}")
    
    # Limitar a quantidade de IDs para evitar sobrecarga (se houverem muitos)
    if len(deal_ids) > 1000:
        print(f"Limitando a consulta para os primeiros 1000 IDs (de {len(deal_ids)} disponíveis)")
        deal_ids = deal_ids[:1000]
    
    # Se não houver IDs, retornar DataFrames vazios
    if not deal_ids:
        print("Nenhum ID de deal encontrado para filtrar campos personalizados")
        return df_deal, pd.DataFrame()
    
    # Filtro para crm_deal_uf baseado nos IDs dos deals da categoria 32
    deal_filter = {"dimensionsFilters": [[]]}
    deal_filter["dimensionsFilters"][0].append({
        "fieldName": "DEAL_ID", 
        "values": deal_ids, 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    print(f"Aplicando filtro para CRM_DEAL_UF com {len(deal_ids)} IDs")
    
    # Carregar dados da tabela crm_deal_uf (onde estão os campos personalizados do funil de negócios)
    df_deal_uf = load_bitrix_data(url_deal_uf, filters=deal_filter)
    
    # Verificar se conseguiu carregar os dados
    if df_deal_uf.empty:
        print("Nenhum dado encontrado em DEAL_UF para os IDs filtrados")
        return df_deal, pd.DataFrame()
    else:
        print(f"Carregados {len(df_deal_uf)} registros de DEAL_UF")
    
    # Verificar as colunas disponíveis em df_deal_uf
    print(f"Colunas disponíveis em DEAL_UF: {df_deal_uf.columns.tolist()}")
    
    # Filtrar apenas as colunas relevantes
    colunas_obrigatorias = ['DEAL_ID', 'UF_CRM_1722605592778']
    
    # Verificar quais colunas existem no DataFrame
    colunas_selecionadas = [coluna for coluna in colunas_obrigatorias if coluna in df_deal_uf.columns]
    
    if len(colunas_selecionadas) < len(colunas_obrigatorias):
        print(f"Aviso: Nem todas as colunas necessárias foram encontradas em DEAL_UF")
        print(f"Colunas necessárias: {colunas_obrigatorias}")
        print(f"Colunas encontradas: {colunas_selecionadas}")
    
    # Verificar se a coluna de cruzamento existe
    if 'UF_CRM_1722605592778' not in df_deal_uf.columns:
        print("ATENÇÃO: Coluna UF_CRM_1722605592778 não encontrada em DEAL_UF!")
        # Tentar sugerir colunas que possam conter o valor desejado
        possiveis_colunas = [col for col in df_deal_uf.columns if 'UF_CRM_' in col]
        if possiveis_colunas:
            print(f"Possíveis colunas alternativas: {possiveis_colunas}")
    
    # Simplificar: manter apenas as colunas necessárias
    if colunas_selecionadas:
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

def mapear_estagios_comune():
    """
    Retorna um dicionário com mapeamento dos estágios do COMUNE
    """
    return {
        "DT1052_22:UC_2QZ8S2": "PENDENTE",
        "DT1052_22:UC_E1VKYT": "PESQUISA NÃO FINALIZADA",
        "DT1052_22:UC_MVS02R": "DEVOLUTIVA EMISSOR",
        "DT1052_22:NEW": "SOLICITAR",
        "DT1052_22:UC_4RQBZV": "URGENTE",
        "DT1052_22:UC_F0IRDH": "SOLICITAR - TEM INFO",
        "DT1052_22:PREPARATION": "AGUARDANDO COMUNE/PARÓQUIA",
        "DT1052_22:UC_S4DFU2": "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO",
        "DT1052_22:UC_1RC076": "AGUARDANDO PDF",
        "DT1052_22:CLIENT": "ENTREGUE PDF",
        "DT1052_22:UC_A9UEMO": "NEGATIVA COMUNE",
        "DT1052_22:SUCCESS": "DOCUMENTO FISICO ENTREGUE",
        "DT1052_22:FAIL": "CANCELADO"
    }

def mapear_estagios_macro():
    """
    Retorna um dicionário com mapeamento dos estágios do COMUNE para a visão macro
    """
    return {
        "DT1052_22:UC_2QZ8S2": "PENDENTE",                    # PENDENTE
        "DT1052_22:UC_E1VKYT": "PESQUISA NÃO FINALIZADA",     # PESQUISA NÃO FINALIZADA
        "DT1052_22:UC_MVS02R": "DEVOLUTIVA EMISSOR",          # DEVOLUTIVA EMISSOR
        "DT1052_22:NEW": "SOLICITAR",                         # SOLICITAR
        "DT1052_22:UC_4RQBZV": "URGENTE",                     # URGENTE
        "DT1052_22:UC_F0IRDH": "SOLICITAR - TEM INFO",        # SOLICITAR - TEM INFO
        "DT1052_22:PREPARATION": "AGUARDANDO COMUNE/PARÓQUIA", # AGUARDANDO COMUNE/PARÓQUIA
        "DT1052_22:UC_S4DFU2": "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO", # AGUARDANDO COMUNE/PARÓQUIA - TEM INFO
        "DT1052_22:UC_1RC076": "AGUARDANDO PDF",              # AGUARDANDO PDF
        "DT1052_22:CLIENT": "ENTREGUE PDF",                   # ENTREGUE PDF
        "DT1052_22:UC_A9UEMO": "NEGATIVA COMUNE",             # NEGATIVA COMUNE
        "DT1052_22:SUCCESS": "DOCUMENTO FISICO ENTREGUE",     # DOCUMENTO FISICO ENTREGUE
        "DT1052_22:FAIL": "CANCELADO"                         # CANCELADO
    } 