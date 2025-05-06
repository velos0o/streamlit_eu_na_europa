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

    # --- Exclusão de Estágios ---
    estagios_excluidos = [
        "DT1052_22:UC_2QZ8S2",  # PENDENTE
        "DT1052_22:UC_E1VKYT",  # PESQUISA NÃO FINALIZADA
        "DT1052_22:UC_MVS02R",  # DEVOLUTIVA EMISSOR
        "DT1052_22:CLIENT",     # ENTREGUE PDF
        "DT1052_22:NEW",        # SOLICITAR
        "DT1052_22:FAIL",       # CANCELADO
        "DT1052_22:SUCCESS",    # DOCUMENTO FISICO ENTREGUE
        "DT1052_22:UC_A9UEMO"   # Novo estágio a ser excluído
    ]
    if coluna_estagio in df_processar.columns:
        df_processar = df_processar[~df_processar[coluna_estagio].isin(estagios_excluidos)]
        if df_processar.empty:
            st.warning("Não há processos de Comune 1 ou Comune 3 após a exclusão dos estágios especificados.")
            return
    else:
        st.warning(f"Coluna de estágio '{coluna_estagio}' não encontrada para aplicar o filtro de exclusão de estágios.")
    # --- Fim da Exclusão de Estágios ---

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

    # df_filtrado_cat contém os dados após o filtro de categoria.
    # Métricas, contagens e gráfico usarão este df.
    df_para_metricas_e_grafico = df_filtrado_cat.copy()

    # --- Contagens Totais (Após filtro de CATEGORIA) ---
    with st.container(border=True):
        st.markdown("##### Contagem de Processos - Filtro de Categoria Aplicado")
        total_geral_cat = len(df_para_metricas_e_grafico)
        total_comune1_cat = 0
        total_comune3_cat = 0

        if not df_para_metricas_e_grafico.empty:
            contagem_categorias_cat = df_para_metricas_e_grafico[coluna_categoria].value_counts()
            total_comune1_cat = contagem_categorias_cat.get(22, 0)
            total_comune3_cat = contagem_categorias_cat.get(60, 0)

        col_cont1, col_cont2, col_cont3 = st.columns(3)
        with col_cont1:
            st.metric("Total Comune 1 (Categoria)", total_comune1_cat)
        with col_cont2:
            st.metric("Total Comune 3 (Categoria)", total_comune3_cat)
        with col_cont3:
            st.metric("Total Geral (Categoria)", total_geral_cat)

    st.write("\n") # Espaço

    # Condições de parada baseadas APENAS no filtro de categoria para métricas e gráfico
    if df_para_metricas_e_grafico.empty:
        if ids_selecionados: # Categorias foram selecionadas, mas resultou em vazio
            st.info("Nenhum processo encontrado para as categorias selecionadas. Ajuste os filtros de categoria.")
        # Se nenhuma categoria foi selecionada e df_calculado tinha dados, a msg "Nenhuma categoria selecionada." já apareceu.
        # Se df_calculado estava vazio, a mensagem inicial já cobriu.
        st.stop() # Para aqui se não há dados para mostrar nas métricas/gráficos.


    # --- Métricas Resumo (Calculadas sobre dados filtrados por CATEGORIA) ---
    with st.container(border=True):
        st.markdown("##### Métricas de Tempo (Dias) - Filtro de Categoria Aplicado")
        if not df_para_metricas_e_grafico.empty:
            med_tempo_medio_cat = df_para_metricas_e_grafico['TEMPO_DIAS'].mean()
            med_tempo_mediana_cat = df_para_metricas_e_grafico['TEMPO_DIAS'].median()
            med_tempo_max_cat = df_para_metricas_e_grafico['TEMPO_DIAS'].max()
        else:
            med_tempo_medio_cat, med_tempo_mediana_cat, med_tempo_max_cat = 0, 0, 0

        col_met1, col_met2, col_met3 = st.columns(3)
        with col_met1:
            st.metric("Tempo Médio (Categoria)", f"{med_tempo_medio_cat:.1f}")
        with col_met2:
            st.metric("Tempo Mediano (Categoria)", f"{med_tempo_mediana_cat:.1f}")
        with col_met3:
            st.metric("Tempo Máximo (Categoria)", f"{med_tempo_max_cat:.0f}")

    # --- Criação das Faixas de Tempo (baseado em filtro de CATEGORIA) ---
    bins = [-1, 30, 60, 100, 120, 160, 180, 200, 220, 240, float('inf')]
    labels = ['0-30', '31-60', '61-100', '101-120', '121-160', '161-180', '181-200', '201-220', '221-240', '241+']

    if not df_para_metricas_e_grafico.empty:
        df_para_metricas_e_grafico['TEMPO_DIAS'] = pd.to_numeric(df_para_metricas_e_grafico['TEMPO_DIAS'], errors='coerce')
        df_com_tempo_cat = df_para_metricas_e_grafico.dropna(subset=['TEMPO_DIAS'])
        
        if not df_com_tempo_cat.empty:
            df_para_metricas_e_grafico['FAIXA_TEMPO'] = pd.cut(df_com_tempo_cat['TEMPO_DIAS'], bins=bins, labels=labels, right=True)
            contagem_por_faixa_cat = df_para_metricas_e_grafico.groupby('FAIXA_TEMPO', observed=False).size().reset_index(name='CONTAGEM')
        else:
             contagem_por_faixa_cat = pd.DataFrame({'FAIXA_TEMPO': labels, 'CONTAGEM': [0]*len(labels)})
    else:
        contagem_por_faixa_cat = pd.DataFrame({'FAIXA_TEMPO': labels, 'CONTAGEM': [0]*len(labels)})

    contagem_por_faixa_cat['FAIXA_TEMPO'] = pd.Categorical(contagem_por_faixa_cat['FAIXA_TEMPO'], categories=labels, ordered=True)
    contagem_por_faixa_cat = contagem_por_faixa_cat.sort_values('FAIXA_TEMPO')


    # --- Gráfico de Barras por Faixa de Tempo (baseado em filtro de CATEGORIA) ---
    st.markdown("##### Distribuição por Faixa de Tempo (Dias) - Filtro de Categoria Aplicado")
    cor_barra = '#3B82F6'

    try:
        fig = px.bar(
            contagem_por_faixa_cat,
            x='FAIXA_TEMPO',
            y='CONTAGEM',
            text='CONTAGEM',
            title="Número de Processos por Faixa de Tempo (Categoria)",
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

    # --- Filtro por Nome/Família (Título) - POSICIONADO ANTES DA TABELA ---
    st.markdown("---")
    termo_busca_titulo_tabela = st.text_input(
        "Buscar por Nome/Família (Título) na tabela abaixo:",
        key="busca_titulo_tabela_tempo_new" # Nova chave ou certificar que a antiga foi removida
    )
    
    # Aplicar filtro de nome ao df_para_metricas_e_grafico para obter df_para_tabela
    df_para_tabela = df_para_metricas_e_grafico.copy() 

    if termo_busca_titulo_tabela and not df_para_tabela.empty:
        termo_busca_titulo_tabela = termo_busca_titulo_tabela.strip()
        df_para_tabela = df_para_tabela[
            df_para_tabela[coluna_titulo].str.contains(termo_busca_titulo_tabela, case=False, na=False)
        ]
    
    # --- Tabela com Processos Exibidos (Filtrados por Categoria e Nome) ---
    st.markdown("##### Detalhes dos Processos Exibidos (Filtrados por Categoria e Nome)")
    
    if df_para_tabela.empty:
        if termo_busca_titulo_tabela:
            st.info(f"Nenhum processo encontrado para '{termo_busca_titulo_tabela}' com as categorias selecionadas.")
        elif not df_para_metricas_e_grafico.empty : # Havia dados de categoria, mas busca por nome vazia não deve limpar tudo
             st.caption("Todos os processos para as categorias selecionadas estão listados abaixo. Digite um Nome/Família para refinar a busca.")
             # Neste caso, df_para_tabela é igual a df_para_metricas_e_grafico, então a tabela mostrará os dados de categoria.
        # else: # df_para_metricas_e_grafico estava vazio, já paramos antes com st.stop()
            # Não é necessário st.caption aqui pois já houve st.stop()
            
    # Mostrar a tabela mesmo que esteja vazia após a busca por nome,
    # ou se a busca por nome estiver vazia (mostrando todos os resultados do filtro de categoria).
    # A mensagem acima já informa o usuário sobre o estado.

    # Ordenar df_para_tabela para exibição (mais antigos primeiro)
    df_exibir_completo = df_para_tabela.sort_values(by='TEMPO_DIAS', ascending=False).copy()

    # Adicionar nome legível do estágio
    if coluna_estagio in df_exibir_completo.columns:
            try:
                df_exibir_completo['Estágio Legível'] = df_exibir_completo[coluna_estagio].apply(simplificar_nome_estagio_comune)
            except KeyError: 
                df_exibir_completo['Estágio Legível'] = "Erro estágio"
    else:
        df_exibir_completo['Estágio Legível'] = "N/A"
        
    if 'DATA_INICIO' not in df_exibir_completo.columns:
            df_exibir_completo['DATA_INICIO'] = pd.NaT 

    colunas_exibir = [coluna_id, coluna_titulo, 'DATA_INICIO', 'TEMPO_DIAS', 'FAIXA_TEMPO', 'Estágio Legível']
    colunas_exibir_existentes = [col for col in colunas_exibir if col in df_exibir_completo.columns]

    if not df_exibir_completo.empty and colunas_exibir_existentes:
        st.dataframe(
            df_exibir_completo[colunas_exibir_existentes], 
            use_container_width=True,
            column_config={
                "DATA_INICIO": st.column_config.DateColumn("Data Início Cálculo", format="DD/MM/YYYY"),
                "TEMPO_DIAS": st.column_config.NumberColumn("Tempo (Dias)"),
                "FAIXA_TEMPO": st.column_config.TextColumn("Faixa Tempo"),
                "Estágio Legível": st.column_config.TextColumn("Estágio")
            }
        )
    elif not df_para_metricas_e_grafico.empty and not termo_busca_titulo_tabela :
        # Se havia dados de categoria e a busca está vazia, mas por algum motivo df_exibir_completo está vazio (ex. erro colunas)
        # Isso é um fallback, a lógica acima com st.caption já deve ter coberto
        st.caption("A tabela está vazia. Verifique os filtros ou a disponibilidade de dados.")
    elif df_para_metricas_e_grafico.empty:
        # Não deve chegar aqui por causa do st.stop() anterior, mas é uma segurança.
        st.info("Não há dados de categoria para exibir na tabela.")

    # A última mensagem "Nenhum processo para exibir na tabela com os filtros atuais."
    # é coberta pelas condições acima.
    # else:
    #      st.caption("Nenhum processo para exibir na tabela com os filtros atuais.") 