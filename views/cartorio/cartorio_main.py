import streamlit as st
from .data_loader import carregar_dados_cartorio
from .analysis import criar_visao_geral_cartorio, analyze_cartorio_ids, analisar_familias_ausentes, analisar_familia_certidoes, analisar_acompanhamento_emissao_familia
from .visualization import visualizar_cartorio_dados, visualizar_grafico_cartorio
from .movimentacoes import analisar_produtividade
from .produtividade import analisar_produtividade_etapas
import pandas as pd
import io
from datetime import datetime

def show_cartorio():
    """
    Exibe a página principal do Cartório
    """
    # Título centralizado
    st.markdown("""
    <h1 style="font-size: 2.8rem; font-weight: 900; color: #1A237E; text-align: center; 
    margin-bottom: 1.5rem; padding-bottom: 10px; border-bottom: 4px solid #1976D2;
    font-family: Arial, Helvetica, sans-serif;">
    <strong>FUNIL DE EMISSÕES BITRIX</strong></h1>
    """, unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px; color: #555; font-family: Arial, Helvetica, sans-serif;'>Monitoramento completo do processo de emissão de documentos nos cartórios.</p>", unsafe_allow_html=True)
    
    # Carregar os dados dos cartórios
    df_cartorio = carregar_dados_cartorio()
    
    if df_cartorio.empty:
        st.warning("Não foi possível carregar os dados dos cartórios. Verifique a conexão com o Bitrix24.")
        return
    else:
        st.success(f"Dados carregados com sucesso: {len(df_cartorio)} registros encontrados.")
    
    # Adicionar filtro de cartório
    cartorio_filter = st.multiselect(
        "Filtrar por Cartório:",
        ["CARTÓRIO CASA VERDE", "CARTÓRIO TATUÁPE"],
        default=["CARTÓRIO CASA VERDE", "CARTÓRIO TATUÁPE"]
    )
    
    # Aplicar filtro de cartório aos dados
    if cartorio_filter and not df_cartorio.empty:
        df_cartorio = df_cartorio[df_cartorio['NOME_CARTORIO'].isin(cartorio_filter)]
        st.info(f"Filtrando para mostrar apenas: {', '.join(cartorio_filter)}")
    
    # Adicionar CSS para aumentar o contraste das abas
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab"] {
        font-weight: 900 !important;
        color: #1A237E !important;
        height: 60px !important;
        padding: 10px 20px !important;
        font-size: 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-right: 5px !important;
        border-radius: 8px 8px 0 0 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1976D2 !important;
        color: white !important;
        font-weight: 900 !important;
        border-bottom: 4px solid #FF9800 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        margin-bottom: 20px !important;
        gap: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Mostrar todas as informações relevantes em uma única página
    if not df_cartorio.empty:
        # Criar abas para organizar o conteúdo
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "Dados Detalhados", 
            "Visão Geral", 
            "Análise de Famílias", 
            "IDs de Família",
            "Análises Famílias",
            "Movimentações",
            "Acompanhamento de Emissão família",
            "Produtividade"
        ])
        
        # Aba 1: Dados Detalhados dos Cartórios
        with tab1:
            # 1. Dados Detalhados (Movido para o topo)
            visualizar_cartorio_dados(df_cartorio)
            
            # Gráfico de distribuição por cartório
            # visualizar_grafico_cartorio(df_cartorio)
        
        # Aba 2: Visão Geral dos Cartórios
        with tab2:
            # 2. Visão Geral
            st.header("Visão Geral dos Cartórios")
            visao_geral = criar_visao_geral_cartorio(df_cartorio)
            if not visao_geral.empty:
                st.dataframe(visao_geral, use_container_width=True)
            else:
                st.info("Não foi possível criar a visão geral. Verifique se os dados estão corretos.")
        
        # Aba 3: Análise de Famílias Ausentes no Cadastro
        with tab3:
            # 3. Análise de Famílias Ausentes no Cadastro
            st.header("Negócios com Famílias não Cadastradas (Categoria 32)")
            
            # Explicação do processo
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <p style="margin: 0;">Esta análise compara os negócios da categoria 32 com o cadastro de famílias para identificar quais
                negócios possuem IDs de família que não estão cadastrados no sistema.</p>
                <p style="margin-top: 10px; font-size: 14px; color: #666;">
                    <strong>Nota:</strong> O processo pode levar alguns instantes, dependendo da quantidade de dados.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão para iniciar a análise
            if st.button("Iniciar Análise"):
                # Executar análise sem spinner (já temos progressbar interno)
                total_ausentes, df_ausentes = analisar_familias_ausentes()
                
                if total_ausentes > 0:
                    # Exibir métrica em destaque
                    st.markdown(f"""
                    <div style="background-color: #ffe4e4; padding: 15px; border-radius: 10px; border-left: 5px solid #e53935; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3 style="margin-top: 0; color: #c62828; font-size: 16px;">Negócios com Famílias não Cadastradas</h3>
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{total_ausentes}</p>
                        <p style="margin-top: 10px; font-size: 14px;">
                            Negócios da categoria 32 cujas famílias (UF_CRM_1722605592778) não estão cadastradas no sistema (UF_CRM_12_1723552666).
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Exibir tabela com os detalhes
                    st.subheader("Detalhes dos Negócios Afetados")
                    st.dataframe(
                        df_ausentes, 
                        use_container_width=True,
                        column_config={
                            "ID do Negócio": st.column_config.NumberColumn("ID do Negócio", format="%d"),
                            "Nome do Negócio": "Nome do Negócio",
                            "Responsável": "Responsável",
                            "ID da Família": st.column_config.TextColumn("ID da Família")
                        }
                    )
                    
                    # Adicionar botão para exportar os dados
                    csv = df_ausentes.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Exportar dados para CSV",
                        data=csv,
                        file_name="negocios_familias_nao_cadastradas.csv",
                        mime="text/csv",
                    )
                elif total_ausentes == 0:
                    st.success("Não foram encontrados negócios com famílias não cadastradas na categoria 32. Todas as famílias estão devidamente registradas!")
            else:
                st.info("Clique no botão acima para iniciar a análise de negócios com famílias não cadastradas.")
        
        # Aba 4: Análise de IDs de Família
        with tab4:
            # 4. Análise de IDs de Família
            st.header("Análise de IDs de Família")
            family_id_summary, family_id_details = analyze_cartorio_ids(df_cartorio)
            
            if not family_id_summary.empty:
                # Exibir resumo em um expander
                with st.expander("Resumo de IDs de Família", expanded=True):
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
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Filtro de status do ID
                    selected_id_status = st.multiselect(
                        "Filtrar por Status do ID",
                        options=['Padrão Correto', 'Duplicado', 'Vazio', 'Formato Inválido'],
                        default=['Duplicado', 'Vazio', 'Formato Inválido'],
                        help="Selecione os status que deseja visualizar"
                    )
                
                with col2:
                    # Filtro de cartório
                    cartorios = sorted(family_id_details['Cartório'].unique())
                    cart_filter = st.multiselect(
                        "Filtrar por Cartório",
                        options=cartorios,
                        help="Selecione os cartórios que deseja visualizar"
                    )
                
                with col3:
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
                if cart_filter:
                    filtered_details = filtered_details[filtered_details['Cartório'].isin(cart_filter)]
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
                        "Cartório": st.column_config.TextColumn(
                            "Cartório",
                            width="medium",
                            help="Nome do cartório"
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
                            file_name=f"analise_ids_familia_cartorio_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.info("Nenhum registro encontrado com os filtros selecionados.")
            else:
                st.info("Não foi possível analisar os IDs de família. Campo não encontrado nos dados.")
        
        # Aba 5: Análises Famílias (Nova aba)
        with tab5:
            st.header("Análise Detalhada de Famílias")
            
            # Explicação do processo
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <p style="margin: 0;">Esta análise realiza o cruzamento de dados das famílias entre várias tabelas do Bitrix, 
                exibindo informações sobre responsáveis, certidões e status de higienização.</p>
                <p style="margin-top: 10px; font-size: 14px; color: #666;">
                    <strong>Nota:</strong> O processo pode levar alguns instantes devido à quantidade de dados analisados.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão para iniciar análise
            if st.button("Realizar Análise de Famílias"):
                # Executar análise 
                df_analise = analisar_familia_certidoes()
                
                if not df_analise.empty:
                    # Exibir a análise da família em formato de tabela
                    st.write("Análise de Famílias por Cartório e Responsável:")
                    
                    # Adicionar filtros para responsáveis e cartórios
                    col_resp, col_cart = st.columns(2)
                    
                    # Filtros
                    with col_resp:
                        responsaveis = ['Todos'] + sorted(df_analise['RESPONSAVEL_ADM'].dropna().unique().tolist())
                        resp_selecionado = st.selectbox("Filtrar por Responsável ADM:", responsaveis)
                        
                    with col_cart:
                        cartorios = ['Todos'] + sorted(df_analise['CARTORIO'].dropna().unique().tolist())
                        cart_selecionado = st.selectbox("Filtrar por Cartório:", cartorios)
                    
                    # Aplicar filtros
                    df_filtrado = df_analise.copy()
                    
                    if resp_selecionado != 'Todos':
                        df_filtrado = df_filtrado[df_filtrado['RESPONSAVEL_ADM'] == resp_selecionado]
                        
                    if cart_selecionado != 'Todos':
                        df_filtrado = df_filtrado[df_filtrado['CARTORIO'] == cart_selecionado]
                    
                    # Exibição de estatísticas gerais (métricas)
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total de Famílias", len(df_filtrado))
                        
                    with col2:
                        media_membros = df_filtrado['MEMBROS'].mean() if 'MEMBROS' in df_filtrado.columns else 0
                        st.metric("Média de Membros", f"{media_membros:.1f}")
                        
                    with col3:
                        total_certidoes = df_filtrado['TOTAL_CERTIDOES'].sum()
                        certidoes_entregues = df_filtrado['CERTIDOES_ENTREGUES'].sum()
                        taxa_entrega = (certidoes_entregues / total_certidoes * 100) if total_certidoes > 0 else 0
                        st.metric("Taxa de Entrega", f"{taxa_entrega:.1f}%")
                        
                    with col4:
                        total_requerentes = df_filtrado['TOTAL_REQUERENTES'].sum() if 'TOTAL_REQUERENTES' in df_filtrado.columns else 0
                        st.metric("Total de Requerentes", total_requerentes)
                    
                    # Exibir tabela com os dados
                    st.dataframe(
                        df_filtrado[[
                            'ID_FAMILIA', 
                            'NOME', 
                            'CARTORIO', 
                            'RESPONSAVEL_ADM', 
                            'RESPONSAVEL_VENDAS', 
                            'TOTAL_CERTIDOES', 
                            'CERTIDOES_ENTREGUES',
                            'MEMBROS',
                            'TOTAL_REQUERENTES',
                            'ID_REQUERENTE',
                            'STATUS_HIGILIZACAO'
                        ]],
                        use_container_width=True
                    )
                else:
                    st.error("Não foi possível realizar a análise. Verifique os logs para mais informações.")
            else:
                st.info("Clique no botão acima para iniciar a análise detalhada de famílias.")
        
        # Aba 6: Movimentações
        with tab6:
            # 6. Análise de Movimentações
            analisar_produtividade(df_cartorio)
        
        # Aba 7: Acompanhamento de Emissão família (Nova aba)
        with tab7:
            # Título e estilo personalizado
            st.markdown("""
            <h1 style="font-size: 2.2rem; font-weight: 800; color: #1A237E; text-align: center; 
            margin-bottom: 1.2rem; padding-bottom: 8px; border-bottom: 3px solid #1976D2;">
            <i class="material-icons" style="vertical-align: middle;">assessment</i>
            Acompanhamento de Emissão por Família</h1>
            """, unsafe_allow_html=True)
            
            # Explicação do processo com estilo aprimorado
            st.markdown("""
            <div style="background-color: #E8EAF6; padding: 18px; border-radius: 8px; margin-bottom: 20px; 
            border-left: 5px solid #3F51B5; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <p style="margin: 0; font-size: 16px; color: #283593;">Esta visão apresenta o acompanhamento de emissão de certidões por família, 
                mostrando o percentual de conclusão das certidões solicitadas.</p>
                <p style="margin-top: 12px; font-size: 14px; color: #455A64;">
                    <strong>Nota:</strong> São consideradas concluídas as certidões que estão em etapas de Sucesso no fluxo do Bitrix.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Carregar dados automaticamente ao abrir a aba
            with st.spinner("Carregando dados de acompanhamento..."):
                df_acompanhamento = analisar_acompanhamento_emissao_familia()
            
            if not df_acompanhamento.empty:
                # Exibição de estatísticas gerais (métricas) com mais estilo
                st.markdown("<h3 style='color: #1A237E; margin-top: 30px;'>Resumo Geral</h3>", unsafe_allow_html=True)
                
                # Calcular estatísticas
                total_certidoes = df_acompanhamento['TOTAL_CERTIDOES'].sum()
                total_concluidas = df_acompanhamento['CERTIDOES_CONCLUIDAS'].sum()
                percentual_geral = (total_concluidas / total_certidoes * 100) if total_certidoes > 0 else 0
                
                # Métricas em cards com cores
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Card estilizado
                    st.markdown(f"""
                    <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h2 style="margin:0; color: #1565C0; font-size: 32px;">{len(df_acompanhamento)}</h2>
                        <p style="margin:0; color: #1976D2; font-weight: bold;">Total de Famílias</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col2:
                    st.markdown(f"""
                    <div style="background-color: #E8F5E9; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h2 style="margin:0; color: #2E7D32; font-size: 32px;">{total_certidoes}</h2>
                        <p style="margin:0; color: #388E3C; font-weight: bold;">Total de Certidões</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col3:
                    st.markdown(f"""
                    <div style="background-color: #FFF8E1; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h2 style="margin:0; color: #FF8F00; font-size: 32px;">{total_concluidas}</h2>
                        <p style="margin:0; color: #FFA000; font-weight: bold;">Certidões Concluídas</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col4:
                    st.markdown(f"""
                    <div style="background-color: #FFEBEE; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h2 style="margin:0; color: #C62828; font-size: 32px;">{percentual_geral:.1f}%</h2>
                        <p style="margin:0; color: #D32F2F; font-weight: bold;">Percentual Geral</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Separador visual
                st.markdown("<hr style='margin: 30px 0; border-color: #E0E0E0;'>", unsafe_allow_html=True)
                
                # Título da tabela com estilo
                st.markdown("<h3 style='color: #1A237E;'>Detalhamento por Família</h3>", unsafe_allow_html=True)
                
                # Preparar dataframe para exibição
                df_display = df_acompanhamento.copy()
                
                # Converter percentual para string formatado (para exibição)
                df_display['PERCENTUAL_TEXTO'] = df_display['PERCENTUAL_CONCLUSAO'].apply(lambda x: f"{x:.1f}%")
                
                # Exibir tabela com os dados - com apenas a barra de progresso
                st.dataframe(
                    df_display,
                    column_config={
                        "ID_FAMILIA": st.column_config.TextColumn(
                            "ID da Família", 
                            help="Identificador único da família",
                            width="medium"
                        ),
                        "NOME_FAMILIA": st.column_config.TextColumn(
                            "Nome da Família", 
                            help="Nome da família registrado no Bitrix",
                            width="large"
                        ),
                        "TOTAL_REQUERENTES": st.column_config.NumberColumn(
                            "Total de Requerentes", 
                            format="%d", 
                            help="Quantidade de requerentes únicos",
                            width="small"
                        ),
                        "TOTAL_CERTIDOES": st.column_config.NumberColumn(
                            "Total de Certidões", 
                            format="%d", 
                            help="Quantidade total de certidões solicitadas",
                            width="small"
                        ),
                        "CERTIDOES_CONCLUIDAS": st.column_config.NumberColumn(
                            "Certidões Concluídas", 
                            format="%d", 
                            help="Quantidade de certidões já concluídas",
                            width="small"
                        ),
                        "PERCENTUAL_TEXTO": st.column_config.TextColumn(
                            "Percentual", 
                            help="Percentual de certidões concluídas",
                            width="small"
                        ),
                        "PERCENTUAL_CONCLUSAO": st.column_config.ProgressColumn(
                            "% Conclusão", 
                            min_value=0, 
                            max_value=100,
                            format=None, # Removendo o formato para exibir apenas a barra
                            help="Progresso visual de certidões concluídas"
                        )
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Adicionar botão para atualizar os dados
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("🔄 Atualizar Dados", key="atualizar_acomp", type="primary"):
                        st.rerun()
                
                # Adicionar botão para exportar os dados com estilo
                with col2:
                    csv = df_acompanhamento.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Exportar dados para CSV",
                        data=csv,
                        file_name=f"acompanhamento_emissao_familia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        help="Clique para baixar os dados em formato CSV"
                    )
                
                # Mostrar informações sobre etapas de sucesso
                with st.expander("Etapas consideradas como Sucesso", expanded=False):
                    st.markdown("""
                    <div style="background-color: #F5F5F5; padding: 15px; border-radius: 6px;">
                        <h4 style="color: #1A237E; margin-top: 0;">Etapas que contam como certidões concluídas:</h4>
                        <ul style="margin-bottom: 0; padding-left: 20px;">
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
                # Mensagem de erro estilizada
                st.markdown("""
                <div style="background-color: #FFEBEE; padding: 15px; border-radius: 8px; margin-top: 20px; 
                border-left: 5px solid #C62828; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <p style="margin: 0; color: #B71C1C; font-weight: bold;">Erro ao carregar dados</p>
                    <p style="margin-top: 8px; color: #D32F2F;">
                        Não foi possível carregar os dados de acompanhamento. Verifique os logs para mais informações.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Botão para tentar novamente
                if st.button("🔄 Tentar Novamente", type="primary"):
                    st.rerun()
        
        # Aba 8: Produtividade por Etapas
        with tab8:
            # Título e estilo personalizado
            st.markdown("""
            <h1 style="font-size: 2.2rem; font-weight: 800; color: #1A237E; text-align: center; 
            margin-bottom: 1.2rem; padding-bottom: 8px; border-bottom: 3px solid #1976D2;">
            <i class="material-icons" style="vertical-align: middle;">speed</i>
            Análise de Produtividade por Etapas</h1>
            """, unsafe_allow_html=True)
            
            # Explicação do processo
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <p style="margin: 0;">Esta análise permite visualizar a produtividade baseada nas datas registradas em cada etapa do processo.
                Você pode analisar por dia, semana e mês, e filtrar por responsável.</p>
                <p style="margin-top: 10px; font-size: 14px; color: #666;">
                    <strong>Nota:</strong> Os dados analisados consideram os campos de data de cada etapa do processo.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Chamar a função de análise de produtividade por etapas
            analisar_produtividade_etapas(df_cartorio)
    else:
        st.info("Nenhum dado disponível para exibir.")
        
    # Rodapé com informação de atualização
    st.markdown("---")
    st.caption("Dados atualizados em tempo real do Bitrix24.") 