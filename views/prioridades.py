import streamlit as st
import pandas as pd

from api.bitrix_connector import load_merged_data
from utils.dataframe_utils import ensure_pandas_df
from views.congelado import carregar_congelados_df, render_congelado_content


REPUTACAO_FIELD = "UF_CRM_1759161772"
TIPOS_REPUTACAO = {
    "RECLAME AQUI": "Reclame Aqui",
    "EXTRAJUDICIAL": "Extrajudicial",
    "PROCON": "PROCON",
    "PROCESSO JUDICIAL": "Processo Judicial",
}


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

    for col in ["UF_CRM_1722883482527", "UF_CRM_1722605592778", REPUTACAO_FIELD, "TITLE", "ID", "STAGE_ID"]:
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
        return pd.DataFrame(columns=["UF_CRM_1722883482527", "UF_CRM_1722605592778", *colunas_flags, "TITLE", "ID", "STAGE_ID"])

    rename_map = {
        "UF_CRM_1722883482527": "Nome da Família",
        "UF_CRM_1722605592778": "ID da Família",
        "TITLE": "Requerente",
        "ID": "ID Deal",
        "STAGE_ID": "Estágio",
    }
    df = df.rename(columns=rename_map)

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


def _render_metric_card(label: str, valor: int) -> str:
    return f"""
    <div class="metrica-custom-prioridade">
        <div class="label">{label}</div>
        <div class="valor">{valor}</div>
    </div>
    """


def show_prioridades():
    st.markdown("<h1 class='page-title'>Prioridades - Reputação</h1>", unsafe_allow_html=True)

    tab = st.session_state.get('prioridades_subpagina', 'reputacao')

    with st.spinner("Carregando dados de reputação..."):
        df_prioridades = _carregar_prioridades_df()

    with st.expander("Reputação", expanded=True):
        if df_prioridades.empty:
            st.info("Nenhum registro encontrado para os canais de reputação selecionados.")
        else:
            metricas = _metricas_macro(df_prioridades)
            st.markdown("#### Métricas Macros")
            metric_items = list(metricas.items())
            cols_por_linha = min(len(metric_items), 4)
            if cols_por_linha == 0:
                cols_por_linha = 1
            for i in range(0, len(metric_items), cols_por_linha):
                row = metric_items[i:i + cols_por_linha]
                cols = st.columns(len(row))
                for (label, valor), col in zip(row, cols):
                    col.metric(label, int(valor))

            st.markdown("#### Registros Detalhados")
            st.dataframe(
                ensure_pandas_df(df_prioridades),
                hide_index=True,
                use_container_width=True,
            )

            st.markdown("#### Resumo por Família")

            df_resumo = _resumo_por_familia(df_prioridades)
            if df_resumo.empty:
                st.info("Não foi possível agrupar registros por família.")
            else:
                st.dataframe(
                    ensure_pandas_df(df_resumo),
                    hide_index=True,
                    use_container_width=True,
                )

    st.markdown("---")
    st.markdown("#### Congelado")

    with st.spinner("Carregando dados de congelados..."):
        df_congelados = carregar_congelados_df()

    if df_congelados.empty:
        st.info("Nenhum registro congelado encontrado no funil 46.")
    else:
        render_congelado_content(df_congelados)

