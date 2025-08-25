import streamlit as st
import pandas as pd
from utils.dataframe_utils import ensure_pandas_df
from datetime import datetime

def parse_flexible_date(series):
    """Tenta converter uma data no formato dd/mm/aaaa, e se falhar, tenta dd/mm assumindo o ano atual."""
    # Primeiro tenta o formato completo
    dates = pd.to_datetime(series, format='%d/%m/%Y', errors='coerce', dayfirst=True)
    # Onde falhou, tenta o formato dd/mm para as datas que falharam
    failed_mask = dates.isna()
    if failed_mask.any():
        # Tenta o formato dd/mm para as datas que falharam
        dates_short_year = pd.to_datetime(series[failed_mask].astype(str), format='%d/%m', errors='coerce', dayfirst=True)
        if not dates_short_year.empty:
            # Se bem-sucedido, atribui o ano atual
            current_year = pd.Timestamp.now().year
            dates_copy = dates.copy()
            dates_copy.loc[failed_mask] = dates_short_year.apply(lambda dt: dt.replace(year=current_year) if pd.notna(dt) else pd.NaT)
            return dates_copy
    return dates

def calcular_tempo_certidoes_brasileiras(df_cartorio):
    """
    Calcula o tempo e o status das certidões brasileiras, retornando colunas separadas.
    """
    if df_cartorio is None or df_cartorio.empty:
        return pd.DataFrame(columns=['Dias Certidões BR', 'Andamento Certidões BR', 'Média Certidões BR'])

    cols_necessarias = ['UF_CRM_34_ID_FAMILIA', 'CREATED_TIME', 'UF_CRM_34_DATA_CERTIDAO_ENTREGUE', 'STAGE_ID']
    if not all(col in df_cartorio.columns for col in cols_necessarias):
        st.warning("Dados do cartório incompletos para calcular tempo das certidões brasileiras.")
        return pd.DataFrame(columns=['Dias Certidões BR', 'Andamento Certidões BR', 'Média Certidões BR'])

    df = df_cartorio[cols_necessarias].copy()

    # Estágios a serem completamente ignorados no cálculo
    IGNORE_STAGES = [
        'DT1098_92:UC_Z24IF7', 'DT1098_94:UC_MGTPX0',
        'DT1098_92:UC_U10R0R', 'DT1098_94:UC_L3JFKO',
        'DT1098_92:FAIL',       'DT1098_94:FAIL',
        'DT1098_102:FAIL',
        'DT1098_102:UC_676WIG',
        'DT1098_104:NEW',
        'DT1098_104:PREPARATION',
        'DT1098_104:SUCCESS',
        'DT1098_104:FAIL'
    ]
    df = df[~df['STAGE_ID'].isin(IGNORE_STAGES)]

    if df.empty:
        return pd.DataFrame(columns=['Dias Certidões BR', 'Andamento Certidões BR', 'Média Certidões BR'])

    df['CREATED_TIME'] = pd.to_datetime(df['CREATED_TIME'], errors='coerce')
    df['UF_CRM_34_DATA_CERTIDAO_ENTREGUE'] = pd.to_datetime(df['UF_CRM_34_DATA_CERTIDAO_ENTREGUE'], errors='coerce')

    SUCCESS_STAGES = ['DT1098_92:SUCCESS', 'DT1098_94:SUCCESS', 'DT1098_102:UC_UHPXE8']
    df['concluida'] = df['STAGE_ID'].isin(SUCCESS_STAGES)

    grouped = df.groupby('UF_CRM_34_ID_FAMILIA')

    resultados = []
    for family_id, group in grouped:
        total_certidoes = len(group)
        if total_certidoes == 0:
            continue

        certidoes_concluidas = group['concluida'].sum()
        
        dias_display = "N/A"
        status_display = f"{certidoes_concluidas}/{total_certidoes} concluídas"
        tempo_dias_media = None

        if certidoes_concluidas == total_certidoes:
            data_inicio = group['CREATED_TIME'].min()
            data_fim = group['UF_CRM_34_DATA_CERTIDAO_ENTREGUE'].max()
            if pd.notna(data_inicio) and pd.notna(data_fim):
                tempo_dias_media = (data_fim - data_inicio).days
                dias_display = f"{tempo_dias_media} dias"
        else:
            data_inicio = group['CREATED_TIME'].min()
            if pd.notna(data_inicio):
                dias_ate_momento = (pd.Timestamp.now() - data_inicio).days
                dias_display = f"{dias_ate_momento} dias"

        resultados.append({
            'ID FAMÍLIA': family_id,
            'Dias Certidões BR': dias_display,
            'Andamento Certidões BR': status_display,
            'Média Certidões BR': tempo_dias_media
        })

    return pd.DataFrame(resultados).set_index('ID FAMÍLIA')

def show_dados_macros(df, df_original, df_cartorio):
    """
    Exibe as métricas macro de tarefas cumpridas com filtros interativos.
    """
    df = ensure_pandas_df(df)

    if df.empty:
        st.warning("Não há dados de entrada para o relatório de Dados Macros.")
        return
    
    # Mapeamento das etapas e suas respectivas colunas de data
    etapas_config = {
        "Procuração": ('PROCURAÇÃO - DATA ENVIO', 'PROCURAÇÃO - DATA CONCLUSÃO'),
        "Análise Docs": ('ANALISE - DATA DE ENVIO', 'ANALISE - DATA CONCLUSÃO'),
        "Tradução": ('TRADUÇÃO - DATA DE INICIO', 'TRADUÇÃO - DATA DE ENTREGA'),
        "Apostila": ('APOSTILA - DATA DE INICIO', 'APOSTILA - DATA DE ENTREGA'),
        "Drive": ('DRIVE - DATA DE INICIO', 'DRIVE - DATA DE ENTREGA')
    }
    col_inicio_processo = 'Data de Inicio das Tratativas'
    col_fim_processo = 'DATA DE FINALIZAÇÃO DA PASTA'

    # --- FILTROS ---
    with st.expander("Filtros", expanded=True):
        col1_filter, col2_filter, col3_filter = st.columns(3)
        
        with col1_filter:
            if 'CONSULTOR RESPONSÁVEL' in df.columns:
                # Tratar valores nulos ou vazios como "Sem Responsável"
                df['CONSULTOR RESPONSÁVEL'] = df['CONSULTOR RESPONSÁVEL'].fillna('Sem Responsável').replace('', 'Sem Responsável')
                responsaveis = sorted(df['CONSULTOR RESPONSÁVEL'].unique())
                
                selected_responsaveis = st.multiselect(
                    "Filtrar por Responsável:",
                    options=responsaveis,
                    default=[]
                )
            else:
                selected_responsaveis = []
                st.info("Coluna 'CONSULTOR RESPONSÁVEL' não encontrada para filtro.")

        with col2_filter:
            # Opções para o filtro de data
            opcoes_data = ["Nenhum"] + list(etapas_config.keys())
            etapa_selecionada = st.selectbox(
                "Filtrar por Data de Conclusão da Etapa:",
                options=opcoes_data
            )

        with col3_filter:
            min_date = datetime(2020, 1, 1).date()
            max_date = datetime.now().date()
            
            selected_start_date = st.date_input("Data de Início", value=None, min_value=min_date, max_value=max_date, format="DD/MM/YYYY", disabled=(etapa_selecionada == "Nenhum"))
            selected_end_date = st.date_input("Data de Fim", value=None, min_value=min_date, max_value=max_date, format="DD/MM/YYYY", disabled=(etapa_selecionada == "Nenhum"))

    # Aplica filtros
    df_filtrado = df.copy()

    # O total de famílias é calculado a partir do dataframe ORIGINAL, contando linhas com nome na coluna 'A'
    if 'A' in df_original.columns:
        total_familias_geral = df_original[df_original['A'].notna() & (df_original['A'] != '')].shape[0]
    else:
        total_familias_geral = 0


    if selected_responsaveis:
        df_filtrado = df_filtrado[df_filtrado['CONSULTOR RESPONSÁVEL'].isin(selected_responsaveis)]
        
    if etapa_selecionada != "Nenhum" and selected_start_date and selected_end_date:
        start_date = pd.to_datetime(selected_start_date)
        end_date = pd.to_datetime(selected_end_date)
        
        _, col_data_conclusao = etapas_config[etapa_selecionada]
        
        if col_data_conclusao in df_filtrado.columns:
            date_series = parse_flexible_date(df_filtrado[col_data_conclusao])
            mask = (date_series >= start_date) & (date_series <= end_date)
            df_filtrado = df_filtrado[mask.fillna(False)]
        else:
            st.warning(f"A coluna de data '{col_data_conclusao}' não foi encontrada para a etapa '{etapa_selecionada}'.")
    
    if df_filtrado.empty:
        st.warning("Não há dados para exibir com os filtros selecionados.")
        return

    # --- Análise de Tarefas Cumpridas ---
    lista_tags = [
        'Emissão', 'Comune', 'Analise Documental', 
        'Tradução', 'Apostilamento', 'Drive', 'Procuração'
    ]
    mapeamento_conclusao = {
        'Procuração': ('PROCURAÇÃO - STATUS', 'Concluida'),
        'Analise Documental': ('ANALISE - STATUS', 'Positiva'),
        'Tradução': ('TRADUÇÃO - STATUS', 'Concluido'),
        'Apostilamento': ('APOSTILA - STATUS', 'Concluido'),
        'Drive': ('DRIVE - STATUS', 'Concluido')
    }

    try:
        lista_cumpridas_por_responsavel = []
        for etapa in lista_tags:
            df_temp = pd.DataFrame()
            if etapa in mapeamento_conclusao:
                coluna, valor_sucesso = mapeamento_conclusao[etapa]
                if coluna in df_filtrado.columns and 'CONSULTOR RESPONSÁVEL' in df_filtrado.columns and not df_filtrado[coluna].isnull().all():
                    condicao = df_filtrado[coluna].str.strip().str.lower() == valor_sucesso.lower()
                    df_etapa_cumprida = df_filtrado.loc[condicao.fillna(False)]
                    df_temp = df_etapa_cumprida[['CONSULTOR RESPONSÁVEL', 'ID FAMÍLIA']].copy()
                    df_temp['CUMPRIDA_TIPO'] = etapa
            elif 'PENDENCIAS' in df_filtrado.columns and 'CONSULTOR RESPONSÁVEL' in df_filtrado.columns: 
                df_etapa_cumprida = df_filtrado.loc[~df_filtrado['PENDENCIAS'].str.contains(etapa, case=False, na=False)]
                df_temp = df_etapa_cumprida[['CONSULTOR RESPONSÁVEL', 'ID FAMÍLIA']].copy()
                df_temp['CUMPRIDA_TIPO'] = etapa
            if not df_temp.empty:
                lista_cumpridas_por_responsavel.append(df_temp)

        # Garante que o cumpridas_df exista, mesmo que vazio
        if not lista_cumpridas_por_responsavel:
            cumpridas_df = pd.DataFrame(columns=['CONSULTOR RESPONSÁVEL', 'ID FAMÍLIA', 'CUMPRIDA_TIPO'])
        else:
            cumpridas_df = pd.concat(lista_cumpridas_por_responsavel, ignore_index=True)
            cumpridas_df.drop_duplicates(inplace=True)

        # Cria a base da tabela com todos os consultores do filtro
        todos_consultores = df_filtrado['CONSULTOR RESPONSÁVEL'].unique()
        display_df = pd.DataFrame(index=todos_consultores)

        # Calcula as famílias paradas
        total_familias_por_consultor = df_filtrado.groupby('CONSULTOR RESPONSÁVEL')['ID FAMÍLIA'].nunique()
        familias_com_tarefa = cumpridas_df.groupby('CONSULTOR RESPONSÁVEL')['ID FAMÍLIA'].nunique()
        
        display_df['Total Famílias'] = total_familias_por_consultor
        familias_paradas = total_familias_por_consultor.sub(familias_com_tarefa, fill_value=0)
        display_df['Famílias Paradas'] = familias_paradas

        # Adiciona as colunas de tarefas cumpridas
        crosstab_cumpridas = pd.crosstab(
            index=cumpridas_df['CONSULTOR RESPONSÁVEL'],
            columns=cumpridas_df['CUMPRIDA_TIPO']
        )
        for tag in lista_tags:
            if tag in crosstab_cumpridas.columns:
                display_df[tag] = crosstab_cumpridas[tag]
            else:
                display_df[tag] = 0
        
        display_df.fillna(0, inplace=True)
        display_df = display_df.astype(int)

        # --- Exibição das Métricas Totais ---
        st.subheader("Totais de Tarefas Cumpridas", divider='green')
        
        # Estilo CSS para os cartões de métrica
        st.markdown("""
        <style>
        [data-testid="stMetric"] {
            background-color: #f0f2f6;
            border: 1px solid #111111;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
        
        totais_por_etapa = display_df[lista_tags].sum()
        
        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
        cols_metricas = [col_metric1, col_metric2, col_metric3, col_metric4]
        
        # Adiciona a métrica de total de famílias primeiro, usando o valor calculado antes dos filtros
        with cols_metricas[0]:
             st.metric("TOTAL DE FAMÍLIAS", total_familias_geral)

        i = 1 # Começa no segundo slot de métrica
        for tag, total in totais_por_etapa.items():
            if i < len(cols_metricas) * 2: # Limita o número de métricas para não sobrecarregar
                with cols_metricas[i % len(cols_metricas)]:
                    st.metric(label=tag, value=int(total))
                i += 1
        
        # --- Tabela de Detalhamento ---
        st.subheader("Contagem de Tarefas por Status e Consultor", divider='green')
        
        crosstab_sorted = display_df.sort_index()

        # Adiciona a linha de total
        total_row = crosstab_sorted.sum().to_frame('TOTAL').T
        crosstab_with_total = pd.concat([crosstab_sorted, total_row])

        st.dataframe(ensure_pandas_df(crosstab_with_total), use_container_width=True)
                
    except Exception as e:
        st.error(f"Erro ao processar tarefas cumpridas: {e}")
        # Se houver um erro, é melhor parar aqui para não mostrar dados inconsistentes.
        return 
    
    # --- MÉTRICAS DE TEMPO MÉDIO ---
    st.markdown("---")
    st.subheader("Tempo Médio por Etapa (com base nos filtros)", divider='orange')
    
    df_tempo = df_filtrado.copy()

    etapas_config_tempo = {
        "Tempo de Procuração": ('PROCURAÇÃO - DATA ENVIO', 'PROCURAÇÃO - DATA CONCLUSÃO'),
        "Tempo Análise Docs": ('ANALISE - DATA DE ENVIO', 'ANALISE - DATA CONCLUSÃO'),
        "Tempo de Tradução": ('TRADUÇÃO - DATA DE INICIO', 'TRADUÇÃO - DATA DE ENTREGA'),
        "Tempo de Apostila": ('APOSTILA - DATA DE INICIO', 'APOSTILA - DATA DE ENTREGA'),
        "Tempo de Drive": ('DRIVE - DATA DE INICIO', 'DRIVE - DATA DE ENTREGA')
    }

    for nome_coluna_tempo, (start_col, end_col) in etapas_config_tempo.items():
        if start_col in df_tempo.columns and end_col in df_tempo.columns:
            start_date = parse_flexible_date(df_tempo[start_col])
            end_date = parse_flexible_date(df_tempo[end_col])
            df_tempo[nome_coluna_tempo] = (end_date - start_date).dt.days
        else:
            df_tempo[nome_coluna_tempo] = pd.NA
            
    if col_inicio_processo in df_tempo.columns and col_fim_processo in df_tempo.columns:
        start_date_total = parse_flexible_date(df_tempo[col_inicio_processo])
        end_date_total = parse_flexible_date(df_tempo[col_fim_processo])
        df_tempo['Tempo de Processo Total'] = (end_date_total - start_date_total).dt.days
    else:
        df_tempo['Tempo de Processo Total'] = pd.NA

    # Calcular dados das certidões brasileiras
    df_cert_br = calcular_tempo_certidoes_brasileiras(df_cartorio)
    if not df_cert_br.empty:
        # Precisamos garantir que o ID FAMÍLIA exista em df_tempo para o merge
        if 'ID FAMÍLIA' in df_tempo.columns:
            df_tempo = pd.merge(df_tempo, df_cert_br, on='ID FAMÍLIA', how='left')
        else:
            st.warning("A coluna 'ID FAMÍLIA' não foi encontrada para calcular o tempo das certidões BR.")

    colunas_media = ['Tempo de Processo Total'] + list(etapas_config_tempo.keys())
    medias = {col: df_tempo[col].mean() for col in colunas_media if col in df_tempo.columns}
    
    if 'Média Certidões BR' in df_tempo.columns:
        media_cert_br = df_tempo['Média Certidões BR'].mean()
        if pd.notna(media_cert_br):
            medias['Tempo Certidões BR'] = media_cert_br

    if medias:
        # Filtrar apenas as métricas que têm valor
        medias_validas = {k: v for k, v in medias.items() if pd.notna(v)}
        
        if medias_validas:
            num_cols_metrics = min(len(medias_validas), 4)
            cols = st.columns(num_cols_metrics)
            
            i = 0
            for etapa, media in medias_validas.items():
                with cols[i % num_cols_metrics]:
                    st.metric(label=etapa, value=f"{int(round(media))} dias")
                    i += 1
        else:
            st.info("Nenhuma métrica de tempo pôde ser calculada para os filtros selecionados.")
            
    else:
        st.info("Nenhuma métrica de tempo pôde ser calculada para os filtros selecionados.")


    # --- Exibição dos Dados Brutos Filtrados ---
    try:
        with st.expander("Ver dados brutos filtrados"):
            colunas_para_exibir = [
                'ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', 'STATUS GERAL', 'PENDENCIAS',
                'PROCURAÇÃO - STATUS', 'ANALISE - STATUS', 'TRADUÇÃO - STATUS', 
                'APOSTILA - STATUS', 'DRIVE - STATUS'
            ]
            colunas_existentes = [col for col in colunas_para_exibir if col in df_filtrado.columns]
            
            dados_brutos = df_filtrado[colunas_existentes]
            
            st.dataframe(ensure_pandas_df(dados_brutos), use_container_width=True)
            
    except Exception as e:
        st.error(f"Erro ao exibir dados brutos: {e}")