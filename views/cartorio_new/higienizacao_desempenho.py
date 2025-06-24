import streamlit as st
import pandas as pd
from data.load_conclusao_higienizacao import load_conclusao_data
from views.cartorio_new.data_loader import carregar_dados_cartorio # Importar dados do cartório
from datetime import datetime, timedelta, date
import re # Para extrair ID da opção do selectbox
import numpy as np # Para operações numéricas
from utils.dataframe_utils import ensure_pandas_df

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
        
        col_ano, col_resp, col_protocol = st.columns(3)
        
        with col_ano:
            # Placeholder para ano - será preenchido após carregar dados
            ano_selecionado = st.empty()
            
        with col_resp:
            # Placeholder para responsáveis - será preenchido após carregar dados
            filtro_responsaveis = st.empty()

        with col_protocol: # Novo filtro para Protocolizado
            # Placeholder para o filtro de protocolizado
            filtro_protocolizado_selecionado = st.empty()
        
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
    
    # AJUSTE: Usar a coluna DATA_VENDA_FAMILIA que é preparada pelo data_loader.py
    coluna_data_venda_bitrix = 'DATA_VENDA_FAMILIA' 

    # Converter a coluna de data para datetime no DataFrame principal uma vez, se existir
    if not df_cartorio.empty and coluna_data_venda_bitrix in df_cartorio.columns:
        df_cartorio[coluna_data_venda_bitrix] = pd.to_datetime(df_cartorio[coluna_data_venda_bitrix], errors='coerce')

    # Para obter os anos disponíveis, usamos diretamente df_cartorio e a coluna_data_venda_bitrix
    # Não precisamos mais filtrar por CATEGORY_ID == '46' aqui, pois DATA_VENDA_FAMILIA já considera isso.
    if not df_cartorio.empty and coluna_data_venda_bitrix in df_cartorio.columns:
        df_com_data_venda = df_cartorio.dropna(subset=[coluna_data_venda_bitrix])
        
        if not df_com_data_venda.empty:
            anos_disponiveis = sorted(df_com_data_venda[coluna_data_venda_bitrix].dt.year.unique().tolist())
            print(f"[DEBUG Higienização Desempenho] Anos disponíveis de DATA_VENDA_FAMILIA: {anos_disponiveis}") # DEBUG
        else:
            print("[DEBUG Higienização Desempenho] Nenhum ano encontrado em DATA_VENDA_FAMILIA após dropna.") # DEBUG
    else:
        print(f"[DEBUG Higienização Desempenho] Coluna {coluna_data_venda_bitrix} não encontrada em df_cartorio ou df_cartorio vazio.") # DEBUG

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

    # --- Filtro Protocolizado (Novo) ---
    opcoes_protocolizado = ["Todos", "Sim", "Não"]
    # Preencher o selectbox de protocolizado
    with filtro_protocolizado_selecionado.container():
        protocolizado_selecionado_valor = st.selectbox(
            "Filtrar por Protocolizado",
            options=opcoes_protocolizado,
            index=0, # Default para "Todos"
            key="protocolizado_select_higienizacao",
            help="Filtrar famílias/pastas com base no status de protocolização do Bitrix."
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
        
        if df_conclusao_raw.empty and (df_cartorio.empty if not isinstance(df_cartorio, pd.DataFrame) or df_cartorio is None else True):
             st.warning(f"Nenhum dado de higienização encontrado para a família ID: {id_familia_filtrar} no período selecionado.")
             if 'df_bitrix_agg' in locals(): df_bitrix_agg = pd.DataFrame(columns=df_bitrix_agg.columns if hasattr(df_bitrix_agg, 'columns') else [])

    # --- Aplicar Filtro de Protocolizado (Novo) ---
    if not df_cartorio.empty and 'UF_CRM_34_PROTOCOLIZADO' in df_cartorio.columns:
        # Assegurar que a coluna é tratada como string para a comparação
        df_cartorio['UF_CRM_34_PROTOCOLIZADO'] = df_cartorio['UF_CRM_34_PROTOCOLIZADO'].astype(str).fillna('nan')
        
        if protocolizado_selecionado_valor == "Sim":
            # VALOR PARA "SIM" (PROTOCOLIZADO) - AJUSTADO PARA TEXTO
            valor_protocolizado_sim = 'PROTOCOLIZADO' 
            df_cartorio = df_cartorio[df_cartorio['UF_CRM_34_PROTOCOLIZADO'] == valor_protocolizado_sim].copy()
            st.info(f"Filtrando por Protocolizado: Sim. {len(df_cartorio)} registros correspondentes.")
        elif protocolizado_selecionado_valor == "Não":
            # VALOR PARA "NÃO" (NÃO PROTOCOLIZADO) - AJUSTADO PARA TEXTO
            valor_protocolizado_nao = 'NÃO PROTOCOLIZADO'
            df_cartorio = df_cartorio[df_cartorio['UF_CRM_34_PROTOCOLIZADO'] == valor_protocolizado_nao].copy()
            st.info(f"Filtrando por Protocolizado: Não. {len(df_cartorio)} registros correspondentes.")
        # Se "Todos", nenhum filtro é aplicado aqui.

        if df_cartorio.empty and protocolizado_selecionado_valor != "Todos":
            st.warning(f"Nenhum dado encontrado para Protocolizado: {protocolizado_selecionado_valor} com os filtros atuais.")
    elif protocolizado_selecionado_valor != "Todos":
        st.warning("Coluna UF_CRM_34_PROTOCOLIZADO não encontrada nos dados do Bitrix para aplicar o filtro.")

    # --- Aplicar Filtro de Data de Venda ---
    # A coluna coluna_data_venda_bitrix (agora DATA_VENDA_FAMILIA) já foi definida e convertida para datetime
    if not df_cartorio.empty and coluna_data_venda_bitrix in df_cartorio.columns:
        if ano_selecionado_valor != "Todos os anos":
            # Converter para inteiro para comparar com o ano extraído das datas
            ano_filtro = int(ano_selecionado_valor)
            
            # AJUSTE: Remover a condição de CATEGORY_ID == '46'
            # A coluna DATA_VENDA_FAMILIA já reflete a lógica da cat 46 do data_loader
            condicao_ano = (df_cartorio[coluna_data_venda_bitrix].dt.year == ano_filtro)
            
            # Aplicar apenas a condição do ano
            df_cartorio_filtrado = df_cartorio[condicao_ano].copy()
            
            if df_cartorio_filtrado.empty:
                st.warning(f"Nenhum dado encontrado para o ano {ano_selecionado_valor} (coluna {coluna_data_venda_bitrix}).")
            else:
                st.success(f"Filtro aplicado: Mostrando dados do ano {ano_selecionado_valor} ({len(df_cartorio_filtrado)} registros da coluna {coluna_data_venda_bitrix}).")
            
            # Atualizar df_cartorio com o resultado da filtragem
            df_cartorio = df_cartorio_filtrado
        else:
            st.info("Mostrando dados de todos os anos disponíveis (filtro de data de venda não aplicado a um ano específico).")
            
    elif ano_selecionado_valor != "Todos os anos": 
        st.warning(f"Não é possível aplicar o filtro de ano de venda, pois a coluna {coluna_data_venda_bitrix} está indisponível ou os dados do Bitrix (df_cartorio) estão vazios.")
        # Se df_cartorio está vazio aqui devido ao filtro de ano, precisamos esvaziar df_conclusao_raw também.
        if df_cartorio.empty: 
             print(f"[DEBUG Higienização Desempenho] df_cartorio ficou vazio devido ao filtro de ano. Esvaziando df_conclusao_raw.")
             df_conclusao_raw = pd.DataFrame(columns=df_conclusao_raw.columns if hasattr(df_conclusao_raw, 'columns') else [])

    # --- Filtrar df_conclusao_raw (planilha) com base nos IDs de família de df_cartorio (após filtro de ano de venda) ---
    if ano_selecionado_valor != "Todos os anos":
        if not df_cartorio.empty and 'UF_CRM_34_ID_FAMILIA' in df_cartorio.columns:
            # df_cartorio já foi filtrado pelo ano de venda.
            # Pegar os IDs de família que sobraram em df_cartorio.
            ids_familia_para_filtrar_planilha = df_cartorio['UF_CRM_34_ID_FAMILIA'].unique().tolist()
            print(f"[DEBUG Higienização Desempenho] IDs de família do Bitrix para o ano {ano_selecionado_valor} (usados para filtrar planilha): {len(ids_familia_para_filtrar_planilha)} IDs")

            if not df_conclusao_raw.empty and 'id_familia' in df_conclusao_raw.columns:
                # Filtrar df_conclusao_raw para manter apenas os IDs de família presentes em ids_familia_para_filtrar_planilha
                df_conclusao_raw = df_conclusao_raw[df_conclusao_raw['id_familia'].isin(ids_familia_para_filtrar_planilha)].copy()
                st.info(f"Métricas da planilha (higienização) também filtradas para famílias com venda no ano de {ano_selecionado_valor}.")
                print(f"[DEBUG Higienização Desempenho] df_conclusao_raw (planilha) filtrado por IDs do ano de venda. Registros restantes: {len(df_conclusao_raw)}")
            elif not df_conclusao_raw.empty: # df_conclusao_raw existe, mas não tem 'id_familia'
                print("[DEBUG Higienização Desempenho] Coluna 'id_familia' não encontrada em df_conclusao_raw para filtrar por ano de venda.")
                df_conclusao_raw = pd.DataFrame(columns=df_conclusao_raw.columns) # Esvaziar para evitar dados inconsistentes
            else: # df_conclusao_raw já estava vazio
                 print("[DEBUG Higienização Desempenho] df_conclusao_raw já estava vazio antes de filtrar por IDs do ano de venda.")
        
        elif df_cartorio.empty and ano_selecionado_valor != "Todos os anos":
            # Se df_cartorio ficou vazio após o filtro de ano, nenhuma família daquele ano foi encontrada no Bitrix.
            # Portanto, as métricas da planilha também devem ser zeradas para esse ano.
            print(f"[DEBUG Higienização Desempenho] df_cartorio está vazio após filtro de ano {ano_selecionado_valor}. Esvaziando df_conclusao_raw para as métricas da planilha.")
            df_conclusao_raw = pd.DataFrame(columns=df_conclusao_raw.columns if hasattr(df_conclusao_raw, 'columns') else [])
            
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
        'DT1098_102:SUCCESS': 'Brasileiras Dispensada',  # Certidão Entregue # ALTERADO DE Emitida PARA Dispensada (SOLICITAÇÃO DUPLICADA)
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
        
        # --- NOVA LÓGICA PARA Pasta C/Emissão Concluída ---
        # Uma família é considerada concluída se TODAS as suas certidões nos funis 92, 94, 102 estão "Emitidas"
        
        # Filtrar apenas certidões dos funis principais para a lógica de conclusão da pasta
        df_funis_principais = df_cartorio[
            df_cartorio['CATEGORY_ID'].astype(str).isin(['92', '94', '102'])
        ].copy()

        if not df_funis_principais.empty:
            # Agrupar por família e contar total de certidões e total de certidões emitidas nesses funis
            conclusao_por_familia = df_funis_principais.groupby(col_id_familia_bitrix).agg(
                total_certidoes_principais = ('STAGE_ID', 'count'),
                total_emitidas_principais = ('CATEGORIA_EMISSAO', lambda x: (x == 'Brasileiras Emitida').sum())
            ).reset_index()

            # Marcar família como concluída se todas as certidões dos funis principais foram emitidas
            # E se existe pelo menos uma certidão nos funis principais
            conclusao_por_familia['familia_concluida_logica_nova'] = (
                (conclusao_por_familia['total_certidoes_principais'] > 0) &
                (conclusao_por_familia['total_emitidas_principais'] == conclusao_por_familia['total_certidoes_principais'])
            ).astype(int)

            # Merge com df_bitrix_agg para adicionar a nova coluna de conclusão
            df_bitrix_agg = pd.merge(
                df_bitrix_agg.reset_index(), # Resetar índice se col_id_familia_bitrix não for índice ainda
                conclusao_por_familia[[col_id_familia_bitrix, 'familia_concluida_logica_nova']],
                on=col_id_familia_bitrix,
                how='left'
            )
            df_bitrix_agg['Pasta C/Emissão Concluída'] = df_bitrix_agg['familia_concluida_logica_nova'].fillna(0).astype(int)
            df_bitrix_agg = df_bitrix_agg.drop(columns=['familia_concluida_logica_nova', 'index'], errors='ignore')
        else:
            # Se não houver certidões nos funis principais (raro, mas para segurança)
            if col_id_familia_bitrix in df_bitrix_agg.columns:
                 df_bitrix_agg = df_bitrix_agg.reset_index() # Assegurar que col_id_familia_bitrix é coluna
            df_bitrix_agg['Pasta C/Emissão Concluída'] = 0
        
        # Garantir que a coluna de ID da família esteja presente se df_bitrix_agg foi recriado ou ficou vazio
        if col_id_familia_bitrix not in df_bitrix_agg.columns and not df_bitrix_agg.empty:
            # Se o ID da família era o índice e foi perdido, tentar recuperar (caso específico)
            # Esta situação é menos provável com o reset_index() acima, mas como fallback.
            if 'index' in df_bitrix_agg.columns and df_bitrix_agg['index'].nunique() == len(df_bitrix_agg):
                 df_bitrix_agg[col_id_familia_bitrix] = df_bitrix_agg['index']
            # Se não, e a coluna realmente sumiu, pode ser necessário recriar com IDs únicos se possível
            # ou aceitar que o merge com df_conclusao_raw pode falhar parcialmente.

        print(f"[DEBUG HIGIENIZAÇÃO] Nova lógica: {df_bitrix_agg['Pasta C/Emissão Concluída'].sum()} famílias com emissão concluída")
        
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

    # --- Exibir a Tabela de PROTOCOLADO (Lógica customizada) ---
    df_cabines_final_custom = pd.DataFrame()
    familias_sem_responsavel_df = pd.DataFrame()
    
    # Verifica se os dataframes base existem e não estão vazios antes de prosseguir
    if 'df_conclusao_raw' in locals() and not df_conclusao_raw.empty and 'df_cartorio' in locals() and not df_cartorio.empty:
        # 1. Identificar famílias da mesa 'Cabines' a partir dos dados já filtrados pela UI
        protocolado_ids = df_conclusao_raw[df_conclusao_raw['mesa'].str.upper() == 'CABINES']['id_familia'].unique()

        if len(protocolado_ids) > 0:
            # 2. Filtrar dados de conclusão para essas famílias
            df_conclusao_protocolado = df_conclusao_raw[df_conclusao_raw['id_familia'].isin(protocolado_ids)].copy()
            
            # 3. Mapear ID da Família para o Consultor (ASSIGNED_BY_NAME) do Bitrix
            consultor_mapping = df_cartorio[df_cartorio['UF_CRM_34_ID_FAMILIA'].isin(protocolado_ids)][['UF_CRM_34_ID_FAMILIA', 'ASSIGNED_BY_NAME']].copy()
            consultor_mapping.dropna(subset=['ASSIGNED_BY_NAME'], inplace=True)
            consultor_mapping = consultor_mapping.drop_duplicates(subset=['UF_CRM_34_ID_FAMILIA'], keep='first')
            consultor_mapping.rename(columns={'ASSIGNED_BY_NAME': 'CONSULTOR'}, inplace=True)

            # Juntar o nome do consultor aos dados de conclusão
            df_conclusao_protocolado = pd.merge(
                df_conclusao_protocolado, consultor_mapping, 
                left_on='id_familia', right_on='UF_CRM_34_ID_FAMILIA', how='left'
            )
            df_conclusao_protocolado['CONSULTOR'].fillna('Sem Responsável', inplace=True)

            familias_sem_responsavel_df = df_conclusao_protocolado[df_conclusao_protocolado['CONSULTOR'] == 'Sem Responsável'].copy()

            # 4. Agregar métricas da planilha por CONSULTOR, contando famílias únicas para PASTAS TOTAIS
            agg_dict_protocolado = {
                'higienizacao_exito': 'sum', 'higienizacao_incompleta': 'sum',
                'higienizacao_tratadas': 'sum', 'higienizacao_distrato': 'sum',
                'id_familia': 'nunique'
            }
            df_cabines_agg = df_conclusao_protocolado.groupby('CONSULTOR').agg(agg_dict_protocolado).reset_index()
            df_cabines_agg.rename(columns={
                'id_familia': 'PASTAS TOTAIS',
                'higienizacao_exito': 'HIGINIZAÇÃO COM ÊXITO',
                'higienizacao_incompleta': 'HIGINIZAÇÃO INCOMPLETA',
                'higienizacao_tratadas': 'HIGINIZAÇÃO TRATADAS',
                'higienizacao_distrato': 'DISTRATO'
            }, inplace=True)

            # 5. Juntar as métricas agregadas do Bitrix (df_bitrix_agg)
            if not df_bitrix_agg.empty:
                df_bitrix_protocolado = df_bitrix_agg[df_bitrix_agg[col_id_familia_bitrix].isin(protocolado_ids)].copy()
                df_bitrix_protocolado = pd.merge(df_bitrix_protocolado, consultor_mapping, left_on=col_id_familia_bitrix, right_on='UF_CRM_34_ID_FAMILIA', how='left')
                df_bitrix_protocolado['CONSULTOR'].fillna('Sem Responsável', inplace=True)

                metricas_bitrix = ['Brasileiras Pendências', 'Brasileiras Pesquisas', 'Brasileiras Solicitadas', 'Brasileiras Emitida', 'Pasta C/Emissão Concluída', 'Brasileiras Dispensada']
                df_bitrix_agg_by_consultor = df_bitrix_protocolado.groupby('CONSULTOR')[metricas_bitrix].sum().reset_index()
                
                df_cabines_final_custom = pd.merge(df_cabines_agg, df_bitrix_agg_by_consultor, on='CONSULTOR', how='outer').fillna(0)
            else:
                df_cabines_final_custom = df_cabines_agg.copy()

            # 7. Garantir colunas e calcular métricas derivadas
            for col in ordem_colunas:
                if col not in df_cabines_final_custom.columns:
                    if col in ['CONVERSÃO (%)', 'Taxa Emissão Concluída (%)']: df_cabines_final_custom[col] = 0.0
                    elif col == 'MESA': df_cabines_final_custom[col] = 'PROTOCOLADO'
                    elif col != 'CONSULTOR': df_cabines_final_custom[col] = 0
            
            df_cabines_final_custom['CONVERSÃO (%)'] = np.where(df_cabines_final_custom['PASTAS TOTAIS'] > 0, (df_cabines_final_custom['HIGINIZAÇÃO COM ÊXITO'] / df_cabines_final_custom['PASTAS TOTAIS']) * 100, 0).round(2)
            df_cabines_final_custom['Taxa Emissão Concluída (%)'] = np.where(df_cabines_final_custom['PASTAS TOTAIS'] > 0, (df_cabines_final_custom['Pasta C/Emissão Concluída'] / df_cabines_final_custom['PASTAS TOTAIS']) * 100, 0).round(2)
            
            df_cabines_final_custom = df_cabines_final_custom.reindex(columns=ordem_colunas).fillna(0)

    # Exibir o card e a tabela de PROTOCOLADO se houver dados
    if not df_cabines_final_custom.empty:
        total_cabines = df_cabines_final_custom['Pasta C/Emissão Concluída'].sum()

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

        df_total_cabines = df_cabines_final_custom.select_dtypes(include=np.number).sum().to_frame().T
        df_total_cabines['MESA'] = 'TOTAL'
        df_total_cabines['CONSULTOR'] = '' # Total não tem consultor
        
        # Recalcular percentuais para a linha de total
        if df_total_cabines['PASTAS TOTAIS'].iloc[0] > 0:
            df_total_cabines['CONVERSÃO (%)'] = (df_total_cabines['HIGINIZAÇÃO COM ÊXITO'] / df_total_cabines['PASTAS TOTAIS'] * 100).round(2)
            df_total_cabines['Taxa Emissão Concluída (%)'] = (df_total_cabines['Pasta C/Emissão Concluída'] / df_total_cabines['PASTAS TOTAIS'] * 100).round(2)
        else:
            df_total_cabines['CONVERSÃO (%)'] = 0.0
            df_total_cabines['Taxa Emissão Concluída (%)'] = 0.0

        df_display_cabines = pd.concat([df_cabines_final_custom, df_total_cabines], ignore_index=True)
        df_display_cabines = ensure_numeric_display(df_display_cabines)
        
        df_percent_cabines = df_display_cabines.copy()
        if 'CONVERSÃO (%)' in df_percent_cabines.columns:
            df_percent_cabines['CONVERSÃO (%)'] = df_percent_cabines['CONVERSÃO (%)'].apply(lambda x: f"{x:.2f}%")
        if 'Taxa Emissão Concluída (%)' in df_percent_cabines.columns:
            df_percent_cabines['Taxa Emissão Concluída (%)'] = df_percent_cabines['Taxa Emissão Concluída (%)'].apply(lambda x: f"{x:.2f}%")
        
        html_table_cabines = df_percent_cabines.to_html(index=False, classes='dataframe')
        st.markdown(html_table_cabines, unsafe_allow_html=True)
        
        csv_cabines_detalhes = convert_df_to_csv(df_cabines_final_custom)
        st.download_button(
            label="Download Detalhes PROTOCOLADO como CSV",
            data=csv_cabines_detalhes,
            file_name='detalhes_protocolado.csv',
            mime='text/csv',
            key='download_protocolado_csv'
        )

        # Nova seção para exibir famílias "Sem Responsável"
        with st.expander("Ver Detalhes das Famílias 'Sem Responsável'"):
            if not familias_sem_responsavel_df.empty:
                st.write("""
                As famílias listadas abaixo pertencem à mesa 'Cabines' (Protocolado), mas não foi possível encontrar um responsável correspondente no Bitrix. 
                Isso pode ocorrer por algumas razões:
                - O campo 'Responsável' (`ASSIGNED_BY_NAME`) está vazio para o registro no Bitrix.
                - Não há mais um registro ativo no funil de emissões para o ID da família.
                - O responsável foi removido e não consta mais nos dados.
                """)
                
                # Selecionar e renomear colunas para exibição
                colunas_para_exibir = {
                    'id_familia': 'ID da Família',
                    'nome_familia': 'Nome da Família (Planilha)',
                    'responsavel': 'Responsável (Planilha)'
                }
                
                df_sem_responsavel_display = familias_sem_responsavel_df[list(colunas_para_exibir.keys())].copy()
                df_sem_responsavel_display.rename(columns=colunas_para_exibir, inplace=True)
                
                st.dataframe(df_sem_responsavel_display.drop_duplicates(), hide_index=True, use_container_width=True)
            else:
                st.info("Não foram encontradas famílias na categoria 'Sem Responsável' para os filtros atuais.")
    else:
        st.info("Não há dados de PROTOCOLADO para exibir com os filtros atuais.") 

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

    st.subheader("Desempenho da Higienização - Vendas Ano 2025")

    # Usar as cópias originais dos dataframes carregados para não serem afetadas pelos filtros globais
    # Estas cópias devem ser feitas logo após o carregamento inicial dos dados.
    # Assumindo que df_conclusao_raw_orig e df_cartorio_orig foram criados no início da função:
    # df_conclusao_raw_orig = load_conclusao_data(...).copy() # Exemplo de como seria no início
    # df_cartorio_orig = carregar_dados_cartorio().copy()     # Exemplo de como seria no início

    # Para esta edição, vamos simular que elas existem e derivar a lógica.
    # No código real, certifique-se de que df_conclusao_raw_orig e df_cartorio_orig 
    # são cópias dos dataframes *antes* de qualquer filtro interativo ser aplicado.
    
    # Se essas variáveis não foram definidas no escopo correto (início da função),
    # esta lógica precisará ser ajustada para recarregar ou usar as variáveis corretas.
    # Por simplicidade nesta edição, vamos assumir que estão disponíveis.
    # No contexto real da função, você faria:
    # df_cartorio_para_2025 = df_cartorio_orig.copy()
    # df_conclusao_para_2025 = df_conclusao_raw_orig.copy()
    # Mas como não posso modificar o início da função aqui, vou usar df_cartorio e df_conclusao_raw
    # e alertar que isso pode ser problemático se eles já estiverem filtrados.
    # A maneira correta seria ter df_cartorio_orig e df_conclusao_raw_orig.

    # Recarregando os dados para garantir que não estão filtrados pelos seletores da UI
    # Esta é uma forma de garantir dados não filtrados para a tabela específica de 2025
    df_conclusao_raw_para_2025 = load_conclusao_data(start_date=None, end_date=None)
    if df_conclusao_raw_para_2025 is None: df_conclusao_raw_para_2025 = pd.DataFrame()
    
    colunas_planilha_esperadas_2025 = ['responsavel', 'mesa', 'id_familia', 'nome_familia', 'higienizacao_exito', 'higienizacao_incompleta', 'higienizacao_tratadas', 'higienizacao_distrato']
    for col in colunas_planilha_esperadas_2025:
        if col not in df_conclusao_raw_para_2025.columns: df_conclusao_raw_para_2025[col] = None
    df_conclusao_raw_para_2025 = df_conclusao_raw_para_2025[[c for c in colunas_planilha_esperadas_2025 if c in df_conclusao_raw_para_2025.columns]].copy()
    df_conclusao_raw_para_2025 = df_conclusao_raw_para_2025.dropna(subset=['id_familia'])


    df_cartorio_para_2025 = carregar_dados_cartorio()
    if df_cartorio_para_2025 is None: df_cartorio_para_2025 = pd.DataFrame()

    df_display_2025 = pd.DataFrame() # DataFrame final para a tabela de 2025

    if not df_cartorio_para_2025.empty and 'DATA_VENDA_FAMILIA' in df_cartorio_para_2025.columns:
        df_cartorio_para_2025['DATA_VENDA_FAMILIA'] = pd.to_datetime(df_cartorio_para_2025['DATA_VENDA_FAMILIA'], errors='coerce')
        df_cartorio_vendas_2025_filtrado = df_cartorio_para_2025[df_cartorio_para_2025['DATA_VENDA_FAMILIA'].dt.year == 2025].copy()

        if not df_cartorio_vendas_2025_filtrado.empty:
            # Aplicar lógica de precedência do pipeline 104 específica para este subconjunto
            df_cartorio_vendas_2025_filtrado = aplicar_logica_precedencia_pipeline_104_higienizacao(df_cartorio_vendas_2025_filtrado)

            ids_familia_2025 = df_cartorio_vendas_2025_filtrado['UF_CRM_34_ID_FAMILIA'].unique().tolist()
            
            df_conclusao_raw_vendas_2025_filtrado = df_conclusao_raw_para_2025[df_conclusao_raw_para_2025['id_familia'].isin(ids_familia_2025)].copy()

            # Processar df_cartorio_vendas_2025_filtrado para criar df_bitrix_agg_2025
            df_bitrix_agg_2025 = pd.DataFrame()
            col_id_familia_bitrix_2025 = 'UF_CRM_34_ID_FAMILIA'

            if 'STAGE_ID' in df_cartorio_vendas_2025_filtrado.columns and col_id_familia_bitrix_2025 in df_cartorio_vendas_2025_filtrado.columns:
                df_cartorio_vendas_2025_filtrado['CATEGORIA_EMISSAO'] = df_cartorio_vendas_2025_filtrado['STAGE_ID'].map(mapeamento_stages).fillna('Categoria Desconhecida')
                df_bitrix_agg_2025_temp = pd.crosstab(df_cartorio_vendas_2025_filtrado[col_id_familia_bitrix_2025], df_cartorio_vendas_2025_filtrado['CATEGORIA_EMISSAO'])
                
                for col in categorias_bitrix_contagem: # categorias_bitrix_contagem é definida globalmente na função
                    if col not in df_bitrix_agg_2025_temp.columns: df_bitrix_agg_2025_temp[col] = 0
                if 'Categoria Desconhecida' in df_bitrix_agg_2025_temp.columns:
                    df_bitrix_agg_2025_temp['Brasileiras Pendências'] += df_bitrix_agg_2025_temp['Categoria Desconhecida']
                    df_bitrix_agg_2025_temp = df_bitrix_agg_2025_temp.drop(columns=['Categoria Desconhecida'], errors='ignore')
                df_bitrix_agg_2025_temp = df_bitrix_agg_2025_temp.reindex(columns=categorias_bitrix_contagem, fill_value=0)
                
                # Lógica Pasta C/Emissão Concluída para 2025
                df_funis_principais_2025 = df_cartorio_vendas_2025_filtrado[
                    df_cartorio_vendas_2025_filtrado['CATEGORY_ID'].astype(str).isin(['92', '94', '102'])
                ].copy()
                if not df_funis_principais_2025.empty:
                    conclusao_por_familia_2025 = df_funis_principais_2025.groupby(col_id_familia_bitrix_2025).agg(
                        total_certidoes_principais=('STAGE_ID', 'count'),
                        total_emitidas_principais=('CATEGORIA_EMISSAO', lambda x: (x == 'Brasileiras Emitida').sum())
                    ).reset_index()
                    conclusao_por_familia_2025['familia_concluida_logica_nova'] = (
                        (conclusao_por_familia_2025['total_certidoes_principais'] > 0) &
                        (conclusao_por_familia_2025['total_emitidas_principais'] == conclusao_por_familia_2025['total_certidoes_principais'])
                    ).astype(int)
                    df_bitrix_agg_2025_temp = pd.merge(
                        df_bitrix_agg_2025_temp.reset_index(),
                        conclusao_por_familia_2025[[col_id_familia_bitrix_2025, 'familia_concluida_logica_nova']],
                        on=col_id_familia_bitrix_2025,
                        how='left'
                    )
                    df_bitrix_agg_2025_temp['Pasta C/Emissão Concluída'] = df_bitrix_agg_2025_temp['familia_concluida_logica_nova'].fillna(0).astype(int)
                    df_bitrix_agg_2025 = df_bitrix_agg_2025_temp.drop(columns=['familia_concluida_logica_nova', 'index'], errors='ignore') # Adicionado 'index' aqui
                    if col_id_familia_bitrix_2025 not in df_bitrix_agg_2025.columns and col_id_familia_bitrix_2025 in df_bitrix_agg_2025_temp.reset_index().columns: # Garantir que o ID da família esteja lá
                        df_bitrix_agg_2025[col_id_familia_bitrix_2025] = df_bitrix_agg_2025_temp.reset_index()[col_id_familia_bitrix_2025]

                else: # Adicionado .copy() para evitar SettingWithCopyWarning
                    df_bitrix_agg_2025 = df_bitrix_agg_2025_temp.copy()
                    df_bitrix_agg_2025['Pasta C/Emissão Concluída'] = 0


            # Merge para 2025
            df_merged_2025 = pd.merge(
                df_conclusao_raw_vendas_2025_filtrado, df_bitrix_agg_2025,
                left_on='id_familia', right_on=col_id_familia_bitrix_2025, how='left'
            )
            for col in novas_colunas_bitrix: # novas_colunas_bitrix é definida globalmente
                if col not in df_merged_2025.columns: df_merged_2025[col] = 0
                df_merged_2025[col] = df_merged_2025[col].fillna(0).astype(int)

            # Agregação para 2025 por mesa
            agg_dict_2025 = {
                'higienizacao_exito': 'sum', 'higienizacao_incompleta': 'sum',
                'higienizacao_tratadas': 'sum', 'higienizacao_distrato': 'sum',
                'Brasileiras Pendências': 'sum', 'Brasileiras Pesquisas': 'sum',
                'Brasileiras Solicitadas': 'sum', 'Brasileiras Emitida': 'sum',
                'Pasta C/Emissão Concluída': 'sum', 'Brasileiras Dispensada': 'sum',
                'id_familia': 'nunique' # Para PASTAS TOTAIS
            }
            df_agregado_2025 = df_merged_2025.groupby('mesa').agg(agg_dict_2025).reset_index()
            df_agregado_2025 = df_agregado_2025.rename(columns={
                'mesa': 'MESA', 'higienizacao_exito': 'HIGINIZAÇÃO COM ÊXITO',
                'higienizacao_incompleta': 'HIGINIZAÇÃO INCOMPLETA',
                'higienizacao_tratadas': 'HIGINIZAÇÃO TRATADAS',
                'higienizacao_distrato': 'DISTRATO',
                'id_familia': 'PASTAS TOTAIS' # Renomear contagem de ID para PASTAS TOTAIS
            })

            # Adicionar CONSULTOR do df_base
            if 'df_base' in locals() and isinstance(df_base, pd.DataFrame): # df_base é definido globalmente
                 df_agregado_2025 = pd.merge(df_agregado_2025, df_base[['MESA', 'CONSULTOR']], on='MESA', how='left')
                 df_agregado_2025['CONSULTOR'] = df_agregado_2025['CONSULTOR'].fillna('N/A')


            # Calcular métricas para 2025
            df_agregado_2025['CONVERSÃO (%)'] = np.where(
                df_agregado_2025['PASTAS TOTAIS'] > 0,
                (df_agregado_2025['HIGINIZAÇÃO COM ÊXITO'] / df_agregado_2025['PASTAS TOTAIS']) * 100, 0
            ).round(2)
            df_agregado_2025['Taxa Emissão Concluída (%)'] = np.where(
                df_agregado_2025['PASTAS TOTAIS'] > 0,
                (df_agregado_2025['Pasta C/Emissão Concluída'] / df_agregado_2025['PASTAS TOTAIS']) * 100, 0
            ).round(2)

            # Garantir todas as colunas da ordem_colunas e preencher com 0/0.0 se faltarem
            for col in ordem_colunas: # ordem_colunas é definida globalmente
                if col not in df_agregado_2025.columns:
                    if col in ['CONVERSÃO (%)', 'Taxa Emissão Concluída (%)']:
                        df_agregado_2025[col] = 0.0
                    elif col == 'CONSULTOR':
                        df_agregado_2025[col] = "N/A"
                    else:
                        df_agregado_2025[col] = 0
            
            df_display_2025 = df_agregado_2025[ordem_colunas].copy() # Aplicar a ordem
            df_display_2025 = ensure_numeric_display(df_display_2025) # Aplicar formatação numérica

            # Adicionar linha de TOTAL para 2025
            if not df_display_2025.empty:
                df_total_2025 = df_display_2025.select_dtypes(include=np.number).sum().to_frame().T
                df_total_2025['MESA'] = 'TOTAL'
                df_total_2025['CONSULTOR'] = ''
                if df_total_2025['PASTAS TOTAIS'].iloc[0] > 0:
                    df_total_2025['CONVERSÃO (%)'] = (df_total_2025['HIGINIZAÇÃO COM ÊXITO'] / df_total_2025['PASTAS TOTAIS'] * 100).round(2)
                    df_total_2025['Taxa Emissão Concluída (%)'] = (df_total_2025['Pasta C/Emissão Concluída'] / df_total_2025['PASTAS TOTAIS'] * 100).round(2)
                else:
                    df_total_2025['CONVERSÃO (%)'] = 0.0
                    df_total_2025['Taxa Emissão Concluída (%)'] = 0.0
                df_total_2025 = ensure_numeric_display(df_total_2025)
                df_display_2025 = pd.concat([df_display_2025, df_total_2025], ignore_index=True)
        
        if not df_display_2025.empty:
            st.markdown("##### Desempenho Higienização - Vendas Ano 2025")
            df_percent_2025 = df_display_2025.copy()
            if 'CONVERSÃO (%)' in df_percent_2025.columns:
                df_percent_2025['CONVERSÃO (%)'] = df_percent_2025['CONVERSÃO (%)'].apply(lambda x: f"{x:.2f}%")
            if 'Taxa Emissão Concluída (%)' in df_percent_2025.columns:
                df_percent_2025['Taxa Emissão Concluída (%)'] = df_percent_2025['Taxa Emissão Concluída (%)'].apply(lambda x: f"{x:.2f}%")
            
            html_table_2025 = df_percent_2025.to_html(index=False, classes='dataframe')
            st.markdown(html_table_2025, unsafe_allow_html=True)

            csv_2025 = convert_df_to_csv(df_display_2025) # convert_df_to_csv é definido globalmente
            st.download_button(
                label="Download Tabela Vendas 2025 como CSV",
                data=csv_2025,
                file_name='desempenho_higienizacao_vendas_2025.csv',
                mime='text/csv',
                key='download_vendas_2025_csv'
            )
        else:
            st.info("Não foram encontrados dados de vendas para o ano de 2025.")
    else:
        st.info("Não foi possível gerar a tabela de vendas para 2025 (coluna 'DATA_VENDA_FAMILIA' não encontrada ou dados do cartório vazios).")

    # Fim da função exibir_higienizacao_desempenho
    # Nenhum return explícito é necessário se a função apenas exibe elementos do Streamlit

# Certifique-se de que as variáveis globais como mapeamento_stages, categorias_bitrix_contagem,
# novas_colunas_bitrix, ordem_colunas, df_base e a função convert_df_to_csv
# estejam acessíveis no escopo onde esta nova seção de código é adicionada.
# Normalmente, elas são definidas no início da função exibir_higienizacao_desempenho.
# A função ensure_numeric_display também deve estar definida.
# A função aplicar_logica_precedencia_pipeline_104_higienizacao também.

# Onde colocar as cópias df_conclusao_raw_orig e df_cartorio_orig:
# Idealmente, logo após estas linhas:
#   df_conclusao_raw = load_conclusao_data(start_date=start_date_to_load, end_date=end_date_to_load)
#   ... (processamento de df_conclusao_raw) ...
#   df_conclusao_raw_orig = df_conclusao_raw.copy()
#
#   df_cartorio = carregar_dados_cartorio()
#   ... (processamento de df_cartorio se houver algum antes dos filtros) ...
#   df_cartorio_orig = df_cartorio.copy()
#
# E então a nova seção usaria _orig. No entanto, a ferramenta de edição atual
# edita em um só bloco. A solução de recarregar os dados para a tabela 2025,
# como fiz acima (df_conclusao_raw_para_2025 = load_conclusao_data(), etc.),
# é uma alternativa viável para garantir dados não filtrados para esta seção específica,
# embora possa ter um pequeno custo de performance se os dados forem grandes.
# Dada a complexidade, esta recarga isolada é mais segura para a edição.

# A adição de 'index' em:
# df_bitrix_agg_2025 = df_bitrix_agg_2025_temp.drop(columns=['familia_concluida_logica_nova', 'index'], errors='ignore')
# é para o caso de reset_index() ter sido chamado em df_bitrix_agg_2025_temp, que pode adicionar uma coluna 'index'.

# A garantia if col_id_familia_bitrix_2025 not in df_bitrix_agg_2025.columns...
# é para tentar readicionar o ID da família se ele se perder após o merge e drop de colunas.
# Em pd.merge(..., right_on=col_id_familia_bitrix_2025, ...), o ID da família do lado direito
# (df_bitrix_agg_2025) é usado para o merge, então ele deve estar como uma coluna lá.
# Se o `reset_index()` foi feito em `df_bitrix_agg_2025_temp`, o ID da família torna-se uma coluna.
# A linha original `df_bitrix_agg = df_bitrix_agg.drop(columns=['familia_concluida_logica_nova', 'index'], errors='ignore')`
# já remove 'index', então é provável que o ID da família já seja uma coluna se o reset_index foi feito.
# O mais importante é que `col_id_familia_bitrix_2025` seja o nome da coluna com ID da família em `df_bitrix_agg_2025`
# antes do merge final com `df_conclusao_raw_vendas_2025_filtrado`.

# O código para df_bitrix_agg_2025 foi ajustado para usar df_bitrix_agg_2025_temp e depois atribuir a df_bitrix_agg_2025
# para evitar modificar o DataFrame enquanto itera ou faz merges parciais que podem perder o ID da família.
# A lógica para `Pasta C/Emissão Concluída` foi aninhada para garantir que `df_bitrix_agg_2025` seja construído passo a passo.
# Adicionado .copy() em `df_bitrix_agg_2025 = df_bitrix_agg_2025_temp.copy()` para o caso de `df_funis_principais_2025` ser vazio.

# Correção em `Pasta C/Emissão Concluída` para `df_bitrix_agg_2025`
# Se `df_bitrix_agg_2025_temp.reset_index()` foi chamado e `col_id_familia_bitrix_2025` era o índice,
# ele agora é uma coluna. Então `df_bitrix_agg_2025_temp[[col_id_familia_bitrix_2025, 'familia_concluida_logica_nova']]` deve funcionar.
# O `drop(columns=['index']` após `reset_index()` pode ser necessário se o índice original não tiver nome ou não for o ID da família.
# No código acima, `df_bitrix_agg_2025_temp.reset_index()` é usado no merge, então o ID da família (se era índice) torna-se coluna.
# A parte final `df_bitrix_agg_2025 = df_bitrix_agg_2025_temp.drop(columns=['familia_concluida_logica_nova', 'index'], errors='ignore')`
# e a verificação subsequente tentam garantir que o ID da família permaneça.
# O crucial é que `df_bitrix_agg_2025` que entra no merge final com `df_conclusao_raw_vendas_2025_filtrado`
# tenha o `col_id_familia_bitrix_2025` como uma coluna.

# Verifiquei as variáveis globais:
# - mapeamento_stages: OK
# - categorias_bitrix_contagem: OK
# - novas_colunas_bitrix: OK
# - ordem_colunas: OK
# - df_base: OK (verificado com `locals()`)
# - convert_df_to_csv: OK (definido como cache_data no início da função)
# - ensure_numeric_display: OK (definido no início do arquivo)
# - aplicar_logica_precedencia_pipeline_104_higienizacao: OK (definido no início do arquivo)

# A lógica de recarregar `df_conclusao_raw_para_2025` e `df_cartorio_para_2025` no início
# desta nova seção é a forma mais robusta de garantir dados não filtrados para esta tabela específica.
# O resto da função `exibir_higienizacao_desempenho` continuará a usar as variáveis `df_conclusao_raw` e `df_cartorio`
# que são progressivamente filtradas pelos seletores da UI.