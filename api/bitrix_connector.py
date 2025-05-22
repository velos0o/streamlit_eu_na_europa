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
    """
    token = None
    url = None
    try:
        # Verificar se estamos em ambiente Streamlit Cloud e se as chaves existem
        if hasattr(st, 'secrets') and st.secrets.get('bitrix') and st.secrets.bitrix.get('BITRIX_TOKEN') and st.secrets.bitrix.get('BITRIX_URL'):
            token = st.secrets.bitrix.BITRIX_TOKEN
            url = st.secrets.bitrix.BITRIX_URL
            # st.info("Credenciais do Bitrix carregadas via st.secrets (nível 'bitrix')") # Debug
        elif hasattr(st, 'secrets') and st.secrets.get('BITRIX_TOKEN') and st.secrets.get('BITRIX_URL'):
            # Fallback para chaves no nível raiz de st.secrets (menos comum, mas possível)
            token = st.secrets.BITRIX_TOKEN
            url = st.secrets.BITRIX_URL
            # st.info("Credenciais do Bitrix carregadas via st.secrets (nível raiz)") # Debug
        else:
            # Tentar variáveis de ambiente locais
            token = os.getenv('BITRIX_TOKEN')
            url = os.getenv('BITRIX_URL')
            # if token and url:
                # st.info("Credenciais do Bitrix carregadas via variáveis de ambiente") # Debug
            # else:
                # st.info("Nenhuma credencial do Bitrix encontrada em st.secrets ou variáveis de ambiente.") # Debug


    except Exception as e:
        # st.warning(f"Erro ao tentar acessar st.secrets para Bitrix: {e}. Tentando variáveis de ambiente.") # Debug
        # Em caso de erro com st.secrets (ex: não existe), tentar variáveis de ambiente
        token = os.getenv('BITRIX_TOKEN')
        url = os.getenv('BITRIX_URL')
        # if token and url:
            # st.info("Credenciais do Bitrix carregadas via variáveis de ambiente após exceção com st.secrets.") # Debug

    if not token or not url:
        st.error("CREDENCIAIS DO BITRIX24 NÃO ENCONTRADAS! Verifique o arquivo secrets.toml ou as variáveis de ambiente (BITRIX_TOKEN, BITRIX_URL).")
        # Poderia levantar uma exceção aqui se preferir interromper a execução:
        # raise ValueError("Credenciais do Bitrix24 não configuradas.")
        return None, None
    
    return token, url

# Obter credenciais
BITRIX_TOKEN, BITRIX_URL = get_credentials()

# URLs base para acesso às tabelas do Bitrix24
# Essas URLs serão construídas dinamicamente se BITRIX_TOKEN e BITRIX_URL forem None
# No entanto, com o st.error acima, o app deve alertar antes disso.

BITRIX_CRM_DEAL_URL = None
BITRIX_CRM_DEAL_UF_URL = None

if BITRIX_TOKEN and BITRIX_URL:
    BITRIX_CRM_DEAL_URL = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
    BITRIX_CRM_DEAL_UF_URL = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
else:
    # Este else pode não ser estritamente necessário se get_credentials() já mostra st.error
    # e potencialmente interrompe ou retorna None, fazendo com que chamadas subsequentes falhem de qualquer maneira.
    # Considerar como o resto do código lida com BITRIX_TOKEN/URL sendo None.
    st.warning("URLs do Bitrix não puderam ser construídas pois as credenciais não foram carregadas.")

# Variável de controle para logs de depuração
SHOW_DEBUG_INFO = False

# Função para carregar os dados do Bitrix com cache do Streamlit
@st.cache_data(ttl=3600)  # Cache válido por 1 hora
def load_bitrix_data(url, filters=None, show_logs=False, force_reload=False):
    """
    Carrega dados do Bitrix24 via API.
    
    Args:
        url (str): URL da API Bitrix24
        filters (dict, optional): Filtros para a consulta
        show_logs (bool): Se deve exibir logs de depuração
        force_reload (bool): Se deve ignorar o cache e forçar recarregamento
        
    Returns:
        pandas.DataFrame: DataFrame com os dados obtidos
    """
    # Se estiver forçando recarregamento, invalidar o cache para esta chamada
    if force_reload:
        load_bitrix_data.clear()
        if show_logs:
            st.info("Cache invalidado para forçar recarregamento")
    
    try:
        if show_logs:
            st.info(f"Tentando acessar: {url}")
            st.write(f"Filtros para {url}: {filters}") # Log dos filtros
        
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
                    if show_logs:
                        st.write(f"DEBUG: Status 200 OK para {url}.")
                        st.write(f"DEBUG: Primeiros 500 chars da resposta bruta (response.text): {response.text[:500]}")
                    try:
                        data = response.json()
                        if show_logs:
                            st.write(f"DEBUG: response.json() bem-sucedido. Tipo de 'data': {type(data)}")
                            if isinstance(data, list) and len(data) > 0:
                                st.write(f"DEBUG: 'data' é uma lista. Tamanho: {len(data)}. Tipo do primeiro item: {type(data[0])}")
                                st.write(f"DEBUG: Primeiro item de 'data' (data[0]): {str(data[0])[:500]}") # Mostrar amostra do primeiro item
                                if len(data) > 1:
                                    st.write(f"DEBUG: Segundo item de 'data' (data[1]): {str(data[1])[:500]}") # Mostrar amostra do segundo item
                            elif isinstance(data, dict):
                                st.write(f"DEBUG: 'data' é um dicionário. Chaves: {list(data.keys())}")
                                st.write(f"DEBUG: Amostra do dicionário 'data': {str(data)[:1000]}")
                            else:
                                st.write(f"DEBUG: 'data' não é lista nem dicionário. Conteúdo (amostra): {str(data)[:500]}")
                        
                        df = pd.DataFrame() # Inicializar df como DataFrame vazio
                        if data: # Se data não for None, [], {}, etc.
                            if isinstance(data, list):
                                if len(data) > 0:
                                    first_item = data[0]
                                    if isinstance(first_item, list): # Cabeçalhos na primeira linha
                                        if show_logs: st.write("DEBUG: Interpretando como lista de listas (cabeçalhos na primeira linha).")
                                        headers = data[0]
                                        rows_data = data[1:]
                                        # Garantir que todas as linhas tenham o mesmo número de colunas que os cabeçalhos
                                        # e preencher com None se faltar, para evitar erros no DataFrame
                                        processed_rows = []
                                        for r_idx, row_item in enumerate(rows_data):
                                            if len(row_item) < len(headers):
                                                # if show_logs: st.write(f"WARN: Linha {r_idx+1} tem {len(row_item)} colunas, cabeçalho tem {len(headers)}. Preenchendo com None.")
                                                processed_rows.append(list(row_item) + [None] * (len(headers) - len(row_item)))
                                            elif len(row_item) > len(headers):
                                                # if show_logs: st.write(f"WARN: Linha {r_idx+1} tem {len(row_item)} colunas, cabeçalho tem {len(headers)}. Truncando.")
                                                processed_rows.append(list(row_item)[:len(headers)])
                                            else:
                                                processed_rows.append(row_item)
                                        df = pd.DataFrame(processed_rows, columns=headers)
                                    elif isinstance(first_item, dict): # Lista de dicionários
                                        if show_logs: st.write("DEBUG: Interpretando como lista de dicionários.")
                                        df = pd.DataFrame(data)
                                    else: # Lista de outros tipos (improvável para API tabular)
                                        if show_logs: st.write("DEBUG: 'data' é uma lista, mas o primeiro item não é lista nem dict. Tentando pd.DataFrame(data).")
                                        try: df = pd.DataFrame(data)
                                        except Exception as e_df: 
                                            if show_logs: st.write(f"DEBUG: Falha ao criar DataFrame de lista de itens não-dict/list: {e_df}")
                                else: # Lista vazia
                                    if show_logs: st.write("DEBUG: 'data' é uma lista vazia. Criando DataFrame vazio.")
                                    # df já é um DataFrame vazio aqui
                            elif isinstance(data, dict): # Resposta é um único dicionário
                                # Pode ser um objeto de erro, ou um objeto único de dados
                                if 'error' in data or 'errors' in data: # Heurística para erro
                                     if show_logs: st.write(f"DEBUG: 'data' é um dicionário e parece ser um erro: {data}")
                                     df = pd.DataFrame([data]) # Transforma o erro em um DataFrame de 1 linha
                                else:
                                     if show_logs: st.write("DEBUG: Interpretando como dicionário único. Criando DataFrame de 1 linha.")
                                     df = pd.DataFrame([data])
                            else: # Nenhum dos formatos esperados
                                if show_logs: st.write(f"DEBUG: 'data' não é lista nem dicionário. Tentando pd.DataFrame([data]). Tipo: {type(data)}.")
                                try: df = pd.DataFrame([data]) # Tenta criar um df de 1 linha
                                except Exception as e_df_single:
                                    if show_logs: st.write(f"DEBUG: Falha ao criar DataFrame de item único não-dict/list: {e_df_single}")
                            
                            if show_logs and not df.empty:
                                st.write(f"DEBUG: DataFrame criado. Colunas: {df.columns.tolist()}")
                                st.write(f"DEBUG: Amostra do DataFrame (head(1)):\n{df.head(1)}")
                            elif show_logs and df.empty:
                                st.write("DEBUG: DataFrame resultante está vazio (após processamento de 'data').")
                                
                            # Log específico para crm_dynamic_items_1098 (repetido para garantir o ponto exato)
                            if "crm_dynamic_items_1098" in url and show_logs:
                                st.write(f"DEBUG_CREATE_DF (crm_dynamic_items_1098) Colunas: {df.columns.tolist() if not df.empty else 'Vazio'}")

                            return df # Retorna o DataFrame criado
                        else: # data é None, ou avalia para False (ex: {}, [])
                            if show_logs:
                                st.warning(f"DEBUG: A API retornou 'data' vazia ou nula para {url} na tentativa {attempt + 1}. Tipo de data: {type(data)}")
                            # df já é um DataFrame vazio, pode retornar ele ou continuar o loop
                            if attempt < max_attempts - 1:
                                time.sleep(2)
                            else:
                                return pd.DataFrame() # Retorna DF vazio se todas as tentativas resultarem em 'data' vazia
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

    # Adicionar o log aqui também, caso o fluxo não entre no try...except de requests.exceptions.RequestException
    # mas saia do loop de tentativas sem sucesso (embora o return pd.DataFrame() lá devesse cobrir)
    # Este if é mais para o caso de df ser definido mas vazio por algum motivo inesperado.
    if "crm_dynamic_items_1098" in url and show_logs and 'df' in locals():
        if df.empty :
            st.write(f"DEBUG FINAL (cartorio_new - crm_dynamic_items_1098) df para {url} está vazio antes do retorno final.")
    
    # Log genérico para outras tabelas se show_logs estiver ativo
    elif show_logs and 'df' in locals() and isinstance(df, pd.DataFrame): # Adicionado isinstance check
        st.write(f"DEBUG (geral) Colunas para {url.split('table=')[-1].split('&')[0] if 'table=' in url else url}:", df.columns.tolist() if not df.empty else "Vazio")
        if not df.empty:
            st.write(f"DEBUG (geral) Amostra (head(1)) para {url.split('table=')[-1].split('&')[0] if 'table=' in url else url}:", df.head(1))

    # Se o df existir e foi modificado no loop, ele é retornado. Se não, um DF vazio.
    if 'df' in locals() and isinstance(df, pd.DataFrame):
        return df
    else:
        # Garante que sempre retorna um DataFrame, mesmo que algo muito errado aconteça
        # e 'df' não seja definido como DataFrame.
        print(f"[WARN] load_bitrix_data: 'df' não é um DataFrame ou não foi definido. URL: {url}")
        return pd.DataFrame()

def load_merged_data(category_id=None, date_from=None, date_to=None, deal_ids=None, debug=False, progress_bar=None, message_container=None, force_reload=False):
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
        force_reload (bool): Se deve ignorar o cache e forçar recarregamento completo
        
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
        if force_reload:
            st.info("Modo de recarregamento forçado ativado - ignorando cache")
    
    try:
        # Preparar os filtros
        api_filters = None # Inicializa sem filtro de API
        local_filter_category_id = None # Para filtro local no Pandas

        # Se não tiver IDs específicos, usar categoria
        if not (deal_ids and len(deal_ids) > 0) and category_id:
            # Para crm_deal (onde category_id pode ser 46, 0, 32 etc.), aplicaremos o filtro localmente por enquanto.
            # Para outras tabelas ou se soubermos que o filtro de API funciona bem para crm_deal, poderíamos ajustar.
            if str(category_id) == '46': # Especificamente para Ficha da Família, carregar tudo de crm_deal e filtrar depois
                if debug: st.write(f"INFO (load_merged_data): Para category_id={category_id} (crm_deal), o filtro de categoria será aplicado localmente após o carregamento.")
                local_filter_category_id = str(category_id)
                # api_filters permanece None para carregar todos os deals
            else: # Para outras category_ids em crm_deal, ou outras tabelas, tentamos o filtro de API
                api_filters = {"dimensionsFilters": [[]]}
                api_filters["dimensionsFilters"][0].append({
                    "fieldName": "CATEGORY_ID", 
                    "values": [str(category_id)], 
                    "type": "INCLUDE", 
                    "operator": "EQUALS"
                })
        
        # Adicionar filtro de IDs se fornecido (este deve funcionar na API)
        if deal_ids and len(deal_ids) > 0:
            if api_filters is None: api_filters = {"dimensionsFilters": [[]]}
            # Garantir que não haja múltiplos filtros de ID se um já foi adicionado
            if not any(f.get("fieldName") == "ID" for f in api_filters["dimensionsFilters"][0]):
                 api_filters["dimensionsFilters"][0].append({
                    "fieldName": "ID", 
                    "values": deal_ids, 
                    "type": "INCLUDE", 
                    "operator": "EQUALS"
                })

        # Filtro de data (mantido como estava, pois parece ser um campo UF_CRM_ específico)
        if date_from and date_to:
            if api_filters is None: api_filters = {"dimensionsFilters": [[]]}
            api_filters["dimensionsFilters"][0].append({
                "fieldName": "UF_CRM_1741206763",
                "values": [date_from, date_to],
                "type": "INCLUDE",
                "operator": "BETWEEN"
            })
        
        if debug:
            st.subheader(f"Carregando tabela crm_deal (Categoria: {category_id})")
            st.write(f"Filtros de API para crm_deal: {api_filters}")
            st.write(f"Filtro local de categoria para crm_deal: {local_filter_category_id}")

        df_deal = load_bitrix_data(BITRIX_CRM_DEAL_URL, filters=api_filters, show_logs=debug, force_reload=force_reload)
        
        # Aplicar filtro local de CATEGORY_ID se necessário (após o carregamento)
        if local_filter_category_id and not df_deal.empty and 'CATEGORY_ID' in df_deal.columns:
            if debug: st.write(f"INFO: Aplicando filtro local para CATEGORY_ID = {local_filter_category_id} em df_deal.")
            # Certificar que a coluna CATEGORY_ID é string para a comparação, como nos filtros da API
            df_deal['CATEGORY_ID'] = df_deal['CATEGORY_ID'].astype(str)
            df_deal = df_deal[df_deal['CATEGORY_ID'] == local_filter_category_id]
            if debug: st.write(f"INFO: df_deal após filtro local: {len(df_deal)} linhas.")
        elif local_filter_category_id and ('CATEGORY_ID' not in df_deal.columns and not df_deal.empty):
            if debug: st.warning(f"WARN: Filtro local de CATEGORY_ID={local_filter_category_id} não aplicado pois a coluna 'CATEGORY_ID' não existe em df_deal.")
        
        if category_id == 46 and debug: 
            st.write("--- DEBUG FICHA FAMÍLIA (category_id 46) --- START --- ")
            st.write("Conteúdo de df_deal (imediatamente após load_bitrix_data):")
            st.write("Colunas df_deal:", df_deal.columns.tolist() if not df_deal.empty else "df_deal vazio")
            if not df_deal.empty:
                st.write("Tipos de dados df_deal (dtypes):", df_deal.dtypes)
                st.write("Amostra df_deal (head(3)):")
                st.dataframe(df_deal.head(3))
                # Verificar especificamente as colunas UF_CRM_ que esperamos
                cols_esperadas_ficha = ['ID', 'UF_CRM_1722883482527', 'UF_CRM_1722605592778']
                for col_chk in cols_esperadas_ficha:
                    if col_chk not in df_deal.columns:
                        st.write(f"ALERTA: Coluna esperada '{col_chk}' NÃO ENCONTRADA em df_deal para category_id 46.")
                    else:
                        st.write(f"INFO: Coluna esperada '{col_chk}' ENCONTRADA em df_deal.")
            st.write("--- DEBUG FICHA FAMÍLIA (df_deal) --- END ---")
        
        # Atualizar progresso - 40%
        if progress_bar:
            update_progress(progress_bar, 0.4, message_container, "Processando dados principais...")
        
        # Se não conseguimos conectar, tentar uma abordagem simplificada
        if df_deal.empty:
            if debug:
                st.warning("Falha ao carregar dados com filtros. Tentando sem filtros...")
            df_deal = load_bitrix_data(BITRIX_CRM_DEAL_URL, show_logs=debug, force_reload=force_reload)
        
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
            st.subheader(f"Carregando tabela crm_deal_uf (Categoria: {category_id})")
            # st.write("Filtro para crm_deal_uf:", deal_filter) # Já existia
        df_deal_uf = load_bitrix_data(BITRIX_CRM_DEAL_UF_URL, deal_filter, show_logs=debug, force_reload=force_reload)
        
        # Logs para df_deal_uf especificamente para category_id 46
        if category_id == 46 and debug:
            st.write("Conteúdo de df_deal_uf (antes de verificar se está vazio):")
            st.write("Colunas df_deal_uf:", df_deal_uf.columns.tolist() if not df_deal_uf.empty else "df_deal_uf vazio")
            if not df_deal_uf.empty:
                st.dataframe(df_deal_uf.head(3))
                cols_ficha_debug = ['UF_CRM_1722883482527', 'UF_CRM_1722605592778', 'DEAL_ID']
                for col_f_debug in cols_ficha_debug:
                    if col_f_debug not in df_deal_uf.columns:
                        st.write(f"DEBUG: Coluna {col_f_debug} AUSENTE em df_deal_uf")
                    else:
                        st.write(f"DEBUG: Amostra {col_f_debug} (em df_deal_uf):", df_deal_uf[[col_f_debug, 'DEAL_ID']].head(2) if 'DEAL_ID' in df_deal_uf.columns else df_deal_uf[[col_f_debug]].head(2))
            st.write("--- FIM DEBUG df_deal_uf ---")
        
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
        merged_df = pd.merge(df_deal, df_deal_uf, left_on="ID", right_on="DEAL_ID", how="left", suffixes=('_deal', '_deal_uf')) # Adicionado suffixes para evitar conflitos
        
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
        
        if category_id == 46 and debug:
            st.write("DEBUG (ficha_familia - category 46) Colunas de df_deal_uf ANTES do merge:", df_deal_uf.columns.tolist() if not df_deal_uf.empty else "df_deal_uf vazio")
            if not df_deal_uf.empty:
                cols_ficha_debug = ['UF_CRM_1722883482527', 'UF_CRM_1722605592778', 'DEAL_ID']
                for col_f_debug in cols_ficha_debug:
                    if col_f_debug not in df_deal_uf.columns:
                        st.write(f"DEBUG (ficha_familia - category 46) Coluna {col_f_debug} AUSENTE em df_deal_uf")
                    else:
                        st.write(f"DEBUG (ficha_familia - category 46) Amostra {col_f_debug} (primeiras 2):", df_deal_uf[[col_f_debug, 'DEAL_ID']].head(2) if 'DEAL_ID' in df_deal_uf.columns else df_deal_uf[[col_f_debug]].head(2))
        
        if category_id == 46 and debug:
            st.write("DEBUG (ficha_familia - category 46) Colunas de merged_df APÓS o merge:", merged_df.columns.tolist() if not merged_df.empty else "merged_df vazio")
            if not merged_df.empty:
                cols_ficha_debug_merged = ['UF_CRM_1722883482527', 'UF_CRM_1722605592778', 'ID']
                for col_f_debug_m in cols_ficha_debug_merged:
                    if col_f_debug_m not in merged_df.columns:
                        st.write(f"DEBUG (ficha_familia - category 46) Coluna {col_f_debug_m} AUSENTE em merged_df")
                    else:
                        st.write(f"DEBUG (ficha_familia - category 46) Amostra {col_f_debug_m} (em merged_df):", merged_df[[col_f_debug_m]].head(2))
            st.write("--- FIM DEBUG merged_df ---")
            
        # Adicionar um log final para merged_df especificamente para category_id 46
        if category_id == 46 and debug:
            st.write("--- DEBUG FICHA FAMÍLIA (merged_df) --- START ---")
            st.write("Conteúdo de merged_df (APÓS merge):")
            st.write("Colunas merged_df:", merged_df.columns.tolist() if not merged_df.empty else "merged_df vazio")
            if not merged_df.empty:
                st.dataframe(merged_df.head(3))
                # Verificar novamente as colunas UF_CRM_ após o merge
                cols_esperadas_merge = ['UF_CRM_1722883482527', 'UF_CRM_1722605592778']
                for col_chk_m in cols_esperadas_merge:
                    # O nome da coluna pode ter mudado por causa dos suffixes no merge,
                    # se elas também existissem em df_deal_uf. Por isso, checamos o original e com sufixo.
                    col_original_no_merge = col_chk_m in merged_df.columns
                    col_com_sufixo_deal_no_merge = f"{col_chk_m}_deal" in merged_df.columns
                    
                    if not col_original_no_merge and not col_com_sufixo_deal_no_merge:
                        st.write(f"ALERTA: Coluna '{col_chk_m}' (ou com sufixo _deal) NÃO ENCONTRADA em merged_df.")
                    elif col_original_no_merge:
                        st.write(f"INFO: Coluna '{col_chk_m}' ENCONTRADA em merged_df.")
                    elif col_com_sufixo_deal_no_merge:
                         st.write(f"INFO: Coluna '{col_chk_m}_deal' ENCONTRADA em merged_df (veio de df_deal).")
            st.write("--- DEBUG FICHA FAMÍLIA (merged_df) --- END ---")

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