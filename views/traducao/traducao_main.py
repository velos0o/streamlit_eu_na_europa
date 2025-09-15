import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np
from datetime import timedelta, datetime
import re

# Adicionar o caminho raiz do projeto ao sys.path
# Isso permite que o módulo 'api' seja encontrado
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

from api.bitrix_connector import load_bitrix_data, get_credentials
from views.cartorio_new.utils import carregar_dados_usuarios_bitrix

def format_timedelta(td):
    """Formata um objeto timedelta em uma string legível."""
    if pd.isna(td):
        return "N/A"
    
    total_seconds = td.total_seconds()
    
    # Se for menos de 1 minuto, formatar com decimais
    if total_seconds < 60:
        return f"{total_seconds:.2f}s".replace('.', ',')

    days, remainder = divmod(int(total_seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "0s"

def show_traducao():
    """
    Exibe a página de Tradução, conectando-se a uma SPA específica do Bitrix24.
    """
    # --- Carregar CSS Compilado ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")
        
    st.markdown('<h1 class="bi-title">Tradução de Documentos</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="cartorio-container cartorio-container--info">', unsafe_allow_html=True)

    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    if not BITRIX_TOKEN or not BITRIX_URL:
        st.error("Credenciais do Bitrix24 não configuradas.")
        st.stop()

    ENTITY_TYPE_ID = 1136
    table_name = f"crm_dynamic_items_{ENTITY_TYPE_ID}"
    
    url_spa = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table={table_name}"

    with st.spinner(f"Carregando dados da tabela '{table_name}'..."):
        df_traducao_full = load_bitrix_data(url_spa, show_logs=False)
        df_usuarios = carregar_dados_usuarios_bitrix()

    if not df_traducao_full.empty:
        TIMESTAMP_COL = 'CREATED_TIME'
        TITLE_COL = 'TITLE'
        FAMILY_ID_COL = 'UF_CRM_50_ID_FAMILIA'
        USER_ID_COL = 'ASSIGNED_BY_ID'
        ENVIADO_ASSINATURA_COL = 'UF_CRM_ENVIADO_ASSINATURA'
        DEVOLVIDO_NUM_COL = 'UF_CRM_DEVOLVIDO_NUM'
        DATA_EM_ANDAMENTO_COL = 'UF_CRM_DATA_EM_ANDAMENTO'
        DATA_DEVOLUCAO_COL = 'UF_CRM_DATA_DEVOLUCAO'
        USER_TRADUTOR_COL = 'UF_CRM_50_USER_TRADUTOR'
        USER_REVISOR_COL = 'UF_CRM_50_USER_REVISOR'
        PRINT_ERROS_COL = 'UF_CRM_50_PRINT_ERROS'
        OBSERVACAO_ERRO_COL = 'UF_CRM_50_OBSERVACAO_DO_ERRO'
        ID_REQUERENTE_COL = 'UF_CRM_50_ID_REQUERENTE'
        DOC_TRADUZIDO_COL = 'UF_CRM_50_DOCUMENTO_TRADUZIDO'
        DOC_SCANEADO_COL = 'UF_CRM_50_DOCUMENTO_SCANEADO'
        DATA_REVISAO_TRADUCAO_COL = 'UF_CRM_50_DATA_REVISAO_TRADUCAO'
        DATA_CONCLUSAO_TRADUCAO_COL = 'UF_CRM_50_DATA_CONCLUSAO_TRADUCAO'
        ENVIAR_FAMILIA_ASSINATURA_COL = 'UF_CRM_50_1755540132711'
        AVALIACAO_TRADUCAO_COL = 'UF_CRM_50_1755539995076'
        STAGE_ID_COL = 'STAGE_ID'
        CATEGORY_ID_COL = 'CATEGORY_ID'

        # IDs dos Estágios
        STAGE_PRODUZIDO = 'DT1136_130:UC_8OTF6D'
        STAGE_PENDENTE = 'DT1136_130:NEW'
        STAGE_DEVOLVIDO = 'DT1136_130:UC_ZUUSW4'

        df_traducao = df_traducao_full[df_traducao_full[USER_ID_COL] != '10'].copy()

        # Filtrar somente o funil (pipeline) CATEGORY_ID = 130
        if CATEGORY_ID_COL in df_traducao.columns:
            df_traducao[CATEGORY_ID_COL] = pd.to_numeric(df_traducao[CATEGORY_ID_COL], errors='coerce')
            df_traducao = df_traducao[df_traducao[CATEGORY_ID_COL] == 130].copy()
        elif STAGE_ID_COL in df_traducao.columns:
            # Fallback: usar prefixo do STAGE_ID que indica o pipeline 130
            df_traducao = df_traducao[df_traducao[STAGE_ID_COL].astype(str).str.startswith('DT1136_130:')].copy()
        else:
            st.warning("Não foi possível aplicar o filtro de CATEGORY_ID=130 (colunas ausentes).")
        
        mapa_usuarios = {}
        if not df_usuarios.empty:
            df_usuarios['ID'] = df_usuarios['ID'].astype(str)
            mapa_usuarios = pd.Series(df_usuarios.FULL_NAME.values, index=df_usuarios.ID).to_dict()

        cols_necessarias = [TIMESTAMP_COL, FAMILY_ID_COL, USER_ID_COL]
        cols_faltantes = [col for col in cols_necessarias if col not in df_traducao.columns]

        if cols_faltantes:
            st.error(f"Colunas necessárias não encontradas: {', '.join(cols_faltantes)}")
            st.info("Colunas disponíveis: " + ", ".join(df_traducao.columns))
            st.stop()

        df_traducao[TIMESTAMP_COL] = pd.to_datetime(df_traducao[TIMESTAMP_COL], errors='coerce') - pd.Timedelta(hours=6)
        df_traducao.dropna(subset=[TIMESTAMP_COL], inplace=True)
        df_traducao.sort_values(by=TIMESTAMP_COL, inplace=True)

        # --- FILTRO DE ESTÁGIOS PERMITIDOS (descartar qualquer outro) ---
        estagios_em_andamento = {'DT1136_130:PREPARATION'}
        estagios_concluidos = {'DT1136_130:SUCCESS', 'DT1136_130:UC_8OTF6D'}
        estagios_permitidos = estagios_em_andamento.union(estagios_concluidos).union({'DT1136_130:NEW', 'DT1136_130:UC_ZUUSW4'})
        if STAGE_ID_COL in df_traducao.columns:
            df_traducao = df_traducao[df_traducao[STAGE_ID_COL].astype(str).isin(estagios_permitidos)].copy()
        
        # --- PREPARAÇÃO DE DADOS PARA FILTROS ---
        # Converter colunas de data para datetime
        for col in [DATA_REVISAO_TRADUCAO_COL, DATA_DEVOLUCAO_COL, DATA_CONCLUSAO_TRADUCAO_COL]:
            if col in df_traducao.columns:
                df_traducao[col] = pd.to_datetime(df_traducao[col], errors='coerce')

        # Obter listas de nomes diretamente das colunas
        tradutores_disponiveis = sorted(df_traducao[USER_TRADUTOR_COL].dropna().unique())
        revisores_disponiveis = sorted(df_traducao[USER_REVISOR_COL].dropna().unique())

        # --- NOVOS FILTROS ---
        with st.expander("Filtros", expanded=True):
            # Linha 1: Filtros de Usuário
            col1, col2 = st.columns(2)
            with col1:
                filtros_tradutores = st.multiselect("Filtrar por Tradutor", tradutores_disponiveis)
            with col2:
                filtros_revisores = st.multiselect("Filtrar por Revisor", revisores_disponiveis)

            # Linha 2: Filtros de Texto
            col3, col4 = st.columns(2)
            with col3:
                filtro_titulo = st.text_input("Filtrar por Título do Documento")
            with col4:
                filtro_familia = st.text_input("Filtrar por ID da Família")

            # Linha 3: Filtros por Período de Data
            st.markdown("##### Filtros por Período")
            col5, col6, col7 = st.columns(3)

            # Filtro para Produzidos
            with col5:
                st.markdown("**Produzidos**")
                filtrar_produzidos_range = st.checkbox("Filtrar período", key='check_prod')
                prod_data_inicio = st.date_input("Data inicial", key='prod_start', disabled=not filtrar_produzidos_range, value=datetime.today())
                prod_data_fim = st.date_input("Data final", key='prod_end', disabled=not filtrar_produzidos_range, value=datetime.today())

            # Filtro para Devolvidos
            with col6:
                st.markdown("**Devolvidos**")
                filtrar_devolvidos_range = st.checkbox("Filtrar período", key='check_dev')
                dev_data_inicio = st.date_input("Data inicial", key='dev_start', disabled=not filtrar_devolvidos_range, value=datetime.today())
                dev_data_fim = st.date_input("Data final", key='dev_end', disabled=not filtrar_devolvidos_range, value=datetime.today())

            # Filtro para Concluídos
            with col7:
                st.markdown("**Concluídos**")
                filtrar_concluidos_range = st.checkbox("Filtrar período", key='check_conc')
                conc_data_inicio = st.date_input("Data inicial", key='conc_start', disabled=not filtrar_concluidos_range, value=datetime.today())
                conc_data_fim = st.date_input("Data final", key='conc_end', disabled=not filtrar_concluidos_range, value=datetime.today())

        # --- APLICAÇÃO DOS FILTROS ---
        df_filtrado = df_traducao.copy()

        # Filtros de usuário (agora filtrando diretamente por nome e com seleção múltipla)
        if filtros_tradutores:
            df_filtrado = df_filtrado[df_filtrado[USER_TRADUTOR_COL].isin(filtros_tradutores)]
        
        if filtros_revisores:
            df_filtrado = df_filtrado[df_filtrado[USER_REVISOR_COL].isin(filtros_revisores)]

        # Filtros de texto
        if filtro_titulo:
            df_filtrado = df_filtrado[df_filtrado[TITLE_COL].str.contains(filtro_titulo, na=False, case=False)]
        if filtro_familia:
            df_filtrado = df_filtrado[df_filtrado[FAMILY_ID_COL].str.contains(filtro_familia, na=False)]

        # Filtros por período de data
        if filtrar_produzidos_range:
            if prod_data_inicio > prod_data_fim:
                st.error("A data inicial de 'Produzidos' não pode ser posterior à data final.")
            else:
                df_filtrado = df_filtrado[df_filtrado[DATA_REVISAO_TRADUCAO_COL].dt.normalize().between(pd.to_datetime(prod_data_inicio), pd.to_datetime(prod_data_fim))]
        
        if filtrar_devolvidos_range:
            if dev_data_inicio > dev_data_fim:
                st.error("A data inicial de 'Devolvidos' não pode ser posterior à data final.")
            else:
                df_filtrado = df_filtrado[df_filtrado[DATA_DEVOLUCAO_COL].dt.normalize().between(pd.to_datetime(dev_data_inicio), pd.to_datetime(dev_data_fim))]

        if filtrar_concluidos_range:
            if conc_data_inicio > conc_data_fim:
                st.error("A data inicial de 'Concluídos' não pode ser posterior à data final.")
            else:
                df_filtrado = df_filtrado[df_filtrado[DATA_CONCLUSAO_TRADUCAO_COL].dt.normalize().between(pd.to_datetime(conc_data_inicio), pd.to_datetime(conc_data_fim))]

        st.success(f"{len(df_filtrado)} registros encontrados.")
        
        # --- CÁLCULO CENTRALIZADO DE MÉTRICAS ---
        
        # Métricas Gerais
        df_filtrado[DATA_EM_ANDAMENTO_COL] = pd.to_datetime(df_filtrado[DATA_EM_ANDAMENTO_COL], errors='coerce')
        df_filtrado[DATA_REVISAO_TRADUCAO_COL] = pd.to_datetime(df_filtrado[DATA_REVISAO_TRADUCAO_COL], errors='coerce') # Usar data de revisão

        # Registros válidos para produção: evitar casos onde EM_ANDAMENTO > REVISAO (duração negativa)
        ordem_valida_producao_mask = (
            df_filtrado[DATA_EM_ANDAMENTO_COL].isna()
        ) | (
            df_filtrado[DATA_REVISAO_TRADUCAO_COL].isna()
        ) | (
            df_filtrado[DATA_EM_ANDAMENTO_COL] <= df_filtrado[DATA_REVISAO_TRADUCAO_COL]
        )

        # Tempo de tradução somente quando a ordem das datas é válida
        df_filtrado['tempo_traducao_conclusao'] = (
            df_filtrado[DATA_REVISAO_TRADUCAO_COL] - df_filtrado[DATA_EM_ANDAMENTO_COL]
        ).where(ordem_valida_producao_mask)
        tempo_medio_geral = df_filtrado['tempo_traducao_conclusao'].mean()

        # Contagem de produzidos: SUCCESS e UC_8OTF6D, respeitando ordem válida de datas
        if STAGE_ID_COL in df_filtrado.columns:
            mask_concluidos_estagio = df_filtrado[STAGE_ID_COL].astype(str).isin(['DT1136_130:SUCCESS', 'DT1136_130:UC_8OTF6D'])
        else:
            mask_concluidos_estagio = pd.Series([False] * len(df_filtrado), index=df_filtrado.index)
        df_filtrado['conta_produzido'] = (
            mask_concluidos_estagio & ordem_valida_producao_mask
        ).astype(int)
        docs_produzidos_geral = int(df_filtrado['conta_produzido'].sum())
        # Pendentes são NEW e UC_ZUUSW4
        if STAGE_ID_COL in df_filtrado.columns:
            mask_pendentes_estagio = df_filtrado[STAGE_ID_COL].astype(str).isin(['DT1136_130:NEW', 'DT1136_130:UC_ZUUSW4'])
            docs_pendentes_geral = int(mask_pendentes_estagio.sum())
        else:
            docs_pendentes_geral = df_filtrado[df_filtrado[STAGE_ID_COL] == STAGE_PENDENTE].shape[0]
        docs_devolvidos_geral = df_filtrado[df_filtrado[STAGE_ID_COL] == STAGE_DEVOLVIDO].shape[0]

        # Métricas de Desempenho por Tradutor
        df_tradutores = pd.DataFrame() # Inicializa vazio
        if not df_filtrado.empty and USER_TRADUTOR_COL in df_filtrado.columns:
            # Em andamento: apenas STAGE_ID PREPARATION (sem regra de datas)
            if STAGE_ID_COL in df_filtrado.columns:
                df_filtrado['em_andamento'] = df_filtrado[STAGE_ID_COL].astype(str).isin(['DT1136_130:PREPARATION'])
            else:
                df_filtrado['em_andamento'] = False
            df_tradutores = df_filtrado.groupby(USER_TRADUTOR_COL).agg(
                docs_pendentes=(STAGE_ID_COL, lambda x: x.astype(str).isin(['DT1136_130:NEW', 'DT1136_130:UC_ZUUSW4']).sum()),
                docs_em_andamento=('em_andamento', 'sum'),
                docs_produzidos=('conta_produzido', 'sum'),
                tempo_medio_conclusao=('tempo_traducao_conclusao', 'mean')
            ).reset_index()
            df_tradutores.rename(columns={
                USER_TRADUTOR_COL: 'Tradutor',
                'docs_pendentes': 'Documentos Pendentes',
                'docs_em_andamento': 'Documentos em Andamento',
                'docs_produzidos': 'Documentos Produzidos',
                'tempo_medio_conclusao': 'Tempo Médio de Tradução'
            }, inplace=True)
            df_tradutores['Tempo Médio de Tradução'] = df_tradutores['Tempo Médio de Tradução'].apply(format_timedelta)

        # --- EXIBIÇÃO DAS MÉTRICAS ---
        
        st.subheader("Métricas Gerais")
        st.markdown("""
        <style>
            .metric-card {
                background-color: #F8F9FA;
                border: 2px solid #007BFF;
                border-radius: .25rem;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,.075);
                display: flex;
                align-items: center;
            }
            .metric-card .icon {
                font-size: 3rem;
                margin-right: 1.5rem;
                color: #007BFF;
            }
            .metric-card .metric-content {
                flex-grow: 1;
            }
            .metric-card .metric-value {
                font-size: 2rem;
                font-weight: 700;
                margin: 0;
            }
            .metric-card .metric-label {
                font-size: 1rem;
                margin: 0;
                color: #6C757D;
            }
            /* Cores alternativas */
            .metric-card.orange { border-color: #FD7E14; }
            .metric-card.orange .icon { color: #FD7E14; }
            .metric-card.red { border-color: #DC3545; }
            .metric-card.red .icon { color: #DC3545; }
            .metric-card.blue { border-color: #17A2B8; }
            .metric-card.blue .icon { color: #17A2B8; }
        </style>
        """, unsafe_allow_html=True)
        
        # Carregar a fonte dos ícones (Bootstrap Icons)
        st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">', unsafe_allow_html=True)
        
        # Layout em colunas para os cards
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="icon"><i class="bi bi-check-circle-fill"></i></div>
                <div class="metric-content">
                    <p class="metric-value">{docs_produzidos_geral}</p>
                    <p class="metric-label">Documentos Produzidos</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-card red">
                <div class="icon"><i class="bi bi-arrow-counterclockwise"></i></div>
                <div class="metric-content">
                    <p class="metric-value">{docs_devolvidos_geral}</p>
                    <p class="metric-label">Documentos Devolvidos</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card orange">
                <div class="icon"><i class="bi bi-pause-circle-fill"></i></div>
                <div class="metric-content">
                    <p class="metric-value">{docs_pendentes_geral}</p>
                    <p class="metric-label">Documentos Pendentes</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-card blue">
                <div class="icon"><i class="bi bi-clock-history"></i></div>
                <div class="metric-content">
                    <p class="metric-value">{format_timedelta(tempo_medio_geral)}</p>
                    <p class="metric-label">Tempo Médio de Tradução</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.subheader("Desempenho por Tradutor")
        
        if not df_tradutores.empty:
            # Reordenar colunas para a exibição final
            colunas_finais = ['Tradutor', 'Documentos Pendentes', 'Documentos em Andamento', 'Documentos Produzidos', 'Tempo Médio de Tradução']
            st.dataframe(df_tradutores[colunas_finais], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado de tradutor para exibir.")
        
        st.subheader("Desempenho por Revisor")
        
        if not df_filtrado.empty and USER_REVISOR_COL in df_filtrado.columns:
            # Remover valores nulos da coluna de revisor antes de agrupar para evitar erros
            df_revisores_filtrado = df_filtrado.dropna(subset=[USER_REVISOR_COL])

            df_revisores = df_revisores_filtrado.groupby(USER_REVISOR_COL).agg(
                total_documentos=('TITLE', 'count')
            ).reset_index()

            df_revisores.rename(columns={
                USER_REVISOR_COL: 'Revisor',
                'total_documentos': 'Documentos Revisados'
            }, inplace=True)

            st.dataframe(df_revisores, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado de revisor para exibir.")

        st.markdown("---")
        st.subheader("Todos os Documentos")
        if not df_filtrado.empty:
            df_detalhes = df_filtrado[[
                TITLE_COL, FAMILY_ID_COL, USER_TRADUTOR_COL, 
                USER_REVISOR_COL, DATA_REVISAO_TRADUCAO_COL, AVALIACAO_TRADUCAO_COL
            ]].copy()

            df_detalhes.rename(columns={
                TITLE_COL: 'Título',
                FAMILY_ID_COL: 'ID Família',
                USER_TRADUTOR_COL: 'Tradutor',
                USER_REVISOR_COL: 'Revisor',
                DATA_REVISAO_TRADUCAO_COL: 'Data Revisão',
                AVALIACAO_TRADUCAO_COL: 'Avaliação'
            }, inplace=True)
            
            st.dataframe(df_detalhes, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum documento para exibir.")

    else:
        st.warning("Nenhum dado encontrado na SPA 'TRADUCAO'.")
        
    st.markdown('</div>', unsafe_allow_html=True)
