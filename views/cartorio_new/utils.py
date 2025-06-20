import pandas as pd
import streamlit as st # Adicionado para st.error
import requests # Adicionado para chamadas HTTP
from api.bitrix_connector import get_credentials, load_bitrix_data # IMPORTANTE: Adicionar esta importação

# --- Configurações do Supabase (copiadas de producao.py) ---
# Idealmente, viriam de st.secrets ou variáveis de ambiente no uso real.

def simplificar_nome_estagio(nome):
    """ Simplifica o nome do estágio para exibição. """
    if pd.isna(nome):
        return "Desconhecido"

    codigo_estagio = str(nome) # Garante que é string

    # Mapeamento Atualizado com base na descrição do usuário e categorias
    # Simplificando nomes para serem mais curtos nos cards
    # ATUALIZADO: Incluindo os novos pipelines 102 (Paróquia) e 104 (Pesquisa BR)
    mapeamento = {
        # === SPA - Type ID 1098 STAGES (Pipelines 92 e 94) ===
        'DT1098_92:NEW': 'AGUARDANDO CERTIDÃO',
        'DT1098_94:NEW': 'AGUARDANDO CERTIDÃO',
        'DT1098_92:UC_P6PYHW': 'PESQUISA - BR',
        'DT1098_94:UC_4YE2PI': 'PESQUISA - BR',
        'DT1098_92:PREPARATION': 'BUSCA - CRC',
        'DT1098_94:PREPARATION': 'BUSCA - CRC',
        'DT1098_92:UC_XBTHZ7': 'DEVOLUTIVA BUSCA - CRC',
        'DT1098_94:CLIENT': 'DEVOLUTIVA BUSCA - CRC', # Nota: CLIENT em Tatuapé é Devolutiva Busca CRC
        'DT1098_92:CLIENT': 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
        'DT1098_92:UC_I61XLW': 'AGUARDANDO DECISÃO CLIENTE',
        'DT1098_94:UC_IQ4WFA': 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
        'DT1098_92:UC_ZWO7BI': 'MONTAGEM REQUERIMENTO CARTÓRIO',
        'DT1098_94:UC_UZHXWF': 'MONTAGEM REQUERIMENTO CARTÓRIO',
        'DT1098_92:UC_83ZGKS': 'SOLICITAR CARTÓRIO DE ORIGEM',
        'DT1098_94:UC_DH38EI': 'SOLICITAR CARTÓRIO DE ORIGEM',
        'DT1098_92:UC_6TECYL': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'DT1098_94:UC_X9UE60': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'DT1098_92:UC_MUJP1P': 'AGUARDANDO CARTÓRIO ORIGEM',
        'DT1098_94:UC_IXCAA5': 'AGUARDANDO CARTÓRIO ORIGEM',
        'DT1098_92:UC_EYBGVD': 'DEVOLUÇÃO ADM',
        'DT1098_94:UC_VS8YKI': 'DEVOLUÇÃO ADM',
        'DT1098_92:UC_KC335Q': 'DEVOLVIDO REQUERIMENTO',
        'DT1098_94:UC_M6A09E': 'DEVOLVIDO REQUERIMENTO',
        'DT1098_92:UC_5LWUTX': 'CERTIDÃO EMITIDA',
        'DT1098_94:UC_K4JS04': 'CERTIDÃO EMITIDA',
        'DT1098_92:FAIL': 'SOLICITAÇÃO DUPLICADA',
        'DT1098_94:FAIL': 'SOLICITAÇÃO DUPLICADA',
        'DT1098_92:UC_Z24IF7': 'CANCELADO',
        'DT1098_94:UC_MGTPX0': 'CANCELADO',
        'DT1098_92:SUCCESS': 'CERTIDÃO ENTREGUE',
        'DT1098_94:SUCCESS': 'CERTIDÃO ENTREGUE',
        'DT1098_92:UC_U10R0R': 'CERTIDÃO DISPENSADA',
        'DT1098_94:UC_L3JFKO': 'CERTIDÃO DISPENSADA',
        
        # === Pipeline 102 (Paróquia) ===
        'DT1098_102:NEW': 'SOLICITAR PARÓQUIA DE ORIGEM',
        'DT1098_102:PREPARATION': 'AGUARDANDO PARÓQUIA DE ORIGEM',
        'DT1098_102:CLIENT': 'CERTIDÃO EMITIDA',
        'DT1098_102:UC_45SBLC': 'DEVOLUÇÃO ADM',
        'DT1098_102:SUCCESS': 'CERTIDÃO ENTREGUE',
        'DT1098_102:FAIL': 'CANCELADO',
        'DT1098_102:UC_676WIG': 'CERTIDÃO DISPENSADA',
        'DT1098_102:UC_UHPXE8': 'CERTIDÃO ENTREGUE',
        
        # === Pipeline 104 (Pesquisa BR) ===
        'DT1098_104:NEW': 'AGUARDANDO PESQUISADOR',
        'DT1098_104:PREPARATION': 'PESQUISA EM ANDAMENTO',
        'DT1098_104:SUCCESS': 'PESQUISA PRONTA PARA EMISSÃO',
        'DT1098_104:FAIL': 'PESQUISA NÃO ENCONTRADA',
        
        # Manter mapeamentos genéricos caso algum STAGE_ID venha sem prefixo DT1098_XX:
        'NEW': 'AGUARDANDO CERTIDÃO', 
        'UC_P6PYHW': 'PESQUISA - BR', 
        'UC_4YE2PI': 'PESQUISA - BR', 
        'PREPARATION': 'BUSCA - CRC',
        'UC_XBTHZ7': 'DEVOLUTIVA BUSCA - CRC',
        'UC_IQ4WFA': 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
        'UC_ZWO7BI': 'MONTAGEM REQUERIMENTO CARTÓRIO',
        'UC_UZHXWF': 'MONTAGEM REQUERIMENTO CARTÓRIO',
        'UC_83ZGKS': 'SOLICITAR CARTÓRIO DE ORIGEM',
        'UC_DH38EI': 'SOLICITAR CARTÓRIO DE ORIGEM',
        'UC_6TECYL': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'UC_X9UE60': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'UC_MUJP1P': 'AGUARDANDO CARTÓRIO ORIGEM',
        'UC_IXCAA5': 'AGUARDANDO CARTÓRIO ORIGEM',
        'UC_EYBGVD': 'DEVOLUÇÃO ADM',
        'UC_VS8YKI': 'DEVOLUÇÃO ADM',
        'UC_KC335Q': 'DEVOLVIDO REQUERIMENTO',
        'UC_M6A09E': 'DEVOLVIDO REQUERIMENTO',
        'UC_5LWUTX': 'CERTIDÃO EMITIDA',
        'UC_K4JS04': 'CERTIDÃO EMITIDA',
        'FAIL': 'SOLICITAÇÃO DUPLICADA',
        'UC_Z24IF7': 'CANCELADO',
        'UC_MGTPX0': 'CANCELADO',
        'SUCCESS': 'CERTIDÃO ENTREGUE',
        'UC_U10R0R': 'CERTIDÃO DISPENSADA',
        'UC_L3JFKO': 'CERTIDÃO DISPENSADA',
        
        # Genéricos para novos pipelines
        'UC_45SBLC': 'DEVOLUÇÃO ADM',
        'UC_676WIG': 'CERTIDÃO DISPENSADA',
        'UC_UHPXE8': 'CERTIDÃO ENTREGUE',
    }

    nome_legivel = mapeamento.get(codigo_estagio)
    if nome_legivel is None and ':' in codigo_estagio:
        apenas_codigo = codigo_estagio.split(':')[-1]
        nome_legivel = mapeamento.get(apenas_codigo)
    if nome_legivel is None:
        return codigo_estagio.split(':')[-1] if ':' in codigo_estagio else codigo_estagio if codigo_estagio else "Desconhecido"
    return nome_legivel

def categorizar_estagio(estagio_legivel):
    """ Categoriza o estágio simplificado em SUCESSO, EM ANDAMENTO ou FALHA. """
    # ATUALIZADO: Incluindo os novos estágios dos pipelines 102 (Paróquia) e 104 (Pesquisa BR)
    sucesso = [
        'CERTIDÃO ENTREGUE',
        'CERTIDÃO EMITIDA',
        'PESQUISA PRONTA PARA EMISSÃO'  # Novo: Pipeline 104
    ]
    falha = [
        'DEVOLUÇÃO ADM',
        'DEVOLVIDO REQUERIMENTO',
        'SOLICITAÇÃO DUPLICADA',
        'CANCELADO',
        'DEVOLUTIVA BUSCA - CRC',
        'CERTIDÃO DISPENSADA',
        'PESQUISA NÃO ENCONTRADA'  # Novo: Pipeline 104
    ]
    if estagio_legivel in sucesso:
        return 'SUCESSO'
    elif estagio_legivel in falha:
        return 'FALHA'
    else:
        return 'EM ANDAMENTO' if estagio_legivel != "Desconhecido" else "DESCONHECIDO"

# --- Função para buscar dados do Supabase (movida de producao.py) ---
def fetch_supabase_producao_data(data_inicio_str, data_fim_str):
    """Busca dados da função RPC get_producao_time_doutora_periodo no Supabase."""
    try:
        # Verificar se as credenciais do Supabase estão configuradas
        if not hasattr(st.secrets, 'supabase'):
            st.warning("Credenciais do Supabase não configuradas. Usando dados de demonstração.")
            return criar_dados_supabase_demo(data_inicio_str, data_fim_str)
        
        headers = {
            "apikey": st.secrets.supabase.anon_key,
            "Authorization": f"Bearer {st.secrets.supabase.service_key}",
            "Content-Type": "application/json",
            "Prefer": "count=exact", 
            "Range-Unit": "items", # Especifica a unidade do range
            "Range": "0-"  # Tenta requisitar do índice 0 até o final
        }
        params = {
            "p_data_inicio": data_inicio_str, # Parâmetro p_data_inicio
            "p_data_fim": data_fim_str      # Parâmetro p_data_fim
        }
        
        print(f"--- DEBUG: Parâmetros enviados para RPC get_producao_time_doutora_periodo: {params} ---")
        
        rpc_url = f"{st.secrets.supabase.url}/rest/v1/rpc/get_producao_time_doutora_periodo"
        
        # Fazer a consulta normal com o período solicitado
        response = requests.post(rpc_url, headers=headers, json=params)
        response.raise_for_status()  # Levanta um erro para respostas HTTP 4xx/5xx

        print(f"--- DEBUG: Resposta HTTP STATUS CODE: {response.status_code} ---")
        print("--- DEBUG: Resposta HTTP HEADERS ---")
        print(response.headers)
        
        response_text_for_log = response.text
        if len(response_text_for_log) > 3000: # Limitar o log se for muito grande
            print(response_text_for_log[:1500] + "... (resposta truncada) ..." + response_text_for_log[-1500:])
        else:
            print(response_text_for_log)

        data = response.json()
        
        print("--- DEBUG: Dados crus da RPC Supabase (get_producao_time_doutora_periodo) ---")
        if isinstance(data, list) and len(data) > 0:
            print(f"Total de registros recebidos: {len(data)}")
            print(f"Primeiro registro recebido: {data[0]}")
            if isinstance(data[0], dict):
                print(f"Chaves no primeiro registro: {list(data[0].keys())}")
            else:
                print("Primeiro registro não é um dicionário.")
        elif isinstance(data, list):
            print("RPC retornou uma lista vazia.")
            st.warning("Nenhum dado encontrado no Supabase para o período especificado.")
            return pd.DataFrame()
        else:
            print(f"RPC retornou dados que não são uma lista: {type(data)}")
            st.error(f"Resposta inesperada da API Supabase: {type(data)}")
            return pd.DataFrame()
        
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            
            print("--- DEBUG: Colunas do DataFrame ANTES do rename ---")
            print(df.columns.tolist())
            if not df.empty:
                print(f"Primeiro registro do DataFrame ANTES do rename:\n{df.head(1)}")
            
            # Renomear colunas para corresponder ao esperado pelo Python
            colunas_rename_map = {
                "timestamp": "data_criacao", 
                "card_id": "id_card",
                "calculated_previous_stage_id": "previous_stage_id",
                # Se stage_id vier com nome diferente, mapear aqui
                "stage_id": "estagio_id",  # Garantir que seja mapeado para estagio_id
            }
            
            # Aplicar rename apenas para colunas que existem
            colunas_para_renomear = {k: v for k, v in colunas_rename_map.items() if k in df.columns}
            if colunas_para_renomear:
                df.rename(columns=colunas_para_renomear, inplace=True)
                print(f"--- DEBUG: Colunas renomeadas: {colunas_para_renomear} ---")
            
            print("--- DEBUG: Colunas do DataFrame DEPOIS do rename ---")
            print(df.columns.tolist())
            if not df.empty:
                print(f"Primeiro registro do DataFrame DEPOIS do rename:\n{df.head(1)}")
                
            # Verificar se as colunas essenciais estão presentes
            colunas_essenciais = ['data_criacao', 'id_card', 'estagio_id', 'movido_por_id']
            colunas_faltando = [col for col in colunas_essenciais if col not in df.columns]
            
            if colunas_faltando:
                st.warning(f"Colunas essenciais não encontradas nos dados do Supabase: {colunas_faltando}. Colunas disponíveis: {df.columns.tolist()}")
                # Criar colunas faltando com valores padrão
                for col in colunas_faltando:
                    df[col] = None
                    
            return df
        else:
            st.warning("Nenhum dado válido retornado do Supabase.")
            return pd.DataFrame()
            
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"Erro HTTP ao buscar dados do Supabase: {http_err}"
        if 'response' in locals():
            error_msg += f" - {response.text}"
        st.error(error_msg)
        print(f"--- DEBUG HTTP ERROR: {error_msg} ---")
        # Usar dados de demonstração em caso de erro
        return criar_dados_supabase_demo(data_inicio_str, data_fim_str)
    except requests.exceptions.RequestException as req_err:
        error_msg = f"Erro de requisição ao buscar dados do Supabase: {req_err}"
        st.error(error_msg)
        print(f"--- DEBUG REQUEST ERROR: {error_msg} ---")
        # Usar dados de demonstração em caso de erro
        return criar_dados_supabase_demo(data_inicio_str, data_fim_str)
    except Exception as e:
        error_msg = f"Erro inesperado ao processar dados do Supabase: {e}"
        st.error(error_msg)
        print(f"--- DEBUG UNEXPECTED ERROR: {error_msg} ---")
        # Usar dados de demonstração em caso de erro
        return criar_dados_supabase_demo(data_inicio_str, data_fim_str)
    
    return pd.DataFrame() # Garante que um DataFrame vazio seja retornado em caso de erro

def criar_dados_supabase_demo(data_inicio_str, data_fim_str):
    """Cria dados de demonstração para quando o Supabase não está disponível."""
    print("--- DEBUG: Criando dados de demonstração do Supabase ---")
    
    # Gerar algumas datas de exemplo no período
    data_inicio = pd.to_datetime(data_inicio_str)
    data_fim = pd.to_datetime(data_fim_str)
    
    # Criar alguns registros de exemplo
    dados_demo = []
    for i in range(10):  # 10 registros de exemplo
        data_exemplo = data_inicio + pd.Timedelta(days=i % ((data_fim - data_inicio).days + 1))
        dados_demo.append({
            'id': i + 1,
            'data_criacao': data_exemplo.strftime('%Y-%m-%d %H:%M:%S'),
            'id_card': f'DEMO_{1000 + i}',
            'previous_stage_id': 'DT1098_92:UC_ZWO7BI',
            'estagio_id': 'DT1098_92:UC_83ZGKS',
            'movido_por_id': f'user_{284 + (i % 3)}',  # Simular alguns usuários ADM
            'id_familia': f'FAM_{100 + i}',
            'id_requerente': f'REQ_{200 + i}'
        })
    
    df_demo = pd.DataFrame(dados_demo)
    st.info("🚧 Usando dados de demonstração do Supabase. Configure as credenciais para dados reais.")
    
    return df_demo

# --- Função para Carregar Usuários do Bitrix ---
@st.cache_data(ttl=3600) # Cache por 1 hora
def carregar_dados_usuarios_bitrix():
    """Carrega dados da tabela b_user do Bitrix24."""
    print("[CACHE MISS] Carregando dados da tabela de usuários do Bitrix.")
    
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    table_name = "user"
    url = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table={table_name}"
    df_users = load_bitrix_data(url, filters=None)

    if df_users is None or df_users.empty or 'error' in df_users.columns:
        st.warning(f"Não foi possível carregar os dados dos usuários (tabela '{table_name}'). Nomes de responsáveis podem não ser exibidos. Verifique o nome da tabela no Biconnector.")
        if df_users is not None and 'error' in df_users.columns:
            st.error(f"API Bitrix retornou erro para tabela '{table_name}': {df_users['error'].iloc[0] if not df_users.empty else 'Erro desconhecido'}")
        return pd.DataFrame()
    
    colunas_usuarios = ['ID', 'NAME', 'LAST_NAME'] 
    colunas_presentes = [col for col in colunas_usuarios if col in df_users.columns]
    
    if 'ID' not in colunas_presentes:
        st.error(f"Coluna 'ID' não encontrada na tabela {table_name}. Mapeamento de nomes de usuário falhará. Colunas encontradas: {df_users.columns.tolist()}")
        return pd.DataFrame()
        
    df_users_selecionados = df_users[colunas_presentes].copy()
    df_users_selecionados['ID'] = pd.to_numeric(df_users_selecionados['ID'], errors='coerce').dropna()
    df_users_selecionados['ID'] = df_users_selecionados['ID'].astype(int)
    
    if 'NAME' in df_users_selecionados.columns and 'LAST_NAME' in df_users_selecionados.columns:
        df_users_selecionados['FULL_NAME'] = df_users_selecionados['NAME'].fillna('') + ' ' + df_users_selecionados['LAST_NAME'].fillna('')
        df_users_selecionados['FULL_NAME'] = df_users_selecionados['FULL_NAME'].str.strip()
    elif 'NAME' in df_users_selecionados.columns:
        df_users_selecionados['FULL_NAME'] = df_users_selecionados['NAME'].fillna('').str.strip()
    else:
        df_users_selecionados['FULL_NAME'] = 'Nome Desconhecido'
    
    df_users_selecionados.loc[df_users_selecionados['FULL_NAME'] == '', 'FULL_NAME'] = 'ID: ' + df_users_selecionados['ID'].astype(str)

    return df_users_selecionados[['ID', 'FULL_NAME']]

# Remover o stub de load_data_cached se ele não for usado por outras funções em utils.py
# if 'load_data_cached' not in globals():
#     print("WARN: load_data_cached não definida globalmente em utils.py. Definindo stub.")
#     def load_data_cached(table_name: str, filters: dict | None = None):
#         # ... (código do stub) ...
#         return pd.DataFrame() 