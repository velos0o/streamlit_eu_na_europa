import streamlit as st
import pandas as pd
from datetime import datetime, time # Adicionado time

# --- Mapeamento e Categorização de Campos ---

# Mapeia nomes técnicos para nomes legíveis e categorias
CAMPOS_DATA = {
    'UF_CRM_DATA_CERTIDAO_EMITIDA': {'nome': 'Certidão Emitida', 'categoria': 'SUCESSO'},
    'UF_CRM_DATA_CERTIDAO_FISICA_ENTREGUE': {'nome': 'Certidão Física Entregue', 'categoria': 'SUCESSO'},
    'UF_CRM_DATA_CERTIDAO_FISICA_ENVIADA': {'nome': 'Certidão Física Enviada', 'categoria': 'SUCESSO'},

    'UF_CRM_DATA_AGUARDANDOCARTORIO_ORIGEM': {'nome': 'Aguardando Cartório Origem', 'categoria': 'EM ANDAMENTO'},
    'UF_CRM_DATA_MONTAR_REQUERIMENTO': {'nome': 'Montagem Requerimento', 'categoria': 'EM ANDAMENTO'},
    'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM': {'nome': 'Solicitação Cartório Origem', 'categoria': 'EM ANDAMENTO'},
    'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM_PRIORIDADE': {'nome': 'Solic. Cart. Origem (Prior.)', 'categoria': 'EM ANDAMENTO'},
    'UF_CRM_DATA_SOLICITAR_REQUERIMENTO': {'nome': 'Solicitação Requerimento', 'categoria': 'EM ANDAMENTO'},

    'UF_CRM_DEVOLUCAO_ADM': {'nome': 'Devolução ADM', 'categoria': 'FALHA'},
    'UF_CRM_DEVOLUCAO_ADM_VERIFICADO': {'nome': 'Devolução ADM Verificada', 'categoria': 'FALHA'},
    'UF_CRM_DEVOLUTIVA_BUSCA': {'nome': 'Devolutiva Busca', 'categoria': 'FALHA'},
    'UF_CRM_DEVOLUTIVA_REQUERIMENTO': {'nome': 'Devolutiva Requerimento', 'categoria': 'FALHA'},
}

# Campos de responsável (usados para a tabela) - apenas a lista de nomes técnicos
CAMPOS_RESPONSAVEL = [
    'UF_CRM_MONTAGEM_PASTA_RESPONSAVEL',
    'UF_CRM_RESPONSAVEL__BUSCA',
    'UF_CRM_RESPONSAVEL_AGUARDANDO_CARTORIO_DE_ORIGEM',
    'UF_CRM_RESPONSAVEL_ANTES_MOVIMENTACAO',
    'UF_CRM_RESPONSAVEL_CERTIDAO_EMITIDA',
    'UF_CRM_RESPONSAVEL_CERTIDO_FISICA_ENTREGUE',
    'UF_CRM_RESPONSAVEL_CERTIDO_FISICA_ENVIADA',
    'UF_CRM_RESPONSAVEL_DEVOLUCAO_ADM',
    'UF_CRM_RESPONSAVEL_DEVOLUCAO_ADM_VERIFICADO',
    'UF_CRM_RESPONSAVEL_DEVOLUTIVA_BUSCA',
    'UF_CRM_RESPONSAVEL_DEVOLVIDOREQUERIMENTO',
    'UF_CRM_RESPONSAVEL_SOLICITACAO_DUPLICADA',
    'UF_CRM_RESPONSAVEL_SOLICITAR_CARTORIO_ORIGEM',
]

# Mapeia campos de responsável para os campos de data correspondentes (aproximado)
# IMPORTANTE: Este mapeamento pode precisar de ajuste fino!
MAPA_RESP_DATA = {
    'UF_CRM_RESPONSAVEL_CERTIDAO_EMITIDA': 'UF_CRM_DATA_CERTIDAO_EMITIDA',
    'UF_CRM_RESPONSAVEL_CERTIDO_FISICA_ENTREGUE': 'UF_CRM_DATA_CERTIDAO_FISICA_ENTREGUE',
    'UF_CRM_RESPONSAVEL_CERTIDO_FISICA_ENVIADA': 'UF_CRM_DATA_CERTIDAO_FISICA_ENVIADA',
    'UF_CRM_RESPONSAVEL_AGUARDANDO_CARTORIO_DE_ORIGEM': 'UF_CRM_DATA_AGUARDANDOCARTORIO_ORIGEM',
    'UF_CRM_MONTAGEM_PASTA_RESPONSAVEL': 'UF_CRM_DATA_MONTAR_REQUERIMENTO', # Suposição
    'UF_CRM_RESPONSAVEL_SOLICITAR_CARTORIO_ORIGEM': 'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM',
    # 'UF_CRM_RESPONSAVEL_SOLICITAR_CARTORIO_ORIGEM_PRIORIDADE': 'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM_PRIORIDADE', # Campo resp. não listado?
    # 'UF_CRM_RESPONSAVEL_SOLICITAR_REQUERIMENTO': 'UF_CRM_DATA_SOLICITAR_REQUERIMENTO', # Campo resp. não listado?
    'UF_CRM_RESPONSAVEL_DEVOLUCAO_ADM': 'UF_CRM_DEVOLUCAO_ADM',
    'UF_CRM_RESPONSAVEL_DEVOLUCAO_ADM_VERIFICADO': 'UF_CRM_DEVOLUCAO_ADM_VERIFICADO',
    'UF_CRM_RESPONSAVEL_DEVOLUTIVA_BUSCA': 'UF_CRM_DEVOLUTIVA_BUSCA',
    'UF_CRM_RESPONSAVEL_DEVOLVIDOREQUERIMENTO': 'UF_CRM_DEVOLUTIVA_REQUERIMENTO', # Suposição
    # Faltam mapeamentos para: _BUSCA, _ANTES_MOVIMENTACAO, _SOLICITACAO_DUPLICADA
}

def exibir_producao(df_original):
    st.subheader("Produção")

    # --- Carregar CSS Compilado ---
    # Tentativa de carregar o CSS externo para estilização dos cards
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado. A estilização dos cards pode estar ausente.")
    # --- Fim Carregar CSS ---

    if df_original.empty:
        st.warning("Não há dados disponíveis para análise de produção.")
        return

    df = df_original.copy() # Trabalhar com uma cópia

    # --- Verificar Colunas Essenciais ---
    colunas_data_necessarias = list(CAMPOS_DATA.keys())
    colunas_resp_necessarias = CAMPOS_RESPONSAVEL
    colunas_presentes = df.columns.tolist()

    colunas_data_faltando = [col for col in colunas_data_necessarias if col not in colunas_presentes]
    colunas_resp_faltando = [col for col in colunas_resp_necessarias if col not in colunas_presentes]

    if colunas_data_faltando:
        st.error(f"Erro: As seguintes colunas de DATA estão faltando no DataFrame e são necessárias para esta análise: {', '.join(colunas_data_faltando)}")
        st.info("Verifique se os nomes dos campos estão corretos e se o data_loader.py está carregando estas colunas.")
        # return # Poderia parar aqui, mas vamos tentar continuar com o que temos

    if colunas_resp_faltando:
        st.warning(f"Aviso: As seguintes colunas de RESPONSÁVEL estão faltando e são necessárias para a tabela de análise por responsável: {', '.join(colunas_resp_faltando)}")
        # A tabela de responsáveis pode ficar incompleta ou vazia

    # --- Filtro de Data ---
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input("Data Inicial", value=pd.to_datetime(datetime.now().date()) - pd.Timedelta(days=30))
    with col2:
        data_final = st.date_input("Data Final", value=pd.to_datetime(datetime.now().date()))

    # Converter para datetime com hora inicial e final para incluir o dia todo
    dt_inicial = pd.to_datetime(datetime.combine(data_inicial, time.min))
    dt_final = pd.to_datetime(datetime.combine(data_final, time.max))

    # --- Processamento e Filtragem ---
    # Converter colunas de data para datetime, tratando erros
    for col in colunas_data_necessarias:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        else:
            df[col] = pd.NaT # Adiciona coluna vazia se não existir

    # Criar uma máscara para filtrar registros onde QUALQUER data relevante cai no período
    mascara_periodo = pd.Series(False, index=df.index)
    for col in colunas_data_necessarias:
         if col in df.columns: # Checa novamente se a coluna existe após conversão/adição
            mascara_periodo = mascara_periodo | ((df[col] >= dt_inicial) & (df[col] <= dt_final))

    df_filtrado = df[mascara_periodo].copy()

    if df_filtrado.empty:
        st.info(f"Nenhuma atividade encontrada entre {data_inicial.strftime('%d/%m/%Y')} e {data_final.strftime('%d/%m/%Y')}.")
        return

    # --- Exibir Métricas por Data (Cards Categorizados com Estilo) ---
    st.markdown("#### Atividades no Período")

    metricas_por_categoria = {'SUCESSO': [], 'EM ANDAMENTO': [], 'FALHA': []}

    # Calcular contagem para cada campo DENTRO do período
    for col_tecnico, info in CAMPOS_DATA.items():
        if col_tecnico in df_filtrado.columns:
             # Conta IDs únicos onde a data específica cai no período
            contagem = df_filtrado.loc[
                (df_filtrado[col_tecnico] >= dt_inicial) & (df_filtrado[col_tecnico] <= dt_final),
                'ID' # Assume que a coluna 'ID' existe e é o identificador único
            ].nunique()
            metricas_por_categoria[info['categoria']].append({'label': info['nome'], 'value': contagem})
        else:
            # Adiciona métrica zerada se a coluna estiver faltando
            metricas_por_categoria[info['categoria']].append({'label': f"{info['nome']} (Campo Ausente)", 'value': 0})

    # Renderizar as métricas nas colunas usando a estrutura de cards
    col_suc, col_and, col_fal = st.columns(3)

    with col_suc:
        st.markdown(f'<h5 class="category-title" style="color: #198754; margin-bottom: 10px;">✅ SUCESSO</h5>', unsafe_allow_html=True)
        st.markdown('<div class="cards-grid">', unsafe_allow_html=True)
        for metrica in metricas_por_categoria['SUCESSO']:
            st.markdown(f"""
            <div class="card-visao-geral card-visao-geral--sucesso fade-in">
                <div class="card-visao-geral__title">{metrica['label']}</div>
                <div class="card-visao-geral__metrics">
                    <span class="card-visao-geral__quantity">{metrica['value']:,}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_and:
        st.markdown(f'<h5 class="category-title" style="color: #ffc107; margin-bottom: 10px;">⏳ EM ANDAMENTO</h5>', unsafe_allow_html=True)
        st.markdown('<div class="cards-grid">', unsafe_allow_html=True)
        for metrica in metricas_por_categoria['EM ANDAMENTO']:
            st.markdown(f"""
            <div class="card-visao-geral card-visao-geral--em-andamento fade-in">
                <div class="card-visao-geral__title">{metrica['label']}</div>
                <div class="card-visao-geral__metrics">
                    <span class="card-visao-geral__quantity">{metrica['value']:,}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_fal:
        st.markdown(f'<h5 class="category-title" style="color: #dc3545; margin-bottom: 10px;">❌ FALHA</h5>', unsafe_allow_html=True)
        st.markdown('<div class="cards-grid">', unsafe_allow_html=True)
        for metrica in metricas_por_categoria['FALHA']:
            st.markdown(f"""
            <div class="card-visao-geral card-visao-geral--falha fade-in">
                <div class="card-visao-geral__title">{metrica['label']}</div>
                <div class="card-visao-geral__metrics">
                    <span class="card-visao-geral__quantity">{metrica['value']:,}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Tabela de Análise por Responsável ---
    st.markdown("#### Análise por Responsável no Período")

    # Preparar dados para a tabela pivot
    dados_pivot = []

    # Iterar sobre os registros filtrados pelo período
    for index, row in df_filtrado.iterrows():
        id_processo = row['ID'] # Assume que 'ID' é o identificador do processo

        # Verificar cada par Responsável/Data mapeado
        for resp_col, data_col in MAPA_RESP_DATA.items():
            # Verificar se as colunas existem e se o responsável não é nulo
            if resp_col in row.index and data_col in row.index and pd.notna(row[resp_col]):
                # Verificar se a data correspondente está no período
                if pd.notna(row[data_col]) and dt_inicial <= row[data_col] <= dt_final:
                    responsavel_id = str(row[resp_col]) # Usar ID como string
                    atividade_nome = CAMPOS_DATA.get(data_col, {}).get('nome', data_col) # Nome legível da atividade/data

                    # Adicionar à lista para pivotagem
                    dados_pivot.append({
                        'Responsavel_ID': responsavel_id,
                        'Atividade': atividade_nome,
                        'ID_Processo': id_processo
                    })

    if not dados_pivot:
        st.info("Nenhuma atividade de responsável encontrada no período selecionado para as colunas mapeadas.")
    else:
        df_pivot_base = pd.DataFrame(dados_pivot)

        # Verificar se df_pivot_base não está vazio antes de pivotar
        if not df_pivot_base.empty:
            try:
                 # Criar tabela pivot: Responsável vs Atividade, contando IDs únicos de processo
                tabela_responsaveis = pd.pivot_table(
                    df_pivot_base,
                    values='ID_Processo',
                    index='Responsavel_ID',
                    columns='Atividade',
                    aggfunc='nunique', # Conta quantos processos únicos cada responsável fez por atividade
                    fill_value=0 # Preenche com 0 onde não houve atividade
                )

                 # Ordenar colunas (atividades) pela ordem definida em CAMPOS_DATA se possível
                ordem_colunas = [info['nome'] for info in CAMPOS_DATA.values() if info['nome'] in tabela_responsaveis.columns]
                tabela_responsaveis = tabela_responsaveis[ordem_colunas]

                # Adicionar uma coluna TOTAL
                tabela_responsaveis['TOTAL GERAL'] = tabela_responsaveis.sum(axis=1)

                # Ordenar por TOTAL GERAL (descendente)
                tabela_responsaveis = tabela_responsaveis.sort_values('TOTAL GERAL', ascending=False)

                # --- Barra de Busca por Responsável --- 
                busca_responsavel = st.text_input("Buscar Responsável:", key="busca_resp_prod")

                tabela_filtrada = tabela_responsaveis
                if busca_responsavel:
                    # Filtrar o índice (Responsavel_ID) - case-insensitive
                    tabela_filtrada = tabela_responsaveis[
                        tabela_responsaveis.index.str.contains(busca_responsavel, case=False, na=False)
                    ]
                
                if tabela_filtrada.empty and busca_responsavel:
                    st.warning(f"Nenhum responsável encontrado para o ID: '{busca_responsavel}'")
                elif not tabela_filtrada.empty:
                    st.dataframe(tabela_filtrada.style.format("{:,}"), use_container_width=True) # Formata números
                    st.caption("A tabela mostra a contagem de processos únicos tratados por cada responsável (ID) em cada atividade, dentro do período selecionado.")
                # Não mostrar nada se a busca inicial for vazia e não houver resultados

            except Exception as e:
                 st.error(f"Ocorreu um erro ao gerar a tabela de responsáveis: {str(e)}")
                 st.dataframe(df_pivot_base) # Mostra dados brutos se pivot falhar
        else:
             st.info("Nenhuma atividade de responsável encontrada no período selecionado após o processamento.")

    # Adicionar aqui a lógica e visualizações de produção
    # st.info("🚧 Seção em construção.") # Remover esta linha

    # Adicionar lógica e visualizações de produção aqui 