import streamlit as st
import pandas as pd
import altair as alt
from utils.google_sheets_connector import get_google_sheets_client, fetch_data_from_sheet

# Importar para conectar ao Bitrix24
import sys
from pathlib import Path
api_path = Path(__file__).parents[2] / 'api'
sys.path.insert(0, str(api_path))
from bitrix_connector import load_bitrix_data, load_merged_data

# Configurações da planilha
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1pB3HTFsaHyqAt3bhxzWG3RjfAxAzl97ydGqT35uYb-w/edit?gid=0#gid=0'
SHEET_NAME = 'Base Higienização'

# Mapeamento das colunas da planilha
COLUNAS_DA_PLANILHA = [
    'BUISCADOR',
    'ID FAMILIA',
    'Nome da\nfamilia ',
    'Certidão a emitir ',
    'DATA \nSOLICITAÇÃO',
    'PROTROCOLADO',
    'ITALIA',
    'STATUS\ncomune',  # Coluna AB para funil de conversão
    'PRIORIDADE',  # Coluna X com informações de priorização
    'DATA \nEMISSÃO',  # Coluna AE com data de emissão
    'HIGIENIZAÇÃO\nHENRIQUE',
    'HIGIENIZAÇÃO\nHENRIQUE\nData Higienização'
]

# Possíveis nomes da coluna de priorização na planilha
POSSIVEIS_COLUNAS_PRIORIZACAO = [
    'PRIORIDADE',
    'RESPONSÁVEL',
    'RESPONSAVEL', 
    'ATRIBUIDO',
    'ATRIBUÍDO',
    'PRIORIZAÇÃO',
    'PRIORIZACAO',
    'PRIORITY'
]

MAPEAMENTO_COLUNAS = {
    'BUISCADOR': 'buscador',
    'ID FAMILIA': 'id_familia',
    'Nome da\nfamilia ': 'nome_familia',
    'Certidão a emitir ': 'certidao_a_emitir',
    'DATA \nSOLICITAÇÃO': 'data_solicitacao',
    'PROTROCOLADO': 'protocolado',
    'ITALIA': 'italia',
    'STATUS\ncomune': 'status_comune',  # Coluna AB para funil
    'PRIORIDADE': 'prioridade',  # Coluna X de priorização
    'DATA \nEMISSÃO': 'data_emissao',  # Coluna AE de emissão
    'HIGIENIZAÇÃO\nHENRIQUE': 'status_higienizacao_henrique', 
    'HIGIENIZAÇÃO\nHENRIQUE\nData Higienização': 'data_higienizacao_henrique'
}

# Adicionar os possíveis nomes ao mapeamento de colunas
for nome_col in POSSIVEIS_COLUNAS_PRIORIZACAO:
    if nome_col not in MAPEAMENTO_COLUNAS:
        MAPEAMENTO_COLUNAS[nome_col] = 'prioridade'

# Nomes das colunas após mapeamento
NOME_COLUNA_STATUS_HIGIENIZACAO = 'status_higienizacao_henrique'
NOME_COLUNA_DATA_HIGIENIZACAO = 'data_higienizacao_henrique'
NOME_COLUNA_STATUS_COMUNE = 'status_comune'

@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados_bitrix_funil46():
    """Carrega dados do Bitrix24 funil 46 para cruzamento."""
    try:
        # Carregar dados do funil 46 usando load_merged_data
        df_bitrix = load_merged_data(
            category_id=46,
            debug=False,
            force_reload=False
        )
        
        if df_bitrix is not None and not df_bitrix.empty:
            # Selecionar apenas as colunas necessárias se existirem
            colunas_necessarias = [
                'ID', 
                'UF_CRM_1722605592778',  # Campo para match com ID FAMILIA
                'UF_CRM_1746046353172'   # Campo de informação adicional
            ]
            
            # Verificar quais colunas existem
            colunas_existentes = [col for col in colunas_necessarias if col in df_bitrix.columns]
            
            if colunas_existentes:
                # st.info(f"✅ Dados do Bitrix24 funil 46 carregados: {len(df_bitrix)} registros")
                return df_bitrix[colunas_existentes].copy()
            else:
                st.warning(f"⚠️ Colunas necessárias não encontradas no Bitrix. Disponíveis: {list(df_bitrix.columns)}")
                # Retornar pelo menos as colunas que existem
                colunas_disponiveis = [col for col in df_bitrix.columns if 'UF_CRM_' in col or col == 'ID'][:10]
                if colunas_disponiveis:
                    return df_bitrix[colunas_disponiveis].copy()
                else:
                    return df_bitrix.copy()
        else:
            st.warning("⚠️ Nenhum dado encontrado no funil 46 do Bitrix24.")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do Bitrix24: {str(e)}")
        return pd.DataFrame()

def fazer_cruzamento_bitrix(df_planilha):
    """Faz o cruzamento entre dados da planilha e Bitrix24."""
    
    # Carregar dados do Bitrix
    df_bitrix = carregar_dados_bitrix_funil46()
    
    if df_bitrix.empty:
        st.warning("⚠️ Nenhum dado foi retornado do Bitrix24 funil 46.")
        return df_planilha.copy(), df_bitrix
    
    # Preparar dados para cruzamento
    if 'id_familia' not in df_planilha.columns:
        st.warning("⚠️ Coluna 'id_familia' não encontrada na planilha.")
        return df_planilha.copy(), df_bitrix
    
    # Verificar qual coluna usar para o match
    coluna_match_bitrix = None
    if 'UF_CRM_1722605592778' in df_bitrix.columns:
        coluna_match_bitrix = 'UF_CRM_1722605592778'
    else:
        # Procurar colunas similares
        colunas_similares = [col for col in df_bitrix.columns if '1722605592778' in str(col)]
        if colunas_similares:
            coluna_match_bitrix = colunas_similares[0]
        else:
            st.error("❌ Campo UF_CRM_1722605592778 não encontrado no Bitrix24.")
            return df_planilha.copy(), df_bitrix
    
    # Preparar dados para merge (garantir que sejam strings)
    df_planilha_prep = df_planilha.copy()
    df_bitrix_prep = df_bitrix.copy()
    
    df_planilha_prep['id_familia'] = df_planilha_prep['id_familia'].astype(str).str.strip()
    df_bitrix_prep[coluna_match_bitrix] = df_bitrix_prep[coluna_match_bitrix].astype(str).str.strip()
    
    # Verificar se há colunas conflitantes antes do merge
    colunas_planilha = set(df_planilha_prep.columns)
    colunas_bitrix = set(df_bitrix_prep.columns)
    colunas_conflitantes = colunas_planilha.intersection(colunas_bitrix)
    
    # Remover colunas conflitantes do Bitrix (exceto a coluna de match)
    if colunas_conflitantes:
        colunas_para_remover = [col for col in colunas_conflitantes if col != coluna_match_bitrix]
        if colunas_para_remover:
            st.info(f"🔄 Removendo colunas conflitantes do Bitrix: {', '.join(colunas_para_remover)}")
            df_bitrix_prep = df_bitrix_prep.drop(columns=colunas_para_remover)
    
    # Fazer o merge baseado em ID FAMILIA
    try:
        # Verificar duplicatas antes do merge
        colunas_planilha_antes = len(df_planilha_prep.columns)
        df_planilha_prep = df_planilha_prep.loc[:, ~df_planilha_prep.columns.duplicated()]
        colunas_planilha_depois = len(df_planilha_prep.columns)
        
        colunas_bitrix_antes = len(df_bitrix_prep.columns)
        df_bitrix_prep = df_bitrix_prep.loc[:, ~df_bitrix_prep.columns.duplicated()]
        colunas_bitrix_depois = len(df_bitrix_prep.columns)
        
        if colunas_planilha_antes != colunas_planilha_depois:
            # Remover log de colunas removidas da planilha
            pass
            
        if colunas_bitrix_antes != colunas_bitrix_depois:
            # Remover log de colunas removidas do Bitrix  
            pass
        
        df_cruzado = df_planilha_prep.merge(
            df_bitrix_prep,
            left_on='id_familia',
            right_on=coluna_match_bitrix,
            how='left',
            suffixes=('', '_bitrix')
        )
        
        # Verificar se há colunas duplicadas após merge
        colunas_duplicadas = []
        colunas_vistas = set()
        for col in df_cruzado.columns:
            if col in colunas_vistas:
                colunas_duplicadas.append(col)
            colunas_vistas.add(col)
        
        if colunas_duplicadas:
            # Remover log de colunas duplicadas após merge
            # Remover colunas duplicadas mantendo a primeira ocorrência
            df_cruzado = df_cruzado.loc[:, ~df_cruzado.columns.duplicated()]
        
        return df_cruzado, df_bitrix
        
    except Exception as e:
        st.error(f"❌ Erro no cruzamento de dados: {str(e)}")
        return df_planilha.copy(), df_bitrix

def show_producao_comune():
    """Exibe a página de Produção Comune com métricas e análises."""
    
    # Carregar estilos CSS
    try:
        with open('assets/styles/css/main.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS não encontrado. Execute a compilação SCSS.")

    # Título principal
    st.markdown('<h1 class="producao-comune-title">Produção Comune</h1>', unsafe_allow_html=True)
    st.markdown("**Análise de dados da planilha de produção do Comune.**")

    # Conectar ao Google Sheets
    client = get_google_sheets_client()
    if not client:
        st.error("❌ Não foi possível conectar ao Google Sheets. Verifique as credenciais.")
        return

    # Carregar dados
    data = fetch_data_from_sheet(client, SPREADSHEET_URL, SHEET_NAME)
    if data is None:
        st.warning("⚠️ Não foi possível carregar os dados da planilha.")
        return

    df = pd.DataFrame(data)
    if df.empty:
        st.info("📋 A planilha está vazia ou não foi possível ler os dados.")
        return

    # Processamento dos dados
    df_processado = processar_dados(df)
    if df_processado is None:
        return

    # Fazer cruzamento com Bitrix24
    df_cruzado, df_bitrix = fazer_cruzamento_bitrix(df_processado)

    # Adicionar coluna de priorização
    df_cruzado['priorizacao'] = determinar_priorizacao(df_cruzado)

    # --- FILTROS ---
    with st.expander("🔍 Filtros", expanded=True):
        col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns([0.25, 0.25, 0.25, 0.25])
        
        with col_filtro1:
            filtro_protocolizado = st.selectbox(
                "Status Protocolização:",
                options=["TODOS", "PROTOCOLADO", "NÃO PROTOCOLADO"],
                index=0,
                key="filtro_protocolizado_producao"
            )
        
        with col_filtro2:
            # Filtro de priorização
            opcoes_priorizacao = ["TODOS"] + list(df_cruzado['priorizacao'].unique())
            filtro_priorizacao = st.selectbox(
                "Priorização:",
                options=opcoes_priorizacao,
                index=0,
                key="filtro_priorizacao_producao"
            )
        
        with col_filtro3:
            # Filtro de nome da família
            termo_familia = st.text_input(
                "Buscar Família:",
                placeholder="Digite o nome da família...",
                key="busca_familia_producao"
            )
        
        with col_filtro4:
            # Filtro de data de emissão
            filtro_data_emissao = st.selectbox(
                "Data de Emissão:",
                options=["TODOS", "COM DATA", "SEM DATA"],
                index=0,
                key="filtro_data_emissao_producao"
            )

    # Aplicar filtros
    df_filtrado = aplicar_filtros_producao(df_processado, filtro_protocolizado, df_cruzado, filtro_data_emissao)
    df_cruzado_filtrado = aplicar_filtros_producao(df_cruzado, filtro_protocolizado, df_cruzado, filtro_data_emissao)
    
    # Aplicar filtro de priorização
    if filtro_priorizacao != "TODOS":
        df_cruzado_filtrado = df_cruzado_filtrado[df_cruzado_filtrado['priorizacao'] == filtro_priorizacao]
        # Sincronizar índices
        df_filtrado = df_filtrado.loc[df_filtrado.index.intersection(df_cruzado_filtrado.index)]
    
    # Aplicar filtro de família
    if termo_familia and 'nome_familia' in df_filtrado.columns:
        mask_familia = df_filtrado['nome_familia'].fillna('').astype(str).str.contains(termo_familia, case=False, na=False)
        df_filtrado = df_filtrado[mask_familia]
        df_cruzado_filtrado = df_cruzado_filtrado.loc[df_cruzado_filtrado.index.intersection(df_filtrado.index)]

    # Verificar se há dados após filtros
    if df_filtrado.empty:
        st.info("📋 Nenhum dado encontrado para os filtros selecionados.")
        return

    # Renderizar seções
    renderizar_metricas_com_filtros(df_filtrado, df_cruzado_filtrado)
    renderizar_analise_priorizacao(df_cruzado_filtrado)
    
    renderizar_analise_protocolizacao(df_cruzado_filtrado, df_bitrix)
    renderizar_status_higienizacao(df_filtrado)
    renderizar_grafico_temporal(df_filtrado)
    renderizar_grafico_emissoes_por_data(df_filtrado)
    renderizar_tabela_dados_com_priorizacao(df_cruzado_filtrado)

def processar_dados(df):
    """Processa e limpa os dados da planilha."""
    
    # Converter ID FAMILIA para string
    if 'ID FAMILIA' in df.columns:
        try:
            df['ID FAMILIA'] = df['ID FAMILIA'].astype(str)
        except Exception as e:
            st.warning(f"⚠️ Erro ao converter ID FAMILIA: {e}")

    # Verificar colunas existentes da lista padrão
    colunas_existentes = [col for col in COLUNAS_DA_PLANILHA if col in df.columns]
    
    # Procurar por colunas de priorização adicionais
    colunas_priorizacao_encontradas = []
    for col in df.columns:
        col_upper = col.upper().strip()
        if any(termo in col_upper for termo in ['PRIORI', 'RESPONSAV', 'ATRIBUI', 'PRIORITY']):
            if col not in colunas_existentes:
                colunas_priorizacao_encontradas.append(col)
    
    # Procurar por colunas de data emissão adicionais
    colunas_emissao_encontradas = []
    for col in df.columns:
        col_upper = col.upper().strip()
        if any(termo in col_upper for termo in ['EMISSÃO', 'EMISSAO', 'EMISSION']):
            if col not in colunas_existentes:
                colunas_emissao_encontradas.append(col)
    
    # Adicionar colunas encontradas (evitando duplicatas)
    for col in colunas_priorizacao_encontradas:
        if col not in colunas_existentes:
            colunas_existentes.append(col)
    
    for col in colunas_emissao_encontradas:
        if col not in colunas_existentes:
            colunas_existentes.append(col)
    
    if not colunas_existentes:
        st.error("❌ Nenhuma das colunas esperadas foi encontrada na planilha.")
        return None
    
    # Selecionar colunas existentes (removendo duplicatas)
    colunas_unicas = list(dict.fromkeys(colunas_existentes))  # Remove duplicatas mantendo ordem
    df_selecionado = df[colunas_unicas].copy()
    
    # Criar mapeamento dinâmico incluindo colunas encontradas
    mapeamento_completo = MAPEAMENTO_COLUNAS.copy()
    
    # Adicionar colunas de priorização ao mapeamento (se não estiverem já)
    for col in colunas_priorizacao_encontradas:
        if col not in mapeamento_completo:
            mapeamento_completo[col] = 'prioridade'
    
    # Adicionar colunas de data emissão ao mapeamento (se não estiverem já)
    for col in colunas_emissao_encontradas:
        if col not in mapeamento_completo:
            mapeamento_completo[col] = 'data_emissao'
    
    # Renomear colunas usando mapeamento completo
    colunas_para_renomear = {k: v for k, v in mapeamento_completo.items() if k in df_selecionado.columns}
    df_renomeado = df_selecionado.rename(columns=colunas_para_renomear)
    
    # Verificar e remover colunas duplicadas após renomeação
    colunas_finais = df_renomeado.columns.tolist()
    colunas_sem_duplicatas = []
    colunas_vistas = set()
    
    for col in colunas_finais:
        if col not in colunas_vistas:
            colunas_sem_duplicatas.append(col)
            colunas_vistas.add(col)
    
    # Selecionar apenas colunas únicas
    df_final = df_renomeado[colunas_sem_duplicatas].copy()
    
    # Verificação adicional com pandas para garantir que não há duplicatas
    try:
        # Usar o método do pandas para verificar e remover duplicatas
        colunas_antes = len(df_final.columns)
        df_final = df_final.loc[:, ~df_final.columns.duplicated()]
        colunas_depois = len(df_final.columns)
        
    except Exception as e:
        st.warning(f"⚠️ Erro na verificação adicional de duplicatas: {str(e)}")
    
    return df_final

def renderizar_metricas_com_filtros(df_processado, df_cruzado=None):
    """Renderiza as métricas principais com filtros."""
    
    st.markdown('<h2 class="producao-comune-subtitle">Métricas Principais</h2>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="producao-comune-metricas producao-comune-metricas--neutral">', unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_familias = calcular_total_familias(df_processado)
            st.metric("👨‍👩‍👧‍👦 Total de Famílias", total_familias)
        
        with col2:
            num_higienizadas = calcular_familias_higienizadas(df_processado)
            st.metric("✅ Famílias Higienizadas", num_higienizadas)
        
        with col3:
            # Calcular Taxa de Conversão: (Higienizadas / Total) * 100
            total_familias = calcular_total_familias(df_processado)
            num_higienizadas = calcular_familias_higienizadas(df_processado)
            
            if total_familias > 0:
                taxa_conversao = (num_higienizadas / total_familias) * 100
                taxa_formatada = f"{taxa_conversao:.1f}%"
            else:
                taxa_formatada = "0.0%"
            
            st.metric("📊 Taxa de Conversão", taxa_formatada)
        
        with col4:
            # Calcular famílias protocolizadas do cruzamento Bitrix
            num_protocolizadas = 0
            if df_cruzado is not None and not df_cruzado.empty:
                # Buscar campo UF_CRM_1746046353172 no cruzamento
                if 'UF_CRM_1746046353172' in df_cruzado.columns:
                    num_protocolizadas = df_cruzado['UF_CRM_1746046353172'].str.contains('PROTOCOL', case=False, na=False).sum()
            
            st.metric("📋 Famílias Protocolizadas", num_protocolizadas)
        
        with col5:
            # Calcular total de emissões
            total_emissoes = calcular_total_emissoes(df_processado)
            st.metric("📋 Total de Emissões", total_emissoes)
        
        st.markdown('</div>', unsafe_allow_html=True)

def renderizar_analise_priorizacao(df_cruzado):
    """Renderiza análise de priorização das famílias em formato de tabela."""
    
    if df_cruzado.empty or 'priorizacao' not in df_cruzado.columns:
        return
    
    st.markdown('<h2 class="producao-comune-subtitle">👤 Análise de Priorização</h2>', unsafe_allow_html=True)
    
    contagem_priorizacao = df_cruzado['priorizacao'].value_counts()
    total = len(df_cruzado)
    
    # Criar DataFrame para a tabela
    dados_tabela = []
    
    for prioridade, count in contagem_priorizacao.items():
        percentual = (count / total * 100) if total > 0 else 0
        
        # Definir ícone baseado na prioridade
        if "ANGÉLICA" in prioridade:
            icone = "👩‍💼"
        elif "LUCAS" in prioridade:
            icone = "👨‍💼"
        else:
            icone = "📄"
        
        dados_tabela.append({
            'Ícone': icone,
            'Priorização': prioridade.title(),
            'Quantidade': count,
            'Percentual': f"{percentual:.1f}%"
        })
    
    # Criar DataFrame
    df_priorizacao = pd.DataFrame(dados_tabela)
    
    # Renderizar tabela
    with st.container():
        st.markdown('<div class="producao-comune-data-table">', unsafe_allow_html=True)
        st.dataframe(
            df_priorizacao, 
            use_container_width=True,
            hide_index=True,
            column_config={
                'Ícone': st.column_config.TextColumn(
                    width="small"
                ),
                'Priorização': st.column_config.TextColumn(
                    width="medium"
                ),
                'Quantidade': st.column_config.NumberColumn(
                    width="small"
                ),
                'Percentual': st.column_config.TextColumn(
                    width="small"
                )
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)

def renderizar_analise_protocolizacao(df_cruzado, df_bitrix):
    """Renderiza tabela simples com as famílias protocolizadas."""
    
    if df_bitrix.empty:
        return
    
    # Descobrir qual coluna foi usada no match
    coluna_match_encontrada = None
    for col in df_cruzado.columns:
        if 'UF_CRM_1722605592778' in str(col) and not col.endswith('_bitrix'):
            coluna_match_encontrada = col
            break
    
    if not coluna_match_encontrada or df_cruzado[coluna_match_encontrada].notna().sum() == 0:
        return
    
    # Filtrar famílias com dados do Bitrix
    df_com_bitrix = df_cruzado[df_cruzado[coluna_match_encontrada].notna()].copy()
    
    # Filtrar famílias protocolizadas
    if 'UF_CRM_1746046353172' in df_com_bitrix.columns:
        mask_protocolizado = df_com_bitrix['UF_CRM_1746046353172'].str.contains('PROTOCOL', case=False, na=False)
        df_protocolizadas = df_com_bitrix[mask_protocolizado].copy()
        
        if not df_protocolizadas.empty:
            st.markdown('<h2 class="producao-comune-subtitle">📋 Famílias Protocolizadas</h2>', unsafe_allow_html=True)
            
            # Preparar dados para a tabela
            colunas_tabela = []
            dados_tabela = []
            
            # Adicionar número da linha
            dados_tabela.append(range(1, len(df_protocolizadas) + 1))
            colunas_tabela.append("Nº")
            
            # ID Família
            if 'id_familia' in df_protocolizadas.columns:
                dados_tabela.append(df_protocolizadas['id_familia'].values)
                colunas_tabela.append("ID Família")
            
            # Nome da Família  
            if 'nome_familia' in df_protocolizadas.columns:
                dados_tabela.append(df_protocolizadas['nome_familia'].values)
                colunas_tabela.append("Nome da Família")
            
            # Status de Protocolização
            dados_tabela.append(df_protocolizadas['UF_CRM_1746046353172'].values)
            colunas_tabela.append("Status Protocolização")
            
            # Procurar campo de prioridade (comuns: PRIORITY, PRIORIDADE, etc.)
            campos_prioridade = [col for col in df_protocolizadas.columns 
                               if any(termo in col.upper() for termo in ['PRIORITY', 'PRIORIDADE', 'URGENT', 'PRIORIT'])]
            
            if campos_prioridade:
                dados_tabela.append(df_protocolizadas[campos_prioridade[0]].values)
                colunas_tabela.append("Prioridade")
            
            # Outras colunas relevantes do Bitrix (limitadas)
            outras_colunas = [col for col in df_protocolizadas.columns 
                            if 'UF_CRM_' in col 
                            and col not in ['UF_CRM_1722605592778', 'UF_CRM_1746046353172']
                            and col not in colunas_tabela][:2]  # Máximo 2 colunas extras
            
            for col in outras_colunas:
                dados_tabela.append(df_protocolizadas[col].values)
                # Limpar nome da coluna
                nome_limpo = col.replace('UF_CRM_', '').replace('_', ' ').title()
                colunas_tabela.append(nome_limpo)
            
            # Criar DataFrame para exibição
            df_tabela = pd.DataFrame(dict(zip(colunas_tabela, dados_tabela)))
            
            with st.container():
                st.markdown('<div class="producao-comune-data-table">', unsafe_allow_html=True)
                st.caption(f"📋 Mostrando {len(df_protocolizadas)} famílias com status relacionado a PROTOCOLIZADO")
                st.dataframe(df_tabela, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

def renderizar_status_higienizacao(df):
    """Renderiza a tabela de status de higienização."""
    
    if NOME_COLUNA_STATUS_HIGIENIZACAO not in df.columns:
        return
        
    st.markdown('<h2 class="producao-comune-subtitle">Status de Higienização</h2>', unsafe_allow_html=True)
    
    contagem_higienizacao = df[NOME_COLUNA_STATUS_HIGIENIZACAO].value_counts()
    if not contagem_higienizacao.empty:
        with st.container():
            st.markdown('<div class="producao-comune-status-table">', unsafe_allow_html=True)
            df_status_display = contagem_higienizacao.reset_index()
            df_status_display.columns = ['Status', 'Contagem']
            st.dataframe(df_status_display, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

def renderizar_grafico_temporal(df):
    """Renderiza o gráfico de higienizações por data."""
    
    if NOME_COLUNA_DATA_HIGIENIZACAO not in df.columns:
        return
        
    st.markdown('<h2 class="producao-comune-subtitle">Higienizações por Data</h2>', unsafe_allow_html=True)
    
    if df[NOME_COLUNA_DATA_HIGIENIZACAO].replace('', pd.NaT).isna().all():
        st.info("📅 Não há dados de data de higienização disponíveis.")
        return

    try:
        df[NOME_COLUNA_DATA_HIGIENIZACAO] = pd.to_datetime(
            df[NOME_COLUNA_DATA_HIGIENIZACAO], 
            errors='coerce',
            format='%d/%m/%Y',  # Especificar formato brasileiro
            dayfirst=True
        )
    except Exception as e:
        st.error(f"❌ Erro ao converter as datas: {e}")
        return

    df_datas_validas = df.dropna(subset=[NOME_COLUNA_DATA_HIGIENIZACAO])

    if not df_datas_validas.empty:
        with st.container():
            st.markdown('<div class="adm-evolucao-grafico">', unsafe_allow_html=True)
            
            # Agrupar por data e contar higienizações
            df_agg = df_datas_validas.groupby(
                df_datas_validas[NOME_COLUNA_DATA_HIGIENIZACAO].dt.date
            ).size().reset_index(name='Higienizacoes')
            df_agg.rename(columns={NOME_COLUNA_DATA_HIGIENIZACAO: 'Data'}, inplace=True)
            
            # Converter Data para string formatada para evitar problemas com o tipo temporal
            df_agg['Data Formatada'] = pd.to_datetime(df_agg['Data']).dt.strftime('%d/%m/%Y')

            # Criar gráfico de barras com estilo do producao_adm.py
            barras = alt.Chart(df_agg).mark_bar(
                color='#4CAF50',  # Verde igual ao producao_adm.py
                size=60  # Barras largas
            ).encode(
                x=alt.X('Data Formatada:O', title='Data', sort=alt.SortField('Data')),
                y=alt.Y('Higienizacoes:Q', title='Quantidade de Higienizações'),
                tooltip=['Data Formatada:O', 'Higienizacoes:Q']
            )
            
            # Adicionar números em cima das barras
            texto = alt.Chart(df_agg).mark_text(
                align='center',
                baseline='bottom',
                dy=-5,  # Deslocamento vertical (acima da barra)
                fontSize=16,
                fontWeight='bold'
            ).encode(
                x='Data Formatada:O',
                y='Higienizacoes:Q',
                text='Higienizacoes:Q'
            )
            
            # Combinar gráficos (barras + texto)
            chart = (barras + texto).properties(
                title='Total de Higienizações Diárias (Henrique)',
                height=300
            ).configure_title(
                fontSize=16
            )
            
            st.altair_chart(chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📅 Não há dados de data válidos para gerar o gráfico.")

def renderizar_grafico_emissoes_por_data(df):
    """Renderiza o gráfico de emissões por data para casos entregues."""
    
    # Verificar se temos as colunas necessárias
    if 'data_emissao' not in df.columns:
        st.info("📅 Coluna de data de emissão não encontrada na planilha.")
        return
        
    if NOME_COLUNA_STATUS_COMUNE not in df.columns:
        st.info("📅 Coluna de status do comune não encontrada.")
        return
    
    # Verificar e remover colunas duplicadas
    try:
        colunas_originais = len(df.columns)
        df_limpo = df.loc[:, ~df.columns.duplicated()].copy()
        colunas_apos_limpeza = len(df_limpo.columns)
        
        # Remover log informativo sobre duplicatas removidas
            
    except Exception as e:
        st.error(f"❌ Erro ao limpar colunas duplicadas: {str(e)}")
        return
        
    st.markdown('<h2 class="producao-comune-subtitle">📊 Emissões por Data (Casos Entregues)</h2>', unsafe_allow_html=True)
    
    # Filtrar apenas casos GANHO (entregues)
    try:
        df_temp = df_limpo.copy()
        df_temp['CATEGORIA'] = df_temp[NOME_COLUNA_STATUS_COMUNE].apply(categorizar_status_comune)
        df_entregues = df_temp[df_temp['CATEGORIA'] == 'GANHO'].copy()
    except Exception as e:
        st.error(f"❌ Erro ao filtrar casos entregues: {str(e)}")
        return
    
    if df_entregues.empty:
        st.info("📅 Não há casos entregues disponíveis para análise.")
        return
    
    # Verificar se há dados de emissão
    try:
        # Simplesmente tentar converter diretamente para verificar se há dados válidos
        teste_conversao = pd.to_datetime(
            df_entregues['data_emissao'], 
            errors='coerce',
            format='%d/%m/%Y',
            dayfirst=True
        )
        datas_validas_count = teste_conversao.notna().sum()
        
        if datas_validas_count == 0:
            st.info("📅 Não há dados de data de emissão válidos para casos entregues.")
            return
        
    except Exception as e:
        st.error(f"❌ Erro ao verificar dados de emissão: {str(e)}")
        return

    # Converter datas de emissão
    try:
        df_entregues['data_emissao_convertida'] = pd.to_datetime(
            df_entregues['data_emissao'], 
            errors='coerce',
            format='%d/%m/%Y',  # Especificar formato brasileiro
            dayfirst=True  # Assumir formato DD/MM/YYYY
        )
        
        # Verificar quantas datas foram convertidas com sucesso
        datas_convertidas = df_entregues['data_emissao_convertida'].dropna()
        
        if datas_convertidas.empty:
            st.warning("⚠️ Nenhuma data de emissão pôde ser convertida. Verifique o formato das datas na planilha.")
            return
        
    except Exception as e:
        st.error(f"❌ Erro ao converter datas de emissão: {str(e)}")
        return

    # Filtrar registros com datas válidas
    df_datas_validas = df_entregues.dropna(subset=['data_emissao_convertida'])

    if df_datas_validas.empty:
        st.info("📅 Nenhuma data de emissão válida encontrada.")
        return

    try:
        with st.container():
            st.markdown('<div class="adm-evolucao-grafico">', unsafe_allow_html=True)
            
            # Agrupar por data e contar emissões
            df_agg = df_datas_validas.groupby(
                df_datas_validas['data_emissao_convertida'].dt.date
            ).size().reset_index(name='Emissoes')
            df_agg.rename(columns={'data_emissao_convertida': 'Data'}, inplace=True)
            
            # Converter Data para string formatada
            df_agg['Data Formatada'] = pd.to_datetime(df_agg['Data']).dt.strftime('%d/%m/%Y')
            
            # Ordenar por data
            df_agg = df_agg.sort_values('Data')

            # Criar gráfico de barras
            barras = alt.Chart(df_agg).mark_bar(
                color='#4CAF50',  # Verde igual ao gráfico de higienizações
                size=60  # Barras largas
            ).encode(
                x=alt.X('Data Formatada:O', 
                       title='Data de Emissão', 
                       sort=alt.SortField('Data')),
                y=alt.Y('Emissoes:Q', title='Quantidade de Emissões'),
                tooltip=['Data Formatada:O', 'Emissoes:Q']
            )
            
            # Adicionar números em cima das barras
            texto = alt.Chart(df_agg).mark_text(
                align='center',
                baseline='bottom',
                dy=-5,  # Deslocamento vertical (acima da barra)
                fontSize=16,  # Tamanho igual ao de higienizações
                fontWeight='bold'
            ).encode(
                x='Data Formatada:O',
                y='Emissoes:Q',
                text='Emissoes:Q'
            )
            
            # Combinar gráficos (barras + texto)
            total_emissoes_chart = int(df_agg['Emissoes'].sum())
            chart = (barras + texto).properties(
                title='Emissões de Documentos por Data',
                height=300  # Altura igual ao de higienizações
            ).configure_title(
                fontSize=16
            )
            
            st.altair_chart(chart, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Erro ao gerar gráfico de emissões: {str(e)}")
        return

def renderizar_tabela_dados_com_priorizacao(df):
    """Renderiza a tabela com todos os dados detalhados com priorização."""
    
    st.markdown('<h2 class="producao-comune-subtitle">Dados Detalhados</h2>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="producao-comune-data-table">', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

def calcular_total_familias(df):
    """Calcula o total de famílias únicas."""
    if 'id_familia' in df.columns:
        return len(df['id_familia'].unique())
    return len(df)

def calcular_familias_higienizadas(df):
    """Calcula o número de famílias higienizadas."""
    if NOME_COLUNA_STATUS_HIGIENIZACAO in df.columns:
        contagem = df[NOME_COLUNA_STATUS_HIGIENIZACAO].value_counts()
        return contagem.get('Higienizado', 0)
    return 0

def calcular_total_emissoes(df):
    """Calcula o total de emissões de documentos entregues."""
    try:
        # Verificar se temos as colunas necessárias
        if 'data_emissao' not in df.columns or NOME_COLUNA_STATUS_COMUNE not in df.columns:
            return 0
        
        # Filtrar apenas casos GANHO (entregues)
        df_temp = df.copy()
        df_temp['CATEGORIA'] = df_temp[NOME_COLUNA_STATUS_COMUNE].apply(categorizar_status_comune)
        df_entregues = df_temp[df_temp['CATEGORIA'] == 'GANHO'].copy()
        
        if df_entregues.empty:
            return 0
        
        # Converter datas de emissão e contar válidas
        datas_convertidas = pd.to_datetime(
            df_entregues['data_emissao'], 
            errors='coerce',
            format='%d/%m/%Y',
            dayfirst=True
        )
        
        return datas_convertidas.notna().sum()
        
    except Exception:
        return 0

def categorizar_status_comune(status):
    """Categoriza o status do comune em GANHO, EM ANDAMENTO ou PERCA."""
    if pd.isna(status):
        return "DESCONHECIDO"
    
    status_str = str(status).strip().upper()
    
    # Categorias conforme especificado no funil_certidoes_italianas.py
    perca = [
        'PENDENTE HIGIENIZAR',
        'PENDENTE', 
        'DADOS PENDENTES',
        'DEVOLUTIVA EMISSOR',
        'NEGATIVA COMUNE',
        'CANCELADO'
    ]
    
    em_andamento = [
        'SOLICITAR',
        'URGENTE',
        'AGUARDANDO COMUNE',
        'AGUARDANDO PARÓQUIA',
        'AGUARDANDO PAGAMENTO DA TAXA',
        'TAXA PAGA',
        'NECESSÁRIO REQUERIMENTO',
        'REQUERIMENTO CONCLUÍDO',
        'AGUARDANDO COMUNE/PARÓQUIA - TEM INFO',
        'AGUARDANDO PDF DO DOC'
    ]
    
    ganho = [
        'PDF DO DOC ENTREGUE',
        'DOCUMENTO FÍSICO ENTREGUE'
    ]
    
    if status_str in [s.upper() for s in ganho]:
        return 'GANHO'
    elif status_str in [s.upper() for s in perca]:
        return 'PERCA'
    elif status_str in [s.upper() for s in em_andamento]:
        return 'EM ANDAMENTO'
    else:
        return 'DESCONHECIDO'

def determinar_priorizacao(df_cruzado):
    """Determina a priorização baseada nos dados da planilha."""
    if df_cruzado.empty:
        return pd.Series(['VAZIO'] * len(df_cruzado), index=df_cruzado.index)
    
    priorizacao = []
    
    # Verificar se existe a coluna 'prioridade' diretamente na planilha
    if 'prioridade' in df_cruzado.columns:
        # Usar dados da coluna de prioridade da planilha
        for idx, row in df_cruzado.iterrows():
            valor_priorizacao = str(row.get('prioridade', '')).strip()
            
            if not valor_priorizacao or valor_priorizacao.upper() in ['NAN', 'NONE', '']:
                priorizacao.append("VAZIO")
            else:
                # Manter o valor original da planilha, apenas formatando
                priorizacao.append(valor_priorizacao.title())
        
        return pd.Series(priorizacao, index=df_cruzado.index)
    
    # Fallback: buscar por colunas que contenham informações de priorização
    colunas_priorizacao_planilha = [col for col in df_cruzado.columns 
                                   if any(termo in col.upper() for termo in ['PRIORI', 'RESPONSAV', 'ATRIBUI'])]
    
    if colunas_priorizacao_planilha:
        coluna_prioridade = colunas_priorizacao_planilha[0]  # Usar a primeira encontrada
        
        for idx, row in df_cruzado.iterrows():
            valor_priorizacao = str(row.get(coluna_prioridade, '')).upper().strip()
            
            if 'ANGELICA' in valor_priorizacao or 'ANGÉLICA' in valor_priorizacao:
                priorizacao.append("PRIORIZADO ANGÉLICA")
            elif 'LUCAS' in valor_priorizacao:
                priorizacao.append("PRIORIZADO LUCAS")
            elif 'PRESENCIAL' in valor_priorizacao:
                priorizacao.append("PRIORIDADE PRESENCIAL")
            elif valor_priorizacao and valor_priorizacao not in ['NAN', 'NONE', '']:
                priorizacao.append(valor_priorizacao.title())
            else:
                priorizacao.append("VAZIO")
    else:
        # Último fallback: buscar nos campos do Bitrix se não houver coluna na planilha
        campos_prioridade = [col for col in df_cruzado.columns 
                            if any(termo in col.upper() for termo in ['PRIORITY', 'PRIORIDADE', 'URGENT', 'PRIORIT', 'RESPONSAVEL', 'ATRIBUIDO'])]
        
        for idx, row in df_cruzado.iterrows():
            prioridade_encontrada = "VAZIO"
            
            # Verificar campos de prioridade
            for campo in campos_prioridade:
                valor = str(row.get(campo, '')).upper()
                if 'ANGELICA' in valor or 'ANGÉLICA' in valor:
                    prioridade_encontrada = "PRIORIZADO ANGÉLICA"
                    break
                elif 'LUCAS' in valor:
                    prioridade_encontrada = "PRIORIZADO LUCAS"
                    break
                elif 'PRESENCIAL' in valor:
                    prioridade_encontrada = "PRIORIDADE PRESENCIAL"
                    break
                elif valor and valor not in ['NAN', 'NONE', '']:
                    if any(nome in valor for nome in ['ANGELICA', 'ANGÉLICA', 'LUCAS']):
                        if 'ANGELICA' in valor or 'ANGÉLICA' in valor:
                            prioridade_encontrada = "PRIORIZADO ANGÉLICA"
                        elif 'LUCAS' in valor:
                            prioridade_encontrada = "PRIORIZADO LUCAS"
                        break
            
            priorizacao.append(prioridade_encontrada)
    
    return pd.Series(priorizacao, index=df_cruzado.index)

def aplicar_filtros_producao(df, filtro_protocolizado, df_cruzado=None, filtro_data_emissao=None):
    """Aplica filtros aos dados de produção."""
    df_filtrado = df.copy()
    
    # Filtro de protocolização
    if filtro_protocolizado != "TODOS" and df_cruzado is not None:
        # Verificar se há dados do Bitrix para determinar protocolização
        if 'UF_CRM_1746046353172' in df_cruzado.columns:
            mask_protocolizado = df_cruzado['UF_CRM_1746046353172'].str.contains('PROTOCOL', case=False, na=False)
            
            if filtro_protocolizado == "PROTOCOLADO":
                indices_protocolizados = df_cruzado[mask_protocolizado].index
                df_filtrado = df_filtrado.loc[df_filtrado.index.intersection(indices_protocolizados)]
            elif filtro_protocolizado == "NÃO PROTOCOLADO":
                indices_nao_protocolizados = df_cruzado[~mask_protocolizado].index
                df_filtrado = df_filtrado.loc[df_filtrado.index.intersection(indices_nao_protocolizados)]
    
    # Filtro de data de emissão
    if filtro_data_emissao != "TODOS" and filtro_data_emissao is not None:
        if 'data_emissao' in df_filtrado.columns:
            if filtro_data_emissao == "COM DATA":
                # Filtrar apenas registros com data de emissão preenchida
                mask_com_data = df_filtrado['data_emissao'].notna() & (df_filtrado['data_emissao'].astype(str).str.strip() != '')
                df_filtrado = df_filtrado[mask_com_data]
            elif filtro_data_emissao == "SEM DATA":
                # Filtrar apenas registros sem data de emissão
                mask_sem_data = df_filtrado['data_emissao'].isna() | (df_filtrado['data_emissao'].astype(str).str.strip() == '')
                df_filtrado = df_filtrado[mask_sem_data]
    
    return df_filtrado

# Para testes locais (opcional)
# if __name__ == '__main__':
#     show_producao_comune() 