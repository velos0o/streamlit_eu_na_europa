"""
Funções utilitárias para o módulo Ficha da Família
"""
import os
import re
from unidecode import unidecode

# Constantes
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets"))
LOGO_SVG_FILENAME = "LOGO-EU.NA.EUROPA-MAIO.24-COLORIDO-VERTICAL.svg"
LOGO_SVG_PATH = os.path.join(ASSETS_DIR, LOGO_SVG_FILENAME)
LOGO_PNG_FILENAME = "logo em png.png"
LOGO_PNG_PATH = os.path.join(ASSETS_DIR, LOGO_PNG_FILENAME)

BASE_URL_DEAL = "https://eunaeuropacidadania.bitrix24.com.br/crm/deal/details/"
BASE_URL_TYPE_1098 = "https://eunaeuropacidadania.bitrix24.com.br/crm/type/1098/details/"

_SLUG_CLEAN_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _slugify(text: str) -> str:
    """Converte texto em slug seguro para nome de arquivo"""
    base = unidecode(str(text or "")).lower()
    base = _SLUG_CLEAN_RE.sub("_", base)
    base = re.sub("_+", "_", base)
    return base.strip("_")


def montar_nome_arquivo_pdf(nome_familia: str, id_familia: str) -> str:
    """Monta nome de arquivo PDF baseado em nome e ID da família"""
    partes = []
    slug_nome = _slugify(nome_familia)
    slug_id = _slugify(id_familia)
    if slug_nome:
        partes.append(slug_nome)
    if slug_id:
        partes.append(slug_id)
    base = "_".join(partes) if partes else "ficha_familia"
    return f"{base}.pdf"


def obter_url_card(familia_serie, tipo: str) -> str | None:
    """Constroi URLs para cards do Bitrix com base nos campos presentes"""
    if tipo == "pasta_pronta":
        custom_link = familia_serie.get('UF_CRM_48_LINK_PASTA_PRONTA') or familia_serie.get('UF_CRM_LINK_PASTA_PRONTA')
        if custom_link and str(custom_link).strip().lower().startswith('http'):
            return str(custom_link).strip()
        deal_id = familia_serie.get('ID') or familia_serie.get('ID_DEAL')
        if deal_id:
            return f"{BASE_URL_DEAL}{str(deal_id).strip().rstrip('/')}/"
        return None

    if tipo == "emissao_brasileira":
        custom_link = familia_serie.get('UF_CRM_48_LINK_EMISSAO_BRASILEIRA') or familia_serie.get('UF_CRM_LINK_EMISSAO_BRASILEIRA')
        if custom_link and str(custom_link).strip().lower().startswith('http'):
            return str(custom_link).strip()
        id_pipeline = familia_serie.get('UF_CRM_48_ID_EMISSAO_BR') or familia_serie.get('UF_CRM_1722605592778') or familia_serie.get('UF_CRM_ID_FAMILIA')
        if id_pipeline:
            id_str = str(id_pipeline).strip().rstrip('/')
            if id_str:
                return f"{BASE_URL_TYPE_1098}{id_str}/"
        return None

    return None


def construir_link_card_pipeline(row) -> str | None:
    """Monta o link direto para o card Bitrix da linha informada.
    
    Pipelines de Emissão Brasileira (usam /crm/type/1098/details/):
    - 92: Casa Verde
    - 94: Tatuapé  
    - 102: Paróquia
    - 104: Pesquisa BR
    
    Outros pipelines usam /crm/deal/details/
    """
    categoria = str(row.get('CATEGORY_ID', '') or '').strip()
    candidatos_id = [
        row.get('ID'),
        row.get('UF_CRM_34_ID_NEGOCIO'),
        row.get('UF_CRM_34_ID_CERTIDAO'),
        row.get('UF_CRM_48_ID_CARD'),
    ]
    card_id = None
    for candidato in candidatos_id:
        if candidato is None:
            continue
        candidato_str = str(candidato).strip()
        if candidato_str and candidato_str.lower() not in {'nan', 'none', 'n/d'}:
            card_id = candidato_str.rstrip('/')
            break

    if not card_id or not card_id.replace(' ', '').isdigit():
        return None

    # Pipelines de emissão brasileira
    if categoria in {'92', '94', '102', '104', '1098'}:
        return f"{BASE_URL_TYPE_1098}{card_id}/"
    return f"{BASE_URL_DEAL}{card_id}/"


def load_page_specific_css(file_path):
    """Carrega CSS específico da página"""
    import streamlit as st
    try:
        with open(file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo CSS não encontrado: {file_path}")


