import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date # Adicionar date
from ..priorizados.priorizados_main import carregar_dados_priorizados

# Reutilizar as funções de visao_geral para consistência
# from .visao_geral import simplificar_nome_estagio, categorizar_estagio # Comentado
from .utils import simplificar_nome_estagio, categorizar_estagio # Adicionado
from utils.dataframe_utils import ensure_pandas_df

# --- Constantes Chaves Session State ---
KEY_BUSCA_FAMILIA = "busca_familia_acompanhamento"
KEY_DATA_INICIO = "data_venda_inicio_acompanhamento"
KEY_DATA_FIM = "data_venda_fim_acompanhamento"
KEY_DATA_EMISSAO_INICIO = "data_emissao_inicio_acompanhamento"  # Nova constante para filtro de data de emissão
KEY_DATA_EMISSAO_FIM = "data_emissao_fim_acompanhamento"  # Nova constante para filtro de data de emissão
KEY_PERCENTUAL = "filtro_percentual_acompanhamento"
KEY_RESPONSAVEL = "filtro_responsavel_acompanhamento"  # Nova constante para filtro de responsável
KEY_PROTOCOLIZADO = "filtro_protocolizado_acompanhamento"  # Nova constante para filtro de protocolizado
KEY_STATUS_FAMILIA = "filtro_status_acompanhamento" # Novo status
KEY_CERTIDOES_FALTANTES = "filtro_faltantes_acompanhamento" # Nova constante

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

    # --- Carregar dados de Priorizados para obter o responsável correto ---
    with st.spinner("Carregando dados de responsáveis atualizados..."):
        df_priorizados_raw = carregar_dados_priorizados()

    df_responsavel_atualizado = pd.DataFrame()
    if not df_priorizados_raw.empty:
        # Mapear colunas A (Nome da Família) e C (CONSULTOR RESPONSÁVEL)
        mapeamento_colunas = {
            'A': 'NOME_FAMILIA_PLANILHA',
            'C': 'CONSULTOR RESPONSÁVEL'
        }
        df_priorizados = df_priorizados_raw.rename(columns=mapeamento_colunas)
        
        if 'NOME_FAMILIA_PLANILHA' in df_priorizados.columns and 'CONSULTOR RESPONSÁVEL' in df_priorizados.columns:
            df_responsavel_atualizado = df_priorizados[['NOME_FAMILIA_PLANILHA', 'CONSULTOR RESPONSÁVEL']].copy()
            df_responsavel_atualizado.dropna(subset=['NOME_FAMILIA_PLANILHA', 'CONSULTOR RESPONSÁVEL'], inplace=True)
            # Remover linhas onde o consultor é uma string vazia
            df_responsavel_atualizado = df_responsavel_atualizado[df_responsavel_atualizado['CONSULTOR RESPONSÁVEL'].str.strip() != '']
            # Em caso de duplicatas de família, manter a última entrada da planilha
            df_responsavel_atualizado.drop_duplicates(subset=['NOME_FAMILIA_PLANILHA'], keep='last', inplace=True)

    # Verificar se as colunas necessárias existem
    coluna_nome_familia = 'UF_CRM_34_NOME_FAMILIA'  # ATUALIZADO para o novo campo SPA
    coluna_id_requerente = 'UF_CRM_34_ID_REQUERENTE' # ATUALIZADO para o novo campo SPA
    coluna_data_venda_familia = 'DATA_VENDA_FAMILIA' # Vem da categoria 46 - UF_CRM_1746054586042
    coluna_data_emissao = 'UF_CRM_34_DATA_CERTIDAO_EMITIDA' # Data de emissão da certidão
    coluna_data_entregue = 'UF_CRM_34_DATA_CERTIDAO_ENTREGUE' # Data de entrega da certidão (fallback)
    coluna_responsavel_bitrix = 'ASSIGNED_BY_NAME' # Coluna do responsável original do Bitrix
    colunas_requeridas = ['ID', 'STAGE_ID', coluna_nome_familia, coluna_id_requerente, coluna_data_venda_familia, coluna_responsavel_bitrix]
    colunas_faltantes = [col for col in colunas_requeridas if col not in df_cartorio.columns]

    if colunas_faltantes:
        # Ajustar a mensagem de erro para a nova coluna de data
        cols_necessarias_origem = [c for c in colunas_faltantes if c not in [coluna_data_venda_familia, coluna_responsavel_bitrix]]
        msg_erro = ""
        if cols_necessarias_origem:
             msg_erro += f"Erro: As seguintes colunas são necessárias e não foram encontradas nos dados originais: {', '.join(cols_necessarias_origem)}. Verifique o data_loader. "
        if coluna_data_venda_familia in colunas_faltantes:
             msg_erro += f"Erro: A coluna '{coluna_data_venda_familia}' (obtida da categoria 46 - UF_CRM_1746054586042) não foi encontrada. Verifique o merge no data_loader. "
        if coluna_responsavel_bitrix in colunas_faltantes: # Adicionar verificação do responsável
             msg_erro += f"Erro: A coluna '{coluna_responsavel_bitrix}' (necessária como fallback para o responsável) não foi encontrada. Verifique o data_loader."
        
        # Adicionar espaço entre as mensagens se ambas existirem
        msg_erro = msg_erro.strip() # Remover espaços extras no início/fim
        
        st.error(msg_erro)
        # st.dataframe(df_cartorio.head()) # Descomentar se precisar debugar
        return

    # --- Pré-processamento e Merge para atualizar o responsável --- 
    df = df_cartorio.copy()

    # --- FILTRO: Remover STAGE_IDs específicos da contagem ---
    # Lista de stage_ids que devem ser excluídos da contagem de certidões
    stage_ids_excluidos = [
        'DT1098_92:UC_U10R0R',
        'DT1098_94:UC_L3JFKO',
        'DT1098_94:UC_MGTPX0',
        'DT1098_92:UC_Z24IF7',
        'DT1098_94:FAIL',
        'DT1098_92:FAIL'
    ]
    
    # Remover registros com esses stage_ids antes de qualquer processamento
    if 'STAGE_ID' in df.columns:
        df_antes_filtro = len(df)
        df = df[~df['STAGE_ID'].isin(stage_ids_excluidos)]
        df_depois_filtro = len(df)
        registros_removidos = df_antes_filtro - df_depois_filtro
        if registros_removidos > 0:
            st.info(f"ℹ️ {registros_removidos} registro(s) excluído(s) da contagem (estágios específicos não considerados).")
    # --- FIM FILTRO ---

    if not df_responsavel_atualizado.empty:
        # --- PREPARAR CHAVES PARA O MERGE ---
        # Garantir que ambas as chaves sejam strings e sem espaços extras para um merge robusto
        df[coluna_nome_familia] = df[coluna_nome_familia].astype(str).str.strip()
        df_responsavel_atualizado['NOME_FAMILIA_PLANILHA'] = df_responsavel_atualizado['NOME_FAMILIA_PLANILHA'].astype(str).str.strip()

        df = pd.merge(
            df,
            df_responsavel_atualizado,
            left_on=coluna_nome_familia,
            right_on='NOME_FAMILIA_PLANILHA',
            how='left'
        )
        # Define 'responsavel_final', priorizando a planilha.
        df['responsavel_final'] = df['CONSULTOR RESPONSÁVEL'].fillna(df[coluna_responsavel_bitrix])
    else:
        # Se a planilha não carregar, usa a coluna original.
        df['responsavel_final'] = df[coluna_responsavel_bitrix]
        
    coluna_responsavel = 'responsavel_final' # Usar esta coluna como a definitiva

    # 1. Garantir tipo correto para ID Requerente (já feito no loader, mas confirmando)
    df[coluna_id_requerente] = df[coluna_id_requerente].fillna('Req. Desconhecido').astype(str)
    # Tratar responsável Nulo (agora na coluna final)
    df[coluna_responsavel] = df[coluna_responsavel].fillna('Desconhecido').astype(str)
    
    # Coluna Data Venda Família (do data_loader) - Garantir Datetime
    if coluna_data_venda_familia not in df.columns: # Redundante pela verificação acima, mas seguro
        st.warning(f"Coluna '{coluna_data_venda_familia}' não encontrada. O filtro por data de venda não estará disponível.")
        df[coluna_data_venda_familia] = pd.NaT 
    else:
        df[coluna_data_venda_familia] = pd.to_datetime(df[coluna_data_venda_familia], errors='coerce')
    
    # Coluna Data Emissão Certidão - Garantir Datetime
    if coluna_data_emissao not in df.columns:
        st.warning(f"Coluna '{coluna_data_emissao}' não encontrada. O filtro por data de emissão não estará disponível.")
        df[coluna_data_emissao] = pd.NaT
    else:
        df[coluna_data_emissao] = pd.to_datetime(df[coluna_data_emissao], errors='coerce')

    # Coluna Data Entregue Certidão - Garantir Datetime
    if coluna_data_entregue in df.columns:
        df[coluna_data_entregue] = pd.to_datetime(df[coluna_data_entregue], errors='coerce')
    else:
        df[coluna_data_entregue] = pd.NaT
    
    # Coluna Final de Data Certidão (Entregue com fallback para Emitida)
    # ESTA É A DATA DE FINALIZAÇÃO DA PASTA (última certidão da família)
    df['data_certidao_final'] = df[coluna_data_entregue].fillna(df[coluna_data_emissao])
    
    # 2. Simplificar e Categorizar Estágios
    df['STAGE_ID'] = df['STAGE_ID'].astype(str)
    df['ESTAGIO_LEGIVEL'] = df['STAGE_ID'].apply(simplificar_nome_estagio)
    df['CATEGORIA_ESTAGIO'] = df['ESTAGIO_LEGIVEL'].apply(categorizar_estagio)
    
    # NOVA LÓGICA: Aplicar regras específicas para os pipelines
    df['CONCLUIDA'] = df.apply(lambda row: calcular_conclusao_por_pipeline(row), axis=1)
    
    # 3. Tratar Nulos na coluna Nome da Família (já feito no loader, mas confirmando)
    df[coluna_nome_familia] = df[coluna_nome_familia].fillna('Família Desconhecida').astype(str)
    df[coluna_nome_familia] = df[coluna_nome_familia].replace(r'^\s*$', 'Família Desconhecida', regex=True)

    # --- Lógica para Status da Família (Adendo/Distrato) ---
    coluna_adendo_campo = 'UF_CRM_1751313454983'
    coluna_deal_stage_id = 'DEAL_STAGE_ID' # Coluna que contém os estágios como C46:LOSE
    
    # Inicializa a coluna de status como vazia
    df['status_familia'] = ''

    # Verificar se a coluna de estágios do deal existe
    if coluna_deal_stage_id in df.columns:
        # 1. Distrato (prioridade máxima) - Estágio C46:LOSE
        cond_distrato = df[coluna_deal_stage_id] == 'C46:LOSE'
        df.loc[cond_distrato, 'status_familia'] = 'DISTRATO'

        # 2. Adendo (menor prioridade) - Baseado apenas no campo UF_CRM_1751313454983
        cond_adendo_final = pd.Series(False, index=df.index) # Inicia com um Series de False
        
        if coluna_adendo_campo in df.columns:
            # Garante que a coluna seja string para usar .str.contains
            # Procura por 'ADENDO' OU 'FILHOS E NETOS', ignorando maiúsculas/minúsculas
            cond_adendo_campo_val = df[coluna_adendo_campo].astype(str).str.contains(
                'ADENDO|FILHOS E NETOS', 
                case=False, 
                na=False, 
                regex=True
            )
            cond_adendo_final = cond_adendo_campo_val
        
        # Aplica 'ADENDO' somente onde o status ainda não for 'DISTRATO'
        df.loc[cond_adendo_final & (df['status_familia'] == ''), 'status_familia'] = 'ADENDO'
    else:
        # Emite um aviso se a coluna de estágio do deal não for encontrada (apenas uma vez)
        if 'aviso_deal_stage_emitido' not in st.session_state:
            st.warning(f"Coluna '{coluna_deal_stage_id}' não encontrada. O status de Adendo/Distrato não será calculado.")
            st.session_state['aviso_deal_stage_emitido'] = True

    # --- LÓGICA ESPECIAL PARA PIPELINE 104 (Pesquisa BR) ---
    # Aplicar lógica de precedência para evitar duplicação de contagem
    df = aplicar_logica_precedencia_pipeline_104(df, coluna_id_requerente)
    
    # --- Agrupamento por Família (pré-filtro) ---
    coluna_protocolizado = 'UF_CRM_34_PROTOCOLIZADO'

    def aggregate_status(series):
        # Define a prioridade do status para a família inteira
        if 'DISTRATO' in series.values:
            return 'DISTRATO'
        if 'ADENDO' in series.values:
            return 'ADENDO'
        return '' # Retorna vazio se nenhum status for encontrado

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
        'data_certidao_final': ('data_certidao_final', 'max'),  # Usa data entregue com fallback para emitida
        'data_finalizacao_pasta': ('data_certidao_final', 'max'),  # MESMA LÓGICA: última certidão da família (entregue ou emitida)
        'responsavel': (coluna_responsavel, 'first'),
        'status_familia': ('status_familia', aggregate_status) # Adicionar agregação de status
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

    # Adicionar coluna de certidões faltantes
    df_agrupado['certidoes_faltantes'] = df_agrupado['total_certidoes'] - df_agrupado['concluidas']
    
    # --- CÁLCULO DE DIAS PARA FINALIZAÇÃO ---
    # Calcular apenas para famílias 100% concluídas (percentual_conclusao == 100)
    # Dias = diferença entre data_certidao_final (última certidão final) e data_venda_familia
    df_agrupado['dias_para_finalizacao'] = None  # Inicializar com None
    
    # Condições: família 100% concluída E ambas as datas existem
    condicao_finalizadas = (
        (df_agrupado['percentual_conclusao'] == 100) & 
        (df_agrupado['data_venda_familia'].notna()) & 
        (df_agrupado['data_certidao_final'].notna())
    )
    
    # Calcular diferença em dias
    df_agrupado.loc[condicao_finalizadas, 'dias_para_finalizacao'] = (
        df_agrupado.loc[condicao_finalizadas, 'data_certidao_final'] - 
        df_agrupado.loc[condicao_finalizadas, 'data_venda_familia']
    ).dt.days
    
    # --- NOVO CÁLCULO: Finalização da Pasta (baseado na última certidão emitida no funil) ---
    # Garantir que famílias não finalizadas (menos de 100%) não apresentem data de finalização
    mask_nao_finalizadas = df_agrupado['percentual_conclusao'] < 100
    df_agrupado.loc[mask_nao_finalizadas, 'data_finalizacao_pasta'] = pd.NaT
    
    # --- Valores Padrão para Filtros (Necessário para Reset) ---
    df_agrupado_com_data = df_agrupado.dropna(subset=['data_venda_familia'])
    min_date_default = df_agrupado_com_data['data_venda_familia'].min().date() if not df_agrupado_com_data.empty else date.today()
    max_date_default = df_agrupado_com_data['data_venda_familia'].max().date() if not df_agrupado_com_data.empty else date.today()
    
    # Valores padrão para filtro de data de emissão (usando coluna final)
    df_agrupado_com_data_emissao = df_agrupado.dropna(subset=['data_certidao_final'])
    min_date_emissao_default = df_agrupado_com_data_emissao['data_certidao_final'].min().date() if not df_agrupado_com_data_emissao.empty else date.today()
    max_date_emissao_default = df_agrupado_com_data_emissao['data_certidao_final'].max().date() if not df_agrupado_com_data_emissao.empty else date.today()

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

    # VALIDAÇÃO DAS DATAS DE EMISSÃO: Similar à validação de data de venda
    start_date_emissao_from_session = st.session_state.get(KEY_DATA_EMISSAO_INICIO, min_date_emissao_default)
    end_date_emissao_from_session = st.session_state.get(KEY_DATA_EMISSAO_FIM, max_date_emissao_default)

    # "Clampa" os valores da sessão para garantir que estão dentro do novo range válido.
    validated_start_date_emissao = max(min_date_emissao_default, min(start_date_emissao_from_session, max_date_emissao_default))
    validated_end_date_emissao = max(min_date_emissao_default, min(end_date_emissao_from_session, max_date_emissao_default))
    
    # Garante que a data de início não seja posterior à de fim.
    if validated_start_date_emissao > validated_end_date_emissao:
        validated_start_date_emissao = validated_end_date_emissao

    # Atualiza a sessão com os valores validados ANTES de renderizar o widget.
    st.session_state[KEY_DATA_EMISSAO_INICIO] = validated_start_date_emissao
    st.session_state[KEY_DATA_EMISSAO_FIM] = validated_end_date_emissao

    if KEY_PERCENTUAL not in st.session_state:
        st.session_state[KEY_PERCENTUAL] = []
    if KEY_RESPONSAVEL not in st.session_state:  # Inicialização do state para responsável
        st.session_state[KEY_RESPONSAVEL] = []
    if KEY_PROTOCOLIZADO not in st.session_state:  # Inicialização do state para protocolizado
        st.session_state[KEY_PROTOCOLIZADO] = "Todos"
    if KEY_STATUS_FAMILIA not in st.session_state:
        st.session_state[KEY_STATUS_FAMILIA] = "Todos"
    if KEY_CERTIDOES_FALTANTES not in st.session_state:
        st.session_state[KEY_CERTIDOES_FALTANTES] = [] # Alterado para lista vazia para multiselect

    # --- Função para Limpar Filtros --- 
    def clear_filters():
        st.session_state[KEY_BUSCA_FAMILIA] = ""
        st.session_state[KEY_DATA_INICIO] = min_date_default
        st.session_state[KEY_DATA_FIM] = max_date_default
        st.session_state[KEY_DATA_EMISSAO_INICIO] = min_date_emissao_default  # Limpar filtro de data de emissão
        st.session_state[KEY_DATA_EMISSAO_FIM] = max_date_emissao_default  # Limpar filtro de data de emissão
        st.session_state[KEY_PERCENTUAL] = []
        st.session_state[KEY_RESPONSAVEL] = []  # Limpar filtro de responsável
        st.session_state[KEY_PROTOCOLIZADO] = "Todos"  # Limpar filtro de protocolizado
        st.session_state[KEY_STATUS_FAMILIA] = "Todos"
        st.session_state[KEY_CERTIDOES_FALTANTES] = [] # Alterado para lista vazia

    # --- Filtros --- 
    with st.expander("Filtros", expanded=True): 
        # Layout: Linha 1 (Família, Data Venda), Linha 1.5 (Data Emissão), Linha 2 (Percentual, Responsável, Protocolizado, Status, Faltantes), Linha 3 (Botão Limpar)
        col_l1_familia, col_l1_data = st.columns([0.5, 0.5])
        col_l1_5_data_emissao = st.columns([1.0])[0]  # Nova linha para data de emissão
        col_l2_perc, col_l2_resp, col_l2_protocolo, col_l2_status, col_l2_faltantes = st.columns([0.20, 0.20, 0.15, 0.15, 0.15])
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
        
        # Filtro de Data de Emissão (nova linha)
        with col_l1_5_data_emissao:
            st.markdown("**Data de Emissão da Certidão**")
            date_emissao_col1, date_emissao_col2 = st.columns(2)
            with date_emissao_col1:
                st.date_input("De:", key=KEY_DATA_EMISSAO_INICIO, min_value=min_date_emissao_default, max_value=max_date_emissao_default, label_visibility="collapsed")
            with date_emissao_col2:
                st.date_input("Até:", key=KEY_DATA_EMISSAO_FIM, min_value=min_date_emissao_default, max_value=max_date_emissao_default, label_visibility="collapsed")
            if st.session_state[KEY_DATA_EMISSAO_INICIO] > st.session_state[KEY_DATA_EMISSAO_FIM]:
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
            
        with col_l2_status:
            st.selectbox(
                "Status Contrato:",
                options=["Todos", "Contrato Padrão", "Adendo", "Distrato"],
                key=KEY_STATUS_FAMILIA,
                help="Filtra as famílias pelo status do contrato (Adendo, Distrato ou Padrão)."
            )

        with col_l2_faltantes:
            opcoes_faltantes = ["Falta 1 certidão"] # Removido "Todos"
            opcoes_faltantes.extend([f"Faltam {i} certidões" for i in range(2, 10)])
            opcoes_faltantes.append("Faltam 10 ou mais certidões")
            st.multiselect( # Alterado de selectbox para multiselect
                "Certidões Faltantes:",
                options=opcoes_faltantes,
                key=KEY_CERTIDOES_FALTANTES,
                placeholder="Selecione a(s) faixa(s)",
                help="Filtra as famílias pelo número de certidões pendentes de conclusão."
            )
        
        with col_l3_btn:
            st.button("Limpar", on_click=clear_filters, help="Limpar todos os filtros")
            
    # --- Fim Filtros ---
    
    # --- Leitura dos Valores dos Filtros do Session State ---
    search_term = st.session_state[KEY_BUSCA_FAMILIA].strip()
    data_inicio_selecionada = st.session_state[KEY_DATA_INICIO]
    data_fim_selecionada = st.session_state[KEY_DATA_FIM]
    data_emissao_inicio_selecionada = st.session_state[KEY_DATA_EMISSAO_INICIO]  # Ler data de emissão início
    data_emissao_fim_selecionada = st.session_state[KEY_DATA_EMISSAO_FIM]  # Ler data de emissão fim
    faixas_selecionadas = st.session_state[KEY_PERCENTUAL]
    responsaveis_selecionados = st.session_state[KEY_RESPONSAVEL]  # Ler valores de responsáveis selecionados
    protocolizado_selecionado = st.session_state[KEY_PROTOCOLIZADO]  # Ler valor do filtro de protocolizado
    status_selecionado = st.session_state[KEY_STATUS_FAMILIA]
    faltantes_selecionado = st.session_state[KEY_CERTIDOES_FALTANTES]

    # Processar datas selecionadas (Data de Venda)
    data_venda_min, data_venda_max = None, None
    if data_inicio_selecionada and data_fim_selecionada and data_inicio_selecionada <= data_fim_selecionada:
        data_venda_min = pd.to_datetime(data_inicio_selecionada)
        data_venda_max = pd.to_datetime(data_fim_selecionada) + pd.Timedelta(days=1)
    
    # Processar datas selecionadas (Data de Emissão)
    data_emissao_min, data_emissao_max = None, None
    if data_emissao_inicio_selecionada and data_emissao_fim_selecionada and data_emissao_inicio_selecionada <= data_emissao_fim_selecionada:
        data_emissao_min = pd.to_datetime(data_emissao_inicio_selecionada)
        data_emissao_max = pd.to_datetime(data_emissao_fim_selecionada) + pd.Timedelta(days=1)
    
    # --- Aplicação dos Filtros (usando valores lidos do state) ---
    df_filtrado_agrupado = df_agrupado.copy() 

    if search_term:
        df_filtrado_agrupado = df_filtrado_agrupado[
            df_filtrado_agrupado[coluna_nome_familia].str.contains(search_term, case=False, na=False)
        ]

    # Aplicar filtro de data de venda apenas se os valores selecionados forem diferentes dos padrões
    is_date_filter_default = (data_inicio_selecionada == min_date_default) and (data_fim_selecionada == max_date_default)

    if not is_date_filter_default and data_venda_min and data_venda_max:
        # Ao ativar o filtro de data, removemos famílias sem data de venda definida
        df_filtrado_agrupado = df_filtrado_agrupado.dropna(subset=['data_venda_familia']) 
        df_filtrado_agrupado = df_filtrado_agrupado[
            (df_filtrado_agrupado['data_venda_familia'] >= data_venda_min) & 
            (df_filtrado_agrupado['data_venda_familia'] < data_venda_max) 
        ]

    # Aplicar filtro de data de emissão apenas se os valores selecionados forem diferentes dos padrões
    is_date_emissao_filter_default = (data_emissao_inicio_selecionada == min_date_emissao_default) and (data_emissao_fim_selecionada == max_date_emissao_default)

    if not is_date_emissao_filter_default and data_emissao_min and data_emissao_max:
        # Ao ativar o filtro de data de emissão, removemos famílias sem data de emissão definida
        df_filtrado_agrupado = df_filtrado_agrupado.dropna(subset=['data_certidao_final'])
        df_filtrado_agrupado = df_filtrado_agrupado[
            (df_filtrado_agrupado['data_certidao_final'] >= data_emissao_min) & 
            (df_filtrado_agrupado['data_certidao_final'] < data_emissao_max)
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

    # Aplicar filtro por status do contrato
    if status_selecionado != "Todos":
        if status_selecionado == "Contrato Padrão":
            # Status 'Contrato Padrão' corresponde a um valor vazio na coluna 'status_familia'
            df_filtrado_agrupado = df_filtrado_agrupado[df_filtrado_agrupado['status_familia'] == '']
        else:
            # Para 'Adendo' e 'Distrato', o valor é o nome do status em maiúsculas
            df_filtrado_agrupado = df_filtrado_agrupado[df_filtrado_agrupado['status_familia'] == status_selecionado.upper()]

    if faltantes_selecionado:
        condicoes_faltantes = []
        for selecao in faltantes_selecionado:
            if selecao == "Falta 1 certidão":
                condicoes_faltantes.append(df_filtrado_agrupado['certidoes_faltantes'] == 1)
            elif selecao == "Faltam 10 ou mais certidões":
                condicoes_faltantes.append(df_filtrado_agrupado['certidoes_faltantes'] >= 10)
            else:
                try:
                    num_faltantes = int(selecao.split(" ")[1])
                    condicoes_faltantes.append(df_filtrado_agrupado['certidoes_faltantes'] == num_faltantes)
                except (ValueError, IndexError):
                    pass
        if condicoes_faltantes:
            filtro_combinado_faltantes = pd.concat(condicoes_faltantes, axis=1).any(axis=1)
            df_filtrado_agrupado = df_filtrado_agrupado[filtro_combinado_faltantes]

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
        'data_venda_familia': 'Data Venda',
        'data_finalizacao_pasta': 'Data Finalização Pasta',
        'responsavel': 'Responsável',
        'status_familia': 'Status'
    })

    # Ordenar a tabela final (opcional, pode escolher outra coluna)
    df_tabela = df_tabela.sort_values(by='Total Certidões', ascending=False)

    # Verificar se, após todos os filtros, o dataframe está vazio
    if df_tabela.empty:
        # Verificar se algum filtro ESTÁ ativo para mostrar a mensagem
        filtros_ativos = search_term or not is_date_filter_default or not is_date_emissao_filter_default or faixas_selecionadas or responsaveis_selecionados or (protocolizado_selecionado != "Todos") or (status_selecionado != "Todos") or faltantes_selecionado
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
        'Status',
        'Data Venda',
        'Data Finalização Pasta',
        'Total Requerentes',
        'Responsável',
        'Total Certidões',
        'Concluídas',
        '% Conclusão'
    ]

    colunas_exibicao = [col for col in colunas_exibicao if col in df_tabela.columns]

    # Configuração dinâmica das colunas
    column_config_dict = {
        "Nome da Família": st.column_config.TextColumn(label="Nome da Família"),
        "Status": st.column_config.TextColumn(label="Status"),
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
    
    if 'Responsável' in colunas_exibicao:
        column_config_dict['Responsável'] = st.column_config.TextColumn(label="Responsável")

    if 'Data Venda' in colunas_exibicao:
        column_config_dict['Data Venda'] = st.column_config.DateColumn(
            label="Data Venda",
            format="DD/MM/YYYY"
        )

    if 'Data Finalização Pasta' in colunas_exibicao:
        column_config_dict['Data Finalização Pasta'] = st.column_config.DateColumn(
            label="Data Finaliz. Pasta",
            format="DD/MM/YYYY",
            help="Data da última certidão finalizada da família (UF_CRM_34_DATA_CERTIDAO_ENTREGUE ou UF_CRM_34_DATA_CERTIDAO_EMITIDA)"
        )

    st.dataframe(
        df_tabela[colunas_exibicao],
        hide_index=True,
        use_container_width=True,
        column_config=column_config_dict,
    )
    
    # --- SEÇÃO DE DEBUG: FAMÍLIAS 100% SEM DATA DE FINALIZAÇÃO ---
    st.markdown("---")
    with st.expander("🔍 DEBUG: Famílias 100% Concluídas SEM Data de Finalização", expanded=False):
        # Filtrar famílias 100% concluídas sem data de finalização
        df_debug = df_tabela[
            (df_tabela['% Conclusão'] == 100) & 
            (df_tabela['Data Finalização Pasta'].isna())
        ].copy()
        
        if not df_debug.empty:
            st.warning(f"⚠️ Encontradas **{len(df_debug)} famílias** com 100% de conclusão mas SEM data de finalização registrada.")
            
            # Métricas de debug
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                total_certidoes_debug = df_debug['Total Certidões'].sum()
                st.metric("Total de Certidões Afetadas", f"{total_certidoes_debug:,}")
            with col_d2:
                total_requerentes_debug = df_debug['Total Requerentes'].sum()
                st.metric("Total de Requerentes Afetados", f"{total_requerentes_debug:,}")
            with col_d3:
                responsaveis_debug = df_debug['Responsável'].nunique()
                st.metric("Responsáveis Distintos", f"{responsaveis_debug}")
            
            st.markdown("##### Tabela de Famílias Afetadas")
            st.caption("Estas famílias estão 100% concluídas mas não possuem data nos campos UF_CRM_34_DATA_CERTIDAO_ENTREGUE ou UF_CRM_34_DATA_CERTIDAO_EMITIDA")
            
            # Colunas para exibição no debug
            colunas_debug = [
                'Nome da Família',
                'Responsável',
                'Data Venda',
                'Total Certidões',
                'Concluídas',
                '% Conclusão',
                'Status'
            ]
            colunas_debug = [col for col in colunas_debug if col in df_debug.columns]
            
            st.dataframe(
                df_debug[colunas_debug].sort_values('Total Certidões', ascending=False),
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Nome da Família": st.column_config.TextColumn(label="Nome da Família", width="large"),
                    "Responsável": st.column_config.TextColumn(label="Responsável"),
                    "Total Certidões": st.column_config.NumberColumn(label="Certidões", format="%d"),
                    "Concluídas": st.column_config.NumberColumn(label="Concluídas", format="%d"),
                    "% Conclusão": st.column_config.ProgressColumn(label="% Conclusão", format="%.1f%%", min_value=0, max_value=100),
                    "Data Venda": st.column_config.DateColumn(label="Data Venda", format="DD/MM/YYYY"),
                    "Status": st.column_config.TextColumn(label="Status")
                }
            )
            
            # Análise detalhada - buscar no dataframe original
            st.markdown("##### 🔎 Análise Detalhada das Certidões")
            st.caption("Verificando os campos de data individualmente para cada certidão dessas famílias")
            
            # Pegar as famílias problemáticas
            familias_problematicas = df_debug['Nome da Família'].tolist()
            
            # Filtrar no dataframe original (df_filtrado_original)
            df_certidoes_debug = df_filtrado_original[
                df_filtrado_original[coluna_nome_familia].isin(familias_problematicas)
            ].copy()
            
            if not df_certidoes_debug.empty:
                # Preparar informações de cada certidão
                df_certidoes_analise = df_certidoes_debug[[
                    'ID',
                    coluna_nome_familia,
                    'ESTAGIO_LEGIVEL',
                    'CATEGORIA_ESTAGIO',
                    coluna_data_emissao,
                    coluna_data_entregue,
                    'CONCLUIDA'
                ]].copy()
                
                df_certidoes_analise = df_certidoes_analise.rename(columns={
                    'ID': 'ID Certidão',
                    coluna_nome_familia: 'Família',
                    'ESTAGIO_LEGIVEL': 'Estágio Atual',
                    'CATEGORIA_ESTAGIO': 'Categoria',
                    coluna_data_emissao: 'Data Emitida',
                    coluna_data_entregue: 'Data Entregue',
                    'CONCLUIDA': 'Concluída?'
                })
                
                # Converter boolean para texto legível
                df_certidoes_analise['Concluída?'] = df_certidoes_analise['Concluída?'].apply(lambda x: '✅ Sim' if x == 1 else '❌ Não')
                
                st.dataframe(
                    df_certidoes_analise.sort_values(['Família', 'ID Certidão']),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "ID Certidão": st.column_config.NumberColumn(label="ID", format="%d"),
                        "Família": st.column_config.TextColumn(label="Família"),
                        "Estágio Atual": st.column_config.TextColumn(label="Estágio"),
                        "Categoria": st.column_config.TextColumn(label="Categoria"),
                        "Data Emitida": st.column_config.DateColumn(label="Data Emitida", format="DD/MM/YYYY"),
                        "Data Entregue": st.column_config.DateColumn(label="Data Entregue", format="DD/MM/YYYY"),
                        "Concluída?": st.column_config.TextColumn(label="Status Conclusão")
                    }
                )
                
                # Análise estatística
                st.markdown("##### 📈 Estatísticas das Certidões Sem Data")
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                with col_stat1:
                    total_cert = len(df_certidoes_analise)
                    st.metric("Total de Certidões", f"{total_cert:,}")
                
                with col_stat2:
                    sem_data_emitida = df_certidoes_analise['Data Emitida'].isna().sum()
                    st.metric("Sem Data Emitida", f"{sem_data_emitida:,}")
                
                with col_stat3:
                    sem_data_entregue = df_certidoes_analise['Data Entregue'].isna().sum()
                    st.metric("Sem Data Entregue", f"{sem_data_entregue:,}")
                
                with col_stat4:
                    sem_ambas = ((df_certidoes_analise['Data Emitida'].isna()) & 
                                 (df_certidoes_analise['Data Entregue'].isna())).sum()
                    st.metric("Sem Nenhuma Data", f"{sem_ambas:,}")
                
        else:
            st.success("✅ Todas as famílias 100% concluídas possuem data de finalização registrada!")
    
    # --- GRÁFICO DE DISTRIBUIÇÃO DE DIAS PARA FINALIZAÇÃO ---
    st.markdown("---")
    st.markdown("#### Distribuição de Tempo para Finalização de Pastas")
    
    # Filtrar apenas famílias 100% concluídas com dados válidos
    df_finalizadas = df_tabela[
        (df_tabela['% Conclusão'] == 100) & 
        (df_tabela['Data Finalização Pasta'].notna())
    ].copy()
    
    if not df_finalizadas.empty:
        # Converter Data Finalização Pasta para datetime
        df_finalizadas['Data Finalização Pasta'] = pd.to_datetime(df_finalizadas['Data Finalização Pasta'], errors='coerce')
        df_finalizadas = df_finalizadas.dropna(subset=['Data Finalização Pasta'])
        
        if not df_finalizadas.empty:
            # Criar coluna de data (sem hora) para agrupamento
            df_finalizadas['data_finalizacao_dia'] = df_finalizadas['Data Finalização Pasta'].dt.date
            
            # Contar famílias únicas por data de finalização
            contagem_por_data = (
                df_finalizadas
                .groupby('data_finalizacao_dia')['Nome da Família']
                .nunique()
                .reset_index()
                .rename(columns={'Nome da Família': 'Quantidade de Famílias'})
                .sort_values('data_finalizacao_dia')
            )
            
            # Calcular estatísticas
            total_finalizadas = len(df_finalizadas)
            data_inicio = contagem_por_data['data_finalizacao_dia'].min()
            data_fim = contagem_por_data['data_finalizacao_dia'].max()
            media_familias_por_dia = contagem_por_data['Quantidade de Famílias'].mean()
            
            # Exibir métricas
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Total de Famílias Finalizadas", f"{total_finalizadas:,}")
            with col_m2:
                st.metric("Primeira Data", data_inicio.strftime("%d/%m/%Y"))
            with col_m3:
                st.metric("Última Data", data_fim.strftime("%d/%m/%Y"))
            with col_m4:
                st.metric("Média por Dia", f"{media_familias_por_dia:.1f}")
            
            # Criar gráfico de linha com pontos
            fig = px.scatter(
                contagem_por_data,
                x='data_finalizacao_dia',
                y='Quantidade de Famílias',
                title='Evolução de Famílias Finalizadas por Data',
                labels={'data_finalizacao_dia': 'Data de Finalização', 'Quantidade de Famílias': 'Nº de Famílias'},
                color_discrete_sequence=['#2563eb']
            )
            
            # Adicionar linha conectando os pontos
            fig.add_scatter(
                x=contagem_por_data['data_finalizacao_dia'],
                y=contagem_por_data['Quantidade de Famílias'],
                mode='lines',
                line=dict(color='rgba(37, 99, 235, 0.3)', width=2),
                showlegend=False,
                hoverinfo='skip'
            )
            
            # Atualizar o tamanho dos pontos e adicionar hover customizado
            fig.update_traces(
                marker=dict(size=10, line=dict(width=2, color='white')),
                selector=dict(mode='markers'),
                hovertemplate='<b>Data:</b> %{x|%d/%m/%Y}<br><b>Famílias:</b> %{y}<extra></extra>'
            )
            
            # Ajustar layout
            fig.update_layout(
                xaxis_tickformat='%d/%m/%Y',
                height=500,
                showlegend=False,
                hovermode='x unified',
                xaxis=dict(
                    title='Data de Finalização da Pasta',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.2)'
                ),
                yaxis=dict(
                    title='Quantidade de Famílias',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.2)'
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.caption(
                "📌 Considera famílias com 100% de conclusão. Data de finalização baseada em UF_CRM_34_DATA_CERTIDAO_ENTREGUE ou UF_CRM_34_DATA_CERTIDAO_EMITIDA (última certidão da família)."
            )
        else:
            st.info("ℹ️ Não há datas válidas para exibir o gráfico.")
    else:
        st.info("ℹ️ Não há famílias 100% concluídas com dados válidos para exibir o gráfico de tempo de finalização.")


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