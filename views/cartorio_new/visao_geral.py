import streamlit as st
import pandas as pd
import plotly.express as px
# Removido import não utilizado de data_loader

def exibir_visao_geral(df_original):
    """
    Exibe a seção Visão Geral com filtro de cartório, métricas e estágios categorizados.
    Utiliza CSS INJETADO para estilização específica das métricas.
    """
    # --- CSS Injetado para Métricas ---
    # REMOVER TODO ESTE BLOCO st.markdown("""...""", unsafe_allow_html=True)
    # st.markdown(""" ... """, unsafe_allow_html=True)
    # --- Fim CSS Injetado ---

    # Carregar CSS compilado externo (MANTER OU AJUSTAR ESTA PARTE)
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")

    # Título já está em cartorio_new_main.py, podemos remover ou manter se fizer sentido aqui
    # st.markdown('<div class="section-title fade-in">Visão Geral dos Estágios</div>', unsafe_allow_html=True)

    if df_original.empty:
        st.warning("Não há dados disponíveis para exibir a visão geral dos estágios.")
        return

    # --- NOVO: Filtro de Cartório ---
    # Substitua 'NOME_CARTORIO' pelo nome correto da coluna se necessário
    coluna_cartorio = 'NOME_CARTORIO' 
    
    if coluna_cartorio not in df_original.columns:
        st.error(f"Erro: A coluna '{coluna_cartorio}' não foi encontrada no DataFrame. Verifique o nome da coluna.")
        st.caption(f"Colunas disponíveis: {list(df_original.columns)}")
        return

    # --- Obter lista de cartórios diretamente dos dados --- 
    # Garante que os valores usados no filtro e nas opções são idênticos
    lista_cartorios_original = sorted(df_original[coluna_cartorio].unique())

    cartorios_selecionados = st.multiselect(
        "Selecione os Cartórios:",
        options=lista_cartorios_original,  # Usar a lista direto dos dados
        default=lista_cartorios_original, # Começa com todos selecionados
        key="filtro_cartorio_visao_geral"
    )

    if not cartorios_selecionados:
        st.warning("Selecione pelo menos um cartório para visualizar os dados.")
        st.write("") 
        return

    # Filtrar DataFrame principal usando os valores selecionados (que vieram dos dados originais)
    df = df_original[df_original[coluna_cartorio].isin(cartorios_selecionados)].copy()

    if df.empty:
        st.info("Nenhum dado encontrado para os cartórios selecionados.")
        return

    # --- DEBUG: Final check of filtered df value_counts ---
    # st.write("--- FINAL DEBUG: Value Counts of Filtered DF ---") # REMOVIDO
    # filtered_counts = df[coluna_cartorio].value_counts()
    # st.dataframe(filtered_counts)
    # st.write(f"Check: Is 'CARTÓRIO TATUAPÉ' in filtered_counts index? {'CARTÓRIO TATUAPÉ' in filtered_counts.index}")
    # st.write("--- END FINAL DEBUG ---") # REMOVIDO
    # --- END DEBUG ---

    # --- Métricas Macro e Sucesso --- 
    total_selecionados = len(df)
    # contagem_cartorios_filtrados = df[coluna_cartorio].value_counts() # Não precisamos mais disso para as métricas específicas

    # !!! CORREÇÃO: Calcular métricas usando CATEGORY_ID do df filtrado !!!
    if 'CATEGORY_ID' not in df.columns:
        st.error("Erro crítico: Coluna 'CATEGORY_ID' não encontrada no DataFrame filtrado!")
        total_casa_verde = 0
        total_tatuape = 0
    else:
        # Contar diretamente os IDs 16 e 34 na coluna CATEGORY_ID do df filtrado
        total_casa_verde = (df['CATEGORY_ID'] == 16).sum()
        total_tatuape = (df['CATEGORY_ID'] == 34).sum()
            
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
    
    # Cálculo de Sucesso (usando a categorização que será feita a seguir)
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
    
    contagem_sucesso = df[df['CATEGORIA'] == 'SUCESSO'].shape[0]
    percentual_sucesso = (contagem_sucesso / total_selecionados * 100) if total_selecionados > 0 else 0
    
    st.metric("Percentual de Conclusão (Sucesso)", f"{percentual_sucesso:.1f}%")
    st.progress(int(percentual_sucesso)) 
    st.markdown("---")
    # --- FIM Métricas ---

    # --- Cálculos e Visualização de Estágios (usando o df filtrado) ---
    st.markdown("#### Detalhamento por Estágio") # Novo subheader

    # Contar processos por estágio no DataFrame filtrado
    contagem_por_estagio = df.groupby('STAGE_NAME_LEGIVEL').size().reset_index(name='QUANTIDADE')

    # Recalcular percentual com base no total filtrado
    # total_processos = len(df) # Já calculado como total_selecionados
    if total_selecionados == 0:
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

    # Renderizar categorias lado a lado
    with st.container(): 
        col1, col2, col3 = st.columns(3)
        with col1:
            renderizar_categoria_visao_geral(estagios_sucesso, "SUCESSO", "✅")
        with col2:
            renderizar_categoria_visao_geral(estagios_andamento, "EM ANDAMENTO", "⏳")
        with col3:
            renderizar_categoria_visao_geral(estagios_falha, "FALHA", "❌")

def renderizar_categoria_visao_geral(df_categoria, titulo, icone):
    """Renderiza uma seção de categoria com seus estágios."""
    if not df_categoria.empty:
        # Título da categoria - ajustado para melhor alinhamento dentro da coluna
        st.markdown(f"""
        <div class="category-header" style="margin-bottom: 10px;">
            <h4 class="category-title" style="margin-bottom: 5px;">{icone} {titulo}</h4>
        </div>
        """, unsafe_allow_html=True)

        # Grid de cards - agora dentro da coluna, o CSS cuida do layout
        st.markdown('<div class="cards-grid">', unsafe_allow_html=True)

        for _, row_data in df_categoria.iterrows():
            # Card com classes BEM e borda vermelha (aplicada via CSS injetado)
            st.markdown(f"""
            <div class="card-visao-geral card-visao-geral--{titulo.lower().replace(' ', '-')} fade-in">
                <div class="card-visao-geral__title">{row_data['STAGE_NAME_LEGIVEL']}</div>
                <div class="card-visao-geral__metrics">
                    <span class="card-visao-geral__quantity">{row_data['QUANTIDADE']}</span>
                    <span class="card-visao-geral__percentage">{row_data['PERCENTUAL']:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True) # Fecha cards-grid

# --- Funções Auxiliares (Copiadas e Adaptadas) ---

def simplificar_nome_estagio(nome):
    """ Simplifica o nome do estágio para exibição. """
    if pd.isna(nome):
        return "Desconhecido"

    codigo_estagio = str(nome) # Garante que é string

    # Mapeamento Atualizado com base na descrição do usuário e categorias
    # Simplificando nomes para serem mais curtos nos cards
    mapeamento = {
        # SUCESSO -> VERDE
        'DT1052_16:SUCCESS': 'Entregue',
        'DT1052_34:SUCCESS': 'Entregue',
        'SUCCESS': 'Entregue',
        'DT1052_16:UC_JRGCW3': 'Física Entregue',
        'DT1052_34:UC_84B1S2': 'Física Entregue',
        'UC_JRGCW3': 'Física Entregue',
        'UC_84B1S2': 'Física Entregue',
        'DT1052_16:CLIENT': 'Emitida (Cliente)',
        'DT1052_34:CLIENT': 'Emitida (Cliente)',
        'DT1052_34:UC_D0RG5P': 'Emitida (Cliente)',
        'CLIENT': 'Emitida (Cliente)',
        'UC_D0RG5P': 'Emitida (Cliente)',

        # EM ANDAMENTO -> Amarelo
        'DT1052_16:UC_7F0WK2': 'Ass. Req. Cliente',
        'DT1052_34:UC_HN9GMI': 'Ass. Req. Cliente',
        'UC_7F0WK2': 'Ass. Req. Cliente',
        'UC_HN9GMI': 'Ass. Req. Cliente',
        'DT1052_16:NEW': 'Aguard. Certidão',
        'DT1052_34:NEW': 'Aguard. Certidão',
        'NEW': 'Aguard. Certidão',
        'DT1052_16:UC_HYO7L2': 'Devolutiva Busca',
        'DT1052_34:UC_5LAJNY': 'Devolutiva Busca',
        'UC_HYO7L2': 'Devolutiva Busca',
        'UC_5LAJNY': 'Devolutiva Busca',
        'DT1052_16:UC_IWZBMO': 'Solic. Cart. Origem',
        'DT1052_34:UC_8L5JUS': 'Solic. Cart. Origem',
        'UC_IWZBMO': 'Solic. Cart. Origem',
        'UC_8L5JUS': 'Solic. Cart. Origem',
        'DT1052_16:UC_KXHDOQ': 'Aguard. Cart. Origem',
        'DT1052_34:UC_6KOYL5': 'Aguard. Cart. Origem',
        'UC_KXHDOQ': 'Aguard. Cart. Origem',
        'UC_6KOYL5': 'Aguard. Cart. Origem',
        'DT1052_16:UC_RJC2DD': 'PRIO2 - Busca CRC',
        'DT1052_34:UC_RJC2DD': 'PRIO2 - Busca CRC',
        'UC_RJC2DD': 'PRIO2 - Busca CRC',
        'K85YX7': 'PRIO2 - Busca CRC', 
        'DT1052_16:PREPARATION': 'Montagem Req.',
        'DT1052_34:PREPARATION': 'Montagem Req.',
        'PREPARATION': 'Montagem Req.',
        'DT1052_16:UC_8EGMU7': 'Cart. Origem Prior.',
        'UC_8EGMU7': 'Cart. Origem Prior.',
        'DT1052_16:UC_QRZ6JG': 'Busca CRC',
        'DT1052_34:UC_68BLQ7': 'Busca CRC',
        'UC_QRZ6JG': 'Busca CRC',
        'UC_68BLQ7': 'Busca CRC',
        'DT1052_16:UC_K85YX7': 'Solic. C. Origem Prior.',
        'DT1052_34:UC_K85YX7': 'Solic. C. Origem Prior.',
        'UC_K85YX7': 'Solic. C. Origem Prior.',

        # FALHA -> VERMELHO
        'DT1052_16:FAIL': 'Devolução ADM',
        'DT1052_34:FAIL': 'Devolução ADM',
        'FAIL': 'Devolução ADM',
        'DT1052_16:UC_R5UEXF': 'Dev. ADM Verif.',
        'DT1052_34:UC_Z3J98J': 'Dev. ADM Verif.',
        'UC_R5UEXF': 'Dev. ADM Verif.',
        'UC_Z3J98J': 'Dev. ADM Verif.',
        'DT1052_16:UC_UG0UDZ': 'Solic. Duplicada',
        'DT1052_34:UC_LF04SU': 'Solic. Duplicada',
        'UC_UG0UDZ': 'Solic. Duplicada',
        'UC_LF04SU': 'Solic. Duplicada',
        'DT1052_16:UC_XM32IE': 'Sem Dados Busca',
        'DT1052_34:UC_XM32IE': 'Sem Dados Busca',
        'UC_XM32IE': 'Sem Dados Busca',
        'DT1052_16:UC_P61ZVH': 'Devolvido Req.',
        'DT1052_34:UC_2BAINE': 'Devolvido Req.',
        'UC_P61ZVH': 'Devolvido Req.',
        'UC_2BAINE': 'Devolvido Req.',
        'DT1052_16:UC_7L6CGJ': 'Cancelado',
        'DT1052_34:UC_7L6CGJ': 'Cancelado',
        'UC_7L6CGJ': 'Cancelado',
        'DT1052_16:UC_3LJ0KG': 'Não Trabalhar',
        'DT1052_34:UC_3LJ0KG': 'Não Trabalhar',
        'UC_3LJ0KG': 'Não Trabalhar',
    }

    # Tentar encontrar no mapeamento completo
    nome_legivel = mapeamento.get(codigo_estagio)

    # Se não encontrou e tem ':', tentar buscar só o código após ':'
    if nome_legivel is None and ':' in codigo_estagio:
        apenas_codigo = codigo_estagio.split(':')[-1]
        nome_legivel = mapeamento.get(apenas_codigo)

    # Se ainda não encontrou, retornar o código original (ou 'Desconhecido')
    if nome_legivel is None:
        if ':' in codigo_estagio:
            # Retorna só o código se não mapeado, para consistência
            return codigo_estagio.split(':')[-1] 
        # Retorna o próprio código se não tiver ':' e não for mapeado
        return codigo_estagio if codigo_estagio else "Desconhecido"

    return nome_legivel

def categorizar_estagio(estagio_legivel):
    """ Categoriza o estágio simplificado em SUCESSO, EM ANDAMENTO ou FALHA. """
    # Listas baseadas nos nomes simplificados e na descrição do usuário
    sucesso = [
        'Entregue', # Simplificado
        'Física Entregue', # Simplificado
        'Emitida (Cliente)' # Simplificado
    ]
    falha = [
        'Devolução ADM',
        'Dev. ADM Verif.', # Simplificado
        'Solic. Duplicada', # Simplificado
        'Sem Dados Busca', # Simplificado
        'Devolvido Req.', # Simplificado
        'Cancelado',
        'Não Trabalhar',
        'Devolutiva Busca' # Nome simplificado correto
    ]

    if estagio_legivel in sucesso:
        return 'SUCESSO'
    elif estagio_legivel in falha:
        return 'FALHA'
    else:
        # Considera qualquer outro estágio mapeado como EM ANDAMENTO
        # Se não for mapeado e não for sucesso/falha, cairá aqui também.
        # Retorna desconhecido se o estágio legível for "Desconhecido"
        return 'EM ANDAMENTO' if estagio_legivel != "Desconhecido" else "DESCONHECIDO" 