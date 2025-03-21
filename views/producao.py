import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import re
import io
import os
import sys
from pathlib import Path

# Importações internas
from api.bitrix_connector import load_merged_data, get_higilizacao_fields
from components.metrics import render_metrics_section
from components.tables import render_styled_table, create_pendencias_table, create_production_table
from components.filters import date_filter_section, responsible_filter, status_filter

# Obter o caminho absoluto para a pasta utils
utils_path = os.path.join(Path(__file__).parents[1], 'utils')
sys.path.insert(0, str(utils_path))

# Agora importa diretamente dos arquivos na pasta utils
from data_processor import calculate_status_counts, filter_dataframe_by_date, create_responsible_status_table
from animation_utils import display_loading_animation, clear_loading_animation, update_progress

def generate_demo_data():
    """
    Gera dados de demonstração para teste quando a API não estiver disponível
    
    Returns:
        pandas.DataFrame: DataFrame com dados sintéticos para demonstração
    """
    # Criar IDs e títulos
    ids = list(range(1, 21))
    titles = [f"Processo #{i}" for i in ids]
    
    # Criar responsáveis
    responsaveis = ["Ana Silva", "Carlos Mendes", "Juliana Costa", "Pedro Santos", "Maria Oliveira"]
    assigned = [responsaveis[i % len(responsaveis)] for i in ids]
    
    # Criar datas de criação (últimos 30 dias)
    hoje = datetime.now()
    datas = [(hoje - timedelta(days=i % 30)).strftime("%Y-%m-%d") for i in ids]
    
    # Criar status de higienização
    status_opcoes = ["COMPLETO", "INCOMPLETO", "PENDENCIA"]
    status = [status_opcoes[i % len(status_opcoes)] for i in ids]
    
    # Criar campos de sim/não
    sim_nao = ["SIM", "NÃO"]
    campo1 = [sim_nao[i % 2] for i in ids]
    campo2 = [sim_nao[(i+1) % 2] for i in ids]
    campo3 = [sim_nao[(i+2) % 2] for i in ids]
    campo4 = [sim_nao[(i+3) % 2] for i in ids]
    campo5 = [sim_nao[(i+4) % 2] for i in ids]
    
    # Criar DataFrame
    df = pd.DataFrame({
        "ID": ids,
        "TITLE": titles,
        "ASSIGNED_BY_NAME": assigned,
        "DATE_CREATE": datas,
        "UF_CRM_1741206763": datas,  # Data para filtro
        "UF_CRM_HIGILIZACAO_STATUS": status,
        "UF_CRM_1741183785848": campo1,  # Documentação
        "UF_CRM_1741183721969": campo2,  # Cadastro
        "UF_CRM_1741183685327": campo3,  # Estrutura
        "UF_CRM_1741183828129": campo4,  # Requerimento
        "UF_CRM_1741198696": campo5,   # Emissões
    })
    
    return df

def analyze_family_ids(df):
    """
    Analisa os IDs de família no DataFrame e retorna o resumo e detalhes
    """
    if 'UF_CRM_1722605592778' not in df.columns:
        return pd.DataFrame(), pd.DataFrame()
    
    # Função para verificar se o ID está no padrão correto
    def check_id_pattern(id_str):
        # Verificar todos os tipos possíveis de valores vazios
        if pd.isna(id_str) or id_str == '' or id_str is None or (isinstance(id_str, str) and id_str.strip() == ''):
            return 'Vazio'
        if not isinstance(id_str, str):
            return 'Formato Inválido'
        # Remover espaços em branco antes de verificar o padrão
        id_str = id_str.strip()
        pattern = r'^\d+x\d+$'
        if re.match(pattern, id_str):
            return 'Padrão Correto'
        return 'Formato Inválido'

    # Criar uma cópia do DataFrame para análise
    analysis_df = df.copy()
    
    # Primeiro, identificar registros vazios
    analysis_df['ID_STATUS'] = analysis_df['UF_CRM_1722605592778'].apply(check_id_pattern)
    
    # Depois, identificar duplicados apenas entre os registros não vazios e com formato válido
    validos_mask = (analysis_df['ID_STATUS'] == 'Padrão Correto')
    
    # Criar uma série temporária apenas com os IDs válidos para verificar duplicados
    ids_validos = analysis_df.loc[validos_mask, 'UF_CRM_1722605592778'].str.strip()
    duplicados_mask = ids_validos.duplicated(keep=False)
    
    # Marcar duplicados apenas nos registros válidos que estão duplicados
    analysis_df.loc[ids_validos[duplicados_mask].index, 'ID_STATUS'] = 'Duplicado'
    
    # Criar resumo
    summary = pd.DataFrame({
        'Status': ['Padrão Correto', 'Duplicado', 'Vazio', 'Formato Inválido'],
        'Quantidade': [
            sum((analysis_df['ID_STATUS'] == 'Padrão Correto')),
            sum((analysis_df['ID_STATUS'] == 'Duplicado')),
            sum((analysis_df['ID_STATUS'] == 'Vazio')),
            sum((analysis_df['ID_STATUS'] == 'Formato Inválido'))
        ]
    })
    
    # Criar detalhamento
    details = analysis_df[[
        'ID',
        'TITLE',
        'UF_CRM_1722605592778',
        'ASSIGNED_BY_NAME',
        'ID_STATUS'
    ]].copy()
    
    details = details.rename(columns={
        'ID': 'ID',
        'TITLE': 'Nome',
        'UF_CRM_1722605592778': 'ID Família',
        'ASSIGNED_BY_NAME': 'Responsável',
        'ID_STATUS': 'Status do ID'
    })
    
    # Ordenar o detalhamento por Status do ID e Responsável
    details = details.sort_values(['Status do ID', 'Responsável'])
    
    return summary, details

def show_producao():
    """
    Exibe a página de produção e análise de higienização
    """
    # Configurações iniciais e estados
    if 'loading_state' not in st.session_state:
        st.session_state['loading_state'] = 'loading'
        st.rerun()

    loading_state = st.session_state.get('loading_state', 'loading')
    demo_mode = st.session_state.get('demo_mode', False)
    debug_mode = st.session_state.get('debug_mode', False)
    use_id_filter = st.session_state.get('use_id_filter', False)
    id_list = st.session_state.get('id_list', None)
    
    # Se estiver carregando, mostrar apenas a animação
    if loading_state == 'loading':
        with st.container():
            progress_bar, animation_container, message_container = display_loading_animation(
                "Carregando dados do Bitrix24...",
                min_display_time=3
            )
            
            try:
                # Determinar se usamos dados de demonstração ou reais
                if demo_mode:
                    # Gerar dados de demonstração
                    update_progress(progress_bar, 0.3, message_container, "Gerando dados de demonstração...")
                    time.sleep(1)
                    
                    filtered_df = generate_demo_data()
                    
                    update_progress(progress_bar, 0.7, message_container, "Processando dados...")
                    time.sleep(1)
                else:
                    # Carregar dados reais da API
                    start_date = st.session_state.get('start_date', datetime.now() - timedelta(days=30))
                    end_date = st.session_state.get('end_date', datetime.now())
                    
                    # Formatar datas para a API
                    date_from = start_date.strftime("%Y-%m-%d")
                    date_to = end_date.strftime("%Y-%m-%d")
                    
                    update_progress(progress_bar, 0.2, message_container, "Conectando à API do Bitrix24...")
                    
                    # Carregar dados com filtro de IDs se necessário
                    filtered_df = load_merged_data(
                        category_id=32,
                        date_from=date_from,
                        date_to=date_to,
                        deal_ids=id_list if use_id_filter else None,
                        debug=debug_mode,
                        progress_bar=progress_bar,
                        message_container=message_container
                    )
                
                # Armazenar dados filtrados na sessão
                st.session_state['filtered_df'] = filtered_df
                
                # Atualizar estado de carregamento
                update_progress(progress_bar, 1.0, message_container, "Dados carregados com sucesso!")
                st.session_state['loading_state'] = 'completed'
                
                # Pequena pausa para mostrar a mensagem de sucesso
                time.sleep(1)
                
                # Recarregar página
                st.rerun()
        
            except Exception as e:
                # Mostrar erro
                update_progress(progress_bar, 1.0, message_container, f"Erro ao carregar dados: {str(e)}")
                time.sleep(2)
                
                # Voltar ao estado inicial
                st.session_state['loading_state'] = 'not_started'
                st.rerun()
                
            # Não exibir o resto da interface durante o carregamento
            return

    st.title("Produção Higienização")
    st.markdown("---")
        
    # Opções avançadas no sidebar
    with st.sidebar.expander("Opções Avançadas", expanded=False):
        # Opção para usar modo de demonstração
        demo_mode = st.checkbox("Modo de demonstração", value=st.session_state.get('demo_mode', False),
                              help="Ative para usar dados de demonstração sem conexão com a API")
        st.session_state['demo_mode'] = demo_mode
        
        # Opção para exibir dados de depuração
        debug_mode = st.checkbox("Modo de depuração", value=st.session_state.get('debug_mode', False),
                               help="Ative para exibir informações técnicas detalhadas")
        st.session_state['debug_mode'] = debug_mode
        
        # Opção para filtrar IDs específicos
        st.subheader("Filtro de IDs")
        use_id_filter = st.checkbox("Filtrar por IDs específicos", value=st.session_state.get('use_id_filter', False),
                                  help="Ative para buscar apenas IDs específicos (mais rápido)")
        st.session_state['use_id_filter'] = use_id_filter
        
        # Campo para digitação dos IDs
        if use_id_filter:
            id_input = st.text_input("Digite os IDs separados por vírgula (ex: 173, 177)", 
                                    value=st.session_state.get('id_input', "173, 177"),
                                    help="Somente IDs numéricos são permitidos")
            st.session_state['id_input'] = id_input
            
            try:
                # Converter a entrada em lista de IDs
                id_list = []
                for id_str in id_input.split(","):
                    id_str = id_str.strip()
                    if id_str:  # Se não estiver vazio
                        id_list.append(id_str)
                
                st.session_state['id_list'] = id_list
                
                if id_list:
                    st.success(f"Filtro configurado para {len(id_list)} IDs")
                else:
                    st.warning("Nenhum ID válido encontrado. Insira IDs separados por vírgula.")
            except Exception as e:
                st.error(f"Erro ao processar IDs: {str(e)}")
    
    try:
        # Área única de filtros
        with st.expander("Filtros", expanded=True):
            col1, col2 = st.columns(2)
            
            # Coluna 1: Filtro de Período
            with col1:
                # Função para ser chamada quando as datas são alteradas
                def atualizar_filtro_data():
                    # Sinalizar que os filtros foram alterados
                    st.session_state['filtros_alterados'] = True
                
                # Chamar o filtro de data com callback automático
                start_date, end_date = date_filter_section(
                    title="Filtro de Período Por Conclusão",
                    on_change=atualizar_filtro_data
                )
                st.session_state['start_date'] = start_date
                st.session_state['end_date'] = end_date
            
            # Coluna 2: Filtros Adicionais
            with col2:
                st.markdown("##### Filtros Adicionais")
                if 'filtered_df' in st.session_state:
                    filtered_df = st.session_state['filtered_df']
                    # Filtro de responsáveis
                    if 'ASSIGNED_BY_NAME' in filtered_df.columns:
                        selected_responsibles = responsible_filter(filtered_df)
                    
                    # Filtro de status
                    selected_status = status_filter()
            
            # Botão de carregamento centralizado
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Recarregar Dados", type="primary", use_container_width=True):
                    st.session_state['loading_state'] = 'loading'
                    st.rerun()
        
        # Se temos dados carregados, exibi-los
        if loading_state == 'completed' and 'filtered_df' in st.session_state:
            filtered_df = st.session_state['filtered_df'].copy()
            
            # Verificar e corrigir colunas necessárias
            for field in get_higilizacao_fields().keys():
                if field not in filtered_df.columns:
                    filtered_df[field] = None
            
            if 'ASSIGNED_BY_NAME' not in filtered_df.columns:
                filtered_df['ASSIGNED_BY_NAME'] = "Não atribuído"
            
            # Aplicar filtros selecionados
            if 'selected_responsibles' in locals() and selected_responsibles:
                filtered_df = filtered_df[filtered_df['ASSIGNED_BY_NAME'].isin(selected_responsibles)]
            
            if 'selected_status' in locals() and selected_status and 'UF_CRM_HIGILIZACAO_STATUS' in filtered_df.columns:
                status_filter_condition = filtered_df['UF_CRM_HIGILIZACAO_STATUS'].fillna('PENDENCIA').isin(selected_status)
                filtered_df = filtered_df[status_filter_condition]
            
            # Aplicar filtro de data APENAS para registros com status COMPLETO
            if 'UF_CRM_1741206763' in filtered_df.columns:
                # Converter para datetime
                date_mask = pd.isna(filtered_df['UF_CRM_1741206763'])
                filtered_df.loc[~date_mask, 'UF_CRM_1741206763'] = pd.to_datetime(filtered_df.loc[~date_mask, 'UF_CRM_1741206763'])
                
                # Criar uma cópia do DataFrame original
                completos_df = filtered_df[filtered_df['UF_CRM_HIGILIZACAO_STATUS'] == 'COMPLETO'].copy()
                outros_df = filtered_df[filtered_df['UF_CRM_HIGILIZACAO_STATUS'] != 'COMPLETO'].copy()
                
                # Aplicar o filtro de data APENAS nos registros COMPLETOS
                if start_date and end_date:
                    date_filter = (
                        (completos_df['UF_CRM_1741206763'] >= start_date) & 
                        (completos_df['UF_CRM_1741206763'] <= end_date)
                    )
                    completos_df = completos_df[date_filter]
                
                # Combinar os DataFrames novamente
                filtered_df = pd.concat([completos_df, outros_df])
            
            # Verificar se temos dados para exibir
            if filtered_df.empty:
                st.warning("Não foram encontrados dados com os filtros selecionados.")
                if st.button("Limpar e carregar novamente", type="primary"):
                    st.session_state['loading_state'] = 'not_started'
                    st.rerun()
                return
            
            # Exibir número de registros após filtros
            st.markdown(f"**{len(filtered_df)} registros** encontrados após aplicação dos filtros.")
            
            # Métricas Macro
            st.markdown("## Métricas Macro")
            counts = calculate_status_counts(filtered_df)
            render_metrics_section(counts)
            
            # Criar seletor de relatórios em vez de tabs
            st.markdown("## Relatórios Detalhados")
            
            # Usar radio buttons para selecionar o relatório
            relatorio_selecionado = st.radio(
                "Selecione o relatório:",
                ["Status por Responsável", "Pendências por Responsável", "Produção Geral"],
                horizontal=True
            )
            
            # Mostrar o relatório selecionado
            if relatorio_selecionado == "Status por Responsável":
                st.subheader("Status por Responsável")
                
                # SOLUÇÃO RADICAL: Criar manualmente a tabela de status por responsável
                if not filtered_df.empty and 'ASSIGNED_BY_NAME' in filtered_df.columns and 'UF_CRM_HIGILIZACAO_STATUS' in filtered_df.columns:
                    # Substituir valores nulos no status por 'PENDENCIA'
                    filtered_df['UF_CRM_HIGILIZACAO_STATUS'] = filtered_df['UF_CRM_HIGILIZACAO_STATUS'].fillna('PENDENCIA')
                    
                    # 1. Agrupar por responsável e status e contar ocorrências
                    status_counts = filtered_df.groupby(['ASSIGNED_BY_NAME', 'UF_CRM_HIGILIZACAO_STATUS']).size().unstack(fill_value=0)
                    
                    # 2. Certificar que todas as colunas de status existem
                    for status in ['COMPLETO', 'INCOMPLETO', 'PENDENCIA']:
                        if status not in status_counts.columns:
                            status_counts[status] = 0
                    
                    # 3. Selecionar apenas as colunas que nos interessam
                    if 'COMPLETO' in status_counts.columns and 'INCOMPLETO' in status_counts.columns and 'PENDENCIA' in status_counts.columns:
                        display_df = status_counts[['COMPLETO', 'INCOMPLETO', 'PENDENCIA']].copy()
                    else:
                        cols = [col for col in ['COMPLETO', 'INCOMPLETO', 'PENDENCIA'] if col in status_counts.columns]
                        display_df = status_counts[cols].copy()
                    
                    # 4. Resetar o índice
                    display_df = display_df.reset_index()
                    
                    # 5. Renomear a coluna de índice
                    display_df = display_df.rename(columns={'ASSIGNED_BY_NAME': 'Responsável'})
                    
                    # 6. REMOVER EXPLICITAMENTE QUALQUER LINHA QUE CONTENHA 'TOTAL'
                    display_df = display_df[~display_df['Responsável'].astype(str).str.lower().str.contains('total')]
                    
                    # 7. Calcular o total para cada linha (soma de PENDENCIA, INCOMPLETO e COMPLETO)
                    # Garantir que estamos usando os nomes corretos das colunas
                    cols_to_sum = [col for col in ['COMPLETO', 'INCOMPLETO', 'PENDENCIA'] if col in display_df.columns]
                    total_por_linha = display_df[cols_to_sum].sum(axis=1)
                    
                    # 8. Calcular o percentual de conclusão
                    if 'COMPLETO' in display_df.columns:
                        display_df['% Conclusão'] = (display_df['COMPLETO'] / total_por_linha * 100).round(1)
                    else:
                        display_df['% Conclusão'] = 0
                    
                    # 9. Criar a coluna de barra de progresso
                    if 'COMPLETO' in display_df.columns:
                        display_df['Progresso'] = display_df.apply(
                            lambda row: row['COMPLETO'] / total_por_linha[row.name] if total_por_linha[row.name] > 0 else 0, 
                            axis=1
                        )
                    else:
                        display_df['Progresso'] = 0
                    
                    # 10. Configurar as colunas para exibição
                    column_config = {
                        "Responsável": st.column_config.TextColumn(
                            "Responsável",
                            width="medium",
                            help="Nome do responsável"
                        ),
                        "PENDENCIA": st.column_config.NumberColumn(
                            "Pendentes",
                            format="%d",
                            width="small",
                            help="Número de processos pendentes"
                        ),
                        "INCOMPLETO": st.column_config.NumberColumn(
                            "Incompletos",
                            format="%d",
                            width="small",
                            help="Número de processos incompletos"
                        ),
                        "COMPLETO": st.column_config.NumberColumn(
                            "Completos",
                            format="%d",
                            width="small",
                            help="Número de processos completos"
                        ),
                        "% Conclusão": st.column_config.NumberColumn(
                            "% Conclusão",
                            format="%.1f%%",
                            width="small",
                            help="Percentual de conclusão"
                        ),
                        "Progresso": st.column_config.ProgressColumn(
                            "Progresso",
                            width="medium",
                            format="",
                            min_value=0,
                            max_value=1,
                            help="Barra de progresso de conclusão"
                        )
                    }
                    
                    # 11. Ordenar por total em ordem decrescente
                    display_df['_total'] = total_por_linha
                    display_df = display_df.sort_values('_total', ascending=False)
                    display_df = display_df.drop(columns=['_total'])
                    
                    # 12. Exibir o DataFrame com as configurações de coluna
                    st.dataframe(
                        display_df,
                        column_config=column_config,
                        use_container_width=True,
                        height=500,
                        hide_index=True
                    )
                else:
                    st.info("Não há dados suficientes para criar a tabela de status por responsável.")
            
            elif relatorio_selecionado == "Pendências por Responsável":
                st.subheader("Pendências por Responsável")
                pendencias_df = create_pendencias_table(filtered_df)
                if not pendencias_df.empty:
                    # Exibir o DataFrame com as configurações de coluna
                    st.dataframe(
                        pendencias_df,
                        column_config={
                            "Responsável": st.column_config.TextColumn(
                                "Responsável",
                                width="medium",
                                help="Nome do responsável"
                            ),
                            "Documentação": st.column_config.NumberColumn(
                                "Documentação",
                                format="%d",
                                width="small",
                                help="Número de pendências em Documentação"
                            ),
                            "Cadastro": st.column_config.NumberColumn(
                                "Cadastro",
                                format="%d",
                                width="small",
                                help="Número de pendências em Cadastro"
                            ),
                            "Estrutura": st.column_config.NumberColumn(
                                "Estrutura",
                                format="%d",
                                width="small",
                                help="Número de pendências em Estrutura"
                            ),
                            "Requerimento": st.column_config.NumberColumn(
                                "Requerimento",
                                format="%d",
                                width="small",
                                help="Número de pendências em Requerimento"
                            ),
                            "Emissões": st.column_config.NumberColumn(
                                "Emissões",
                                format="%d",
                                width="small",
                                help="Número de pendências em Emissões"
                            ),
                            "Total": st.column_config.NumberColumn(
                                "Total",
                                format="%d",
                                width="small",
                                help="Total de pendências"
                            )
                        },
                        use_container_width=True,
                        height=500,
                        hide_index=True
                    )
                    
                    # Exibir a linha de total separada logo abaixo da tabela
                    st.markdown("<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; font-weight: bold;'>", unsafe_allow_html=True)
                    cols = st.columns([3, 1, 1, 1, 1, 1, 1])
                    with cols[0]:
                        st.markdown("<div style='text-align: left; font-weight: bold;'>Total:</div>", unsafe_allow_html=True)
                    with cols[1]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{pendencias_df['Documentação'].sum()}</div>", unsafe_allow_html=True)
                    with cols[2]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{pendencias_df['Cadastro'].sum()}</div>", unsafe_allow_html=True)
                    with cols[3]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{pendencias_df['Estrutura'].sum()}</div>", unsafe_allow_html=True)
                    with cols[4]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{pendencias_df['Requerimento'].sum()}</div>", unsafe_allow_html=True)
                    with cols[5]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{pendencias_df['Emissões'].sum()}</div>", unsafe_allow_html=True)
                    with cols[6]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{pendencias_df['Total'].sum()}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.success("Não há pendências! Todos os processos estão completos ou em andamento.")
            
            elif relatorio_selecionado == "Produção Geral":
                st.subheader("Produção Geral")
                production_df = create_production_table(filtered_df)
                if not production_df.empty:
                    # Exibir o DataFrame com as configurações de coluna
                    st.dataframe(
                        production_df,
                        column_config={
                            "Responsável": st.column_config.TextColumn(
                                "Responsável",
                                width="medium",
                                help="Nome do responsável"
                            ),
                            "Documentação": st.column_config.NumberColumn(
                                "Documentação",
                                format="%d",
                                width="small",
                                help="Número de itens concluídos em Documentação"
                            ),
                            "Cadastro": st.column_config.NumberColumn(
                                "Cadastro",
                                format="%d",
                                width="small",
                                help="Número de itens concluídos em Cadastro"
                            ),
                            "Estrutura": st.column_config.NumberColumn(
                                "Estrutura",
                                format="%d",
                                width="small",
                                help="Número de itens concluídos em Estrutura"
                            ),
                            "Requerimento": st.column_config.NumberColumn(
                                "Requerimento",
                                format="%d",
                                width="small",
                                help="Número de itens concluídos em Requerimento"
                            ),
                            "Emissões": st.column_config.NumberColumn(
                                "Emissões",
                                format="%d",
                                width="small",
                                help="Número de itens concluídos em Emissões"
                            ),
                            "Total": st.column_config.NumberColumn(
                                "Total",
                                format="%d",
                                width="small",
                                help="Total de itens concluídos"
                            )
                        },
                        use_container_width=True,
                        height=500,
                        hide_index=True
                    )
                    
                    # Exibir a linha de total separada logo abaixo da tabela
                    st.markdown("<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; font-weight: bold;'>", unsafe_allow_html=True)
                    cols = st.columns([3, 1, 1, 1, 1, 1, 1])
                    with cols[0]:
                        st.markdown("<div style='text-align: left; font-weight: bold;'>Total:</div>", unsafe_allow_html=True)
                    with cols[1]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{production_df['Documentação'].sum()}</div>", unsafe_allow_html=True)
                    with cols[2]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{production_df['Cadastro'].sum()}</div>", unsafe_allow_html=True)
                    with cols[3]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{production_df['Estrutura'].sum()}</div>", unsafe_allow_html=True)
                    with cols[4]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{production_df['Requerimento'].sum()}</div>", unsafe_allow_html=True)
                    with cols[5]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{production_df['Emissões'].sum()}</div>", unsafe_allow_html=True)
                    with cols[6]:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{production_df['Total'].sum()}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("Não há dados suficientes para criar a tabela de produção.")
            
            # Análise de IDs de Família (movida para o final)
            st.markdown("## Análise de IDs de Família")
            family_id_summary, family_id_details = analyze_family_ids(filtered_df)
            
            if not family_id_summary.empty:
                # Exibir resumo em um expander
                with st.expander("Resumo de IDs de Família", expanded=False):
                    # Configurar as colunas para o resumo
                    summary_config = {
                        "Status": st.column_config.TextColumn(
                            "Status do ID",
                            width="medium",
                            help="Classificação do ID de Família"
                        ),
                        "Quantidade": st.column_config.NumberColumn(
                            "Quantidade",
                            format="%d",
                            width="small",
                            help="Número de registros"
                        )
                    }
                    
                    st.dataframe(
                        family_id_summary,
                        column_config=summary_config,
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Filtros para o detalhamento
                st.markdown("### Filtros de Análise")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Filtro de status do ID
                    selected_id_status = st.multiselect(
                        "Filtrar por Status do ID",
                        options=['Padrão Correto', 'Duplicado', 'Vazio', 'Formato Inválido'],
                        default=['Duplicado', 'Vazio', 'Formato Inválido'],
                        help="Selecione os status que deseja visualizar"
                    )
                
                with col2:
                    # Filtro de responsável
                    responsaveis = sorted(family_id_details['Responsável'].unique())
                    resp_filter = st.multiselect(
                        "Filtrar por Responsável",
                        options=responsaveis,
                        help="Selecione os responsáveis que deseja visualizar"
                    )
                
                # Aplicar filtros
                filtered_details = family_id_details.copy()
                if selected_id_status:
                    filtered_details = filtered_details[filtered_details['Status do ID'].isin(selected_id_status)]
                if resp_filter:
                    filtered_details = filtered_details[filtered_details['Responsável'].isin(resp_filter)]
                
                # Exibir detalhes filtrados
                if not filtered_details.empty:
                    # Configurar as colunas para o detalhamento
                    details_config = {
                        "ID": st.column_config.TextColumn(
                            "ID",
                            width="small",
                            help="ID do registro"
                        ),
                        "Nome": st.column_config.TextColumn(
                            "Nome",
                            width="medium",
                            help="Nome do registro"
                        ),
                        "ID Família": st.column_config.TextColumn(
                            "ID Família",
                            width="medium",
                            help="ID da Família"
                        ),
                        "Responsável": st.column_config.TextColumn(
                            "Responsável",
                            width="medium",
                            help="Nome do responsável"
                        ),
                        "Status do ID": st.column_config.TextColumn(
                            "Status do ID",
                            width="small",
                            help="Status do ID de Família"
                        )
                    }
                    
                    st.dataframe(
                        filtered_details,
                        column_config=details_config,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Adicionar botão para exportar
                    if st.button("Exportar Análise para Excel"):
                        # Converter para Excel
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            # Aba de resumo
                            family_id_summary.to_excel(writer, sheet_name='Resumo', index=False)
                            # Aba de detalhes
                            filtered_details.to_excel(writer, sheet_name='Detalhamento', index=False)
                        
                        # Oferecer para download
                        st.download_button(
                            label="Baixar arquivo Excel",
                            data=output.getvalue(),
                            file_name=f"analise_ids_familia_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.info("Nenhum registro encontrado com os filtros selecionados.")
            else:
                st.info("Não foi possível analisar os IDs de família. Campo não encontrado nos dados.")
            
            # Rodapé
            st.markdown("---")
            source_type = "de DEMONSTRAÇÃO" if demo_mode else f"atualizados da API{' (filtrados por IDs)' if use_id_filter else ''}"
            st.markdown(f"*Dados {source_type} em: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
            
            # Descrição dos campos
            with st.expander("Descrição dos Campos de Higienização"):
                fields = get_higilizacao_fields()
                for field_id, field_name in fields.items():
                    st.markdown(f"**{field_name}**: `{field_id}`")
        
        elif loading_state == 'not_started':
            st.info("Utilize os filtros acima e clique em 'Aplicar Filtros' para carregar os dados do Bitrix24.")
                
    except Exception as e:
        st.error(f"Erro ao renderizar a página de produção: {str(e)}")
        if debug_mode:
            st.expander("Detalhes do erro", expanded=True).exception(e)
        else:
            st.info("Ative o 'Modo de depuração' na seção 'Opções Avançadas' na barra lateral para ver mais detalhes do erro.") 