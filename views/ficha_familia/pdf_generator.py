"""
Módulo de geração de PDF para Ficha da Família
"""
import html
import os
from functools import lru_cache
from io import BytesIO
from datetime import datetime

try:
    import cairosvg
except (ImportError, OSError):
    cairosvg = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ImportError:
    SimpleDocTemplate = None

from .utils import LOGO_SVG_PATH, LOGO_PNG_PATH


@lru_cache(maxsize=1)
def _load_logo_image_bytes():
    """Obtém bytes do logo em PNG. Usa arquivo pronto e, se necessário, converte o SVG."""
    if os.path.exists(LOGO_PNG_PATH):
        try:
            with open(LOGO_PNG_PATH, "rb") as png_file:
                return png_file.read()
        except Exception as exc:
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
    except Exception as exc:
        print(f"[WARN] Falha ao converter logo SVG para PNG: {exc}")
        return None


def _create_logo_flowable(max_height_mm: float = 20):  # Reduzido de 28
    """Cria o flowable do logo para o PDF, se disponível."""
    logo_bytes = _load_logo_image_bytes()
    if not logo_bytes:
        return None
    try:
        img = Image(BytesIO(logo_bytes))
        img.hAlign = "LEFT"
        img._restrictSize(25 * mm, max_height_mm * mm)  # Reduzido de 32mm
        return img
    except Exception as exc:
        print(f"[WARN] Falha ao preparar imagem do logo: {exc}")
        return None


def _format_text_for_paragraph(value) -> str:
    """Normaliza texto para uso em Paragraph."""
    text = html.escape(str(value if value not in [None, "None"] else "N/D"))
    return text.replace("\n", "<br/>")


def _build_key_value_table(items, label_style, value_style, label_width_mm: float = 58.0):
    """Constrói tabela chave-valor para o PDF"""
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
                ("LEFTPADDING", (0, 0), (-1, -1), 6),  # Reduzido de 8
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),   # Reduzido de 4
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F9F9F9")),  # Cinza claro
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),  # Cinza neutro
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),  # Cinza claro
            ]
        )
    )
    return table


def gerar_pdf_ficha(contexto_pdf: dict) -> bytes:
    """Gera PDF da ficha completa - OTIMIZADO PARA A4 MINIMALISTA"""
    if SimpleDocTemplate is None:
        raise RuntimeError("Biblioteca 'reportlab' não está instalada. Instale com 'pip install reportlab'.")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12 * mm,  # Margens reduzidas para A4
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    # DESIGN MINIMALISTA - Fontes menores e cores neutras
    titulo_style = ParagraphStyle(
        "FichaTitulo",
        parent=styles["Heading1"],
        fontSize=14,  # Reduzido de 20
        leading=17,
        textColor=colors.HexColor("#333333"),  # Cinza escuro neutro
        spaceAfter=2,
        spaceBefore=0,
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=10,  # Reduzido de 13
        leading=12,
        spaceBefore=6,  # Reduzido de 12
        spaceAfter=3,   # Reduzido de 6
        textColor=colors.HexColor("#555555"),  # Cinza neutro
        borderPadding=(0, 0, 2),
    )
    table_label_style = ParagraphStyle(
        "TabelaLabel",
        parent=styles["Normal"],
        fontSize=7.5,  # Reduzido de 9.3
        textColor=colors.HexColor("#555555"),
        leading=9,
        spaceAfter=0,
    )
    table_value_style = ParagraphStyle(
        "TabelaValor",
        parent=styles["Normal"],
        fontSize=7.5,  # Reduzido de 9.3
        leading=9,
        textColor=colors.HexColor("#333333"),
    )

    story = []

    # Header
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

    # Alertas
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

    # Requerentes
    requerentes = contexto_pdf.get("requerentes") or []
    if requerentes:
        story.append(Paragraph("Status Emissões Brasileiras", section_title_style))
        
        for req in requerentes:
            info_basica = [
                Paragraph(f"<b>{_format_text_for_paragraph(req.get('Requerente'))}</b>", table_label_style),
                Paragraph(f"Posição: {_format_text_for_paragraph(req.get('Posição'))}", table_value_style),
            ]
            
            certidoes_info = []
            for tipo in ['Nascimento', 'Casamento', 'Óbito']:
                status_simples = req.get(tipo, 'N/D')
                certidoes_info.append(Paragraph(f"{tipo}: {_format_text_for_paragraph(status_simples)}", table_value_style))
            
            info_basica.extend(certidoes_info)
            
            card_basico = Table(
                [info_basica],
                colWidths=[None, 35 * mm, 35 * mm, 35 * mm],
            )
            card_basico.setStyle(
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
            story.append(card_basico)
            
            # Detalhes adicionais
            tem_detalhes = False
            detalhes_rows = []
            
            for tipo in ['Nascimento', 'Casamento', 'Óbito']:
                detalhes_key = f'{tipo}_Detalhes'
                if detalhes_key in req and req[detalhes_key]:
                    tem_detalhes = True
                    for idx, detalhe in enumerate(req[detalhes_key]):
                        pipeline = detalhe.get('pipeline', 'N/D')
                        status = detalhe.get('status', 'N/D')
                        card_id = detalhe.get('card_id', 'N/D')
                        
                        tipo_label = tipo if idx == 0 else f"  └ Duplicado"
                        
                        detalhes_rows.append([
                            Paragraph(f"<font size='8'>{tipo_label}</font>", table_value_style),
                            Paragraph(f"<font size='8'>{_format_text_for_paragraph(pipeline)}</font>", table_value_style),
                            Paragraph(f"<font size='8'>{_format_text_for_paragraph(status)}</font>", table_value_style),
                            Paragraph(f"<font size='8'>Card: {card_id}</font>", table_value_style),
                        ])
            
            if tem_detalhes:
                detalhes_rows.insert(0, [
                    Paragraph("<b><font size='8'>Certidão</font></b>", table_label_style),
                    Paragraph("<b><font size='8'>Pipeline</font></b>", table_label_style),
                    Paragraph("<b><font size='8'>Status</font></b>", table_label_style),
                    Paragraph("<b><font size='8'>ID Card</font></b>", table_label_style),
                ])
                
                tabela_detalhes = Table(
                    detalhes_rows,
                    colWidths=[35 * mm, 40 * mm, 50 * mm, 25 * mm],
                )
                tabela_detalhes.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5F8FF")),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FAFBFF")),
                            ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#E0E5F0")),
                            ("GRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#E8EBF2")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 4),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )
                story.append(Spacer(1, 2 * mm))
                story.append(tabela_detalhes)
            
            story.append(Spacer(1, 5 * mm))

    # Resumo
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


