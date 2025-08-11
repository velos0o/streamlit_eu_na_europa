import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np
from datetime import timedelta, datetime

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
    
    # Se não houver partes (dias, horas, minutos), significa que é 0s.
    # A lógica acima já trata durações de 1s a 59s.
    return " ".join(parts) if parts else "0s"

def show_scaner():
    """
    Exibe a página Scaner, conectando-se a uma SPA específica do Bitrix24.
    """
    # --- Carregar CSS Compilado ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")
        
    st.markdown('<h1 class="bi-title">Scaner de Documentos</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="cartorio-container cartorio-container--info">', unsafe_allow_html=True)

    # Obter credenciais e construir a URL da API para a SPA
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    if not BITRIX_TOKEN or not BITRIX_URL:
        st.error("Credenciais do Bitrix24 não configuradas. Verifique o `secrets.toml` ou as variáveis de ambiente.")
        st.stop()

    # ID da SPA "SCANER" é 1132. No biconnector, isso se traduz no nome da tabela.
    ENTITY_TYPE_ID = 1132
    table_name = f"crm_dynamic_items_{ENTITY_TYPE_ID}"
    
    # URL para acessar a tabela da SPA via biconnector, seguindo o padrão do cartorio_new
    url_spa = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table={table_name}"

    # Carregar os dados da SPA
    with st.spinner(f"Carregando dados da tabela '{table_name}'..."):
        df_scaner_full = load_bitrix_data(url_spa, show_logs=False)
        df_usuarios = carregar_dados_usuarios_bitrix()

    if not df_scaner_full.empty:
        # --- Nomes das colunas (ASSUMIDOS) ---
        TIMESTAMP_COL = 'CREATED_TIME'
        FAMILY_ID_COL = 'UF_CRM_48_ID_FAMILIA'
        USER_ID_COL = 'UF_CRM_48_ID_USUARIO'
        TITLE_COL = 'TITLE'

        # --- Excluir usuário "Lucas Veloso" (ID 10) ANTES de todos os cálculos ---
        df_scaner = df_scaner_full[df_scaner_full[USER_ID_COL] != '10'].copy()
        
        # --- Mapeamento de Usuários ---
        mapa_usuarios = {}
        if not df_usuarios.empty:
            df_usuarios['ID'] = df_usuarios['ID'].astype(str)
            mapa_usuarios = pd.Series(df_usuarios.FULL_NAME.values, index=df_usuarios.ID).to_dict()

        # Verificação de colunas
        cols_necessarias = [TIMESTAMP_COL, FAMILY_ID_COL, USER_ID_COL]
        cols_faltantes = [col for col in cols_necessarias if col not in df_scaner.columns]

        if cols_faltantes:
            st.error(f"As seguintes colunas necessárias não foram encontradas no DataFrame: {', '.join(cols_faltantes)}")
            st.info("Colunas disponíveis: " + ", ".join(df_scaner.columns))
            st.stop()

        # --- Preparação dos Dados ---
        df_scaner[TIMESTAMP_COL] = pd.to_datetime(df_scaner[TIMESTAMP_COL], errors='coerce')
        df_scaner.dropna(subset=[TIMESTAMP_COL], inplace=True)
        df_scaner.sort_values(by=TIMESTAMP_COL, inplace=True)
        
        # --- FILTROS ---
        with st.expander("Filtros", expanded=True):
            # Obter lista de usuários e famílias para os filtros
            usuarios_disponiveis = sorted(df_scaner[USER_ID_COL].map(mapa_usuarios).dropna().unique())
            
            # Linha 1: Filtros de Usuário e Família
            col1, col2 = st.columns(2)
            with col1:
                filtro_usuario = st.selectbox("Filtrar por usuário", ["Todos"] + usuarios_disponiveis)
            with col2:
                filtro_familia = st.text_input("Filtrar por ID da família")

            # Linha 2: Filtro de Data (range)
            min_date = df_scaner[TIMESTAMP_COL].min().date()
            max_date = df_scaner[TIMESTAMP_COL].max().date()
            
            col_check, col_start, col_end = st.columns([1, 2, 2])
            with col_check:
                st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True) # Espaçador para alinhar
                aplicar_filtro_data = st.checkbox("Filtrar por data", value=False) # Padrão: sem filtro
            with col_start:
                filtro_data_inicio = st.date_input("Data inicial", value=min_date, min_value=min_date, max_value=max_date, disabled=not aplicar_filtro_data)
            with col_end:
                filtro_data_fim = st.date_input("Data final", value=max_date, min_value=min_date, max_value=max_date, disabled=not aplicar_filtro_data)

        # Aplicar filtros
        df_filtrado = df_scaner.copy()

        if aplicar_filtro_data:
            if filtro_data_inicio > filtro_data_fim:
                st.error("A data inicial não pode ser posterior à data final.")
                st.stop()
            else:
                df_filtrado = df_filtrado[(df_filtrado[TIMESTAMP_COL].dt.date >= filtro_data_inicio) & (df_filtrado[TIMESTAMP_COL].dt.date <= filtro_data_fim)]

        if filtro_usuario != "Todos":
            # Inverter o mapa para encontrar o ID pelo nome
            mapa_nomes_inverso = {v: k for k, v in mapa_usuarios.items()}
            id_usuario_filtrado = mapa_nomes_inverso.get(filtro_usuario)
            if id_usuario_filtrado:
                df_filtrado = df_filtrado[df_filtrado[USER_ID_COL] == id_usuario_filtrado]
        if filtro_familia:
            df_filtrado = df_filtrado[df_filtrado[FAMILY_ID_COL].str.contains(filtro_familia, na=False)]

        st.success(f"{len(df_filtrado)} registros encontrados para os filtros aplicados.")

        # --- Metas ---
        META_DIARIA_TOTAL = 1680
        META_DIARIA_POR_PESSOA = 336
        
        # A lógica de metas só é aplicada se o filtro de data estiver ativo
        if aplicar_filtro_data:
            # Contar apenas dias úteis (segunda a sexta)
            num_dias = len(pd.bdate_range(start=filtro_data_inicio, end=filtro_data_fim))
            
            # Se não houver dias úteis no período, a meta é 0
            if num_dias == 0:
                st.info("O período selecionado não contém dias úteis. As metas não são aplicáveis.")
                meta_total_periodo = 0
                meta_pessoa_periodo = 0
            else:
                meta_total_periodo = META_DIARIA_TOTAL * num_dias
                meta_pessoa_periodo = META_DIARIA_POR_PESSOA * num_dias
            
            total_envios_periodo = len(df_filtrado)
            
            if meta_total_periodo > 0 and total_envios_periodo >= meta_total_periodo:
                st.balloons()
                st.success(f"Parabéns! A meta para o período de {num_dias} dia(s) útil(eis) de {meta_total_periodo} envios foi atingida!")

        # --- Métricas Macro ---
        st.subheader("Métricas Gerais")
        total_envios = len(df_filtrado)
        total_familias = df_filtrado[FAMILY_ID_COL].nunique()
        
        tempo_medio_cards = df_filtrado[TIMESTAMP_COL].diff().mean()
        primeiro_envio_familia = df_filtrado.groupby(FAMILY_ID_COL)[TIMESTAMP_COL].min().sort_values()
        tempo_medio_familias = primeiro_envio_familia.diff().mean()

        st.markdown('<div class="producao-comune-metricas producao-comune-metricas--neutral">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Envios (Filtrado)", f"{total_envios}")
        col2.metric("Total de Famílias (Filtrado)", f"{total_familias}")
        col3.metric("Tempo Médio por Card", format_timedelta(tempo_medio_cards))
        col4.metric("Tempo Médio por Família", format_timedelta(tempo_medio_familias))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # --- Tabela por Usuário ---
        st.subheader("Desempenho por Usuário")
        
        if not df_filtrado.empty:
            total_enviado_por_usuario = df_filtrado.groupby(USER_ID_COL).size().reset_index(name='Total Enviado')
            df_filtrado['time_diff'] = df_filtrado.groupby(USER_ID_COL)[TIMESTAMP_COL].diff()
            tempo_medio_por_usuario = df_filtrado.groupby(USER_ID_COL)['time_diff'].mean().reset_index(name='Tempo Médio de Envio')

            df_desempenho = pd.merge(total_enviado_por_usuario, tempo_medio_por_usuario, on=USER_ID_COL, how='left')
            df_desempenho[USER_ID_COL] = df_desempenho[USER_ID_COL].astype(str).map(mapa_usuarios).fillna(df_desempenho[USER_ID_COL])
            df_desempenho.rename(columns={USER_ID_COL: 'Responsável'}, inplace=True)
            
            # Adicionar meta e progresso apenas se o filtro de data estiver ativo
            colunas_tabela = ['Responsável', 'Total Enviado', 'Tempo Médio de Envio']
            if aplicar_filtro_data:
                df_desempenho['Progresso'] = df_desempenho.apply(lambda row: f"{row['Total Enviado']} / {meta_pessoa_periodo}", axis=1)
                colunas_tabela = ['Responsável', 'Total Enviado', 'Progresso', 'Tempo Médio de Envio']

            df_desempenho['Tempo Médio de Envio'] = df_desempenho['Tempo Médio de Envio'].apply(format_timedelta)
            
            st.markdown('<div class="scaner-table">', unsafe_allow_html=True)
            st.dataframe(df_desempenho[colunas_tabela], use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhum dado de desempenho para exibir com os filtros atuais.")

        # --- Tabela de Todos os Cards Enviados ---
        st.markdown("---")
        st.subheader("Todos os Cards Enviados (Filtrado)")
        if not df_filtrado.empty:
            df_detalhes = df_filtrado[[TITLE_COL, FAMILY_ID_COL, USER_ID_COL, TIMESTAMP_COL]].copy()
            df_detalhes[USER_ID_COL] = df_detalhes[USER_ID_COL].astype(str).map(mapa_usuarios).fillna(df_detalhes[USER_ID_COL])
            df_detalhes.rename(columns={
                TITLE_COL: 'Título',
                FAMILY_ID_COL: 'ID da Família',
                USER_ID_COL: 'Responsável',
                TIMESTAMP_COL: 'Data de Envio'
            }, inplace=True)
            st.dataframe(df_detalhes, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum card para exibir com os filtros atuais.")

    else:
        st.warning("Nenhum dado encontrado na SPA 'SCANER' ou ocorreu um erro durante o carregamento.")
        
    st.markdown('</div>', unsafe_allow_html=True)
