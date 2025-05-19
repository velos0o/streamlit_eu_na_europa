import streamlit as st
import pandas as pd
# Remover import re, não é mais necessário
from datetime import date
import numpy as np

# Importar AgGrid
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

# --- Função Auxiliar Copiada de visao_geral.py ---
# TODO: Considerar mover esta função para um módulo utils compartilhado
def simplificar_nome_estagio(nome):
    """ Simplifica o nome do estágio para exibição. """
    if pd.isna(nome):
        return "Desconhecido"

    codigo_estagio = str(nome) # Garante que é string

    # Mapeamento Atualizado com base na descrição do usuário e categorias
    mapeamento = {
        # SPA - Type ID 1098 STAGES
        'DT1098_92:NEW': 'AGUARDANDO CERTIDÃO',
        'DT1098_94:NEW': 'AGUARDANDO CERTIDÃO',
        'DT1098_92:UC_P6PYHW': 'PESQUISA - BR',
        'DT1098_94:UC_4YE2PI': 'PESQUISA - BR',
        'DT1098_92:PREPARATION': 'BUSCA - CRC',
        'DT1098_94:PREPARATION': 'BUSCA - CRC',
        'DT1098_92:UC_XBTHZ7': 'DEVOLUTIVA BUSCA - CRC',
        'DT1098_94:CLIENT': 'DEVOLUTIVA BUSCA - CRC', # Nota: CLIENT em Tatuapé é Devolutiva Busca CRC
        'DT1098_92:CLIENT': 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
        'DT1098_94:UC_IQ4WFA': 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
        'DT1098_92:UC_ZWO7BI': 'MONTAGEM REQUERIMENTO CARTÓRIO',
        'DT1098_94:UC_UZHXWF': 'MONTAGEM REQUERIMENTO CARTÓRIO',
        'DT1098_92:UC_83ZGKS': 'SOLICITAR CARTÓRIO DE ORIGEM',
        'DT1098_94:UC_DH38EI': 'SOLICITAR CARTÓRIO DE ORIGEM',
        'DT1098_92:UC_6TECYL': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'DT1098_94:UC_X9UE60': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'DT1098_92:UC_MUJP1P': 'AGUARDANDO CARTÓRIO ORIGEM',
        'DT1098_94:UC_IXCAA5': 'AGUARDANDO CARTÓRIO ORIGEM',
        'DT1098_92:UC_EYBGVD': 'DEVOLUÇÃO ADM',
        'DT1098_94:UC_VS8YKI': 'DEVOLUÇÃO ADM',
        'DT1098_92:UC_KC335Q': 'DEVOLVIDO REQUERIMENTO',
        'DT1098_94:UC_M6A09E': 'DEVOLVIDO REQUERIMENTO',
        'DT1098_92:UC_5LWUTX': 'CERTIDÃO EMITIDA',
        'DT1098_94:UC_K4JS04': 'CERTIDÃO EMITIDA',
        'DT1098_92:FAIL': 'SOLICITAÇÃO DUPLICADA',
        'DT1098_94:FAIL': 'SOLICITAÇÃO DUPLICADA',
        'DT1098_92:UC_Z24IF7': 'CANCELADO',
        'DT1098_94:UC_MGTPX0': 'CANCELADO',
        'DT1098_92:SUCCESS': 'CERTIDÃO ENTREGUE',
        'DT1098_94:SUCCESS': 'CERTIDÃO ENTREGUE',
        'DT1098_92:UC_U10R0R': 'CERTIDÃO DISPENSADA', # NOVO
        'DT1098_94:UC_L3JFKO': 'CERTIDÃO DISPENSADA', # NOVO
        # Manter mapeamentos genéricos caso algum STAGE_ID venha sem prefixo DT1098_XX:
        'NEW': 'AGUARDANDO CERTIDÃO',
        'UC_P6PYHW': 'PESQUISA - BR',
        'UC_4YE2PI': 'PESQUISA - BR',
        'PREPARATION': 'BUSCA - CRC',
        'UC_XBTHZ7': 'DEVOLUTIVA BUSCA - CRC',
        'UC_IQ4WFA': 'APENAS ASS. REQ CLIENTE P/MONTAGEM',
        'UC_ZWO7BI': 'MONTAGEM REQUERIMENTO CARTÓRIO',
        'UC_UZHXWF': 'MONTAGEM REQUERIMENTO CARTÓRIO',
        'UC_83ZGKS': 'SOLICITAR CARTÓRIO DE ORIGEM',
        'UC_DH38EI': 'SOLICITAR CARTÓRIO DE ORIGEM',
        'UC_6TECYL': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'UC_X9UE60': 'SOLICITAR CARTÓRIO DE ORIGEM PRIORIDADE',
        'UC_MUJP1P': 'AGUARDANDO CARTÓRIO ORIGEM',
        'UC_IXCAA5': 'AGUARDANDO CARTÓRIO ORIGEM',
        'UC_EYBGVD': 'DEVOLUÇÃO ADM',
        'UC_VS8YKI': 'DEVOLUÇÃO ADM',
        'UC_KC335Q': 'DEVOLVIDO REQUERIMENTO',
        'UC_M6A09E': 'DEVOLVIDO REQUERIMENTO',
        'UC_5LWUTX': 'CERTIDÃO EMITIDA',
        'UC_K4JS04': 'CERTIDÃO EMITIDA',
        'FAIL': 'SOLICITAÇÃO DUPLICADA',
        'UC_Z24IF7': 'CANCELADO',
        'UC_MGTPX0': 'CANCELADO',
        'SUCCESS': 'CERTIDÃO ENTREGUE',
        'UC_U10R0R': 'CERTIDÃO DISPENSADA', # NOVO GENÉRICO
        'UC_L3JFKO': 'CERTIDÃO DISPENSADA', # NOVO GENÉRICO
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

# TODO: Mover para utils
def categorizar_estagio(estagio_legivel):
    """ Categoriza o estágio simplificado em SUCESSO, EM ANDAMENTO ou FALHA. """
    # ATUALIZADO com base nos novos nomes de estágio do SPA
    sucesso = [
        'CERTIDÃO ENTREGUE',
        'CERTIDÃO EMITIDA' # Considerado sucesso no contexto de etapas concluídas antes da entrega final
    ]
    falha = [
        'DEVOLUÇÃO ADM',
        'DEVOLVIDO REQUERIMENTO',
        'SOLICITAÇÃO DUPLICADA',
        'CANCELADO',
        'DEVOLUTIVA BUSCA - CRC', # Se a devolutiva da busca significa que não encontrou, é uma falha de progresso.
                                 # Se significa que a busca foi devolvida para correção, pode ser 'EM ANDAMENTO'. Precisa confirmar a semântica.
                                 # Por ora, classificando como FALHA se impede o progresso direto.
        'CERTIDÃO DISPENSADA', # NOVO - Classificado como FALHA
    ]

    if estagio_legivel in sucesso:
        return 'SUCESSO'
    elif estagio_legivel in falha:
        return 'FALHA'
    else:
        return 'EM ANDAMENTO' if estagio_legivel != "Desconhecido" else "DESCONHECIDO"

def exibir_pendencias(df_original):
    """
    Exibe uma tabela dinâmica mostrando a contagem de processos por responsável e estágio,
    com filtro por nome e estilização SCSS.
    """
    st.markdown("#### Pendências por Responsável e Estágio")

    if df_original is None or df_original.empty:
        st.warning("Não há dados disponíveis para exibir as pendências.")
        return

    df = df_original.copy()

    # --- Definição das Colunas --- 
    coluna_data_criacao = 'CREATED_TIME' # Coluna para o filtro de data
    coluna_responsavel_adm = 'UF_CRM_34_ADM_DE_PASTA' # ATUALIZADO para o novo campo SPA
    # Assumindo que existe uma coluna com o nome do assigned_by
    # Se o nome for diferente, ajuste aqui!
    coluna_assigned_name = 'ASSIGNED_BY_NAME' 
    coluna_estagio_id = 'STAGE_ID'
    coluna_estagio_name = 'STAGE_NAME'
    # Mantendo a coluna de ID caso precise no futuro, mas o foco é o nome
    coluna_assigned_id = 'ASSIGNED_BY_ID' 
    coluna_nome_familia = 'UF_CRM_34_NOME_FAMILIA' # ATUALIZADO para o novo campo SPA

    # Determinar qual coluna de estágio usar
    coluna_estagio = coluna_estagio_id if coluna_estagio_id in df.columns else coluna_estagio_name

    # --- Criar coluna ESTAGIO_SIMPLIFICADO (MOVIDO PARA CIMA) ---
    # Garantir que a coluna de estágio seja string antes de aplicar
    df[coluna_estagio] = df[coluna_estagio].astype(str)
    df['ESTAGIO_SIMPLIFICADO'] = df[coluna_estagio].apply(simplificar_nome_estagio)

    # --- Expander para Filtros --- 
    with st.expander("Filtros", expanded=True): # Começa expandido
        # Linha 1: Filtro de Data
        col_data1, col_data2, col_data3 = st.columns([0.3, 0.35, 0.35])
        with col_data1:
            aplicar_filtro_data = st.checkbox("Data Criação", value=False, key="aplicar_filtro_data_pendencias")

        datas_validas = pd.Series(dtype='datetime64[ns]') # Inicializa como série vazia
        min_date = date.today()
        max_date = date.today()

        if coluna_data_criacao not in df.columns:
            with col_data1:
                st.caption(f":warning: Coluna '{coluna_data_criacao}' não encontrada.")
            aplicar_filtro_data = False # Força desabilitar se coluna não existe
        else:
            # Tenta converter para datetime ANTES de calcular min/max
            df[coluna_data_criacao] = pd.to_datetime(df[coluna_data_criacao], errors='coerce')
            datas_validas = df[coluna_data_criacao].dropna()
            if not datas_validas.empty:
                min_date = datas_validas.min().date()
                max_date = datas_validas.max().date()

        # Campos de data aparecem apenas se o checkbox estiver marcado
        data_inicio = None
        data_fim = None
        if aplicar_filtro_data:
            with col_data2:
                data_inicio = st.date_input(
                    "De:",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="data_inicio_pendencias",
                    label_visibility="collapsed"
                )
            with col_data3:
                data_fim = st.date_input(
                    "Até:",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="data_fim_pendencias",
                    label_visibility="collapsed"
                )

        # Linha 2: Filtro de Etapas e Busca Responsável
        col_etapa, col_busca = st.columns([0.6, 0.4])

        # Linha 3: Filtro de Família
        # Verificar se a coluna família existe para habilitar o filtro
        filtro_familia_habilitado = coluna_nome_familia in df.columns
        if not filtro_familia_habilitado:
            st.caption(f":warning: Coluna '{coluna_nome_familia}' não encontrada. Filtro de família desabilitado.")

        termo_busca_familia_widget = st.text_input(
            "Buscar Família/Contrato:",
            key="busca_familia_pendencias_widget",
            placeholder="Nome...",
            disabled=not filtro_familia_habilitado # Desabilitar se coluna não existe
        )

        # --- Sugestões para Busca de Família --- 
        sugestoes_familia = []
        termo_digitado_familia = termo_busca_familia_widget.strip()
        if termo_digitado_familia and filtro_familia_habilitado:
            # Obter nomes únicos do DF ORIGINAL para sugestões mais completas
            nomes_unicos_familia = df_original[coluna_nome_familia].fillna('Desconhecido').astype(str).unique()
            sugestoes_familia = [ 
                nome for nome in nomes_unicos_familia 
                if termo_digitado_familia.lower() in nome.lower()
            ][:5] # Limitar a 5 sugestões
            
            if sugestoes_familia:
                st.caption("Sugestões: " + ", ".join(sugestoes_familia))
            elif len(termo_digitado_familia) > 1: # Não mostrar se só digitou 1 letra e não achou
                st.caption("Nenhuma família/contrato encontrado para o termo digitado.")

        # Obter etapas disponíveis a partir da coluna já criada
        # Precisamos recalcular após filtro de data se ele for aplicado
        # Placeholder: recalcular etapas depois
        # ATUALIZADO com base nos novos nomes de estágio do SPA
        estagios_sucesso_para_excluir_filtro = ['CERTIDÃO ENTREGUE', 'CERTIDÃO EMITIDA']
        opcoes_etapas_filtro = sorted([
            e for e in df['ESTAGIO_SIMPLIFICADO'].unique() 
            if e not in estagios_sucesso_para_excluir_filtro
        ])

        with col_etapa:
            etapas_selecionadas_widget = st.multiselect(
                "Etapa(s):",
                options=opcoes_etapas_filtro, 
                default=opcoes_etapas_filtro, # Default para todas as pendentes (exceto sucesso)
                key="filtro_etapas_pendencias_widget",
                # label_visibility="collapsed" # Manter label para clareza
            )
        with col_busca:
            termo_busca_widget = st.text_input(
                "Buscar Responsável:", 
                key="busca_responsavel_pendencias_widget", 
                placeholder="Nome...",
                # label_visibility="collapsed"
            ) 

    # --- Aplicar Filtros (Fora do Expander) ---
    # Aplicar filtro de data se ativo e datas válidas
    if aplicar_filtro_data and data_inicio and data_fim:
        start_datetime = pd.to_datetime(data_inicio)
        end_datetime = pd.to_datetime(data_fim) + pd.Timedelta(days=1)

        df = df[
            (df[coluna_data_criacao].notna()) &
            (df[coluna_data_criacao] >= start_datetime) &
            (df[coluna_data_criacao] < end_datetime)
        ].copy()

    # Aplicar filtro de Família/Contrato
    termo_familia = termo_busca_familia_widget.strip()
    if termo_familia and filtro_familia_habilitado:
        # Tratar Nulos na coluna antes de filtrar
        df[coluna_nome_familia] = df[coluna_nome_familia].fillna('Desconhecido').astype(str)
        df = df[df[coluna_nome_familia].str.contains(termo_familia, case=False, na=False)]

    # Verificar se df ficou vazio APÓS filtro de família (e data)
    if df.empty:
        st.info("Nenhum dado encontrado para os filtros de data e/ou família aplicados.")
        return

    # --- Verificação das Colunas Essenciais ---
    colunas_necessarias = [coluna_estagio_id, coluna_estagio_name]
    # colunas_responsaveis = [coluna_responsavel_adm, coluna_assigned_name, coluna_assigned_id] # Reavaliar uso
    
    colunas_faltando = [col for col in colunas_necessarias if col not in df.columns and col != coluna_estagio_name] 
    if 'STAGE_ID' not in df.columns and 'STAGE_NAME' not in df.columns:
         colunas_faltando.append("STAGE_ID ou STAGE_NAME")

    if colunas_faltando:
        st.error(f"Erro: Colunas essenciais de estágio não encontradas: {colunas_faltando}")
        st.caption(f"Colunas disponíveis: {list(df.columns)}")
        return
        
    # Verificar se existe a coluna principal de responsável (ASSIGNED_BY_NAME ou ASSIGNED_BY_ID)
    existe_assigned_name = coluna_assigned_name in df.columns
    existe_assigned_id = coluna_assigned_id in df.columns
    # existe_resp_adm = coluna_responsavel_adm in df.columns # Não é prioritário aqui
    
    if not existe_assigned_name and not existe_assigned_id:
         st.error(f"Erro: Nenhuma coluna para identificar o responsável primário encontrada (verificadas: '{coluna_assigned_name}', '{coluna_assigned_id}').")
         st.caption(f"Colunas disponíveis: {list(df.columns)}")
         return
    
    # --- Pré-processamento (Continuação) --- 
    df = df.dropna(subset=[coluna_estagio], how='all') 
    
    # Garantir que as colunas de responsável existam (mesmo que vazias)
    if coluna_assigned_name not in df.columns: df[coluna_assigned_name] = pd.NA
    if coluna_assigned_id not in df.columns: df[coluna_assigned_id] = pd.NA
    if coluna_responsavel_adm not in df.columns: df[coluna_responsavel_adm] = pd.NA # Para a função extrair_nome_responsavel, caso seja usada em outro contexto

    # Priorizar ASSIGNED_BY_NAME, depois tentar extrair de ASSIGNED_BY_ID
    df['RESP_NOME_TEMP'] = pd.NA # Inicializar
    if existe_assigned_name:
        df['RESP_NOME_TEMP'] = df[coluna_assigned_name].apply(extrair_nome_responsavel)
    
    # Se RESP_NOME_TEMP ainda estiver vazio e ASSIGNED_BY_ID existir, tentar extrair dele
    # (A função extrair_nome_responsavel pode precisar ser ajustada para lidar com IDs diretamente se for o caso)
    if existe_assigned_id:
        condition_resp_vazio_after_name = df['RESP_NOME_TEMP'].isin([None, '', 'nan', 'None', '<NA>', '[]']) | df['RESP_NOME_TEMP'].isnull()
        df.loc[condition_resp_vazio_after_name, 'RESP_NOME_TEMP'] = df.loc[condition_resp_vazio_after_name, coluna_assigned_id].apply(extrair_nome_responsavel)

    # Identificar valores "vazios" padrão (None, NaN, strings vazias, 'nan', 'None', <NA>)
    empty_values = [None, '', 'nan', 'None', '<NA>', '[]']
    # Verificar onde o nome extraído é considerado vazio
    condition_resp_final_vazio = df['RESP_NOME_TEMP'].isin(empty_values) | df['RESP_NOME_TEMP'].isnull()
    
    # Preencher com "SEM_RESPONSAVEL" onde ainda está vazio
    df.loc[condition_resp_final_vazio, 'RESP_NOME_TEMP'] = 'SEM_RESPONSAVEL'

    # Definir a coluna final
    df['RESPONSAVEL_NOME'] = df['RESP_NOME_TEMP']

    # Remover linhas onde RESPONSAVEL_NOME ainda é vazio ou 'SEM_RESPONSAVEL' se quisermos ignorá-los
    # Por enquanto, vamos mantê-los para que os números batam
    # df = df[df['RESPONSAVEL_NOME'] != 'SEM_RESPONSAVEL'] # Descomentar se quiser remover
    df = df.dropna(subset=['RESPONSAVEL_NOME'])
    df = df[df['RESPONSAVEL_NOME'] != '']

    # Remover coluna temporária
    df = df.drop(columns=['RESP_NOME_TEMP'])

    # --- NOVO: Filtrar para remover estágios de sucesso --- 
    # ATUALIZADO com base nos novos nomes de estágio do SPA
    estagios_excluir = ['CERTIDÃO ENTREGUE', 'CERTIDÃO EMITIDA']
    df = df[~df['ESTAGIO_SIMPLIFICADO'].isin(estagios_excluir)]

    # Verificar se o df está vazio APÓS filtro de data E exclusão de sucesso
    if df.empty:
        st.info("Não há pendências encontradas (após excluir estágios de sucesso e aplicar filtros de data/etapa/busca).") # Mensagem mais completa
        return

    # --- Aplicar Filtro de Etapas ---
    # Recalcular etapas disponíveis APÓS filtros anteriores
    lista_etapas_pendentes_atualizada = sorted(df['ESTAGIO_SIMPLIFICADO'].unique())
    # Filtrar o dataframe com base no valor do widget
    etapas_selecionadas = etapas_selecionadas_widget
    if etapas_selecionadas:
        # Filtrar apenas pelas etapas que AINDA existem no df filtrado
        etapas_validas_selecionadas = [e for e in etapas_selecionadas if e in lista_etapas_pendentes_atualizada]
        df = df[df['ESTAGIO_SIMPLIFICADO'].isin(etapas_validas_selecionadas)]
    else:
        st.warning("Nenhuma etapa selecionada no filtro.")
        return # Mais simples retornar aqui

    # Verificar se df ficou vazio APÓS filtro de etapas
    if df.empty:
        st.info("Nenhuma pendência encontrada para as etapas selecionadas.")
        return

    # Obter termo de busca do widget
    termo_busca = termo_busca_widget

    # --- Criação da Tabela Dinâmica (agora com df filtrado por data, etapas) ---
    try:
        tabela_pendencias = pd.pivot_table(
            df,
            values='ID',
            index='RESPONSAVEL_NOME',
            columns='ESTAGIO_SIMPLIFICADO',
            aggfunc='count',
            fill_value=0
        )
        
        # --- Mapear Categorias para Colunas --- 
        mapa_categoria_coluna = {col: categorizar_estagio(col) for col in tabela_pendencias.columns}
        
        # Ordenar colunas por categoria e depois alfabeticamente
        ordem_categorias = {'EM ANDAMENTO': 1, 'SUCESSO': 2, 'FALHA': 3, 'DESCONHECIDO': 4}
        colunas_ordenadas = sorted(
            tabela_pendencias.columns,
            key=lambda col: (ordem_categorias.get(mapa_categoria_coluna.get(col, 'DESCONHECIDO'), 99), col)
        )
        tabela_pendencias = tabela_pendencias[colunas_ordenadas]
        # Atualizar mapa após reordenar (se necessário, mas as categorias são as mesmas)
        mapa_categoria_coluna = {col: categorizar_estagio(col) for col in tabela_pendencias.columns}

        # Adicionar Total por Responsável
        tabela_pendencias['TOTAL GERAL'] = tabela_pendencias.sum(axis=1)
        
        # Adicionar Total por Estágio
        tabela_pendencias.loc['TOTAL GERAL'] = tabela_pendencias.sum(axis=0)
        tabela_pendencias.loc['TOTAL GERAL', 'TOTAL GERAL'] = tabela_pendencias.loc['TOTAL GERAL', :].iloc[:-1].sum()

    except Exception as e:
        st.error(f"Erro ao criar a tabela dinâmica: {e}")
        st.dataframe(df[['RESPONSAVEL_NOME', 'ESTAGIO_SIMPLIFICADO', 'ID']].head())
        return

    # Resetar índice para tornar 'RESPONSAVEL_NOME' uma coluna
    tabela_pendencias_reset = tabela_pendencias.reset_index()
    # Renomear índice para um nome mais amigável
    tabela_pendencias_reset = tabela_pendencias_reset.rename(columns={'RESPONSAVEL_NOME': 'Responsável'})

    # --- Filtragem por Responsável (termo_busca) ANTES de adicionar Total Geral ---
    tabela_filtrada_antes_total = tabela_pendencias_reset.copy()
    
    # Excluir a linha TOTAL GERAL temporariamente se ela existir da pivot table original
    if 'TOTAL GERAL' in tabela_filtrada_antes_total['Responsável'].values:
        tabela_sem_total_original = tabela_filtrada_antes_total[tabela_filtrada_antes_total['Responsável'] != 'TOTAL GERAL'].copy()
    else:
        tabela_sem_total_original = tabela_filtrada_antes_total.copy()
        
    # Aplicar filtro de busca
    if termo_busca:
        mask = tabela_sem_total_original['Responsável'].str.contains(termo_busca, case=False, na=False)
        tabela_filtrada = tabela_sem_total_original[mask]
        if tabela_filtrada.empty:
             st.info("Nenhum responsável encontrado para o termo buscado.")
             # Mantem tabela_filtrada vazia para não mostrar nada
    else:
        # Se não houver busca, usa todos os dados (sem o total original)
        tabela_filtrada = tabela_sem_total_original

    # --- Recalcular e Adicionar Total Geral (APÓS filtro de busca) ---
    if not tabela_filtrada.empty:
        # Calcular totais apenas das colunas numéricas (estágios + TOTAL GERAL da pivot original se existir)
        numeric_cols = tabela_filtrada.select_dtypes(include=np.number).columns
        total_row_calculada = tabela_filtrada[numeric_cols].sum().to_frame().T
        total_row_calculada['Responsável'] = 'TOTAL GERAL'
        # Garantir que a coluna 'Responsável' seja a primeira
        cols = ['Responsável'] + [col for col in tabela_filtrada.columns if col != 'Responsável']
        total_row_calculada = total_row_calculada[cols]
        
        # Concatenar a nova linha de total
        tabela_filtrada = pd.concat([tabela_filtrada, total_row_calculada], ignore_index=True)
    # Se tabela_filtrada estava vazia após a busca, ela continua vazia

    # --- Configuração das Colunas para st.dataframe (APÓS TODA MANIPULAÇÃO) ---
    st.markdown("##### Contagem de Processos")

    # --- Exibição com st.dataframe ---
    column_config = {
        "Responsável": st.column_config.TextColumn(
            "Responsável",
            help="Nome do responsável pelo processo.",
            width="large",
        )
    }
    # Adicionar colunas presentes na tabela filtrada (exceto 'Responsável')
    for col_name in tabela_filtrada.columns:
        if col_name == 'Responsável':
            continue # Já configurado
            
        is_total_geral = (col_name == 'TOTAL GERAL')
        column_config[col_name] = st.column_config.NumberColumn(
            "Total" if is_total_geral else col_name, # Label especial para Total Geral
            help=f"Total de processos para o responsável." if is_total_geral else f"Processos no estágio {col_name}",
            format="%d",
            width="small" if is_total_geral else "medium",
        )

    # --- Exibição com st.dataframe ---
    if tabela_filtrada.empty:
         st.info("Tabela de pendências vazia.")
    else:
        # DEBUG 2: Verificar colunas antes de exibir (REMOVIDO)
        # st.write("Debug 2: Colunas da tabela_filtrada:", tabela_filtrada.columns.tolist())
        
        st.dataframe(
            tabela_filtrada,
            column_config=column_config,
            use_container_width=True, # Tentar usar largura total
            hide_index=True # Esconder o índice numérico padrão do dataframe resetado
            # Não há parâmetro direto para altura fixa como no AgGrid
        )

    # --- Opção de Download (mantida por enquanto) ---
    @st.cache_data
    def convert_df_to_csv(df_to_convert):
       # Usar a tabela original antes do reset para manter o nome como índice
       return tabela_pendencias.to_csv(index=True).encode('utf-8')
    csv = convert_df_to_csv(tabela_pendencias)
    st.download_button(
       label="Download Tabela Completa como CSV",
       data=csv,
       file_name='pendencias_responsaveis_estagios.csv',
       mime='text/csv',
       key='download-pendencias-csv'
    ) 

def extrair_nome_responsavel(resp):
    """ Extrai o nome do responsável de diferentes formatos possíveis ou retorna 'SEM_RESPONSAVEL'. """
    if resp == 'SEM_RESPONSAVEL':
        return 'SEM_RESPONSAVEL'
    if isinstance(resp, (list, dict)):
        if isinstance(resp, dict):
            # Tenta buscar por 'name' ou 'NAME', caso contrário retorna a representação string
            return resp.get('name', resp.get('NAME', str(resp)))
        elif isinstance(resp, list) and len(resp) > 0 and isinstance(resp[0], dict):
            # Pega o nome do primeiro item da lista, se for um dict
            return resp[0].get('name', resp[0].get('NAME', str(resp)))
        else:
            # Caso de lista vazia ou lista com itens não-dict
            return str(resp)
    # Se for string ou outro tipo, retorna como string
    return str(resp) 