import streamlit as st
import pandas as pd
from api.bitrix_connector import load_bitrix_data, get_credentials

CACHE_TTL_SECONDS = 3600

@st.cache_data(ttl=CACHE_TTL_SECONDS)
def carregar_dados_spa_scanner(force_reload: bool = False, debug: bool = False) -> pd.DataFrame:
    """
    Carrega dados da SPA de Scanner (ENTITY_TYPE_ID=1132) via Bitrix Biconnector.

    Retorna um DataFrame com, no mínimo, as colunas:
    - UF_CRM_48_ID_FAMILIA
    - UF_CRM_48_ID_REQUERENTE
    - UF_CRM_48_DOCUMENTO_SCANEADO
    - TITLE
    """
    token, base_url = get_credentials()
    if not token or not base_url:
        return pd.DataFrame()

    table_name = "crm_dynamic_items_1132"
    url = f"{base_url}/bitrix/tools/biconnector/pbi.php?token={token}&table={table_name}"

    if force_reload:
        try:
            carregar_dados_spa_scanner.clear()
        except Exception:
            pass

    df = load_bitrix_data(url, show_logs=debug, force_reload=force_reload)
    if df is None or df.empty:
        return pd.DataFrame()

    # Garantir colunas mínimas e tipos
    col_mins = [
        'UF_CRM_48_ID_FAMILIA',
        'UF_CRM_48_ID_REQUERENTE',
        'UF_CRM_48_DOCUMENTO_SCANEADO',
        'UF_CRM_48_LINK_DRIVE',
        'TITLE',
    ]
    for c in col_mins:
        if c not in df.columns:
            df[c] = None

    # Normalizações básicas
    df['UF_CRM_48_ID_FAMILIA'] = df['UF_CRM_48_ID_FAMILIA'].astype(str).str.strip()
    df['UF_CRM_48_ID_REQUERENTE'] = df['UF_CRM_48_ID_REQUERENTE'].astype(str).str.strip()
    df['UF_CRM_48_DOCUMENTO_SCANEADO'] = df['UF_CRM_48_DOCUMENTO_SCANEADO'].astype(str).str.strip()
    if 'UF_CRM_48_LINK_DRIVE' in df.columns:
        df['UF_CRM_48_LINK_DRIVE'] = df['UF_CRM_48_LINK_DRIVE'].astype(str).str.strip()
    df['TITLE'] = df['TITLE'].astype(str).str.strip()

    return df
