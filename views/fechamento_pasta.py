"""
Módulo da aba "Fechamento de Pasta".

Fornece uma visão consolidada do andamento das famílias no funil 46
com filtros por responsável, datas e estágio, além de destacar as
datas de início e finalização da pasta.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import altair as alt
from typing import Dict, Any, Optional, Tuple
from datetime import date

from api.bitrix_connector import load_merged_data
from utils.dataframe_utils import ensure_pandas_df
import calendar


def _montar_calendario_html(calendario_df: pd.DataFrame, weeks: list[list[date]], weekday_names: list[str], target_month: int) -> tuple[str, int]:
    dias = calendario_df.copy()
    dias["data"] = pd.to_datetime(dias["data"]).dt.date
    dias_map = dias.set_index("data").to_dict("index")

    html = [
        "<div class='calendar-container'>",
        "  <div class='calendar-grid'>"
    ]

    html.append("    <div class='calendar-header'></div>")
    for nome in weekday_names:
        html.append(f"    <div class='calendar-header-day'>{nome}</div>")

    for semana_idx, semana in enumerate(weeks):
        semana_nome = f"Semana {semana_idx + 1}"
        html.append(f"    <div class='calendar-week-label'>{semana_nome}</div>")

        for dia in semana:
            info = dias_map.get(dia, {})
            no_mes = info.get("no_mes", 1 if dia.month == target_month else 0)
            is_hoje = info.get("is_hoje", 1 if dia == date.today() else 0)
            entregas = int(info.get("Entregas", 0))
            familias = info.get("Familias", "Sem entregas")
            responsaveis = info.get("Responsaveis", "-")

            classes = ["calendar-cell"]
            if no_mes != 1:
                classes.append("out-month")
            if is_hoje:
                classes.append("today")
            if entregas > 0:
                classes.append("has-delivery")

            tooltip = (
                f"Dia {dia.strftime('%d/%m/%Y')}<br>"
                f"Entregas: {entregas}<br>"
                f"Famílias: {familias}<br>"
                f"Responsáveis: {responsaveis}"
            )

            html.append(
                "    <div class='{}' title='{}'>"
                .format(" ".join(classes), tooltip.replace("'", "&#39;"))
            )
            html.append(f"      <div class='cell-day'>Dia {dia.day}</div>")
            if entregas > 0:
                suffix = "entregues" if entregas > 1 else "entrega"
                html.append(f"      <div class='cell-badge'>> {entregas} {suffix}</div>")
            html.append("    </div>")

    html.append("  </div>")
    html.append("</div>")

    estilos = """
    <style>
    .calendar-container {
        width: 100%;
        background: #ffffff;
        border: 1px solid #e1e5eb;
        border-radius: 16px;
        padding: 16px 20px 20px 20px;
        box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);
        margin-top: 16px;
    }
    .calendar-grid {
        display: grid;
        grid-template-columns: 120px repeat(7, minmax(120px, 1fr));
        gap: 10px;
        align-items: stretch;
    }
    .calendar-header {
        height: 32px;
    }
    .calendar-header-day {
        font-weight: 700;
        color: #1f2937;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.12em;
        text-align: center;
        padding: 12px 0;
        border-bottom: 1px solid #e5e7eb;
    }
    .calendar-week-label {
        font-weight: 600;
        color: #0f172a;
        padding: 16px 8px 16px 4px;
        font-size: 13px;
        letter-spacing: 0.02em;
    }
    .calendar-cell {
        background: linear-gradient(120deg, rgba(248, 250, 252, 0.95), rgba(241, 245, 249, 0.9));
        border-radius: 16px;
        padding: 16px;
        min-height: 92px;
        position: relative;
        border: 1px solid rgba(148, 163, 184, 0.3);
        transition: all 0.2s ease;
    }
    .calendar-cell:hover {
        border-color: #2563eb;
        box-shadow: 0 14px 30px rgba(37, 99, 235, 0.15);
        transform: translateY(-2px);
        background: #eef2ff;
    }
    .calendar-cell.out-month {
        background: rgba(248, 250, 252, 0.6);
        border-style: dashed;
        opacity: 0.65;
    }
    .calendar-cell.today {
        border-color: #22c55e;
        background: linear-gradient(120deg, rgba(220, 252, 231, 0.8), rgba(187, 247, 208, 0.8));
    }
    .calendar-cell.has-delivery {
        background: linear-gradient(145deg, rgba(37, 99, 235, 0.14), rgba(37, 99, 235, 0.05));
        border-color: rgba(37, 99, 235, 0.35);
    }
    .calendar-cell.empty {
        background: transparent;
        border: none;
    }
    .cell-day {
        font-size: 14px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 10px;
    }
    .cell-badge {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
        color: #fff;
        font-weight: 600;
        font-size: 11px;
        border-radius: 999px;
        padding: 4px 10px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    </style>
    """

    altura = 120 + (len(weeks) * 120)
    return estilos + "\n".join(html), altura

@st.cache_data(show_spinner=False)
def load_crm_deal_data(category_id: int) -> pd.DataFrame:
    """Carrega dados do CRM Bitrix usando a função centralizada."""
    try:
        df = load_merged_data(category_id=category_id, debug=False, force_reload=False)
    except Exception as exc:  # pragma: no cover - tratamos em runtime
        st.error(f"Erro ao carregar dados da categoria {category_id}: {exc}")
        return pd.DataFrame()

    if df is None or df.empty:
        st.warning("Nenhum dado encontrado para o funil informado.")
        return pd.DataFrame()

    return df


ORDENS_ETAPA: Dict[str, int] = {
    "EMISSÃO BRASILEIRA": 70,
    "ANÁLISE DOCUMENTAL": 90,
    "TRADUÇÃO": 130,
    "APOSTILAMENTO": 140,
    "DRIVE": 150,
    "RECURSO": 160,
    "PROTOCOLO": 170,
}


CODIGOS_ETAPA = {
    "EMISSÃO BRASILEIRA": {"UC_8Z2EZF"},
    "ANÁLISE DOCUMENTAL": {"UC_N1FI74", "UC_SKSQFO", "UC_K952AX", "UC_2JQ8E2R"},
    "TRADUÇÃO": {"UC_CSFCZP"},
    "APOSTILAMENTO": {"UC_F12U3R"},
    "DRIVE": {"UC_1ARFYMM"},
    "RECURSO": {"UC_SISEKVR"},
    "PROTOCOLO": {"UC_5W7TYZ"},
}


ETAPA_KEYWORDS = {
    "PROTOCOLO": ["PROTOCOLO", "WON", "SUCCESS"],
    "RECURSO": ["RECURSO"],
    "DRIVE": ["DRIVE"],
    "APOSTILAMENTO": ["APOSTILAMENTO", "APOSTILA"],
    "TRADUÇÃO": ["TRADUCAO", "TRADU", "TRADUÇÃO"],
    "ANÁLISE DOCUMENTAL": ["ANALISE DOCUMENTAL", "ANALISE", "ANÁLISE DOCUMENTAL"],
    "EMISSÃO BRASILEIRA": ["EMISSAO", "EMISSÃO", "EMISSAO BRASILEIRA", "EMISSÃO BRASILEIRA"],
}


def _resolver_responsavel(row: pd.Series) -> str:
    for col in [
        "ASSIGNED_BY_NAME",
        "ASSIGNED_BY",
        "ASSIGNED_BY_ID",
        "UF_CRM_1746198853",
    ]:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col]).strip()
    return "N/D"


def _calcular_maior_ordem(stages_df: pd.DataFrame) -> int:
    if stages_df is None or stages_df.empty:
        return 0

    maior = 0
    semanticas = stages_df.get("STAGE_SEMANTIC_ID")
    if semanticas is not None:
        try:
            semanticas = semanticas.dropna().astype(str).str.upper()
            if any(s in {"S", "SUCCESS", "WON"} for s in semanticas):
                maior = max(maior, ORDENS_ETAPA.get("PROTOCOLO", 170))
        except Exception:  # pragma: no cover - robustez para dados inesperados
            pass

    valores_id = stages_df.get("STAGE_ID")
    valores_nome = stages_df.get("STAGE_NAME")
    tokens = []
    for serie in (valores_id, valores_nome):
        if serie is None:
            continue
        try:
            tokens.extend(serie.dropna().astype(str).tolist())
        except Exception:  # pragma: no cover
            continue

    tokens_upper = [token.upper() for token in tokens]

    for etapa, codigos in CODIGOS_ETAPA.items():
        if any(codigo in token for token in tokens_upper for codigo in codigos):
            maior = max(maior, ORDENS_ETAPA.get(etapa, 0))

    for etapa, palavras in ETAPA_KEYWORDS.items():
        if any(any(keyword in token for keyword in palavras) for token in tokens_upper):
            maior = max(maior, ORDENS_ETAPA.get(etapa, 0))

    return maior


def _etapa_atual_por_ordem(ordem: int) -> str:
    etapa_atual = "Não iniciado"
    for etapa, valor in sorted(ORDENS_ETAPA.items(), key=lambda item: item[1]):
        if ordem >= valor:
            etapa_atual = etapa
    return etapa_atual


def _montar_status_por_familia(df: pd.DataFrame) -> pd.DataFrame:
    col_nome = "UF_CRM_1722883482527"
    col_id = "UF_CRM_1722605592778"

    for coluna in [col_nome, col_id, "STAGE_ID"]:
        if coluna not in df.columns:
            df[coluna] = None

    date_inicio_col = "UF_CRM_1758839739214"
    date_fim_col = "UF_CRM_1758839982694"
    situacao_col = "UF_CRM_1758859117203"

    registros: list[Dict[str, Any]] = []

    agrupadores = [col for col in [col_nome, col_id] if col in df.columns]
    if not agrupadores:
        return pd.DataFrame()

    for chave, grupo in df.groupby(agrupadores, dropna=False):
        if isinstance(chave, tuple):
            nome_familia, id_familia = chave[0], chave[1]
        else:
            nome_familia, id_familia = chave, ""

        maior_ordem = _calcular_maior_ordem(grupo[[col for col in ["STAGE_ID", "STAGE_NAME", "STAGE_SEMANTIC_ID"] if col in grupo.columns]])
        etapas_status = {
            etapa: ("✅" if maior_ordem >= ordem else "")
            for etapa, ordem in ORDENS_ETAPA.items()
        }

        responsavel = _resolver_responsavel(grupo.iloc[0]) if not grupo.empty else "N/D"

        data_inicio = pd.to_datetime(grupo.get(date_inicio_col), errors="coerce") if date_inicio_col in grupo else pd.Series(dtype="datetime64[ns]")
        data_fim = pd.to_datetime(grupo.get(date_fim_col), errors="coerce") if date_fim_col in grupo else pd.Series(dtype="datetime64[ns]")
        situacao_pasta = ""
        if situacao_col in grupo:
            serie_situacao = grupo[situacao_col].dropna()
            if not serie_situacao.empty:
                situacao_pasta = str(serie_situacao.iloc[0]).strip()

        stage_tokens: list[str] = []
        if "STAGE_NAME" in grupo.columns:
            stage_tokens.extend(
                grupo["STAGE_NAME"].dropna().astype(str).str.upper().tolist()
            )
        if "STAGE_ID" in grupo.columns:
            stage_tokens.extend(
                grupo["STAGE_ID"].dropna().astype(str).str.upper().tolist()
            )

        analise_negativa = any("NEGATIV" in token for token in stage_tokens)
        analise_positiva = any("POSITIV" in token for token in stage_tokens)

        registros.append({
            "Nome da Família": str(nome_familia) if nome_familia is not None else "",
            "ID da Família": str(id_familia) if id_familia is not None else "",
            "Responsável": responsavel,
            "Etapa Atual": _etapa_atual_por_ordem(maior_ordem),
            "__ORDEM_MAX__": maior_ordem,
            "Data Início": data_inicio.min() if not data_inicio.empty else pd.NaT,
            "Data Finalização": data_fim.min() if not data_fim.empty else pd.NaT,
            "Situação Pasta": situacao_pasta,
            "ANÁLISE NEGATIVA": "✅" if analise_negativa else "",
            "ANÁLISE POSITIVA": "✅" if analise_positiva else "",
            **etapas_status,
        })

    df_out = pd.DataFrame(registros)
    if df_out.empty:
        return df_out

    colunas_ordenadas = [
        "Nome da Família",
        "ID da Família",
        "Responsável",
        "Etapa Atual",
        "Data Início",
        "Data Finalização",
        "EMISSÃO BRASILEIRA",
        "ANÁLISE DOCUMENTAL",
        "ANÁLISE NEGATIVA",
        "ANÁLISE POSITIVA",
        "TRADUÇÃO",
        "APOSTILAMENTO",
        "DRIVE",
        "RECURSO",
        "PROTOCOLO",
    ]

    colunas_presentes = [col for col in colunas_ordenadas if col in df_out.columns]
    df_out = df_out[colunas_presentes + [col for col in df_out.columns if col not in colunas_presentes]]

    return df_out


def _intervalo_padrao(series: pd.Series) -> Optional[Tuple[date, date]]:
    if series is None:
        return None
    series_validas = series.dropna()
    if series_validas.empty:
        return None
    inicio = series_validas.min().date()
    fim = series_validas.max().date()
    return inicio, fim


def _aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    filtros_container = st.container()
    with filtros_container:
        col1, col2, col3 = st.columns([1.2, 1, 1])

        responsaveis = sorted({resp for resp in df["Responsável"].dropna().unique() if str(resp).strip()})
        etapas = ["Todos"] + list(ORDENS_ETAPA.keys())

        with col1:
            responsavel_sel = st.multiselect(
                "Responsável",
                options=responsaveis,
                default=None,
                help="Selecione um ou mais responsáveis para filtrar."
            )

        with col2:
            etapa_filtro = st.selectbox(
                "Etapa do Processo",
                options=etapas,
                index=0,
            )

        with col3:
            nome_busca = st.text_input("Nome da Família", placeholder="Digite para filtrar pelo nome")

        col4, col5, col6 = st.columns([1, 1, 1])

        with col4:
            id_busca = st.text_input("ID da Família", placeholder="Digite para filtrar pelo ID")

        intervalo_inicio_default = _intervalo_padrao(df.get("Data Início"))
        intervalo_final_default = _intervalo_padrao(df.get("Data Finalização"))

        with col5:
            filtrar_inicio = st.checkbox("Filtrar Data de Início", key="chk_data_inicio")
            if filtrar_inicio and intervalo_inicio_default:
                datas_inicio = st.date_input(
                    "Intervalo de Início",
                    value=intervalo_inicio_default,
                    key="date_inicio_intervalo",
                )
            else:
                if filtrar_inicio and not intervalo_inicio_default:
                    st.info("Nenhuma data de início disponível nos dados.")
                datas_inicio = None

        with col6:
            filtrar_final = st.checkbox("Filtrar Data de Finalização", key="chk_data_final")
            if filtrar_final and intervalo_final_default:
                datas_finalizacao = st.date_input(
                    "Intervalo de Finalização",
                    value=intervalo_final_default,
                    key="date_final_intervalo",
                )
            else:
                if filtrar_final and not intervalo_final_default:
                    st.info("Nenhuma data de finalização disponível nos dados.")
                datas_finalizacao = None

    df_filtrado = df.copy()

    if responsavel_sel:
        df_filtrado = df_filtrado[df_filtrado["Responsável"].isin(responsavel_sel)]

    if etapa_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Etapa Atual"] == etapa_filtro]

    if nome_busca:
        df_filtrado = df_filtrado[df_filtrado["Nome da Família"].str.contains(nome_busca, case=False, na=False)]

    if id_busca:
        df_filtrado = df_filtrado[df_filtrado["ID da Família"].str.contains(id_busca, case=False, na=False)]

    def _filtrar_datas(df_base: pd.DataFrame, coluna: str, intervalo):
        if not intervalo:
            return df_base

        inicio, fim = intervalo
        if inicio is not None:
            df_base = df_base[df_base[coluna] >= pd.to_datetime(inicio)]
        if fim is not None:
            df_base = df_base[df_base[coluna] <= pd.to_datetime(fim)]
        return df_base

    if isinstance(datas_inicio, tuple) and datas_inicio:
        df_filtrado = _filtrar_datas(df_filtrado, "Data Início", datas_inicio)
    if isinstance(datas_finalizacao, tuple) and datas_finalizacao:
        df_filtrado = _filtrar_datas(df_filtrado, "Data Finalização", datas_finalizacao)

    return df_filtrado


def _renderizar_metricas(df: pd.DataFrame) -> None:
    st.markdown("#### Indicadores por Responsável")
    responsaveis = sorted(df["Responsável"].dropna().unique())
    for responsavel in responsaveis:
        subset = df[df["Responsável"] == responsavel]
        total_resp = subset["ID da Família"].nunique()
        finalizadas_resp = subset[subset["PROTOCOLO"] == "✅"]["ID da Família"].nunique()
        andamento_resp = total_resp - finalizadas_resp
        drive_resp = subset[subset["DRIVE"] == "✅"]["ID da Família"].nunique()
        apost_resp = subset[subset["APOSTILAMENTO"] == "✅"]["ID da Família"].nunique()
        emissao_resp = subset[subset["EMISSÃO BRASILEIRA"] == "✅"]["ID da Família"].nunique()
        traducao_resp = subset[subset["TRADUÇÃO"] == "✅"]["ID da Família"].nunique()
        analise_resp = subset[subset["ANÁLISE DOCUMENTAL"] == "✅"]["ID da Família"].nunique()
        analise_neg_resp = subset[subset["ANÁLISE NEGATIVA"] == "✅"]["ID da Família"].nunique()
        analise_pos_resp = subset[subset["ANÁLISE POSITIVA"] == "✅"]["ID da Família"].nunique()

        def _render_card(column, label, value, background, text_color="#1c1c1c"):
            column.markdown(
                f"""
                <div style='background:{background}; padding:16px 12px; border-radius:10px; text-align:center; margin-bottom:10px;'>
                    <div style='font-size:13px; font-weight:600; color:{text_color}; text-transform:uppercase; letter-spacing:0.03em;'>{label}</div>
                    <div style='font-size:28px; font-weight:700; color:{text_color}; margin-top:4px;'>{int(value):,}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        perc_concluido = 0 if total_resp == 0 else finalizadas_resp / total_resp
        st.markdown(
            f"""
            <div style='display:flex; align-items:center; justify-content:space-between; margin: 18px 0 12px 0;'>
                <div style='font-size:26px; font-weight:800; color:#0b2447; letter-spacing:0.02em;'>
                    {responsavel}
                </div>
                <div style='display:flex; align-items:center; gap:12px;'>
                    <div style='font-size:15px; font-weight:600; color:#0f5132;'>PROGRESSO</div>
                    <div style='background:rgba(25, 135, 84, 0.35); border-radius:14px; padding:6px 14px; color:#0f5132; font-weight:700;'>
                        {perc_concluido:.0%}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        row1 = st.columns(4)
        _render_card(row1[0], f"Total de Famílias", total_resp, "#f1f3f5")
        _render_card(row1[1], "Em Andamento", andamento_resp, "rgba(255, 193, 7, 0.5)")
        _render_card(row1[2], "Em Drive", drive_resp, "rgba(13, 110, 253, 0.35)", text_color="#0b2447")
        _render_card(row1[3], "Em Apostilamento", apost_resp, "rgba(255, 159, 64, 0.4)")

        row2 = st.columns(4)
        _render_card(row2[0], "Pasta Pronta", finalizadas_resp, "rgba(25, 135, 84, 0.45)", text_color="#0f3d27")
        _render_card(row2[1], "Emissão Brasileira", emissao_resp, "rgba(0, 123, 255, 0.2)")
        _render_card(row2[2], "Tradução", traducao_resp, "rgba(102, 16, 242, 0.2)")
        _render_card(row2[3], "Análise Documental", analise_resp, "rgba(13, 202, 240, 0.25)")

        row3 = st.columns(2)
        _render_card(row3[0], "Análise Negativa", analise_neg_resp, "rgba(220, 53, 69, 0.35)", text_color="#5a0a14")
        _render_card(row3[1], "Análise Positiva", analise_pos_resp, "rgba(25, 135, 84, 0.35)", text_color="#0f3d27")

        st.markdown(
            f"""
            <div style='display:flex; align-items:center; gap:10px; margin:12px 0 24px 0;'>
                <div style='flex:1; height:10px; background:rgba(25, 135, 84, 0.2); border-radius:6px; overflow:hidden;'>
                    <div style='width:{perc_concluido*100:.0f}%; height:100%; background:#198754; border-radius:6px;'></div>
                </div>
                <div style='font-weight:700; color:#0f5132; min-width:60px; text-align:right;'>{perc_concluido:.0%}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")


def _resumo_etapas_por_responsavel(df: pd.DataFrame) -> pd.DataFrame:
    agrupado = (
        df.groupby(["Responsável", "Etapa Atual"], dropna=False)["ID da Família"]
        .nunique()
        .reset_index(name="Famílias")
    )
    analise_negativa = (
        df[df["ANÁLISE NEGATIVA"] == "✅"]
        .groupby("Responsável")["ID da Família"]
        .nunique()
        .reset_index(name="ANÁLISE NEGATIVA")
    )
    analise_positiva = (
        df[df["ANÁLISE POSITIVA"] == "✅"]
        .groupby("Responsável")["ID da Família"]
        .nunique()
        .reset_index(name="ANÁLISE POSITIVA")
    )
    if not analise_negativa.empty:
        agrupado = agrupado.merge(analise_negativa, on="Responsável", how="left")
    if not analise_positiva.empty:
        agrupado = agrupado.merge(analise_positiva, on="Responsável", how="left")
    for col in ["ANÁLISE NEGATIVA", "ANÁLISE POSITIVA"]:
        if col in agrupado.columns:
            agrupado[col] = agrupado[col].fillna(0).astype(int)

    return agrupado


def _renderizar_resumo_visual(df: pd.DataFrame) -> None:
    resumo = _resumo_etapas_por_responsavel(df)
    if resumo.empty:
        st.info("Sem dados para montar o resumo visual no momento.")
        return

    etapas_ordenadas = ["Não iniciado"] + [etapa for etapa, _ in sorted(ORDENS_ETAPA.items(), key=lambda item: item[1])]
    resumo["Etapa Atual"] = pd.Categorical(resumo["Etapa Atual"], categories=etapas_ordenadas, ordered=True)
    resumo = resumo.sort_values(["Responsável", "Etapa Atual"], kind="stable")

    st.markdown("#### Evolução das Pastas por Responsável")

    tabela_resumo = resumo.pivot_table(
        index="Responsável",
        columns="Etapa Atual",
        values="Famílias",
        aggfunc="sum",
        fill_value=0,
    )

    tabela_resumo = tabela_resumo.reindex(columns=etapas_ordenadas, fill_value=0)
    if "ANÁLISE NEGATIVA" in resumo.columns:
        tabela_resumo["ANÁLISE NEGATIVA"] = resumo.groupby("Responsável")["ANÁLISE NEGATIVA"].max()
    if "ANÁLISE POSITIVA" in resumo.columns:
        tabela_resumo["ANÁLISE POSITIVA"] = resumo.groupby("Responsável")["ANÁLISE POSITIVA"].max()
    tabela_resumo["TOTAL"] = tabela_resumo.sum(axis=1)
    tabela_resumo = tabela_resumo.reset_index()

    totais = resumo.groupby("Responsável")["Famílias"].sum().reset_index(name="Total")
    resumo = resumo.merge(totais, on="Responsável", how="left")

    base = alt.Chart(resumo)

    responsaveis_ordenados = resumo.sort_values("Total", ascending=False, kind="stable")["Responsável"].unique().tolist()
    if responsaveis_ordenados:
        valor_inicial = [{"Responsável": responsaveis_ordenados[0]}]
        selecao_responsavel = alt.selection_point(fields=["Responsável"], value=valor_inicial)
    else:
        selecao_responsavel = alt.selection_point(fields=["Responsável"])

    barras = base.mark_bar().encode(
        y=alt.Y(
            "Responsável:N",
            sort=alt.EncodingSortField(field="Total", order="descending"),
            title="Responsável"
        ),
        x=alt.X("sum(Famílias):Q", title="Famílias"),
        color=alt.Color(
            "Etapa Atual:N",
            scale=alt.Scale(domain=etapas_ordenadas),
            legend=alt.Legend(title="Etapa")
        ),
        tooltip=[
            "Responsável",
            "Etapa Atual",
            alt.Tooltip("Famílias:Q", format=",d")
        ],
        opacity=alt.condition(selecao_responsavel, alt.value(1), alt.value(0.35))
    ).add_params(selecao_responsavel)

    textos = base.mark_text(dx=0, dy=0, color="black").encode(
        y=alt.Y(
            "Responsável:N",
            sort=alt.EncodingSortField(field="Total", order="descending")
        ),
        x=alt.X("sum(Famílias):Q"),
        detail="Etapa Atual",
        text=alt.Text("sum(Famílias):Q", format=".0f"),
        color=alt.value("black"),
    )

    detalhe = base.mark_bar(size=35).transform_filter(
        selecao_responsavel
    ).encode(
        y=alt.Y("Etapa Atual:N", sort=etapas_ordenadas, title="Etapa"),
        x=alt.X("sum(Famílias):Q", title="Famílias"),
        color=alt.Color(
            "Etapa Atual:N",
            scale=alt.Scale(domain=etapas_ordenadas),
            legend=None
        ),
        tooltip=[
            "Responsável",
            "Etapa Atual",
            alt.Tooltip("Famílias:Q", format=",d")
        ],
    ).properties(height=260)

    detalhe_texto = detalhe.mark_text(align="left", dx=5, color="#1c1c1c").encode(
        text=alt.Text("sum(Famílias):Q", format=".0f")
    )

    altura = max(480, 70 * resumo["Responsável"].nunique())
    grafico_superior = (barras + textos).properties(height=altura, width="container")
    grafico_inferior = (detalhe + detalhe_texto).resolve_scale(color="independent")

    st.altair_chart(
        alt.vconcat(grafico_superior, grafico_inferior).resolve_scale(x="shared"),
        use_container_width=True
    )

    tabela_resumo_display = tabela_resumo.copy()
    numeric_cols = [col for col in tabela_resumo_display.columns if col != "Responsável"]
    tabela_resumo_display[numeric_cols] = tabela_resumo_display[numeric_cols].fillna(0).astype(int)

    styled_table_html = (
        tabela_resumo_display.style
        .format(precision=0)
        .background_gradient(axis=1, cmap="Blues")
        .set_properties(**{"font-weight": "600"}, subset=pd.IndexSlice[:, ["TOTAL"]])
        .set_table_attributes('style="border-collapse:collapse;width:100%;"')
        .set_table_styles([
            {"selector": "th", "props": [("font-size", "14px"), ("background-color", "#f1f3f5"), ("color", "#1c1c1c"), ("padding", "8px"), ("text-align", "center"), ("border", "1px solid #dee2e6")]},
            {"selector": "td", "props": [("padding", "8px"), ("text-align", "center"), ("border", "1px solid #dee2e6"), ("font-size", "13px")]}])
        .to_html()
    )

    st.markdown("##### Quantidade de Famílias por Etapa")
    st.markdown(styled_table_html, unsafe_allow_html=True)
    st.markdown("---")


def _renderizar_timeline(df_andamento: pd.DataFrame, df_concluidos: pd.DataFrame) -> None:
    st.markdown("### Linha do Tempo e Entregas")

    if (df_andamento is None or df_andamento.empty) and (df_concluidos is None or df_concluidos.empty):
        st.info("Sem dados suficientes para montar a linha do tempo.")
        return

    campos_base = ["Responsável", "Nome da Família", "ID da Família", "Data Início", "Data Finalização"]

    df_lista = []
    if df_andamento is not None and not df_andamento.empty:
        df_lista.append(df_andamento[campos_base].copy())
    if df_concluidos is not None and not df_concluidos.empty:
        missing_cols = [col for col in ["Nome da Família", "ID da Família", "Data Início"] if col not in df_concluidos.columns]
        for col in missing_cols:
            df_concluidos[col] = pd.NA
        df_lista.append(df_concluidos[campos_base].copy())

    if not df_lista:
        st.info("Sem registros para exibir na linha do tempo.")
        return

    df_timeline = pd.concat(df_lista, ignore_index=True)
    df_timeline["Responsável"] = df_timeline["Responsável"].fillna("Sem responsável")

    today = pd.Timestamp.today().normalize()
    df_timeline["Data Final Plot"] = df_timeline["Data Finalização"].fillna(today)
    df_timeline["Data Início Plot"] = df_timeline["Data Início"].fillna(df_timeline["Data Final Plot"])

    df_timeline = df_timeline.dropna(subset=["Data Início Plot", "Data Final Plot"])

    df_timeline["Status"] = df_timeline["Data Finalização"].apply(lambda x: "Concluída" if pd.notna(x) else "Em andamento")

    if df_timeline.empty:
        st.info("Sem datas válidas para exibir na linha do tempo.")
    else:
        st.markdown("#### Linha do Tempo de Conclusões")

        timeline_chart = (
            alt.Chart(df_timeline)
            .mark_bar(height=22, cornerRadius=6)
            .encode(
                y=alt.Y(
                    "Responsável:N",
                    sort="-x",
                    axis=alt.Axis(title="Responsável", labelFontSize=12, titleFontSize=14)
                ),
                x=alt.X(
                    "Data Início Plot:T",
                    title="Período",
                    axis=alt.Axis(format="%d/%m", labelAngle=0, tickCount="day")
                ),
                x2=alt.X2("Data Final Plot:T"),
                color=alt.Color(
                    "Status:N",
                    scale=alt.Scale(domain=["Em andamento", "Concluída"], range=["#FFC107", "#198754"]),
                    legend=alt.Legend(title="Status")
                ),
                tooltip=[
                    alt.Tooltip("Responsável", title="Responsável"),
                    alt.Tooltip("Nome da Família", title="Família"),
                    alt.Tooltip("Data Início Plot:T", title="Início"),
                    alt.Tooltip("Data Finalização:T", title="Entrega"),
                    alt.Tooltip("Status", title="Status"),
                ],
            )
            .properties(height=max(420, 28 * df_timeline["Responsável"].nunique()), width="container")
        )

        pontos_entrega = (
            alt.Chart(df_timeline[pd.notna(df_timeline["Data Finalização"])])
            .mark_point(size=120, filled=True, color="#0f5132")
            .encode(
                y=alt.Y("Responsável:N", sort="-x"),
                x=alt.X("Data Finalização:T"),
                tooltip=[
                    alt.Tooltip("Responsável", title="Responsável"),
                    alt.Tooltip("Nome da Família", title="Família"),
                    alt.Tooltip("Data Finalização:T", title="Entrega"),
                ],
            )
        )

        linha_entrega = (
            alt.Chart(df_timeline[pd.notna(df_timeline["Data Finalização"])])
            .mark_rule(color="#0f5132", strokeDash=[4, 4])
            .encode(x="Data Finalização:T")
        )

        st.altair_chart(timeline_chart + pontos_entrega + linha_entrega, use_container_width=True)

        df_entregas = df_timeline[pd.notna(df_timeline["Data Finalização"])][[
            "Responsável", "Nome da Família", "Data Finalização"
        ]].copy()

        if not df_entregas.empty:
            st.markdown("##### Calendário de Entregas (estilo mês)")
            st.markdown(
                """
                <style>
                .calendar-select-label {
                    font-weight: 600;
                    color: #1f2937;
                    font-size: 13px;
                    letter-spacing: 0.04em;
                    text-transform: uppercase;
                    margin-bottom: 6px;
                }
                div[data-testid="stSelectbox"][data-key="sel_mes_calendario"] > label {
                    display: none;
                }
                div[data-testid="stSelectbox"][data-key="sel_mes_calendario"] div[data-baseweb="select"] {
                    background: linear-gradient(115deg, rgba(248,250,252,0.95), rgba(226,232,240,0.9));
                    border: 1px solid rgba(148, 163, 184, 0.4);
                    border-radius: 12px;
                    padding: 12px 14px;
                    min-height: 48px;
                    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
                }
                div[data-testid="stSelectbox"][data-key="sel_mes_calendario"] div[data-baseweb="select"] span {
                    font-weight: 600;
                    color: #0f172a;
                    letter-spacing: 0.02em;
                }
                div[data-testid="stSelectbox"][data-key="sel_mes_calendario"] div[data-baseweb="select"] svg {
                    color: #1d4ed8;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            st.markdown("<div class='calendar-select-label'>Selecione o mês</div>", unsafe_allow_html=True)

            df_entregas["Data Finalização"] = pd.to_datetime(df_entregas["Data Finalização"]).dt.normalize()
            meses_disponiveis = (
                df_entregas["Data Finalização"].dt.to_period("M").sort_values().unique()
            )

            if len(meses_disponiveis) == 0:
                st.info("Nenhuma entrega com data definida.")
            else:
                meses_labels = [p.strftime("%B/%Y") for p in meses_disponiveis]
                idx_default = len(meses_disponiveis) - 1
                mes_escolhido_label = st.selectbox(
                    "Selecione o mês",
                    options=list(range(len(meses_disponiveis))),
                    format_func=lambda i: meses_labels[i],
                    index=idx_default,
                    key="sel_mes_calendario",
                    label_visibility="collapsed"
                )
                mes_period = meses_disponiveis[mes_escolhido_label]
                mes_inicio = mes_period.to_timestamp()
                mes_fim = (mes_period + 1).to_timestamp() - pd.Timedelta(days=1)

                cal = calendar.Calendar(firstweekday=6)  # Domingo primeiro
                month_weeks = cal.monthdatescalendar(mes_inicio.year, mes_inicio.month)

                registros = []
                for semana_idx, semana in enumerate(month_weeks):
                    for dia in semana:
                        registros.append({
                            "data": pd.Timestamp(dia),
                            "semana_idx": semana_idx,
                            "dia": dia.day,
                            "no_mes": 1 if dia.month == mes_inicio.month else 0,
                            "is_hoje": 1 if dia == pd.Timestamp.today().date() else 0
                        })

                calendario_df = pd.DataFrame(registros)

                def _join_limited(series, limit=3):
                    itens = list(dict.fromkeys(map(str, series)))
                    if len(itens) > limit:
                        return ", ".join(itens[:limit]) + f" +{len(itens)-limit}"
                    return ", ".join(itens)

                agregados = (
                    df_entregas[df_entregas["Data Finalização"].between(mes_inicio, mes_fim)]
                    .groupby("Data Finalização")
                    .agg(
                        Entregas=("Nome da Família", "count"),
                        Familias=("Nome da Família", _join_limited),
                        Responsaveis=("Responsável", _join_limited)
                    )
                    .reset_index()
                    .rename(columns={"Data Finalização": "data"})
                )

                calendario_df = calendario_df.merge(agregados, on="data", how="left")
                calendario_df["Entregas"] = calendario_df["Entregas"].fillna(0).astype(int)
                calendario_df["Familias"] = calendario_df["Familias"].fillna("Sem entregas")
                calendario_df["Responsaveis"] = calendario_df["Responsaveis"].fillna("-")

                calendario_df["data"] = calendario_df["data"].dt.date

                cal = calendar.Calendar(firstweekday=6)
                month_weeks = cal.monthdatescalendar(mes_inicio.year, mes_inicio.month)
                weekday_names = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]

                calendario_html, calendario_altura = _montar_calendario_html(
                    calendario_df,
                    weeks=month_weeks,
                    weekday_names=weekday_names,
                    target_month=mes_inicio.month
                )

                components.html(
                    calendario_html,
                    height=calendario_altura,
                    scrolling=False
                )

    st.markdown("---")


def _renderizar_alerta_ajustes(df_concluidos: pd.DataFrame) -> None:
    if df_concluidos.empty:
        return

    st.markdown("### Ajustes de Pastas Concluídas")

    st.warning(
        "Gestor, atenção: as pastas listadas abaixo constam como concluidas (possuem data de finalização) e precisam de ajustes da Doutora Gabriely.",
        icon="⚠️"
    )

    resumo = (
        df_concluidos.groupby("Responsável")["ID da Família"].nunique().reset_index(name="Pastas Concluídas")
    )
    detalhado = df_concluidos[[
        "Responsável",
        "ID da Família",
        "Nome da Família",
        "Data Finalização"
    ]].sort_values(["Responsável", "Nome da Família"], kind="stable")

    if not resumo.empty:
        total_row = pd.DataFrame({
            "Responsável": ["TOTAL"],
            "Pastas Concluídas": [int(resumo["Pastas Concluídas"].sum())]
        })
        resumo = pd.concat([resumo, total_row], ignore_index=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### Responsáveis Impactados")
        st.dataframe(
            ensure_pandas_df(resumo.sort_values("Pastas Concluídas", ascending=False, kind="stable")),
            hide_index=True,
            use_container_width=True,
        )

    with col2:
        st.markdown("#### Famílias que Precisam de Ajuste")
        st.dataframe(
            ensure_pandas_df(detalhado),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Data Finalização": st.column_config.DateColumn("Data Finalização")
            }
        )

    st.caption("Utilize este quadro para coordenar ajustes diretamente com a Doutora Gabriely.")


def show_fechamento_pasta():
    """Renderiza a página de fechamento de pasta."""
    st.markdown("<h1 class='page-title'>Fechamento de Pasta</h1>", unsafe_allow_html=True)
    st.caption("Visão consolidada das famílias no processo de conclusão de pasta.")

    df_crm = load_crm_deal_data(category_id=46)
    if df_crm.empty:
        st.info("Sem dados para exibir no momento.")
        return

    df_status = _montar_status_por_familia(df_crm)
    if df_status.empty:
        st.info("Não foi possível montar o status por família com os dados disponíveis.")
        return

    df_status["Data Início"] = pd.to_datetime(df_status["Data Início"], errors="coerce")
    df_status["Data Finalização"] = pd.to_datetime(df_status["Data Finalização"], errors="coerce")

    df_status["Situação Pasta"] = df_status["Situação Pasta"].fillna("")
    df_status["Status Ajustado"] = df_status["Situação Pasta"].str.upper()
    df_status.loc[df_status["Status Ajustado"] == "", "Status Ajustado"] = "EM ANDAMENTO"
    df_status.loc[df_status["Data Finalização"].notna(), "Status Ajustado"] = "CONCLUIDO"

    df_concluidos = df_status[df_status["Status Ajustado"] == "CONCLUIDO"].copy()
    df_status = df_status[df_status["Status Ajustado"] == "EM ANDAMENTO"].copy()

    if df_status.empty:
        st.info("Nenhuma pasta marcada como 'EM ANDAMENTO' no momento.")

    if df_status.empty and df_concluidos.empty:
        return

    df_filtrado = _aplicar_filtros(df_status)

    df_ordenado = df_filtrado.sort_values(
        by=["Responsável", "__ORDEM_MAX__", "Nome da Família"],
        ascending=[True, False, True],
        kind="stable",
    )

    if not df_ordenado.empty:
        _renderizar_metricas(df_ordenado)
        _renderizar_resumo_visual(df_ordenado)

    if st.session_state.get("_mostrar_timeline_fechamento") is None:
        st.session_state._mostrar_timeline_fechamento = True

    st.session_state._mostrar_timeline_fechamento = st.checkbox(
        "Mostrar linha do tempo e entregas por período",
        value=st.session_state._mostrar_timeline_fechamento,
        help="Desmarque para ocultar a visão temporal e focar apenas nos indicadores",
    )

    if st.session_state._mostrar_timeline_fechamento:
        _renderizar_timeline(df_ordenado, df_concluidos)

    _renderizar_alerta_ajustes(df_concluidos)


