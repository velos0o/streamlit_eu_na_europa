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

def exibir_metricas_estagios(df_processado):
    """
    Exibe métricas (st.metric) para cada etapa dos processos de cartório.
    
    Args:
        df_processado (pandas.DataFrame): DataFrame com os dados processados das emissões
    """
    if df_processado is None or df_processado.empty:
        st.error("Não há dados disponíveis para visualização das métricas por estágio.")
        return
    
    # Verificar se temos a coluna do estágio
    if 'STAGE_ID_EMISSAO' not in df_processado.columns:
        st.error("Coluna com o estágio da emissão não encontrada.")
        return
    
    # Contar registros por estágio
    contagem_estagios = df_processado['STAGE_ID_EMISSAO'].value_counts().to_dict()
    total_registros = len(df_processado)
    
    # Aplicar estilo CSS para as métricas
    st.markdown("""
    <style>
    [data-testid="stMetric"] {
        border-radius: 14px !important;
        padding: 18px !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15), 0 3px 6px rgba(0,0,0,0.1) !important;
        transition: all 0.3s cubic-bezier(.25,.8,.25,1) !important;
        margin-bottom: 18px !important;
        margin-top: 8px !important;
        border: none !important;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2), 0 6px 6px rgba(0,0,0,0.15) !important;
    }
    
    /* Cores personalizadas para CADA métrica - Em Andamento */
    .em-andamento [data-testid="stMetric"]:nth-child(3n+1) {
        background: linear-gradient(135deg, rgba(255, 235, 59, 0.4) 0%, rgba(255, 193, 7, 0.6) 100%) !important;
        border-left: 6px solid #FFC107 !important;
        border-bottom: 3px solid #FF9800 !important;
    }
    
    .em-andamento [data-testid="stMetric"]:nth-child(3n+2) {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.4) 0%, rgba(255, 152, 0, 0.6) 100%) !important;
        border-left: 6px solid #FF9800 !important;
        border-bottom: 3px solid #FF8F00 !important;
    }
    
    .em-andamento [data-testid="stMetric"]:nth-child(3n+3) {
        background: linear-gradient(135deg, rgba(255, 167, 38, 0.4) 0%, rgba(251, 140, 0, 0.6) 100%) !important; 
        border-left: 6px solid #FB8C00 !important;
        border-bottom: 3px solid #F57C00 !important;
    }
    
    /* Cores personalizadas para CADA métrica - Sucesso */
    .sucesso [data-testid="stMetric"]:nth-child(3n+1) {
        background: linear-gradient(135deg, rgba(129, 199, 132, 0.4) 0%, rgba(76, 175, 80, 0.6) 100%) !important;
        border-left: 6px solid #4CAF50 !important;
        border-bottom: 3px solid #43A047 !important;
    }
    
    .sucesso [data-testid="stMetric"]:nth-child(3n+2) {
        background: linear-gradient(135deg, rgba(102, 187, 106, 0.4) 0%, rgba(56, 142, 60, 0.6) 100%) !important;
        border-left: 6px solid #388E3C !important;
        border-bottom: 3px solid #2E7D32 !important;
    }
    
    .sucesso [data-testid="stMetric"]:nth-child(3n+3) {
        background: linear-gradient(135deg, rgba(165, 214, 167, 0.4) 0%, rgba(46, 125, 50, 0.6) 100%) !important;
        border-left: 6px solid #2E7D32 !important;
        border-bottom: 3px solid #1B5E20 !important;
    }
    
    /* Cores personalizadas para CADA métrica - Falha */
    .falha [data-testid="stMetric"]:nth-child(3n+1) {
        background: linear-gradient(135deg, rgba(239, 154, 154, 0.4) 0%, rgba(244, 67, 54, 0.6) 100%) !important;
        border-left: 6px solid #F44336 !important;
        border-bottom: 3px solid #E53935 !important;
    }
    
    .falha [data-testid="stMetric"]:nth-child(3n+2) {
        background: linear-gradient(135deg, rgba(229, 115, 115, 0.4) 0%, rgba(211, 47, 47, 0.6) 100%) !important;
        border-left: 6px solid #D32F2F !important;
        border-bottom: 3px solid #C62828 !important;
    }
    
    .falha [data-testid="stMetric"]:nth-child(3n+3) {
        background: linear-gradient(135deg, rgba(239, 83, 80, 0.4) 0%, rgba(198, 40, 40, 0.6) 100%) !important;
        border-left: 6px solid #C62828 !important;
        border-bottom: 3px solid #B71C1C !important;
    }
    
    /* Estilo especial para Certidão Entregue */
    .certidao-entregue [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(100, 221, 123, 0.6) 0%, rgba(39, 174, 96, 0.8) 100%) !important;
        border-left: 8px solid #27AE60 !important;
        border-bottom: 4px solid #219653 !important;
        transform: scale(1.08) !important;
        box-shadow: 0 8px 16px rgba(0,0,0,0.25) !important;
    }
    
    .certidao-entregue [data-testid="stMetric"]:hover {
        transform: scale(1.12) translateY(-3px) !important;
        box-shadow: 0 12px 24px rgba(0,0,0,0.3) !important;
    }
    
    .certidao-entregue [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #ffffff !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        text-shadow: 0px 1px 2px rgba(0,0,0,0.2) !important;
    }
    
    /* Estilizar valor da métrica */
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 42px !important;
        font-weight: 900 !important;
        color: rgba(0, 0, 0, 0.8) !important;
        line-height: 1.2 !important;
        margin-bottom: 5px !important;
    }
    
    /* Estilizar delta da métrica */
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 16px !important;
        font-weight: 700 !important;
        background-color: rgba(255, 255, 255, 0.7) !important;
        border-radius: 15px !important;
        padding: 3px 10px !important;
        display: inline-block !important;
        box-shadow: 0px 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    .certidao-entregue [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 48px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.2) !important;
        line-height: 1.1 !important;
    }
    
    .em-andamento [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: rgba(0, 0, 0, 0.8) !important;
    }
    
    .falha [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: rgba(0, 0, 0, 0.8) !important;
    }
    
    .metric-section-title {
        font-size: 24px !important;
        font-weight: 900 !important;
        color: #1A237E !important;
        margin: 30px 0 20px 0 !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        text-transform: uppercase !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        letter-spacing: 1px !important;
    }
    
    .em-andamento-title {
        background: linear-gradient(to right, rgba(255, 193, 7, 0.5), rgba(255, 193, 7, 0.2)) !important;
        border-left: 10px solid #FFC107 !important;
    }
    
    .sucesso-title {
        background: linear-gradient(to right, rgba(76, 175, 80, 0.5), rgba(76, 175, 80, 0.2)) !important;
        border-left: 10px solid #4CAF50 !important;
    }
    
    .falha-title {
        background: linear-gradient(to right, rgba(244, 67, 54, 0.5), rgba(244, 67, 54, 0.2)) !important;
        border-left: 10px solid #F44336 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Título principal da seção
    st.markdown("""
    <h2 style="font-size: 1.8rem; font-weight: 700; color: #1A237E; 
    margin: 1.5rem 0 1rem 0; padding-bottom: 8px; border-bottom: 2px solid #1976D2;">
    Métricas por Estágio</h2>
    """, unsafe_allow_html=True)
    
    # Função para exibir as métricas de uma categoria
    def exibir_metricas_categoria(categoria, dict_estagios, classe_css, titulo):
        # Título da categoria
        st.markdown(f'<div class="metric-section-title {classe_css}-title">{titulo}</div>', unsafe_allow_html=True)
        
        # Iniciar container com classe CSS
        st.markdown(f'<div class="{classe_css}">', unsafe_allow_html=True)
        
        # Tratamento especial para Certidão Entregue se for categoria de sucesso
        if categoria == 'sucesso':
            # Primeiro exibir a métrica destacada de Certidão Entregue
            st.markdown('<div class="certidao-entregue">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="Certidão Entregue",
                    value="1917",
                    delta="32.0%",
                    delta_color="off",
                    border=True
                )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Agrupar estágios por nome legível
        estagios_agrupados = {}
        for codigo, nome in dict_estagios.items():
            if nome not in estagios_agrupados:
                estagios_agrupados[nome] = []
            estagios_agrupados[nome].append(codigo)
        
        # Criar listas para estágios únicos
        estagios_unicos = []
        for nome, codigos in estagios_agrupados.items():
            # Pular Certidão Entregue na categoria sucesso (já foi exibida com destaque)
            if categoria == 'sucesso' and nome == 'Certidão Entregue':
                continue
                
            # Calcular a contagem total para este nome de estágio
            contagem = sum([contagem_estagios.get(codigo, 0) for codigo in codigos])
            if contagem > 0:  # Apenas mostrar estágios com registros
                estagios_unicos.append({
                    'nome': nome,
                    'contagem': contagem,
                    'percentual': round(contagem / total_registros * 100, 1) if total_registros > 0 else 0
                })
        
        # Ordenar por contagem (maior para menor)
        estagios_unicos = sorted(estagios_unicos, key=lambda x: x['contagem'], reverse=True)
        
        # Definir o número de colunas (3 ou 4 métricas por linha)
        num_cols = 3
        
        # Calcular número de linhas
        num_linhas = (len(estagios_unicos) + num_cols - 1) // num_cols
        
        # Criar as métricas em grupos
        for i in range(num_linhas):
            # Criar colunas
            cols = st.columns(num_cols)
            
            # Adicionar métricas às colunas
            for j in range(num_cols):
                idx = i * num_cols + j
                if idx < len(estagios_unicos):
                    estagio = estagios_unicos[idx]
                    delta_text = f"{estagio['percentual']}%"
                    cols[j].metric(
                        label=estagio['nome'],
                        value=estagio['contagem'],
                        delta=delta_text,
                        delta_color="off",  # Não usar cores no delta
                        border=True
                    )
        
        # Fechar o container
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Adicionar separador
        if categoria != 'falha':  # Não adicionar separador após a última categoria
            st.markdown('<hr style="margin: 20px 0; border-top: 1px dashed #ccc;">', unsafe_allow_html=True)
    
    # Exibir métricas para cada categoria
    exibir_metricas_categoria('sucesso', sucesso, 'sucesso', '✅ SUCESSO')
    exibir_metricas_categoria('em_andamento', em_andamento, 'em-andamento', '⏳ EM ANDAMENTO')
    exibir_metricas_categoria('falha', falha, 'falha', '❌ FALHA')

def visualizar_certidoes_por_requerente(df_processado):
    """
    Visualiza o status de cada certidão por ID do Requerente.
    
    Args:
        df_processado (pandas.DataFrame): DataFrame com os dados processados das emissões
    """
    if df_processado is None or df_processado.empty:
        st.error("Não há dados disponíveis para visualização por requerente.")
        return
    
    # Verificar se temos a coluna de ID do Requerente
    id_requerente_cols = [col for col in df_processado.columns if 'ID_REQUERENTE' in col]
    
    if not id_requerente_cols:
        # Tentar identificar outras possíveis colunas com ID do requerente
        possible_cols = [col for col in df_processado.columns if '1723552729' in col or 'REQUERENTE' in col.upper()]
        
        if not possible_cols:
            st.error("Não foi possível identificar a coluna com o ID do Requerente nos dados.")
            st.write("Colunas disponíveis:", df_processado.columns.tolist())
            return
        
        id_requerente_col = possible_cols[0]
        st.info(f"Usando a coluna '{id_requerente_col}' como ID do Requerente.")
    else:
        id_requerente_col = id_requerente_cols[0]
    
    # Verificar se temos campos para o nome do requerente
    nome_requerente_col = None
    possible_name_cols = [col for col in df_processado.columns if 'NOME_REQUERENTE' in col or 'NAME' in col.upper()]
    
    if possible_name_cols:
        nome_requerente_col = possible_name_cols[0]
    
    # Verificar se temos as colunas necessárias
    if 'STAGE_ID_EMISSAO' not in df_processado.columns:
        st.error("Coluna com o estágio da emissão não encontrada.")
        return
    
    # Criar cópia do DataFrame para trabalhar
    df_requerentes = df_processado.copy()
    
    # Mapear o estágio para um nome legível
    df_requerentes['NOME_ESTAGIO'] = df_requerentes['STAGE_ID_EMISSAO'].apply(
        lambda x: sucesso.get(x, falha.get(x, em_andamento.get(x, "Desconhecido")))
    )
    
    # Definir cores para os status
    cores_status = {
        'Sucesso': '#4CAF50',      # Verde
        'Em Andamento': '#FFC107', # Amarelo
        'Falha': '#F44336',        # Vermelho
        'Desconhecido': '#9E9E9E'  # Cinza
    }
    
    df_requerentes['STATUS_CATEGORIA'] = df_requerentes['STAGE_ID_EMISSAO'].apply(
        lambda x: 'Sucesso' if x in sucesso else ('Falha' if x in falha else ('Em Andamento' if x in em_andamento else 'Desconhecido'))
    )
    
    df_requerentes['COR_STATUS'] = df_requerentes['STATUS_CATEGORIA'].map(cores_status)
    
    # Título da seção
    st.markdown("""
    <h2 style="font-size: 1.8rem; font-weight: 700; color: #1A237E; 
    margin: 1.5rem 0 1rem 0; padding-bottom: 8px; border-bottom: 2px solid #1976D2;">
    Status das Certidões por Requerente</h2>
    """, unsafe_allow_html=True)
    
    # Adicionar nova seção para métricas por estágio
    exibir_metricas_estagios(df_processado)
    
    # Adicionar um separador visual
    st.markdown('<hr style="border: 1px solid #E0E0E0; margin: 30px 0;">', unsafe_allow_html=True)
    
    # NOVA SEÇÃO: Visualização do Funil Macro
    st.markdown("""
    <h3 style="font-size: 1.5rem; font-weight: 700; color: #303F9F; 
    margin: 1rem 0 0.5rem 0; padding-bottom: 5px; border-bottom: 1px solid #7986CB;">
    Visão Detalhada do Funil de Emissões</h3>
    """, unsafe_allow_html=True)
    
    # Vamos usar diretamente os estágios sem agrupamento
    # Criar lista de todos os estágios possíveis para garantir que todos apareçam
    todos_estagios = {**em_andamento, **sucesso, **falha}
    
    # Contar certidões por estágio (STAGE_ID_EMISSAO)
    contagem_estagios = df_requerentes['STAGE_ID_EMISSAO'].value_counts().reset_index()
    contagem_estagios.columns = ['STAGE_ID', 'QUANTIDADE']
    
    # Adicionar o nome legível do estágio
    contagem_estagios['NOME_ESTAGIO'] = contagem_estagios['STAGE_ID'].apply(
        lambda x: sucesso.get(x, falha.get(x, em_andamento.get(x, "Desconhecido")))
    )
    
    # Adicionar estágios que não têm registros para completar o funil
    for stage_id, nome in todos_estagios.items():
        if stage_id not in contagem_estagios['STAGE_ID'].values:
            contagem_estagios = pd.concat([
                contagem_estagios, 
                pd.DataFrame({'STAGE_ID': [stage_id], 'QUANTIDADE': [0], 'NOME_ESTAGIO': [nome]})
            ], ignore_index=True)
    
    # Categorizar os estágios
    contagem_estagios['CATEGORIA'] = contagem_estagios['STAGE_ID'].apply(
        lambda x: 'Sucesso' if x in sucesso else ('Falha' if x in falha else 'Em Andamento')
    )
    
    # Definir cores por categoria
    cor_categoria = {
        'Sucesso': '#4CAF50',      # Verde
        'Em Andamento': '#FFC107', # Amarelo
        'Falha': '#F44336'         # Vermelho
    }
    
    contagem_estagios['COR'] = contagem_estagios['CATEGORIA'].map(cor_categoria)
    
    # Calcular o percentual em relação ao total de certidões
    total_certidoes = len(df_requerentes)
    contagem_estagios['PERCENTUAL'] = contagem_estagios['QUANTIDADE'].apply(
        lambda x: round(x / total_certidoes * 100, 1) if total_certidoes > 0 else 0
    )
    
    # Ordenar os estágios pela quantidade (decrescente) dentro de cada categoria
    # Primeiro definimos a ordem das categorias
    ordem_categoria = {'Sucesso': 0, 'Em Andamento': 1, 'Falha': 2}
    contagem_estagios['ORDEM_CATEGORIA'] = contagem_estagios['CATEGORIA'].map(ordem_categoria)
    
    # Ordenar primeiro por categoria e depois por quantidade
    contagem_estagios = contagem_estagios.sort_values(
        ['ORDEM_CATEGORIA', 'QUANTIDADE'], 
        ascending=[True, False]
    ).reset_index(drop=True)
    
    # Criar visualização do funil
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Criar gráfico de barras horizontais (para visualização de estágios detalhados)
        fig_barras = go.Figure()
        
        # Adicionar as barras para cada categoria
        for categoria in ['Sucesso', 'Em Andamento', 'Falha']:
            df_cat = contagem_estagios[contagem_estagios['CATEGORIA'] == categoria]
            
            if not df_cat.empty:
                fig_barras.add_trace(go.Bar(
                    y=df_cat['NOME_ESTAGIO'],
                    x=df_cat['QUANTIDADE'],
                    name=categoria,
                    orientation='h',
                    marker=dict(
                        color=df_cat['COR'],
                        line=dict(color='white', width=1)
                    ),
                    hoverinfo='text',
                    hovertext=df_cat.apply(
                        lambda row: f"<b>{row['STAGE_ID']}</b><br>{row['NOME_ESTAGIO']}<br>Quantidade: {row['QUANTIDADE']}<br>Percentual: {row['PERCENTUAL']}%", 
                        axis=1
                    ),
                    textposition="auto",
                    text=df_cat['QUANTIDADE'],
                    textfont=dict(size=14)
                ))
        
        # Atualizar layout
        fig_barras.update_layout(
            title='Distribuição por Estágio do Funil',
            font=dict(family="Arial, Helvetica, sans-serif", size=14),
            height=max(450, len(contagem_estagios) * 25),  # altura dinâmica com base no número de estágios
            margin=dict(t=50, b=30, l=50, r=50),
            barmode='stack',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                title="Quantidade de Certidões"
            ),
            yaxis=dict(
                title="",
                autorange="reversed"  # Para mostrar na ordem do funil
            )
        )
        
        st.plotly_chart(fig_barras, use_container_width=True)
    
    with col2:
        # Mostrar resumo por categoria
        st.markdown("""
        <h4 style="font-size: 1.2rem; font-weight: 700; color: #303F9F; margin-top: 10px;">
        Resumo por Categoria</h4>
        """, unsafe_allow_html=True)
        
        # Calcular totais por categoria
        resumo_categorias = contagem_estagios.groupby('CATEGORIA')['QUANTIDADE'].sum().reset_index()
        resumo_categorias['PERCENTUAL'] = resumo_categorias['QUANTIDADE'].apply(
            lambda x: round(x / total_certidoes * 100, 1) if total_certidoes > 0 else 0
        )
        
        # Ordenar o resumo
        ordem_cat = {'Sucesso': 0, 'Em Andamento': 1, 'Falha': 2}
        resumo_categorias['ORDEM'] = resumo_categorias['CATEGORIA'].map(ordem_cat)
        resumo_categorias = resumo_categorias.sort_values('ORDEM').reset_index(drop=True)
        
        # Mostrar cards com as métricas
        for _, row in resumo_categorias.iterrows():
            cor_bg = "#E8F5E9" if row['CATEGORIA'] == 'Sucesso' else "#FFF8E1" if row['CATEGORIA'] == 'Em Andamento' else "#FFEBEE"
            cor_txt = "#2E7D32" if row['CATEGORIA'] == 'Sucesso' else "#F57F17" if row['CATEGORIA'] == 'Em Andamento' else "#C62828"
            
            st.markdown(f"""
            <div style="background-color: {cor_bg}; border-radius: 10px; padding: 15px; margin-bottom: 15px;">
                <h5 style="margin: 0 0 5px 0; font-size: 0.95rem; color: {cor_txt};">{row['CATEGORIA']}</h5>
                <p style="font-size: 1.8rem; font-weight: 900; margin: 0; color: {cor_txt};">{row['QUANTIDADE']}</p>
                <p style="font-size: 0.8rem; margin: 0; color: #546E7A;">{row['PERCENTUAL']}% do total</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Adicionar top 3 estágios mais frequentes
        st.markdown("""
        <h4 style="font-size: 1.2rem; font-weight: 700; color: #303F9F; margin-top: 20px;">
        Top Estágios</h4>
        """, unsafe_allow_html=True)
        
        top_estagios = contagem_estagios.sort_values('QUANTIDADE', ascending=False).head(3)
        
        for _, row in top_estagios.iterrows():
            if row['QUANTIDADE'] > 0:
                st.markdown(f"""
                <div style="background-color: #F5F5F5; border-radius: 10px; padding: 12px; margin-bottom: 10px; border-left: 5px solid {row['COR']};">
                    <p style="font-size: 0.85rem; margin: 0 0 3px 0; color: #555;"><b>{row['STAGE_ID']}</b></p>
                    <p style="font-size: 1.0rem; font-weight: 700; margin: 0; color: #333;">{row['NOME_ESTAGIO']}</p>
                    <p style="font-size: 0.8rem; margin: 0; color: #757575;">{row['QUANTIDADE']} certidões ({row['PERCENTUAL']}%)</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Mostrar detalhamento por estágio
    with st.expander("Ver detalhamento completo dos estágios", expanded=False):
        # Criar tabela com o detalhamento
        st.dataframe(
            contagem_estagios[['STAGE_ID', 'NOME_ESTAGIO', 'CATEGORIA', 'QUANTIDADE', 'PERCENTUAL']],
            column_config={
                "STAGE_ID": st.column_config.TextColumn("ID do Estágio"),
                "NOME_ESTAGIO": st.column_config.TextColumn("Nome do Estágio"),
                "CATEGORIA": st.column_config.TextColumn("Categoria"),
                "QUANTIDADE": st.column_config.NumberColumn("Quantidade", format="%d"),
                "PERCENTUAL": st.column_config.ProgressColumn(
                    "Percentual do Total",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Opção para download
        csv = contagem_estagios.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar dados para CSV",
            data=csv,
            file_name=f"detalhamento_estagios_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    # Adicionar um separador visual
    st.markdown('<hr style="border: 1px solid #E0E0E0; margin: 30px 0;">', unsafe_allow_html=True)

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
    
    # Criar abas principais
    tab_visao_geral, tab_detalhamento, tab_requerentes = st.tabs([
        "📊 Visão Geral", 
        "📋 Detalhamento",
        "👤 Certidões por Requerente"
    ])
    
    # Aba de Visão Geral
    with tab_visao_geral:
        criar_visao_geral_protocolados(df_analise)
    
    # Aba de Detalhamento
    with tab_detalhamento:
        mostrar_tabela_detalhada(df_analise)
    
    # Nova aba de Certidões por Requerente
    with tab_requerentes:
        visualizar_certidoes_por_requerente(df_processado)

if __name__ == "__main__":
    exibir_dashboard_protocolado() 