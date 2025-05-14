import streamlit as st
import pandas as pd
from datetime import datetime, date # Adicionar date

# Reutilizar as funções de visao_geral para consistência
from .visao_geral import simplificar_nome_estagio, categorizar_estagio

# --- Constantes Chaves Session State ---
KEY_BUSCA_FAMILIA = "busca_familia_acompanhamento"
KEY_DATA_INICIO = "data_venda_inicio_acompanhamento"
KEY_DATA_FIM = "data_venda_fim_acompanhamento"
KEY_PERCENTUAL = "filtro_percentual_acompanhamento"
KEY_RESPONSAVEL = "filtro_responsavel_acompanhamento"  # Nova constante para filtro de responsável

def exibir_acompanhamento(df_cartorio):
    """
    Exibe a aba de Acompanhamento de Emissões por Família.
    Mostra métricas macro DIN MICAS (refletem filtros aplicados) e uma tabela 
    com Totais de Requerentes (contagem única), Certidões e Concluídas por Família.
    Inclui filtros com opção de limpeza.
    Aplica estilos via SCSS.
    
    Nota: Agora utiliza a coluna DATA_VENDA_FAMILIA que é obtida a partir do 
    campo UF_CRM_1746054586042 da categoria 46 do crm_deal.
    """
    # --- Carregar CSS Compilado ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")
    # --- Fim Carregar CSS ---

    st.subheader("Acompanhamento por Família")

    if df_cartorio is None or df_cartorio.empty:
        st.warning("Dados de cartório não disponíveis para acompanhamento.")
        return

    # Verificar se as colunas necessárias existem
    coluna_nome_familia = 'UF_CRM_34_NOME_FAMILIA'  # ATUALIZADO para o novo campo SPA
    coluna_id_requerente = 'UF_CRM_34_ID_REQUERENTE' # ATUALIZADO para o novo campo SPA
    coluna_data_venda_familia = 'DATA_VENDA_FAMILIA' # Vem da categoria 46 - UF_CRM_1746054586042
    coluna_responsavel = 'ASSIGNED_BY_NAME' # Coluna do responsável (ASSUMIDO)
    colunas_requeridas = ['ID', 'STAGE_ID', coluna_nome_familia, coluna_id_requerente, coluna_data_venda_familia, coluna_responsavel]
    colunas_faltantes = [col for col in colunas_requeridas if col not in df_cartorio.columns]

    if colunas_faltantes:
        # Ajustar a mensagem de erro para a nova coluna de data
        cols_necessarias_origem = [c for c in colunas_faltantes if c not in [coluna_data_venda_familia, coluna_responsavel]]
        msg_erro = ""
        if cols_necessarias_origem:
             msg_erro += f"Erro: As seguintes colunas são necessárias e não foram encontradas nos dados originais: {', '.join(cols_necessarias_origem)}. Verifique o data_loader. "
        if coluna_data_venda_familia in colunas_faltantes:
             msg_erro += f"Erro: A coluna '{coluna_data_venda_familia}' (obtida da categoria 46 - UF_CRM_1746054586042) não foi encontrada. Verifique o merge no data_loader. "
        if coluna_responsavel in colunas_faltantes: # Adicionar verificação do responsável
             msg_erro += f"Erro: A coluna '{coluna_responsavel}' (necessária para o responsável) não foi encontrada. Verifique o data_loader."
        
        # Adicionar espaço entre as mensagens se ambas existirem
        msg_erro = msg_erro.strip() # Remover espaços extras no início/fim
        
        st.error(msg_erro)
        # st.dataframe(df_cartorio.head()) # Descomentar se precisar debugar
        return

    # --- Pré-processamento --- 
    df = df_cartorio.copy()

    # 1. Garantir tipo correto para ID Requerente (já feito no loader, mas confirmando)
    df[coluna_id_requerente] = df[coluna_id_requerente].fillna('Req. Desconhecido').astype(str)
    # Tratar responsável Nulo (antes da agregação)
    df[coluna_responsavel] = df[coluna_responsavel].fillna('Desconhecido').astype(str)
    
    # Coluna Data Venda Família (do data_loader) - Garantir Datetime
    if coluna_data_venda_familia not in df.columns: # Redundante pela verificação acima, mas seguro
        st.warning(f"Coluna '{coluna_data_venda_familia}' não encontrada. O filtro por data de venda não estará disponível.")
        df[coluna_data_venda_familia] = pd.NaT 
    else:
        df[coluna_data_venda_familia] = pd.to_datetime(df[coluna_data_venda_familia], errors='coerce')

    # 2. Simplificar e Categorizar Estágios
    df['STAGE_ID'] = df['STAGE_ID'].astype(str)
    df['ESTAGIO_LEGIVEL'] = df['STAGE_ID'].apply(simplificar_nome_estagio)
    df['CATEGORIA_ESTAGIO'] = df['ESTAGIO_LEGIVEL'].apply(categorizar_estagio)
    df['CONCLUIDA'] = df['CATEGORIA_ESTAGIO'] == 'SUCESSO'

    # 3. Tratar Nulos na coluna Nome da Família (já feito no loader, mas confirmando)
    df[coluna_nome_familia] = df[coluna_nome_familia].fillna('Família Desconhecida').astype(str)
    df[coluna_nome_familia] = df[coluna_nome_familia].replace(r'^\s*$', 'Família Desconhecida', regex=True)

    # --- Agrupamento por Família (pré-filtro) ---
    # Mover agregação para ANTES dos filtros para ter a base completa
    df_agrupado = df.groupby(coluna_nome_familia).agg(
        total_certidoes=('ID', 'count'),
        total_requerentes=(coluna_id_requerente, pd.Series.nunique),
        concluidas=('CONCLUIDA', 'sum'),
        # Usar 'first' aqui é seguro porque data_venda_familia já foi agregada no loader
        data_venda_familia=(coluna_data_venda_familia, 'first'),
        # Pegar o primeiro responsável encontrado para a família
        responsavel=(coluna_responsavel, 'first')
    ).reset_index()

    # Calcular Percentual de Conclusão
    df_agrupado['percentual_conclusao'] = (
        (df_agrupado['concluidas'] / df_agrupado['total_certidoes'] * 100)
    ).fillna(0) # Preencher NaN com 0 se total_certidoes for 0

    # --- Valores Padrão para Filtros (Necessário para Reset) ---
    df_agrupado_com_data = df_agrupado.dropna(subset=['data_venda_familia'])
    min_date_default = df_agrupado_com_data['data_venda_familia'].min().date() if not df_agrupado_com_data.empty else date.today()
    max_date_default = df_agrupado_com_data['data_venda_familia'].max().date() if not df_agrupado_com_data.empty else date.today()

    # --- Inicialização do Session State --- 
    if KEY_BUSCA_FAMILIA not in st.session_state:
        st.session_state[KEY_BUSCA_FAMILIA] = ""
    if KEY_DATA_INICIO not in st.session_state:
        st.session_state[KEY_DATA_INICIO] = min_date_default
    if KEY_DATA_FIM not in st.session_state:
        st.session_state[KEY_DATA_FIM] = max_date_default
    if KEY_PERCENTUAL not in st.session_state:
        st.session_state[KEY_PERCENTUAL] = []
    if KEY_RESPONSAVEL not in st.session_state:  # Inicialização do state para responsável
        st.session_state[KEY_RESPONSAVEL] = []

    # --- Função para Limpar Filtros --- 
    def clear_filters():
        st.session_state[KEY_BUSCA_FAMILIA] = ""
        st.session_state[KEY_DATA_INICIO] = min_date_default
        st.session_state[KEY_DATA_FIM] = max_date_default
        st.session_state[KEY_PERCENTUAL] = []
        st.session_state[KEY_RESPONSAVEL] = []  # Limpar filtro de responsável

    # --- Filtros --- 
    with st.expander("Filtros", expanded=True): 
        # Layout: Linha 1 (Família, Data), Linha 2 (Percentual, Responsável), Linha 3 (Botão Limpar)
        col_l1_familia, col_l1_data = st.columns([0.5, 0.5])
        col_l2_perc, col_l2_resp = st.columns([0.5, 0.5])  # Nova linha com colunas para percentual e responsável
        col_l3_empty, col_l3_btn = st.columns([0.8, 0.2])  # Renomear para l3 (linha 3)
        
        with col_l1_familia:
            st.text_input(
                "Buscar Família/Contrato", # Label consistente
                placeholder="Digite parte do nome...",
                key=KEY_BUSCA_FAMILIA 
            )

            # --- Sugestões para Busca de Família --- 
            sugestoes_familia = []
            # Ler termo diretamente do session_state que o widget atualiza
            termo_digitado_familia = st.session_state.get(KEY_BUSCA_FAMILIA, "").strip()
            # A coluna nome_familia é verificada no início, assumimos que existe aqui
            if termo_digitado_familia:
                # Usar df_agrupado que já tem nomes únicos e tratados
                nomes_unicos_familia = df_agrupado[coluna_nome_familia].unique()
                sugestoes_familia = [ 
                    nome for nome in nomes_unicos_familia 
                    if termo_digitado_familia.lower() in str(nome).lower() # Garantir str 
                ][:5] # Limitar a 5 sugestões
                
                if sugestoes_familia:
                    st.caption("Sugestões: " + ", ".join(sugestoes_familia))
                elif len(termo_digitado_familia) > 1: 
                    st.caption("Nenhuma família/contrato encontrado.")

        with col_l1_data:
            st.markdown("**Data de Venda**") 
            # Usar colunas internas para alinhar De/Até
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                st.date_input("De", key=KEY_DATA_INICIO, min_value=min_date_default, max_value=max_date_default, label_visibility="collapsed")
            with date_col2:
                st.date_input("Até", key=KEY_DATA_FIM, min_value=min_date_default, max_value=max_date_default, label_visibility="collapsed")
            if st.session_state[KEY_DATA_INICIO] > st.session_state[KEY_DATA_FIM]:
                 st.warning("Data 'De' não pode ser maior que a data 'Até'.")

        with col_l2_perc:
            opcoes_percentual = [
                "0% - 9%", 
                "10% - 30%",
                "31% - 50%",
                "51% - 70%",
                "71% - 90%",
                "91% - 99%", 
                "100%",       
            ]
            st.multiselect(
                "Filtrar por Faixa de % Conclusão",
                options=opcoes_percentual,
                placeholder="Selecione a(s) faixa(s)", # Placeholder melhorado
                key=KEY_PERCENTUAL 
            )
        
        with col_l2_resp:
            # Obter lista de responsáveis únicos para o filtro
            responsaveis_unicos = sorted(df_agrupado['responsavel'].unique().tolist())
            # Remover valores vazios ou nulos se existirem
            responsaveis_unicos = [resp for resp in responsaveis_unicos if resp and str(resp).strip() != '']
            
            st.multiselect(
                "Filtrar por Responsável",
                options=responsaveis_unicos,
                placeholder="Selecione um ou mais responsáveis",
                key=KEY_RESPONSAVEL
            )
            
        with col_l3_btn:
            # Adicionar um pouco de espaço acima do botão
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) 
            st.button("Limpar", on_click=clear_filters, help="Limpar todos os filtros")
            
    # --- Fim Filtros ---
    
    # --- Leitura dos Valores dos Filtros do Session State ---
    search_term = st.session_state[KEY_BUSCA_FAMILIA].strip()
    data_inicio_selecionada = st.session_state[KEY_DATA_INICIO]
    data_fim_selecionada = st.session_state[KEY_DATA_FIM]
    faixas_selecionadas = st.session_state[KEY_PERCENTUAL]
    responsaveis_selecionados = st.session_state[KEY_RESPONSAVEL]  # Ler valores de responsáveis selecionados
    
    # Processar datas selecionadas
    data_venda_min, data_venda_max = None, None
    if data_inicio_selecionada and data_fim_selecionada and data_inicio_selecionada <= data_fim_selecionada:
        data_venda_min = pd.to_datetime(data_inicio_selecionada)
        data_venda_max = pd.to_datetime(data_fim_selecionada) + pd.Timedelta(days=1)
    
    # --- Aplicação dos Filtros (usando valores lidos do state) ---
    df_filtrado_agrupado = df_agrupado.copy() 

    if search_term:
        df_filtrado_agrupado = df_filtrado_agrupado[
            df_filtrado_agrupado[coluna_nome_familia].str.contains(search_term, case=False, na=False)
        ]

    if data_venda_min and data_venda_max:
         df_filtrado_agrupado = df_filtrado_agrupado.dropna(subset=['data_venda_familia']) 
         df_filtrado_agrupado = df_filtrado_agrupado[
             (df_filtrado_agrupado['data_venda_familia'] >= data_venda_min) & 
             (df_filtrado_agrupado['data_venda_familia'] < data_venda_max) 
         ]

    if faixas_selecionadas:
        condicoes = [] 
        for faixa in faixas_selecionadas:
            if faixa == "0% - 9%":
                condicoes.append((df_filtrado_agrupado['percentual_conclusao'] >= 0) & (df_filtrado_agrupado['percentual_conclusao'] < 10))
            elif faixa == "10% - 30%":
                condicoes.append((df_filtrado_agrupado['percentual_conclusao'] >= 10) & (df_filtrado_agrupado['percentual_conclusao'] < 31))
            elif faixa == "31% - 50%":
                 condicoes.append((df_filtrado_agrupado['percentual_conclusao'] >= 31) & (df_filtrado_agrupado['percentual_conclusao'] < 51))
            elif faixa == "51% - 70%":
                 condicoes.append((df_filtrado_agrupado['percentual_conclusao'] >= 51) & (df_filtrado_agrupado['percentual_conclusao'] < 71))
            elif faixa == "71% - 90%":
                 condicoes.append((df_filtrado_agrupado['percentual_conclusao'] >= 71) & (df_filtrado_agrupado['percentual_conclusao'] < 91))
            elif faixa == "91% - 99%": # Intervalo ajustado
                 condicoes.append((df_filtrado_agrupado['percentual_conclusao'] >= 91) & (df_filtrado_agrupado['percentual_conclusao'] < 100))
            elif faixa == "100%": # Nova condição exata
                 condicoes.append(df_filtrado_agrupado['percentual_conclusao'] == 100)

        if condicoes:
            filtro_combinado = pd.concat(condicoes, axis=1).any(axis=1)
            df_filtrado_agrupado = df_filtrado_agrupado[filtro_combinado]
    
    # Aplicar filtro por responsável
    if responsaveis_selecionados:
        df_filtrado_agrupado = df_filtrado_agrupado[
            df_filtrado_agrupado['responsavel'].isin(responsaveis_selecionados)
        ]

    # --- Cálculos Macro DIN MICOS (após filtros) ---
    # Obter a lista de famílias que passaram pelos filtros
    familias_filtradas = df_filtrado_agrupado[coluna_nome_familia].unique()

    # Filtrar o DataFrame ORIGINAL ('df') com base nessas famílias
    df_filtrado_original = df[df[coluna_nome_familia].isin(familias_filtradas)]

    # Recalcular métricas com base no df filtrado original
    total_familias_filtrado = len(familias_filtradas) if 'Família Desconhecida' not in familias_filtradas else len(familias_filtradas) -1 # Não contar 'Desconhecida'
    total_certidoes_filtrado = len(df_filtrado_original)
    total_requerentes_filtrado = df_filtrado_original[df_filtrado_original[coluna_id_requerente] != 'Req. Desconhecido'][coluna_id_requerente].nunique()
    concluidas_filtrado = df_filtrado_original['CONCLUIDA'].sum()
    percentual_conclusao_filtrado = (concluidas_filtrado / total_certidoes_filtrado * 100) if total_certidoes_filtrado > 0 else 0
    
    # --- Exibir Métricas Macro DIN MICAS ---
    col1, col2, col3, col4, col5 = st.columns(5) 
    col1.metric("Famílias", f"{total_familias_filtrado:,}")
    col2.metric("Certidões", f"{total_certidoes_filtrado:,}")
    col3.metric("Requerentes", f"{total_requerentes_filtrado:,}", help=f"Contagem de IDs únicos ({coluna_id_requerente}) das famílias filtradas.")
    col4.metric("Concluídas", f"{concluidas_filtrado:,}")
    col5.metric("% Conclusão", f"{percentual_conclusao_filtrado:.1f}%", help="Percentual calculado sobre as certidões das famílias filtradas.")
    st.markdown("---") # Divisor


    # --- Preparação da Tabela Final ---
    st.markdown("#### Detalhamento por Família")
    
    # Renomear colunas do df_filtrado_agrupado para exibição
    df_tabela = df_filtrado_agrupado.rename(columns={
        coluna_nome_familia: 'Nome da Família',
        'total_certidoes': 'Total Certidões',
        'total_requerentes': 'Total Requerentes',
        'concluidas': 'Concluídas',
        'percentual_conclusao': '% Conclusão',
        'data_venda_familia': 'Data Venda', # Renomear coluna de data
        'responsavel': 'Responsável' # Renomear coluna de responsável
    })

    # Ordenar a tabela final (opcional, pode escolher outra coluna)
    df_tabela = df_tabela.sort_values(by='Total Certidões', ascending=False)

    # Verificar se, após todos os filtros, o dataframe está vazio
    if df_tabela.empty:
        # Verificar se algum filtro ESTÁ ativo para mostrar a mensagem
        filtros_ativos = search_term or (data_venda_min and data_venda_max) or faixas_selecionadas or responsaveis_selecionados
        if filtros_ativos:
             st.warning("Nenhuma família encontrada com os critérios de filtros aplicados.")
        # else: Não mostrar nada se não há filtros e a tabela está vazia (já avisado no início)
    else:
         # Mostrar contagem baseada no df_filtrado_agrupado (que virou df_tabela)
        st.caption(f"> Exibindo {len(df_tabela)} de {len(df_agrupado)} famílias após aplicação dos filtros.")

    # --- Exibição da Tabela com Estilos --- 

    # Selecionar e reordenar colunas para exibição
    colunas_exibicao = [
        'Nome da Família',
        'Data Venda', # Adicionada
        'Total Requerentes',
        'Responsável', # Adicionada
        'Total Certidões',
        'Concluídas',
        '% Conclusão'
    ]
    # Remover 'Data Venda' se a coluna não existir no df_tabela final (caso raro de erro no loader)
    if 'Data Venda' not in df_tabela.columns:
        colunas_exibicao.remove('Data Venda')
    # Remover 'Responsável' se a coluna não existir
    if 'Responsável' not in df_tabela.columns:
        colunas_exibicao.remove('Responsável')

    # Configuração dinâmica das colunas
    column_config_dict = {
        "Nome da Família": st.column_config.TextColumn(label="Nome da Família"),
        "Total Requerentes": st.column_config.NumberColumn(
            label="Total Requerentes", 
            format="%d",
            help=f"Contagem de IDs únicos ({coluna_id_requerente})"
        ),
        "Total Certidões": st.column_config.NumberColumn(label="Total Certidões", format="%d"),
        "Concluídas": st.column_config.NumberColumn(label="Concluídas", format="%d"),
        "% Conclusão": st.column_config.ProgressColumn(
            label="% Conclusão",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
    }
    
    # Adicionar configuração para responsável se a coluna for exibida
    if 'Responsável' in colunas_exibicao:
        column_config_dict['Responsável'] = st.column_config.TextColumn(
            label="Responsável"
        )

    # Adicionar configuração para data de venda se a coluna for exibida
    if 'Data Venda' in colunas_exibicao:
        column_config_dict['Data Venda'] = st.column_config.DateColumn(
            label="Data Venda",
            format="DD/MM/YYYY"
        )

    st.dataframe(
        df_tabela[colunas_exibicao], # Usar df_tabela com colunas selecionadas
        hide_index=True,
        use_container_width=True,
        column_config=column_config_dict,
    ) 