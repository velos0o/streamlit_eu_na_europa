"""
FICHA DA FAMÍLIA - Relatório Individual de Famílias
===================================================

ATUALIZAÇÃO - NOVOS PIPELINES 102 E 104:
- Pipeline 102: Paróquia 
- Pipeline 104: Pesquisa BR

Alterações realizadas:
1. Nova função load_cartorio_data_all_pipelines() para carregar dados dos pipelines 92, 94, 102 e 104
2. Atualização da função simplificar_nome_estagio() em utils.py para incluir mapeamentos dos novos estágios
3. Atualização do map_stage_to_relatorio com categorias dos novos pipelines
4. Ampliação do resumo_status_categorias_temp para incluir as novas categorias
5. Suporte ao novo campo NOME_PIPELINE para identificação do pipeline de origem

Novos Estágios Mapeados:
Pipeline 102 (Paróquia):
- DT1098_102:NEW → SOLICITAR PARÓQUIA DE ORIGEM
- DT1098_102:PREPARATION → AGUARDANDO PARÓQUIA DE ORIGEM  
- DT1098_102:CLIENT → CERTIDÃO EMITIDA
- DT1098_102:UC_45SBLC → DEVOLUÇÃO ADM
- DT1098_102:SUCCESS → CERTIDÃO ENTREGUE
- DT1098_102:FAIL → CANCELADO
- DT1098_102:UC_676WIG → CERTIDÃO DISPENSADA
- DT1098_102:UC_UHPXE8 → CERTIDÃO ENTREGUE

Pipeline 104 (Pesquisa BR):
- DT1098_104:NEW → AGUARDANDO PESQUISADOR
- DT1098_104:PREPARATION → PESQUISA EM ANDAMENTO
- DT1098_104:SUCCESS → PESQUISA PRONTA PARA EMISSÃO
- DT1098_104:FAIL → PESQUISA NÃO ENCONTRADA

LÓGICA DE PRECEDÊNCIA PIPELINE 104:
Quando uma pessoa tem "PESQUISA PRONTA PARA EMISSÃO" no pipeline 104 e também possui
registros nos pipelines superiores (92, 94, 102), o sistema mostra apenas o status 
dos pipelines superiores, pois após a pesquisa estar pronta, o card é duplicado 
para os outros pipelines onde o processo continua.

LÓGICA DE "Pasta C/Emissão Concluída":
Esta é uma MÉTRICA DERIVADA, não um status direto. É calculada quando TODAS as 
certidões ativas de uma família estão no status "Brasileiras Emitida". 
Baseada na mesma lógica do higienizacao_desempenho.py.
"""

from functools import lru_cache
from io import BytesIO

import streamlit as st
# importยอด_เยี่ยม_navigation_utils # Comentado por enquanto
import pandas as pd # Adicionado para manipulação de dados
import os # Adicionado para manipulação de caminhos
import re
from datetime import datetime

import time
import html


try:
    import cairosvg
except (ImportError, OSError):  # pragma: no cover - dependência opcional ou sem libcairo instalado
    cairosvg = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ImportError:  # pragma: no cover - dependência opcional
    SimpleDocTemplate = None

# Importar a função central de carregamento do Bitrix
from api.bitrix_connector import load_merged_data
from utils.dataframe_utils import ensure_pandas_df
from unidecode import unidecode

# Nota: Imports de views.* movidos para dentro das funções para evitar importação circular


BASE_URL_DEAL = "https://eunaeuropacidadania.bitrix24.com.br/crm/deal/details/"
BASE_URL_TYPE_1098 = "https://eunaeuropacidadania.bitrix24.com.br/crm/type/1098/details/"

# Configurações e utilitários para geração de PDF
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets"))
LOGO_SVG_FILENAME = "LOGO-EU.NA.EUROPA-MAIO.24-COLORIDO-VERTICAL.svg"
LOGO_SVG_PATH = os.path.join(ASSETS_DIR, LOGO_SVG_FILENAME)
LOGO_PNG_FILENAME = "logo em png.png"
LOGO_PNG_PATH = os.path.join(ASSETS_DIR, LOGO_PNG_FILENAME)
_SLUG_CLEAN_RE = re.compile(r"[^a-zA-Z0-9_-]+")


@lru_cache(maxsize=1)
def _load_logo_image_bytes():
    """Obtém bytes do logo em PNG. Usa arquivo pronto e, se necessário, converte o SVG."""
    if os.path.exists(LOGO_PNG_PATH):
        try:
            with open(LOGO_PNG_PATH, "rb") as png_file:
                return png_file.read()
        except Exception as exc:  # pragma: no cover - log auxiliar
            print(f"[WARN] Falha ao carregar logo PNG: {exc}")

    if cairosvg is None:
        return None
    if not os.path.exists(LOGO_SVG_PATH):
        print(f"[WARN] Logo SVG não encontrado em {LOGO_SVG_PATH}")
        return None
    try:
        with open(LOGO_SVG_PATH, "rb") as svg_file:
            svg_data = svg_file.read()
        return cairosvg.svg2png(bytestring=svg_data)
    except Exception as exc:  # pragma: no cover - log auxiliar
        print(f"[WARN] Falha ao converter logo SVG para PNG: {exc}")
        return None


def _create_logo_flowable(max_height_mm: float = 28):
    """Cria o flowable do logo para o PDF, se disponível."""
    logo_bytes = _load_logo_image_bytes()
    if not logo_bytes:
        return None
    try:
        img = Image(BytesIO(logo_bytes))
        img.hAlign = "LEFT"
        img._restrictSize(32 * mm, max_height_mm * mm)
        return img
    except Exception as exc:  # pragma: no cover - log auxiliar
        print(f"[WARN] Falha ao preparar imagem do logo: {exc}")
        return None


def _format_text_for_paragraph(value) -> str:
    """Normaliza texto para uso em Paragraph."""
    text = html.escape(str(value if value not in [None, "None"] else "N/D"))
    return text.replace("\n", "<br/>")


def obter_url_card(familia_serie: pd.Series, tipo: str) -> str | None:
    """Constroi URLs para cards do Bitrix com base nos campos presentes."""
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


def construir_link_card_pipeline(row: pd.Series) -> str | None:
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

    # Pipelines de emissão brasileira (92=Casa Verde, 94=Tatuapé, 102=Paróquia, 104=Pesquisa BR)
    # Todos usam o URL /crm/type/1098/details/
    if categoria in {'92', '94', '102', '104', '1098'}:
        return f"{BASE_URL_TYPE_1098}{card_id}/"
    return f"{BASE_URL_DEAL}{card_id}/"


def _slugify(text: str) -> str:
    base = unidecode(str(text or "")).lower()
    base = _SLUG_CLEAN_RE.sub("_", base)
    base = re.sub("_+", "_", base)
    return base.strip("_")


def _montar_nome_arquivo_pdf(nome_familia: str, id_familia: str) -> str:
    partes = []
    slug_nome = _slugify(nome_familia)
    slug_id = _slugify(id_familia)
    if slug_nome:
        partes.append(slug_nome)
    if slug_id:
        partes.append(slug_id)
    base = "_".join(partes) if partes else "ficha_familia"
    return f"{base}.pdf"


def _build_key_value_table(items, label_style, value_style, label_width_mm: float = 58.0):
    if not items:
        return None

    table_data = []
    for label, raw_value in items:
        label_text = f"<b>{html.escape(str(label))}</b>"
        value_render = _format_text_for_paragraph(raw_value)
        table_data.append([
            Paragraph(label_text, label_style),
            Paragraph(value_render, value_style),
        ])

    table = Table(table_data, colWidths=[label_width_mm * mm, None], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F7FF")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1B3885")),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F4")),
            ]
        )
    )
    return table


def gerar_pdf_ficha(contexto_pdf: dict) -> bytes:
    if SimpleDocTemplate is None:
        raise RuntimeError("Biblioteca 'reportlab' não está instalada. Instale com 'pip install reportlab'.")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=24 * mm,
        bottomMargin=22 * mm,
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "FichaTitulo",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F2E6D"),
        spaceAfter=2,
        spaceBefore=0,
    )
    subtitulo_style = ParagraphStyle(
        "FichaSubTitulo",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#5F6C85"),
        leading=11,
        spaceBefore=0,
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=13,
        leading=15,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor("#133C8B"),
        borderPadding=(0, 0, 4),
    )
    table_label_style = ParagraphStyle(
        "TabelaLabel",
        parent=styles["Normal"],
        fontSize=9.3,
        textColor=colors.HexColor("#1E3A66"),
        leading=11,
        spaceAfter=0,
    )
    table_value_style = ParagraphStyle(
        "TabelaValor",
        parent=styles["Normal"],
        fontSize=9.3,
        leading=12,
        textColor=colors.HexColor("#2F394C"),
    )
    resumo_value_style = ParagraphStyle(
        "ResumoValor",
        parent=styles["Normal"],
        fontSize=10,
        alignment=1,
    )

    story = []

    logo_flowable = _create_logo_flowable()
    data_emissao = contexto_pdf.get("data_emissao") or datetime.now()
    header_left = logo_flowable if logo_flowable else Spacer(32 * mm, 18 * mm)

    header_right_style = ParagraphStyle(
        "CabecalhoDireita",
        parent=styles["Normal"],
        leading=14,
        fontSize=10.5,
        textColor=colors.HexColor("#243754"),
        alignment=2,
        spaceBefore=0,
        spaceAfter=0,
    )
    header_right = Paragraph(
        (
            "<font size='12'><b>Relatório Individual de Famílias</b></font><br/>"
            f"<font size='10'>Emitido em {data_emissao.strftime('%d/%m/%Y %H:%M')}</font>"
        ),
        header_right_style,
    )

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[48 * mm, None],
        hAlign="LEFT",
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 10 * mm))

    alertas = contexto_pdf.get("alertas") or []
    if alertas:
        cards = []
        for alerta in alertas:
            titulo = html.escape(str(alerta.get("titulo", "")))
            descricao = _format_text_for_paragraph(alerta.get("descricao", ""))
            bg_color = colors.HexColor(alerta.get("bg_color", "#F8E2A0"))
            text_color = colors.HexColor(alerta.get("text_color", "#2F2A29"))

            alert_box = Table(
                [[
                    Paragraph(
                        f"<para align='center'><font size='10'><b>{titulo}</b></font><br/><font size='9'>{descricao}</font></para>",
                        ParagraphStyle(
                            "AlertCard",
                            parent=styles["Normal"],
                            textColor=text_color,
                            leading=11,
                        )
                    )
                ]],
                colWidths=[None],
            )
            alert_box.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E1C46A")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            cards.append(alert_box)

        alerts_table = Table(
            [cards],
            colWidths=[doc.width / len(cards) for _ in cards],
        )
        alerts_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(alerts_table)
        story.append(Spacer(1, 8 * mm))

    def _add_table_section(title: str, items: list, col_width_mm: float = 58.0):
        if not items:
            return
        story.append(Paragraph(title, section_title_style))
        info_table = _build_key_value_table(items, table_label_style, table_value_style, label_width_mm=col_width_mm)
        if info_table:
            story.append(info_table)

    _add_table_section("Informações Gerais", contexto_pdf.get("dados_basicos"), col_width_mm=62)
    _add_table_section("Procuração", contexto_pdf.get("sec_procuracao"), col_width_mm=62)
    _add_table_section("Comune", contexto_pdf.get("sec_comune"), col_width_mm=62)
    _add_table_section("Documentação e Serviços", contexto_pdf.get("sec_doc_serv"), col_width_mm=62)
    _add_table_section("Detalhes", contexto_pdf.get("sec_detalhes"), col_width_mm=62)

    requerentes = contexto_pdf.get("requerentes") or []
    if requerentes:
        story.append(Paragraph("Status Emissões Brasileiras", section_title_style))
        cards = []
        cards_data = []
        for req in requerentes:
            cards_data.append(
                [
                    Paragraph(f"<b>{_format_text_for_paragraph(req.get('Requerente'))}</b>", table_label_style),
                    Paragraph(f"Posição: {_format_text_for_paragraph(req.get('Posição'))}", table_value_style),
                    Paragraph(f"Nascimento: {_format_text_for_paragraph(req.get('Nascimento'))}", table_value_style),
                    Paragraph(f"Casamento: {_format_text_for_paragraph(req.get('Casamento'))}", table_value_style),
                    Paragraph(f"Óbito: {_format_text_for_paragraph(req.get('Óbito'))}", table_value_style),
                ]
            )

        for dados_card in cards_data:
            card = Table(
                [dados_card],
                colWidths=[None, 32 * mm, 32 * mm, 32 * mm, 32 * mm],
            )
            card.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
                        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7DFEF")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            cards.append(card)

        for card in cards:
            story.append(card)
            story.append(Spacer(1, 4 * mm))

    resumo = contexto_pdf.get("resumo") or {}
    total_certidoes = contexto_pdf.get("total_certidoes") or 0
    resumo = contexto_pdf.get("resumo") or {}
    total_certidoes = contexto_pdf.get("total_certidoes") or 0
    if resumo:
        story.append(Paragraph("Resumo Emissões", section_title_style))
    resumo_cards = []
    for status, quantidade in resumo.items():
        if not quantidade and status not in ("Outros", "Pasta C/Emissão Concluída"):
            continue
        card = Table(
            [[
                Paragraph(
                    f"<para align='center'><font size='9'><b>{_format_text_for_paragraph(status)}</b></font><br/>"
                    f"<font size='12'>{quantidade}</font></para>",
                    ParagraphStyle(
                        "ResumoCard",
                        parent=styles["Normal"],
                        textColor=colors.HexColor("#1B2A4A"),
                        leading=12,
                    )
                )
            ]],
            colWidths=[35 * mm],
            rowHeights=[22 * mm],
        )
        card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F8FF")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C5D4F2")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        resumo_cards.append(card)

    total_card = Table(
        [[
            Paragraph(
                f"<para align='center'><font size='9'><b>Total</b></font><br/><font size='12'>{total_certidoes}</font></para>",
                ParagraphStyle("ResumoTotal", parent=styles["Normal"], textColor=colors.HexColor("#102347"), leading=12),
            )
        ]],
        colWidths=[35 * mm],
        rowHeights=[22 * mm],
    )
    total_card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E3EDFF")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#6885C3")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    resumo_cards.append(total_card)

    resumo_grid = Table([resumo_cards], colWidths=[doc.width / len(resumo_cards) for _ in resumo_cards])
    resumo_grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(resumo_grid)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Importar função de simplificação de estágio
# Tratamento de erro caso o arquivo não exista ou a função não seja encontrada
try:
    from views.cartorio_new.visao_geral import simplificar_nome_estagio
except ImportError as e:
    st.error(f"Erro ao importar 'simplificar_nome_estagio': {e}. A exibição do status da certidão pode falhar.")
    # Definir uma função placeholder para evitar erros fatais
    def simplificar_nome_estagio(nome):
        return str(nome) if nome else "Erro Import"

def load_crm_deal_data(category_id):
    """Carrega dados do CRM Deal (Funil/Categoria especificado) usando a função central load_merged_data."""
    print(f"[INFO] Solicitando dados CRM para category_id: {category_id} via load_merged_data")
    try:
        # Chama a função central passando o category_id desejado
        # Opcional: Passar debug=True se quiser ver os logs detalhados de load_merged_data
        # Opcional: Passar force_reload=True para ignorar o cache durante testes
        df_crm_merged = load_merged_data(category_id=category_id, debug=False, force_reload=False)

        if df_crm_merged is None or df_crm_merged.empty:
            st.warning(f"Nenhum dado encontrado ou erro ao carregar dados para a categoria {category_id}.")
            print(f"[AVISO] load_merged_data retornou vazio para category_id {category_id}")
            return pd.DataFrame() # Retorna DF vazio para consistência
        else:
            print(f"[INFO] Dados para category_id {category_id} carregados com sucesso via load_merged_data ({len(df_crm_merged)} linhas).")
            # Verificar se as colunas essenciais para a busca/ficha existem
            colunas_necessarias = ['ID', 'UF_CRM_1722883482527', 'UF_CRM_1722605592778']
            colunas_faltantes = [col for col in colunas_necessarias if col not in df_crm_merged.columns]
            if colunas_faltantes:
                st.error(f"Erro Crítico: As seguintes colunas essenciais estão faltando nos dados carregados: {colunas_faltantes}")
                print(f"[ERRO] Colunas essenciais ausentes após merge: {colunas_faltantes}. Colunas presentes: {list(df_crm_merged.columns)}")
                return pd.DataFrame()
            return df_crm_merged

    except ImportError:
        st.error("Erro Crítico: Não foi possível importar 'load_merged_data' de 'api.bitrix_connector'. Verifique a estrutura do projeto.")
        print("[ERRO CRÍTICO] Falha ao importar load_merged_data")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro inesperado ao chamar load_merged_data: {e}")
        print(f"[ERRO CRÍTICO] Erro inesperado em load_crm_deal_data ao chamar load_merged_data: {e}")
        return pd.DataFrame()

# Função para carregar CSS (pode ser movida para um utilitário depois)
def load_page_specific_css(file_path):
    try:
        with open(file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo CSS não encontrado: {file_path}")

# Função removida - agora usamos load_data_all_pipelines() do views.cartorio_new.data_loader

def exibir_ficha_familia(familia_serie, emissoes_df):
    # Imports lazy para evitar importação circular
    from views.scaner.data_loader import carregar_dados_spa_scanner
    from views.cartorio_new.data_loader import carregar_dados_cartorio
    from views.reclamacoes.data_loader import carregar_dados_reclamacoes
    from views.comune_new.data_loader import load_comune_data
    
    alertas_para_pdf = []
    resumo_status_categorias = {}
    total_certidoes_reais_para_exibicao = 0
    dados_pdf = {
        'dados_basicos': [],
        'sec_procuracao': [],
        'sec_comune': [],
        'sec_doc_serv': [],
        'sec_detalhes': [],
        'requerentes': [],
        'resumo': {},
        'total_certidoes': 0,
        'alertas': alertas_para_pdf,
        'data_emissao': datetime.now(),
        'nome_familia': '',
        'id_familia': '',
    }
    proxima_posicao_alerta = 65
    alert_css_base = """
    <style>
    @keyframes ficha-alert-pulse {
      0% {
        transform: translateY(0);
        box-shadow: 0 18px 34px rgba(16,33,61,0.20);
      }
      50% {
        transform: translateY(-3px);
        box-shadow: 0 24px 42px rgba(16,33,61,0.28);
      }
      100% {
        transform: translateY(0);
        box-shadow: 0 18px 34px rgba(16,33,61,0.20);
      }
    }
    .ficha-alert-base {
       position: fixed;
       right: 24px;
       width: 260px;
       min-height: 120px;
       border-radius: 16px;
       display: flex;
       align-items: center;
       gap: 12px;
       padding: 18px 22px;
       border: 1px solid var(--alert-border, rgba(0,0,0,0.25));
       background: var(--alert-bg, #FFC107);
       color: var(--alert-color, #1c1c1c);
       box-shadow: 0 14px 28px rgba(16,33,61,0.20);
       opacity: 0.99;
       z-index: 9999;
     }
     .ficha-alert-base.no-icon {
       padding-left: 26px;
     }
     .ficha-alert-text {
       display: flex;
       flex-direction: column;
       gap: 6px;
     }
     .ficha-alert-title {
       font-weight: 800;
       letter-spacing: 0.045em;
       text-transform: uppercase;
       font-size: 1rem;
       line-height: 1.3;
     }
     .ficha-alert-subtitle {
       font-size: 0.9rem;
       line-height: 1.45;
       font-weight: 600;
       opacity: 0.98;
     }
     </style>
     """
    alert_css_injetado = False

    def _render_alert_box(titulo_texto, subtitulo_texto, background_color, border_color, text_color, top_position):
        nonlocal alert_css_injetado
        if not alert_css_injetado:
            st.markdown(alert_css_base, unsafe_allow_html=True)
            alert_css_injetado = True

        titulo_html = f"<div class='ficha-alert-title'>{html.escape(str(titulo_texto))}</div>" if titulo_texto else ""
        subtitulo_html = f"<div class='ficha-alert-subtitle'>{html.escape(str(subtitulo_texto))}</div>" if subtitulo_texto else ""

        style_parts = [
            f"top:{int(top_position)}px",
            f"--alert-bg:{background_color}",
            f"--alert-border:{border_color}",
            f"--alert-color:{text_color}"
        ]
        style_attr = '; '.join(style_parts)
        class_extra = ' no-icon'

        alert_html = (
            f"<div class='ficha-alert-base{class_extra}' style='{style_attr}'>"
            f"<div class='ficha-alert-text'>{titulo_html}{subtitulo_html}</div>"
            "</div>"
        )
        st.markdown(alert_html, unsafe_allow_html=True)

    tabela_emissoes_css = '''
    <style>
    .cert-status-wrapper {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .cert-status-wrapper.duplicado {
        position: relative;
        border-left: 4px solid #FF9800;
        padding-left: 16px;
    }
    .cert-status-wrapper.duplicado::before {
        content: "Duplicado";
        position: absolute;
        top: -10px;
        left: 0;
        transform: translate(-6px, -50%);
        background: linear-gradient(135deg, #FF9800 0%, #FB8C00 100%);
        color: #FFFFFF;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        padding: 3px 9px;
        border-radius: 999px;
        box-shadow: 0 4px 10px rgba(255, 152, 0, 0.35);
        text-transform: uppercase;
    }
    .cert-card {
        background: #FFFFFF;
        border: 1px solid rgba(13, 110, 253, 0.18);
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 14px 28px rgba(16, 33, 61, 0.12);
        display: flex;
        flex-direction: column;
        gap: 10px;
        text-align: left;
    }
    .cert-card.default-status {
        background: linear-gradient(135deg, #F8FAFF 0%, #EEF3FF 100%);
        border: 1px dashed rgba(13, 110, 253, 0.35);
        color: #4A5663;
        box-shadow: none;
    }
    .cert-card-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
    }
    .cert-status-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #10213D;
        line-height: 1.35;
    }
    .cert-status-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }
    .cert-chip {
        --chip-bg: rgba(13, 110, 253, 0.14);
        --chip-color: #0D47A1;
        background: var(--chip-bg);
        color: var(--chip-color);
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 999px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .cert-chip svg {
        width: 12px;
        height: 12px;
    }
    .cert-note {
        font-size: 0.80rem;
        color: #617089;
        line-height: 1.45;
    }
    .cert-status-links {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .cert-link-button {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        border-radius: 6px;
        text-decoration: none;
        background: transparent;
        border: 1px solid rgba(13, 110, 253, 0.35);
        color: #0D6EFD !important;
        font-size: 0.76rem;
        font-weight: 600;
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        box-shadow: none;
    }
    .cert-link-button:hover {
        background-color: rgba(13, 110, 253, 0.08);
        border-color: rgba(13, 110, 253, 0.55);
        color: #0B5ED7 !important;
    }
    .cert-link-icon {
        font-size: 0.85em;
        line-height: 1;
    }
    .ficha-download-bar {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 12px;
        margin: 14px 0 8px 0;
    }
    </style>
    '''
    tabela_emissoes_css_injetado = False

    # EXIBIR AVISO "MAPA INICIAL" SE CAMPO ESPECÍFICO FOR "SIM"
    if str(familia_serie.get('UF_CRM_1750454794052', '')).strip().upper() == 'SIM':
        mapa_inicial_css = """
        <style>
        @keyframes pulse-border {
          0% {
            box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.8);
          }
          70% {
            box-shadow: 0 0 0 12px rgba(255, 193, 7, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(255, 193, 7, 0);
          }
        }

        .mapa-inicial-notification {
          position: fixed;
          top: 65px;
          right: 0;
          width: 150px;
          height: 150px;
          background-color: #FFC107; /* Amarelo Âmbar */
          color: #1c1c1c;
          border-radius: 8px 0 0 8px;
          display: flex;
          justify-content: center;
          align-items: center;
          font-weight: bold;
          font-size: 1.1em;
          text-align: center;
          z-index: 9999;
          box-shadow: 0 4px 12px rgba(0,0,0,0.25);
          animation: pulse-border 2s infinite;
          padding: 10px;
          border: 2px solid #FFA000;
          border-right: none;
        }
        </style>
        """
        mapa_inicial_html = "<div class='mapa-inicial-notification'>MAPA INICIAL</div>"
        st.markdown(mapa_inicial_html + mapa_inicial_css, unsafe_allow_html=True)
        proxima_posicao_alerta = 240
    else:
        proxima_posicao_alerta = 65

    canal_especial_valor = str(familia_serie.get('UF_CRM_1759161772', '') or '').strip()
    if canal_especial_valor:
        canal_especial_upper = canal_especial_valor.upper()
        canais_validos = {
            'RECLAME AQUI': {
                'bg': 'linear-gradient(135deg, #FF6B6B 0%, #F44336 100%)',
                'border': 'rgba(255,255,255,0.35)',
                'color': '#FFFFFF',
                'label': 'Reclame Aqui',
                'accent': '#E53935',
                'icon_bg': 'rgba(255,255,255,0.22)',
                'icon_color': '#FFFFFF',
                'icon': (
                    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'"
                    " stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
                    "<path d='M21.707 20.293 13.414 12l8.293-8.293a1 1 0 0 0-1.414-1.414L12 10.586 3.707 2.293A1 1 0 1 0 2.293 3.707L10.586 12l-8.293 8.293a1 1 0 1 0 1.414 1.414L12 13.414l8.293 8.293a1 1 0 0 0 1.414-1.414Z'/>"
                    "</svg>"
                )
            },
            'EXTRAJUDICIAL': {
                'bg': '#5E35B1',
                'border': 'rgba(255,255,255,0.28)',
                'color': '#FFFFFF',
                'label': 'Extrajudicial'
            },
            'PROCON': {
                'bg': '#FFB300',
                'border': 'rgba(0,0,0,0.15)',
                'color': '#1C1C1C',
                'label': 'PROCON'
            },
            'PROCESSO JUDICIAL': {
                'bg': '#1E88E5',
                'border': 'rgba(255,255,255,0.3)',
                'color': '#FFFFFF',
                'label': 'Processo Judicial'
            }
        }
        if canal_especial_upper in canais_validos:
            canal_config = canais_validos[canal_especial_upper]
            _render_alert_box(
                "Canal de Reclamação",
                canal_config['label'],
                canal_config['bg'],
                canal_config['border'],
                canal_config['color'],
                proxima_posicao_alerta
            )
            proxima_posicao_alerta += 195
            alertas_para_pdf.append({
                'titulo': 'Canal de Reclamação',
                'descricao': canal_config['label'],
                'bg_color': '#FFC107',
                'text_color': '#1C1C1C'
            })

    distrato_valor = str(familia_serie.get('UF_CRM_1759159659148', '') or '').strip().upper()
    if distrato_valor == 'SIM':
        distrato_icon = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'"
            " stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
            "<path d='M12 21s-6-4.35-6-10a6 6 0 1 1 12 0c0 5.65-6 10-6 10Z'/>"
            "<path d='m9.5 9.5 5 5'/>"
            "<path d='m14.5 9.5-5 5'/>"
            "</svg>"
        )
        _render_alert_box(
            "Família em Distrato",
            "Acompanhar com prioridade",
            "#FF3B30",
            "rgba(0,0,0,0.1)",
            "#FFFFFF",
            proxima_posicao_alerta
        )
        proxima_posicao_alerta += 195
        alertas_para_pdf.append({
            'titulo': 'Família em Distrato',
            'descricao': 'Acompanhar com prioridade',
            'bg_color': '#FF3B30',
            'text_color': '#FFFFFF'
        })

    # Iniciar a string HTML com o contêiner principal e adicionar título
    html_ficha_completa = "<div class='ficha-familia-container' style='width:100%; max-width:100%; margin-right:0; margin-left:0;'>"
    
    # Título principal da ficha
    html_ficha_completa += "<div style='background-color:#0070F2; color:white; text-align:center; padding:10px; margin-bottom:15px; font-size:1.3em; font-weight:bold; border-radius:5px;'>ACOMPANHAMENTO FAMÍLIA</div>"

    # DEBUG: Imprimir colunas disponíveis
    print("[DEBUG] Colunas disponíveis na família:", list(familia_serie.index))
    print("\n[DEBUG] Primeiros 10 campos e seus valores:")
    contador = 0
    for campo, valor in familia_serie.items():
        if contador < 10:
            print(f"[DEBUG] {campo}: {valor}")
            contador += 1
    
    # DEBUG: Listar todos os campos UF_CRM e seus valores
    print("\n[DEBUG] Todos campos UF_CRM e seus valores:")
    for campo, valor in familia_serie.items():
        if str(campo).startswith('UF_CRM'):
            print(f"[DEBUG] {campo}: {valor}")
    
    # --- Coleta todos os dados primeiro ---
    nome_familia = familia_serie.get('UF_CRM_1722883482527', 'N/D')
    
    # Tentar múltiplas alternativas para Data de Venda
    data_venda = None
    # Campos mais prováveis para DATA DE VENDA
    campos_data_venda = [
        'UF_CRM_1746054586042',  # ID informado pelo cliente
        'UF_CRM_1739362935',     # Possível campo de data
        'UF_CRM_1725397957843',  # Campo anterior
        'DATE_CREATE',           # Data de criação do registro
        'BEGINDATE',             # Data de início
        'CLOSEDATE'              # Data de fechamento
    ]
    
    for campo in campos_data_venda:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            data_venda = familia_serie.get(campo)
            print(f"[DEBUG] Data de venda encontrada no campo '{campo}': {data_venda}")
            break
            
    if data_venda is None or data_venda == 'None':
        data_venda = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para Data de Venda")
    
    id_familia = familia_serie.get('UF_CRM_1722605592778', 'N/D')
    
    # Tentar múltiplas alternativas para ADM Responsável
    adm_responsavel = None
    # Campos mais prováveis para ADM RESPONSÁVEL
    campos_adm = [
        'UF_CRM_1730730467',    # ID informado pelo cliente
        'ASSIGNED_BY_ID',       # Responsável atribuído
        'ASSIGNED_BY',          # Nome do responsável
        'RESPONSIBLE_ID',       # Outra possibilidade 
        'UF_CRM_1746198853',    # Campo anterior
        'CREATED_BY_ID'         # Criador do registro
    ]
    
    for campo in campos_adm:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            adm_responsavel = familia_serie.get(campo)
            print(f"[DEBUG] ADM Responsável encontrado no campo '{campo}': {adm_responsavel}")
            break
            
    if adm_responsavel is None or adm_responsavel == 'None':
        adm_responsavel = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para ADM Responsável")
    
    # Link do Contrato
    link_contrato_raw = familia_serie.get('UF_CRM_1750453631850', 'N/D')
    link_contrato_display = f"<a href='{link_contrato_raw}' target='_blank' class='ficha-link'>Acessar Contrato</a>" if str(link_contrato_raw).startswith('http') else str(link_contrato_raw)

    # Tentar múltiplas alternativas para Procuração
    procuracao_detalhes = None
    # Campos mais prováveis para PROCURAÇÃO
    campos_proc = [
        'UF_CRM_1746046262136',   # ID correto identificado pelo cliente - PROCURAÇÃO PENDENTE
        'UF_CRM_1744671378914',   # ID anterior
        'UF_CRM_1737561431',      # Possível campo de procuração
        'UF_CRM_1746089520',      # Possível campo de procuração
        'COMMENTS',               # Comentários gerais
        'DESCRIPTION'             # Descrição
    ]
    
    for campo in campos_proc:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            procuracao_detalhes = familia_serie.get(campo)
            print(f"[DEBUG] Procuração encontrada no campo '{campo}': {procuracao_detalhes}")
            break
            
    if procuracao_detalhes is None or procuracao_detalhes == 'None':
        procuracao_detalhes = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para Procuração")
    
    # Tentar múltiplas alternativas para Etapa Comune
    etapa_comune = None
    # Campos mais prováveis para ETAPA COMUNE
    campos_comune = [
        'UF_CRM_1746045819198',   # ID informado pelo cliente
        'UF_CRM_1737823612831',   # Campo anterior
        'STAGE_ID',               # ID do estágio
        'STAGE_SEMANTIC_ID',      # Semântica do estágio
        'UF_CRM_1737561431'       # Possível campo de comune
    ]
    
    for campo in campos_comune:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            etapa_comune = familia_serie.get(campo)
            print(f"[DEBUG] Etapa Comune encontrada no campo '{campo}': {etapa_comune}")
            break
            
    if etapa_comune is None or etapa_comune == 'None':
        etapa_comune = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para Etapa Comune")
    
    data_solicitacao_comune = familia_serie.get('UF_CRM_1737823552173', 'N/D')
    if data_solicitacao_comune is None or data_solicitacao_comune == 'None': data_solicitacao_comune = 'N/D'
    prazo_comune = familia_serie.get('UF_CRM_1746202791172', 'N/D')
    if prazo_comune is None or prazo_comune == 'None': prazo_comune = 'N/D'
    analise_doc = familia_serie.get('UF_CRM_1746045866262', 'N/D')
    if analise_doc is None or analise_doc == 'None': analise_doc = 'N/D'
    traducao = familia_serie.get('UF_CRM_1746045880601', 'N/D')
    if traducao is None or traducao == 'None': traducao = 'N/D'
    apostilamento = familia_serie.get('UF_CRM_1746045919198', 'N/D')
    if apostilamento is None or apostilamento == 'None': apostilamento = 'N/D'
    drive_link_raw = familia_serie.get('UF_CRM_DRIVE', 'N/D')
    drive_display = f"<a href='{drive_link_raw}' target='_blank' class='ficha-link'>Acessar Link</a>" if str(drive_link_raw).startswith('http') else str(drive_link_raw)
    qnt_familiares = familia_serie.get('UF_CRM_QUANTIDADE_FAMILIARES', 'N/D')
    if qnt_familiares is None or qnt_familiares == 'None': qnt_familiares = 'N/D'
    qnt_requerentes = familia_serie.get('UF_CRM_1743182118', 'N/D')
    if qnt_requerentes is None or qnt_requerentes == 'None': qnt_requerentes = 'N/D'
    emissoes_status_geral = familia_serie.get('UF_CRM_1746459875884', 'N/D')
    if emissoes_status_geral is None or emissoes_status_geral == 'None': emissoes_status_geral = 'N/D'

    # (Lógica de processamento de emissões, agora incluindo a posição na árvore)
    requerentes_data_list_of_dicts = []
    processamento_emissoes_ok = False
    # Mapa de documentos por (ID_Requerente, TipoCertidao) -> lista de links (Drive preferido primeiro)
    docs_map = {}
    try:
        id_familia_str_local = str(familia_serie.get('UF_CRM_1722605592778', '')).strip()
        if id_familia_str_local:
            df_docs_spa_local = carregar_dados_spa_scanner()
            if df_docs_spa_local is not None and not df_docs_spa_local.empty:
                df_docs_spa_local['UF_CRM_48_ID_FAMILIA'] = df_docs_spa_local['UF_CRM_48_ID_FAMILIA'].astype(str).str.strip()
                df_docs_spa_local['UF_CRM_48_ID_REQUERENTE'] = df_docs_spa_local['UF_CRM_48_ID_REQUERENTE'].astype(str).str.strip()
                docs_familia_local = df_docs_spa_local[df_docs_spa_local['UF_CRM_48_ID_FAMILIA'] == id_familia_str_local].copy()
                if not docs_familia_local.empty:
                    def _inferir_tipo_certidao_spa(titulo: str) -> str:
                        # Normaliza acentuação e caixa para evitar falsos positivos
                        t_norm = unidecode(str(titulo)).upper()
                        # Match exato prioritário
                        if 'CERTIDAO NASCIMENTO' in t_norm or 'NASCIMENTO' in t_norm:
                            return 'Nascimento'
                        if 'CERTIDAO CASAMENTO' in t_norm or 'MATRIMONIO' in t_norm or 'CASAMENTO' in t_norm:
                            return 'Casamento'
                        if 'CERTIDAO OBITO' in t_norm or 'OBITO' in t_norm or 'OBITO' in t_norm or 'OBIT' in t_norm:
                            return 'Óbito'
                        # Alguns títulos podem vir abreviados; fallback seguro
                        if 'NASC' in t_norm:
                            return 'Nascimento'
                        if 'CASA' in t_norm or 'MATRIM' in t_norm:
                            return 'Casamento'
                        if 'OBIT' in t_norm:
                            return 'Óbito'
                        return 'Outro'
                    docs_familia_local['__tipo__'] = docs_familia_local['TITLE'].apply(_inferir_tipo_certidao_spa)
                    for _i, r in docs_familia_local.iterrows():
                        req_id = str(r.get('UF_CRM_48_ID_REQUERENTE', '')).strip()
                        tipo = str(r.get('__tipo__', 'Outro'))
                        link_drive = str(r.get('UF_CRM_48_LINK_DRIVE', '')).strip()
                        link_scan = str(r.get('UF_CRM_48_DOCUMENTO_SCANEADO', '')).strip()
                        chosen_link = link_drive if link_drive.lower().startswith('http') else (link_scan if link_scan.lower().startswith('http') else '')
                        # Guardar um link por par (Requerente, Tipo). Não sobrescrever se já existir
                        if req_id and tipo in ['Nascimento', 'Casamento', 'Óbito'] and chosen_link:
                            chave_doc = (req_id, tipo)
                            if chave_doc not in docs_map:
                                docs_map[chave_doc] = []
                            if chosen_link not in docs_map[chave_doc]:
                                docs_map[chave_doc].append(chosen_link)
    except Exception as _e:
        print(f"[WARN] Falha ao montar docs_map SPA: {_e}")
    
    # NOVA LÓGICA: Função para determinar categoria baseada em Pipeline + Status
    # Esta correção resolve o problema de chaves duplicadas no mapeamento anterior
    def determinar_categoria_por_pipeline_status(category_id, stage_name_legivel):
            """Determina a categoria do resumo baseada no pipeline (CATEGORY_ID) e status (STAGE_NAME_LEGIVEL)"""
            category_id_str = str(category_id)
            status_upper = str(stage_name_legivel).upper() if pd.notna(stage_name_legivel) else ""
            
            # Pipeline 92 e 94 (Cartórios Casa Verde e Tatuapé)
            if category_id_str in ['92', '94']:
                if status_upper == "AGUARDANDO DECISÃO CLIENTE":
                    return "AGUARDANDO DECISÃO CLIENTE"
                if status_upper in ["AGUARDANDO CERTIDÃO", "BUSCA - CRC", "DEVOLUTIVA BUSCA - CRC", 
                                  "APENAS ASS. REQ CLIENTE P/MONTAGEM", "MONTAGEM REQUERIMENTO CARTÓRIO", 
                                  "SOLICITAR CARTÓRIO DE ORIGEM", "SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", 
                                  "DEVOLUÇÃO ADM", "DEVOLVIDO REQUERIMENTO"] or "DEVOLUÇÃO ADM" in status_upper:
                    return "Brasileiras Pendências"
                elif status_upper == "PESQUISA - BR":
                    return "Brasileiras Pesquisas"
                elif status_upper == "AGUARDANDO CARTÓRIO ORIGEM":
                    return "Brasileiras Solicitadas"
                elif status_upper in ["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]:
                    return "Brasileiras Emitida"  # CORRIGIDO: Era "Pasta C/Emissão Concluída"
                elif status_upper in ["SOLICITAÇÃO DUPLICADA", "CANCELADO", "CERTIDÃO DISPENSADA"]:
                    return "Brasileiras Dispensada"  # Não contabilizada no resumo ativo
                    
            # Pipeline 102 (Paróquia)
            elif category_id_str == '102':
                if status_upper in ["SOLICITAR PARÓQUIA DE ORIGEM", "DEVOLUÇÃO ADM"] or "DEVOLUÇÃO ADM" in status_upper:
                    return "Paróquia Pendências"
                elif status_upper == "AGUARDANDO PARÓQUIA DE ORIGEM":
                    return "Paróquia Solicitadas"
                elif status_upper in ["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]:
                    return "Paróquia Emitida"  # CORRIGIDO: Consistente com a lógica
                elif status_upper in ["SOLICITAÇÃO DUPLICADA", "CANCELADO", "CERTIDÃO DISPENSADA"]:
                    return "Paróquia Dispensada"  # Não contabilizada no resumo ativo
                    
            # Pipeline 104 (Pesquisa BR)
            elif category_id_str == '104':
                if status_upper == "AGUARDANDO PESQUISADOR":
                    return "Pesquisa BR Pendências"
                elif status_upper == "PESQUISA EM ANDAMENTO":
                    return "Pesquisa BR Em Andamento"
                elif status_upper == "PESQUISA PRONTA PARA EMISSÃO":
                    return "Pesquisa BR Concluída"
                elif status_upper == "PESQUISA NÃO ENCONTRADA":
                    return "Pesquisa BR Não Encontrada"
            
            # Default para casos não mapeados
            return "Outros"

    pipeline_nome_map = {
        '92': 'Cartório 92',
        '94': 'Cartório 94',
        '102': 'Paróquia',
        '104': 'Pesquisa BR'
    }

    def obter_nome_pipeline_legivel(row: pd.Series) -> str:
        nome_pipeline = str(row.get('NOME_PIPELINE', '') or '').strip()
        if nome_pipeline:
            return nome_pipeline
        categoria_id_local = str(row.get('CATEGORY_ID', '') or '').strip()
        return pipeline_nome_map.get(categoria_id_local, f"Pipeline {categoria_id_local}" if categoria_id_local else '')

    if emissoes_df is not None and not emissoes_df.empty:
        col_stage_para_simplificar = None
        if 'STAGE_ID' in emissoes_df.columns: col_stage_para_simplificar = 'STAGE_ID'
        elif 'STAGE_NAME' in emissoes_df.columns: col_stage_para_simplificar = 'STAGE_NAME'
        if col_stage_para_simplificar:
            try:
                emissoes_df['STAGE_NAME_LEGIVEL'] = emissoes_df[col_stage_para_simplificar].apply(simplificar_nome_estagio)
                # Normalização para novo estágio: UC_PBAY8U -> [EM EXECUÇÃO]DEVOLUÇÃO ADM
                try:
                    mask_uc_pbay8u = pd.Series(False, index=emissoes_df.index)
                    if 'STAGE_ID' in emissoes_df.columns:
                        mask_uc_pbay8u = mask_uc_pbay8u | emissoes_df['STAGE_ID'].astype(str).str.upper().str.contains('UC_PBAY8U', na=False)
                    if 'STAGE_NAME' in emissoes_df.columns:
                        mask_uc_pbay8u = mask_uc_pbay8u | emissoes_df['STAGE_NAME'].astype(str).str.upper().str.contains('UC_PBAY8U', na=False)
                    emissoes_df.loc[mask_uc_pbay8u, 'STAGE_NAME_LEGIVEL'] = '[EM EXECUÇÃO]DEVOLUÇÃO ADM'
                except Exception:
                    pass
                processamento_emissoes_ok = True
                # DEBUG ADICIONADO
                print("\n[DEBUG ANTES DO LOOP DE REQUERENTES] Primeiras 20 linhas de emissoes_df com STAGE_NAME_LEGIVEL:")
                if not emissoes_df.empty and col_stage_para_simplificar in emissoes_df.columns :
                    print(emissoes_df[['TITLE', 'UF_CRM_34_TIPO_DE_CERTIDAO', col_stage_para_simplificar, 'STAGE_NAME_LEGIVEL']].head(20))
                else:
                    print("[DEBUG ANTES DO LOOP DE REQUERENTES] emissoes_df vazio ou coluna de stage ausente.")
            except Exception: emissoes_df['STAGE_NAME_LEGIVEL'] = emissoes_df[col_stage_para_simplificar]; processamento_emissoes_ok = True
        else: processamento_emissoes_ok = False
        if processamento_emissoes_ok:
            map_tipo_certidao = {'NASCIMENTO': 'Nascimento', 'CASAMENTO': 'Casamento', 'ÓBITO': 'Óbito'}
            # Adicionando UF_CRM_34_POSICAO_ARVORE à lista de colunas necessárias
            cols_req = ['UF_CRM_34_ID_REQUERENTE', 'TITLE', 'UF_CRM_34_TIPO_DE_CERTIDAO', 'STAGE_NAME_LEGIVEL', 'UF_CRM_34_POSICAO_ARVORE']
            
            # Verificamos se todas as colunas necessárias existem
            colunas_faltantes = [col for col in cols_req if col not in emissoes_df.columns]
            
            if colunas_faltantes:
                print(f"[AVISO] Colunas ausentes nos dados: {colunas_faltantes}")
                if 'UF_CRM_34_POSICAO_ARVORE' in colunas_faltantes:
                    # Criar coluna com valor padrão se ela estiver faltando
                    emissoes_df['UF_CRM_34_POSICAO_ARVORE'] = "N/D"
                    colunas_faltantes.remove('UF_CRM_34_POSICAO_ARVORE')
            
            if not colunas_faltantes:  # Se todas as colunas obrigatórias estiverem presentes
                col_id_requerente = cols_req[0]
                emissoes_df[col_id_requerente] = emissoes_df[col_id_requerente].fillna('').astype(str)

                valores_invalidos_id_norm = {
                    '', 'nan', 'none', 'null', 'n/d',
                    'id requerente n/d', 'id req. nao localizado', 'id req. nao localizados',
                    'id req. nao localizado.', 'id req. nao localizados.', 'id req. nao localizado)'
                }

                def _normalizar_id(valor: str) -> str:
                    texto = str(valor or '').strip()
                    texto_norm = unidecode(texto).lower()
                    return '' if texto_norm in valores_invalidos_id_norm else texto

                emissoes_df[col_id_requerente] = emissoes_df[col_id_requerente].apply(_normalizar_id)

                def _extrair_nome_limpo(titulo: str) -> str:
                    texto = str(titulo or '').strip()
                    if ' - ' in texto:
                        texto = texto.split(' - ', 1)[1]
                    texto = re.sub(r'\(.*?\)', '', texto)
                    return re.sub(r'\s+', ' ', texto).strip()

                emissoes_df['_NOME_LIMPO'] = emissoes_df['TITLE'].apply(_extrair_nome_limpo)

                emissoes_df['_ID_REQUERENTE_ORIGINAL'] = emissoes_df[col_id_requerente].apply(
                    lambda valor: valor if valor else 'ID Requerente N/D'
                )

                def _gerar_chave_sem_id(row) -> str:
                    nome_limpo = row.get('_NOME_LIMPO', '') or ''
                    posicao_val = str(row.get('UF_CRM_34_POSICAO_ARVORE', '') or '').strip()
                    partes = [unidecode(nome_limpo).upper()]
                    if posicao_val:
                        partes.append(unidecode(posicao_val).upper())
                    base = '_'.join(partes).strip('_')
                    base = re.sub(r'[^A-Z0-9]+', '_', base)
                    if not base:
                        base = f"REQUERENTE_{row.name}"
                    return f"SEM_ID::{base}"

                emissoes_df['_ID_REQUERENTE_GRUPO'] = emissoes_df['_ID_REQUERENTE_ORIGINAL']
                mask_sem_id = emissoes_df['_ID_REQUERENTE_ORIGINAL'] == 'ID Requerente N/D'
                emissoes_df.loc[mask_sem_id, '_ID_REQUERENTE_GRUPO'] = emissoes_df.loc[mask_sem_id].apply(_gerar_chave_sem_id, axis=1)

                emissoes_df[cols_req[1]] = emissoes_df[cols_req[1]].fillna('Nome N/D').astype(str)
                emissoes_df[cols_req[2]] = emissoes_df[cols_req[2]].fillna('Tipo N/D').astype(str)
                emissoes_df[cols_req[3]] = emissoes_df[cols_req[3]].fillna('Status N/D').astype(str)
                emissoes_df[cols_req[4]] = emissoes_df[cols_req[4]].fillna('Não informado').astype(str)

                grouped_by_requerente = emissoes_df.groupby('_ID_REQUERENTE_GRUPO', sort=False)
                if grouped_by_requerente.ngroups > 0:
                    for id_req_grupo, grupo in grouped_by_requerente:
                        id_req_original = grupo['_ID_REQUERENTE_ORIGINAL'].iloc[0] if '_ID_REQUERENTE_ORIGINAL' in grupo.columns else id_req_grupo
                        nome_req_bruto = ''
                        if '_NOME_LIMPO' in grupo.columns and grupo['_NOME_LIMPO'].iloc[0]:
                            nome_req_bruto = grupo['_NOME_LIMPO'].iloc[0]
                        elif not grupo[cols_req[1]].empty:
                            nome_req_bruto = grupo[cols_req[1]].iloc[0]
                        else:
                            nome_req_bruto = "Req. Desconhecido"

                        posicao_arvore = grupo[cols_req[4]].iloc[0] if not grupo[cols_req[4]].empty else "N/D"

                        if not id_req_original or id_req_original == 'ID Requerente N/D':
                            nome_req_bruto = nome_req_bruto or (grupo[cols_req[1]].iloc[0] if not grupo[cols_req[1]].empty else "Req. Desconhecido")

                        nome_limpo = str(nome_req_bruto)
                        prefixes_to_remove = ["NASCIMENTO - ", "CASAMENTO - ", "ÓBITO - "]
                        for prefix in prefixes_to_remove:
                            if nome_limpo.startswith(prefix):
                                nome_limpo = nome_limpo[len(prefix):]
                                break
                        nome_req_disp = nome_limpo.strip()

                        if not nome_req_disp:
                            nome_req_disp = "Requerente sem identificação"

                        cert_status = {v: 'Dispensado' for k, v in map_tipo_certidao.items() if v}
                        
                        # NOVA LÓGICA: Precedência de pipelines
                        # Se a pessoa tem "PESQUISA PRONTA PARA EMISSÃO" no pipeline 104,
                        # devemos verificar se ela tem registros nos pipelines superiores (92, 94, 102)
                        pipeline_104_pronto = False
                        registros_pipelines_superiores = []
                        
                        # Verificar se há registro no pipeline 104 com status "PESQUISA PRONTA PARA EMISSÃO"
                        for _, row in grupo.iterrows():
                            if 'CATEGORY_ID' in row and str(row['CATEGORY_ID']) == '104':
                                if row[cols_req[3]] == 'PESQUISA PRONTA PARA EMISSÃO':
                                    pipeline_104_pronto = True
                            elif 'CATEGORY_ID' in row and str(row['CATEGORY_ID']) in ['92', '94', '102']:
                                registros_pipelines_superiores.append(row)
                        
                        # Aplicar lógica de precedência
                        if pipeline_104_pronto and registros_pipelines_superiores:
                            # Se tem pipeline 104 pronto E registros nos superiores,
                            # processar apenas os registros dos pipelines superiores
                            print(f"[DEBUG PRECEDÊNCIA] ID_REQUERENTE {id_req_original}: Pipeline 104 pronto, usando status dos pipelines superiores")
                            for row in registros_pipelines_superiores:
                                tipo_l = map_tipo_certidao.get(str(row[cols_req[2]]).upper())
                                if tipo_l: 
                                    cert_status[tipo_l] = row[cols_req[3]] if cert_status[tipo_l] == 'Dispensado' or row[cols_req[3]] != 'Dispensado' else cert_status[tipo_l]
                        else:
                            # Lógica normal: processar todos os registros
                            for _, row in grupo.iterrows():
                                tipo_l = map_tipo_certidao.get(str(row[cols_req[2]]).upper())
                                if tipo_l: 
                                    cert_status[tipo_l] = row[cols_req[3]] if cert_status[tipo_l] == 'Dispensado' or row[cols_req[3]] != 'Dispensado' else cert_status[tipo_l]

                        # Incluir a posição na árvore nos dados a serem exibidos
                        requerentes_data_list_of_dicts.append({
                    'ID_Requerente': id_req_original,
                    'ID_Requerente_Grupo': id_req_grupo,
                            'Requerente': nome_req_disp,
                            'Posição': posicao_arvore,
                            **cert_status
                        })
                else: processamento_emissoes_ok = False
            else: processamento_emissoes_ok = False
    # (FIM DA LÓGICA DE PROCESSAMENTO DE EMISSÕES)

    # Ordenar requerentes_data_list_of_dicts por posição na ordem: ITALIANO, FAMILIAR, REQUERENTE
    if requerentes_data_list_of_dicts:
        def ordem_posicao(item):
            posicao = item.get('Posição', '').upper()
            if posicao == 'ITALIANO': return 1
            elif posicao in ['FAMILIAR', 'FAMILIA']: 
                item['Posição'] = 'FAMILIAR'
                return 2
            elif posicao == 'REQUERENTE': return 3
            else: return 4
        
        requerentes_data_list_of_dicts.sort(key=ordem_posicao)

    # --- Montar a Tabela HTML Única --- 
    html_ficha_completa = "<div class='ficha-familia-container' style='width:100%; max-width:100%; margin-right:0; margin-left:0;'>"
    html_ficha_completa += "<div style='background-color:#0070F2; color:white; text-align:center; padding:10px; margin-bottom:15px; font-size:1.3em; font-weight:bold; border-radius:5px;'>ACOMPANHAMENTO FAMÍLIA</div>"

    # DEBUG: Imprimir colunas disponíveis
    print("[DEBUG] Colunas disponíveis na família:", list(familia_serie.index))
    print("\n[DEBUG] Primeiros 10 campos e seus valores:")
    contador = 0
    for campo, valor in familia_serie.items():
        if contador < 10:
            print(f"[DEBUG] {campo}: {valor}")
            contador += 1
    
    # DEBUG: Listar todos os campos UF_CRM e seus valores
    print("\n[DEBUG] Todos campos UF_CRM e seus valores:")
    for campo, valor in familia_serie.items():
        if str(campo).startswith('UF_CRM'):
            print(f"[DEBUG] {campo}: {valor}")
    
    # --- Coleta todos os dados primeiro ---
    nome_familia = familia_serie.get('UF_CRM_1722883482527', 'N/D')
    
    # Tentar múltiplas alternativas para Data de Venda
    data_venda = None
    # Campos mais prováveis para DATA DE VENDA
    campos_data_venda = [
        'UF_CRM_1746054586042',  # ID informado pelo cliente
        'UF_CRM_1739362935',     # Possível campo de data
        'UF_CRM_1725397957843',  # Campo anterior
        'DATE_CREATE',           # Data de criação do registro
        'BEGINDATE',             # Data de início
        'CLOSEDATE'              # Data de fechamento
    ]
    
    for campo in campos_data_venda:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            data_venda = familia_serie.get(campo)
            print(f"[DEBUG] Data de venda encontrada no campo '{campo}': {data_venda}")
            break
            
    if data_venda is None or data_venda == 'None':
        data_venda = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para Data de Venda")
    
    id_familia = familia_serie.get('UF_CRM_1722605592778', 'N/D')
    
    # Tentar múltiplas alternativas para ADM Responsável
    adm_responsavel = None
    # Campos mais prováveis para ADM RESPONSÁVEL
    campos_adm = [
        'UF_CRM_1730730467',    # ID informado pelo cliente
        'ASSIGNED_BY_ID',       # Responsável atribuído
        'ASSIGNED_BY',          # Nome do responsável
        'RESPONSIBLE_ID',       # Outra possibilidade 
        'UF_CRM_1746198853',    # Campo anterior
        'CREATED_BY_ID'         # Criador do registro
    ]
    
    for campo in campos_adm:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            adm_responsavel = familia_serie.get(campo)
            print(f"[DEBUG] ADM Responsável encontrado no campo '{campo}': {adm_responsavel}")
            break
            
    if adm_responsavel is None or adm_responsavel == 'None':
        adm_responsavel = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para ADM Responsável")
    
    # Link do Contrato
    link_contrato_raw = familia_serie.get('UF_CRM_1750453631850', 'N/D')
    link_contrato_display = f"<a href='{link_contrato_raw}' target='_blank' class='ficha-link'>Acessar Contrato</a>" if str(link_contrato_raw).startswith('http') else str(link_contrato_raw)

    # Tentar múltiplas alternativas para Procuração
    procuracao_detalhes = None
    # Campos mais prováveis para PROCURAÇÃO
    campos_proc = [
        'UF_CRM_1746046262136',   # ID correto identificado pelo cliente - PROCURAÇÃO PENDENTE
        'UF_CRM_1744671378914',   # ID anterior
        'UF_CRM_1737561431',      # Possível campo de procuração
        'UF_CRM_1746089520',      # Possível campo de procuração
        'COMMENTS',               # Comentários gerais
        'DESCRIPTION'             # Descrição
    ]
    
    for campo in campos_proc:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            procuracao_detalhes = familia_serie.get(campo)
            print(f"[DEBUG] Procuração encontrada no campo '{campo}': {procuracao_detalhes}")
            break
            
    if procuracao_detalhes is None or procuracao_detalhes == 'None':
        procuracao_detalhes = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para Procuração")
    
    # Tentar múltiplas alternativas para Etapa Comune
    etapa_comune = None
    # Campos mais prováveis para ETAPA COMUNE
    campos_comune = [
        'UF_CRM_1746045819198',   # ID informado pelo cliente
        'UF_CRM_1737823612831',   # Campo anterior
        'STAGE_ID',               # ID do estágio
        'STAGE_SEMANTIC_ID',      # Semântica do estágio
        'UF_CRM_1737561431'       # Possível campo de comune
    ]
    
    for campo in campos_comune:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            etapa_comune = familia_serie.get(campo)
            print(f"[DEBUG] Etapa Comune encontrada no campo '{campo}': {etapa_comune}")
            break
            
    if etapa_comune is None or etapa_comune == 'None':
        etapa_comune = 'N/D'
        print("[DEBUG] Nenhum valor encontrado para Etapa Comune")
    
    data_solicitacao_comune = familia_serie.get('UF_CRM_1737823552173', 'N/D')
    if data_solicitacao_comune is None or data_solicitacao_comune == 'None': data_solicitacao_comune = 'N/D'
    prazo_comune = familia_serie.get('UF_CRM_1746202791172', 'N/D')
    if prazo_comune is None or prazo_comune == 'None': prazo_comune = 'N/D'
    analise_doc = familia_serie.get('UF_CRM_1746045866262', 'N/D')
    if analise_doc is None or analise_doc == 'None': analise_doc = 'N/D'
    traducao = familia_serie.get('UF_CRM_1746045880601', 'N/D')
    if traducao is None or traducao == 'None': traducao = 'N/D'
    apostilamento = familia_serie.get('UF_CRM_1746045919198', 'N/D')
    if apostilamento is None or apostilamento == 'None': apostilamento = 'N/D'
    drive_link_raw = familia_serie.get('UF_CRM_DRIVE', 'N/D')
    drive_display = f"<a href='{drive_link_raw}' target='_blank' class='ficha-link'>Acessar Link</a>" if str(drive_link_raw).startswith('http') else str(drive_link_raw)
    qnt_familiares = familia_serie.get('UF_CRM_QUANTIDADE_FAMILIARES', 'N/D')
    if qnt_familiares is None or qnt_familiares == 'None': qnt_familiares = 'N/D'
    qnt_requerentes = familia_serie.get('UF_CRM_1743182118', 'N/D')
    if qnt_requerentes is None or qnt_requerentes == 'None': qnt_requerentes = 'N/D'
    emissoes_status_geral = familia_serie.get('UF_CRM_1746459875884', 'N/D')
    if emissoes_status_geral is None or emissoes_status_geral == 'None': emissoes_status_geral = 'N/D'

    # (Lógica de processamento de emissões, agora incluindo a posição na árvore)
    requerentes_data_list_of_dicts = []
    processamento_emissoes_ok = False
    # Mapa de documentos por (ID_Requerente, TipoCertidao) -> lista de links (Drive preferido primeiro)
    docs_map = {}
    try:
        id_familia_str_local = str(familia_serie.get('UF_CRM_1722605592778', '')).strip()
        if id_familia_str_local:
            df_docs_spa_local = carregar_dados_spa_scanner()
            if df_docs_spa_local is not None and not df_docs_spa_local.empty:
                df_docs_spa_local['UF_CRM_48_ID_FAMILIA'] = df_docs_spa_local['UF_CRM_48_ID_FAMILIA'].astype(str).str.strip()
                df_docs_spa_local['UF_CRM_48_ID_REQUERENTE'] = df_docs_spa_local['UF_CRM_48_ID_REQUERENTE'].astype(str).str.strip()
                docs_familia_local = df_docs_spa_local[df_docs_spa_local['UF_CRM_48_ID_FAMILIA'] == id_familia_str_local].copy()
                if not docs_familia_local.empty:
                    def _inferir_tipo_certidao_spa(titulo: str) -> str:
                        # Normaliza acentuação e caixa para evitar falsos positivos
                        t_norm = unidecode(str(titulo)).upper()
                        # Match exato prioritário
                        if 'CERTIDAO NASCIMENTO' in t_norm or 'NASCIMENTO' in t_norm:
                            return 'Nascimento'
                        if 'CERTIDAO CASAMENTO' in t_norm or 'MATRIMONIO' in t_norm or 'CASAMENTO' in t_norm:
                            return 'Casamento'
                        if 'CERTIDAO OBITO' in t_norm or 'OBITO' in t_norm or 'OBITO' in t_norm or 'OBIT' in t_norm:
                            return 'Óbito'
                        # Alguns títulos podem vir abreviados; fallback seguro
                        if 'NASC' in t_norm:
                            return 'Nascimento'
                        if 'CASA' in t_norm or 'MATRIM' in t_norm:
                            return 'Casamento'
                        if 'OBIT' in t_norm:
                            return 'Óbito'
                        return 'Outro'
                    docs_familia_local['__tipo__'] = docs_familia_local['TITLE'].apply(_inferir_tipo_certidao_spa)
                    for _i, r in docs_familia_local.iterrows():
                        req_id = str(r.get('UF_CRM_48_ID_REQUERENTE', '')).strip()
                        tipo = str(r.get('__tipo__', 'Outro'))
                        link_drive = str(r.get('UF_CRM_48_LINK_DRIVE', '')).strip()
                        link_scan = str(r.get('UF_CRM_48_DOCUMENTO_SCANEADO', '')).strip()
                        chosen_link = link_drive if link_drive.lower().startswith('http') else (link_scan if link_scan.lower().startswith('http') else '')
                        # Guardar um link por par (Requerente, Tipo). Não sobrescrever se já existir
                        if req_id and tipo in ['Nascimento', 'Casamento', 'Óbito'] and chosen_link:
                            chave_doc = (req_id, tipo)
                            if chave_doc not in docs_map:
                                docs_map[chave_doc] = []
                            if chosen_link not in docs_map[chave_doc]:
                                docs_map[chave_doc].append(chosen_link)
    except Exception as _e:
        print(f"[WARN] Falha ao montar docs_map SPA: {_e}")
    
    # NOVA LÓGICA: Função para determinar categoria baseada em Pipeline + Status
    # Esta correção resolve o problema de chaves duplicadas no mapeamento anterior
    def determinar_categoria_por_pipeline_status(category_id, stage_name_legivel):
            """Determina a categoria do resumo baseada no pipeline (CATEGORY_ID) e status (STAGE_NAME_LEGIVEL)"""
            category_id_str = str(category_id)
            status_upper = str(stage_name_legivel).upper() if pd.notna(stage_name_legivel) else ""
            
            # Pipeline 92 e 94 (Cartórios Casa Verde e Tatuapé)
            if category_id_str in ['92', '94']:
                if status_upper == "AGUARDANDO DECISÃO CLIENTE":
                    return "AGUARDANDO DECISÃO CLIENTE"
                if status_upper in ["AGUARDANDO CERTIDÃO", "BUSCA - CRC", "DEVOLUTIVA BUSCA - CRC", 
                                  "APENAS ASS. REQ CLIENTE P/MONTAGEM", "MONTAGEM REQUERIMENTO CARTÓRIO", 
                                  "SOLICITAR CARTÓRIO DE ORIGEM", "SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE", 
                                  "DEVOLUÇÃO ADM", "DEVOLVIDO REQUERIMENTO"] or "DEVOLUÇÃO ADM" in status_upper:
                    return "Brasileiras Pendências"
                elif status_upper == "PESQUISA - BR":
                    return "Brasileiras Pesquisas"
                elif status_upper == "AGUARDANDO CARTÓRIO ORIGEM":
                    return "Brasileiras Solicitadas"
                elif status_upper in ["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]:
                    return "Brasileiras Emitida"  # CORRIGIDO: Era "Pasta C/Emissão Concluída"
                elif status_upper in ["SOLICITAÇÃO DUPLICADA", "CANCELADO", "CERTIDÃO DISPENSADA"]:
                    return "Brasileiras Dispensada"  # Não contabilizada no resumo ativo
                    
            # Pipeline 102 (Paróquia)
            elif category_id_str == '102':
                if status_upper in ["SOLICITAR PARÓQUIA DE ORIGEM", "DEVOLUÇÃO ADM"] or "DEVOLUÇÃO ADM" in status_upper:
                    return "Paróquia Pendências"
                elif status_upper == "AGUARDANDO PARÓQUIA DE ORIGEM":
                    return "Paróquia Solicitadas"
                elif status_upper in ["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]:
                    return "Paróquia Emitida"  # CORRIGIDO: Consistente com a lógica
                elif status_upper in ["SOLICITAÇÃO DUPLICADA", "CANCELADO", "CERTIDÃO DISPENSADA"]:
                    return "Paróquia Dispensada"  # Não contabilizada no resumo ativo
                    
            # Pipeline 104 (Pesquisa BR)
            elif category_id_str == '104':
                if status_upper == "AGUARDANDO PESQUISADOR":
                    return "Pesquisa BR Pendências"
                elif status_upper == "PESQUISA EM ANDAMENTO":
                    return "Pesquisa BR Em Andamento"
                elif status_upper == "PESQUISA PRONTA PARA EMISSÃO":
                    return "Pesquisa BR Concluída"
                elif status_upper == "PESQUISA NÃO ENCONTRADA":
                    return "Pesquisa BR Não Encontrada"
            
            # Default para casos não mapeados
            return "Outros"

    pipeline_nome_map = {
        '92': 'Cartório 92',
        '94': 'Cartório 94',
        '102': 'Paróquia',
        '104': 'Pesquisa BR'
    }

    def obter_nome_pipeline_legivel(row: pd.Series) -> str:
        nome_pipeline = str(row.get('NOME_PIPELINE', '') or '').strip()
        if nome_pipeline:
            return nome_pipeline
        categoria_id_local = str(row.get('CATEGORY_ID', '') or '').strip()
        return pipeline_nome_map.get(categoria_id_local, f"Pipeline {categoria_id_local}" if categoria_id_local else '')

    if emissoes_df is not None and not emissoes_df.empty:
        col_stage_para_simplificar = None
        if 'STAGE_ID' in emissoes_df.columns: col_stage_para_simplificar = 'STAGE_ID'
        elif 'STAGE_NAME' in emissoes_df.columns: col_stage_para_simplificar = 'STAGE_NAME'
        if col_stage_para_simplificar:
            try:
                emissoes_df['STAGE_NAME_LEGIVEL'] = emissoes_df[col_stage_para_simplificar].apply(simplificar_nome_estagio)
                # Normalização para novo estágio: UC_PBAY8U -> [EM EXECUÇÃO]DEVOLUÇÃO ADM
                try:
                    mask_uc_pbay8u = pd.Series(False, index=emissoes_df.index)
                    if 'STAGE_ID' in emissoes_df.columns:
                        mask_uc_pbay8u = mask_uc_pbay8u | emissoes_df['STAGE_ID'].astype(str).str.upper().str.contains('UC_PBAY8U', na=False)
                    if 'STAGE_NAME' in emissoes_df.columns:
                        mask_uc_pbay8u = mask_uc_pbay8u | emissoes_df['STAGE_NAME'].astype(str).str.upper().str.contains('UC_PBAY8U', na=False)
                    emissoes_df.loc[mask_uc_pbay8u, 'STAGE_NAME_LEGIVEL'] = '[EM EXECUÇÃO]DEVOLUÇÃO ADM'
                except Exception:
                    pass
                processamento_emissoes_ok = True
                # DEBUG ADICIONADO
                print("\n[DEBUG ANTES DO LOOP DE REQUERENTES] Primeiras 20 linhas de emissoes_df com STAGE_NAME_LEGIVEL:")
                if not emissoes_df.empty and col_stage_para_simplificar in emissoes_df.columns :
                    print(emissoes_df[['TITLE', 'UF_CRM_34_TIPO_DE_CERTIDAO', col_stage_para_simplificar, 'STAGE_NAME_LEGIVEL']].head(20))
                else:
                    print("[DEBUG ANTES DO LOOP DE REQUERENTES] emissoes_df vazio ou coluna de stage ausente.")
            except Exception: emissoes_df['STAGE_NAME_LEGIVEL'] = emissoes_df[col_stage_para_simplificar]; processamento_emissoes_ok = True
        else: processamento_emissoes_ok = False
        if processamento_emissoes_ok:
            map_tipo_certidao = {'NASCIMENTO': 'Nascimento', 'CASAMENTO': 'Casamento', 'ÓBITO': 'Óbito'}
            # Adicionando UF_CRM_34_POSICAO_ARVORE à lista de colunas necessárias
            cols_req = ['UF_CRM_34_ID_REQUERENTE', 'TITLE', 'UF_CRM_34_TIPO_DE_CERTIDAO', 'STAGE_NAME_LEGIVEL', 'UF_CRM_34_POSICAO_ARVORE']
            
            # Verificamos se todas as colunas necessárias existem
            colunas_faltantes = [col for col in cols_req if col not in emissoes_df.columns]
            
            if colunas_faltantes:
                print(f"[AVISO] Colunas ausentes nos dados: {colunas_faltantes}")
                if 'UF_CRM_34_POSICAO_ARVORE' in colunas_faltantes:
                    # Criar coluna com valor padrão se ela estiver faltando
                    emissoes_df['UF_CRM_34_POSICAO_ARVORE'] = "N/D"
                    colunas_faltantes.remove('UF_CRM_34_POSICAO_ARVORE')
            
            if not colunas_faltantes:  # Se todas as colunas obrigatórias estiverem presentes
                col_id_requerente = cols_req[0]
                emissoes_df[col_id_requerente] = emissoes_df[col_id_requerente].fillna('').astype(str)

                valores_invalidos_id_norm = {
                    '', 'nan', 'none', 'null', 'n/d',
                    'id requerente n/d', 'id req. nao localizado', 'id req. nao localizados',
                    'id req. nao localizado.', 'id req. nao localizados.', 'id req. nao localizado)'
                }

                def _normalizar_id(valor: str) -> str:
                    texto = str(valor or '').strip()
                    texto_norm = unidecode(texto).lower()
                    return '' if texto_norm in valores_invalidos_id_norm else texto

                emissoes_df[col_id_requerente] = emissoes_df[col_id_requerente].apply(_normalizar_id)

                def _extrair_nome_limpo(titulo: str) -> str:
                    texto = str(titulo or '').strip()
                    if ' - ' in texto:
                        texto = texto.split(' - ', 1)[1]
                    texto = re.sub(r'\(.*?\)', '', texto)
                    return re.sub(r'\s+', ' ', texto).strip()

                emissoes_df['_NOME_LIMPO'] = emissoes_df['TITLE'].apply(_extrair_nome_limpo)

                emissoes_df['_ID_REQUERENTE_ORIGINAL'] = emissoes_df[col_id_requerente].apply(
                    lambda valor: valor if valor else 'ID Requerente N/D'
                )

                def _gerar_chave_sem_id(row) -> str:
                    nome_limpo = row.get('_NOME_LIMPO', '') or ''
                    posicao_val = str(row.get('UF_CRM_34_POSICAO_ARVORE', '') or '').strip()
                    partes = [unidecode(nome_limpo).upper()]
                    if posicao_val:
                        partes.append(unidecode(posicao_val).upper())
                    base = '_'.join(partes).strip('_')
                    base = re.sub(r'[^A-Z0-9]+', '_', base)
                    if not base:
                        base = f"REQUERENTE_{row.name}"
                    return f"SEM_ID::{base}"

                emissoes_df['_ID_REQUERENTE_GRUPO'] = emissoes_df['_ID_REQUERENTE_ORIGINAL']
                mask_sem_id = emissoes_df['_ID_REQUERENTE_ORIGINAL'] == 'ID Requerente N/D'
                emissoes_df.loc[mask_sem_id, '_ID_REQUERENTE_GRUPO'] = emissoes_df.loc[mask_sem_id].apply(_gerar_chave_sem_id, axis=1)

                emissoes_df[cols_req[1]] = emissoes_df[cols_req[1]].fillna('Nome N/D').astype(str)
                emissoes_df[cols_req[2]] = emissoes_df[cols_req[2]].fillna('Tipo N/D').astype(str)
                emissoes_df[cols_req[3]] = emissoes_df[cols_req[3]].fillna('Status N/D').astype(str)
                emissoes_df[cols_req[4]] = emissoes_df[cols_req[4]].fillna('Não informado').astype(str)

                grouped_by_requerente = emissoes_df.groupby('_ID_REQUERENTE_GRUPO', sort=False)
                if grouped_by_requerente.ngroups > 0:
                    for id_req_grupo, grupo in grouped_by_requerente:
                        id_req_original = grupo['_ID_REQUERENTE_ORIGINAL'].iloc[0] if '_ID_REQUERENTE_ORIGINAL' in grupo.columns else id_req_grupo
                        nome_req_bruto = ''
                        if '_NOME_LIMPO' in grupo.columns and grupo['_NOME_LIMPO'].iloc[0]:
                            nome_req_bruto = grupo['_NOME_LIMPO'].iloc[0]
                        elif not grupo[cols_req[1]].empty:
                            nome_req_bruto = grupo[cols_req[1]].iloc[0]
                        else:
                            nome_req_bruto = "Req. Desconhecido"

                        posicao_arvore = grupo[cols_req[4]].iloc[0] if not grupo[cols_req[4]].empty else "N/D"

                        if not id_req_original or id_req_original == 'ID Requerente N/D':
                            nome_req_bruto = nome_req_bruto or (grupo[cols_req[1]].iloc[0] if not grupo[cols_req[1]].empty else "Req. Desconhecido")

                        nome_limpo = str(nome_req_bruto)
                        prefixes_to_remove = ["NASCIMENTO - ", "CASAMENTO - ", "ÓBITO - "]
                        for prefix in prefixes_to_remove:
                            if nome_limpo.startswith(prefix):
                                nome_limpo = nome_limpo[len(prefix):]
                                break
                        nome_req_disp = nome_limpo.strip()

                        if not nome_req_disp:
                            nome_req_disp = "Requerente sem identificação"

                        cert_status = {v: 'Dispensado' for k, v in map_tipo_certidao.items() if v}
                        
                        # NOVA LÓGICA: Precedência de pipelines
                        # Se a pessoa tem "PESQUISA PRONTA PARA EMISSÃO" no pipeline 104,
                        # devemos verificar se ela tem registros nos pipelines superiores (92, 94, 102)
                        pipeline_104_pronto = False
                        registros_pipelines_superiores = []
                        
                        # Verificar se há registro no pipeline 104 com status "PESQUISA PRONTA PARA EMISSÃO"
                        for _, row in grupo.iterrows():
                            if 'CATEGORY_ID' in row and str(row['CATEGORY_ID']) == '104':
                                if row[cols_req[3]] == 'PESQUISA PRONTA PARA EMISSÃO':
                                    pipeline_104_pronto = True
                            elif 'CATEGORY_ID' in row and str(row['CATEGORY_ID']) in ['92', '94', '102']:
                                registros_pipelines_superiores.append(row)
                        
                        # Aplicar lógica de precedência
                        if pipeline_104_pronto and registros_pipelines_superiores:
                            # Se tem pipeline 104 pronto E registros nos superiores,
                            # processar apenas os registros dos pipelines superiores
                            print(f"[DEBUG PRECEDÊNCIA] ID_REQUERENTE {id_req_original}: Pipeline 104 pronto, usando status dos pipelines superiores")
                            for row in registros_pipelines_superiores:
                                tipo_l = map_tipo_certidao.get(str(row[cols_req[2]]).upper())
                                if tipo_l: 
                                    cert_status[tipo_l] = row[cols_req[3]] if cert_status[tipo_l] == 'Dispensado' or row[cols_req[3]] != 'Dispensado' else cert_status[tipo_l]
                        else:
                            # Lógica normal: processar todos os registros
                            for _, row in grupo.iterrows():
                                tipo_l = map_tipo_certidao.get(str(row[cols_req[2]]).upper())
                                if tipo_l: 
                                    cert_status[tipo_l] = row[cols_req[3]] if cert_status[tipo_l] == 'Dispensado' or row[cols_req[3]] != 'Dispensado' else cert_status[tipo_l]

                        # Incluir a posição na árvore nos dados a serem exibidos
                        requerentes_data_list_of_dicts.append({
                    'ID_Requerente': id_req_original,
                    'ID_Requerente_Grupo': id_req_grupo,
                            'Requerente': nome_req_disp,
                            'Posição': posicao_arvore,
                            **cert_status
                        })
                else: processamento_emissoes_ok = False
            else: processamento_emissoes_ok = False
    # (FIM DA LÓGICA DE PROCESSAMENTO DE EMISSÕES)

    # Ordenar requerentes_data_list_of_dicts por posição na ordem: ITALIANO, FAMILIAR, REQUERENTE
    if requerentes_data_list_of_dicts:
        def ordem_posicao(item):
            posicao = item.get('Posição', '').upper()
            if posicao == 'ITALIANO': return 1
            elif posicao in ['FAMILIAR', 'FAMILIA']: 
                item['Posição'] = 'FAMILIAR'
                return 2
            elif posicao == 'REQUERENTE': return 3
            else: return 4
        
        requerentes_data_list_of_dicts.sort(key=ordem_posicao)

    # --- Montar a Tabela HTML Única --- 
    html_ficha_completa += "<div class='ficha-secao dados-consolidado-tabela-secao'>"
    html_ficha_completa += "<table class='ficha-info-tabela' style='width:100%; border-collapse:collapse; border:1px solid #ddd;'>"
    
    td_style = "border:1px solid #ddd; padding:8px;"
    td_label_style = f"{td_style} color:#0070F2; font-weight:bold; width:20%;"
    td_data_style = f"{td_style} width:30%;"
    
    link_pasta_pronta = obter_url_card(familia_serie, tipo='pasta_pronta')
    link_pasta_pronta_display = (
        f"<a href='{link_pasta_pronta}' target='_blank' class='ficha-link'>Abrir card Pasta Pronta</a>"
        if link_pasta_pronta else 'N/D'
    )

    html_ficha_completa += f"<tr><td style='{td_label_style}'>Nome da Família:</td><td style='{td_data_style}'>{nome_familia}</td><td style='{td_label_style}'>ID da Família:</td><td style='{td_data_style}'>{id_familia}</td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Data de Venda:</td><td style='{td_data_style}'>{data_venda}</td><td style='{td_label_style}'>ADM Responsável:</td><td style='{td_data_style}'>{adm_responsavel}</td></tr>"

    dados_pdf['dados_basicos'] = [
        ("Nome da Família", nome_familia),
        ("ID da Família", id_familia),
        ("Data de Venda", data_venda),
        ("ADM Responsável", adm_responsavel),
        ("Link do Contrato", link_contrato_raw),
        ("Card Pasta Pronta", link_pasta_pronta or 'N/D'),
    ]
    dados_pdf['nome_familia'] = nome_familia
    dados_pdf['id_familia'] = id_familia

    html_ficha_completa += f"<tr><td style='{td_label_style}'>Link do Contrato:</td><td style='{td_data_style}'>{link_contrato_display}</td><td style='{td_label_style}'>Card Pasta Pronta:</td><td style='{td_data_style}'>{link_pasta_pronta_display}</td></tr>"

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>PROCURAÇÃO</h4></td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Detalhes Procuração:</td><td colspan='3' style='{td_style}'>{procuracao_detalhes}</td></tr>" 
    dados_pdf['sec_procuracao'] = [("Detalhes Procuração", procuracao_detalhes)]

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>COMUNE</h4></td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Etapa Comune:</td><td style='{td_data_style}'>{etapa_comune}</td><td style='{td_label_style}'>Data Solicitação Comune:</td><td style='{td_data_style}'>{data_solicitacao_comune}</td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Prazo Comune:</td><td style='{td_data_style}'>{prazo_comune}</td><td style='{td_label_style}'></td><td style='{td_data_style}'></td></tr>"
    dados_pdf['sec_comune'] = [
        ("Etapa Comune", etapa_comune),
        ("Data Solicitação Comune", data_solicitacao_comune),
        ("Prazo Comune", prazo_comune),
    ]

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>DOCUMENTAÇÃO E SERVIÇOS</h4></td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Análise Documental:</td><td style='{td_data_style}'>{analise_doc}</td><td style='{td_label_style}'>Tradução:</td><td style='{td_data_style}'>{traducao}</td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Apostilamento:</td><td style='{td_data_style}'>{apostilamento}</td><td style='{td_label_style}'>Drive:</td><td style='{td_data_style}'>{drive_display}</td></tr>"
    dados_pdf['sec_doc_serv'] = [
        ("Análise Documental", analise_doc),
        ("Tradução", traducao),
        ("Apostilamento", apostilamento),
        ("Drive", drive_link_raw),
    ]

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>DETALHES</h4></td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Qnt. Familiares:</td><td style='{td_data_style}'>{qnt_familiares}</td><td style='{td_label_style}'>Qnt. Requerentes:</td><td style='{td_data_style}'>{qnt_requerentes}</td></tr>"
    html_ficha_completa += f"<tr><td style='{td_label_style}'>Emissões (Status Geral):</td><td style='{td_data_style}'>{emissoes_status_geral}</td><td style='{td_label_style}'></td><td style='{td_data_style}'></td></tr>"
    dados_pdf['sec_detalhes'] = [
        ("Qnt. Familiares", qnt_familiares),
        ("Qnt. Requerentes", qnt_requerentes),
        ("Emissões (Status Geral)", emissoes_status_geral),
    ]

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>STATUS EMISSÕES BRASILEIRAS</h4></td></tr>"
    
    empty_cell_style = "text-align:center; border:1px solid #ddd; padding:8px; font-style:italic; color:#666;"
    
    if processamento_emissoes_ok and requerentes_data_list_of_dicts:
        html_ficha_completa += f"<tr><td colspan='4' style='padding:0; border:0;'>"
        html_ficha_completa += "<table style='width:100%; border-collapse:collapse; border:1px solid #ddd;'>"

        html_ficha_completa += "<tr class='emissoes-header-row'>"
        html_ficha_completa += "<th style='color:#0070F2; width:15%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Posição</th>"
        html_ficha_completa += "<th style='color:#0070F2; width:25%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Requerente</th>"
        html_ficha_completa += "<th style='color:#0070F2; width:20%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Nascimento</th>"
        html_ficha_completa += "<th style='color:#0070F2; width:20%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Casamento</th>"
        html_ficha_completa += "<th style='color:#0070F2; width:20%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Óbito</th>"
        html_ficha_completa += "</tr>"

        
        for req_data in requerentes_data_list_of_dicts:
            html_ficha_completa += "<tr class='emissoes-data-row'>"
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{req_data['Posição']}</td>"
            html_ficha_completa += f"<td style='text-align:left; border:1px solid #ddd; padding:8px;'>{req_data['Requerente']}</td>"
            # Células com cards informativos e links
            def _render_cell_with_eye(tipo_cert: str) -> str:
                nonlocal tabela_emissoes_css_injetado
                if not tabela_emissoes_css_injetado:
                    st.markdown(tabela_emissoes_css, unsafe_allow_html=True)
                    tabela_emissoes_css_injetado = True

                status_original = str(req_data.get(tipo_cert, '') or '')
                status_principal = html.escape(status_original)
                status_original_upper = status_original.upper()
                req_id_key = str(req_data.get('ID_Requerente', '')).strip()
                req_id_grupo = str(req_data.get('ID_Requerente_Grupo', '')).strip()
                chave_documento = req_id_key if req_id_key and req_id_key.upper() not in ['ID REQUERENTE N/D', ''] else req_id_grupo
                lista_links = docs_map.get((chave_documento, tipo_cert)) if chave_documento else None

                blocos_html = []
                tem_duplicados = False

                registros_cert = pd.DataFrame()
                if processamento_emissoes_ok:
                    chave_busca = req_id_key if req_id_key and req_id_key.upper() not in ['ID REQUERENTE N/D', ''] else req_id_grupo
                    if chave_busca:
                        registros_cert = emissoes_df[
                            emissoes_df['_ID_REQUERENTE_GRUPO'].astype(str) == chave_busca
                        ]
                        registros_cert = registros_cert[
                            registros_cert['UF_CRM_34_TIPO_DE_CERTIDAO'].astype(str).str.upper() == tipo_cert.upper()
                        ].copy()

                        if not registros_cert.empty:
                            registros_cert['__CARD_LINK__'] = registros_cert.apply(construir_link_card_pipeline, axis=1)

                if registros_cert is not None and not registros_cert.empty:
                    tem_duplicados = len(registros_cert) > 1
                    for _, reg_local in registros_cert.iterrows():
                        status_local_raw = reg_local.get('STAGE_NAME_LEGIVEL', status_original) or status_original
                        status_local = html.escape(str(status_local_raw))
                        pipeline_nome_raw = obter_nome_pipeline_legivel(reg_local)
                        pipeline_legivel = html.escape(pipeline_nome_raw) if pipeline_nome_raw else ''
                        stage_fallback_raw = reg_local.get('STAGE_NAME', '')
                        stage_fallback = html.escape(str(stage_fallback_raw)) if stage_fallback_raw else ''

                        link_buttons = []
                        link_card = reg_local.get('__CARD_LINK__')
                        if link_card:
                            link_buttons.append(
                                "<a class='cert-link-button cert-card-link' href='"
                                + html.escape(link_card, quote=True)
                                + "' target='_blank' title='Abrir card Bitrix'>"
                                "<span class='cert-link-icon'>🔗</span><span>Card</span></a>"
                            )

                        for link_individual in lista_links or []:
                            if link_individual:
                                link_buttons.append(
                                    "<a class='cert-link-button' href='"
                                    + html.escape(link_individual, quote=True)
                                    + "' target='_blank' title='Abrir documento'><span class='cert-link-icon'>📄</span><span>Documento</span></a>"
                                )
                        links_html = ''.join(link_buttons)

                        chips = []
                        if pipeline_legivel:
                            chips.append("<span class='cert-chip' style='--chip-bg: rgba(0, 150, 136, 0.15); --chip-color: #004D40;'>" + pipeline_legivel + "</span>")
                        elif stage_fallback:
                            chips.append("<span class='cert-chip'>" + stage_fallback + "</span>")
                        if tem_duplicados:
                            chips.append("<span class='cert-chip' style='--chip-bg: rgba(255, 152, 0, 0.18); --chip-color: #E65100;'>Duplicado</span>")
                        chips_html = ''.join(chips) or "<span class='cert-chip'>Sem pipeline</span>"

                        notas = []
                        if not links_html:
                            if lista_links:
                                notas.append("<div class='cert-note'>Links anexados não foram reconhecidos como URLs válidos.</div>")
                            else:
                                notas.append("<div class='cert-note'>Documento digital não vinculado na SPA para esta certidão.</div>")
                        if status_original_upper in ['CERTIDÃO DISPENSADA', 'CANCELADO', 'SOLICITAÇÃO DUPLICADA']:
                            notas.append("<div class='cert-note'>Certidão fora do escopo ativo.</div>")
                        note_html = ''.join(notas)

                        blocos_html.append(
                            "<div class='cert-card'>"
                            "<div class='cert-card-header'>"
                            f"<div class='cert-status-title'>{status_local}</div>"
                            f"<div class='cert-status-meta'>{chips_html}</div>"
                            "</div>"
                            f"<div class='cert-status-links'>{links_html}</div>"
                            f"{note_html}"
                            "</div>"
                        )
                else:
                    informacao_adicional = ''
                    if status_original_upper in ['CERTIDÃO DISPENSADA', 'CANCELADO', 'SOLICITAÇÃO DUPLICADA']:
                        informacao_adicional = "<div class='cert-note'>Certidão fora do escopo ativo.</div>"
                    elif not status_original or status_original_upper in ['DISPENSADO', 'N/D', 'STATUS N/D']:
                        informacao_adicional = "<div class='cert-note'>Sem atualizações registradas para esta certidão.</div>"
                    elif lista_links:
                        link_buttons = []
                        link_card_fallback = None
                        try:
                            if emissoes_df is not None and not emissoes_df.empty:
                                subset_card = emissoes_df[(emissoes_df['_ID_REQUERENTE_GRUPO'].astype(str) == chave_busca) &
                                                          (emissoes_df['UF_CRM_34_TIPO_DE_CERTIDAO'].astype(str).str.upper() == tipo_cert.upper())]
                                if not subset_card.empty:
                                    link_card_fallback = construir_link_card_pipeline(subset_card.iloc[0])
                        except Exception:
                            link_card_fallback = None

                        if link_card_fallback:
                            link_buttons.append(
                                "<a class='cert-link-button cert-card-link' href='"
                                + html.escape(link_card_fallback, quote=True)
                                + "' target='_blank' title='Abrir card Bitrix'>"
                                "<span class='cert-link-icon'>🔗</span><span>Card</span></a>"
                            )

                        for link_individual in lista_links:
                            if link_individual:
                                link_buttons.append(
                                    "<a class='cert-link-button' href='"
                                    + html.escape(link_individual, quote=True)
                                    + "' target='_blank' title='Abrir documento'><span class='cert-link-icon'>📄</span><span>Documento</span></a>"
                                )
                        links_html = ''.join(link_buttons)
                        informacao_adicional = "<div class='cert-note'>Documento digital disponível na SPA.</div>" if links_html else "<div class='cert-note'>Documento digital não encontrado na SPA.</div>"
                        blocos_html.append(
                            "<div class='cert-card'>"
                            f"<div class='cert-status-title'>{status_principal}</div>"
                            f"<div class='cert-status-links'>{links_html}</div>"
                            f"{informacao_adicional}"
                            "</div>"
                        )
                    else:
                        titulo_padrao = status_principal if status_principal else html.escape('Status não informado')
                        blocos_html.append(
                            "<div class='cert-card default-status'>"
                            f"<div class='cert-status-title'>{titulo_padrao}</div>"
                            f"{informacao_adicional}"
                            "</div>"
                        )

                wrapper_classes = "cert-status-wrapper" + (" duplicado" if tem_duplicados or len(blocos_html) > 1 else "")
                return f"<div class='{wrapper_classes}'>" + ''.join(blocos_html) + "</div>"

            nasc_html = _render_cell_with_eye('Nascimento')
            casa_html = _render_cell_with_eye('Casamento')
            obito_html = _render_cell_with_eye('Óbito')
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{nasc_html}</td>"
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{casa_html}</td>"
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{obito_html}</td>"
            html_ficha_completa += "</tr>"
        
    html_ficha_completa += "</table>"
    html_ficha_completa += "</td></tr>"

    # --- NOVA LÓGICA PARA POPULAR resumo_status_categorias --- 
    # 1. Definir df_emissoes_ativas (usando emissoes_df que é o df_emissoes_filtradas com STAGE_NAME_LEGIVEL)
    df_emissoes_ativas = pd.DataFrame()
    total_certidoes_reais_para_exibicao = 0

    if emissoes_df is not None and not emissoes_df.empty and 'STAGE_NAME_LEGIVEL' in emissoes_df.columns:
        status_de_dispensa_reais = ["SOLICITAÇÃO DUPLICADA", "CANCELADO"]  # Status que indicam dispensa real
        # Garante que estamos comparando strings com strings e lidando com NaNs em STAGE_NAME_LEGIVEL
        emissoes_df_valid_stages = emissoes_df[pd.notna(emissoes_df['STAGE_NAME_LEGIVEL'])].copy()
        emissoes_df_valid_stages['STAGE_NAME_LEGIVEL_UPPER'] = emissoes_df_valid_stages['STAGE_NAME_LEGIVEL'].astype(str).str.upper()

        df_emissoes_ativas = emissoes_df_valid_stages[
            ~emissoes_df_valid_stages['STAGE_NAME_LEGIVEL_UPPER'].isin(status_de_dispensa_reais)
        ].copy()
        total_certidoes_reais_para_exibicao = len(df_emissoes_ativas)

    elif emissoes_df is not None and not emissoes_df.empty:  # Fallback se STAGE_NAME_LEGIVEL não existir ou for problemático
        df_emissoes_ativas = emissoes_df.copy()
        total_certidoes_reais_para_exibicao = len(df_emissoes_ativas)

    # 2. Reinicializar e popular resumo_status_categorias com base em df_emissoes_ativas
    # Usando o map_stage_to_relatorio definido anteriormente
    # ATUALIZADO: Incluindo categorias dos novos pipelines 102 e 104
    resumo_status_categorias_temp = {  # Renomeado para evitar conflito de escopo se existir antes
            # Pipelines 92 e 94 (Cartórios)
            'Brasileiras Pendências': 0,
            'Brasileiras Pesquisas': 0,
            'Brasileiras Solicitadas': 0,
            'Brasileiras Emitida': 0,  # CORRIGIDO: Status direto de emissão
            'AGUARDANDO DECISÃO CLIENTE': 0,
            # Pipeline 102 (Paróquia)
            'Paróquia Pendências': 0,
            'Paróquia Solicitadas': 0,
            'Paróquia Emitida': 0,  # CORRIGIDO: Consistente com a lógica
            # Pipeline 104 (Pesquisa BR)
            'Pesquisa BR Pendências': 0,
            'Pesquisa BR Em Andamento': 0,
            'Pesquisa BR Concluída': 0,
            'Pesquisa BR Não Encontrada': 0,
            # 'Brasileiras Dispensada': 0, # Não incluímos aqui, pois df_emissoes_ativas já as exclui
            # 'Paróquia Dispensada': 0, # Não incluímos aqui, pois df_emissoes_ativas já as exclui
            'Outros': 0
        }

    if not df_emissoes_ativas.empty:
        # NOVA LÓGICA: Aplicar precedência de pipelines também no resumo
        # Criar DataFrame para processar precedência
        df_processado = df_emissoes_ativas.copy()
        
        # Identificar pessoas que têm "PESQUISA PRONTA PARA EMISSÃO" no pipeline 104
        # e também têm registros nos pipelines superiores (92, 94, 102)
        if 'UF_CRM_34_ID_REQUERENTE' in df_processado.columns and 'CATEGORY_ID' in df_processado.columns:
            # Agrupar por ID_REQUERENTE para aplicar a lógica de precedência
            requerentes_para_remover_104 = []
            
            for id_requerente, grupo_req in df_processado.groupby('UF_CRM_34_ID_REQUERENTE'):
                # Verificar se tem pipeline 104 com "PESQUISA PRONTA PARA EMISSÃO"
                tem_104_pronto = False
                tem_pipelines_superiores = False
                
                for _, row in grupo_req.iterrows():
                    if str(row['CATEGORY_ID']) == '104' and row['STAGE_NAME_LEGIVEL'] == 'PESQUISA PRONTA PARA EMISSÃO':
                        tem_104_pronto = True
                    elif str(row['CATEGORY_ID']) in ['92', '94', '102']:
                        tem_pipelines_superiores = True
                
                # Se tem 104 pronto E pipelines superiores, remover registros do 104 do resumo
                if tem_104_pronto and tem_pipelines_superiores:
                    requerentes_para_remover_104.append(id_requerente)
                    print(f"[DEBUG PRECEDÊNCIA RESUMO] ID_REQUERENTE {id_requerente}: Removendo pipeline 104 do resumo (precedência)")
            
            # Remover registros do pipeline 104 para os requerentes identificados
            if requerentes_para_remover_104:
                mask_remover = (df_processado['UF_CRM_34_ID_REQUERENTE'].isin(requerentes_para_remover_104)) & (df_processado['CATEGORY_ID'].astype(str) == '104')
                df_processado = df_processado[~mask_remover].copy()
                print(f"[DEBUG PRECEDÊNCIA RESUMO] Removidos {mask_remover.sum()} registros do pipeline 104 devido à precedência")
        
        # Continuar com a lógica normal de resumo usando df_processado
        for _idx, certidao_ativa_row in df_processado.iterrows():
            status_legivel = certidao_ativa_row['STAGE_NAME_LEGIVEL']
            category_id = certidao_ativa_row.get('CATEGORY_ID', '')

            if pd.isna(status_legivel) or (isinstance(status_legivel, str) and not status_legivel.strip()):
                continue

            categoria_para_resumo = determinar_categoria_por_pipeline_status(category_id, status_legivel)

            if categoria_para_resumo.endswith("Dispensada"):
                continue

            if categoria_para_resumo in resumo_status_categorias_temp:
                resumo_status_categorias_temp[categoria_para_resumo] += 1
            else:
                resumo_status_categorias_temp['Outros'] += 1

            total_certidoes_reais_para_exibicao += 1
        
        # Atualizar total com o DataFrame processado
        total_certidoes_reais_para_exibicao = len(df_processado)
        
        # ADICIONAR LÓGICA DE "Pasta C/Emissão Concluída" (métrica derivada)
        # Calcular se a família tem TODAS as certidões ativas como "Brasileiras Emitida"
        total_ativas = (resumo_status_categorias_temp['Brasileiras Pendências'] + 
                       resumo_status_categorias_temp['Brasileiras Pesquisas'] + 
                       resumo_status_categorias_temp['Brasileiras Solicitadas'] + 
                       resumo_status_categorias_temp['Brasileiras Emitida'] +
                       resumo_status_categorias_temp.get('AGUARDANDO DECISÃO CLIENTE', 0))
        
        if total_ativas > 0 and total_ativas == resumo_status_categorias_temp['Brasileiras Emitida']:
            resumo_status_categorias_temp['Pasta C/Emissão Concluída'] = 1
        else:
            resumo_status_categorias_temp['Pasta C/Emissão Concluída'] = 0
    
    # Atribuir o resultado calculado ao nome da variável que o HTML do resumo espera
    resumo_status_categorias = resumo_status_categorias_temp
    # --- FIM DA NOVA LÓGICA --- 

    html_ficha_completa += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#e0e0e0; border:1px solid #ddd; padding:8px;'><h4 class='ficha-sub-titulo titulo-secao-ficha' style='color:#0070F2; text-align:center; margin:5px 0;'>RESUMO EMISSÕES</h4></td></tr>"

    
    html_ficha_completa += f"<tr><td colspan='4' style='padding:0; border:0;'>"
    html_ficha_completa += "<table style='width:100%; border-collapse:collapse; border:1px solid #ddd;'>"
    
    html_ficha_completa += "<tr class='resumo-header-row'>"
    html_ficha_completa += "<th style='color:#0070F2; width:30%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Status</th>"
    html_ficha_completa += "<th style='color:#0070F2; width:20%; text-align:center; border:1px solid #ddd; padding:8px; background-color:#f5f5f5;'>Quantidade</th>"
    html_ficha_completa += "</tr>"
    
    for status, quantidade in resumo_status_categorias.items():
        if quantidade > 0 or status == 'Outros': 
            html_ficha_completa += "<tr class='resumo-data-row'>"
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px; font-weight:bold;'>{status}</td>"
            html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px;'>{quantidade}</td>"
            html_ficha_completa += "</tr>"
    
    html_ficha_completa += "<tr class='resumo-total-row' style='background-color:#f0f0f0;'>"
    html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px; font-weight:bold;'>TOTAL</td>"
    html_ficha_completa += f"<td style='text-align:center; border:1px solid #ddd; padding:8px; font-weight:bold;'>{total_certidoes_reais_para_exibicao}</td>"
    html_ficha_completa += "</tr>"
    
    html_ficha_completa += "</table>"
    html_ficha_completa += "</td></tr>"
    
    # Adicionar linha para o botão de download abaixo do resumo
    html_ficha_completa += "<tr><td colspan='4' style='border:1px solid #ddd; padding:8px; text-align:right;'>"
    html_ficha_completa += "<div class='resumo-emissoes-download'></div>"
    html_ficha_completa += "</td></tr>"
    
    if df_emissoes_ativas.empty and emissoes_df is not None and not emissoes_df.empty:
        html_ficha_completa += f"<tr><td colspan='4' style='{empty_cell_style}'>Aviso: Não foi possível processar os detalhes das emissões.</td></tr>"
    elif df_emissoes_ativas.empty:
        html_ficha_completa += f"<tr><td colspan='4' style='{empty_cell_style}'>Nenhuma emissão detalhada encontrada para esta família.</td></tr>"

    html_ficha_completa += "</table>"
    html_ficha_completa += "</div>" # Fecha dados-consolidado-tabela-secao
    html_ficha_completa += "</div>" # Fecha ficha-familia-container

    if emissoes_df is not None and not emissoes_df.empty and processamento_emissoes_ok:
        dados_pdf['resumo'] = dict(resumo_status_categorias)
        dados_pdf['total_certidoes'] = total_certidoes_reais_para_exibicao
    else:
        dados_pdf['resumo'] = {}
        dados_pdf['total_certidoes'] = 0

    st.session_state['ficha_pdf_context'] = dados_pdf

    # Para garantir que a ficha ocupe todo o espaço disponível,
    # vamos incluir CSS adicional diretamente na página
    css_fullwidth = '''
    <style>
    .ficha-familia-container {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        padding: 20px !important;
    }
    /* Tentativa de forçar o container pai do Streamlit a ter largura total */
    div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        flex: 0 1 100% !important;
    }
    </style>
    '''
    
    # Primeiro injetamos o CSS, depois o HTML da ficha
    st.markdown(css_fullwidth, unsafe_allow_html=True)
    st.markdown(html_ficha_completa, unsafe_allow_html=True)
    
    # ==========================
    # BOTÃO DE DOWNLOAD DA FICHA EM PDF
    # ==========================
    try:
        # Gerar o PDF da ficha completa
        context_pdf = st.session_state.get('ficha_pdf_context')
        if context_pdf:
            pdf_bytes = gerar_pdf_ficha(context_pdf)
            
            # Nome do arquivo
            nome_familia = familia_serie.get('TITLE', 'Família')
            id_familia_val = familia_serie.get('UF_CRM_1722605592778', '')
            nome_arquivo_pdf = _montar_nome_arquivo_pdf(nome_familia, str(id_familia_val))
            
            # Criar botão de download do PDF
            st.download_button(
                label="📄 Baixar Ficha Completa (PDF)",
                data=pdf_bytes,
                file_name=nome_arquivo_pdf,
                mime="application/pdf",
                key=f"download_ficha_pdf_{familia_serie.get('ID', 'familia')}",
                use_container_width=True
            )
    except Exception as e:
        st.warning(f"Não foi possível gerar o PDF da ficha. Erro: {str(e)}")
        # Fallback: oferecer download em CSV do resumo
        if 'resumo_status_categorias' in locals() and resumo_status_categorias:
            import io
            csv_buffer = io.StringIO()
            csv_buffer.write("Status,Quantidade\n")
            for status, quantidade in resumo_status_categorias.items():
                if quantidade > 0 or status == 'Outros':
                    csv_buffer.write(f'"{status}",{quantidade}\n')
            csv_buffer.write(f'"TOTAL",{total_certidoes_reais_para_exibicao}\n')
            csv_data = csv_buffer.getvalue()
            
            nome_arquivo = f"Resumo_Emissoes_{nome_familia.replace(' ', '_')}.csv"
            st.download_button(
                label="📥 Baixar Resumo de Emissões (CSV)",
                data=csv_data,
                file_name=nome_arquivo,
                mime="text/csv",
                key=f"download_resumo_{familia_serie.get('ID', 'familia')}"
            )

    # ==========================
    # DOCUMENTOS (SPA 1132) - Links Drive
    # ==========================
    try:
        id_familia_str = str(familia_serie.get('UF_CRM_1722605592778', '')).strip()
        if id_familia_str and id_familia_str.upper() not in ['N/D', 'NONE', 'NAN', '']:
            st.markdown("---")
            st.markdown("#### Documentos (SPA - Scanner)")

            df_docs_spa = carregar_dados_spa_scanner()
            if df_docs_spa is not None and not df_docs_spa.empty:
                df_docs_spa['UF_CRM_48_ID_FAMILIA'] = df_docs_spa['UF_CRM_48_ID_FAMILIA'].astype(str).str.strip()
                docs_familia = df_docs_spa[df_docs_spa['UF_CRM_48_ID_FAMILIA'] == id_familia_str].copy()

                if not docs_familia.empty:
                    # Inferir tipo de certidão a partir do TITLE
                    def inferir_tipo_certidao(titulo: str) -> str:
                        t_norm = unidecode(str(titulo)).upper()
                        if 'CERTIDAO NASCIMENTO' in t_norm or 'NASCIMENTO' in t_norm or 'NASC' in t_norm:
                            return 'Nascimento'
                        if 'CERTIDAO CASAMENTO' in t_norm or 'MATRIMONIO' in t_norm or 'CASAMENTO' in t_norm or 'MATRIM' in t_norm or 'CASA' in t_norm:
                            return 'Casamento'
                        if 'CERTIDAO OBITO' in t_norm or 'OBITO' in t_norm or 'OBIT' in t_norm or 'OBITO' in t_norm:
                            return 'Óbito'
                        return 'Outro'

                    docs_familia['Certidão'] = docs_familia['TITLE'].apply(inferir_tipo_certidao)

                    # Selecionar link do Drive preferencialmente
                    def escolher_link(row):
                        link_drive = str(row.get('UF_CRM_48_LINK_DRIVE', '')).strip()
                        link_scan = str(row.get('UF_CRM_48_DOCUMENTO_SCANEADO', '')).strip()
                        return link_drive if link_drive.lower().startswith('http') else (link_scan if link_scan.lower().startswith('http') else '')

                    docs_familia['Link'] = docs_familia.apply(escolher_link, axis=1)

                    # Agrupar por Requerente e exibir como "pastas" (expanders)
                    id_to_name = {}
                    try:
                        if isinstance(requerentes_data_list_of_dicts, list):
                            for it in requerentes_data_list_of_dicts:
                                _id = str(it.get('ID_Requerente', '')).strip()
                                _nm = str(it.get('Requerente', '')).strip()
                                if _id and _id != 'ID Requerente N/D':
                                    id_to_name[_id] = _nm
                    except Exception:
                        id_to_name = {}

                    # Ordenar por nome do requerente quando possível
                    try:
                        docs_familia['_req_name'] = docs_familia['UF_CRM_48_ID_REQUERENTE'].map(id_to_name).fillna('')
                    except Exception:
                        docs_familia['_req_name'] = ''

                    for req_id, g in docs_familia.groupby('UF_CRM_48_ID_REQUERENTE'):
                        req_id_str = str(req_id)
                        display_name = id_to_name.get(req_id_str, f"Requerente {req_id_str}")
                        qtd = int(len(g))
                        with st.expander(f"{display_name} — {qtd} documento(s)", expanded=False):
                            # Ordenar documentos por tipo e título
                            g_sorted = g.sort_values(by=['Certidão', 'TITLE'], kind='stable')
                            for _i, r in g_sorted.iterrows():
                                url = str(r.get('Link', '')).strip()
                                cert = str(r.get('Certidão', 'Documento'))
                                titulo = str(r.get('TITLE', 'Documento'))
                                if url:
                                    st.markdown(f"- {cert} • {titulo} — <a href='{url}' target='_blank'>abrir</a>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"- {cert} • {titulo} — sem link disponível")
                else:
                    st.info("Nenhum documento encontrado na SPA para esta família.")
            else:
                st.info("Não foi possível carregar dados da SPA de documentos.")
    except Exception as e:
        st.warning(f"Falha ao processar documentos da SPA: {e}")

    dados_pdf['requerentes'] = [
        {
            'Posição': item.get('Posição', 'N/D'),
            'Requerente': item.get('Requerente', 'N/D'),
            'Nascimento': item.get('Nascimento', 'N/D'),
            'Casamento': item.get('Casamento', 'N/D'),
            'Óbito': item.get('Óbito', 'N/D'),
        }
        for item in requerentes_data_list_of_dicts
    ]

def exibir_metricas_macro():
    # ============================
    # STATUS DE PROTOCOLO (GERAL)
    # ============================
    try:
        df_crm_deals_full_local = load_crm_deal_data(category_id=46)
    except Exception:
        df_crm_deals_full_local = pd.DataFrame()

    st.markdown("#### STATUS FAMILIAS")
    
    total_familias_f46 = 0
    familias_concluidas_protocolo = 0
    familias_andamento_protocolo = 0

    try:
        if df_crm_deals_full_local is not None and not df_crm_deals_full_local.empty:
            col_id_familia = 'UF_CRM_1722605592778'
            col_stage = 'STAGE_ID'
            if col_id_familia in df_crm_deals_full_local.columns:
                df_f46 = df_crm_deals_full_local[[c for c in [col_id_familia, col_stage, 'STAGE_NAME', 'STAGE_SEMANTIC_ID'] if c in df_crm_deals_full_local.columns]].copy()
                df_f46[col_id_familia] = df_f46[col_id_familia].astype(str).str.strip()
                ids_f46 = df_f46[col_id_familia].replace('', pd.NA).dropna().unique().tolist()
                total_familias_f46 = len(ids_f46)

                codigos_por_etapa_pp = {
                    'EMISSÃO BRASILEIRA': {'UC_8Z2EZF'},
                    'ANÁLISE DOCUMENTAL': {'UC_N1FI74', 'UC_SKSQFO', 'UC_K952AX', 'UC_2JQ8E2R'},
                    'TRADUÇÃO': {'UC_CSFCZP'},
                    'APOSTILAMENTO': {'UC_F12U3R'},
                    'DRIVE': {'UC_1ARFYMM'},
                    'RECURSO': {'UC_SISEKVR'},
                    'PROTOCOLO': {'UC_5W7TYZ'},
                }
                ordem_por_etapa_pp = {
                    'EMISSÃO BRASILEIRA': 70,
                    'ANÁLISE DOCUMENTAL': 90,
                    'TRADUÇÃO': 130,
                    'APOSTILAMENTO': 140,
                    'DRIVE': 150,
                    'RECURSO': 160,
                    'PROTOCOLO': 170,
                }

                def calcular_maior_ordem_para_grupo(stages_df: pd.DataFrame) -> int:
                    if stages_df is None or stages_df.empty:
                        return 0
                    maior = 0
                    try:
                        if 'STAGE_SEMANTIC_ID' in stages_df.columns:
                            semanticas = stages_df['STAGE_SEMANTIC_ID'].dropna().astype(str).str.upper().tolist()
                            if any(s in ['S', 'SUCCESS', 'WON'] for s in semanticas):
                                maior = max(maior, ordem_por_etapa_pp.get('PROTOCOLO', 170))
                    except Exception:
                        pass
                    valores_id = []
                    valores_nome = []
                    try:
                        if 'STAGE_ID' in stages_df.columns:
                            valores_id = stages_df['STAGE_ID'].dropna().astype(str).tolist()
                    except Exception:
                        valores_id = []
                    try:
                        if 'STAGE_NAME' in stages_df.columns:
                            valores_nome = stages_df['STAGE_NAME'].dropna().astype(str).tolist()
                    except Exception:
                        valores_nome = []
                    tokens = [unidecode(v).upper() for v in (valores_id + valores_nome)]
                    for etapa, codigos in codigos_por_etapa_pp.items():
                        for codigo in codigos:
                            if any(codigo in t for t in tokens):
                                maior = max(maior, ordem_por_etapa_pp.get(etapa, 0))
                    stage_keywords = {
                        'PROTOCOLO': ['PROTOCOLO', 'WON', 'SUCCESS'],
                        'RECURSO': ['RECURSO'],
                        'DRIVE': ['DRIVE'],
                        'APOSTILAMENTO': ['APOSTILAMENTO', 'APOSTILA'],
                        'TRADUÇÃO': ['TRADUCAO', 'TRADU', 'TRADUÇÃO'],
                        'ANÁLISE DOCUMENTAL': ['ANALISE DOCUMENTAL', 'ANALISE', 'ANÁLISE DOCUMENTAL'],
                        'EMISSÃO BRASILEIRA': ['EMISSAO', 'EMISSÃO', 'EMISSAO BRASILEIRA', 'EMISSÃO BRASILEIRA']
                    }
                    for etapa, keywords in stage_keywords.items():
                        if any(any(kw in t for kw in keywords) for t in tokens):
                            maior = max(maior, ordem_por_etapa_pp.get(etapa, 0))
                    return maior

                maiores = []
                for fam_id, g in df_f46.groupby(col_id_familia):
                    cols_grp = [c for c in [col_stage, 'STAGE_NAME', 'STAGE_SEMANTIC_ID'] if c in g.columns]
                    maior = calcular_maior_ordem_para_grupo(g[cols_grp] if cols_grp else pd.DataFrame())
                    maiores.append(maior)
                familias_concluidas_protocolo = sum(1 for m in maiores if m >= 170)
                familias_andamento_protocolo = max(0, total_familias_f46 - familias_concluidas_protocolo)
    except Exception:
        pass

    st.markdown("""
    <style>
    .metricas-container-pp { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0 4px 0; }
    .metrica-custom-pp { background: #F8F9FA; border: 2px solid #DEE2E6; border-radius: 6px; padding: 16px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metrica-custom-pp:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: #ADB5BD; }
    .metrica-custom-pp .label { color: #6C757D; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; line-height: 1.2; }
    .metrica-custom-pp .valor { color: #495057; font-weight: 700; font-size: 30px; line-height: 1.2; margin-bottom: 4px; }
    </style>
    <div class="metricas-container-pp">
        <div class="metrica-custom-pp"><div class="label">Total de Famílias</div><div class="valor">""" + str(int(total_familias_f46)) + """</div></div>
        <div class="metrica-custom-pp"><div class="label">Em Andamento (não protocolado)</div><div class="valor">""" + str(int(familias_andamento_protocolo)) + """</div></div>
        <div class="metrica-custom-pp"><div class="label">Concluídas (protocolado)</div><div class="valor">""" + str(int(familias_concluidas_protocolo)) + """</div></div>
    </div>
    """, unsafe_allow_html=True)

    def _status_protocolo_por_familia_geral(df_cat46: pd.DataFrame) -> pd.DataFrame:
        if df_cat46 is None or df_cat46.empty:
            return pd.DataFrame()

        col_nome = 'UF_CRM_1722883482527'
        col_id_familia = 'UF_CRM_1722605592778'
        col_stage = 'STAGE_ID'

        for c in [col_nome, col_id_familia, col_stage]:
            if c not in df_cat46.columns:
                df_cat46[c] = None

        codigos_por_etapa = {
            'EMISSÃO BRASILEIRA': {'UC_8Z2EZF'},
            'ANÁLISE DOCUMENTAL': {'UC_N1FI74', 'UC_SKSQFO', 'UC_K952AX', 'UC_2JQ8E2R'},
            'TRADUÇÃO': {'UC_CSFCZP'},
            'APOSTILAMENTO': {'UC_F12U3R'},
            'DRIVE': {'UC_1ARFYMM'},
            'RECURSO': {'UC_SISEKVR'},
            'PROTOCOLO': {'UC_5W7TYZ'},
        }

        ordem_por_etapa = {
            'EMISSÃO BRASILEIRA': 70,
            'ANÁLISE DOCUMENTAL': 90,
            'TRADUÇÃO': 130,
            'APOSTILAMENTO': 140,
            'DRIVE': 150,
            'RECURSO': 160,
            'PROTOCOLO': 170,
        }

        def calcular_maior_ordem_para_grupo_detalhe(stages_df: pd.DataFrame) -> int:
            if stages_df is None or stages_df.empty:
                return 0
            maior = 0
            try:
                if 'STAGE_SEMANTIC_ID' in stages_df.columns:
                    semanticas = stages_df['STAGE_SEMANTIC_ID'].dropna().astype(str).str.upper().tolist()
                    if any(s in ['S', 'SUCCESS', 'WON'] for s in semanticas):
                        maior = max(maior, ordem_por_etapa.get('PROTOCOLO', 170))
            except Exception:
                pass
            valores_id = []
            valores_nome = []
            try:
                if 'STAGE_ID' in stages_df.columns:
                    valores_id = stages_df['STAGE_ID'].dropna().astype(str).tolist()
            except Exception:
                valores_id = []
            try:
                if 'STAGE_NAME' in stages_df.columns:
                    valores_nome = stages_df['STAGE_NAME'].dropna().astype(str).tolist()
            except Exception:
                valores_nome = []
            tokens = [unidecode(v).upper() for v in (valores_id + valores_nome)]
            for etapa, codigos in codigos_por_etapa.items():
                for codigo in codigos:
                    if any(codigo in t for t in tokens):
                        maior = max(maior, ordem_por_etapa.get(etapa, 0))
            stage_keywords = {
                'PROTOCOLO': ['PROTOCOLO', 'WON', 'SUCCESS'],
                'RECURSO': ['RECURSO'],
                'DRIVE': ['DRIVE'],
                'APOSTILAMENTO': ['APOSTILAMENTO', 'APOSTILA'],
                'TRADUÇÃO': ['TRADUCAO', 'TRADU', 'TRADUÇÃO'],
                'ANÁLISE DOCUMENTAL': ['ANALISE DOCUMENTAL', 'ANALISE', 'ANÁLISE DOCUMENTAL'],
                'EMISSÃO BRASILEIRA': ['EMISSAO', 'EMISSÃO', 'EMISSAO BRASILEIRA', 'EMISSÃO BRASILEIRA']
            }
            for etapa, keywords in stage_keywords.items():
                if any(any(kw in t for kw in keywords) for t in tokens):
                    maior = max(maior, ordem_por_etapa.get(etapa, 0))
            return maior

        grupo_cols = [c for c in [col_nome, col_id_familia] if c in df_cat46.columns]
        if not grupo_cols:
            return pd.DataFrame()

        registros = []
        for chave, g in df_cat46.groupby(grupo_cols):
            if isinstance(chave, tuple):
                nome_fam, id_fam = chave[0], chave[1]
            else:
                nome_fam, id_fam = chave, ''

            cols_grp = [c for c in [col_stage, 'STAGE_NAME', 'STAGE_SEMANTIC_ID'] if c in g.columns]
            maior_ordem = calcular_maior_ordem_para_grupo_detalhe(g[cols_grp] if cols_grp else pd.DataFrame())
            etapas_status = {}
            for etapa, ordem in ordem_por_etapa.items():
                etapas_status[etapa] = '✅' if maior_ordem >= ordem else ''

            registros.append({
                'Nome da Família': str(nome_fam) if nome_fam is not None else '',
                'ID da Família': str(id_fam) if id_fam is not None else '',
                **etapas_status,
                '__ORDEM_MAX__': maior_ordem,
            })

        df_out = pd.DataFrame(registros)
        if not df_out.empty:
            df_out = df_out.sort_values(by='__ORDEM_MAX__', ascending=False, kind='stable').drop(columns=['__ORDEM_MAX__'])

        colunas_ordenadas = [
            'Nome da Família', 'ID da Família',
            'EMISSÃO BRASILEIRA', 'ANÁLISE DOCUMENTAL', 'TRADUÇÃO', 'APOSTILAMENTO', 'DRIVE', 'RECURSO', 'PROTOCOLO'
        ]
        presentes = [c for c in colunas_ordenadas if c in df_out.columns]
        if presentes:
            df_out = df_out[presentes]
        return df_out

    st.markdown("---")
    st.markdown("#### STATUS FAMÍLIAS")
    st.caption("Etapas concluídas até o protocolo para todas as famílias do funil 46.")

    try:
        df_status_geral = _status_protocolo_por_familia_geral(df_crm_deals_full_local)
    except Exception as e:
        df_status_geral = pd.DataFrame()
        st.warning(f"Falha ao montar STATUS DE PROTOCOLO (Geral): {e}")

    if df_status_geral is None or df_status_geral.empty:
        st.info("Nenhuma informação de protocolo encontrada.")
    else:
        st.dataframe(
            ensure_pandas_df(df_status_geral),
            hide_index=True,
            use_container_width=True,
            column_config={
                'Nome da Família': st.column_config.TextColumn('Nome da Família', width='large'),
                'ID da Família': st.column_config.TextColumn('ID da Família', width='medium'),
                'EMISSÃO BRASILEIRA': st.column_config.TextColumn('EMISSÃO BRASILEIRA', width='small'),
                'ANÁLISE DOCUMENTAL': st.column_config.TextColumn('ANÁLISE DOCUMENTAL', width='small'),
                'TRADUÇÃO': st.column_config.TextColumn('TRADUÇÃO', width='small'),
                'APOSTILAMENTO': st.column_config.TextColumn('APOSTILAMENTO', width='small'),
                'DRIVE': st.column_config.TextColumn('DRIVE', width='small'),
                'RECURSO': st.column_config.TextColumn('RECURSO', width='small'),
                'PROTOCOLO': st.column_config.TextColumn('PROTOCOLO', width='small'),
            }
        )

    

    # ============================
    # ACOMPANHAMENTO GERAL (todas as famílias)
    # ============================
    st.markdown("---")
    st.markdown("#### ACOMPANHAMENTO EMISSÕES BRASILEIRAS FAMÍLIAS")

    with st.spinner("Carregando dados do SPA..."):
        try:
            df_cartorio_all = carregar_dados_cartorio()
        except Exception:
            df_cartorio_all = pd.DataFrame()

    col_id_familia_spa = 'UF_CRM_34_ID_FAMILIA'
    col_nome_familia_spa = 'UF_CRM_34_NOME_FAMILIA'
    col_resp_spa = 'ASSIGNED_BY_NAME'

    if df_cartorio_all is None or df_cartorio_all.empty or col_id_familia_spa not in df_cartorio_all.columns:
        st.info("Sem dados suficientes para o acompanhamento geral.")
        return

    df_spa_base = df_cartorio_all[[c for c in [col_id_familia_spa, 'STAGE_ID', 'STAGE_NAME', col_nome_familia_spa, col_resp_spa] if c in df_cartorio_all.columns]].copy()
    success_mask = pd.Series(False, index=df_spa_base.index)
    if 'STAGE_ID' in df_spa_base.columns:
        success_mask = success_mask | df_spa_base['STAGE_ID'].astype(str).str.contains('SUCCESS', na=False)
    if 'STAGE_NAME' in df_spa_base.columns:
        success_mask = success_mask | df_spa_base['STAGE_NAME'].astype(str).str.upper().isin(['CERTIDÃO EMITIDA', 'CERTIDÃO ENTREGUE'])
    df_spa_base['__success__'] = success_mask.astype(int)

    fam_metrics = df_spa_base.groupby(col_id_familia_spa).agg(
        total_itens=('__success__', 'count'),
        concluidas=('__success__', 'sum')
    ).reset_index()

    # KPIs
    total_familias = fam_metrics[col_id_familia_spa].nunique()
    fam_concluidas = fam_metrics[(fam_metrics['total_itens'] > 0) & (fam_metrics['concluidas'] == fam_metrics['total_itens'])]
    familias_concluidas_count = int(len(fam_concluidas))
    fam_andamento = fam_metrics[(fam_metrics['total_itens'] > 0) & (fam_metrics['concluidas'] < fam_metrics['total_itens'])]
    familias_andamento_count = int(len(fam_andamento))
    st.markdown("""
    <style>
    .metricas-container-geral { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0 4px 0; }
    .metrica-custom-geral { background: #F8F9FA; border: 2px solid #DEE2E6; border-radius: 6px; padding: 16px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metrica-custom-geral:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: #ADB5BD; }
    .metrica-custom-geral .label { color: #6C757D; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; line-height: 1.2; }
    .metrica-custom-geral .valor { color: #495057; font-weight: 700; font-size: 30px; line-height: 1.2; margin-bottom: 4px; }
    </style>
    <div class="metricas-container-geral">
        <div class="metrica-custom-geral"><div class="label">Total Famílias no Funil</div><div class="valor">""" + str(int(total_familias)) + """</div></div>
        <div class="metrica-custom-geral"><div class="label">Em Andamento</div><div class="valor">""" + str(int(familias_andamento_count)) + """</div></div>
        <div class="metrica-custom-geral"><div class="label">Concluídas</div><div class="valor">""" + str(int(familias_concluidas_count)) + """</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Tabela de Progresso (todas as famílias)
    nome_por_id = pd.Series(dtype=object)
    if col_nome_familia_spa in df_spa_base.columns:
        nome_por_id = (
            df_spa_base[[col_id_familia_spa, col_nome_familia_spa]]
            .dropna(subset=[col_id_familia_spa])
            .drop_duplicates(subset=[col_id_familia_spa])
            .set_index(col_id_familia_spa)[col_nome_familia_spa]
        )
    resp_por_id = pd.Series(dtype=object)
    if col_resp_spa in df_spa_base.columns:
        resp_por_id = (
            df_spa_base[[col_id_familia_spa, col_resp_spa]]
            .dropna(subset=[col_id_familia_spa])
            .drop_duplicates(subset=[col_id_familia_spa])
            .set_index(col_id_familia_spa)[col_resp_spa]
        )

    fam_metrics['Percentual'] = fam_metrics.apply(lambda r: (r['concluidas'] / r['total_itens'] * 100) if r['total_itens'] > 0 else 0.0, axis=1)
    fam_metrics['Concluídas/Total'] = fam_metrics.apply(lambda r: f"{int(r['concluidas'])}/{int(r['total_itens'])}", axis=1)
    fam_metrics['Progresso'] = fam_metrics['Percentual']
    fam_metrics['Percentual'] = fam_metrics['Percentual'].apply(lambda v: '✅ 100%' if v >= 100 else f"{v:.1f}%")

    fam_metrics[col_id_familia_spa] = fam_metrics[col_id_familia_spa].astype(str).str.strip()
    df_prog_show = fam_metrics.copy()
    df_prog_show['ID da Família'] = df_prog_show[col_id_familia_spa]
    df_prog_show['Nome da Família'] = df_prog_show['ID da Família'].map(nome_por_id.to_dict()) if not nome_por_id.empty else ''
    df_prog_show['Responsável'] = df_prog_show['ID da Família'].map(resp_por_id.to_dict()) if not resp_por_id.empty else ''

    cols_final = [c for c in ['Nome da Família', 'ID da Família', 'Responsável', 'Progresso', 'Concluídas/Total', 'Percentual'] if c in df_prog_show.columns]
    st.dataframe(
        ensure_pandas_df(df_prog_show[cols_final]),
        hide_index=True,
        use_container_width=True,
        column_config={
            'Nome da Família': st.column_config.TextColumn('Nome da Família', width='large'),
            'ID da Família': st.column_config.TextColumn('ID da Família', width='medium'),
            'Responsável': st.column_config.TextColumn('Responsável', width='medium'),
            'Progresso': st.column_config.ProgressColumn('Progresso', format='%.1f%%', min_value=0, max_value=100),
            'Concluídas/Total': st.column_config.TextColumn('Concluídas/Total', width='small'),
            'Percentual': st.column_config.TextColumn('Percentual', width='small'),
        }
    )

def show_ficha_familia():
    # Imports lazy para evitar importação circular
    from views.cartorio_new.data_loader import carregar_dados_cartorio
    
    # REMOVIDO: Configuração do layout da página (já feita em main.py)
    # Comentado para evitar conflito: st.set_page_config() deve ser chamado apenas uma vez
    # try:
    #     st.set_page_config(layout="wide")
    # except st.errors.StreamlitAPIException as e:
    #     # st.toast(f"Nota: st.set_page_config(layout=\"wide\") já foi chamado anteriormente. {e}")
    #     pass # Ignora o erro se já foi configurado

    st.markdown("<h1 class='page-title initial-page-title'>Ficha da Família</h1>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Busque por uma famílias para encontrar status do processo da mesma.</p>", unsafe_allow_html=True)

    # Garantir que toda a página use a largura máxima disponível
    st.markdown('''
    <style>
    .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Estilos para a tabela de resultados de busca */
    .search-results-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 15px;
        font-size: 14px;
    }
    .search-results-table th {
        background-color: #f0f0f0;
        padding: 8px 12px;
        text-align: left;
        border: 1px solid #ddd;
        font-weight: 600;
    }
    .search-results-table td {
        padding: 8px 12px;
        border: 1px solid #ddd;
        vertical-align: top;
    }
    .search-results-table tr:hover {
        background-color: #f9f9f9;
        cursor: pointer;
    }
    .search-results-table tr.selected {
        background-color: #e0f0ff;
    }
    /* Estilos para o contador de resultados */
    .results-count {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 10px;
        font-style: italic;
    }
    </style>
    ''', unsafe_allow_html=True)

    # Carregar os dados das famílias antecipadamente para agilizar a busca
    df_crm_deals_full = load_crm_deal_data(category_id=46)
    
    # Preparar estado para armazenar família selecionada
    if "familia_selecionada_id" not in st.session_state:
        st.session_state.familia_selecionada_id = None
    if "resultados_busca" not in st.session_state:
        st.session_state.resultados_busca = pd.DataFrame()
    
    # Função para atualizar o ID da família selecionada
    def selecionar_familia(id_familia):
        st.session_state.familia_selecionada_id = id_familia

    # Container para busca e resultados
    with st.container():
        col1, col2 = st.columns([5, 1])
        
        with col1:
            campo_busca_familia_principal = 'UF_CRM_1722883482527'
            termo_busca = st.text_input(
                "Busca Nome da Família",
                placeholder="Digite o nome da família...", 
                key="busca_familia_principal_input",
                label_visibility="collapsed"
            ).strip()

            if "busca_avancada_loading" not in st.session_state:
                st.session_state.busca_avancada_loading = False

        with col2:
            if st.button("🔍 BUSCAR", help="Abre opções de buscar"):
                with st.spinner('Carregando busca...'):
                    time.sleep(0.8) # Simula carregamento 
                    st.session_state.busca_avancada_loading = True
    # Processamento da busca
    familia_selecionada_data = pd.Series(dtype=object)
    df_emissoes_filtradas = pd.DataFrame()
    
    if df_crm_deals_full is not None and not df_crm_deals_full.empty:
        if campo_busca_familia_principal in df_crm_deals_full.columns:
            # Preparar colunas para exibição nos resultados da busca
            df_crm_deals_full[campo_busca_familia_principal] = df_crm_deals_full[campo_busca_familia_principal].astype(str).fillna('')
            
            # Se houver termo de busca, filtrar resultados
            if termo_busca:
                resultados_busca_df = df_crm_deals_full[
                    df_crm_deals_full[campo_busca_familia_principal].str.contains(termo_busca, case=False, na=False)
                ].copy()
                
                # Limitar a 10 resultados para performance
                resultados_busca_df = resultados_busca_df.head(10)
                
                # Armazenar os resultados da busca na sessão
                st.session_state.resultados_busca = resultados_busca_df
                
                # Exibir resultados da busca
                if not resultados_busca_df.empty:
                    st.markdown(f"<div class='results-count'>Encontrados {len(resultados_busca_df)} resultados para '{termo_busca}'</div>", unsafe_allow_html=True)
                    
                    # Preparar dados para exibição em tabela amigável
                    dados_para_exibicao = []
                    
                    # Loop para gerar linhas da tabela
                    for idx, row in resultados_busca_df.iterrows():
                        nome_familia = row.get(campo_busca_familia_principal, "")
                        id_familia = row.get('UF_CRM_1722605592778', "N/D")
                        
                        # Tentar encontrar o nome de um requerente, se disponível
                        nome_requerente = "Não informado"
                        if 'UF_CRM_1723029889441' in row and row['UF_CRM_1723029889441']:
                            nome_requerente = row['UF_CRM_1723029889441']
                        elif 'TITLE' in row and row['TITLE']:
                            nome_requerente = row['TITLE']
                        
                        # Adicionar à lista de resultados para exibição
                        dados_para_exibicao.append({
                            "Nome da Família": nome_familia,
                            "ID da Família": id_familia,
                            "Requerente": nome_requerente
                        })
                    
                    # Criar DataFrame para exibição
                    df_resultados = pd.DataFrame(dados_para_exibicao)
                    
                    # Exibir resultados como uma tabela interativa
                    st.dataframe(
                        ensure_pandas_df(df_resultados),
                        column_config={
                            "Nome da Família": st.column_config.TextColumn("Nome da Família", width="large"),
                            "ID da Família": st.column_config.TextColumn("ID da Família", width="medium"),
                            "Requerente": st.column_config.TextColumn("Requerente", width="large")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Adicionar seletor na interface do Streamlit para capturar a seleção do usuário
                    familia_ids = resultados_busca_df['UF_CRM_1722605592778'].astype(str).tolist() if 'UF_CRM_1722605592778' in resultados_busca_df.columns else []
                    familia_nomes = resultados_busca_df[campo_busca_familia_principal].astype(str).tolist()
                    
                    # Criar opções para o seletor: "ID - Nome Família"
                    opcoes_selecao = []
                    for idx, id_familia in enumerate(familia_ids):
                        nome = familia_nomes[idx] if idx < len(familia_nomes) else "Família"
                        opcoes_selecao.append(f"{id_familia} - {nome}")
                    
                    if opcoes_selecao:
                        familia_selecionada_option = st.selectbox(
                            "👇 Selecione uma família para ver detalhes completos:",
                            options=["Selecione..."] + opcoes_selecao,
                            key="family_selector"
                        )
                        
                        if familia_selecionada_option != "Selecione...":
                            # Extrair o ID da família da opção selecionada
                            id_familia_selecionada = familia_selecionada_option.split(" - ")[0]
                            # DEBUG ADICIONADO
                            print(f"[DEBUG FILTRO EMISSOES] ID da Família Selecionada para filtrar emissões: '{id_familia_selecionada}' (Tipo: {type(id_familia_selecionada)})")
                            
                            # Obter os dados da família selecionada
                            familia_selecionada_data = resultados_busca_df[
                                resultados_busca_df['UF_CRM_1722605592778'].astype(str) == id_familia_selecionada
                            ].iloc[0]
                            
                            # Buscar emissões relacionadas à família selecionada
                            # ATUALIZADO: Usar nova função que carrega todos os pipelines
                            from views.cartorio_new.data_loader import load_data_all_pipelines
                            df_cartorio_completo = load_data_all_pipelines()
                            
                            campo_ligacao_emissoes = 'UF_CRM_34_ID_FAMILIA'
                            
                            if df_cartorio_completo is not None and not df_cartorio_completo.empty and campo_ligacao_emissoes in df_cartorio_completo.columns:
                                df_cartorio_completo[campo_ligacao_emissoes] = df_cartorio_completo[campo_ligacao_emissoes].astype(str).fillna('')
                                df_emissoes_filtradas = df_cartorio_completo[
                                    df_cartorio_completo[campo_ligacao_emissoes] == id_familia_selecionada
                                ].copy()
                            # DEBUG ADICIONADO
                            print(f"[DEBUG FILTRO EMISSOES] Número de emissões encontradas para a família ID '{id_familia_selecionada}': {len(df_emissoes_filtradas)}")
                            if not df_emissoes_filtradas.empty:
                                print("[DEBUG FILTRO EMISSOES] Primeiras 5 emissões filtradas (colunas relevantes):")
                                print(df_emissoes_filtradas[['TITLE', 'UF_CRM_34_ID_REQUERENTE', 'STAGE_ID', 'UF_CRM_34_ID_FAMILIA', 'NOME_PIPELINE']].head())
                            else:
                                print(f"[DEBUG FILTRO EMISSOES] Nenhuma emissão encontrada para o ID de família '{id_familia_selecionada}'. Verifique se este ID existe na coluna 'UF_CRM_34_ID_FAMILIA'.")
                                if df_cartorio_completo is not None and not df_cartorio_completo.empty and 'UF_CRM_34_ID_FAMILIA' in df_cartorio_completo.columns:
                                    print("[DEBUG FILTRO EMISSOES] Alguns IDs de família presentes:")
                                    print(df_cartorio_completo['UF_CRM_34_ID_FAMILIA'].unique()[:20]) # Mostra até 20 IDs únicos
                            
                            st.success(f"Família selecionada: {familia_selecionada_data.get(campo_busca_familia_principal, '')}")
                else:
                    st.info(f"Nenhuma família encontrada para '{termo_busca}'.")
        else:
            st.error(f"Coluna de busca '{campo_busca_familia_principal}' não existe nos dados do CRM.")
    elif df_crm_deals_full is None:
        st.error("Falha ao carregar dados do CRM.")
    
    st.markdown("---")
    
    if not familia_selecionada_data.empty:
        exibir_ficha_familia(familia_selecionada_data, df_emissoes_filtradas)

        context_download = st.session_state.get('ficha_pdf_context')

        link_pasta_pronta = str(
            familia_selecionada_data.get('UF_CRM_48_LINK_PASTA_PRONTA')
            or familia_selecionada_data.get('UF_CRM_LINK_PASTA_PRONTA')
            or ''
        ).strip()
        link_emissao_brasileira = str(
            familia_selecionada_data.get('UF_CRM_48_LINK_EMISSAO_BRASILEIRA')
            or familia_selecionada_data.get('UF_CRM_LINK_EMISSAO_BRASILEIRA')
            or ''
        ).strip()

        with st.container():
            col_link1, col_link2 = st.columns([1, 1])
            with col_link1:
                if link_pasta_pronta.lower().startswith('http'):
                    st.link_button('Abrir card Pasta Pronta', url=link_pasta_pronta)
                else:
                    st.caption('Card Pasta Pronta: N/D')
            with col_link2:
                if link_emissao_brasileira.lower().startswith('http'):
                    st.link_button('Abrir card Emissão Brasileira', url=link_emissao_brasileira)
                else:
                    st.caption('Card Emissão Brasileira: N/D')
    else:
        if not termo_busca:
            exibir_metricas_macro()

# Para testar isoladamente (opcional)
if __name__ == '__main__':
    # Simular st.session_state se necessário para testes
    if 'pagina_atual' not in st.session_state:
        st.session_state['pagina_atual'] = "Ficha da Família"
    if 'emissao_subpagina' not in st.session_state:
        st.session_state.emissao_subpagina = 'Visão Geral'
    if 'comune_subpagina' not in st.session_state:
        st.session_state.comune_subpagina = 'Visão Geral'
        
    show_ficha_familia() 