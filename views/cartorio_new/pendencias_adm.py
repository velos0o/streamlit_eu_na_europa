import streamlit as st
import pandas as pd
import re # Adicionado import re
from datetime import date
import numpy as np

# Importar AgGrid
# from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode # Removido AgGrid pois não é usado

# Importar funções do novo utils
from .utils import simplificar_nome_estagio, categorizar_estagio

# --- Função Auxiliar Copiada de visao_geral.py ---
# TODO: Considerar mover esta função para um módulo utils compartilhado
# def simplificar_nome_estagio(nome):

def exibir_pendencias_adm(df_cartorio_original):
    """
    Exibe uma tabela dinâmica mostrando a contagem de processos por ADM de Pasta e estágio,
    com filtro por nome e estilização SCSS.
    Coluna 'DEVOLUÇÃO ADM' destacada.
    """
    # --- Carregar CSS Compilado ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")
    
    st.markdown('<div class="cartorio-container cartorio-container--info">', unsafe_allow_html=True)
    st.title("Pendências ADM")

    if df_cartorio_original is None or df_cartorio_original.empty:
        st.warning("Não há dados disponíveis para exibir as pendências.")
        return

    df = df_cartorio_original.copy()

    # --- Definição das Colunas ---
    coluna_data_criacao = 'CREATED_TIME' # Coluna para o filtro de data
    coluna_responsavel_adm = 'UF_CRM_34_ADM_DE_PASTA' # Campo principal para responsável
    # Fallback para ASSIGNED_BY_NAME se UF_CRM_34_ADM_DE_PASTA não estiver preenchido
    # coluna_assigned_name = 'ASSIGNED_BY_NAME'
    coluna_estagio_id = 'STAGE_ID'
    coluna_estagio_name = 'STAGE_NAME'
    # Mantendo a coluna de ID caso precise no futuro, mas o foco é o nome
    # coluna_assigned_id = 'ASSIGNED_BY_ID' # Não usado diretamente para nome na tabela final
    coluna_nome_familia = 'UF_CRM_34_NOME_FAMILIA' # ATUALIZADO para o novo campo SPA

    # Determinar qual coluna de estágio usar
    coluna_estagio = coluna_estagio_id if coluna_estagio_id in df.columns else coluna_estagio_name

    # --- Criar coluna ESTAGIO_SIMPLIFICADO (MOVIDO PARA CIMA) ---
    # Garantir que a coluna de estágio seja string antes de aplicar
    if coluna_estagio not in df.columns:
        st.error(f"Coluna de estágio ('{coluna_estagio}') não encontrada. Não é possível prosseguir.")
        return
    df[coluna_estagio] = df[coluna_estagio].astype(str)
    df['ESTAGIO_SIMPLIFICADO'] = df[coluna_estagio].apply(simplificar_nome_estagio)

    # --- Expander para Filtros ---
    with st.expander("Filtros", expanded=True): # Começa expandido
        # Linha 1: Filtro de Data
        col_data1, col_data2, col_data3 = st.columns([0.3, 0.35, 0.35])
        with col_data1:
            aplicar_filtro_data = st.checkbox("Data Criação", value=False, key="aplicar_filtro_data_pendencias_adm")

        datas_validas_series = pd.Series(dtype='datetime64[ns]') # Inicializa como série vazia
        min_date_val = date.today()
        max_date_val = date.today()

        if coluna_data_criacao not in df.columns:
            with col_data1:
                st.caption(f":warning: Coluna '{coluna_data_criacao}' não encontrada.")
            aplicar_filtro_data = False # Força desabilitar se coluna não existe
        else:
            # Tenta converter para datetime ANTES de calcular min/max
            df[coluna_data_criacao] = pd.to_datetime(df[coluna_data_criacao], errors='coerce')
            datas_validas_series = df[coluna_data_criacao].dropna()
            if not datas_validas_series.empty:
                min_date_val = datas_validas_series.min().date()
                max_date_val = datas_validas_series.max().date()

        # Campos de data aparecem apenas se o checkbox estiver marcado
        data_inicio = None
        data_fim = None
        if aplicar_filtro_data:
            with col_data2:
                data_inicio = st.date_input(
                    "De:",
                    value=min_date_val,
                    min_value=min_date_val,
                    max_value=max_date_val,
                    key="data_inicio_pendencias_adm",
                    label_visibility="collapsed"
                )
            with col_data3:
                data_fim = st.date_input(
                    "Até:",
                    value=max_date_val,
                    min_value=min_date_val,
                    max_value=max_date_val,
                    key="data_fim_pendencias_adm",
                    label_visibility="collapsed"
                )

        # Linha 2: Filtro de Etapas e Busca Responsável (ADM de Pasta)
        col_etapa, col_busca, col_protocolizado = st.columns([0.5, 0.3, 0.2])

        # Linha 3: Filtro de Família
        # Verificar se a coluna família existe para habilitar o filtro
        filtro_familia_habilitado = coluna_nome_familia in df.columns
        if not filtro_familia_habilitado:
            st.caption(f":warning: Coluna '{coluna_nome_familia}' não encontrada. Filtro de família desabilitado.")

        termo_busca_familia_widget = st.text_input(
            "Buscar Família/Contrato:",
            key="busca_familia_pendencias_adm_widget",
            placeholder="Nome...",
            disabled=not filtro_familia_habilitado # Desabilitar se coluna não existe
        )

        # --- Sugestões para Busca de Família ---
        # sugestoes_familia = [] # Removido, não usado diretamente depois
        termo_digitado_familia = termo_busca_familia_widget.strip()
        if termo_digitado_familia and filtro_familia_habilitado and coluna_nome_familia in df_cartorio_original.columns:
            nomes_unicos_familia_sugestao = df_cartorio_original[coluna_nome_familia].fillna('Desconhecido').astype(str).unique()
            sugestoes_familia_list = [
                nome for nome in nomes_unicos_familia_sugestao
                if termo_digitado_familia.lower() in nome.lower()
            ][:5] # Limitar a 5 sugestões

            if sugestoes_familia_list:
                st.caption("Sugestões: " + ", ".join(sugestoes_familia_list))
            elif len(termo_digitado_familia) > 1:
                st.caption("Nenhuma família/contrato encontrado para o termo digitado.")

        estagios_sucesso_para_excluir_filtro = ['CERTIDÃO ENTREGUE', 'CERTIDÃO EMITIDA']
        opcoes_etapas_filtro = sorted([
            e for e in df['ESTAGIO_SIMPLIFICADO'].unique()
            if e not in estagios_sucesso_para_excluir_filtro
        ])

        with col_etapa:
            etapas_selecionadas_widget = st.multiselect(
                "Etapa(s):",
                options=opcoes_etapas_filtro,
                default=opcoes_etapas_filtro,
                key="filtro_etapas_pendencias_adm_widget",
            )
        with col_busca:
            termo_busca_widget = st.text_input(
                "Buscar ADM de Pasta:",
                key="busca_responsavel_pendencias_adm_widget",
                placeholder="Nome...",
            )
        
        with col_protocolizado:
            # --- Filtro de Protocolizado ---
            coluna_protocolizado = 'UF_CRM_34_PROTOCOLIZADO'
            filtro_protocolizado_habilitado = coluna_protocolizado in df.columns
            if filtro_protocolizado_habilitado:
                filtro_protocolizado = st.selectbox(
                    "Protocolizado:",
                    options=["Todos", "PROTOCOLIZADO", "NÃO PROTOCOLIZADO"],
                    index=0,
                    key="filtro_protocolizado_pendencias_adm"
                )
            else:
                st.caption(f":warning: Campo protocolizado não encontrado.")
                filtro_protocolizado = "Todos"

    # --- Aplicar Filtros (Fora do Expander) ---
    if aplicar_filtro_data and data_inicio and data_fim and coluna_data_criacao in df.columns:
        start_datetime = pd.to_datetime(data_inicio)
        end_datetime = pd.to_datetime(data_fim) + pd.Timedelta(days=1)
        df = df[
            (df[coluna_data_criacao].notna()) &
            (df[coluna_data_criacao] >= start_datetime) &
            (df[coluna_data_criacao] < end_datetime)
        ].copy()

    termo_familia = termo_busca_familia_widget.strip()
    if termo_familia and filtro_familia_habilitado and coluna_nome_familia in df.columns:
        df[coluna_nome_familia] = df[coluna_nome_familia].fillna('Desconhecido').astype(str)
        df = df[df[coluna_nome_familia].str.contains(termo_familia, case=False, na=False)]

    # --- Aplicar Filtro de Protocolizado ---
    if filtro_protocolizado != "Todos" and filtro_protocolizado_habilitado:
        if coluna_protocolizado in df.columns:
            df[coluna_protocolizado] = df[coluna_protocolizado].fillna('').astype(str).str.strip().str.upper()
            if filtro_protocolizado == "PROTOCOLIZADO":
                df = df[df[coluna_protocolizado] == 'PROTOCOLIZADO']
            elif filtro_protocolizado == "NÃO PROTOCOLIZADO":
                df = df[df[coluna_protocolizado] != 'PROTOCOLIZADO']

    if df.empty:
        st.info("Nenhum dado encontrado para os filtros de data e/ou família aplicados.")
        return

    # --- Verificação e Preparação de Colunas de Responsável ---
    existe_resp_adm = coluna_responsavel_adm in df.columns
    # existe_assigned_name = coluna_assigned_name in df.columns # Não verificaremos mais o fallback aqui

    if not existe_resp_adm:
         st.error(f"Erro: A coluna principal de ADM de Pasta ('{coluna_responsavel_adm}') não foi encontrada. Não é possível prosseguir.")
         st.caption(f"Colunas disponíveis: {list(df.columns)}")
         return
    # elif not existe_resp_adm: # Implica que existe_assigned_name é True # Lógica de fallback removida
        #  st.warning(f"Aviso: Coluna principal de ADM de Pasta ('{coluna_responsavel_adm}') não encontrada. Usando '{coluna_assigned_name}' como fallback.")
        #  df[coluna_responsavel_adm] = pd.NA
        #  existe_resp_adm = True # Simula que existe para a lógica subsequente

    if coluna_responsavel_adm not in df.columns: df[coluna_responsavel_adm] = pd.NA # Deve ser redundante devido à checagem acima
    # if coluna_assigned_name not in df.columns: df[coluna_assigned_name] = pd.NA # Não é mais usado como fallback direto

    df['RESP_NOME_TEMP'] = df[coluna_responsavel_adm].apply(extrair_nome_responsavel)
    empty_values = [None, '', 'nan', 'None', '<NA>', 'NaN', '[]']
    # condition_adm_vazio = df['RESP_NOME_TEMP'].isin(empty_values) | df['RESP_NOME_TEMP'].isnull()

    # if existe_assigned_name: # Lógica de fallback removida
        # df[coluna_assigned_name] = df[coluna_assigned_name].apply(lambda x: extrair_nome_responsavel(x) if pd.notna(x) else None)
        # df.loc[condition_adm_vazio & df[coluna_assigned_name].notnull(), 'RESP_NOME_TEMP'] = df.loc[condition_adm_vazio & df[coluna_assigned_name].notnull(), coluna_assigned_name]

    df['RESP_NOME_TEMP'] = df['RESP_NOME_TEMP'].astype(str)
    condition_ainda_vazio = df['RESP_NOME_TEMP'].isin(empty_values + ['none']) | df['RESP_NOME_TEMP'].isnull()
    df.loc[condition_ainda_vazio, 'RESP_NOME_TEMP'] = 'SEM_RESPONSAVEL_ADM'
    df['RESPONSAVEL_ADM_NOME'] = df['RESP_NOME_TEMP']

    df = df[df['RESPONSAVEL_ADM_NOME'] != 'SEM_RESPONSAVEL_ADM'] # Mantemos esta linha para excluir os explicitamente sem ADM

    if df.empty:
        st.info("Não há dados de responsáveis válidos (ADM de Pasta) após o processamento para os filtros aplicados.")
        return

    estagios_excluir = ['CERTIDÃO ENTREGUE', 'CERTIDÃO EMITIDA']
    df = df[~df['ESTAGIO_SIMPLIFICADO'].isin(estagios_excluir)]

    if df.empty:
        st.info("Não há pendências encontradas (após excluir estágios de sucesso e aplicar outros filtros).")
        return

    etapas_selecionadas = etapas_selecionadas_widget
    if etapas_selecionadas:
        lista_etapas_pendentes_atualizada = sorted(df['ESTAGIO_SIMPLIFICADO'].unique())
        etapas_validas_selecionadas = [e for e in etapas_selecionadas if e in lista_etapas_pendentes_atualizada]
        if not etapas_validas_selecionadas and etapas_selecionadas:
            st.warning("As etapas selecionadas não existem nos dados filtrados. Mostrando todas as etapas pendentes disponíveis.")
        elif etapas_validas_selecionadas:
            df = df[df['ESTAGIO_SIMPLIFICADO'].isin(etapas_validas_selecionadas)]
    # else: # Se nenhuma etapa for selecionada, não filtra por etapa, mostra todas as pendentes
        # st.warning("Nenhuma etapa selecionada no filtro. Mostrando todas as etapas pendentes.")

    if df.empty:
        st.info("Nenhuma pendência encontrada para as etapas selecionadas (ou todas, se nenhuma foi selecionada).")
        return

    termo_busca = termo_busca_widget.strip()

    try:
        if df.empty or 'RESPONSAVEL_ADM_NOME' not in df.columns or df['RESPONSAVEL_ADM_NOME'].nunique() == 0:
            st.info("Não há dados para gerar a tabela de pendências por ADM de Pasta com os filtros atuais.")
            return

        tabela_pendencias = pd.pivot_table(
            df,
            values='ID',
            index='RESPONSAVEL_ADM_NOME',
            columns='ESTAGIO_SIMPLIFICADO',
            aggfunc='count',
            fill_value=0
        )

        mapa_categoria_coluna = {col: categorizar_estagio(col) for col in tabela_pendencias.columns}
        ordem_categorias = {'EM ANDAMENTO': 1, 'FALHA': 2, 'SUCESSO': 3, 'DESCONHECIDO': 4}
        colunas_ordenadas = sorted(
            tabela_pendencias.columns,
            key=lambda col: (ordem_categorias.get(mapa_categoria_coluna.get(col, 'DESCONHECIDO'), 99), col)
        )
        tabela_pendencias = tabela_pendencias.reindex(columns=colunas_ordenadas, fill_value=0)

        tabela_pendencias['TOTAL GERAL'] = tabela_pendencias.sum(axis=1)
        if not tabela_pendencias.empty:
            total_geral_row = tabela_pendencias.sum(axis=0).to_frame().T
            total_geral_row.index = ['TOTAL GERAL']
            if 'TOTAL GERAL' in total_geral_row.columns:
                total_geral_row['TOTAL GERAL'] = total_geral_row.drop(columns=['TOTAL GERAL']).sum(axis=1)
            tabela_pendencias = pd.concat([tabela_pendencias, total_geral_row])

    except Exception as e:
        st.error(f"Erro ao criar a tabela dinâmica: {e}")
        return

    tabela_pendencias_reset = tabela_pendencias.reset_index().rename(columns={'index': 'ADM de Pasta'})
    tabela_filtrada_df = tabela_pendencias_reset

    if termo_busca:
        tabela_adm_sem_total = tabela_filtrada_df[tabela_filtrada_df['ADM de Pasta'] != 'TOTAL GERAL']
        mask_busca = tabela_adm_sem_total['ADM de Pasta'].str.contains(termo_busca, case=False, na=False)
        tabela_busca_resultado = tabela_adm_sem_total[mask_busca]

        if tabela_busca_resultado.empty:
            st.info(f"Nenhum ADM de Pasta encontrado para o termo '{termo_busca}'.")
            tabela_filtrada_df = pd.DataFrame(columns=tabela_filtrada_df.columns)
        else:
            linha_total_original = tabela_filtrada_df[tabela_filtrada_df['ADM de Pasta'] == 'TOTAL GERAL']
            tabela_filtrada_df = pd.concat([tabela_busca_resultado, linha_total_original], ignore_index=True)
            # Recalcular total geral para a tabela filtrada pela busca
            if not tabela_busca_resultado.empty and 'TOTAL GERAL' in tabela_filtrada_df['ADM de Pasta'].values:
                numeric_cols_busca = tabela_busca_resultado.select_dtypes(include=np.number).columns
                total_row_recalculado = tabela_busca_resultado[numeric_cols_busca].sum()
                total_geral_index = tabela_filtrada_df[tabela_filtrada_df['ADM de Pasta'] == 'TOTAL GERAL'].index
                if not total_geral_index.empty:
                    for col in numeric_cols_busca:
                        tabela_filtrada_df.loc[total_geral_index, col] = total_row_recalculado[col]
                    if 'TOTAL GERAL' in numeric_cols_busca: # Recalcular a célula TOTAL GERAL da linha TOTAL GERAL
                         tabela_filtrada_df.loc[total_geral_index, 'TOTAL GERAL'] = total_row_recalculado.drop(labels, errors='ignore').sum() if 'TOTAL GERAL' in total_row_recalculado else total_row_recalculado.sum()


    st.markdown("##### Contagem de Processos")
    column_config_dict = {
        "ADM de Pasta": st.column_config.TextColumn(
            "ADM de Pasta",
            help="Nome do ADM de Pasta responsável pelo processo.",
            width="large",
        )
    }
    if not tabela_filtrada_df.empty:
        for col_name_cfg in tabela_filtrada_df.columns:
            if col_name_cfg == 'ADM de Pasta':
                continue
            is_total_geral_cfg_col = (col_name_cfg == 'TOTAL GERAL')
            is_devolucao_adm_cfg_col = (col_name_cfg == 'DEVOLUÇÃO ADM')

            label_cfg = col_name_cfg
            help_text_cfg = f"Processos no estágio {col_name_cfg}"
            width_cfg = "medium"

            if is_total_geral_cfg_col:
                label_cfg = "TOTAL"
                help_text_cfg = "Total de processos para o ADM de Pasta."
                width_cfg = "small"
            elif is_devolucao_adm_cfg_col:
                label_cfg = "⚠️ DEVOLUÇÃO ADM ⚠️"
                help_text_cfg = "Processos devolvidos pela administração. ATENÇÃO ESPECIAL!"

            column_config_dict[col_name_cfg] = st.column_config.NumberColumn(
                label_cfg,
                help=help_text_cfg,
                format="%d",
                width=width_cfg,
            )

    if tabela_filtrada_df.empty:
         st.info("Tabela de pendências por ADM de Pasta vazia para os filtros aplicados.")
    else:
        st.dataframe(
            tabela_filtrada_df,
            column_config=column_config_dict,
            use_container_width=True,
            hide_index=True
        )

    @st.cache_data
    def convert_df_to_csv_adm(df_to_convert):
       return df_to_convert.to_csv(index=False).encode('utf-8')

    if 'tabela_pendencias' in locals() and not tabela_pendencias.empty:
        # Usa a tabela ANTES do reset_index e filtro de busca para o download completo
        csv_download_full = convert_df_to_csv_adm(tabela_pendencias.reset_index()) 
        st.download_button(
           label="Download Tabela Completa (ADM) como CSV",
           data=csv_download_full,
           file_name='pendencias_adm_pasta_estagios.csv',
           mime='text/csv',
           key='download-pendencias-adm-csv-full'
        )
    elif not tabela_filtrada_df.empty:
        csv_download_filtered = convert_df_to_csv_adm(tabela_filtrada_df)
        st.download_button(
           label="Download Tabela Filtrada (ADM) como CSV",
           data=csv_download_filtered,
           file_name='pendencias_adm_pasta_estagios_filtrada.csv',
           mime='text/csv',
           key='download-pendencias-adm-csv-filtered'
        )

    # --- NOVA SEÇÃO: Detalhes das Devoluções ADM ---
    st.markdown("---")
    st.markdown("##### Detalhes das Devoluções ADM")

    # Usar o DataFrame 'df' que já foi processado para filtros e nomes de responsáveis ADM
    # e filtrado pelas etapas selecionadas no multiselect.
    # Se o multiselect de etapas não incluir 'DEVOLUÇÃO ADM', esta tabela pode ficar vazia.
    df_devolucoes = df[df['ESTAGIO_SIMPLIFICADO'] == 'DEVOLUÇÃO ADM'].copy()

    if df_devolucoes.empty:
        st.info("Nenhum item encontrado em 'DEVOLUÇÃO ADM' para os filtros aplicados ou a etapa não foi selecionada no filtro de etapas.")
    else:
        colunas_detalhes = {
            'RESPONSAVEL_ADM_NOME': 'ADM de Pasta',
            'ID': 'ID do Item',
            # Verificar se estas colunas existem no df_original/df
            'UF_CRM_34_ID_FAMILIA': 'ID Família',
            'UF_CRM_34_MOTIVO_DA_DEVOLUCAO_ADM': 'Motivo da Devolução ADM',
            'UF_CRM_34_OBSERVACAO_DEVOLUCAO_ADM': 'Observação Devolução ADM'
        }
        
        colunas_para_exibir = []
        colunas_ausentes = []

        for col_original, nome_exibicao in colunas_detalhes.items():
            if col_original in df_devolucoes.columns:
                colunas_para_exibir.append(col_original)
            elif col_original not in ['RESPONSAVEL_ADM_NOME', 'ID']: # ID e RESPONSAVEL_ADM_NOME já são verificados/criados
                colunas_ausentes.append(f"{nome_exibicao} (Campo original: {col_original})")
        
        if colunas_ausentes:
            st.warning(f"As seguintes colunas não foram encontradas e não serão exibidas na tabela de detalhes: {', '.join(colunas_ausentes)}.")

        if not colunas_para_exibir:
            st.error("Nenhuma coluna válida encontrada para exibir os detalhes das devoluções.")
        else:
            df_detalhes_final = df_devolucoes[colunas_para_exibir].rename(columns=colunas_detalhes)
            
            # Preencher NaNs com string vazia para melhor visualização
            for col in df_detalhes_final.columns:
                if df_detalhes_final[col].dtype == 'object':
                    df_detalhes_final[col] = df_detalhes_final[col].fillna('')
                else:
                    # Para colunas numéricas, pode-se querer preencher com 0 ou manter NaT/NaN dependendo do tipo
                    # Por enquanto, vamos focar nas de texto para o fillna('')
                    pass 
            
            st.dataframe(
                df_detalhes_final,
                use_container_width=True,
                hide_index=True
            )

            csv_detalhes_devolucao = convert_df_to_csv_adm(df_detalhes_final) # Reutiliza a função de conversão
            st.download_button(
               label="Download Detalhes Devolução ADM como CSV",
               data=csv_detalhes_devolucao,
               file_name='detalhes_devolucao_adm.csv',
               mime='text/csv',
               key='download-detalhes-devolucao-adm-csv'
            )

    st.markdown('</div>', unsafe_allow_html=True)  # Fecha cartorio-container

def extrair_nome_responsavel(resp):
    """ Extrai o nome do responsável de diferentes formatos possíveis. """
    if resp is None or pd.isna(resp):
        return None

    if isinstance(resp, str):
        # Remove aspas e colchetes comuns em representações de lista como string
        cleaned_resp = resp.strip("[]'\"")
        # Se for um ID numérico como string
        if cleaned_resp.isdigit():
            return f"ID:{cleaned_resp}" # Ou apenas cleaned_resp se preferir exibir só o ID
        # Tenta extrair nome de padrões como "Nome Sobrenome [123]" ou "[123] Nome Sobrenome"
        match = re.match(r"^(.*?)\s*\[\d+\]$|^\[\d+\]\s*(.*)", cleaned_resp)
        if match:
            return (match.group(1) or match.group(2) or "").strip()
        return cleaned_resp if cleaned_resp else None

    if isinstance(resp, list):
        if not resp:
            return None
        nomes = []
        for item in resp:
            if isinstance(item, dict):
                nomes.append(item.get('name', item.get('NAME', str(item))))
            else:
                nomes.append(str(item))
        return ', '.join(filter(None, nomes)) or None

    if isinstance(resp, dict):
        return resp.get('name', resp.get('NAME', str(resp)))

    return str(resp)