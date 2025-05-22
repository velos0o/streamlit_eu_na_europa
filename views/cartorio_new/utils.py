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
    mapeamento = {
        # SPA - Type ID 1098 STAGES
        'DT1098_92:NEW': 'AGUARDANDO CERTIDÃO',
        'DT1098_94:NEW': 'AGUARDANDO CERTIDÃO',
        'DT1098_92:UC_P6PYHW': 'PESQUISA - BR',
        'DT1098_94:UC_4YE2PI': 'PESQUISA - BR',
        'DT1098_92:PREPARATION': 'BUSCA - CRC',
        'DT1098_94:PREPARATION': 'BUSCA - CRC',
        'DT1098_92:UC_XBTHZ7': 'DEVOLUTIVA BUSCA - CRC',
        'DT1098_94:CLIENT': 'DEVOLUTIVA BUSCA - CRC', # Nota: CLIENT em Tatuapé é Devolutiva Busca CRC
        'DT1098_92:CLIENT': 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
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
    sucesso = [
        'CERTIDÃO ENTREGUE',
        'CERTIDÃO EMITIDA'
    ]
    falha = [
        'DEVOLUÇÃO ADM',
        'DEVOLVIDO REQUERIMENTO',
        'SOLICITAÇÃO DUPLICADA',
        'CANCELADO',
        'DEVOLUTIVA BUSCA - CRC',
        'CERTIDÃO DISPENSADA',
    ]
    if estagio_legivel in sucesso:
        return 'SUCESSO'
    elif estagio_legivel in falha:
        return 'FALHA'
    else:
        return 'EM ANDAMENTO' if estagio_legivel != "Desconhecido" else "DESCONHECIDO"

# --- Função para buscar dados do Supabase (movida de producao.py) ---
def fetch_supabase_producao_data(data_inicio_str, data_fim_str):
    """Busca dados da função RPC get_producao_adm_periodo no Supabase."""
    headers = {
        "apikey": st.secrets.supabase.anon_key,
        "Authorization": f"Bearer {st.secrets.supabase.service_key}",
        "Content-Type": "application/json"
    }
    params = {
        "data_inicio": data_inicio_str,
        "data_fim": data_fim_str
    }
    rpc_url = f"{st.secrets.supabase.url}/rest/v1/rpc/get_producao_adm_periodo"
    try:
        response = requests.post(rpc_url, headers=headers, json=params)
        response.raise_for_status()  # Levanta um erro para respostas HTTP 4xx/5xx
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Erro HTTP ao buscar dados do Supabase: {http_err} - {response.text}")
    except requests.exceptions.RequestException as req_err:
        st.error(f"Erro de requisição ao buscar dados do Supabase: {req_err}")
    except Exception as e:
        st.error(f"Erro inesperado ao processar dados do Supabase: {e}")
    return [] 

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