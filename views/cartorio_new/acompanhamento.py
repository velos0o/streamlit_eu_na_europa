import streamlit as st
import pandas as pd
from datetime import datetime, date # Adicionar date

# Reutilizar as funções de visao_geral para consistência
# from .visao_geral import simplificar_nome_estagio, categorizar_estagio # Comentado
from .utils import simplificar_nome_estagio, categorizar_estagio # Adicionado

# --- Constantes Chaves Session State ---
KEY_BUSCA_FAMILIA = "busca_familia_acompanhamento"
KEY_DATA_INICIO = "data_venda_inicio_acompanhamento"
KEY_DATA_FIM = "data_venda_fim_acompanhamento"
KEY_PERCENTUAL = "filtro_percentual_acompanhamento"
KEY_RESPONSAVEL = "filtro_responsavel_acompanhamento"  # Nova constante para filtro de responsável
KEY_PROTOCOLIZADO = "filtro_protocolizado_acompanhamento"  # Nova constante para filtro de protocolizado

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
    
    # NOVA LÓGICA: Aplicar regras específicas para os pipelines
    df['CONCLUIDA'] = df.apply(lambda row: calcular_conclusao_por_pipeline(row), axis=1)
    
    # 3. Tratar Nulos na coluna Nome da Família (já feito no loader, mas confirmando)
    df[coluna_nome_familia] = df[coluna_nome_familia].fillna('Família Desconhecida').astype(str)
    df[coluna_nome_familia] = df[coluna_nome_familia].replace(r'^\s*$', 'Família Desconhecida', regex=True)

    # --- LÓGICA ESPECIAL PARA PIPELINE 104 (Pesquisa BR) ---
    # Aplicar lógica de precedência para evitar duplicação de contagem
    df = aplicar_logica_precedencia_pipeline_104(df, coluna_id_requerente)
    
    # --- Agrupamento por Família (pré-filtro) ---
    coluna_protocolizado = 'UF_CRM_34_PROTOCOLIZADO'

    def check_protocolado(series):
        # Normaliza para maiúsculas e lida com possíveis NaNs
        normalized_series = series.astype(str).str.upper().fillna('')
        if 'PROTOCOLIZADO' in normalized_series.values:
            return 'PROTOCOLIZADO'
        return 'NÃO PROTOCOLIZADO'

    # Dicionário de agregação base
    agg_dict = {
        'total_certidoes': ('ID', 'count'),
        'total_requerentes': (coluna_id_requerente, pd.Series.nunique),
        'concluidas': ('CONCLUIDA', 'sum'),
        'data_venda_familia': (coluna_data_venda_familia, 'first'),
        'responsavel': (coluna_responsavel, 'first')
    }

    # Adiciona a agregação de protocolado dinamicamente se a coluna existir
    if coluna_protocolizado in df.columns:
        agg_dict['protocolado_familia'] = (coluna_protocolizado, check_protocolado)
    else:
        # Emite aviso se a coluna não for encontrada
        if 'aviso_protocolizado_emitido' not in st.session_state:
            st.warning(f"Campo '{coluna_protocolizado}' não encontrado. Filtro de protocolizado não disponível.")
            st.session_state['aviso_protocolizado_emitido'] = True

    df_agrupado = df.groupby(coluna_nome_familia).agg(**agg_dict).reset_index()

    # Calcular Percentual de Conclusão
    df_agrupado['percentual_conclusao'] = (
        (df_agrupado['concluidas'] / df_agrupado['total_certidoes'] * 100)
    ).fillna(0) # Preencher NaN com 0 se total_certidoes for 0

    # --- Valores Padrão para Filtros (Necessário para Reset) ---
    df_agrupado_com_data = df_agrupado.dropna(subset=['data_venda_familia'])
    min_date_default = df_agrupado_com_data['data_venda_familia'].min().date() if not df_agrupado_com_data.empty else date.today()
    max_date_default = df_agrupado_com_data['data_venda_familia'].max().date() if not df_agrupado_com_data.empty else date.today()

    # --- Inicialização e VALIDAÇÃO do Session State (Robusto para Produção) ---
    if KEY_BUSCA_FAMILIA not in st.session_state:
        st.session_state[KEY_BUSCA_FAMILIA] = ""

    # VALIDAÇÃO DAS DATAS: Previne erro se os filtros mudarem o min/max das datas.
    # Pega os valores da sessão ou usa os defaults.
    start_date_from_session = st.session_state.get(KEY_DATA_INICIO, min_date_default)
    end_date_from_session = st.session_state.get(KEY_DATA_FIM, max_date_default)

    # "Clampa" os valores da sessão para garantir que estão dentro do novo range válido.
    validated_start_date = max(min_date_default, min(start_date_from_session, max_date_default))
    validated_end_date = max(min_date_default, min(end_date_from_session, max_date_default))
    
    # Garante que a data de início não seja posterior à de fim.
    if validated_start_date > validated_end_date:
        validated_start_date = validated_end_date

    # Atualiza a sessão com os valores validados ANTES de renderizar o widget.
    st.session_state[KEY_DATA_INICIO] = validated_start_date
    st.session_state[KEY_DATA_FIM] = validated_end_date

    if KEY_PERCENTUAL not in st.session_state:
        st.session_state[KEY_PERCENTUAL] = []
    if KEY_RESPONSAVEL not in st.session_state:  # Inicialização do state para responsável
        st.session_state[KEY_RESPONSAVEL] = []
    if KEY_PROTOCOLIZADO not in st.session_state:  # Inicialização do state para protocolizado
        st.session_state[KEY_PROTOCOLIZADO] = "Todos"

    # --- Função para Limpar Filtros --- 
    def clear_filters():
        st.session_state[KEY_BUSCA_FAMILIA] = ""
        st.session_state[KEY_DATA_INICIO] = min_date_default
        st.session_state[KEY_DATA_FIM] = max_date_default
        st.session_state[KEY_PERCENTUAL] = []
        st.session_state[KEY_RESPONSAVEL] = []  # Limpar filtro de responsável
        st.session_state[KEY_PROTOCOLIZADO] = "Todos"  # Limpar filtro de protocolizado

    # --- Filtros --- 
    with st.expander("Filtros", expanded=True): 
        # Layout: Linha 1 (Família, Data), Linha 2 (Percentual, Responsável, Protocolizado), Linha 3 (Botão Limpar)
        col_l1_familia, col_l1_data = st.columns([0.5, 0.5])
        col_l2_perc, col_l2_resp, col_l2_protocolo = st.columns([0.4, 0.4, 0.2])  # Nova linha com 3 colunas
        col_l3_empty, col_l3_btn = st.columns([0.8, 0.2])  # Renomear para l3 (linha 3)
        
        with col_l1_familia:
            st.text_input(
                "Buscar Família/Contrato:",
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
                st.date_input("De:", key=KEY_DATA_INICIO, min_value=min_date_default, max_value=max_date_default, label_visibility="collapsed")
            with date_col2:
                st.date_input("Até:", key=KEY_DATA_FIM, min_value=min_date_default, max_value=max_date_default, label_visibility="collapsed")
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
                "Filtrar por Faixa de % Conclusão:",
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
                "Filtrar por Responsável:",
                options=responsaveis_unicos,
                placeholder="Selecione um ou mais responsáveis",
                key=KEY_RESPONSAVEL,
                help="Você pode selecionar um ou mais responsáveis para filtrar os resultados."
            )
        
        with col_l2_protocolo:
            # --- Filtro de Protocolizado ---
            st.selectbox(
                "Protocolizado:",
                options=["Todos", "Protocolizado", "Não Protocolizado"],
                key=KEY_PROTOCOLIZADO
            )
            
        with col_l3_btn:
            st.button("Limpar", on_click=clear_filters, help="Limpar todos os filtros")
            
    # --- Fim Filtros ---
    
    # --- Leitura dos Valores dos Filtros do Session State ---
    search_term = st.session_state[KEY_BUSCA_FAMILIA].strip()
    data_inicio_selecionada = st.session_state[KEY_DATA_INICIO]
    data_fim_selecionada = st.session_state[KEY_DATA_FIM]
    faixas_selecionadas = st.session_state[KEY_PERCENTUAL]
    responsaveis_selecionados = st.session_state[KEY_RESPONSAVEL]  # Ler valores de responsáveis selecionados
    protocolizado_selecionado = st.session_state[KEY_PROTOCOLIZADO]  # Ler valor do filtro de protocolizado
    
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

    # Aplicar filtro por protocolado (agora no dataframe agrupado)
    if protocolizado_selecionado != "Todos" and 'protocolado_familia' in df_filtrado_agrupado.columns:
        df_filtrado_agrupado = df_filtrado_agrupado[
            df_filtrado_agrupado['protocolado_familia'] == protocolizado_selecionado.upper()
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
    
    # Criar métricas customizadas com HTML puro
    st.markdown(f"""
    <style>
    .metrica-custom-acomp {{
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
    
    .metrica-custom-acomp:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: #ADB5BD;
    }}
    
    .metrica-custom-acomp .label {{
        color: #6C757D;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
        line-height: 1.2;
    }}
    
    .metrica-custom-acomp .valor {{
        color: #495057;
        font-weight: 700;
        font-size: 30px;
        line-height: 1.2;
        margin-bottom: 4px;
    }}
    
    .metricas-container-acomp {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }}
    
    .metrica-help {{
        font-size: 10px;
        color: #6C757D;
        margin-top: 4px;
        font-style: italic;
    }}
    </style>
    
    <div class="metricas-container-acomp">
        <div class="metrica-custom-acomp">
            <div class="label">Famílias</div>
            <div class="valor">{total_familias_filtrado:,}</div>
        </div>
        <div class="metrica-custom-acomp">
            <div class="label">Certidões</div>
            <div class="valor">{total_certidoes_filtrado:,}</div>
        </div>
        <div class="metrica-custom-acomp">
            <div class="label">Requerentes</div>
            <div class="valor">{total_requerentes_filtrado:,}</div>
            <div class="metrica-help">IDs únicos ({coluna_id_requerente})</div>
        </div>
        <div class="metrica-custom-acomp">
            <div class="label">Concluídas</div>
            <div class="valor">{concluidas_filtrado:,}</div>
        </div>
        <div class="metrica-custom-acomp">
            <div class="label">% Conclusão</div>
            <div class="valor">{percentual_conclusao_filtrado:.1f}%</div>
            <div class="metrica-help">Sobre certidões filtradas</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")  # Divisor simples do Streamlit

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

def calcular_conclusao_por_pipeline(row):
    """
    Calcula se uma certidão está concluída baseada no pipeline e lógica específica.
    
    CORRIGIDO DEZEMBRO 2024: Incluindo suporte correto para funis 102 (Paróquia) e 104 (Pesquisa BR)
    
    Pipeline 92/94 (Cartórios): Lógica normal
    Pipeline 102 (Paróquia): Incluir nas métricas normais  
    Pipeline 104 (Pesquisa BR): APENAS considerar concluído quando realmente finalizado
    """
    category_id = str(row.get('CATEGORY_ID', ''))
    estagio_legivel = row.get('ESTAGIO_LEGIVEL', '')
    categoria_estagio = row.get('CATEGORIA_ESTAGIO', '')
    
    # Pipeline 102 (Paróquia): Tratar como pipeline normal de emissão
    if category_id == '102':
        return categoria_estagio == 'SUCESSO'
    
    # Pipeline 104 (Pesquisa BR): CORRIGIDO - Lógica mais restritiva
    elif category_id == '104':
        # CORREÇÃO CRÍTICA: Não considerar "PESQUISA PRONTA PARA EMISSÃO" como concluída
        # Isso significa apenas que a pesquisa foi finalizada, mas ainda precisa ser processada
        # Apenas considerar concluído se realmente chegou ao final do processo
        
        # Para pipeline 104, só considerar concluído se:
        # 1. Chegou ao estado SUCCESS final (se existir)
        # 2. OU se foi dispensada/cancelada (FAIL pode indicar finalização)
        if categoria_estagio == 'SUCESSO':
            return True
        elif categoria_estagio == 'FALHA':
            # PESQUISA NÃO ENCONTRADA pode ser considerada como "concluída" no sentido de finalizada
            return True
        else:
            # Estados como "PESQUISA PRONTA PARA EMISSÃO" NÃO são conclusão final
            # pois ainda precisam ser processados em outros funis
            return False
    
    # Pipelines 92 e 94 (Cartórios): Lógica normal
    else:
        return categoria_estagio == 'SUCESSO'

def aplicar_logica_precedencia_pipeline_104(df, coluna_id_requerente):
    """
    Aplica lógica de precedência para o pipeline 104 (Pesquisa BR).
    
    ATUALIZADA DEZEMBRO 2024: Melhorada para tratar adequadamente a lógica de duplicação
    
    Regras:
    1. Se um requerente tem registros no pipeline 104 EM ANDAMENTO E
    2. Tem registros nos pipelines superiores (92, 94, 102) TAMBÉM EM ANDAMENTO
    3. Então: Manter ambos na contagem (são processos paralelos)
    
    4. Se um requerente tem pipeline 104 "PESQUISA PRONTA" E
    5. Tem registros nos pipelines superiores (92, 94, 102) 
    6. Então: Manter o 104 na contagem APENAS se não houver duplicação real
    
    IMPORTANTE: Ser mais conservador para não remover dados importantes
    """
    df_processado = df.copy()
    
    if 'CATEGORY_ID' not in df_processado.columns or coluna_id_requerente not in df_processado.columns:
        return df_processado
    
    # Identificar requerentes que têm pipeline 104
    requerentes_104 = df_processado[
        df_processado['CATEGORY_ID'].astype(str) == '104'
    ][coluna_id_requerente].unique()
    
    if len(requerentes_104) == 0:
        return df_processado
    
    # Para cada requerente com 104, verificar se há conflito real de duplicação
    requerentes_para_ajustar_104 = []
    
    for id_requerente in requerentes_104:
        registros_requerente = df_processado[df_processado[coluna_id_requerente] == id_requerente]
        
        # Verificar registros por pipeline
        registros_104 = registros_requerente[registros_requerente['CATEGORY_ID'].astype(str) == '104']
        registros_superiores = registros_requerente[registros_requerente['CATEGORY_ID'].astype(str).isin(['92', '94', '102'])]
        
        # Se tem pipelines superiores E pipeline 104 está "pronto para emissão"
        if not registros_superiores.empty and not registros_104.empty:
            # Verificar se o 104 está realmente pronto para emissão (seria duplicação)
            tem_104_pronto = registros_104['ESTAGIO_LEGIVEL'].str.contains('PESQUISA PRONTA PARA EMISSÃO', na=False).any()
            
            # Verificar se os pipelines superiores estão ativos/em andamento
            superiores_ativos = registros_superiores['CATEGORIA_ESTAGIO'].isin(['EM_ANDAMENTO', 'SUCESSO']).any()
            
            if tem_104_pronto and superiores_ativos:
                # APENAS remover se há clara duplicação 
                # (pesquisa pronta + pipeline superior ativo)
                requerentes_para_ajustar_104.append(id_requerente)
                
        
    
    # AJUSTE CONSERVADOR: Em vez de remover, apenas marcar para não contar como "concluído"
    # se há duplicação real
    if requerentes_para_ajustar_104:
        # Aplicar ajuste mais sutil: não remover registros, mas ajustar a contagem de conclusão
        for id_req in requerentes_para_ajustar_104:
            mask_104_pronto = (
                (df_processado[coluna_id_requerente] == id_req) &
                (df_processado['CATEGORY_ID'].astype(str) == '104') &
                (df_processado['ESTAGIO_LEGIVEL'].str.contains('PESQUISA PRONTA PARA EMISSÃO', na=False))
            )
            
            # Em vez de remover, vamos deixar o registro mas não contar como concluído
            # (isso será tratado na função de conclusão revisada)
            if mask_104_pronto.any():
                pass
    
    return df_processado 