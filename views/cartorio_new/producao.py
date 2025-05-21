import streamlit as st
import pandas as pd
from datetime import datetime, time
import numpy as np # Adicionado para cálculos de desvio padrão
import os # Importar os para manipulação de caminhos
import requests # Adicionado para chamadas HTTP

# Importar funções do novo utils
from .utils import fetch_supabase_producao_data # Adicionado

# Obter o diretório do arquivo atual
_PRODUCAO_DIR = os.path.dirname(os.path.abspath(__file__))
# Construir o caminho para a pasta assets subindo dois níveis (views/cartorio_new -> streamlit_eu_na_europa)
_ASSETS_DIR = os.path.join(_PRODUCAO_DIR, '..', '..', 'assets')
_CSS_PATH = os.path.join(_ASSETS_DIR, 'styles', 'css', 'main.css')

# --- Mapeamento e Categorização de Campos ---

# Mapeia nomes técnicos para nomes legíveis, categorias e origens (se aplicável)
CAMPOS_DATA = {
    # SUCESSO
    'UF_CRM_34_DATA_CERTIDAO_EMITIDA': {'nome': 'DATA CERTIDÃO EMITIDA (SPA)', 'categoria': 'SUCESSO'},
    'UF_CRM_34_DATA_CERTIDAO_ENTREGUE': {'nome': 'DATA CERTIDÃO ENTREGUE (SPA)', 'categoria': 'SUCESSO'},

    # EM ANDAMENTO
    'UF_CRM_34_DATA_AGUARDANDO_CARTORIO_ORIGEM': {'nome': 'DATA AGUARDANDO CART. ORIGEM (SPA)', 'categoria': 'EM ANDAMENTO'},
    'UF_CRM_34_DATA_MONTAGEM_REQUERIMENTO': {'nome': 'DATA MONTAGEM REQUERIMENTO (SPA)', 'categoria': 'EM ANDAMENTO'},
    'UF_CRM_34_DATA_SOLICITAR_CARTORIO_ORIGEM': {'nome': 'DATA SOLICITAR CART. ORIGEM (SPA)', 'categoria': 'EM ANDAMENTO'},
    'UF_CRM_34_DATA_ASSINATURA_REQUERIMENTO': {'nome': 'DATA ASSINATURA REQUERIMENTO (SPA)', 'categoria': 'EM ANDAMENTO'},
    'UF_CRM_DATA_BUSCA_CRC_AUTOMACAO': {'nome': 'DATA BUSCA CRC (SPA)', 'categoria': 'EM ANDAMENTO'},
    'UF_CRM_34_DATA_PESQUISA_BR': {'nome': 'DATA PESQUISA BR (SPA)', 'categoria': 'EM ANDAMENTO'},

    # FALHA
    'UF_CRM_34_DATA_DEVOLUCAO_ADM': {'nome': 'DATA DEVOLUÇÃO ADM (SPA)', 'categoria': 'FALHA'},
    'UF_CRM_34_DATA_DEVOLUITIVA_BUSCA_CRC': {'nome': 'DATA DEVOLUTIVA BUSCA CRC (SPA)', 'categoria': 'FALHA'},
    'UF_CRM_34_DATA_DEVOLVIDO_REQUERIMENTO': {'nome': 'DATA DEVOLVIDO REQUERIMENTO (SPA)', 'categoria': 'FALHA'},
}

# Campos de responsável (usados para a tabela) - apenas a lista de nomes técnicos
CAMPOS_RESPONSAVEL = [
    'UF_CRM_34_RESPONSAVEL_CERTIDAO_EMITIDA',
    'UF_CRM_34_RESPONSAVEL_DATA_CERTIDAO_ENTREGUE',
    'UF_CRM_RESPONSAVEL_AGUARDANDO_CARTORIO_DE_ORIGEM',
    'UF_CRM_34_RESPONSAVEL_MONTAGEM_REQUERIMENTO',
    'UF_CRM_34_RESPONSAVEL_SOLICITAR_CARTORIO_ORIGEM',
    'UF_CRM_34_RESPONSAVEL_ASSINATURA_REQUERIMENTO',
    'UF_CRM_34_RESPONSAVEL_DEVOLUCAO_ADM',
    'UF_CRM_34_RESPONSAVEL_DEVOLUITIVA_BUSCA_CRC',
    'UF_CRM_34_RESPONSAVEL_DEVOLVIDO_REQUERIMENTO',
    'UF_CRM_RESPONSAVEL_BUSCA_CRC_AUTOMACAO',
    'UF_CRM_34_RESPONSAVEL_PESQUISA_BR',
]

# Mapeia campos de responsável para os campos de data correspondentes
MAPA_RESP_DATA = {
    'UF_CRM_34_RESPONSAVEL_CERTIDAO_EMITIDA': 'UF_CRM_34_DATA_CERTIDAO_EMITIDA',
    'UF_CRM_34_RESPONSAVEL_DATA_CERTIDAO_ENTREGUE': 'UF_CRM_34_DATA_CERTIDAO_ENTREGUE',
    'UF_CRM_RESPONSAVEL_AGUARDANDO_CARTORIO_DE_ORIGEM': 'UF_CRM_34_DATA_AGUARDANDO_CARTORIO_ORIGEM',
    'UF_CRM_34_RESPONSAVEL_MONTAGEM_REQUERIMENTO': 'UF_CRM_34_DATA_MONTAGEM_REQUERIMENTO',
    'UF_CRM_34_RESPONSAVEL_SOLICITAR_CARTORIO_ORIGEM': 'UF_CRM_34_DATA_SOLICITAR_CARTORIO_ORIGEM',
    'UF_CRM_34_RESPONSAVEL_ASSINATURA_REQUERIMENTO': 'UF_CRM_34_DATA_ASSINATURA_REQUERIMENTO',
    'UF_CRM_34_RESPONSAVEL_DEVOLUCAO_ADM': 'UF_CRM_34_DATA_DEVOLUCAO_ADM',
    'UF_CRM_34_RESPONSAVEL_DEVOLUITIVA_BUSCA_CRC': 'UF_CRM_34_DATA_DEVOLUITIVA_BUSCA_CRC',
    'UF_CRM_34_RESPONSAVEL_DEVOLVIDO_REQUERIMENTO': 'UF_CRM_34_DATA_DEVOLVIDO_REQUERIMENTO',
    'UF_CRM_RESPONSAVEL_BUSCA_CRC_AUTOMACAO': 'UF_CRM_DATA_BUSCA_CRC_AUTOMACAO',
    'UF_CRM_34_RESPONSAVEL_PESQUISA_BR': 'UF_CRM_34_DATA_PESQUISA_BR',
}

# --- Configurações do Supabase --- (REMOVIDO - MOVIDO PARA UTILS)
# ATENÇÃO: Substitua pelos seus valores reais! Idealmente, use st.secrets ou variáveis de ambiente.
# SUPABASE_URL = "https://mdjrgbclsayzvnniwarj.supabase.co"  # Substitua pelo URL base do seu projeto Supabase
# SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1kanJnYmNsc2F5enZubml3YXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4NDAyMjMsImV4cCI6MjA2MzQxNjIyM30.c6WQMKBeupAlDs8MXNge06sdgp7Iw4AuvgpCIUrkukM"
# SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1kanJnYmNsc2F5enZubml3YXJqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Nzg0MDIyMywiZXhwIjoyMDYzNDE2MjIzfQ.aotXFfu8t0bXv5NoqCq50qaa0CKH8POAYZETd_W78R8"

# --- Funções Auxiliares Supabase --- (REMOVIDO - MOVIDO PARA UTILS)
# def fetch_supabase_producao_data(data_inicio_str, data_fim_str):
#     """Busca dados da função RPC get_producao_adm_periodo no Supabase."""
#     headers = {
#         "apikey": SUPABASE_ANON_KEY,
#         "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
#         "Content-Type": "application/json",
#         "Prefer": "return=representation"
#     }
#     payload = {
#         "data_inicio": data_inicio_str,
#         "data_fim": data_fim_str
#     }
#     try:
#         rpc_url = f"{SUPABASE_URL}/rest/v1/rpc/get_producao_adm_periodo"
#         response = requests.post(rpc_url, headers=headers, json=payload)
#         response.raise_for_status()  # Levanta um erro para respostas HTTP 4xx/5xx
#         return response.json()
#     except requests.exceptions.HTTPError as http_err:
#         st.error(f"Erro HTTP ao buscar dados do Supabase: {http_err} - {response.text}")
#     except requests.exceptions.RequestException as req_err:
#         st.error(f"Erro de requisição ao buscar dados do Supabase: {req_err}")
#     except Exception as e:
#         st.error(f"Erro inesperado ao processar dados do Supabase: {e}")
#     return []

def exibir_producao(df_original):
    st.subheader("Produção")

    # --- Carregar CSS Compilado ---
    try:
        # Usar o caminho absoluto calculado
        print(f"[Debug Produção] Tentando carregar CSS de: {_CSS_PATH}")
        if os.path.exists(_CSS_PATH):
            with open(_CSS_PATH, 'r', encoding='utf-8') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
                print("[Debug Produção] CSS carregado com sucesso.")
        else:
            st.warning(f"Arquivo CSS principal não encontrado em: {_CSS_PATH}")
            print(f"[Debug Produção] Falha ao carregar CSS: Arquivo não existe em {_CSS_PATH}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar o CSS em Produção: {e}")
    # --- Fim Carregar CSS ---

    if df_original.empty:
        st.warning("Não há dados disponíveis para análise de produção.")
        return

    df = df_original.copy() # Trabalhar com uma cópia

    # --- Verificar Colunas Essenciais e Calcular Primeira Data ---
    colunas_data_necessarias = list(CAMPOS_DATA.keys())
    colunas_resp_necessarias = CAMPOS_RESPONSAVEL
    colunas_presentes = df.columns.tolist()

    colunas_data_faltando = [col for col in colunas_data_necessarias if col not in colunas_presentes]
    colunas_resp_faltando = [col for col in colunas_resp_necessarias if col not in colunas_presentes]

    # Calcular data do primeiro registro ANTES de converter e potencialmente perder dados
    primeira_data_geral = pd.NaT
    datas_validas_geral = []
    for col in colunas_data_necessarias:
        if col in df.columns:
            # Tenta converter para datetime, coerce força NaT em erros
            datas_col = pd.to_datetime(df[col], errors='coerce')
            # Adiciona apenas datas válidas à lista
            datas_validas_geral.append(datas_col.dropna())

    if datas_validas_geral:
        # Concatena todas as séries de datas válidas
        todas_as_datas = pd.concat(datas_validas_geral)
        if not todas_as_datas.empty:
            primeira_data_geral = todas_as_datas.min()

    if colunas_data_faltando:
        st.error(f"Erro: As seguintes colunas de DATA estão faltando no DataFrame e são necessárias para esta análise: {', '.join(colunas_data_faltando)}")
        st.info("Verifique se os nomes dos campos estão corretos e se o data_loader.py está carregando estas colunas.")
        # return # Poderia parar aqui, mas vamos tentar continuar com o que temos

    if colunas_resp_faltando:
        st.warning(f"Aviso: As seguintes colunas de RESPONSÁVEL estão faltando e são necessárias para a tabela de análise por responsável: {', '.join(colunas_resp_faltando)}")
        # A tabela de responsáveis pode ficar incompleta ou vazia

    # Exibir data do primeiro registro
    if pd.notna(primeira_data_geral):
        st.caption(f"🗓️ Primeiro registro de atividade encontrado em: {primeira_data_geral.strftime('%d/%m/%Y')}")
    else:
        st.caption("🗓️ Nenhuma data de atividade encontrada nos dados.")

    # --- Filtro de Data ---
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input("Data Inicial", value=pd.to_datetime(datetime.now().date()) - pd.Timedelta(days=30))
    with col2:
        data_final = st.date_input("Data Final", value=pd.to_datetime(datetime.now().date()))

    # Converter para datetime com hora inicial e final para incluir o dia todo
    dt_inicial = pd.to_datetime(datetime.combine(data_inicial, time.min))
    dt_final = pd.to_datetime(datetime.combine(data_final, time.max))

    # --- Filtro de Atividades ---
    lista_nomes_atividades = sorted([info['nome'] for info in CAMPOS_DATA.values()])
    atividades_selecionadas = st.multiselect(
        "Filtrar Atividades/Métricas:",
        options=lista_nomes_atividades,
        default=lista_nomes_atividades, # Por padrão, mostrar todas
        key="filtro_atividades_prod"
    )

    if not atividades_selecionadas:
        st.warning("Selecione pelo menos uma atividade para visualizar os dados.")
        return # Impede a execução se nada for selecionado

    # Criar um dicionário CAMPOS_DATA filtrado com base na seleção
    CAMPOS_DATA_FILTRADO = {k: v for k, v in CAMPOS_DATA.items() if v['nome'] in atividades_selecionadas}
    colunas_data_filtradas = list(CAMPOS_DATA_FILTRADO.keys())

    # --- Processamento e Análise de Picos ---
    # Converter colunas de data para datetime no DataFrame de trabalho 'df', tratando erros
    # Usar colunas_data_necessarias (todas) para cálculo de picos e primeira data
    datas_validas_dict = {}
    for col in colunas_data_necessarias:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            datas_validas_dict[col] = df[col].dropna() # Guarda datas válidas por coluna
        else:
            df[col] = pd.NaT # Adiciona coluna vazia se não existir
            datas_validas_dict[col] = pd.Series(dtype='datetime64[ns]') # Série vazia

    # Calcular atividades totais por dia (usando as datas válidas já convertidas)
    todas_as_datas_df = pd.concat(datas_validas_dict.values())
    atividades_por_dia = pd.Series(dtype=int) # Inicializa série vazia
    if not todas_as_datas_df.empty:
        # Agrupa por data (ignorando a hora) e conta as ocorrências
        atividades_por_dia = todas_as_datas_df.dt.normalize().value_counts().sort_index()

    # Calcular média e desvio padrão das atividades diárias GERAIS
    media_atividades_diarias = atividades_por_dia.mean()
    std_atividades_diarias = atividades_por_dia.std()
    limite_pico = media_atividades_diarias + 3 * std_atividades_diarias

    # Identificar dias com pico DENTRO do período selecionado
    datas_periodo = pd.date_range(start=dt_inicial.normalize(), end=dt_final.normalize())
    dias_com_pico = atividades_por_dia[
        (atividades_por_dia.index.isin(datas_periodo)) &
        (atividades_por_dia > limite_pico)
    ]

    # Exibir aviso sobre picos, se houver
    if not dias_com_pico.empty:
        datas_pico_str = ", ".join([d.strftime('%d/%m/%Y') for d in dias_com_pico.index])
        st.warning(f"📈 **Atenção:** Detectado volume de atividades significativamente alto nos dias: {datas_pico_str}. Isso pode indicar ações automáticas ou eventos incomuns.")
        # Opção para remover dias com pico
        remover_picos = st.checkbox("Remover dias com pico da análise?", key="remover_picos_prod")
    else:
        remover_picos = False # Garante que a variável exista mesmo sem picos

    # --- Filtragem de dados para o período selecionado ---
    # Criar uma máscara para filtrar registros onde QUALQUER data RELEVANTE (SELECIONADA) cai no período
    mascara_periodo = pd.Series(False, index=df.index)
    for col in colunas_data_filtradas: # Usa as colunas filtradas pela seleção do usuário
         if col in df.columns:
            # Assegura que a coluna foi convertida para datetime anteriormente
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                 mascara_periodo = mascara_periodo | ((df[col] >= dt_inicial) & (df[col] <= dt_final))

    df_filtrado_inicial = df[mascara_periodo].copy() # Filtro inicial pelo período e atividades selecionadas

    # Aplicar exclusão de picos se solicitado e houver picos no período
    if remover_picos and not dias_com_pico.empty:
        datas_pico_a_remover = dias_com_pico.index.normalize() # Datas normalizadas dos picos

        mascara_excluir_picos = pd.Series(True, index=df_filtrado_inicial.index) # Começa permitindo tudo
        for col in colunas_data_necessarias: # Verifica picos em TODAS as colunas originais
             if col in df_filtrado_inicial.columns:
                  # Verifica se a coluna de data existe e não está vazia antes de normalizar
                  if pd.api.types.is_datetime64_any_dtype(df_filtrado_inicial[col]) and not df_filtrado_inicial[col].isnull().all():
                     # Marca como False se a data (normalizada) da coluna estiver na lista de picos
                     mascara_excluir_picos = mascara_excluir_picos & (~df_filtrado_inicial[col].dt.normalize().isin(datas_pico_a_remover))

        df_filtrado = df_filtrado_inicial[mascara_excluir_picos].copy()
        st.info(f"Dias com pico ({datas_pico_str}) foram removidos da análise.")
    else:
        df_filtrado = df_filtrado_inicial # Usa o df filtrado apenas pelo período

    if df_filtrado.empty:
        # Mensagem ajustada para refletir possível exclusão de picos
        if remover_picos and not dias_com_pico.empty:
             st.info(f"Nenhuma atividade encontrada entre {data_inicial.strftime('%d/%m/%Y')} e {data_final.strftime('%d/%m/%Y')} (dados Bitrix) após a remoção dos dias com pico.")
        else:
             st.info(f"Nenhuma atividade encontrada entre {data_inicial.strftime('%d/%m/%Y')} e {data_final.strftime('%d/%m/%Y')} (dados Bitrix).")
        # Não retorna imediatamente, pois podemos ter dados do Supabase
        # return # Comentado para permitir que a seção do Supabase seja exibida

    # --- Exibir Métricas por Data (Cards Categorizados com Estilo) ---
    st.markdown("#### Atividades no Período (Dados Bitrix)")

    metricas_por_categoria = {'SUCESSO': [], 'EM ANDAMENTO': [], 'FALHA': []}

    # Calcular contagem para cada campo SELECIONADO DENTRO do período
    for col_tecnico, info in CAMPOS_DATA_FILTRADO.items(): # Itera sobre os campos filtrados
        if col_tecnico in df_filtrado.columns:
             # Conta IDs únicos onde a data específica cai no período
            contagem = df_filtrado.loc[
                (df_filtrado[col_tecnico] >= dt_inicial) & (df_filtrado[col_tecnico] <= dt_final),
                'ID' # Assume que a coluna 'ID' existe e é o identificador único
            ].nunique()
            metricas_por_categoria[info['categoria']].append({'label': info['nome'], 'value': contagem})
        # Não adiciona mais métricas zeradas para campos não selecionados
        # else:
            # Adiciona métrica zerada se a coluna estiver faltando (mas deveria existir se foi selecionada)
            # metricas_por_categoria[info['categoria']].append({'label': f"{info['nome']} (Campo Ausente)", 'value': 0})

    # Renderizar as métricas nas colunas usando a estrutura de cards
    col_suc, col_and, col_fal = st.columns(3)

    with col_suc:
        # Usar a variável SCSS $success (compilada) - assumindo que a classe .category-title ou um estilo inline use essa variável
        # Temporariamente, vamos manter a cor aqui, mas idealmente viria do CSS compilado.
        # Se as variáveis SCSS estiverem corretamente mapeadas para classes CSS, poderíamos remover o style inline.
        st.markdown(f'<h5 class="category-title" style="color: var(--color-success, #22C55E); margin-bottom: 10px;">✅ SUCESSO</h5>', unsafe_allow_html=True) # Cor atualizada para $success
        st.markdown('<div class="cards-grid">', unsafe_allow_html=True)
        for metrica in metricas_por_categoria['SUCESSO']:
            # Verificar se a métrica corresponde a uma atividade selecionada
            if metrica['label'] in atividades_selecionadas:
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
        # Usar a variável SCSS $warning (compilada)
        st.markdown(f'<h5 class="category-title" style="color: var(--color-warning, #F59E0B); margin-bottom: 10px;">⏳ EM ANDAMENTO</h5>', unsafe_allow_html=True) # Cor atualizada para $warning
        st.markdown('<div class="cards-grid">', unsafe_allow_html=True)
        for metrica in metricas_por_categoria['EM ANDAMENTO']:
             # Verificar se a métrica corresponde a uma atividade selecionada
             if metrica['label'] in atividades_selecionadas:
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
        # Usar a variável SCSS $danger (compilada)
        st.markdown(f'<h5 class="category-title" style="color: var(--color-danger, #EF4444); margin-bottom: 10px;">❌ FALHA</h5>', unsafe_allow_html=True) # Cor atualizada para $danger
        st.markdown('<div class="cards-grid">', unsafe_allow_html=True)
        for metrica in metricas_por_categoria['FALHA']:
             # Verificar se a métrica corresponde a uma atividade selecionada
             if metrica['label'] in atividades_selecionadas:
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
            # Verifica se a DATA CORRESPONDENTE está entre as atividades SELECIONADAS
            if data_col in CAMPOS_DATA_FILTRADO:
                # Verificar se as colunas existem e se o responsável não é nulo
                if resp_col in row.index and data_col in row.index and pd.notna(row[resp_col]):
                    # Verificar se a data correspondente está no período
                    if pd.notna(row[data_col]) and dt_inicial <= row[data_col] <= dt_final:
                        responsavel_id = str(row[resp_col]) # Usar ID como string
                        # Usa o nome do CAMPOS_DATA_FILTRADO para garantir consistência
                        atividade_nome = CAMPOS_DATA_FILTRADO[data_col]['nome']

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

                 # Ordenar colunas (atividades) pela ordem definida em CAMPOS_DATA_FILTRADO se possível
                ordem_colunas = [info['nome'] for info in CAMPOS_DATA_FILTRADO.values() if info['nome'] in tabela_responsaveis.columns]
                # Garantir que colunas não mapeadas (se houver) não causem erro
                colunas_presentes_na_tabela = [col for col in ordem_colunas if col in tabela_responsaveis.columns]
                tabela_responsaveis = tabela_responsaveis[colunas_presentes_na_tabela]

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
             st.info("Nenhuma atividade de responsável encontrada no período selecionado (dados Bitrix) após o processamento.")

    # --- Análise de Histórico de Movimentações do Supabase ---
    st.markdown("---") # Divisor visual
    st.markdown("#### Histórico de Movimentações por Responsável (Dados Supabase)")

    # Os filtros de data_inicial e data_final já existem acima
    data_inicio_api = data_inicial.strftime('%Y-%m-%d')
    data_fim_api = data_final.strftime('%Y-%m-%d')

    dados_supabase_raw = fetch_supabase_producao_data(data_inicio_api, data_fim_api)

    if not dados_supabase_raw:
        st.warning(f"Nenhum histórico de movimentações encontrado no Supabase para o período de {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}.")
    else:
        df_supabase = pd.DataFrame(dados_supabase_raw)
        
        # Assegurar que data_criacao é datetime
        if 'data_criacao' in df_supabase.columns:
            df_supabase['data_criacao'] = pd.to_datetime(df_supabase['data_criacao'])
        
        if df_supabase.empty:
            st.info("Nenhuma movimentação de responsável encontrada no Supabase para o período selecionado.")
        else:
            try:
                # Colunas esperadas da função: id_movimentacao, movido_por_id, estagio_id, id_card, data_criacao
                tabela_responsaveis_supabase = pd.pivot_table(
                    df_supabase,
                    values='id_card',
                    index='movido_por_id',
                    columns='estagio_id',
                    aggfunc='nunique',
                    fill_value=0
                )

                if not tabela_responsaveis_supabase.empty:
                    tabela_responsaveis_supabase['TOTAL GERAL'] = tabela_responsaveis_supabase.sum(axis=1)
                    tabela_responsaveis_supabase = tabela_responsaveis_supabase.sort_values('TOTAL GERAL', ascending=False)
                else:
                    st.info("A tabela de pivô para o histórico de responsáveis (Supabase) está vazia após o processamento.")

                busca_responsavel_supabase = st.text_input(
                    "Buscar Responsável no Histórico (Supabase):", 
                    key="busca_resp_supabase_hist"
                )
                
                tabela_filtrada_supabase = tabela_responsaveis_supabase
                if busca_responsavel_supabase and not tabela_responsaveis_supabase.empty:
                    # Assegurar que o índice é string para a busca
                    idx_str = tabela_responsaveis_supabase.index.astype(str)
                    tabela_filtrada_supabase = tabela_responsaveis_supabase[
                        idx_str.str.contains(busca_responsavel_supabase, case=False, na=False)
                    ]
                
                if tabela_filtrada_supabase.empty and busca_responsavel_supabase:
                    st.warning(f"Nenhum responsável encontrado para '{busca_responsavel_supabase}' no histórico do Supabase.")
                elif not tabela_filtrada_supabase.empty:
                    st.dataframe(tabela_filtrada_supabase.style.format("{:,}"), use_container_width=True)
                    st.caption("A tabela mostra a contagem de cards únicos para os quais cada responsável ('movido_por_id') registrou uma movimentação para um estágio ('estagio_id'), com base no histórico do Supabase. Os valores são os IDs dos estágios.")
                elif tabela_responsaveis_supabase.empty and not busca_responsavel_supabase: # Se a tabela original já estava vazia e não houve busca
                    st.info("Nenhuma atividade de responsável para exibir do histórico do Supabase no período selecionado.")

            except Exception as e:
                 st.error(f"Ocorreu um erro ao gerar a tabela de histórico de responsáveis (Supabase): {str(e)}")
                 st.dataframe(df_supabase.head()) # Mostra uma amostra dos dados brutos se pivot falhar

    # Adicionar aqui a lógica e visualizações de produção
    # st.info("🚧 Seção em construção.") # Remover esta linha

    # Adicionar lógica e visualizações de produção aqui 