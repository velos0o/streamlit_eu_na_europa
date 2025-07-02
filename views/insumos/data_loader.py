import streamlit as st
import pandas as pd
import logging
import requests
import json
from io import StringIO

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=3600)
def get_bitrix_data():
    """
    Busca dados da tabela crm_dynamic_items_1118 do Bitrix24 via conector PBI.
    Processa a resposta JSON que o Bitrix retorna.
    """
    url = ""
    try:
        base_url = st.secrets["bitrix"]["BITRIX_URL"]
        token = st.secrets["bitrix"]["BITRIX_TOKEN"]
        table_name = "crm_dynamic_items_1118"
        
        url = f"{base_url}/bitrix/tools/biconnector/pbi.php?token={token}&table={table_name}"
        
        logger.info(f"Buscando dados de: {url}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Processar a resposta JSON
        try:
            data = response.json()
            if isinstance(data, list) and len(data) > 1 and isinstance(data[0], list):
                headers = data[0]
                rows_data = data[1:]
                df = pd.DataFrame(rows_data, columns=headers)
                logger.info(f"Dados de '{table_name}' carregados e processados com sucesso. Shape: {df.shape}")
            else:
                logger.warning("A resposta do Bitrix não está no formato esperado (lista de listas).")
                st.warning("A estrutura de dados recebida do Bitrix é inesperada.")
                st.json(data[:5]) # Mostra os 5 primeiros itens para depuração
                return pd.DataFrame()
        except json.JSONDecodeError:
            logger.error("Falha ao decodificar a resposta do Bitrix como JSON.")
            st.error("O Bitrix retornou uma resposta que não é um JSON válido.")
            st.code(f"Resposta do servidor (primeiros 500 caracteres):\n{response.text[:500]}", language="text")
            return pd.DataFrame()
        except Exception as parse_error:
            logger.error(f"Erro ao processar a resposta do Bitrix: {parse_error}")
            st.error("Ocorreu um erro ao processar os dados recebidos do Bitrix.")
            st.code(f"Resposta do servidor (primeiros 500 caracteres):\n{response.text[:500]}", language="text")
            return pd.DataFrame()

        if 'CATEGORY_ID' in df.columns:
            df['CATEGORY_ID'] = pd.to_numeric(df['CATEGORY_ID'], errors='coerce')
        
        return df

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Erro HTTP ao buscar dados do Bitrix: {http_err}")
        st.error(f"Falha na comunicação com o Bitrix (Erro HTTP {http_err.response.status_code}). Verifique a URL e o token de acesso em seus secrets.")
        st.code(f"URL: {url}\nResposta: {http_err.response.text[:500]}", language="text")
        return pd.DataFrame()
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Erro de conexão ao buscar dados do Bitrix: {req_err}")
        st.error(f"Não foi possível conectar ao servidor do Bitrix. Verifique sua conexão com a internet ou o status do servidor.")
        st.code(f"URL: {url}", language="text")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar ou processar dados do Bitrix: {e}")
        st.error("Falha inesperada ao carregar dados do Bitrix. Veja os detalhes abaixo.")
        st.code(f"URL: {url}\nTipo do Erro: {type(e).__name__}\nDetalhes: {e}", language="text")
        return pd.DataFrame()

def get_mapa_inicial_data():
    """Filtra dados para MAPA INICIAL (category_id 114)."""
    df = get_bitrix_data()
    if df.empty or 'CATEGORY_ID' not in df.columns:
        return pd.DataFrame()
    return df[df['CATEGORY_ID'] == 114].copy()

def get_fluxo_financeiro_data():
    """Filtra dados para FLUXO FINANCEIRO (category_id 116)."""
    df = get_bitrix_data()
    if df.empty or 'CATEGORY_ID' not in df.columns:
        return pd.DataFrame()
    return df[df['CATEGORY_ID'] == 116].copy()

def get_ia_data():
    """Filtra dados para IA (category_id 118)."""
    df = get_bitrix_data()
    if df.empty or 'CATEGORY_ID' not in df.columns:
        return pd.DataFrame()
    return df[df['CATEGORY_ID'] == 118].copy()

def get_criacao_adendo_data():
    """Filtra dados para CRIAÇÃO DE ADENDO (category_id 126)."""
    df = get_bitrix_data()
    if df.empty or 'CATEGORY_ID' not in df.columns:
        return pd.DataFrame()
    return df[df['CATEGORY_ID'] == 126].copy() 