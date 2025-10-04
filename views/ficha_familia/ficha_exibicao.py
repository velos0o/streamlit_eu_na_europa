"""
Módulo de exibição da ficha completa da família
Responsável por renderizar todos os componentes HTML da ficha
"""
import streamlit as st
import pandas as pd
import html
from datetime import datetime
from unidecode import unidecode

from .utils import obter_url_card, construir_link_card_pipeline, montar_nome_arquivo_pdf
from .pdf_generator import gerar_pdf_ficha
from .emissoes_processor import processar_emissoes
from .business_logic import obter_nome_pipeline_legivel
from .display_components import (
    render_alert_box,
    render_mapa_inicial_notification,
    CANAIS_ESPECIAIS_CONFIG
)


def exibir_ficha_familia(familia_serie, emissoes_df):
    """
    Exibe a ficha completa da família com todos os dados e emissões.
    
    Args:
        familia_serie: Série do pandas com os dados da família
        emissoes_df: DataFrame com as emissões brasileiras da família
    """
    # Imports lazy para evitar import circular
    from views.scaner.data_loader import carregar_dados_spa_scanner
    
    # Inicializar contexto PDF
    alertas_para_pdf = []
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
    
    # CSS já foi injetado no início da página via inject_all_ficha_css()
    
    # === ALERTAS VISUAIS ===
    _exibir_alertas(familia_serie, alertas_para_pdf, proxima_posicao_alerta)
    
    # === EXTRAIR DADOS BÁSICOS ===
    dados_familia = _extrair_dados_familia(familia_serie)
    
    # === PROCESSAR EMISSÕES ===
    requerentes_data_list, processamento_ok, resumo_categorias, total_certidoes = processar_emissoes(
        emissoes_df, familia_serie
    )
    
    # === CARREGAR DOCUMENTOS SPA ===
    docs_map = _carregar_documentos_spa(familia_serie)
    
    # === CONSTRUIR HTML DA FICHA ===
    html_ficha = _construir_html_ficha(
        dados_familia,
        requerentes_data_list,
        resumo_categorias,
        total_certidoes,
        emissoes_df,
        processamento_ok,
        docs_map
    )
    
    # Exibir HTML
    st.markdown(html_ficha, unsafe_allow_html=True)
    
    # === PREPARAR DADOS PDF ===
    _preparar_dados_pdf(dados_pdf, dados_familia, requerentes_data_list, resumo_categorias, total_certidoes, emissoes_df, processamento_ok)
    
    st.session_state['ficha_pdf_context'] = dados_pdf
    
    # === BOTÃO DOWNLOAD PDF ===
    _exibir_botao_download_pdf(familia_serie)
    
    # === DOCUMENTOS SPA ===
    _exibir_documentos_spa(familia_serie, requerentes_data_list)


def _exibir_alertas(familia_serie, alertas_para_pdf, proxima_posicao_alerta):
    """Exibe alertas visuais (Mapa Inicial, Canal Especial, Distrato)"""
    # Mapa Inicial
    if str(familia_serie.get('UF_CRM_1750454794052', '')).strip().upper() == 'SIM':
        render_mapa_inicial_notification()
        proxima_posicao_alerta = 240
    else:
        proxima_posicao_alerta = 65
    
    # Canal Especial
    canal_especial_valor = str(familia_serie.get('UF_CRM_1759161772', '') or '').strip()
    if canal_especial_valor:
        canal_especial_upper = canal_especial_valor.upper()
        if canal_especial_upper in CANAIS_ESPECIAIS_CONFIG:
            canal_config = CANAIS_ESPECIAIS_CONFIG[canal_especial_upper]
            render_alert_box(
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
    
    # Distrato
    distrato_valor = str(familia_serie.get('UF_CRM_1759159659148', '') or '').strip().upper()
    if distrato_valor == 'SIM':
        render_alert_box(
            "Família em Distrato",
            "Acompanhar com prioridade",
            "#FF3B30",
            "rgba(0,0,0,0.1)",
            "#FFFFFF",
            proxima_posicao_alerta
        )
        alertas_para_pdf.append({
            'titulo': 'Família em Distrato',
            'descricao': 'Acompanhar com prioridade',
            'bg_color': '#FF3B30',
            'text_color': '#FFFFFF'
        })


def _extrair_dados_familia(familia_serie):
    """Extrai todos os dados básicos da família"""
    print("[DEBUG] Colunas disponíveis:", list(familia_serie.index))
    
    dados = {}
    
    # Nome e ID
    dados['nome_familia'] = familia_serie.get('UF_CRM_1722883482527', 'N/D')
    dados['id_familia'] = familia_serie.get('UF_CRM_1722605592778', 'N/D')
    
    # Data de Venda
    dados['data_venda'] = _buscar_campo_alternativo(familia_serie, [
        'UF_CRM_1746054586042',
        'UF_CRM_1739362935',
        'UF_CRM_1725397957843',
        'DATE_CREATE',
        'BEGINDATE',
        'CLOSEDATE'
    ], 'Data de Venda')
    
    # ADM Responsável
    dados['adm_responsavel'] = _buscar_campo_alternativo(familia_serie, [
        'UF_CRM_1730730467',
        'ASSIGNED_BY_ID',
        'ASSIGNED_BY',
        'RESPONSIBLE_ID',
        'UF_CRM_1746198853',
        'CREATED_BY_ID'
    ], 'ADM Responsável')
    
    # Link Contrato
    link_contrato_raw = familia_serie.get('UF_CRM_1750453631850', 'N/D')
    dados['link_contrato'] = link_contrato_raw
    dados['link_contrato_display'] = f"<a href='{link_contrato_raw}' target='_blank' class='ficha-link'>Acessar Contrato</a>" if str(link_contrato_raw).startswith('http') else str(link_contrato_raw)
    
    # Procuração
    dados['procuracao_detalhes'] = _buscar_campo_alternativo(familia_serie, [
        'UF_CRM_1746046262136',
        'UF_CRM_1744671378914',
        'UF_CRM_1737561431',
        'UF_CRM_1746089520',
        'COMMENTS',
        'DESCRIPTION'
    ], 'Procuração')
    
    # Etapa Comune
    dados['etapa_comune'] = _buscar_campo_alternativo(familia_serie, [
        'UF_CRM_1746045819198',
        'UF_CRM_1737823612831',
        'STAGE_ID',
        'STAGE_SEMANTIC_ID',
        'UF_CRM_1737561431'
    ], 'Etapa Comune')
    
    # Outros campos
    dados['data_solicitacao_comune'] = familia_serie.get('UF_CRM_1737823552173', 'N/D') or 'N/D'
    dados['prazo_comune'] = familia_serie.get('UF_CRM_1746202791172', 'N/D') or 'N/D'
    dados['analise_doc'] = familia_serie.get('UF_CRM_1746045866262', 'N/D') or 'N/D'
    dados['traducao'] = familia_serie.get('UF_CRM_1746045880601', 'N/D') or 'N/D'
    dados['apostilamento'] = familia_serie.get('UF_CRM_1746045919198', 'N/D') or 'N/D'
    
    # Drive
    drive_link_raw = familia_serie.get('UF_CRM_DRIVE', 'N/D')
    dados['drive_link'] = drive_link_raw
    dados['drive_display'] = f"<a href='{drive_link_raw}' target='_blank' class='ficha-link'>Acessar Link</a>" if str(drive_link_raw).startswith('http') else str(drive_link_raw)
    
    # Quantidades
    dados['qnt_familiares'] = familia_serie.get('UF_CRM_QUANTIDADE_FAMILIARES', 'N/D') or 'N/D'
    dados['qnt_requerentes'] = familia_serie.get('UF_CRM_1743182118', 'N/D') or 'N/D'
    dados['emissoes_status_geral'] = familia_serie.get('UF_CRM_1746459875884', 'N/D') or 'N/D'
    
    return dados


def _buscar_campo_alternativo(familia_serie, campos, nome_campo):
    """Busca valor em múltiplos campos alternativos"""
    for campo in campos:
        if campo in familia_serie and familia_serie.get(campo) and str(familia_serie.get(campo)).lower() not in ['none', 'nan', '']:
            valor = familia_serie.get(campo)
            print(f"[DEBUG] {nome_campo} encontrado no campo '{campo}': {valor}")
            return valor
    
    print(f"[DEBUG] Nenhum valor encontrado para {nome_campo}")
    return 'N/D'


def _carregar_documentos_spa(familia_serie):
    """Carrega documentos da SPA e cria mapa de documentos"""
    from views.scaner.data_loader import carregar_dados_spa_scanner
    
    docs_map = {}
    try:
        id_familia_str = str(familia_serie.get('UF_CRM_1722605592778', '')).strip()
        if id_familia_str:
            df_docs_spa = carregar_dados_spa_scanner()
            if df_docs_spa is not None and not df_docs_spa.empty:
                df_docs_spa['UF_CRM_48_ID_FAMILIA'] = df_docs_spa['UF_CRM_48_ID_FAMILIA'].astype(str).str.strip()
                df_docs_spa['UF_CRM_48_ID_REQUERENTE'] = df_docs_spa['UF_CRM_48_ID_REQUERENTE'].astype(str).str.strip()
                docs_familia = df_docs_spa[df_docs_spa['UF_CRM_48_ID_FAMILIA'] == id_familia_str].copy()
                
                if not docs_familia.empty:
                    def _inferir_tipo_certidao_spa(titulo: str) -> str:
                        t_norm = unidecode(str(titulo)).upper()
                        if 'CERTIDAO NASCIMENTO' in t_norm or 'NASCIMENTO' in t_norm or 'NASC' in t_norm:
                            return 'Nascimento'
                        if 'CERTIDAO CASAMENTO' in t_norm or 'MATRIMONIO' in t_norm or 'CASAMENTO' in t_norm or 'MATRIM' in t_norm or 'CASA' in t_norm:
                            return 'Casamento'
                        if 'CERTIDAO OBITO' in t_norm or 'OBITO' in t_norm or 'OBIT' in t_norm:
                            return 'Óbito'
                        return 'Outro'
                    
                    docs_familia['__tipo__'] = docs_familia['TITLE'].apply(_inferir_tipo_certidao_spa)
                    for _i, r in docs_familia.iterrows():
                        req_id = str(r.get('UF_CRM_48_ID_REQUERENTE', '')).strip()
                        tipo = str(r.get('__tipo__', 'Outro'))
                        link_drive = str(r.get('UF_CRM_48_LINK_DRIVE', '')).strip()
                        link_scan = str(r.get('UF_CRM_48_DOCUMENTO_SCANEADO', '')).strip()
                        chosen_link = link_drive if link_drive.lower().startswith('http') else (link_scan if link_scan.lower().startswith('http') else '')
                        
                        if req_id and tipo in ['Nascimento', 'Casamento', 'Óbito'] and chosen_link:
                            chave_doc = (req_id, tipo)
                            if chave_doc not in docs_map:
                                docs_map[chave_doc] = []
                            if chosen_link not in docs_map[chave_doc]:
                                docs_map[chave_doc].append(chosen_link)
    except Exception as e:
        print(f"[WARN] Falha ao carregar docs SPA: {e}")
    
    return docs_map


def _construir_html_ficha(dados_familia, requerentes_data, resumo_categorias, total_certidoes, emissoes_df, processamento_ok, docs_map):
    """Constrói o HTML completo da ficha"""
    html = "<div class='ficha-familia-container' style='width:100%; max-width:100%; margin-right:0; margin-left:0;'>"
    html += "<div style='background-color:#333; color:white; text-align:center; padding:8px; margin-bottom:12px; font-size:1.1em; font-weight:600; border-radius:0;'>ACOMPANHAMENTO FAMÍLIA</div>"
    
    # Tabela de dados - Design minimalista
    html += "<div class='ficha-secao dados-consolidado-tabela-secao'>"
    html += "<table class='ficha-info-tabela' style='width:100%; border-collapse:collapse; border:1px solid #E0E0E0;'>"
    
    td_style = "border:1px solid #E0E0E0; padding:6px 8px; font-size:0.85rem;"
    td_label_style = f"{td_style} color:#555; font-weight:600; width:20%; background:#F9F9F9;"
    td_data_style = f"{td_style} width:30%;"
    
    # Dados básicos
    html += f"<tr><td style='{td_label_style}'>Nome da Família:</td><td style='{td_data_style}'>{dados_familia['nome_familia']}</td><td style='{td_label_style}'>ID da Família:</td><td style='{td_data_style}'>{dados_familia['id_familia']}</td></tr>"
    html += f"<tr><td style='{td_label_style}'>Data de Venda:</td><td style='{td_data_style}'>{dados_familia['data_venda']}</td><td style='{td_label_style}'>ADM Responsável:</td><td style='{td_data_style}'>{dados_familia['adm_responsavel']}</td></tr>"
    html += f"<tr><td style='{td_label_style}'>Link do Contrato:</td><td style='{td_data_style}'>{dados_familia['link_contrato_display']}</td><td style='{td_label_style}'>Card Pasta Pronta:</td><td style='{td_data_style}'>{_obter_link_pasta_pronta_display(dados_familia)}</td></tr>"
    
    # Procuração
    html += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#F5F5F5; border:1px solid #E0E0E0; padding:6px;'><h4 style='color:#555; text-align:left; margin:3px 0; font-size:0.9rem; font-weight:600;'>PROCURAÇÃO</h4></td></tr>"
    html += f"<tr><td style='{td_label_style}'>Detalhes Procuração:</td><td colspan='3' style='{td_style}'>{dados_familia['procuracao_detalhes']}</td></tr>"
    
    # Comune
    html += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#F5F5F5; border:1px solid #E0E0E0; padding:6px;'><h4 style='color:#555; text-align:left; margin:3px 0; font-size:0.9rem; font-weight:600;'>COMUNE</h4></td></tr>"
    html += f"<tr><td style='{td_label_style}'>Etapa Comune:</td><td style='{td_data_style}'>{dados_familia['etapa_comune']}</td><td style='{td_label_style}'>Data Solicitação:</td><td style='{td_data_style}'>{dados_familia['data_solicitacao_comune']}</td></tr>"
    html += f"<tr><td style='{td_label_style}'>Prazo Comune:</td><td style='{td_data_style}'>{dados_familia['prazo_comune']}</td><td style='{td_label_style}'></td><td style='{td_data_style}'></td></tr>"
    
    # Documentação
    html += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#F5F5F5; border:1px solid #E0E0E0; padding:6px;'><h4 style='color:#555; text-align:left; margin:3px 0; font-size:0.9rem; font-weight:600;'>DOCUMENTAÇÃO E SERVIÇOS</h4></td></tr>"
    html += f"<tr><td style='{td_label_style}'>Análise Documental:</td><td style='{td_data_style}'>{dados_familia['analise_doc']}</td><td style='{td_label_style}'>Tradução:</td><td style='{td_data_style}'>{dados_familia['traducao']}</td></tr>"
    html += f"<tr><td style='{td_label_style}'>Apostilamento:</td><td style='{td_data_style}'>{dados_familia['apostilamento']}</td><td style='{td_label_style}'>Drive:</td><td style='{td_data_style}'>{dados_familia['drive_display']}</td></tr>"
    
    # Detalhes
    html += f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#F5F5F5; border:1px solid #E0E0E0; padding:6px;'><h4 style='color:#555; text-align:left; margin:3px 0; font-size:0.9rem; font-weight:600;'>DETALHES</h4></td></tr>"
    html += f"<tr><td style='{td_label_style}'>Qnt. Familiares:</td><td style='{td_data_style}'>{dados_familia['qnt_familiares']}</td><td style='{td_label_style}'>Qnt. Requerentes:</td><td style='{td_data_style}'>{dados_familia['qnt_requerentes']}</td></tr>"
    html += f"<tr><td style='{td_label_style}'>Emissões (Status Geral):</td><td style='{td_data_style}'>{dados_familia['emissoes_status_geral']}</td><td style='{td_label_style}'></td><td style='{td_data_style}'></td></tr>"
    
    # Status Emissões
    html += _construir_html_emissoes(requerentes_data, emissoes_df, processamento_ok, docs_map, td_style, td_label_style)
    
    # Resumo
    html += _construir_html_resumo(resumo_categorias, total_certidoes, td_style, td_label_style)
    
    html += "</table></div></div>"
    
    return html


def _obter_link_pasta_pronta_display(dados_familia):
    """Gera HTML do link da pasta pronta"""
    # Implementação simplificada - poderia obter do familia_serie se necessário
    return "N/D"


def _construir_html_emissoes(requerentes_data, emissoes_df, processamento_ok, docs_map, td_style, td_label_style):
    """Constrói seção HTML de emissões com cards visuais completos"""
    # CSS já foi injetado no início da página via inject_all_ficha_css()
    
    html = f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#F5F5F5; border:1px solid #E0E0E0; padding:6px;'><h4 style='color:#555; text-align:left; margin:3px 0; font-size:0.9rem; font-weight:600;'>STATUS EMISSÕES BRASILEIRAS</h4></td></tr>"
    
    if not processamento_ok or not requerentes_data:
        html += f"<tr><td colspan='4' style='text-align:center; border:1px solid #ddd; padding:8px; font-style:italic; color:#666;'>Nenhuma emissão encontrada para esta família.</td></tr>"
        return html
    
    html += "<tr><td colspan='4' style='padding:0; border:0;'>"
    html += "<table style='width:100%; border-collapse:collapse; border:1px solid #E0E0E0;'>"
    html += "<tr>"
    html += "<th style='color:#555; width:15%; text-align:center; border:1px solid #E0E0E0; padding:6px; background-color:#F9F9F9; font-size:0.8rem; font-weight:600;'>Posição</th>"
    html += "<th style='color:#555; width:25%; text-align:center; border:1px solid #E0E0E0; padding:6px; background-color:#F9F9F9; font-size:0.8rem; font-weight:600;'>Requerente</th>"
    html += "<th style='color:#555; width:20%; text-align:center; border:1px solid #E0E0E0; padding:6px; background-color:#F9F9F9; font-size:0.8rem; font-weight:600;'>Nascimento</th>"
    html += "<th style='color:#555; width:20%; text-align:center; border:1px solid #E0E0E0; padding:6px; background-color:#F9F9F9; font-size:0.8rem; font-weight:600;'>Casamento</th>"
    html += "<th style='color:#555; width:20%; text-align:center; border:1px solid #E0E0E0; padding:6px; background-color:#F9F9F9; font-size:0.8rem; font-weight:600;'>Óbito</th>"
    html += "</tr>"
    
    for req_data in requerentes_data:
        html += "<tr>"
        html += f"<td style='text-align:center; border:1px solid #E0E0E0; padding:6px; font-size:0.8rem;'>{req_data['Posição']}</td>"
        html += f"<td style='text-align:left; border:1px solid #E0E0E0; padding:6px; font-size:0.8rem;'>{req_data['Requerente']}</td>"
        
        # Renderizar cada tipo de certidão com cards visuais
        for tipo_cert in ['Nascimento', 'Casamento', 'Óbito']:
            cell_html = _render_cell_with_visual_cards(
                req_data, tipo_cert, emissoes_df, processamento_ok, docs_map
            )
            html += f"<td style='text-align:center; border:1px solid #E0E0E0; padding:6px; font-size:0.8rem;'>{cell_html}</td>"
        
        html += "</tr>"
    
    html += "</table></td></tr>"
    return html


def _render_cell_with_visual_cards(req_data, tipo_cert, emissoes_df, processamento_ok, docs_map):
    """Renderiza célula com cards visuais completos, incluindo duplicados e links"""
    status_original = str(req_data.get(tipo_cert, '') or '')
    status_original_upper = status_original.upper()
    req_id_key = str(req_data.get('ID_Requerente', '')).strip()
    req_id_grupo = str(req_data.get('ID_Requerente_Grupo', '')).strip()
    chave_documento = req_id_key if req_id_key and req_id_key.upper() not in ['ID REQUERENTE N/D', ''] else req_id_grupo
    lista_links = docs_map.get((chave_documento, tipo_cert)) if chave_documento else None
    
    blocos_html = []
    tem_duplicados = False
    
    # Buscar registros desta certidão no DataFrame de emissões
    registros_cert = pd.DataFrame()
    if processamento_ok and emissoes_df is not None and not emissoes_df.empty:
        chave_busca = req_id_key if req_id_key and req_id_key.upper() not in ['ID REQUERENTE N/D', ''] else req_id_grupo
        if chave_busca and '_ID_REQUERENTE_GRUPO' in emissoes_df.columns:
            registros_cert = emissoes_df[
                emissoes_df['_ID_REQUERENTE_GRUPO'].astype(str) == chave_busca
            ]
            if 'UF_CRM_34_TIPO_DE_CERTIDAO' in registros_cert.columns:
                registros_cert = registros_cert[
                    registros_cert['UF_CRM_34_TIPO_DE_CERTIDAO'].astype(str).str.upper() == tipo_cert.upper()
                ].copy()
                
                if not registros_cert.empty:
                    registros_cert['__CARD_LINK__'] = registros_cert.apply(construir_link_card_pipeline, axis=1)
    
    # Se há registros, criar cards para cada um
    if registros_cert is not None and not registros_cert.empty:
        tem_duplicados = len(registros_cert) > 1
        
        for _, reg_local in registros_cert.iterrows():
            status_local_raw = reg_local.get('STAGE_NAME_LEGIVEL', status_original) or status_original
            status_local = html.escape(str(status_local_raw))
            pipeline_nome_raw = obter_nome_pipeline_legivel(reg_local)
            pipeline_legivel = html.escape(pipeline_nome_raw) if pipeline_nome_raw else ''
            
            # Links
            link_buttons = []
            link_card = reg_local.get('__CARD_LINK__')
            if link_card:
                link_buttons.append(
                    f"<a class='cert-link-button cert-card-link' href='{html.escape(link_card, quote=True)}' "
                    f"target='_blank' title='Abrir card Bitrix'>"
                    f"<span class='cert-link-icon'>🔗</span><span>Card</span></a>"
                )
            
            for link_individual in lista_links or []:
                if link_individual:
                    link_buttons.append(
                        f"<a class='cert-link-button' href='{html.escape(link_individual, quote=True)}' "
                        f"target='_blank' title='Abrir documento'>"
                        f"<span class='cert-link-icon'>📄</span><span>Documento</span></a>"
                    )
            
            links_html = ''.join(link_buttons)
            
            # Chips (badges)
            chips = []
            if pipeline_legivel:
                chips.append(
                    f"<span class='cert-chip' style='--chip-bg: rgba(0, 150, 136, 0.15); --chip-color: #004D40;'>{pipeline_legivel}</span>"
                )
            if tem_duplicados:
                chips.append(
                    "<span class='cert-chip' style='--chip-bg: rgba(255, 152, 0, 0.18); --chip-color: #E65100;'>Duplicado</span>"
                )
            chips_html = ''.join(chips) if chips else "<span class='cert-chip'>Sem pipeline</span>"
            
            # Notas informativas
            notas = []
            if not links_html:
                if lista_links:
                    notas.append("<div class='cert-note'>Links anexados não foram reconhecidos como URLs válidos.</div>")
                else:
                    notas.append("<div class='cert-note'>Documento digital não vinculado na SPA para esta certidão.</div>")
            
            if status_original_upper in ['CERTIDÃO DISPENSADA', 'CANCELADO', 'SOLICITAÇÃO DUPLICADA']:
                notas.append("<div class='cert-note'>Certidão fora do escopo ativo.</div>")
            
            note_html = ''.join(notas)
            
            # Montar card
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
        # Sem registros detalhados, exibir status simples
        status_principal = html.escape(status_original)
        informacao_adicional = ''
        
        if status_original_upper in ['CERTIDÃO DISPENSADA', 'CANCELADO', 'SOLICITAÇÃO DUPLICADA']:
            informacao_adicional = "<div class='cert-note'>Certidão fora do escopo ativo.</div>"
        elif not status_original or status_original_upper in ['DISPENSADO', 'N/D', 'STATUS N/D']:
            informacao_adicional = "<div class='cert-note'>Sem atualizações registradas para esta certidão.</div>"
        
        blocos_html.append(
            "<div class='cert-card default-status'>"
            f"<div class='cert-status-title'>{status_principal}</div>"
            f"{informacao_adicional}"
            "</div>"
        )
    
    # Wrapper para múltiplos cards (se houver duplicados)
    wrapper_classes = "cert-status-wrapper" + (" duplicado" if tem_duplicados or len(blocos_html) > 1 else "")
    return f"<div class='{wrapper_classes}'>" + ''.join(blocos_html) + "</div>"


def _construir_html_resumo(resumo_categorias, total_certidoes, td_style, td_label_style):
    """Constrói seção HTML de resumo"""
    html = f"<tr><td colspan='4' class='td-titulo-secao' style='background-color:#F5F5F5; border:1px solid #E0E0E0; padding:6px;'><h4 style='color:#555; text-align:left; margin:3px 0; font-size:0.9rem; font-weight:600;'>RESUMO EMISSÕES</h4></td></tr>"
    html += "<tr><td colspan='4' style='padding:0; border:0;'>"
    html += "<table style='width:100%; border-collapse:collapse; border:1px solid #E0E0E0;'>"
    html += "<tr><th style='color:#555; width:30%; text-align:center; border:1px solid #E0E0E0; padding:6px; background-color:#F9F9F9; font-size:0.8rem; font-weight:600;'>Status</th>"
    html += "<th style='color:#555; width:20%; text-align:center; border:1px solid #E0E0E0; padding:6px; background-color:#F9F9F9; font-size:0.8rem; font-weight:600;'>Quantidade</th></tr>"
    
    for status, quantidade in resumo_categorias.items():
        if quantidade > 0 or status == 'Outros':
            html += f"<tr><td style='text-align:center; border:1px solid #E0E0E0; padding:6px; font-size:0.8rem; font-weight:600;'>{status}</td>"
            html += f"<td style='text-align:center; border:1px solid #E0E0E0; padding:6px; font-size:0.8rem;'>{quantidade}</td></tr>"
    
    html += f"<tr style='background-color:#F5F5F5;'><td style='text-align:center; border:1px solid #E0E0E0; padding:6px; font-size:0.8rem; font-weight:700;'>TOTAL</td>"
    html += f"<td style='text-align:center; border:1px solid #E0E0E0; padding:6px; font-size:0.8rem; font-weight:700;'>{total_certidoes}</td></tr>"
    html += "</table></td></tr>"
    html += "<tr><td colspan='4' style='border:1px solid #E0E0E0; padding:6px; text-align:right;'><div class='resumo-emissoes-download'></div></td></tr>"
    
    return html


def _preparar_dados_pdf(dados_pdf, dados_familia, requerentes_data, resumo_categorias, total_certidoes, emissoes_df, processamento_ok):
    """Prepara dados para geração do PDF"""
    dados_pdf['dados_basicos'] = [
        ("Nome da Família", dados_familia['nome_familia']),
        ("ID da Família", dados_familia['id_familia']),
        ("Data de Venda", dados_familia['data_venda']),
        ("ADM Responsável", dados_familia['adm_responsavel']),
        ("Link do Contrato", dados_familia['link_contrato']),
    ]
    dados_pdf['nome_familia'] = dados_familia['nome_familia']
    dados_pdf['id_familia'] = dados_familia['id_familia']
    dados_pdf['sec_procuracao'] = [("Detalhes Procuração", dados_familia['procuracao_detalhes'])]
    dados_pdf['sec_comune'] = [
        ("Etapa Comune", dados_familia['etapa_comune']),
        ("Data Solicitação Comune", dados_familia['data_solicitacao_comune']),
        ("Prazo Comune", dados_familia['prazo_comune']),
    ]
    dados_pdf['sec_doc_serv'] = [
        ("Análise Documental", dados_familia['analise_doc']),
        ("Tradução", dados_familia['traducao']),
        ("Apostilamento", dados_familia['apostilamento']),
        ("Drive", dados_familia['drive_link']),
    ]
    dados_pdf['sec_detalhes'] = [
        ("Qnt. Familiares", dados_familia['qnt_familiares']),
        ("Qnt. Requerentes", dados_familia['qnt_requerentes']),
        ("Emissões (Status Geral)", dados_familia['emissoes_status_geral']),
    ]
    
    # Enriquecer dados dos requerentes
    requerentes_pdf = []
    for item in requerentes_data:
        req_pdf = {
            'Posição': item.get('Posição', 'N/D'),
            'Requerente': item.get('Requerente', 'N/D'),
            'Nascimento': item.get('Nascimento', 'N/D'),
            'Casamento': item.get('Casamento', 'N/D'),
            'Óbito': item.get('Óbito', 'N/D'),
        }
        
        # Adicionar detalhes se disponíveis
        if processamento_ok and emissoes_df is not None and not emissoes_df.empty:
            req_id_key = str(item.get('ID_Requerente', '')).strip()
            req_id_grupo = str(item.get('ID_Requerente_Grupo', '')).strip()
            chave_busca = req_id_key if req_id_key and req_id_key.upper() not in ['ID REQUERENTE N/D', ''] else req_id_grupo
            
            if chave_busca:
                for tipo_cert in ['NASCIMENTO', 'CASAMENTO', 'ÓBITO']:
                    registros = emissoes_df[
                        (emissoes_df['_ID_REQUERENTE_GRUPO'].astype(str) == chave_busca) &
                        (emissoes_df['UF_CRM_34_TIPO_DE_CERTIDAO'].astype(str).str.upper() == tipo_cert)
                    ]
                    
                    if not registros.empty:
                        detalhes = []
                        for _, reg in registros.iterrows():
                            pipeline = obter_nome_pipeline_legivel(reg) or 'N/D'
                            status_det = reg.get('STAGE_NAME_LEGIVEL', 'N/D')
                            card_id = reg.get('ID', '')
                            detalhes.append({
                                'pipeline': pipeline,
                                'status': str(status_det),
                                'card_id': str(card_id)
                            })
                        
                        tipo_label = tipo_cert.capitalize()
                        req_pdf[f'{tipo_label}_Detalhes'] = detalhes
        
        requerentes_pdf.append(req_pdf)
    
    dados_pdf['requerentes'] = requerentes_pdf
    
    if processamento_ok:
        dados_pdf['resumo'] = dict(resumo_categorias)
        dados_pdf['total_certidoes'] = total_certidoes
    else:
        dados_pdf['resumo'] = {}
        dados_pdf['total_certidoes'] = 0


def _exibir_botao_download_pdf(familia_serie):
    """Exibe botão de download do PDF"""
    try:
        context_pdf = st.session_state.get('ficha_pdf_context')
        if context_pdf:
            pdf_bytes = gerar_pdf_ficha(context_pdf)
            
            nome_familia = familia_serie.get('TITLE', 'Família')
            id_familia_val = familia_serie.get('UF_CRM_1722605592778', '')
            nome_arquivo_pdf = montar_nome_arquivo_pdf(nome_familia, str(id_familia_val))
            
            # Layout com 2 botões lado a lado
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📄 Baixar Ficha Completa (PDF)",
                    data=pdf_bytes,
                    file_name=nome_arquivo_pdf,
                    mime="application/pdf",
                    key=f"download_ficha_pdf_{familia_serie.get('ID', 'familia')}",
                    use_container_width=True
                )
            
            with col2:
                # Gerar CSV simplificado
                csv_data = _gerar_csv_status_simplificado(familia_serie)
                if csv_data:
                    nome_csv = f"Status_Certidoes_{str(id_familia_val).replace(' ', '_')}.csv"
                    st.download_button(
                        label="📊 Baixar Tabela Status (CSV)",
                        data=csv_data,
                        file_name=nome_csv,
                        mime="text/csv",
                        key=f"download_csv_{familia_serie.get('ID', 'familia')}",
                        use_container_width=True
                    )
    except Exception as e:
        st.warning(f"Não foi possível gerar o PDF da ficha. Erro: {str(e)}")


def _gerar_csv_status_simplificado(familia_serie):
    """Gera CSV simplificado com status das certidões"""
    try:
        import io
        
        # Pegar dados do contexto PDF que já tem as informações processadas
        context_pdf = st.session_state.get('ficha_pdf_context', {})
        requerentes = context_pdf.get('requerentes', [])
        
        if not requerentes:
            return None
        
        # Criar buffer CSV
        csv_buffer = io.StringIO()
        
        # Cabeçalho
        csv_buffer.write("Família,ID Família,Posição,Requerente,Nascimento,Casamento,Óbito\n")
        
        # Nome e ID da família
        nome_familia = familia_serie.get('UF_CRM_1722883482527', 'N/D')
        id_familia = familia_serie.get('UF_CRM_1722605592778', 'N/D')
        
        # Função para simplificar status
        def simplificar_status(status_raw):
            """Simplifica status complexos para categorias principais"""
            if not status_raw or status_raw in ['N/D', 'Dispensado', 'Status N/D']:
                return 'Não iniciado'
            
            status = str(status_raw).upper()
            
            # Emitidas
            if any(x in status for x in ['EMITIDA', 'ENTREGUE', 'CERTIDÃO EMITIDA']):
                return 'Emitida ✓'
            
            # Solicitadas/Aguardando
            if any(x in status for x in ['AGUARDANDO', 'SOLICITADA', 'EM ANDAMENTO']):
                return 'Solicitada'
            
            # Pendências
            if any(x in status for x in ['PENDÊNCIA', 'DEVOLUÇÃO', 'DEVOLVIDO']):
                return 'Pendência'
            
            # Pesquisas
            if any(x in status for x in ['PESQUISA', 'BUSCA']):
                return 'Pesquisa'
            
            # Dispensadas/Canceladas
            if any(x in status for x in ['DISPENSADA', 'CANCELADO', 'DUPLICADA']):
                return 'Dispensada'
            
            # Aguardando cliente
            if 'DECISÃO CLIENTE' in status or 'AGUARDANDO CLIENTE' in status:
                return 'Aguardando Cliente'
            
            # Outros
            return status_raw if len(str(status_raw)) < 30 else 'Em processamento'
        
        # Processar cada requerente
        for req in requerentes:
            posicao = req.get('Posição', 'N/D')
            requerente = req.get('Requerente', 'N/D')
            nasc = simplificar_status(req.get('Nascimento', 'N/D'))
            casa = simplificar_status(req.get('Casamento', 'N/D'))
            obito = simplificar_status(req.get('Óbito', 'N/D'))
            
            # Escapar vírgulas e aspas no CSV
            def escape_csv(val):
                val_str = str(val).replace('"', '""')
                if ',' in val_str or '"' in val_str or '\n' in val_str:
                    return f'"{val_str}"'
                return val_str
            
            csv_buffer.write(f"{escape_csv(nome_familia)},{escape_csv(id_familia)},{escape_csv(posicao)},{escape_csv(requerente)},{escape_csv(nasc)},{escape_csv(casa)},{escape_csv(obito)}\n")
        
        # Adicionar linha de resumo
        csv_buffer.write("\n")
        csv_buffer.write("RESUMO GERAL\n")
        
        resumo = context_pdf.get('resumo', {})
        if resumo:
            csv_buffer.write("Categoria,Quantidade\n")
            for cat, qtd in resumo.items():
                if qtd > 0:
                    csv_buffer.write(f"{escape_csv(cat)},{qtd}\n")
            
            total = context_pdf.get('total_certidoes', 0)
            csv_buffer.write(f"TOTAL,{total}\n")
        
        return csv_buffer.getvalue()
        
    except Exception as e:
        print(f"[ERRO] Falha ao gerar CSV: {e}")
        return None


def _exibir_documentos_spa(familia_serie, requerentes_data):
    """Exibe seção de documentos da SPA"""
    from views.scaner.data_loader import carregar_dados_spa_scanner
    
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
                    def inferir_tipo_certidao(titulo: str) -> str:
                        t_norm = unidecode(str(titulo)).upper()
                        if 'CERTIDAO NASCIMENTO' in t_norm or 'NASCIMENTO' in t_norm or 'NASC' in t_norm:
                            return 'Nascimento'
                        if 'CERTIDAO CASAMENTO' in t_norm or 'MATRIMONIO' in t_norm or 'CASAMENTO' in t_norm:
                            return 'Casamento'
                        if 'CERTIDAO OBITO' in t_norm or 'OBITO' in t_norm or 'OBIT' in t_norm:
                            return 'Óbito'
                        return 'Outro'

                    docs_familia['Certidão'] = docs_familia['TITLE'].apply(inferir_tipo_certidao)

                    def escolher_link(row):
                        link_drive = str(row.get('UF_CRM_48_LINK_DRIVE', '')).strip()
                        link_scan = str(row.get('UF_CRM_48_DOCUMENTO_SCANEADO', '')).strip()
                        return link_drive if link_drive.lower().startswith('http') else (link_scan if link_scan.lower().startswith('http') else '')

                    docs_familia['Link'] = docs_familia.apply(escolher_link, axis=1)

                    # Mapa de IDs para nomes
                    id_to_name = {}
                    try:
                        if isinstance(requerentes_data, list):
                            for it in requerentes_data:
                                _id = str(it.get('ID_Requerente', '')).strip()
                                _nm = str(it.get('Requerente', '')).strip()
                                if _id and _id != 'ID Requerente N/D':
                                    id_to_name[_id] = _nm
                    except Exception:
                        id_to_name = {}

                    # Agrupar por requerente e exibir
                    for req_id, g in docs_familia.groupby('UF_CRM_48_ID_REQUERENTE'):
                        req_id_str = str(req_id)
                        display_name = id_to_name.get(req_id_str, f"Requerente {req_id_str}")
                        qtd = int(len(g))
                        with st.expander(f"{display_name} — {qtd} documento(s)", expanded=False):
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


