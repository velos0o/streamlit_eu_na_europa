import streamlit as st
import pandas as pd

# Reutilizar as funções de visao_geral para consistência
from .visao_geral import simplificar_nome_estagio, categorizar_estagio

def exibir_acompanhamento(df_cartorio):
    """
    Exibe a aba de Acompanhamento de Emissões por Família.
    Mostra métricas macro e uma tabela com Totais de Requerentes (contagem única),
    Certidões e Concluídas por Família.
    Aplica estilos via SCSS.
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
    coluna_nome_familia = 'UF_CRM_12_1722882763189'
    coluna_id_requerente = 'UF_CRM_12_1723552729' # ID para contagem
    colunas_requeridas = ['ID', 'STAGE_ID', coluna_nome_familia, coluna_id_requerente]
    colunas_faltantes = [col for col in colunas_requeridas if col not in df_cartorio.columns]

    if colunas_faltantes:
        st.error(f"Erro: As seguintes colunas são necessárias e não foram encontradas: {', '.join(colunas_faltantes)}. Verifique o data_loader e a origem dos dados (Bitrix).")
        st.dataframe(df_cartorio.head())
        return

    # --- Pré-processamento --- 
    df = df_cartorio.copy()

    # 1. Garantir tipo correto para ID Requerente (já feito no loader, mas confirmando)
    df[coluna_id_requerente] = df[coluna_id_requerente].fillna('Req. Desconhecido').astype(str)

    # 2. Simplificar e Categorizar Estágios
    df['STAGE_ID'] = df['STAGE_ID'].astype(str)
    df['ESTAGIO_LEGIVEL'] = df['STAGE_ID'].apply(simplificar_nome_estagio)
    df['CATEGORIA_ESTAGIO'] = df['ESTAGIO_LEGIVEL'].apply(categorizar_estagio)
    df['CONCLUIDA'] = df['CATEGORIA_ESTAGIO'] == 'SUCESSO'

    # 3. Tratar Nulos na coluna Nome da Família (já feito no loader, mas confirmando)
    df[coluna_nome_familia] = df[coluna_nome_familia].fillna('Família Desconhecida').astype(str)
    df[coluna_nome_familia] = df[coluna_nome_familia].replace(r'^\s*$', 'Família Desconhecida', regex=True)

    # --- Cálculos Macro (Reintroduzindo contagem de requerentes) ---
    total_familias_geral = df[df[coluna_nome_familia] != 'Família Desconhecida'][coluna_nome_familia].nunique()
    total_certidoes_geral = len(df)
    # Contar requerentes únicos GERAL
    total_requerentes_geral = df[df[coluna_id_requerente] != 'Req. Desconhecido'][coluna_id_requerente].nunique()
    concluidas_geral = df['CONCLUIDA'].sum()
    percentual_conclusao_geral = (concluidas_geral / total_certidoes_geral * 100) if total_certidoes_geral > 0 else 0

    # --- Exibir Métricas Macro (Voltando para 5 colunas) ---
    col1, col2, col3, col4, col5 = st.columns(5) # 5 colunas novamente
    col1.metric("Famílias", f"{total_familias_geral:,}")
    col2.metric("Certidões", f"{total_certidoes_geral:,}")
    col3.metric("Requerentes", f"{total_requerentes_geral:,}", help="Contagem de IDs únicos de requerentes (UF_CRM_12_1723552729)")
    col4.metric("Concluídas", f"{concluidas_geral:,}")
    col5.metric("% Conclusão", f"{percentual_conclusao_geral:.1f}%")
    st.markdown("---") # Divisor

    # --- Agrupamento por Família e Cálculos (Contando requerentes únicos) ---
    st.markdown("#### Detalhamento por Família")
    
    # Filtrar famílias com base nos IDs únicos antes de agrupar pode ser mais eficiente
    familias_unicas = df[coluna_nome_familia].unique()
    # st.write(f"Total de famílias únicas encontradas (incluindo desconhecidas): {len(familias_unicas)}")
    
    df_agrupado = df.groupby(coluna_nome_familia).agg(
        total_certidoes=('ID', 'count'),
        # Contar requerentes únicos por família
        total_requerentes=(coluna_id_requerente, pd.Series.nunique),
        concluidas=('CONCLUIDA', 'sum')
    ).reset_index()

    # Calcular Percentual de Conclusão
    df_agrupado['percentual_conclusao'] = (
        (df_agrupado['concluidas'] / df_agrupado['total_certidoes'] * 100)
    )

    # Renomear colunas para exibição
    df_agrupado = df_agrupado.rename(columns={
        coluna_nome_familia: 'Nome da Família',
        'total_certidoes': 'Total Certidões',
        'total_requerentes': 'Total Requerentes', # Reintroduzido
        'concluidas': 'Concluídas',
        'percentual_conclusao': '% Conclusão'
    })

    # Ordenar
    df_agrupado = df_agrupado.sort_values(by='Total Certidões', ascending=False)

    # --- Barra de Busca --- 
    search_term = st.text_input(
        "Buscar por Nome da Família", 
        placeholder="Digite parte do nome para buscar...",
        key="busca_familia_acompanhamento"
    ).strip()
    
    # --- Filtro por Faixa de Percentual de Conclusão ---
    opcoes_percentual = [
        "10% - 30%",
        "31% - 50%",
        "51% - 70%",
        "71% - 90%",
        "91% - 100%",
        "0% - 9%" # Adicionando a faixa inicial
    ]
    faixas_selecionadas = st.multiselect(
        "Filtrar por Faixa de % Conclusão",
        options=opcoes_percentual,
        key="filtro_percentual_acompanhamento"
    )

    df_filtrado = df_agrupado # Começa com todos os dados agrupados

    # Aplicar filtro de busca por nome
    if search_term:
        df_filtrado = df_agrupado[df_agrupado['Nome da Família'].str.contains(search_term, case=False, na=False)]
        st.caption(f"> Exibindo {len(df_filtrado)} de {len(df_agrupado)} famílias encontradas para \"{search_term}\".")
        # Removido o warning de 'nenhuma família encontrada' daqui para mostrar após todos os filtros

    # Aplicar filtro por faixa de percentual SE houver seleção
    if faixas_selecionadas:
        df_filtrado_percentual = pd.DataFrame() # DataFrame vazio para concatenar os resultados
        for faixa in faixas_selecionadas:
            if faixa == "0% - 9%":
                min_val, max_val = 0, 9.99
            elif faixa == "10% - 30%":
                min_val, max_val = 10, 30.99
            elif faixa == "31% - 50%":
                min_val, max_val = 31, 50.99
            elif faixa == "51% - 70%":
                min_val, max_val = 51, 70.99
            elif faixa == "71% - 90%":
                min_val, max_val = 71, 90.99
            elif faixa == "91% - 100%":
                min_val, max_val = 91, 100
            else:
                continue # Caso inválido

            # Filtra o df_filtrado (que já pode ter o filtro de nome aplicado)
            df_faixa_atual = df_filtrado[
                (df_filtrado['% Conclusão'] >= min_val) & 
                (df_filtrado['% Conclusão'] <= max_val)
            ]
            df_filtrado_percentual = pd.concat([df_filtrado_percentual, df_faixa_atual])

        df_filtrado = df_filtrado_percentual.drop_duplicates() # Atualiza df_filtrado com o resultado do filtro de percentual
        st.caption(f"> Exibindo {len(df_filtrado)} famílias após aplicar filtros de nome e percentual.")

    # Verificar se, após todos os filtros, o dataframe está vazio
    if df_filtrado.empty:
        if search_term or faixas_selecionadas:
             st.warning(f"Nenhuma família encontrada com os critérios de busca e/ou filtros de percentual aplicados.")
        # else: # Se não houver filtros e estiver vazio (caso raro)
        #    st.warning("Não há dados de família para exibir.") # Comentado para evitar redundância se já houver aviso no início

    # --- Exibição da Tabela com Estilos (usando df_filtrado) --- 

    # Selecionar e reordenar colunas para exibição
    colunas_exibicao = [
        'Nome da Família',
        'Total Requerentes', # Reintroduzido
        'Total Certidões',
        'Concluídas',
        '% Conclusão'
    ]

    st.dataframe(
        df_filtrado[colunas_exibicao], # Exibe o DataFrame filtrado
        hide_index=True,
        use_container_width=True,
        column_config={
            "Nome da Família": st.column_config.TextColumn(label="Nome da Família"),
            "Total Requerentes": st.column_config.NumberColumn(
                label="Total Requerentes", 
                format="%d",
                help="Contagem de IDs únicos (UF_CRM_12_1723552729)"
                ),
            "Total Certidões": st.column_config.NumberColumn(label="Total Certidões", format="%d"),
            "Concluídas": st.column_config.NumberColumn(label="Concluídas", format="%d"),
            "% Conclusão": st.column_config.ProgressColumn(
                label="% Conclusão",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    ) 