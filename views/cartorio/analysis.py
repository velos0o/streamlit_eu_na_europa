import pandas as pd
import re
import streamlit as st
from datetime import datetime
import io
from .data_loader import carregar_estagios_bitrix, carregar_dados_negocios

def analyze_cartorio_ids(df):
    """
    Analisa os IDs de família no DataFrame para cartórios e retorna o resumo e detalhes
    """
    if 'UF_CRM_12_1723552666' not in df.columns:
        return pd.DataFrame(), pd.DataFrame()
    
    # Função para verificar se o ID está no padrão correto
    def check_id_pattern(id_str):
        # Verificar todos os tipos possíveis de valores vazios
        if pd.isna(id_str) or id_str == '' or id_str is None or (isinstance(id_str, str) and id_str.strip() == ''):
            return 'Vazio'
        if not isinstance(id_str, str):
            return 'Formato Inválido'
        # Remover espaços em branco antes de verificar o padrão
        id_str = id_str.strip()
        pattern = r'^\d+x\d+$'
        if re.match(pattern, id_str):
            return 'Padrão Correto'
        return 'Formato Inválido'

    # Criar uma cópia do DataFrame para análise
    analysis_df = df.copy()
    
    # Primeiro, identificar registros vazios
    analysis_df['ID_STATUS'] = analysis_df['UF_CRM_12_1723552666'].apply(check_id_pattern)
    
    # Depois, identificar duplicados apenas entre os registros não vazios e com formato válido
    validos_mask = (analysis_df['ID_STATUS'] == 'Padrão Correto')
    
    # Criar uma série temporária apenas com os IDs válidos para verificar duplicados
    ids_validos = analysis_df.loc[validos_mask, 'UF_CRM_12_1723552666'].str.strip()
    duplicados_mask = ids_validos.duplicated(keep=False)
    
    # Marcar duplicados apenas nos registros válidos que estão duplicados
    analysis_df.loc[ids_validos[duplicados_mask].index, 'ID_STATUS'] = 'Duplicado'
    
    # Criar resumo
    summary = pd.DataFrame({
        'Status': ['Padrão Correto', 'Duplicado', 'Vazio', 'Formato Inválido'],
        'Quantidade': [
            sum((analysis_df['ID_STATUS'] == 'Padrão Correto')),
            sum((analysis_df['ID_STATUS'] == 'Duplicado')),
            sum((analysis_df['ID_STATUS'] == 'Vazio')),
            sum((analysis_df['ID_STATUS'] == 'Formato Inválido'))
        ]
    })
    
    # Criar detalhamento
    details = analysis_df[[
        'ID',
        'TITLE',
        'UF_CRM_12_1723552666',
        'ASSIGNED_BY_NAME',
        'NOME_CARTORIO',
        'ID_STATUS'
    ]].copy()
    
    details = details.rename(columns={
        'ID': 'ID',
        'TITLE': 'Nome',
        'UF_CRM_12_1723552666': 'ID Família',
        'ASSIGNED_BY_NAME': 'Responsável',
        'NOME_CARTORIO': 'Cartório',
        'ID_STATUS': 'Status do ID'
    })
    
    # Ordenar o detalhamento por Status do ID, Cartório e Responsável
    details = details.sort_values(['Status do ID', 'Cartório', 'Responsável'])
    
    return summary, details

def criar_visao_geral_cartorio(df):
    """
    Cria uma visão geral dos cartórios com os estágios como colunas
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos cartórios
        
    Returns:
        pandas.DataFrame: DataFrame pivotado com os estágios como colunas
    """
    if df.empty:
        return pd.DataFrame()
    
    # Verificar se temos o stage_name diretamente nos dados ou se precisamos obtê-lo
    if 'STAGE_NAME' not in df.columns:
        # Verificar se temos stage_id para fazer o mapeamento
        if 'STAGE_ID' not in df.columns:
            st.error("Colunas STAGE_ID ou STAGE_NAME não encontradas.")
            st.write("Colunas disponíveis:", df.columns.tolist())
            return pd.DataFrame()
        
        # Obter estágios do Bitrix
        df_stages = carregar_estagios_bitrix()
        
        # Lista dos estágios específicos para exibir (IDs)
        estagios_especificos = [
            'DT1052_16:FAIL',
            'DT1052_16:NEW',
            'DT1052_16:SUCCESS',
            'DT1052_16:UC_7F0WK2',
            'DT1052_16:UC_HYO7L2',
            'DT1052_16:UC_JRGCW3',
            'DT1052_16:UC_KXHDOQ',
            'DT1052_16:UC_P61ZVH',
            'DT1052_16:UC_R5UEXF'
        ]
        
        # Criar mapeamento de STAGE_ID para nome do estágio
        stage_mapping = {}
        
        # Filtrar apenas os estágios dos pipelines de cartório
        if not df_stages.empty and 'STATUS_ID' in df_stages.columns and 'NAME' in df_stages.columns:
            # Filtrar estágios relacionados aos pipelines de cartório
            df_stages_filtered = df_stages[df_stages['STATUS_ID'].isin(estagios_especificos)]
            
            # Criar um mapeamento de STAGE_ID para nome do estágio
            stage_mapping = dict(zip(df_stages_filtered['STATUS_ID'], df_stages_filtered['NAME']))
        
        # Se não conseguiu obter nomes dos estágios, usar os IDs originais sem o prefixo
        for estagio in estagios_especificos:
            if estagio not in stage_mapping:
                # Extrair apenas o nome sem o prefixo (tudo após o ":")
                nome_simplificado = estagio.split(':')[-1]
                stage_mapping[estagio] = nome_simplificado
        
        # Adicionar a coluna STAGE_NAME mapeada a partir do STAGE_ID
        df['STAGE_NAME'] = df['STAGE_ID'].map(stage_mapping)
        
        # Se após o mapeamento ainda tiver valores nulos, usar o STAGE_ID original
        df['STAGE_NAME'] = df['STAGE_NAME'].fillna(df['STAGE_ID'])
    
    # Lista dos nomes de estágios que queremos exibir
    # Se não tivermos os IDs específicos, vamos verificar nos dados existentes
    if 'STAGE_NAME' in df.columns:
        estagios_disponiveis = df['STAGE_NAME'].unique().tolist()
        stage_names_especificos = [
            'FAIL', 'NEW', 'SUCCESS', 'UC_7F0WK2', 'UC_HYO7L2', 
            'UC_JRGCW3', 'UC_KXHDOQ', 'UC_P61ZVH', 'UC_R5UEXF'
        ]
        
        # Filtrar apenas os estágios que realmente existem nos dados
        estagios_para_exibir = []
        for estagio in estagios_disponiveis:
            # Verificar se o estágio corresponde a algum dos específicos (comparando finais de string)
            for estagio_especifico in stage_names_especificos:
                if estagio.endswith(estagio_especifico):
                    estagios_para_exibir.append(estagio)
                    break
        
        # Se não encontramos nenhum estágio específico, usar todos os disponíveis
        if not estagios_para_exibir:
            estagios_para_exibir = estagios_disponiveis
    else:
        estagios_para_exibir = []
    
    # Contar registros por responsável e estágio
    if not df.empty and 'ASSIGNED_BY_NAME' in df.columns and 'STAGE_NAME' in df.columns:
        contagem = df.groupby(['ASSIGNED_BY_NAME', 'STAGE_NAME', 'NOME_CARTORIO']).size().reset_index(name='TOTAL')
        
        # Filtrar apenas os estágios específicos se tivermos algum
        if estagios_para_exibir:
            contagem = contagem[contagem['STAGE_NAME'].isin(estagios_para_exibir)]
        
        # Criar a tabela pivotada com estágios como colunas
        pivot_table = contagem.pivot_table(
            index=['ASSIGNED_BY_NAME', 'NOME_CARTORIO'],
            columns='STAGE_NAME',
            values='TOTAL',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Calcular totais por responsável
        pivot_table['TOTAL'] = pivot_table.iloc[:, 2:].sum(axis=1)
        
        # Adicionar percentual baseado nos estágios SUCCESS
        # Verificar se temos estágios SUCCESS nos dados
        success_columns = []
        for col in pivot_table.columns:
            if isinstance(col, str) and ':SUCCESS' in col:
                success_columns.append(col)
        
        # Se encontramos alguma coluna SUCCESS, calcular o percentual
        if success_columns:
            # Somar todos os SUCCESS para cada linha
            pivot_table['TOTAL_SUCCESS'] = 0
            for col in success_columns:
                pivot_table['TOTAL_SUCCESS'] += pivot_table[col]
            
            # Calcular percentual (Total / Total_SUCCESS)
            pivot_table['PERCENTUAL_CONVERSAO'] = 0.0
            mask = pivot_table['TOTAL_SUCCESS'] > 0
            pivot_table.loc[mask, 'PERCENTUAL_CONVERSAO'] = (pivot_table.loc[mask, 'TOTAL'] / pivot_table.loc[mask, 'TOTAL_SUCCESS'] * 100).round(2)
        
        return pivot_table
    else:
        st.error("Colunas necessárias não encontradas para criar a visão geral.")
        if not df.empty:
            st.write("Colunas disponíveis:", df.columns.tolist())
        return pd.DataFrame()

def analisar_familias_ausentes():
    """
    Analisa famílias que estão presentes em crm_deal (ID da Família em UF_CRM_1722605592778)
    mas não estão presentes em crm_dynamic_item_1052 (ID da Família em UF_CRM_12_1723552666).
    
    Filtra apenas negócios da categoria 32.
    
    Returns:
        tuple: (Métrica de contagem, DataFrame com os detalhes dos negócios ausentes)
    """
    try:
        # Criar placeholders para o progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Carregar dados
        status_text.info("Carregando negócios da categoria 32...")
        progress_bar.progress(10)
        
        from .data_loader import carregar_dados_cartorio
        
        # Carregar dados dos negócios
        df_deal, df_deal_uf = carregar_dados_negocios()
        
        # Verificar se conseguiu carregar os dados
        if df_deal.empty:
            progress_bar.progress(100)
            status_text.error("Não foi possível carregar os dados da tabela crm_deal para a categoria 32.")
            return 0, pd.DataFrame()
            
        # Mostrar progresso
        status_text.info(f"Carregados {len(df_deal)} negócios da categoria 32")
        progress_bar.progress(30)
        
        # Carregar dados de cartório
        status_text.info("Carregando cadastro de famílias...")
        progress_bar.progress(70)
        
        df_cartorio = carregar_dados_cartorio()
        
        # Simplificar: manter apenas a coluna necessária para a comparação
        df_dynamic_item = df_cartorio[['UF_CRM_12_1723552666']] if not df_cartorio.empty else pd.DataFrame()
        
        # Verificar se conseguiu carregar os dados
        if df_dynamic_item.empty:
            progress_bar.progress(100)
            status_text.error("Não foi possível carregar os dados da tabela crm_dynamic_items_1052.")
            return 0, pd.DataFrame()
        
        # Mesclar df_deal com df_deal_uf para obter os IDs de família
        status_text.info("Analisando dados...")
        progress_bar.progress(80)
        
        # Usar merge otimizado
        df_merged = pd.merge(
            df_deal,
            df_deal_uf,
            left_on='ID',
            right_on='DEAL_ID',
            how='inner'
        )
        
        # Filtrar apenas registros que possuem ID de família
        df_merged = df_merged[df_merged['UF_CRM_1722605592778'].notna()]
        
        if df_merged.empty:
            progress_bar.progress(100)
            status_text.warning("Não foram encontrados registros com ID de família na categoria 32.")
            return 0, pd.DataFrame()
        
        # Filtrar apenas registros que possuem ID de família em crm_dynamic_item
        df_dynamic_item = df_dynamic_item[df_dynamic_item['UF_CRM_12_1723552666'].notna()]
        
        if df_dynamic_item.empty:
            progress_bar.progress(100)
            status_text.warning("Não foram encontrados registros com ID de família na tabela crm_dynamic_items_1052.")
            return 0, pd.DataFrame()
        
        # Obter lista de IDs de família em cada tabela
        ids_familia_deal = df_merged['UF_CRM_1722605592778'].dropna().unique().astype(str)
        ids_familia_dynamic = df_dynamic_item['UF_CRM_12_1723552666'].dropna().unique().astype(str)
        
        # Encontrar IDs de família que existem em crm_deal mas não em crm_dynamic_item_1052
        ids_ausentes = set(ids_familia_deal) - set(ids_familia_dynamic)
        
        # Contagem de famílias ausentes
        total_ausentes = len(ids_ausentes)
        
        # Atualizar progresso
        progress_bar.progress(90)
        status_text.info(f"Encontradas {total_ausentes} famílias não cadastradas")
        
        # Se não houver famílias ausentes, retornar
        if total_ausentes == 0:
            progress_bar.progress(100)
            status_text.success("Análise concluída: não há famílias ausentes.")
            return 0, pd.DataFrame()
        
        # Filtrar os negócios que têm as famílias ausentes
        df_ausentes = df_merged[df_merged['UF_CRM_1722605592778'].astype(str).isin(ids_ausentes)]
        
        # Renomear colunas para melhor visualização
        df_resultado = df_ausentes.rename(columns={
            'ID': 'ID do Negócio',
            'UF_CRM_1722605592778': 'ID da Família',
            'TITLE': 'Nome do Negócio',
            'ASSIGNED_BY_NAME': 'Responsável'
        })
        
        # Selecionar apenas as colunas relevantes na ordem solicitada
        df_resultado = df_resultado[['ID do Negócio', 'Nome do Negócio', 'Responsável', 'ID da Família']]
        
        # Concluir progresso
        progress_bar.progress(100)
        status_text.success("Análise concluída com sucesso!")
        
        return total_ausentes, df_resultado
        
    except Exception as e:
        st.error(f"Erro durante a análise: {str(e)}")
        return 0, pd.DataFrame()

def analisar_familia_certidoes():
    """
    Analisa os dados de famílias, cruzando informações entre diferentes tabelas para obter:
    - NOME da família
    - ID FAMILIA (UF_CRM_12_1723552666)
    - RESPONSAVEL ADM (cruzamento com category_id = 32)
    - CARTÓRIO (PIPELINE)
    - ASSIGN
    - TOTAL DE CERTIDÕES (contagem de repetições do ID)
    - RESPONSAVEL VENDAS (cruzamento com category_id = 6)
    - CERTIDÕES ENTREGUES (etapas de ganhos e sucesso)
    - STATUS DA HIGILIZAÇÃO (UF_CRM_HIGILIZACAO_STATUS da category_id = 32)
    
    Returns:
        pandas.DataFrame: Tabela com a análise completa
    """
    try:
        # Criar placeholders para o progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Carregar dados dos cartórios (onde está UF_CRM_12_1723552666)
        status_text.info("Carregando dados de famílias dos cartórios...")
        from .data_loader import carregar_dados_cartorio, carregar_dados_negocios, load_bitrix_data, get_credentials
        
        df_cartorio = carregar_dados_cartorio()
        progress_bar.progress(20)
        
        if df_cartorio.empty:
            status_text.error("Não foi possível carregar os dados dos cartórios.")
            progress_bar.progress(100)
            return pd.DataFrame()
        
        # Filtrar apenas os registros que possuem ID de família
        df_cartorio = df_cartorio[['ID', 'TITLE', 'UF_CRM_12_1723552666', 'UF_CRM_12_1723552729', 'ASSIGNED_BY_NAME', 'NOME_CARTORIO', 'STAGE_ID']].copy()
        df_cartorio = df_cartorio.dropna(subset=['UF_CRM_12_1723552666'])
        
        status_text.info(f"Encontradas {len(df_cartorio)} famílias com ID nos cartórios")
        progress_bar.progress(30)
        
        # Obter negócios da categoria 32 (Administrativo)
        status_text.info("Carregando negócios administrativos (Categoria 32)...")
        df_adm, df_adm_uf = carregar_dados_negocios()
        progress_bar.progress(50)
        
        if df_adm.empty:
            status_text.warning("Não foi possível carregar os negócios da categoria 32.")
        
        # Obter negócios da categoria 6 (Vendas)
        status_text.info("Carregando negócios de vendas (Categoria 6)...")
        
        # Obter token do Bitrix24
        BITRIX_TOKEN, BITRIX_URL = get_credentials()
        
        # URL para acessar a tabela crm_deal
        url_deal = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
        url_deal_uf = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
        
        # Preparar filtro para a categoria 6 (Vendas)
        category_filter = {"dimensionsFilters": [[]]}
        category_filter["dimensionsFilters"][0].append({
            "fieldName": "CATEGORY_ID", 
            "values": ["6"], 
            "type": "INCLUDE", 
            "operator": "EQUALS"
        })
        
        # Carregar dados de vendas
        df_vendas = load_bitrix_data(url_deal, filters=category_filter)
        
        progress_bar.progress(70)
        
        if df_vendas.empty:
            status_text.warning("Não foi possível carregar os negócios da categoria 6 (Vendas).")
        else:
            # Simplificar: selecionar apenas as colunas necessárias
            df_vendas = df_vendas[['ID', 'TITLE', 'ASSIGNED_BY_NAME', 'STAGE_ID']].copy()
            
            # Obter lista de IDs dos deals para filtrar a tabela crm_deal_uf
            deal_ids = df_vendas['ID'].astype(str).tolist()
            
            # Limitar a quantidade de IDs para evitar sobrecarga (se houverem muitos)
            if len(deal_ids) > 1000:
                deal_ids = deal_ids[:1000]
            
            # Filtro para crm_deal_uf baseado nos IDs dos deals da categoria 6
            deal_filter = {"dimensionsFilters": [[]]}
            deal_filter["dimensionsFilters"][0].append({
                "fieldName": "DEAL_ID", 
                "values": deal_ids, 
                "type": "INCLUDE", 
                "operator": "EQUALS"
            })
            
            # Carregar campos UF dos negócios de vendas
            df_vendas_uf = load_bitrix_data(url_deal_uf, filters=deal_filter)
            
            if not df_vendas_uf.empty:
                # Manter apenas as colunas necessárias
                df_vendas_uf = df_vendas_uf[['DEAL_ID', 'UF_CRM_1722605592778']].copy()
        
        progress_bar.progress(85)
        status_text.info("Processando dados e realizando cruzamentos...")
        
        # Agrupar por ID de família para obter contagens
        analise_familia = df_cartorio.groupby('UF_CRM_12_1723552666').agg(
            NOME=('TITLE', 'first'),
            CARTORIO=('NOME_CARTORIO', 'first'),
            ASSIGN=('ASSIGNED_BY_NAME', 'first'),
            TOTAL_CERTIDOES=('ID', 'count'),
            ID_REQUERENTE=('UF_CRM_12_1723552729', lambda x: x.iloc[0] if not x.isna().all() else 'Não disponível')
        ).reset_index()
        
        # Renomear a coluna de ID
        analise_familia = analise_familia.rename(columns={'UF_CRM_12_1723552666': 'ID_FAMILIA'})
        
        # Calcular total de requerentes únicos por família
        def contar_requerentes_unicos(id_familia):
            df_filtrado = df_cartorio[df_cartorio['UF_CRM_12_1723552666'] == id_familia]
            requerentes_unicos = df_filtrado['UF_CRM_12_1723552729'].dropna().unique()
            return len(requerentes_unicos)
            
        # Adicionar contagem de requerentes únicos
        analise_familia['TOTAL_REQUERENTES'] = analise_familia['ID_FAMILIA'].apply(contar_requerentes_unicos)
        
        # Adicionar contagem de membros por família (cada ID de certidão representa um membro)
        analise_familia['MEMBROS'] = analise_familia['TOTAL_CERTIDOES'] / 3  # Considerando média de 3 certidões por membro
        # Garantir que o número de membros seja pelo menos 1
        analise_familia['MEMBROS'] = analise_familia['MEMBROS'].apply(lambda x: max(1, round(x)))

        # Adicionar contagem de certidões entregues (SUCCESS)
        def contar_certidoes_entregues(id_familia):
            # Filtrar pelo ID da família
            df_filtrado = df_cartorio[df_cartorio['UF_CRM_12_1723552666'] == id_familia]
            
            # Lista de códigos de estágio que representam sucesso (baseado no arquivo visualization.py)
            success_codes = [
                'SUCCESS', 
                'DT1052_16:SUCCESS', 
                'DT1052_34:SUCCESS',
                'DT1052_16:UC_JRGCW3',
                'DT1052_34:UC_84B1S2',
                'UC_JRGCW3',
                'UC_84B1S2',
                'DT1052_16:CLIENT',
                'DT1052_34:CLIENT',
                'DT1052_34:UC_D0RG5P',
                'CLIENT',
                'UC_D0RG5P'
            ]
            
            # Verificar se algum dos registros tem estágio de sucesso
            return sum(df_filtrado['STAGE_ID'].isin(success_codes))
        
        # Aplicar a função em cada ID de família
        analise_familia['CERTIDOES_ENTREGUES'] = analise_familia['ID_FAMILIA'].apply(contar_certidoes_entregues)
        
        # Adicionar responsável ADM e status da higienização
        if not df_adm.empty and not df_adm_uf.empty:
            # Mesclar ID da família do negócio (UF_CRM_1722605592778) com o responsável
            df_adm_completo = pd.merge(
                df_adm, 
                df_adm_uf, 
                left_on='ID', 
                right_on='DEAL_ID', 
                how='inner'
            )
            
            # Criar dicionário para mapear ID da família para responsável ADM
            resp_adm_map = {}
            status_higienizacao_map = {}
            
            # Verificar se a coluna de higienização existe nos dados
            tem_coluna_higienizacao = 'UF_CRM_HIGILIZACAO_STATUS' in df_adm_uf.columns
            
            for _, row in df_adm_completo.iterrows():
                if not pd.isna(row['UF_CRM_1722605592778']):
                    resp_adm_map[row['UF_CRM_1722605592778']] = row['ASSIGNED_BY_NAME']
                    
                    # Obter status de higienização apenas se a coluna existir
                    if tem_coluna_higienizacao:
                        status = row['UF_CRM_HIGILIZACAO_STATUS'] if 'UF_CRM_HIGILIZACAO_STATUS' in row and not pd.isna(row['UF_CRM_HIGILIZACAO_STATUS']) else 'Não definido'
                    else:
                        status = 'Campo não disponível'
                    
                    status_higienizacao_map[row['UF_CRM_1722605592778']] = status
            
            # Aplicar mapeamento para obter o responsável ADM
            analise_familia['RESPONSAVEL_ADM'] = analise_familia['ID_FAMILIA'].map(resp_adm_map)
            analise_familia['STATUS_HIGILIZACAO'] = analise_familia['ID_FAMILIA'].map(status_higienizacao_map)
            
            # Substituir valores NaN no status de higienização
            analise_familia['STATUS_HIGILIZACAO'] = analise_familia['STATUS_HIGILIZACAO'].fillna('Não encontrado')
        else:
            analise_familia['RESPONSAVEL_ADM'] = 'Não disponível'
            analise_familia['STATUS_HIGILIZACAO'] = 'Não disponível'
        
        # Adicionar responsável de vendas
        if 'df_vendas' in locals() and not df_vendas.empty and 'df_vendas_uf' in locals() and not df_vendas_uf.empty:
            # Mesclar ID da família do negócio (UF_CRM_1722605592778) com o responsável de vendas
            df_vendas_completo = pd.merge(
                df_vendas, 
                df_vendas_uf, 
                left_on='ID', 
                right_on='DEAL_ID', 
                how='inner'
            )
            
            # Criar dicionário para mapear ID da família para responsável de vendas
            resp_vendas_map = {}
            
            for _, row in df_vendas_completo.iterrows():
                if not pd.isna(row['UF_CRM_1722605592778']):
                    resp_vendas_map[row['UF_CRM_1722605592778']] = row['ASSIGNED_BY_NAME']
            
            # Aplicar mapeamento para obter o responsável de vendas
            analise_familia['RESPONSAVEL_VENDAS'] = analise_familia['ID_FAMILIA'].map(resp_vendas_map)
        else:
            analise_familia['RESPONSAVEL_VENDAS'] = 'Não disponível'
        
        # Finalizar progresso
        progress_bar.progress(100)
        status_text.success(f"Análise concluída para {len(analise_familia)} famílias")
        
        # Ordenar pelo número total de certidões (decrescente)
        analise_familia = analise_familia.sort_values('TOTAL_CERTIDOES', ascending=False)
        
        # Preencher valores NaN
        analise_familia = analise_familia.fillna('Não disponível')
        
        return analise_familia
        
    except Exception as e:
        st.error(f"Erro na análise de famílias: {str(e)}")
        return pd.DataFrame() 