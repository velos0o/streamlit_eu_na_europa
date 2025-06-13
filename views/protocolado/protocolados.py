import streamlit as st
import pandas as pd
import gspread

@st.cache_data(ttl=300)
def carregar_dados_protocolados():
    """
    Carrega dados da planilha Google Sheets de forma segura usando uma Conta de Serviço.
    """
    try:
        # Autenticar usando as credenciais do secrets.toml
        creds = st.secrets["google"]["sheets"]
        sa = gspread.service_account_from_dict(creds)
        
        # Abrir a planilha pelo ID
        sheet_id = "15L7SdGgbF3nhiE3ptk7WFmuTwbxSY3rA1hfCnYmMFMM"
        sh = sa.open_by_key(sheet_id)
        
        # Selecionar a primeira aba (gid=0)
        worksheet = sh.get_worksheet(0)
        
        # Ler os dados e pular as duas primeiras linhas do cabeçalho
        data = worksheet.get_all_values()
        if len(data) < 3:
            return pd.DataFrame() # Retorna DF vazio se não houver dados suficientes
            
        df = pd.DataFrame(data[2:])
        
        # Definir nomes de colunas de 'A' a 'V'
        num_cols = len(df.columns)
        col_names = [chr(ord('A') + i) for i in range(num_cols)]
        df.columns = col_names[:num_cols]

        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Planilha não encontrada. Verifique o ID e se a conta de serviço tem permissão de 'Leitor'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha: {e}")
        return pd.DataFrame()

def show_protocolados():
    """
    Exibe o relatório de Protocolados com análises e filtros interativos.
    """
    st.header("Relatório de Protocolados", divider='rainbow')
    
    df_raw = carregar_dados_protocolados()
    
    if df_raw.empty:
        st.warning("Não foi possível carregar os dados ou a planilha está vazia.")
        return

    # Mapeamento e renomeação de colunas
    mapeamento_colunas = {
        'B': 'ID FAMÍLIA', 'C': 'CONSULTOR RESPONSÁVEL', 'D': 'STATUS GERAL', 'E': 'PENDENCIAS',
        'F': 'PROCURAÇÃO - STATUS', 'G': 'PROCURAÇÃO - ADM RESPONSAVEL', 'H': 'PROCURAÇÃO - DATA ENVIO', 'I': 'PROCURAÇÃO - DATA CONCLUSÃO',
        'J': 'ANALISE - RESPONSÁVEL', 'K': 'ANALISE - DATA DE ENVIO', 'L': 'ANALISE - STATUS', 'M': 'ANALISE - DATA CONCLUSÃO',
        'N': 'TRADUÇÃO - DATA DE INICIO', 'O': 'TRADUÇÃO - STATUS', 'P': 'TRADUÇÃO - DATA DE ENTREGA',
        'Q': 'APOSTILA - DATA DE INICIO', 'R': 'APOSTILA - STATUS', 'S': 'APOSTILA - DATA DE ENTREGA',
        'T': 'DRIVE - DATA DE INICIO', 'U': 'DRIVE - STATUS', 'V': 'DRIVE - DATA DE ENTREGA',
    }
    
    df = df_raw.rename(columns=mapeamento_colunas)
    if 'PENDENCIAS' in df.columns:
        df['PENDENCIAS'] = df['PENDENCIAS'].fillna('SEM PENDENCIAS').replace('', 'SEM PENDENCIAS')

    # --- Filtros na Sidebar ---
    st.sidebar.header("Filtros de Análise")
    
    consultores_unicos = sorted(df['CONSULTOR RESPONSÁVEL'].dropna().unique())
    status_unicos = sorted(df['STATUS GERAL'].dropna().unique())
    
    consultores_selecionados = st.sidebar.multiselect(
        "Consultor Responsável", options=consultores_unicos, default=consultores_unicos
    )
    status_selecionado = st.sidebar.multiselect(
        "Status Geral", options=status_unicos, default=status_unicos
    )

    # Aplicação dos filtros
    df_filtrado = df[
        df['CONSULTOR RESPONSÁVEL'].isin(consultores_selecionados) &
        df['STATUS GERAL'].isin(status_selecionado)
    ]

    # --- Análise 1: Métricas Gerais ---
    st.subheader("Visão Geral", divider='blue')
    
    col1, col2 = st.columns(2)
    with col1:
        total_familias = df_filtrado['ID FAMÍLIA'].nunique()
        st.metric("TOTAL DE FAMÍLIAS", total_familias)

    # Contagem total de cada tipo de pendência
    pendencias_gerais = df_filtrado[df_filtrado['PENDENCIAS'] != 'SEM PENDENCIAS']['PENDENCIAS']
    if not pendencias_gerais.empty:
        lista_tags = [
            'Emissão', 'Comune', 'Analise Documental', 
            'Tradução', 'Apostilamento', 'Drive', 'Procuração'
        ]
        
        contagem_tags = pd.Series(dtype=int)
        if not pendencias_gerais.empty:
            contagem_tags = pendencias_gerais.str.split(',').explode().str.strip().value_counts()
            
        st.write("Totais por Tipo de Pendência:")
        
        # Exibir métricas em colunas
        num_cols = 4 
        cols = st.columns(num_cols)
        
        for i, tag in enumerate(lista_tags):
            with cols[i % num_cols]:
                st.metric(label=tag, value=contagem_tags.get(tag, 0))

    # --- Análise 2: Pendências por Responsável ---
    st.subheader("Pendências por Responsável", divider='blue')

    pendencias_df = df_filtrado[['CONSULTOR RESPONSÁVEL', 'PENDENCIAS']].copy()
    pendencias_df = pendencias_df[pendencias_df['PENDENCIAS'] != 'SEM PENDENCIAS']

    if pendencias_df.empty:
        st.info("Nenhuma pendência encontrada para os filtros selecionados.")
    else:
        # Processar as pendências
        pendencias_df['PENDENCIAS_LIST'] = pendencias_df['PENDENCIAS'].str.split(',')
        pendencias_exploded = pendencias_df.explode('PENDENCIAS_LIST')
        pendencias_exploded['PENDENCIA_TIPO'] = pendencias_exploded['PENDENCIAS_LIST'].str.strip()

        # Tabela: Detalhamento de pendências por consultor e tipo
        st.write("Contagem de Pendências por Tipo e Consultor")
        crosstab_pendencias = pd.crosstab(
            index=pendencias_exploded['CONSULTOR RESPONSÁVEL'],
            columns=pendencias_exploded['PENDENCIA_TIPO']
        )
        
        # Garantir que todas as colunas de pendências possíveis existam
        lista_tags = [
            'Emissão', 'Comune', 'Analise Documental', 
            'Tradução', 'Apostilamento', 'Drive', 'Procuração'
        ]
        for tag in lista_tags:
            if tag not in crosstab_pendencias.columns:
                crosstab_pendencias[tag] = 0
        
        # Reordenar colunas e adicionar total
        crosstab_pendencias = crosstab_pendencias[lista_tags]
        crosstab_pendencias['Total de Pendências'] = crosstab_pendencias.sum(axis=1)

        st.dataframe(crosstab_pendencias.sort_values(by='Total de Pendências', ascending=False), use_container_width=True)

        # Gráfico: Detalhamento de pendências por tipo e consultor
        st.write("Gráfico de Detalhamento das Pendências")
        st.bar_chart(crosstab_pendencias.drop(columns=['Total de Pendências']))

    # --- Exibição dos Dados Brutos Filtrados ---
    with st.expander("Ver dados brutos filtrados"):
        colunas_para_exibir = list(mapeamento_colunas.values())
        colunas_existentes = [col for col in colunas_para_exibir if col in df_filtrado.columns]
        st.dataframe(df_filtrado[colunas_existentes]) 