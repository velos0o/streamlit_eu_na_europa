import streamlit as st
from .data_loader import carregar_dados_cartorio, carregar_dados_crm_deal_com_uf
from .analysis import (
    criar_visao_geral_cartorio,
    analyze_cartorio_ids,
    analisar_familias_ausentes,
    analisar_familia_certidoes,
    analisar_acompanhamento_emissao_familia
)
from .visualization import visualizar_cartorio_dados
from .movimentacoes import analisar_produtividade as analisar_movimentacoes
from .produtividade import analisar_produtividade_etapas
from .analise_tempo_crm import mostrar_dashboard_tempo_crm
from .protocolado import exibir_dashboard_protocolado
from .emissoes_cartao import exibir_dashboard_emissoes_cartao
import pandas as pd
import io
import datetime  # Modificando para importar o módulo completo
from datetime import datetime as dt  # Renomeando para evitar conflitos
import os
import sys
from pathlib import Path
from components.report_guide import show_contextual_help

def show_cartorio():
    """
    Exibe a página principal do Cartório com layout e clareza aprimorados.
    """
    # Título principal da página
    st.markdown("""
    <h1 style="font-size: 2.5rem; font-weight: 700; color: #1A237E; text-align: center;
    margin-bottom: 1rem; padding-bottom: 8px; border-bottom: 3px solid #1976D2;
    font-family: Arial, Helvetica, sans-serif;">
    Painel de Controle - Cartório</h1>
    """, unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1rem; color: #555; font-family: Arial, Helvetica, sans-serif; margin-bottom: 1.5rem;'>Monitoramento do funil de emissões e qualidade dos dados.</p>", unsafe_allow_html=True)

    # Adicionar seção de ajuda específica para certidões entregues
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Análise de Documentos e Certidões")
    with col2:
        if st.button("🔍 Ajuda: Certidões Entregues", type="secondary", use_container_width=True):
            show_contextual_help("certidoes")

    # Carregar os dados dos cartórios
    with st.spinner("Carregando dados dos cartórios..."):
        try:
            df_cartorio = carregar_dados_cartorio()
            if not df_cartorio.empty:
                st.success(f"Dados dos cartórios carregados: {len(df_cartorio)} registros encontrados.")
            else:
                st.warning("Não foi possível carregar os dados dos cartórios. Nenhum registro encontrado.")
                return
        except Exception as e:
            st.error(f"Erro ao carregar dados dos cartórios: {str(e)}")
            return

    # Carregar dados do crm_deal com UF_CRM_1722605592778 para comparação
    with st.spinner("Carregando dados de CRM para comparação..."):
        try:
            df_crm_deal = carregar_dados_crm_deal_com_uf()
            if not df_crm_deal.empty:
                st.success(f"Dados de CRM (categoria 0) carregados: {len(df_crm_deal)} registros encontrados.")
                
                # Verificar se o campo UF_CRM_1722605592778 está presente
                if 'UF_CRM_CAMPO_COMPARACAO' not in df_crm_deal.columns:
                    st.warning("Campo UF_CRM_1722605592778 não encontrado nos dados do CRM. A comparação não estará disponível.")
            else:
                st.info("Não foram encontrados dados na categoria 0 do CRM para comparação.")
        except Exception as e:
            st.error(f"Erro ao carregar dados do CRM: {str(e)}")
            df_crm_deal = pd.DataFrame()  # Garantir que temos um DataFrame vazio em caso de erro

    st.divider() # Adiciona um separador

    # Renomear a coluna para facilitar a comparação
    if 'UF_CRM_12_1723552666' in df_cartorio.columns:
        # Normalizar o ID da família para comparação
        df_cartorio['ID_FAMILIA'] = df_cartorio['UF_CRM_12_1723552666'].astype(str).str.strip()
        # Remover espaços em branco e garantir que é string
        df_cartorio['ID_FAMILIA'] = df_cartorio['ID_FAMILIA'].str.replace(' ', '')
    else:
        st.warning("Campo UF_CRM_12_1723552666 não encontrado nos dados do cartório. A comparação não estará disponível.")
        df_cartorio['ID_FAMILIA'] = None  # Adicionar coluna vazia para evitar erros
    
    # Mesclar os dados do cartório com os dados do CRM_DEAL
    if not df_crm_deal.empty and 'UF_CRM_CAMPO_COMPARACAO' in df_crm_deal.columns:
        # Adicionar informações sobre a operação
        st.info("Comparando ID da família (UF_CRM_12_1723552666) com dados do CRM categoria 0 (UF_CRM_1722605592778)...")
        
        # Normalizar para facilitar a junção
        df_crm_deal['ID_FAMILIA'] = df_crm_deal['UF_CRM_CAMPO_COMPARACAO'].astype(str).str.strip()
        # Remover espaços em branco e garantir que é string
        df_crm_deal['ID_FAMILIA'] = df_crm_deal['ID_FAMILIA'].str.replace(' ', '')
        
        # Debug: Exibir alguns exemplos para verificar o formato
        with st.expander("📊 Debug: Exemplos de IDs para comparação", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Exemplos de IDs do Cartório (UF_CRM_12_1723552666)")
                ids_cartorio = df_cartorio['ID_FAMILIA'].dropna().unique()
                if len(ids_cartorio) > 0:
                    st.write(ids_cartorio[:10].tolist())
                else:
                    st.warning("Nenhum ID encontrado no cartório.")
                
                st.metric("Total de IDs únicos do Cartório", len(ids_cartorio))
                
            with col2:
                st.subheader("Exemplos de IDs do CRM (UF_CRM_1722605592778)")
                ids_crm = df_crm_deal['ID_FAMILIA'].dropna().unique()
                if len(ids_crm) > 0:
                    st.write(ids_crm[:10].tolist())
                else:
                    st.warning("Nenhum ID encontrado no CRM.")
                
                st.metric("Total de IDs únicos do CRM", len(ids_crm))
            
            # Verificar interseção
            ids_comuns = set(ids_cartorio) & set(ids_crm)
            st.subheader("Comparação de IDs")
            st.metric("Total de IDs em comum", len(ids_comuns))
            if len(ids_comuns) > 0:
                st.write("Exemplos de IDs em comum:")
                st.write(list(ids_comuns)[:10])
        
        # Adicionar um prefixo nas colunas do crm_deal para evitar conflitos
        colunas_crm = {col: f'CRM_{col}' for col in df_crm_deal.columns if col != 'ID_FAMILIA'}
        df_crm_deal = df_crm_deal.rename(columns=colunas_crm)
        
        # Realizar o merge com outer join para preservar todos os registros
        try:
            df_cartorio = pd.merge(
                df_cartorio,
                df_crm_deal,
                on='ID_FAMILIA',
                how='left',
                suffixes=('', '_crm')
            )
            
            # Contar quantos registros têm correspondência
            registros_com_correspondencia = df_cartorio['CRM_ID'].notna().sum()
            percentual = round((registros_com_correspondencia / len(df_cartorio) * 100), 1) if len(df_cartorio) > 0 else 0
            
            st.success(f"Correspondência encontrada: {registros_com_correspondencia} de {len(df_cartorio)} registros ({percentual}%).")
        except Exception as e:
            st.error(f"Erro ao mesclar dados do cartório com CRM: {str(e)}")
    else:
        st.info("Dados de CRM não disponíveis para comparação ou campo UF_CRM_1722605592778 não encontrado.")

    # Filtro de cartório (mantido no topo para aplicação global)
    st.markdown("#### Filtros Gerais")
    
    # Criar colunas para os filtros
    col_cartorio, col_id_familia = st.columns(2)
    
    with col_cartorio:
        cartorio_filter = st.multiselect(
            "Selecione os Cartórios:",
            options=sorted(df_cartorio['NOME_CARTORIO'].unique()), # Opções dinâmicas
            default=sorted(df_cartorio['NOME_CARTORIO'].unique()), # Padrão: todos
            help="Selecione um ou mais cartórios para filtrar os dados exibidos abaixo."
        )
    
    # Adicionar filtro para IDs de família que têm correspondência com UF_CRM_1722605592778
    if 'CRM_UF_CRM_CAMPO_COMPARACAO' in df_cartorio.columns:
        with col_id_familia:
            # Identificar registros com correspondência
            tem_correspondencia = df_cartorio['CRM_UF_CRM_CAMPO_COMPARACAO'].notna()
            
            # Opções para o filtro de ID Família
            opcoes_id_familia = [
                "Todos", 
                "Com correspondência no CRM", 
                "Sem correspondência no CRM"
            ]
            
            id_familia_filter = st.selectbox(
                "Filtrar por correspondência com CRM:",
                options=opcoes_id_familia,
                index=0,
                help="Filtra IDs de família com base na correspondência com o campo UF_CRM_1722605592778 do CRM."
            )
    
    # Adicionar filtro de data (criado em/data da venda)
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 5px solid #1976D2;">
        <h4 style="margin-top: 0; color: #1A237E; font-size: 1.1rem;">📅 Filtro por Data da Venda</h4>
        <p style="margin-bottom: 5px; font-size: 0.9rem; color: #555;">
            Selecione o período desejado para visualizar os registros por data de criação.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Adicionar checkbox para desativar o filtro de data em posição mais destacada
    sem_filtro_data = st.checkbox("✅ Sem filtro de data (mostrar todos os registros independente da data)", 
                               value=True, 
                               key="sem_filtro_data_cartorio",
                               help="Marque esta opção para desativar o filtro de data e ver todos os registros")
    
    # Determinar campo de data disponível
    campo_data = None
    if 'DATE_CREATE' in df_cartorio.columns:
        campo_data = 'DATE_CREATE'
    elif 'CRM_DATE_CREATE' in df_cartorio.columns:
        campo_data = 'CRM_DATE_CREATE'
    
    # Mostrar os campos de data somente se a opção "Sem filtro" NÃO estiver marcada
    if campo_data and not sem_filtro_data:
        col_data_inicio, col_data_fim = st.columns(2)
        # Converter para formato datetime se necessário
        if not pd.api.types.is_datetime64_any_dtype(df_cartorio[campo_data]):
            try:
                df_cartorio[campo_data] = pd.to_datetime(df_cartorio[campo_data], errors='coerce')
            except:
                st.warning(f"Não foi possível converter o campo {campo_data} para formato de data.")
        
        # Obter a data mínima e máxima para os limites do calendário
        try:
            min_date = df_cartorio[campo_data].min().date()
            max_date = df_cartorio[campo_data].max().date()
            
            # Se as datas são inválidas, usar valores padrão
            if pd.isna(min_date) or pd.isna(max_date):
                from datetime import timedelta
                today = dt.now().date()
                min_date = today - timedelta(days=365)  # 1 ano atrás
                max_date = today
            
            with col_data_inicio:
                data_inicio = st.date_input(
                    "Data da Venda (início):",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    help="Filtrar registros a partir desta data de criação"
                )
            
            with col_data_fim:
                data_fim = st.date_input(
                    "Data da Venda (fim):",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    help="Filtrar registros até esta data de criação"
                )
            
            # Formatação bonita para as datas
            inicio_formatado = data_inicio.strftime('%d/%m/%Y')
            fim_formatado = data_fim.strftime('%d/%m/%Y')
            
            # Mostrar intervalo de datas selecionado
            st.markdown(f"""
            <div style="background-color: #E3F2FD; padding: 10px; border-radius: 5px; text-align: center; margin-top: 10px; margin-bottom: 15px;">
                <p style="margin: 0; font-weight: 600; color: #1976D2;">
                    Período selecionado: {inicio_formatado} a {fim_formatado}
                </p>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Erro ao configurar filtro de data: {str(e)}")
    elif sem_filtro_data:
        st.success("✅ Filtro de data desativado. Exibindo todos os registros, independente da data.")
    elif not campo_data:
        st.warning("Não foi possível encontrar um campo de data para filtragem. O filtro de Data da Venda não está disponível.")

    # Aplicar filtro de cartório aos dados
    if cartorio_filter:
        df_cartorio_filtrado = df_cartorio[df_cartorio['NOME_CARTORIO'].isin(cartorio_filter)].copy()
        st.info(f"Exibindo dados para: {', '.join(cartorio_filter)}")
    else:
        st.warning("Nenhum cartório selecionado. Exibindo todos os dados.")
        df_cartorio_filtrado = df_cartorio.copy()
    
    # Aplicar filtro de ID Família se selecionado
    if 'CRM_UF_CRM_CAMPO_COMPARACAO' in df_cartorio_filtrado.columns and id_familia_filter != "Todos":
        if id_familia_filter == "Com correspondência no CRM":
            df_cartorio_filtrado = df_cartorio_filtrado[df_cartorio_filtrado['CRM_UF_CRM_CAMPO_COMPARACAO'].notna()]
            st.info(f"Filtrando por IDs de família com correspondência no CRM: {len(df_cartorio_filtrado)} registros.")
        elif id_familia_filter == "Sem correspondência no CRM":
            df_cartorio_filtrado = df_cartorio_filtrado[df_cartorio_filtrado['CRM_UF_CRM_CAMPO_COMPARACAO'].isna()]
            st.info(f"Filtrando por IDs de família sem correspondência no CRM: {len(df_cartorio_filtrado)} registros.")
    
    # Aplicar filtro de data
    if campo_data and 'data_inicio' in locals() and 'data_fim' in locals() and not sem_filtro_data:
        # Converter as datas para datetime para comparação
        data_inicio_dt = pd.to_datetime(data_inicio)
        data_fim_dt = pd.to_datetime(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # Até o final do dia
        
        # Contar registros antes de aplicar o filtro
        total_antes = len(df_cartorio_filtrado)
        
        # Aplicar filtro de data
        mask_data = (df_cartorio_filtrado[campo_data] >= data_inicio_dt) & (df_cartorio_filtrado[campo_data] <= data_fim_dt)
        df_cartorio_filtrado = df_cartorio_filtrado[mask_data]
        
        # Contar registros após o filtro
        total_depois = len(df_cartorio_filtrado)
        percentual = round(total_depois/total_antes*100 if total_antes > 0 else 0, 1)
        
        # Se pelo menos um filtro foi aplicado, mostrar resumo visual
        if data_inicio != min_date or data_fim != max_date:
            # Determinar a cor com base no percentual de filtragem
            cor_fundo = "#E8F5E9" if percentual > 50 else "#FFF8E1" if percentual > 20 else "#FFEBEE"
            cor_texto = "#2E7D32" if percentual > 50 else "#F57F17" if percentual > 20 else "#C62828"
            
            # Exibir um resumo visual do resultado do filtro
            st.markdown(f"""
            <div style="background-color: {cor_fundo}; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 5px solid {cor_texto}; display: flex; align-items: center;">
                <div style="flex: 1;">
                    <h4 style="margin-top: 0; color: {cor_texto}; font-size: 1.1rem;">Resultado do Filtro de Data</h4>
                    <p style="margin-bottom: 0; font-size: 0.9rem;">
                        De <strong>{total_antes}</strong> registros, <strong>{total_depois}</strong> atendem ao filtro de data ({percentual}%)
                    </p>
                </div>
                <div style="width: 100px; height: 100px; margin-left: 15px;">
                    <svg viewBox="0 0 36 36" width="100%" height="100%">
                        <path d="M18 2.0845
                            a 15.9155 15.9155 0 0 1 0 31.831
                            a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none" stroke="#E0E0E0" stroke-width="3" />
                        <path d="M18 2.0845
                            a 15.9155 15.9155 0 0 1 0 31.831
                            a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none" stroke="{cor_texto}" stroke-width="3" stroke-dasharray="{percentual}, 100" />
                        <text x="18" y="20.5" font-family="Arial" font-size="10" text-anchor="middle" fill="{cor_texto}" font-weight="bold">{percentual}%</text>
                    </svg>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider() # Adiciona um separador

    # Adicionar CSS para as abas (mantido)
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab"] {
        font-weight: 600 !important; /* Ajuste no peso da fonte */
        color: #1A237E !important;
        height: 55px !important; /* Ajuste na altura */
        padding: 8px 18px !important; /* Ajuste no padding */
        font-size: 1rem !important; /* Tamanho de fonte padrão */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-right: 5px !important;
        border-radius: 8px 8px 0 0 !important;
        border-bottom: 2px solid transparent !important; /* Borda inferior sutil */
    }
    .stTabs [aria-selected="true"] {
        background-color: #E3F2FD !important; /* Cor de fundo mais suave */
        color: #1976D2 !important; /* Cor do texto */
        font-weight: 700 !important; /* Destaque para aba ativa */
        border-bottom: 3px solid #FF9800 !important; /* Borda inferior destacada */
    }
    .stTabs [data-baseweb="tab-list"] {
        margin-bottom: 25px !important; /* Aumento do espaçamento */
        gap: 8px !important; /* Ajuste no espaçamento entre abas */
    }
    /* Estilo para expanders */
    .streamlit-expanderHeader {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #1A237E !important;
        background-color: #f0f2f6 !important; /* Fundo suave */
        border-radius: 5px !important;
        padding: 10px 15px !important;
    }
    /* Estilo para títulos dentro das abas */
    h2.tab-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1A237E;
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 6px;
        border-bottom: 2px solid #1976D2;
    }
    </style>
    """, unsafe_allow_html=True)

    # Mostrar informações relevantes com a nova estrutura de abas
    if not df_cartorio_filtrado.empty:
        # Criar 7 abas reorganizadas (adicionando a nova aba de Análise de Tempo)
        tab_visao_geral, tab_prod_etapas, tab_tempo_crm, tab_movimentacoes, tab_acomp_emissao, tab_qualidade, tab_protocolado, tab_emissoes_cartao, tab_visao_anterior = st.tabs([
            "📊 Visão Geral",
            "⏱️ Produtividade por Etapas",
            "⏳ Análise de Tempo",
            "🔄 Movimentações",
            "📈 Acompanhamento Emissão",
            "🔍 Qualidade dos Dados",
            "📋 Status Protocolado",
            "🪪 Certidões Carrão",
            "📑 Visão Anterior"
        ])

        # Aba 1: Visão Geral
        with tab_visao_geral:
            st.markdown("<h2 class='tab-title'>Visão Geral dos Dados</h2>", unsafe_allow_html=True)
            st.caption("Tabela com os dados brutos filtrados dos cartórios selecionados.")
            
            # Adicionar expander para mostrar estatísticas sobre a correspondência com o CRM
            if 'CRM_UF_CRM_CAMPO_COMPARACAO' in df_cartorio_filtrado.columns:
                with st.expander("Estatísticas de Correspondência com CRM", expanded=True):
                    # Calcular estatísticas
                    total_registros = len(df_cartorio_filtrado)
                    com_correspondencia = df_cartorio_filtrado['CRM_UF_CRM_CAMPO_COMPARACAO'].notna().sum()
                    sem_correspondencia = total_registros - com_correspondencia
                    
                    # Calcular percentuais
                    perc_com = (com_correspondencia / total_registros * 100) if total_registros > 0 else 0
                    perc_sem = (sem_correspondencia / total_registros * 100) if total_registros > 0 else 0
                    
                    # Exibir em colunas com métricas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Registros", total_registros)
                    with col2:
                        st.metric("Com Correspondência", com_correspondencia, f"{perc_com:.1f}%")
                    with col3:
                        st.metric("Sem Correspondência", sem_correspondencia, f"{perc_sem:.1f}%")
            
            # Exibir a tabela de dados
            visualizar_cartorio_dados(df_cartorio_filtrado)
            
            # Adicionar expander para mostrar detalhes das correspondências entre ID_FAMILIA e UF_CRM_1722605592778
            if 'CRM_UF_CRM_CAMPO_COMPARACAO' in df_cartorio_filtrado.columns:
                with st.expander("Detalhes de Correspondência entre UF_CRM_12_1723552666 e UF_CRM_1722605592778", expanded=True):
                    # Criar DataFrame para exibição focada na correspondência
                    df_correspondencia = df_cartorio_filtrado[[
                        'ID_FAMILIA', 'NOME_CARTORIO', 'TITLE', 'ASSIGNED_BY_NAME', 
                        'CRM_ID', 'CRM_TITLE', 'CRM_ASSIGNED_BY_NAME', 'CRM_DATE_CREATE'
                    ]].copy()
                    
                    # Renomear colunas para melhor visualização
                    df_correspondencia = df_correspondencia.rename(columns={
                        'ID_FAMILIA': 'ID Família',
                        'NOME_CARTORIO': 'Cartório',
                        'TITLE': 'Nome no Cartório',
                        'ASSIGNED_BY_NAME': 'Responsável Cartório',
                        'CRM_ID': 'ID no CRM',
                        'CRM_TITLE': 'Nome no CRM',
                        'CRM_ASSIGNED_BY_NAME': 'Responsável CRM',
                        'CRM_DATE_CREATE': 'Data Criação CRM'
                    })
                    
                    # Adicionar coluna de status
                    df_correspondencia['Status'] = df_correspondencia['ID no CRM'].apply(
                        lambda x: "✅ Com correspondência" if pd.notna(x) else "❌ Sem correspondência"
                    )
                    
                    # Mostrar a tabela
                    st.dataframe(
                        df_correspondencia,
                        column_config={
                            "ID Família": st.column_config.TextColumn(
                                "ID Família", 
                                help="UF_CRM_12_1723552666"
                            ),
                            "Cartório": st.column_config.TextColumn(
                                "Cartório", 
                                width="medium"
                            ),
                            "Nome no Cartório": st.column_config.TextColumn(
                                "Nome no Cartório", 
                                width="medium"
                            ),
                            "Responsável Cartório": st.column_config.TextColumn(
                                "Resp. Cartório", 
                                width="medium"
                            ),
                            "ID no CRM": st.column_config.TextColumn(
                                "ID no CRM", 
                                width="small"
                            ),
                            "Nome no CRM": st.column_config.TextColumn(
                                "Nome no CRM", 
                                width="medium"
                            ),
                            "Responsável CRM": st.column_config.TextColumn(
                                "Resp. CRM", 
                                width="medium"
                            ),
                            "Data Criação CRM": st.column_config.DatetimeColumn(
                                "Data Criação", 
                                format="DD/MM/YYYY HH:mm", 
                                width="medium"
                            ),
                            "Status": st.column_config.TextColumn(
                                "Status", 
                                width="medium"
                            )
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Adicionar botão para exportar
                    csv = df_correspondencia.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Exportar Correspondências para CSV",
                        data=csv,
                        file_name=f"correspondencias_id_familia_{dt.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        help="Baixar os dados de correspondência em formato CSV"
                    )
            
            # Gráfico de distribuição por cartório (mantido comentado)
            # st.subheader("Distribuição por Cartório")
            # visualizar_grafico_cartorio(df_cartorio_filtrado)

        # Aba 2: Produtividade por Etapas
        with tab_prod_etapas:
            st.markdown("<h2 class='tab-title'>Produtividade por Etapas</h2>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <p style="margin: 0;">Análise da produtividade baseada nas datas de conclusão de cada etapa do processo.
                Filtre por período (dia, semana, mês) e por responsável.</p>
                <p style="margin-top: 10px; font-size: 14px; color: #666;">
                    <strong>Nota:</strong> Considera os campos de data específicos de cada etapa.
                </p>
            </div>
            """, unsafe_allow_html=True)
            analisar_produtividade_etapas(df_cartorio_filtrado) # Passando o df filtrado

        # Nova Aba: Análise de Tempo do CRM
        with tab_tempo_crm:
            st.markdown("<h2 class='tab-title'>Análise de Tempo do Processo</h2>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <p style="margin: 0;">Visualização do funil de processamento e análise detalhada do tempo entre etapas do processo.</p>
                <p style="margin-top: 10px; font-size: 14px; color: #666;">
                    <strong>Personalização:</strong> Utilize as configurações na barra lateral para ajustar os parâmetros de SLA.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Chamar o dashboard de tempo passando o dataframe filtrado
            mostrar_dashboard_tempo_crm(df_cartorio_filtrado)

        # Aba 3: Movimentações
        with tab_movimentacoes:
            st.markdown("<h2 class='tab-title'>Análise de Movimentações</h2>", unsafe_allow_html=True)
            st.caption("Análise geral de movimentações e produtividade (método anterior).")
            # Conteúdo original da Aba 6
            analisar_movimentacoes(df_cartorio_filtrado) # Usando alias e passando o df filtrado

        # Aba 4: Acompanhamento Emissão
        with tab_acomp_emissao:
            st.markdown("<h2 class='tab-title'>Acompanhamento de Emissão por Família</h2>", unsafe_allow_html=True)
            # Conteúdo original da Aba 3 (renomeada)
            # Explicação do processo com estilo aprimorado
            st.markdown("""
            <div style="background-color: #E8EAF6; padding: 18px; border-radius: 8px; margin-bottom: 20px;
            border-left: 5px solid #3F51B5; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <p style="margin: 0; font-size: 1rem; color: #283593;">Acompanhamento do percentual de conclusão das certidões solicitadas por família.</p>
                <p style="margin-top: 12px; font-size: 0.9rem; color: #455A64;">
                    <strong>Nota:</strong> Certidões em etapas de Sucesso no Bitrix são consideradas concluídas.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Carregar dados (a função não depende do filtro de cartório aplicado aqui, busca dados gerais)
            with st.spinner("Carregando dados de acompanhamento..."):
                # Idealmente, a função analisar_acompanhamento_emissao_familia também deveria aceitar o filtro,
                # mas mantendo como está por enquanto.
                df_acompanhamento = analisar_acompanhamento_emissao_familia()

            if df_acompanhamento is not None and not df_acompanhamento.empty:
                # Aplicar filtro de ID Família se o df_cartorio_filtrado tiver essa coluna
                if 'ID_FAMILIA' in df_cartorio_filtrado.columns and 'ID_FAMILIA' in df_acompanhamento.columns:
                    ids_filtrados = df_cartorio_filtrado['ID_FAMILIA'].unique()
                    df_acompanhamento_filtrado = df_acompanhamento[df_acompanhamento['ID_FAMILIA'].isin(ids_filtrados)]
                    st.info(f"Exibindo acompanhamento para {len(df_acompanhamento_filtrado)} famílias presentes nos cartórios selecionados.")
                else:
                    df_acompanhamento_filtrado = df_acompanhamento # Mostrar todos se não for possível filtrar

                if not df_acompanhamento_filtrado.empty:
                    # Exibição de estatísticas gerais (métricas) com mais estilo
                    st.markdown("<h3 style='color: #1A237E; margin-top: 30px; font-size: 1.3rem;'>Resumo Geral do Acompanhamento</h3>", unsafe_allow_html=True)

                    # Calcular estatísticas com base nos dados filtrados
                    total_familias = len(df_acompanhamento_filtrado)
                    total_certidoes = df_acompanhamento_filtrado['TOTAL_CERTIDOES'].sum()
                    total_concluidas = df_acompanhamento_filtrado['CERTIDOES_CONCLUIDAS'].sum()
                    percentual_geral = (total_concluidas / total_certidoes * 100) if total_certidoes > 0 else 0

                    # Métricas em cards com cores
                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    with m_col1:
                        st.markdown("""
                        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: 110px; display: flex; flex-direction: column; justify-content: center;">
                            <h2 style="margin:0; color: #1565C0; font-size: 2rem;">{total_familias}</h2>
                            <p style="margin:0; color: #1976D2; font-weight: bold; font-size: 0.9rem;">Famílias Analisadas</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with m_col2:
                        st.markdown("""
                        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: 110px; display: flex; flex-direction: column; justify-content: center;">
                            <h2 style="margin:0; color: #2E7D32; font-size: 2rem;">{total_certidoes}</h2>
                            <p style="margin:0; color: #388E3C; font-weight: bold; font-size: 0.9rem;">Total de Certidões</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with m_col3:
                        st.markdown("""
                        <div style="background-color: #FFF8E1; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: 110px; display: flex; flex-direction: column; justify-content: center;">
                            <h2 style="margin:0; color: #FF8F00; font-size: 2rem;">{total_concluidas}</h2>
                            <p style="margin:0; color: #FFA000; font-weight: bold; font-size: 0.9rem;">Certidões Concluídas</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with m_col4:
                        st.markdown("""
                        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: 110px; display: flex; flex-direction: column; justify-content: center;">
                            <h2 style="margin:0; color: #C62828; font-size: 2rem;">{percentual_geral:.1f}%</h2>
                            <p style="margin:0; color: #D32F2F; font-weight: bold; font-size: 0.9rem;">Percentual Concluído</p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Separador visual
                    st.divider()

                    # Título da tabela com estilo
                    st.markdown("<h3 style='color: #1A237E; font-size: 1.3rem;'>Detalhamento por Família</h3>", unsafe_allow_html=True)

                    # Preparar dataframe para exibição
                    df_display = df_acompanhamento_filtrado.copy()
                    df_display['PERCENTUAL_TEXTO'] = df_display['PERCENTUAL_CONCLUSAO'].apply(lambda x: f"{x:.1f}%")

                    # Exibir tabela com os dados
                    st.dataframe(
                        df_display,
                        column_config={
                            "ID_FAMILIA": st.column_config.TextColumn("ID Família", help="Identificador único da família", width="medium"),
                            "NOME_FAMILIA": st.column_config.TextColumn("Nome da Família", help="Nome da família registrado", width="large"),
                            "TOTAL_REQUERENTES": st.column_config.NumberColumn("Requerentes", format="%d", help="Quantidade de requerentes", width="small"),
                            "TOTAL_CERTIDOES": st.column_config.NumberColumn("Total Cert.", format="%d", help="Total de certidões solicitadas", width="small"),
                            "CERTIDOES_CONCLUIDAS": st.column_config.NumberColumn("Concluídas", format="%d", help="Certidões concluídas", width="small"),
                            "PERCENTUAL_TEXTO": st.column_config.TextColumn("Perc. Texto", help="Percentual concluído", width="small"),
                            "PERCENTUAL_CONCLUSAO": st.column_config.ProgressColumn("% Conclusão", min_value=0, max_value=100, format=" ", help="Progresso visual") # Format vazio para mostrar só barra
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                    # Botões de ação
                    btn_col1, btn_col2 = st.columns([1, 4])
                    with btn_col1:
                        if st.button("🔄 Atualizar Dados", key="atualizar_acomp", type="primary", help="Recarrega os dados de acompanhamento"):
                            st.rerun()
                    with btn_col2:
                        csv = df_acompanhamento_filtrado.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Exportar para CSV",
                            data=csv,
                            file_name=f"acompanhamento_emissao_familia_{dt.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            help="Baixar os dados detalhados em formato CSV"
                        )

                    # Informações sobre etapas de sucesso (mantido em expander)
                    with st.expander("Definição de Etapas de Sucesso", expanded=False):
                        st.markdown("""
                        <div style="background-color: #F5F5F5; padding: 15px; border-radius: 6px;">
                            <h4 style="color: #1A237E; margin-top: 0;">Etapas que contam como certidões concluídas:</h4>
                            <ul style="margin-bottom: 0; padding-left: 20px; font-size: 0.9rem;">
                                <li><code>SUCCESS</code> - Sucesso geral</li>
                                <li><code>DT1052_16:SUCCESS</code> - Sucesso Casa Verde</li>
                                <li><code>DT1052_34:SUCCESS</code> - Sucesso Tatuapé</li>
                                <li><code>DT1052_16:UC_JRGCW3</code> - Certidão Pronta Casa Verde</li>
                                <li><code>DT1052_34:UC_84B1S2</code> - Certidão Pronta Tatuapé</li>
                                <li><code>UC_JRGCW3</code> - Certidão Pronta (genérico)</li>
                                <li><code>UC_84B1S2</code> - Certidão Pronta (genérico)</li>
                                <li><code>DT1052_16:CLIENT</code> - Entregue ao Cliente Casa Verde</li>
                                <li><code>DT1052_34:CLIENT</code> - Entregue ao Cliente Tatuapé</li>
                                <li><code>DT1052_34:UC_D0RG5P</code> - Finalização específica Tatuapé</li>
                                <li><code>CLIENT</code> - Entregue ao Cliente (genérico)</li>
                                <li><code>UC_D0RG5P</code> - Finalização específica (genérico)</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Nenhuma família encontrada para os cartórios selecionados nesta análise.")
            else:
                # Mensagem de erro estilizada (mantida)
                st.markdown("""
                <div style="background-color: #FFEBEE; padding: 15px; border-radius: 8px; margin-top: 20px;
                border-left: 5px solid #C62828; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <p style="margin: 0; color: #B71C1C; font-weight: bold;">Erro ao carregar dados</p>
                    <p style="margin-top: 8px; color: #D32F2F;">
                        Não foi possível carregar os dados de acompanhamento. Verifique a conexão ou os logs.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔄 Tentar Novamente", key="tentar_acomp", type="primary"):
                    st.rerun()

        # Aba 5: Qualidade dos Dados (Agrupando antigas abas 4, 5, 7)
        with tab_qualidade:
            st.markdown("<h2 class='tab-title'>Análises de Qualidade dos Dados</h2>", unsafe_allow_html=True)
            st.caption("Verificações de higienização, IDs de família e consistência dos cadastros.")
            st.divider()

            # Expander 1: Análise Detalhada de Higienização (antiga Aba 4)
            with st.expander("Análise Detalhada de Higienização", expanded=False):
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                    <p style="margin: 0;">Cruzamento de dados das famílias entre tabelas do Bitrix,
                    exibindo informações sobre responsáveis, certidões e status de higienização.</p>
                    <p style="margin-top: 10px; font-size: 14px; color: #666;">
                        <strong>Nota:</strong> A análise completa pode levar alguns instantes.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Executar Análise de Higienização", key="exec_higienizacao"):
                    with st.spinner("Analisando higienização..."):
                        df_analise_hig = analisar_familia_certidoes() # Função original

                    if df_analise_hig is not None and not df_analise_hig.empty:
                        st.write("Resultado da Análise de Higienização:")

                        # Adicionar filtros (adaptados da versão original)
                        f_col_resp, f_col_cart = st.columns(2)
                        with f_col_resp:
                            responsaveis_hig = ['Todos'] + sorted(df_analise_hig['RESPONSAVEL_ADM'].dropna().unique().tolist())
                            resp_sel_hig = st.selectbox("Filtrar por Responsável ADM:", responsaveis_hig, key="resp_hig")
                        with f_col_cart:
                            cartorios_hig = ['Todos'] + sorted(df_analise_hig['CARTORIO'].dropna().unique().tolist())
                            cart_sel_hig = st.selectbox("Filtrar por Cartório:", cartorios_hig, key="cart_hig")

                        # Aplicar filtros
                        df_filtrado_hig = df_analise_hig.copy()
                        if resp_sel_hig != 'Todos':
                            df_filtrado_hig = df_filtrado_hig[df_filtrado_hig['RESPONSAVEL_ADM'] == resp_sel_hig]
                        if cart_sel_hig != 'Todos':
                            df_filtrado_hig = df_filtrado_hig[df_filtrado_hig['CARTORIO'] == cart_sel_hig]

                        # Métricas (adaptadas)
                        st.markdown("<h4 style='margin-top: 20px;'>Resumo Filtrado:</h4>", unsafe_allow_html=True)
                        m_hig_col1, m_hig_col2, m_hig_col3, m_hig_col4 = st.columns(4)
                        with m_hig_col1:
                            st.metric("Famílias", len(df_filtrado_hig))
                        with m_hig_col2:
                            media_membros_hig = df_filtrado_hig['MEMBROS'].mean() if 'MEMBROS' in df_filtrado_hig.columns and not df_filtrado_hig['MEMBROS'].empty else 0
                            st.metric("Média Membros", f"{media_membros_hig:.1f}")
                        with m_hig_col3:
                            total_cert_hig = df_filtrado_hig['TOTAL_CERTIDOES'].sum()
                            entregues_hig = df_filtrado_hig['CERTIDOES_ENTREGUES'].sum()
                            taxa_hig = (entregues_hig / total_cert_hig * 100) if total_cert_hig > 0 else 0
                            st.metric("Taxa Entrega", f"{taxa_hig:.1f}%")
                        with m_hig_col4:
                            total_req_hig = df_filtrado_hig['TOTAL_REQUERENTES'].sum() if 'TOTAL_REQUERENTES' in df_filtrado_hig.columns else 0
                            st.metric("Total Requerentes", f"{total_req_hig}")

                        # Tabela (adaptada)
                        st.dataframe(
                            df_filtrado_hig[[
                                'ID_FAMILIA', 'NOME', 'CARTORIO', 'RESPONSAVEL_ADM', 'RESPONSAVEL_VENDAS',
                                'TOTAL_CERTIDOES', 'CERTIDOES_ENTREGUES', 'MEMBROS', 'TOTAL_REQUERENTES',
                                'ID_REQUERENTE', 'STATUS_HIGILIZACAO'
                            ]].rename(columns={ # Renomeando para melhor leitura
                                'ID_FAMILIA': 'ID Família', 'NOME': 'Nome Família', 'CARTORIO': 'Cartório',
                                'RESPONSAVEL_ADM': 'Resp. ADM', 'RESPONSAVEL_VENDAS': 'Resp. Vendas',
                                'TOTAL_CERTIDOES': 'Total Cert.', 'CERTIDOES_ENTREGUES': 'Entregues',
                                'MEMBROS': 'Membros', 'TOTAL_REQUERENTES': 'Requerentes', 'ID_REQUERENTE': 'ID Requerente',
                                'STATUS_HIGILIZACAO': 'Status Hig.'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                        # Adicionar exportação para CSV
                        csv_hig = df_filtrado_hig.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Exportar Análise Higienização (CSV)",
                            data=csv_hig,
                            file_name=f"analise_higienizacao_{dt.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            key="export_hig"
                        )
                    elif df_analise_hig is not None:
                         st.info("Nenhum dado encontrado na análise de higienização.")
                    else:
                        st.error("Erro ao realizar a análise de higienização. Verifique os logs.")
                else:
                    st.info("Clique no botão acima para executar a análise detalhada de higienização.")

            st.divider() # Separador entre expanders

            # Expander 2: Verificação de IDs de Família (antiga Aba 5)
            with st.expander("Verificação de IDs de Família (Duplicados, Inválidos)", expanded=False):
                st.markdown("""
                <p style="margin-bottom: 15px;">Identifica IDs de família que estão duplicados, vazios ou fora do padrão esperado nos registros dos cartórios selecionados.</p>
                """, unsafe_allow_html=True)

                # Usar o df_cartorio_filtrado que já tem o filtro de cartório aplicado
                with st.spinner("Analisando IDs de família..."):
                     # Adicionar verificação se a coluna existe antes de chamar a análise
                    if 'ID_FAMILIA' in df_cartorio_filtrado.columns:
                         family_id_summary, family_id_details = analyze_cartorio_ids(df_cartorio_filtrado)
                    else:
                         family_id_summary, family_id_details = pd.DataFrame(), pd.DataFrame() # DataFrames vazios se a coluna não existir
                         st.warning("Coluna 'ID_FAMILIA' não encontrada nos dados carregados para esta análise.")

                if family_id_summary is not None and not family_id_summary.empty:
                    st.markdown("##### Resumo da Verificação")
                    st.dataframe(
                        family_id_summary,
                        column_config={
                            "Status": st.column_config.TextColumn("Status do ID", width="medium", help="Classificação do ID"),
                            "Quantidade": st.column_config.NumberColumn("Quantidade", format="%d", width="small", help="Número de registros")
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                    st.markdown("##### Detalhes dos IDs com Problemas")
                    # Filtros para o detalhamento (simplificados, usando dados já filtrados por cartório)
                    status_options = family_id_details['Status do ID'].unique()
                    selected_id_status = st.multiselect(
                        "Filtrar por Status do ID:",
                        options=status_options,
                        default=[s for s in status_options if s != 'Padrão Correto'], # Padrão: mostrar problemas
                        key="status_id_filter",
                        help="Selecione os status que deseja visualizar nos detalhes."
                    )

                    resp_options = sorted(family_id_details['Responsável'].dropna().unique())
                    resp_filter = st.multiselect(
                        "Filtrar por Responsável:",
                        options=resp_options,
                        key="resp_id_filter",
                        help="Selecione os responsáveis."
                    )

                    # Aplicar filtros adicionais
                    filtered_details = family_id_details.copy()
                    if selected_id_status:
                        filtered_details = filtered_details[filtered_details['Status do ID'].isin(selected_id_status)]
                    if resp_filter:
                        filtered_details = filtered_details[filtered_details['Responsável'].isin(resp_filter)]

                    if not filtered_details.empty:
                        st.dataframe(
                            filtered_details,
                            column_config={
                                "ID": st.column_config.TextColumn("ID Registro", width="small"),
                                "Nome": st.column_config.TextColumn("Nome Registro", width="medium"),
                                "ID Família": st.column_config.TextColumn("ID Família", width="medium"),
                                "Cartório": st.column_config.TextColumn("Cartório", width="medium"),
                                "Responsável": st.column_config.TextColumn("Responsável", width="medium"),
                                "Status do ID": st.column_config.TextColumn("Status ID", width="small")
                            },
                            use_container_width=True,
                            hide_index=True,
                            key="details_id_table"
                        )

                        # Botão para exportar Excel
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            family_id_summary.to_excel(writer, sheet_name='Resumo_IDs', index=False)
                            filtered_details.to_excel(writer, sheet_name='Detalhes_IDs', index=False)
                        excel_data = output.getvalue()

                        st.download_button(
                            label="📥 Exportar Verificação de IDs (Excel)",
                            data=excel_data,
                            file_name=f"verificacao_ids_familia_{dt.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="export_ids_excel"
                        )
                    else:
                        st.info("Nenhum registro encontrado com os filtros de status e responsável selecionados.")
                elif family_id_summary is not None:
                     st.info("Nenhum problema encontrado nos IDs de família para os cartórios selecionados.")
                # Não mostrar erro se a coluna 'ID_FAMILIA' não foi encontrada, já foi avisado antes.

            st.divider() # Separador entre expanders

            # Expander 3: Confronto Emissão vs Cadastro Famílias (antiga Aba 7)
            with st.expander("Confronto Emissão vs Cadastro de Famílias", expanded=False):
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                    <p style="margin: 0;">Compara negócios da categoria 'Emissão' (ID 32) com o cadastro geral de famílias,
                    identificando negócios cuja família associada não está cadastrada no sistema.</p>
                    <p style="margin-top: 10px; font-size: 14px; color: #666;">
                        <strong>Nota:</strong> A análise completa pode levar alguns instantes.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Executar Análise de Confronto", key="exec_confronto"):
                    # A função original analisar_familias_ausentes não parece depender do df_cartorio,
                    # ela busca dados específicos (categoria 32 e cadastro geral). Mantendo assim.
                    with st.spinner("Realizando confronto de dados..."):
                        total_ausentes, df_ausentes = analisar_familias_ausentes()

                    if df_ausentes is not None and total_ausentes > 0:
                        st.markdown("""
                        <div style="background-color: #ffebee; padding: 15px; border-radius: 10px; border-left: 5px solid #e53935; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h4 style="margin-top: 0; color: #c62828;">Negócios com Famílias Não Cadastradas: <span style='font-size: 1.5rem; font-weight: bold;'>{total_ausentes}</span></h4>
                            <p style="font-size: 0.9rem; margin-bottom: 0;">
                                Negócios da categoria 32 que referenciam IDs de família (<code>UF_CRM_1722605592778</code>)
                                que não foram encontrados no cadastro geral (<code>UF_CRM_12_1723552666</code>).
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.subheader("Detalhes dos Negócios Afetados")
                        st.dataframe(
                            df_ausentes,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "ID do Negócio": st.column_config.NumberColumn("ID Negócio", format="%d"),
                                "Nome do Negócio": "Nome Negócio",
                                "Responsável": "Responsável",
                                "ID da Família": st.column_config.TextColumn("ID Família (Não Cadastrada)")
                            }
                        )

                        csv_ausentes = df_ausentes.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Exportar Dados para CSV",
                            data=csv_ausentes,
                            file_name=f"negocios_familias_nao_cadastradas_{dt.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            key="exp_negocios_csv"
                        )
                    elif df_ausentes is not None and total_ausentes == 0:
                        st.success("✅ Confronto realizado! Todos os negócios da categoria 32 possuem famílias cadastradas.")
                    else:
                         st.error("Erro ao realizar a análise de confronto. Verifique os logs.")
                else:
                    st.info("Clique no botão acima para executar a análise de confronto.")

        # Nova Aba: Status Protocolado Emissões Brasileiras
        with tab_protocolado:
            st.markdown("<h2 class='tab-title'>Status Protocolado Emissões Brasileiras</h2>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background-color: #E8EAF6; padding: 18px; border-radius: 8px; margin-bottom: 20px;
            border-left: 5px solid #3F51B5; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <p style="margin: 0; font-size: 1rem; color: #283593;">Análise das famílias protocoladas e status das emissões, com foco nas unidades Carrão e Alphaville.</p>
                <p style="margin-top: 12px; font-size: 0.9rem; color: #455A64;">
                    <strong>Nota:</strong> Esta visualização exibe o progresso das emissões para cada família protocolada.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Chamar a função que exibe o dashboard de protocolado
            exibir_dashboard_protocolado()

        # Nova Aba: Emissões Cartão
        with tab_emissoes_cartao:
            # Chamar a função que exibe o dashboard de emissões cartão
            exibir_dashboard_emissoes_cartao()

        # Aba 6: Visão Anterior
        with tab_visao_anterior:
            st.markdown("<h2 class='tab-title'>Visão Anterior (Agregada)</h2>", unsafe_allow_html=True)
            st.caption("Visão agregada por cartório (método anterior).")
            # Conteúdo original da Aba 8
            with st.spinner("Gerando visão anterior..."):
                visao_geral_anterior = criar_visao_geral_cartorio(df_cartorio_filtrado) # Passando o df filtrado

            if visao_geral_anterior is not None and not visao_geral_anterior.empty:
                st.dataframe(visao_geral_anterior, use_container_width=True, hide_index=True)
            elif visao_geral_anterior is not None:
                 st.info("Nenhum dado disponível para a visão anterior com os filtros aplicados.")
            else:
                st.error("Não foi possível gerar a visão anterior. Verifique os dados ou logs.")
    else:
        st.info("Nenhum dado disponível para os cartórios selecionados.")

    # Rodapé
    st.divider()
    st.caption(f"Painel Cartório | Dados atualizados em: {dt.now().strftime('%d/%m/%Y %H:%M:%S')}") 

# Para teste direto deste arquivo
if __name__ == "__main__":
    show_cartorio() 