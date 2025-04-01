import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from api.bitrix_connector import load_bitrix_data, get_credentials
from datetime import datetime

# Dicionários de mapeamento de estágios
em_andamento = {
    'DT1052_16:NEW': 'Aguardando Certidão',
    'DT1052_34:NEW': 'Aguardando Certidão',
    'DT1052_16:UC_QRZ6JG': 'Busca CRC',
    'DT1052_34:UC_68BLQ7': 'Busca CRC',
    'DT1052_16:UC_7F0WK2': 'Apenas Ass. Req. Cliente P/ Montagem',
    'DT1052_34:UC_HN9GMI': 'Apenas Ass. Req. Cliente P/ Montagem',
    'DT1052_16:PREPARATION': 'Montagem Requerimento Cartório',
    'DT1052_34:PREPARATION': 'Montagem Requerimento Cartório',
    'DT1052_16:UC_IWZBMO': 'Solicitar Cart. Origem',
    'DT1052_34:CLIENT': 'Certidão Emitida',
    'DT1052_34:UC_8L5JUS': 'Solicitar Cart. Origem',
    'DT1052_16:UC_8EGMU7': 'Cart. Origem Prioridade',
    'DT1052_16:UC_KXHDOQ': 'Aguard. Cart. Origem',
    'DT1052_34:UC_6KOYL5': 'Aguard. Cart. Origem',
    'DT1052_16:CLIENT': 'Certidão Emitida',
    'DT1052_34:UC_D0RG5P': 'Certidão Emitida',
    'DT1052_16:UC_JRGCW3': 'Certidão Física',
    'DT1052_34:UC_84B1S2': 'Certidão Física',
    # Versões curtas dos nomes (sem prefixo)
    'NEW': 'Aguard. Certidão',
    'PREPARATION': 'Mont. Requerim.',
    'CLIENT': 'Certidão Emitida',
    'UC_QRZ6JG': 'Busca CRC',
    'UC_68BLQ7': 'Busca CRC',
    'UC_7F0WK2': 'Solic. Requerim.',
    'UC_HN9GMI': 'Solic. Requerim.',
    'UC_IWZBMO': 'Solic. C. Origem',
    'UC_8L5JUS': 'Solic. C. Origem',
    'UC_8EGMU7': 'C. Origem Prior.',
    'UC_KXHDOQ': 'Aguard. C. Origem',
    'UC_6KOYL5': 'Aguard. C. Origem',
    'UC_D0RG5P': 'Certidão Emitida',
    'UC_JRGCW3': 'Certidão Física',
    'UC_84B1S2': 'Certidão Física'
}

# SUCESSO
sucesso = {
    'DT1052_16:SUCCESS': 'Certidão Entregue',
    'DT1052_34:SUCCESS': 'Certidão Entregue',
    'SUCCESS': 'Certidão Entregue'
}

# FALHA
falha = {
    'DT1052_16:FAIL': 'Devolução ADM',
    'DT1052_34:FAIL': 'Devolução ADM',
    'DT1052_16:UC_R5UEXF': 'Dev. ADM Verificado',
    'DT1052_34:UC_Z3J98J': 'Dev. ADM Verificado',
    'DT1052_16:UC_HYO7L2': 'Devolutiva Busca',
    'DT1052_34:UC_5LAJNY': 'Devolutiva Busca',
    'DT1052_16:UC_UG0UDZ': 'Solicitação Duplicada',
    'DT1052_34:UC_LF04SU': 'Solicitação Duplicada',
    'DT1052_16:UC_P61ZVH': 'Devolvido Requerimento',
    'DT1052_34:UC_2BAINE': 'Devolvido Requerimento',
    # Versões curtas dos nomes (sem prefixo)
    'FAIL': 'Devolução ADM',
    'UC_R5UEXF': 'Dev. ADM Verif.',
    'UC_Z3J98J': 'Dev. ADM Verif.',
    'UC_HYO7L2': 'Dev. Busca',
    'UC_5LAJNY': 'Dev. Busca',
    'UC_UG0UDZ': 'Solic. Duplicada',
    'UC_LF04SU': 'Solic. Duplicada',
    'UC_P61ZVH': 'Dev. Requerim.',
    'UC_2BAINE': 'Dev. Requerim.'
}

def carregar_dados_protocolado():
    """
    Carregar dados necessários para análise de protocolados:
    1. crm_deal (category_id = 32)
    2. crm_dynamic_items_1052 (emissões - cartório)
    """
    # Obter token do Bitrix24
    BITRIX_TOKEN, BITRIX_URL = get_credentials()
    
    # URLs para acessar as tabelas
    url_deal = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal"
    url_deal_uf = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_deal_uf"
    url_cartorio = f"{BITRIX_URL}/bitrix/tools/biconnector/pbi.php?token={BITRIX_TOKEN}&table=crm_dynamic_items_1052"
    
    # Preparar filtro para a categoria 32
    category_filter = {"dimensionsFilters": [[]]}
    category_filter["dimensionsFilters"][0].append({
        "fieldName": "CATEGORY_ID", 
        "values": ["32"], 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    # Carregar dados principais dos negócios com filtro de categoria
    with st.spinner("Carregando dados de negócios (crm_deal)..."):
        df_deal = load_bitrix_data(url_deal, filters=category_filter)
        
        if df_deal.empty:
            st.error("Não foi possível carregar os dados de negócios. Verifique a conexão com o Bitrix24.")
            return None, None, None
        
        # Selecionar colunas necessárias
        df_deal = df_deal[['ID', 'TITLE', 'ASSIGNED_BY_NAME', 'STAGE_ID']]
    
    # Obter lista de IDs dos deals para filtrar a tabela crm_deal_uf
    deal_ids = df_deal['ID'].astype(str).tolist()
    
    # Filtro para crm_deal_uf baseado nos IDs dos deals da categoria 32
    deal_filter = {"dimensionsFilters": [[]]}
    deal_filter["dimensionsFilters"][0].append({
        "fieldName": "DEAL_ID", 
        "values": deal_ids, 
        "type": "INCLUDE", 
        "operator": "EQUALS"
    })
    
    # Carregar dados da tabela crm_deal_uf
    with st.spinner("Carregando dados de campos personalizados (crm_deal_uf)..."):
        df_deal_uf = load_bitrix_data(url_deal_uf, filters=deal_filter)
        
        if df_deal_uf.empty:
            st.error("Não foi possível carregar os campos personalizados. Verifique a conexão com o Bitrix24.")
            return None, None, None
    
    # Carregar dados de emissões (cartório)
    with st.spinner("Carregando dados de emissões (crm_dynamic_items_1052)..."):
        df_cartorio = load_bitrix_data(url_cartorio)
        
        if df_cartorio.empty:
            st.error("Não foi possível carregar os dados de emissões. Verifique a conexão com o Bitrix24.")
            return None, None, None
        
        # Filtrar apenas os cartórios Casa Verde (16) e Tatuápe (34)
        if 'CATEGORY_ID' in df_cartorio.columns:
            df_cartorio = df_cartorio[df_cartorio['CATEGORY_ID'].isin([16, 34])].copy()
            st.success(f"Dados filtrados: {len(df_cartorio)} registros de cartório (categoria 16 e 34)")
        else:
            st.warning("Campo CATEGORY_ID não encontrado em crm_dynamic_items_1052. Usando todos os registros.")
    
    # Exibir um resumo dos dados carregados
    st.success(f"""
    Dados carregados com sucesso:
    - Negócios (categoria 32): {len(df_deal)} registros
    - Campos personalizados: {len(df_deal_uf)} registros
    - Emissões de cartório: {len(df_cartorio)} registros
    """)
    
    return df_deal, df_deal_uf, df_cartorio

def processar_dados_protocolado(df_deal, df_deal_uf, df_cartorio):
    """
    Processar os dados carregados para análise de protocolados
    """
    # Verificar se temos todos os dataframes necessários
    if df_deal is None or df_deal_uf is None or df_cartorio is None:
        return None
    
    # Filtrar apenas os campos necessários em crm_deal_uf
    campos_deal_uf = ['DEAL_ID', 'UF_CRM_1722605592778', 'UF_CRM_1735661425423']
    
    # Verificar se os campos existem
    campos_existentes_deal_uf = [campo for campo in campos_deal_uf if campo in df_deal_uf.columns]
    if len(campos_existentes_deal_uf) < len(campos_deal_uf):
        campos_faltantes = set(campos_deal_uf) - set(campos_existentes_deal_uf)
        st.warning(f"Campos não encontrados em df_deal_uf: {campos_faltantes}")
    
    df_deal_uf_filtrado = df_deal_uf[campos_existentes_deal_uf]
    
    # Verificar se o campo de ID da família existe e não está vazio
    if 'UF_CRM_1722605592778' in df_deal_uf_filtrado.columns:
        df_deal_uf_filtrado = df_deal_uf_filtrado.dropna(subset=['UF_CRM_1722605592778'])
    else:
        st.error("Campo 'UF_CRM_1722605592778' (ID da Família) não encontrado em df_deal_uf")
        return None
    
    # Procurar campos na tabela de cartório
    # Primeiro vamos procurar o campo ID da família nas colunas disponíveis
    id_familia_cols = [col for col in df_cartorio.columns if '1723552666' in col]
    id_requerente_cols = [col for col in df_cartorio.columns if '1723552729' in col]
    nome_familia_cols = [col for col in df_cartorio.columns if '1722882763189' in col]
    
    # Se não encontramos os campos esperados, buscar pelos nomes completos
    if not id_familia_cols:
        if 'UF_CRM_12_1723552666' in df_cartorio.columns:
            id_familia_cols = ['UF_CRM_12_1723552666']
        else:
            # Buscar qualquer coluna com ID_FAMILIA ou similar no nome
            id_familia_cols = [col for col in df_cartorio.columns if 'ID_FAMILIA' in col.upper()]
    
    if not id_familia_cols:
        st.error("Não foi possível encontrar o campo ID da Família na tabela de cartório")
        return None
    
    # Usar o primeiro campo encontrado para cada tipo
    id_familia_col = id_familia_cols[0] if id_familia_cols else None
    id_requerente_col = id_requerente_cols[0] if id_requerente_cols else None
    nome_familia_col = nome_familia_cols[0] if nome_familia_cols else None
    
    # Remover registros sem ID da família
    df_cartorio_filtrado = df_cartorio.dropna(subset=[id_familia_col]) if id_familia_col else df_cartorio
    
    # Mesclar df_deal com df_deal_uf para obter o ID da família
    df_deal_merged = pd.merge(
        df_deal, 
        df_deal_uf_filtrado,
        left_on='ID',
        right_on='DEAL_ID',
        how='inner'
    )
    
    # Filtrar apenas os protocolados
    if 'UF_CRM_1735661425423' in df_deal_merged.columns:
        valores_filtro = ['PROTOCOLADOS COMPLETOS', 'PROTOCOLADOS INCOMPLETOS']
        df_protocolados = df_deal_merged[df_deal_merged['UF_CRM_1735661425423'].isin(valores_filtro)]
        st.success(f"Filtrados {len(df_protocolados)} negócios protocolados")
    else:
        st.warning("Campo 'UF_CRM_1735661425423' (Status Protocolado) não encontrado. Usando todos os registros.")
        df_protocolados = df_deal_merged
    
    # Verificar tipos de dados e converter se necessário
    familia_deal_col = 'UF_CRM_1722605592778'
    tipo_familia_deal = df_protocolados[familia_deal_col].dtype
    tipo_familia_cartorio = df_cartorio_filtrado[id_familia_col].dtype
    
    # Se os tipos forem diferentes, converter para string
    if tipo_familia_deal != tipo_familia_cartorio:
        df_protocolados[familia_deal_col] = df_protocolados[familia_deal_col].astype(str)
        df_cartorio_filtrado[id_familia_col] = df_cartorio_filtrado[id_familia_col].astype(str)
    
    # Cruzar dados dos protocolados com as emissões pelo ID da família
    df_resultado = pd.merge(
        df_protocolados,
        df_cartorio_filtrado,
        left_on=familia_deal_col,
        right_on=id_familia_col,
        how='inner'
    )
    
    # Se o resultado estiver vazio ou com poucos registros, pode ser um problema nos dados
    if df_resultado.empty:
        st.error("Não foi possível cruzar os dados. Não foram encontradas correspondências entre negócios protocolados e emissões.")
        return None
    else:
        st.success(f"""
        Cruzamento realizado com sucesso:
        - Negócios protocolados: {len(df_protocolados)}
        - Famílias únicas: {df_resultado[familia_deal_col].nunique()}
        - Total de registros: {len(df_resultado)}
        """)
    
    # Criar colunas para análise de status
    df_resultado['STATUS_CATEGORIA'] = df_resultado['STAGE_ID_y'].apply(
        lambda x: 'Sucesso' if x in sucesso else ('Em Andamento' if x in em_andamento else ('Falha' if x in falha else 'Desconhecido'))
    )
    
    # Mapear colunas para nomes padronizados
    colunas_renomeadas = {
        familia_deal_col: 'ID_FAMILIA',
        id_familia_col: 'ID_FAMILIA_EMISSAO',
        'STAGE_ID_x': 'STAGE_ID_DEAL',
        'STAGE_ID_y': 'STAGE_ID_EMISSAO'
    }
    
    # Adicionar campos de requerente e nome da família se disponíveis
    if id_requerente_col:
        colunas_renomeadas[id_requerente_col] = 'ID_REQUERENTE'
    
    if nome_familia_col:
        colunas_renomeadas[nome_familia_col] = 'NOME_FAMILIA'
    
    if 'UF_CRM_1735661425423' in df_resultado.columns:
        colunas_renomeadas['UF_CRM_1735661425423'] = 'STATUS_PROTOCOLADO'
    
    # Renomear colunas para melhor entendimento
    df_resultado = df_resultado.rename(columns=colunas_renomeadas)
    
    # Exibir resumo da distribuição de status
    with st.expander("Distribuição de status das emissões", expanded=False):
        status_count = df_resultado['STATUS_CATEGORIA'].value_counts()
        st.write(f"Concluídas (Sucesso): {status_count.get('Sucesso', 0)}")
        st.write(f"Em Andamento: {status_count.get('Em Andamento', 0)}")
        st.write(f"Com Falha: {status_count.get('Falha', 0)}")
        st.write(f"Desconhecido: {status_count.get('Desconhecido', 0)}")
    
    return df_resultado

def analisar_protocolados(df):
    """
    Realiza a análise consolidada dos protocolados
    """
    if df is None or df.empty:
        st.error("Não há dados suficientes para análise.")
        return
    
    # Análise por família
    df_analise_familia = df.groupby(['ID_FAMILIA', 'NOME_FAMILIA', 'STATUS_PROTOCOLADO']).agg(
        TOTAL_REQUERENTES=('ID_REQUERENTE', 'nunique') if 'ID_REQUERENTE' in df.columns else ('STATUS_CATEGORIA', 'size'),
        # Usar size() em vez de count('ID') para contar registros
        TOTAL_EMISSOES=('STATUS_CATEGORIA', 'size'),
        EMISSOES_CONCLUIDAS=('STATUS_CATEGORIA', lambda x: (x == 'Sucesso').sum()),
        EMISSOES_EM_ANDAMENTO=('STATUS_CATEGORIA', lambda x: (x == 'Em Andamento').sum()),
        EMISSOES_FALHA=('STATUS_CATEGORIA', lambda x: (x == 'Falha').sum())
    ).reset_index()
    
    # Calcular percentual de conclusão
    df_analise_familia['PERCENTUAL_CONCLUSAO'] = (df_analise_familia['EMISSOES_CONCLUIDAS'] / df_analise_familia['TOTAL_EMISSOES'] * 100).round(1)
    
    return df_analise_familia

def criar_visao_geral_protocolados(df_analise):
    """
    Cria a visão geral dos protocolados - resumos e gráficos
    """
    if df_analise is None or df_analise.empty:
        st.error("Não há dados suficientes para análise.")
        return
    
    # Resumo geral
    total_familias = df_analise['ID_FAMILIA'].nunique()
    total_requerentes = df_analise['TOTAL_REQUERENTES'].sum()
    total_emissoes = df_analise['TOTAL_EMISSOES'].sum()
    emissoes_concluidas = df_analise['EMISSOES_CONCLUIDAS'].sum()
    emissoes_andamento = df_analise['EMISSOES_EM_ANDAMENTO'].sum()
    emissoes_falha = df_analise['EMISSOES_FALHA'].sum()
    
    percentual_conclusao_geral = (emissoes_concluidas / total_emissoes * 100) if total_emissoes > 0 else 0
    
    # Destacar a métrica principal - Total de Protocolados
    st.markdown("""
    <div style="background-color: #EDE7F6; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #673AB7; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="text-align: center; margin: 0; color: #512DA8; font-size: 2.2rem;">
            Total de Protocolados no funil de Emissões: <span style="color: #D81B60;">{}</span>
        </h2>
    </div>
    """.format(total_familias), unsafe_allow_html=True)
    
    # Exibir métricas principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Famílias", f"{total_familias}")
        st.metric("Total de Requerentes", f"{total_requerentes}")
    
    with col2:
        st.metric("Total de Emissões", f"{total_emissoes}")
        st.metric("Emissões Concluídas", f"{emissoes_concluidas} ({percentual_conclusao_geral:.1f}%)")
    
    with col3:
        st.metric("Emissões em Andamento", f"{emissoes_andamento}")
        st.metric("Emissões com Falha", f"{emissoes_falha}")
    
    # Gráfico de progresso geral
    fig_progresso = go.Figure()
    
    # Adicionar barras para cada categoria
    fig_progresso.add_trace(go.Bar(
        y=['Progresso Geral'],
        x=[emissoes_concluidas],
        name='Concluídas',
        orientation='h',
        marker=dict(color='#4CAF50')
    ))
    
    fig_progresso.add_trace(go.Bar(
        y=['Progresso Geral'],
        x=[emissoes_andamento],
        name='Em Andamento',
        orientation='h',
        marker=dict(color='#FFC107')
    ))
    
    fig_progresso.add_trace(go.Bar(
        y=['Progresso Geral'],
        x=[emissoes_falha],
        name='Falha',
        orientation='h',
        marker=dict(color='#F44336')
    ))
    
    # Atualizar layout
    fig_progresso.update_layout(
        title='Progresso Geral das Emissões',
        barmode='stack',
        height=150,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(title='Quantidade de Emissões')
    )
    
    st.plotly_chart(fig_progresso, use_container_width=True)
    
    # Gráfico de pizza para o status das emissões
    fig_pizza = px.pie(
        names=['Concluídas', 'Em Andamento', 'Falha'],
        values=[emissoes_concluidas, emissoes_andamento, emissoes_falha],
        title='Distribuição de Status das Emissões',
        color_discrete_sequence=['#4CAF50', '#FFC107', '#F44336']
    )
    
    fig_pizza.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    st.plotly_chart(fig_pizza, use_container_width=True)
    
    # Visão das famílias que faltam concluir emissões
    familias_pendentes = df_analise[df_analise['PERCENTUAL_CONCLUSAO'] < 100].shape[0]
    familias_concluidas = df_analise[df_analise['PERCENTUAL_CONCLUSAO'] == 100].shape[0]
    
    st.subheader("Famílias com Emissões Pendentes")
    
    # Gráfico de barras para famílias pendentes vs concluídas
    fig_familias = go.Figure()
    fig_familias.add_trace(go.Bar(
        x=['Famílias com Emissões Pendentes', 'Famílias com Emissões Concluídas'],
        y=[familias_pendentes, familias_concluidas],
        marker_color=['#FF5722', '#4CAF50']
    ))
    
    fig_familias.update_layout(
        title='Status de Conclusão por Família',
        xaxis=dict(title=''),
        yaxis=dict(title='Quantidade de Famílias')
    )
    
    st.plotly_chart(fig_familias, use_container_width=True)

def mostrar_tabela_detalhada(df_analise):
    """
    Exibe tabela detalhada com as informações de cada família
    """
    if df_analise is None or df_analise.empty:
        st.error("Não há dados suficientes para análise.")
        return
    
    st.subheader("Tabela Detalhada por Família")
    
    # Filtros para a tabela
    col1, col2 = st.columns(2)
    with col1:
        status_filtro = st.multiselect(
            "Filtrar por Status Protocolado:",
            options=sorted(df_analise['STATUS_PROTOCOLADO'].unique()),
            default=sorted(df_analise['STATUS_PROTOCOLADO'].unique())
        )
    
    with col2:
        conclusao_filtro = st.slider(
            "Filtrar por % Mínimo de Conclusão:",
            min_value=0,
            max_value=100,
            value=0,
            step=5
        )
    
    # Aplicar filtros
    df_filtrado = df_analise.copy()
    if status_filtro:
        df_filtrado = df_filtrado[df_filtrado['STATUS_PROTOCOLADO'].isin(status_filtro)]
    
    df_filtrado = df_filtrado[df_filtrado['PERCENTUAL_CONCLUSAO'] >= conclusao_filtro]
    
    # Ordenar por ID da família
    df_filtrado = df_filtrado.sort_values('ID_FAMILIA')
    
    # Adicionar formatação para percentual
    df_filtrado['PERCENTUAL_FORMATADO'] = df_filtrado['PERCENTUAL_CONCLUSAO'].apply(lambda x: f"{x:.1f}%")
    
    # Exibir tabela com formatação
    st.dataframe(
        df_filtrado,
        column_config={
            "ID_FAMILIA": st.column_config.TextColumn("ID Família", width="medium"),
            "NOME_FAMILIA": st.column_config.TextColumn("Nome da Família", width="large"),
            "STATUS_PROTOCOLADO": st.column_config.TextColumn("Status Protocolado", width="medium"),
            "TOTAL_REQUERENTES": st.column_config.NumberColumn("Total Requerentes", format="%d", width="small"),
            "TOTAL_EMISSOES": st.column_config.NumberColumn("Total Emissões", format="%d", width="small"),
            "EMISSOES_CONCLUIDAS": st.column_config.NumberColumn("Concluídas", format="%d", width="small"),
            "EMISSOES_EM_ANDAMENTO": st.column_config.NumberColumn("Em Andamento", format="%d", width="small"),
            "EMISSOES_FALHA": st.column_config.NumberColumn("Falha", format="%d", width="small"),
            "PERCENTUAL_FORMATADO": st.column_config.TextColumn("% Conclusão", width="small"),
            "PERCENTUAL_CONCLUSAO": st.column_config.ProgressColumn("Progresso", min_value=0, max_value=100, format="")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Opção para download
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar para CSV",
        data=csv,
        file_name=f"status_protocolado_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

def exibir_dashboard_protocolado():
    """
    Função principal para exibir o dashboard de Status Protocolado
    """
    # Título e descrição
    st.markdown("""
    <h1 style="font-size: 2.5rem; font-weight: 700; color: #1A237E; text-align: center;
    margin-bottom: 1rem; padding-bottom: 8px; border-bottom: 3px solid #1976D2;
    font-family: Arial, Helvetica, sans-serif;">
    Status Protocolado Emissões Brasileiras</h1>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; font-size: 1rem; color: #555; font-family: Arial, Helvetica, sans-serif; margin-bottom: 1.5rem;'>Análise das famílias protocoladas e status das emissões.</p>", unsafe_allow_html=True)
    
    # Adicionar um expander com informações sobre a fonte dos dados
    with st.expander("ℹ️ Sobre a fonte de dados", expanded=False):
        st.markdown("""
        Esta análise utiliza dados das seguintes fontes do Bitrix24:
        - **crm_deal**: Negócios com categoria 32 (Administrativo)
        - **crm_dynamic_items_1052**: Emissões de cartório (categorias 16 e 34)
        
        **Campos importantes:**
        - `UF_CRM_1722605592778`: ID da Família nos negócios
        - `UF_CRM_1735661425423`: Status do Protocolo nos negócios
        - `UF_CRM_12_1723552666`: ID da Família nas emissões
        - `UF_CRM_12_1723552729`: ID do Requerente nas emissões
        - `UF_CRM_12_1722882763189`: Nome da Família nas emissões
        """)
    
    # Carregar dados com tratamento de erro mais amigável
    try:
        with st.spinner("Carregando dados do Bitrix24..."):
            df_deal, df_deal_uf, df_cartorio = carregar_dados_protocolado()
            
            if df_deal is None or df_deal_uf is None or df_cartorio is None:
                st.error("Não foi possível carregar todos os dados necessários para análise.")
                
                # Botões de ação
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🔄 Tentar Novamente", type="primary", key="retry_load"):
                        st.rerun()
                with col2:
                    if st.button("🧩 Ver Solução Alternativa", key="alt_solution"):
                        st.info("""
                        **Possíveis soluções:**
                        
                        1. Verificar se os campos personalizados estão disponíveis no Bitrix:
                           - Acessar a administração do Bitrix24
                           - Verificar os campos personalizados nas tabelas de negócios e emissões
                           - Verificar os IDs exatos dos campos de ID da Família, ID do Requerente e Nome da Família
                        
                        2. Importar os dados diretamente:
                           - Exportar os dados relevantes do Bitrix24 para CSV
                           - Carregar os CSVs diretamente no painel
                        """)
                
                return
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        if st.button("🔄 Tentar Novamente", type="primary"):
            st.rerun()
        return
    
    # Processar dados
    try:
        with st.spinner("Processando dados..."):
            df_processado = processar_dados_protocolado(df_deal, df_deal_uf, df_cartorio)
            
            if df_processado is None or df_processado.empty:
                st.error("Não foi possível processar os dados para análise. Verifique os logs acima para mais detalhes.")
                if st.button("🔄 Tentar Novamente", type="primary", key="retry_process"):
                    st.rerun()
                return
            
            # Análise final dos dados
            df_analise = analisar_protocolados(df_processado)
            
            if df_analise is None or df_analise.empty:
                st.error("Não foi possível analisar os dados processados.")
                if st.button("🔄 Tentar Novamente", type="primary", key="retry_analyze"):
                    st.rerun()
                return
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")
        
        # Mostrar informações técnicas para diagnóstico
        with st.expander("Informações técnicas para diagnóstico", expanded=False):
            import traceback
            st.code(traceback.format_exc())
            
        if st.button("🔄 Tentar Novamente", type="primary", key="retry_exception"):
            st.rerun()
        return
    
    # Filtro por unidade
    st.markdown("#### Filtros Gerais")
    unidade_filter = st.radio(
        "Selecione a Unidade:",
        options=["Todas", "Carrão", "Alphaville"],
        horizontal=True
    )
    
    # Filtro simulado por unidade (como não temos essa informação nos dados, é apenas ilustrativo)
    st.info(f"Exibindo dados para: {unidade_filter}")
    
    # Criar duas abas principais
    tab_visao_geral, tab_detalhamento = st.tabs([
        "📊 Visão Geral", 
        "📋 Detalhamento"
    ])
    
    # Aba de Visão Geral
    with tab_visao_geral:
        criar_visao_geral_protocolados(df_analise)
    
    # Aba de Detalhamento
    with tab_detalhamento:
        mostrar_tabela_detalhada(df_analise)

if __name__ == "__main__":
    exibir_dashboard_protocolado() 