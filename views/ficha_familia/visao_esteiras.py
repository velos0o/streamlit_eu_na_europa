"""
Visão consolidada por esteira para cruzar dados do funil 46 com emissões brasileiras.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

try:
    from views.cartorio_new.utils import simplificar_nome_estagio
except ImportError:  # fallback mínimo
    def simplificar_nome_estagio(valor):
        return str(valor or "")


ESTEIRA_ORDER = [
    "CONGELADO",
    "DISTRATO",
    "FLUXO NORMAL",
    "GERAR PROVAS",
    "PRIORIDADE ATENDIMENTO",
    "PROMESSAS",
    "PROTOCOLADO",
    "NÃO SELECIONADA",
    "NÃO INFORMADA",
]


def _normalizar_esteira(valor) -> str:
    texto = str(valor or "").strip()
    if not texto:
        return "NÃO INFORMADA"
    return texto.upper()


@st.cache_data(show_spinner=False)
def _construir_pivot_macro(
    df_familias: pd.DataFrame, df_emissoes: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Constrói uma tabela cruzada Esteira x Estágio (contagem)."""

    if df_familias is None or df_familias.empty:
        return pd.DataFrame(), pd.DataFrame()
    if df_emissoes is None or df_emissoes.empty:
        return pd.DataFrame(), pd.DataFrame()

    col_familia = "UF_CRM_1722605592778"
    col_emissao_familia = "UF_CRM_34_ID_FAMILIA"
    col_esteira = "UF_CRM_ESTEIRA"

    if col_emissao_familia not in df_emissoes.columns or col_familia not in df_familias.columns:
        return pd.DataFrame(), pd.DataFrame()

    df_fam = df_familias[[col_familia, col_esteira]].copy()
    df_fam[col_familia] = df_fam[col_familia].fillna("").astype(str).str.strip()
    df_fam[col_esteira] = df_fam[col_esteira].apply(_normalizar_esteira)

    df_fam = df_fam[df_fam[col_familia] != ""]
    if df_fam.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_aux = df_emissoes.copy()
    df_aux[col_emissao_familia] = df_aux[col_emissao_familia].fillna("").astype(str).str.strip()
    df_aux = df_aux[df_aux[col_emissao_familia] != ""]
    if df_aux.empty:
        return pd.DataFrame(), pd.DataFrame()

    if "STAGE_ID" in df_aux.columns:
        df_aux["STAGE_NAME_LEGIVEL"] = df_aux["STAGE_ID"].apply(simplificar_nome_estagio)
    elif "STAGE_NAME" in df_aux.columns:
        df_aux["STAGE_NAME_LEGIVEL"] = df_aux["STAGE_NAME"].apply(simplificar_nome_estagio)
    else:
        df_aux["STAGE_NAME_LEGIVEL"] = df_aux.get("STAGE_NAME_LEGIVEL", "")

    df_aux = df_aux[df_aux["STAGE_NAME_LEGIVEL"].astype(str).str.strip() != ""]
    if df_aux.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_merge = df_aux.merge(
        df_fam,
        left_on=col_emissao_familia,
        right_on=col_familia,
        how="inner",
    )
    if df_merge.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Construir identificador único para o card
    possiveis_ids = [
        "ID",
        "UF_CRM_34_ID_CERTIDAO",
        "UF_CRM_48_ID_CARD",
        "UF_CRM_34_ID_NEGOCIO",
        "UF_CRM_34_ID_CARTORIO",
    ]
    df_merge["__CARD_ID__"] = ""
    for coluna in possiveis_ids:
        if coluna in df_merge.columns:
            df_merge["__CARD_ID__"] = df_merge["__CARD_ID__"].where(
                df_merge["__CARD_ID__"].astype(str).str.strip() != "",
                df_merge[coluna].fillna("").astype(str).str.strip(),
            )
    df_merge["__CARD_ID__"] = df_merge["__CARD_ID__"].where(
        df_merge["__CARD_ID__"].astype(str).str.strip() != "",
        df_merge[col_emissao_familia] + "::" + df_merge["STAGE_NAME_LEGIVEL"],
    )

    df_merge = df_merge[df_merge["__CARD_ID__"].astype(str).str.strip() != ""]
    if df_merge.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_merge = df_merge.sort_values(by=["__CARD_ID__", "STAGE_NAME_LEGIVEL"]).drop_duplicates(
        subset=["__CARD_ID__"], keep="last"
    )

    pivot = (
        df_merge.pivot_table(
            index=col_esteira,
            columns="STAGE_NAME_LEGIVEL",
            values="__CARD_ID__",
            aggfunc=lambda x: len(pd.unique(x)),
            fill_value=0,
        )
        .astype(int)
    )

    if pivot.empty:
        return pivot, df_merge

    pivot = pivot.reindex(ESTEIRA_ORDER, fill_value=0)
    pivot["Total"] = pivot.sum(axis=1)
    total_linha = pivot.sum(axis=0)
    pivot.loc["Total Geral"] = total_linha

    return pivot, df_merge


def _obter_listas_nao_categorizadas(df_familias: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    if df_familias is None or df_familias.empty:
        return {}

    col_id_familia = "UF_CRM_1722605592778"
    col_nome_familia = "UF_CRM_1722883482527"
    col_esteira = "UF_CRM_ESTEIRA"

    df_aux = df_familias[[col_id_familia, col_nome_familia, col_esteira]].copy()
    df_aux[col_id_familia] = df_aux[col_id_familia].fillna("").astype(str).str.strip()
    df_aux = df_aux[df_aux[col_id_familia] != ""]

    df_aux[col_esteira] = df_aux[col_esteira].apply(_normalizar_esteira)

    nao_selecionada = df_aux[df_aux[col_esteira] == "NÃO SELECIONADA"].copy()
    nao_informada = df_aux[df_aux[col_esteira] == "NÃO INFORMADA"].copy()

    return {
        "NÃO SELECIONADA": nao_selecionada,
        "NÃO INFORMADA": nao_informada,
    }


def exibir_visao_esteiras(df_familias: pd.DataFrame, df_emissoes: pd.DataFrame) -> None:
    """Renderiza apenas a visão macro (tabela Esteira x Estágio)."""

    if df_familias is None or df_familias.empty:
        return
    if df_emissoes is None or df_emissoes.empty:
        return

    with st.spinner("Montando visão por esteira (macro)..."):
        pivot_macro, df_merge = _construir_pivot_macro(df_familias, df_emissoes)

    if pivot_macro is None or pivot_macro.empty:
        st.info("Sem dados suficientes para montar a tabela Esteira x Estágio.")
        return

    st.markdown("### Emissões Brasileiras por Esteira")
    st.caption(
        "Consolida o funil 46 (Pasta Pronta) com as emissões brasileiras, agrupando as famílias pelo campo de esteira."
    )

    pivot_filtrado = pivot_macro.copy()

    # Remover linhas totalmente vazias (exceto Total Geral)
    linhas_para_remover = [
        idx
        for idx in pivot_filtrado.index
        if idx != "Total Geral" and pivot_filtrado.loc[idx, "Total"] == 0
    ]
    if linhas_para_remover:
        pivot_filtrado = pivot_filtrado.drop(index=linhas_para_remover)

    # Remover colunas com zero em todas as esteiras (desconsidera Total Geral)
    colunas_zero = [
        col
        for col in pivot_filtrado.columns
        if col != "Total" and pivot_filtrado.loc[pivot_filtrado.index != "Total Geral", col].sum() == 0
    ]
    if colunas_zero:
        pivot_filtrado = pivot_filtrado.drop(columns=colunas_zero)

    # Ordenar colunas (alfabética) e manter Total no fim
    colunas = [c for c in pivot_filtrado.columns if c != "Total"]
    colunas_ordenadas = sorted(colunas, key=lambda nome: nome.lower())
    pivot_exibicao = pivot_filtrado[colunas_ordenadas + ["Total"]]

    # Preparar DataFrame final com coluna Esteira
    pivot_exibicao = (
        pivot_exibicao
        .rename_axis("Esteira")
        .reset_index()
    )

    estilos_base = [
        {
            "selector": "th",
            "props": "font-weight:bold; text-transform:uppercase; background-color:#eef2f6;"
        },
        {
            "selector": "td",
            "props": "padding:8px 10px; text-align:center;"
        },
        {
            "selector": "td:first-child",
            "props": "text-align:left; font-weight:600;"
        },
    ]

    def _destacar_total(row):
        return ["font-weight:bold;background-color:#f1f5f9;" if row.name == len(pivot_exibicao) - 1 else "" for _ in row]

    tabela_estilizada = (
        pivot_exibicao.style
        .format("{:,}", subset=pivot_exibicao.columns[1:])
        .set_table_styles(estilos_base)
        .apply(_destacar_total, axis=1)
    )

    st.dataframe(
        tabela_estilizada,
        use_container_width=True,
        height=min(600, 60 * (pivot_exibicao.shape[0] + 1)),
    )

    # Famílias sem esteira válida
    listas_nao_categorizadas = _obter_listas_nao_categorizadas(df_familias)
    if listas_nao_categorizadas:
        with st.expander("Famílias sem esteira definida"):
            for chave, df_lista in listas_nao_categorizadas.items():
                st.markdown(f"**{chave}** — {len(df_lista):,} famílias")
                if not df_lista.empty:
                    st.dataframe(
                        df_lista.rename(columns={
                            "UF_CRM_1722605592778": "ID Família",
                            "UF_CRM_1722883482527": "Nome",
                        }).set_index("ID Família"),
                        use_container_width=True,
                        height=min(350, 35 * (len(df_lista) + 1)),
                    )

    # Cards duplicados (mesmo ID) caso existam
    if df_merge is not None and "__CARD_ID__" in df_merge.columns:
        duplicados = (
            df_merge[df_merge.duplicated("__CARD_ID__", keep=False)]
            .sort_values("__CARD_ID__")
        )
        if not duplicados.empty:
            with st.expander("Cards duplicados (mesmo ID em múltiplas famílias/esteiras)"):
                st.dataframe(
                    duplicados[["__CARD_ID__", "UF_CRM_1722883482527", "UF_CRM_ESTEIRA", "STAGE_NAME_LEGIVEL"]],
                    use_container_width=True,
                    height=min(400, 35 * (len(duplicados) + 1)),
                )


def _calcular_totais(df_familias: pd.DataFrame, df_pivot: pd.DataFrame, df_merge: pd.DataFrame) -> Dict[str, int]:
    total_funil = df_familias["UF_CRM_1722605592778"].nunique() if df_familias is not None else 0
    total_pivot = int(df_pivot.loc["Total Geral", "Total"]) if df_pivot is not None and not df_pivot.empty and "Total" in df_pivot.columns else 0
    total_emissoes_distintas = df_merge["__CARD_ID__"].nunique() if df_merge is not None and "__CARD_ID__" in df_merge.columns else 0
    return {
        "Total famílias no funil": total_funil,
        "Total emissões distintas": total_emissoes_distintas,
        "Total contado na tabela": total_pivot,
    }


