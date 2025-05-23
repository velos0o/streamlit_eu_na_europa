import streamlit as st
import pandas as pd
from datetime import datetime, time
import numpy as np
import os # Importar os para manipulação de caminhos

# Funções que podem ser úteis
from .utils import simplificar_nome_estagio, fetch_supabase_producao_data, carregar_dados_usuarios_bitrix

# Obter o diretório do arquivo atual
_PRODUCAO_ADM_DIR = os.path.dirname(os.path.abspath(__file__))
# Construir o caminho para a pasta assets subindo dois níveis (views/cartorio_new -> streamlit_eu_na_europa)
_ASSETS_DIR = os.path.join(_PRODUCAO_ADM_DIR, '..', '..', 'assets')
_CSS_PATH = os.path.join(_ASSETS_DIR, 'styles', 'css', 'main.css')

# Lista de IDs dos ADMs relevantes (como strings)
LISTA_IDS_ADMS_RELEVANTES = [
    "284", "66", "194", "614", "288", "344", 
    "106",  # Lucas Veloso
    "342", "186", "616", "148"
]
# Lista com o prefixo "user_" para facilitar a checagem com dados do Supabase
LISTA_IDS_ADMS_RELEVANTES_COM_PREFIXO = LISTA_IDS_ADMS_RELEVANTES + [f"user_{id_adm}" for id_adm in LISTA_IDS_ADMS_RELEVANTES]

# Estágios de devolução/pendência ADM monitorados
ESTAGIOS_DEVOLUCAO_ADM = [
    'DEVOLUÇÃO ADM', 
    'DEVOLVIDO REQUERIMENTO',
    'DEVOLUTIVA BUSCA - CRC',
    'APENAS ASS. REQ CLIENTE P/MONTAGEM'
]

def exibir_producao_adm(df_cartorio_original):
    st.markdown('<div class="cartorio-container cartorio-container--info">', unsafe_allow_html=True)
    st.title("Dashboard de Pendências ADM")
    
    # --- Carregar CSS Compilado ---
    try:
        # Usar o caminho absoluto calculado
        print(f"[Debug Produção ADM] Tentando carregar CSS de: {_CSS_PATH}")
        if os.path.exists(_CSS_PATH):
            with open(_CSS_PATH, 'r', encoding='utf-8') as f:
                css_content = f.read()
                print(f"[Debug Produção ADM] CSS carregado com sucesso. Tamanho: {len(css_content)} bytes.")
                
                # Injetar o CSS na página
                st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
        else:
            st.warning(f"Arquivo CSS principal não encontrado em: {_CSS_PATH}")
            print(f"[Debug Produção ADM] Falha ao carregar CSS: Arquivo não existe em {_CSS_PATH}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar o CSS em Produção ADM: {e}")
        print(f"[Debug Produção ADM] Erro detalhado: {str(e)}")
    
    # Remover CSS inline específico - usar apenas classes SCSS
    st.markdown("---")

    # --- Carregar Mapa de Usuários ---
    df_usuarios = carregar_dados_usuarios_bitrix()
    mapa_usuarios = {}
    if not df_usuarios.empty:
        df_usuarios['ID'] = df_usuarios['ID'].astype(str)
        mapa_usuarios = pd.Series(df_usuarios.FULL_NAME.values, index=df_usuarios.ID).to_dict()
        for user_id_str, full_name in list(mapa_usuarios.items()):
            mapa_usuarios[f"user_{user_id_str}"] = full_name
    else:
        st.warning("Mapeamento de nomes de usuário não disponível. Os IDs dos responsáveis podem ser exibidos.")

    if df_cartorio_original is None or df_cartorio_original.empty:
        st.warning("Dados de cartório não disponíveis para análise de produção ADM.")
        return

    df = df_cartorio_original.copy()

    # --- FILTRO INICIAL POR ADMS RELEVANTES ---
    col_adm_pasta_bitrix = 'UF_CRM_34_ADM_DE_PASTA'
    nomes_adms_relevantes_para_filtro_bitrix = []
    if col_adm_pasta_bitrix in df.columns:
        nomes_adms_relevantes_map = {id_adm: mapa_usuarios.get(id_adm, mapa_usuarios.get(f"user_{id_adm}", f"ID_DESCONHECIDO_{id_adm}")) for id_adm in LISTA_IDS_ADMS_RELEVANTES}
        nomes_adms_relevantes_para_filtro_bitrix = [name for name in nomes_adms_relevantes_map.values() if not name.startswith("ID_DESCONHECIDO")]
        
        df[col_adm_pasta_bitrix] = df[col_adm_pasta_bitrix].fillna("Desconhecido").astype(str)
        df_original_len = len(df)
        df = df[df[col_adm_pasta_bitrix].isin(nomes_adms_relevantes_para_filtro_bitrix)]
        if df.empty and nomes_adms_relevantes_para_filtro_bitrix:
            st.warning(f"Nenhum dado encontrado no Bitrix para os ADMs de Pasta relevantes: {', '.join(nomes_adms_relevantes_para_filtro_bitrix)}")
    else:
        st.warning(f"Coluna ADM de Pasta ('{col_adm_pasta_bitrix}') não encontrada nos dados do Bitrix. O filtro de ADM principal não será aplicado.")

    if 'STAGE_ID' in df.columns:
        df['ESTAGIO_ATUAL_LEGIVEL'] = df['STAGE_ID'].apply(simplificar_nome_estagio)
    else:
        st.error("Coluna STAGE_ID não encontrada para determinar o estágio atual.")
        return
    
    # --- Filtro de Período para Análise de Resoluções ---
    st.subheader("🗓️ Filtros para Análise")
    
    # Filtro de período
    col_data1, col_data2 = st.columns(2)
    with col_data1:
        data_inicio_analise = st.date_input("Data Inicial", value=datetime.now().date() - pd.Timedelta(days=30), key="data_inicio_resol_adm_geral")
    with col_data2:
        data_fim_analise = st.date_input("Data Final", value=datetime.now().date(), key="data_fim_resol_adm_geral")

    if data_inicio_analise > data_fim_analise:
        st.warning("A data inicial da análise não pode ser posterior à data final.")
        return
    
    # Filtro de Consultor (ADM)
    if mapa_usuarios:
        # Criar uma lista de nomes baseada nos IDs relevantes
        nomes_adms_para_filtro = [mapa_usuarios.get(id_adm, mapa_usuarios.get(f"user_{id_adm}", f"ID {id_adm}")) 
                                 for id_adm in LISTA_IDS_ADMS_RELEVANTES]
        # Remover duplicatas e ordenar
        nomes_adms_para_filtro = sorted(list(set(nomes_adms_para_filtro)))
        # Adicionar opção para selecionar todos
        nomes_adms_para_filtro = ['Todos os ADMs'] + nomes_adms_para_filtro
        
        adm_selecionado = st.selectbox("Filtrar por Consultor (ADM)", 
                                      options=nomes_adms_para_filtro,
                                      index=0)
    else:
        adm_selecionado = 'Todos os ADMs'
        st.warning("Mapeamento de usuários não disponível. Mostrando todos os ADMs.")
    
    # Filtro de Tipo de Pendência
    tipos_pendencia_para_filtro = ['Todos os Tipos'] + ESTAGIOS_DEVOLUCAO_ADM
    tipo_pendencia_selecionado = st.selectbox("Filtrar por Tipo de Pendência", 
                                           options=tipos_pendencia_para_filtro,
                                           index=0)
    
    st.info(f"""
    **Filtros aplicados:**
    - Período: {data_inicio_analise.strftime('%d/%m/%Y')} a {data_fim_analise.strftime('%d/%m/%Y')}
    - Consultor: {adm_selecionado}
    - Tipo de Pendência: {tipo_pendencia_selecionado}
    """)
    
    st.markdown("---")

    # --- Carregar Dados do Supabase para o período selecionado ---
    with st.spinner(f"Carregando dados..."):
        df_supabase = pd.DataFrame()
        dados_supabase_raw = fetch_supabase_producao_data(
            data_inicio_analise.strftime('%Y-%m-%d'),
            data_fim_analise.strftime('%Y-%m-%d')
        )
        if dados_supabase_raw is not None and not dados_supabase_raw.empty:
            df_supabase = pd.DataFrame(dados_supabase_raw)
            if 'data_criacao' in df_supabase.columns:
                df_supabase['data_criacao'] = pd.to_datetime(df_supabase['data_criacao'], format='ISO8601', errors='coerce')
            
            # Verificar se a coluna estagio_id existe ou procurar por alternativas
            col_estagio = None
            if 'estagio_id' in df_supabase.columns:
                col_estagio = 'estagio_id'
            elif 'stage_id' in df_supabase.columns:
                col_estagio = 'stage_id'
            elif 'STAGE_ID' in df_supabase.columns:
                col_estagio = 'STAGE_ID'
            
            if col_estagio:
                df_supabase['_TEMP_STAGE_NAME'] = df_supabase[col_estagio].apply(simplificar_nome_estagio)
                df_supabase['STAGE_NAME_PADRONIZADO'] = df_supabase['_TEMP_STAGE_NAME'].apply(
                    lambda x: x.split('/')[-1].strip() if isinstance(x, str) and '/' in x else x
                )
                df_supabase.drop(columns=['_TEMP_STAGE_NAME'], inplace=True)
            else:
                st.warning(f"Coluna de estágio não encontrada nos dados do Supabase. Colunas disponíveis: {df_supabase.columns.tolist()}")
                df_supabase['STAGE_NAME_PADRONIZADO'] = None
        else:
            st.warning("Nenhum dado de histórico encontrado no Supabase para o período selecionado.")
        
        if not df_supabase.empty and 'id_card' in df_supabase.columns and 'data_criacao' in df_supabase.columns:
            df_supabase = df_supabase.sort_values(by=['id_card', 'data_criacao'])
            df_supabase['PROXIMO_ESTAGIO_PADRONIZADO'] = df_supabase.groupby('id_card')['STAGE_NAME_PADRONIZADO'].shift(-1)
            df_supabase['PROXIMA_DATA_CRIACAO'] = df_supabase.groupby('id_card')['data_criacao'].shift(-1)
            df_supabase['PROXIMO_MOVED_BY_ID'] = df_supabase.groupby('id_card')['movido_por_id'].shift(-1)
            if 'id' in df_supabase.columns:
                df_supabase['PROXIMA_MOVIMENTACAO_SUPABASE_ID'] = df_supabase.groupby('id_card')['id'].shift(-1)
        else:
            if df_supabase.empty:
                st.warning("Não foram encontrados dados no Supabase para o período selecionado.")
            else:
                df_supabase['PROXIMO_ESTAGIO_PADRONIZADO'] = None
                df_supabase['PROXIMA_DATA_CRIACAO'] = None
                df_supabase['PROXIMO_MOVED_BY_ID'] = None
                if 'id' in df_supabase.columns:
                    df_supabase['PROXIMA_MOVIMENTACAO_SUPABASE_ID'] = None

    # --- VISÃO GERAL SIMPLIFICADA ---
    st.subheader("📌 Resumo de Pendências e Resoluções")
    
    # 1. Total de Pendências Ativas por ADM
    df_pendencias_ativas_bitrix = df[df['ESTAGIO_ATUAL_LEGIVEL'].isin(ESTAGIOS_DEVOLUCAO_ADM)].copy()
    
    # Aplicar filtro de tipo de pendência selecionado
    if tipo_pendencia_selecionado != 'Todos os Tipos':
        df_pendencias_ativas_bitrix = df_pendencias_ativas_bitrix[
            df_pendencias_ativas_bitrix['ESTAGIO_ATUAL_LEGIVEL'] == tipo_pendencia_selecionado
        ]
    
    # Aplicar filtro de ADM selecionado
    if adm_selecionado != 'Todos os ADMs' and col_adm_pasta_bitrix in df_pendencias_ativas_bitrix.columns:
        df_pendencias_ativas_bitrix = df_pendencias_ativas_bitrix[
            df_pendencias_ativas_bitrix[col_adm_pasta_bitrix] == adm_selecionado
        ]
    
    total_pendencias_ativas = len(df_pendencias_ativas_bitrix)
    
    contagem_ativas_por_adm = pd.Series(dtype='int')
    if not df_pendencias_ativas_bitrix.empty and col_adm_pasta_bitrix in df_pendencias_ativas_bitrix.columns:
        df_pendencias_ativas_bitrix[col_adm_pasta_bitrix] = df_pendencias_ativas_bitrix[col_adm_pasta_bitrix].fillna('ADM Desconhecido')
        df_pendencias_ativas_bitrix.loc[df_pendencias_ativas_bitrix[col_adm_pasta_bitrix].str.strip() == '', col_adm_pasta_bitrix] = 'ADM Desconhecido'
        contagem_ativas_por_adm = df_pendencias_ativas_bitrix.groupby(col_adm_pasta_bitrix).size()
    
    # 2. Coletar todas as resoluções
    lista_dfs_pendencias_resolvidas = []
    if not df_supabase.empty:
        col_id_bitrix_map = 'ID'
        col_id_supabase_map = 'id_card'
        for tipo_pendencia in ESTAGIOS_DEVOLUCAO_ADM:
            # Pular se não for o tipo selecionado (quando um tipo específico for selecionado)
            if tipo_pendencia_selecionado != 'Todos os Tipos' and tipo_pendencia != tipo_pendencia_selecionado:
                continue
                
            _, df_detalhe_resolvidas_tipo = analisar_resolucao_pendencia(
                df_bitrix_atual=df,
                df_supabase_hist=df_supabase,
                nome_pendencia_especifica=tipo_pendencia,
                lista_todos_estagios_pendencia=ESTAGIOS_DEVOLUCAO_ADM,
                col_adm_pasta_bitrix=col_adm_pasta_bitrix,
                col_id_bitrix=col_id_bitrix_map,
                col_id_supabase=col_id_supabase_map,
                mapa_nomes_usuarios=mapa_usuarios,
                renderizar_saida_streamlit=False,
                filtro_adm=adm_selecionado
            )
            if df_detalhe_resolvidas_tipo is not None and not df_detalhe_resolvidas_tipo.empty:
                lista_dfs_pendencias_resolvidas.append(df_detalhe_resolvidas_tipo)
    
    df_todas_pendencias_resolvidas = pd.DataFrame()
    total_pendencias_resolvidas = 0
    if lista_dfs_pendencias_resolvidas:
        df_todas_pendencias_resolvidas = pd.concat(lista_dfs_pendencias_resolvidas, ignore_index=True)
        
        # Aplicar filtro de ADM selecionado para resoluções
        if adm_selecionado != 'Todos os ADMs' and 'Responsável pela Resolução' in df_todas_pendencias_resolvidas.columns:
            df_todas_pendencias_resolvidas = df_todas_pendencias_resolvidas[
                df_todas_pendencias_resolvidas['Responsável pela Resolução'] == adm_selecionado
            ]
            
        total_pendencias_resolvidas = len(df_todas_pendencias_resolvidas)
    
    # 3. Exibir Métricas Resumidas
    col1, col2, col3 = st.columns(3)
    
    st.markdown('<div class="producao-adm producao-adm__metricas">', unsafe_allow_html=True)
    col1.metric("Total de Pendências Ativas", f"{total_pendencias_ativas}")
    col2.metric("Total de Pendências Resolvidas", f"{total_pendencias_resolvidas}")
    
    # Calcular percentual de resolução se existirem pendências
    total_geral = total_pendencias_ativas + total_pendencias_resolvidas
    percentual_resolucao = 0
    if total_geral > 0:
        percentual_resolucao = (total_pendencias_resolvidas / total_geral) * 100
    col3.metric("Percentual de Resolução", f"{percentual_resolucao:.1f}%")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("<h3>📊 Análise por ADM</h3>", unsafe_allow_html=True)
    
    # 4. Criar tabela consolidada por ADM com pendências e resoluções
    df_consolidado_adm = pd.DataFrame(index=nomes_adms_relevantes_para_filtro_bitrix if nomes_adms_relevantes_para_filtro_bitrix else list(mapa_usuarios.values()))
    df_consolidado_adm.index.name = 'ADM de Pasta'
    df_consolidado_adm['Pendências Ativas'] = df_consolidado_adm.index.map(contagem_ativas_por_adm).fillna(0).astype(int)
    df_consolidado_adm['Pendências Resolvidas'] = 0
    df_consolidado_adm['Tempo Médio de Resolução (dias)'] = 0
    
    # 5. Calcular resoluções e tempo médio por ADM
    if not df_todas_pendencias_resolvidas.empty and 'ID Responsável pela Resolução' in df_todas_pendencias_resolvidas.columns:
        # Garantir que temos a coluna de Responsável mapeada para nomes
        if 'Responsável pela Resolução' not in df_todas_pendencias_resolvidas.columns:
            df_todas_pendencias_resolvidas['Responsável pela Resolução'] = df_todas_pendencias_resolvidas['ID Responsável pela Resolução'].astype(str).map(mapa_usuarios).fillna(df_todas_pendencias_resolvidas['ID Responsável pela Resolução'])
        
        # Filtrar pelos ADMs relevantes
        df_resolvidas_adms_relevantes = df_todas_pendencias_resolvidas[
            df_todas_pendencias_resolvidas['ID Responsável pela Resolução'].astype(str).isin(LISTA_IDS_ADMS_RELEVANTES_COM_PREFIXO)
        ].copy()
        
        if not df_resolvidas_adms_relevantes.empty:
            # Contagem de resoluções por ADM
            contagem_resolvidas_por_adm = df_resolvidas_adms_relevantes.groupby('Responsável pela Resolução').size()
            df_consolidado_adm['Pendências Resolvidas'] = df_consolidado_adm.index.map(contagem_resolvidas_por_adm).fillna(0).astype(int)
            
            # Tempo médio de resolução por ADM
            if 'Tempo para Resolução (dias)' in df_resolvidas_adms_relevantes.columns:
                tempo_medio_por_adm = df_resolvidas_adms_relevantes.groupby('Responsável pela Resolução')['Tempo para Resolução (dias)'].mean()
                df_consolidado_adm['Tempo Médio de Resolução (dias)'] = df_consolidado_adm.index.map(tempo_medio_por_adm).fillna(0).round(1)
    
    # 6. Calcular a Taxa de Conversão (novo)
    df_consolidado_adm['Total de Pendências'] = df_consolidado_adm['Pendências Ativas'] + df_consolidado_adm['Pendências Resolvidas']
    df_consolidado_adm['Taxa de Conversão (%)'] = (df_consolidado_adm['Pendências Resolvidas'] / df_consolidado_adm['Total de Pendências'] * 100).round(1)
    # Substituir NaN (quando Total de Pendências é zero) por 0
    df_consolidado_adm['Taxa de Conversão (%)'] = df_consolidado_adm['Taxa de Conversão (%)'].fillna(0)
    
    # 7. Ordenar e exibir o dataframe consolidado
    df_consolidado_adm = df_consolidado_adm.sort_values(by=['Pendências Ativas', 'Pendências Resolvidas'], ascending=[False, False])
    
    # Reorganizar colunas e remover coluna auxiliar
    colunas_ordem_para_exibir = [
        'Pendências Ativas', 
        'Pendências Resolvidas', 
        'Taxa de Conversão (%)',
        'Tempo Médio de Resolução (dias)'
    ]
    df_consolidado_adm = df_consolidado_adm[colunas_ordem_para_exibir]
    
    df_consolidado_adm = df_consolidado_adm.reset_index()
    
    # Aplicar filtro de ADM selecionado à tabela se não for "Todos os ADMs"
    if adm_selecionado != 'Todos os ADMs':
        df_consolidado_adm = df_consolidado_adm[df_consolidado_adm['ADM de Pasta'] == adm_selecionado]
    
    # Aplicar formatação para destacar taxas de conversão mais altas
    def highlight_conversao(s):
        """Adiciona formatação de cores baseada na taxa de conversão"""
        # Verificar se a coluna atual é a Taxa de Conversão (%)
        if s.name != 'Taxa de Conversão (%)':
            return [''] * len(s)
        
        # Converter para números para fazer as comparações
        try:
            values = pd.to_numeric(s)
            is_max = values == values.max()
            is_high = values >= 75
            is_medium = (values >= 50) & (values < 75)
            is_low = (values >= 25) & (values < 50)
            is_very_low = (values < 25) & (values > 0)
            is_zero = values == 0
            
            return ['background-color: #4CAF50; color: white; font-weight: bold' if v else  # verde (máximo)
                    'background-color: #8BC34A; color: black' if h else  # verde claro (alto)
                    'background-color: #FFEB3B; color: black' if m else  # amarelo (médio)
                    'background-color: #FFC107; color: black' if l else  # laranja (baixo)
                    'background-color: #FF9800; color: black' if vl else  # laranja forte (muito baixo)
                    'background-color: #F5F5F5; color: #9E9E9E' if z else ''  # cinza (zero)
                    for v, h, m, l, vl, z in zip(is_max, is_high, is_medium, is_low, is_very_low, is_zero)]
        except:
            # Se houver erro na conversão, retornar sem formatação
            return [''] * len(s)
    
    # Aplicar estilo à tabela
    styled_df = df_consolidado_adm.style.apply(highlight_conversao)
    
    # Formatar números decimais
    styled_df = styled_df.format({
        'Taxa de Conversão (%)': '{:.1f}%',
        'Tempo Médio de Resolução (dias)': '{:.1f}'
    })
    
    st.markdown('<div class="producao-adm producao-adm__tabela">', unsafe_allow_html=True)
    st.dataframe(styled_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.caption("""
    **Tabela 1: Resumo por ADM**
    - **Pendências Ativas**: Baseadas no ADM de Pasta
    - **Pendências Resolvidas**: Baseadas no Responsável pela movimentação
    - **Taxa de Conversão**: (Pendências Resolvidas ÷ Total de Pendências) × 100%
    - **Tempo Médio**: Tempo médio entre entrada e resolução da pendência (em dias)
    """)
    
    # --- EVOLUÇÃO DAS RESOLUÇÕES (GRÁFICO) ---
    st.markdown("---")
    st.markdown("<h3>📈 Evolução das Resoluções</h3>", unsafe_allow_html=True)
    
    # Verificar se há dados para criar o gráfico
    if not df_todas_pendencias_resolvidas.empty and 'Data da Resolução' in df_todas_pendencias_resolvidas.columns:
        # Garantir que Data da Resolução é datetime
        try:
            df_todas_pendencias_resolvidas['Data da Resolução'] = pd.to_datetime(df_todas_pendencias_resolvidas['Data da Resolução'])
        except:
            st.warning("Não foi possível converter as datas para o formato correto.")
            
        # Criar coluna de data (sem hora) para agrupamento
        df_todas_pendencias_resolvidas['Data Resolução'] = df_todas_pendencias_resolvidas['Data da Resolução'].dt.date
        
        # Agrupar dados por data
        df_para_grafico = df_todas_pendencias_resolvidas.copy()
        
        # Agrupar por data para gráfico simplificado com total diário
        df_resol_por_dia = df_para_grafico.groupby('Data Resolução').size().reset_index(name='Resoluções')
        
        # Importar Altair para gráficos
        import altair as alt
        
        # Criar gráfico de barras com linha de tendência
        barras = alt.Chart(df_resol_por_dia).mark_bar(
            color='#4CAF50',
            size=40  # Barras ainda mais largas
        ).encode(
            x=alt.X('Data Resolução:T', title='Data', axis=alt.Axis(format='%d/%m/%Y')),
            y=alt.Y('Resoluções:Q', title='Quantidade de Resoluções'),
            tooltip=['Data Resolução:T', 'Resoluções:Q']
        )
        
        # Adicionar números em cima das barras
        texto = alt.Chart(df_resol_por_dia).mark_text(
            align='center',
            baseline='bottom',
            dy=-5,  # Deslocamento vertical (acima da barra)
            fontSize=14,
            fontWeight='bold'
        ).encode(
            x='Data Resolução:T',
            y='Resoluções:Q',
            text='Resoluções:Q'
        )
        
        # Adicionar linha de tendência
        linha_tendencia = alt.Chart(df_resol_por_dia).transform_regression(
            'Data Resolução', 'Resoluções'
        ).mark_line(
            color='red', 
            strokeWidth=3,
            strokeDash=[5, 5]
        ).encode(
            x='Data Resolução:T',
            y='Resoluções:Q'
        )
        
        # Combinar gráficos (barras + texto + linha de tendência)
        chart = (barras + texto + linha_tendencia).properties(
            title='Total de Resoluções Diárias',
            height=300
        ).configure_title(
            fontSize=16
        )
        
        # Exibir o gráfico
        st.markdown('<div class="adm-evolucao-grafico">', unsafe_allow_html=True)
        st.altair_chart(chart, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.info("Não há dados suficientes para mostrar a evolução das resoluções.")
    
    # --- ANÁLISE DETALHADA POR TIPO DE PENDÊNCIA ---
    st.markdown("---")
    st.markdown("<h3>🔍 Detalhes por Tipo de Pendência</h3>", unsafe_allow_html=True)
    
    # 7. Exibir detalhes de cada tipo de pendência em expansores
    st.markdown('<div class="adm-detalhes-pendencia">', unsafe_allow_html=True)
    if not df_supabase.empty:
        for tipo_pendencia in ESTAGIOS_DEVOLUCAO_ADM:
            # Pular se não for o tipo selecionado (quando um tipo específico for selecionado)
            if tipo_pendencia_selecionado != 'Todos os Tipos' and tipo_pendencia != tipo_pendencia_selecionado:
                continue
                
            with st.expander(f"Pendências: {tipo_pendencia}", expanded=tipo_pendencia_selecionado != 'Todos os Tipos'):
                analisar_resolucao_pendencia(
                    df_bitrix_atual=df, 
                    df_supabase_hist=df_supabase, 
                    nome_pendencia_especifica=tipo_pendencia, 
                    lista_todos_estagios_pendencia=ESTAGIOS_DEVOLUCAO_ADM, 
                    col_adm_pasta_bitrix=col_adm_pasta_bitrix,
                    col_id_bitrix='ID',
                    col_id_supabase='id_card',
                    mapa_nomes_usuarios=mapa_usuarios,
                    renderizar_saida_streamlit=True,
                    filtro_adm=adm_selecionado
                )
    else:
        st.info("Nenhum dado disponível para análise detalhada por tipo de pendência.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fecha cartorio-container

def analisar_resolucao_pendencia(
    df_bitrix_atual, 
    df_supabase_hist, 
    nome_pendencia_especifica, 
    lista_todos_estagios_pendencia,
    col_adm_pasta_bitrix,
    col_id_bitrix,
    col_id_supabase,
    mapa_nomes_usuarios,
    renderizar_saida_streamlit=True,
    filtro_adm='Todos os ADMs'
):
    """
    Analisa a resolução de um tipo específico de pendência.
    """
    if renderizar_saida_streamlit:
        st.markdown(f"**Análise de Pendências: {nome_pendencia_especifica}**")

    if df_supabase_hist.empty:
        if renderizar_saida_streamlit:
            st.info(f"Nenhum dado de histórico disponível para analisar '{nome_pendencia_especifica}'.")
        return None, pd.DataFrame()

    # Filtrar entradas para o tipo de pendência específico
    df_entradas_na_pendencia = df_supabase_hist[
        df_supabase_hist['STAGE_NAME_PADRONIZADO'] == nome_pendencia_especifica
    ].copy()
    
    if df_entradas_na_pendencia.empty:
        if renderizar_saida_streamlit:
            st.info(f"Nenhum item entrou no estágio '{nome_pendencia_especifica}' no período analisado.")
            # Métricas zeradas
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            col_metric1.metric(label=f"Ocorrências ({nome_pendencia_especifica})", value=0)
            col_metric2.metric(label=f"Resolvidas", value=0)
            col_metric3.metric(label=f"Taxa de Resolução", value="0%")
        return df_entradas_na_pendencia, pd.DataFrame()

    # Calcular métricas básicas
    total_ocorrencias = len(df_entradas_na_pendencia)
    cards_unicos_na_pendencia = df_entradas_na_pendencia[col_id_supabase].nunique()

    # Identificar quais pendências foram resolvidas (saíram para um estágio não-pendência)
    df_entradas_na_pendencia['FOI_RESOLVIDA'] = (
        df_entradas_na_pendencia['PROXIMO_ESTAGIO_PADRONIZADO'].notna() & 
        (~df_entradas_na_pendencia['PROXIMO_ESTAGIO_PADRONIZADO'].isin(lista_todos_estagios_pendencia))
    )
    
    # Filtrar apenas as resolvidas para análise
    df_pendencias_resolvidas_detalhe = df_entradas_na_pendencia[df_entradas_na_pendencia['FOI_RESOLVIDA']].copy()
    
    # Calcular métricas de resolução
    total_resolvidas = len(df_pendencias_resolvidas_detalhe)
    taxa_resolucao = (total_resolvidas / total_ocorrencias * 100) if total_ocorrencias > 0 else 0

    # Exibir métricas principais
    if renderizar_saida_streamlit:
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        col_metric1.metric(label=f"Ocorrências ({nome_pendencia_especifica})", value=f"{total_ocorrencias:,} ({cards_unicos_na_pendencia} únicos)")
        col_metric2.metric(label=f"Resolvidas", value=f"{total_resolvidas:,}")
        col_metric3.metric(label=f"Taxa de Resolução", value=f"{taxa_resolucao:.1f}%")
        st.caption(f"Considera todas as entradas no estágio '{nome_pendencia_especifica}' no período e verifica se a movimentação seguinte as tirou de um estado de pendência.")

    # Se não há pendências resolvidas, retornar
    if df_pendencias_resolvidas_detalhe.empty:
        if renderizar_saida_streamlit:
            st.info(f"Nenhuma ocorrência de '{nome_pendencia_especifica}' foi identificada como resolvida no período.")
        return df_entradas_na_pendencia, df_pendencias_resolvidas_detalhe

    # Renomear colunas para melhor apresentação
    df_pendencias_resolvidas_detalhe = df_pendencias_resolvidas_detalhe.rename(
        columns={
            col_id_supabase: 'ID Card',
            'data_criacao': 'Data Entrada na Pendência',
            'movido_por_id': 'ID Responsável Entrada Pendência',
            'STAGE_NAME_PADRONIZADO': 'Estágio de Pendência',
            'PROXIMO_ESTAGIO_PADRONIZADO': 'Estágio Pós-Resolução',
            'PROXIMA_DATA_CRIACAO': 'Data da Resolução',
            'PROXIMO_MOVED_BY_ID': 'ID Responsável pela Resolução'
        }
    )
    
    # Mapear IDs para nomes
    if 'ID Responsável pela Resolução' in df_pendencias_resolvidas_detalhe.columns:
        df_pendencias_resolvidas_detalhe['Responsável pela Resolução'] = df_pendencias_resolvidas_detalhe['ID Responsável pela Resolução'].astype(str).map(mapa_nomes_usuarios).fillna(df_pendencias_resolvidas_detalhe['ID Responsável pela Resolução'])
    
    if 'ID Responsável Entrada Pendência' in df_pendencias_resolvidas_detalhe.columns:
        df_pendencias_resolvidas_detalhe['Responsável Entrada Pendência'] = df_pendencias_resolvidas_detalhe['ID Responsável Entrada Pendência'].astype(str).map(mapa_nomes_usuarios).fillna(df_pendencias_resolvidas_detalhe['ID Responsável Entrada Pendência'])
    
    # Aplicar filtro de ADM se especificado
    if filtro_adm != 'Todos os ADMs' and 'Responsável pela Resolução' in df_pendencias_resolvidas_detalhe.columns:
        df_pendencias_resolvidas_detalhe = df_pendencias_resolvidas_detalhe[
            df_pendencias_resolvidas_detalhe['Responsável pela Resolução'] == filtro_adm
        ]
        # Recalcular total após filtro
        total_resolvidas = len(df_pendencias_resolvidas_detalhe)
    
    # Calcular tempo de resolução
    df_pendencias_resolvidas_detalhe['Tempo para Resolução (dias)'] = (
        (df_pendencias_resolvidas_detalhe['Data da Resolução'] - df_pendencias_resolvidas_detalhe['Data Entrada na Pendência']).dt.total_seconds() / (24 * 60 * 60)
    ).round(1)

    # Exibir tabelas e estatísticas se renderizar_saida_streamlit=True
    if renderizar_saida_streamlit:
        # Exibir detalhes das pendências resolvidas
        st.markdown("#### Detalhes das Pendências Resolvidas")
        
        # Merge com df_bitrix_atual para adicionar ADM da Pasta
        df_pendencias_resolvidas_detalhe['ID Card'] = df_pendencias_resolvidas_detalhe['ID Card'].astype(str)
        df_bitrix_atual_temp = df_bitrix_atual.copy()
        
        if col_id_bitrix in df_bitrix_atual_temp.columns:
            df_bitrix_atual_temp[col_id_bitrix] = df_bitrix_atual_temp[col_id_bitrix].astype(str)
            
            df_pendencias_resolvidas_detalhe_merged = pd.merge(
                df_pendencias_resolvidas_detalhe,
                df_bitrix_atual_temp[[col_id_bitrix, col_adm_pasta_bitrix] if col_adm_pasta_bitrix in df_bitrix_atual_temp.columns else df_bitrix_atual_temp[[col_id_bitrix]]],
                left_on='ID Card',
                right_on=col_id_bitrix,
                how='left'
            )
            
            if col_adm_pasta_bitrix in df_pendencias_resolvidas_detalhe_merged.columns:
                df_pendencias_resolvidas_detalhe_merged[col_adm_pasta_bitrix] = df_pendencias_resolvidas_detalhe_merged[col_adm_pasta_bitrix].fillna('N/A')
            
            # Formatar datas para exibição
            if 'Data Entrada na Pendência' in df_pendencias_resolvidas_detalhe_merged.columns:
                df_pendencias_resolvidas_detalhe_merged['Data Entrada na Pendência'] = pd.to_datetime(df_pendencias_resolvidas_detalhe_merged['Data Entrada na Pendência']).dt.strftime('%d/%m/%Y %H:%M')
            
            if 'Data da Resolução' in df_pendencias_resolvidas_detalhe_merged.columns:
                df_pendencias_resolvidas_detalhe_merged['Data da Resolução'] = pd.to_datetime(df_pendencias_resolvidas_detalhe_merged['Data da Resolução']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Definir colunas a serem exibidas
            colunas_para_exibir = [
                'ID Card', 
                'Responsável pela Resolução', 
                'Data Entrada na Pendência', 
                'Data da Resolução', 
                'Tempo para Resolução (dias)',
                col_adm_pasta_bitrix
            ]
            
            colunas_existentes = [col for col in colunas_para_exibir if col in df_pendencias_resolvidas_detalhe_merged.columns]
            
            # Exibir tabela de detalhes
            if not df_pendencias_resolvidas_detalhe_merged.empty:
                st.dataframe(df_pendencias_resolvidas_detalhe_merged[colunas_existentes], use_container_width=True)
                
                # Exibir estatísticas do tempo de resolução
                if 'Tempo para Resolução (dias)' in df_pendencias_resolvidas_detalhe_merged.columns and len(df_pendencias_resolvidas_detalhe_merged) > 1:
                    stats_col1, stats_col2, stats_col3 = st.columns(3)
                    with stats_col1:
                        tempo_min = df_pendencias_resolvidas_detalhe_merged['Tempo para Resolução (dias)'].min()
                        st.metric("Tempo Mínimo", f"{tempo_min:.1f} dias")
                    with stats_col2:
                        tempo_medio = df_pendencias_resolvidas_detalhe_merged['Tempo para Resolução (dias)'].mean()
                        st.metric("Tempo Médio", f"{tempo_medio:.1f} dias")
                    with stats_col3:
                        tempo_max = df_pendencias_resolvidas_detalhe_merged['Tempo para Resolução (dias)'].max()
                        st.metric("Tempo Máximo", f"{tempo_max:.1f} dias")
            else:
                st.info("Nenhum detalhe disponível após o processamento.")
        else:
            st.error(f"Coluna ID '{col_id_bitrix}' não encontrada para merge.")
            st.dataframe(df_pendencias_resolvidas_detalhe, use_container_width=True)

    return df_entradas_na_pendencia, df_pendencias_resolvidas_detalhe 