import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import altair as alt
from datetime import date
import calendar
import textwrap


def _join_limited(series: pd.Series, limit: int = 3) -> str:
    """Concatena valores únicos de forma compacta para uso em tooltips."""
    itens: list[str] = []
    for valor in series.astype(str):
        valor = valor.strip()
        if not valor:
            continue
        if valor not in itens:
            itens.append(valor)
    if not itens:
        return "-"
    if len(itens) > limit:
        return ", ".join(itens[:limit]) + f" +{len(itens) - limit}"
    return ", ".join(itens)


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
            montagens = int(info.get("Montagens", 0))
            familias = info.get("Familias", "Sem montagens")
            responsaveis = info.get("Responsaveis", "-")

            classes = ["calendar-cell"]
            if no_mes != 1:
                classes.append("out-month")
            if is_hoje:
                classes.append("today")
            if montagens > 0:
                classes.append("has-delivery")

            tooltip = (
                f"Dia {dia.strftime('%d/%m/%Y')}<br>"
                f"Montagens: {montagens}<br>"
                f"Famílias: {familias}<br>"
                f"Responsáveis: {responsaveis}"
            )

            html.append(
                "    <div class='{}' title='{}'>".format(" ".join(classes), tooltip.replace("'", "&#39;"))
            )
            html.append(f"      <div class='cell-day'>{dia.day}</div>")
            if montagens > 0:
                suffix = "montagens" if montagens > 1 else "montagem"
                html.append(f"      <div class='cell-badge'>{montagens} {suffix}</div>")
            html.append("    </div>")

    html.append("  </div>")
    html.append("</div>")

    estilos = """
    <style>
    .calendar-container {
        width: 100%;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px 20px 20px 20px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
        margin-top: 12px;
    }
    .calendar-grid {
        display: grid;
        grid-template-columns: 110px repeat(7, minmax(110px, 1fr));
        gap: 10px;
        align-items: stretch;
    }
    .calendar-header {
        height: 32px;
    }
    .calendar-header-day {
        font-weight: 700;
        color: #0f172a;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.12em;
        text-align: center;
        padding: 10px 0;
        border-bottom: 1px solid #e2e8f0;
    }
    .calendar-week-label {
        font-weight: 600;
        color: #1f2937;
        padding: 14px 6px 14px 2px;
        font-size: 13px;
        letter-spacing: 0.02em;
    }
    .calendar-cell {
        background: linear-gradient(125deg, rgba(248, 250, 252, 0.95), rgba(226, 232, 240, 0.9));
        border-radius: 16px;
        padding: 16px;
        min-height: 92px;
        position: relative;
        border: 1px solid rgba(148, 163, 184, 0.35);
        transition: all 0.2s ease;
    }
    .calendar-cell:hover {
        border-color: #1d4ed8;
        box-shadow: 0 14px 30px rgba(29, 78, 216, 0.14);
        transform: translateY(-2px);
        background: #e0e7ff;
    }
    .calendar-cell.out-month {
        background: rgba(248, 250, 252, 0.6);
        border-style: dashed;
        opacity: 0.6;
    }
    .calendar-cell.today {
        border-color: #16a34a;
        background: linear-gradient(120deg, rgba(220, 252, 231, 0.8), rgba(187, 247, 208, 0.85));
    }
    .calendar-cell.has-delivery {
        background: linear-gradient(140deg, rgba(37, 99, 235, 0.22), rgba(37, 99, 235, 0.08));
        border-color: rgba(37, 99, 235, 0.4);
    }
    .cell-day {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 8px;
    }
    .cell-badge {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
        color: #fff;
        font-weight: 600;
        font-size: 11px;
        border-radius: 999px;
        padding: 4px 12px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    </style>
    """

    altura = 140 + (len(weeks) * 110)
    return estilos + "\n".join(html), altura


def _render_calendario_montagens(df_concluidas: pd.DataFrame) -> None:
    df_calendario = df_concluidas.copy()
    df_calendario['DATA_MONTAGEM_DATE'] = pd.to_datetime(df_calendario['DATA_MONTAGEM_DATE'], errors='coerce')
    df_calendario = df_calendario.dropna(subset=['DATA_MONTAGEM_DATE'])

    if df_calendario.empty:
        st.info("Não há montagens concluídas com data registrada para montar o calendário.")
        return

    df_calendario['DATA_MONTAGEM_DATE'] = df_calendario['DATA_MONTAGEM_DATE'].dt.normalize()

    meses_disponiveis = (
        df_calendario['DATA_MONTAGEM_DATE']
        .dt.to_period('M')
        .sort_values()
        .unique()
    )

    if len(meses_disponiveis) == 0:
        st.info("Nenhuma data disponível para o calendário.")
        return

    meses_labels = [period.strftime('%B/%Y') for period in meses_disponiveis]
    idx_default = len(meses_disponiveis) - 1

    mes_idx = st.selectbox(
        "Selecione o mês",
        options=list(range(len(meses_disponiveis))),
        format_func=lambda i: meses_labels[i],
        index=idx_default,
        key="montagem_calendario_mes",
    )

    mes_period = meses_disponiveis[mes_idx]
    mes_inicio = mes_period.to_timestamp()
    mes_fim = (mes_period + 1).to_timestamp() - pd.Timedelta(days=1)

    cal = calendar.Calendar(firstweekday=6)  # Domingo
    month_weeks = cal.monthdatescalendar(mes_inicio.year, mes_inicio.month)

    registros = []
    for semana_idx, semana in enumerate(month_weeks):
        for dia in semana:
            registros.append({
                'data': pd.Timestamp(dia),
                'semana_idx': semana_idx,
                'no_mes': 1 if dia.month == mes_inicio.month else 0,
                'is_hoje': 1 if dia == pd.Timestamp.today().date() else 0,
            })

    calendario_df = pd.DataFrame(registros)

    agregados = (
        df_calendario[df_calendario['DATA_MONTAGEM_DATE'].between(mes_inicio, mes_fim)]
        .groupby('DATA_MONTAGEM_DATE')
        .agg(
            Montagens=('DATA_MONTAGEM_DATE', 'size'),
            Familias=('NOME_FAMILIA', _join_limited),
            Responsaveis=('RESPONSAVEL_MONTAGEM', _join_limited)
        )
        .reset_index()
        .rename(columns={'DATA_MONTAGEM_DATE': 'data'})
    )

    calendario_df = calendario_df.merge(agregados, on='data', how='left')
    calendario_df['Montagens'] = calendario_df['Montagens'].fillna(0).astype(int)
    calendario_df['Familias'] = calendario_df['Familias'].fillna('Sem montagens')
    calendario_df['Responsaveis'] = calendario_df['Responsaveis'].fillna('-')
    calendario_df['data'] = calendario_df['data'].dt.date

    weekday_names = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    calendario_html, altura = _montar_calendario_html(
        calendario_df,
        weeks=month_weeks,
        weekday_names=weekday_names,
        target_month=mes_inicio.month,
    )

    components.html(calendario_html, height=altura, scrolling=False)

from .utils import simplificar_nome_estagio
from utils.dataframe_utils import ensure_pandas_df


def exibir_montagem_requerimento(df_cartorio):
    """Exibe o painel de Montagem de Requerimento com métricas e desempenho por responsável."""

    # --- Carregar CSS global ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")

    st.subheader("Montagem de Requerimento")

    if df_cartorio is None or df_cartorio.empty:
        st.warning("Dados de cartório não disponíveis para esta análise.")
        return

    df = ensure_pandas_df(df_cartorio).copy()

    # Colunas necessárias
    col_stage = 'STAGE_ID'
    col_responsavel = 'UF_CRM_34_RESPONSAVEL_SOLICITAR_CARTORIO_ORIGEM'
    col_data_solicitacao = 'UF_CRM_34_DATA_SOLICITAR_CARTORIO_ORIGEM'
    col_nome_familia = 'UF_CRM_34_NOME_FAMILIA'
    col_id_familia = 'UF_CRM_34_ID_FAMILIA'

    required_cols = [col_stage, col_responsavel, col_data_solicitacao]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(
            "As seguintes colunas são necessárias para a visão de Montagem de Requerimento e não foram encontradas nos dados: "
            + ", ".join(missing)
        )
        return

    # Responsável & Data
    df['RESPONSAVEL_MONTAGEM'] = (
        df[col_responsavel]
        .fillna('Sem Responsável')
        .astype(str)
        .replace({'': 'Sem Responsável', 'nan': 'Sem Responsável'})
        .str.strip()
    )

    df['DATA_MONTAGEM'] = pd.to_datetime(df[col_data_solicitacao], errors='coerce')
    df['DATA_MONTAGEM_DATE'] = df['DATA_MONTAGEM'].dt.date

    # Tratar campos auxiliares de estágio
    df[col_stage] = df[col_stage].astype(str)
    df['ESTAGIO_LEGIVEL'] = df[col_stage].apply(simplificar_nome_estagio)

    stage_order = [
        'AGUARDANDO CERTIDÃO',
        'PESQUISA - BR',
        'BUSCA - CRC',
        'DEVOLUTIVA BUSCA - CRC',
        'APENAS ASS. REQ CLIENTE P/MONTAGEM',
        'MONTAGEM REQUERIMENTO CARTÓRIO',
        'SOLICITAR CARTÓRIO DE ORIGEM',
        'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'AGUARDANDO CARTÓRIO ORIGEM',
        'DEVOLUÇÃO ADM',
        'DEVOLVIDO REQUERIMENTO',
        'AGUARDANDO DECISÃO CLIENTE',
        'CERTIDÃO EMITIDA',
        'CERTIDÃO ENTREGUE',
        'CERTIDÃO DISPENSADA',
        'SOLICITAÇÃO DUPLICADA',
        'CANCELADO',
        'ENVIAR PARÓQUIA',
        'EMISSÃO CLIENTE'
    ]

    stage_rank = {nome: idx for idx, nome in enumerate(stage_order, start=1)}
    df['STAGE_RANK'] = df['ESTAGIO_LEGIVEL'].map(stage_rank)
    estagios_concluidos = {
        'DEVOLVIDO REQUERIMENTO',
        'SOLICITAR CARTÓRIO DE ORIGEM',
        'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'AGUARDANDO CARTÓRIO ORIGEM',
        'DEVOLUÇÃO ADM',
        'CERTIDÃO EMITIDA',
        'CERTIDÃO ENTREGUE',
        'CERTIDÃO DISPENSADA',
        'SOLICITAÇÃO DUPLICADA',
        'CANCELADO',
        'ENVIAR PARÓQUIA',
        'EMISSÃO CLIENTE'
    }

    def classificar_status(row):
        estagio = row['ESTAGIO_LEGIVEL']

        if estagio == 'AGUARDANDO DECISÃO CLIENTE':
            return 'Pendente de Montagem'

        if estagio in estagios_concluidos:
            return 'Montagem Concluída'

        if pd.notna(row['DATA_MONTAGEM']):
            return 'Montagem Concluída'

        return 'Pendente de Montagem'

    df['STATUS_MONTAGEM'] = df.apply(classificar_status, axis=1)

    if col_nome_familia in df.columns:
        df['NOME_FAMILIA'] = df[col_nome_familia].fillna('Família Desconhecida').astype(str)
    else:
        df['NOME_FAMILIA'] = 'Família Desconhecida'

    if col_id_familia in df.columns:
        df['ID_FAMILIA'] = df[col_id_familia].fillna('').astype(str)
    else:
        df['ID_FAMILIA'] = ''

    # --- Métricas Principais ---
    df_concluidas = df[df['STATUS_MONTAGEM'] == 'Montagem Concluída'].copy()

    if df_concluidas.empty:
        st.info("Nenhuma montagem concluída registrada até o momento.")
        return

    total_registros = len(df)
    total_montagens = len(df_concluidas)
    total_pendentes = (df['STATUS_MONTAGEM'] == 'Pendente de Montagem').sum()
    registros_classificados = total_montagens + total_pendentes
    taxa_conclusao = (total_montagens / registros_classificados * 100) if registros_classificados else 0
    responsaveis_ativos = df_concluidas[df_concluidas['RESPONSAVEL_MONTAGEM'] != 'Sem Responsável']['RESPONSAVEL_MONTAGEM'].nunique()

    st.markdown(
        f"""
        <style>
        .montagem-metricas {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin: 12px 0 24px 0;
        }}
        .montagem-card {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .montagem-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
        }}
        .montagem-card__label {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #6c757d;
            margin-bottom: 6px;
            font-weight: 600;
        }}
        .montagem-card__value {{
            font-size: 34px;
            font-weight: 700;
            color: #2b2f38;
            margin-bottom: 4px;
        }}
        .montagem-card__hint {{
            font-size: 11px;
            color: #868e96;
        }}
        </style>
        <div class="montagem-metricas">
            <div class="montagem-card">
                <div class="montagem-card__label">Itens Monitorados</div>
                <div class="montagem-card__value">{total_registros:,}</div>
                <div class="montagem-card__hint">Universo filtrado</div>
            </div>
            <div class="montagem-card">
                <div class="montagem-card__label">Montagens Concluídas</div>
                <div class="montagem-card__value">{total_montagens:,}</div>
                <div class="montagem-card__hint">Etapas já montadas</div>
            </div>
            <div class="montagem-card">
                <div class="montagem-card__label">Pendentes de Montagem</div>
                <div class="montagem-card__value">{total_pendentes:,}</div>
                <div class="montagem-card__hint">Etapas anteriores à montagem</div>
            </div>
            <div class="montagem-card">
                <div class="montagem-card__label">Taxa de Conclusão</div>
                <div class="montagem-card__value">{taxa_conclusao:.1f}%</div>
                <div class="montagem-card__hint">Montadas vs. classificadas</div>
            </div>
            <div class="montagem-card">
                <div class="montagem-card__label">Responsáveis Ativos</div>
                <div class="montagem-card__value">{responsaveis_ativos}</div>
                <div class="montagem-card__hint">Com ao menos uma montagem</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # --- Evolução diária ---
    df_montadas = df_concluidas[df_concluidas['DATA_MONTAGEM'].notna()].copy()

    if not df_montadas.empty:
        total_periodo = len(df_montadas)
        st.markdown(
            f"""
            <div style='display:flex; gap:12px; align-items:center; margin-bottom:8px;'>
                <div style='font-size:16px; font-weight:700; color:#0f172a;'>Evolução diária de montagens</div>
                <div style='background:rgba(37,99,235,0.15); color:#1d4ed8; font-weight:700; padding:4px 10px; border-radius:999px; font-size:12px; letter-spacing:0.06em;'>Total {total_periodo:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        evolucao = (
            df_montadas
            .groupby(pd.Grouper(key='DATA_MONTAGEM', freq='D'))
            .size()
            .reset_index(name='Montagens')
        )
        evolucao['DATA_MONTAGEM'] = pd.to_datetime(evolucao['DATA_MONTAGEM'])

        base_chart = alt.Chart(evolucao).encode(x=alt.X('DATA_MONTAGEM:T', title='Data'), y=alt.Y('Montagens:Q', title='Montagens concluídas'))
        area = base_chart.mark_area(line={'color': '#4a7bef'}, color='rgba(74, 123, 239, 0.35)')
        pontos = base_chart.mark_point(color='#1d4ed8', size=90)
        textos = base_chart.mark_text(dy=-12, color='#1d4ed8', fontWeight='bold').encode(text='Montagens:Q')

        chart = (area + pontos + textos).properties(title='Evolução diária de montagens', height=260)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Ainda não há montagens concluídas com data registrada dentro dos filtros selecionados.")

    # --- Desempenho por responsável ---
    st.markdown("### Ranking de Produção por Responsável")
    st.markdown(
        """
        <style>
        .montagem-ranking-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
        }
        .montagem-ranking-header h4 {
            margin: 0;
            font-size: 20px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: 0.02em;
        }
        .montagem-ranking-header span {
            font-size: 12px;
            text-transform: uppercase;
            color: #475569;
            letter-spacing: 0.08em;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    total_label = "montagem" if total_montagens == 1 else "montagens"
    st.markdown(
        f"""    
        <div class='montagem-ranking-header'>
            <h4>Líderes do Período</h4>
            <span>{total_montagens:,} {total_label}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    df_concluidas_valid = df_concluidas[df_concluidas['RESPONSAVEL_MONTAGEM'] != 'Sem Responsável'].copy()

    if df_concluidas_valid.empty:
        st.info("Montagens concluidas ainda não estão atribuídas a responsáveis.")
    else:
        ranking_responsaveis = (
            df_concluidas_valid
            .groupby('RESPONSAVEL_MONTAGEM')
            .size()
            .reset_index(name='total_montagens')
            .sort_values('total_montagens', ascending=False, kind='stable')
        )

        ranking_responsaveis['posicao'] = range(1, len(ranking_responsaveis) + 1)

        top_cards = ranking_responsaveis.head(3)
        if not top_cards.empty:
            st.markdown("**Top 3 responsáveis em montagens concluídas**")
            st.markdown(
                """
                <style>
                .montagem-ranking-cards {
                    display: grid;
                    gap: 12px;
                    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                    margin-bottom: 16px;
                }
                .montagem-ranking-card {
                    border-radius: 16px;
                    padding: 18px 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
                    border: 1px solid rgba(37, 99, 235, 0.2);
                    background: linear-gradient(135deg, rgba(248, 250, 252, 0.92), rgba(226, 232, 240, 0.85));
                }
                .montagem-ranking-card__posicao {
                    font-size: 13px;
                    font-weight: 600;
                    letter-spacing: 0.06em;
                    text-transform: uppercase;
                }
                .montagem-ranking-card__responsavel {
                    font-size: 20px;
                    font-weight: 700;
                    color: #0f172a;
                }
                .montagem-ranking-card__valor {
                    font-size: 30px;
                    font-weight: 800;
                    color: #0f172a;
                }
                .montagem-ranking-card__label {
                    font-size: 12px;
                    text-transform: uppercase;
                    color: #475569;
                    letter-spacing: 0.04em;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            cards_html = ["<div class='montagem-ranking-cards'>"]
            palette = ["#2563eb", "#0ea5e9", "#10b981"]
            for idx, row in top_cards.iterrows():
                cor = palette[min(row['posicao'] - 1, len(palette) - 1)]
                total_montagens = int(row['total_montagens'])
                label_montagem = "Montagem Concluída" if total_montagens == 1 else "Montagens Concluídas"
                card_html = textwrap.dedent(
                    f"""
                    <div class='montagem-ranking-card' style="border-color:{cor}33; background: linear-gradient(135deg, {cor}20, {cor}05);">
                        <div class='montagem-ranking-card__posicao' style="color:{cor};">Top {int(row['posicao'])}</div>
                        <div class='montagem-ranking-card__responsavel'>{row['RESPONSAVEL_MONTAGEM']}</div>
                        <div class='montagem-ranking-card__valor'>{total_montagens:,}</div>
                        <div class='montagem-ranking-card__label'>{label_montagem}</div>
                    </div>
                    """
                )
                cards_html.append(card_html.replace("\n", "").replace("  ", " ").strip())
            cards_html.append("</div>")
            st.markdown("".join(cards_html), unsafe_allow_html=True)

        if len(ranking_responsaveis) > 3:
            st.markdown("#### Demais posições")
            colunas_cards = [
                "Posição",
                "Responsável",
                "Montagens Concluídas"
            ]
            restante = ranking_responsaveis.iloc[3:]

            st.markdown(
                """
                <style>
                .montagem-ranking-list {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                .montagem-ranking-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border: 1px solid rgba(148, 163, 184, 0.3);
                    border-radius: 14px;
                    padding: 12px 16px;
                    background: #ffffff;
                    box-shadow: 0 10px 18px rgba(15, 23, 42, 0.04);
                    transition: transform 0.15s ease, box-shadow 0.15s ease;
                }
                .montagem-ranking-item:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 14px 24px rgba(37, 99, 235, 0.12);
                }
                .montagem-ranking-item__badge {
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #cbd5f5, #e2e8f0);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 700;
                    color: #1e293b;
                }
                .montagem-ranking-item__info {
                    display: flex;
                    flex-direction: column;
                }
                .montagem-ranking-item__titulo {
                    font-weight: 700;
                    color: #0f172a;
                }
                .montagem-ranking-item__descricao {
                    font-size: 12px;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }
                .montagem-ranking-item__valor {
                    font-weight: 800;
                    font-size: 20px;
                    color: #0f172a;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            restante_cards = ["<div class='montagem-ranking-list'>"]
            for _, row in restante.iterrows():
                posicao = int(row['posicao'])
                total_montagens = int(row['total_montagens'])
                restante_html = textwrap.dedent(
                    f"""
                    <div class='montagem-ranking-item'>
                        <div style="display:flex; align-items:center; gap:12px;">
                            <div class='montagem-ranking-item__badge'>{posicao}</div>
                            <div class='montagem-ranking-item__info'>
                                <div class='montagem-ranking-item__titulo'>{row['RESPONSAVEL_MONTAGEM']}</div>
                                <div class='montagem-ranking-item__descricao'>Montagens Concluídas</div>
                            </div>
                        </div>
                        <div class='montagem-ranking-item__valor'>{total_montagens:,}</div>
                    </div>
                    """
                )
                restante_cards.append(restante_html.replace("\n", "").replace("  ", " ").strip())
            restante_cards.append("</div>")
            st.markdown("".join(restante_cards), unsafe_allow_html=True)

    st.markdown("### Produção Diária por Responsável")
    producao_diaria = df_concluidas_valid.dropna(subset=['DATA_MONTAGEM_DATE']).copy()
    if not producao_diaria.empty:
        producao_diaria['DATA_MONTAGEM_DATE'] = pd.to_datetime(producao_diaria['DATA_MONTAGEM_DATE'])

    if producao_diaria.empty:
        st.info("Nenhuma montagem concluída com data registrada.")
    else:
        data_anos = sorted(producao_diaria['DATA_MONTAGEM_DATE'].dt.year.unique(), reverse=True)
        ano_selecionado = st.selectbox("Ano", options=data_anos, index=0, key="montagem_filtro_ano")

        producao_ano = producao_diaria[producao_diaria['DATA_MONTAGEM_DATE'].dt.year == ano_selecionado]

        meses_map = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        meses_disponiveis = sorted(producao_ano['DATA_MONTAGEM_DATE'].dt.month.unique())
        mes_labels = [f"{meses_map[m]}" for m in meses_disponiveis]
        mes_idx = st.selectbox("Mês", options=list(range(len(meses_disponiveis))), format_func=lambda i: mes_labels[i], index=len(meses_disponiveis)-1, key="montagem_filtro_mes")
        mes_selecionado = meses_disponiveis[mes_idx]

        producao_periodo = producao_ano[producao_ano['DATA_MONTAGEM_DATE'].dt.month == mes_selecionado]

        data_inicio = producao_periodo['DATA_MONTAGEM_DATE'].min()
        data_fim = producao_periodo['DATA_MONTAGEM_DATE'].max()
        intervalo = st.date_input(
            "Período personalizado",
            value=(data_inicio.date(), data_fim.date()),
            min_value=data_inicio.date(),
            max_value=data_fim.date(),
            key="montagem_periodo_personalizado"
        )

        if isinstance(intervalo, tuple) and len(intervalo) == 2:
            start_date, end_date = intervalo
            producao_periodo = producao_periodo[
                (producao_periodo['DATA_MONTAGEM_DATE'].dt.date >= start_date) &
                (producao_periodo['DATA_MONTAGEM_DATE'].dt.date <= end_date)
            ]

        resumo_periodo = (
            producao_periodo
            .groupby('RESPONSAVEL_MONTAGEM')
            .size()
            .reset_index(name='total_montagens')
            .sort_values('total_montagens', ascending=False, kind='stable')
        )

        if resumo_periodo.empty:
            st.info("Sem montagens concluídas no período selecionado.")
        else:
            st.caption("Resumo de montagens concluídas por responsável no intervalo selecionado.")
            st.markdown(
                """
                <style>
                .montagem-resumo-periodo {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                    gap: 12px;
                }
                .montagem-resumo-card {
                    background: linear-gradient(135deg, rgba(226, 232, 240, 0.6), rgba(226, 232, 240, 0.35));
                    border: 1px solid rgba(148,163,184,0.25);
                    border-radius: 16px;
                    padding: 14px 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    box-shadow: 0 12px 22px rgba(15,23,42,0.08);
                }
                .montagem-resumo-card__titulo {
                    font-size: 16px;
                    font-weight: 700;
                    color: #0f172a;
                }
                .montagem-resumo-card__valor {
                    font-size: 28px;
                    font-weight: 800;
                    color: #0f172a;
                }
                .montagem-resumo-card__label {
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: #475569;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            cards_periodo = ["<div class='montagem-resumo-periodo'>"]
            for _, row in resumo_periodo.iterrows():
                total_montagens = int(row['total_montagens'])
                label = "Montagem no Período" if total_montagens == 1 else "Montagens no Período"
                periodo_html = textwrap.dedent(
                    f"""
                    <div class='montagem-resumo-card'>
                        <div class='montagem-resumo-card__titulo'>{row['RESPONSAVEL_MONTAGEM']}</div>
                        <div class='montagem-resumo-card__valor'>{total_montagens:,}</div>
                        <div class='montagem-resumo-card__label'>{label}</div>
                    </div>
                    """
                )
                cards_periodo.append(periodo_html.replace("\n", "").replace("  ", " ").strip())
            cards_periodo.append("</div>")
            st.markdown("".join(cards_periodo), unsafe_allow_html=True)

    st.markdown("### Calendário de Montagens")
    st.caption("Visualize, por dia e responsável, como as montagens concluídas se distribuíram ao longo do mês selecionado.")
    _render_calendario_montagens(df_concluidas)


