import streamlit as st
import pandas as pd
from data.load_conclusao_higienizacao import load_conclusao_data
from views.cartorio_new.data_loader import carregar_dados_cartorio # Importar dados do cartório
from datetime import datetime, timedelta, date
import re # Para extrair ID da opção do selectbox
import numpy as np # Para operações numéricas

def aplicar_logica_precedencia_pipeline_104_higienizacao(df):
    """
    Aplica lógica de precedência específica para higienização no pipeline 104.
    
    CORRIGIDA DEZEMBRO 2024: Melhorada para tratar adequadamente a lógica de duplicação
    
    Regras especiais para higienização:
    1. Se pipeline 104 tem registros EM ANDAMENTO E existe pipeline superior (92, 94, 102):
       - Manter ambos (são processos paralelos)
    2. Se pipeline 104 tem "PESQUISA PRONTA PARA EMISSÃO" E existe pipeline superior ATIVO:
       - Ajustar para evitar duplicação nas métricas de "Pasta C/Emissão Concluída"
    3. Se pipeline 104 é o ÚNICO para a família: manter na contagem sempre
    
    IMPORTANTE: Ser mais conservador para não remover dados importantes
    """
    if 'CATEGORY_ID' not in df.columns or 'UF_CRM_34_ID_FAMILIA' not in df.columns:
        return df
    
    df_processado = df.copy()
    
    # Identificar famílias que têm pipeline 104
    familias_104 = df_processado[
        df_processado['CATEGORY_ID'].astype(str) == '104'
    ]['UF_CRM_34_ID_FAMILIA'].unique()
    
    if len(familias_104) == 0:
        return df_processado
    
    # Para cada família com 104, verificar se há conflito real de duplicação
    familias_para_ajustar_104 = []
    
    for id_familia in familias_104:
        registros_familia = df_processado[df_processado['UF_CRM_34_ID_FAMILIA'] == id_familia]
        
        # Verificar registros por pipeline
        registros_104 = registros_familia[registros_familia['CATEGORY_ID'].astype(str) == '104']
        registros_superiores = registros_familia[registros_familia['CATEGORY_ID'].astype(str).isin(['92', '94', '102'])]
        
        # Se tem pipelines superiores E pipeline 104
        if not registros_superiores.empty and not registros_104.empty:
            # Verificar se há 104 "pronto para emissão" 
            tem_104_pronto = registros_104['STAGE_ID'].str.contains('SUCCESS', na=False).any()
            
            # Verificar se os pipelines superiores estão ativos
            superiores_com_sucesso = registros_superiores['STAGE_ID'].str.contains('SUCCESS', na=False).any()
            
            if tem_104_pronto and superiores_com_sucesso:
                # Se há clara duplicação (ambos prontos/concluídos)
                familias_para_ajustar_104.append(id_familia)
                print(f"[DEBUG HIGIENIZAÇÃO] FAMÍLIA {id_familia}: Pipeline 104 pronto com pipeline superior concluído, ajustando para evitar duplicação")
            else:
                print(f"[DEBUG HIGIENIZAÇÃO] FAMÍLIA {id_familia}: Pipeline 104 e superiores coexistindo normalmente")
        else:
            print(f"[DEBUG HIGIENIZAÇÃO] FAMÍLIA {id_familia}: Apenas pipeline 104 ou sem conflito, mantendo na contagem")
    
    # AJUSTE CONSERVADOR: Em vez de remover completamente, apenas ajustar a contagem
    # quando há duplicação clara
    if familias_para_ajustar_104:
        # Para higienização, vamos manter uma abordagem mais conservadora
        # Removendo apenas quando há duplicação muito clara
        familias_para_remover_realmente = []
        
        for id_familia in familias_para_ajustar_104:
            registros_familia = df_processado[df_processado['UF_CRM_34_ID_FAMILIA'] == id_familia]
            registros_104 = registros_familia[registros_familia['CATEGORY_ID'].astype(str) == '104']
            registros_superiores = registros_familia[registros_familia['CATEGORY_ID'].astype(str).isin(['92', '94', '102'])]
            
            # Verificar se há duplicação MUITO clara (ambos concluídos)
            tem_104_success = registros_104['STAGE_ID'].str.contains('SUCCESS', na=False).any()
            tem_superiores_success = registros_superiores['STAGE_ID'].str.contains('SUCCESS', na=False).any()
            
            if tem_104_success and tem_superiores_success:
                # Só remover quando ambos estão "SUCCESS" (duplicação clara)
                familias_para_remover_realmente.append(id_familia)
        
        if familias_para_remover_realmente:
            mask_remover = (
                df_processado['UF_CRM_34_ID_FAMILIA'].isin(familias_para_remover_realmente) &
                (df_processado['CATEGORY_ID'].astype(str) == '104')
            )
            df_processado = df_processado[~mask_remover].copy()
            print(f"[DEBUG HIGIENIZAÇÃO] Removidos {mask_remover.sum()} registros do pipeline 104 devido à duplicação clara")
    
    return df_processado

# Função auxiliar para garantir tipos numéricos corretos para exibição
def ensure_numeric_display(df):
    # Lista de colunas que devem ser inteiras
    int_columns = [
        'PASTAS TOTAIS', 'HIGINIZAÇÃO COM ÊXITO', 'HIGINIZAÇÃO INCOMPLETA',
        'HIGINIZAÇÃO TRATADAS', 'DISTRATO', 'Brasileiras Pendências',
        'Brasileiras Pesquisas', 'Brasileiras Solicitadas', 'Brasileiras Emitida',
        'Pasta C/Emissão Concluída', 'Brasileiras Dispensada'
    ]
    
    # Lista de colunas que devem ser float (percentuais)
    percent_columns = ['CONVERSÃO (%)', 'Taxa Emissão Concluída (%)']
    
    # Lista de colunas que devem ser strings
    string_columns = ['MESA', 'CONSULTOR']
    
    df_clean = df.copy()
    
    # Tratar colunas inteiras
    for col in int_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(int)
    
    # Tratar colunas de porcentagem - manter como float em vez de strings
    for col in percent_columns:
        if col in df_clean.columns:
            # Remover o símbolo "%" se existir e converter para número
            if df_clean[col].dtype == object:
                df_clean[col] = pd.to_numeric(df_clean[col].astype(str).str.replace('%', '').str.strip(), errors='coerce').fillna(0)
            else:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
            # Arredondar para 2 casas decimais, mas manter como float (sem converter para string)
            df_clean[col] = df_clean[col].round(2)
    
    # Tratar colunas de texto
    for col in string_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('').astype(str)
    
    return df_clean

def exibir_higienizacao_desempenho():
    """
    Exibe a tabela de desempenho da higienização por mesa e consultor,
    com opção de filtro por data e dados de emissões do Bitrix.
    """
    # Função auxiliar para converter DataFrame para CSV
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    st.subheader("Desempenho da Higienização por Mesa")

    # --- Carregar CSS Compilado ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")

    # --- FILTROS UNIFICADOS ---
    with st.expander("📊 Filtros", expanded=True):
        st.markdown('<div class="filtros-container">', unsafe_allow_html=True)
        
        # --- SEÇÃO 1: FILTROS DE DATA ---
        st.markdown('<div class="filtro-section">', unsafe_allow_html=True)
        st.markdown('<label class="filtro-label">Filtros de Data</label>', unsafe_allow_html=True)
        
        col_data1, col_data2, col_data_check = st.columns([2,2,1])
        
        with col_data1:
            data_inicio_filtro = st.date_input("Data Início (Opcional)", value=None, key="data_inicio_filtro")
        with col_data2:
            data_fim_filtro = st.date_input("Data Fim (Opcional)", value=None, key="data_fim_filtro")
        with col_data_check:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            aplicar_filtro_data = st.checkbox("Aplicar Datas", value=False, help="Marque para filtrar os dados da planilha pelo período selecionado.", key="aplicar_filtro_data")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- SEÇÃO 2: FILTROS ADICIONAIS ---
        st.markdown('<div class="filtro-section">', unsafe_allow_html=True)
        st.markdown('<label class="filtro-label">Filtros Adicionais</label>', unsafe_allow_html=True)
        
        col_ano, col_resp = st.columns(2)
        
        with col_ano:
            # Placeholder para ano - será preenchido após carregar dados
            ano_selecionado = st.empty()
            
        with col_resp:
            # Placeholder para responsáveis - será preenchido após carregar dados
            filtro_responsaveis = st.empty()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- SEÇÃO 3: FILTROS POR FAMÍLIA ---
        st.markdown('<div class="filtro-section">', unsafe_allow_html=True)
        st.markdown('<label class="filtro-label">Filtros por Família</label>', unsafe_allow_html=True)
        
        col_id, col_nome = st.columns(2)
        
        with col_id:
            filtro_id_familia = st.text_input("ID da Família (exato)", key="filtro_id_familia_higienizacao")
            filtro_id_familia = filtro_id_familia.strip()
            
        with col_nome:
            # Placeholder para famílias - será preenchido após carregar dados
            filtro_nome_familia_selecionado = st.empty()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True) # Fecha filtros-container

    # Variáveis para passar para a função de carregamento
    start_date_to_load = None
    end_date_to_load = None

    if aplicar_filtro_data:
        if data_inicio_filtro and data_fim_filtro:
            if data_inicio_filtro > data_fim_filtro:
                st.warning("A data de início não pode ser posterior à data de fim.")
                return
            start_date_to_load = data_inicio_filtro
            end_date_to_load = data_fim_filtro
            st.info(f"Filtro de data aplicado: {start_date_to_load.strftime('%d/%m/%Y')} a {end_date_to_load.strftime('%d/%m/%Y')}")
            
            # Debug: Informar sobre o filtro de data
            print("\n=== DEBUG: Filtro de Data ===")
            print(f"Aplicando filtro de data: {start_date_to_load.strftime('%d/%m/%Y')} a {end_date_to_load.strftime('%d/%m/%Y')}")
        elif data_inicio_filtro or data_fim_filtro:
            st.warning("Por favor, selecione ambas as datas (início e fim) para aplicar o filtro de data.")
            print("\n=== DEBUG: Tentativa de filtro de data incompleta ===")
            print(f"Data início: {data_inicio_filtro}")
            print(f"Data fim: {data_fim_filtro}")
    else:
        print("\n=== DEBUG: Sem filtro de data aplicado ===")

    # --- Carregar Dados (Necessário antes dos filtros por família para popular selectbox) ---
    # 1. Dados da Planilha de Conclusão
    spinner_message = "Carregando todos os dados de conclusão da planilha..."
    if start_date_to_load and end_date_to_load:
        spinner_message = f"Carregando dados de conclusão entre {start_date_to_load.strftime('%d/%m/%Y')} e {end_date_to_load.strftime('%d/%m/%Y')}..."
    
    with st.spinner(spinner_message):
        df_conclusao_raw = load_conclusao_data(start_date=start_date_to_load, end_date=end_date_to_load)
        if df_conclusao_raw is None:
             df_conclusao_raw = pd.DataFrame() # Continuar com DF vazio

        # Garantir colunas mesmo se vazio
        colunas_planilha_esperadas = [
            'responsavel', 'mesa', 'id_familia', 'nome_familia', 
            'higienizacao_exito', 'higienizacao_incompleta', 'higienizacao_tratadas',
            'higienizacao_distrato'  # Nova coluna adicionada
        ]
        for col in colunas_planilha_esperadas:
            if col not in df_conclusao_raw.columns:
                df_conclusao_raw[col] = None 

        colunas_planilha = [
            'responsavel', 'mesa', 'id_familia', 'nome_familia', 
            'higienizacao_exito', 'higienizacao_incompleta', 'higienizacao_tratadas',
            'higienizacao_distrato'  # Nova coluna adicionada
        ]
        df_conclusao_raw = df_conclusao_raw[colunas_planilha].copy()
        df_conclusao_raw = df_conclusao_raw.dropna(subset=['id_familia']) 

    # 2. Dados do Bitrix (Funil Emissões 1098)
    with st.spinner("Carregando dados de emissões do Bitrix..."):
        df_cartorio = carregar_dados_cartorio()
        if df_cartorio is None:
            df_cartorio = pd.DataFrame() 
            st.warning("Não foi possível carregar os dados de emissões do Bitrix.")
    
    # --- PREENCHER OS FILTROS AGORA QUE OS DADOS FORAM CARREGADOS ---

    # --- Filtro de Data de Venda ---
    # Obter anos disponíveis a partir das datas de venda
    anos_disponiveis = []
    ano_atual = datetime.now().year
    
    if not df_cartorio.empty and 'DATA_VENDA_FAMILIA' in df_cartorio.columns:
        df_cartorio['DATA_VENDA_FAMILIA'] = pd.to_datetime(df_cartorio['DATA_VENDA_FAMILIA'], errors='coerce')
        df_com_data = df_cartorio.dropna(subset=['DATA_VENDA_FAMILIA'])
        
        if not df_com_data.empty:
            # Extrair apenas o ano das datas
            anos_disponiveis = sorted(df_com_data['DATA_VENDA_FAMILIA'].dt.year.unique().tolist())
    
    # Se não houver anos na base, usar o ano atual como padrão
    if not anos_disponiveis:
        anos_disponiveis = [ano_atual]
    
    # Adicionar opção para "Todos os anos"
    opcoes_anos = ["Todos os anos"] + [str(ano) for ano in anos_disponiveis]

    # Preencher o selectbox de ano
    with ano_selecionado.container():
        ano_selecionado_valor = st.selectbox(
            "Filtrar por Ano de Venda",
            options=opcoes_anos,
            index=0,
            key="ano_venda_select"
        )

    # --- Filtro de Responsável ---
    # Obter lista de responsáveis únicos
    responsaveis_unicos = []
    responsaveis_mapeamento = {}  # Para mapear nomes normalizados -> originais
    
    # Dicionário de correções para casos específicos com variação ortográfica
    correcoes_ortograficas = {
        "DANYELLE": "DANYELE",  # Variações da mesma pessoa
        "VITOR": "VICTOR",      # Casos onde podem ser a mesma pessoa
        "VICTOR": "VICTOR"
    }

    # Função para normalizar nomes (extrair apenas primeiro nome)
    def normalizar_nome(nome):
        if not nome or not isinstance(nome, str):
            return ""
        # Pegar apenas o primeiro nome 
        primeiro_nome = nome.strip().split()[0].upper()
        
        # Aplicar correções ortográficas se existirem
        if primeiro_nome in correcoes_ortograficas:
            primeiro_nome = correcoes_ortograficas[primeiro_nome]
            
        return primeiro_nome
    
    # Da tabela de conclusão
    if not df_conclusao_raw.empty and 'responsavel' in df_conclusao_raw.columns:
        responsaveis_planilha = df_conclusao_raw['responsavel'].dropna().unique().tolist()
        for resp in responsaveis_planilha:
            if not resp or str(resp).strip() == '':
                continue
            nome_norm = normalizar_nome(resp)
            if nome_norm:
                # Mapear o nome normalizado para o original
                if nome_norm not in responsaveis_mapeamento:
                    responsaveis_mapeamento[nome_norm] = [resp]
                elif resp not in responsaveis_mapeamento[nome_norm]:
                    responsaveis_mapeamento[nome_norm].append(resp)
    
    # Do Bitrix
    if not df_cartorio.empty and 'ASSIGNED_BY_NAME' in df_cartorio.columns:
        responsaveis_bitrix = df_cartorio['ASSIGNED_BY_NAME'].dropna().unique().tolist()
        for resp in responsaveis_bitrix:
            if not resp or str(resp).strip() == '':
                continue
            nome_norm = normalizar_nome(resp)
            if nome_norm:
                # Mapear o nome normalizado para o original
                if nome_norm not in responsaveis_mapeamento:
                    responsaveis_mapeamento[nome_norm] = [resp]
                elif resp not in responsaveis_mapeamento[nome_norm]:
                    responsaveis_mapeamento[nome_norm].append(resp)
    
    # Criar lista de nomes normalizados (apenas primeiro nome) para o filtro
    responsaveis_unicos = sorted(list(responsaveis_mapeamento.keys()))

    # Debug: mostrar o mapeamento de nomes
    print("\n=== DEBUG: Mapeamento de nomes de responsáveis ===")
    for nome_norm, variantes in responsaveis_mapeamento.items():
        print(f"{nome_norm}: {variantes}")
    print("=== FIM DEBUG ===\n")
    
    # Preparar a mensagem de ajuda com as correções aplicadas
    correcoes_info = ", ".join([f"{k} → {v}" for k, v in correcoes_ortograficas.items() if k != v])
    mensagem_ajuda = f"Selecione o responsável pelo primeiro nome. Variações de sobrenome e algumas correções ortográficas ({correcoes_info}) foram unificadas."

    # Preencher o multiselect de responsáveis
    with filtro_responsaveis.container():
        filtro_responsaveis_valor = st.multiselect(
            "Filtrar por Responsável",
            options=responsaveis_unicos,
            default=[],
            placeholder="Selecione um ou mais responsáveis",
            key="filtro_responsaveis_higienizacao",
            help=mensagem_ajuda
        )

    # --- Filtro por Família ---
    opcoes_familia = ["Todas"] 
    if not df_conclusao_raw.empty:
        df_conclusao_raw['nome_familia'] = df_conclusao_raw['nome_familia'].fillna('Sem Nome')
        df_conclusao_raw['responsavel'] = df_conclusao_raw['responsavel'].fillna('Sem Responsável')
        df_conclusao_raw['id_familia'] = df_conclusao_raw['id_familia'].astype(str) 

        df_conclusao_raw['opcao_selectbox'] = df_conclusao_raw.apply(
            lambda row: f"{row['nome_familia']} \\\\ {row['responsavel']} \\\\ {row['id_familia']}", axis=1
        )
        lista_opcoes = sorted(df_conclusao_raw['opcao_selectbox'].unique().tolist())
        opcoes_familia.extend(lista_opcoes)

    # Preencher o selectbox de famílias
    with filtro_nome_familia_selecionado.container():
        filtro_nome_familia_selecionado_valor = st.selectbox(
            "Nome da Família (\\ Responsável \\ ID)", 
            options=opcoes_familia, 
            key="filtro_nome_familia_higienizacao"
        )

    # --- Aplicar Filtros por Família (afeta df_conclusao_raw e df_cartorio) --- 
    id_familia_filtrar = None

    if filtro_id_familia:
        id_familia_filtrar = filtro_id_familia
        st.info(f"Filtrando pelo ID da Família: {id_familia_filtrar}")
    elif filtro_nome_familia_selecionado_valor != "Todas":
        match = re.search(r'\\\\ ([^\\\\]+)$', filtro_nome_familia_selecionado_valor)
        if match:
            id_familia_filtrar = match.group(1).strip()
            st.info(f"Filtrando pela família selecionada (ID: {id_familia_filtrar})")
        else:
            st.warning("Não foi possível extrair o ID da família da opção selecionada.")

    if id_familia_filtrar:
        df_conclusao_raw = df_conclusao_raw[df_conclusao_raw['id_familia'] == id_familia_filtrar].copy()
        if not df_cartorio.empty and 'UF_CRM_34_ID_FAMILIA' in df_cartorio.columns:
            df_cartorio = df_cartorio[df_cartorio['UF_CRM_34_ID_FAMILIA'] == id_familia_filtrar].copy()
        
        if df_conclusao_raw.empty:
             st.warning(f"Nenhum dado de higienização encontrado para a família ID: {id_familia_filtrar} no período selecionado.")
             if 'df_bitrix_agg' in locals(): df_bitrix_agg = pd.DataFrame(columns=df_bitrix_agg.columns if hasattr(df_bitrix_agg, 'columns') else [])

    # --- Aplicar Filtro de Data de Venda ---
    if not df_cartorio.empty and 'DATA_VENDA_FAMILIA' in df_cartorio.columns:
        if ano_selecionado_valor != "Todos os anos":
            # Converter para inteiro para comparar com o ano extraído das datas
            ano_filtro = int(ano_selecionado_valor)
            
            # Filtrar df_cartorio apenas pelo ano selecionado
            df_cartorio = df_cartorio[df_cartorio['DATA_VENDA_FAMILIA'].dt.year == ano_filtro].copy()
            
            if df_cartorio.empty:
                st.warning(f"Nenhum dado encontrado para o ano selecionado: {ano_selecionado_valor}")
            else:
                st.success(f"Filtro aplicado: Mostrando dados do ano {ano_selecionado_valor} ({len(df_cartorio)} registros)")
        else:
            # Se "Todos os anos" for selecionado, não aplicar filtro de ano
            st.info("Mostrando dados de todos os anos disponíveis")
            
    # --- Aplicar Filtro de Responsável ---
    if filtro_responsaveis_valor:
        # Expandir os nomes normalizados para incluir todas as variações
        nomes_expandidos = []
        for nome_norm in filtro_responsaveis_valor:
            if nome_norm in responsaveis_mapeamento:
                nomes_expandidos.extend(responsaveis_mapeamento[nome_norm])
        
        # Debug: mostrar os nomes expandidos
        print("\n=== DEBUG: Nomes expandidos para filtro ===")
        print(f"Nomes normalizados selecionados: {filtro_responsaveis_valor}")
        print(f"Nomes expandidos para filtro: {nomes_expandidos}")
        print("=== FIM DEBUG ===\n")
        
        # Filtrar df_conclusao_raw por responsável (usando todas as variações)
        if not df_conclusao_raw.empty and 'responsavel' in df_conclusao_raw.columns:
            df_conclusao_raw = df_conclusao_raw[df_conclusao_raw['responsavel'].isin(nomes_expandidos)].copy()
        
        # Filtrar df_cartorio por responsável (usando todas as variações)
        if not df_cartorio.empty and 'ASSIGNED_BY_NAME' in df_cartorio.columns:
            df_cartorio = df_cartorio[df_cartorio['ASSIGNED_BY_NAME'].isin(nomes_expandidos)].copy()
        
        if df_conclusao_raw.empty and df_cartorio.empty:
            nomes_str = ', '.join(filtro_responsaveis_valor)
            st.warning(f"Nenhum dado encontrado para o(s) responsável(eis) selecionado(s): {nomes_str}")

    # --- MOVER PROCESSAMENTO DE DADOS PARA ANTES DAS FAIXAS ---

    # --- APLICAR LÓGICA ESPECIAL PARA PIPELINE 104 (PESQUISA BR) ---
    # Aplicar lógica de precedência antes de calcular métricas
    if not df_cartorio.empty and 'CATEGORY_ID' in df_cartorio.columns:
        df_cartorio = aplicar_logica_precedencia_pipeline_104_higienizacao(df_cartorio)

    # --- Mapeamento de Estágios Bitrix ---
    # ATUALIZADO: Incluindo os novos funis 102 (Paróquia) e 104 (Pesquisa BR)
    mapeamento_stages = {
        # === Pipeline 92 ===
        'DT1098_92:NEW': 'Brasileiras Pendências', 
        'DT1098_92:UC_P6PYHW': 'Brasileiras Pesquisas',
        'DT1098_92:PREPARATION': 'Brasileiras Pendências', 
        'DT1098_92:UC_XBTHZ7': 'Brasileiras Pendências',
        'DT1098_92:CLIENT': 'Brasileiras Pendências', 
        'DT1098_92:UC_ZWO7BI': 'Brasileiras Pendências',
        'DT1098_92:UC_83ZGKS': 'Brasileiras Pendências', 
        'DT1098_92:UC_6TECYL': 'Brasileiras Pendências',
        'DT1098_92:UC_MUJP1P': 'Brasileiras Solicitadas', 
        'DT1098_92:UC_EYBGVD': 'Brasileiras Pendências',
        'DT1098_92:UC_KC335Q': 'Brasileiras Pendências', 
        'DT1098_92:UC_5LWUTX': 'Brasileiras Emitida',
        'DT1098_92:FAIL': 'Brasileiras Dispensada', 
        'DT1098_92:UC_Z24IF7': 'Brasileiras Dispensada',
        'DT1098_92:UC_U10R0R': 'Brasileiras Dispensada', 
        'DT1098_92:SUCCESS': 'Brasileiras Emitida',
        
        # === Pipeline 94 ===
        'DT1098_94:NEW': 'Brasileiras Pendências', 
        'DT1098_94:UC_4YE2PI': 'Brasileiras Pesquisas',
        'DT1098_94:PREPARATION': 'Brasileiras Pendências', 
        'DT1098_94:CLIENT': 'Brasileiras Pendências',
        'DT1098_94:UC_IQ4WFA': 'Brasileiras Pendências', 
        'DT1098_94:UC_UZHXWF': 'Brasileiras Pendências',
        'DT1098_94:UC_DH38EI': 'Brasileiras Pendências', 
        'DT1098_94:UC_X9UE60': 'Brasileiras Pendências',
        'DT1098_94:UC_IXCAA5': 'Brasileiras Solicitadas', 
        'DT1098_94:UC_VS8YKI': 'Brasileiras Pendências',
        'DT1098_94:UC_M6A09E': 'Brasileiras Pendências', 
        'DT1098_94:UC_K4JS04': 'Brasileiras Emitida',
        'DT1098_94:FAIL': 'Brasileiras Dispensada', 
        'DT1098_94:UC_MGTPX0': 'Brasileiras Dispensada',
        'DT1098_94:UC_L3JFKO': 'Brasileiras Dispensada', 
        'DT1098_94:SUCCESS': 'Brasileiras Emitida',
        
        # === Pipeline 102 (Paróquia) ===
        'DT1098_102:NEW': 'Brasileiras Pendências',
        'DT1098_102:PREPARATION': 'Brasileiras Pendências',
        'DT1098_102:CLIENT': 'Brasileiras Emitida',
        'DT1098_102:UC_45SBLC': 'Brasileiras Pendências',  # Devolução ADM como pendência
        'DT1098_102:SUCCESS': 'Brasileiras Emitida',  # Certidão Entregue
        'DT1098_102:FAIL': 'Brasileiras Dispensada',  # Cancelado
        'DT1098_102:UC_676WIG': 'Brasileiras Dispensada',  # Certidão Dispensada
        'DT1098_102:UC_UHPXE8': 'Brasileiras Emitida',  # Certidão Entregue
        
        # === Pipeline 104 (Pesquisa BR) - LÓGICA ESPECIAL ===
        # IMPORTANTE: Pipeline 104 será tratado de forma especial na função aplicar_logica_precedencia_pipeline_104
        'DT1098_104:NEW': 'Brasileiras Pesquisas',  # Aguardando Pesquisador
        'DT1098_104:PREPARATION': 'Brasileiras Pesquisas',  # Pesquisa em Andamento
        'DT1098_104:SUCCESS': 'Brasileiras Pesquisas',  # Pesquisa Pronta - consideramos como pesquisa finalizada
        'DT1098_104:FAIL': 'Brasileiras Dispensada',  # Pesquisa Não Encontrada
    }
    col_id_familia_bitrix = 'UF_CRM_34_ID_FAMILIA'
    df_bitrix_agg = pd.DataFrame() # Inicializar df_bitrix_agg

    if not df_cartorio.empty and 'STAGE_ID' in df_cartorio.columns and col_id_familia_bitrix in df_cartorio.columns:
        df_cartorio['CATEGORIA_EMISSAO'] = df_cartorio['STAGE_ID'].map(mapeamento_stages).fillna('Categoria Desconhecida')
        
        # NOVO: Adicionar coluna de conclusão corrigida para cada registro
        df_cartorio['CONCLUIDA_CORRIGIDA'] = df_cartorio.apply(
            lambda row: calcular_conclusao_corrigida_por_pipeline(row), axis=1
        )
        
        df_bitrix_agg = pd.crosstab(df_cartorio[col_id_familia_bitrix], df_cartorio['CATEGORIA_EMISSAO'])
        
        categorias_bitrix_contagem = [
            'Brasileiras Pendências', 'Brasileiras Pesquisas', 'Brasileiras Solicitadas',
            'Brasileiras Emitida', 'Brasileiras Dispensada'
        ]
        for col in categorias_bitrix_contagem:
            if col not in df_bitrix_agg.columns:
                 df_bitrix_agg[col] = 0
        
        if 'Categoria Desconhecida' in df_bitrix_agg.columns:
            if 'Brasileiras Pendências' in df_bitrix_agg.columns:
                df_bitrix_agg['Brasileiras Pendências'] += df_bitrix_agg['Categoria Desconhecida']
            else:
                df_bitrix_agg['Brasileiras Pendências'] = df_bitrix_agg['Categoria Desconhecida']
            df_bitrix_agg = df_bitrix_agg.drop(columns=['Categoria Desconhecida'], errors='ignore')

        df_bitrix_agg = df_bitrix_agg.reindex(columns=categorias_bitrix_contagem, fill_value=0)
        
        # CORRIGIDO: Calcular "Pasta C/Emissão Concluída" usando a lógica corrigida
        # Primeiro, agrupar por família e verificar se TODAS as certidões estão realmente concluídas
        conclusao_por_familia = df_cartorio.groupby(col_id_familia_bitrix).agg({
            'CONCLUIDA_CORRIGIDA': ['count', 'sum']
        })
        conclusao_por_familia.columns = ['total_certidoes', 'total_concluidas']
        conclusao_por_familia = conclusao_por_familia.reset_index()
        
        # Uma família está "C/Emissão Concluída" apenas se TODAS as certidões estão concluídas
        # E se há pelo menos uma certidão (evitar divisão por zero)
        conclusao_por_familia['familia_concluida'] = (
            (conclusao_por_familia['total_certidoes'] > 0) &
            (conclusao_por_familia['total_concluidas'] == conclusao_por_familia['total_certidoes'])
        ).astype(int)
        
        # Merge com df_bitrix_agg para adicionar a coluna corrigida
        df_bitrix_agg = pd.merge(
            df_bitrix_agg.reset_index(),
            conclusao_por_familia[[col_id_familia_bitrix, 'familia_concluida']],
            on=col_id_familia_bitrix,
            how='left'
        )
        
        # Renomear e garantir que existe
        df_bitrix_agg['Pasta C/Emissão Concluída'] = df_bitrix_agg['familia_concluida'].fillna(0).astype(int)
        df_bitrix_agg = df_bitrix_agg.drop(columns=['familia_concluida'], errors='ignore')
        
        print(f"[DEBUG HIGIENIZAÇÃO] Cálculo corrigido: {df_bitrix_agg['Pasta C/Emissão Concluída'].sum()} famílias com emissão concluída")
        
    else:
        df_bitrix_agg = pd.DataFrame()

    # Garantir que todas as colunas necessárias existam
    novas_colunas_bitrix = [
        'Brasileiras Pendências', 'Brasileiras Pesquisas', 'Brasileiras Solicitadas',
        'Brasileiras Emitida', 'Pasta C/Emissão Concluída', 'Brasileiras Dispensada'
    ]
    
    if df_bitrix_agg.empty: # Se df_bitrix_agg não foi populado (ex: df_cartorio vazio)
        colunas_esperadas_bitrix_vazio = [col_id_familia_bitrix] + novas_colunas_bitrix
        df_bitrix_agg = pd.DataFrame(columns=colunas_esperadas_bitrix_vazio)

    # --- Merge: Planilha + Dados Bitrix Agregados --- 
    df_merged = pd.merge(
        df_conclusao_raw, df_bitrix_agg,
        left_on='id_familia', right_on=col_id_familia_bitrix, how='left'
    )
    for col in novas_colunas_bitrix: # Preencher NaNs nas colunas do Bitrix com 0
        if col not in df_merged.columns: # Adicionar coluna se não existir do merge
            df_merged[col] = 0
        df_merged[col] = df_merged[col].fillna(0).astype(int)

    # --- Agregação Final por Mesa e Consultor --- 
    agg_dict = {
        'higienizacao_exito': 'sum',
        'higienizacao_incompleta': 'sum',
        'higienizacao_tratadas': 'sum',
        'higienizacao_distrato': 'sum',  # Nova coluna adicionada
        'Brasileiras Pendências': 'sum',
        'Brasileiras Pesquisas': 'sum',
        'Brasileiras Solicitadas': 'sum',
        'Brasileiras Emitida': 'sum',
        'Pasta C/Emissão Concluída': 'sum',
        'Brasileiras Dispensada': 'sum'
    }

    # Debug: Imprimir dados antes da agregação
    print("\n=== DEBUG: Dados antes da agregação ===")
    print(f"Total de registros em df_merged: {len(df_merged)}")
    print("\nContagens por status:")
    if 'higienizacao_exito' in df_merged.columns:
        print(f"Higienização com Êxito (soma total): {df_merged['higienizacao_exito'].sum()}")
        # Mostrar contagem por mesa
        print("\nContagem de Êxito por Mesa:")
        print(df_merged.groupby('mesa')['higienizacao_exito'].sum())
    else:
        print("Coluna 'higienizacao_exito' não encontrada!")
    print("=== FIM DEBUG ===\n")

    df_agregado_final = df_merged.groupby(['mesa', 'responsavel']).agg(agg_dict).reset_index()

    # Debug: Imprimir dados após agregação
    print("\n=== DEBUG: Dados após agregação ===")
    print(f"Total de registros em df_agregado_final: {len(df_agregado_final)}")
    print("\nSoma total de higienização com êxito após agregação:")
    if 'higienizacao_exito' in df_agregado_final.columns:
        print(df_agregado_final['higienizacao_exito'].sum())
    print("=== FIM DEBUG ===\n")

    # --- Merge Final com a Base --- 
    data_base = {
        'MESA': ['MESA 8', 'MESA 7', 'MESA 6', 'MESA 5', 'MESA 4', 'MESA 3', 'MESA 2', 'MESA 1', 'MESA 0', 'Cabines', 'CARRÃO'],
        'PASTAS TOTAIS': [105, 46, 46, 70, 106, 46, 66, 66, 49, 113, 123],
        'CONSULTOR': ['NADYA', 'FELIPE', 'VITOR', 'BIANCA', 'DANYELE', 'LAYLA', 'LAYLA', 'JULIANE', 'JULIANE', 'STEFANY', 'Fernanda']
    }
    df_base = pd.DataFrame(data_base)

    # Garantir que a coluna MESA em df_base esteja em maiúsculas para o merge
    df_base['MESA'] = df_base['MESA'].str.upper()

    # Debug: Mostrar dados antes do merge
    print("\n=== DEBUG: Dados antes do merge final ===")
    print("df_base:")
    print(df_base)
    print("\ndf_agregado_final antes do rename:")
    print(df_agregado_final)

    # Primeiro, agregar os dados por MESA (somando todas as métricas)
    metricas_para_somar = [
        'higienizacao_exito', 'higienizacao_incompleta', 'higienizacao_tratadas',
        'higienizacao_distrato', 'Brasileiras Pendências', 'Brasileiras Pesquisas',
        'Brasileiras Solicitadas', 'Brasileiras Emitida', 'Pasta C/Emissão Concluída',
        'Brasileiras Dispensada'
    ]
    
    df_agregado_por_mesa = df_agregado_final.groupby('mesa')[metricas_para_somar].sum().reset_index()

    # Debug: Mostrar agregação por mesa
    print("\nAgregação por mesa (antes do rename):")
    print(df_agregado_por_mesa)

    # Renomear colunas
    df_agregado_por_mesa = df_agregado_por_mesa.rename(columns={
        'mesa': 'MESA',
        'higienizacao_exito': 'HIGINIZAÇÃO COM ÊXITO',
        'higienizacao_incompleta': 'HIGINIZAÇÃO INCOMPLETA',
        'higienizacao_tratadas': 'HIGINIZAÇÃO TRATADAS',
        'higienizacao_distrato': 'DISTRATO'
    })

    # Debug: Mostrar após rename
    print("\nAgregação por mesa (após rename):")
    print(df_agregado_por_mesa)

    # Fazer o merge com a base
    df_final = pd.merge(df_base, df_agregado_por_mesa, on='MESA', how='left')

    # Preencher NaN com 0
    colunas_numericas = df_final.select_dtypes(include=['float64', 'int64']).columns
    df_final[colunas_numericas] = df_final[colunas_numericas].fillna(0)
    
    # Garantir que sejam números inteiros onde apropriado
    colunas_inteiras = [
        'HIGINIZAÇÃO COM ÊXITO', 'HIGINIZAÇÃO INCOMPLETA', 'HIGINIZAÇÃO TRATADAS', 
        'DISTRATO', 'Brasileiras Pendências', 'Brasileiras Pesquisas', 
        'Brasileiras Solicitadas', 'Brasileiras Emitida', 'Pasta C/Emissão Concluída',
        'Brasileiras Dispensada'
    ]
    
    for col in colunas_inteiras:
        if col in df_final.columns:
            df_final[col] = df_final[col].fillna(0).astype(int)

    # --- Calcular métricas ---
    df_final['CONVERSÃO (%)'] = np.where(
        df_final['PASTAS TOTAIS'] > 0,
        (df_final['HIGINIZAÇÃO COM ÊXITO'] / df_final['PASTAS TOTAIS']) * 100,
        0
    )
    df_final['CONVERSÃO (%)'] = df_final['CONVERSÃO (%)'].fillna(0).round(2)

    df_final['Taxa Emissão Concluída (%)'] = np.where(
        df_final['PASTAS TOTAIS'] > 0,
        (df_final['Pasta C/Emissão Concluída'] / df_final['PASTAS TOTAIS']) * 100,
        0
    )
    df_final['Taxa Emissão Concluída (%)'] = df_final['Taxa Emissão Concluída (%)'].fillna(0).round(2)

    # Definir ordem das colunas
    ordem_colunas = [
        'MESA', 'PASTAS TOTAIS', 'CONSULTOR',
        'HIGINIZAÇÃO COM ÊXITO', 'HIGINIZAÇÃO INCOMPLETA', 'HIGINIZAÇÃO TRATADAS',
        'DISTRATO', 'CONVERSÃO (%)',
        'Brasileiras Pendências', 'Brasileiras Pesquisas', 'Brasileiras Solicitadas',
        'Brasileiras Emitida', 'Pasta C/Emissão Concluída', 'Taxa Emissão Concluída (%)',
        'Brasileiras Dispensada'
    ]

    # Garantir que todas as colunas existam
    for col in ordem_colunas:
        if col not in df_final.columns:
            if col in ['CONVERSÃO (%)', 'Taxa Emissão Concluída (%)']:
                df_final[col] = 0.0
            else:
                df_final[col] = 0

    df_final = df_final[ordem_colunas]

    # Debug: Mostrar dados após cálculos
    print("\n=== DEBUG: Dados após cálculos ===")
    print("df_final com todas as colunas:")
    print(df_final)

    # Renomear 'CABINES' para 'PROTOCOLADO' para exibição (após o merge ter usado 'CABINES')
    df_final['MESA'] = df_final['MESA'].replace('CABINES', 'PROTOCOLADO')

    # --- Exibir a Tabela Principal (APENAS MESAS 1-8, para alinhar com o card acima) --- 
    mesas_1_8_list = [f'MESA {i}' for i in range(1, 9)] # Definindo a lista de mesas 1-8

    # Card para MESAS 1-8
    # Garantir que a coluna existe antes de somar
    if 'Pasta C/Emissão Concluída' not in df_final.columns:
        df_final['Pasta C/Emissão Concluída'] = 0
    df_final['Pasta C/Emissão Concluída'] = pd.to_numeric(df_final['Pasta C/Emissão Concluída'], errors='coerce').fillna(0).astype(int)
    
    total_mesas_1_8_card = df_final[df_final['MESA'].isin(mesas_1_8_list)]['Pasta C/Emissão Concluída'].sum()

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    ">
        <div style="
            color: #495057;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            text-align: center;
        ">TOTAL DE PASTAS COM EMISSÃO CONCLUÍDA (MESAS 1-8)</div>
        <div style="
            color: #212529;
            font-size: 28px;
            font-weight: 700;
            text-align: center;
            margin: 0;
        ">{int(total_mesas_1_8_card)} PASTAS</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Filtrar dados para a tabela de MESAS 1-8 (excluindo PROTOCOLADO e CARRÃO explicitamente)
    df_display_mesas = df_final[
        df_final['MESA'].isin(mesas_1_8_list)
    ].copy()

    # Nos casos em que não há dados reais para MESAS 1-8, mostrar mensagem amigável
    # Usar df_display_mesas para a verificação
    if df_display_mesas.empty or ('HIGINIZAÇÃO COM ÊXITO' in df_display_mesas.columns and df_display_mesas['HIGINIZAÇÃO COM ÊXITO'].sum() == 0):
        st.warning("""
        Não foi possível carregar os dados da planilha para as MESAS 1-8. Isso pode ocorrer por algumas razões:
        
        1. A planilha pode estar com formato diferente do esperado
        2. Os cabeçalhos da planilha podem ter sido alterados
        3. Pode haver um problema de conexão com o Google Sheets
        
        Por favor, verifique a planilha e tente novamente.
        """)
        
        # Mostrar tabela básica com as metas para MESAS 1-8 se os dados da planilha falharem
        df_base_mesas_1_8 = df_base[df_base['MESA'].isin(mesas_1_8_list)].copy()
        # Renomear 'Cabines' para 'PROTOCOLADO' também em df_base se for exibido
        df_base_mesas_1_8['MESA'] = df_base_mesas_1_8['MESA'].replace('Cabines', 'PROTOCOLADO') 
        st.markdown("### Dados Básicos (Metas por Mesa 1-8)")
        st.dataframe(df_base_mesas_1_8, hide_index=True, use_container_width=True)
        # Não retornar a função inteira, apenas a seção de MESAS 1-8
    else:
        # --- Continuação normal do código se houver dados para MESAS 1-8 ---
        # Calcular totais para MESAS 1-8
        df_total_mesas = df_display_mesas.select_dtypes(include=np.number).sum().to_frame().T
        df_total_mesas['MESA'] = 'TOTAL'
        df_total_mesas['CONSULTOR'] = '' 
        
        # Recalcular percentuais para a linha de total
        if 'PASTAS TOTAIS' in df_total_mesas.columns and df_total_mesas['PASTAS TOTAIS'].iloc[0] > 0:
            if 'HIGINIZAÇÃO COM ÊXITO' not in df_total_mesas.columns:
                df_total_mesas['HIGINIZAÇÃO COM ÊXITO'] = 0
            df_total_mesas['CONVERSÃO (%)'] = (
                df_total_mesas['HIGINIZAÇÃO COM ÊXITO'] / df_total_mesas['PASTAS TOTAIS'] * 100
            ).round(2)
            
            if 'Pasta C/Emissão Concluída' not in df_total_mesas.columns:
                df_total_mesas['Pasta C/Emissão Concluída'] = 0
            df_total_mesas['Taxa Emissão Concluída (%)'] = (
                df_total_mesas['Pasta C/Emissão Concluída'] / df_total_mesas['PASTAS TOTAIS'] * 100
            ).round(2)
        else:
            df_total_mesas['CONVERSÃO (%)'] = 0.0
            df_total_mesas['Taxa Emissão Concluída (%)'] = 0.0
            
        df_total_mesas = ensure_numeric_display(df_total_mesas) # Aplicar formatação
        df_display_mesas_final = pd.concat([df_display_mesas, df_total_mesas], ignore_index=True)
        df_display_mesas_final = ensure_numeric_display(df_display_mesas_final)

        st.markdown("""
        <style>
        table.dataframe {
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
        }
        table.dataframe th {
            background-color: #4a7bef;
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 8px;
            border: 1px solid #dddddd;
        }
        table.dataframe td {
            text-align: center;
            padding: 6px;
            border: 1px solid #dddddd;
        }
        table.dataframe tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        table.dataframe tr:hover {
            background-color: #ddd;
        }
        table.dataframe tr:last-child {
            background-color: #ffd580;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        df_percent = df_display_mesas_final.copy()
        if 'CONVERSÃO (%)' in df_percent.columns:
            df_percent['CONVERSÃO (%)'] = df_percent['CONVERSÃO (%)'].apply(lambda x: f"{x:.2f}%")
        if 'Taxa Emissão Concluída (%)' in df_percent.columns:
            df_percent['Taxa Emissão Concluída (%)'] = df_percent['Taxa Emissão Concluída (%)'].apply(lambda x: f"{x:.2f}%")
        
        html_table = df_percent.to_html(index=False, classes='dataframe')
        st.markdown(html_table, unsafe_allow_html=True)

        csv_principal = convert_df_to_csv(df_display_mesas_final)
        st.download_button(
            label="Download Tabela MESAS 1-8 como CSV",
            data=csv_principal,
            file_name='desempenho_higienizacao_mesas_1_8.csv',
            mime='text/csv',
            key='download_mesas_1_8_csv'
        )
        st.markdown("---")

    # --- Exibir a Tabela de PROTOCOLADO --- 
    df_cabines_final = df_final[df_final['MESA'] == 'PROTOCOLADO'].copy()
    if not df_cabines_final.empty:
        # Verificar se a coluna Pasta C/Emissão Concluída existe
        if 'Pasta C/Emissão Concluída' not in df_cabines_final.columns:
            print("ALERTA: Criando coluna 'Pasta C/Emissão Concluída' em df_cabines_final")
            df_cabines_final['Pasta C/Emissão Concluída'] = 0
            
        # Garantir que é um número inteiro para exibição
        df_cabines_final['Pasta C/Emissão Concluída'] = pd.to_numeric(df_cabines_final['Pasta C/Emissão Concluída'], errors='coerce').fillna(0).astype(int)
        # Calcular total de Pasta C/Emissão Concluída para PROTOCOLADO
        total_cabines = df_cabines_final['Pasta C/Emissão Concluída'].sum()

        # Exibir card de PROTOCOLADO com design mais profissional e harmônico
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="
                color: #495057;
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
                text-align: center;
            ">TOTAL DE PASTAS COM EMISSÃO CONCLUÍDA (PROTOCOLADO)</div>
            <div style="
                color: #212529;
                font-size: 28px;
                font-weight: 700;
                text-align: center;
                margin: 0;
            ">{int(total_cabines)} PASTAS</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        if 'PASTAS TOTAIS' in df_cabines_final.columns:
            df_cabines_final.loc[:, 'PASTAS TOTAIS'] = pd.to_numeric(df_cabines_final['PASTAS TOTAIS'], errors='coerce').fillna(0).astype(int)

        df_total_cabines = df_cabines_final.select_dtypes(include=np.number).sum().to_frame().T
        df_total_cabines['MESA'] = 'TOTAL'
        df_display_cabines = pd.concat([df_cabines_final, df_total_cabines], ignore_index=True)

        # Aplicar formatação numérica para garantir compatibilidade com Arrow
        df_display_cabines = ensure_numeric_display(df_display_cabines)
        
        # Formatar as colunas de porcentagem antes de converter para HTML
        df_percent_cabines = df_display_cabines.copy()
        if 'CONVERSÃO (%)' in df_percent_cabines.columns:
            df_percent_cabines['CONVERSÃO (%)'] = df_percent_cabines['CONVERSÃO (%)'].apply(lambda x: f"{x:.2f}%")
        if 'Taxa Emissão Concluída (%)' in df_percent_cabines.columns:
            df_percent_cabines['Taxa Emissão Concluída (%)'] = df_percent_cabines['Taxa Emissão Concluída (%)'].apply(lambda x: f"{x:.2f}%")
        
        # Converter para HTML e exibir
        html_table_cabines = df_percent_cabines.to_html(index=False, classes='dataframe')
        st.markdown(html_table_cabines, unsafe_allow_html=True)
        
        csv_cabines_detalhes = convert_df_to_csv(df_cabines_final)
        st.download_button(
            label="Download Detalhes PROTOCOLADO como CSV",
            data=csv_cabines_detalhes,
            file_name='detalhes_protocolado.csv',
            mime='text/csv',
            key='download_protocolado_csv'
        )
    else:
        st.info("Não há dados de PROTOCOLADO na planilha para exibir detalhes.") 

    st.markdown("---")

    # --- Seção CARRÃO ---
    df_carrao_final = df_final[df_final['MESA'] == 'CARRÃO'].copy()
    if not df_carrao_final.empty:
        # Verificar se a coluna Pasta C/Emissão Concluída existe
        if 'Pasta C/Emissão Concluída' not in df_carrao_final.columns:
            print("ALERTA: Criando coluna 'Pasta C/Emissão Concluída' em df_carrao_final")
            df_carrao_final['Pasta C/Emissão Concluída'] = 0
            
        # Garantir que é um número inteiro para exibição
        df_carrao_final['Pasta C/Emissão Concluída'] = pd.to_numeric(df_carrao_final['Pasta C/Emissão Concluída'], errors='coerce').fillna(0).astype(int)
        # Calcular total de Pasta C/Emissão Concluída para CARRÃO
        total_carrao = df_carrao_final['Pasta C/Emissão Concluída'].sum()

        # Exibir card de CARRÃO com design mais profissional e harmônico
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="
                color: #495057;
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
                text-align: center;
            ">TOTAL DE PASTAS COM EMISSÃO CONCLUÍDA (CARRÃO)</div>
            <div style="
                color: #212529;
                font-size: 28px;
                font-weight: 700;
                text-align: center;
                margin: 0;
            ">{int(total_carrao)} PASTAS</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        if 'PASTAS TOTAIS' in df_carrao_final.columns:
            df_carrao_final.loc[:, 'PASTAS TOTAIS'] = pd.to_numeric(df_carrao_final['PASTAS TOTAIS'], errors='coerce').fillna(0).astype(int)

        df_total_carrao = df_carrao_final.select_dtypes(include=np.number).sum().to_frame().T
        df_total_carrao['MESA'] = 'TOTAL'
        df_display_carrao = pd.concat([df_carrao_final, df_total_carrao], ignore_index=True)

        # Aplicar formatação numérica para garantir compatibilidade com Arrow
        df_display_carrao = ensure_numeric_display(df_display_carrao)
        
        # Formatar as colunas de porcentagem antes de converter para HTML
        df_percent_carrao = df_display_carrao.copy()
        if 'CONVERSÃO (%)' in df_percent_carrao.columns:
            df_percent_carrao['CONVERSÃO (%)'] = df_percent_carrao['CONVERSÃO (%)'].apply(lambda x: f"{x:.2f}%")
        if 'Taxa Emissão Concluída (%)' in df_percent_carrao.columns:
            df_percent_carrao['Taxa Emissão Concluída (%)'] = df_percent_carrao['Taxa Emissão Concluída (%)'].apply(lambda x: f"{x:.2f}%")
        
        # Converter para HTML e exibir
        html_table_carrao = df_percent_carrao.to_html(index=False, classes='dataframe')
        st.markdown(html_table_carrao, unsafe_allow_html=True)
        
        csv_carrao_detalhes = convert_df_to_csv(df_carrao_final)
        st.download_button(
            label="Download Detalhes CARRÃO como CSV",
            data=csv_carrao_detalhes,
            file_name='detalhes_carrao.csv',
            mime='text/csv',
            key='download_carrao_csv'
        )
    else:
        st.info("Não há dados de CARRÃO na planilha para exibir detalhes.") 

    st.markdown("---")

def calcular_conclusao_corrigida_por_pipeline(row):
    """
    Calcula se uma certidão está concluída usando a lógica corrigida para pipeline 104.
    
    CORRIGIDO DEZEMBRO 2024: Mesma lógica aplicada no acompanhamento.py
    
    Pipeline 102 (Paróquia): Lógica normal
    Pipeline 104 (Pesquisa BR): APENAS SUCCESS ou FAIL são considerados finalizados
    Outros pipelines: Lógica normal baseada em mapeamento
    """
    category_id = str(row.get('CATEGORY_ID', ''))
    stage_id = str(row.get('STAGE_ID', ''))
    categoria_emissao = row.get('CATEGORIA_EMISSAO', '')
    
    # Pipeline 102 (Paróquia): Tratar como pipeline normal
    if category_id == '102':
        return categoria_emissao == 'Brasileiras Emitida'
    
    # Pipeline 104 (Pesquisa BR): CORRIGIDO - Lógica mais restritiva
    elif category_id == '104':
        # CORREÇÃO CRÍTICA: Apenas considerar realmente finalizado
        if 'SUCCESS' in stage_id:
            # Se chegou ao SUCCESS final (se existir mapeamento específico)
            return True
        elif 'FAIL' in stage_id:
            # Se foi dispensada/cancelada (processo finalizado)
            return True
        else:
            # Qualquer outro estado (incluindo "PRONTA PARA EMISSÃO") NÃO é conclusão final
            return False
    
    # Pipelines 92 e 94 (Cartórios): Lógica normal baseada no mapeamento
    else:
        return categoria_emissao == 'Brasileiras Emitida' 