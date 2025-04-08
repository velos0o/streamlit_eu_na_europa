import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import json
from io import StringIO

# Carregar variáveis de ambiente
load_dotenv()

def carregar_dados_planilha():
    """
    Carrega os dados da planilha do Google "Emissões Cartão"
    
    Returns:
        pandas.DataFrame: DataFrame com os dados da planilha
    """
    try:
        # ID da planilha a partir da URL
        planilha_id = "1x_LOEGoL4LHHdbCH6OETSTPeHtf24WFLmFTv7_zXPNY"
        
        # URL para exportar a planilha como CSV
        csv_url = f"https://docs.google.com/spreadsheets/d/{planilha_id}/export?format=csv"
        
        st.info("Tentando acessar a planilha...")
        
        # Fazer requisição HTTP para obter os dados
        response = requests.get(csv_url)
        
        if response.status_code != 200:
            st.error(f"Erro ao acessar a planilha (código {response.status_code})")
            st.error("""
            ### A planilha não está acessível! Siga estes passos:
            
            1. Abra a planilha: [Certidões Carrão](https://docs.google.com/spreadsheets/d/1x_LOEGoL4LHHdbCH6OETSTPeHtf24WFLmFTv7_zXPNY/)
            2. Clique no botão "Compartilhar" no canto superior direito
            3. Clique em "Geral" e selecione "Qualquer pessoa com o link"
            4. Mude a configuração para "Qualquer pessoa na internet com este link pode visualizar"
            5. Clique em "Concluído"
            6. Tente novamente clicar em "Atualizar Dados"
            """)
            return pd.DataFrame()
        
        # Converter CSV para DataFrame
        df = pd.read_csv(StringIO(response.content.decode('utf-8')))
        
        # Verificar se o DataFrame não está vazio
        if df.empty:
            st.warning("A planilha foi acessada, mas não contém dados. Verifique se existe conteúdo na planilha.")
            return pd.DataFrame()
        
        # Renomear colunas para formato padrão
        colunas_mapeadas = {
            'ADM RESPONSAVEL': 'ADM_RESPONSAVEL',
            'NOME DA FAMILIA': 'NOME_FAMILIA',
            'NOME DO REQUERENTE': 'NOME_REQUERENTE',
            'CARTÓRIO': 'CARTORIO',
            'TIPO CERTIDÃO': 'TIPO_CERTIDAO',
            'LIVRO': 'LIVRO',
            'FOLHA': 'FOLHA',
            'TERMO': 'TERMO',
            'STATUS EMPRESA': 'STATUS_EMPRESA',
            'DATA DE SOLICITAÇÃO': 'DATA_SOLICITACAO',
            'DATA DE ENTREGA OU ATUALIZAÇÃO DO CARTÓRIO': 'DATA_ENTREGA_ATUALIZACAO',
            'STATUS CARTÓRIOS': 'STATUS_CARTORIOS',
            'OBS - CARTÓRIO': 'OBS_CARTORIO',
            'OBS - EMPRESA': 'OBS_EMPRESA',
            'STATUS DA EMISSÃO': 'STATUS_EMISSAO',
            'OBSERVAÇÃO': 'OBSERVACAO'
        }
        
        # Aplicar o mapeamento de colunas caso necessário
        colunas_renomeadas = {}
        for coluna_original, coluna_nova in colunas_mapeadas.items():
            if coluna_original in df.columns:
                colunas_renomeadas[coluna_original] = coluna_nova
        
        if colunas_renomeadas:
            df = df.rename(columns=colunas_renomeadas)
        
        # Converter colunas de data
        for coluna in ['DATA_SOLICITACAO', 'DATA_ENTREGA_ATUALIZACAO']:
            if coluna in df.columns:
                df[coluna] = pd.to_datetime(df[coluna], errors='coerce')
        
        # Preencher valores nulos em campos de texto com string vazia
        colunas_texto = ['ADM_RESPONSAVEL', 'NOME_FAMILIA', 'NOME_REQUERENTE', 'CARTORIO', 
                        'TIPO_CERTIDAO', 'STATUS_EMPRESA', 'STATUS_CARTORIOS', 
                        'OBS_CARTORIO', 'OBS_EMPRESA', 'STATUS_EMISSAO', 'OBSERVACAO']
        
        for coluna in colunas_texto:
            if coluna in df.columns:
                df[coluna] = df[coluna].fillna('')
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha: {str(e)}")
        st.error("""
        Erro ao acessar a planilha. Verifique:
        1. Sua conexão com a internet
        2. Se a planilha está compartilhada publicamente com opção "Qualquer pessoa com o link"
        3. Se a planilha existe e está acessível
        """)
        return pd.DataFrame()

def calcular_metricas_emissao(df):
    """
    Calcula métricas gerais sobre as emissões
    
    Args:
        df: DataFrame com os dados de emissões
    
    Returns:
        dict: Dicionário com as métricas calculadas
    """
    if df.empty:
        return {
            'total_familias': 0,
            'total_requerentes': 0,
            'total_certidoes': 0,
            'status_emissao': {},
            'status_cartorio': {},
            'status_empresa': {},
            'adm_responsaveis': {}
        }
    
    # Famílias únicas
    familias_unicas = df['NOME_FAMILIA'].unique()
    total_familias = len(familias_unicas)
    
    # Requerentes únicos
    requerentes_unicos = df['NOME_REQUERENTE'].unique()
    total_requerentes = len(requerentes_unicos)
    
    # Total de certidões (cada linha representa uma certidão)
    total_certidoes = len(df)
    
    # Contagens por status
    status_emissao = df['STATUS_EMISSAO'].value_counts().to_dict()
    status_cartorio = df['STATUS_CARTORIOS'].value_counts().to_dict()
    status_empresa = df['STATUS_EMPRESA'].value_counts().to_dict()
    
    # Contagem por ADM responsável
    adm_responsaveis = df['ADM_RESPONSAVEL'].value_counts().to_dict()
    
    return {
        'total_familias': total_familias,
        'total_requerentes': total_requerentes,
        'total_certidoes': total_certidoes,
        'status_emissao': status_emissao,
        'status_cartorio': status_cartorio,
        'status_empresa': status_empresa,
        'adm_responsaveis': adm_responsaveis
    }

def criar_resumo_por_familia(df):
    """
    Cria um resumo dos dados agrupados por família
    
    Args:
        df: DataFrame com os dados de emissões
    
    Returns:
        pandas.DataFrame: DataFrame com o resumo por família
    """
    if df.empty:
        return pd.DataFrame()
    
    # Agrupar por família
    resumo_familia = df.groupby('NOME_FAMILIA').agg(
        ADM_RESPONSAVEL=('ADM_RESPONSAVEL', 'first'),
        Total_Requerentes=('NOME_REQUERENTE', 'nunique'),
        Total_Certidoes=('TIPO_CERTIDAO', 'count'),
        Status_Emissao=('STATUS_EMISSAO', lambda x: x.value_counts().to_dict()),
        Status_Cartorio=('STATUS_CARTORIOS', lambda x: x.value_counts().to_dict()),
        Status_Empresa=('STATUS_EMPRESA', lambda x: x.value_counts().to_dict()),
        Ultima_Atualizacao=('DATA_ENTREGA_ATUALIZACAO', 'max')
    ).reset_index()
    
    # Calcular percentuais de conclusão
    def calcular_percentual_concluido(status_dict):
        if not status_dict:
            return 0
        
        total = sum(status_dict.values())
        if total == 0:
            return 0
        
        # Considerar como concluídos os status "Concluído", "Entregue", etc.
        # Esta lista deve ser adaptada conforme os status reais da planilha
        status_concluidos = ['Concluído', 'Entregue', 'Finalizado', 'Pronto para retirada']
        
        concluidos = sum(status_dict.get(status, 0) for status in status_concluidos)
        return round((concluidos / total) * 100, 1)
    
    # Aplicar cálculo de percentual
    resumo_familia['Percentual_Concluido'] = resumo_familia['Status_Emissao'].apply(calcular_percentual_concluido)
    
    # Converter dicionários para string para exibição
    resumo_familia['Status_Emissao_Texto'] = resumo_familia['Status_Emissao'].apply(
        lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()])
    )
    
    resumo_familia['Status_Cartorio_Texto'] = resumo_familia['Status_Cartorio'].apply(
        lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()])
    )
    
    resumo_familia['Status_Empresa_Texto'] = resumo_familia['Status_Empresa'].apply(
        lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()])
    )
    
    return resumo_familia

def criar_resumo_por_requerente(df):
    """
    Cria um resumo dos dados agrupados por requerente
    
    Args:
        df: DataFrame com os dados de emissões
    
    Returns:
        pandas.DataFrame: DataFrame com o resumo por requerente
    """
    if df.empty:
        return pd.DataFrame()
    
    # Agrupar por requerente
    resumo_requerente = df.groupby(['NOME_FAMILIA', 'NOME_REQUERENTE']).agg(
        ADM_RESPONSAVEL=('ADM_RESPONSAVEL', 'first'),
        Total_Certidoes=('TIPO_CERTIDAO', 'count'),
        Status_Emissao=('STATUS_EMISSAO', lambda x: x.value_counts().to_dict()),
        Status_Cartorio=('STATUS_CARTORIOS', lambda x: x.value_counts().to_dict()),
        Status_Empresa=('STATUS_EMPRESA', lambda x: x.value_counts().to_dict()),
        Ultima_Atualizacao=('DATA_ENTREGA_ATUALIZACAO', 'max')
    ).reset_index()
    
    # Calcular percentuais de conclusão
    def calcular_percentual_concluido(status_dict):
        if not status_dict:
            return 0
        
        total = sum(status_dict.values())
        if total == 0:
            return 0
        
        # Considerar como concluídos os status "Concluído", "Entregue", etc.
        status_concluidos = ['Concluído', 'Entregue', 'Finalizado', 'Pronto para retirada']
        
        concluidos = sum(status_dict.get(status, 0) for status in status_concluidos)
        return round((concluidos / total) * 100, 1)
    
    # Aplicar cálculo de percentual
    resumo_requerente['Percentual_Concluido'] = resumo_requerente['Status_Emissao'].apply(calcular_percentual_concluido)
    
    # Converter dicionários para string para exibição
    resumo_requerente['Status_Emissao_Texto'] = resumo_requerente['Status_Emissao'].apply(
        lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()])
    )
    
    resumo_requerente['Status_Cartorio_Texto'] = resumo_requerente['Status_Cartorio'].apply(
        lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()])
    )
    
    resumo_requerente['Status_Empresa_Texto'] = resumo_requerente['Status_Empresa'].apply(
        lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()])
    )
    
    # Ordenar por família e requerente
    resumo_requerente = resumo_requerente.sort_values(['NOME_FAMILIA', 'NOME_REQUERENTE'])
    
    return resumo_requerente

def criar_graficos_resumo(df, metricas):
    """
    Cria gráficos de resumo com base nos dados
    
    Args:
        df: DataFrame com os dados de emissões
        metricas: Dicionário com métricas calculadas
    """
    if df.empty:
        st.warning("Sem dados disponíveis para gerar gráficos.")
        return
    
    # Layout de colunas
    col1, col2 = st.columns(2)
    
    # Gráfico 1: Status da Emissão
    with col1:
        if metricas['status_emissao']:
            # Preparar dados para o gráfico
            status_df = pd.DataFrame({
                'Status': list(metricas['status_emissao'].keys()),
                'Quantidade': list(metricas['status_emissao'].values())
            })
            
            # Criar o gráfico
            fig_status = px.pie(
                status_df, 
                values='Quantidade', 
                names='Status',
                title='Distribuição por Status da Emissão',
                hole=0.4,  # Para criar um gráfico de donut
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            # Ajustar layout
            fig_status.update_layout(
                margin=dict(t=50, b=0, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig_status, use_container_width=True)
    
    # Gráfico 2: Status dos Cartórios
    with col2:
        if metricas['status_cartorio']:
            # Preparar dados para o gráfico
            status_df = pd.DataFrame({
                'Status': list(metricas['status_cartorio'].keys()),
                'Quantidade': list(metricas['status_cartorio'].values())
            })
            
            # Criar o gráfico
            fig_cartorio = px.pie(
                status_df, 
                values='Quantidade', 
                names='Status',
                title='Distribuição por Status do Cartório',
                hole=0.4,  # Para criar um gráfico de donut
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            
            # Ajustar layout
            fig_cartorio.update_layout(
                margin=dict(t=50, b=0, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig_cartorio, use_container_width=True)
    
    # Gráfico 3: Responsáveis ADM (Barras horizontais)
    if metricas['adm_responsaveis']:
        # Preparar dados para o gráfico
        adm_df = pd.DataFrame({
            'Responsável': list(metricas['adm_responsaveis'].keys()),
            'Quantidade': list(metricas['adm_responsaveis'].values())
        }).sort_values('Quantidade', ascending=False)
        
        # Criar o gráfico
        fig_adm = px.bar(
            adm_df,
            x='Quantidade',
            y='Responsável',
            orientation='h',
            title='Distribuição por Responsável ADM',
            color='Quantidade',
            color_continuous_scale='Viridis'
        )
        
        # Ajustar layout
        fig_adm.update_layout(
            margin=dict(t=50, b=0, l=0, r=0),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_adm, use_container_width=True)

def exibir_dashboard_emissoes_cartao():
    """
    Exibe o dashboard completo de Emissões Cartão
    """
    # Título e descrição
    st.markdown("<h2 class='tab-title'>Certidões Carrão</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #E8EAF6; padding: 18px; border-radius: 8px; margin-bottom: 20px;
    border-left: 5px solid #3F51B5; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <p style="margin: 0; font-size: 1rem; color: #283593;">
            Acompanhamento das certidões do Carrão por família e requerente.
        </p>
        <p style="margin-top: 12px; font-size: 0.9rem; color: #455A64;">
            <strong>Fonte:</strong> Planilha do Google - Certidões Carrão
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados automaticamente na primeira vez ou se o botão for clicado
    if 'df_emissoes' not in st.session_state or st.session_state.get('dados_atualizados', False):
        with st.spinner("Carregando dados da planilha..."):
            st.session_state['df_emissoes'] = carregar_dados_planilha()
            if 'dados_atualizados' in st.session_state:
                del st.session_state['dados_atualizados']
    
    # Mostrar botão para atualizar dados
    col_botao, col_info = st.columns([1, 3])
    with col_botao:
        if st.button("🔄 Atualizar Dados", type="primary", key="carregar_emissoes"):
            st.session_state['dados_atualizados'] = True
            st.rerun()  # Força o recarregamento da página
    with col_info:
        st.caption("Os dados são carregados automaticamente. Clique no botão para atualizar.")
    
    # Verificar se temos dados para mostrar
    if 'df_emissoes' in st.session_state and not st.session_state['df_emissoes'].empty:
        df = st.session_state['df_emissoes']
        
        # Mostrar info de dados carregados
        st.success(f"Dados carregados com sucesso: {len(df)} certidões encontradas.")
        
        # Adicionar filtros
        st.markdown("### Filtros")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro de Responsável ADM
            responsaveis = ['Todos'] + sorted(df['ADM_RESPONSAVEL'].unique().tolist())
            resp_selecionado = st.selectbox("Responsável ADM:", responsaveis, key="filtro_adm")
        
        with col2:
            # Filtro de Família
            familias = ['Todas'] + sorted(df['NOME_FAMILIA'].unique().tolist())
            familia_selecionada = st.selectbox("Família:", familias, key="filtro_familia")
        
        with col3:
            # Filtro de Status da Emissão
            status_emissoes = ['Todos'] + sorted(df['STATUS_EMISSAO'].unique().tolist())
            status_selecionado = st.selectbox("Status da Emissão:", status_emissoes, key="filtro_status")
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if resp_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['ADM_RESPONSAVEL'] == resp_selecionado]
        
        if familia_selecionada != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['NOME_FAMILIA'] == familia_selecionada]
        
        if status_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['STATUS_EMISSAO'] == status_selecionado]
        
        # Calcular métricas com base nos dados filtrados
        metricas = calcular_metricas_emissao(df_filtrado)
        
        # Mostrar métricas
        st.markdown("### Métricas Gerais")
        
        # Cards para métricas principais
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(f"""
            <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: 110px; display: flex; flex-direction: column; justify-content: center;">
                <h2 style="margin:0; color: #1565C0; font-size: 2rem;">{metricas['total_familias']}</h2>
                <p style="margin:0; color: #1976D2; font-weight: bold; font-size: 0.9rem;">Famílias</p>
            </div>
            """, unsafe_allow_html=True)
        
        with m_col2:
            st.markdown(f"""
            <div style="background-color: #E8F5E9; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: 110px; display: flex; flex-direction: column; justify-content: center;">
                <h2 style="margin:0; color: #2E7D32; font-size: 2rem;">{metricas['total_requerentes']}</h2>
                <p style="margin:0; color: #388E3C; font-weight: bold; font-size: 0.9rem;">Requerentes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with m_col3:
            st.markdown(f"""
            <div style="background-color: #FFF8E1; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: 110px; display: flex; flex-direction: column; justify-content: center;">
                <h2 style="margin:0; color: #FF8F00; font-size: 2rem;">{metricas['total_certidoes']}</h2>
                <p style="margin:0; color: #FFA000; font-weight: bold; font-size: 0.9rem;">Certidões</p>
            </div>
            """, unsafe_allow_html=True)
        
        with m_col4:
            # Calcular percentual de certidões concluídas
            status_concluidos = ['Concluído', 'Entregue', 'Finalizado', 'Pronto para retirada']
            total_concluidas = sum(metricas['status_emissao'].get(status, 0) for status in status_concluidos)
            perc_concluidas = (total_concluidas / metricas['total_certidoes'] * 100) if metricas['total_certidoes'] > 0 else 0
            
            st.markdown(f"""
            <div style="background-color: #FFEBEE; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: 110px; display: flex; flex-direction: column; justify-content: center;">
                <h2 style="margin:0; color: #C62828; font-size: 2rem;">{perc_concluidas:.1f}%</h2>
                <p style="margin:0; color: #D32F2F; font-weight: bold; font-size: 0.9rem;">Percentual Concluído</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Adicionar gráficos de resumo
        st.markdown("### Distribuição por Status")
        criar_graficos_resumo(df_filtrado, metricas)
        
        # Criar abas para visualização por família e por requerente
        st.markdown("### Análise Detalhada")
        tab_familia, tab_requerente, tab_dados_brutos = st.tabs([
            "📋 Por Família", 
            "👤 Por Requerente", 
            "📊 Dados Brutos"
        ])
        
        # Aba: Por Família
        with tab_familia:
            resumo_familia = criar_resumo_por_familia(df_filtrado)
            
            if not resumo_familia.empty:
                st.dataframe(
                    resumo_familia[[
                        'NOME_FAMILIA', 'ADM_RESPONSAVEL', 'Total_Requerentes', 
                        'Total_Certidoes', 'Percentual_Concluido', 
                        'Status_Emissao_Texto', 'Status_Cartorio_Texto', 
                        'Ultima_Atualizacao'
                    ]],
                    column_config={
                        "NOME_FAMILIA": st.column_config.TextColumn("Nome da Família", width="large"),
                        "ADM_RESPONSAVEL": st.column_config.TextColumn("Responsável ADM", width="medium"),
                        "Total_Requerentes": st.column_config.NumberColumn("Requerentes", format="%d", width="small"),
                        "Total_Certidoes": st.column_config.NumberColumn("Certidões", format="%d", width="small"),
                        "Percentual_Concluido": st.column_config.ProgressColumn("% Concluído", min_value=0, max_value=100, format="%.1f%%"),
                        "Status_Emissao_Texto": st.column_config.TextColumn("Status Emissão", width="large"),
                        "Status_Cartorio_Texto": st.column_config.TextColumn("Status Cartório", width="large"),
                        "Ultima_Atualizacao": st.column_config.DatetimeColumn("Última Atualização", format="DD/MM/YYYY")
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Botão para download
                csv_familia = resumo_familia.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar para CSV",
                    data=csv_familia,
                    file_name=f"emissoes_cartao_familia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    help="Baixar os dados detalhados em formato CSV"
                )
            else:
                st.info("Nenhum dado encontrado com os filtros aplicados.")
        
        # Aba: Por Requerente
        with tab_requerente:
            resumo_requerente = criar_resumo_por_requerente(df_filtrado)
            
            if not resumo_requerente.empty:
                st.dataframe(
                    resumo_requerente[[
                        'NOME_FAMILIA', 'NOME_REQUERENTE', 'ADM_RESPONSAVEL',
                        'Total_Certidoes', 'Percentual_Concluido', 
                        'Status_Emissao_Texto', 'Status_Cartorio_Texto', 
                        'Ultima_Atualizacao'
                    ]],
                    column_config={
                        "NOME_FAMILIA": st.column_config.TextColumn("Nome da Família", width="large"),
                        "NOME_REQUERENTE": st.column_config.TextColumn("Nome do Requerente", width="large"),
                        "ADM_RESPONSAVEL": st.column_config.TextColumn("Responsável ADM", width="medium"),
                        "Total_Certidoes": st.column_config.NumberColumn("Certidões", format="%d", width="small"),
                        "Percentual_Concluido": st.column_config.ProgressColumn("% Concluído", min_value=0, max_value=100, format="%.1f%%"),
                        "Status_Emissao_Texto": st.column_config.TextColumn("Status Emissão", width="large"),
                        "Status_Cartorio_Texto": st.column_config.TextColumn("Status Cartório", width="large"),
                        "Ultima_Atualizacao": st.column_config.DatetimeColumn("Última Atualização", format="DD/MM/YYYY")
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Botão para download
                csv_requerente = resumo_requerente.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar para CSV",
                    data=csv_requerente,
                    file_name=f"emissoes_cartao_requerente_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    help="Baixar os dados detalhados em formato CSV"
                )
            else:
                st.info("Nenhum dado encontrado com os filtros aplicados.")
        
        # Aba: Dados Brutos
        with tab_dados_brutos:
            st.markdown("#### Dados Brutos das Emissões")
            st.caption("Tabela com os dados brutos filtrados.")
            
            st.dataframe(
                df_filtrado,
                use_container_width=True,
                hide_index=True
            )
            
            # Botão para download
            csv_brutos = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar para CSV",
                data=csv_brutos,
                file_name=f"emissoes_cartao_dados_brutos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Baixar os dados brutos em formato CSV"
            )
    else:
        # Caso não tenha dados ou seja a primeira vez
        if 'df_emissoes' in st.session_state and st.session_state['df_emissoes'].empty:
            st.warning("Não foi possível carregar dados da planilha. Verifique a conexão ou as credenciais.")
        else:
            st.info("Clique no botão 'Atualizar Dados' para iniciar.")
    
    # Rodapé informativo
    st.divider()
    st.caption("Fonte de dados: Planilha do Google - Certidões Carrão | Atualizado em: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

# Para teste direto deste arquivo
if __name__ == "__main__":
    exibir_dashboard_emissoes_cartao() 