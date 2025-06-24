import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import sys
from pathlib import Path
import time

# Adicionar o caminho da API para importação
api_path = Path(__file__).parents[2] / 'api'
sys.path.insert(0, str(api_path))

# Adicionar o caminho dos utils para importação
utils_path = Path(__file__).parents[2] / 'utils'
sys.path.insert(0, str(utils_path))

# Importar a função que usa cache da API Bitrix
from bitrix_connector import load_bitrix_data
from refresh_utils import handle_refresh_trigger, get_force_reload_status, clear_force_reload_flag
from utils.dataframe_utils import ensure_pandas_df

def analisar_produtividade(df):
    """
    Análise de produtividade baseada nos dados de movimentação de cards
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos cartórios
    """
    # Aplicar estilo personalizado para botão de atualização
    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 4px;
        transition-duration: 0.3s;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Verificar se temos as colunas necessárias para a análise
    colunas_necessarias = [
        'PREVIOUS_STAGE_ID',
        'MOVED_TIME',
        'CLOSEDATE',
        'STAGE_ID',
        'MOVED_BY_NAME',
        'UPDATED_BY_NAME',
        'UF_CRM_12_1723552666',  # ID da Familia
        'UF_CRM_12_1723552729',  # ID de Requerente
        'UF_CRM_12_1722534861891'  # Tipo de documento (Óbito, Casamento, Nascimento)
    ]
    
    colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
    if colunas_faltantes:
        st.error(f"Colunas necessárias não encontradas: {', '.join(colunas_faltantes)}")
        st.write("Colunas disponíveis:", df.columns.tolist())
        return
    
    # Adicionar nomes dos estágios para melhor visualização
    df = mapear_estagio_para_nome(df)
    
    st.markdown("## Visão de Movimentações")
    
    # Botão de atualização que força a recarga da página e limpa o cache
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Atualizar Dados", key="btn_atualizar", help="Força a atualização dos dados ignorando o cache"):
            with st.spinner("Atualizando dados e limpando cache..."):
                # Mostrar mensagem de feedback
                st.info("Limpando cache e recarregando dados em tempo real...")
                
                # Limpar todos os caches antes de recarregar
                st.cache_data.clear()
                
                # Limpar também o cache específico da API Bitrix
                load_bitrix_data.clear()
                
                # Definir flags no estado da sessão para consistência com o resto do projeto
                st.session_state['full_refresh'] = True
                st.session_state['force_reload'] = True
                st.session_state['loading_state'] = 'loading'
                
                # Pequena pausa para garantir que o cache seja completamente limpo
                time.sleep(0.5)
                st.success("Cache limpo! Recarregando página...")
                time.sleep(0.5)
                st.rerun()
        
        # Texto de ajuda para o botão de atualização
        st.caption("""
        Use este botão para forçar a atualização 
        dos dados em tempo real e limpar o cache
        """)
    
    # Verificar se há atualização global acionada por outro botão do sistema
    if handle_refresh_trigger():
        # Indicar que estamos atualizando
        st.info("⏳ Atualizando dados como parte de uma atualização global...")
        time.sleep(0.5)
        st.rerun()
    
    # Se estiver forçando recarregamento, exibir indicador
    force_reload = get_force_reload_status()
    if force_reload:
        st.info("⏳ Dados sendo atualizados diretamente da API (ignorando cache)...")
        # Limpar a flag após seu uso
        clear_force_reload_flag()
    
    st.info("""
    **O que é a Visão de Movimentações?**
    • Esta visão mostra a análise detalhada das movimentações dos cards entre etapas do fluxo de trabalho.
    • Permite identificar padrões, gargalos e fluxos mais comuns no processo.
    • Todas as análises consideram apenas movimentações entre etapas distintas, excluindo atualizações que não alteraram a etapa.
    """)
    
    # Aplicar filtros para análise
    st.sidebar.markdown("### Filtros de Movimentações")
    
    # Filtro de período
    hoje = datetime.now()
    data_inicio = st.sidebar.date_input(
        "Data Inicial",
        value=hoje - timedelta(days=30),    
        max_value=hoje,
        key="mov_data_inicio"
    )
    data_fim = st.sidebar.date_input(
        "Data Final",
        value=hoje,
        max_value=hoje,
        min_value=data_inicio,
        key="mov_data_fim"
    )
    
    # Filtro de tipo de documento
    tipos_documento = df['UF_CRM_12_1722534861891'].dropna().unique().tolist()
    tipo_documento_selecionado = st.sidebar.multiselect(
        "Tipo de Documento",
        options=tipos_documento,
        default=tipos_documento,
        key="mov_tipo_documento"
    )
    
    # Filtro de responsável
    responsaveis = df['MOVED_BY_NAME'].dropna().unique().tolist()
    responsavel_selecionado = st.sidebar.multiselect(
        "Responsável",
        options=responsaveis,
        default=responsaveis,
        key="mov_responsavel"
    )
    
    # Explicação sobre filtros
    with st.sidebar.expander("Sobre os Filtros", expanded=False):
        st.markdown("""
        **Como usar os filtros:**
        • **Data Inicial e Final**: Selecione o período que deseja analisar.
        • **Tipo de Documento**: Filtre por tipos específicos de documento (Nascimento, Casamento, Óbito).
        • **Responsável**: Filtre pelos colaboradores que realizaram movimentações.
        
        Todos os filtros são aplicados em conjunto (operação AND).
        """)
    
    # Preparar os dados
    # Converter colunas de data para datetime
    df['MOVED_TIME'] = pd.to_datetime(df['MOVED_TIME'], errors='coerce')
    df['CLOSEDATE'] = pd.to_datetime(df['CLOSEDATE'], errors='coerce')
    
    # Filtrar por período
    periodo_inicio = pd.to_datetime(data_inicio)
    periodo_fim = pd.to_datetime(data_fim) + timedelta(days=1) - timedelta(seconds=1)
    
    # Primeiro filtrar pelo período
    df_filtrado = df[(df['MOVED_TIME'] >= periodo_inicio) & 
                     (df['MOVED_TIME'] <= periodo_fim)]
    
    # Aplicar outros filtros se selecionados
    if tipo_documento_selecionado:
        df_filtrado = df_filtrado[df_filtrado['UF_CRM_12_1722534861891'].isin(tipo_documento_selecionado)]
    
    if responsavel_selecionado:
        df_filtrado = df_filtrado[df_filtrado['MOVED_BY_NAME'].isin(responsavel_selecionado)]
    
    if df_filtrado.empty:
        st.warning("Não há dados disponíveis para o período e filtros selecionados.")
        return
    
    # Criar abas para organizar as análises
    tab1, tab2, tab3 = st.tabs([
        "Movimentações Temporais",  # Alterada para primeira aba
        "Movimentação por Etapa", 
        "Movimentações por Responsável"
    ])
    
    with tab1:
        analisar_produtividade_temporal(df_filtrado)  # Agora é a primeira aba
    
    with tab2:
        comparar_estagio_atual_anterior(df_filtrado)  # Agora é a segunda aba
    
    with tab3:
        analisar_produtividade_responsavel(df_filtrado)

def mapear_estagio_para_nome(df):
    """
    Mapeia os IDs de estágio para nomes mais descritivos usando o mapeamento definido
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos cartórios
        
    Returns:
        pandas.DataFrame: DataFrame com colunas adicionais para nomes de estágios
    """
    # Criar uma cópia do DataFrame para não modificar o original
    df_modificado = df.copy()
    
    # Definir o mapeamento de estágios para nomes didáticos
    # EM ANDAMENTO
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
    
    # Combinar todos os mapeamentos
    mapeamento_completo = {**em_andamento, **sucesso, **falha}
    
    # Adicionar informação de categoria para cada estágio
    categorias_estagios = {}
    for estagio in em_andamento:
        categorias_estagios[estagio] = 'EM ANDAMENTO'
    for estagio in sucesso:
        categorias_estagios[estagio] = 'SUCESSO'
    for estagio in falha:
        categorias_estagios[estagio] = 'FALHA'
    
    # Adicionar colunas com os nomes dos estágios
    if 'STAGE_ID' in df_modificado.columns:
        df_modificado['STAGE_NAME'] = df_modificado['STAGE_ID'].map(mapeamento_completo)
        # Manter o ID original quando não houver mapeamento
        df_modificado['STAGE_NAME'] = df_modificado['STAGE_NAME'].fillna(df_modificado['STAGE_ID'])
        # Adicionar categoria do estágio
        df_modificado['STAGE_CATEGORY'] = df_modificado['STAGE_ID'].map(categorias_estagios)
    
    if 'PREVIOUS_STAGE_ID' in df_modificado.columns:
        df_modificado['PREVIOUS_STAGE_NAME'] = df_modificado['PREVIOUS_STAGE_ID'].map(mapeamento_completo)
        # Manter o ID original quando não houver mapeamento
        df_modificado['PREVIOUS_STAGE_NAME'] = df_modificado['PREVIOUS_STAGE_NAME'].fillna(df_modificado['PREVIOUS_STAGE_ID'])
        # Adicionar categoria do estágio anterior
        df_modificado['PREVIOUS_STAGE_CATEGORY'] = df_modificado['PREVIOUS_STAGE_ID'].map(categorias_estagios)
    
    return df_modificado 

def comparar_estagio_atual_anterior(df):
    """
    Compara o estágio atual com o estágio anterior
    
    Args:
        df (pandas.DataFrame): DataFrame filtrado com os dados dos cartórios
    """
    st.subheader("Comparação entre Estágio Atual e Anterior")
    
    # Verificar se temos as colunas de nome de estágio
    usar_nomes = 'STAGE_NAME' in df.columns and 'PREVIOUS_STAGE_NAME' in df.columns
    
    # Definir quais colunas usar para a análise
    coluna_atual = 'STAGE_NAME' if usar_nomes else 'STAGE_ID'
    coluna_anterior = 'PREVIOUS_STAGE_NAME' if usar_nomes else 'PREVIOUS_STAGE_ID'
    
    # Remover linhas onde estágio anterior ou atual são nulos
    df_valido = df.dropna(subset=[coluna_anterior, coluna_atual]).copy()
    
    if df_valido.empty:
        st.warning("Não há dados válidos para análise comparativa de estágios.")
        return
    
    # Criar resumo visual do fluxo de trabalho
    st.markdown("### Resumo do Fluxo de Trabalho")
    
    # Adicionar indicadores de resumo numérico no topo
    total_movimentacoes = len(df_valido)
    
    # Criar layout de colunas para métricas de resumo
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total de Movimentações",
            f"{total_movimentacoes}",
            help="Número total de movimentações de cards entre estágios"
        )
    
    with col2:
        # Calcular quantos cards diferentes foram movimentados
        cards_unicos = df_valido['UF_CRM_12_1723552666'].nunique()
        st.metric(
            "Cards Únicos Movimentados",
            f"{cards_unicos}",
            help="Número de cards/famílias únicas que tiveram movimentação"
        )
    
    with col3:
        # Calcular média diária de movimentações
        dias_periodo = df_valido['MOVED_TIME'].dt.date.nunique()
        media_diaria = round(total_movimentacoes / max(dias_periodo, 1), 1)
        st.metric(
            "Média Diária",
            f"{media_diaria}",
            help="Média de movimentações por dia no período selecionado"
        )
    
    # Adicionar explicação das métricas
    st.info("""
    **Interpretação das métricas:**
    • **Total de Movimentações**: Número total de vezes que cards mudaram de uma etapa para outra no período.
    • **Cards Únicos Movimentados**: Quantidade de processos distintos que tiveram alguma mudança de etapa.
    • **Média Diária**: Quantidade média de movimentações ocorridas por dia no período analisado.
    """)
    
    # Criar visualização mais didática das principais transições
    st.markdown("### Principais Movimentações entre Etapas")

    # Agrupar por estágio anterior e atual, contando a quantidade de movimentações
    contagem_movimentacoes = df_valido.groupby([coluna_anterior, coluna_atual]).size().reset_index(name='QUANTIDADE')
    
    # Adicionar coluna com texto mais didático
    contagem_movimentacoes['DESCRIÇÃO'] = contagem_movimentacoes.apply(
        lambda row: f"{row['QUANTIDADE']} cards movidos de '{row[coluna_anterior]}' para '{row[coluna_atual]}'", 
        axis=1
    )
    
    # Ordenar por quantidade (maior para menor)
    contagem_movimentacoes = contagem_movimentacoes.sort_values('QUANTIDADE', ascending=False)
    
    # Pegar apenas as 10 principais transições para melhor visualização
    top_transicoes = contagem_movimentacoes.head(10)
    
    # Criar uma coluna de transição para o gráfico de barras
    top_transicoes['TRANSICAO'] = top_transicoes.apply(lambda row: f"{row[coluna_anterior]} → {row[coluna_atual]}", axis=1)
    
    # Criar gráfico de barras horizontais para as principais transições
    fig_top = px.bar(
        top_transicoes,
        y='TRANSICAO',
        x='QUANTIDADE',
        orientation='h',
        text='QUANTIDADE',
        labels={
            'QUANTIDADE': 'Número de Movimentações',
            'TRANSICAO': 'Transição entre Estágios'
        },
        title="Top 10 Movimentações mais Frequentes"
    )
    
    # Melhorar a formatação do gráfico
    fig_top.update_traces(
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Quantidade: %{x}<extra></extra>'
    )
    
    fig_top.update_layout(
        height=500,
        yaxis={'categoryorder': 'total ascending'},
        font=dict(size=14),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    st.plotly_chart(fig_top, use_container_width=True)
    
    # Adicionar explicação do gráfico de barras
    st.info("""
    **Como interpretar este gráfico:**
    • Mostra as 10 transições mais frequentes entre etapas específicas.
    • Quanto mais longa a barra, maior o número de cards que seguiram aquele caminho.
    • Ajuda a identificar os fluxos mais comuns no processo.
    • A seta "→" indica a direção da movimentação (de qual etapa para qual etapa).
    """)
    
    # Exibir tabela com as movimentações em formato mais didático
    st.dataframe(
        top_transicoes[['DESCRIÇÃO', coluna_anterior, coluna_atual, 'QUANTIDADE']],
        column_config={
            "DESCRIÇÃO": st.column_config.TextColumn("Descrição da Movimentação"),
            coluna_anterior: st.column_config.TextColumn("Estágio Anterior"),
            coluna_atual: st.column_config.TextColumn("Estágio Atual"),
            "QUANTIDADE": st.column_config.NumberColumn("Quantidade", format="%d")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Criar tabela de todas as movimentações para referência
    with st.expander("Ver todas as movimentações em detalhe", expanded=False):
        st.dataframe(
            contagem_movimentacoes[['DESCRIÇÃO', coluna_anterior, coluna_atual, 'QUANTIDADE']],
            column_config={
                "DESCRIÇÃO": st.column_config.TextColumn("Descrição da Movimentação"),
                coluna_anterior: st.column_config.TextColumn("Estágio Anterior"),
                coluna_atual: st.column_config.TextColumn("Estágio Atual"),
                "QUANTIDADE": st.column_config.NumberColumn("Quantidade", format="%d")
            },
            use_container_width=True,
            hide_index=True
        )
    
    # Criar gráfico de sankey para visualizar fluxo entre estágios
    st.markdown("### Fluxo entre Estágios")
    
    # Permitir ao usuário limitar o número de conexões para melhor visualização
    num_conexoes = st.slider(
        "Número de conexões a exibir:",
        min_value=5,
        max_value=min(30, len(contagem_movimentacoes)),
        value=15,
        step=5,
        help="Ajuste para melhorar a legibilidade do gráfico"
    )
    
    # Filtrar apenas as principais transições para o gráfico Sankey
    top_sankey = contagem_movimentacoes.head(num_conexoes)
    
    # Criar lista de estágios únicos para indexação
    estagios_unicos = pd.concat([
        top_sankey[coluna_anterior], 
        top_sankey[coluna_atual]
    ]).unique()
    
    # Criar mapeamento de estágio para índice
    estag_para_idx = {estagio: i for i, estagio in enumerate(estagios_unicos)}
    
    # Preparar dados para o gráfico Sankey
    source = [estag_para_idx[estagio] for estagio in top_sankey[coluna_anterior]]
    target = [estag_para_idx[estagio] for estagio in top_sankey[coluna_atual]]
    value = top_sankey['QUANTIDADE'].tolist()
    
    # Criar o gráfico Sankey com configurações melhoradas
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',  # Melhor arranjo para visibilidade
        node=dict(
            pad=20,
            thickness=30,
            line=dict(color="black", width=0.5),
            label=list(estagios_unicos),
            color='rgba(31, 119, 180, 0.8)'  # Azul padrão
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            label=[f"{q}" for q in value],  # Simplificar labels
            hovertemplate='<b>%{value}</b> cards movidos de <b>%{source.label}</b> para <b>%{target.label}</b><extra></extra>'
        )
    )])
    
    fig.update_layout(
        title={
            'text': f"Fluxo das {num_conexoes} Principais Movimentações entre Estágios",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        height=700,  # Aumentar altura
        font=dict(size=14),  # Aumentar fonte
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Adicionar explicação do gráfico Sankey detalhado
    st.info("""
    **Como interpretar este gráfico de fluxo:**
    • Cada nó (retângulo) representa uma etapa do processo.
    • As linhas de conexão mostram o volume de cards que se movem de uma etapa para outra.
    • Quanto mais larga a conexão, maior o volume de movimentações naquele caminho.
    • Use o controle deslizante acima para ajustar o número de conexões exibidas e melhorar a legibilidade.
    • Passe o mouse sobre as conexões ou nós para ver detalhes.
    """)
    
    # Análise por tipo de documento
    if 'UF_CRM_12_1722534861891' in df_valido.columns:
        st.markdown("### Movimentações por Tipo de Documento")
        
        # Agrupar por tipo de documento para mostrar volume
        volume_por_tipo = df_valido.groupby('UF_CRM_12_1722534861891').size().reset_index(name='QUANTIDADE')
        volume_por_tipo = volume_por_tipo.sort_values('QUANTIDADE', ascending=False)
        
        # Mostrar gráfico de volume por tipo de documento
        fig_tipos = px.pie(
            volume_por_tipo,
            values='QUANTIDADE',
            names='UF_CRM_12_1722534861891',
            title="Volume de Movimentações por Tipo de Documento",
            hole=0.4
        )
        
        fig_tipos.update_layout(
            height=500,
            font=dict(size=14)
        )
        
        st.plotly_chart(fig_tipos, use_container_width=True)
        
        # Adicionar explicação do gráfico de pizza
        st.info("""
        **Como interpretar este gráfico de pizza:**
        • Mostra a distribuição de movimentações por tipo de documento (Nascimento, Casamento, Óbito, etc).
        • Cada fatia representa o percentual de movimentações para aquele tipo de documento.
        • Ajuda a identificar quais tipos de documento estão tendo mais movimento no período.
        """)
        
        # Agrupar por tipo de documento, estágio anterior e atual
        contagem_tipo_doc = df_valido.groupby(['UF_CRM_12_1722534861891', coluna_anterior, coluna_atual]).size().reset_index(name='QUANTIDADE')
        
        # Adicionar coluna com texto didático
        contagem_tipo_doc['DESCRIÇÃO'] = contagem_tipo_doc.apply(
            lambda row: f"{row['QUANTIDADE']} cards movidos de '{row[coluna_anterior]}' para '{row[coluna_atual]}'", 
            axis=1
        )
        
        # Criar seletores para filtrar por tipo de documento
        tipos_doc = contagem_tipo_doc['UF_CRM_12_1722534861891'].unique().tolist()
        tipo_selecionado = st.selectbox(
            "Selecione o tipo de documento para análise detalhada:",
            options=tipos_doc
        )
        
        # Filtrar dados pelo tipo de documento selecionado
        df_tipo = contagem_tipo_doc[contagem_tipo_doc['UF_CRM_12_1722534861891'] == tipo_selecionado]
        
        # Ordenar por quantidade (maior para menor)
        df_tipo = df_tipo.sort_values('QUANTIDADE', ascending=False)
        
        # Exibir tabela com as movimentações para o tipo selecionado
        st.dataframe(
            df_tipo.head(10)[['DESCRIÇÃO', coluna_anterior, coluna_atual, 'QUANTIDADE']],
            column_config={
                "DESCRIÇÃO": st.column_config.TextColumn("Descrição da Movimentação"),
                coluna_anterior: st.column_config.TextColumn("Estágio Anterior"),
                coluna_atual: st.column_config.TextColumn("Estágio Atual"),
                "QUANTIDADE": st.column_config.NumberColumn("Quantidade", format="%d")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Adicionar explicação da tabela por tipo de documento
        st.info(f"""
        **Como interpretar esta tabela para {tipo_selecionado}:**
        • Mostra as movimentações mais frequentes para o tipo de documento selecionado.
        • Permite identificar padrões específicos por tipo de documento.
        • Ordenada por quantidade (maior para menor).
        • Mostra apenas as 10 movimentações mais frequentes para melhor legibilidade.
        """)
        
        # Adicionar gráfico de heatmap para visualizar melhor as transições
        # Limitar para as top 10 etapas anteriores e atuais para melhor visualização
        top_anterior = df_tipo[coluna_anterior].value_counts().nlargest(10).index.tolist()
        top_atual = df_tipo[coluna_atual].value_counts().nlargest(10).index.tolist()
        
        df_tipo_filtered = df_tipo[
            df_tipo[coluna_anterior].isin(top_anterior) & 
            df_tipo[coluna_atual].isin(top_atual)
        ]
        
        pivot_transicoes = df_tipo_filtered.pivot_table(
            index=coluna_anterior,
            columns=coluna_atual,
            values='QUANTIDADE',
            fill_value=0
        )
        
        # Criar heatmap
        fig_heatmap = px.imshow(
            pivot_transicoes,
            labels=dict(x="Estágio Atual", y="Estágio Anterior", color="Quantidade"),
            title=f"Mapa de Calor das Principais Transições para {tipo_selecionado}",
            color_continuous_scale="YlOrRd",
            text_auto=True
        )
        
        fig_heatmap.update_layout(
            height=600,
            xaxis_tickangle=-45,
            font=dict(size=14)
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Adicionar explicação do mapa de calor
        st.info(f"""
        **Como interpretar este mapa de calor para {tipo_selecionado}:**
        • As cores mais intensas (vermelho escuro) indicam mais movimentações entre aquelas etapas.
        • O eixo Y mostra as etapas de origem (anteriores) e o eixo X as etapas de destino (atuais).
        • Ajuda a visualizar padrões de movimentação específicos para este tipo de documento.
        • Os números mostram a quantidade exata de movimentações em cada transição.
        """)
    else:
        st.warning("Campo 'UF_CRM_12_1722534861891' (Tipo de documento) não encontrado para análise.") 

def analisar_produtividade_temporal(df):
    """
    Analisa a produtividade ao longo do tempo
    
    Args:
        df (pandas.DataFrame): DataFrame filtrado com os dados dos cartórios
    """
    st.subheader("Movimentações ao Longo do Tempo")
    
    st.info("""
    **Visão Geral das Movimentações Temporais** 📊📈
    
    Esta visão analisa apenas as **movimentações reais** entre etapas diferentes - quando um card realmente muda de status.
    Não são consideradas:
    • Atualizações que não alteraram a etapa do card
    • Cards sem etapa anterior (primeira entrada no sistema)
    • Movimentações onde a etapa atual é igual à anterior
    
    Isso permite uma visão mais precisa da produtividade efetiva do fluxo de trabalho.
    """)
    
    st.markdown("""
    <div style='background-color:#EFEFEF; padding:10px; border-radius:5px; margin-bottom:15px'>
    <strong>✅ Critérios de filtragem:</strong><br>
    • Usamos <code>MOVED_TIME</code> como referência de data/hora da movimentação<br>
    • Exigimos que exista um estágio anterior (<code>PREVIOUS_STAGE_ID</code> não nulo)<br>
    • Garantimos que o estágio atual seja diferente do anterior (verdadeira mudança de status)<br>
    • Todos os gráficos e métricas consideram apenas movimentações que atendam a estes critérios
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar se temos a coluna de data de movimentação
    if 'MOVED_TIME' not in df.columns:
        st.error("Coluna 'MOVED_TIME' não encontrada para análise temporal.")
        return
    
    # Verificar quais colunas usar
    usar_nomes = 'STAGE_NAME' in df.columns
    coluna_estagio = 'STAGE_NAME' if usar_nomes else 'STAGE_ID'
    coluna_estagio_anterior = 'PREVIOUS_STAGE_NAME' if usar_nomes else 'PREVIOUS_STAGE_ID'
    
    # Converter para datetime se necessário
    df['MOVED_TIME'] = pd.to_datetime(df['MOVED_TIME'], errors='coerce')
    
    # Remover linhas sem data de movimentação e sem estágio anterior (primeira etapa)
    df_valido = df.dropna(subset=['MOVED_TIME']).copy()
    
    # Uma movimentação ocorre quando há um estágio anterior (não é null)
    df_movimentacoes = df_valido.dropna(subset=[coluna_estagio_anterior]).copy()
    
    # Filtrar apenas as verdadeiras mudanças de etapa (onde etapa anterior != etapa atual)
    df_movimentacoes = df_movimentacoes[df_movimentacoes[coluna_estagio_anterior] != df_movimentacoes[coluna_estagio]].copy()
    
    df_movimentacoes['TIPO_ACAO'] = 'Movimentação'
    
    # Para este caso, só vamos considerar as movimentações para análise temporal
    df_analise = df_movimentacoes.copy()
    
    if df_analise.empty:
        st.warning("Não há dados válidos para análise temporal após filtrar por movimentações entre etapas.")
        return
    
    # Criar nova coluna com data formatada para diferentes agrupamentos
    df_analise['DATA'] = df_analise['MOVED_TIME'].dt.date
    df_analise['SEMANA'] = df_analise['MOVED_TIME'].dt.strftime('%Y-%U')
    df_analise['MES'] = df_analise['MOVED_TIME'].dt.strftime('%Y-%m')
    
    # Adicionar colunas mais amigáveis para exibição
    df_analise['SEMANA_FORMATADA'] = df_analise['MOVED_TIME'].dt.strftime('Semana %U/%Y')
    df_analise['MES_FORMATADO'] = df_analise['MOVED_TIME'].dt.strftime('%B/%Y')
    
    # Exibir estatísticas básicas sobre os dados filtrados
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Total de Movimentações entre Etapas",
            f"{len(df_analise)}",
            help="Movimentações onde o card mudou de uma etapa para outra"
        )
    
    with col2:
        st.metric(
            "Cards Únicos Movimentados",
            f"{df_analise['UF_CRM_12_1723552666'].nunique()}",
            help="Número de cards/famílias únicas que tiveram movimentação entre etapas"
        )
    
    # Guias para escolher entre visão diária, semanal ou mensal
    tab_dia, tab_semana, tab_mes = st.tabs(["Movimentações Diárias", "Movimentações Semanais", "Movimentações Mensais"])
    
    with tab_dia:
        analisar_produtividade_por_periodo(df_analise, 'DATA', 'DATA', coluna_estagio, "Diária")
        
    with tab_semana:
        analisar_produtividade_por_periodo(df_analise, 'SEMANA', 'SEMANA_FORMATADA', coluna_estagio, "Semanal")
        
    with tab_mes:
        analisar_produtividade_por_periodo(df_analise, 'MES', 'MES_FORMATADO', coluna_estagio, "Mensal")
    
    # Análise de tempo médio entre estágios
    if 'MOVED_TIME' in df.columns and 'CLOSEDATE' in df.columns:
        st.markdown("### Tempo Médio entre Movimentações")
        
        # Agrupar por ID da Família e calcular estatísticas
        if 'UF_CRM_12_1723552666' in df.columns:
            # Ordenar os dados por ID da Família e data de movimentação
            df_tempo = df_movimentacoes.dropna(subset=['UF_CRM_12_1723552666', 'MOVED_TIME']).copy()
            df_tempo = df_tempo.sort_values(['UF_CRM_12_1723552666', 'MOVED_TIME'])
            
            # Calcular a diferença de tempo entre movimentações para o mesmo ID de família
            df_tempo['PROXIMA_MOVIMENTACAO'] = df_tempo.groupby('UF_CRM_12_1723552666')['MOVED_TIME'].shift(-1)
            df_tempo['TEMPO_ATE_PROXIMA'] = (df_tempo['PROXIMA_MOVIMENTACAO'] - df_tempo['MOVED_TIME']).dt.total_seconds() / 3600  # em horas
            
            # Remover outliers e valores negativos
            df_tempo = df_tempo[(df_tempo['TEMPO_ATE_PROXIMA'] > 0) & (df_tempo['TEMPO_ATE_PROXIMA'] < 720)]  # Limitar a 30 dias (720 horas)
            
            # Agrupar por estágio atual e calcular tempo médio até a próxima movimentação
            tempo_medio = df_tempo.groupby(coluna_estagio)['TEMPO_ATE_PROXIMA'].agg(['mean', 'median', 'count']).reset_index()
            tempo_medio = tempo_medio.rename(columns={'mean': 'Média (horas)', 'median': 'Mediana (horas)', 'count': 'Quantidade'})
            tempo_medio['Média (horas)'] = tempo_medio['Média (horas)'].round(2)
            tempo_medio['Mediana (horas)'] = tempo_medio['Mediana (horas)'].round(2)
            
            # Calcular a média em dias também para melhor interpretação
            tempo_medio['Média (dias)'] = (tempo_medio['Média (horas)'] / 24).round(2)
            
            # Ordenar por tempo médio (maior para menor)
            tempo_medio = tempo_medio.sort_values('Média (horas)', ascending=False)
            
            # Exibir tabela com os tempos médios
            st.dataframe(
                tempo_medio,
                column_config={
                    coluna_estagio: st.column_config.TextColumn("Estágio"),
                    "Média (horas)": st.column_config.NumberColumn("Média (horas)", format="%.2f"),
                    "Média (dias)": st.column_config.NumberColumn("Média (dias)", format="%.2f"),
                    "Mediana (horas)": st.column_config.NumberColumn("Mediana (horas)", format="%.2f"),
                    "Quantidade": st.column_config.NumberColumn("Quantidade", format="%d")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Gráfico de barras para visualizar tempos médios (limitando aos 15 principais para legibilidade)
            top_tempos = tempo_medio.head(15)
            
            fig_tempo = px.bar(
                top_tempos,
                x='Média (horas)',
                y=coluna_estagio,
                title="Tempo Médio de Permanência em Cada Estágio",
                labels={coluna_estagio: 'Estágio', 'Média (horas)': 'Tempo Médio (horas)'},
                text='Média (horas)',
                orientation='h'
            )
            
            fig_tempo.update_layout(
                height=600,
                yaxis={'categoryorder': 'total ascending'},
                font=dict(size=14)
            )
            
            st.plotly_chart(fig_tempo, use_container_width=True)
        else:
            st.warning("Campo 'UF_CRM_12_1723552666' (ID da Família) não encontrado para análise de tempo médio.") 

def analisar_produtividade_por_periodo(df, coluna_periodo, coluna_exibicao, coluna_estagio, tipo_periodo):
    """
    Analisa a produtividade para um período específico (dia, semana, mês)
    """
    try:
        st.markdown(f"### Movimentações {tipo_periodo}")
        
        # Agrupar movimentações pelo período
        contagem_periodo = df.groupby([coluna_periodo, coluna_estagio]).size().reset_index(name='QUANTIDADE')
        
        # Calcular total por período para todos os estágios
        total_por_periodo = contagem_periodo.groupby(coluna_periodo)['QUANTIDADE'].sum().reset_index()
        
        # Garantir que as datas estejam em formato string para gráficos
        if coluna_periodo == 'DATA':
            total_por_periodo['PERIODO_STR'] = [d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d) for d in total_por_periodo[coluna_periodo]]
            coluna_para_grafico = 'PERIODO_STR'
        elif coluna_exibicao != coluna_periodo and coluna_exibicao in df.columns:
            periodo_para_formatado = {}
            for idx, row in df.drop_duplicates([coluna_periodo, coluna_exibicao]).iterrows():
                if pd.notna(row[coluna_periodo]) and pd.notna(row[coluna_exibicao]):
                    periodo_para_formatado[row[coluna_periodo]] = str(row[coluna_exibicao])
            total_por_periodo['PERIODO_STR'] = total_por_periodo[coluna_periodo].map(periodo_para_formatado)
            total_por_periodo['PERIODO_STR'] = total_por_periodo['PERIODO_STR'].fillna(total_por_periodo[coluna_periodo].astype(str))
            coluna_para_grafico = 'PERIODO_STR'
        else:
            total_por_periodo['PERIODO_STR'] = total_por_periodo[coluna_periodo].astype(str)
            coluna_para_grafico = 'PERIODO_STR'
        
        # Ordenar por período
        total_por_periodo = total_por_periodo.sort_values(coluna_periodo)
        
        # Criar gráfico de linha com mais detalhes visuais
        fig_linha = px.line(
            total_por_periodo, 
            x=coluna_para_grafico, 
            y='QUANTIDADE',
            title=f"Volume Total de Movimentações ({tipo_periodo})",
            labels={coluna_para_grafico: 'Período', 'QUANTIDADE': 'Quantidade'},
            markers=True,
            text='QUANTIDADE'
        )
        
        fig_linha.update_traces(
            textposition='top center',
            line=dict(width=3),
            marker=dict(size=8)
        )
        
        fig_linha.update_layout(
            height=500,
            xaxis_tickangle=-45 if len(total_por_periodo) > 10 else 0,
            font=dict(size=14),
            margin=dict(l=20, r=20, t=50, b=100 if len(total_por_periodo) > 10 else 50)
        )
        
        st.plotly_chart(fig_linha, use_container_width=True)
        
        # Criar visualização por etapa
        st.markdown(f"### Movimentações por Etapa ({tipo_periodo})")
        
        # Usar apenas os 10 estágios mais comuns
        top_estagios = contagem_periodo.groupby(coluna_estagio)['QUANTIDADE'].sum().nlargest(10).index
        df_top = df[df[coluna_estagio].isin(top_estagios)].copy()
        
        # Agrupar novamente com apenas os top estágios
        contagem_top = df_top.groupby([coluna_periodo, coluna_estagio]).size().reset_index(name='QUANTIDADE')
        
        # Criar pivot table
        pivot = contagem_top.pivot(
            index=coluna_periodo,
            columns=coluna_estagio,
            values='QUANTIDADE'
        ).fillna(0)
        
        # Resetar índice
        pivot = pivot.reset_index()
        
        # Adicionar coluna de período formatado
        if coluna_periodo == 'DATA':
            pivot['PERIODO_STR'] = [d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d) for d in pivot[coluna_periodo]]
        else:
            pivot['PERIODO_STR'] = pivot[coluna_periodo].astype(str)
        
        # Ordenar por período
        pivot = pivot.sort_values(coluna_periodo)
        
        # Preparar dados para o gráfico
        df_plot = pd.melt(
            pivot,
            id_vars=['PERIODO_STR'],
            value_vars=[col for col in pivot.columns if col not in [coluna_periodo, 'PERIODO_STR']],
            var_name='ESTAGIO',
            value_name='QUANTIDADE'
        )
        
        # Criar gráfico de barras empilhadas
        fig_barras = px.bar(
            df_plot,
            x='PERIODO_STR',
            y='QUANTIDADE',
            color='ESTAGIO',
            title=f"Movimentações por Etapa ({tipo_periodo}) - Top 10 Estágios",
            labels={
                'PERIODO_STR': 'Período',
                'QUANTIDADE': 'Quantidade',
                'ESTAGIO': 'Estágio'
            },
            barmode='stack'
        )
        
        # Melhorar a formatação do gráfico
        fig_barras.update_layout(
            height=600,
            xaxis_tickangle=-45,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=20, r=20, t=100, b=100),
            yaxis_title="Quantidade de Movimentações",
            xaxis_title="Período",
            plot_bgcolor='white',
            yaxis=dict(
                gridcolor='lightgray',
                gridwidth=1
            ),
            xaxis=dict(
                gridcolor='lightgray',
                gridwidth=1
            )
        )
        
        st.plotly_chart(fig_barras, use_container_width=True)
        
        # Adicionar explicação do gráfico
        st.info("""
        **Como interpretar este gráfico:**
        • Cada barra representa um período
        • As cores diferentes representam diferentes estágios
        • A altura de cada segmento colorido mostra a quantidade de movimentações para aquele estágio
        • A altura total da barra mostra o total de movimentações no período
        """)
        
    except Exception as e:
        st.error(f"Erro ao criar visualização: {str(e)}")
        st.write("Por favor, entre em contato com o suporte técnico se o problema persistir.")

def analisar_produtividade_responsavel(df):
    """
    Analisa a produtividade por responsável
    
    Args:
        df (pandas.DataFrame): DataFrame filtrado com os dados dos cartórios
    """
    st.subheader("Movimentações por Responsável")
    st.info("""
    **O que é esta análise?**
    Esta análise mostra o desempenho individual de cada responsável pelas movimentações de cards.
    Permite identificar quem está movimentando mais cards, quais etapas cada pessoa mais trabalha, e padrões de especialização.
    """)
    
    # Definição dos grupos de usuários por cartório
    GRUPO_TATUAPE = {
        'Isabella Maielli': '330',
        'Karolina Pantaleão': '332'
    }
    
    GRUPO_CASA_VERDE = {
        'Vanessa Casa Verde': '210',
        'Stael Casa Verde': '214',
        'Alexandre Casa Verde': '266',
        'Marcelo': '276',
        'Ana Beatriz Pacheco': '278',
        'Beatriz Costa': '526',
        'João Vitor': '528',
        'Luana Carolina Mangano': '604',
        'Bianca Lima': '612'
    }
    
    # Lista de usuários prioritários por cartório (incluindo nomes e IDs)
    usuarios_tatuape = []
    for nome, id_usuario in GRUPO_TATUAPE.items():
        usuarios_tatuape.extend([nome, id_usuario])
    usuarios_tatuape.append('Cartório Tatuapé')
    
    usuarios_casa_verde = []
    for nome, id_usuario in GRUPO_CASA_VERDE.items():
        usuarios_casa_verde.extend([nome, id_usuario])
    
    # Combinar todos os usuários prioritários
    usuarios_prioritarios = usuarios_tatuape + usuarios_casa_verde
    
    # Criar mapeamento de IDs para nomes para unificar as contagens
    mapeamento_id_nome = {**{v: k for k, v in GRUPO_TATUAPE.items()},
                         **{v: k for k, v in GRUPO_CASA_VERDE.items()}}
    
    # Criar mapeamento de grupo para cada usuário
    mapeamento_grupo = {}
    for nome in GRUPO_TATUAPE:
        mapeamento_grupo[nome] = 'Cartório Tatuapé'
        mapeamento_grupo[GRUPO_TATUAPE[nome]] = 'Cartório Tatuapé'
    
    for nome in GRUPO_CASA_VERDE:
        mapeamento_grupo[nome] = 'Cartório Casa Verde'
        mapeamento_grupo[GRUPO_CASA_VERDE[nome]] = 'Cartório Casa Verde'
    
    # Verificar se temos as colunas necessárias
    if 'MOVED_BY_NAME' not in df.columns or 'MOVED_TIME' not in df.columns:
        st.error("Colunas 'MOVED_BY_NAME' ou 'MOVED_TIME' não encontradas para análise por responsável.")
        return
    
    # Verificar quais colunas usar
    usar_nomes = 'STAGE_NAME' in df.columns
    coluna_estagio = 'STAGE_NAME' if usar_nomes else 'STAGE_ID'
    
    # Converter para datetime se necessário
    df['MOVED_TIME'] = pd.to_datetime(df['MOVED_TIME'], errors='coerce')
    
    # Remover linhas sem responsável ou data
    df_valido = df.dropna(subset=['MOVED_BY_NAME', 'MOVED_TIME']).copy()
    
    if df_valido.empty:
        st.warning("Não há dados válidos para análise por responsável.")
        return
    
    # Criar nova coluna com data formatada
    df_valido['DATA'] = df_valido['MOVED_TIME'].dt.date
    
    # Antes de fazer qualquer análise, unificar os IDs com os nomes e adicionar informação do grupo
    df_valido['MOVED_BY_NAME'] = df_valido['MOVED_BY_NAME'].replace(mapeamento_id_nome)
    df_valido['GRUPO'] = df_valido['MOVED_BY_NAME'].map(mapeamento_grupo)
    
    # Criar tabela de produtividade diária por responsável
    produtividade_diaria = df_valido.groupby(['MOVED_BY_NAME', 'DATA']).size().reset_index(name='QUANTIDADE')
    
    # Pivot table para responsáveis nas linhas e datas nas colunas
    pivot_responsavel = produtividade_diaria.pivot_table(
        index='MOVED_BY_NAME',
        columns='DATA',
        values='QUANTIDADE',
        fill_value=0
    )
    
    # Adicionar coluna de total por responsável
    pivot_responsavel['TOTAL'] = pivot_responsavel.sum(axis=1)
    
    # Ordenar primeiro os usuários prioritários, depois os demais por total
    usuarios_ordenados = (
        pd.concat([
            pivot_responsavel[pivot_responsavel.index.isin(usuarios_prioritarios)],
            pivot_responsavel[~pivot_responsavel.index.isin(usuarios_prioritarios)]
        ])
        .sort_values('TOTAL', ascending=False)
    )
    
    # Resetar índice para exibição em streamlit
    pivot_responsavel_display = usuarios_ordenados.reset_index()
    
    # Adicionar coluna de destaque
    pivot_responsavel_display['DESTAQUE'] = pivot_responsavel_display['MOVED_BY_NAME'].isin(usuarios_prioritarios)
    
    # Exibir tabela com a produtividade diária
    st.markdown("### Movimentações Diárias por Responsável")
    st.dataframe(
        pivot_responsavel_display,
        column_config={
            "MOVED_BY_NAME": st.column_config.TextColumn(
                "Responsável",
                help="Nome do responsável pelas movimentações"
            ),
            "TOTAL": st.column_config.NumberColumn(
                "Total",
                help="Total de movimentações no período",
                format="%d"
            ),
            "DESTAQUE": st.column_config.CheckboxColumn(
                "Usuário Prioritário",
                help="Indica se é um usuário prioritário"
            )
        },
        use_container_width=True
    )
    
    # Adicionar explicação da tabela
    st.info("""
    **Como interpretar esta tabela:**
    • Cada linha representa um responsável.
    • As colunas mostram as datas do período analisado.
    • Os valores nas células indicam quantas movimentações cada pessoa realizou em cada dia.
    • A coluna "TOTAL" mostra o total de movimentações de cada responsável no período completo.
    • Os usuários prioritários estão destacados e aparecem primeiro na listagem.
    """)
    
    # Atualizar o gráfico de barras para mostrar os grupos
    total_por_responsavel = usuarios_ordenados.reset_index()[['MOVED_BY_NAME', 'TOTAL']]
    
    # Criar coluna de cores para destacar grupos diferentes
    total_por_responsavel['GRUPO'] = total_por_responsavel['MOVED_BY_NAME'].map(mapeamento_grupo)
    total_por_responsavel['COR'] = total_por_responsavel['GRUPO'].fillna('Outros Usuários')
    
    fig = px.bar(
        total_por_responsavel,
        x='TOTAL',
        y='MOVED_BY_NAME',
        title="Total de Movimentações por Responsável",
        labels={
            'TOTAL': 'Quantidade de Movimentações',
            'MOVED_BY_NAME': 'Responsável',
            'COR': 'Grupo'
        },
        orientation='h',
        color='COR',
        color_discrete_map={
            'Cartório Tatuapé': '#1f77b4',     # Azul escuro
            'Cartório Casa Verde': '#2ca02c',   # Verde
            'Outros Usuários': '#a6cee3'        # Azul claro
        },
        text='TOTAL'
    )

    fig.update_traces(
        textposition='outside',  # Coloca os números fora das barras
        textfont=dict(size=14),  # Aumenta o tamanho da fonte dos números
        cliponaxis=False  # Permite que os números apareçam mesmo fora da área do gráfico
    )

    fig.update_layout(
        height=800,  # Aumentar altura para melhor visualização
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            range=[0, total_por_responsavel['TOTAL'].max() * 1.15]  # Aumenta o espaço para os números
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Adicionar explicação do gráfico
    st.info("""
    **Como interpretar este gráfico:**
    • Mostra o total de movimentações realizadas por cada responsável no período.
    • As barras azuis escuras representam os usuários prioritários.
    • As barras azuis claras representam os demais usuários.
    • As barras mais longas indicam maior volume de trabalho.
    """)
    
    # Adicionar nova seção para análise temporal dos usuários prioritários
    st.markdown("### Movimentações dos Usuários Prioritários ao Longo do Tempo")
    
    # Criar DataFrame apenas com usuários prioritários
    df_prioritarios = df_valido[df_valido['MOVED_BY_NAME'].isin(usuarios_prioritarios)].copy()
    
    # Permitir seleção do período de análise
    col1, col2 = st.columns(2)
    with col1:
        periodo = st.selectbox(
            "Selecione o período de análise:",
            ["Diário", "Semanal", "Mensal"],
            index=0
        )
    
    with col2:
        # Criar lista organizada de usuários por cartório
        opcoes_tatuape = [f"[Tatuapé] {nome}" for nome in GRUPO_TATUAPE.keys()]
        opcoes_casa_verde = [f"[Casa Verde] {nome}" for nome in GRUPO_CASA_VERDE.keys()]
        
        # Combinar as listas mantendo a organização por cartório
        opcoes_selecao = sorted(opcoes_tatuape) + sorted(opcoes_casa_verde)
        
        usuarios_selecionados = st.multiselect(
            "Selecione os usuários para visualizar:",
            options=opcoes_selecao,
            default=sorted(opcoes_casa_verde)[:5]  # Seleciona os 5 primeiros do Casa Verde por padrão
        )
    
    # Criar lista de nomes selecionados para filtrar
    nomes_e_ids_selecionados = set()
    for selecao in usuarios_selecionados:
        # Remover o prefixo do cartório para obter o nome
        nome = selecao.split("] ")[1]
        nomes_e_ids_selecionados.add(nome)
        
        # Adicionar o ID correspondente
        if nome in GRUPO_TATUAPE:
            nomes_e_ids_selecionados.add(GRUPO_TATUAPE[nome])
        elif nome in GRUPO_CASA_VERDE:
            nomes_e_ids_selecionados.add(GRUPO_CASA_VERDE[nome])
    
    # Filtrar pelos usuários selecionados (usando MOVED_BY_NAME original, antes do mapeamento)
    df_plot = df_prioritarios[df_prioritarios['MOVED_BY_NAME'].isin(nomes_e_ids_selecionados)].copy()
    
    if not df_plot.empty:
        # Adicionar colunas de período
        df_plot['DATA'] = df_plot['MOVED_TIME'].dt.date
        df_plot['SEMANA'] = df_plot['MOVED_TIME'].dt.strftime('%Y-%U')
        df_plot['MES'] = df_plot['MOVED_TIME'].dt.strftime('%Y-%m')
        
        # Definir agrupamento baseado no período selecionado
        if periodo == "Diário":
            coluna_tempo = 'DATA'
            formato_data = lambda x: x.strftime('%d/%m/%Y') if hasattr(x, 'strftime') else str(x)
        elif periodo == "Semanal":
            coluna_tempo = 'SEMANA'
            formato_data = lambda x: f"Semana {x.split('-')[1]}/{x.split('-')[0]}"
        else:  # Mensal
            coluna_tempo = 'MES'
            formato_data = lambda x: f"{pd.to_datetime(x + '-01').strftime('%B/%Y')}"
        
        # Agrupar dados
        df_agrupado = df_plot.groupby([coluna_tempo, 'MOVED_BY_NAME']).size().reset_index(name='QUANTIDADE')
        
        # Formatar datas para exibição
        df_agrupado['PERIODO_FORMATADO'] = df_agrupado[coluna_tempo].apply(formato_data)
        
        # Criar gráfico de linhas
        fig = px.line(
            df_agrupado,
            x='PERIODO_FORMATADO',
            y='QUANTIDADE',
            color='MOVED_BY_NAME',
            markers=True,
            title=f"Movimentações {periodo}s por Usuário Prioritário",
            labels={
                'PERIODO_FORMATADO': 'Período',
                'QUANTIDADE': 'Quantidade de Movimentações',
                'MOVED_BY_NAME': 'Responsável'
            }
        )
        
        # Melhorar a formatação do gráfico
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=20, r=20, t=100, b=100),
            yaxis_title="Quantidade de Movimentações",
            xaxis_title="Período",
            plot_bgcolor='white',
            yaxis=dict(
                gridcolor='lightgray',
                gridwidth=1
            ),
            xaxis=dict(
                gridcolor='lightgray',
                gridwidth=1
            )
        )
        
        # Adicionar valores nos pontos
        fig.update_traces(
            textposition="top center",
            texttemplate="%{y}",
            textfont=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Adicionar tabela com os dados
        st.markdown("#### Dados Detalhados")
        
        # Pivot table para mostrar os dados em formato tabular
        pivot = df_agrupado.pivot(
            index='PERIODO_FORMATADO',
            columns='MOVED_BY_NAME',
            values='QUANTIDADE'
        ).fillna(0)
        
        # Adicionar total por período
        pivot['TOTAL'] = pivot.sum(axis=1)
        
        # Resetar índice para exibição
        pivot_display = pivot.reset_index()
        
        # Exibir tabela
        st.dataframe(
            pivot_display,
            column_config={
                "PERIODO_FORMATADO": st.column_config.TextColumn(
                    "Período",
                    help=f"Período {periodo.lower()}"
                ),
                "TOTAL": st.column_config.NumberColumn(
                    "Total",
                    help="Total de movimentações no período",
                    format="%d"
                )
            },
            use_container_width=True
        )
        
        # Adicionar explicação
        st.info(f"""
        **Como interpretar esta visualização:**
        • O gráfico mostra a evolução {periodo.lower()} das movimentações de cada usuário prioritário selecionado.
        • Cada linha representa um usuário, com cores diferentes para fácil identificação.
        • Os pontos mostram os valores exatos em cada período.
        • A tabela abaixo fornece os valores detalhados para cada período.
        • Use os filtros acima para:
          - Alterar a granularidade temporal (Diário/Semanal/Mensal)
          - Selecionar quais usuários deseja visualizar
        """)
    else:
        st.warning("Não há dados para os usuários selecionados no período.")
    
    # Adicionar análise de produtividade por responsável e etapa
    st.markdown("### Movimentações por Responsável e Etapa")
    
    # Agrupar por responsável e estágio
    prod_por_estagio = df_valido.groupby(['MOVED_BY_NAME', coluna_estagio]).size().reset_index(name='QUANTIDADE')
    
    # Pivot table para ver quais etapas cada responsável mais trabalha
    pivot_estagio_resp = prod_por_estagio.pivot_table(
        index='MOVED_BY_NAME',
        columns=coluna_estagio,
        values='QUANTIDADE',
        fill_value=0
    )
    
    # Adicionar coluna de total
    pivot_estagio_resp['TOTAL'] = pivot_estagio_resp.sum(axis=1)
    
    # Ordenar primeiro os usuários prioritários, depois os demais por total
    pivot_estagio_resp = pd.concat([
        pivot_estagio_resp[pivot_estagio_resp.index.isin(usuarios_prioritarios)],
        pivot_estagio_resp[~pivot_estagio_resp.index.isin(usuarios_prioritarios)]
    ]).sort_values('TOTAL', ascending=False)
    
    # Adicionar coluna de destaque
    pivot_display = pivot_estagio_resp.reset_index()
    pivot_display['DESTAQUE'] = pivot_display['MOVED_BY_NAME'].isin(usuarios_prioritarios)
    
    # Exibir tabela
    st.dataframe(
        pivot_display,
        column_config={
            "MOVED_BY_NAME": st.column_config.TextColumn(
                "Responsável",
                help="Nome do responsável pelas movimentações"
            ),
            "TOTAL": st.column_config.NumberColumn(
                "Total",
                help="Total de movimentações",
                format="%d"
            ),
            "DESTAQUE": st.column_config.CheckboxColumn(
                "Usuário Prioritário",
                help="Indica se é um usuário prioritário"
            )
        },
        use_container_width=True
    )
    
    # Adicionar explicação da tabela
    st.info("""
    **Como interpretar esta tabela:**
    • Cada linha representa um responsável.
    • As colunas mostram as diferentes etapas do fluxo de trabalho.
    • Os valores nas células indicam quantas movimentações cada pessoa realizou em cada etapa.
    • A coluna "TOTAL" mostra o total de movimentações de cada responsável.
    • Os usuários prioritários estão destacados e aparecem primeiro na listagem.
    """)
    
    # Gráfico de heatmap focado nos usuários prioritários
    st.markdown("### Especialização dos Usuários Prioritários por Etapa")
    
    # Selecionar apenas usuários prioritários para o heatmap
    pivot_prioritarios = pivot_estagio_resp[pivot_estagio_resp.index.isin(usuarios_prioritarios)].drop(columns=['TOTAL'])
    
    # Normalizar por linha para visualizar percentual por responsável
    pivot_norm = pivot_prioritarios.div(pivot_prioritarios.sum(axis=1), axis=0)
    
    # Criar heatmap
    fig_heat = px.imshow(
        pivot_norm,
        title="Especialização dos Usuários Prioritários por Etapa (% do total de movimentações)",
        labels=dict(x="Etapa", y="Responsável", color="% do Total"),
        color_continuous_scale="Viridis",
        text_auto=".1%"
    )
    
    fig_heat.update_layout(
        height=500,
        xaxis_tickangle=-45,
        margin=dict(l=20, r=20, t=50, b=100)
    )
    
    st.plotly_chart(fig_heat, use_container_width=True)
    
    # Adicionar explicação do mapa de calor
    st.info("""
    **Como interpretar este mapa de calor:**
    • Mostra apenas os usuários prioritários.
    • As cores mais intensas indicam maior concentração de atividade naquela etapa.
    • Os valores mostram o percentual do trabalho total de cada responsável dedicado a cada etapa.
    • Permite identificar especialização: responsáveis que trabalham predominantemente em etapas específicas.
    • Um valor de 80% significa que 80% das movimentações daquela pessoa foram naquela etapa específica.
    """)
    
    # Análise por tipo de documento
    if 'UF_CRM_12_1722534861891' in df_valido.columns:
        st.markdown("### Movimentações por Tipo de Documento")
        
        # Agrupar por responsável e tipo de documento
        prod_tipo_doc = df_valido.groupby(['MOVED_BY_NAME', 'UF_CRM_12_1722534861891']).size().reset_index(name='QUANTIDADE')
        
        # Pivot table para responsáveis nas linhas e tipos de documento nas colunas
        pivot_tipo_doc = prod_tipo_doc.pivot_table(
            index='MOVED_BY_NAME',
            columns='UF_CRM_12_1722534861891',
            values='QUANTIDADE',
            fill_value=0
        )
        
        # Adicionar coluna de total por responsável
        pivot_tipo_doc['TOTAL'] = pivot_tipo_doc.sum(axis=1)
        
        # Ordenar primeiro os usuários prioritários, depois os demais por total
        pivot_tipo_doc = pd.concat([
            pivot_tipo_doc[pivot_tipo_doc.index.isin(usuarios_prioritarios)],
            pivot_tipo_doc[~pivot_tipo_doc.index.isin(usuarios_prioritarios)]
        ]).sort_values('TOTAL', ascending=False)
        
        # Adicionar coluna de destaque
        pivot_tipo_doc_display = pivot_tipo_doc.reset_index()
        pivot_tipo_doc_display['DESTAQUE'] = pivot_tipo_doc_display['MOVED_BY_NAME'].isin(usuarios_prioritarios)
        
        # Exibir tabela
        st.dataframe(
            pivot_tipo_doc_display,
            column_config={
                "MOVED_BY_NAME": st.column_config.TextColumn(
                    "Responsável",
                    help="Nome do responsável pelas movimentações"
                ),
                "TOTAL": st.column_config.NumberColumn(
                    "Total",
                    help="Total de movimentações",
                    format="%d"
                ),
                "DESTAQUE": st.column_config.CheckboxColumn(
                    "Usuário Prioritário",
                    help="Indica se é um usuário prioritário"
                )
            },
            use_container_width=True
        )
        
        # Adicionar explicação da tabela
        st.info("""
        **Como interpretar esta tabela:**
        • Cada linha representa um responsável.
        • As colunas mostram os diferentes tipos de documento (Nascimento, Casamento, Óbito, etc).
        • Os valores nas células indicam quantas movimentações cada pessoa realizou para cada tipo de documento.
        • A coluna "TOTAL" mostra o total geral de movimentações de cada responsável.
        • Os usuários prioritários estão destacados e aparecem primeiro na listagem.
        """)
        
        # Criar gráfico de barras empilhadas apenas para usuários prioritários
        st.markdown("### Distribuição de Tipos de Documento por Usuário Prioritário")
        
        # Transformar dados para formato adequado para plotly
        pivot_melt = pd.melt(
            pivot_tipo_doc[pivot_tipo_doc.index.isin(usuarios_prioritarios)].reset_index(),
            id_vars=['MOVED_BY_NAME'],
            value_vars=[col for col in pivot_tipo_doc.columns if col != 'TOTAL'],
            var_name='TIPO_DOCUMENTO',
            value_name='QUANTIDADE'
        )
        
        fig_tipo_doc = px.bar(
            pivot_melt,
            x='MOVED_BY_NAME',
            y='QUANTIDADE',
            color='TIPO_DOCUMENTO',
            title="Movimentações por Tipo de Documento - Usuários Prioritários",
            labels={
                'MOVED_BY_NAME': 'Responsável',
                'QUANTIDADE': 'Quantidade',
                'TIPO_DOCUMENTO': 'Tipo de Documento'
            },
            barmode='stack'
        )
        
        fig_tipo_doc.update_layout(
            xaxis_tickangle=-45,
            height=600,
            margin=dict(l=20, r=20, t=50, b=100),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig_tipo_doc, use_container_width=True)
        
        # Adicionar explicação do gráfico
        st.info("""
        **Como interpretar este gráfico:**
        • Mostra apenas os usuários prioritários.
        • Cada barra representa um responsável.
        • As cores indicam diferentes tipos de documento.
        • A altura total da barra mostra o volume total de movimentações do responsável.
        • A proporção de cada cor mostra a distribuição do trabalho por tipo de documento.
        • Útil para identificar especialização por tipo de documento entre os usuários prioritários.
        """)
    else:
        st.warning("Campo 'UF_CRM_12_1722534861891' (Tipo de documento) não encontrado para análise por tipo de documento.") 