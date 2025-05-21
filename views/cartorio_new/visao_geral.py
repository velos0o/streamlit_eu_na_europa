import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date # Adicionado datetime e date
import os # Importar os para manipulação de caminhos

# Importar funções do novo utils
from .utils import simplificar_nome_estagio, categorizar_estagio

# Obter o diretório do arquivo atual
_VISAO_GERAL_DIR = os.path.dirname(os.path.abspath(__file__))
# Construir o caminho para a pasta assets subindo dois níveis (views/cartorio_new -> streamlit_eu_na_europa)
_ASSETS_DIR = os.path.join(_VISAO_GERAL_DIR, '..', '..', 'assets')
_CSS_PATH = os.path.join(_ASSETS_DIR, 'styles', 'css', 'main.css')

def exibir_visao_geral(df_original):
    """
    Exibe a seção Visão Geral com filtro de cartório, filtro de data, métricas e estágios categorizados.
    Utiliza CSS INJETADO para estilização específica das métricas.
    """
    # --- CSS Injetado para Métricas ---
    # REMOVER TODO ESTE BLOCO st.markdown("""...""", unsafe_allow_html=True)
    # st.markdown(""" ... """, unsafe_allow_html=True)
    # --- Fim CSS Injetado ---

    # Carregar CSS compilado externo (MANTER OU AJUSTAR ESTA PARTE)
    try:
        # Usar o caminho absoluto calculado
        print(f"[Debug Visão Geral] Tentando carregar CSS de: {_CSS_PATH}")
        if os.path.exists(_CSS_PATH):
            with open(_CSS_PATH, 'r', encoding='utf-8') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
                print("[Debug Visão Geral] CSS carregado com sucesso.")
        else:
             st.warning(f"Arquivo CSS principal não encontrado em: {_CSS_PATH}")
             print(f"[Debug Visão Geral] Falha ao carregar CSS: Arquivo não existe em {_CSS_PATH}")
    except FileNotFoundError:
        # Esta exceção pode não ser mais necessária com a verificação os.path.exists
        st.warning(f"Erro ao tentar abrir o arquivo CSS principal (main.css) em {_CSS_PATH}.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar o CSS: {e}")

    # Título já está em cartorio_new_main.py, podemos remover ou manter se fizer sentido aqui
    # st.markdown('<div class="section-title fade-in">Visão Geral dos Estágios</div>', unsafe_allow_html=True)

    if df_original.empty:
        st.warning("Não há dados disponíveis para exibir a visão geral dos estágios.")
        return

    # --- Definição Nomes Colunas --- 
    coluna_cartorio = 'NOME_CARTORIO' 
    coluna_data = 'CREATED_TIME'
    coluna_nome_familia = 'UF_CRM_34_NOME_FAMILIA' # ATUALIZADO para o novo campo SPA
    
    # --- Verificação Colunas Essenciais --- 
    if coluna_cartorio not in df_original.columns:
        st.error(f"Erro: A coluna '{coluna_cartorio}' não foi encontrada no DataFrame. Verifique o nome da coluna.")
        st.caption(f"Colunas disponíveis: {list(df_original.columns)}")
        return

    # --- Define default values before expander --- 
    cartorios_selecionados = None
    termo_busca_familia_widget = ""
    aplicar_filtro_data = False
    data_inicio = None
    data_fim = None
    filtro_familia_habilitado = False # Default this too

    # --- Expander para Filtros --- 
    with st.expander("Filtros", expanded=True):
        # Linha 1: Cartório e Família
        col_f1_cartorio, col_f1_familia = st.columns([0.6, 0.4])

        with col_f1_cartorio:
            # --- Filtro de Cartório --- 
            lista_cartorios_original = sorted(df_original[coluna_cartorio].unique())
            cartorios_selecionados = st.multiselect(
                "Cartórios:",
                options=lista_cartorios_original,
                default=lista_cartorios_original,
                key="filtro_cartorio_visao_geral"
            )

        with col_f1_familia:
            # --- Filtro Família --- 
            filtro_familia_habilitado = coluna_nome_familia in df_original.columns
            if not filtro_familia_habilitado:
                st.caption(f":warning: Coluna '{coluna_nome_familia}' não encontrada.")
            termo_busca_familia_widget = st.text_input(
                "Buscar Família/Contrato:",
                key="busca_familia_visao_geral_widget",
                placeholder="Nome...",
                disabled=not filtro_familia_habilitado
            )

            # --- Sugestões para Busca de Família --- 
            sugestoes_familia = []
            termo_digitado_familia = termo_busca_familia_widget.strip()
            if termo_digitado_familia and filtro_familia_habilitado:
                nomes_unicos_familia = df_original[coluna_nome_familia].fillna('Desconhecido').astype(str).unique()
                sugestoes_familia = [ 
                    nome for nome in nomes_unicos_familia 
                    if termo_digitado_familia.lower() in nome.lower()
                ][:5] # Limitar a 5 sugestões
                
                if sugestoes_familia:
                    st.caption("Sugestões: " + ", ".join(sugestoes_familia))
                elif len(termo_digitado_familia) > 1: 
                    st.caption("Nenhuma família/contrato encontrado.")

        # Linha 2: Filtro de Data
        col_data1, col_data2, col_data3 = st.columns([0.3, 0.35, 0.35])
        with col_data1:
            aplicar_filtro_data = st.checkbox("Data Criação", value=False, key="aplicar_filtro_data_visao")

        datas_validas = pd.Series(dtype='datetime64[ns]')
        min_date = date.today()
        max_date = date.today()

        if coluna_data not in df_original.columns:
            with col_data1:
                st.caption(f":warning: Coluna '{coluna_data}' não encontrada.")
            aplicar_filtro_data = False
        else:
            df_original[coluna_data] = pd.to_datetime(df_original[coluna_data], errors='coerce')
            # Calcular min/max APENAS se filtro for aplicado e coluna existe
            # datas_validas = df[coluna_data].dropna() # Mover para dentro do if

        data_inicio = None
        data_fim = None
        if aplicar_filtro_data and coluna_data in df_original.columns:
            datas_validas = df_original[coluna_data].dropna()
            if not datas_validas.empty:
                min_date = datas_validas.min().date()
                max_date = datas_validas.max().date()
            
            with col_data2:
                data_inicio = st.date_input("De:", value=min_date, min_value=min_date, max_value=max_date, key="data_inicio_visao_geral", label_visibility="collapsed")
            with col_data3:
                data_fim = st.date_input("Até:", value=max_date, min_value=min_date, max_value=max_date, key="data_fim_visao_geral", label_visibility="collapsed")


    # --- Aplicação dos Filtros --- 
    # Filtro Cartório (aplicado primeiro)
    if cartorios_selecionados is None: # Check if widget was rendered
        st.error("Erro interno: Filtro de cartório não foi inicializado.")
        st.stop()

    if cartorios_selecionados:
         df = df_original[df_original[coluna_cartorio].isin(cartorios_selecionados)].copy()
    else:
        st.warning("Selecione pelo menos um cartório para visualizar os dados.")
        st.stop()

    # Filtro Família
    termo_familia = termo_busca_familia_widget.strip()
    if termo_familia and filtro_familia_habilitado:
        # Ensure the column exists before using .str accessor
        if coluna_nome_familia in df.columns:
            df[coluna_nome_familia] = df[coluna_nome_familia].fillna('Desconhecido').astype(str)
            df = df[df[coluna_nome_familia].str.contains(termo_familia, case=False, na=False)]
        else:
            # This case should ideally not happen due to the check before, but safety first
            st.warning(f"Coluna {coluna_nome_familia} não encontrada ao aplicar filtro de família.")

    # Filtro Data (se ativo)
    if aplicar_filtro_data and data_inicio and data_fim:
        # Ensure the column exists
        if coluna_data in df.columns:
            start_datetime = pd.to_datetime(data_inicio)
            end_datetime = pd.to_datetime(data_fim) + pd.Timedelta(days=1)
            df = df[
                (df[coluna_data].notna()) &
                (df[coluna_data] >= start_datetime) &
                (df[coluna_data] < end_datetime)
            ].copy()
        else:
            st.warning(f"Coluna {coluna_data} não encontrada ao aplicar filtro de data.")

    # --- Checagens após filtros combinados ---
    if df.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
        st.stop() # Interrompe se o DataFrame final estiver vazio


    # --- Métricas (Calculadas sobre o df FINALMENTE FILTRADO) ---
    total_selecionados = len(df) # Recalcula o total com base no df filtrado por cartório E data

    # !!! CORREÇÃO: Calcular métricas usando CATEGORY_ID do df FINALMENTE FILTRADO !!!
    if 'CATEGORY_ID' not in df.columns:
        st.error("Erro crítico: Coluna 'CATEGORY_ID' não encontrada no DataFrame filtrado!")
        total_casa_verde = 0
        total_tatuape = 0
    else:
        # Contar diretamente os IDs 92 e 94 na coluna CATEGORY_ID do df filtrado
        total_casa_verde = (df['CATEGORY_ID'] == 92).sum() # ATUALIZADO para novo ID
        total_tatuape = (df['CATEGORY_ID'] == 94).sum()  # ATUALIZADO para novo ID
            
    # Remover loop anterior
    # total_casa_verde = 0
    # total_tatuape = 0
    # target_casa_verde = 'CARTÓRIO CASA VERDE'
    # target_tatuape = 'CARTÓRIO TATUAPÉ'
    # for index_val, count in contagem_cartorios_filtrados.items():
    #     cleaned_index_val = str(index_val).strip() # Limpa espaços da chave atual
    #     if cleaned_index_val == target_casa_verde:
    #         total_casa_verde = count
    #     elif cleaned_index_val == target_tatuape:
    #         total_tatuape = count

    st.markdown("#### Métricas por Cartório")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Total Selecionado", f"{total_selecionados:,}")
    with col_m2:
        st.metric("Total Casa Verde", f"{total_casa_verde:,}")
    with col_m3:
        st.metric("Total Tatuapé", f"{total_tatuape:,}")
    st.markdown("---")
    
    # --- Processamento e Categorização (no df FINALMENTE FILTRADO) ---
    # Certifique-se que as colunas necessárias para categorização existem
    stage_col = None
    if 'STAGE_ID' in df.columns:
        stage_col = 'STAGE_ID'
    elif 'STAGE_NAME' in df.columns:
        stage_col = 'STAGE_NAME'
    else:
        st.error("Coluna de estágio ('STAGE_ID' ou 'STAGE_NAME') não encontrada nos dados filtrados.")
        return

    df[stage_col] = df[stage_col].astype(str)
    df['STAGE_NAME_LEGIVEL'] = df[stage_col].apply(simplificar_nome_estagio)
    df['CATEGORIA'] = df['STAGE_NAME_LEGIVEL'].apply(categorizar_estagio)

    # --- Cálculos e Visualização de Estágios (usando o df FINALMENTE FILTRADO) ---
    st.markdown("#### Detalhamento por Estágio") # Subheader

    # Contar processos por estágio no DataFrame FINALMENTE filtrado
    contagem_por_estagio = df.groupby('STAGE_NAME_LEGIVEL').size().reset_index(name='QUANTIDADE')

    # Recalcular percentual com base no total_selecionados (já filtrado)
    if total_selecionados == 0:
        # Esta condição já foi verificada e interrompida acima, mas mantemos por segurança
        st.info("Nenhum processo encontrado nos dados filtrados.")
        return

    contagem_por_estagio['PERCENTUAL'] = (contagem_por_estagio['QUANTIDADE'] / total_selecionados * 100).round(1)

    # Categorizar estágios (já feito acima para métrica de sucesso)
    # contagem_por_estagio['CATEGORIA'] = contagem_por_estagio['STAGE_NAME_LEGIVEL'].apply(categorizar_estagio)
    # Reutiliza a coluna 'CATEGORIA' do df ou recalcula no contagem_por_estagio se necessário:
    mapa_categorias = df[['STAGE_NAME_LEGIVEL', 'CATEGORIA']].drop_duplicates().set_index('STAGE_NAME_LEGIVEL')['CATEGORIA']
    contagem_por_estagio['CATEGORIA'] = contagem_por_estagio['STAGE_NAME_LEGIVEL'].map(mapa_categorias)

    # Ordenar por categoria e quantidade
    contagem_por_estagio['ORDEM_CATEGORIA'] = contagem_por_estagio['CATEGORIA'].map({
        'SUCESSO': 1,
        'EM ANDAMENTO': 2,
        'FALHA': 3,
        'DESCONHECIDO': 4 # Garante que desconhecido vá para o fim
    }).fillna(4)

    contagem_por_estagio = contagem_por_estagio.sort_values(
        ['ORDEM_CATEGORIA', 'QUANTIDADE'],
        ascending=[True, False]
    )

    # Separar por categoria
    estagios_sucesso = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'SUCESSO']
    estagios_andamento = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'EM ANDAMENTO']
    estagios_falha = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'FALHA']

    # --- Calcula totais e percentuais ANTES de chamar a renderização --- 
    contagem_por_categoria = df['CATEGORIA'].value_counts()
    total_categorias_validas = contagem_por_categoria.drop('DESCONHECIDO', errors='ignore').sum()
    sucesso_count = contagem_por_categoria.get('SUCESSO', 0)
    andamento_count = contagem_por_categoria.get('EM ANDAMENTO', 0)
    falha_count = contagem_por_categoria.get('FALHA', 0)
    sucesso_perc = (sucesso_count / total_categorias_validas * 100) if total_categorias_validas > 0 else 0
    andamento_perc = (andamento_count / total_categorias_validas * 100) if total_categorias_validas > 0 else 0
    falha_perc = (falha_count / total_categorias_validas * 100) if total_categorias_validas > 0 else 0

    # Renderizar categorias lado a lado, passando os totais
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            renderizar_categoria_visao_geral(estagios_sucesso, "SUCESSO", "✅", sucesso_count, sucesso_perc)
        with col2:
            renderizar_categoria_visao_geral(estagios_andamento, "EM ANDAMENTO", "⏳", andamento_count, andamento_perc)
        with col3:
            renderizar_categoria_visao_geral(estagios_falha, "FALHA", "❌", falha_count, falha_perc)

def renderizar_categoria_visao_geral(df_categoria, titulo, icone, total_count, total_perc):
    """Renderiza uma seção de categoria com seu total e estágios."""
    # Renderiza a coluna mesmo que não haja estágios, desde que haja contagem total > 0
    if not df_categoria.empty or total_count > 0:
        # Título da categoria - ajustado para melhor alinhamento dentro da coluna
        st.markdown(f"""
        <div class="category-header" style="margin-bottom: 10px;">
            <h4 class="category-title" style="margin-bottom: 5px;">{icone} {titulo}</h4>
        </div>
        """, unsafe_allow_html=True)

        # --- NOVO: Exibir Métrica Resumo da Categoria (COMO UM CARD) --- 
        # st.metric(label=f"Total {titulo}", value=f"{total_count:,}", delta=f"{total_perc:.1f}%", delta_color="off") # Removido st.metric
        # st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px; border-top: 1px solid #eee;'>", unsafe_allow_html=True) # Removido hr

        # Gerar HTML para o card de resumo - REMOVENDO ESTILOS INLINE
        st.markdown(f"""
        <div class="card-visao-geral card-visao-geral--summary card-visao-geral--{titulo.lower().replace(' ', '-')}">
            <div class="card-visao-geral__title">Total {titulo}</div>
            <div class="card-visao-geral__metrics">
                <span class="card-visao-geral__quantity">{total_count:,}</span>
                <span class="card-visao-geral__percentage">{total_perc:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Grid de cards - agora dentro da coluna, o CSS cuida do layout
        # Exibir apenas se houver dados de estágios
        if not df_categoria.empty:
            st.markdown('<div class="cards-grid">', unsafe_allow_html=True)

            for _, row_data in df_categoria.iterrows():
                # Card com classes BEM - REMOVENDO fade-in duplicado se já estiver no CSS
                # Mantendo modificador de classe baseado no título para estilização específica (ex: cor de borda)
                st.markdown(f"""
                <div class="card-visao-geral card-visao-geral--{titulo.lower().replace(' ', '-')}">
                    <div class="card-visao-geral__title">{row_data['STAGE_NAME_LEGIVEL']}</div>
                    <div class="card-visao-geral__metrics">
                        <span class="card-visao-geral__quantity">{row_data['QUANTIDADE']}</span>
                        <span class="card-visao-geral__percentage">{row_data['PERCENTUAL']:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True) # Fecha cards-grid
        else:
            st.caption(f"Nenhum estágio detalhado em {titulo}.") # Mensagem se não houver cards

# --- Funções Auxiliares (Copiadas e Adaptadas) ---

# As funções simplificar_nome_estagio e categorizar_estagio foram movidas para utils.py
# def simplificar_nome_estagio(nome):
#     """ Simplifica o nome do estágio para exibição. """
#     if pd.isna(nome):
#         return "Desconhecido"
#
#     codigo_estagio = str(nome) # Garante que é string
#
#     # Mapeamento Atualizado com base na descrição do usuário e categorias
#     # Simplificando nomes para serem mais curtos nos cards
#     mapeamento = {
#         # SPA - Type ID 1098 STAGES
#         'DT1098_92:NEW': 'AGUARDANDO CERTIDÃO',
#         'DT1098_94:NEW': 'AGUARDANDO CERTIDÃO',
#         'DT1098_92:UC_P6PYHW': 'PESQUISA - BR',
#         'DT1098_94:UC_4YE2PI': 'PESQUISA - BR',
#         'DT1098_92:PREPARATION': 'BUSCA - CRC',
#         'DT1098_94:PREPARATION': 'BUSCA - CRC',
#         'DT1098_92:UC_XBTHZ7': 'DEVOLUTIVA BUSCA - CRC',
#         'DT1098_94:CLIENT': 'DEVOLUTIVA BUSCA - CRC', # Nota: CLIENT em Tatuapé é Devolutiva Busca CRC
#         'DT1098_92:CLIENT': 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
#         'DT1098_94:UC_IQ4WFA': 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
#         'DT1098_92:UC_ZWO7BI': 'MONTAGEM REQUERIMENTO CARTÓRIO',
#         'DT1098_94:UC_UZHXWF': 'MONTAGEM REQUERIMENTO CARTÓRIO',
#         'DT1098_92:UC_83ZGKS': 'SOLICITAR CARTÓRIO DE ORIGEM',
#         'DT1098_94:UC_DH38EI': 'SOLICITAR CARTÓRIO DE ORIGEM',
#         'DT1098_92:UC_6TECYL': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
#         'DT1098_94:UC_X9UE60': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
#         'DT1098_92:UC_MUJP1P': 'AGUARDANDO CARTÓRIO ORIGEM',
#         'DT1098_94:UC_IXCAA5': 'AGUARDANDO CARTÓRIO ORIGEM',
#         'DT1098_92:UC_EYBGVD': 'DEVOLUÇÃO ADM',
#         'DT1098_94:UC_VS8YKI': 'DEVOLUÇÃO ADM',
#         'DT1098_92:UC_KC335Q': 'DEVOLVIDO REQUERIMENTO',
#         'DT1098_94:UC_M6A09E': 'DEVOLVIDO REQUERIMENTO',
#         'DT1098_92:UC_5LWUTX': 'CERTIDÃO EMITIDA',
#         'DT1098_94:UC_K4JS04': 'CERTIDÃO EMITIDA',
#         'DT1098_92:FAIL': 'SOLICITAÇÃO DUPLICADA',
#         'DT1098_94:FAIL': 'SOLICITAÇÃO DUPLICADA',
#         'DT1098_92:UC_Z24IF7': 'CANCELADO',
#         'DT1098_94:UC_MGTPX0': 'CANCELADO',
#         'DT1098_92:SUCCESS': 'CERTIDÃO ENTREGUE',
#         'DT1098_94:SUCCESS': 'CERTIDÃO ENTREGUE',
#         'DT1098_92:UC_U10R0R': 'CERTIDÃO DISPENSADA', # NOVO
#         'DT1098_94:UC_L3JFKO': 'CERTIDÃO DISPENSADA', # NOVO
#         # Manter mapeamentos genéricos caso algum STAGE_ID venha sem prefixo DT1098_XX:
#         'NEW': 'AGUARDANDO CERTIDÃO',
#         'UC_P6PYHW': 'PESQUISA - BR', # Casa Verde
#         'UC_4YE2PI': 'PESQUISA - BR', # Tatuapé
#         'PREPARATION': 'BUSCA - CRC',
#         'UC_XBTHZ7': 'DEVOLUTIVA BUSCA - CRC', # Casa Verde
#         # 'CLIENT' mapeado para dois nomes diferentes dependendo do cartório, 
#         # o mapeamento direto de 'CLIENT' se torna ambíguo aqui sem mais contexto.
#         # Idealmente, a lógica consideraria o CATEGORY_ID junto com STAGE_ID para desambiguar 'CLIENT'.
#         # Por ora, se 'CLIENT' vier sozinho, pode levar a um nome. Se vier prefixado, será correto.
#         # 'CLIENT': 'DEVOLUTIVA BUSCA - CRC' ou 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
#         'UC_IQ4WFA': 'APENAS ASS. REQ CLIENTE P/MONTAGEM', # Tatuapé
#         'UC_ZWO7BI': 'MONTAGEM REQUERIMENTO CARTÓRIO', # Casa Verde
#         'UC_UZHXWF': 'MONTAGEM REQUERIMENTO CARTÓRIO', # Tatuapé
#         'UC_83ZGKS': 'SOLICITAR CARTÓRIO DE ORIGEM', # Casa Verde
#         'UC_DH38EI': 'SOLICITAR CARTÓRIO DE ORIGEM', # Tatuapé
#         'UC_6TECYL': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE', # Casa Verde
#         'UC_X9UE60': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE', # Tatuapé
#         'UC_MUJP1P': 'AGUARDANDO CARTÓRIO ORIGEM', # Casa Verde
#         'UC_IXCAA5': 'AGUARDANDO CARTÓRIO ORIGEM', # Tatuapé
#         'UC_EYBGVD': 'DEVOLUÇÃO ADM', # Casa Verde
#         'UC_VS8YKI': 'DEVOLUÇÃO ADM', # Tatuapé
#         'UC_KC335Q': 'DEVOLVIDO REQUERIMENTO', # Casa Verde
#         'UC_M6A09E': 'DEVOLVIDO REQUERIMENTO', # Tatuapé
#         'UC_5LWUTX': 'CERTIDÃO EMITIDA', # Casa Verde
#         'UC_K4JS04': 'CERTIDÃO EMITIDA', # Tatuapé
#         'FAIL': 'SOLICITAÇÃO DUPLICADA',
#         'UC_Z24IF7': 'CANCELADO', # Casa Verde
#         'UC_MGTPX0': 'CANCELADO', # Tatuapé
#         'SUCCESS': 'CERTIDÃO ENTREGUE',
#         'UC_U10R0R': 'CERTIDÃO DISPENSADA', # NOVO GENÉRICO
#         'UC_L3JFKO': 'CERTIDÃO DISPENSADA', # NOVO GENÉRICO
#     }
#
#     # Tentar encontrar no mapeamento completo
#     nome_legivel = mapeamento.get(codigo_estagio)
#
#     # Se não encontrou e tem ':', tentar buscar só o código após ':'
#     if nome_legivel is None and ':' in codigo_estagio:
#         apenas_codigo = codigo_estagio.split(':')[-1]
#         nome_legivel = mapeamento.get(apenas_codigo)
#
#     # Se ainda não encontrou, retornar o código original (ou 'Desconhecido')
#     if nome_legivel is None:
#         if ':' in codigo_estagio:
#             # Retorna só o código se não mapeado, para consistência
#             return codigo_estagio.split(':')[-1] 
#         # Retorna o próprio código se não tiver ':' e não for mapeado
#         return codigo_estagio if codigo_estagio else "Desconhecido"
#
#     return nome_legivel
#
# def categorizar_estagio(estagio_legivel):
#     """ Categoriza o estágio simplificado em SUCESSO, EM ANDAMENTO ou FALHA. """
#     # ATUALIZADO com base nos novos nomes de estágio do SPA
#     sucesso = [
#         'CERTIDÃO ENTREGUE',
#         'CERTIDÃO EMITIDA' # Considerado sucesso no contexto de etapas concluídas antes da entrega final
#     ]
#     falha = [
#         'DEVOLUÇÃO ADM',
#         'DEVOLVIDO REQUERIMENTO',
#         'SOLICITAÇÃO DUPLICADA',
#         'CANCELADO',
#         'DEVOLUTIVA BUSCA - CRC', # Se a devolutiva da busca significa que não encontrou, é uma falha de progresso.
#                                  # Se significa que a busca foi devolvida para correção, pode ser 'EM ANDAMENTO'. Precisa confirmar a semântica.
#                                  # Por ora, classificando como FALHA se impede o progresso direto.
#         'CERTIDÃO DISPENSADA', # NOVO - Classificado como FALHA
#     ]
#
#     if estagio_legivel in sucesso:
#         return 'SUCESSO'
#     elif estagio_legivel in falha:
#         return 'FALHA'
#     else:
#         # Considera qualquer outro estágio mapeado como EM ANDAMENTO
#         # Se não for mapeado e não for sucesso/falha, cairá aqui também.
#         # Retorna desconhecido se o estágio legível for "Desconhecido"
#         return 'EM ANDAMENTO' if estagio_legivel != "Desconhecido" else "DESCONHECIDO" 