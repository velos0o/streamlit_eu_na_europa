import streamlit as st
import pandas as pd
from api.bitrix_connector import load_bitrix_data, get_credentials
from datetime import datetime
from dotenv import load_dotenv
import functools # Importar functools para lru_cache

# Carregar variáveis de ambiente
load_dotenv()

# --- Cach  e Config --- 
# Usar st.cache_data para cache gerenciado pelo Streamlit
# ttl (time-to-live) opcional para expirar o cache (ex: 1 hora = 3600 segundos)
CACHE_TTL = 3600 # Cache por 1 hora

@st.cache_data(ttl=CACHE_TTL)
def load_data_cached(table_name: str, filters: dict | None = None):
    """
    Função genérica cacheada para carregar dados do Bitrix.
    Abstrai a chamada load_bitrix_data para facilitar o cache.
    """
    print(f"[CACHE MISS] Carregando dados da API Bitrix para: {table_name}")
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    url = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table={table_name}"
    df = load_bitrix_data(url, filters=filters)
    if df is None:
        return pd.DataFrame() # Retorna DF vazio em caso de erro
    return df

# @st.cache_data # Cache será aplicado na chamada de load_data_cached
def load_data_all_pipelines():
    """
    Carrega dados de TODOS os pipelines de cartório (categorias 92, 94, 102 e 104)
    incluindo os novos pipelines de Paróquia e Pesquisa BR.
    
    ATUALIZADO DEZEMBRO 2024: Inclui pipelines 102 (Paróquia) e 104 (Pesquisa BR)
    
    IMPORTANTE: Esta é agora a função PRINCIPAL para carregar dados de cartório.
    A função load_data() foi mantida apenas para compatibilidade com código antigo.
    """
    table_name = "crm_dynamic_items_1098"
    
    # Preparar filtro para TODAS as categorias de pipelines
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["92", "94", "102", "104"], # Incluindo os novos pipelines
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    print(f"[INFO] Solicitando dados para {table_name} com filtro ALL PIPELINES: {category_filter}")
    df_items = load_data_cached(table_name, filters=category_filter)
    
    # Se o DataFrame estiver vazio após filtro na API, retornar
    if df_items.empty:
        st.warning(f"Nenhum dado encontrado para as categorias 92, 94, 102 ou 104 na tabela {table_name}.")
        return pd.DataFrame()
    
    print(f"[DEBUG] Total de registros recebidos da API (ALL PIPELINES): {len(df_items)}")
    
    # --- Processamento Pós-Carregamento ---
    df_items = df_items.copy()
    
    # Verificar se a coluna CATEGORY_ID existe
    if 'CATEGORY_ID' not in df_items.columns:
        st.error(f"Coluna CATEGORY_ID não encontrada na tabela {table_name}.")
        return pd.DataFrame()
    
    # Garantir tipo numérico para CATEGORY_ID e tratar erros
    try:
        df_items['CATEGORY_ID'] = pd.to_numeric(df_items['CATEGORY_ID'], errors='coerce')
        df_items = df_items.dropna(subset=['CATEGORY_ID'])
        df_items['CATEGORY_ID'] = df_items['CATEGORY_ID'].astype('int64')
        
        # Verificar se apenas as categorias esperadas estão presentes
        categorias_presentes = df_items['CATEGORY_ID'].unique()
        categorias_validas = [92, 94, 102, 104]
        if not all(cat in categorias_validas for cat in categorias_presentes):
            print(f"[WARN] Categorias inesperadas encontradas: {categorias_presentes}. Refiltrando localmente.")
            df_items = df_items[df_items['CATEGORY_ID'].isin(categorias_validas)].copy()

    except Exception as e:
        print(f"[DEBUG] Erro ao processar CATEGORY_ID: {str(e)}")
        return pd.DataFrame()
    
    # Verificar duplicados por ID
    if 'ID' in df_items.columns:
        duplicados = df_items.duplicated(subset=['ID'])
        n_duplicados = duplicados.sum()
        if n_duplicados > 0:
            print(f"[DEBUG] Encontrados {n_duplicados} registros duplicados por ID. Removendo...")
            df_items = df_items.drop_duplicates(subset=['ID'], keep='first')
    
    # Adicionar nome do pipeline/cartório
    df_items['NOME_PIPELINE'] = df_items['CATEGORY_ID'].map({
        92: 'CARTÓRIO CASA VERDE',
        94: 'CARTÓRIO TATUÁPE',
        102: 'PARÓQUIA',
        104: 'PESQUISA BR'
    })
    
    # Adicionar também NOME_CARTORIO para compatibilidade com código existente
    df_items['NOME_CARTORIO'] = df_items['CATEGORY_ID'].map({
        92: 'CARTÓRIO CASA VERDE',
        94: 'CARTÓRIO TATUÁPE',
        102: 'PARÓQUIA',
        104: 'PESQUISA BR'
    })
    
    print(f"[DEBUG] Total final após processamento (ALL PIPELINES): {len(df_items)}")
    print(f"[DEBUG] Distribuição por pipeline: {df_items['CATEGORY_ID'].value_counts().to_dict()}")
    
    return df_items

# Modificar load_data para usar o cache e filtro na API
# @st.cache_data # Cache será aplicado na chamada de load_data_cached
def load_data():
    """
    Carrega dados do cartório (categorias 92 e 94 - SPA) com filtro aplicado na API
    e usando a função de carregamento cacheada.
    """
    table_name = "crm_dynamic_items_1098"  # Alterado para nova tabela SPA
    
    # Preparar filtro para as categorias 92 e 94
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["92", "94"], # Alterado para novas categorias SPA
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    print(f"[INFO] Solicitando dados para {table_name} com filtro: {category_filter}")
    df_items = load_data_cached(table_name, filters=category_filter)
    
    # Se o DataFrame estiver vazio após filtro na API, retornar
    if df_items.empty:
        st.warning(f"Nenhum dado encontrado para as categorias 92 ou 94 na tabela {table_name}.") # Mensagem atualizada
        return pd.DataFrame()
    
    print(f"[DEBUG] Colunas recebidas da API para {table_name} (antes do processamento): {df_items.columns.tolist()}") # Log Adicionado
    print(f"[DEBUG] Total de registros brutos recebidos da API (filtrados): {len(df_items)}")
    
    # --- Processamento Pós-Carregamento (verificações ainda importantes) ---
    # Criar cópia antes de modificar
    df_items = df_items.copy()
    
    # Verificar se a coluna CATEGORY_ID existe (embora tenhamos filtrado por ela)
    if 'CATEGORY_ID' not in df_items.columns:
        st.error(f"Coluna CATEGORY_ID inesperadamente ausente após filtro na API para {table_name}.")
        return pd.DataFrame()
    
    # Garantir tipo numérico para CATEGORY_ID e tratar erros
    try:
        df_items['CATEGORY_ID'] = pd.to_numeric(df_items['CATEGORY_ID'], errors='coerce')
        df_items = df_items.dropna(subset=['CATEGORY_ID'])
        df_items['CATEGORY_ID'] = df_items['CATEGORY_ID'].astype('int64')
        # Verificar se *apenas* 92 e 94 estão presentes após conversão
        categorias_presentes = df_items['CATEGORY_ID'].unique()
        if not all(cat in [92, 94] for cat in categorias_presentes): # Alterado para novas categorias
            print(f"[WARN] Categorias inesperadas encontradas após filtro na API: {categorias_presentes}. Refiltrando localmente.")
            df_items = df_items[df_items['CATEGORY_ID'].isin([92, 94])].copy() # Alterado para novas categorias

    except Exception as e:
        print(f"[DEBUG] Erro ao processar CATEGORY_ID pós-filtro: {str(e)}")
        return pd.DataFrame()
    
    # Verificar duplicados por ID (ainda relevante)
    if 'ID' in df_items.columns:
        duplicados = df_items.duplicated(subset=['ID'])
        n_duplicados = duplicados.sum()
        if n_duplicados > 0:
            print(f"[DEBUG] Encontrados {n_duplicados} registros duplicados por ID após filtro. Removendo...")
            df_items = df_items.drop_duplicates(subset=['ID'], keep='first')
    
    # Adicionar nome do cartório
    df_items['NOME_CARTORIO'] = df_items['CATEGORY_ID'].map({
        92: 'CARTÓRIO CASA VERDE',  # Alterado para nova categoria
        94: 'CARTÓRIO TATUÁPE'   # Alterado para nova categoria
    })
    
    print(f"[DEBUG] Total final após processamento local: {len(df_items)}")
    return df_items

def carregar_dados_negocios():
    """
    Carrega os dados dos negócios da categoria 32 e seus campos personalizados,
    usando a função de carregamento cacheada.
    """
    # Tabela principal de negócios
    table_deal = "crm_deal"
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["32"], 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    df_deal = load_data_cached(table_deal, filters=category_filter)
    if df_deal.empty:
        return pd.DataFrame(), pd.DataFrame()
    df_deal = df_deal[['ID', 'TITLE', 'ASSIGNED_BY_NAME']].copy() # Selecionar colunas e copiar
    
    # Tabela UF de negócios
    table_deal_uf = "crm_deal_uf"
    deal_ids = df_deal['ID'].astype(str).tolist()
    if len(deal_ids) > 1000: # Limitar IDs no filtro
        deal_ids = deal_ids[:1000]
    deal_filter = {"dimensionsFilters": [[]]}
    deal_filter["dimensionsFilters"][0].append({
        "fieldName": "DEAL_ID", 
        "values": deal_ids, 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    df_deal_uf = load_data_cached(table_deal_uf, filters=deal_filter)
    if df_deal_uf.empty:
        return df_deal, pd.DataFrame()
        
    # Processar colunas UF
    colunas_obrigatorias = ['DEAL_ID', 'UF_CRM_1722605592778']
    colunas_selecionadas = colunas_obrigatorias.copy()
    if 'UF_CRM_HIGILIZACAO_STATUS' in df_deal_uf.columns:
        colunas_selecionadas.append('UF_CRM_HIGILIZACAO_STATUS')
    df_deal_uf = df_deal_uf[colunas_selecionadas].copy() # Selecionar e copiar
    
    return df_deal, df_deal_uf

#@st.cache_data(ttl=CACHE_TTL) # Cachear também os estágios
def carregar_estagios_bitrix():
    """
    Carrega os estágios dos funis do Bitrix24, usando cache.
    """
    return load_data_cached("crm_status")

#@st.cache_data(ttl=CACHE_TTL) # Cachear crm_deal categoria 0
def carregar_dados_crm_deal_com_uf():
    """
    Carrega dados de CRM_DEAL (cat 0) e CRM_DEAL_UF, usando cache.
    """
    # Carregar crm_deal com filtro de categoria 0
    table_deal = "crm_deal"
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["0"], 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    df_deal = load_data_cached(table_deal, filters=category_filter)
    if df_deal.empty:
        st.warning("Não foi possível carregar os dados da tabela crm_deal para a categoria 0.")
        return pd.DataFrame()
        
    # Selecionar colunas e processar data
    colunas_necessarias = ['ID', 'TITLE', 'CATEGORY_ID', 'ASSIGNED_BY_NAME', 'DATE_CREATE']
    colunas_presentes = [col for col in colunas_necessarias if col in df_deal.columns]
    if 'DATE_CREATE' not in colunas_presentes:
        st.warning("Campo DATE_CREATE não encontrado...")
    df_deal = df_deal[colunas_presentes].copy()
    if 'DATE_CREATE' in df_deal.columns:
        df_deal['DATE_CREATE'] = pd.to_datetime(df_deal['DATE_CREATE'], errors='coerce')

    # Carregar crm_deal_uf com filtro de ID
    table_deal_uf = "crm_deal_uf"
    deal_ids = df_deal['ID'].astype(str).tolist()
    if len(deal_ids) > 1000:
        deal_ids = deal_ids[:1000]
    deal_filter = {"dimensionsFilters": [[]]}
    deal_filter["dimensionsFilters"][0].append({
        "fieldName": "DEAL_ID", 
        "values": deal_ids, 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    df_deal_uf = load_data_cached(table_deal_uf, filters=deal_filter)
    if df_deal_uf.empty:
        st.warning("Não foi possível carregar os dados da tabela crm_deal_uf para a categoria 0.")
        # Retornar df_deal mesmo assim, pois pode ser útil
        df_deal['UF_CRM_CAMPO_COMPARACAO'] = None # Adicionar coluna vazia
        return df_deal 

    # Selecionar colunas UF
    col_comparacao = 'UF_CRM_1722605592778'
    colunas_uf_obrigatorias = ['DEAL_ID']
    if col_comparacao in df_deal_uf.columns:
        colunas_uf_obrigatorias.append(col_comparacao)
    else:
        st.warning(f"Campo {col_comparacao} não encontrado na tabela crm_deal_uf.")
    df_deal_uf_filtrado = df_deal_uf[colunas_uf_obrigatorias].copy()

    # Mesclar
    df_mesclado = pd.merge(
        df_deal,
        df_deal_uf_filtrado,
        left_on='ID',
        right_on='DEAL_ID',
        how='left' # Usar left para manter todos os deals da categoria 0
    )
    
    # Renomear e preencher NAs se a coluna foi encontrada
    if col_comparacao in df_mesclado.columns:
        df_mesclado = df_mesclado.rename(columns={col_comparacao: 'UF_CRM_CAMPO_COMPARACAO'})
        df_mesclado['UF_CRM_CAMPO_COMPARACAO'] = df_mesclado['UF_CRM_CAMPO_COMPARACAO'].fillna('N/A') # Preencher NAs pós-merge
    else:
        df_mesclado['UF_CRM_CAMPO_COMPARACAO'] = 'N/A' # Garantir coluna padrão

    return df_mesclado

# Função para carregar dados do crm_deal com category_id = 46
def carregar_dados_crm_deal_cat46():
    """
    Carrega dados de CRM_DEAL (cat 46) e seus campos personalizados (UF_CRM_1746054586042 - data venda),
    usando a função de carregamento cacheada.
    
    Returns:
        pandas.DataFrame: DataFrame com dados da categoria 46 com data de venda.
    """
    # Carregar crm_deal com filtro de categoria 46
    table_deal = "crm_deal"
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["46"], 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    df_deal = load_data_cached(table_deal, filters=category_filter)
    if df_deal.empty:
        print("[WARN] Não foi possível carregar os dados da tabela crm_deal para a categoria 46.")
        return pd.DataFrame()
        
    # Selecionar colunas e processar dados básicos
    colunas_necessarias = ['ID', 'TITLE', 'ASSIGNED_BY_NAME']
    colunas_presentes = [col for col in colunas_necessarias if col in df_deal.columns]
    df_deal = df_deal[colunas_presentes].copy()

    # Carregar crm_deal_uf com filtro de ID para obter campos personalizados
    table_deal_uf = "crm_deal_uf"
    deal_ids = df_deal['ID'].astype(str).tolist()
    if len(deal_ids) > 1000:
        deal_ids = deal_ids[:1000]
    deal_filter = {"dimensionsFilters": [[]]}
    deal_filter["dimensionsFilters"][0].append({
        "fieldName": "DEAL_ID", 
        "values": deal_ids, 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    df_deal_uf = load_data_cached(table_deal_uf, filters=deal_filter)
    if df_deal_uf.empty:
        print("[WARN] Não foi possível carregar os dados da tabela crm_deal_uf para a categoria 46.")
        return pd.DataFrame()

    # Selecionar campos personalizados necessários
    colunas_uf_obrigatorias = ['DEAL_ID', 'UF_CRM_1722605592778', 'UF_CRM_1746054586042']
    colunas_uf_presentes = [col for col in colunas_uf_obrigatorias if col in df_deal_uf.columns]
    
    # Verificar se os campos chave existem
    campos_faltantes = set(colunas_uf_obrigatorias) - set(colunas_uf_presentes)
    if campos_faltantes:
        print(f"[WARN] Campos obrigatórios ausentes em crm_deal_uf: {campos_faltantes}")
        if 'UF_CRM_1722605592778' not in colunas_uf_presentes or 'DEAL_ID' not in colunas_uf_presentes:
            print("[ERROR] Campo de ID Família ou DEAL_ID não encontrado. Impossível prosseguir.")
            return pd.DataFrame()
    
    df_deal_uf_filtrado = df_deal_uf[colunas_uf_presentes].copy()

    # Mesclar dados principais com UFs
    df_mesclado = pd.merge(
        df_deal,
        df_deal_uf_filtrado,
        left_on='ID',
        right_on='DEAL_ID',
        how='inner'
    )
    
    # Processar data de venda (UF_CRM_1746054586042)
    if 'UF_CRM_1746054586042' in df_mesclado.columns:
        df_mesclado = df_mesclado.rename(columns={'UF_CRM_1746054586042': 'DATA_VENDA'})
        df_mesclado['DATA_VENDA'] = pd.to_datetime(df_mesclado['DATA_VENDA'], errors='coerce')
        print(f"[INFO] Coluna de data de venda processada. {df_mesclado['DATA_VENDA'].notna().sum()} registros com data.")
    else:
        df_mesclado['DATA_VENDA'] = pd.NaT
        print("[WARN] Coluna de data de venda não encontrada.")

    # Garantir que UF_CRM_1722605592778 esteja como string para facilitar o merge
    df_mesclado['UF_CRM_1722605592778'] = df_mesclado['UF_CRM_1722605592778'].fillna('N/A').astype(str).str.strip()
    
    return df_mesclado

# A função principal agora chama load_data(), que usa o cache internamente
# Não precisa cachear esta função diretamente
def carregar_dados_cartorio():
    """
    Carrega os dados dos cartórios (cat 92, 94, 102 e 104) usando cache e filtro na API,
    e faz o merge com os dados de negócio (cat 46) para obter a data de venda (UF_CRM_1746054586042).
    
    ATUALIZADO DEZEMBRO 2024: Agora inclui os novos funis 102 (Paróquia) e 104 (Pesquisa BR)

    Returns:
        pandas.DataFrame: DataFrame com os dados dos cartórios filtrados e enriquecidos com a data de venda.
    """
    try:
        # MUDANÇA CRÍTICA: Carregar TODOS os pipelines (92, 94, 102, 104) em vez de apenas 92 e 94
        df_cartorio = load_data_all_pipelines()

        if df_cartorio.empty:
            # Mensagem de load_data_all_pipelines já deve ter aparecido
            # print("Nenhum dado de item de cartório carregado.") 
            return pd.DataFrame()

        # Carregar dados de negócio (cat 46) com data de venda (NOVA IMPLEMENTAÇÃO)
        df_deal_cat46 = carregar_dados_crm_deal_cat46()
        if df_deal_cat46.empty:
            st.warning("Dados de negócio (cat 46) não encontrados. A coluna 'Data de Venda' não será adicionada.")
            # Verificar se a abordagem antiga ainda está configurada como fallback
            df_deal_cat0 = carregar_dados_crm_deal_com_uf()
            if df_deal_cat0.empty:
                print("[WARN] Dados de negócio (cat 0 e cat 46) não disponíveis. Nenhuma data de venda será adicionada.")
                df_cartorio['DATA_VENDA'] = pd.NaT
            else:
                # FALLBACK - Usar abordagem antiga com cat 0 como antes
                print("[INFO] Usando dados de categoria 0 como fallback para data de venda.")
                # Manter código existente para cat 0
                col_id_familia_deal = 'UF_CRM_CAMPO_COMPARACAO'
                col_data_venda = 'DATE_CREATE'
                if col_id_familia_deal not in df_deal_cat0.columns:
                    print(f"[ERROR] Coluna chave '{col_id_familia_deal}' não encontrada nos dados de negócio (cat 0).")
                    df_cartorio['DATA_VENDA'] = pd.NaT
                elif col_data_venda not in df_deal_cat0.columns:
                    print(f"[WARN] Coluna '{col_data_venda}' não encontrada nos dados de negócio (cat 0).")
                    df_cartorio['DATA_VENDA'] = pd.NaT
                else:
                    # Manter código existente para processamento cat 0
                    # [CÓDIGO EXISTENTE MANTIDO]
                    df_deal_to_merge = df_deal_cat0[[col_id_familia_deal, col_data_venda]].copy()
                    df_deal_to_merge = df_deal_to_merge.dropna(subset=[col_id_familia_deal, col_data_venda])
                    df_deal_to_merge = df_deal_to_merge.sort_values(by=col_data_venda, ascending=True)
                    df_deal_to_merge = df_deal_to_merge.drop_duplicates(subset=[col_id_familia_deal], keep='first')
                    
                    # --- Processamento Coluna ID Família no Cartório ---
                    col_id_familia_cartorio = 'UF_CRM_34_ID_FAMILIA'
                    if col_id_familia_cartorio not in df_cartorio.columns:
                        print(f"[ERROR] Coluna chave '{col_id_familia_cartorio}' não encontrada nos dados do cartório.")
                        df_cartorio['DATA_VENDA'] = pd.NaT
                    else:
                        # Preparar para merge
                        df_cartorio[col_id_familia_cartorio] = df_cartorio[col_id_familia_cartorio].fillna('N/A').astype(str).str.strip()
                        df_deal_to_merge[col_id_familia_deal] = df_deal_to_merge[col_id_familia_deal].astype(str).str.strip()

                        # Realizar merge com abordagem antiga
                        print(f"[INFO] Realizando merge entre Cartório e Deals (cat 0) usando '{col_id_familia_cartorio}' e '{col_id_familia_deal}'")
                        df_cartorio = pd.merge(
                            df_cartorio,
                            df_deal_to_merge,
                            left_on=col_id_familia_cartorio,
                            right_on=col_id_familia_deal,
                            how='left'
                        )
                        
                        # Renomear e processar
                        df_cartorio = df_cartorio.rename(columns={col_data_venda: 'DATA_VENDA'})
                        df_cartorio['DATA_VENDA'] = pd.to_datetime(df_cartorio['DATA_VENDA'], errors='coerce')
                        
                        n_merged = df_cartorio['DATA_VENDA'].notna().sum()
                        print(f"[INFO] Merge cat 0 concluído. {n_merged} registros receberam Data de Venda.")
        else:
            # NOVA IMPLEMENTAÇÃO - Usar dados da cat 46
            print(f"[INFO] Processando merge com dados de negócio categoria 46 ({len(df_deal_cat46)} registros)")
            
            # Selecionar colunas relevantes do df_deal_cat46 para o merge
            col_id_familia_cat46 = 'UF_CRM_1722605592778'  # ID da família
            col_data_venda = 'DATA_VENDA'  # Já renomeado na função carregar_dados_crm_deal_cat46
            
            # Preparar dados para merge
            df_deal_to_merge = df_deal_cat46[[col_id_familia_cat46, col_data_venda]].copy()
            
            # Remover registros sem ID ou data
            df_deal_to_merge = df_deal_to_merge.dropna(subset=[col_id_familia_cat46, col_data_venda])
            
            # Ordenar por data (ascendente) e pegar a primeira data para cada ID de família
            df_deal_to_merge = df_deal_to_merge.sort_values(by=col_data_venda, ascending=True)
            df_deal_to_merge = df_deal_to_merge.drop_duplicates(subset=[col_id_familia_cat46], keep='first')
            
            # Coluna ID Família no Cartório
            col_id_familia_cartorio = 'UF_CRM_34_ID_FAMILIA'
            
            if col_id_familia_cartorio not in df_cartorio.columns:
                print(f"[ERROR] Coluna chave '{col_id_familia_cartorio}' não encontrada nos dados do cartório.")
                df_cartorio['DATA_VENDA'] = pd.NaT
            else:
                # Preparar colunas para merge em ambos DataFrames
                df_cartorio[col_id_familia_cartorio] = df_cartorio[col_id_familia_cartorio].fillna('N/A').astype(str).str.strip()
                
                # Realizar o merge
                print(f"[INFO] Realizando merge entre Cartório ({len(df_cartorio)}) e Deals cat 46 ({len(df_deal_to_merge)})")
                print(f"[INFO] Usando '{col_id_familia_cartorio}' e '{col_id_familia_cat46}'")
                df_cartorio = pd.merge(
                    df_cartorio,
                    df_deal_to_merge,
                    left_on=col_id_familia_cartorio,
                    right_on=col_id_familia_cat46,
                    how='left'
                )
                
                # Ver quantos registros receberam data
                n_merged = df_cartorio['DATA_VENDA'].notna().sum()
                print(f"[INFO] Merge cat 46 concluído. {n_merged} registros receberam Data de Venda.")
        
        # Mover o processamento restante para após o merge, caso dependam dos dados mesclados
        # ou precisem ser refeitos no dataframe 'df_cartorio' atualizado
        df = df_cartorio # Renomear de volta para 'df' para o resto do código

        # Verificar se as colunas UF_CRM_... existem agora na tabela principal
        coluna_id_requerente = 'UF_CRM_34_ID_REQUERENTE' # Alterado para novo campo SPA
        if coluna_id_requerente not in df.columns:
            print(f"[WARN] Coluna {coluna_id_requerente} (ID Requerente SPA - para contagem) não encontrada na tabela principal.") # Mensagem atualizada
            df[coluna_id_requerente] = 'Req. Desconhecido' # Valor padrão
        else:
            # Tratar como string e preencher NaNs para contagem nunique
            df[coluna_id_requerente] = df[coluna_id_requerente].fillna('Req. Desconhecido').astype(str)
            df[coluna_id_requerente] = df[coluna_id_requerente].replace(r'^\\s*$', 'Req. Desconhecido', regex=True)
            # print(f"[DEBUG] Coluna {coluna_id_requerente} (ID Requerente) processada.") # Comentado para reduzir log
        
        # Tratar a NOVA coluna de Nome da Família
        coluna_nome_familia = 'UF_CRM_34_NOME_FAMILIA' # Alterado para novo campo SPA
        if coluna_nome_familia not in df.columns:
            print(f"[WARN] Coluna {coluna_nome_familia} (Nome da Família SPA) não encontrada na tabela principal.") # Mensagem atualizada
            df[coluna_nome_familia] = 'Família Desconhecida' # Valor padrão
        else:
            # Preencher NaNs e converter para string, tratar espaços vazios
            df[coluna_nome_familia] = df[coluna_nome_familia].fillna('Família Desconhecida').astype(str)
            df[coluna_nome_familia] = df[coluna_nome_familia].replace(r'^\\s*$', 'Família Desconhecida', regex=True)
            # print(f"[DEBUG] Coluna {coluna_nome_familia} processada.") # Comentado

        # GARANTIR dados EXATAMENTE conforme esperado (reaplicar verificações)
        # 1. Verificar e converter CATEGORY_ID para numérico, se necessário
        if 'CATEGORY_ID' in df.columns and df['CATEGORY_ID'].dtype != 'int64': # Adicionado check se coluna existe
            df['CATEGORY_ID'] = pd.to_numeric(df['CATEGORY_ID'], errors='coerce')
            df = df.dropna(subset=['CATEGORY_ID'])
            df['CATEGORY_ID'] = df['CATEGORY_ID'].astype('int64')
        elif 'CATEGORY_ID' not in df.columns:
            print("[ERROR] Coluna CATEGORY_ID ausente.")
            # Talvez retornar df vazio ou tomar outra ação?
            return pd.DataFrame() # Retorna vazio por segurança
            
        # 2. Verificar se há duplicações baseado no ID
        if 'ID' in df.columns:
            duplicados = df.duplicated(subset=['ID'], keep=False)
            if duplicados.any():
                n_duplicados = duplicados.sum()
                print(f"ATENÇÃO: Encontrados {n_duplicados} registros duplicados por ID. Mantendo apenas a primeira ocorrência.")
                df = df.drop_duplicates(subset=['ID'], keep='first')
        else:
            print("[WARN] Coluna 'ID' não encontrada para checar duplicados.")
        
        # 3. Garantir filtragem ESTRITA por categoria 92, 94, 102 e 104
        df = df[df['CATEGORY_ID'].isin([92, 94, 102, 104])].copy() # Alterado para novas categorias
        
        # 4. Verificar e remover registros que não pertencem às categorias 92, 94, 102 e 104 (redundante)
        registros_invalidos = ~df['CATEGORY_ID'].isin([92, 94, 102, 104]) # Alterado para novas categorias
        if registros_invalidos.any():
            n_invalidos = registros_invalidos.sum()
            print(f"ATENÇÃO: Removidos {n_invalidos} registros com categorias diferentes de 92, 94, 102 ou 104.") # Mensagem atualizada
            df = df[df['CATEGORY_ID'].isin([92, 94, 102, 104])] # Alterado para novas categorias
        
        # 5. Verificar se há valores nulos em CATEGORY_ID
        nulos = df['CATEGORY_ID'].isna()
        if nulos.any():
            n_nulos = nulos.sum()
            print(f"ATENÇÃO: Removidos {n_nulos} registros com CATEGORY_ID nulo.")
            df = df.dropna(subset=['CATEGORY_ID'])
        
        # 6. Garantir mapeamento dos nomes de cartório
        #    Se NOME_CARTORIO não foi criado em load_data(), criar aqui
        if 'NOME_CARTORIO' not in df.columns:
             print("[INFO] Criando coluna NOME_CARTORIO.")
             df['NOME_CARTORIO'] = df['CATEGORY_ID'].map({
                 92: 'CARTÓRIO CASA VERDE', # Alterado para nova categoria
                 94: 'CARTÓRIO TATUÁPE',  # Alterado para nova categoria
                 102: 'PARÓQUIA',
                 104: 'PESQUISA BR'
             })
        
        # --- Cálculo da Data de Venda Agregada por Família ---
        # Precisamos agregar a data de venda por família para usar no filtro do acompanhamento.py
        # Vamos pegar a data de venda mais antiga por família (já que filtramos deals originais)
        if 'DATA_VENDA' in df.columns and 'coluna_nome_familia' in locals():
            df_vendas_familia = df.dropna(subset=['DATA_VENDA', coluna_nome_familia])
            df_vendas_familia = df_vendas_familia.sort_values(by='DATA_VENDA', ascending=True)
            # Agrupar pelo NOME da família (já que é isso que usamos em acompanhamento.py)
            # e pegar a primeira (mais antiga) data de venda
            map_familia_data_venda = df_vendas_familia.groupby(coluna_nome_familia)['DATA_VENDA'].first()
            # Mapear essa data de volta para o DataFrame principal
            df['DATA_VENDA_FAMILIA'] = df[coluna_nome_familia].map(map_familia_data_venda)
            df['DATA_VENDA_FAMILIA'] = pd.to_datetime(df['DATA_VENDA_FAMILIA'], errors='coerce')
            print("[INFO] Data de venda agregada por família ('DATA_VENDA_FAMILIA') foi calculada (mais antiga).")
        else:
            print("[WARN] Não foi possível calcular a data de venda agregada por família.")
            df['DATA_VENDA_FAMILIA'] = pd.NaT
        
        # 7. Verificações finais de contagem
        count_cat_92 = (df['CATEGORY_ID'] == 92).sum() # Alterado para nova categoria
        count_cat_94 = (df['CATEGORY_ID'] == 94).sum() # Alterado para nova categoria
        count_cat_102 = (df['CATEGORY_ID'] == 102).sum() # Alterado para nova categoria
        count_cat_104 = (df['CATEGORY_ID'] == 104).sum() # Alterado para nova categoria
        total_registros = len(df)
        
        if count_cat_92 + count_cat_94 + count_cat_102 + count_cat_104 != total_registros: # Verificação atualizada
            print(f"ERRO GRAVE: Inconsistência nas contagens! Total: {total_registros}, Soma categorias: {count_cat_92 + count_cat_94 + count_cat_102 + count_cat_104}") # Mensagem atualizada
            # Última tentativa de correção
            df = df[df['CATEGORY_ID'].isin([92, 94, 102, 104])].copy() # Alterado para novas categorias
            # Recontar após correção
            count_cat_92 = (df['CATEGORY_ID'] == 92).sum() # Alterado para nova categoria
            count_cat_94 = (df['CATEGORY_ID'] == 94).sum() # Alterado para nova categoria
            count_cat_102 = (df['CATEGORY_ID'] == 102).sum() # Alterado para nova categoria
            count_cat_104 = (df['CATEGORY_ID'] == 104).sum() # Alterado para nova categoria
            total_registros = len(df)
            if count_cat_92 + count_cat_94 + count_cat_102 + count_cat_104 != total_registros: # Verificação atualizada
                 print("❌ ERRO CRÍTICO: Inconsistência nas contagens persiste.")
            
        print(f"Dados do cartório carregados e processados: {total_registros} registros ({count_cat_92} Casa Verde, {count_cat_94} Tatuapé, {count_cat_102} Paróquia, {count_cat_104} Pesquisa BR)") # Mensagem atualizada
        
        # Garantir que STAGE_ID está presente
        if 'STAGE_ID' not in df.columns:
            print("[WARN] Coluna STAGE_ID não encontrada no DataFrame final do cartório.")
            # Você pode querer adicionar uma coluna padrão ou parar aqui
            df['STAGE_ID'] = 'STAGE_DESCONHECIDO' 

        # Retornar o dataframe final 'df'
        return df
        
    except Exception as e:
        import traceback
        print(f"Erro ao carregar/processar dados do cartório: {str(e)}")
        print(traceback.format_exc())
        return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro 