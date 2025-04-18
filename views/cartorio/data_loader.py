import streamlit as st
import pandas as pd
from api.bitrix_connector import load_bitrix_data, get_credentials
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def load_data():
    """
    Carrega dados do cartório com filtros rigorosos para garantir que apenas
    registros válidos dos cartórios Casa Verde (16) e Tatuapé (34) sejam incluídos.
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
    
    # Verificar contagem inicial
    print(f"[DEBUG] Total de registros brutos: {len(df_items)}")
    
    # Criar cópia antes de modificar para evitar warnings
    df_items = df_items.copy()
    
    # Verificar se a coluna CATEGORY_ID existe
    if 'CATEGORY_ID' not in df_items.columns:
        st.error("Coluna CATEGORY_ID não encontrada nos dados carregados.")
        print(f"[DEBUG] Colunas disponíveis: {df_items.columns.tolist()}")
        return pd.DataFrame()
    
    # Converter CATEGORY_ID para numérico e garantir valores corretos
    try:
        # Converter para numérico, tratando valores não numéricos como NaN
        df_items['CATEGORY_ID'] = pd.to_numeric(df_items['CATEGORY_ID'], errors='coerce')
        
        # Remover NaN
        df_items = df_items.dropna(subset=['CATEGORY_ID'])
        
        # Verificar tipos antes de conversão para inteiro
        print(f"[DEBUG] Tipo de CATEGORY_ID: {df_items['CATEGORY_ID'].dtype}")
        
        # Converter para inteiro para garantir comparações precisas
        df_items['CATEGORY_ID'] = df_items['CATEGORY_ID'].astype('int64')
    except Exception as e:
        print(f"[DEBUG] Erro ao processar CATEGORY_ID: {str(e)}")
        return pd.DataFrame()
    
    # Verificar valores únicos na coluna CATEGORY_ID
    categorias_unicas = df_items['CATEGORY_ID'].unique()
    print(f"[DEBUG] Valores únicos em CATEGORY_ID: {categorias_unicas}")
    
    # PASSO CRUCIAL: Filtrar rigidamente apenas os registros com CATEGORY_ID exatamente 16 ou 34
    df_filtrado_casa_verde = df_items[df_items['CATEGORY_ID'] == 16].copy()
    df_filtrado_tatuape = df_items[df_items['CATEGORY_ID'] == 34].copy()
    
    # Concatenar os DataFrames filtrados
    df_filtrado = pd.concat([df_filtrado_casa_verde, df_filtrado_tatuape], ignore_index=True)
    
    # Verificar a contagem por categoria após a filtragem
    print(f"[DEBUG] Total após filtragem por categoria: {len(df_filtrado)}")
    print(f"[DEBUG] - Casa Verde (16): {len(df_filtrado_casa_verde)}")
    print(f"[DEBUG] - Tatuapé (34): {len(df_filtrado_tatuape)}")
    
    # Verificar se temos registros duplicados por ID
    if 'ID' in df_filtrado.columns:
        duplicados = df_filtrado.duplicated(subset=['ID'])
        n_duplicados = duplicados.sum()
        
        if n_duplicados > 0:
            print(f"[DEBUG] Encontrados {n_duplicados} registros duplicados por ID. Removendo duplicados...")
            df_filtrado = df_filtrado.drop_duplicates(subset=['ID'], keep='first')
    
    # Adicionar o nome do cartório para melhor visualização
    df_filtrado['NOME_CARTORIO'] = df_filtrado['CATEGORY_ID'].map({
        16: 'CARTÓRIO CASA VERDE',
        34: 'CARTÓRIO TATUÁPE'
    })
    
    # print(f"[DEBUG] Total final após todo processamento: {len(df_filtrado)}")                 # Log comentado
    # print(f"[DEBUG] - Casa Verde (16): {(df_filtrado['CATEGORY_ID'] == 16).sum()}")       # Log comentado
    # print(f"[DEBUG] - Tatuapé (34): {(df_filtrado['CATEGORY_ID'] == 34).sum()}")           # Log comentado
    
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
    Carrega os dados dos cartórios Casa Verde (16) e Tatuápe (34) garantindo
    a correta filtragem e contagem dos registros.
    
    Returns:
        pandas.DataFrame: DataFrame com os dados dos cartórios filtrados.
    """
    try:
        # Carregar dados brutos
        df = load_data()
        
        if df.empty:
            print("Nenhum dado de cartório carregado.")
            return pd.DataFrame()

        # GARANTIR dados EXATAMENTE conforme esperado
        # 1. Verificar e converter CATEGORY_ID para numérico, se necessário
        if df['CATEGORY_ID'].dtype != 'int64':
            df['CATEGORY_ID'] = pd.to_numeric(df['CATEGORY_ID'], errors='coerce')
            df = df.dropna(subset=['CATEGORY_ID'])
            
        # 2. Verificar se há duplicações baseado no ID (aplicando novamente para garantia)
        duplicados = df.duplicated(subset=['ID'], keep=False)
        if duplicados.any():
            # Registrar no log a presença de duplicações
            n_duplicados = duplicados.sum()
            print(f"ATENÇÃO: Encontrados {n_duplicados} registros duplicados por ID. Mantendo apenas a primeira ocorrência.")
            
            # Manter apenas a primeira ocorrência de cada ID
            df = df.drop_duplicates(subset=['ID'], keep='first')
        
        # 3. Garantir filtragem ESTRITA por categoria 16 e 34
        # Aplicar filtro rigoroso para manter apenas registros das categorias 16 e 34
        df = df[df['CATEGORY_ID'].isin([16, 34])].copy()
        
        # 4. Verificar e remover registros que não pertencem às categorias 16 e 34 (redundante, mas para garantia)
        registros_invalidos = ~df['CATEGORY_ID'].isin([16, 34])
        if registros_invalidos.any():
            n_invalidos = registros_invalidos.sum()
            print(f"ATENÇÃO: Removidos {n_invalidos} registros com categorias diferentes de 16 e 34.")
            
            # Aplicar filtro novamente para garantir
            df = df[df['CATEGORY_ID'].isin([16, 34])]
        
        # 5. Verificar se há valores nulos em CATEGORY_ID
        nulos = df['CATEGORY_ID'].isna()
        if nulos.any():
            n_nulos = nulos.sum()
            print(f"ATENÇÃO: Removidos {n_nulos} registros com CATEGORY_ID nulo.")
            df = df.dropna(subset=['CATEGORY_ID'])
        
        # 6. Garantir mapeamento dos nomes de cartório - FORÇAR valores corretos
        df['NOME_CARTORIO'] = df['CATEGORY_ID'].map({
            16: 'CARTÓRIO CASA VERDE',
            34: 'CARTÓRIO TATUÁPE'
        })
        
        # 7. Força verificação final para garantir dados íntegros
        # Confirmar que os valores de CATEGORY_ID são apenas 16 e 34
        categorias_unicas = df['CATEGORY_ID'].unique()
        # print(f"Categorias presentes após filtragem: {categorias_unicas}")                      # Log comentado
        
        # 8. Confirmar total de registros e contagem por categoria  
        count_cat_16 = (df['CATEGORY_ID'] == 16).sum()
        count_cat_34 = (df['CATEGORY_ID'] == 34).sum()
        total_registros = len(df)
        
        # 9. Verificação final - garantir que números batem
        if count_cat_16 + count_cat_34 != total_registros:
            print(f"ERRO GRAVE: Ainda há inconsistência nas contagens! Total: {total_registros}, Soma categorias: {count_cat_16 + count_cat_34}")
            # Última tentativa de correção
            df = df[df['CATEGORY_ID'].isin([16, 34])].copy()
            count_cat_16 = (df['CATEGORY_ID'] == 16).sum()
            count_cat_34 = (df['CATEGORY_ID'] == 34).sum()
            total_registros = len(df)
        
        # print(f"Dados do cartório carregados com sucesso: {total_registros} registros")        # Log comentado
        # print(f"- Cartório Casa Verde (16): {count_cat_16} registros")                     # Log comentado
        # print(f"- Cartório Tatuapé (34): {count_cat_34} registros")                      # Log comentado
        
        # 10. Verificação FINAL absoluta - se ainda houver inconsistência, mostrar aviso CRÍTICO
        if count_cat_16 + count_cat_34 != total_registros:
            print("❌ ERRO CRÍTICO: Após todas as tentativas, ainda há inconsistência nas contagens.")
            
        return df
    except Exception as e:
        import traceback
        print(f"Erro ao carregar dados do cartório: {str(e)}")
        print(traceback.format_exc())
        return pd.DataFrame()  # Retorna DataFrame vazio em caso de erro 