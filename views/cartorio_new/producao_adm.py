import streamlit as st
import pandas as pd
from datetime import datetime, time
import numpy as np
import os # Importar os para manipulação de caminhos

# Funções que podem ser úteis
from .utils import simplificar_nome_estagio, fetch_supabase_producao_data, carregar_dados_usuarios_bitrix

# Obter o diretório do arquivo atual
_PRODUCAO_ADM_DIR = os.path.dirname(os.path.abspath(__file__))

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

# Mapeamento de estágios para campos de data correspondentes
MAPEAMENTO_ESTAGIOS_CAMPOS_DATA = {
    'DEVOLUÇÃO ADM': {
        'campo_data_entrada': 'UF_CRM_34_DATA_DEVOLUCAO_ADM',
        'campo_responsavel_entrada': 'UF_CRM_34_RESPONSAVEL_DEVOLUCAO_ADM',
        'estagios_resolucao': [
            'UF_CRM_34_DATA_ASSINATURA_REQUERIMENTO',
            'UF_CRM_34_DATA_MONTAGEM_REQUERIMENTO', 
            'UF_CRM_34_DATA_CERTIDAO_EMITIDA',
            'UF_CRM_34_DATA_CERTIDAO_ENTREGUE'
        ],
        'responsaveis_resolucao': [
            'UF_CRM_34_RESPONSAVEL_ASSINATURA_REQUERIMENTO',
            'UF_CRM_34_RESPONSAVEL_MONTAGEM_REQUERIMENTO',
            'UF_CRM_34_RESPONSAVEL_CERTIDAO_EMITIDA', 
            'UF_CRM_34_RESPONSAVEL_DATA_CERTIDAO_ENTREGUE'
        ]
    },
    'DEVOLVIDO REQUERIMENTO': {
        'campo_data_entrada': 'UF_CRM_34_DATA_DEVOLVIDO_REQUERIMENTO',
        'campo_responsavel_entrada': None,  # Não tem campo específico
        'estagios_resolucao': [
            'UF_CRM_34_DATA_ASSINATURA_REQUERIMENTO',
            'UF_CRM_34_DATA_MONTAGEM_REQUERIMENTO',
            'UF_CRM_34_DATA_CERTIDAO_EMITIDA'
        ],
        'responsaveis_resolucao': [
            'UF_CRM_34_RESPONSAVEL_ASSINATURA_REQUERIMENTO',
            'UF_CRM_34_RESPONSAVEL_MONTAGEM_REQUERIMENTO',
            'UF_CRM_34_RESPONSAVEL_CERTIDAO_EMITIDA'
        ]
    },
    'DEVOLUTIVA BUSCA - CRC': {
        'campo_data_entrada': 'UF_CRM_34_DATA_DEVOLUITIVA_BUSCA_CRC',
        'campo_responsavel_entrada': 'UF_CRM_34_RESPONSAVEL_DEVOLUITIVA_BUSCA_CRC',
        'estagios_resolucao': [
            'UF_CRM_34_DATA_MONTAGEM_REQUERIMENTO',
            'UF_CRM_34_DATA_ASSINATURA_REQUERIMENTO',
            'UF_CRM_34_DATA_CERTIDAO_EMITIDA'
        ],
        'responsaveis_resolucao': [
            'UF_CRM_34_RESPONSAVEL_MONTAGEM_REQUERIMENTO',
            'UF_CRM_34_RESPONSAVEL_ASSINATURA_REQUERIMENTO',
            'UF_CRM_34_RESPONSAVEL_CERTIDAO_EMITIDA'
        ]
    },
    'APENAS ASS. REQ CLIENTE P/MONTAGEM': {
        'campo_data_entrada': None,  # Não tem campo específico
        'campo_responsavel_entrada': None,
        'estagios_resolucao': [
            'UF_CRM_34_DATA_ASSINATURA_REQUERIMENTO',
            'UF_CRM_34_DATA_MONTAGEM_REQUERIMENTO'
        ],
        'responsaveis_resolucao': [
            'UF_CRM_34_RESPONSAVEL_ASSINATURA_REQUERIMENTO',
            'UF_CRM_34_RESPONSAVEL_MONTAGEM_REQUERIMENTO'
        ]
    }
}

def exibir_producao_adm(df_cartorio_original):
    st.markdown('<div class="cartorio-container cartorio-container--info">', unsafe_allow_html=True)
    st.title("Dashboard de Pendências ADM")
    
    # --- Carregar CSS Compilado ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
            st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal não encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar o CSS: {e}")
    
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
    # --- Expander para Filtros ---
    with st.expander("Filtros", expanded=True):  # Começa expandido
        # Linha 1: Filtro de Data
        col_data1, col_data2, col_data3 = st.columns([0.3, 0.35, 0.35])
        with col_data1:
            aplicar_filtro_data = st.checkbox("Data Análise", value=False, key="aplicar_filtro_data_producao_adm")

        data_inicio_analise = None
        data_fim_analise = None
        
        # Campos de data aparecem apenas se o checkbox estiver marcado
        if aplicar_filtro_data:
            with col_data2:
                data_inicio_analise = st.date_input(
                    "De:",
                    value=datetime.now().date() - pd.Timedelta(days=30),
                    key="data_inicio_resol_adm_geral",
                    label_visibility="collapsed"
                )
            with col_data3:
                data_fim_analise = st.date_input(
                    "Até:",
                    value=datetime.now().date(),
                    key="data_fim_resol_adm_geral",
                    label_visibility="collapsed"
                )
        else:
            # Usar valores padrão quando filtro de data não está ativado
            data_inicio_analise = datetime.now().date() - pd.Timedelta(days=30)
            data_fim_analise = datetime.now().date()

        if data_inicio_analise and data_fim_analise and data_inicio_analise > data_fim_analise:
            st.error("⚠️ A data inicial não pode ser posterior à data final.")
            return
        
        # Linha 2: Filtros de Categorização
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        # Filtro de Consultor (ADM)
        with col_filtro1:
            if mapa_usuarios:
                # Criar uma lista de nomes baseada nos IDs relevantes
                nomes_adms_para_filtro = [mapa_usuarios.get(id_adm, mapa_usuarios.get(f"user_{id_adm}", f"ID {id_adm}")) 
                                         for id_adm in LISTA_IDS_ADMS_RELEVANTES]
                # Remover duplicatas e ordenar
                nomes_adms_para_filtro = sorted(list(set(nomes_adms_para_filtro)))
                # Adicionar opção para selecionar todos
                nomes_adms_para_filtro = ['Todos os ADMs'] + nomes_adms_para_filtro
                
                adm_selecionado = st.selectbox(
                    "Filtrar por Consultor (ADM):", 
                    options=nomes_adms_para_filtro,
                    index=0
                )
            else:
                adm_selecionado = 'Todos os ADMs'
                st.warning("⚠️ Mapeamento de usuários não disponível. Mostrando todos os ADMs.")
        
        # Filtro de Tipo de Pendência
        with col_filtro2:
            tipos_pendencia_para_filtro = ['Todos os Tipos'] + ESTAGIOS_DEVOLUCAO_ADM
            tipo_pendencia_selecionado = st.selectbox(
                "Filtrar por Tipo de Pendência:", 
                options=tipos_pendencia_para_filtro,
                index=0
            )

        # Filtro de Protocolizado
        with col_filtro3:
            coluna_protocolizado = 'UF_CRM_34_PROTOCOLIZADO'
            filtro_protocolizado_habilitado = coluna_protocolizado in df.columns
            if filtro_protocolizado_habilitado:
                filtro_protocolizado = st.selectbox(
                    "Protocolizado:",
                    options=["Todos", "Protocolizado", "Não Protocolizado"],
                    index=0,
                    key="filtro_protocolizado_producao_adm"
                )
            else:
                st.caption(f":warning: Campo protocolizado não encontrado.")
                filtro_protocolizado = "Todos"
    
    # --- Aplicar Filtros (Fora do Expander) ---
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

    # Aplicar filtro de Protocolizado
    if filtro_protocolizado != "Todos" and filtro_protocolizado_habilitado:
        if coluna_protocolizado in df.columns:
            # Converter para string e normalizar valores
            df[coluna_protocolizado] = df[coluna_protocolizado].fillna('').astype(str).str.strip().str.upper()
            
            if filtro_protocolizado == "Protocolizado":
                # Os valores no campo são "PROTOCOLIZADO"
                df = df[df[coluna_protocolizado] == 'PROTOCOLIZADO']
            elif filtro_protocolizado == "Não Protocolizado":
                # Consideramos como não protocolizado qualquer valor diferente de "PROTOCOLIZADO"
                df = df[df[coluna_protocolizado] != 'PROTOCOLIZADO']
        else:
            st.warning(f"Coluna {coluna_protocolizado} não encontrada ao aplicar filtro de protocolizado.")

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
    # Calcular percentual de resolução se existirem pendências
    total_geral = total_pendencias_ativas + total_pendencias_resolvidas
    percentual_resolucao = 0
    if total_geral > 0:
        percentual_resolucao = (total_pendencias_resolvidas / total_geral) * 100
        
    # Criar métricas customizadas com HTML puro
    st.markdown(f"""
    <style>
    .metrica-custom-adm {{
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
    }}
    
    .metrica-custom-adm:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: #ADB5BD;
    }}
    
    .metrica-custom-adm .label {{
        color: #6C757D;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
        line-height: 1.2;
    }}
    
    .metrica-custom-adm .valor {{
        color: #495057;
        font-weight: 700;
        font-size: 30px;
        line-height: 1.2;
        margin-bottom: 4px;
    }}
    
    .metricas-container-adm {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }}
    </style>
    
    <div class="metricas-container-adm">
        <div class="metrica-custom-adm">
            <div class="label">Total de Pendências Ativas</div>
            <div class="valor">{total_pendencias_ativas:,}</div>
        </div>
        <div class="metrica-custom-adm">
            <div class="label">Total de Pendências Resolvidas</div>
            <div class="valor">{total_pendencias_resolvidas:,}</div>
        </div>
        <div class="metrica-custom-adm">
            <div class="label">Percentual de Resolução</div>
            <div class="valor">{percentual_resolucao:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("<h3>📊 Análise por ADM</h3>", unsafe_allow_html=True)
    
    # 4. Criar tabela consolidada por ADM com pendências e resoluções
    df_consolidado_adm = pd.DataFrame(index=nomes_adms_relevantes_para_filtro_bitrix if nomes_adms_relevantes_para_filtro_bitrix else list(mapa_usuarios.values()))
    df_consolidado_adm.index.name = 'ADM de Pasta'
    df_consolidado_adm['Pendências Ativas'] = df_consolidado_adm.index.map(contagem_ativas_por_adm).fillna(0).astype(int)
    
    # Colunas para método Supabase
    df_consolidado_adm['Resolvidas (Supabase)'] = 0
    df_consolidado_adm['Tempo Médio Supabase (dias)'] = 0
    
    # Colunas para método Bitrix  
    df_consolidado_adm['Resolvidas (Bitrix)'] = 0
    df_consolidado_adm['Tempo Médio Bitrix (dias)'] = 0
    
    # 5. Calcular resoluções e tempo médio por ADM - MÉTODO SUPABASE
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
            df_consolidado_adm['Resolvidas (Supabase)'] = df_consolidado_adm.index.map(contagem_resolvidas_por_adm).fillna(0).astype(int)
            
            # Tempo médio de resolução por ADM
            if 'Tempo para Resolução (dias)' in df_resolvidas_adms_relevantes.columns:
                tempo_medio_por_adm = df_resolvidas_adms_relevantes.groupby('Responsável pela Resolução')['Tempo para Resolução (dias)'].mean()
                df_consolidado_adm['Tempo Médio Supabase (dias)'] = df_consolidado_adm.index.map(tempo_medio_por_adm).fillna(0).round(1)
    
    # 6. Calcular resoluções e tempo médio por ADM - MÉTODO BITRIX (NOVO)
    # Primeiro, executar a análise por campos do Bitrix se ainda não foi executada
    if 'resultados_bitrix' not in locals():
        resultados_bitrix = analisar_pendencias_por_campos_bitrix(
            df_bitrix=df,
            mapa_usuarios=mapa_usuarios,
            col_adm_pasta_bitrix=col_adm_pasta_bitrix,
            filtro_adm='Todos os ADMs'  # Para consolidado por ADM, analisar todos
        )
    
    # Consolidar dados do método Bitrix por ADM
    dados_bitrix_por_adm = {}
    
    for tipo_pendencia, resultado in resultados_bitrix.items():
        for detalhe in resultado['detalhes_resolvidas']:
            responsavel = detalhe['Responsavel_Resolucao']
            if responsavel not in dados_bitrix_por_adm:
                dados_bitrix_por_adm[responsavel] = {
                    'total_resolvidas': 0,
                    'tempos_resolucao': []
                }
            
            dados_bitrix_por_adm[responsavel]['total_resolvidas'] += 1
            if detalhe['Tempo_Resolucao_Dias'] is not None:
                dados_bitrix_por_adm[responsavel]['tempos_resolucao'].append(detalhe['Tempo_Resolucao_Dias'])
    
    # Aplicar dados do Bitrix ao DataFrame consolidado
    for adm_nome in df_consolidado_adm.index:
        if adm_nome in dados_bitrix_por_adm:
            df_consolidado_adm.loc[adm_nome, 'Resolvidas (Bitrix)'] = dados_bitrix_por_adm[adm_nome]['total_resolvidas']
            
            if dados_bitrix_por_adm[adm_nome]['tempos_resolucao']:
                tempo_medio = np.mean(dados_bitrix_por_adm[adm_nome]['tempos_resolucao'])
                df_consolidado_adm.loc[adm_nome, 'Tempo Médio Bitrix (dias)'] = round(tempo_medio, 1)
    
    # 7. Calcular Taxas de Conversão para ambos os métodos
    # Taxa Supabase
    df_consolidado_adm['Total Pendências (Supabase)'] = df_consolidado_adm['Pendências Ativas'] + df_consolidado_adm['Resolvidas (Supabase)']
    df_consolidado_adm['Taxa Conversão Supabase (%)'] = (df_consolidado_adm['Resolvidas (Supabase)'] / df_consolidado_adm['Total Pendências (Supabase)'] * 100).round(1)
    df_consolidado_adm['Taxa Conversão Supabase (%)'] = df_consolidado_adm['Taxa Conversão Supabase (%)'].fillna(0)
    
    # Taxa Bitrix
    df_consolidado_adm['Total Pendências (Bitrix)'] = df_consolidado_adm['Pendências Ativas'] + df_consolidado_adm['Resolvidas (Bitrix)']
    df_consolidado_adm['Taxa Conversão Bitrix (%)'] = (df_consolidado_adm['Resolvidas (Bitrix)'] / df_consolidado_adm['Total Pendências (Bitrix)'] * 100).round(1)
    df_consolidado_adm['Taxa Conversão Bitrix (%)'] = df_consolidado_adm['Taxa Conversão Bitrix (%)'].fillna(0)
    
    # 8. Ordenar e preparar para exibição
    df_consolidado_adm = df_consolidado_adm.sort_values(by=['Pendências Ativas', 'Resolvidas (Bitrix)'], ascending=[False, False])
    
    # Reorganizar colunas para melhor visualização
    colunas_ordem_final = [
        'Pendências Ativas',
        'Resolvidas (Supabase)', 
        'Resolvidas (Bitrix)',
        'Taxa Conversão Supabase (%)',
        'Taxa Conversão Bitrix (%)',
        'Tempo Médio Supabase (dias)',
        'Tempo Médio Bitrix (dias)'
    ]
    
    df_consolidado_adm_display = df_consolidado_adm[colunas_ordem_final].copy()
    df_consolidado_adm_display = df_consolidado_adm_display.reset_index()
    
    # Aplicar filtro de ADM selecionado à tabela se não for "Todos os ADMs"
    if adm_selecionado != 'Todos os ADMs':
        df_consolidado_adm_display = df_consolidado_adm_display[df_consolidado_adm_display['ADM de Pasta'] == adm_selecionado]
    
    # Aplicar formatação para destacar diferenças entre métodos
    def highlight_comparacao_metodos(s):
        """Adiciona formatação comparando os dois métodos"""
        if 'Resolvidas (Supabase)' in s.name:
            return ['background-color: #E3F2FD' for _ in s]  # Azul claro para Supabase
        elif 'Resolvidas (Bitrix)' in s.name:
            return ['background-color: #E8F5E8' for _ in s]  # Verde claro para Bitrix
        elif 'Taxa Conversão Supabase' in s.name:
            return ['background-color: #E3F2FD' for _ in s]
        elif 'Taxa Conversão Bitrix' in s.name:
            return ['background-color: #E8F5E8' for _ in s]
        elif 'Tempo Médio Supabase' in s.name:
            return ['background-color: #E3F2FD' for _ in s]
        elif 'Tempo Médio Bitrix' in s.name:
            return ['background-color: #E8F5E8' for _ in s]
        return [''] * len(s)
    
    # Aplicar estilo à tabela
    styled_df_consolidado = df_consolidado_adm_display.style.apply(highlight_comparacao_metodos)
    
    # Formatar números decimais
    styled_df_consolidado = styled_df_consolidado.format({
        'Taxa Conversão Supabase (%)': '{:.1f}%',
        'Taxa Conversão Bitrix (%)': '{:.1f}%',
        'Tempo Médio Supabase (dias)': '{:.1f}',
        'Tempo Médio Bitrix (dias)': '{:.1f}'
    })
    
    st.markdown('<div class="producao-adm producao-adm__tabela">', unsafe_allow_html=True)
    st.dataframe(styled_df_consolidado, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.caption("""
    **Tabela Comparativa por ADM** - Comparação entre métodos Supabase e Bitrix
    - **🔵 Colunas Azuis**: Método Supabase (baseado em histórico de movimentações)
    - **🟢 Colunas Verdes**: Método Bitrix (baseado em campos de data específicos)
    - **Pendências Ativas**: Baseadas no ADM de Pasta atual
    - **Resolvidas**: Baseadas no Responsável pela movimentação/resolução
    - **Taxa de Conversão**: (Pendências Resolvidas ÷ Total de Pendências) × 100%
    """)
    
    # Adicionar análise das diferenças entre métodos por ADM
    if not df_consolidado_adm_display.empty:
        st.markdown("#### 📊 Comparação de Métodos por ADM")
        
        # Calcular estatísticas gerais de diferença
        df_temp = df_consolidado_adm_display.copy()
        df_temp['Diferença Resolvidas'] = df_temp['Resolvidas (Bitrix)'] - df_temp['Resolvidas (Supabase)']
        df_temp['Diferença Taxa (%)'] = df_temp['Taxa Conversão Bitrix (%)'] - df_temp['Taxa Conversão Supabase (%)']
        
        # Mostrar estatísticas resumidas
        total_dif_resolvidas = df_temp['Diferença Resolvidas'].sum()
        media_dif_taxa = df_temp['Diferença Taxa (%)'].mean()
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            if total_dif_resolvidas > 0:
                st.success(f"✅ **{total_dif_resolvidas:,}** resoluções a mais identificadas pelo método Bitrix")
            elif total_dif_resolvidas < 0:
                st.warning(f"⚠️ **{abs(total_dif_resolvidas):,}** resoluções a mais identificadas pelo método Supabase")
            else:
                st.info("📊 Ambos os métodos identificaram o mesmo total de resoluções")
        
        with col_stat2:
            if abs(media_dif_taxa) > 0.1:
                if media_dif_taxa > 0:
                    st.success(f"📈 Taxa média **{media_dif_taxa:.1f}%** maior no método Bitrix")
                else:
                    st.warning(f"📉 Taxa média **{abs(media_dif_taxa):.1f}%** maior no método Supabase")
            else:
                st.info("📊 Taxas médias similares entre os métodos")

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
        
        # Converter Data Resolução para string formatada para evitar problemas com o tipo temporal
        df_resol_por_dia['Data Formatada'] = pd.to_datetime(df_resol_por_dia['Data Resolução']).dt.strftime('%d/%m/%Y')
        
        # Importar Altair para gráficos
        import altair as alt
        
        # Criar gráfico de barras com linha de tendência
        barras = alt.Chart(df_resol_por_dia).mark_bar(
            color='#4CAF50',
            size=60  # Barras ainda mais largas
        ).encode(
            x=alt.X('Data Formatada:O', title='Data', sort=alt.SortField('Data Resolução')),
            y=alt.Y('Resoluções:Q', title='Quantidade de Resoluções'),
            tooltip=['Data Formatada:O', 'Resoluções:Q']
        )
        
        # Adicionar números em cima das barras
        texto = alt.Chart(df_resol_por_dia).mark_text(
            align='center',
            baseline='bottom',
            dy=-5,  # Deslocamento vertical (acima da barra)
            fontSize=16,
            fontWeight='bold'
        ).encode(
            x='Data Formatada:O',
            y='Resoluções:Q',
            text='Resoluções:Q'
        )
        
        # Combinar gráficos (apenas barras + texto)
        chart = (barras + texto).properties(
            title='Total de Resoluções Diárias (Todos os Dias do Período)',
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
    
    # --- NOVA ANÁLISE POR CAMPOS DO BITRIX ---
    st.markdown("### 📊 Análise por Campos de Data do Bitrix (Método Assertivo)")
    
    # Executar a análise por campos do Bitrix (se ainda não foi executada na seção anterior)
    if 'resultados_bitrix' not in locals():
        with st.spinner("Analisando pendências usando campos de data do Bitrix..."):
            resultados_bitrix = analisar_pendencias_por_campos_bitrix(
                df_bitrix=df,
                mapa_usuarios=mapa_usuarios,
                col_adm_pasta_bitrix=col_adm_pasta_bitrix,
                filtro_adm=adm_selecionado
            )
    
    # Criar tabela consolidada dos resultados do Bitrix
    dados_comparacao_bitrix = []
    total_resolvidas_bitrix = 0
    total_pendencias_bitrix = 0
    
    for tipo_pendencia, resultado in resultados_bitrix.items():
        # Pular se não for o tipo selecionado (quando um tipo específico for selecionado)
        if tipo_pendencia_selecionado != 'Todos os Tipos' and tipo_pendencia != tipo_pendencia_selecionado:
            continue
            
        dados_comparacao_bitrix.append({
            'Tipo de Pendência': tipo_pendencia,
            'Total com Pendência': resultado['total_com_pendencia'],
            'Total Resolvidas': resultado['total_resolvidas'],
            'Taxa de Resolução (%)': f"{resultado['taxa_resolucao']:.1f}%"
        })
        total_resolvidas_bitrix += resultado['total_resolvidas']
        total_pendencias_bitrix += resultado['total_com_pendencia']
    
    if dados_comparacao_bitrix:
        df_comparacao_bitrix = pd.DataFrame(dados_comparacao_bitrix)
        st.markdown("#### Resultados por Campos de Data do Bitrix:")
        st.dataframe(df_comparacao_bitrix, use_container_width=True)
        
        # Métricas totais do método Bitrix
        taxa_geral_bitrix = (total_resolvidas_bitrix / total_pendencias_bitrix * 100) if total_pendencias_bitrix > 0 else 0
        
        col_bit1, col_bit2, col_bit3 = st.columns(3)
        col_bit1.metric("Total Pendências (Bitrix)", f"{total_pendencias_bitrix:,}")
        col_bit2.metric("Total Resolvidas (Bitrix)", f"{total_resolvidas_bitrix:,}")
        col_bit3.metric("Taxa Resolução (Bitrix)", f"{taxa_geral_bitrix:.1f}%")
        
        st.caption("""
        **Método Bitrix**: Baseado nos campos de data específicos de cada etapa.
        - Mais assertivo pois usa as datas exatas registradas no Bitrix
        - Não depende do histórico do Supabase
        - Identifica pendências que foram resolvidas através das datas de etapas posteriores
        """)
    
    # --- COMPARAÇÃO DE MÉTODOS ---
    st.markdown("---")
    st.markdown("### ⚖️ Comparação entre Métodos")
    
    # Calcular totais do método Supabase para comparação
    total_resolvidas_supabase = total_pendencias_resolvidas  # Já calculado anteriormente
    total_pendencias_supabase = total_pendencias_ativas + total_pendencias_resolvidas
    taxa_geral_supabase = percentual_resolucao  # Já calculado anteriormente
    
    # Criar tabela de comparação
    dados_comparacao_geral = [
        {
            'Método': 'Supabase (Histórico)',
            'Total Pendências': total_pendencias_supabase,
            'Total Resolvidas': total_resolvidas_supabase,
            'Taxa de Resolução (%)': f"{taxa_geral_supabase:.1f}%",
            'Observações': 'Baseado em movimentações históricas'
        },
        {
            'Método': 'Bitrix (Campos de Data)',
            'Total Pendências': total_pendencias_bitrix,
            'Total Resolvidas': total_resolvidas_bitrix,
            'Taxa de Resolução (%)': f"{taxa_geral_bitrix:.1f}%",
            'Observações': 'Baseado em campos de data específicos'
        }
    ]
    
    df_comparacao_geral = pd.DataFrame(dados_comparacao_geral)
    
    # Aplicar destaque para o método com maior número de resoluções
    def highlight_melhor_metodo(s):
        if s.name == 'Total Resolvidas':
            max_val = s.max()
            return ['background-color: #4CAF50; color: white; font-weight: bold' if v == max_val else '' for v in s]
        return [''] * len(s)
    
    styled_comparacao = df_comparacao_geral.style.apply(highlight_melhor_metodo)
    st.dataframe(styled_comparacao, use_container_width=True)
    
    # Mostrar diferença entre métodos
    diferenca_resolvidas = total_resolvidas_bitrix - total_resolvidas_supabase
    diferenca_taxa = taxa_geral_bitrix - taxa_geral_supabase
    
    if diferenca_resolvidas != 0 or abs(diferenca_taxa) > 0.1:
        st.markdown("#### 📈 Análise das Diferenças:")
        
        col_dif1, col_dif2 = st.columns(2)
        with col_dif1:
            if diferenca_resolvidas > 0:
                st.success(f"✅ Método Bitrix identificou **{diferenca_resolvidas:,}** resoluções a mais")
            elif diferenca_resolvidas < 0:
                st.warning(f"⚠️ Método Supabase identificou **{abs(diferenca_resolvidas):,}** resoluções a mais")
            else:
                st.info("📊 Ambos os métodos identificaram o mesmo número de resoluções")
        
        with col_dif2:
            if abs(diferenca_taxa) > 0.1:
                if diferenca_taxa > 0:
                    st.success(f"📊 Taxa de resolução **{diferenca_taxa:.1f}%** maior no método Bitrix")
                else:
                    st.warning(f"📊 Taxa de resolução **{abs(diferenca_taxa):.1f}%** maior no método Supabase")
    
    # 7. Exibir detalhes de cada tipo de pendência em expansores
    st.markdown('<div class="adm-detalhes-pendencia">', unsafe_allow_html=True)
    
    # Mostrar detalhes do método Supabase (original)
    if not df_supabase.empty:
        st.markdown("### 📋 Detalhamento - Método Supabase (Histórico)")
        for tipo_pendencia in ESTAGIOS_DEVOLUCAO_ADM:
            # Pular se não for o tipo selecionado (quando um tipo específico for selecionado)
            if tipo_pendencia_selecionado != 'Todos os Tipos' and tipo_pendencia != tipo_pendencia_selecionado:
                continue
                
            with st.expander(f"Supabase: {tipo_pendencia}", expanded=False):
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
    
    # Mostrar detalhes do método Bitrix (novo)
    st.markdown("### 📋 Detalhamento - Método Bitrix (Campos de Data)")
    for tipo_pendencia in ESTAGIOS_DEVOLUCAO_ADM:
        # Pular se não for o tipo selecionado (quando um tipo específico for selecionado)
        if tipo_pendencia_selecionado != 'Todos os Tipos' and tipo_pendencia != tipo_pendencia_selecionado:
            continue
            
        with st.expander(f"Bitrix: {tipo_pendencia}", expanded=False):
            if tipo_pendencia in resultados_bitrix:
                resultado = resultados_bitrix[tipo_pendencia]
                
                # Mostrar métricas
                col_met1, col_met2, col_met3 = st.columns(3)
                col_met1.metric("Total com Pendência", f"{resultado['total_com_pendencia']:,}")
                col_met2.metric("Total Resolvidas", f"{resultado['total_resolvidas']:,}")
                col_met3.metric("Taxa de Resolução", f"{resultado['taxa_resolucao']:.1f}%")
                
                # Mostrar detalhes das resolvidas
                if resultado['detalhes_resolvidas']:
                    st.markdown("**Detalhes das Pendências Resolvidas:**")
                    
                    df_detalhes = pd.DataFrame(resultado['detalhes_resolvidas'])
                    
                    # Formatar colunas para exibição
                    df_detalhes_display = df_detalhes.copy()
                    
                    if 'Data_Entrada_Pendencia' in df_detalhes_display.columns:
                        df_detalhes_display['Data Entrada Pendência'] = pd.to_datetime(df_detalhes_display['Data_Entrada_Pendencia']).dt.strftime('%d/%m/%Y %H:%M')
                    
                    if 'Data_Resolucao' in df_detalhes_display.columns:
                        df_detalhes_display['Data Resolução'] = pd.to_datetime(df_detalhes_display['Data_Resolucao']).dt.strftime('%d/%m/%Y %H:%M')
                    
                    if 'Tempo_Resolucao_Dias' in df_detalhes_display.columns:
                        df_detalhes_display['Tempo Resolução (dias)'] = df_detalhes_display['Tempo_Resolucao_Dias'].round(1)
                    
                    # Renomear colunas para exibição
                    colunas_rename = {
                        'Responsavel_Resolucao': 'Responsável Resolução',
                        'ADM_Pasta': 'ADM de Pasta',
                        'Estagio_Resolucao': 'Estágio de Resolução'
                    }
                    df_detalhes_display = df_detalhes_display.rename(columns=colunas_rename)
                    
                    # Selecionar colunas para exibição
                    colunas_exibir = ['ID', 'Responsável Resolução', 'Data Entrada Pendência', 'Data Resolução', 'Tempo Resolução (dias)', 'ADM de Pasta']
                    colunas_existentes = [col for col in colunas_exibir if col in df_detalhes_display.columns]
                    
                    st.dataframe(df_detalhes_display[colunas_existentes], use_container_width=True)
                    
                    # Estatísticas de tempo
                    if 'Tempo_Resolucao_Dias' in df_detalhes.columns and not df_detalhes['Tempo_Resolucao_Dias'].isna().all():
                        tempos_validos = df_detalhes['Tempo_Resolucao_Dias'].dropna()
                        if len(tempos_validos) > 0:
                            col_stat1, col_stat2, col_stat3 = st.columns(3)
                            col_stat1.metric("Tempo Mínimo", f"{tempos_validos.min():.1f} dias")
                            col_stat2.metric("Tempo Médio", f"{tempos_validos.mean():.1f} dias")
                            col_stat3.metric("Tempo Máximo", f"{tempos_validos.max():.1f} dias")
                else:
                    st.info("Nenhuma pendência resolvida identificada pelos campos de data.")
            else:
                st.info("Não foram encontrados dados para este tipo de pendência.")
    
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

def analisar_pendencias_por_campos_bitrix(df_bitrix, mapa_usuarios, col_adm_pasta_bitrix, filtro_adm='Todos os ADMs'):
    """
    Analisa pendências usando os campos de data específicos do Bitrix.
    Método mais assertivo que complementa a análise do Supabase.
    """
    resultados = {}
    
    for estagio_pendencia, config in MAPEAMENTO_ESTAGIOS_CAMPOS_DATA.items():
        resultado_estagio = {
            'total_com_pendencia': 0,
            'total_resolvidas': 0,
            'detalhes_resolvidas': [],
            'taxa_resolucao': 0
        }
        
        campo_data_entrada = config['campo_data_entrada']
        campos_data_resolucao = config['estagios_resolucao']
        campos_responsavel_resolucao = config['responsaveis_resolucao']
        
        # Se não tem campo de data de entrada, usar estágio atual
        if campo_data_entrada and campo_data_entrada in df_bitrix.columns:
            # Cards que passaram por esta pendência (tem data preenchida)
            df_com_pendencia = df_bitrix[df_bitrix[campo_data_entrada].notna()].copy()
        else:
            # Cards que estão atualmente nesta pendência
            df_com_pendencia = df_bitrix[df_bitrix['ESTAGIO_ATUAL_LEGIVEL'] == estagio_pendencia].copy()
        
        resultado_estagio['total_com_pendencia'] = len(df_com_pendencia)
        
        if df_com_pendencia.empty:
            resultados[estagio_pendencia] = resultado_estagio
            continue
        
        # Verificar resoluções
        for _, row in df_com_pendencia.iterrows():
            data_entrada_pendencia = None
            if campo_data_entrada and campo_data_entrada in row.index:
                data_entrada_pendencia = row[campo_data_entrada]
            
            # Verificar se foi resolvida (tem data posterior em algum estágio de resolução)
            foi_resolvida = False
            data_resolucao = None
            responsavel_resolucao = None
            estagio_resolucao = None
            
            for i, campo_resolucao in enumerate(campos_data_resolucao):
                if campo_resolucao in row.index and pd.notna(row[campo_resolucao]):
                    data_campo_resolucao = pd.to_datetime(row[campo_resolucao])
                    
                    # Se não temos data de entrada, considera como resolvida
                    if data_entrada_pendencia is None:
                        foi_resolvida = True
                        data_resolucao = data_campo_resolucao
                        estagio_resolucao = campo_resolucao
                        
                        # Buscar responsável correspondente
                        if i < len(campos_responsavel_resolucao):
                            campo_resp = campos_responsavel_resolucao[i]
                            if campo_resp in row.index and pd.notna(row[campo_resp]):
                                responsavel_resolucao = row[campo_resp]
                        break
                    else:
                        # Verificar se a data de resolução é posterior à entrada
                        data_entrada_pd = pd.to_datetime(data_entrada_pendencia)
                        if data_campo_resolucao > data_entrada_pd:
                            foi_resolvida = True
                            data_resolucao = data_campo_resolucao
                            estagio_resolucao = campo_resolucao
                            
                            # Buscar responsável correspondente
                            if i < len(campos_responsavel_resolucao):
                                campo_resp = campos_responsavel_resolucao[i]
                                if campo_resp in row.index and pd.notna(row[campo_resp]):
                                    responsavel_resolucao = row[campo_resp]
                            break
            
            if foi_resolvida:
                # Mapear responsável para nome
                nome_responsavel = 'N/A'
                if responsavel_resolucao:
                    responsavel_str = str(responsavel_resolucao)
                    nome_responsavel = mapa_usuarios.get(responsavel_str, 
                                                       mapa_usuarios.get(f"user_{responsavel_str}", 
                                                                        responsavel_str))
                
                # Aplicar filtro de ADM se especificado
                if filtro_adm != 'Todos os ADMs' and nome_responsavel != filtro_adm:
                    continue
                
                # Calcular tempo de resolução
                tempo_resolucao = None
                if data_entrada_pendencia and data_resolucao:
                    tempo_resolucao = (data_resolucao - pd.to_datetime(data_entrada_pendencia)).total_seconds() / (24 * 60 * 60)
                
                detalhe = {
                    'ID': row.get('ID', 'N/A'),
                    'ADM_Pasta': row.get(col_adm_pasta_bitrix, 'N/A'),
                    'Data_Entrada_Pendencia': data_entrada_pendencia,
                    'Data_Resolucao': data_resolucao,
                    'Responsavel_Resolucao': nome_responsavel,
                    'ID_Responsavel_Resolucao': responsavel_resolucao,
                    'Estagio_Resolucao': estagio_resolucao,
                    'Tempo_Resolucao_Dias': tempo_resolucao
                }
                resultado_estagio['detalhes_resolvidas'].append(detalhe)
        
        resultado_estagio['total_resolvidas'] = len(resultado_estagio['detalhes_resolvidas'])
        
        # Calcular taxa de resolução
        if resultado_estagio['total_com_pendencia'] > 0:
            resultado_estagio['taxa_resolucao'] = (resultado_estagio['total_resolvidas'] / resultado_estagio['total_com_pendencia']) * 100
        
        resultados[estagio_pendencia] = resultado_estagio
    
    return resultados 