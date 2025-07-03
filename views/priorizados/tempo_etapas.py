import streamlit as st
import pandas as pd
from utils.dataframe_utils import ensure_pandas_df

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


def show_tempo_etapas(df_filtrado, df_cartorio):
    """
    Exibe uma tabela com o tempo de conclusão de cada etapa do processo por família.
    """
    st.caption("Esta seção calcula o tempo (em dias) que cada família levou para concluir as principais etapas do processo.")

    if df_filtrado.empty:
        st.warning("Não há dados para exibir com os filtros selecionados.")
        return
        
    # Calcular dados das certidões brasileiras
    df_cert_br = calcular_tempo_certidoes_brasileiras(df_cartorio)

    # Mapeamento das etapas e suas respectivas colunas de data
    etapas_config = {
        "Tempo de Procuração": ('PROCURAÇÃO - DATA ENVIO', 'PROCURAÇÃO - DATA CONCLUSÃO'),
        "Tempo Análise Docs": ('ANALISE - DATA DE ENVIO', 'ANALISE - DATA CONCLUSÃO'),
        "Tempo de Tradução": ('TRADUÇÃO - DATA DE INICIO', 'TRADUÇÃO - DATA DE ENTREGA'),
        "Tempo de Apostila": ('APOSTILA - DATA DE INICIO', 'APOSTILA - DATA DE ENTREGA'),
        "Tempo de Drive": ('DRIVE - DATA DE INICIO', 'DRIVE - DATA DE ENTREGA')
    }
    
    # Colunas para o tempo total do processo
    col_inicio_processo = 'Data de Inicio das Tratativas'
    col_fim_processo = 'DATA DE FINALIZAÇÃO DA PASTA'

    # Selecionar colunas relevantes e criar uma cópia
    colunas_necessarias = ['A', 'ID FAMÍLIA', col_inicio_processo, col_fim_processo] 
    for start_col, end_col in etapas_config.values():
        colunas_necessarias.extend([start_col, end_col])
    
    colunas_existentes = [col for col in colunas_necessarias if col in df_filtrado.columns]
    
    if 'A' not in colunas_existentes or 'ID FAMÍLIA' not in colunas_existentes:
        st.error("As colunas 'A' (Nome da Família) e 'ID FAMÍLIA' são essenciais e não foram encontradas.")
        return

    df_tempo = df_filtrado[colunas_existentes].copy()
    df_tempo = df_tempo.rename(columns={'A': 'Nome da Família'})

    for nome_coluna_tempo, (start_col, end_col) in etapas_config.items():
        if start_col in df_tempo.columns and end_col in df_tempo.columns:
            start_date = pd.to_datetime(df_tempo[start_col], format='%d/%m/%Y', dayfirst=True, errors='coerce')
            end_date = pd.to_datetime(df_tempo[end_col], format='%d/%m/%Y', dayfirst=True, errors='coerce')
            df_tempo[nome_coluna_tempo] = (end_date - start_date).dt.days
        else:
            df_tempo[nome_coluna_tempo] = pd.NA
            
    # Calcular o tempo total do processo
    if col_inicio_processo in df_tempo.columns and col_fim_processo in df_tempo.columns:
        # Corrigido: Assegurar que ambas as datas sejam lidas com formato completo Dia/Mês/Ano
        start_date_total = pd.to_datetime(df_tempo[col_inicio_processo], format='%d/%m/%Y', dayfirst=True, errors='coerce')
        end_date_total = pd.to_datetime(df_tempo[col_fim_processo], format='%d/%m/%Y', dayfirst=True, errors='coerce')
        df_tempo['Tempo de Processo Total'] = (end_date_total - start_date_total).dt.days
    else:
        df_tempo['Tempo de Processo Total'] = pd.NA

    df_final = pd.merge(df_tempo, df_cert_br, on='ID FAMÍLIA', how='left')
    df_final = df_final.set_index('Nome da Família')
    
    colunas_para_exibir = list(etapas_config.keys()) + ['Dias Certidões BR', 'Andamento Certidões BR', 'Tempo de Processo Total']
    
    # Garantir que as colunas existam no dataframe antes de tentar acessá-las
    colunas_existentes_final = [col for col in colunas_para_exibir if col in df_final.columns]
    
    df_final_display = df_final[colunas_existentes_final].copy()
    df_final_display.dropna(how='all', inplace=True)

    # --- MÉTRICAS DE MÉDIA ---
    st.subheader("Tempo Médio por Etapa")
    
    # Estilo CSS para os cartões de métrica
    st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #f0f2f6; /* cinza claro */
        border: 1px solid #111111; /* borda preta */
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Calcular médias das etapas da planilha
    colunas_media = ['Tempo de Processo Total'] + list(etapas_config.keys())
    medias = {col: df_final[col].mean() for col in colunas_media if col in df_final.columns}
    
    # Calcular média das certidões brasileiras separadamente
    media_cert_br = df_final['Média Certidões BR'].mean()
    if pd.notna(media_cert_br):
        medias['Tempo Certidões BR'] = media_cert_br

    # Prevenir erro se 'medias' estiver vazio
    if medias:
        cols = st.columns(len(medias))
        for i, (etapa, media) in enumerate(medias.items()):
            with cols[i]:
                st.metric(label=etapa, value=f"{media:.1f} dias" if pd.notna(media) else "N/A")

    st.markdown("---")
    
    st.subheader("Detalhes por Família")
    if df_final_display.empty:
        st.info("Nenhum tempo de etapa pôde ser calculado para os dados filtrados.")
    else:
        search_term = st.text_input("Buscar por Nome da Família:", placeholder="Digite um nome para filtrar...")

        # Garantir que estamos usando o dataframe com as colunas corretas
        df_display = ensure_pandas_df(df_final_display)
        
        if search_term:
            df_display = df_display[df_display.index.str.contains(search_term, case=False, na=False)]

        if df_display.empty:
            st.warning("Nenhuma família encontrada com o termo buscado.")
        else:
            # Formatação manual dos valores numéricos para incluir 'dias' onde aplicável
            df_styled = df_display.copy()
            for col in etapas_config.keys():
                if col in df_styled.columns:
                    # Aplicar formatação apenas em colunas que são de tempo (numéricas)
                    df_styled[col] = df_styled[col].apply(lambda x: f"{int(x)} dias" if pd.notna(x) and isinstance(x, (int, float)) else x)
            if 'Tempo de Processo Total' in df_styled.columns:
                df_styled['Tempo de Processo Total'] = df_styled['Tempo de Processo Total'].apply(lambda x: f"{int(x)} dias" if pd.notna(x) and isinstance(x, (int, float)) else x)
            
            st.dataframe(df_styled, use_container_width=True)
        
        with st.expander("Ver dados brutos de datas utilizados no cálculo"):
            # Exibe o dataframe que contém as datas originais
            st.dataframe(ensure_pandas_df(df_tempo), use_container_width=True) 