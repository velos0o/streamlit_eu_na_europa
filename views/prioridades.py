import streamlit as st
import pandas as pd

from api.bitrix_connector import load_merged_data
from utils.dataframe_utils import ensure_pandas_df
from views.cartorio_new.data_loader import carregar_dados_cartorio
from views.congelado import _status_protocolo_por_familia, render_congelado_content


REPUTACAO_FIELD = "UF_CRM_1759161772"
TIPOS_REPUTACAO = {
    "RECLAME AQUI": "Reclame Aqui",
    "EXTRAJUDICIAL": "Extrajudicial",
    "PROCON": "PROCON",
    "PROCESSO JUDICIAL": "Processo Judicial",
}

PRIORIDADES_RENAME_MAP = {
    "UF_CRM_1722883482527": "Nome da Família",
    "UF_CRM_1722605592778": "ID da Família",
    "TITLE": "Requerente",
    "ID": "ID Deal",
    "STAGE_ID": "Estágio",
}

STAGE_CODE_MAP = {
    "EMISSÃO BRASILEIRA": {"UC_8Z2EZF"},
    "ANÁLISE DOCUMENTAL": {"UC_N1FI74", "UC_SKSQFO", "UC_K952AX", "UC_2JQ8E2R"},
    "TRADUÇÃO": {"UC_CSFCZP"},
    "APOSTILAMENTO": {"UC_F12U3R"},
    "DRIVE": {"UC_1ARFYMM"},
    "RECURSO": {"UC_SISEKVR"},
    "PROTOCOLO": {"UC_5W7TYZ", "SUCCESS"},
}

STAGE_ORDER_MAP = {
    "EMISSÃO BRASILEIRA": 70,
    "ANÁLISE DOCUMENTAL": 90,
    "TRADUÇÃO": 130,
    "APOSTILAMENTO": 140,
    "DRIVE": 150,
    "RECURSO": 160,
    "PROTOCOLO": 170,
}

STAGE_COLUMNS_ORDER = [
    "Nome da Família",
    "ID da Família",
    "EMISSÃO BRASILEIRA",
    "ANÁLISE DOCUMENTAL",
    "TRADUÇÃO",
    "APOSTILAMENTO",
    "DRIVE",
    "RECURSO",
    "PROTOCOLO",
]


STAGE_NAME_KEYWORDS = {
    "EMISSÃO BRASILEIRA": {"EMISSAO BRASILEIRA"},
    "ANÁLISE DOCUMENTAL": {"ANALISE DOCUMENTAL"},
    "TRADUÇÃO": {"TRADUCAO"},
    "APOSTILAMENTO": {"APOSTILAMENTO"},
    "DRIVE": {"DRIVE"},
    "RECURSO": {"RECURSO"},
    "PROTOCOLO": {"PROTOCOLO", "CERTIDAO EMITIDA", "CERTIDAO ENTREGUE", "CERTIDAO PRONTA"},
}


def _normalize_text(txt: str) -> str:
    if txt is None:
        return ""
    import unicodedata

    txt = unicodedata.normalize("NFKD", str(txt).strip())
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    return txt.upper()


def _normalize_family_id(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if pd.isna(valor):
            return ""
        if isinstance(valor, float) and valor.is_integer():
            valor = int(valor)
        return str(valor).strip()
    s = str(valor).strip()
    if not s:
        return ""
    s = s.replace("\u00a0", "").replace(" ", "")
    if s.endswith(".0"):
        s = s[:-2]
    return s.upper()


def _normalizar_multivalorado(valor) -> list[str]:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return []
    if isinstance(valor, list):
        return [str(v).strip() for v in valor if str(v).strip()]
    s = str(valor).strip()
    if not s:
        return []
    try:
        import json

        parsed = json.loads(s)
        if isinstance(parsed, list):
            return [str(v).strip() for v in parsed if str(v).strip()]
    except Exception:
        pass
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    try:
        import re

        tokens = re.split(r"[\,\n;\|/\\\t]+", s)
        tokens = [t.strip().strip('"\'').strip() for t in tokens if t and t.strip()]
        return tokens if tokens else []
    except Exception:
        pass
    return [s]


def _carregar_prioridades_df() -> pd.DataFrame:
    df = load_merged_data(category_id=46, debug=False, force_reload=False)
    if df is None or df.empty:
        return pd.DataFrame()

    colunas_minimas = list(PRIORIDADES_RENAME_MAP.keys()) + [REPUTACAO_FIELD]
    for col in colunas_minimas:
        if col not in df.columns:
            df[col] = None

    df["__reputacao_lista__"] = df[REPUTACAO_FIELD].apply(_normalizar_multivalorado)

    def classificar(tokens: list[str]) -> dict[str, str]:
        resultado = {nome: "" for nome in TIPOS_REPUTACAO.values()}
        if not tokens:
            return resultado

        def _normalize(txt: str) -> str:
            import unicodedata

            txt = unicodedata.normalize("NFKD", str(txt).strip())
            txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
            return txt.upper()

        tokens_norm = {_normalize(t) for t in tokens if t}
        for chave, label in TIPOS_REPUTACAO.items():
            if _normalize(chave) in tokens_norm:
                resultado[label] = "SIM"
        return resultado

    reputacao_flags = df["__reputacao_lista__"].apply(classificar)
    df_flags = pd.DataFrame(list(reputacao_flags))
    df = pd.concat([df, df_flags], axis=1)

    colunas_flags = list(TIPOS_REPUTACAO.values())
    mask_any = df[colunas_flags].astype(str).apply(lambda col: col.str.upper() == "SIM").any(axis=1)
    df = df[mask_any].copy()
    if df.empty:
        colunas_vazias = [PRIORIDADES_RENAME_MAP.get(c, c) for c in PRIORIDADES_RENAME_MAP.keys()]
        return pd.DataFrame(columns=[*colunas_vazias, *colunas_flags])

    df = df.rename(columns=PRIORIDADES_RENAME_MAP)

    colunas = ["Nome da Família", "ID da Família", *colunas_flags, "Requerente", "ID Deal", "Estágio"]
    colunas_presentes = [col for col in colunas if col in df.columns]
    df = df[colunas_presentes].copy()

    sort_cols = [col for col in ["Nome da Família", "ID da Família"] if col in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols, kind="stable")

    return df


def _resumo_por_familia(df_prioridades: pd.DataFrame) -> pd.DataFrame:
    if df_prioridades is None or df_prioridades.empty:
        return pd.DataFrame()

    col_nome = "Nome da Família"
    col_id = "ID da Família"
    colunas_flags = [nome for nome in TIPOS_REPUTACAO.values() if nome in df_prioridades.columns]

    def any_sim(series: pd.Series) -> str:
        return "SIM" if (series.astype(str).str.upper() == "SIM").any() else ""

    agrupado = (
        df_prioridades.groupby([col for col in [col_nome, col_id] if col in df_prioridades.columns])[colunas_flags]
        .agg(any_sim)
        .reset_index()
    )
    return agrupado


def _metricas_macro(df_prioridades: pd.DataFrame) -> dict[str, int]:
    if df_prioridades is None or df_prioridades.empty:
        return {"Total Famílias": 0, **{label: 0 for label in TIPOS_REPUTACAO.values()}}

    col_id = "ID da Família"
    colunas_flags = [nome for nome in TIPOS_REPUTACAO.values() if nome in df_prioridades.columns]

    df_tmp = df_prioridades.copy()
    if col_id in df_tmp.columns:
        df_tmp[col_id] = df_tmp[col_id].astype(str).str.strip()

    total_familias = 0
    if col_id in df_tmp.columns:
        total_familias = df_tmp[col_id].replace("", pd.NA).dropna().nunique()
    elif not df_tmp.empty:
        total_familias = len(df_tmp)

    totais = {"Total Famílias": int(total_familias)}
    for flag in colunas_flags:
        if col_id in df_tmp.columns:
            totais[flag] = (
                df_tmp[df_tmp[flag].astype(str).str.upper() == "SIM"][col_id]
                .replace("", pd.NA)
                .dropna()
                .nunique()
            )
        else:
            totais[flag] = int((df_tmp[flag].astype(str).str.upper() == "SIM").sum())
    return totais


def _status_reputacao_por_familia(df_prioridades: pd.DataFrame) -> pd.DataFrame:
    if df_prioridades is None or df_prioridades.empty:
        return pd.DataFrame()

    col_nome = "Nome da Família" if "Nome da Família" in df_prioridades.columns else "UF_CRM_1722883482527"
    col_id = "ID da Família" if "ID da Família" in df_prioridades.columns else "UF_CRM_1722605592778"
    col_stage = "Estágio" if "Estágio" in df_prioridades.columns else "STAGE_ID"
    col_stage_name = "STAGE_NAME" if "STAGE_NAME" in df_prioridades.columns else None

    for c in [col_nome, col_id, col_stage]:
        if c not in df_prioridades.columns:
            return pd.DataFrame()

    colunas_util = [col_nome, col_id, col_stage]
    if col_stage_name:
        colunas_util.append(col_stage_name)

    df_trabalho = df_prioridades[colunas_util].copy()
    df_trabalho[col_stage] = df_trabalho[col_stage].astype(str)

    def detectar_maior_ordem(grupo_df: pd.DataFrame) -> int:
        if grupo_df is None or grupo_df.empty:
            return 0
        valores_stage_id = grupo_df[col_stage].dropna().astype(str).tolist()
        valores_stage_name = (
            grupo_df[col_stage_name].dropna().astype(str).tolist()
            if col_stage_name and col_stage_name in grupo_df.columns
            else []
        )
        maior = 0
        for valor in valores_stage_id:
            for etapa, codigos in STAGE_CODE_MAP.items():
                for codigo in codigos:
                    if codigo and codigo in valor:
                        maior = max(maior, STAGE_ORDER_MAP.get(etapa, 0))
            if "SUCCESS" in valor.upper():
                maior = max(maior, STAGE_ORDER_MAP.get("PROTOCOLO", 0))
        for valor in valores_stage_name:
            valor_norm = _normalize_text(valor)
            for etapa, keywords in STAGE_NAME_KEYWORDS.items():
                for keyword in keywords:
                    if keyword and keyword in valor_norm:
                        maior = max(maior, STAGE_ORDER_MAP.get(etapa, 0))
        return maior

    group_cols = [c for c in [col_nome, col_id] if c in df_trabalho.columns]
    if not group_cols:
        return pd.DataFrame()

    registros = []
    for chave, grupo in df_trabalho.groupby(group_cols):
        if isinstance(chave, tuple):
            nome_fam = chave[0]
            id_fam = chave[1] if len(chave) > 1 else ""
        else:
            nome_fam = chave
            id_fam = ""

        maior_ordem = detectar_maior_ordem(grupo)
        if maior_ordem <= 0:
            continue

        etapas_status = {}
        for etapa, ordem in STAGE_ORDER_MAP.items():
            etapas_status[etapa] = "✅" if maior_ordem >= ordem else ""

        registros.append({
            "Nome da Família": str(nome_fam) if nome_fam is not None else "",
            "ID da Família": str(id_fam) if id_fam is not None else "",
            **etapas_status,
            "__ORDEM_MAX__": maior_ordem,
        })

    df_out = pd.DataFrame(registros)
    if df_out.empty:
        return pd.DataFrame()

    df_out = df_out.sort_values(by="__ORDEM_MAX__", ascending=False, kind="stable").drop(columns=["__ORDEM_MAX__"])

    presentes = [c for c in STAGE_COLUMNS_ORDER if c in df_out.columns]
    if presentes:
        df_out = df_out[presentes]
    return df_out


def _carregar_emissoes_reputacao_df(df_prioridades: pd.DataFrame) -> pd.DataFrame:
    if df_prioridades is None or df_prioridades.empty:
        return pd.DataFrame()

    col_id_prior = "ID da Família" if "ID da Família" in df_prioridades.columns else "UF_CRM_1722605592778"
    if col_id_prior not in df_prioridades.columns:
        return pd.DataFrame()

    ids_reputacao = (
        df_prioridades[col_id_prior]
        .apply(_normalize_family_id)
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )
    if not ids_reputacao:
        return pd.DataFrame()

    df_emissoes = carregar_dados_cartorio()
    if df_emissoes is None or df_emissoes.empty:
        return pd.DataFrame()

    col_id_familia = "UF_CRM_34_ID_FAMILIA"
    if col_id_familia not in df_emissoes.columns:
        return pd.DataFrame()

    df_emissoes = df_emissoes.copy()
    df_emissoes[col_id_familia] = df_emissoes[col_id_familia].apply(_normalize_family_id)
    df_filtrado = df_emissoes[df_emissoes[col_id_familia].isin(ids_reputacao)].copy()
    return df_filtrado


def _status_emissoes_reputacao(df_prioridades: pd.DataFrame, df_emissoes_filtrado: pd.DataFrame | None = None) -> pd.DataFrame:
    if df_prioridades is None or df_prioridades.empty:
        return pd.DataFrame()

    if df_emissoes_filtrado is None:
        df_emissoes_filtrado = _carregar_emissoes_reputacao_df(df_prioridades)

    if df_emissoes_filtrado is None or df_emissoes_filtrado.empty:
        return pd.DataFrame()

    col_id_familia = "UF_CRM_34_ID_FAMILIA"
    col_nome_familia = (
        "UF_CRM_34_NOME_FAMILIA" if "UF_CRM_34_NOME_FAMILIA" in df_emissoes_filtrado.columns else None
    )
    col_stage = "STAGE_ID"
    if col_stage not in df_emissoes_filtrado.columns or col_id_familia not in df_emissoes_filtrado.columns:
        return pd.DataFrame()

    if col_nome_familia is None:
        col_nome_familia = "TITLE" if "TITLE" in df_emissoes_filtrado.columns else col_id_familia

    df_trabalho = df_emissoes_filtrado[[col for col in {col_id_familia, col_nome_familia, col_stage} if col in df_emissoes_filtrado.columns]].copy()
    col_stage_name = "STAGE_NAME" if "STAGE_NAME" in df_emissoes_filtrado.columns else None
    if col_stage_name:
        df_trabalho[col_stage_name] = df_emissoes_filtrado[col_stage_name]

    df_trabalho[col_stage] = df_trabalho[col_stage].astype(str)

    def detectar_maior_ordem(grupo_df: pd.DataFrame) -> int:
        if grupo_df is None or grupo_df.empty:
            return 0
        valores_stage_id = grupo_df[col_stage].dropna().astype(str).tolist()
        valores_stage_name = (
            grupo_df[col_stage_name].dropna().astype(str).tolist()
            if col_stage_name and col_stage_name in grupo_df.columns
            else []
        )
        maior = 0
        for valor in valores_stage_id:
            for etapa, codigos in STAGE_CODE_MAP.items():
                for codigo in codigos:
                    if codigo and codigo in valor:
                        maior = max(maior, STAGE_ORDER_MAP.get(etapa, 0))
            if "SUCCESS" in valor.upper():
                maior = max(maior, STAGE_ORDER_MAP.get("PROTOCOLO", 0))
        for valor in valores_stage_name:
            valor_norm = _normalize_text(valor)
            for etapa, keywords in STAGE_NAME_KEYWORDS.items():
                for keyword in keywords:
                    if keyword and keyword in valor_norm:
                        maior = max(maior, STAGE_ORDER_MAP.get(etapa, 0))
        return maior

    registros = []
    group_cols = [col for col in [col_nome_familia, col_id_familia] if col in df_trabalho.columns]
    if not group_cols:
        return pd.DataFrame()

    for chave, grupo in df_trabalho.groupby(group_cols):
        if isinstance(chave, tuple):
            nome_fam = chave[0]
            id_fam = chave[1] if len(chave) > 1 else ""
        else:
            nome_fam = chave
            id_fam = ""

        maior_ordem = detectar_maior_ordem(grupo)
        if maior_ordem <= 0:
            continue

        etapas_status = {}
        for etapa, ordem in STAGE_ORDER_MAP.items():
            etapas_status[etapa] = "✅" if maior_ordem >= ordem else ""

        registros.append({
            "Nome da Família": str(nome_fam) if nome_fam is not None else "",
            "ID da Família": str(id_fam) if id_fam is not None else "",
            **etapas_status,
            "__ORDEM_MAX__": maior_ordem,
        })

    df_out = pd.DataFrame(registros)
    if df_out.empty:
        return pd.DataFrame()

    df_out = df_out.sort_values(by="__ORDEM_MAX__", ascending=False, kind="stable").drop(columns=["__ORDEM_MAX__"])

    presentes = [c for c in STAGE_COLUMNS_ORDER if c in df_out.columns]
    if presentes:
        df_out = df_out[presentes]
    return df_out


def _metricas_emissoes(df_emiss: pd.DataFrame) -> dict[str, int]:
    if df_emiss is None or df_emiss.empty:
        return {
            "Famílias": 0,
            "Certidões": 0,
            "Requerentes": 0,
            "Concluídas": 0,
        }

    base_id_col = "UF_CRM_34_ID_FAMILIA" if "UF_CRM_34_ID_FAMILIA" in df_emiss.columns else "ID"
    col_requerente = "UF_CRM_34_ID_REQUERENTE" if "UF_CRM_34_ID_REQUERENTE" in df_emiss.columns else None

    df_tmp = df_emiss.copy()
    df_tmp[base_id_col] = df_tmp[base_id_col].astype(str).str.strip()
    total_familias = df_tmp[base_id_col].replace("", pd.NA).dropna().nunique()

    total_certidoes = len(df_tmp)
    if col_requerente and col_requerente in df_tmp.columns:
        total_requerentes = (
            df_tmp[df_tmp[col_requerente].astype(str).str.strip() != ""][col_requerente]
            .astype(str)
            .str.strip()
            .nunique()
        )
    else:
        total_requerentes = total_familias

    concluidas = 0
    if "STAGE_ID" in df_tmp.columns:
        mask_success = df_tmp["STAGE_ID"].astype(str).str.contains("SUCCESS", na=False)
        concluidas = int(mask_success.sum())
    elif "STAGE_NAME" in df_tmp.columns:
        concluidas = int(
            df_tmp["STAGE_NAME"].astype(str).str.upper().isin(["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]).sum()
        )

    return {
        "Famílias": int(total_familias),
        "Certidões": int(total_certidoes),
        "Requerentes": int(total_requerentes),
        "Concluídas": int(concluidas),
    }


def _render_emissoes_reputacao_content(
    df_emissoes: pd.DataFrame,
) -> None:
    if df_emissoes is None or df_emissoes.empty:
        st.info("Nenhum dado do SPA encontrado para as famílias de reputação.")
        return

    df_emissoes = df_emissoes.copy()
    df_emissoes.rename(
        columns={
            "UF_CRM_34_NOME_FAMILIA": "Nome da Família",
            "UF_CRM_34_ID_FAMILIA": "ID da Família",
        },
        inplace=True,
    )

    for col in ["Nome da Família", "ID da Família", "STAGE_NAME", "ASSIGNED_BY_NAME"]:
        if col not in df_emissoes.columns:
            df_emissoes[col] = ""

    st.markdown("#### ACOMPANHAMENTO DE EMISSÕES – REPUTAÇÃO")
    st.caption("Resumo das famílias de reputação em emissões brasileiras com filtros e detalhamento.")

    with st.expander("Filtros", expanded=True):
        col_f1, col_f2, col_f3 = st.columns([0.5, 0.25, 0.25])
        with col_f1:
            filtro_nome = st.text_input(
                "Buscar Família/Contrato:",
                placeholder="Digite parte do nome...",
            )
        with col_f2:
            etapas_disponiveis = (
                df_emissoes["STAGE_NAME"].dropna().astype(str).unique().tolist()
                if "STAGE_NAME" in df_emissoes.columns
                else []
            )
            filtro_etapas = st.multiselect(
                "Estágio:",
                options=sorted([e for e in etapas_disponiveis if e.strip()]),
            )
        with col_f3:
            responsaveis_disponiveis = (
                df_emissoes["ASSIGNED_BY_NAME"].dropna().astype(str).unique().tolist()
                if "ASSIGNED_BY_NAME" in df_emissoes.columns
                else []
            )
            filtro_responsavel = st.multiselect(
                "Responsável:",
                options=sorted([r for r in responsaveis_disponiveis if r.strip()]),
            )

    df_filtrado = df_emissoes.copy()
    if filtro_nome:
        df_filtrado = df_filtrado[
            df_filtrado["Nome da Família"].astype(str).str.contains(filtro_nome, case=False, na=False)
        ]
    if filtro_etapas:
        df_filtrado = df_filtrado[df_filtrado["STAGE_NAME"].astype(str).isin(filtro_etapas)]
    if filtro_responsavel:
        df_filtrado = df_filtrado[df_filtrado["ASSIGNED_BY_NAME"].astype(str).isin(filtro_responsavel)]

    total_familias_filtrado = (
        df_filtrado["Nome da Família"].astype(str).str.strip().replace("", pd.NA).dropna().nunique()
    )
    total_certidoes_filtrado = len(df_filtrado)

    df_calculo = df_filtrado.copy()
    if "STAGE_ID" in df_calculo.columns:
        mask_success = df_calculo["STAGE_ID"].astype(str).str.contains("SUCCESS", na=False)
    else:
        mask_success = pd.Series(False, index=df_calculo.index)
    if "STAGE_NAME" in df_calculo.columns:
        mask_success = mask_success | df_calculo["STAGE_NAME"].astype(str).str.upper().isin(
            ["CERTIDÃO EMITIDA", "CERTIDÃO ENTREGUE"]
        )
    df_calculo["__success__"] = mask_success.astype(int)

    concluidas_filtrado = int(df_calculo["__success__"].sum())
    pendentes_filtrado = int(total_certidoes_filtrado - concluidas_filtrado)

    perc_conclusao = (concluidas_filtrado / total_certidoes_filtrado * 100) if total_certidoes_filtrado > 0 else 0.0

    st.markdown(
        """
        <style>
        .metricas-container-reput-top { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 12px 0 4px 0; }
        .metrica-custom-reput { background: #F8F9FA; border: 2px solid #DEE2E6; border-radius: 6px; padding: 16px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .metrica-custom-reput:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: #ADB5BD; }
        .metrica-custom-reput .label { color: #6C757D; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; line-height: 1.2; }
        .metrica-custom-reput .valor { color: #495057; font-weight: 700; font-size: 30px; line-height: 1.2; margin-bottom: 4px; }
        .metricas-container-reput-sec { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 12px 0 4px 0; }
        .metrica-reput-emitidas { background: #E8F5E9; border-color: #A5D6A7; }
        .metrica-reput-pendentes { background: #FFF3E0; border-color: #FFCC80; }
        </style>
        <div class="metricas-container-reput-top">
            <div class="metrica-custom-reput"><div class="label">Famílias</div><div class="valor">""" + str(int(total_familias_filtrado)) + """</div></div>
            <div class="metrica-custom-reput"><div class="label">% Conclusão (itens)</div><div class="valor">""" + (f"{perc_conclusao:.1f}%") + """</div></div>
        </div>
        <div class="metricas-container-reput-sec">
            <div class="metrica-custom-reput metrica-reput-emitidas"><div class="label">Certidões Emitidas</div><div class="valor">""" + str(int(concluidas_filtrado)) + """</div></div>
            <div class="metrica-custom-reput metrica-reput-pendentes"><div class="label">Certidões Pendentes</div><div class="valor">""" + str(max(pendentes_filtrado, 0)) + """</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.info("Nenhuma família de reputação encontrada com os filtros selecionados.")
        return

    group_cols = [col for col in ["Nome da Família", "ID da Família"] if col in df_filtrado.columns]
    df_group = df_calculo.copy()
    if "ASSIGNED_BY_NAME" in df_group.columns:
        df_group["ASSIGNED_BY_NAME"] = df_group["ASSIGNED_BY_NAME"].astype(str)

    agg_dict = {
        "total_certidoes": ("__success__", "count"),
        "concluidas": ("__success__", "sum"),
    }
    if "ASSIGNED_BY_NAME" in df_group.columns:
        agg_dict["Responsável"] = ("ASSIGNED_BY_NAME", "first")
    if "STAGE_NAME" in df_group.columns:
        agg_dict["Estágio Atual"] = ("STAGE_NAME", "last")

    df_acomp = df_group.groupby(group_cols).agg(**agg_dict).reset_index()
    df_acomp["Percentual"] = df_acomp.apply(
        lambda r: (r["concluidas"] / r["total_certidoes"] * 100) if r["total_certidoes"] > 0 else 0.0,
        axis=1,
    )
    df_acomp["Concluídas/Total"] = df_acomp.apply(
        lambda r: f"{int(r['concluidas'])}/{int(r['total_certidoes'])}",
        axis=1,
    )

    st.dataframe(
        ensure_pandas_df(df_acomp),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Nome da Família": st.column_config.TextColumn("Nome da Família", width="large"),
            "ID da Família": st.column_config.TextColumn("ID da Família", width="medium"),
            "Responsável": st.column_config.TextColumn("Responsável", width="medium"),
            "Estágio Atual": st.column_config.TextColumn("Estágio Atual", width="medium"),
            "total_certidoes": st.column_config.NumberColumn("Total Certidões", format="%d"),
            "concluidas": st.column_config.NumberColumn("Concluídas", format="%d"),
            "Concluídas/Total": st.column_config.TextColumn("Concluídas/Total", width="small"),
            "Percentual": st.column_config.ProgressColumn(
                "Percentual",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )


def _render_metric_card(label: str, valor: int | float | str) -> str:
    return (
        "<div class=\"metrica-custom-macro\">"
        f"<div class=\"label\">{label}</div>"
        f"<div class=\"valor\">{valor}</div>"
        "</div>"
    )


def show_prioridades():
    st.markdown("<h1 class='page-title'>Prioridades - Reputação</h1>", unsafe_allow_html=True)

    st.session_state['prioridades_subpagina'] = 'reputacao'

    with st.spinner("Carregando dados de reputação..."):
        df_prioridades = _carregar_prioridades_df()

    if df_prioridades.empty:
        st.info("Nenhum registro encontrado para os canais de reputação selecionados.")
        return

    # --- Métricas Macros (no topo) ---
    metricas = _metricas_macro(df_prioridades)

    st.markdown("#### MÉTRICAS MACROS")
    st.markdown("""
    <style>
    .metricas-container-macro { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin: 12px 0 16px 0; }
    .metrica-custom-macro { background: #F8F9FA; border: 2px solid #DEE2E6; border-radius: 6px; padding: 16px; text-align: center; min-height: 110px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metrica-custom-macro:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: #ADB5BD; }
    .metrica-custom-macro .label { color: #6C757D; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; line-height: 1.2; }
    .metrica-custom-macro .valor { color: #495057; font-weight: 700; font-size: 30px; line-height: 1.2; margin-bottom: 4px; }
    </style>
    """, unsafe_allow_html=True)

    cards_html = "".join([
        _render_metric_card(label, int(valor) if isinstance(valor, (int, float)) else valor)
        for label, valor in metricas.items()
    ])
    st.markdown(f"<div class='metricas-container-macro'>{cards_html}</div>", unsafe_allow_html=True)

    st.markdown("---")  # Separador visual

    # --- Restante do conteúdo ---
    df_emissoes_reputacao = _carregar_emissoes_reputacao_df(df_prioridades)

    st.markdown("#### STATUS REPUTAÇÃO – ETAPAS DO FUNIL")
    st.caption("Etapas concluídas por família com base no funil 46 (Congelados). ✅ indica etapa concluída.")
    df_status_reputacao = _status_reputacao_por_familia(df_prioridades)
    if df_status_reputacao.empty:
        st.info("Nenhuma família com etapas de reputação identificadas no funil.")
    else:
        st.dataframe(
            ensure_pandas_df(df_status_reputacao),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Nome da Família": st.column_config.TextColumn("Nome da Família", width="large"),
                "ID da Família": st.column_config.TextColumn("ID da Família", width="medium"),
                "EMISSÃO BRASILEIRA": st.column_config.TextColumn("EMISSÃO BRASILEIRA", width="small"),
                "ANÁLISE DOCUMENTAL": st.column_config.TextColumn("ANÁLISE DOCUMENTAL", width="small"),
                "TRADUÇÃO": st.column_config.TextColumn("TRADUÇÃO", width="small"),
                "APOSTILAMENTO": st.column_config.TextColumn("APOSTILAMENTO", width="small"),
                "DRIVE": st.column_config.TextColumn("DRIVE", width="small"),
                "RECURSO": st.column_config.TextColumn("RECURSO", width="small"),
                "PROTOCOLO": st.column_config.TextColumn("PROTOCOLO", width="small"),
            },
        )

    with st.expander("REGISTROS DETALHADOS", expanded=False):
        st.dataframe(
            ensure_pandas_df(df_prioridades),
            hide_index=True,
            use_container_width=True,
        )

    with st.expander("RESUMO POR FAMÍLIA", expanded=False):
        df_resumo = _resumo_por_familia(df_prioridades)
        if df_resumo.empty:
            st.info("Não foi possível agrupar registros por família.")
        else:
            st.dataframe(
                ensure_pandas_df(df_resumo),
                hide_index=True,
                use_container_width=True,
            )

    if df_emissoes_reputacao is None or df_emissoes_reputacao.empty:
        st.info("Nenhum dado do SPA encontrado para as famílias de reputação.")
        return

    _render_emissoes_reputacao_content(df_emissoes_reputacao)

