import streamlit as st
import pandas as pd
from data.load_conclusao_higienizacao import load_conclusao_data
from views.cartorio_new.data_loader import carregar_dados_cartorio # Importar dados do cartório
from datetime import datetime, timedelta, date
import re # Para extrair ID da opção do selectbox
import numpy as np # Para operações numéricas

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
        df_conclusao_raw = load_conclusao_data(start_date=start_date_to_load, end_date=end_date_to_load)
        if df_conclusao_raw is None:
             df_conclusao_raw = pd.DataFrame() # Continuar com DF vazio

        # Garantir colunas mesmo se vazio
        colunas_planilha_esperadas = ['responsavel', 'mesa', 'id_familia', 'nome_familia', 'higienizacao_exito', 'higienizacao_incompleta', 'higienizacao_tratadas']
        for col in colunas_planilha_esperadas:
            if col not in df_conclusao_raw.columns:
                df_conclusao_raw[col] = None 

        colunas_planilha = ['responsavel', 'mesa', 'id_familia', 'nome_familia', 'higienizacao_exito', 'higienizacao_incompleta', 'higienizacao_tratadas']
        df_conclusao_raw = df_conclusao_raw[colunas_planilha].copy()
        df_conclusao_raw = df_conclusao_raw.dropna(subset=['id_familia']) 

    # 2. Dados do Bitrix (Funil Emissões 1098)
    with st.spinner("Carregando dados de emissões do Bitrix..."):
        df_cartorio = carregar_dados_cartorio()
        if df_cartorio is None:
            df_cartorio = pd.DataFrame() 
            st.warning("Não foi possível carregar os dados de emissões do Bitrix.")
    
    # --- Filtros Adicionais: Data de Venda e Responsável ---
    st.markdown("**Filtros Adicionais:**")
    
    # --- Filtro de Data de Venda ---
    col_venda1, col_venda2 = st.columns(2)
    
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
    
    with col_venda1:
        ano_selecionado = st.selectbox(
            "Filtrar por Ano de Venda",
            options=opcoes_anos,
            index=0
        )
    
    with col_venda2:
        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
        mostrar_info_filtro_ano = st.checkbox("Mostrar detalhes do filtro de ano", value=False)
        
        if mostrar_info_filtro_ano and ano_selecionado != "Todos os anos":
            st.info(f"Filtrando vendas do ano: {ano_selecionado}")
            # Adicionar informações de quantos registros existem neste ano
            if not df_cartorio.empty and 'DATA_VENDA_FAMILIA' in df_cartorio.columns:
                count_ano = df_cartorio[df_cartorio['DATA_VENDA_FAMILIA'].dt.year == int(ano_selecionado)].shape[0]
                st.caption(f"({count_ano} registros encontrados neste ano)")

    # --- Filtro de Responsável ---
    # Obter lista de responsáveis únicos
    responsaveis_unicos = []
    
    # Da tabela de conclusão
    if not df_conclusao_raw.empty and 'responsavel' in df_conclusao_raw.columns:
        responsaveis_planilha = df_conclusao_raw['responsavel'].dropna().unique().tolist()
        responsaveis_unicos.extend(responsaveis_planilha)
    
    # Do Bitrix
    if not df_cartorio.empty and 'ASSIGNED_BY_NAME' in df_cartorio.columns:
        responsaveis_bitrix = df_cartorio['ASSIGNED_BY_NAME'].dropna().unique().tolist()
        responsaveis_unicos.extend(responsaveis_bitrix)
    
    # Remover duplicatas e ordenar
    responsaveis_unicos = sorted(list(set([r for r in responsaveis_unicos if r and str(r).strip() != ''])))
    
    filtro_responsaveis = st.multiselect(
        "Filtrar por Responsável",
        options=responsaveis_unicos,
        default=[],
        placeholder="Selecione um ou mais responsáveis"
    )

    # --- Widgets de Filtro por Família --- 
    col_filtros1, col_filtros2 = st.columns(2)
    
    with col_filtros1:
        filtro_id_familia = st.text_input("ID da Família (exato)", key="filtro_id_fam")
        filtro_id_familia = filtro_id_familia.strip() 

    with col_filtros2:
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
        
        filtro_nome_familia_selecionado = st.selectbox(
            "Nome da Família (\\ Responsável \\ ID)", 
            options=opcoes_familia, 
            key="filtro_nome_fam"
        )

    # --- Aplicar Filtros por Família (afeta df_conclusao_raw e df_cartorio) --- 
    id_familia_filtrar = None
    
    if filtro_id_familia:
        id_familia_filtrar = filtro_id_familia
        st.info(f"Filtrando pelo ID da Família: {id_familia_filtrar}")
    elif filtro_nome_familia_selecionado != "Todas":
        match = re.search(r'\\\\ ([^\\\\]+)$', filtro_nome_familia_selecionado)
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
        if ano_selecionado != "Todos os anos":
            # Converter para inteiro para comparar com o ano extraído das datas
            ano_filtro = int(ano_selecionado)
            
            # Filtrar df_cartorio apenas pelo ano selecionado
            df_cartorio = df_cartorio[df_cartorio['DATA_VENDA_FAMILIA'].dt.year == ano_filtro].copy()
            
            if df_cartorio.empty:
                st.warning(f"Nenhum dado encontrado para o ano selecionado: {ano_selecionado}")
            else:
                st.success(f"Filtro aplicado: Mostrando dados do ano {ano_selecionado} ({len(df_cartorio)} registros)")
        else:
            # Se "Todos os anos" for selecionado, não aplicar filtro de ano
            st.info("Mostrando dados de todos os anos disponíveis")
            
    # --- Aplicar Filtro de Responsável ---
    if filtro_responsaveis:
        # Filtrar df_conclusao_raw por responsável
        if not df_conclusao_raw.empty and 'responsavel' in df_conclusao_raw.columns:
            df_conclusao_raw = df_conclusao_raw[df_conclusao_raw['responsavel'].isin(filtro_responsaveis)].copy()
        
        # Filtrar df_cartorio por responsável
        if not df_cartorio.empty and 'ASSIGNED_BY_NAME' in df_cartorio.columns:
            df_cartorio = df_cartorio[df_cartorio['ASSIGNED_BY_NAME'].isin(filtro_responsaveis)].copy()
        
        if df_conclusao_raw.empty and df_cartorio.empty:
            st.warning(f"Nenhum dado encontrado para o(s) responsável(eis) selecionado(s): {', '.join(filtro_responsaveis)}")

    # --- MOVER PROCESSAMENTO DE DADOS PARA ANTES DAS FAIXAS ---

    # --- Mapeamento de Estágios Bitrix ---
    mapeamento_stages = {
        'DT1098_92:NEW': 'Brasileiras Pendências', 'DT1098_92:UC_P6PYHW': 'Brasileiras Pesquisas',
        'DT1098_92:PREPARATION': 'Brasileiras Pendências', 'DT1098_92:UC_XBTHZ7': 'Brasileiras Pendências',
        'DT1098_92:CLIENT': 'Brasileiras Pendências', 'DT1098_92:UC_ZWO7BI': 'Brasileiras Pendências',
        'DT1098_92:UC_83ZGKS': 'Brasileiras Pendências', 'DT1098_92:UC_6TECYL': 'Brasileiras Pendências',
        'DT1098_92:UC_MUJP1P': 'Brasileiras Solicitadas', 'DT1098_92:UC_EYBGVD': 'Brasileiras Pendências',
        'DT1098_92:UC_KC335Q': 'Brasileiras Pendências', 'DT1098_92:UC_5LWUTX': 'Brasileiras Emitida',
        'DT1098_92:FAIL': 'Brasileiras Dispensada', 'DT1098_92:UC_Z24IF7': 'Brasileiras Dispensada',
        'DT1098_92:UC_U10R0R': 'Brasileiras Dispensada', 'DT1098_92:SUCCESS': 'Brasileiras Emitida',
        'DT1098_94:NEW': 'Brasileiras Pendências', 'DT1098_94:UC_4YE2PI': 'Brasileiras Pesquisas',
        'DT1098_94:PREPARATION': 'Brasileiras Pendências', 'DT1098_94:CLIENT': 'Brasileiras Pendências',
        'DT1098_94:UC_IQ4WFA': 'Brasileiras Pendências', 'DT1098_94:UC_UZHXWF': 'Brasileiras Pendências',
        'DT1098_94:UC_DH38EI': 'Brasileiras Pendências', 'DT1098_94:UC_X9UE60': 'Brasileiras Pendências',
        'DT1098_94:UC_IXCAA5': 'Brasileiras Solicitadas', 'DT1098_94:UC_VS8YKI': 'Brasileiras Pendências',
        'DT1098_94:UC_M6A09E': 'Brasileiras Pendências', 'DT1098_94:UC_K4JS04': 'Brasileiras Emitida',
        'DT1098_94:FAIL': 'Brasileiras Dispensada', 'DT1098_94:UC_MGTPX0': 'Brasileiras Dispensada',
        'DT1098_94:UC_L3JFKO': 'Brasileiras Dispensada', 'DT1098_94:SUCCESS': 'Brasileiras Emitida'
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
        
        df_bitrix_agg['TOTAL_ATIVAS'] = df_bitrix_agg['Brasileiras Pendências'] + \
                                        df_bitrix_agg['Brasileiras Pesquisas'] + \
                                        df_bitrix_agg['Brasileiras Solicitadas'] + \
                                        df_bitrix_agg['Brasileiras Emitida']
        
        df_bitrix_agg['Pasta C/Emissão Concluída'] = np.where(
            (df_bitrix_agg['TOTAL_ATIVAS'] > 0) & (df_bitrix_agg['TOTAL_ATIVAS'] == df_bitrix_agg['Brasileiras Emitida']), 1, 0
        )
        df_bitrix_agg = df_bitrix_agg.drop(columns=['TOTAL_ATIVAS'])
        df_bitrix_agg = df_bitrix_agg.reset_index()
        
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
        'higienizacao_exito': 'sum', 'higienizacao_incompleta': 'sum', 'higienizacao_tratadas': 'sum',
        'Brasileiras Pendências': 'sum', 'Brasileiras Pesquisas': 'sum', 'Brasileiras Solicitadas': 'sum',
        'Brasileiras Emitida': 'sum', 'Pasta C/Emissão Concluída': 'sum', 'Brasileiras Dispensada': 'sum'
    }
    df_agregado_final = df_merged.groupby(['mesa', 'responsavel']).agg(agg_dict).reset_index()

    # --- Merge Final com a Base --- 
    data_base = {
        'MESA': ['MESA 8', 'MESA 7', 'MESA 6', 'MESA 5', 'MESA 4', 'MESA 3', 'MESA 2', 'MESA 1', 'MESA 0', 'CABINES', 'CARRÃO'],
        'PASTAS TOTAIS': [105, 46, 46, 70, 70, 46, 66, 66, 49, 113, 123],
        'CONSULTOR': ['NADYA', 'FELIPE', 'VITOR', 'BIANCA', 'DANYELE', 'LAYLA', 'LAYLA', 'JULIANE', 'JULIANE', 'STEFANY', 'Fernanda']
    }
    df_base = pd.DataFrame(data_base)

    df_agregado_final = df_agregado_final.rename(columns={
        'mesa': 'MESA', 'responsavel': 'CONSULTOR',
        'higienizacao_exito': 'HIGINIZAÇÃO COM ÊXITO',
        'higienizacao_incompleta': 'HIGINIZAÇÃO INCOMPLETA',
        'higienizacao_tratadas': 'HIGINIZAÇÃO TRATADAS'
    })
    df_final = pd.merge(df_base, df_agregado_final, on=['MESA', 'CONSULTOR'], how='left')

    colunas_contagem_numericas = [
        'PASTAS TOTAIS', # Adicionado para garantir que seja tratado como numérico e preenchido
        'HIGINIZAÇÃO COM ÊXITO', 'HIGINIZAÇÃO INCOMPLETA', 'HIGINIZAÇÃO TRATADAS',
        'Brasileiras Pendências', 'Brasileiras Pesquisas', 'Brasileiras Solicitadas',
        'Brasileiras Emitida', 'Pasta C/Emissão Concluída', 'Brasileiras Dispensada'
    ]
    for col in colunas_contagem_numericas:
         if col not in df_final.columns: # Adiciona a coluna com 0 se não existir do merge/base
             df_final[col] = 0
         df_final[col] = df_final[col].fillna(0)
         # Tentar converter para int, mas se falhar (ex: se já for float com decimais), manter como está ou float
         try:
             df_final[col] = df_final[col].astype(int)
         except ValueError:
             df_final[col] = df_final[col].astype(float) # ou apenas deixar como está após fillna(0)

    # --- Adicionar Coluna de Conversão ---
    df_final['CONVERSÃO (%)'] = np.where(
        df_final['PASTAS TOTAIS'] > 0,
        (df_final['HIGINIZAÇÃO COM ÊXITO'] / df_final['PASTAS TOTAIS']) * 100,
        0
    )
    df_final['CONVERSÃO (%)'] = df_final['CONVERSÃO (%)'].fillna(0).round(2)

    # --- Adicionar Coluna de Taxa Emissão Concluída ---
    df_final['Taxa Emissão Concluída (%)'] = np.where(
        df_final['PASTAS TOTAIS'] > 0,
        (df_final['Pasta C/Emissão Concluída'] / df_final['PASTAS TOTAIS']) * 100,
        0
    )
    df_final['Taxa Emissão Concluída (%)'] = df_final['Taxa Emissão Concluída (%)'].fillna(0).round(2)

    ordem_colunas = [
        'MESA', 'PASTAS TOTAIS', 'CONSULTOR',
        'HIGINIZAÇÃO COM ÊXITO', 'HIGINIZAÇÃO INCOMPLETA', 'HIGINIZAÇÃO TRATADAS', 'CONVERSÃO (%)',
        'Brasileiras Pendências', 'Brasileiras Pesquisas', 'Brasileiras Solicitadas',
        'Brasileiras Emitida', 'Pasta C/Emissão Concluída', 'Taxa Emissão Concluída (%)', 'Brasileiras Dispensada'
    ]
    # Garantir que todas as colunas em ordem_colunas existam em df_final, adicionando-as com 0 ou formato apropriado se necessário
    for col_ordem in ordem_colunas:
        if col_ordem not in df_final.columns:
            df_final[col_ordem] = 0
            if col_ordem == 'CONVERSÃO (%)' or col_ordem == 'Taxa Emissão Concluída (%)':
                 df_final[col_ordem] = df_final[col_ordem].astype(float).round(2)
            else: 
                 df_final[col_ordem] = df_final[col_ordem].astype(int)

    df_final = df_final[ordem_colunas]
    
    # --- FIM DO PROCESSAMENTO DE DADOS MOVIDO ---


    # --- Calcular Contagens para as Faixas (AGORA USANDO df_final) ---
    contagem_total_mesas_1_8_faixa = 0
    if not df_final.empty and 'HIGINIZAÇÃO COM ÊXITO' in df_final.columns:
        mesas_1_8_list_faixa = [f'MESA {i}' for i in range(1, 9)]
        df_mesas_1_8_faixa_filtrado = df_final[df_final['MESA'].isin(mesas_1_8_list_faixa)]
        contagem_total_mesas_1_8_faixa = df_mesas_1_8_faixa_filtrado['HIGINIZAÇÃO COM ÊXITO'].sum()
    
    faixa_style = "background-color: #FFA726; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
    titulo_style = "color: white; margin: 0; font-size: 1.1em; font-weight: bold;"
    contagem_style = "color: white; font-size: 2em; font-weight: bolder; margin: 8px 0 0 0;"

    st.markdown(f"""
    <div style="{faixa_style}">
        <h4 style="{titulo_style}">TOTAL DE HIGIENIZAÇÕES COM ÊXITO (MESAS 1-8)</h4>
        <p style="{contagem_style}">{contagem_total_mesas_1_8_faixa} PASTAS</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("--- ")

    # --- Exibir a Tabela Principal (SEM CABINES) --- 
    df_final_sem_cabines = df_final[df_final['MESA'] != 'CABINES'].copy()
    if not df_final_sem_cabines.empty:
        df_total_principal = df_final_sem_cabines.select_dtypes(include=np.number).sum().to_frame().T
        df_total_principal['MESA'] = 'TOTAL' 
        df_display_principal = pd.concat([df_final_sem_cabines, df_total_principal], ignore_index=True)
        
        # Corrigir CONVERSÃO (%) na linha TOTAL para a tabela principal
        if 'TOTAL' in df_display_principal['MESA'].values:
            total_row_idx_principal = df_display_principal[df_display_principal['MESA'] == 'TOTAL'].index
            if not total_row_idx_principal.empty:
                idx_p = total_row_idx_principal[0]
                sum_hig_exito_p = df_display_principal.loc[idx_p, 'HIGINIZAÇÃO COM ÊXITO']
                sum_pastas_totais_p = df_display_principal.loc[idx_p, 'PASTAS TOTAIS']
                df_display_principal.loc[idx_p, 'CONVERSÃO (%)'] = \
                    (sum_hig_exito_p / sum_pastas_totais_p * 100).round(2) if sum_pastas_totais_p > 0 else 0
                
                # Calcular Taxa Emissão Concluída (%) na linha TOTAL para a tabela principal
                sum_emissao_concluida_p = df_display_principal.loc[idx_p, 'Pasta C/Emissão Concluída']
                df_display_principal.loc[idx_p, 'Taxa Emissão Concluída (%)'] = \
                    (sum_emissao_concluida_p / sum_pastas_totais_p * 100).round(2) if sum_pastas_totais_p > 0 else 0

        for col_obj in df_display_principal.select_dtypes(include='object').columns:
            if col_obj != 'MESA': 
                 df_display_principal[col_obj] = df_display_principal[col_obj].fillna('')
        
        # Formatar CONVERSÃO (%) e Taxa Emissão Concluída (%) como string com % no final ANTES de exibir
        if 'CONVERSÃO (%)' in df_display_principal.columns:
            df_display_principal['CONVERSÃO (%)'] = df_display_principal['CONVERSÃO (%)'].apply(lambda x: f"{x:.2f}%")
        if 'Taxa Emissão Concluída (%)' in df_display_principal.columns:
            df_display_principal['Taxa Emissão Concluída (%)'] = df_display_principal['Taxa Emissão Concluída (%)'].apply(lambda x: f"{x:.2f}%")

        st.dataframe(df_display_principal, hide_index=True, use_container_width=True)
    else:
        st.info("Não há dados para exibir na tabela principal com os filtros atuais.")

    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')
    csv_principal = convert_df_to_csv(df_final_sem_cabines) 
    st.download_button(
        label="Download Tabela Principal como CSV", data=csv_principal,
        file_name='desempenho_higienizacao_mesas.csv', mime='text/csv', key='download_principal'
    )
    st.markdown("--- ") 

    # --- Calcular Contagem para Faixa de Cabines (AGORA USANDO df_final) ---
    contagem_cabines_exito_faixa = 0
    if not df_final.empty and 'HIGINIZAÇÃO COM ÊXITO' in df_final.columns:
        df_cabines_faixa_filtrado = df_final[df_final['MESA'] == 'CABINES']
        contagem_cabines_exito_faixa = df_cabines_faixa_filtrado['HIGINIZAÇÃO COM ÊXITO'].sum()

    st.markdown(f"""
    <div style="{faixa_style}">
        <h4 style="{titulo_style}">TOTAL DE HIGIENIZAÇÕES COM ÊXITO (CABINES)</h4>
        <p style="{contagem_style}">{contagem_cabines_exito_faixa} PASTAS</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Tabela Detalhada para CABINES (TODOS os status) --- 
    df_cabines_final = df_final[df_final['MESA'] == 'CABINES'].copy()
    if not df_cabines_final.empty:
        st.markdown("--- ") 
        if 'PASTAS TOTAIS' in df_cabines_final.columns:
            # Assegurar que PASTAS TOTAIS seja numérico antes de usar na linha de total para cabines
            df_cabines_final.loc[:, 'PASTAS TOTAIS'] = pd.to_numeric(df_cabines_final['PASTAS TOTAIS'], errors='coerce').fillna(0).astype(int)

        df_total_cabines = df_cabines_final.select_dtypes(include=np.number).sum().to_frame().T
        df_total_cabines['MESA'] = 'TOTAL' 
        df_display_cabines = pd.concat([df_cabines_final, df_total_cabines], ignore_index=True)

        # Corrigir CONVERSÃO (%) na linha TOTAL para a tabela de cabines
        if 'TOTAL' in df_display_cabines['MESA'].values:
            total_row_idx_cabines = df_display_cabines[df_display_cabines['MESA'] == 'TOTAL'].index
            if not total_row_idx_cabines.empty:
                idx_c = total_row_idx_cabines[0]
                sum_hig_exito_c = df_display_cabines.loc[idx_c, 'HIGINIZAÇÃO COM ÊXITO']
                sum_pastas_totais_c = df_display_cabines.loc[idx_c, 'PASTAS TOTAIS']
                df_display_cabines.loc[idx_c, 'CONVERSÃO (%)'] = \
                    (sum_hig_exito_c / sum_pastas_totais_c * 100).round(2) if sum_pastas_totais_c > 0 else 0

                # Calcular Taxa Emissão Concluída (%) na linha TOTAL para a tabela de cabines
                sum_emissao_concluida_c = df_display_cabines.loc[idx_c, 'Pasta C/Emissão Concluída']
                df_display_cabines.loc[idx_c, 'Taxa Emissão Concluída (%)'] = \
                    (sum_emissao_concluida_c / sum_pastas_totais_c * 100).round(2) if sum_pastas_totais_c > 0 else 0

        for col_obj_cab in df_display_cabines.select_dtypes(include='object').columns:
            if col_obj_cab != 'MESA': 
                 df_display_cabines[col_obj_cab] = df_display_cabines[col_obj_cab].fillna('')

        # Formatar CONVERSÃO (%) e Taxa Emissão Concluída (%) como string com % no final ANTES de exibir
        if 'CONVERSÃO (%)' in df_display_cabines.columns:
            df_display_cabines['CONVERSÃO (%)'] = df_display_cabines['CONVERSÃO (%)'].apply(lambda x: f"{x:.2f}%")
        if 'Taxa Emissão Concluída (%)' in df_display_cabines.columns:
            df_display_cabines['Taxa Emissão Concluída (%)'] = df_display_cabines['Taxa Emissão Concluída (%)'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(df_display_cabines, hide_index=True, use_container_width=True)
        
        csv_cabines_detalhes = convert_df_to_csv(df_cabines_final)
        st.download_button(
            label="Download Detalhes Cabines (Todos Status) como CSV", data=csv_cabines_detalhes,
            file_name='detalhes_cabines_todos_status.csv', mime='text/csv', key='download_cabines_detalhes'
        )
    else:
        st.info("Não há dados de CABINES na planilha para exibir detalhes.") 

    st.markdown("--- ") # Separador antes da nova seção CARRÃO

    # --- Seção Detalhada: CARRÃO ---
    # Calcular Contagem para Faixa de CARRÃO (AGORA USANDO df_final)
    contagem_carrao_exito_faixa = 0
    if not df_final.empty and 'HIGINIZAÇÃO COM ÊXITO' in df_final.columns:
        df_carrao_faixa_filtrado = df_final[df_final['MESA'] == 'CARRÃO']
        if not df_carrao_faixa_filtrado.empty: # Checar se o filtro resultou em algo
            contagem_carrao_exito_faixa = df_carrao_faixa_filtrado['HIGINIZAÇÃO COM ÊXITO'].sum()

    st.markdown(f"""
    <div style="{faixa_style}">
        <h4 style="{titulo_style}">TOTAL DE HIGIENIZAÇÕES COM ÊXITO (CARRÃO)</h4>
        <p style="{contagem_style}">{contagem_carrao_exito_faixa} PASTAS</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Tabela Detalhada para CARRÃO (TODOS os status) --- 
    df_carrao_final = df_final[df_final['MESA'] == 'CARRÃO'].copy()

    if not df_carrao_final.empty:
        st.markdown("--- ") 
        if 'PASTAS TOTAIS' in df_carrao_final.columns:
            df_carrao_final.loc[:, 'PASTAS TOTAIS'] = pd.to_numeric(df_carrao_final['PASTAS TOTAIS'], errors='coerce').fillna(0).astype(int)

        df_total_carrao = df_carrao_final.select_dtypes(include=np.number).sum().to_frame().T
        df_total_carrao['MESA'] = 'TOTAL' 
        df_display_carrao = pd.concat([df_carrao_final, df_total_carrao], ignore_index=True)

        # Corrigir CONVERSÃO (%) e Taxa Emissão Concluída (%) na linha TOTAL para a tabela de CARRÃO
        if 'TOTAL' in df_display_carrao['MESA'].values:
            total_row_idx_carrao = df_display_carrao[df_display_carrao['MESA'] == 'TOTAL'].index
            if not total_row_idx_carrao.empty:
                idx_cr = total_row_idx_carrao[0]
                sum_hig_exito_cr = df_display_carrao.loc[idx_cr, 'HIGINIZAÇÃO COM ÊXITO']
                sum_pastas_totais_cr = df_display_carrao.loc[idx_cr, 'PASTAS TOTAIS']
                df_display_carrao.loc[idx_cr, 'CONVERSÃO (%)'] = \
                    (sum_hig_exito_cr / sum_pastas_totais_cr * 100).round(2) if sum_pastas_totais_cr > 0 else 0

                sum_emissao_concluida_cr = df_display_carrao.loc[idx_cr, 'Pasta C/Emissão Concluída']
                df_display_carrao.loc[idx_cr, 'Taxa Emissão Concluída (%)'] = \
                    (sum_emissao_concluida_cr / sum_pastas_totais_cr * 100).round(2) if sum_pastas_totais_cr > 0 else 0

        for col_obj_cr in df_display_carrao.select_dtypes(include='object').columns:
            if col_obj_cr != 'MESA': 
                 df_display_carrao[col_obj_cr] = df_display_carrao[col_obj_cr].fillna('')

        # Formatar CONVERSÃO (%) e Taxa Emissão Concluída (%) como string com % no final ANTES de exibir
        if 'CONVERSÃO (%)' in df_display_carrao.columns:
            df_display_carrao['CONVERSÃO (%)'] = df_display_carrao['CONVERSÃO (%)'].apply(lambda x: f"{x:.2f}%")
        if 'Taxa Emissão Concluída (%)' in df_display_carrao.columns:
            df_display_carrao['Taxa Emissão Concluída (%)'] = df_display_carrao['Taxa Emissão Concluída (%)'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(df_display_carrao, hide_index=True, use_container_width=True)
        
        csv_carrao_detalhes = convert_df_to_csv(df_carrao_final) # Reutiliza a função convert_df_to_csv
        st.download_button(
            label="Download Detalhes CARRÃO (Todos Status) como CSV", data=csv_carrao_detalhes,
            file_name='detalhes_carrao_todos_status.csv', mime='text/csv', key='download_carrao_detalhes'
        )
    else:
        st.info("Não há dados de CARRÃO na planilha para exibir detalhes.") 

    # Tabela de detalhes específica para incompletas removida anteriormente 