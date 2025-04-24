import streamlit as st
import pandas as pd
from api.bitrix_connector import load_bitrix_data, get_credentials
from datetime import datetime
from dotenv import load_dotenv
import functools # Importar functools para lru_cache

# Carregar variáveis de ambiente
load_dotenv()

# --- Cache Config --- 
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

# Modificar load_data para usar o cache e filtro na API
# @st.cache_data # Cache será aplicado na chamada de load_data_cached
def load_data():
    """
    Carrega dados do cartório (categorias 16 e 34) com filtro aplicado na API
    e usando a função de carregamento cacheada.
    """
    table_name = "crm_dynamic_items_1052"
    
    # Preparar filtro para as categorias 16 e 34
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["16", "34"], # Valores como string, conforme exemplo em carregar_dados_negocios
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    print(f"[INFO] Solicitando dados para {table_name} com filtro: {category_filter}")
    df_items = load_data_cached(table_name, filters=category_filter)
    
    # Se o DataFrame estiver vazio após filtro na API, retornar
    if df_items.empty:
        st.warning(f"Nenhum dado encontrado para as categorias 16 ou 34 na tabela {table_name}.")
        return pd.DataFrame()
    
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
        # Verificar se *apenas* 16 e 34 estão presentes após conversão
        categorias_presentes = df_items['CATEGORY_ID'].unique()
        if not all(cat in [16, 34] for cat in categorias_presentes):
            print(f"[WARN] Categorias inesperadas encontradas após filtro na API: {categorias_presentes}. Refiltrando localmente.")
            df_items = df_items[df_items['CATEGORY_ID'].isin([16, 34])].copy()

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
        16: 'CARTÓRIO CASA VERDE',
        34: 'CARTÓRIO TATUÁPE'
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

# A função principal agora chama load_data(), que usa o cache internamente
# Não precisa cachear esta função diretamente
def carregar_dados_cartorio():
    """
    Carrega os dados dos cartórios (cat 16 e 34) usando cache e filtro na API.
    Assume que os campos UF_CRM_... estão na tabela principal.

    Returns:
        pandas.DataFrame: DataFrame com os dados dos cartórios filtrados.
    """
    try:
        # Carregar dados brutos (agora filtrados na API e cacheados)
        df = load_data()

        if df.empty:
            # Mensagem de load_data já deve ter aparecido
            # print("Nenhum dado de item de cartório carregado.") 
            return pd.DataFrame()

        # --- Verificações e Processamento Adicional --- 
        # (Campos UF, Duplicados, Nomes Cartório, etc.)

        # Verificar se as colunas UF_CRM_... existem agora na tabela principal
        coluna_id_requerente = 'UF_CRM_12_1723552729'
        if coluna_id_requerente not in df.columns:
            print(f"[WARN] Coluna {coluna_id_requerente} (ID Requerente - para contagem) não encontrada na tabela principal.")
            df[coluna_id_requerente] = 'Req. Desconhecido' # Valor padrão
        else:
            # Tratar como string e preencher NaNs para contagem nunique
            df[coluna_id_requerente] = df[coluna_id_requerente].fillna('Req. Desconhecido').astype(str)
            df[coluna_id_requerente] = df[coluna_id_requerente].replace(r'^\s*$', 'Req. Desconhecido', regex=True)
            print(f"[DEBUG] Coluna {coluna_id_requerente} (ID Requerente) processada.")

        # Coluna ID Família Antigo (Não mais usada para agrupar, mas pode existir)
        if 'UF_CRM_12_1723552666' not in df.columns:
            print("[WARN] Coluna UF_CRM_12_1723552666 (ID Família - Antigo) não encontrada na tabela principal.")
            df['UF_CRM_12_1723552666'] = 'N/A' # Adiciona coluna com N/A para evitar erros
        else:
            # Preencher NaNs e converter para string, se existir
            df['UF_CRM_12_1723552666'] = df['UF_CRM_12_1723552666'].fillna('N/A').astype(str)
        
        # Tratar a NOVA coluna de Nome da Família
        coluna_nome_familia = 'UF_CRM_12_1722882763189'
        if coluna_nome_familia not in df.columns:
            print(f"[WARN] Coluna {coluna_nome_familia} (Nome da Família) não encontrada na tabela principal.")
            df[coluna_nome_familia] = 'Família Desconhecida' # Valor padrão
        else:
            # Preencher NaNs e converter para string, tratar espaços vazios
            df[coluna_nome_familia] = df[coluna_nome_familia].fillna('Família Desconhecida').astype(str)
            df[coluna_nome_familia] = df[coluna_nome_familia].replace(r'^\s*$', 'Família Desconhecida', regex=True)
            print(f"[DEBUG] Coluna {coluna_nome_familia} processada.")

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
        
        # 3. Garantir filtragem ESTRITA por categoria 16 e 34
        df = df[df['CATEGORY_ID'].isin([16, 34])].copy()
        
        # 4. Verificar e remover registros que não pertencem às categorias 16 e 34 (redundante)
        registros_invalidos = ~df['CATEGORY_ID'].isin([16, 34])
        if registros_invalidos.any():
            n_invalidos = registros_invalidos.sum()
            print(f"ATENÇÃO: Removidos {n_invalidos} registros com categorias diferentes de 16 e 34.")
            df = df[df['CATEGORY_ID'].isin([16, 34])]
        
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
                 16: 'CARTÓRIO CASA VERDE',
                 34: 'CARTÓRIO TATUÁPE'
             })
        
        # 7. Verificações finais de contagem
        count_cat_16 = (df['CATEGORY_ID'] == 16).sum()
        count_cat_34 = (df['CATEGORY_ID'] == 34).sum()
        total_registros = len(df)
        
        if count_cat_16 + count_cat_34 != total_registros:
            print(f"ERRO GRAVE: Inconsistência nas contagens! Total: {total_registros}, Soma categorias: {count_cat_16 + count_cat_34}")
            # Última tentativa de correção
            df = df[df['CATEGORY_ID'].isin([16, 34])].copy()
            # Recontar após correção
            count_cat_16 = (df['CATEGORY_ID'] == 16).sum()
            count_cat_34 = (df['CATEGORY_ID'] == 34).sum()
            total_registros = len(df)
            if count_cat_16 + count_cat_34 != total_registros:
                 print("❌ ERRO CRÍTICO: Inconsistência nas contagens persiste.")
            
        print(f"Dados do cartório carregados e processados: {total_registros} registros ({count_cat_16} Casa Verde, {count_cat_34} Tatuapé)")
        return df
        
    except Exception as e:
        import traceback
        print(f"Erro ao carregar/processar dados do cartório: {str(e)}")
        print(traceback.format_exc())
        return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro 