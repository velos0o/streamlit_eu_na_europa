import requests
import json
import pandas as pd
import streamlit as st
from datetime import datetime
import time
import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Obter o caminho absoluto para a pasta utils
utils_path = os.path.join(Path(__file__).parents[1], 'utils')
sys.path.insert(0, str(utils_path))

# Agora importa diretamente do arquivo animation_utils
from animation_utils import update_progress

# Carregar variáveis de ambiente
load_dotenv()

# Obter credenciais do ambiente ou Streamlit Secrets
def get_credentials():
    """
    Obtém as credenciais do Bitrix24 de acordo com o ambiente:
    1. Primeiro tenta do Streamlit Secrets
    2. Se não encontrar, tenta das variáveis de ambiente (.env)
    3. Se não encontrar, usa os valores padrão (que devem ser substituídos em produção)
    """
    try:
        # Verificar se estamos em ambiente Streamlit Cloud
        if hasattr(st, 'secrets') and 'BITRIX_TOKEN' in st.secrets:
            token = st.secrets.BITRIX_TOKEN
            url = st.secrets.BITRIX_URL
        else:
            # Usar variáveis de ambiente locais
            token = os.getenv('BITRIX_TOKEN')
            url = os.getenv('BITRIX_URL')
    except Exception as e:
        # Se ocorrer qualquer erro ao tentar acessar secrets, usar variáveis de ambiente
        token = os.getenv('BITRIX_TOKEN')
        url = os.getenv('BITRIX_URL')
    
    # Retornar valores padrão se não encontrados
    if not token or not url:
        token = "RuUSETRkbFD3whitfgMbioX8qjLgcdPubr"  # Token padrão - substitua em produção
        url = "https://eunaeuropacidadania.bitrix24.com.br"  # URL padrão - substitua em produção
    
    return token, url

# Obter credenciais
BITRIX_TOKEN, BITRIX_URL = get_credentials()

# URLs base para acesso às tabelas do Bitrix24
BITRIX_CRM_DEAL_URL = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
BITRIX_CRM_DEAL_UF_URL = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"

# Variável de controle para logs de depuração
SHOW_DEBUG_INFO = False

# Função para carregar os dados do Bitrix com cache do Streamlit
@st.cache_data(ttl=3600)  # Cache válido por 1 hora
def load_bitrix_data(url, filters=None, show_logs=False):
    """
    Carrega dados do Bitrix24 via API.
    
    Args:
        url (str): URL da API Bitrix24
        filters (dict, optional): Filtros para a consulta
        show_logs (bool): Se deve exibir logs de depuração
        
    Returns:
        pandas.DataFrame: DataFrame com os dados obtidos
    """
    try:
        if show_logs:
            st.info(f"Tentando acessar: {url}")
        headers = {"Content-Type": "application/json"}
        
        # Tentar até 3 vezes em caso de falha
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if filters:
                    if show_logs:
                        st.write(f"Enviando filtros: {json.dumps(filters)}")
                    response = requests.post(url, data=json.dumps(filters), headers=headers, timeout=30)
                else:
                    response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    # Tentar interpretar a resposta como JSON
                    try:
                        data = response.json()
                        
                        # Verificar se obtivemos dados
                        if data:
                            # Mostrar um exemplo da estrutura dos dados para diagnóstico
                            if show_logs:
                                st.write("Estrutura da resposta da API:")
                            
                            # Verificar o formato dos dados
                            if isinstance(data, list):
                                # Se for uma lista, verificar o primeiro item
                                if len(data) > 0:
                                    first_item = data[0]
                                    
                                    # Verificar se o primeiro item parece ser um cabeçalho
                                    if isinstance(first_item, list):
                                        if show_logs:
                                            st.write("Dados em formato tabular com cabeçalhos na primeira linha")
                                            st.write(f"Cabeçalhos encontrados: {first_item}")
                                        
                                        # Usar a primeira linha como cabeçalhos e o resto como dados
                                        headers = data[0]
                                        
                                        # Criar dicionário para cada linha usando os cabeçalhos
                                        rows = []
                                        for row in data[1:]:
                                            row_dict = {}
                                            for i, value in enumerate(row):
                                                if i < len(headers):
                                                    row_dict[headers[i]] = value
                                            rows.append(row_dict)
                                        
                                        # Criar DataFrame com os dados transformados
                                        df = pd.DataFrame(rows)
                                        
                                    elif isinstance(first_item, dict):
                                        if show_logs:
                                            st.write(f"Colunas disponíveis: {list(first_item.keys())}")
                                            st.write("Exemplo do primeiro registro:")
                                            st.json(first_item)
                                        df = pd.DataFrame(data)
                                    else:
                                        if show_logs:
                                            st.write(f"Colunas disponíveis: ['Item não é um dicionário']")
                                            st.write("Exemplo do primeiro registro:")
                                            st.json(first_item)
                                        # Tentar criar um DataFrame mesmo assim
                                        df = pd.DataFrame(data)
                            else:
                                if show_logs:
                                    st.write(f"Tipo de dados recebido: {type(data)}")
                                    st.write(f"Amostra: {str(data)[:500]}")
                                df = pd.DataFrame([data])
                            
                            # Mostrar informações do DataFrame para diagnóstico
                            if show_logs:
                                st.write(f"DataFrame criado com {len(df)} linhas e {len(df.columns)} colunas")
                                st.write(f"Colunas do DataFrame: {list(df.columns)}")
                            
                            return df
                        else:
                            if show_logs:
                                st.warning(f"A API retornou uma lista vazia na tentativa {attempt + 1}")
                            if attempt < max_attempts - 1:
                                time.sleep(2)  # Aguardar antes de tentar novamente
                            else:
                                return pd.DataFrame()
                    except json.JSONDecodeError as je:
                        if show_logs:
                            st.error(f"Erro ao decodificar JSON: {str(je)}")
                            st.write(f"Resposta da API (primeiros 500 caracteres): {response.text[:500]}")
                        return pd.DataFrame()
                else:
                    if show_logs:
                        st.error(f"Erro ao acessar a API Bitrix24 na tentativa {attempt + 1}: Código {response.status_code}")
                        st.write(f"Resposta da API: {response.text[:500]}")
                    if attempt < max_attempts - 1:
                        time.sleep(2)  # Aguardar antes de tentar novamente
                    else:
                        return pd.DataFrame()
            except requests.exceptions.RequestException as re:
                if show_logs:
                    st.error(f"Erro de conexão na tentativa {attempt + 1}: {str(re)}")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Aguardar antes de tentar novamente
                else:
                    return pd.DataFrame()
        
        return pd.DataFrame()  # Retornar DataFrame vazio se todas as tentativas falharem
        
    except Exception as e:
        if show_logs:
            st.error(f"Erro ao carregar dados do Bitrix24: {str(e)}")
        return pd.DataFrame()

def load_merged_data(category_id=None, date_from=None, date_to=None, deal_ids=None, debug=False, progress_bar=None, message_container=None):
    """
    Carrega e mescla dados das tabelas crm_deal e crm_deal_uf.
    
    Args:
        category_id (int, optional): ID da categoria para filtrar
        date_from (str, optional): Data inicial para filtro
        date_to (str, optional): Data final para filtro
        deal_ids (list, optional): Lista de IDs específicos a serem carregados
        debug (bool): Se deve mostrar informações de depuração
        progress_bar: Placeholder da barra de progresso (opcional)
        message_container: Placeholder da mensagem (opcional)
        
    Returns:
        pandas.DataFrame: DataFrame com os dados mesclados
    """
    global SHOW_DEBUG_INFO
    SHOW_DEBUG_INFO = debug
    
    # Atualizar progresso - Início
    if progress_bar:
        update_progress(progress_bar, 0.05, message_container, "Iniciando carregamento de dados...")
    
    if debug:
        st.write("### Carregando dados do Bitrix24")
        st.write(f"Categoria: {category_id}, Período: {date_from} a {date_to}")
        if deal_ids:
            st.write(f"IDs específicos: {deal_ids}")
    
    try:
        # Preparar os filtros
        filters = {"dimensionsFilters": [[]]}
        
        # Adicionar filtro de IDs se fornecido
        if deal_ids and len(deal_ids) > 0:
            filters["dimensionsFilters"][0].append({
                "fieldName": "ID", 
                "values": deal_ids, 
                "type": "INCLUDE", 
                "operator": "EQUALS"
            })
        # Se não tiver IDs específicos, usar categoria
        elif category_id:
            filters["dimensionsFilters"][0].append({
                "fieldName": "CATEGORY_ID", 
                "values": [category_id], 
                "type": "INCLUDE", 
                "operator": "EQUALS"
            })
        
        if date_from and date_to:
            filters["dimensionsFilters"][0].append({
                "fieldName": "UF_CRM_1741206763",  # Campo de data
                "values": [date_from, date_to],
                "type": "INCLUDE",
                "operator": "BETWEEN"
            })
        
        # Atualizar progresso - 10%
        if progress_bar:
            update_progress(progress_bar, 0.1, message_container, "Carregando tabela principal...")
        
        # Carregar dados principais
        if debug:
            st.subheader("Carregando tabela crm_deal")
        df_deal = load_bitrix_data(BITRIX_CRM_DEAL_URL, filters if filters["dimensionsFilters"][0] else None, show_logs=debug)
        
        # Atualizar progresso - 40%
        if progress_bar:
            update_progress(progress_bar, 0.4, message_container, "Processando dados principais...")
        
        # Se não conseguimos conectar, tentar uma abordagem simplificada
        if df_deal.empty:
            if debug:
                st.warning("Falha ao carregar dados com filtros. Tentando sem filtros...")
            df_deal = load_bitrix_data(BITRIX_CRM_DEAL_URL, show_logs=debug)
        
        # Verificar se temos dados
        if df_deal.empty:
            if debug:
                st.error("Não foi possível obter dados da tabela crm_deal")
            
            # Criar um dataframe sintético para fins de teste, se solicitado
            if debug and st.button("Criar dados de teste"):
                st.warning("Criando dados de teste para demonstração")
                df_deal = pd.DataFrame({
                    'ID': range(1, 11),
                    'TITLE': [f"Negócio {i}" for i in range(1, 11)],
                    'CATEGORY_ID': [32] * 10,
                    'ASSIGNED_BY_NAME': ["Responsável " + str(i % 3) for i in range(1, 11)],
                    'DATE_CREATE': [datetime.now().strftime("%Y-%m-%d")] * 10
                })
                st.write("Dados de teste criados com sucesso!")
            else:
                return pd.DataFrame()
            
        # Atualizar progresso - 50%
        if progress_bar:
            update_progress(progress_bar, 0.5, message_container, "Carregando tabela de campos personalizados...")
        
        # Preparar filtro para a tabela UF com base nos IDs encontrados
        if not df_deal.empty and 'ID' in df_deal.columns:
            # Obter IDs da tabela principal para filtrar a tabela UF
            if deal_ids is None or len(deal_ids) == 0:
                # Usar todos os IDs encontrados
                sample_ids = df_deal['ID'].astype(str).tolist()
                
                # Atualizar o filtro para usar todos os IDs encontrados
                deal_filter = {"dimensionsFilters": [[]]}
                deal_filter["dimensionsFilters"][0].append({
                    "fieldName": "DEAL_ID", 
                    "values": sample_ids, 
                    "type": "INCLUDE", 
                    "operator": "EQUALS"
                })
            else:
                # Se já temos IDs específicos, usar eles
                deal_filter = {"dimensionsFilters": [[]]}
                deal_filter["dimensionsFilters"][0].append({
                    "fieldName": "DEAL_ID", 
                    "values": [str(id) for id in deal_ids],  # Já está convertendo para string, o que é correto
                    "type": "INCLUDE", 
                    "operator": "EQUALS"
                })
        else:
            deal_filter = filters
        
        # Carregar dados personalizados com filtro otimizado
        if debug:
            st.subheader("Carregando tabela crm_deal_uf")
            st.write("Filtro para crm_deal_uf:", deal_filter)  # Debug adicional
        df_deal_uf = load_bitrix_data(BITRIX_CRM_DEAL_UF_URL, deal_filter, show_logs=debug)
        
        # Atualizar progresso - 70%
        if progress_bar:
            update_progress(progress_bar, 0.7, message_container, "Processando campos personalizados...")
        
        # Se não conseguimos conectar, tentar com o filtro original
        if df_deal_uf.empty and debug:
            st.warning("Falha ao carregar dados com filtro de IDs. Tentando com filtro original...")
            df_deal_uf = load_bitrix_data(BITRIX_CRM_DEAL_UF_URL, filters if filters["dimensionsFilters"][0] else None, show_logs=debug)
            
        # Verificar se temos dados
        if df_deal_uf.empty:
            if debug:
                st.error("Não foi possível obter dados da tabela crm_deal_uf")
            
            # Criar um dataframe sintético para fins de teste, se solicitado
            if debug and st.button("Criar dados UF de teste"):
                st.warning("Criando dados UF de teste para demonstração")
                df_deal_uf = pd.DataFrame({
                    'DEAL_ID': range(1, 11),
                    'UF_CRM_HIGILIZACAO_STATUS': ['COMPLETO', 'INCOMPLETO', 'PENDENCIA'] * 3 + ['COMPLETO'],
                    'UF_CRM_1741183785848': ['SIM', 'NÃO'] * 5,
                    'UF_CRM_1741183721969': ['SIM', 'NÃO'] * 5,
                    'UF_CRM_1741183685327': ['SIM', 'NÃO'] * 5,
                    'UF_CRM_1741183828129': ['SIM', 'NÃO'] * 5,
                    'UF_CRM_1741198696': ['SIM', 'NÃO'] * 5
                })
                st.write("Dados UF de teste criados com sucesso!")
            else:
                if not df_deal.empty:
                    if debug:
                        st.warning("Continuando apenas com dados básicos (sem campos personalizados)")
                    # Criar DataFrame UF vazio com as colunas necessárias
                    df_deal_uf = pd.DataFrame(columns=['DEAL_ID'] + list(get_higilizacao_fields().keys()))
                else:
                    return pd.DataFrame()
        
        # Atualizar progresso - 80%
        if progress_bar:
            update_progress(progress_bar, 0.8, message_container, "Verificando estrutura dos dados...")
        
        # Verificar se as colunas necessárias existem
        if 'ID' not in df_deal.columns:
            if debug:
                st.error("Coluna 'ID' não encontrada na tabela crm_deal")
            # Tentar criar a coluna ID se houver uma coluna similar
            if 'id' in df_deal.columns:
                if debug:
                    st.info("Encontrada coluna 'id' em minúsculas. Usando-a como 'ID'.")
                df_deal['ID'] = df_deal['id']
            elif 'ID_' in df_deal.columns:
                if debug:
                    st.info("Encontrada coluna 'ID_'. Usando-a como 'ID'.")
                df_deal['ID'] = df_deal['ID_']
            else:
                # Verificar se há alguma coluna que possa servir como ID
                id_column_found = False
                for col in df_deal.columns:
                    # Verificar se a coluna é uma string
                    if isinstance(col, str) and 'id' in col.lower():
                        if debug:
                            st.info(f"Usando coluna '{col}' como 'ID'.")
                        df_deal['ID'] = df_deal[col]
                        id_column_found = True
                        break
                
                if not id_column_found:
                    # Se não encontrou nenhuma coluna de ID, criar uma
                    if debug:
                        st.warning("Criando coluna 'ID' com valores sequenciais.")
                    df_deal['ID'] = range(1, len(df_deal) + 1)
            
        if 'DEAL_ID' not in df_deal_uf.columns:
            if debug:
                st.error("Coluna 'DEAL_ID' não encontrada na tabela crm_deal_uf")
            # Tentar criar a coluna DEAL_ID se houver uma coluna similar
            if 'deal_id' in df_deal_uf.columns:
                if debug:
                    st.info("Encontrada coluna 'deal_id' em minúsculas. Usando-a como 'DEAL_ID'.")
                df_deal_uf['DEAL_ID'] = df_deal_uf['deal_id']
            elif 'DEAL_ID_' in df_deal_uf.columns:
                if debug:
                    st.info("Encontrada coluna 'DEAL_ID_'. Usando-a como 'DEAL_ID'.")
                df_deal_uf['DEAL_ID'] = df_deal_uf['DEAL_ID_']
            else:
                # Verificar se há alguma coluna que possa servir como DEAL_ID
                deal_id_column_found = False
                for col in df_deal_uf.columns:
                    # Verificar se a coluna é uma string
                    if isinstance(col, str) and 'deal' in col.lower() and 'id' in col.lower():
                        if debug:
                            st.info(f"Usando coluna '{col}' como 'DEAL_ID'.")
                        df_deal_uf['DEAL_ID'] = df_deal_uf[col]
                        deal_id_column_found = True
                        break
                
                if not deal_id_column_found:
                    # Se não encontrou nenhuma coluna de DEAL_ID, usar o ID da tabela deal
                    if 'ID' in df_deal.columns:
                        if debug:
                            st.warning("Copiando valores da coluna 'ID' da tabela crm_deal para DEAL_ID na tabela crm_deal_uf.")
                        df_deal_uf['DEAL_ID'] = df_deal['ID'][:len(df_deal_uf)] if len(df_deal_uf) < len(df_deal) else df_deal['ID']
                    else:
                        # Se não encontrou nenhuma coluna de DEAL_ID, criar uma
                        if debug:
                            st.warning("Criando coluna 'DEAL_ID' com valores sequenciais.")
                        df_deal_uf['DEAL_ID'] = range(1, len(df_deal_uf) + 1)
        
        # Mostrar resumo dos dados antes de mesclar
        if debug:
            st.write(f"Tabela crm_deal: {len(df_deal)} registros")
            st.write(f"Tabela crm_deal_uf: {len(df_deal_uf)} registros")
            
            # Mostrar os primeiros registros para diagnóstico - SEM USAR EXPANDER
            st.write("### Primeiros registros das tabelas")
            st.write("crm_deal (primeiros 3 registros):")
            st.dataframe(df_deal.head(3))
            
            st.write("crm_deal_uf (primeiros 3 registros):")
            st.dataframe(df_deal_uf.head(3))
        
        # Atualizar progresso - 90%
        if progress_bar:
            update_progress(progress_bar, 0.9, message_container, "Mesclando dados...")
        
        # Mesclar os dados (ID de crm_deal = DEAL_ID de crm_deal_uf)
        if debug:
            st.info("Mesclando dados das duas tabelas...")
        
        # Preparar tipos de dados para mesclagem
        df_deal['ID'] = df_deal['ID'].astype(str)
        df_deal_uf['DEAL_ID'] = df_deal_uf['DEAL_ID'].astype(str)
        
        # Verificar se há campos de higienização nas tabelas
        higilizacao_fields = get_higilizacao_fields()
        missing_fields = []
        
        for field in higilizacao_fields.keys():
            if field not in df_deal.columns and field not in df_deal_uf.columns:
                missing_fields.append(field)
        
        if missing_fields and debug:
            st.warning(f"Os seguintes campos de higienização não foram encontrados: {missing_fields}")
            
            # Buscar campos similares usando correspondência parcial
            for field in missing_fields:
                field_found = False
                
                # Procurar na tabela df_deal_uf
                for col in df_deal_uf.columns:
                    if isinstance(col, str) and field.split('_')[-1] in col:
                        if debug:
                            st.info(f"Usando '{col}' como substituto para '{field}'")
                        df_deal_uf[field] = df_deal_uf[col]
                        field_found = True
                        break
                
                if not field_found and debug:
                    st.warning(f"Criando coluna vazia para '{field}'")
                    df_deal_uf[field] = None
        
        # Realizar a mesclagem
        merged_df = pd.merge(df_deal, df_deal_uf, left_on="ID", right_on="DEAL_ID", how="left")
        
        if debug:
            st.success(f"Dados mesclados com sucesso! {len(merged_df)} registros gerados.")
        
        # Garantir que temos as colunas necessárias
        for field in get_higilizacao_fields().keys():
            if field not in merged_df.columns:
                if debug:
                    st.warning(f"Coluna '{field}' não encontrada nos dados. Criando coluna vazia.")
                merged_df[field] = None
                
        # Verificar a coluna de responsável
        if 'ASSIGNED_BY_NAME' not in merged_df.columns:
            if debug:
                st.warning("Coluna 'ASSIGNED_BY_NAME' não encontrada. Usando 'ASSIGNED_BY' ou criando coluna.")
            if 'ASSIGNED_BY' in merged_df.columns:
                merged_df['ASSIGNED_BY_NAME'] = merged_df['ASSIGNED_BY']
            else:
                merged_df['ASSIGNED_BY_NAME'] = "Não atribuído"
        
        # Atualizar progresso - 100%
        if progress_bar:
            update_progress(progress_bar, 1.0, message_container, "Dados carregados com sucesso!")
            time.sleep(0.5)  # Pequena pausa para mostrar a conclusão
        
        return merged_df
        
    except Exception as e:
        if debug:
            st.error(f"Erro ao processar os dados: {str(e)}")
            st.exception(e)
        
        # Em caso de erro, atualizar progresso
        if progress_bar:
            update_progress(progress_bar, 1.0, message_container, "Erro ao carregar dados!")
            
        return pd.DataFrame()

def get_higilizacao_fields():
    """
    Retorna os campos relacionados à higienização de dados
    
    Returns:
        dict: Dicionário com os nomes dos campos e suas descrições
    """
    return {
        "UF_CRM_HIGILIZACAO_STATUS": "Status geral",
        "UF_CRM_1741183785848": "Documentação Pend/Infos",
        "UF_CRM_1741183721969": "Cadastro na Árvore Higielizado",
        "UF_CRM_1741183685327": "Estrutura Árvore Higieniza",
        "UF_CRM_1741183828129": "Requerimento",
        "UF_CRM_1741198696": "Emissões Brasileiras Bitrix24"
    }

def get_status_color(status):
    """
    Determina a cor CSS com base no status
    
    Args:
        status (str): Status da higienização
        
    Returns:
        str: Classe CSS para o status
    """
    if not status or pd.isna(status):
        return "status-pending"
    
    status = str(status).upper()
    
    if status in ["COMPLETO", "SIM"]:
        return "status-complete"
    elif status == "INCOMPLETO":
        return "status-incomplete"
    elif status == "PENDENCIA":
        return "status-pending"
    else:
        return "" 