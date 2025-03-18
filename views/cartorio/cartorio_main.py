import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import io
import traceback
from dotenv import load_dotenv
from datetime import datetime, timedelta
from api.bitrix_connector import load_bitrix_data, get_credentials
import re
import requests

# Carregar variáveis de ambiente
load_dotenv()

def carregar_dados_cartorio():
    """
    Carrega os dados dos cartórios Casa Verde e Tatuápe
    
    Returns:
        pandas.DataFrame: DataFrame com os dados filtrados dos cartórios
    """
    # Garantir acesso ao módulo streamlit
    import streamlit as st_module
    # Garantir acesso ao módulo requests
    import requests as requests_module
    import traceback
    
    try:
        # Logs detalhados
        debug_info = {}
        
        # Obter token do Bitrix24
        try:
            from api.bitrix_connector import get_credentials
            BITRIX_TOKEN, BITRIX_URL = get_credentials()
            debug_info["credentials"] = "obtidas"
        except Exception as cred_error:
            if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
                st_module.error(f"❌ Erro ao obter credenciais: {str(cred_error)}")
                st_module.code(traceback.format_exc())
            debug_info["credentials_error"] = str(cred_error)
            return pd.DataFrame()
        
        # Verificar se temos as credenciais necessárias
        if not BITRIX_TOKEN or not BITRIX_URL:
            if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
                st_module.error("🔑 Credenciais do Bitrix24 não encontradas ou inválidas")
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
        if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
            token_masked = f"{BITRIX_TOKEN[:5]}...{BITRIX_TOKEN[-3:]}" if len(BITRIX_TOKEN) > 8 else "***"
            st_module.info(f"🔗 Tentando acessar: {BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={token_masked}&table=crm_dynamic_items_1052")
        
        # Fazer requisição manual para diagnóstico detalhado
        if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
            try:
                # Tentar acessar a API diretamente para diagnóstico
                st_module.info("Realizando requisição de diagnóstico...")
                
                # Adicionar cabeçalhos completos
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "*/*",
                    "Content-Type": "application/json",
                    "Accept-Encoding": "gzip, deflate, br"
                }
                
                # Usar a biblioteca requests para diagnóstico
                with st_module.spinner("Testando acesso à API..."):
                    test_response = requests_module.get(safe_url, headers=headers, timeout=30)
                    st_module.write(f"Status da resposta: {test_response.status_code}")
                    
                    # Mostrar cabeçalhos da resposta
                    st_module.write("Cabeçalhos da resposta:", dict(test_response.headers))
                    
                    # Verificar se o conteúdo pode ser interpretado como JSON
                    try:
                        json_data = test_response.json()
                        st_module.success("✅ Resposta decodificada como JSON com sucesso")
                        if isinstance(json_data, list):
                            st_module.write(f"Número de itens na resposta: {len(json_data)}")
                        debug_info["test_response_valid"] = True
                    except Exception as json_error:
                        st_module.error(f"❌ Erro ao decodificar resposta como JSON: {str(json_error)}")
                        st_module.code(test_response.text[:500] + "..." if len(test_response.text) > 500 else test_response.text)
                        debug_info["test_response_valid"] = False
                        debug_info["json_error"] = str(json_error)
                
            except Exception as request_error:
                st_module.error(f"❌ Erro na requisição de diagnóstico: {str(request_error)}")
                st_module.code(traceback.format_exc())
                debug_info["request_error"] = str(request_error)
        
        # Carregar os dados com ou sem exibição de logs conforme o modo de depuração
        show_logs = 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']
        try:
            from api.bitrix_connector import load_bitrix_data
            df_items = load_bitrix_data(safe_url, show_logs=show_logs)
            debug_info["load_data_called"] = True
        except Exception as load_error:
            if show_logs:
                st_module.error(f"❌ Erro ao carregar dados com load_bitrix_data: {str(load_error)}")
                st_module.code(traceback.format_exc())
            debug_info["load_error"] = str(load_error)
            return pd.DataFrame()
        
        # Se o DataFrame estiver vazio, retornar DataFrame vazio
        if df_items is None or df_items.empty:
            if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
                st_module.error("📊 Não foram encontrados dados na tabela crm_dynamic_items_1052")
            debug_info["df_empty"] = True
            return pd.DataFrame()
        else:
            debug_info["df_empty"] = False
        
        # Adicionar log de depuração
        if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
            st_module.success(f"✅ Dados carregados com sucesso: {len(df_items)} registros")
            st_module.write("Colunas disponíveis:", df_items.columns.tolist())
            debug_info["df_columns"] = df_items.columns.tolist()
        
        # Verificar se a coluna CATEGORY_ID existe
        if 'CATEGORY_ID' not in df_items.columns:
            if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
                st_module.error("❌ Coluna CATEGORY_ID não encontrada nos dados recebidos")
                st_module.write("Colunas disponíveis:", df_items.columns.tolist())
            debug_info["category_id_missing"] = True
            return pd.DataFrame()
        else:
            debug_info["category_id_missing"] = False
        
        # Filtrar apenas os cartórios Casa Verde (16) e Tatuápe (34)
        df_filtrado = df_items[df_items['CATEGORY_ID'].isin([16, 34])].copy()  # Usar .copy() para evitar SettingWithCopyWarning
        
        # Adicionar log de depuração
        if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
            st_module.success(f"✅ Dados filtrados: {len(df_filtrado)} registros após filtro de cartórios")
            debug_info["filtered_records"] = len(df_filtrado)
        
        # Adicionar o nome do cartório para melhor visualização
        df_filtrado.loc[:, 'NOME_CARTORIO'] = df_filtrado['CATEGORY_ID'].map({
            16: 'CARTÓRIO CASA VERDE',
            34: 'CARTÓRIO TATUÁPE'
        })
        
        # Armazenar informações de depuração na sessão
        if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
            st_module.session_state['DEBUG_INFO'] = debug_info
            
        return df_filtrado
    
    except Exception as e:
        # Log de erro detalhado no modo de depuração
        if 'BITRIX_DEBUG' in st_module.session_state and st_module.session_state['BITRIX_DEBUG']:
            st_module.error(f"❌ Erro geral ao carregar dados do cartório: {str(e)}")
            st_module.code(traceback.format_exc())
            
            # Criar um relatório de diagnóstico completo
            st_module.error("Relatório de Diagnóstico")
            
            # Versão do Python e bibliotecas
            import sys
            import pandas as pd
            import streamlit as st
            import requests as requests_module
            
            diagnostic_report = {
                "python_version": sys.version,
                "streamlit_version": st.__version__,
                "pandas_version": pd.__version__,
                "requests_version": requests_module.__version__,
                "error": str(e),
                "error_type": type(e).__name__
            }
            
            # Exibir relatório
            for key, value in diagnostic_report.items():
                st_module.text(f"{key}: {value}")
                
            # Armazenar relatório na sessão
            st_module.session_state['ERROR_DIAGNOSTIC'] = diagnostic_report
        else:
            st_module.error("Não foi possível carregar os dados dos cartórios. Ative o modo de depuração para mais detalhes.")
        
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

def visualizar_cartorio_dados(df_cartorio, use_animation=True):
    """
    Visualiza os dados detalhados dos cartórios
    
    Args:
        df_cartorio (pd.DataFrame): DataFrame contendo os dados dos cartórios
        use_animation (bool): Se True, usa animações Lottie. Se False, usa elementos estáticos
    """
    try:
        # Verificar se as animações estão desativadas nas sessões
        if st.session_state.get('DISABLE_ANIMATIONS', False):
            use_animation = False
            
        # Verificar se existem dados para visualizar
        if df_cartorio is None or df_cartorio.empty:
            st.warning("Não há dados disponíveis para visualização.")
            return
            
        # Obter lista de cartórios
        cartorios = df_cartorio['NOME_CARTORIO'].unique()
        
        # Configurar a disposição das métricas
        col1, col2, col3 = st.columns(3)
        
        # 1. Cartório com mais processos
        with col1:
            try:
                st.subheader("🏢 Cartório com mais processos")
                
                # Contar processos por cartório
                processos_por_cartorio = df_cartorio['NOME_CARTORIO'].value_counts().reset_index()
                processos_por_cartorio.columns = ['CARTÓRIO', 'PROCESSOS']
                
                if not processos_por_cartorio.empty:
                    # Obter o cartório com mais processos
                    top_cartorio = processos_por_cartorio.iloc[0]
                    
                    # Exibir métrica destacada
                    st.metric(
                        label=top_cartorio['CARTÓRIO'], 
                        value=f"{top_cartorio['PROCESSOS']} processos"
                    )
                    
                    # Mostrar tabela completa
                    st.dataframe(processos_por_cartorio, use_container_width=True)
                    
                    # Exibir animação ou ícone estático
                    if use_animation:
                        try:
                            # Tentar exibir a animação
                            from utils.animation_utils import load_lottieurl
                            
                            # Carregar animação do prédio/cartório
                            lottie_building = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_6e0qqtpa.json")
                            
                            if lottie_building:
                                import streamlit_lottie as st_lottie
                                st_lottie.st_lottie(lottie_building, speed=1, height=150, key="building")
                        except Exception as anim_error:
                            if st.session_state.get('DEBUG_MODE', False):
                                st.warning(f"Não foi possível exibir a animação: {str(anim_error)}")
                            # Fallback para ícone estático
                            st.markdown("🏢")
                    else:
                        # Usar ícone estático quando animações estiverem desativadas
                        st.markdown("<div style='text-align: center; font-size: 3rem;'>🏢</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro ao processar cartório com mais processos: {str(e)}")
        
        # 2. Status mais comum
        with col2:
            try:
                st.subheader("📊 Status mais comum")
                
                # Contar processos por status
                status_counts = df_cartorio['STATUS'].value_counts().reset_index()
                status_counts.columns = ['STATUS', 'QUANTIDADE']
                
                if not status_counts.empty:
                    # Obter o status mais comum
                    top_status = status_counts.iloc[0]
                    
                    # Exibir métrica destacada
                    st.metric(
                        label=top_status['STATUS'], 
                        value=f"{top_status['QUANTIDADE']} processos"
                    )
                    
                    # Mostrar tabela completa
                    st.dataframe(status_counts, use_container_width=True)
                    
                    # Exibir animação ou ícone estático
                    if use_animation:
                        try:
                            # Tentar exibir a animação
                            from utils.animation_utils import load_lottieurl
                            
                            # Carregar animação de status/documento
                            lottie_document = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_x17ybolp.json")
                            
                            if lottie_document:
                                import streamlit_lottie as st_lottie
                                st_lottie.st_lottie(lottie_document, speed=1, height=150, key="document")
                        except Exception as anim_error:
                            if st.session_state.get('DEBUG_MODE', False):
                                st.warning(f"Não foi possível exibir a animação: {str(anim_error)}")
                            # Fallback para ícone estático
                            st.markdown("📄")
                    else:
                        # Usar ícone estático quando animações estiverem desativadas
                        st.markdown("<div style='text-align: center; font-size: 3rem;'>📄</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erro ao processar status mais comum: {str(e)}")
        
        # 3. Tempo médio de processamento
        with col3:
            try:
                st.subheader("⏱️ Tempo médio de processamento")
                
                # Calcular o tempo médio se houver dados disponíveis
                if 'DIAS_EM_PROCESSAMENTO' in df_cartorio.columns:
                    tempo_medio = df_cartorio['DIAS_EM_PROCESSAMENTO'].mean()
                    tempo_medio_formatado = f"{tempo_medio:.1f} dias"
                    
                    # Exibir métrica destacada
                    st.metric(
                        label="Média Geral", 
                        value=tempo_medio_formatado
                    )
                    
                    # Calcular tempo médio por cartório
                    tempo_por_cartorio = df_cartorio.groupby('NOME_CARTORIO')['DIAS_EM_PROCESSAMENTO'].mean().reset_index()
                    tempo_por_cartorio.columns = ['CARTÓRIO', 'MÉDIA DE DIAS']
                    tempo_por_cartorio['MÉDIA DE DIAS'] = tempo_por_cartorio['MÉDIA DE DIAS'].round(1)
                    
                    st.dataframe(tempo_por_cartorio, use_container_width=True)
                    
                    # Exibir animação ou ícone estático
                    if use_animation:
                        try:
                            # Tentar exibir a animação
                            from utils.animation_utils import load_lottieurl
                            
                            # Carregar animação de tempo/relógio
                            lottie_time = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_yvnurvr4.json")
                            
                            if lottie_time:
                                import streamlit_lottie as st_lottie
                                st_lottie.st_lottie(lottie_time, speed=1, height=150, key="time")
                        except Exception as anim_error:
                            if st.session_state.get('DEBUG_MODE', False):
                                st.warning(f"Não foi possível exibir a animação: {str(anim_error)}")
                            # Fallback para ícone estático
                            st.markdown("⏱️")
                    else:
                        # Usar ícone estático quando animações estiverem desativadas
                        st.markdown("<div style='text-align: center; font-size: 3rem;'>⏱️</div>", unsafe_allow_html=True)
                else:
                    st.info("Dados de tempo de processamento não disponíveis.")
            except Exception as e:
                st.error(f"Erro ao processar tempo médio: {str(e)}")
        
        # 4. Gráfico de distribuição de processos
        st.header("Distribuição de Processos por Cartório e Status")
        try:
            # Criar tabela pivot para o gráfico
            pivot_df = df_cartorio.pivot_table(
                index='NOME_CARTORIO',
                columns='STATUS',
                values='ID',
                aggfunc='count',
                fill_value=0
            ).reset_index()
            
            # Verificar se há dados para exibir
            if pivot_df.shape[0] > 0 and pivot_df.shape[1] > 1:
                # Plotar gráfico de barras empilhadas
                import plotly.express as px
                
                fig = px.bar(
                    pivot_df, 
                    x='NOME_CARTORIO',
                    y=pivot_df.columns[1:],
                    title="Processos por Cartório e Status",
                    labels={'NOME_CARTORIO': 'Cartório', 'value': 'Quantidade de Processos'},
                    height=400
                )
                
                fig.update_layout(
                    xaxis_title="Cartório",
                    yaxis_title="Quantidade de Processos",
                    legend_title="Status",
                    barmode='stack'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há dados suficientes para exibir o gráfico de distribuição.")
        except Exception as e:
            st.error(f"Erro ao processar gráfico de distribuição: {str(e)}")
            if st.session_state.get('DEBUG_MODE', False):
                import traceback
                st.code(traceback.format_exc())
        
        # 5. Tabela detalhada dos processos
        st.header("Detalhes dos Processos em Cartório")
        try:
            # Formatar tabela para exibição
            tabela_detalhes = df_cartorio.copy()
            
            # Verificar e formatar colunas de data
            colunas_data = [col for col in tabela_detalhes.columns if 'DATA' in col]
            for col in colunas_data:
                try:
                    if tabela_detalhes[col].dtype == 'object' or pd.api.types.is_datetime64_any_dtype(tabela_detalhes[col]):
                        tabela_detalhes[col] = pd.to_datetime(tabela_detalhes[col], errors='coerce')
                        tabela_detalhes[col] = tabela_detalhes[col].dt.strftime('%d/%m/%Y')
                except Exception as date_error:
                    if st.session_state.get('DEBUG_MODE', False):
                        st.warning(f"Erro ao formatar coluna de data {col}: {str(date_error)}")
            
            # Exibir tabela interativa
            st.dataframe(tabela_detalhes, use_container_width=True)
            
            # Adicionar opções para download dos dados
            download_col1, download_col2 = st.columns(2)
            
            # Opção para download Excel
            with download_col1:
                try:
                    st.download_button(
                        label="📥 Exportar para Excel",
                        data=convert_df_to_excel(tabela_detalhes),
                        file_name="cartorio_detalhes.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                except Exception as e:
                    if st.session_state.get('DEBUG_MODE', False):
                        st.error(f"Erro ao gerar Excel: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
            
            # Opção para download CSV
            with download_col2:
                try:
                    st.download_button(
                        label="📥 Exportar para CSV",
                        data=convert_df_to_csv(tabela_detalhes),
                        file_name="cartorio_detalhes.csv",
                        mime="text/csv",
                    )
                except Exception as e:
                    if st.session_state.get('DEBUG_MODE', False):
                        st.error(f"Erro ao gerar CSV: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                
        except Exception as e:
            st.error(f"Erro ao exibir tabela detalhada: {str(e)}")
            if st.session_state.get('DEBUG_MODE', False):
                import traceback
                st.code(traceback.format_exc())
                
    except Exception as e:
        st.error(f"Erro na visualização dos dados: {str(e)}")
        if st.session_state.get('DEBUG_MODE', False):
            import traceback
            st.code(traceback.format_exc())

def analisar_familias_ausentes(use_animation=True):
    """
    Analisa negócios com IDs de família que não estão cadastrados no sistema
    
    Args:
        use_animation (bool): Se True, usa animações de carregamento. Se False, usa spinner simples.
        
    Returns:
        tuple: (total_ausentes, df_resultado) - Total de famílias ausentes e DataFrame com detalhes
    """
    try:
        # Verificar se a função de animação está disponível
        animation_available = False
        try:
            from utils.animation_utils import display_loading_animation, update_progress, clear_loading_animation
            animation_available = True
        except ImportError:
            animation_available = False
        
        # Determinar se devemos usar animação com base na disponibilidade e preferência
        use_animation = use_animation and animation_available and not st.session_state.get('DISABLE_ANIMATIONS', False)
        
        # Iniciar animação ou spinner
        if use_animation:
            progress_bar, animation_container, status_text = display_loading_animation(
                message="Analisando famílias não cadastradas...",
                min_display_time=3
            )
            # Iniciar progresso
            update_progress(progress_bar, 0.05, status_text, "Iniciando análise...")
        else:
            # Usar spinner simples
            status_text = st.empty()
            progress_bar = st.progress(0)
            status_text.info("Iniciando análise...")
            progress_bar.progress(0.05)
        
        # Obter token do Bitrix24
        BITRIX_TOKEN, BITRIX_URL = get_credentials()
        
        # Atualizar progresso
        if use_animation:
            update_progress(progress_bar, 0.1, status_text, "Carregando informações do CRM...")
        else:
            status_text.info("Carregando informações do CRM...")
            progress_bar.progress(0.1)
        
        # URL para acessar a tabela crm_deal (Categoria 32 - Cadastro)
        url_deal = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
        
        # Carregar os dados da categoria 32 (Cadastro)
        filters = {"dimensionsFilters": [[{
            "fieldName": "CATEGORY_ID", 
            "values": [32], 
            "type": "INCLUDE", 
            "operator": "EQUALS"
        }]]}
        
        df_deal = load_bitrix_data(url_deal, filters)
        
        # Se o DataFrame estiver vazio, retornar DataFrame vazio
        if df_deal is None or df_deal.empty:
            if use_animation:
                update_progress(progress_bar, 1.0, status_text, "Não foram encontrados negócios na categoria 32.")
                clear_loading_animation(progress_bar, animation_container, status_text)
            else:
                status_text.warning("Não foram encontrados negócios na categoria 32.")
                progress_bar.progress(1.0)
            return 0, pd.DataFrame()
        
        # Atualizar progresso
        if use_animation:
            update_progress(progress_bar, 0.3, status_text, "Carregando campos personalizados...")
        else:
            status_text.info("Carregando campos personalizados...")
            progress_bar.progress(0.3)
        
        # URL para acessar a tabela crm_deal_uf (Campos personalizados)
        url_deal_uf = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
        
        # Carregar os dados dos campos personalizados para os IDs da categoria 32
        deal_ids = df_deal['ID'].tolist()
        
        # Dividir em lotes de 100 para evitar problemas de tamanho de requisição
        batch_size = 100
        df_uf_list = []
        
        # Definir o número de batches
        num_batches = (len(deal_ids) + batch_size - 1) // batch_size
        
        for i in range(0, len(deal_ids), batch_size):
            batch_ids = deal_ids[i:i+batch_size]
            
            # Atualizar progresso com base na posição atual
            batch_progress = 0.3 + (0.3 * (i / len(deal_ids)))
            if use_animation:
                update_progress(progress_bar, batch_progress, status_text, 
                                f"Carregando lote {i//batch_size + 1} de {num_batches}...")
            else:
                status_text.info(f"Carregando lote {i//batch_size + 1} de {num_batches}...")
                progress_bar.progress(batch_progress)
            
            # Filtrar apenas os IDs deste lote
            batch_filters = {"dimensionsFilters": [[{
                "fieldName": "ID", 
                "values": batch_ids, 
                "type": "INCLUDE", 
                "operator": "EQUALS"
            }]]}
            
            df_batch = load_bitrix_data(url_deal_uf, batch_filters)
            if df_batch is not None and not df_batch.empty:
                df_uf_list.append(df_batch)
        
        # Combinar todos os batches
        if df_uf_list:
            df_deal_uf = pd.concat(df_uf_list, ignore_index=True)
        else:
            df_deal_uf = pd.DataFrame()
        
        # Se não encontrou dados de campos personalizados, retornar
        if df_deal_uf.empty:
            if use_animation:
                update_progress(progress_bar, 1.0, status_text, "Não foram encontrados campos personalizados para os negócios.")
                clear_loading_animation(progress_bar, animation_container, status_text)
            else:
                status_text.warning("Não foram encontrados campos personalizados para os negócios.")
                progress_bar.progress(1.0)
            return 0, pd.DataFrame()
        
        # Atualizar progresso
        if use_animation:
            update_progress(progress_bar, 0.6, status_text, "Mesclando dados...")
        else:
            status_text.info("Mesclando dados...")
            progress_bar.progress(0.6)
        
        # Filtrar apenas as linhas que contêm o campo de ID de família
        df_deal_uf_id = df_deal_uf[df_deal_uf['FIELD_NAME'] == 'UF_CRM_1722605592778'].copy()
        
        # Se não encontrou o campo de ID de família, retornar
        if df_deal_uf_id.empty:
            if use_animation:
                update_progress(progress_bar, 1.0, status_text, "Não foram encontrados IDs de família nos negócios.")
                clear_loading_animation(progress_bar, animation_container, status_text)
            else:
                status_text.warning("Não foram encontrados IDs de família nos negócios.")
                progress_bar.progress(1.0)
            return 0, pd.DataFrame()
        
        # Mesclar os dataframes para ter ID, título e ID da família
        df_merged = pd.merge(df_deal, df_deal_uf_id, on='ID', how='inner')
        
        # Renomear a coluna VALUE para UF_CRM_1722605592778 (ID da família no negócio)
        df_merged.rename(columns={'VALUE': 'UF_CRM_1722605592778'}, inplace=True)
        
        # Remover registros onde o ID da família está vazio
        df_merged = df_merged[~df_merged['UF_CRM_1722605592778'].isna()]
        
        # Se não sobrou nenhum registro com ID de família, retornar
        if df_merged.empty:
            if use_animation:
                update_progress(progress_bar, 1.0, status_text, "Nenhum negócio com ID de família válido encontrado.")
                clear_loading_animation(progress_bar, animation_container, status_text)
            else:
                status_text.warning("Nenhum negócio com ID de família válido encontrado.")
                progress_bar.progress(1.0)
            return 0, pd.DataFrame()
        
        # Atualizar progresso
        if use_animation:
            update_progress(progress_bar, 0.7, status_text, "Carregando informações adicionais dos negócios...")
        else:
            status_text.info("Carregando informações adicionais dos negócios...")
            progress_bar.progress(0.7)
        
        # Carregar dados da tabela de items dinâmicos (crm_dynamic_items_1052) - Famílias
        url_dynamic_items = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1052"
        df_dynamic_item = load_bitrix_data(url_dynamic_items)
        
        # Se não conseguiu carregar os dados das famílias, retornar
        if df_dynamic_item is None or df_dynamic_item.empty:
            if use_animation:
                update_progress(progress_bar, 1.0, status_text, "Não foram encontrados registros de famílias.")
                clear_loading_animation(progress_bar, animation_container, status_text)
            else:
                status_text.warning("Não foram encontrados registros de famílias.")
                progress_bar.progress(1.0)
            return 0, pd.DataFrame()
        
        # Verificar se a coluna de ID de família existe na tabela dinâmica
        if 'UF_CRM_12_1723552666' not in df_dynamic_item.columns:
            if use_animation:
                update_progress(progress_bar, 1.0, status_text, "Não foram encontrados registros com ID de família na tabela crm_dynamic_items_1052.")
                clear_loading_animation(progress_bar, animation_container, status_text)
            else:
                status_text.warning("Não foram encontrados registros com ID de família na tabela crm_dynamic_items_1052.")
                progress_bar.progress(1.0)
            return 0, pd.DataFrame()
        
        # Obter lista de IDs de família em cada tabela
        ids_familia_deal = df_merged['UF_CRM_1722605592778'].dropna().unique().astype(str)
        ids_familia_dynamic = df_dynamic_item['UF_CRM_12_1723552666'].dropna().unique().astype(str)
        
        # Encontrar IDs de família que existem em crm_deal mas não em crm_dynamic_item_1052
        ids_ausentes = set(ids_familia_deal) - set(ids_familia_dynamic)
        
        # Contagem de famílias ausentes
        total_ausentes = len(ids_ausentes)
        
        # Atualizar progresso
        if use_animation:
            update_progress(progress_bar, 0.9, status_text, f"Encontradas {total_ausentes} famílias não cadastradas")
        else:
            status_text.info(f"Encontradas {total_ausentes} famílias não cadastradas")
            progress_bar.progress(0.9)
        
        # Se não houver famílias ausentes, retornar
        if total_ausentes == 0:
            if use_animation:
                update_progress(progress_bar, 1.0, status_text, "Análise concluída: não há famílias ausentes.")
                clear_loading_animation(progress_bar, animation_container, status_text)
            else:
                status_text.success("Análise concluída: não há famílias ausentes.")
                progress_bar.progress(1.0)
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
        if use_animation:
            update_progress(progress_bar, 1.0, status_text, "Análise concluída com sucesso!")
            clear_loading_animation(progress_bar, animation_container, status_text)
        else:
            status_text.success("Análise concluída com sucesso!")
            progress_bar.progress(1.0)
        
        return total_ausentes, df_resultado
        
    except Exception as e:
        if use_animation and 'animation_container' in locals() and 'progress_bar' in locals() and 'status_text' in locals():
            try:
                clear_loading_animation(progress_bar, animation_container, status_text)
            except:
                pass
        
        st.error(f"Erro durante a análise: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return 0, pd.DataFrame()

def show_cartorio():
    """
    Função principal para exibir a interface de análise de cartórios
    """
    # Inicializar o modo de depuração como verdadeiro por padrão para resolver problemas de Streamlit Cloud
    if 'DEBUG_MODE' not in st.session_state:
        st.session_state.DEBUG_MODE = True
    
    try:
        st.title("🏢 Análise de Cartórios")
        
        # Sidebar com opções de depuração
        with st.sidebar:
            st.subheader("Opções de Depuração")
            debug_mode = st.checkbox("Ativar modo de depuração", value=st.session_state.DEBUG_MODE)
            st.session_state.DEBUG_MODE = debug_mode
            
            # Opções adicionais quando o modo de depuração está ativado
            if debug_mode:
                st.session_state.DISABLE_ANIMATIONS = st.checkbox(
                    "Desativar animações", 
                    value=st.session_state.get('DISABLE_ANIMATIONS', False),
                    help="Útil se estiver enfrentando problemas com animações"
                )
                
                st.session_state.LOAD_BASIC_DATA_ONLY = st.checkbox(
                    "Carregar apenas dados básicos", 
                    value=st.session_state.get('LOAD_BASIC_DATA_ONLY', False),
                    help="Carrega apenas dados essenciais para depuração"
                )
                
                # Exibir informações de diagnóstico
                st.subheader("Informações de Diagnóstico")
                st.write(f"Versão do Streamlit: {st.__version__}")
                st.write(f"Diretório de trabalho: {os.getcwd()}")
                st.write(f"Arquivos no diretório atual: {len(os.listdir())}")
                
                # Verificar se os secrets estão disponíveis
                try:
                    secrets_available = hasattr(st, 'secrets') and 'bitrix_token' in st.secrets
                    st.write(f"Secrets disponíveis: {secrets_available}")
                except Exception as e:
                    st.error(f"Erro ao verificar secrets: {str(e)}")
        
        # Interface principal
        tabs = st.tabs(["Cadastro de Famílias", "Relatórios", "Sobre"])
        
        with tabs[0]:
            st.header("Cadastro de Famílias")
            
            # Opções de análise
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Analisar Famílias Ausentes", type="primary"):
                    # Usar um try/except específico para a funcionalidade
                    try:
                        # Chame a função com base nas configurações de animação
                        use_animation = not st.session_state.get('DISABLE_ANIMATIONS', False)
                        total_ausentes, df_resultado = analisar_familias_ausentes(use_animation)
                        
                        # Exibir resultados
                        if total_ausentes > 0:
                            st.subheader(f"📊 {total_ausentes} famílias não cadastradas")
                            st.dataframe(df_resultado, use_container_width=True)
                            
                            # Criar um container para os botões de download
                            download_col1, download_col2 = st.columns(2)
                            
                            # Opção para exportar os resultados para Excel
                            with download_col1:
                                try:
                                    st.download_button(
                                        label="📥 Exportar para Excel",
                                        data=convert_df_to_excel(df_resultado),
                                        file_name="familias_ausentes.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                                except Exception as e:
                                    if st.session_state.DEBUG_MODE:
                                        st.error(f"Erro ao gerar Excel: {str(e)}")
                            
                            # Opção para exportar os resultados para CSV
                            with download_col2:
                                try:
                                    st.download_button(
                                        label="📥 Exportar para CSV",
                                        data=convert_df_to_csv(df_resultado),
                                        file_name="familias_ausentes.csv",
                                        mime="text/csv"
                                    )
                                except Exception as e:
                                    if st.session_state.DEBUG_MODE:
                                        st.error(f"Erro ao gerar CSV: {str(e)}")
                        else:
                            st.success("✅ Todas as famílias estão corretamente cadastradas!")
                    except Exception as e:
                        st.error(f"Erro durante a análise de famílias ausentes: {str(e)}")
                        if st.session_state.DEBUG_MODE:
                            import traceback
                            st.code(traceback.format_exc())
            
            with col2:
                # Adicionar opções futuras aqui
                pass
        
        with tabs[1]:
            st.header("Relatórios")
            
            # Carregar dados dos cartórios
            try:
                with st.spinner("Carregando dados dos cartórios..."):
                    df_cartorio = carregar_dados_cartorio()
                
                if df_cartorio is None or df_cartorio.empty:
                    st.warning("Não foi possível carregar os dados dos cartórios. Verifique a conexão com o Bitrix24.")
                else:
                    # Adicionar filtros
                    cartorio_filter = st.multiselect(
                        "Filtrar por Cartório:",
                        df_cartorio['NOME_CARTORIO'].unique().tolist(),
                        default=df_cartorio['NOME_CARTORIO'].unique().tolist()
                    )
                    
                    if cartorio_filter:
                        df_filtrado = df_cartorio[df_cartorio['NOME_CARTORIO'].isin(cartorio_filter)]
                        
                        # Verificar se há dados após a filtragem
                        if not df_filtrado.empty:
                            # Determinar se as animações devem ser usadas
                            use_animation = not st.session_state.get('DISABLE_ANIMATIONS', False)
                            
                            # Visualizar os dados com ou sem animações
                            visualizar_cartorio_dados(df_filtrado, use_animation)
                        else:
                            st.warning("Nenhum dado disponível após a aplicação dos filtros.")
                    else:
                        st.info("Selecione pelo menos um cartório para visualizar os dados.")
            except Exception as e:
                st.error(f"Erro ao carregar ou processar dados dos cartórios: {str(e)}")
                if st.session_state.DEBUG_MODE:
                    import traceback
                    st.code(traceback.format_exc())
        
        with tabs[2]:
            st.header("Sobre")
            st.markdown("""
            ### Análise de Cartórios
            
            Este módulo permite analisar os processos em cartório e verificar o cadastro de famílias no sistema.
            
            **Recursos disponíveis:**
            - Análise de famílias ausentes no cadastro
            - Visualização de métricas e gráficos sobre processos em cartório
            - Exportação de dados para Excel
            
            **Em caso de problemas:**
            1. Ative o modo de depuração no painel lateral
            2. Tente desativar as animações se estiver enfrentando problemas de carregamento
            3. Verifique os logs de erro para diagnóstico
            """)
            
            # Exibir versão
            st.caption("Versão 1.0.1 | Dados atualizados em tempo real do Bitrix24")
    
    except Exception as e:
        st.error(f"Erro ao exibir a interface de análise de cartórios: {str(e)}")
        if st.session_state.DEBUG_MODE:
            import traceback
            st.code(traceback.format_exc())

def convert_df_to_excel(df):
    """
    Converte um DataFrame para o formato Excel.
    
    Args:
        df (pd.DataFrame): DataFrame a ser convertido
        
    Returns:
        bytes: Conteúdo do Excel em formato de bytes
    """
    try:
        # Criar um buffer para armazenar o arquivo Excel
        output = io.BytesIO()
        
        # Criar o objeto Excel Writer
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Escrever o DataFrame para o Excel
            df.to_excel(writer, sheet_name='Dados', index=False)
            
            # Acessar a planilha para formatação
            workbook = writer.book
            worksheet = writer.sheets['Dados']
            
            # Formatar o cabeçalho
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Aplicar formatação ao cabeçalho
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Ajustar largura das colunas
            for i, col in enumerate(df.columns):
                # Encontrar a largura máxima na coluna
                max_len = max(
                    df[col].astype(str).apply(len).max(),  # Comprimento máximo dos dados
                    len(str(col))  # Comprimento do cabeçalho
                ) + 2  # Adicionar um pouco de espaço extra
                
                # Definir a largura da coluna (limitando a um máximo razoável)
                worksheet.set_column(i, i, min(max_len, 50))
        
        # Obter os bytes do buffer
        output.seek(0)
        return output.getvalue()
    
    except Exception as e:
        import traceback
        st.error(f"Erro ao converter DataFrame para Excel: {str(e)}")
        st.code(traceback.format_exc())
        
        # Em caso de erro, retornar um Excel simples sem formatação
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer.getvalue()

def convert_df_to_csv(df):
    """
    Converte um DataFrame para o formato CSV.
    
    Args:
        df (pd.DataFrame): DataFrame a ser convertido
        
    Returns:
        bytes: Conteúdo do CSV em formato de bytes
    """
    try:
        # Converter para CSV
        return df.to_csv(index=False).encode('utf-8-sig')
    except Exception as e:
        if st.session_state.get('DEBUG_MODE', False):
            import traceback
            st.error(f"Erro ao converter DataFrame para CSV: {str(e)}")
            st.code(traceback.format_exc())
        
        # Fallback simples em caso de erro
        return df.to_csv(index=False).encode('utf-8') 