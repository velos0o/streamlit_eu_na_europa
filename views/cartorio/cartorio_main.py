import streamlit as st
from .data_loader import carregar_dados_cartorio
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
import pandas as pd
import io
from datetime import datetime

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

    # Carregar os dados dos cartórios
    with st.spinner("Carregando dados dos cartórios..."):
        df_cartorio = carregar_dados_cartorio()

    if df_cartorio.empty:
        st.warning("Não foi possível carregar os dados dos cartórios. Verifique a conexão com o Bitrix24.")
        return
    else:
        st.success(f"Dados carregados: {len(df_cartorio)} registros encontrados.")
        st.divider() # Adiciona um separador

    # Filtro de cartório (mantido no topo para aplicação global)
    st.markdown("#### Filtros Gerais")
    cartorio_filter = st.multiselect(
        "Selecione os Cartórios:",
        options=sorted(df_cartorio['NOME_CARTORIO'].unique()), # Opções dinâmicas
        default=sorted(df_cartorio['NOME_CARTORIO'].unique()), # Padrão: todos
        help="Selecione um ou mais cartórios para filtrar os dados exibidos abaixo."
    )

    # Aplicar filtro de cartório aos dados
    if cartorio_filter:
        df_cartorio_filtrado = df_cartorio[df_cartorio['NOME_CARTORIO'].isin(cartorio_filter)].copy()
        st.info(f"Exibindo dados para: {', '.join(cartorio_filter)}")
    else:
        st.warning("Nenhum cartório selecionado. Exibindo todos os dados.")
        df_cartorio_filtrado = df_cartorio.copy()

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
        # Criar 6 abas reorganizadas
        tab_visao_geral, tab_prod_etapas, tab_movimentacoes, tab_acomp_emissao, tab_qualidade, tab_visao_anterior = st.tabs([
            "📊 Visão Geral",
            "⏱️ Produtividade por Etapas",
            "🔄 Movimentações",
            "📈 Acompanhamento Emissão",
            "🔍 Qualidade dos Dados",
            "📑 Visão Anterior"
        ])

        # Aba 1: Visão Geral
        with tab_visao_geral:
            st.markdown("<h2 class='tab-title'>Visão Geral dos Dados</h2>", unsafe_allow_html=True)
            st.caption("Tabela com os dados brutos filtrados dos cartórios selecionados.")
            visualizar_cartorio_dados(df_cartorio_filtrado)
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
                            file_name=f"acompanhamento_emissao_familia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
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
                            file_name=f"analise_higienizacao_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
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
                            file_name=f"verificacao_ids_familia_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
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
                            label="📥 Exportar Negócios Ausentes (CSV)",
                            data=csv_ausentes,
                            file_name=f"negocios_familias_nao_cadastradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            key="export_ausentes"
                        )
                    elif df_ausentes is not None and total_ausentes == 0:
                        st.success("✅ Confronto realizado! Todos os negócios da categoria 32 possuem famílias cadastradas.")
                    else:
                         st.error("Erro ao realizar a análise de confronto. Verifique os logs.")
                else:
                    st.info("Clique no botão acima para executar a análise de confronto.")


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
    st.caption(f"Painel Cartório | Dados atualizados em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}") 