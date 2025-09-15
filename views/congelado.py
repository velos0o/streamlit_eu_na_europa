import streamlit as st
import pandas as pd
import os
import unicodedata

from api.bitrix_connector import load_merged_data
from views.cartorio_new.data_loader import carregar_dados_cartorio
from utils.dataframe_utils import ensure_pandas_df
from utils.refresh_utils import load_csv_with_refresh
from utils.google_sheets_connector import get_google_sheets_client, fetch_data_from_sheet


def _carregar_congelados_df() -> pd.DataFrame:
    """Carrega deals do funil 46 e filtra registros com congelamento indicado.

    Campos relevantes:
    - UF_CRM_1722883482527: Nome da Família
    - UF_CRM_1722605592778: ID da Família
    - UF_CRM_1757540720: Tipo do congelado (lista)
    - TITLE, ID, STAGE_ID (apoio)
    """
    df = load_merged_data(category_id=46, debug=False, force_reload=False)
    if df is None or df.empty:
        return pd.DataFrame()

    # Garantir colunas esperadas
    col_nome = 'UF_CRM_1722883482527'
    col_id_familia = 'UF_CRM_1722605592778'
    col_tipo = 'UF_CRM_1757540720'

    for col in [col_nome, col_id_familia, col_tipo]:
        if col not in df.columns:
            df[col] = None

    # Tratar campo multi-seleção (exibir TODOS os valores encontrados, sem filtrar)

    def parse_multiselect(valor) -> list:
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return []
        if isinstance(valor, list):
            return [str(v).strip() for v in valor if str(v).strip()]
        s = str(valor).strip()
        if not s:
            return []
        # Tentar JSON array
        try:
            import json
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass
        # Normalizar e dividir por separadores via regex (vírgula, quebra de linha, ; | / \ tab)
        s = s.replace('\r\n', '\n').replace('\r', '\n')
        try:
            import re
            tokens = re.split(r"[\,\n;\|/\\\t]+", s)
            tokens = [t.strip().strip('"\'').strip() for t in tokens if t and t.strip()]
            return tokens if tokens else []
        except Exception:
            pass
        # Valor único
        return [s]

    df['__tipos_lista__'] = df[col_tipo].apply(parse_multiselect)
    # Remover linhas sem qualquer tipo selecionado
    df = df[df['__tipos_lista__'].map(lambda x: len(x) > 0)].copy()
    if df.empty:
        return pd.DataFrame(columns=[col_nome, col_id_familia, 'TITLE', 'ID', 'STAGE_ID', 'Congelado Emissão Brasileira', 'Congelado Comune', 'Congelado Protocolo'])

    # Sanitizar e normalizar
    def _sanitize_token(v):
        s = str(v).strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()
        return s

    def _normalize(s: str) -> str:
        import unicodedata
        s = str(s).strip()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(ch for ch in s if not unicodedata.combining(ch))
        return s.upper().strip()

    invalid_norm = {
        '', 'NONE', 'NULL', 'NULO', 'NENHUM', 'N/A', 'NA',
        'NAO SELECIONADO', 'NAO SELECIONADA', 'NAO INFORMADO', 'NAO INFORMADA',
        'SEM VALOR', 'SEM SELECAO', 'SEM SELEÇÃO', '-'
    }

    def _tem_tipo(tokens, alvo_norm):
        if not tokens:
            return False
        tokens_clean = [_sanitize_token(t) for t in tokens]
        tokens_norm = [_normalize(t) for t in tokens_clean]
        tokens_validos = [t for t in tokens_norm if t not in invalid_norm]
        return alvo_norm in tokens_validos

    alvo_emissao = 'EMISSAO BRASILERIA'
    alvo_comune = 'COMUNE'
    alvo_protocolo = 'PROTOCOLO'

    df['Congelado Emissão Brasileira'] = df['__tipos_lista__'].apply(lambda lst: 'SIM' if _tem_tipo(lst, alvo_emissao) else '')
    df['Congelado Comune'] = df['__tipos_lista__'].apply(lambda lst: 'SIM' if _tem_tipo(lst, alvo_comune) else '')
    df['Congelado Protocolo'] = df['__tipos_lista__'].apply(lambda lst: 'SIM' if _tem_tipo(lst, alvo_protocolo) else '')

    # Manter apenas registros que possuam ao menos um dos tipos
    mask_any = (
        (df['Congelado Emissão Brasileira'] == 'SIM') |
        (df['Congelado Comune'] == 'SIM') |
        (df['Congelado Protocolo'] == 'SIM')
    )
    df = df[mask_any].copy()

    cols_show = [
        col_nome,
        col_id_familia,
        'Congelado Emissão Brasileira',
        'Congelado Comune',
        'Congelado Protocolo',
        'TITLE',
        'ID',
        'STAGE_ID'
    ]
    cols_show_presentes = [c for c in cols_show if c in df.columns]
    df_final = df[cols_show_presentes].copy()

    # Ordenação simples por Nome e ID Família
    sort_cols = [c for c in ['Nome da Família', 'ID da Família'] if c in df_final.columns]
    if not sort_cols:
        sort_cols = [c for c in [col_nome, col_id_familia] if c in df_final.columns]
    if sort_cols:
        df_final = df_final.sort_values(by=sort_cols, kind='stable')

    return df_final


def _status_protocolo_por_familia(df_cat46: pd.DataFrame) -> pd.DataFrame:
    """Monta a visão STATUS DE PROTOCOLO por família para deals cat 46 marcados como 'Congelado Protocolo'.

    Etapas contempladas (em ordem):
    70  → EMISSÃO BRASILEIRA
    90  → ANÁLISE DOCUMENTAL (inclui variantes: análise negativa/positiva/reanálise)
    130 → TRADUÇÃO
    140 → APOSTILAMENTO
    150 → DRIVE
    160 → RECURSO
    170 → PROTOCOLO

    Regras:
    - Considera concluída (✅) a etapa se existir ao menos um card da família em algum estágio mapeado para aquela etapa.
    - Para ANÁLISE DOCUMENTAL, considera qualquer um dos códigos de análise (90/100/110/120).
    - Ordena famílias pela maior ordem atingida (mais próximo de PROTOCOLO primeiro).
    """
    if df_cat46 is None or df_cat46.empty:
        return pd.DataFrame()

    col_nome = 'UF_CRM_1722883482527'
    col_id_familia = 'UF_CRM_1722605592778'
    col_stage = 'STAGE_ID'

    for c in [col_nome, col_id_familia, col_stage, 'Congelado Protocolo']:
        if c not in df_cat46.columns:
            df_cat46[c] = None

    df_proto = df_cat46[df_cat46['Congelado Protocolo'].astype(str).str.upper().eq('SIM')].copy()
    if df_proto.empty:
        return pd.DataFrame(columns=['Nome da Família', 'ID da Família', 'EMISSÃO BRASILEIRA', 'ANÁLISE DOCUMENTAL', 'TRADUÇÃO', 'APOSTILAMENTO', 'DRIVE', 'RECURSO', 'PROTOCOLO'])

    # Mapeamento por códigos (usamos o sufixo UC_* para busca robusta em STAGE_ID)
    codigos_por_etapa = {
        'EMISSÃO BRASILEIRA': {'UC_8Z2EZF'},
        'ANÁLISE DOCUMENTAL': {'UC_N1FI74', 'UC_SKSQFO', 'UC_K952AX', 'UC_2JQ8E2R'},  # inclui negativa/positiva/reanálise
        'TRADUÇÃO': {'UC_CSFCZP'},
        'APOSTILAMENTO': {'UC_F12U3R'},
        'DRIVE': {'UC_1ARFYMM'},
        'RECURSO': {'UC_SISEKVR'},
        'PROTOCOLO': {'UC_5W7TYZ'},
    }

    ordem_por_etapa = {
        'EMISSÃO BRASILEIRA': 70,
        'ANÁLISE DOCUMENTAL': 90,  # 90/100/110/120 colapsados
        'TRADUÇÃO': 130,
        'APOSTILAMENTO': 140,
        'DRIVE': 150,
        'RECURSO': 160,
        'PROTOCOLO': 170,
    }

    def contem_codigo(stage_value: str, codigo_sufixo: str) -> bool:
        if pd.isna(stage_value):
            return False
        s = str(stage_value)
        return codigo_sufixo in s

    def detectar_maior_ordem(stages_serie: pd.Series) -> int:
        if stages_serie is None or stages_serie.empty:
            return 0
        valores = stages_serie.dropna().astype(str).tolist()
        maior = 0
        for v in valores:
            for etapa, codigos in codigos_por_etapa.items():
                for codigo in codigos:
                    if codigo in v:
                        maior = max(maior, ordem_por_etapa.get(etapa, 0))
        return maior

    # Agregar por família
    grupo_cols = [c for c in [col_nome, col_id_familia] if c in df_proto.columns]
    if not grupo_cols:
        return pd.DataFrame()

    registros = []
    for chave, g in df_proto.groupby(grupo_cols):
        if isinstance(chave, tuple):
            nome_fam, id_fam = chave[0], chave[1]
        else:
            nome_fam, id_fam = chave, ''

        maior_ordem = detectar_maior_ordem(g[col_stage])
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

    # Garantir colunas na ordem desejada
    colunas_ordenadas = [
        'Nome da Família', 'ID da Família',
        'EMISSÃO BRASILEIRA', 'ANÁLISE DOCUMENTAL', 'TRADUÇÃO', 'APOSTILAMENTO', 'DRIVE', 'RECURSO', 'PROTOCOLO'
    ]
    presentes = [c for c in colunas_ordenadas if c in df_out.columns]
    if presentes:
        df_out = df_out[presentes]
    return df_out


def show_congelado():
    st.markdown("<h1 class='page-title'>Congelado</h1>", unsafe_allow_html=True)

    with st.spinner("Carregando dados..."):
        df_congelados = _carregar_congelados_df()

    if df_congelados.empty:
        st.info("Nenhum registro congelado encontrado no funil 46.")
        return

    # Renomear para apresentação
    rename_map = {
        'UF_CRM_1722883482527': 'Nome da Família',
        'UF_CRM_1722605592778': 'ID da Família',
        'TITLE': 'Requerente',
        'ID': 'ID Deal',
        'STAGE_ID': 'Estágio'
    }

    df_mostrar = df_congelados.rename(columns={k: v for k, v in rename_map.items() if k in df_congelados.columns})

    st.dataframe(
        ensure_pandas_df(df_mostrar),
        hide_index=True,
        use_container_width=True
    )

    

    # Construir visão consolidada por família (usado para acompanhamento; não exibido)
    col_nome = 'UF_CRM_1722883482527'
    col_id_familia = 'UF_CRM_1722605592778'

    df_flags = df_congelados.copy()
    # Garantir colunas de flags
    for c in ['Congelado Emissão Brasileira', 'Congelado Comune', 'Congelado Protocolo']:
        if c not in df_flags.columns:
            df_flags[c] = ''

    # Agregar por família (qualquer SIM dentro do grupo => SIM)
    def any_sim(series):
        return 'SIM' if (series.astype(str).str.upper() == 'SIM').any() else ''

    group_cols = [c for c in [col_nome, col_id_familia] if c in df_flags.columns]
    if group_cols:
        df_consol = (
            df_flags.groupby(group_cols).agg({
                'Congelado Emissão Brasileira': any_sim,
                'Congelado Comune': any_sim,
                'Congelado Protocolo': any_sim,
            }).reset_index()
        )
    else:
        df_consol = pd.DataFrame(columns=[
            col_nome, col_id_familia,
            'Congelado Emissão Brasileira', 'Congelado Comune', 'Congelado Protocolo'
        ])

    # Trazer status de congelado do SPA (UF_CRM_34_CONGELADO)
    with st.spinner("Carregando status de congelamento (Emissões)..."):
        try:
            df_cartorio = carregar_dados_cartorio()
        except Exception:
            df_cartorio = pd.DataFrame()

    col_id_familia_spa = 'UF_CRM_34_ID_FAMILIA'
    col_nome_familia_spa = 'UF_CRM_34_NOME_FAMILIA'
    col_congelado_spa = 'UF_CRM_34_CONGELADO'

    if not df_cartorio.empty and col_id_familia_spa in df_cartorio.columns:
        df_spa = df_cartorio[[c for c in [col_id_familia_spa, col_nome_familia_spa, col_congelado_spa] if c in df_cartorio.columns]].copy()
        # Normalizar status por família: CONGELADO se qualquer item marcar
        def norm(val: str) -> str:
            s = str(val or '').strip().upper()
            return 'CONGELADO' if s == 'CONGELADO' else 'NÃO CONGELADO'
        # Agrupar por ID família do SPA
        if col_congelado_spa in df_spa.columns:
            spa_agg = (
                df_spa.groupby(col_id_familia_spa)[col_congelado_spa]
                .apply(lambda s: 'CONGELADO' if (s.astype(str).str.upper() == 'CONGELADO').any() else 'NÃO CONGELADO')
                .reset_index()
            )
        else:
            spa_agg = df_spa.copy()
            spa_agg[col_congelado_spa] = 'NÃO CONGELADO'

        # Preparar chaves de merge (strings, trim)
        if col_id_familia in df_consol.columns:
            df_consol[col_id_familia] = df_consol[col_id_familia].astype(str).str.strip()
        spa_agg[col_id_familia_spa] = spa_agg[col_id_familia_spa].astype(str).str.strip()

        df_consol = pd.merge(
            df_consol, spa_agg,
            left_on=col_id_familia,
            right_on=col_id_familia_spa,
            how='left'
        )
        # Se não houver informação no SPA, manter vazio
        if col_congelado_spa in df_consol.columns:
            df_consol[col_congelado_spa] = df_consol[col_congelado_spa].fillna('NÃO CONGELADO')
    else:
        # Sem dados do SPA: criar coluna default
        df_consol[col_congelado_spa] = 'NÃO CONGELADO'

    # Preparar para exibição posterior
    rename_map2 = {
        'UF_CRM_1722883482527': 'Nome da Família',
        'UF_CRM_1722605592778': 'ID da Família',
        col_congelado_spa: 'UF_CRM_34_CONGELADO'
    }
    df_consol_show = df_consol.rename(columns={k: v for k, v in rename_map2.items() if k in df_consol.columns})
    ordered_cols = ['Nome da Família', 'ID da Família', 'UF_CRM_34_CONGELADO']
    cols_presentes = [c for c in ordered_cols if c in df_consol_show.columns]
    df_consol_show = df_consol_show[cols_presentes].copy()

    # ============================
    # Métricas Macros
    # ============================
    st.markdown("---")
    st.markdown("#### Métricas Macros")

    # Totais por tipo de congelado (Emissão, Comune)
    total_emissao = 0
    total_comune = 0
    try:
        base_id_col = 'UF_CRM_1722605592778'
        col_flag_emissao = 'Congelado Emissão Brasileira'
        col_flag_comune = 'Congelado Comune'
        df_tmp = df_congelados.copy()
        if base_id_col in df_tmp.columns:
            df_tmp[base_id_col] = df_tmp[base_id_col].astype(str).str.strip()
        # Emissão
        if col_flag_emissao in df_tmp.columns:
            em = df_tmp[df_tmp[col_flag_emissao].astype(str).str.upper().eq('SIM')]
            if base_id_col in em.columns:
                total_emissao = em[base_id_col].replace('', pd.NA).dropna().nunique()
            else:
                total_emissao = len(em)
        # Comune
        if col_flag_comune in df_tmp.columns:
            cm = df_tmp[df_tmp[col_flag_comune].astype(str).str.upper().eq('SIM')]
            if base_id_col in cm.columns:
                total_comune = cm[base_id_col].replace('', pd.NA).dropna().nunique()
            else:
                total_comune = len(cm)
    except Exception:
        total_emissao, total_comune = 0, 0

    # Famílias congeladas no SPA
    familias_congeladas_count = 0
    col_congelado_spa = 'UF_CRM_34_CONGELADO'
    if col_congelado_spa in df_consol_show.columns:
        try:
            familias_congeladas_count = int(
                (df_consol_show[col_congelado_spa].astype(str).str.upper() == 'CONGELADO').sum()
            )
        except Exception:
            familias_congeladas_count = 0

    # Famílias concluídas (100% dos itens no SPA)
    familias_concluidas_count = 0
    if not df_cartorio.empty and 'ID da Família' in df_consol_show.columns and 'UF_CRM_34_ID_FAMILIA' in df_cartorio.columns:
        try:
            df_spa_base_macro = df_cartorio[['UF_CRM_34_ID_FAMILIA', 'STAGE_ID', 'STAGE_NAME']].copy()
            success_mask_macro = pd.Series(False, index=df_spa_base_macro.index)
            if 'STAGE_ID' in df_spa_base_macro.columns:
                success_mask_macro = success_mask_macro | df_spa_base_macro['STAGE_ID'].astype(str).str.contains('SUCCESS', na=False)
            if 'STAGE_NAME' in df_spa_base_macro.columns:
                success_mask_macro = success_mask_macro | df_spa_base_macro['STAGE_NAME'].astype(str).str.upper().isin(['CERTIDÃO EMITIDA', 'CERTIDÃO ENTREGUE'])
            df_spa_base_macro['__success__'] = success_mask_macro.astype(int)
            fam_metrics_macro = df_spa_base_macro.groupby('UF_CRM_34_ID_FAMILIA').agg(
                total_itens=('__success__', 'count'),
                concluidas=('__success__', 'sum')
            ).reset_index()
            fam_metrics_macro['UF_CRM_34_ID_FAMILIA'] = fam_metrics_macro['UF_CRM_34_ID_FAMILIA'].astype(str).str.strip()
            df_congeladas_ids = (
                df_consol_show[df_consol_show[col_congelado_spa].astype(str).str.upper() == 'CONGELADO']
                ['ID da Família']
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )
            fam_sel = fam_metrics_macro[fam_metrics_macro['UF_CRM_34_ID_FAMILIA'].isin(df_congeladas_ids)].copy()
            familias_concluidas_count = int(((fam_sel['total_itens'] > 0) & (fam_sel['concluidas'] == fam_sel['total_itens'])).sum())
        except Exception:
            familias_concluidas_count = 0

    st.markdown("""
    <style>
    .metricas-container-macro { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 12px 0 4px 0; }
    .metrica-custom-macro { background: #F8F9FA; border: 2px solid #DEE2E6; border-radius: 6px; padding: 16px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metrica-custom-macro:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: #ADB5BD; }
    .metrica-custom-macro .label { color: #6C757D; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; line-height: 1.2; }
    .metrica-custom-macro .valor { color: #495057; font-weight: 700; font-size: 30px; line-height: 1.2; margin-bottom: 4px; }
    </style>
    <div class="metricas-container-macro">
        <div class="metrica-custom-macro"><div class="label">Famílias Congeladas</div><div class="valor">""" + str(int(familias_congeladas_count)) + """</div></div>
        <div class="metrica-custom-macro"><div class="label">Emissão Congeladas</div><div class="valor">""" + str(int(total_emissao)) + """</div></div>
        <div class="metrica-custom-macro"><div class="label">Comune Congeladas</div><div class="valor">""" + str(int(total_comune)) + """</div></div>
        <div class="metrica-custom-macro"><div class="label">Concluídas</div><div class="valor">""" + str(int(familias_concluidas_count)) + """</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ============================
    # STATUS DE PROTOCOLO (logo abaixo das métricas)
    # ============================
    st.markdown("---")
    st.markdown("#### STATUS DE PROTOCOLO")
    st.caption("Etapas concluídas até o protocolo para famílias marcadas como 'Congelado Protocolo'. Onde estiver ✅ está completo.")

    try:
        df_status = _status_protocolo_por_familia(df_congelados)
    except Exception as e:
        df_status = pd.DataFrame()
        st.warning(f"Falha ao montar STATUS DE PROTOCOLO: {e}")

    if df_status is None or df_status.empty:
        st.info("Nenhuma família marcada como 'Congelado Protocolo' encontrada.")
    else:
        st.dataframe(
            ensure_pandas_df(df_status),
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
    # Acompanhamento de Emissão Congeladas
    # ============================
    st.markdown("---")
    st.markdown("#### Acompanhamento de Emissão Congeladas")

    # Enriquecer com Responsável (via SPA) para filtros, se possível
    responsavel_col_name = 'Responsável'
    if not df_cartorio.empty and 'ASSIGNED_BY_NAME' in df_cartorio.columns and col_id_familia_spa in df_cartorio.columns:
        mapa_resp = (
            df_cartorio[[col_id_familia_spa, 'ASSIGNED_BY_NAME']]
            .dropna(subset=[col_id_familia_spa])
            .drop_duplicates(subset=[col_id_familia_spa])
        )
        df_consol_show = pd.merge(
            df_consol_show,
            mapa_resp,
            left_on='ID da Família' if 'ID da Família' in df_consol_show.columns else col_id_familia,
            right_on=col_id_familia_spa,
            how='left'
        )
        if 'ASSIGNED_BY_NAME' in df_consol_show.columns:
            df_consol_show[responsavel_col_name] = df_consol_show['ASSIGNED_BY_NAME']
            # Limpeza
            cols_drop_aux = [c for c in ['ASSIGNED_BY_NAME', col_id_familia_spa] if c in df_consol_show.columns]
            if cols_drop_aux:
                df_consol_show.drop(columns=cols_drop_aux, inplace=True)
    else:
        df_consol_show[responsavel_col_name] = ''

    # Filtros
    with st.expander("Filtros", expanded=True):
        col_f1, col_f3, col_f4 = st.columns([0.45, 0.3, 0.25])

        with col_f1:
            termo_busca_familia = st.text_input("Buscar Família/Contrato:", placeholder="Digite parte do nome...")

        with col_f3:
            # Status do SPA
            status_congelado = st.selectbox(
                "Status Congelado (SPA):",
                options=["Todos", "CONGELADO", "NÃO CONGELADO"],
                index=0
            )

        with col_f4:
            # Responsável
            responsaveis = sorted([r for r in df_consol_show[responsavel_col_name].dropna().astype(str).unique().tolist() if r.strip() != ''])
            resp_sel = st.multiselect(
                "Responsável (SPA):",
                options=responsaveis,
                placeholder="Selecione um ou mais"
            )

    # Aplicar filtros
    df_acomp = df_consol_show.copy()
    if termo_busca_familia:
        if 'Nome da Família' in df_acomp.columns:
            df_acomp = df_acomp[df_acomp['Nome da Família'].astype(str).str.contains(termo_busca_familia, case=False, na=False)]
    if status_congelado != 'Todos' and 'UF_CRM_34_CONGELADO' in df_acomp.columns:
        df_acomp = df_acomp[df_acomp['UF_CRM_34_CONGELADO'].astype(str).str.upper() == status_congelado]
    if resp_sel and responsavel_col_name in df_acomp.columns:
        df_acomp = df_acomp[df_acomp[responsavel_col_name].isin(resp_sel)]

    # Exibir apenas famílias marcadas como CONGELADO no SPA
    if 'UF_CRM_34_CONGELADO' in df_acomp.columns:
        df_acomp = df_acomp[df_acomp['UF_CRM_34_CONGELADO'].astype(str).str.upper() == 'CONGELADO']

    # KPIs: famílias, concluídas e % conclusão com base no SPA
    total_familias = len(df_acomp) if not df_acomp.empty else 0
    # Buscar métricas de conclusão no SPA para as famílias selecionadas
    concluidas = 0
    total_itens = 0
    if not df_cartorio.empty and total_familias > 0 and 'ID da Família' in df_acomp.columns and col_id_familia_spa in df_cartorio.columns:
        ids_sel = df_acomp['ID da Família'].astype(str).str.strip().unique().tolist()
        df_spa_sel = df_cartorio[df_cartorio[col_id_familia_spa].astype(str).str.strip().isin(ids_sel)].copy()
        if not df_spa_sel.empty:
            total_itens = len(df_spa_sel)
            # Concluídas: heurística SUCCESS em STAGE_ID ou STAGE_NAME em (CERTIDÃO EMITIDA/ENTREGUE)
            mask_success = df_spa_sel['STAGE_ID'].astype(str).str.contains('SUCCESS', na=False) if 'STAGE_ID' in df_spa_sel.columns else False
            if 'STAGE_NAME' in df_spa_sel.columns:
                mask_success = mask_success | df_spa_sel['STAGE_NAME'].astype(str).str.upper().isin(['CERTIDÃO EMITIDA', 'CERTIDÃO ENTREGUE'])
            concluidas = int(mask_success.sum()) if hasattr(mask_success, 'sum') else 0
    perc_conclusao = (concluidas / total_itens * 100) if total_itens > 0 else 0.0

    # KPIs em cards (novo formato) – remover card de "Concluídas (itens)"
    st.markdown("""
    <style>
    .metricas-container-cong-top { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 12px 0 4px 0; }
    .metrica-custom-cong { background: #F8F9FA; border: 2px solid #DEE2E6; border-radius: 6px; padding: 16px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metrica-custom-cong:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: #ADB5BD; }
    .metrica-custom-cong .label { color: #6C757D; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; line-height: 1.2; }
    .metrica-custom-cong .valor { color: #495057; font-weight: 700; font-size: 30px; line-height: 1.2; margin-bottom: 4px; }
    </style>
    <div class="metricas-container-cong-top">
        <div class="metrica-custom-cong"><div class="label">Famílias</div><div class="valor">""" + str(int(total_familias)) + """</div></div>
        <div class="metrica-custom-cong"><div class="label">% Conclusão (itens)</div><div class="valor">""" + (f"{perc_conclusao:.1f}%") + """</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Métricas específicas: CERTIDÕES EMITIDAS vs PENDENTES (design do acompanhamento)
    emitidas_count = 0
    pendentes_count = 0
    if not df_cartorio.empty and total_familias > 0 and 'ID da Família' in df_acomp.columns and col_id_familia_spa in df_cartorio.columns:
        ids_sel = df_acomp['ID da Família'].astype(str).str.strip().unique().tolist()
        df_spa_sel = df_cartorio[df_cartorio[col_id_familia_spa].astype(str).str.strip().isin(ids_sel)].copy()
        if not df_spa_sel.empty:
            total_itens_emit_check = len(df_spa_sel)
            # Emitidas: preferir STAGE_NAME == CERTIDÃO EMITIDA; fallback SUCCESS
            mask_emitidas = pd.Series(False, index=df_spa_sel.index)
            if 'STAGE_NAME' in df_spa_sel.columns:
                mask_emitidas = df_spa_sel['STAGE_NAME'].astype(str).str.upper().eq('CERTIDÃO EMITIDA')
            if 'STAGE_ID' in df_spa_sel.columns:
                mask_emitidas = mask_emitidas | df_spa_sel['STAGE_ID'].astype(str).str.contains('SUCCESS', na=False)
            emitidas_count = int(mask_emitidas.sum())
            pendentes_count = int(total_itens_emit_check - emitidas_count)

    st.markdown("""
    <style>
    .metrica-custom-cong {
        background: #F8F9FA;
        border: 2px solid #DEE2E6;
        border-radius: 6px;
        padding: 16px;
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .metrica-custom-cong:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: #ADB5BD; }
    .metrica-custom-cong .label { color: #6C757D; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; line-height: 1.2; }
    .metrica-custom-cong .valor { color: #495057; font-weight: 700; font-size: 30px; line-height: 1.2; margin-bottom: 4px; }
    .metricas-container-cong2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 12px 0 4px 0; }
    .metrica-emitidas { background: #E8F5E9; border-color: #A5D6A7; }
    .metrica-pendentes { background: #FFF3E0; border-color: #FFCC80; }
    </style>
    <div class="metricas-container-cong2">
        <div class="metrica-custom-cong metrica-emitidas"><div class="label">Certidões Emitidas</div><div class="valor">""" + str(int(emitidas_count)) + """</div></div>
        <div class="metrica-custom-cong metrica-pendentes"><div class="label">Certidões Pendentes</div><div class="valor">""" + str(int(pendentes_count)) + """</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Exibição final com progresso individual (Concluídas/Total e barra %)
    df_acomp_show = df_acomp.copy()
    if 'UF_CRM_34_CONGELADO' in df_acomp_show.columns:
        df_acomp_show = df_acomp_show.rename(columns={'UF_CRM_34_CONGELADO': 'Congelado'})

    # Calcular métricas por família a partir do SPA
    df_acomp_show['Concluídas/Total'] = ''
    df_acomp_show['Percentual'] = 0.0
    if not df_cartorio.empty and 'ID da Família' in df_acomp_show.columns and col_id_familia_spa in df_cartorio.columns:
        df_spa_base = df_cartorio[[col_id_familia_spa, 'STAGE_ID', 'STAGE_NAME']].copy()
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
        fam_metrics[col_id_familia_spa] = fam_metrics[col_id_familia_spa].astype(str).str.strip()
        df_acomp_show['ID da Família'] = df_acomp_show['ID da Família'].astype(str).str.strip()
        df_acomp_show = pd.merge(
            df_acomp_show,
            fam_metrics,
            left_on='ID da Família',
            right_on=col_id_familia_spa,
            how='left'
        )
        for c in ['total_itens', 'concluidas']:
            if c in df_acomp_show.columns:
                df_acomp_show[c] = pd.to_numeric(df_acomp_show[c], errors='coerce').fillna(0).astype(int)
        if 'total_itens' in df_acomp_show.columns and 'concluidas' in df_acomp_show.columns:
            df_acomp_show['Percentual'] = df_acomp_show.apply(
                lambda r: (r['concluidas'] / r['total_itens'] * 100) if r['total_itens'] > 0 else 0.0,
                axis=1
            )
            df_acomp_show['Concluídas/Total'] = df_acomp_show.apply(
                lambda r: f"{int(r['concluidas'])}/{int(r['total_itens'])}", axis=1
            )
            # Colunas auxiliares: barra de progresso (Progresso) e rótulo colorido para 100%
            df_acomp_show['Progresso'] = df_acomp_show['Percentual']
            df_acomp_show['Percentual'] = df_acomp_show['Percentual'].apply(lambda v: '🟢 100%' if v >= 100 else f"{v:.1f}%")
        if col_id_familia_spa in df_acomp_show.columns:
            df_acomp_show.drop(columns=[col_id_familia_spa], inplace=True, errors='ignore')

    cols_final = [c for c in ['Nome da Família', 'ID da Família', 'Congelado', 'Progresso', responsavel_col_name, 'Concluídas/Total', 'Percentual'] if c in df_acomp_show.columns]
    st.dataframe(
        ensure_pandas_df(df_acomp_show[cols_final]),
        hide_index=True,
        use_container_width=True,
        column_config={
            'Nome da Família': st.column_config.TextColumn('Nome da Família', width='large'),
            'ID da Família': st.column_config.TextColumn('ID da Família', width='medium'),
            'Congelado': st.column_config.TextColumn('Congelado', width='small'),
            'Progresso': st.column_config.ProgressColumn('Progresso', format='%.1f%%', min_value=0, max_value=100),
            'Concluídas/Total': st.column_config.TextColumn('Concluídas/Total', width='small'),
            'Percentual': st.column_config.TextColumn('Percentual', width='small'),
            responsavel_col_name: st.column_config.TextColumn('Responsável', width='medium')
        }
    )

    # ============================
    
    # ============================
    # Relatório Comune (Planilha)
    # ============================
    st.markdown("---")
    st.markdown("#### Comune – Prioridade ITALIANO")

    with st.spinner("Carregando planilha do Comune..."):
        df_comune_prior = _carregar_comune_prioritario_df()

    if df_comune_prior.empty:
        st.info("Nenhum registro marcado com Prioridade ITALIANO na planilha do Comune.")
        return

    st.dataframe(
        ensure_pandas_df(df_comune_prior),
        hide_index=True,
        use_container_width=True,
    )

 
def _carregar_comune_prioritario_df() -> pd.DataFrame:
    """Carrega a planilha do Comune, filtra por 'Prioridade ITALIANO' marcada
    e retorna dataframe com colunas: Nome da família, ID FAMILIA, STATUS comune.

    A função tenta detectar nomes de colunas equivalentes de forma resiliente.
    """
    try:
        # 1) Tentar carregar do Google Sheets (Base Higienização)
        SHEET_NAME = 'Base Higienização'
        SHEET_URL = 'https://docs.google.com/spreadsheets/d/1pB3HTFsaHyqAt3bhxzWG3RjfAxAzl97ydGqT35uYb-w/edit?gid=0#gid=0'

        def _extract_sheet_id_from_url(url: str) -> str:
            try:
                import re
                m = re.search(r"/d/([a-zA-Z0-9\-_]+)", url)
                return m.group(1) if m else ''
            except Exception:
                return ''

        df_raw = pd.DataFrame()
        try:
            client = get_google_sheets_client()
            if client is not None:
                # Tentar leitura manual (evita erro de cabeçalho duplicado do get_all_records)
                sheet_title_ok = False
                values = None
                try:
                    # Preferir abrir pela URL completa
                    ss = client.open_by_url(SHEET_URL)
                    try:
                        ws_by_name = ss.worksheet(SHEET_NAME)
                        if ws_by_name is not None:
                            sheet_title_ok = True
                            values = ws_by_name.get_all_values()
                    except Exception:
                        ws0 = ss.get_worksheet_by_id(0)
                        if ws0 is not None and ws0.title.strip().lower() == SHEET_NAME.strip().lower():
                            sheet_title_ok = True
                            values = ws0.get_all_values()
                except Exception:
                    # Fallback: abrir por chave extraída (sem alterar ID)
                    try:
                        _sid = _extract_sheet_id_from_url(SHEET_URL)
                        if _sid:
                            ss = client.open_by_key(_sid)
                            try:
                                ws_by_name = ss.worksheet(SHEET_NAME)
                                if ws_by_name is not None:
                                    sheet_title_ok = True
                                    values = ws_by_name.get_all_values()
                            except Exception:
                                ws0 = ss.get_worksheet_by_id(0)
                                if ws0 is not None and ws0.title.strip().lower() == SHEET_NAME.strip().lower():
                                    sheet_title_ok = True
                                    values = ws0.get_all_values()
                    except Exception as e_open:
                        st.warning(f"Falha ao abrir planilha pelo ID/URL: {e_open}")
                if sheet_title_ok and values and len(values) > 0:
                    # Detectar dinamicamente a linha de cabeçalho
                    header_idx = 0
                    prioridade_literal = 'Prioridade ITALIANO'
                    for i, row in enumerate(values[:50]):  # varre até 50 primeiras linhas
                        # considera linha com pelo menos 2 colunas não vazias
                        non_empty = sum(1 for c in row if str(c).strip() != '')
                        if prioridade_literal in row or non_empty >= 2:
                            header_idx = i
                            break
                    header = values[header_idx]
                    rows = values[header_idx + 1:] if len(values) > header_idx + 1 else []
                    # Deduplicar cabeçalhos mantendo ordem
                    seen = {}
                    header_unique = []
                    for h in header:
                        key = h if h is not None else ''
                        key = key.strip()
                        if key in seen:
                            seen[key] += 1
                            header_unique.append(f"{key}.{seen[key]}")
                        else:
                            seen[key] = 0
                            header_unique.append(key)
                    try:
                        df_raw = pd.DataFrame(rows, columns=header_unique)
                    except Exception:
                        df_raw = pd.DataFrame(rows)
        except Exception:
            pass

        # Sem fallback para CSV local; se falhar, aborta claramente
        if df_raw is None or df_raw.empty:
            st.error("Não foi possível carregar dados da planilha (Sheets). Verifique permissões de acesso e o ID/URL fornecido.")
            return pd.DataFrame(columns=['Nome da família', 'ID FAMILIA', 'STATUS comune'])

        df = ensure_pandas_df(df_raw).copy()

        # Normalizar cabeçalhos: remover BOM e espaços extras para comparação literal
        if isinstance(df.columns, pd.Index):
            col_ren = {}
            for c in df.columns:
                try:
                    s = str(c)
                    if s.startswith('\ufeff'):
                        s = s.lstrip('\ufeff')
                    s = s.strip()
                    col_ren[c] = s
                except Exception:
                    col_ren[c] = c
            try:
                df.rename(columns=col_ren, inplace=True)
            except Exception:
                pass

        # Helper: converter letra de coluna (Excel) para índice 0-based
        def _col_letter_to_index(col_letters: str) -> int:
            s = str(col_letters or '').strip().upper()
            total = 0
            for ch in s:
                if 'A' <= ch <= 'Z':
                    total = total * 26 + (ord(ch) - ord('A') + 1)
            return max(0, total - 1)

        # Exigir nomes/índices conforme solicitado
        prioridade_col = 'Prioridade ITALIANO'
        prioridade_series = None
        if prioridade_col in df.columns:
            prioridade_series = df[prioridade_col]
        else:
            # Tentar cabeçalhos deduplicados (ex.: 'Prioridade ITALIANO.1')
            candidatos = [c for c in df.columns if str(c).strip().startswith(prioridade_col)]
            if candidatos:
                prioridade_series = df[candidatos[0]]
            else:
                # Fallback por posição (coluna I -> índice 8)
                try:
                    idx_i = _col_letter_to_index('I')
                    if df.shape[1] > idx_i:
                        prioridade_series = df.iloc[:, idx_i]
                    else:
                        st.warning("Coluna 'Prioridade ITALIANO' não encontrada na planilha do Comune.")
                        return pd.DataFrame(columns=['Nome da família', 'ID FAMILIA', 'STATUS comune'])
                except Exception:
                    st.warning("Coluna 'Prioridade ITALIANO' não encontrada na planilha do Comune.")
                    return pd.DataFrame(columns=['Nome da família', 'ID FAMILIA', 'STATUS comune'])
        
        # STATUS comune preferindo posição AO
        status_col = None
        try:
            idx_ao = _col_letter_to_index('AO')
            if df.shape[1] > idx_ao:
                status_col = df.columns[idx_ao]
        except Exception:
            pass
        if not status_col:
            status_col = 'STATUS comune' if 'STATUS comune' in df.columns else ('Etapa' if 'Etapa' in df.columns else None)

        # Nome da família preferindo posição H
        nome_familia_col = None
        try:
            idx_h = _col_letter_to_index('H')
            if df.shape[1] > idx_h:
                nome_familia_col = df.columns[idx_h]
        except Exception:
            pass
        if not nome_familia_col:
            nome_familia_col = 'Nome da família' if 'Nome da família' in df.columns else (
                'Família' if 'Família' in df.columns else ('Familia' if 'Familia' in df.columns else ('Nome' if 'Nome' in df.columns else None))
            )
        id_familia_col = 'ID FAMILIA' if 'ID FAMILIA' in df.columns else (
            'Id Familia App' if 'Id Familia App' in df.columns else (
                'Id Família App' if 'Id Família App' in df.columns else ('ID da Família' if 'ID da Família' in df.columns else None)
            )
        )

        # Função para interpretar marcação
        TRUE_VALUES = {'1', 'true', 'sim', 'yes', 'y', 'x', 'marcado', 'checked', 'on'}

        def norm_text(s: str) -> str:
            s = str(s or '').strip().lower()
            try:
                s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
            except Exception:
                pass
            s = s.replace('\n', ' ').replace('\r', ' ')
            s = ' '.join(s.split())
            return s

        def is_marked(v) -> bool:
            if pd.isna(v):
                return False
            if isinstance(v, bool):
                return v is True
            # Numérico: somente 1 é verdadeiro
            if isinstance(v, (int, float)):
                try:
                    return int(v) == 1
                except Exception:
                    return False
            s = norm_text(str(v))
            return s in TRUE_VALUES

        try:
            mask_prior = prioridade_series.astype(str).str.strip().str.lower().isin({'sim','true','1','x','checked','on','✓','check'})
        except Exception:
            try:
                mask_prior = prioridade_series.apply(is_marked)
            except Exception:
                mask_prior = prioridade_series.astype(str).apply(is_marked)

        # Diagnóstico removido
        try:
            _ = mask_prior
        except Exception:
            pass

        df_filtrado = df[mask_prior].copy()
        if df_filtrado.empty:
            return pd.DataFrame(columns=['Nome da família', 'ID FAMILIA', 'STATUS comune'])

        # Montar resultado com renomeação amigável
        resultado_cols = {}
        if nome_familia_col:
            resultado_cols['Nome da família'] = df_filtrado[nome_familia_col].astype(str)
        else:
            resultado_cols['Nome da família'] = ''

        if id_familia_col:
            resultado_cols['ID FAMILIA'] = df_filtrado[id_familia_col].astype(str)
        else:
            resultado_cols['ID FAMILIA'] = ''

        if status_col and status_col in df_filtrado.columns:
            resultado_cols['STATUS comune'] = df_filtrado[status_col].astype(str)
        else:
            resultado_cols['STATUS comune'] = ''

        df_out = pd.DataFrame(resultado_cols)
        if 'Nome da família' in df_out.columns:
            df_out = df_out.sort_values(by=['Nome da família'], kind='stable')

        # Destacar em verde o status "PDF DO DOC ENTREGUE"
        try:
            if 'STATUS comune' in df_out.columns:
                def _highlight_status(val):
                    s = str(val or '').strip()
                    # normalizar (sem acento, minúsculo) para checagem robusta
                    try:
                        import unicodedata
                        sn = ''.join(c for c in unicodedata.normalize('NFKD', s).lower() if not unicodedata.combining(c))
                    except Exception:
                        sn = s.lower()
                    if 'pdf' in sn and 'entregue' in sn:
                        return f"🟢 {s}"
                    return s
                df_out['STATUS comune'] = df_out['STATUS comune'].apply(_highlight_status)
        except Exception:
            pass
        return df_out

    except Exception as e:
        st.error(f"Erro ao carregar/filtrar planilha do Comune: {e}")
        return pd.DataFrame(columns=['Nome da família', 'ID FAMILIA', 'STATUS comune'])
