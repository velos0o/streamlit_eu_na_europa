import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from api.bitrix_connector import load_bitrix_data, get_credentials
import re
import io
import requests
import traceback

# Carregar variáveis de ambiente
load_dotenv()

def carregar_dados_cartorio():
    """
    Carrega os dados dos cartórios Casa Verde e Tatuápe
    
    Returns:
        pandas.DataFrame: DataFrame com os dados filtrados dos cartórios
    """
    try:
        # Logs detalhados
        debug_info = {}
        
        # Obter token do Bitrix24
        try:
            from api.bitrix_connector import get_credentials
            BITRIX_TOKEN, BITRIX_URL = get_credentials()
            debug_info["credentials"] = "obtidas"
        except Exception as cred_error:
            if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
                st.error(f"❌ Erro ao obter credenciais: {str(cred_error)}")
                st.code(traceback.format_exc())
            debug_info["credentials_error"] = str(cred_error)
            return pd.DataFrame()
        
        # Verificar se temos as credenciais necessárias
        if not BITRIX_TOKEN or not BITRIX_URL:
            if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
                st.error("🔑 Credenciais do Bitrix24 não encontradas ou inválidas")
            debug_info["credentials_valid"] = False
            return pd.DataFrame()
        else:
            debug_info["credentials_valid"] = True
        
        # URL para acessar a tabela crm_dynamic_items_1052
        url_items = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1052"
        debug_info["url_constructed"] = True
        
        # Contornar possíveis problemas de codificação URL
        safe_url = url_items.replace(" ", "%20")
        
        # Adicionar log de depuração
        if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
            token_masked = f"{BITRIX_TOKEN[:5]}...{BITRIX_TOKEN[-3:]}" if len(BITRIX_TOKEN) > 8 else "***"
            st.info(f"🔗 Tentando acessar: {BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={token_masked}&table=crm_dynamic_items_1052")
        
        # Fazer requisição manual para diagnóstico detalhado
        if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
            try:
                # Tentar acessar a API diretamente para diagnóstico
                st.info("Realizando requisição de diagnóstico...")
                
                # Adicionar cabeçalhos completos
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "*/*",
                    "Content-Type": "application/json",
                    "Accept-Encoding": "gzip, deflate, br"
                }
                
                # Usar a biblioteca requests para diagnóstico
                with st.spinner("Testando acesso à API..."):
                    test_response = requests.get(safe_url, headers=headers, timeout=30)
                    st.write(f"Status da resposta: {test_response.status_code}")
                    
                    # Mostrar cabeçalhos da resposta
                    st.write("Cabeçalhos da resposta:", dict(test_response.headers))
                    
                    # Verificar se o conteúdo pode ser interpretado como JSON
                    try:
                        json_data = test_response.json()
                        st.success("✅ Resposta decodificada como JSON com sucesso")
                        if isinstance(json_data, list):
                            st.write(f"Número de itens na resposta: {len(json_data)}")
                        debug_info["test_response_valid"] = True
                    except Exception as json_error:
                        st.error(f"❌ Erro ao decodificar resposta como JSON: {str(json_error)}")
                        st.code(test_response.text[:500] + "..." if len(test_response.text) > 500 else test_response.text)
                        debug_info["test_response_valid"] = False
                        debug_info["json_error"] = str(json_error)
                
            except Exception as request_error:
                st.error(f"❌ Erro na requisição de diagnóstico: {str(request_error)}")
                st.code(traceback.format_exc())
                debug_info["request_error"] = str(request_error)
        
        # Carregar os dados com ou sem exibição de logs conforme o modo de depuração
        show_logs = 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']
        try:
            from api.bitrix_connector import load_bitrix_data
            df_items = load_bitrix_data(safe_url, show_logs=show_logs)
            debug_info["load_data_called"] = True
        except Exception as load_error:
            if show_logs:
                st.error(f"❌ Erro ao carregar dados com load_bitrix_data: {str(load_error)}")
                st.code(traceback.format_exc())
            debug_info["load_error"] = str(load_error)
            return pd.DataFrame()
        
        # Se o DataFrame estiver vazio, retornar DataFrame vazio
        if df_items is None or df_items.empty:
            if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
                st.error("📊 Não foram encontrados dados na tabela crm_dynamic_items_1052")
            debug_info["df_empty"] = True
            return pd.DataFrame()
        else:
            debug_info["df_empty"] = False
        
        # Adicionar log de depuração
        if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
            st.success(f"✅ Dados carregados com sucesso: {len(df_items)} registros")
            st.write("Colunas disponíveis:", df_items.columns.tolist())
            debug_info["df_columns"] = df_items.columns.tolist()
        
        # Verificar se a coluna CATEGORY_ID existe
        if 'CATEGORY_ID' not in df_items.columns:
            if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
                st.error("❌ Coluna CATEGORY_ID não encontrada nos dados recebidos")
                st.write("Colunas disponíveis:", df_items.columns.tolist())
            debug_info["category_id_missing"] = True
            return pd.DataFrame()
        else:
            debug_info["category_id_missing"] = False
        
        # Filtrar apenas os cartórios Casa Verde (16) e Tatuápe (34)
        df_filtrado = df_items[df_items['CATEGORY_ID'].isin([16, 34])].copy()  # Usar .copy() para evitar SettingWithCopyWarning
        
        # Adicionar log de depuração
        if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
            st.success(f"✅ Dados filtrados: {len(df_filtrado)} registros após filtro de cartórios")
            debug_info["filtered_records"] = len(df_filtrado)
        
        # Adicionar o nome do cartório para melhor visualização
        df_filtrado.loc[:, 'NOME_CARTORIO'] = df_filtrado['CATEGORY_ID'].map({
            16: 'CARTÓRIO CASA VERDE',
            34: 'CARTÓRIO TATUÁPE'
        })
        
        # Armazenar informações de depuração na sessão
        if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
            st.session_state['DEBUG_INFO'] = debug_info
            
        return df_filtrado
    
    except Exception as e:
        # Log de erro detalhado no modo de depuração
        if 'BITRIX_DEBUG' in st.session_state and st.session_state['BITRIX_DEBUG']:
            st.error(f"❌ Erro geral ao carregar dados do cartório: {str(e)}")
            st.code(traceback.format_exc())
            
            # Criar um relatório de diagnóstico completo
            st.error("Relatório de Diagnóstico")
            
            # Versão do Python e bibliotecas
            import sys
            import pandas as pd
            import streamlit as st
            import requests
            
            diagnostic_report = {
                "python_version": sys.version,
                "streamlit_version": st.__version__,
                "pandas_version": pd.__version__,
                "requests_version": requests.__version__,
                "error": str(e),
                "error_type": type(e).__name__
            }
            
            # Exibir relatório
            for key, value in diagnostic_report.items():
                st.text(f"{key}: {value}")
                
            # Armazenar relatório na sessão
            st.session_state['ERROR_DIAGNOSTIC'] = diagnostic_report
        else:
            st.error("Não foi possível carregar os dados dos cartórios. Ative o modo de depuração para mais detalhes.")
        
        return pd.DataFrame()

def criar_visao_geral_cartorio(df):
    """
    Cria uma visão geral dos cartórios com os estágios como colunas
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos cartórios
        
    Returns:
        pandas.DataFrame: DataFrame pivotado com os estágios como colunas
    """
    if df.empty:
        return pd.DataFrame()
    
    # Verificar se temos o stage_name diretamente nos dados ou se precisamos obtê-lo
    if 'STAGE_NAME' not in df.columns:
        # Verificar se temos stage_id para fazer o mapeamento
        if 'STAGE_ID' not in df.columns:
            st.error("Colunas STAGE_ID ou STAGE_NAME não encontradas.")
            st.write("Colunas disponíveis:", df.columns.tolist())
            return pd.DataFrame()
        
        # Obter token e URL do Bitrix24
        BITRIX_TOKEN, BITRIX_URL = get_credentials()
        
        # Obter estágios únicos do pipeline para mapear nomes
        url_stages = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_status"
        df_stages = load_bitrix_data(url_stages)
        
        # Lista dos estágios específicos para exibir (IDs)
        estagios_especificos = [
            'DT1052_16:FAIL',
            'DT1052_16:NEW',
            'DT1052_16:SUCCESS',
            'DT1052_16:UC_7F0WK2',
            'DT1052_16:UC_HYO7L2',
            'DT1052_16:UC_JRGCW3',
            'DT1052_16:UC_KXHDOQ',
            'DT1052_16:UC_P61ZVH',
            'DT1052_16:UC_R5UEXF'
        ]
        
        # Criar mapeamento de STAGE_ID para nome do estágio
        stage_mapping = {}
        
        # Filtrar apenas os estágios dos pipelines de cartório
        if not df_stages.empty and 'STATUS_ID' in df_stages.columns and 'NAME' in df_stages.columns:
            # Filtrar estágios relacionados aos pipelines de cartório
            df_stages_filtered = df_stages[df_stages['STATUS_ID'].isin(estagios_especificos)]
            
            # Criar um mapeamento de STAGE_ID para nome do estágio
            stage_mapping = dict(zip(df_stages_filtered['STATUS_ID'], df_stages_filtered['NAME']))
        
        # Se não conseguiu obter nomes dos estágios, usar os IDs originais sem o prefixo
        for estagio in estagios_especificos:
            if estagio not in stage_mapping:
                # Extrair apenas o nome sem o prefixo (tudo após o ":")
                nome_simplificado = estagio.split(':')[-1]
                stage_mapping[estagio] = nome_simplificado
        
        # Adicionar a coluna STAGE_NAME mapeada a partir do STAGE_ID
        df['STAGE_NAME'] = df['STAGE_ID'].map(stage_mapping)
        
        # Se após o mapeamento ainda tiver valores nulos, usar o STAGE_ID original
        df['STAGE_NAME'] = df['STAGE_NAME'].fillna(df['STAGE_ID'])
    
    # Lista dos nomes de estágios que queremos exibir
    # Se não tivermos os IDs específicos, vamos verificar nos dados existentes
    if 'STAGE_NAME' in df.columns:
        estagios_disponiveis = df['STAGE_NAME'].unique().tolist()
        stage_names_especificos = [
            'FAIL', 'NEW', 'SUCCESS', 'UC_7F0WK2', 'UC_HYO7L2', 
            'UC_JRGCW3', 'UC_KXHDOQ', 'UC_P61ZVH', 'UC_R5UEXF'
        ]
        
        # Filtrar apenas os estágios que realmente existem nos dados
        estagios_para_exibir = []
        for estagio in estagios_disponiveis:
            # Verificar se o estágio corresponde a algum dos específicos (comparando finais de string)
            for estagio_especifico in stage_names_especificos:
                if estagio.endswith(estagio_especifico):
                    estagios_para_exibir.append(estagio)
                    break
        
        # Se não encontramos nenhum estágio específico, usar todos os disponíveis
        if not estagios_para_exibir:
            estagios_para_exibir = estagios_disponiveis
    else:
        estagios_para_exibir = []
    
    # Contar registros por responsável e estágio
    if not df.empty and 'ASSIGNED_BY_NAME' in df.columns and 'STAGE_NAME' in df.columns:
        contagem = df.groupby(['ASSIGNED_BY_NAME', 'STAGE_NAME', 'NOME_CARTORIO']).size().reset_index(name='TOTAL')
        
        # Filtrar apenas os estágios específicos se tivermos algum
        if estagios_para_exibir:
            contagem = contagem[contagem['STAGE_NAME'].isin(estagios_para_exibir)]
        
        # Criar a tabela pivotada com estágios como colunas
        pivot_table = contagem.pivot_table(
            index=['ASSIGNED_BY_NAME', 'NOME_CARTORIO'],
            columns='STAGE_NAME',
            values='TOTAL',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Calcular totais por responsável
        pivot_table['TOTAL'] = pivot_table.iloc[:, 2:].sum(axis=1)
        
        # Adicionar percentual baseado nos estágios SUCCESS
        # Verificar se temos estágios SUCCESS nos dados
        success_columns = []
        for col in pivot_table.columns:
            if isinstance(col, str) and ':SUCCESS' in col:
                success_columns.append(col)
        
        # Se encontramos alguma coluna SUCCESS, calcular o percentual
        if success_columns:
            # Somar todos os SUCCESS para cada linha
            pivot_table['TOTAL_SUCCESS'] = 0
            for col in success_columns:
                pivot_table['TOTAL_SUCCESS'] += pivot_table[col]
            
            # Calcular percentual (Total / Total_SUCCESS)
            pivot_table['PERCENTUAL_CONVERSAO'] = 0.0
            mask = pivot_table['TOTAL_SUCCESS'] > 0
            pivot_table.loc[mask, 'PERCENTUAL_CONVERSAO'] = (pivot_table.loc[mask, 'TOTAL'] / pivot_table.loc[mask, 'TOTAL_SUCCESS'] * 100).round(2)
        
        return pivot_table
    else:
        st.error("Colunas necessárias não encontradas para criar a visão geral.")
        if not df.empty:
            st.write("Colunas disponíveis:", df.columns.tolist())
        return pd.DataFrame()

def analyze_cartorio_ids(df):
    """
    Analisa os IDs de família no DataFrame para cartórios e retorna o resumo e detalhes
    """
    if 'UF_CRM_12_1723552666' not in df.columns:
        return pd.DataFrame(), pd.DataFrame()
    
    # Função para verificar se o ID está no padrão correto
    def check_id_pattern(id_str):
        # Verificar todos os tipos possíveis de valores vazios
        if pd.isna(id_str) or id_str == '' or id_str is None or (isinstance(id_str, str) and id_str.strip() == ''):
            return 'Vazio'
        if not isinstance(id_str, str):
            return 'Formato Inválido'
        # Remover espaços em branco antes de verificar o padrão
        id_str = id_str.strip()
        pattern = r'^\d+x\d+$'
        if re.match(pattern, id_str):
            return 'Padrão Correto'
        return 'Formato Inválido'

    # Criar uma cópia do DataFrame para análise
    analysis_df = df.copy()
    
    # Primeiro, identificar registros vazios
    analysis_df['ID_STATUS'] = analysis_df['UF_CRM_12_1723552666'].apply(check_id_pattern)
    
    # Depois, identificar duplicados apenas entre os registros não vazios e com formato válido
    validos_mask = (analysis_df['ID_STATUS'] == 'Padrão Correto')
    
    # Criar uma série temporária apenas com os IDs válidos para verificar duplicados
    ids_validos = analysis_df.loc[validos_mask, 'UF_CRM_12_1723552666'].str.strip()
    duplicados_mask = ids_validos.duplicated(keep=False)
    
    # Marcar duplicados apenas nos registros válidos que estão duplicados
    analysis_df.loc[ids_validos[duplicados_mask].index, 'ID_STATUS'] = 'Duplicado'
    
    # Criar resumo
    summary = pd.DataFrame({
        'Status': ['Padrão Correto', 'Duplicado', 'Vazio', 'Formato Inválido'],
        'Quantidade': [
            sum((analysis_df['ID_STATUS'] == 'Padrão Correto')),
            sum((analysis_df['ID_STATUS'] == 'Duplicado')),
            sum((analysis_df['ID_STATUS'] == 'Vazio')),
            sum((analysis_df['ID_STATUS'] == 'Formato Inválido'))
        ]
    })
    
    # Criar detalhamento
    details = analysis_df[[
        'ID',
        'TITLE',
        'UF_CRM_12_1723552666',
        'ASSIGNED_BY_NAME',
        'NOME_CARTORIO',
        'ID_STATUS'
    ]].copy()
    
    details = details.rename(columns={
        'ID': 'ID',
        'TITLE': 'Nome',
        'UF_CRM_12_1723552666': 'ID Família',
        'ASSIGNED_BY_NAME': 'Responsável',
        'NOME_CARTORIO': 'Cartório',
        'ID_STATUS': 'Status do ID'
    })
    
    # Ordenar o detalhamento por Status do ID, Cartório e Responsável
    details = details.sort_values(['Status do ID', 'Cartório', 'Responsável'])
    
    return summary, details

def visualizar_cartorio_dados(df):
    """
    Visualiza os dados detalhados dos cartórios.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos cartórios
    """
    if df.empty:
        st.warning("Não há dados disponíveis para visualização.")
        return
    
    # Verificar se temos as colunas necessárias
    colunas_necessarias = ['STAGE_ID', 'ASSIGNED_BY_ID', 'ASSIGNED_BY_NAME']
    
    colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
    if colunas_faltantes:
        st.error(f"Colunas necessárias não encontradas: {', '.join(colunas_faltantes)}")
        st.write("Colunas disponíveis:", df.columns.tolist())
        return
    
    # Obter token e URL do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # Obter estágios únicos do pipeline
    url_stages = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_status"
    df_stages = load_bitrix_data(url_stages)
    
    # Filtrar apenas os estágios dos pipelines de cartório
    if 'ENTITY_ID' in df_stages.columns and 'STATUS_ID' in df_stages.columns and 'NAME' in df_stages.columns:
        # Encontrar os pipelines corretos
        pipeline_entities = df_stages[df_stages['NAME'].str.contains('CARTÓRIO', case=False, na=False)]['ENTITY_ID'].unique()
        
        # Filtrar estágios desses pipelines
        df_stages_filtered = df_stages[df_stages['ENTITY_ID'].isin(pipeline_entities)]
        
        # Criar um mapeamento de STAGE_ID para nome do estágio
        stage_mapping = dict(zip(df_stages_filtered['STATUS_ID'], df_stages_filtered['NAME']))
        
        # Adicionar nome do estágio ao DataFrame principal
        df['STAGE_NAME'] = df['STAGE_ID'].map(stage_mapping)
    else:
        # Caso não consiga obter o nome dos estágios, usar o ID
        df['STAGE_NAME'] = df['STAGE_ID']
    
    # Limpar todos os estilos anteriores para evitar conflitos
    st.markdown("""
    <style>
    .section-title {
        font-size: 24px;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 20px;
        color: #333;
        border-bottom: 2px solid #4285f4;
        padding-bottom: 10px;
    }
    .section-subtitle {
        font-size: 20px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 15px;
        color: #555;
        border-left: 4px solid #34a853;
        padding-left: 10px;
    }
    </style>
    <div class="section-title">Dados Detalhados dos Cartórios</div>
    """, unsafe_allow_html=True)

    # Verificar se o DataFrame está vazio
    if df.empty:
        st.warning("Não há dados disponíveis para exibição com os filtros selecionados.")
    else:
        # Contar total de processos na etapa SUCCESS
        success_count = 0
        
        # Definir todos os códigos que representam SUCCESS
        success_codes = [
            'SUCCESS', 
            'DT1052_16:SUCCESS', 
            'DT1052_34:SUCCESS'
        ]
        
        # Verificar quais colunas estão disponíveis
        success_columns = []
        if 'STAGE_NAME' in df.columns:
            success_columns.append('STAGE_NAME')
        if 'STAGE_ID' in df.columns:
            success_columns.append('STAGE_ID')
            
        # Se encontramos alguma coluna para verificar
        if success_columns:
            # Criar um filtro combinado para encontrar SUCCESS em qualquer coluna disponível
            success_mask = pd.Series(False, index=df.index)
            
            for column in success_columns:
                for code in success_codes:
                    # Verificar correspondência exata com os códigos de sucesso
                    success_mask = success_mask | (df[column] == code)
                    # Verificar também se contém o código (para caso de textos mais longos)
                    success_mask = success_mask | df[column].str.contains(f":{code}$", regex=True, na=False)
            
            # Contar registros que satisfazem o filtro
            success_count = df[success_mask].shape[0]
        else:
            st.warning("Não foi possível identificar processos concluídos (colunas STAGE_NAME e STAGE_ID não encontradas)")
        
        # Criar contêineres simples com cores de fundo diretas
        col1, col2, col3 = st.columns(3)
        
        # Usar uma abordagem mais simples com divs HTML
        with col1:
            st.markdown("""
            <div style="background-color: #f0f7ff; padding: 15px; border-radius: 10px; border-left: 5px solid #4285f4; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0; color: #1967d2; font-size: 16px;">Total de Cartórios</h3>
                <p style="font-size: 24px; font-weight: bold; margin: 0;">{}</p>
            </div>
            """.format(
                len(df['NOME_CARTORIO'].unique())
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background-color: #f0fff7; padding: 15px; border-radius: 10px; border-left: 5px solid #34a853; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0; color: #188038; font-size: 16px;">Total de Processos</h3>
                <p style="font-size: 24px; font-weight: bold; margin: 0;">{}</p>
            </div>
            """.format(
                len(df)
            ), unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #4caf50; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0; color: #2e7d32; font-size: 16px;">Total de Processos Concluídos (SUCCESS)</h3>
                <p style="font-size: 24px; font-weight: bold; margin: 0;">{}</p>
            </div>
            """.format(
                success_count
            ), unsafe_allow_html=True)
        
        # Métricas por estágio
        st.markdown('<div class="section-subtitle">Métricas por Estágio</div>', unsafe_allow_html=True)
        
        # Usar nomes mais legíveis para os estágios
        def simplificar_nome_estagio(nome):
            if pd.isna(nome):
                return "Desconhecido"
            
            # Se o nome contém dois pontos, pegar a parte depois dos dois pontos
            if isinstance(nome, str) and ':' in nome:
                codigo_estagio = nome
            else:
                codigo_estagio = nome  # Usar o nome completo como código
            
            # Mapeamento completo dos códigos para nomes legíveis e curtos
            # EM ANDAMENTO
            em_andamento = {
                'DT1052_16:NEW': 'Aguardando Certidão',
                'DT1052_34:NEW': 'Aguardando Certidão',
                'DT1052_16:UC_QRZ6JG': 'Busca CRC',
                'DT1052_34:UC_68BLQ7': 'Busca CRC',
                'DT1052_16:UC_7F0WK2': 'Solicitar Requerimento',
                'DT1052_34:UC_HN9GMI': 'Solicitar Requerimento',
                'DT1052_16:PREPARATION': 'Montagem Requerimento',
                'DT1052_34:PREPARATION': 'Montagem Requerimento',
                'DT1052_16:UC_IWZBMO': 'Solicitar Cart. Origem',
                'DT1052_34:CLIENT': 'Certidão Emitida',
                'DT1052_34:UC_8L5JUS': 'Solicitar Cart. Origem',
                'DT1052_16:UC_8EGMU7': 'Cart. Origem Prioridade',
                'DT1052_16:UC_KXHDOQ': 'Aguard. Cart. Origem',
                'DT1052_34:UC_6KOYL5': 'Aguard. Cart. Origem',
                'DT1052_16:CLIENT': 'Certidão Emitida',
                'DT1052_34:UC_D0RG5P': 'Certidão Emitida',
                'DT1052_16:UC_JRGCW3': 'Certidão Física',
                'DT1052_34:UC_84B1S2': 'Certidão Física',
                # Versões curtas dos nomes (sem prefixo)
                'NEW': 'Aguard. Certidão',
                'PREPARATION': 'Mont. Requerim.',
                'CLIENT': 'Certidão Emitida',
                'UC_QRZ6JG': 'Busca CRC',
                'UC_68BLQ7': 'Busca CRC',
                'UC_7F0WK2': 'Solic. Requerim.',
                'UC_HN9GMI': 'Solic. Requerim.',
                'UC_IWZBMO': 'Solic. C. Origem',
                'UC_8L5JUS': 'Solic. C. Origem',
                'UC_8EGMU7': 'C. Origem Prior.',
                'UC_KXHDOQ': 'Aguard. C. Origem',
                'UC_6KOYL5': 'Aguard. C. Origem',
                'UC_D0RG5P': 'Certidão Emitida',
                'UC_JRGCW3': 'Certidão Física',
                'UC_84B1S2': 'Certidão Física'
            }
            
            # SUCESSO
            sucesso = {
                'DT1052_16:SUCCESS': 'Certidão Entregue',
                'DT1052_34:SUCCESS': 'Certidão Entregue',
                'SUCCESS': 'Certidão Entregue'
            }
            
            # FALHA
            falha = {
                'DT1052_16:FAIL': 'Devolução ADM',
                'DT1052_34:FAIL': 'Devolução ADM',
                'DT1052_16:UC_R5UEXF': 'Dev. ADM Verificado',
                'DT1052_34:UC_Z3J98J': 'Dev. ADM Verificado',
                'DT1052_16:UC_HYO7L2': 'Devolutiva Busca',
                'DT1052_34:UC_5LAJNY': 'Devolutiva Busca',
                'DT1052_16:UC_UG0UDZ': 'Solicitação Duplicada',
                'DT1052_34:UC_LF04SU': 'Solicitação Duplicada',
                'DT1052_16:UC_P61ZVH': 'Devolvido Requerimento',
                'DT1052_34:UC_2BAINE': 'Devolvido Requerimento',
                # Versões curtas dos nomes (sem prefixo)
                'FAIL': 'Devolução ADM',
                'UC_R5UEXF': 'Dev. ADM Verif.',
                'UC_Z3J98J': 'Dev. ADM Verif.',
                'UC_HYO7L2': 'Dev. Busca',
                'UC_5LAJNY': 'Dev. Busca',
                'UC_UG0UDZ': 'Solic. Duplicada',
                'UC_LF04SU': 'Solic. Duplicada',
                'UC_P61ZVH': 'Dev. Requerim.',
                'UC_2BAINE': 'Dev. Requerim.'
            }
            
            # Unificar todos os mapeamentos em um único dicionário
            mapeamento_completo = {**em_andamento, **sucesso, **falha}
            
            # Verificar se o código está no mapeamento completo
            if codigo_estagio in mapeamento_completo:
                return mapeamento_completo[codigo_estagio]
            
            # Se não encontrar o código completo, tentar verificar apenas a parte após os dois pontos
            if isinstance(codigo_estagio, str) and ':' in codigo_estagio:
                apenas_codigo = codigo_estagio.split(':')[-1]
                if apenas_codigo in mapeamento_completo:
                    return mapeamento_completo[apenas_codigo]
            
            # Caso não encontre um mapeamento, retornar o nome original simplificado
            if isinstance(nome, str) and ':' in nome:
                return nome.split(':')[-1]
            return nome
        
        # Verificar qual coluna usar para os estágios
        if 'STAGE_NAME' in df.columns:
            # Adicionar coluna com nome legível do estágio
            df.loc[:, 'STAGE_NAME_LEGIVEL'] = df['STAGE_NAME'].apply(simplificar_nome_estagio)
        elif 'STAGE_ID' in df.columns:
            # Se não tiver STAGE_NAME, usar STAGE_ID
            df.loc[:, 'STAGE_NAME_LEGIVEL'] = df['STAGE_ID'].apply(simplificar_nome_estagio)
        else:
            # Se não tiver nenhum dos dois, criar uma coluna padrão
            df.loc[:, 'STAGE_NAME_LEGIVEL'] = "Desconhecido"
            st.warning("Não foi possível identificar os estágios (colunas STAGE_NAME e STAGE_ID não encontradas)")
        
        # Contar quantos processos estão em cada estágio
        contagem_por_estagio = df.groupby('STAGE_NAME_LEGIVEL').size().reset_index(name='QUANTIDADE')
        
        # Calcular o percentual
        contagem_por_estagio['PERCENTUAL'] = (contagem_por_estagio['QUANTIDADE'] / len(df) * 100).round(2)
        
        # Categorizar estágios
        def categorizar_estagio(estagio):
            # Lista de estágios considerados como SUCESSO
            sucesso_stages = ['Certidão Entregue']
            
            # Lista de estágios considerados como FALHA
            falha_stages = [
                'Devolução ADM', 'Dev. ADM Verificado', 'Devolutiva Busca', 
                'Solicitação Duplicada', 'Solic. Duplicada', 'Devolvido Requerimento',
                'Dev. Requerim.', 'Dev. ADM Verif.', 'Dev. Busca'
            ]
            
            # Verificar categoria
            if estagio in sucesso_stages:
                return 'SUCESSO'
            elif estagio in falha_stages:
                return 'FALHA'
            else:
                return 'EM ANDAMENTO'
        
        # Adicionar categoria ao DataFrame de contagem
        contagem_por_estagio['CATEGORIA'] = contagem_por_estagio['STAGE_NAME_LEGIVEL'].apply(categorizar_estagio)
        
        # Definir cores por categoria
        contagem_por_estagio['COR'] = contagem_por_estagio['CATEGORIA'].map({
            'SUCESSO': '#4caf50',      # Verde
            'EM ANDAMENTO': '#ffb300', # Amarelo
            'FALHA': '#f44336'         # Vermelho
        })
        
        # Ordenar primeiro por categoria, depois por quantidade descendente
        contagem_por_estagio['ORDEM_CATEGORIA'] = contagem_por_estagio['CATEGORIA'].map({
            'SUCESSO': 1,
            'EM ANDAMENTO': 2,
            'FALHA': 3
        })
        
        contagem_por_estagio = contagem_por_estagio.sort_values(
            ['ORDEM_CATEGORIA', 'QUANTIDADE'], 
            ascending=[True, False]
        )
        
        # Determinar a quantidade de colunas para o layout
        n_colunas = min(12, len(contagem_por_estagio))  # Usar até 12 colunas
        
        # Separar por categoria
        estagios_sucesso = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'SUCESSO']
        estagios_andamento = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'EM ANDAMENTO']
        estagios_falha = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'FALHA']
        
        # Função para renderizar uma linha de cards por categoria
        def renderizar_linha_cards(df_categoria, titulo):
            if not df_categoria.empty:
                # Título da categoria com a cor correspondente
                cor_titulo = df_categoria.iloc[0]['COR']
                st.markdown(f"""
                <div style="margin-top: 15px; margin-bottom: 8px; border-left: 5px solid {cor_titulo}; padding-left: 10px;">
                    <h4 style="margin: 0; color: {cor_titulo};">{titulo}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Determinar número de colunas para esta categoria
                n_cols = min(12, len(df_categoria))
                cols = st.columns(n_cols)
                
                # Renderizar cards para esta categoria
                for i, (_, row) in enumerate(df_categoria.iterrows()):
                    col_idx = i % n_cols
                    cor = row['COR']
                    
                    with cols[col_idx]:
                        st.markdown(f"""
                        <div style="background-color: {cor}20; padding: 8px 5px; border-radius: 8px; border-left: 5px solid {cor}; margin-bottom: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; height: 90px; display: flex; flex-direction: column; justify-content: space-between;">
                            <h3 style="margin-top: 0; color: {cor}; font-size: 11px; white-space: normal; overflow: hidden; text-overflow: ellipsis; height: 36px; display: flex; align-items: center; justify-content: center;">{row['STAGE_NAME_LEGIVEL']}</h3>
                            <p style="font-size: 20px; font-weight: bold; margin: 0;">{row['QUANTIDADE']}</p>
                            <p style="font-size: 10px; margin: 0;">({row['PERCENTUAL']}%)</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Renderizar cada categoria em sua própria linha
        renderizar_linha_cards(estagios_sucesso, "SUCESSO")
        renderizar_linha_cards(estagios_andamento, "EM ANDAMENTO")
        renderizar_linha_cards(estagios_falha, "FALHA")
        
        # Se quiser ver todos os estágios em forma de tabela
        with st.expander("Ver todos os estágios detalhados", expanded=False):
            st.dataframe(
                contagem_por_estagio[['CATEGORIA', 'STAGE_NAME_LEGIVEL', 'QUANTIDADE', 'PERCENTUAL']],
                column_config={
                    "CATEGORIA": st.column_config.TextColumn("Categoria"),
                    "STAGE_NAME_LEGIVEL": st.column_config.TextColumn("Estágio"),
                    "QUANTIDADE": st.column_config.NumberColumn("Quantidade", format="%d"),
                    "PERCENTUAL": st.column_config.ProgressColumn(
                        "Percentual",
                        format="%.2f%%",
                        min_value=0,
                        max_value=100
                    )
                },
                use_container_width=True,
                hide_index=True
            )
    
    # Análise por família
    st.markdown('<div class="section-subtitle">Análise por Família</div>', unsafe_allow_html=True)
    
    # Verificar se temos os campos UF_CRM necessários
    uf_crm_campos = ['UF_CRM_12_1723552666', 'UF_CRM_12_1722882763189', 'UF_CRM_12_1724194024', 'TITLE']
    uf_crm_faltantes = [col for col in uf_crm_campos if col not in df.columns]
    
    if uf_crm_faltantes:
        st.warning(f"Alguns campos de família não foram encontrados: {', '.join(uf_crm_faltantes)}")
        st.write("Colunas disponíveis:", df.columns.tolist())
    else:
        # Criar uma cópia do DataFrame para análise por família
        df_familia = df.copy()
        
        # Filtrar apenas os registros que têm ID de família
        df_familia = df_familia[df_familia['UF_CRM_12_1723552666'].notna()].copy()
        
        if df_familia.empty:
            st.info("Não há dados com ID de família para análise.")
        else:
            # Total de IDs de família únicos
            total_familias = df_familia['UF_CRM_12_1723552666'].nunique()
            
            # Total de famílias com pelo menos um processo concluído
            # Definir todos os códigos que representam SUCCESS
            success_codes = [
                'SUCCESS', 
                'DT1052_16:SUCCESS', 
                'DT1052_34:SUCCESS'
            ]
            
            # Verificar quais colunas estão disponíveis para buscar SUCCESS
            success_columns = []
            if 'STAGE_NAME' in df_familia.columns:
                success_columns.append('STAGE_NAME')
            if 'STAGE_ID' in df_familia.columns:
                success_columns.append('STAGE_ID')
                
            # Se encontramos alguma coluna para verificar
            familias_concluidas = 0
            df_success = pd.DataFrame()  # Inicializar com DataFrame vazio
            if success_columns:
                # Criar um filtro combinado para encontrar SUCCESS em qualquer coluna disponível
                success_mask = pd.Series(False, index=df_familia.index)
                
                for column in success_columns:
                    for code in success_codes:
                        # Verificar correspondência exata com os códigos de sucesso
                        success_mask = success_mask | (df_familia[column] == code)
                        # Verificar também se contém o código (para caso de textos mais longos)
                        success_mask = success_mask | df_familia[column].str.contains(f":{code}$", regex=True, na=False)
                
                # Filtrar os dados e contar famílias únicas
                df_success = df_familia[success_mask]
                familias_concluidas = df_success['UF_CRM_12_1723552666'].nunique() if not df_success.empty else 0
            else:
                st.warning("Não foi possível identificar famílias com processos concluídos")
            
            # Percentual de famílias com processos concluídos
            percentual = round((familias_concluidas / total_familias * 100), 2) if total_familias > 0 else 0
            
            # Exibir métricas de famílias em HTML puro
            st.markdown(f"""
            <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                <div style="flex: 1; background-color: #f0f7ff; padding: 15px; border-radius: 10px; border-left: 5px solid #4285f4; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; color: #1967d2; font-size: 16px;">Total de Famílias</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 0;">{total_familias}</p>
                </div>
                <div style="flex: 1; background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #4caf50; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; color: #2e7d32; font-size: 16px;">Famílias com Certidão Entregue</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 0;">{familias_concluidas}</p>
                </div>
                <div style="flex: 1; background-color: #f0fff7; padding: 15px; border-radius: 10px; border-left: 5px solid #34a853; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; color: #188038; font-size: 16px;">% de Famílias com Certidão Entregue</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 0;">{percentual}%</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Agrupar por ID de família
            df_familia_grouped = df_familia.groupby('UF_CRM_12_1723552666').agg({
                'UF_CRM_12_1722882763189': 'first',  # Nome da família
                'UF_CRM_12_1724194024': 'first',     # Pessoa responsável pela família
                'TITLE': 'first',                    # Nome do negócio
                'NOME_CARTORIO': 'first',            # Cartório
                'ASSIGNED_BY_NAME': 'first',         # Responsável pelo processo
                'ID': 'count'                        # Total de processos
            }).reset_index()
            
            # Renomear colunas para melhor visualização
            df_familia_grouped = df_familia_grouped.rename(columns={
                'UF_CRM_12_1723552666': 'ID da Família',
                'UF_CRM_12_1722882763189': 'Nome da Família',
                'UF_CRM_12_1724194024': 'Responsável pela Família',
                'TITLE': 'Nome do Negócio',
                'NOME_CARTORIO': 'Cartório',
                'ASSIGNED_BY_NAME': 'Responsável pelo Processo',
                'ID': 'Total de Processos'
            })
            
            # Calcular quantos processos de cada família chegaram até o estágio SUCCESS
            # Usar o df_success já calculado anteriormente
            if not df_success.empty:
                df_success_grouped = df_success.groupby('UF_CRM_12_1723552666').size().reset_index(name='Certidões Entregues')
                
                # Mesclar com o DataFrame de família
                df_familia_final = pd.merge(
                    df_familia_grouped, 
                    df_success_grouped, 
                    left_on='ID da Família', 
                    right_on='UF_CRM_12_1723552666', 
                    how='left'
                )
                
                # Preencher valores NaN com 0
                df_familia_final['Certidões Entregues'] = df_familia_final['Certidões Entregues'].fillna(0)
                
                # Calcular o percentual de conclusão
                df_familia_final['% de Entrega'] = (df_familia_final['Certidões Entregues'] / df_familia_final['Total de Processos'] * 100).round(2)
                
                # Adicionar cruzamento com dados de negócios
                # Obter token do Bitrix24
                BITRIX_TOKEN, BITRIX_URL = get_credentials()
                
                # URLs para acessar as tabelas de negócios
                url_deal = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
                url_deal_uf = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
                
                # Criar função para status de carregamento
                status_msg = st.empty()
                status_msg.info("Carregando informações adicionais dos negócios...")
                
                # Carregar dados dos negócios que tenham ID de família
                df_deal = load_bitrix_data(url_deal)
                
                if not df_deal.empty:
                    # Simplificar, selecionando apenas as colunas necessárias
                    df_deal = df_deal[['ID', 'TITLE']]
                    
                    # Carregar campos personalizados dos negócios
                    df_deal_uf = load_bitrix_data(url_deal_uf)
                    
                    if not df_deal_uf.empty:
                        # Filtrar apenas campos relevantes
                        df_deal_uf = df_deal_uf[['DEAL_ID', 'UF_CRM_1722605592778', 'UF_CRM_HIGILIZACAO_STATUS']]
                        
                        # Juntar com os negócios
                        df_deal_merged = pd.merge(df_deal, df_deal_uf, left_on='ID', right_on='DEAL_ID', how='inner')
                        
                        # Filtrar apenas negócios que têm ID de família
                        df_deal_merged = df_deal_merged[df_deal_merged['UF_CRM_1722605592778'].notna()]
                        
                        if not df_deal_merged.empty:
                            # Mapear IDs de família de negócios para IDs de família de cartório
                            ids_familia_deal = df_deal_merged['UF_CRM_1722605592778'].astype(str)
                            ids_familia_cartorio = df_familia_final['ID da Família'].astype(str)
                            
                            # Juntar com as famílias do cartório
                            df_familia_final['ID da Família (str)'] = df_familia_final['ID da Família'].astype(str)
                            df_deal_merged['UF_CRM_1722605592778'] = df_deal_merged['UF_CRM_1722605592778'].astype(str)
                            
                            # Criar um mapeamento de ID de família para Status de Higienização
                            status_mapping = dict(zip(df_deal_merged['UF_CRM_1722605592778'], df_deal_merged['UF_CRM_HIGILIZACAO_STATUS']))
                            
                            # Adicionar o Status de Higienização com base no mapeamento
                            df_familia_final['Status de Higienização'] = df_familia_final['ID da Família (str)'].map(status_mapping)
                            
                            # Função para formatar o status de higienização
                            def formatar_status_higienizacao(status):
                                if pd.isna(status) or status == "":
                                    return "Não definido"
                                
                                # Mapeamento de valores comuns
                                mapeamento = {
                                    "1": "Aguardando",
                                    "2": "Em Andamento",
                                    "3": "Concluído",
                                    "4": "Falha",
                                    "UC_1BCCUF": "Aguardando",
                                    "UC_BX0TFL": "Em Andamento",
                                    "UC_LYT3WT": "Concluído",
                                    "UC_MJXK0N": "Falha"
                                }
                                
                                if status in mapeamento:
                                    return mapeamento[status]
                                return status
                            
                            # Aplicar formatação no status de higienização
                            df_familia_final['Status de Higienização'] = df_familia_final['Status de Higienização'].apply(formatar_status_higienizacao)
                            
                            # Remover a coluna intermediária
                            df_familia_final = df_familia_final.drop(columns=['ID da Família (str)'])
                            
                            # Remover a coluna duplicada de ID da Família que veio do join anterior
                            if 'UF_CRM_12_1723552666' in df_familia_final.columns:
                                df_familia_final = df_familia_final.drop(columns=['UF_CRM_12_1723552666'])
                            
                            status_msg.success("Informações adicionais carregadas com sucesso!")
                        else:
                            status_msg.warning("Não foram encontrados negócios com ID de Família.")
                            # Adicionar coluna vazia para status de higienização
                            df_familia_final['Status de Higienização'] = ""
                    else:
                        status_msg.warning("Não foi possível carregar campos personalizados dos negócios.")
                        df_familia_final['Status de Higienização'] = ""
                else:
                    status_msg.warning("Não foi possível carregar dados dos negócios.")
                    df_familia_final['Status de Higienização'] = ""
                
                # Exibir a tabela final
                st.markdown('<div class="section-subtitle">Detalhamento por ID de Família</div>', unsafe_allow_html=True)
                st.dataframe(
                    df_familia_final,
                    column_config={
                        "% de Entrega": st.column_config.ProgressColumn(
                            "% de Entrega",
                            format="%{.2f}%",
                            min_value=0,
                            max_value=100,
                        ),
                        "Total de Processos": st.column_config.NumberColumn(
                            "Total",
                            format="%d"
                        ),
                        "Certidões Entregues": st.column_config.NumberColumn(
                            "Certidões Entregues",
                            format="%d"
                        ),
                        "Status de Higienização": st.column_config.TextColumn(
                            "Status de Higienização",
                            help="Status de higienização obtido da tabela de negócios"
                        )
                    },
                    use_container_width=True
                )
                
                # Mostrar gráfico do status de higienização
                if 'Status de Higienização' in df_familia_final.columns:
                    st.markdown('<div class="section-subtitle">Status de Higienização</div>', unsafe_allow_html=True)
                    
                    # Contar quantos registros existem por status de higienização
                    status_counts = df_familia_final['Status de Higienização'].value_counts().reset_index()
                    status_counts.columns = ['Status', 'Quantidade']
                    
                    # Calcular percentual
                    status_counts['Percentual'] = (status_counts['Quantidade'] / status_counts['Quantidade'].sum() * 100).round(2)
                    
                    # Definir cores para cada status
                    cores_status = {
                        'Não definido': '#9e9e9e',  # Cinza
                        'Aguardando': '#ffb300',    # Amarelo
                        'Em Andamento': '#2196f3',  # Azul
                        'Concluído': '#4caf50',     # Verde
                        'Falha': '#f44336'          # Vermelho
                    }
                    
                    # Mapear cores para cada status no DataFrame
                    status_counts['Cor'] = status_counts['Status'].map(lambda x: cores_status.get(x, '#9e9e9e'))
                    
                    # Criar dois gráficos lado a lado
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de pizza para status de higienização
                        fig_pie = px.pie(
                            status_counts,
                            values='Quantidade',
                            names='Status',
                            title='Distribuição por Status de Higienização',
                            color='Status',
                            color_discrete_map=cores_status
                        )
                        fig_pie.update_traces(textinfo='percent+label')
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        # Gráfico de barras para status de higienização
                        fig_bar = px.bar(
                            status_counts,
                            x='Status',
                            y='Quantidade',
                            title='Quantidade por Status de Higienização',
                            text='Quantidade',
                            color='Status',
                            color_discrete_map=cores_status
                        )
                        fig_bar.update_layout(xaxis_title="Status", yaxis_title="Quantidade")
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    # Adicionar tabela de resumo dos status de higienização
                    with st.expander("Ver resumo detalhado de Status de Higienização", expanded=False):
                        # Configuração da tabela de resumo
                        st.dataframe(
                            status_counts,
                            column_config={
                                "Status": st.column_config.TextColumn(
                                    "Status de Higienização",
                                    width="medium"
                                ),
                                "Quantidade": st.column_config.NumberColumn(
                                    "Quantidade",
                                    format="%d"
                                ),
                                "Percentual": st.column_config.ProgressColumn(
                                    "Percentual",
                                    format="%.2f%%",
                                    min_value=0,
                                    max_value=100
                                )
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                        
                        # Adicionar botão para exportar o resumo
                        csv = status_counts.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Exportar resumo para CSV",
                            data=csv,
                            file_name=f"resumo_status_higienizacao_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv"
                        )
                
                # Gráfico simplificado - sumário ao invés de por família
                st.markdown('<div class="section-subtitle">Resumo de Processos por Status</div>', unsafe_allow_html=True)
                
                # Dados para o gráfico simplificado
                total_processos = df_familia.shape[0]  # Total de registros é o total de processos
                total_concluidos = df_success.shape[0] if not df_success.empty else 0  # Total de processos concluídos
                
                status_data = pd.DataFrame({
                    'Status': ['Em Andamento', 'Certidão Entregue'],
                    'Quantidade': [total_processos - total_concluidos, total_concluidos]
                })
                
                # Criar gráfico de pizza
                fig = px.pie(
                    status_data,
                    values='Quantidade',
                    names='Status',
                    title='Status dos Processos',
                    color='Status',
                    color_discrete_map={
                        'Em Andamento': '#1976D2',
                        'Certidão Entregue': '#4CAF50'
                    }
                )
                
                # Atualizar layout
                fig.update_layout(
                    legend_title="Status",
                    height=400
                )
                
                # Exibir o gráfico
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há certidões entregues (SUCCESS) nas famílias selecionadas.")
                
                # Exibir apenas a tabela de famílias sem a coluna de conclusão
                st.dataframe(df_familia_grouped, use_container_width=True)
    
    # Criar visão agrupada por responsável e estágio
    st.markdown('<div class="section-title">Detalhamento por Cartório, Responsável e Estágio</div>', unsafe_allow_html=True)

    # Garantir que temos a coluna STAGE_NAME antes de agrupar
    if 'STAGE_NAME' not in df.columns and 'STAGE_ID' in df.columns:
        # Mapear STAGE_ID para STAGE_NAME se ainda não foi feito
        BITRIX_TOKEN, BITRIX_URL = get_credentials()
        url_stages = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_status"
        df_stages = load_bitrix_data(url_stages)
        
        if not df_stages.empty and 'STATUS_ID' in df_stages.columns and 'NAME' in df_stages.columns:
            # Encontrar os pipelines corretos
            pipeline_entities = df_stages[df_stages['NAME'].str.contains('CARTÓRIO', case=False, na=False)]['ENTITY_ID'].unique()
            
            # Filtrar estágios desses pipelines
            df_stages_filtered = df_stages[df_stages['ENTITY_ID'].isin(pipeline_entities)]
            
            # Criar um mapeamento de STAGE_ID para nome do estágio
            stage_mapping = dict(zip(df_stages_filtered['STATUS_ID'], df_stages_filtered['NAME']))
            
            # Adicionar nome do estágio ao DataFrame principal
            df['STAGE_NAME'] = df['STAGE_ID'].map(stage_mapping)
            
            # Caso não tenha mapeamento, usar o ID como nome
            df['STAGE_NAME'] = df['STAGE_NAME'].fillna(df['STAGE_ID'])

    # Usar nomes mais legíveis para os estágios
    def simplificar_nome_estagio(nome):
        if pd.isna(nome):
            return "Desconhecido"
        
        # Se o nome contém dois pontos, pegar a parte depois dos dois pontos
        if isinstance(nome, str) and ':' in nome:
            codigo_estagio = nome
        else:
            codigo_estagio = nome  # Usar o nome completo como código
        
        # Mapeamento completo dos códigos para nomes legíveis e curtos
        # EM ANDAMENTO
        em_andamento = {
            'DT1052_16:NEW': 'Aguardando Certidão',
            'DT1052_34:NEW': 'Aguardando Certidão',
            'DT1052_16:UC_QRZ6JG': 'Busca CRC',
            'DT1052_34:UC_68BLQ7': 'Busca CRC',
            'DT1052_16:UC_7F0WK2': 'Solicitar Requerimento',
            'DT1052_34:UC_HN9GMI': 'Solicitar Requerimento',
            'DT1052_16:PREPARATION': 'Montagem Requerimento',
            'DT1052_34:PREPARATION': 'Montagem Requerimento',
            'DT1052_16:UC_IWZBMO': 'Solicitar Cart. Origem',
            'DT1052_34:CLIENT': 'Certidão Emitida',
            'DT1052_34:UC_8L5JUS': 'Solicitar Cart. Origem',
            'DT1052_16:UC_8EGMU7': 'Cart. Origem Prioridade',
            'DT1052_16:UC_KXHDOQ': 'Aguard. Cart. Origem',
            'DT1052_34:UC_6KOYL5': 'Aguard. Cart. Origem',
            'DT1052_16:CLIENT': 'Certidão Emitida',
            'DT1052_34:UC_D0RG5P': 'Certidão Emitida',
            'DT1052_16:UC_JRGCW3': 'Certidão Física',
            'DT1052_34:UC_84B1S2': 'Certidão Física',
            # Versões curtas dos nomes (sem prefixo)
            'NEW': 'Aguard. Certidão',
            'PREPARATION': 'Mont. Requerim.',
            'CLIENT': 'Certidão Emitida',
            'UC_QRZ6JG': 'Busca CRC',
            'UC_68BLQ7': 'Busca CRC',
            'UC_7F0WK2': 'Solic. Requerim.',
            'UC_HN9GMI': 'Solic. Requerim.',
            'UC_IWZBMO': 'Solic. C. Origem',
            'UC_8L5JUS': 'Solic. C. Origem',
            'UC_8EGMU7': 'C. Origem Prior.',
            'UC_KXHDOQ': 'Aguard. C. Origem',
            'UC_6KOYL5': 'Aguard. C. Origem',
            'UC_D0RG5P': 'Certidão Emitida',
            'UC_JRGCW3': 'Certidão Física',
            'UC_84B1S2': 'Certidão Física'
        }
        
        # SUCESSO
        sucesso = {
            'DT1052_16:SUCCESS': 'Certidão Entregue',
            'DT1052_34:SUCCESS': 'Certidão Entregue',
            'SUCCESS': 'Certidão Entregue'
        }
        
        # FALHA
        falha = {
            'DT1052_16:FAIL': 'Devolução ADM',
            'DT1052_34:FAIL': 'Devolução ADM',
            'DT1052_16:UC_R5UEXF': 'Dev. ADM Verificado',
            'DT1052_34:UC_Z3J98J': 'Dev. ADM Verificado',
            'DT1052_16:UC_HYO7L2': 'Devolutiva Busca',
            'DT1052_34:UC_5LAJNY': 'Devolutiva Busca',
            'DT1052_16:UC_UG0UDZ': 'Solicitação Duplicada',
            'DT1052_34:UC_LF04SU': 'Solicitação Duplicada',
            'DT1052_16:UC_P61ZVH': 'Devolvido Requerimento',
            'DT1052_34:UC_2BAINE': 'Devolvido Requerimento',
            # Versões curtas dos nomes (sem prefixo)
            'FAIL': 'Devolução ADM',
            'UC_R5UEXF': 'Dev. ADM Verif.',
            'UC_Z3J98J': 'Dev. ADM Verif.',
            'UC_HYO7L2': 'Dev. Busca',
            'UC_5LAJNY': 'Dev. Busca',
            'UC_UG0UDZ': 'Solic. Duplicada',
            'UC_LF04SU': 'Solic. Duplicada',
            'UC_P61ZVH': 'Dev. Requerim.',
            'UC_2BAINE': 'Dev. Requerim.'
        }
        
        # Unificar todos os mapeamentos em um único dicionário
        mapeamento_completo = {**em_andamento, **sucesso, **falha}
        
        # Verificar se o código está no mapeamento completo
        if codigo_estagio in mapeamento_completo:
            return mapeamento_completo[codigo_estagio]
        
        # Se não encontrar o código completo, tentar verificar apenas a parte após os dois pontos
        if isinstance(codigo_estagio, str) and ':' in codigo_estagio:
            apenas_codigo = codigo_estagio.split(':')[-1]
            if apenas_codigo in mapeamento_completo:
                return mapeamento_completo[apenas_codigo]
        
        # Caso não encontre um mapeamento, retornar o nome original simplificado
        if isinstance(nome, str) and ':' in nome:
            return nome.split(':')[-1]
        return nome

    # Aplicar a função para simplificar os nomes dos estágios
    df['STAGE_NAME_LEGIVEL'] = df['STAGE_NAME'].apply(simplificar_nome_estagio)

    # Agora agrupar usando o nome legível do estágio
    grouped_df = df.groupby(['NOME_CARTORIO', 'ASSIGNED_BY_NAME', 'STAGE_NAME_LEGIVEL']).size().reset_index(name='TOTAL')

    # Calcular o total por responsável para percentuais
    total_by_responsible = df.groupby('ASSIGNED_BY_NAME').size().reset_index(name='TOTAL_RESPONSAVEL')

    # Mesclar os DataFrames
    result_df = pd.merge(grouped_df, total_by_responsible, on='ASSIGNED_BY_NAME', how='left')

    # Calcular o percentual
    result_df['PERCENTUAL'] = (result_df['TOTAL'] / result_df['TOTAL_RESPONSAVEL'] * 100).round(2)

    # Calcular percentual de won para cada estágio
    # Verificar se temos a coluna related aos deals fechados
    if 'CLOSED' in df.columns or 'IS_WON' in df.columns:
        won_column = 'IS_WON' if 'IS_WON' in df.columns else 'CLOSED'
        
        # Filtrar apenas os deals vencidos/fechados
        df_won = df[df[won_column] == 'Y'].copy()
        
        # Criar visão agrupada dos deals vencidos
        won_grouped = df_won.groupby(['NOME_CARTORIO', 'ASSIGNED_BY_NAME', 'STAGE_NAME_LEGIVEL']).size().reset_index(name='TOTAL_WON')
        
        # Mesclar com o DataFrame principal
        result_df = pd.merge(result_df, won_grouped, on=['NOME_CARTORIO', 'ASSIGNED_BY_NAME', 'STAGE_NAME_LEGIVEL'], how='left')
        
        # Preencher valores NaN com 0
        result_df['TOTAL_WON'] = result_df['TOTAL_WON'].fillna(0)
        
        # Calcular o percentual de won
        result_df['PERCENTUAL_WON'] = (result_df['TOTAL_WON'] / result_df['TOTAL'] * 100).round(2)

    # Reorganizar as colunas para melhor visualização
    cols = ['NOME_CARTORIO', 'ASSIGNED_BY_NAME', 'STAGE_NAME_LEGIVEL', 'TOTAL', 'PERCENTUAL']
    if 'PERCENTUAL_WON' in result_df.columns:
        cols.append('PERCENTUAL_WON')

    # Exibir o DataFrame ordenado
    st.dataframe(
        result_df[cols].sort_values(['NOME_CARTORIO', 'ASSIGNED_BY_NAME', 'STAGE_NAME_LEGIVEL']),
        column_config={
            "NOME_CARTORIO": "Cartório",
            "ASSIGNED_BY_NAME": "Responsável",
            "STAGE_NAME_LEGIVEL": "Estágio",
            "TOTAL": "Total",
            "PERCENTUAL": st.column_config.ProgressColumn(
                "% do Total",
                format="%.2f%%",
                min_value=0,
                max_value=100
            ),
            "PERCENTUAL_WON": st.column_config.ProgressColumn(
                "% de Sucesso",
                format="%.2f%%",
                min_value=0,
                max_value=100
            )
        },
        use_container_width=True
    )
    
    # Gráfico de barras por cartório
    st.markdown('<div class="section-title">Distribuição de Processos por Cartório</div>', unsafe_allow_html=True)
    cartorio_counts = df.groupby('NOME_CARTORIO').size().reset_index(name='TOTAL')
    
    # Calcular percentuais
    cartorio_counts['PERCENTUAL'] = (cartorio_counts['TOTAL'] / cartorio_counts['TOTAL'].sum() * 100).round(2)
    
    # Criar gráfico de pizza
    fig = px.pie(
        cartorio_counts,
        values='TOTAL',
        names='NOME_CARTORIO',
        title="Distribuição de Processos por Cartório",
        hover_data=['PERCENTUAL'],
        custom_data=['PERCENTUAL'],
        labels={'NOME_CARTORIO': 'Cartório', 'TOTAL': 'Total de Processos'}
    )
    
    # Configurar o texto mostrado no gráfico
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>" +
                     "Total: %{value}<br>" +
                     "Percentual: %{customdata[0]:.2f}%<extra></extra>"
    )
    
    # Atualizar layout
    fig.update_layout(
        showlegend=True,
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar tabela com os números
    with st.expander("Ver números detalhados", expanded=False):
        st.dataframe(
            cartorio_counts,
            column_config={
                "NOME_CARTORIO": st.column_config.TextColumn("Cartório"),
                "TOTAL": st.column_config.NumberColumn("Total de Processos", format="%d"),
                "PERCENTUAL": st.column_config.NumberColumn("Percentual", format="%.2f%%")
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Gráfico de responsáveis se solicitado
    if st.checkbox("Mostrar Gráfico de Responsáveis"):
        st.markdown('<div class="section-title">Distribuição de Processos por Responsável</div>', unsafe_allow_html=True)
        resp_counts = df.groupby(['NOME_CARTORIO', 'ASSIGNED_BY_NAME']).size().reset_index(name='TOTAL')
        fig2 = px.bar(
            resp_counts,
            x='ASSIGNED_BY_NAME',
            y='TOTAL',
            color='NOME_CARTORIO',
            barmode='group',
            labels={'ASSIGNED_BY_NAME': 'Responsável', 'TOTAL': 'Total de Processos', 'NOME_CARTORIO': 'Cartório'},
            title="Total de Processos por Responsável e Cartório"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Análise de IDs de Família
    st.markdown("## Análise de IDs de Família")
    family_id_summary, family_id_details = analyze_cartorio_ids(df)
    
    if not family_id_summary.empty:
        # Exibir resumo em um expander
        with st.expander("Resumo de IDs de Família", expanded=True):
            # Configurar as colunas para o resumo
            summary_config = {
                "Status": st.column_config.TextColumn(
                    "Status do ID",
                    width="medium",
                    help="Classificação do ID de Família"
                ),
                "Quantidade": st.column_config.NumberColumn(
                    "Quantidade",
                    format="%d",
                    width="small",
                    help="Número de registros"
                )
            }
            
            st.dataframe(
                family_id_summary,
                column_config=summary_config,
                use_container_width=True,
                hide_index=True
            )
        
        # Filtros para o detalhamento
        st.markdown("### Filtros de Análise")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro de status do ID
            selected_id_status = st.multiselect(
                "Filtrar por Status do ID",
                options=['Padrão Correto', 'Duplicado', 'Vazio', 'Formato Inválido'],
                default=['Duplicado', 'Vazio', 'Formato Inválido'],
                help="Selecione os status que deseja visualizar"
            )
        
        with col2:
            # Filtro de cartório
            cartorios = sorted(family_id_details['Cartório'].unique())
            cart_filter = st.multiselect(
                "Filtrar por Cartório",
                options=cartorios,
                help="Selecione os cartórios que deseja visualizar"
            )
        
        with col3:
            # Filtro de responsável
            responsaveis = sorted(family_id_details['Responsável'].unique())
            resp_filter = st.multiselect(
                "Filtrar por Responsável",
                options=responsaveis,
                help="Selecione os responsáveis que deseja visualizar"
            )
        
        # Aplicar filtros
        filtered_details = family_id_details.copy()
        if selected_id_status:
            filtered_details = filtered_details[filtered_details['Status do ID'].isin(selected_id_status)]
        if cart_filter:
            filtered_details = filtered_details[filtered_details['Cartório'].isin(cart_filter)]
        if resp_filter:
            filtered_details = filtered_details[filtered_details['Responsável'].isin(resp_filter)]
        
        # Exibir detalhes filtrados
        if not filtered_details.empty:
            # Configurar as colunas para o detalhamento
            details_config = {
                "ID": st.column_config.TextColumn(
                    "ID",
                    width="small",
                    help="ID do registro"
                ),
                "Nome": st.column_config.TextColumn(
                    "Nome",
                    width="medium",
                    help="Nome do registro"
                ),
                "ID Família": st.column_config.TextColumn(
                    "ID Família",
                    width="medium",
                    help="ID da Família"
                ),
                "Cartório": st.column_config.TextColumn(
                    "Cartório",
                    width="medium",
                    help="Nome do cartório"
                ),
                "Responsável": st.column_config.TextColumn(
                    "Responsável",
                    width="medium",
                    help="Nome do responsável"
                ),
                "Status do ID": st.column_config.TextColumn(
                    "Status do ID",
                    width="small",
                    help="Status do ID de Família"
                )
            }
            
            st.dataframe(
                filtered_details,
                column_config=details_config,
                use_container_width=True,
                hide_index=True
            )
            
            # Adicionar botão para exportar
            if st.button("Exportar Análise para Excel"):
                # Converter para Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Aba de resumo
                    family_id_summary.to_excel(writer, sheet_name='Resumo', index=False)
                    # Aba de detalhes
                    filtered_details.to_excel(writer, sheet_name='Detalhamento', index=False)
                
                # Oferecer para download
                st.download_button(
                    label="Baixar arquivo Excel",
                    data=output.getvalue(),
                    file_name=f"analise_ids_familia_cartorio_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Nenhum registro encontrado com os filtros selecionados.")
    else:
        st.info("Não foi possível analisar os IDs de família. Campo não encontrado nos dados.")

def analisar_familias_ausentes():
    """
    Analisa famílias que estão presentes em crm_deal (ID da Família em UF_CRM_1722605592778)
    mas não estão presentes em crm_dynamic_item_1052 (ID da Família em UF_CRM_12_1723552666).
    
    Filtra apenas negócios da categoria 32.
    
    Returns:
        tuple: (Métrica de contagem, DataFrame com os detalhes dos negócios ausentes)
    """
    try:
        # Criar placeholders para o progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Obter token do Bitrix24
        status_text.info("Inicializando conexão com Bitrix24...")
        BITRIX_TOKEN, BITRIX_URL = get_credentials()
        
        # URLs para acessar as tabelas
        url_deal = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
        url_deal_uf = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
        url_dynamic_item = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1052"
        
        # Preparar filtro para a categoria 32
        category_filter = {"dimensionsFilters": [[]]}
        category_filter["dimensionsFilters"][0].append({
            "fieldName": "CATEGORY_ID", 
            "values": ["32"], 
            "type": "INCLUDE", 
            "operator": "EQUALS"
        })
        
        # Carregar dados principais dos negócios com filtro de categoria
        status_text.info("Carregando negócios da categoria 32...")
        progress_bar.progress(10)
        
        df_deal = load_bitrix_data(url_deal, filters=category_filter)
        
        # Verificar se conseguiu carregar os dados
        if df_deal.empty:
            progress_bar.progress(100)
            status_text.error("Não foi possível carregar os dados da tabela crm_deal para a categoria 32.")
            return 0, pd.DataFrame()
            
        # Mostrar progresso
        status_text.info(f"Carregados {len(df_deal)} negócios da categoria 32")
        progress_bar.progress(30)
        
        # Simplificar: selecionar apenas as colunas necessárias para otimizar
        df_deal = df_deal[['ID', 'TITLE', 'ASSIGNED_BY_NAME']]
        
        # Obter lista de IDs dos deals para filtrar a tabela crm_deal_uf
        deal_ids = df_deal['ID'].astype(str).tolist()
        
        # Limitar a quantidade de IDs para evitar sobrecarga (se houverem muitos)
        if len(deal_ids) > 1000:
            status_text.warning(f"Limitando análise a 1000 negócios dos {len(deal_ids)} encontrados")
            deal_ids = deal_ids[:1000]
        
        # Filtro para crm_deal_uf baseado nos IDs dos deals da categoria 32
        deal_filter = {"dimensionsFilters": [[]]}
        deal_filter["dimensionsFilters"][0].append({
            "fieldName": "DEAL_ID", 
            "values": deal_ids, 
            "type": "INCLUDE", 
            "operator": "EQUALS"
        })
        
        # Carregar dados da tabela crm_deal_uf (onde estão os campos personalizados do funil de negócios)
        status_text.info("Carregando campos personalizados dos negócios...")
        progress_bar.progress(50)
        
        df_deal_uf = load_bitrix_data(url_deal_uf, filters=deal_filter)
        
        # Verificar se conseguiu carregar os dados
        if df_deal_uf.empty:
            progress_bar.progress(100)
            status_text.error("Não foi possível carregar os dados da tabela crm_deal_uf.")
            return 0, pd.DataFrame()
        
        # Simplificar: manter apenas as colunas necessárias
        df_deal_uf = df_deal_uf[['DEAL_ID', 'UF_CRM_1722605592778']]
        
        # Carregar dados da tabela crm_dynamic_items_1052 (cadastro de famílias)
        status_text.info("Carregando cadastro de famílias...")
        progress_bar.progress(70)
        
        df_dynamic_item = load_bitrix_data(url_dynamic_item)
        
        # Verificar se conseguiu carregar os dados
        if df_dynamic_item.empty:
            progress_bar.progress(100)
            status_text.error("Não foi possível carregar os dados da tabela crm_dynamic_items_1052.")
            return 0, pd.DataFrame()
        
        # Simplificar: manter apenas a coluna necessária para a comparação
        df_dynamic_item = df_dynamic_item[['UF_CRM_12_1723552666']]
        
        # Mesclar df_deal com df_deal_uf para obter os IDs de família
        status_text.info("Analisando dados...")
        progress_bar.progress(80)
        
        # Usar merge otimizado
        df_merged = pd.merge(
            df_deal,
            df_deal_uf,
            left_on='ID',
            right_on='DEAL_ID',
            how='inner'
        )
        
        # Filtrar apenas registros que possuem ID de família
        df_merged = df_merged[df_merged['UF_CRM_1722605592778'].notna()]
        
        if df_merged.empty:
            progress_bar.progress(100)
            status_text.warning("Não foram encontrados registros com ID de família na categoria 32.")
            return 0, pd.DataFrame()
        
        # Filtrar apenas registros que possuem ID de família em crm_dynamic_item
        df_dynamic_item = df_dynamic_item[df_dynamic_item['UF_CRM_12_1723552666'].notna()]
        
        if df_dynamic_item.empty:
            progress_bar.progress(100)
            status_text.warning("Não foram encontrados registros com ID de família na tabela crm_dynamic_items_1052.")
            return 0, pd.DataFrame()
        
        # Obter lista de IDs de família em cada tabela
        ids_familia_deal = df_merged['UF_CRM_1722605592778'].dropna().unique().astype(str)
        ids_familia_dynamic = df_dynamic_item['UF_CRM_12_1723552666'].dropna().unique().astype(str)
        
        # Encontrar IDs de família que existem em crm_deal mas não em crm_dynamic_item_1052
        ids_ausentes = set(ids_familia_deal) - set(ids_familia_dynamic)
        
        # Contagem de famílias ausentes
        total_ausentes = len(ids_ausentes)
        
        # Atualizar progresso
        progress_bar.progress(90)
        status_text.info(f"Encontradas {total_ausentes} famílias não cadastradas")
        
        # Se não houver famílias ausentes, retornar
        if total_ausentes == 0:
            progress_bar.progress(100)
            status_text.success("Análise concluída: não há famílias ausentes.")
            return 0, pd.DataFrame()
        
        # Filtrar os negócios que têm as famílias ausentes
        df_ausentes = df_merged[df_merged['UF_CRM_1722605592778'].astype(str).isin(ids_ausentes)]
        
        # Renomear colunas para melhor visualização
        df_resultado = df_ausentes.rename(columns={
            'ID': 'ID do Negócio',
            'UF_CRM_1722605592778': 'ID da Família',
            'TITLE': 'Nome do Negócio',
            'ASSIGNED_BY_NAME': 'Responsável'
        })
        
        # Selecionar apenas as colunas relevantes na ordem solicitada
        df_resultado = df_resultado[['ID do Negócio', 'Nome do Negócio', 'Responsável', 'ID da Família']]
        
        # Concluir progresso
        progress_bar.progress(100)
        status_text.success("Análise concluída com sucesso!")
        
        return total_ausentes, df_resultado
        
    except Exception as e:
        st.error(f"Erro durante a análise: {str(e)}")
        return 0, pd.DataFrame()

def show_cartorio():
    """
    Exibe a página principal do Cartório
    """
    # Ativar modo de depuração para diagnóstico de problemas no Streamlit Cloud
    if 'BITRIX_DEBUG' not in st.session_state:
        st.session_state['BITRIX_DEBUG'] = True  # Ativar por padrão para capturar o erro
    
    # Adicionar opção de depuração na barra lateral
    with st.sidebar:
        st.session_state['BITRIX_DEBUG'] = st.checkbox("Modo de depuração", value=st.session_state['BITRIX_DEBUG'])
    
    # Se modo de depuração ativado, exibir informações sobre o ambiente
    if st.session_state['BITRIX_DEBUG']:
        with st.expander("Informações de Depuração", expanded=True):
            st.markdown("### Diagnóstico do Ambiente")
            
            # Log de informações básicas
            st.info("Versão do Streamlit: " + st.__version__)
            
            # Verificar se estamos em Streamlit Cloud ou local
            try:
                is_cloud = hasattr(st, 'secrets')
                st.success(f"Ambiente: {'Streamlit Cloud' if is_cloud else 'Local'}")
                
                # Verificar secrets
                if is_cloud:
                    try:
                        # Verificar a existência e o formato dos secrets
                        secrets_items = []
                        if hasattr(st, 'secrets'):
                            for key in dir(st.secrets):
                                if not key.startswith('_') and not callable(getattr(st.secrets, key)):
                                    if isinstance(getattr(st.secrets, key), dict):
                                        secrets_items.append(f"{key}: <dict>")
                                    else:
                                        secrets_items.append(f"{key}: <valor definido>")
                        
                        has_secrets = len(secrets_items) > 0
                        st.success(f"Secrets configurados: {'Sim' if has_secrets else 'Não'}")
                        
                        if has_secrets:
                            st.write("Chaves disponíveis nos secrets:", ", ".join(secrets_items))
                        else:
                            st.warning("⚠️ Nenhum secret encontrado. Verifique a configuração no dashboard do Streamlit.")
                    except Exception as secret_error:
                        st.error(f"Erro ao verificar secrets: {str(secret_error)}")
                        st.code(traceback.format_exc())
            except Exception as env_error:
                st.error(f"Erro ao verificar ambiente: {str(env_error)}")
                st.code(traceback.format_exc())
            
            # Verificação do sistema de arquivos
            try:
                import os
                current_dir = os.getcwd()
                st.success(f"Diretório de trabalho: {current_dir}")
                
                # Listar arquivos importantes
                if os.path.exists('.streamlit'):
                    has_secrets_file = os.path.exists('.streamlit/secrets.toml')
                    st.success(f"Arquivo de secrets (.streamlit/secrets.toml): {'Presente' if has_secrets_file else 'Ausente'}")
                else:
                    st.warning("Diretório .streamlit não encontrado")
            except Exception as fs_error:
                st.error(f"Erro ao verificar sistema de arquivos: {str(fs_error)}")
                st.code(traceback.format_exc())
            
            # Testar obtenção de credenciais
            try:
                from api.bitrix_connector import get_credentials
                token, url = get_credentials()
                if token and url:
                    st.success("Credenciais carregadas com sucesso")
                    # Mostrar versões parciais para verificação sem expor totalmente
                    if token:
                        token_masked = f"{token[:5]}...{token[-3:]}" if len(token) > 8 else "***"
                    else:
                        token_masked = "não definido"
                    
                    st.code(f"Token: {token_masked}\nURL: {url}")
                else:
                    st.error("Credenciais não obtidas corretamente")
            except Exception as cred_error:
                st.error(f"Erro ao carregar credenciais: {str(cred_error)}")
                st.code(traceback.format_exc())
            
            # Botão para testar a API diretamente
            if st.button("Testar API do Bitrix24 (Diagnóstico)"):
                try:
                    import requests
                    import json
                    from api.bitrix_connector import get_credentials
                    
                    token, url = get_credentials()
                    
                    if not token or not url:
                        st.error("Credenciais não disponíveis para teste de API")
                    else:
                        # Teste simples para verificar se podemos acessar a API
                        test_url = f"{url}/bitrix/tools/biconnector/pbi.php?token={token}&table=crm_dynamic_items_1052&limit=1"
                        
                        with st.spinner("Testando API do Bitrix24..."):
                            try:
                                # Adicionar cabeçalhos completos
                                headers = {
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                    "Accept": "*/*",
                                    "Content-Type": "application/json",
                                    "Accept-Encoding": "gzip, deflate, br"
                                }
                                
                                # Fazer a requisição com timeout e headers
                                response = requests.get(test_url, headers=headers, timeout=20)
                                
                                # Capturar informações da resposta
                                st.write(f"Status Code: {response.status_code}")
                                st.write(f"Cabeçalhos da resposta: {dict(response.headers)}")
                                
                                # Tentar decodificar como JSON
                                try:
                                    json_data = response.json()
                                    st.success("Resposta decodificada como JSON com sucesso")
                                    if isinstance(json_data, list) and len(json_data) > 0:
                                        st.write(f"Número de itens na resposta: {len(json_data)}")
                                        if len(json_data) > 1:
                                            st.write("Estrutura da resposta:", json_data[0])
                                    else:
                                        st.write("Estrutura da resposta:", json_data)
                                except json.JSONDecodeError:
                                    st.error("Não foi possível decodificar a resposta como JSON")
                                    st.code(response.text[:500] + "..." if len(response.text) > 500 else response.text)
                            except Exception as req_error:
                                st.error(f"Erro na requisição: {str(req_error)}")
                                st.code(traceback.format_exc())
                except Exception as api_error:
                    st.error(f"Erro ao testar API: {str(api_error)}")
                    st.code(traceback.format_exc())
    
    # Título centralizado
    st.markdown("<h1 style='text-align: center;'>Monitoramento de Cartórios</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Esta seção apresenta dados sobre os processos em cartório.</p>", unsafe_allow_html=True)
    
    # Carregar os dados dos cartórios
    df_cartorio = carregar_dados_cartorio()
    
    if df_cartorio.empty:
        st.warning("Não foi possível carregar os dados dos cartórios. Verifique a conexão com o Bitrix24.")
        
        # Se modo de depuração ativado, mostrar informações adicionais
        if st.session_state['BITRIX_DEBUG']:
            st.error("Falha ao carregar dados dos cartórios - Verifique o seguinte:")
            st.markdown("""
            1. As credenciais do Bitrix24 estão configuradas corretamente?
            2. A URL do Bitrix24 está acessível?
            3. Os tokens estão válidos e não expiraram?
            4. A tabela crm_dynamic_items_1052 existe e está acessível?
            """)
            
            # Botão para testar conexão
            if st.button("Testar Conexão com Bitrix24"):
                try:
                    import requests
                    from api.bitrix_connector import get_credentials
                    
                    token, url = get_credentials()
                    test_url = f"{url}/bitrix/tools/biconnector/pbi.php?token={token}&table=crm_dynamic_items_1052&limit=1"
                    
                    with st.spinner("Testando conexão..."):
                        response = requests.get(test_url, timeout=10)
                        
                        if response.status_code == 200:
                            st.success(f"Conexão bem-sucedida! Código: {response.status_code}")
                            # Mostrar primeiros 200 caracteres da resposta
                            st.code(response.text[:200] + "...")
                        else:
                            st.error(f"Falha na conexão. Código: {response.status_code}")
                            st.code(response.text[:200] + "...")
                except Exception as conn_error:
                    st.error(f"Erro no teste de conexão: {str(conn_error)}")
        
        return
    else:
        st.success(f"Dados carregados com sucesso: {len(df_cartorio)} registros encontrados.")
    
    # Adicionar filtro de cartório
    cartorio_filter = st.multiselect(
        "Filtrar por Cartório:",
        ["CARTÓRIO CASA VERDE", "CARTÓRIO TATUÁPE"],
        default=["CARTÓRIO CASA VERDE", "CARTÓRIO TATUÁPE"]
    )
    
    # Aplicar filtro de cartório aos dados
    if cartorio_filter and not df_cartorio.empty:
        df_cartorio = df_cartorio[df_cartorio['NOME_CARTORIO'].isin(cartorio_filter)]
        st.info(f"Filtrando para mostrar apenas: {', '.join(cartorio_filter)}")
    
    # Mostrar todas as informações relevantes em uma única página
    if not df_cartorio.empty:
        # 1. Visão Geral
        st.header("Visão Geral dos Cartórios")
        visao_geral = criar_visao_geral_cartorio(df_cartorio)
        if not visao_geral.empty:
            st.dataframe(visao_geral, use_container_width=True)
        else:
            st.info("Não foi possível criar a visão geral. Verifique se os dados estão corretos.")
        
        # 2. Dados Detalhados
        visualizar_cartorio_dados(df_cartorio)
        
        # 3. Análise de Famílias Ausentes no Cadastro
        st.header("Negócios com Famílias não Cadastradas (Categoria 32)")
        
        # Criar caixa expansível para mostrar a análise (inicialmente fechada)
        with st.expander("Exibir análise de negócios com famílias não cadastradas", expanded=False):
            # Explicação do processo
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <p style="margin: 0;">Esta análise compara os negócios da categoria 32 com o cadastro de famílias para identificar quais
                negócios possuem IDs de família que não estão cadastrados no sistema.</p>
                <p style="margin-top: 10px; font-size: 14px; color: #666;">
                    <strong>Nota:</strong> O processo pode levar alguns instantes, dependendo da quantidade de dados.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão para iniciar a análise
            if st.button("Iniciar Análise"):
                # Executar análise sem spinner (já temos progressbar interno)
                total_ausentes, df_ausentes = analisar_familias_ausentes()
                
                if total_ausentes > 0:
                    # Exibir métrica em destaque
                    st.markdown(f"""
                    <div style="background-color: #ffe4e4; padding: 15px; border-radius: 10px; border-left: 5px solid #e53935; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3 style="margin-top: 0; color: #c62828; font-size: 16px;">Negócios com Famílias não Cadastradas</h3>
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{total_ausentes}</p>
                        <p style="margin-top: 10px; font-size: 14px;">
                            Negócios da categoria 32 cujas famílias (UF_CRM_1722605592778) não estão cadastradas no sistema (UF_CRM_12_1723552666).
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Exibir tabela com os detalhes
                    st.subheader("Detalhes dos Negócios Afetados")
                    st.dataframe(
                        df_ausentes, 
                        use_container_width=True,
                        column_config={
                            "ID do Negócio": st.column_config.NumberColumn("ID do Negócio", format="%d"),
                            "Nome do Negócio": "Nome do Negócio",
                            "Responsável": "Responsável",
                            "ID da Família": st.column_config.NumberColumn("ID da Família", format="%d")
                        }
                    )
                    
                    # Adicionar botão para exportar os dados
                    csv = df_ausentes.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Exportar dados para CSV",
                        data=csv,
                        file_name="negocios_familias_nao_cadastradas.csv",
                        mime="text/csv",
                    )
                elif total_ausentes == 0:
                    st.success("Não foram encontrados negócios com famílias não cadastradas na categoria 32. Todas as famílias estão devidamente registradas!")
            else:
                st.info("Clique no botão acima para iniciar a análise de negócios com famílias não cadastradas.")
    else:
        st.info("Nenhum dado disponível para exibir.")
        
    # Rodapé com informação de atualização
    st.markdown("---")
    st.caption("Dados atualizados em tempo real do Bitrix24.") 