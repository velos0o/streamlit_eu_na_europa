import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import sys
from pathlib import Path
import traceback

# Controle de depuração - definir como False em produção
DEBUG_MODE = False

# Função auxiliar para gerar dados simulados de reclamações
@st.cache_data(ttl=600) # Cache por 10 minutos para dados simulados
def _gerar_dados_simulados_reclamacoes():
    """
    Gera dados simulados para demonstração quando a API não está disponível
    """
    st.warning("⚠️ Usando dados simulados para demonstração. Recarregue ou clique em 'Atualizar Dados' para tentar novamente.")
    
    # Simular um atraso na carga para mostrar o spinner
    time.sleep(1)
    
    # Criar dados simulados
    data = {
        "ID": list(range(1, 51)),
        "DATA_CRIACAO": [(datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d") for _ in range(50)],
        "ADM_RESPONSAVEL": random.choices(["Ana Silva", "Carlos Santos", "Luciana Oliveira", "Pedro Almeida", "Maria Souza"], k=50),
        "CPF": [f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}" for _ in range(50)],
        "DEPARTAMENTO": random.choices(["Atendimento", "Financeiro", "Técnico", "Jurídico", "Comercial"], k=50),
        "DESCRICAO_RECLAMACAO": [
            "Problemas com processo de emissão",
            "Atraso na entrega de documentos",
            "Informações incorretas",
            "Valores cobrados indevidamente",
            "Falta de retorno do atendente",
            "Documentação recusada sem justificativa",
            "Sistema fora do ar durante processo",
            "Documento emitido com erro",
            "Cobrança em duplicidade",
            "Não recebi confirmação do pedido"
        ] * 5,
        "EMAIL": [f"cliente{i}@exemplo.com" for i in range(1, 51)],
        "ORIGEM": random.choices(["Site", "Telefone", "Email", "WhatsApp", "Presencial"], k=50),
        "TELEFONE": [f"({random.randint(11, 99)}) {random.randint(90000, 99999)}-{random.randint(1000, 9999)}" for _ in range(50)],
        "STATUS": random.choices(["Nova", "Em análise", "Respondida", "Resolvida", "Cancelada"], weights=[10, 30, 25, 25, 10], k=50)
    }
    
    df = pd.DataFrame(data)
    
    # Converter coluna de data para datetime
    df["DATA_CRIACAO"] = pd.to_datetime(df["DATA_CRIACAO"])
    
    # Ordenar por data de criação (mais recentes primeiro)
    df = df.sort_values(by="DATA_CRIACAO", ascending=False)
    
    return df

# Função para carregar dados da entidade 1086
@st.cache_data(ttl=600) # Cache por 10 minutos, pode ser ajustado
def carregar_dados_reclamacoes(force_reload=False, debug=DEBUG_MODE):
    """
    Carrega os dados da entidade 1086 (Reclamações) do Bitrix24
    
    Args:
        force_reload (bool): Se True, força o recarregamento dos dados ignorando o cache
        debug (bool): Se True, exibe informações de depuração
    
    Returns:
        pandas.DataFrame: DataFrame com os dados de reclamações
    """
    # Importar as funções necessárias do bi_connector aqui dentro para evitar ciclos
    try:
        # Tentar importar do caminho relativo padrão
        from api.bitrix_connector import load_bitrix_data, get_credentials
        if debug:
            st.info("Importado bitrix_connector de 'api.bitrix_connector'")
            
    except ImportError as e1:
        if debug:
            st.warning(f"Falha ao importar de api.bitrix_connector: {e1}")
        try:
            # Tentar importar do caminho raiz
            sys.path.insert(0, str(Path(__file__).parents[2])) # Vai para a raiz do projeto
            from api.bitrix_connector import load_bitrix_data, get_credentials
            if debug:
                st.success("Importado bitrix_connector da raiz do projeto.")
        except ImportError as e2:
            if debug:
                st.error(f"Erro final ao importar módulo bitrix_connector: {str(e2)}")
            return _gerar_dados_simulados_reclamacoes()

    # Limpar mensagens de depuração anteriores se não estiver em modo debug
    if not debug and 'limpar_mensagens_debug' not in st.session_state:
        st.session_state.limpar_mensagens_debug = st.empty()
    elif not debug and 'limpar_mensagens_debug' in st.session_state:
        st.session_state.limpar_mensagens_debug.empty()

    try:
        # Obter credenciais do Bitrix24
        BITRIX_TOKEN, BITRIX_URL = get_credentials()
        
        # Exibir informação sobre as credenciais para diagnóstico (ocultando o token completo)
        if debug:
            token_display = BITRIX_TOKEN[:5] + "*****" if BITRIX_TOKEN and len(BITRIX_TOKEN) > 5 else "Token não encontrado"
            st.info(f"Tentando conectar ao Bitrix: {BITRIX_URL} com token: {token_display}")
        
        # URL para a entidade 1086 no Bitrix24
        url_reclamacoes = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1086"
        
        # Tentar carregar dados
        with st.spinner("Carregando dados de reclamações do Bitrix24..."):
            filters = {"dimensionsFilters": [[]]} # Filtro vazio pode ajudar em alguns casos
            
            if debug:
                url_display = url_reclamacoes.replace(BITRIX_TOKEN, token_display)
                st.info(f"Tentando acessar: {url_display}")
            
            df_reclamacoes = load_bitrix_data(url_reclamacoes, filters=filters, show_logs=debug, force_reload=force_reload)
            
            if df_reclamacoes is None or df_reclamacoes.empty:
                if debug: st.warning("Tentativa 1 falhou. Tentando sem filtros...")
                df_reclamacoes = load_bitrix_data(url_reclamacoes, filters=None, show_logs=debug, force_reload=force_reload)
            
            if df_reclamacoes is None or df_reclamacoes.empty:
                if debug: st.warning("Tentativa 2 falhou. Tentando nomes alternativos de tabela...")
                alternate_urls = [
                    f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_1086",
                    f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_item_1086",
                    f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=b_crm_dynamic_items_1086"
                ]
                for url in alternate_urls:
                    if debug:
                        url_display = url.replace(BITRIX_TOKEN, token_display)
                        st.info(f"Tentando URL alternativa: {url_display}")
                    df_reclamacoes = load_bitrix_data(url, filters=None, show_logs=debug, force_reload=force_reload)
                    if df_reclamacoes is not None and not df_reclamacoes.empty:
                        if debug: st.success(f"Conexão bem-sucedida com URL alternativa!")
                        break
            
            if df_reclamacoes is None or df_reclamacoes.empty:
                st.error("❌ Não foi possível conectar à API Bitrix24 para carregar dados de reclamações.")
                if st.button("Tentar novamente", key="btn_retry_reclamacoes_api"):
                    st.rerun()
                return _gerar_dados_simulados_reclamacoes()
            
            if debug:
                st.success(f"Dados brutos carregados: {len(df_reclamacoes)} registros.")
                st.write("Amostra dados brutos:")
                st.write(f"Colunas: {list(df_reclamacoes.columns)}")
                if len(df_reclamacoes) > 0: st.write(df_reclamacoes.iloc[0])
            
            # --- Processamento dos dados ---
            colunas_mapeamento = {
                'ID': 'ID', 'TITLE': 'TITULO', 'DATE_CREATE': 'DATA_CRIACAO',
                'STAGE_ID': 'ID_ESTAGIO', 'ASSIGNED_BY_ID': 'ID_RESPONSAVEL',
                'ASSIGNED_BY_NAME': 'ADM_RESPONSAVEL', 'UF_CRM_28_CPF': 'CPF',
                'UF_CRM_28_DEPARTAMENTO': 'DEPARTAMENTO',
                'UF_CRM_28_DESCRICAO_RECLAMACAO': 'DESCRICAO_RECLAMACAO',
                'UF_CRM_28_EMAIL': 'EMAIL', 'UF_CRM_28_ORIGEM': 'ORIGEM',
                'UF_CRM_28_TELEFONE': 'TELEFONE', 'STAGE_NAME': 'STATUS'
            }
            
            df_processado = df_reclamacoes.copy()
            colunas_renomeadas = {}
            for col_original, col_novo in colunas_mapeamento.items():
                if col_original in df_processado.columns:
                    colunas_renomeadas[col_original] = col_novo
                else:
                    df_processado[col_novo] = None # Garante que a coluna exista
                    if debug: st.warning(f"Coluna esperada '{col_original}' não encontrada. Criando coluna '{col_novo}' vazia.")

            df_processado.rename(columns=colunas_renomeadas, inplace=True)

            if 'DATA_CRIACAO' in df_processado.columns:
                df_processado['DATA_CRIACAO'] = pd.to_datetime(df_processado['DATA_CRIACAO'], errors='coerce')
                df_processado = df_processado.sort_values(by="DATA_CRIACAO", ascending=False)
            else:
                 if debug: st.warning("Coluna 'DATA_CRIACAO' não encontrada para ordenação.")

            if debug: st.success(f"Dados processados: {len(df_processado)} reclamações.")

            if not debug and 'limpar_mensagens_debug' in st.session_state:
                st.session_state.limpar_mensagens_debug.empty()
            
            return df_processado
    
    except Exception as e:
        st.error(f"❌ Erro crítico ao carregar dados de reclamações: {str(e)}")
        if debug:
            st.code(traceback.format_exc(), language="python")
        return _gerar_dados_simulados_reclamacoes() 