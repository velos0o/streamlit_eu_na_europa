import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# Obter o diretório do arquivo atual
_VISAO_GERAL_COMUNE_DIR = os.path.dirname(os.path.abspath(__file__))
# Construir o caminho para a pasta assets subindo dois níveis (views/comune_new -> streamlit_eu_na_europa)
_ASSETS_DIR = os.path.join(_VISAO_GERAL_COMUNE_DIR, '..', '..', 'assets')
_CSS_PATH = os.path.join(_ASSETS_DIR, 'styles', 'css', 'main.css')

def exibir_visao_geral_comune(df_original):
    """
    Exibe a seção Visão Geral para Comune com filtro de data, métricas e estágios categorizados.
    Utiliza o estilo visual de cards definido no CSS principal.
    """
    # Carregar CSS compilado externo
    try:
        if os.path.exists(_CSS_PATH):
            with open(_CSS_PATH, 'r', encoding='utf-8') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        else:
            st.warning(f"Arquivo CSS principal não encontrado em: {_CSS_PATH}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar o CSS: {e}")

    if df_original.empty:
        st.warning("Não há dados disponíveis para exibir a visão geral dos estágios de Comune.")
        return

    # --- Definição Nomes Colunas ---
    coluna_data = 'CREATED_TIME'
    coluna_estagio = 'STAGE_ID'
    coluna_estagio_legivel = 'STAGE_NAME_LEGIVEL' # Nova coluna usada para filtro

    # --- Verificação Colunas Essenciais ---
    colunas_necessarias = [coluna_data, coluna_estagio]
    colunas_ausentes = [col for col in colunas_necessarias if col not in df_original.columns]
    if colunas_ausentes:
        st.error(f"Erro: As seguintes colunas essenciais não foram encontradas: {', '.join(colunas_ausentes)}. Verifique o carregamento dos dados.")
        st.caption(f"Colunas disponíveis: {list(df_original.columns)}")
        return

    # Calcular nomes legíveis dos estágios ANTES dos filtros
    # para que a lista de filtros esteja completa
    if coluna_estagio in df_original.columns:
        df_original[coluna_estagio_legivel] = df_original[coluna_estagio].apply(simplificar_nome_estagio_comune)
    else:
        st.error("Coluna de estágio essencial não encontrada.")
        return

    # --- Define default values before expander ---
    aplicar_filtro_data = False
    data_inicio = None
    data_fim = None
    estagios_selecionados = [] # Inicializar lista vazia para filtro de estágio

    # --- Expander para Filtros ---
    with st.expander("Filtros", expanded=True):
        # Linha 1: Filtro de Data
        col_f1_data_chk, col_f1_data_ini, col_f1_data_fim = st.columns([0.3, 0.35, 0.35])

        with col_f1_data_chk:
            aplicar_filtro_data = st.checkbox("Data Criação", value=False, key="aplicar_filtro_data_comune")

        # Preparar datas apenas se a coluna existir
        min_date = date.today()
        max_date = date.today()
        if coluna_data in df_original.columns:
            df_original[coluna_data] = pd.to_datetime(df_original[coluna_data], errors='coerce')
            datas_validas = df_original[coluna_data].dropna()
            if not datas_validas.empty:
                min_date = datas_validas.min().date()
                max_date = datas_validas.max().date()
            else:
                # Se não houver datas válidas, desabilitar o filtro
                aplicar_filtro_data = False
                with col_f1_data_chk:
                     st.caption("Sem datas válidas.")

        with col_f1_data_ini:
            data_inicio = st.date_input("De:", value=min_date, min_value=min_date, max_value=max_date, key="data_inicio_comune", label_visibility="collapsed", disabled=not aplicar_filtro_data)
        with col_f1_data_fim:
            data_fim = st.date_input("Até:", value=max_date, min_value=min_date, max_value=max_date, key="data_fim_comune", label_visibility="collapsed", disabled=not aplicar_filtro_data)

        # Linha 2: Filtro de Estágio
        st.markdown("#### Filtro por Estágio")
        # Obter a lista única de estágios legíveis do DataFrame original
        lista_estagios_unicos = sorted(df_original[coluna_estagio_legivel].unique())
        
        # Garantir que "Todos" não esteja na lista para evitar duplicação
        if "Todos" in lista_estagios_unicos:
             lista_estagios_unicos.remove("Todos")
             
        # Adicionar opção "Todos" no início (ou deixar o padrão como lista vazia = todos)
        # options_estagios = ["Todos"] + lista_estagios_unicos
        
        estagios_selecionados = st.multiselect(
            "Selecione os estágios para exibir:",
            options=lista_estagios_unicos,
            default=[], # Por padrão, nenhum selecionado (mostra todos)
            key="filtro_estagio_visao_geral",
            help="Se nenhum estágio for selecionado, todos serão exibidos."
        )

    # --- Aplicação dos Filtros ---
    df = df_original.copy()

    # Filtro Data (se ativo)
    if aplicar_filtro_data and data_inicio and data_fim and coluna_data in df.columns:
        try:
            start_datetime = pd.to_datetime(data_inicio)
            # Adicionar 1 dia e subtrair 1 nanossegundo para incluir a data final completa
            end_datetime = pd.to_datetime(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)

            df = df[
                (df[coluna_data].notna()) &
                (df[coluna_data] >= start_datetime) &
                (df[coluna_data] <= end_datetime) # Usar <= agora
            ].copy()
        except Exception as e:
            st.error(f"Erro ao aplicar filtro de data: {e}")
            # Considerar parar ou usar o df sem filtro de data
            df = df_original.copy() # Reverter para original em caso de erro

    # Filtro Estágio (se alguma opção foi selecionada)
    if estagios_selecionados: # Se a lista não estiver vazia
        df = df[df[coluna_estagio_legivel].isin(estagios_selecionados)].copy()
        st.info(f"Filtrando por {len(estagios_selecionados)} estágios selecionados.")

    # --- Checagens após filtros combinados ---
    if df.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
        st.stop()

    # --- Métricas Globais ---
    # Métrica 1: Total carregado (antes dos filtros da tela) - REMOVIDA
    # Métrica 2: Total visível (após filtros da tela)
    total_visivel_filtrado = len(df)

    st.markdown("#### Métricas Gerais")
    col_m1, col_m2, col_m3 = st.columns(3) # Layout para futuras métricas
    with col_m1:
        # Removida a métrica 'Total Geral'
        st.metric("Total Exibido (Filtros Aplicados)", f"{total_visivel_filtrado:,}")
    # with col_m2: # Removido conteúdo de col_m2 que exibia o total filtrado
    #     st.metric("Total Visível (Filtros Aplicados)", f"{total_visivel_filtrado:,}")
    # Adicionar mais métricas relevantes para Comune aqui (col_m2, col_m3)
    st.markdown("---")

    # --- Processamento e Categorização (no df FINALMENTE FILTRADO) ---
    df_processar = df
    if df_processar.empty:
        st.info("Nenhum processo para exibir nos estágios com os filtros aplicados.")
        return

    # As colunas STAGE_NAME_LEGIVEL e CATEGORIA já devem existir se a lógica acima foi executada
    if coluna_estagio_legivel not in df_processar.columns:
         df_processar[coluna_estagio_legivel] = df_processar[coluna_estagio].apply(simplificar_nome_estagio_comune)
    if 'CATEGORIA' not in df_processar.columns:
         df_processar['CATEGORIA'] = df_processar[coluna_estagio].apply(categorizar_estagio_comune)

    # --- Cálculos e Visualização de Estágios ---
    st.markdown("#### Detalhamento por Estágio")

    # Calcular contagem e percentual sobre o TOTAL VISÍVEL FILTRADO
    contagem_por_estagio = df_processar.groupby(['STAGE_NAME_LEGIVEL', 'CATEGORIA', coluna_estagio]).size().reset_index(name='QUANTIDADE')

    if total_visivel_filtrado == 0:
        # Esta checagem é redundante devido à checagem df_processar.empty acima, mas mantém por segurança
        st.info("Nenhum processo encontrado nos dados filtrados.")
        return

    contagem_por_estagio['PERCENTUAL'] = (contagem_por_estagio['QUANTIDADE'] / total_visivel_filtrado * 100).round(1)

    # Ordenar por categoria e quantidade
    contagem_por_estagio['ORDEM_CATEGORIA'] = contagem_por_estagio['CATEGORIA'].map({
        'SUCESSO': 1,
        'EM ANDAMENTO': 2,
        'FALHA': 3,
        'NÃO MAPEADO': 4 # Categoria para não mapeados
    }).fillna(4) # Default para não mapeado

    contagem_por_estagio = contagem_por_estagio.sort_values(
        ['ORDEM_CATEGORIA', 'QUANTIDADE'],
        ascending=[True, False]
    )

    # Separar por categoria
    estagios_sucesso = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'SUCESSO']
    estagios_andamento = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'EM ANDAMENTO']
    estagios_falha = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'FALHA']
    estagios_nao_mapeados = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'NÃO MAPEADO']

    # --- Calcula totais e percentuais ANTES de chamar a renderização ---
    # Usar contagem de categoria do df_processar (filtrado pela tela)
    contagem_por_categoria = df_processar['CATEGORIA'].value_counts()
    total_categorias_validas = contagem_por_categoria.drop('NÃO MAPEADO', errors='ignore').sum() # Exclui não mapeados do % total

    sucesso_count = contagem_por_categoria.get('SUCESSO', 0)
    andamento_count = contagem_por_categoria.get('EM ANDAMENTO', 0)
    falha_count = contagem_por_categoria.get('FALHA', 0)
    nao_mapeado_count = contagem_por_categoria.get('NÃO MAPEADO', 0)

    # Percentuais calculados sobre o total VÁLIDO (excluindo não mapeados)
    sucesso_perc = (sucesso_count / total_categorias_validas * 100) if total_categorias_validas > 0 else 0
    andamento_perc = (andamento_count / total_categorias_validas * 100) if total_categorias_validas > 0 else 0
    falha_perc = (falha_count / total_categorias_validas * 100) if total_categorias_validas > 0 else 0
    # Percentual de não mapeados sobre o TOTAL VISÍVEL FILTRADO
    nao_mapeado_perc = (nao_mapeado_count / total_visivel_filtrado * 100) if total_visivel_filtrado > 0 else 0


    # Renderizar categorias lado a lado (4 colunas)
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            renderizar_categoria_visao_geral_comune(estagios_sucesso, "SUCESSO", "✅", sucesso_count, sucesso_perc, coluna_estagio=coluna_estagio)
        with col2:
            renderizar_categoria_visao_geral_comune(estagios_andamento, "EM ANDAMENTO", "⏳", andamento_count, andamento_perc, coluna_estagio=coluna_estagio)
        with col3:
            renderizar_categoria_visao_geral_comune(estagios_falha, "FALHA", "❌", falha_count, falha_perc, coluna_estagio=coluna_estagio)
        with col4:
            renderizar_categoria_visao_geral_comune(estagios_nao_mapeados, "NÃO MAPEADO", "❓", nao_mapeado_count, nao_mapeado_perc, exibir_id=True, coluna_estagio=coluna_estagio)


def renderizar_categoria_visao_geral_comune(df_categoria, titulo, icone, total_count, total_perc, exibir_id=False, coluna_estagio=None):
    """Renderiza uma seção de categoria com seu total e estágios para Comune."""
    if not df_categoria.empty or total_count > 0:
        # Título da categoria
        st.markdown(f"""
        <div class="category-header" style="margin-bottom: 10px;">
            <h4 class="category-title" style="margin-bottom: 5px;">{icone} {titulo}</h4>
        </div>
        """, unsafe_allow_html=True)

        # Card de Resumo da Categoria
        classe_modificadora = titulo.lower().replace(' ', '-')
        st.markdown(f"""
        <div class="card-visao-geral card-visao-geral--summary card-visao-geral--{classe_modificadora}">
            <div class="card-visao-geral__title">Total {titulo}</div>
            <div class="card-visao-geral__metrics">
                <span class="card-visao-geral__quantity">{total_count:,}</span>
                <span class="card-visao-geral__percentage">{total_perc:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Grid de cards detalhados
        if not df_categoria.empty:
            st.markdown('<div class="cards-grid">', unsafe_allow_html=True)

            for _, row_data in df_categoria.iterrows():
                nome_exibicao = row_data['STAGE_NAME_LEGIVEL']
                # Se for não mapeado, mostra o ID original para facilitar o mapeamento
                if exibir_id and coluna_estagio:
                    nome_exibicao = f"{row_data[coluna_estagio]}" # Mostra o ID original
                
                # Define o title do card com o ID original do estágio, se disponível
                title_html = f"title=\"{row_data.get(coluna_estagio, nome_exibicao)}\"" if coluna_estagio else ""

                st.markdown(f"""
                <div class="card-visao-geral card-visao-geral--{classe_modificadora}">
                    <div class="card-visao-geral__title" {title_html}>{nome_exibicao}</div>
                    <div class="card-visao-geral__metrics">
                        <span class="card-visao-geral__quantity">{row_data['QUANTIDADE']}</span>
                        <span class="card-visao-geral__percentage">{row_data['PERCENTUAL']:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True) # Fecha cards-grid
        # else: # Não precisa de mensagem se o card de resumo já mostra 0
            # st.caption(f"Nenhum estágio detalhado em {titulo}.")


# --- Funções Auxiliares Específicas para Comune ---

_MAPA_ESTAGIOS_COMUNE = {
    # EM ANDAMENTO
    'DT1052_22:UC_2QZ8S2': 'Pendente',
    'DT1052_58:NEW': 'Pendente',
    'DT1052_60:NEW': 'Pendente',
    'DT1052_60:PREPARATION': 'Pesquisa Não Finalizada',
    'DT1052_58:PREPARATION': 'Pesquisa Não Finalizada',
    'DT1052_22:UC_E1VKYT': 'Pesquisa Não Finalizada',
    'DT1052_22:UC_MVS02R': 'Devolutiva Emissor',
    'DT1052_60:CLIENT': 'Devolutiva Emissor', # Nota: CLIENT pode ser ambíguo, verificar se é sempre devolutiva
    'DT1052_60:UC_W9AOG0': 'Solicitar',
    'DT1052_22:NEW': 'Solicitar',
    'DT1052_60:UC_Y90N01': 'Urgente',
    'DT1052_22:UC_4RQBZV': 'Urgente',
    'DT1052_22:PREPARATION': 'Aguardando Comune',
    'DT1052_58:UC_9FSEEV': 'Aguardando Comune',
    'DT1052_60:UC_UWK6T2': 'Aguardando Comune',
    'DT1052_60:UC_GC6Z58': 'Aguardando PDF',
    'DT1052_58:UC_AOUKIF': 'Aguardando PDF',
    'DT1052_22:UC_1RC076': 'Aguardando PDF',
    'DT1052_22:UC_QTUYZS': 'Aguardando Pagamento Taxa',
    'DT1052_22:UC_OESFPO': 'Taxa Paga',
    'DT1052_58:UC_N7QPCD': 'Taxa Paga',
    'DT1052_22:UC_SLFSUP': 'Necessário Requerimento',
    'DT1052_58:UC_9MWW44': 'Necessário Requerimento',
    'DT1052_22:UC_37J9PI': 'Requerimento Concluído',
    'DT1052_58:UC_4I3AQ0': 'Requerimento Concluído',
    'DT1052_22:UC_S4DFU2': 'Aguardando Comune/Paróquia - Tem Info',

    # SUCESSO
    'DT1052_22:CLIENT': 'Entregue PDF', # Nota: Ambiguidade com 'Devolutiva Emissor'
    'DT1052_58:UC_LSRGXS': 'Entregue PDF',
    'DT1052_60:UC_VFSGD9': 'Entregue PDF',
    'DT1052_22:SUCCESS': 'Documento Físico Entregue',
    'DT1052_58:SUCCESS': 'Documento Físico Entregue',
    'DT1052_60:SUCCESS': 'Documento Físico Entregue', # Supondo que 60 também tem SUCCESS

    # FALHA
    'DT1052_60:UC_KH4KP6': 'Negativa Comune',
    'DT1052_58:UC_5V1OH9': 'Negativa Comune',
    'DT1052_22:UC_A9UEMO': 'Negativa Comune',
    'DT1052_58:FAIL': 'Cancelado',
    'DT1052_60:FAIL': 'Cancelado',
    'DT1052_22:FAIL': 'Cancelado',
}

def simplificar_nome_estagio_comune(stage_id):
    """ Simplifica o nome do estágio de Comune usando o mapeamento fornecido. """
    if pd.isna(stage_id):
        return "Desconhecido"
    stage_id_str = str(stage_id)
    return _MAPA_ESTAGIOS_COMUNE.get(stage_id_str, stage_id_str) # Retorna o próprio ID se não mapeado

def categorizar_estagio_comune(stage_id):
    """ Categoriza o STAGE_ID de Comune em SUCESSO, EM ANDAMENTO, FALHA ou NÃO MAPEADO. """
    if pd.isna(stage_id):
        return 'NÃO MAPEADO' # Ou talvez 'Desconhecido' dependendo da regra

    stage_id_str = str(stage_id)

    # Verifica se está no mapeamento
    if stage_id_str not in _MAPA_ESTAGIOS_COMUNE:
        return 'NÃO MAPEADO'

    # Categorias baseadas na sua lista original (verificar ambiguidade de CLIENT)
    sucesso_ids = [
        'DT1052_22:CLIENT', 'DT1052_58:UC_LSRGXS', 'DT1052_60:UC_VFSGD9',
        'DT1052_22:SUCCESS', 'DT1052_58:SUCCESS', 'DT1052_60:SUCCESS' # Adicionado 60:SUCCESS
    ]
    falha_ids = [
        'DT1052_60:UC_KH4KP6', 'DT1052_58:UC_5V1OH9', 'DT1052_22:UC_A9UEMO',
        'DT1052_58:FAIL', 'DT1052_60:FAIL', 'DT1052_22:FAIL'
    ]

    # Atenção à ambiguidade: DT1052_22:CLIENT está em Sucesso (Entregue PDF)
    # e DT1052_60:CLIENT está em Andamento (Devolutiva Emissor).
    # A lógica atual prioriza a categoria definida aqui.
    # Se DT1052_60:CLIENT deve ser 'EM ANDAMENTO', precisa ser tratado diferente.

    if stage_id_str in sucesso_ids:
        return 'SUCESSO'
    elif stage_id_str in falha_ids:
        return 'FALHA'
    else:
        # Todos os outros mapeados são considerados EM ANDAMENTO
        return 'EM ANDAMENTO'

