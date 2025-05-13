import streamlit as st
import pandas as pd
from data.load_conclusao_higienizacao import load_conclusao_data
from views.cartorio_new.data_loader import carregar_dados_cartorio # Importar dados do cartório
from datetime import datetime, timedelta
import re # Para extrair ID da opção do selectbox
import numpy as np # Para operações numéricas
import os # Para verificar se o arquivo existe

def exibir_higienizacao_desempenho():
    """
    Exibe a tabela de desempenho da higienização por mesa e consultor,
    com opção de filtro por data e dados de emissões do Bitrix.
    """
    st.subheader("Desempenho da Higienização por Mesa")

    # --- Filtros --- 
    st.markdown("**Filtros:**")
    
    # --- Filtro de Data (Opcional) ---
    col_data1, col_data2, col_data_check = st.columns([2,2,1])
    
    with col_data1:
        data_inicio_filtro = st.date_input("Data Início (Opcional)", value=None) # Inicia como None
    with col_data2:
        data_fim_filtro = st.date_input("Data Fim (Opcional)", value=None) # Inicia como None
    with col_data_check:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) # Espaçador
        aplicar_filtro_data = st.checkbox("Aplicar Datas", value=False, help="Marque para filtrar os dados da planilha pelo período selecionado.")

    # Variáveis para passar para a função de carregamento
    start_date_to_load = None
    end_date_to_load = None

    if aplicar_filtro_data:
        if data_inicio_filtro and data_fim_filtro:
            if data_inicio_filtro > data_fim_filtro:
                st.warning("A data de início não pode ser posterior à data de fim.")
                return # Ou desabilitar o filtro
            start_date_to_load = data_inicio_filtro
            end_date_to_load = data_fim_filtro
            st.info(f"Filtro de data aplicado: {start_date_to_load.strftime('%d/%m/%Y')} a {end_date_to_load.strftime('%d/%m/%Y')}")
        elif data_inicio_filtro or data_fim_filtro: # Se apenas uma data for preenchida
            st.warning("Por favor, selecione ambas as datas (início e fim) para aplicar o filtro de data.")
            # Considerar não aplicar o filtro se apenas uma data estiver definida
            # Ou definir um comportamento padrão (ex: usar a data preenchida como início e hoje como fim)

    # --- Carregar Dados (Necessário antes dos filtros por família para popular selectbox) ---
    # 1. Dados da Planilha de Conclusão
    spinner_message = "Carregando todos os dados de conclusão da planilha..."
    if start_date_to_load and end_date_to_load:
        spinner_message = f"Carregando dados de conclusão entre {start_date_to_load.strftime('%d/%m/%Y')} e {end_date_to_load.strftime('%d/%m/%Y')}..."
    
    with st.spinner(spinner_message):
        # Tentar carregar dados da planilha Google
        df_conclusao_raw = load_conclusao_data(start_date=start_date_to_load, end_date=end_date_to_load)
        
        # Verificar se df_conclusao_raw está vazio (falha ao carregar)
        if df_conclusao_raw.empty:
            # Tentar carregar dados locais como fallback
            st.warning("Não foi possível carregar os dados da planilha Google. Tentando usar dados locais...")
            try:
                # Verificar se temos um arquivo CSV local para usar
                local_data_path = os.path.join("data", "conclusao_higienizacao_local.csv")
                if os.path.exists(local_data_path):
                    df_conclusao_raw = pd.read_csv(local_data_path)
                    st.success("Dados locais carregados com sucesso!")
                    
                    # Converter colunas de data se necessário
                    if 'data' in df_conclusao_raw.columns:
                        df_conclusao_raw['data'] = pd.to_datetime(df_conclusao_raw['data'], errors='coerce')
                        
                    # Aplicar filtro de data se necessário
                    if start_date_to_load and end_date_to_load and 'data' in df_conclusao_raw.columns:
                        start_datetime = datetime.combine(start_date_to_load, datetime.min.time())
                        end_datetime = datetime.combine(end_date_to_load, datetime.max.time())
                        df_filtrado = df_conclusao_raw.dropna(subset=['data']).copy()
                        mask = (df_filtrado['data'] >= start_datetime) & (df_filtrado['data'] <= end_datetime)
                        df_conclusao_raw = df_filtrado[mask]
                else:
                    st.error("Arquivo de dados locais não encontrado.")
                    # Criar um DataFrame vazio com as colunas esperadas
                    df_conclusao_raw = pd.DataFrame()
            except Exception as e:
                st.error(f"Erro ao carregar dados locais: {str(e)}")
                df_conclusao_raw = pd.DataFrame()

        # Garantir colunas mesmo se vazio
        colunas_planilha_esperadas = ['responsavel', 'mesa', 'id_familia', 'nome_familia', 'higienizacao_exito', 'higienizacao_incompleta', 'higienizacao_tratadas']
        for col in colunas_planilha_esperadas:
            if col not in df_conclusao_raw.columns:
                df_conclusao_raw[col] = None # Adiciona coluna vazia se ausente

        # Selecionar colunas necessárias (incluindo nome_familia agora)
        colunas_planilha = ['responsavel', 'mesa', 'id_familia', 'nome_familia', 'higienizacao_exito', 'higienizacao_incompleta', 'higienizacao_tratadas']
        # Filtrar para selecionar apenas as colunas que existem
        colunas_existentes = [col for col in colunas_planilha if col in df_conclusao_raw.columns]
        df_conclusao_raw = df_conclusao_raw[colunas_existentes].copy()
        
        # Remover linhas sem ID somente se a coluna existir
        if 'id_familia' in df_conclusao_raw.columns:
            df_conclusao_raw = df_conclusao_raw.dropna(subset=['id_familia']) # Remover linhas sem ID

    # Adicionar um botão para salvar dados locais para uso futuro
    if not df_conclusao_raw.empty:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📥 Salvar dados localmente", help="Salva os dados atuais em um arquivo local para uso futuro"):
                try:
                    # Criar diretório 'data' se não existir
                    os.makedirs("data", exist_ok=True)
                    # Salvar em CSV
                    local_data_path = os.path.join("data", "conclusao_higienizacao_local.csv")
                    df_conclusao_raw.to_csv(local_data_path, index=False)
                    st.success(f"Dados salvos com sucesso em {local_data_path}")
                except Exception as e:
                    st.error(f"Erro ao salvar dados: {str(e)}")

    # 2. Dados do Bitrix (Funil Emissões 1098)
    with st.spinner("Carregando dados de emissões do Bitrix..."):
        df_cartorio = carregar_dados_cartorio()
        if df_cartorio is None or df_cartorio.empty:
            df_cartorio = pd.DataFrame() # Continuar com DF vazio
            st.warning("Não foi possível carregar os dados de emissões do Bitrix.")
            
            # Tentar carregar dados locais como fallback
            try:
                local_cartorio_path = os.path.join("data", "emissoes_bitrix_local.csv")
                if os.path.exists(local_cartorio_path):
                    df_cartorio = pd.read_csv(local_cartorio_path)
                    st.success("Dados locais de emissões carregados com sucesso!")
            except Exception as e:
                st.error(f"Erro ao carregar dados locais de emissões: {str(e)}")

    # Adicionar botão para salvar dados de emissões localmente
    if not df_cartorio.empty:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📥 Salvar emissões localmente", help="Salva os dados de emissões em um arquivo local para uso futuro"):
                try:
                    # Criar diretório 'data' se não existir
                    os.makedirs("data", exist_ok=True)
                    # Salvar em CSV
                    local_cartorio_path = os.path.join("data", "emissoes_bitrix_local.csv")
                    df_cartorio.to_csv(local_cartorio_path, index=False)
                    st.success(f"Dados de emissões salvos com sucesso em {local_cartorio_path}")
                except Exception as e:
                    st.error(f"Erro ao salvar dados de emissões: {str(e)}")

    # --- Widgets de Filtro por Família --- 
    col_filtros1, col_filtros2 = st.columns(2)
    
    with col_filtros1:
        filtro_id_familia = st.text_input("ID da Família (exato)", key="filtro_id_fam")
        filtro_id_familia = filtro_id_familia.strip() # Remover espaços extras do input

    with col_filtros2:
        opcoes_familia = ["Todas"] # Opção padrão
        if not df_conclusao_raw.empty:
            # Criar coluna formatada para o selectbox, tratando NaNs
            df_conclusao_raw['nome_familia'] = df_conclusao_raw['nome_familia'].fillna('Sem Nome')
            df_conclusao_raw['responsavel'] = df_conclusao_raw['responsavel'].fillna('Sem Responsável')
            df_conclusao_raw['id_familia'] = df_conclusao_raw['id_familia'].astype(str) # Garantir string

            df_conclusao_raw['opcao_selectbox'] = df_conclusao_raw.apply(
                lambda row: f"{row['nome_familia']} \\ {row['responsavel']} \\ {row['id_familia']}", axis=1
            )
            lista_opcoes = sorted(df_conclusao_raw['opcao_selectbox'].unique().tolist())
            opcoes_familia.extend(lista_opcoes)
        
        filtro_nome_familia_selecionado = st.selectbox(
            "Nome da Família (\ Responsável \ ID)", 
            options=opcoes_familia, 
            key="filtro_nome_fam"
        )

    # --- Aplicar Filtros por Família --- 
    id_familia_filtrar = None
    
    # Prioridade 1: Filtro por ID digitado
    if filtro_id_familia:
        id_familia_filtrar = filtro_id_familia
        st.info(f"Filtrando pelo ID da Família: {id_familia_filtrar}")
    # Prioridade 2: Filtro por nome selecionado (se ID não foi digitado)
    elif filtro_nome_familia_selecionado != "Todas":
        # Extrair o ID da string selecionada (última parte após \\)
        match = re.search(r'\\ ([^\\]+)$', filtro_nome_familia_selecionado)
        if match:
            id_familia_filtrar = match.group(1).strip()
            st.info(f"Filtrando pela família selecionada (ID: {id_familia_filtrar})")
        else:
            st.warning("Não foi possível extrair o ID da família da opção selecionada.")

    # Aplicar filtro se um ID foi definido
    if id_familia_filtrar:
        df_conclusao_raw = df_conclusao_raw[df_conclusao_raw['id_familia'] == id_familia_filtrar].copy()
        if not df_cartorio.empty and 'UF_CRM_34_ID_FAMILIA' in df_cartorio.columns:
            df_cartorio = df_cartorio[df_cartorio['UF_CRM_34_ID_FAMILIA'] == id_familia_filtrar].copy()
        
        if df_conclusao_raw.empty:
             st.warning(f"Nenhum dado de higienização encontrado para a família ID: {id_familia_filtrar} no período selecionado.")
             # Limpar df_bitrix_agg para não mostrar dados de emissão órfãos
             if 'df_bitrix_agg' in locals(): df_bitrix_agg = pd.DataFrame(columns=df_bitrix_agg.columns)

    # --- Calcular Contagem SEM PROTOCOLO (Mesas 1-8) ANTES da tabela principal ---
    # Renomear variável para clareza
    contagem_total_mesas_1_8 = 0
    if not df_conclusao_raw.empty and 'mesa' in df_conclusao_raw.columns:
        # Remover filtro de incompletas - Contar TOTAL
        # df_incompletas_geral_temp = df_conclusao_raw[df_conclusao_raw['higienizacao_incompleta'] == True].copy()
        mesas_1_8 = [f'MESA {i}' for i in range(1, 9)]
        contagem_total_mesas_1_8 = df_conclusao_raw[df_conclusao_raw['mesa'].isin(mesas_1_8)].shape[0]
    
    # Estilo CSS para a faixa (pode ser reutilizado ou definido aqui)
    faixa_style = "background-color: #FFA726; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
    titulo_style = "color: white; margin: 0; font-size: 1.1em; font-weight: bold;"
    contagem_style = "color: white; font-size: 2em; font-weight: bolder; margin: 8px 0 0 0;"

    # Exibir Faixa 1: TOTAL Mesas 1-8
    st.markdown(f"""
    <div style="{faixa_style}">
        <h4 style="{titulo_style}">EMISSÕES INCOMPLETAS ALPHA SEM PROTOCOLO (MESAS 1-8)</h4>
        <p style="{contagem_style}">{contagem_total_mesas_1_8} PASTAS</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("--- ") # Separador antes da tabela principal

    # --- Mapeamento de Estágios Bitrix --- 
    mapeamento_stages = {
        # Casa Verde (92)
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
        'DT1098_92:UC_5LWUTX': 'Pasta C/Emissão Concluída',
        'DT1098_92:FAIL': 'Brasileiras Dispensada',
        'DT1098_92:UC_Z24IF7': 'Brasileiras Dispensada',
        'DT1098_92:SUCCESS': 'Pasta C/Emissão Concluída',
        # Tatuapé (94)
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
        'DT1098_94:UC_K4JS04': 'Pasta C/Emissão Concluída',
        'DT1098_94:FAIL': 'Brasileiras Dispensada',
        'DT1098_94:UC_MGTPX0': 'Brasileiras Dispensada',
        'DT1098_94:SUCCESS': 'Pasta C/Emissão Concluída'
    }
    col_id_familia_bitrix = 'UF_CRM_34_ID_FAMILIA'

    # Aplicar mapeamento e agregar dados do Bitrix por ID Família
    if not df_cartorio.empty and 'STAGE_ID' in df_cartorio.columns and col_id_familia_bitrix in df_cartorio.columns:
        df_cartorio['CATEGORIA_EMISSAO'] = df_cartorio['STAGE_ID'].map(mapeamento_stages).fillna('Categoria Desconhecida')
        # Contar as ocorrências de cada categoria por família
        df_bitrix_agg = pd.crosstab(df_cartorio[col_id_familia_bitrix], df_cartorio['CATEGORIA_EMISSAO'])
        # Renomear colunas para evitar conflitos e garantir nomes desejados
        novas_colunas_bitrix = [
            'Brasileiras Pendências', 'Brasileiras Pesquisas', 'Brasileiras Solicitadas',
            'Brasileiras Emitidas', 'Pasta C/Emissão Concluída', 'Brasileiras Dispensada'
        ]
        # Adicionar colunas faltantes com 0
        for col in novas_colunas_bitrix:
            if col not in df_bitrix_agg.columns:
                 df_bitrix_agg[col] = 0
        df_bitrix_agg = df_bitrix_agg[novas_colunas_bitrix] # Garantir ordem e seleção
        df_bitrix_agg = df_bitrix_agg.reset_index() # Transformar índice (id_familia) em coluna
    else:
        st.info("Não foi possível agregar dados de emissão do Bitrix.")
        # Criar DataFrame vazio com as colunas esperadas para o merge
        colunas_esperadas_bitrix = [col_id_familia_bitrix] + novas_colunas_bitrix
        df_bitrix_agg = pd.DataFrame(columns=colunas_esperadas_bitrix)

    # --- Merge: Planilha + Dados Bitrix Agregados --- 
    df_merged = pd.merge(
        df_conclusao_raw, # Usar o DF da planilha ANTES da agregação por mesa
        df_bitrix_agg,
        left_on='id_familia', # ID da família da Planilha (já tratado)
        right_on=col_id_familia_bitrix, # ID da família do Bitrix (já tratado)
        how='left'
    )

    # Preencher NaNs nas colunas de contagem do Bitrix com 0 após o merge
    for col in novas_colunas_bitrix:
        df_merged[col] = df_merged[col].fillna(0).astype(int)

    # <<< DEBUG: Inspecionar df_merged para CABINES >>> REMOVIDO
    # print("\nDEBUG: Inspecionando df_merged ANTES da agregação final...")
    # df_merged_cabines_debug = df_merged[df_merged['mesa'] == 'CABINES']
    # print(f"  Shape de df_merged para CABINES: {df_merged_cabines_debug.shape}")
    # if not df_merged_cabines_debug.empty:
    #     print("  Primeiras linhas de df_merged para CABINES:")
    #     print(df_merged_cabines_debug.head())
    #     print("  Soma de higienizacao_exito para CABINES em df_merged:", df_merged_cabines_debug['higienizacao_exito'].sum())
    #     print("  Soma de higienizacao_incompleta para CABINES em df_merged:", df_merged_cabines_debug['higienizacao_incompleta'].sum())
    #     print("  Soma de Brasileiras Pendências para CABINES em df_merged:", df_merged_cabines_debug['Brasileiras Pendências'].sum())
    # <<< FIM DEBUG >>> REMOVIDO

    # --- Agregação Final por Mesa e Consultor (PARA TABELA PRINCIPAL) --- 
    # Define o que agregar e como
    agg_dict = {
        'higienizacao_exito': 'sum',
        'higienizacao_incompleta': 'sum',
        'higienizacao_tratadas': 'sum',
        # Adicionar agregação para as novas colunas do Bitrix
        'Brasileiras Pendências': 'sum',
        'Brasileiras Pesquisas': 'sum',
        'Brasileiras Solicitadas': 'sum',
        'Brasileiras Emitidas': 'sum',
        'Pasta C/Emissão Concluída': 'sum',
        'Brasileiras Dispensada': 'sum'
    }
    df_agregado_final = df_merged.groupby(['mesa', 'responsavel']).agg(agg_dict).reset_index()

    # --- Merge Final com a Base (PARA TABELA PRINCIPAL) --- 
    data_base = {
        'MESA': ['MESA 8', 'MESA 7', 'MESA 6', 'MESA 5', 'MESA 4', 'MESA 3', 'MESA 2', 'MESA 1', 'MESA 0', 'CABINES'],
        'PASTAS TOTAIS': [105, 46, 46, 70, 70, 46, 66, 66, 49, None], # None para Cabines
        'CONSULTOR': ['NADYA', 'FELIPE', 'ANGELICA', 'BIANCA', 'DANYELE', 'LAYLA', 'LAYLA', 'JULIANE', 'JULIANE', 'STEFANY'] # << MODIFICADO para CABINES
    }
    df_base = pd.DataFrame(data_base)

    # Renomear colunas do agregado para corresponder ao df_base antes do merge final
    df_agregado_final = df_agregado_final.rename(columns={
        'mesa': 'MESA',
        'responsavel': 'CONSULTOR',
        'higienizacao_exito': 'HIGINIZAÇÃO COM ÊXITO',
        'higienizacao_incompleta': 'HIGINIZAÇÃO INCOMPLETA',
        'higienizacao_tratadas': 'HIGINIZAÇÃO TRATADAS'
    })

    df_final = pd.merge(df_base, df_agregado_final, on=['MESA', 'CONSULTOR'], how='left')

    # Preencher NaNs finais com 0 para todas as colunas de contagem
    colunas_contagem_todas = [
        'HIGINIZAÇÃO COM ÊXITO', 'HIGINIZAÇÃO INCOMPLETA', 'HIGINIZAÇÃO TRATADAS',
        'Brasileiras Pendências', 'Brasileiras Pesquisas', 'Brasileiras Solicitadas',
        'Brasileiras Emitidas', 'Pasta C/Emissão Concluída', 'Brasileiras Dispensada'
    ]
    for col in colunas_contagem_todas:
         if col in df_final.columns: # Verifica se a coluna existe antes de preencher
             df_final[col] = df_final[col].fillna(0).astype(int)
         else:
             df_final[col] = 0 # Adiciona coluna com 0 se ela não existiu no merge

    # Ajustar a ordem das colunas para exibição
    ordem_colunas = [
        'MESA', 'PASTAS TOTAIS', 'CONSULTOR',
        'HIGINIZAÇÃO COM ÊXITO', 'HIGINIZAÇÃO INCOMPLETA', 'HIGINIZAÇÃO TRATADAS',
        # Novas colunas
        'Brasileiras Pendências', 'Brasileiras Pesquisas', 'Brasileiras Solicitadas',
        'Brasileiras Emitidas', 'Pasta C/Emissão Concluída', 'Brasileiras Dispensada'
    ]
    df_final = df_final[ordem_colunas]

    # --- FILTRAR df_final para REMOVER CABINES ANTES DE EXIBIR TABELA PRINCIPAL ---
    df_final_sem_cabines = df_final[df_final['MESA'] != 'CABINES'].copy()

    # --- Exibir a Tabela Principal (SEM CABINES) --- 
    # st.dataframe(df_final_sem_cabines, hide_index=True, use_container_width=True) # Linha antiga
    if not df_final_sem_cabines.empty:
        # Calcular linha de total para a tabela principal
        df_total_principal = df_final_sem_cabines.select_dtypes(include=np.number).sum().to_frame().T
        df_total_principal['MESA'] = 'TOTAL' # Adicionar identificador
        # Concatenar com o DataFrame original, garantindo que as colunas não numéricas sejam preenchidas
        df_display_principal = pd.concat([df_final_sem_cabines, df_total_principal], ignore_index=True)
        # Preencher NaNs nas colunas de objeto da linha de total (ex: CONSULTOR)
        for col in df_display_principal.select_dtypes(include='object').columns:
            if col != 'MESA': # Não sobrescrever o TOTAL
                 df_display_principal[col] = df_display_principal[col].fillna('')
        st.dataframe(df_display_principal, hide_index=True, use_container_width=True)
    else:
        st.info("Não há dados para exibir na tabela principal com os filtros atuais.")

    # Botão de download da tabela principal
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')
    # csv_principal = convert_df_to_csv(df_final) # Linha antiga
    csv_principal = convert_df_to_csv(df_final_sem_cabines) # Usa DF sem Cabines
    st.download_button(
        label="Download Tabela Principal como CSV",
        data=csv_principal,
        file_name='desempenho_higienizacao_mesas.csv', 
        mime='text/csv',
        key='download_principal' # Chave única
    )

    st.markdown("--- ") # Separador antes da nova seção

    # --- Seção Detalhada: EMISSÕES INCOMPLETAS ALPHA PROTOCOLADAS (CABINES) ---
    # Mudar para contagem TOTAL de Cabines
    
    # Calcular contagem TOTAL de Cabines
    contagem_total_cabines = 0
    if not df_conclusao_raw.empty and 'mesa' in df_conclusao_raw.columns:
        # print("\nDEBUG: Para contagem da faixa laranja CABINES...") # DEBUG Removido
        # print(f"  df_conclusao_raw shape: {df_conclusao_raw.shape}") # DEBUG Removido
        # print(f"  Unique 'mesa' values in df_conclusao_raw: {df_conclusao_raw['mesa'].unique()}") # DEBUG Removido
        
        df_temp_cabines = df_conclusao_raw[df_conclusao_raw['mesa'] == 'CABINES'] # DEBUG Removido o print disto
        # print(f"  Linhas onde mesa == 'CABINES': {df_temp_cabines.shape[0]}") # DEBUG Removido
        # if df_temp_cabines.shape[0] > 0:
            # print(df_temp_cabines.head()) # DEBUG Removido

        contagem_total_cabines = df_temp_cabines.shape[0]

    # Exibir Faixa Laranja para Cabines com a contagem TOTAL
    st.markdown(f"""
    <div style="{faixa_style}">
        <h4 style="{titulo_style}">EMISSÕES INCOMPLETAS ALPHA PROTOCOLADAS (CABINES)</h4>
        <p style="{contagem_style}">{contagem_total_cabines} PASTAS</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Tabela Detalhada para CABINES (TODOS os status) --- 
    # Filtrar a TABELA PRINCIPAL (df_final) para MESA == 'CABINES'
    df_cabines_final = df_final[df_final['MESA'] == 'CABINES'].copy()

    if not df_cabines_final.empty:
        st.markdown("--- ") # Separador antes da tabela de detalhes
        
        # TRATAMENTO ADICIONAL para NaN em 'PASTAS TOTAIS' antes de exibir
        if 'PASTAS TOTAIS' in df_cabines_final.columns:
            df_cabines_final.loc[:, 'PASTAS TOTAIS'] = df_cabines_final['PASTAS TOTAIS'].fillna(0).astype(int)

        # Calcular linha de total para a tabela de Cabines
        df_total_cabines = df_cabines_final.select_dtypes(include=np.number).sum().to_frame().T
        df_total_cabines['MESA'] = 'TOTAL' # Adicionar identificador
        # Concatenar
        df_display_cabines = pd.concat([df_cabines_final, df_total_cabines], ignore_index=True)
        # Preencher NaNs nas colunas de objeto da linha de total
        for col in df_display_cabines.select_dtypes(include='object').columns:
            if col != 'MESA': 
                 df_display_cabines[col] = df_display_cabines[col].fillna('')
        
        # Exibir o DataFrame filtrado (já tem as colunas corretas da tabela principal)
        # st.dataframe(df_cabines_final, hide_index=True, use_container_width=True) # Linha antiga
        st.dataframe(df_display_cabines, hide_index=True, use_container_width=True)
        
        # Botão de download para detalhes de cabines
        # Usar df_cabines_final para download (sem a linha de total na exportação)
        csv_cabines_detalhes = convert_df_to_csv(df_cabines_final)
        st.download_button(
            label="Download Detalhes Cabines (Todos Status) como CSV",
            data=csv_cabines_detalhes,
            file_name='detalhes_cabines_todos_status.csv', 
            mime='text/csv',
            key='download_cabines_detalhes' # Chave única diferente
        )
    # else:
        # Opcional: Mostrar mensagem se não houver dados de cabines
        # st.info("Não há dados de CABINES na planilha para exibir detalhes.")

    # Tabela de detalhes específica para incompletas removida anteriormente
    # Se contagem_cabines_incompletas > 0:
    #    # ... lógica para criar e mostrar df_tabela_cabines_detalhes ...
    #    pass 
    # else:
    #    st.info("Não há emissões incompletas protocoladas (Cabines) para exibir detalhes.") 