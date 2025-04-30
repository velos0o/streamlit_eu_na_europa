import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os # Adicionado para verificar existência do arquivo CSV

# Importar função de simplificação de estágio
from .visao_geral import simplificar_nome_estagio_comune

def exibir_tempo_solicitacao(df_comune):
    """
    Exibe a análise do tempo de solicitação (em dias) para os processos de Comune 1 e 3,
    utilizando fontes de data específicas para cada categoria.
    Permite filtros por Categoria (CATEGORY_ID) e Nome (TITLE).
    """
    st.subheader("Análise de Tempo de Solicitação (Comune 1 e 3)")

    if df_comune.empty:
        st.warning("Não há dados de Comune para analisar o tempo de solicitação.")
        return

    # --- Colunas Necessárias ---
    coluna_id = 'ID'
    coluna_data_criacao_original = 'CREATED_TIME' # Ainda necessária como fallback ou referência
    coluna_titulo = 'TITLE' # Coluna para busca por família/nome
    coluna_estagio = 'STAGE_ID' # Coluna original do estágio
    coluna_categoria = 'CATEGORY_ID' # Coluna para filtro de categoria
    coluna_data_comune3 = 'UF_CRM_12_DATA_SOLICITACAO' # Coluna específica para Comune 3
    coluna_data_comune1_csv = 'Movido em' # Coluna de data no CSV para Comune 1

    # Verificar colunas essenciais mínimas
    colunas_necessarias_base = [coluna_id, coluna_titulo, coluna_estagio, coluna_categoria]
    colunas_ausentes_base = [col for col in colunas_necessarias_base if col not in df_comune.columns]
    if colunas_ausentes_base:
        st.error(f"Colunas essenciais não encontradas: {', '.join(colunas_ausentes_base)}.")
        return

    # --- Pré-processamento Inicial e Filtro de Categorias ---
    df_comune[coluna_categoria] = pd.to_numeric(df_comune[coluna_categoria], errors='coerce')
    df_comune = df_comune.dropna(subset=[coluna_categoria])
    df_comune[coluna_categoria] = df_comune[coluna_categoria].astype(int)

    # Filtrar APENAS Comune 1 (22) e Comune 3 (60)
    ids_categorias_analisar = [22, 60]
    df_processar = df_comune[df_comune[coluna_categoria].isin(ids_categorias_analisar)].copy()

    if df_processar.empty:
        st.warning("Não há processos de Comune 1 ou Comune 3 nos dados fornecidos.")
        return

    # Garantir que a coluna ID é adequada para merge
    df_processar[coluna_id] = df_processar[coluna_id].astype(str)

    # Data de hoje para cálculo do tempo
    data_hoje = pd.to_datetime(datetime.now().date())

    # DataFrames para armazenar resultados por categoria
    df_comune1_calculado = pd.DataFrame()
    df_comune3_calculado = pd.DataFrame()
    df_comune3_erros = pd.DataFrame()

    # --- Processamento Comune 3 (CATEGORY_ID = 60) ---
    df_comune3 = df_processar[df_processar[coluna_categoria] == 60].copy()
    if not df_comune3.empty:
        if coluna_data_comune3 not in df_comune3.columns:
            st.error(f"Coluna '{coluna_data_comune3}' necessária para Comune 3 não encontrada.")
            # Considerar todos do Comune 3 como erro neste caso
            df_comune3_erros = df_comune3[[coluna_id, coluna_titulo, coluna_estagio]].copy()
        else:
            # Tentar converter a data específica do Comune 3
            df_comune3['DATA_INICIO'] = pd.to_datetime(df_comune3[coluna_data_comune3], errors='coerce')

            # Separar erros (data inválida ou ausente)
            df_comune3_erros = df_comune3[df_comune3['DATA_INICIO'].isna()][[coluna_id, coluna_titulo, coluna_estagio]].copy()

            # Calcular TEMPO_DIAS para os válidos
            df_comune3_validos = df_comune3.dropna(subset=['DATA_INICIO']).copy()
            if not df_comune3_validos.empty:
                df_comune3_validos['TEMPO_DIAS'] = (data_hoje - df_comune3_validos['DATA_INICIO']).dt.days
                # Remover tempos negativos (caso haja datas futuras)
                df_comune3_validos = df_comune3_validos[df_comune3_validos['TEMPO_DIAS'] >= 0]
                df_comune3_calculado = df_comune3_validos

    # --- Processamento Comune 1 (CATEGORY_ID = 22) ---
    df_comune1 = df_processar[df_processar[coluna_categoria] == 22].copy()
    if not df_comune1.empty:
        path_csv_comune1 = 'views/comune_new/Planilhas/Emissões Italiana, Antes de movimentação geral - comune.csv'
        if not os.path.exists(path_csv_comune1):
            st.error(f"Arquivo CSV para Comune 1 não encontrado em: {path_csv_comune1}")
        else:
            try:
                df_csv = pd.read_csv(path_csv_comune1, low_memory=False) # Adicionado low_memory=False por precaução
                # Garantir que a coluna de ID no CSV também seja string para o merge
                if coluna_id not in df_csv.columns:
                     st.error(f"Coluna '{coluna_id}' não encontrada no arquivo CSV: {path_csv_comune1}")
                elif coluna_data_comune1_csv not in df_csv.columns:
                    st.error(f"Coluna de data '{coluna_data_comune1_csv}' não encontrada no arquivo CSV: {path_csv_comune1}")
                else:
                    df_csv[coluna_id] = df_csv[coluna_id].astype(str)

                    # Realizar o merge
                    df_comune1_merged = pd.merge(df_comune1, df_csv[[coluna_id, coluna_data_comune1_csv]], on=coluna_id, how='left')

                    # Tentar converter a data do CSV ('Movido em')
                    df_comune1_merged['DATA_INICIO'] = pd.to_datetime(df_comune1_merged[coluna_data_comune1_csv], errors='coerce')

                    # Calcular TEMPO_DIAS para os válidos (merge bem-sucedido e data válida)
                    df_comune1_validos = df_comune1_merged.dropna(subset=['DATA_INICIO']).copy()
                    if not df_comune1_validos.empty:
                        df_comune1_validos['TEMPO_DIAS'] = (data_hoje - df_comune1_validos['DATA_INICIO']).dt.days
                        # Remover tempos negativos
                        df_comune1_validos = df_comune1_validos[df_comune1_validos['TEMPO_DIAS'] >= 0]
                        df_comune1_calculado = df_comune1_validos
                    
                    # Opcional: Identificar e talvez listar erros do Comune 1 (merge falhou ou data CSV inválida)
                    # df_comune1_erros = df_comune1_merged[df_comune1_merged['DATA_INICIO'].isna()]

            except Exception as e:
                st.error(f"Erro ao ler ou processar o arquivo CSV '{path_csv_comune1}': {e}")

    # --- Combinar Resultados Válidos ---
    df_calculado = pd.concat([df_comune1_calculado, df_comune3_calculado], ignore_index=True)

    if df_calculado.empty and df_comune3_erros.empty:
         st.warning("Nenhum processo de Comune 1 ou 3 pôde ser processado para análise de tempo (verifique fontes de dados e colunas).")
         return
    elif df_calculado.empty:
         st.warning("Nenhum processo teve seu tempo calculado com sucesso. Verifique as fontes de data.")
         # Mesmo que não haja dados calculados, podemos querer mostrar os erros do Comune 3
         # Continue a execução para mostrar a seção de erros

    # --- Exibir Erros do Comune 3 ---
    if not df_comune3_erros.empty:
        st.markdown("---")
        with st.expander(f"Processos do Comune 3 sem Data de Início Válida ({len(df_comune3_erros)})", expanded=False):
            st.warning(f"Os seguintes {len(df_comune3_erros)} processos do Comune 3 não puderam ter o tempo calculado pois a coluna '{coluna_data_comune3}' está vazia ou com formato inválido.")
            
            # Adicionar nome legível do estágio aos erros também
            if coluna_estagio in df_comune3_erros.columns:
                 # É mais seguro fazer merge se df_comune tiver o estágio simplificado, ou chamar a função aqui
                 # Para simplificar, vamos apenas mostrar o STAGE_ID por enquanto, ou chamar a função
                 try:
                     # Tenta aplicar a função. Se falhar (ex: coluna não existe no df original), mostra N/A
                     df_comune3_erros['Estágio Legível'] = df_comune3_erros[coluna_estagio].apply(simplificar_nome_estagio_comune)
                 except KeyError:
                     df_comune3_erros['Estágio Legível'] = "Erro ao obter estágio"

                 colunas_erros_exibir = [coluna_id, coluna_titulo, 'Estágio Legível']
            else:
                 colunas_erros_exibir = [coluna_id, coluna_titulo]


            st.dataframe(
                df_comune3_erros[colunas_erros_exibir],
                use_container_width=True,
                column_config={
                     coluna_titulo: "Nome/Família",
                     "Estágio Legível": "Estágio Atual"
                }
                )
        st.markdown("---")


    # --- Filtros Interativos (Aplicados sobre df_calculado) ---
    categorias_map_filtrado = {22: "Comune 1", 60: "Comune 3"}
    categorias_nomes_filtrado = list(categorias_map_filtrado.values())

    categorias_selecionadas_nomes = st.multiselect(
        "Filtrar por Categoria:",
        options=categorias_nomes_filtrado,
        default=categorias_nomes_filtrado, # Padrão: Mostrar ambos
        key="filtro_categoria_tempo_new"
    )

    # Mapear nomes selecionados de volta para IDs
    ids_selecionados = [k for k, v in categorias_map_filtrado.items() if v in categorias_selecionadas_nomes]

    # Aplicar filtro de categoria
    if ids_selecionados:
         # Filtrar apenas se df_calculado não estiver vazio
         if not df_calculado.empty:
             df_filtrado_cat = df_calculado[df_calculado[coluna_categoria].isin(ids_selecionados)]
         else:
             df_filtrado_cat = df_calculado # Mantem vazio se já estava
    else:
        # Se nada for selecionado, mostrar dataframe vazio (ou mensagem)
        df_filtrado_cat = pd.DataFrame(columns=df_calculado.columns)
        if not df_calculado.empty: # Só mostra a info se havia dados calculados
            st.info("Nenhuma categoria selecionada.")


    # Filtro por Nome (TITLE) sobre o resultado do filtro de categoria
    termo_busca_titulo = st.text_input("Buscar por Nome/Família (Título):", key="busca_titulo_tempo_new")
    df_filtrado = df_filtrado_cat.copy() # Começa com o resultado do filtro de categoria

    if termo_busca_titulo and not df_filtrado.empty:
        termo_busca_titulo = termo_busca_titulo.strip()
        df_filtrado = df_filtrado[df_filtrado[coluna_titulo].str.contains(termo_busca_titulo, case=False, na=False)]


    # --- Contagens Totais (Após filtros aplicados) ---
    with st.container(border=True):
        st.markdown("##### Contagem de Processos - Filtro Aplicado")
        total_geral = len(df_filtrado)
        total_comune1 = 0
        total_comune3 = 0

        if not df_filtrado.empty:
            contagem_categorias = df_filtrado[coluna_categoria].value_counts()
            total_comune1 = contagem_categorias.get(22, 0)
            total_comune3 = contagem_categorias.get(60, 0)

        col_cont1, col_cont2, col_cont3 = st.columns(3)
        with col_cont1:
            st.metric("Total Comune 1", total_comune1)
        with col_cont2:
            st.metric("Total Comune 3", total_comune3)
        with col_cont3:
            st.metric("Total Geral Filtrado", total_geral)

    st.write("\n") # Espaço

    if df_filtrado.empty and (ids_selecionados or termo_busca_titulo):
        st.info("Nenhum processo encontrado para os filtros aplicados.")
        # Para aqui para não mostrar métricas/gráficos vazios sem necessidade
        # Se quiser mostrar vazio, comente o st.stop()
        st.stop() # Para a execução aqui se não há dados para mostrar
    elif df_filtrado.empty and not df_calculado.empty :
         # Caso onde há dados calculados, mas filtros não selecionaram nada
         st.info("Selecione categorias ou ajuste a busca para ver os resultados.")
         st.stop()
    # Se df_calculado estava vazio desde o início, a mensagem já foi dada antes


    # --- Métricas Resumo (Calculadas sobre dados filtrados) ---
    with st.container(border=True):
        st.markdown("##### Métricas de Tempo (Dias) - Filtro Aplicado")
        # Recalcular métricas com base no df_filtrado final
        if not df_filtrado.empty:
            med_tempo_medio = df_filtrado['TEMPO_DIAS'].mean()
            med_tempo_mediana = df_filtrado['TEMPO_DIAS'].median()
            med_tempo_max = df_filtrado['TEMPO_DIAS'].max()
        else:
            # Isso não deveria acontecer por causa do st.stop() acima, mas por segurança:
            med_tempo_medio, med_tempo_mediana, med_tempo_max = 0, 0, 0

        col_met1, col_met2, col_met3 = st.columns(3)
        with col_met1:
            st.metric("Tempo Médio", f"{med_tempo_medio:.1f}")
        with col_met2:
            st.metric("Tempo Mediano", f"{med_tempo_mediana:.1f}")
        with col_met3:
            st.metric("Tempo Máximo", f"{med_tempo_max:.0f}")

    # --- Criação das Faixas de Tempo ---
    bins = [-1, 30, 60, 100, 120, 160, 180, 200, 220, 240, float('inf')]
    labels = ['0-30', '31-60', '61-100', '101-120', '121-160', '161-180', '181-200', '201-220', '221-240', '241+']

    # Aplicar faixas ao df_filtrado
    if not df_filtrado.empty:
        # Certificar que TEMPO_DIAS é numérico antes de cortar
        df_filtrado['TEMPO_DIAS'] = pd.to_numeric(df_filtrado['TEMPO_DIAS'], errors='coerce')
        df_filtrado_com_tempo = df_filtrado.dropna(subset=['TEMPO_DIAS'])
        
        if not df_filtrado_com_tempo.empty:
            df_filtrado['FAIXA_TEMPO'] = pd.cut(df_filtrado_com_tempo['TEMPO_DIAS'], bins=bins, labels=labels, right=True)
            contagem_por_faixa = df_filtrado.groupby('FAIXA_TEMPO', observed=False).size().reset_index(name='CONTAGEM')
        else:
             # Caso onde TEMPO_DIAS era NaN para todos no df_filtrado (improvável, mas seguro)
             contagem_por_faixa = pd.DataFrame({'FAIXA_TEMPO': labels, 'CONTAGEM': [0]*len(labels)})
    else:
        # Se df_filtrado estava vazio
        contagem_por_faixa = pd.DataFrame({'FAIXA_TEMPO': labels, 'CONTAGEM': [0]*len(labels)})

    # Garantir a ordem correta das faixas mesmo se vazio
    contagem_por_faixa['FAIXA_TEMPO'] = pd.Categorical(contagem_por_faixa['FAIXA_TEMPO'], categories=labels, ordered=True)
    contagem_por_faixa = contagem_por_faixa.sort_values('FAIXA_TEMPO')


    # --- Gráfico de Barras por Faixa de Tempo ---
    st.markdown("##### Distribuição por Faixa de Tempo (Dias)")
    cor_barra = '#3B82F6'

    try:
        fig = px.bar(
            contagem_por_faixa,
            x='FAIXA_TEMPO',
            y='CONTAGEM',
            text='CONTAGEM',
            title="Número de Processos por Faixa de Tempo",
            labels={'FAIXA_TEMPO': 'Faixa de Tempo (Dias)', 'CONTAGEM': 'Nº Processos'}
        )
        fig.update_traces(
            textposition='outside',
            marker_color=cor_barra,
            textfont_size=12,
            hovertemplate='<b>%{x}</b><br>Processos: %{y}<extra></extra>'
        )
        fig.update_layout(
            xaxis_title=None,
            yaxis_title="Número de Processos",
            xaxis=dict(categoryorder='array', categoryarray=labels, showgrid=False),
            template="plotly_white",
            title_font_size=18,
            yaxis=dict(showgrid=True, gridcolor='LightGray'),
            bargap=0.2,
            margin=dict(t=50, b=50, l=50, r=30)
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar o gráfico de barras: {e}")

    # --- Tabela com Processos mais Antigos (Filtrada) ---
    st.markdown("---")
    st.markdown("##### Detalhes dos Processos Exibidos (Top 10 Mais Antigos)")
    if not df_filtrado.empty:
        df_top10_antigos = df_filtrado.nlargest(10, 'TEMPO_DIAS').copy()

        # Adicionar nome legível do estágio
        if coluna_estagio in df_top10_antigos.columns:
             try:
                 df_top10_antigos['Estágio Legível'] = df_top10_antigos[coluna_estagio].apply(simplificar_nome_estagio_comune)
             except KeyError: # Caso a coluna exista mas a função falhe por algum motivo
                 df_top10_antigos['Estágio Legível'] = "Erro estágio"
        else:
            df_top10_antigos['Estágio Legível'] = "N/A"
            
        # Adicionar a coluna de Data de Início usada no cálculo
        # A coluna DATA_INICIO foi criada durante o processamento
        if 'DATA_INICIO' not in df_top10_antigos.columns:
             # Se por algum motivo não existir (ex: só havia erros), criar vazia
              df_top10_antigos['DATA_INICIO'] = pd.NaT 

        # Selecionar colunas relevantes
        # Usar DATA_INICIO ao invés de coluna_data_criacao_original
        colunas_exibir = [coluna_id, coluna_titulo, 'DATA_INICIO', 'TEMPO_DIAS', 'FAIXA_TEMPO', 'Estágio Legível']
        colunas_exibir = [col for col in colunas_exibir if col in df_top10_antigos.columns] # Garantir que existem

        if not colunas_exibir:
            st.warning("Não foi possível encontrar colunas para exibir na tabela.")
        else:
            st.dataframe(
                df_top10_antigos[colunas_exibir],
                use_container_width=True,
                column_config={
                    # Renomear DATA_INICIO para algo mais genérico na exibição
                    "DATA_INICIO": st.column_config.DateColumn("Data Início Cálculo", format="DD/MM/YYYY"),
                    "TEMPO_DIAS": st.column_config.NumberColumn("Tempo (Dias)"),
                    "FAIXA_TEMPO": st.column_config.TextColumn("Faixa Tempo"),
                    "Estágio Legível": st.column_config.TextColumn("Estágio")
                }
            )
    else:
         st.caption("Nenhum processo para exibir na tabela com os filtros atuais.") 