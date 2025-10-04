"""
Módulo de métricas e estatísticas para Ficha da Família
"""
import html
import streamlit as st
import pandas as pd
from unidecode import unidecode
from utils.dataframe_utils import ensure_pandas_df


# ==========================
# Constantes de mapeamento
# ==========================

ETAPAS_PROCESSO_ORDENADAS = [
    ("EMISSÃO BRASILEIRA", 70),
    ("ANÁLISE DOCUMENTAL", 90),
    ("TRADUÇÃO", 130),
    ("APOSTILAMENTO", 140),
    ("DRIVE", 150),
    ("RECURSO", 160),
    ("PROTOCOLO", 170),
]

ORDEM_POR_ETAPA = {etapa: ordem for etapa, ordem in ETAPAS_PROCESSO_ORDENADAS}

CODIGOS_POR_ETAPA = {
    "EMISSÃO BRASILEIRA": {"UC_8Z2EZF"},
    "ANÁLISE DOCUMENTAL": {"UC_N1FI74", "UC_SKSQFO", "UC_K952AX", "UC_2JQ8E2R"},
    "TRADUÇÃO": {"UC_CSFCZP"},
    "APOSTILAMENTO": {"UC_F12U3R"},
    "DRIVE": {"UC_1ARFYMM"},
    "RECURSO": {"UC_SISEKVR"},
    "PROTOCOLO": {"UC_5W7TYZ"},
}

STAGE_KEYWORDS = {
    "PROTOCOLO": ["PROTOCOLO", "WON", "SUCCESS"],
    "RECURSO": ["RECURSO"],
    "DRIVE": ["DRIVE"],
    "APOSTILAMENTO": ["APOSTILAMENTO", "APOSTILA"],
    "TRADUÇÃO": ["TRADUCAO", "TRADU", "TRADUÇÃO"],
    "ANÁLISE DOCUMENTAL": ["ANALISE DOCUMENTAL", "ANALISE", "ANÁLISE DOCUMENTAL"],
    "EMISSÃO BRASILEIRA": ["EMISSAO", "EMISSÃO", "EMISSAO BRASILEIRA", "EMISSÃO BRASILEIRA"],
}

ESTEIRA_ORDEM = [
    "CONGELADO",
    "DISTRATO",
    "FLUXO NORMAL",
    "GERAR PROVAS",
    "PRIORIDADE ATENDIMENTO",
    "PROMESSAS",
    "PROTOCOLADO",
]

ESTEIRA_STYLE_MAP = {
    "CONGELADO": {"bg": "#F4F6F9", "border": "#CBD5E1", "color": "#0F172A"},
    "DISTRATO": {"bg": "#F3F4F6", "border": "#D1D5DB", "color": "#1F2937"},
    "FLUXO NORMAL": {"bg": "#F1F5F9", "border": "#C7D2FE", "color": "#111827"},
    "GERAR PROVAS": {"bg": "#EEF2F6", "border": "#CBD5E1", "color": "#1F2937"},
    "PRIORIDADE ATENDIMENTO": {"bg": "#F3F6FB", "border": "#C7D2FE", "color": "#111827"},
    "PROMESSAS": {"bg": "#F1F4F8", "border": "#D1D5DB", "color": "#1F2937"},
    "PROTOCOLADO": {"bg": "#EEF4FB", "border": "#BFDBFE", "color": "#0F172A"},
}

DEFAULT_ESTEIRA_STYLE = {"bg": "#F7F8FA", "border": "#E4E6EB", "color": "#1F2937"}


def calcular_maior_ordem_para_grupo(stages_df: pd.DataFrame) -> int:
    """Retorna a maior ordem (etapa concluída) para um conjunto de estágios."""
    if stages_df is None or stages_df.empty:
        return 0

    maior = 0

    try:
        if "STAGE_SEMANTIC_ID" in stages_df.columns:
            semanticas = (
                stages_df["STAGE_SEMANTIC_ID"].dropna().astype(str).str.upper().tolist()
            )
            if any(s in ["S", "SUCCESS", "WON"] for s in semanticas):
                maior = max(maior, ORDEM_POR_ETAPA.get("PROTOCOLO", 170))
    except Exception:
        pass

    valores_id = []
    valores_nome = []

    try:
        if "STAGE_ID" in stages_df.columns:
            valores_id = stages_df["STAGE_ID"].dropna().astype(str).tolist()
    except Exception:
        valores_id = []

    try:
        if "STAGE_NAME" in stages_df.columns:
            valores_nome = stages_df["STAGE_NAME"].dropna().astype(str).tolist()
    except Exception:
        valores_nome = []

    tokens = [unidecode(str(v)).upper() for v in (valores_id + valores_nome)]

    for etapa, codigos in CODIGOS_POR_ETAPA.items():
        for codigo in codigos:
            if any(codigo in token for token in tokens):
                maior = max(maior, ORDEM_POR_ETAPA.get(etapa, 0))

    for etapa, keywords in STAGE_KEYWORDS.items():
        if any(any(kw in token for kw in keywords) for token in tokens):
            maior = max(maior, ORDEM_POR_ETAPA.get(etapa, 0))

    return maior


def obter_etapa_por_ordem(ordem: int) -> str:
    """Retorna o rótulo da etapa correspondente à ordem informada."""
    etapa_atual = "Sem Etapa"
    for etapa, ordem_minima in ETAPAS_PROCESSO_ORDENADAS:
        if ordem >= ordem_minima:
            etapa_atual = etapa
    return etapa_atual


def normalizar_esteira(valor) -> str:
    """Normaliza o valor da esteira para texto padrão."""
    texto = str(valor or "").strip()
    if not texto:
        return "Não informado"
    return texto.upper()


def gerar_relatorio_por_esteira(df_crm_deals_full_local: pd.DataFrame) -> pd.DataFrame:
    """Gera tabela de contagem por etapa do processo separada por esteira."""
    if df_crm_deals_full_local is None or df_crm_deals_full_local.empty:
        return pd.DataFrame()

    col_id_familia = "UF_CRM_1722605592778"
    col_esteira = "UF_CRM_ESTEIRA"

    if col_id_familia not in df_crm_deals_full_local.columns:
        return pd.DataFrame()

    stage_cols = [
        c for c in ["STAGE_ID", "STAGE_NAME", "STAGE_SEMANTIC_ID"] if c in df_crm_deals_full_local.columns
    ]
    if not stage_cols:
        return pd.DataFrame()

    df_base = df_crm_deals_full_local[[col_id_familia] + stage_cols + ([col_esteira] if col_esteira in df_crm_deals_full_local.columns else [])].copy()
    df_base[col_id_familia] = df_base[col_id_familia].astype(str).str.strip()

    registros = []

    for fam_id, grupo in df_base.groupby(col_id_familia):
        stages_df = grupo[stage_cols]
        maior_ordem = calcular_maior_ordem_para_grupo(stages_df)
        etapa_label = obter_etapa_por_ordem(maior_ordem)

        esteira_valor = ""
        if col_esteira in grupo.columns:
            esteiras_validas = grupo[col_esteira].dropna().astype(str).str.strip()
            if not esteiras_validas.empty:
                esteira_valor = esteiras_validas.iloc[0]

        registros.append({
            "Esteira": normalizar_esteira(esteira_valor),
            "Etapa": etapa_label,
        })

    if not registros:
        return pd.DataFrame()

    df_registros = pd.DataFrame(registros)
    df_registros["Contagem"] = 1

    df_pivot = (
        df_registros
        .groupby(["Esteira", "Etapa"], dropna=False)["Contagem"]
        .sum()
        .unstack(fill_value=0)
    )

    colunas_desejadas = [etapa for etapa, _ in ETAPAS_PROCESSO_ORDENADAS] + ["Sem Etapa"]
    colunas_presentes = [c for c in colunas_desejadas if c in df_pivot.columns]
    colunas_extras = [c for c in df_pivot.columns if c not in colunas_presentes]
    df_pivot = df_pivot.reindex(columns=colunas_presentes + sorted(colunas_extras), fill_value=0)

    ordem_esteira = [e for e in ESTEIRA_ORDEM if e in df_pivot.index]
    outras_esteiras = [e for e in df_pivot.index if e not in ordem_esteira]
    df_pivot = df_pivot.reindex(ordem_esteira + sorted(outras_esteiras), fill_value=0)

    df_pivot["Total"] = df_pivot.sum(axis=1)
    df_pivot.loc["TOTAL GERAL"] = df_pivot.sum(axis=0)

    return df_pivot


SIMPLICITY_BADGE_COLOR = "#1F2937"


def _render_kaban_card_html(esteira: str, linha: pd.Series) -> str:
    """Constrói o HTML de um cartão estilo Kanban para a esteira informada."""
    estilo = ESTEIRA_STYLE_MAP.get(esteira, DEFAULT_ESTEIRA_STYLE)

    esteira_upper = esteira.upper()

    itens_html = []
    if esteira_upper != "DISTRATO":
        for etapa, _ in ETAPAS_PROCESSO_ORDENADAS + [("Sem Etapa", 0)]:
            if etapa not in linha:
                continue
            valor = int(linha.get(etapa, 0))
            valor_str = str(valor)
            muted_class = " muted" if valor == 0 else ""
            itens_html.append(
                "<div class='esteira-item" + muted_class + "'>"
                + f"<span class='esteira-item-label'>{html.escape(etapa)}</span>"
                + f"<span class='esteira-item-value'>{valor_str}</span>"
                + "</div>"
            )
    else:
        itens_html.append(
            "<div class='esteira-item resumo-distrato'>"
            "<span class='esteira-item-label'>Status</span>"
            + "<span class='esteira-item-value'>Processos rescindidos</span>"
            + "</div>"
        )

    total_val = int(linha.get("Total", 0))

    return (
        f"<div class='esteira-card' style=\"--card-bg:{estilo['bg']}; --card-border:{estilo['border']}; --card-text:{estilo['color']};\">"
        f"<div class='esteira-card-head'>"
        f"<span class='esteira-badge'>{html.escape(esteira)}</span>"
        f"<span class='esteira-total'>{total_val}</span>"
        "</div>"
        f"<div class='esteira-items'>{''.join(itens_html)}</div>"
        "</div>"
    )


def _exibir_kaban_por_esteira(relatorio_df: pd.DataFrame):
    """Renderiza os cartões Kanban das esteiras em layout responsivo."""
    if relatorio_df is None or relatorio_df.empty:
        st.info("Não foi possível gerar o relatório por esteira (dados insuficientes).")
        return

    total_geral = relatorio_df.loc["TOTAL GERAL"] if "TOTAL GERAL" in relatorio_df.index else pd.Series(dtype=float)
    relatorio_sem_total = relatorio_df.drop(index=["TOTAL GERAL"], errors="ignore")

    cards_html = "".join(_render_kaban_card_html(esteira, linha) for esteira, linha in relatorio_sem_total.iterrows())

    summary_parts = []
    if not total_geral.empty:
        for etapa, _ in ETAPAS_PROCESSO_ORDENADAS + [("Sem Etapa", 0)]:
            if etapa in total_geral:
                summary_parts.append(f"<span>{html.escape(etapa)} <strong>{int(total_geral[etapa])}</strong></span>")
        summary_parts.append(f"<span>Total Geral <strong>{int(total_geral.get('Total', 0))}</strong></span>")

    summary_html = "".join(summary_parts) if summary_parts else ""

    summary_block = f"<div class='esteira-summary'>{summary_html}</div>" if summary_html else ""

    html_template = """
    <style>
    .esteira-section {
        margin-top: 8px;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .esteira-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 18px;
    }
    @media (max-width: 1500px) {
        .esteira-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
    }
    @media (max-width: 1100px) {
        .esteira-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    @media (max-width: 720px) {
        .esteira-grid {
            grid-template-columns: repeat(1, minmax(0, 1fr));
        }
    }
        .esteira-card {
            position: relative;
            background: linear-gradient(135deg, var(--card-bg, #FFFFFF) 0%, rgba(255,255,255,0.95) 90%);
            border: 1px solid var(--card-border, #E5E7EB);
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 12px 22px rgba(15, 23, 42, 0.08);
            color: var(--card-text, #1F2937);
            display: flex;
            flex-direction: column;
            gap: 12px;
            overflow: hidden;
        }
    .esteira-card::before,
    .esteira-card::after {
        content: "";
        position: absolute;
        border-radius: inherit;
        inset: 0;
        z-index: -1;
    }
    .esteira-card::before {
        transform: translate(-6px, -6px);
        background: linear-gradient(135deg, rgba(148, 163, 184, 0.16), rgba(148, 163, 184, 0));
        opacity: 0.5;
    }
    .esteira-card::after {
        transform: translate(6px, 6px);
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.08), rgba(15, 23, 42, 0));
        filter: blur(0.35px);
        opacity: 0.28;
    }
    .esteira-card-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .esteira-badge {
        font-weight: 600;
        font-size: 0.82rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .esteira-total {
        background: rgba(31, 41, 55, 0.08);
        color: #111827;
        border-radius: 999px;
        padding: 3px 10px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .esteira-items {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 10px;
    }
    .esteira-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 10px;
        border-radius: 12px;
        border: 1px solid rgba(17, 24, 39, 0.08);
        background: rgba(255, 255, 255, 0.78);
    }
    .esteira-item.muted {
        opacity: 0.45;
    }
    .esteira-item-label {
        font-size: 0.76rem;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .esteira-item-value {
        font-weight: 600;
        font-size: 0.85rem;
    }
    .esteira-item.resumo-distrato {
        justify-content: center;
        flex-direction: column;
        text-align: center;
        gap: 4px;
        padding: 16px 12px;
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.18);
    }
    .esteira-item.resumo-distrato .esteira-item-label {
        font-size: 0.75rem;
        opacity: 0.65;
    }
    .esteira-summary {
        padding: 14px 16px;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        background: #ECEFF4;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 10px;
    }
    .esteira-summary span {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 12px;
        border-radius: 8px;
        border: 1px solid #D3DAE6;
        background: #FFFFFF;
        font-size: 0.78rem;
        font-weight: 500;
        letter-spacing: 0.02em;
        color: #111827;
    }
    .esteira-summary strong {
        font-size: 0.92rem;
        font-weight: 600;
        color: #0F172A;
    }
    .esteira-summary span::before {
        content: "";
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 999px;
        background: #1F2937;
        margin-right: 8px;
    }
    </style>
    <div class="esteira-section">
        <div class="esteira-grid">
            __CARDS__
        </div>
        __SUMMARY__
    </div>
    """

    st.markdown(
        html_template
        .replace("__CARDS__", cards_html)
        .replace("__SUMMARY__", summary_block),
        unsafe_allow_html=True,
    )


def exibir_metricas_macro(df_crm_deals_full_local, df_spa_base):
    """Exibe métricas macro gerais das famílias"""
    
    # ============================
    # STATUS DE PROTOCOLO (GERAL)
    # ============================
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
                stage_cols = [c for c in ['STAGE_ID', 'STAGE_NAME', 'STAGE_SEMANTIC_ID'] if c in df_f46.columns]

                maiores = []
                for fam_id, g in df_f46.groupby(col_id_familia):
                    stages_df = g[stage_cols] if stage_cols else pd.DataFrame()
                    maior = calcular_maior_ordem_para_grupo(stages_df)
                    maiores.append(maior)
                limite_protocolo = ORDEM_POR_ETAPA.get('PROTOCOLO', 170)
                familias_concluidas_protocolo = sum(1 for m in maiores if m >= limite_protocolo)
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

    # Tabela de status de protocolo
    df_status_geral = _status_protocolo_por_familia_geral(df_crm_deals_full_local)
    
    st.markdown("---")
    st.markdown("#### STATUS FAMÍLIAS")
    st.caption("Etapas concluídas até o protocolo para todas as famílias do funil 46.")

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

    col_id_familia_spa = 'UF_CRM_34_ID_FAMILIA'
    col_nome_familia_spa = 'UF_CRM_34_NOME_FAMILIA'
    col_resp_spa = 'ASSIGNED_BY_NAME'

    if df_spa_base is None or df_spa_base.empty or col_id_familia_spa not in df_spa_base.columns:
        st.info("Sem dados suficientes para o acompanhamento geral.")
        return

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

    # Tabela de Progresso
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

    relatorio_esteira_df = gerar_relatorio_por_esteira(df_crm_deals_full_local)

    st.markdown("---")
    st.markdown("#### RELATÓRIO POR ESTEIRA (FUNIL 46)")
    st.caption("Contagem de famílias por etapa principal do processo separada por esteira (UF_CRM_ESTEIRA).")

    _exibir_kaban_por_esteira(relatorio_esteira_df)


def _status_protocolo_por_familia_geral(df_cat46: pd.DataFrame) -> pd.DataFrame:
    """Gera tabela de status de protocolo por família"""
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


