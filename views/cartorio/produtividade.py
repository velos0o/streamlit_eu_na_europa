import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def formatar_nome_etapa(campo):
    """
    Formata o nome de uma etapa do processo, removendo prefixos e substituindo underscores por espaços
    
    Args:
        campo (str): Nome do campo original
        
    Returns:
        str: Nome formatado da etapa
    """
    # Mapeamento das etapas para os novos nomes conforme solicitado
    mapeamento_etapas = {
        'UF_CRM_DATA_SOLICITAR_REQUERIMENTO': 'Deu ganho na Busca',
        'UF_CRM_DEVOLUTIVA_BUSCA': 'Deu perca na Busca',
        'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM': 'Requerimento Montado',
        'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM_PRIORIDADE': 'Requerimento Montado',
        'UF_CRM_DATA_AGUARDANDOCARTORIO_ORIGEM': 'Solicitado ao Cartório Origem',
        'UF_CRM_DEVOLUCAO_ADM': 'DEVOLUÇÃO ADM',
        'UF_CRM_DEVOLUCAO_ADM_VERIFICADO': 'DEVOLUÇÃO ADM VERIFICADO',
        'UF_CRM_SOLICITACAO_DUPLICADO': 'SOLICITAÇÃO DUPLICADA'
    }
    
    # Verificar se o campo está no mapeamento
    if campo in mapeamento_etapas:
        return mapeamento_etapas[campo]
    
    # Caso contrário, usar a formatação padrão
    nome = campo.replace('UF_CRM_DATA_', '').replace('UF_CRM_', '')
    # Garantir que todos os underlines são substituídos por espaços
    while '_' in nome:
        nome = nome.replace('_', ' ')
    return nome.title()

def analisar_produtividade_etapas(df):
    """
    Análise de produtividade baseada nas datas de cada etapa do processo
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos cartórios
    """
    # Lista de campos de datas para análise
    campos_data = [
        'UF_CRM_DATA_AGUARDANDOCARTORIO_ORIGEM',
        'UF_CRM_DATA_CERTIDAO_EMITIDA',
        'UF_CRM_DATA_CERTIDAO_FISICA_ENTREGUE',
        'UF_CRM_DATA_CERTIDAO_FISICA_ENVIADA',
        'UF_CRM_DATA_MONTAR_REQUERIMENTO',
        'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM',
        # Removemos UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM_PRIORIDADE da lista para processá-lo especialmente
        'UF_CRM_DATA_SOLICITAR_REQUERIMENTO',
        'UF_CRM_DEVOLUCAO_ADM',
        'UF_CRM_DEVOLUCAO_ADM_VERIFICADO',
        'UF_CRM_DEVOLUTIVA_BUSCA',
        'UF_CRM_DEVOLUTIVA_REQUERIMENTO',
        'UF_CRM_SOLICITACAO_DUPLICADO'
    ]
    
    # Verificar se temos as colunas necessárias para a análise
    colunas_faltantes = [col for col in campos_data if col not in df.columns]
    if colunas_faltantes:
        st.warning(f"Algumas colunas de datas não foram encontradas: {', '.join(colunas_faltantes)}")
        campos_data = [col for col in campos_data if col in df.columns]
    
    # Colunas para consolidar em uma única métrica
    campo_origem = 'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM'
    campo_origem_prioridade = 'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM_PRIORIDADE'
    
    # Consolidar dados de UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM_PRIORIDADE em UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM
    if campo_origem in df.columns and campo_origem_prioridade in df.columns:
        # Criar cópia para não modificar o original
        df = df.copy()
        
        # Onde UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM é nulo mas UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM_PRIORIDADE não é,
        # copie o valor de PRIORIDADE para o campo regular
        mascara = df[campo_origem].isna() & ~df[campo_origem_prioridade].isna()
        df.loc[mascara, campo_origem] = df.loc[mascara, campo_origem_prioridade]
        
        # Adicionar o campo_origem à lista de campos se ainda não estiver
        if campo_origem not in campos_data:
            campos_data.append(campo_origem)
            
    if not campos_data:
        st.error("Nenhuma coluna de data necessária para análise foi encontrada.")
        return
    
    st.markdown("## Análise de Produtividade por Etapas")
    st.info("""
    **O que é a Análise de Produtividade por Etapas?**
    • Esta análise mostra os registros de datas e horas para cada etapa do processo.
    • Permite identificar a velocidade de processamento, produtividade e distribuição do trabalho.
    • Os dados são exibidos por dia, semana e mês para facilitar diferentes níveis de análise.
    """)
    
    # Converter todas as colunas de data para datetime
    for campo in campos_data:
        df[campo] = pd.to_datetime(df[campo], errors='coerce')
    
    # Aplicar filtros para análise
    st.markdown("### Filtros de Produtividade")
    
    # Filtro de período no topo da página
    hoje = datetime.now()
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input(
            "Data Inicial",
            value=hoje - timedelta(days=30),
            max_value=hoje,
            key="prod_data_inicio"
        )
    with col2:
        data_fim = st.date_input(
            "Data Final",
            value=hoje,
            max_value=hoje,
            min_value=data_inicio,
            key="prod_data_fim"
        )
    
    # Filtro de responsável se existir a coluna
    responsavel_selecionado = None
    if 'ASSIGNED_BY_NAME' in df.columns:
        responsaveis = df['ASSIGNED_BY_NAME'].dropna().unique().tolist()
        responsavel_selecionado = st.multiselect(
            "Responsável",
            options=responsaveis,
            default=[],
            key="prod_responsavel"
        )
    
    # Explicação sobre filtros
    with st.expander("Sobre os Filtros", expanded=False):
        st.markdown("""
        **Como usar os filtros:**
        • **Data Inicial e Final**: Selecione o período que deseja analisar.
        • **Responsável**: Filtre pelos colaboradores responsáveis (se disponível).
        
        Todos os filtros são aplicados em conjunto (operação AND).
        """)
    
    # Preparar dados filtrados para o período selecionado
    periodo_inicio = pd.to_datetime(data_inicio)
    periodo_fim = pd.to_datetime(data_fim) + timedelta(days=1) - timedelta(seconds=1)
    
    # Criar dataframe apenas com as colunas de data e informações relevantes
    colunas_selecionadas = campos_data.copy()
    colunas_info = ['ID', 'TITLE', 'ASSIGNED_BY_NAME', 'UF_CRM_12_1723552666'] if 'UF_CRM_12_1723552666' in df.columns else ['ID', 'TITLE']
    
    for col in colunas_info:
        if col in df.columns:
            colunas_selecionadas.append(col)
    
    df_analise = df[colunas_selecionadas].copy()
    
    # Filtra por responsável se selecionado
    if responsavel_selecionado and 'ASSIGNED_BY_NAME' in df_analise.columns:
        df_analise = df_analise[df_analise['ASSIGNED_BY_NAME'].isin(responsavel_selecionado)]
    
    # Preparar para filtragem por data
    df_filtrado = df_analise.copy()
    
    # Processar filtragem por data
    dfs_por_campo = []
    registros_filtrados = set()  # Para guardar IDs únicos
    
    if not df_filtrado.empty:
        for campo in campos_data:
            if campo not in df_filtrado.columns:
                continue
                
            # Filtrar registros com data no período para este campo
            filtro_campo = (df_filtrado[campo] >= periodo_inicio) & (df_filtrado[campo] <= periodo_fim)
            df_campo = df_filtrado[filtro_campo].copy()
            
            if not df_campo.empty:
                # Adicionar ao conjunto de IDs únicos se a coluna ID existir
                if 'ID' in df_campo.columns:
                    registros_filtrados.update(df_campo['ID'].unique())
                dfs_por_campo.append(df_campo)
        
        # Unir todos os dataframes filtrados preservando todas as colunas
        if dfs_por_campo:
            # Preservar todas as colunas no dataframe unido, mantendo os dados originais
            if 'ID' in df_filtrado.columns:
                # Se temos a coluna ID, podemos filtrar por IDs mais facilmente
                df_filtrado = df_filtrado[df_filtrado['ID'].isin(registros_filtrados)]
            else:
                # Caso contrário, fazer merge manual
                df_filtrado = pd.concat(dfs_por_campo).drop_duplicates()
        else:
            st.warning("Nenhum registro encontrado no período selecionado.")
            df_filtrado = pd.DataFrame()
    else:
        df_filtrado = pd.DataFrame()
    
    if df_filtrado.empty:
        st.warning("Não há dados disponíveis para o período e filtros selecionados.")
        return
    
    # Criar abas para diferentes visões
    tab_metricas, tab_grafico_diario, tab_dia, tab_semana, tab_mes, tab_responsavel = st.tabs([
        "Métricas por Etapa",
        "Evolução Diária",
        "Visão Diária", 
        "Visão Semanal", 
        "Visão Mensal",
        "Por Responsável"
    ])
    
    # Aba de métricas por etapa
    with tab_metricas:
        mostrar_metricas_etapa(df_filtrado, campos_data, periodo_inicio, periodo_fim)
    
    # Aba de gráfico diário
    with tab_grafico_diario:
        mostrar_grafico_diario(df_filtrado, campos_data)
    
    # Aba de visão diária
    with tab_dia:
        mostrar_visao_produtividade(df_filtrado, campos_data, 'Diária', 'D')
    
    # Aba de visão semanal
    with tab_semana:
        mostrar_visao_produtividade(df_filtrado, campos_data, 'Semanal', 'W')
    
    # Aba de visão mensal
    with tab_mes:
        mostrar_visao_produtividade(df_filtrado, campos_data, 'Mensal', 'M')
    
    # Aba de análise por responsável
    with tab_responsavel:
        if 'ASSIGNED_BY_NAME' in df_filtrado.columns:
            analisar_produtividade_responsavel(df_filtrado, campos_data)
        else:
            st.info("Dados de responsável não disponíveis para análise.")

def mostrar_metricas_etapa(df, campos_data, periodo_inicio, periodo_fim):
    """
    Mostra as métricas de produtividade por etapa
    
    Args:
        df (pandas.DataFrame): DataFrame com dados filtrados
        campos_data (list): Lista de campos de data para análise
        periodo_inicio (datetime): Data inicial do período
        periodo_fim (datetime): Data final do período
    """
    # Adicionar estilo visual para a seção
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1976D2 0%, #64B5F6 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h3 style="margin-top: 0; color: white; font-size: 22px; font-weight: 700; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); color: #FFFFFF !important;">
            📊 MÉTRICAS DE PRODUTIVIDADE POR ETAPA
        </h3>
        <p style="margin-bottom: 0; font-size: 14px; color: rgba(255,255,255,0.9); text-align: center; color: #FFFFFF !important;">
            Resumo das principais métricas de produtividade para cada etapa do processo.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar e exibir informações sobre as colunas existentes
    colunas_existentes = [col for col in campos_data if col in df.columns]
    colunas_faltantes = [col for col in campos_data if col not in df.columns]
    
    if colunas_faltantes:
        st.warning(f"**Atenção:** Alguns campos não estão disponíveis nos dados: {', '.join(colunas_faltantes)}")
    
    # Calcular dados para cada campo
    dados_campos = {}
    dias_com_atividade = set()
    total_geral = 0
    
    # Guardar IDs para verificar registros únicos
    ids_por_etapa = {}
    todos_ids = set()
    
    for campo in colunas_existentes:
        # Obter série temporal filtrada
        serie_data = df[campo].dropna()
        
        # Verificar se o campo tem algum dado
        if serie_data.empty:
            continue
            
        # Nome amigável para o campo
        nome_etapa = formatar_nome_etapa(campo)
        
        # Calcular estatísticas básicas
        total = len(serie_data)
        total_geral += total
        
        # Guardar IDs únicos para esta etapa
        if 'ID' in df.columns:
            ids_etapa = set(df.loc[~df[campo].isna(), 'ID'].unique())
            ids_por_etapa[nome_etapa] = ids_etapa
            todos_ids.update(ids_etapa)
        
        # Calcular dados temporais
        if not serie_data.empty:
            datas_unicas = set(serie_data.dt.date)
            dias_com_atividade.update(datas_unicas)
            
            # Agrupar por dia
            contagem_diaria = serie_data.dt.date.value_counts().sort_index()
            
            # Encontrar dia com maior produtividade
            if not contagem_diaria.empty:
                dia_max = contagem_diaria.idxmax()
                valor_max = contagem_diaria.max()
                
                # Calcular média diária (apenas para dias em que houve atividade)
                media_diaria = total / len(contagem_diaria)
                
                # Guardar estatísticas
                dados_campos[nome_etapa] = {
                    'total': total,
                    'dia_max': dia_max,
                    'valor_max': valor_max,
                    'media_diaria': media_diaria,
                    'num_dias': len(contagem_diaria),
                    'campo_original': campo
                }
    
    # Se não houver dados, mostra mensagem e sai
    if not dados_campos:
        st.warning("Não há dados disponíveis para análise no período selecionado.")
        return
    
    # Adicionar etapa "Busca Realizada" que é a soma de "Deu ganho na Busca" e "Deu perca na Busca"
    if "Deu ganho na Busca" in dados_campos and "Deu perca na Busca" in dados_campos:
        ganho_busca = dados_campos["Deu ganho na Busca"]["total"]
        perca_busca = dados_campos["Deu perca na Busca"]["total"]
        total_busca = ganho_busca + perca_busca
        
        # Calcular dia máximo e valor máximo combinados
        # Para simplificar, usamos o maior valor entre os dois
        dia_max_ganho = dados_campos["Deu ganho na Busca"]["dia_max"]
        dia_max_perca = dados_campos["Deu perca na Busca"]["dia_max"]
        valor_max_ganho = dados_campos["Deu ganho na Busca"]["valor_max"]
        valor_max_perca = dados_campos["Deu perca na Busca"]["valor_max"]
        
        if valor_max_ganho >= valor_max_perca:
            dia_max_busca = dia_max_ganho
            valor_max_busca = valor_max_ganho
        else:
            dia_max_busca = dia_max_perca
            valor_max_busca = valor_max_perca
        
        # Calcular número de dias combinados
        dias_ganho = dados_campos["Deu ganho na Busca"]["num_dias"]
        dias_perca = dados_campos["Deu perca na Busca"]["num_dias"]
        dias_total = max(dias_ganho, dias_perca)  # Estimativa conservadora
        
        # Média diária combinada
        media_diaria_busca = total_busca / dias_total if dias_total > 0 else 0
        
        # Adicionar aos dados
        dados_campos["Busca Realizada"] = {
            'total': total_busca,
            'dia_max': dia_max_busca,
            'valor_max': valor_max_busca,
            'media_diaria': media_diaria_busca,
            'num_dias': dias_total,
            'campo_original': 'UF_CRM_BUSCA_REALIZADA'  # Campo virtual
        }
        
        # Incluir no total geral
        total_geral += total_busca
        
        # Incluir IDs
        if "Deu ganho na Busca" in ids_por_etapa and "Deu perca na Busca" in ids_por_etapa:
            ids_busca = ids_por_etapa["Deu ganho na Busca"].union(ids_por_etapa["Deu perca na Busca"])
            ids_por_etapa["Busca Realizada"] = ids_busca
    
    # Calcular métricas gerais
    num_dias_periodo = (periodo_fim.date() - periodo_inicio.date()).days + 1
    num_dias_com_atividade = len(dias_com_atividade)
    taxa_dias_ativos = num_dias_com_atividade / num_dias_periodo * 100
    
    # Métricas gerais no topo com estilo aprimorado
    st.markdown("""
    <div style="background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h4 style="color: #1565C0; margin-top: 0; font-size: 18px; border-bottom: 2px solid #1976D2; padding-bottom: 8px; margin-bottom: 15px;">
            📈 Métricas Gerais
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Cores para as métricas
    col1, col2, col3 = st.columns(3)
    
    # Cores para os cards
    cores_cards = ["#1E88E5", "#43A047", "#E53935"]
    icones_cards = ["📊", "📅", "📈"]
    titulos_cards = ["Total de Atividades", "Dias com Atividades", "Média Diária"]
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {cores_cards[0]} 0%, #64B5F6 100%); border-radius: 10px; padding: 15px; color: white; text-align: center; height: 130px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="margin:0; font-size: 16px; opacity: 0.9; color: #FFFFFF !important;">{icones_cards[0]} {titulos_cards[0]}</h4>
            <p style="font-size: 36px; font-weight: bold; margin: 10px 0; color: #FFFFFF !important;">{total_geral:,}</p>
            <p style="font-size: 12px; margin: 0; opacity: 0.8; color: #FFFFFF !important;">Total em todas as etapas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {cores_cards[1]} 0%, #81C784 100%); border-radius: 10px; padding: 15px; color: white; text-align: center; height: 130px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="margin:0; font-size: 16px; opacity: 0.9; color: #FFFFFF !important;">{icones_cards[1]} {titulos_cards[1]}</h4>
            <p style="font-size: 36px; font-weight: bold; margin: 10px 0; color: #FFFFFF !important;">{num_dias_com_atividade} <span style="font-size: 16px; color: #FFFFFF !important;">de {num_dias_periodo}</span></p>
            <p style="font-size: 12px; margin: 0; opacity: 0.8; color: #FFFFFF !important;">{taxa_dias_ativos:.0f}% do período</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        media_valor = total_geral/num_dias_com_atividade if num_dias_com_atividade > 0 else 0
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {cores_cards[2]} 0%, #EF5350 100%); border-radius: 10px; padding: 15px; color: white; text-align: center; height: 130px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="margin:0; font-size: 16px; opacity: 0.9; color: #FFFFFF !important;">{icones_cards[2]} {titulos_cards[2]}</h4>
            <p style="font-size: 36px; font-weight: bold; margin: 10px 0; color: #FFFFFF !important;">{media_valor:.1f}</p>
            <p style="font-size: 12px; margin: 0; opacity: 0.8; color: #FFFFFF !important;">Atividades por dia</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Exibir informações sobre a contagem
    if 'ID' in df.columns:
        st.markdown(f"""
        <div style="background-color: #e8f4fd; border-left: 4px solid #1976D2; padding: 12px; margin: 20px 0; border-radius: 4px; font-size: 14px;">
            <p style="margin: 0;"><strong>Informações sobre a contagem:</strong></p>
            <ul style="margin: 5px 0 0 20px; padding: 0;">
                <li>Total de registros únicos: <strong>{len(todos_ids)}</strong></li>
                <li>Total de atividades somadas: <strong>{total_geral}</strong></li>
                <li>A diferença ocorre porque um mesmo registro pode estar em múltiplas etapas.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Seção de métricas para o grupo Pesquisa
    st.markdown("""
    <div style="background: #f8f9fa; border-radius: 10px; padding: 15px; margin: 25px 0 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h4 style="color: #1565C0; margin-top: 0; font-size: 18px; border-bottom: 2px solid #1976D2; padding-bottom: 8px; margin-bottom: 15px;">
            🔍 Métricas de Pesquisa
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Dicionário com descrições explicativas para cada métrica
    descricoes_metricas = {
        'Deu ganho na Busca': 'Pesquisas realizadas com sucesso, onde o documento foi encontrado, permitindo avançar com o processo.',
        'Deu perca na Busca': 'Pesquisas onde o documento não foi encontrado, interrompendo o fluxo normal do processo.',
        'Busca Realizada': 'Total de pesquisas realizadas, incluindo as bem sucedidas e as que não tiveram sucesso.',
        'Requerimento Montado': 'Documentação preparada e organizada após pesquisa bem sucedida, prontos para solicitação ao cartório.',
        'Solicitado ao Cartório Origem': 'Requerimento já enviado formalmente ao cartório onde o documento está registrado, aguardando retorno.',
        'DEVOLUÇÃO ADM': 'Processos que foram devolvidos por questões administrativas e precisam de revisão ou correção.',
        'DEVOLUÇÃO ADM VERIFICADO': 'Processos devolvidos que já foram analisados pela administração e estão sendo processados.',
        'SOLICITAÇÃO DUPLICADA': 'Solicitações identificadas como duplicadas de processos já existentes no sistema.',
        'Certidão Emitida': 'Documento oficial foi emitido pelo cartório e recebido pela equipe.',
        'Certidão Física Entregue': 'Documento físico já foi entregue ao solicitante final.',
        'Certidão Física Enviada': 'Documento físico foi enviado mas ainda não foi confirmada a entrega ao destinatário.',
    }
    
    # Criar cards para métricas de pesquisa
    if "Deu ganho na Busca" in dados_campos and "Deu perca na Busca" in dados_campos and "Busca Realizada" in dados_campos:
        ganho_busca = dados_campos["Deu ganho na Busca"]["total"]
        perca_busca = dados_campos["Deu perca na Busca"]["total"]
        total_busca = dados_campos["Busca Realizada"]["total"]
        
        # Taxa de sucesso
        taxa_sucesso = (ganho_busca / total_busca * 100) if total_busca > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #43A047 0%, #81C784 100%); border-radius: 10px; padding: 15px; color: white; text-align: center; height: 160px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="margin:0; font-size: 16px; opacity: 0.9; color: #FFFFFF !important;">💹 Ganhos de Pesquisa</h4>
                <p style="font-size: 36px; font-weight: bold; margin: 10px 0; color: #FFFFFF !important;">{ganho_busca:,}</p>
                <p style="font-size: 12px; margin: 0; opacity: 0.8; color: #FFFFFF !important;">{taxa_sucesso:.1f}% de sucesso</p>
                <p style="font-size: 11px; margin-top: 5px; opacity: 0.9; color: #FFFFFF !important;">Pesquisas com resultados positivos</p>
                <p style="font-size: 10px; margin-top: 5px; opacity: 0.8; color: #FFFFFF !important;">{descricoes_metricas["Deu ganho na Busca"]}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #E53935 0%, #EF5350 100%); border-radius: 10px; padding: 15px; color: white; text-align: center; height: 160px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="margin:0; font-size: 16px; opacity: 0.9; color: #FFFFFF !important;">📉 Percas de Pesquisa</h4>
                <p style="font-size: 36px; font-weight: bold; margin: 10px 0; color: #FFFFFF !important;">{perca_busca:,}</p>
                <p style="font-size: 12px; margin: 0; opacity: 0.8; color: #FFFFFF !important;">{100-taxa_sucesso:.1f}% de insucesso</p>
                <p style="font-size: 11px; margin-top: 5px; opacity: 0.9; color: #FFFFFF !important;">Pesquisas sem resultados encontrados</p>
                <p style="font-size: 10px; margin-top: 5px; opacity: 0.8; color: #FFFFFF !important;">{descricoes_metricas["Deu perca na Busca"]}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1976D2 0%, #64B5F6 100%); border-radius: 10px; padding: 15px; color: white; text-align: center; height: 160px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="margin:0; font-size: 16px; opacity: 0.9; color: #FFFFFF !important;">Busca Realizada</h4>
                <p style="font-size: 36px; font-weight: bold; margin: 10px 0; color: #FFFFFF !important;">{total_busca:,}</p>
                <p style="font-size: 12px; margin: 0; opacity: 0.8; color: #FFFFFF !important;">Total realizado</p>
                <p style="font-size: 11px; margin-top: 5px; opacity: 0.9; color: #FFFFFF !important;">Soma de ganhos e percas ({ganho_busca:,} + {perca_busca:,})</p>
                <p style="font-size: 10px; margin-top: 5px; opacity: 0.8; color: #FFFFFF !important;">{descricoes_metricas["Busca Realizada"]}</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Adicionar explicação sobre a lógica das métricas de busca
        st.markdown("""
        <div style="background-color: #f0f7ff; border-radius: 8px; padding: 15px; margin-top: 20px; border-left: 5px solid #1976D2;">
            <h5 style="margin-top: 0; color: #1565C0; font-size: 16px;">📋 Explicação Detalhada das Métricas de Busca</h5>
        </div>
        """, unsafe_allow_html=True)
        
        # Usar componentes nativos do Streamlit em vez de HTML complexo
        st.subheader("Lógica de contagem das métricas de busca:")
        
        # Criar as explicações das métricas com markdown nativo
        st.markdown(f"""
        * **Deu ganho na Busca ({ganho_busca:,})**: Representa o número de pesquisas que foram realizadas com sucesso, ou seja, encontraram o que estava sendo buscado. Cada registro contabilizado nesta métrica indica uma busca que teve resultado positivo, gerando valor para o processo.
        
        * **Deu perca na Busca ({perca_busca:,})**: Representa o número de pesquisas que não tiveram sucesso, ou seja, não encontraram resultados satisfatórios. Estas são buscas válidas e completas, mas que não retornaram os dados esperados.
        
        * **Busca Realizada ({total_busca:,})**: Representa o total de buscas realizadas no período, incluindo tanto as bem-sucedidas quanto as mal-sucedidas. É calculada pela soma das buscas com ganho e com perca ({ganho_busca:,} + {perca_busca:,}).
        """)
        
        st.markdown(f"""
        A **Taxa de Sucesso** é calculada dividindo o número de ganhos pelo total de buscas realizadas: {ganho_busca:,} ÷ {total_busca:,} = {taxa_sucesso:.1f}%
        """)
        
        st.subheader("Importância destas métricas:")
        
        st.markdown("""
        * Uma **alta taxa de sucesso** indica eficiência no processo de busca e qualidade nas informações utilizadas para realizar as pesquisas.
        
        * Um **alto volume de buscas** com **baixa taxa de sucesso** pode indicar necessidade de aprimoramento nos critérios ou métodos de busca.
        
        * Estas métricas ajudam a identificar oportunidades de melhoria e a mensurar a efetividade do processo de pesquisa ao longo do tempo.
        """)
    else:
        st.info("Dados de pesquisa não disponíveis para o período selecionado.")
    
    # Seção de métricas por etapa com estilo aprimorado
    st.markdown("""
    <div style="background: #f8f9fa; border-radius: 10px; padding: 15px; margin: 25px 0 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h4 style="color: #1565C0; margin-top: 0; font-size: 18px; border-bottom: 2px solid #1976D2; padding-bottom: 8px; margin-bottom: 15px;">
            🔍 Produtividade por Etapa
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Definir cores para as etapas - cores mais próximas e harmônicas
    cores_etapas = [
        "#1976D2", "#1E88E5", "#2196F3", "#42A5F5", "#64B5F6", 
        "#2979FF", "#2962FF", "#3949AB", "#3F51B5", "#5C6BC0", 
        "#536DFE", "#5677FC", "#7986CB"
    ]
    
    # Organizar campos em ordem de maior volume
    campos_ordenados = sorted(dados_campos.keys(), key=lambda x: dados_campos[x]['total'], reverse=True)
    
    # Etapas a excluir da visualização de Produtividade por Etapa
    etapas_excluir = ["Busca Realizada", "Deu ganho na Busca", "Deu perca na Busca"]
    
    # Filtrar campos ordenados para excluir as etapas especificadas
    campos_ordenados = [campo for campo in campos_ordenados if campo not in etapas_excluir]
    
    # Identificar etapas de perda para destacar em vermelho
    etapas_perda = ["DEVOLUÇÃO ADM", "DEVOLUÇÃO ADM VERIFICADO", "SOLICITAÇÃO DUPLICADA"]
    
    # Separar etapas de perda das demais
    campos_perda = [campo for campo in campos_ordenados if campo in etapas_perda]
    campos_regulares = [campo for campo in campos_ordenados if campo not in etapas_perda]
    
    # Definir número de colunas
    NUM_COLUNAS = 3
    
    # Seção para etapas regulares
    if campos_regulares:
        
        # Criar linhas de cards para etapas regulares
        for i in range(0, len(campos_regulares), NUM_COLUNAS):
            # Obter o grupo de etapas para esta linha
            etapas_linha = campos_regulares[i:i+NUM_COLUNAS]
            
            # Criar colunas
            cols = st.columns(NUM_COLUNAS)
            
            # Preencher cada coluna
            for j, etapa in enumerate(etapas_linha):
                if j < len(cols):  # Verificar se ainda há colunas disponíveis
                    with cols[j]:
                        dados = dados_campos[etapa]
                        cor_index = i + j % len(cores_etapas)
                        cor_etapa = cores_etapas[cor_index % len(cores_etapas)]
                        
                        # Usar componentes nativos do Streamlit em vez de HTML complexo
                        with st.container():
                            # Card principal com borda colorida
                            st.markdown(f"""
                            <div style="border: 2px solid {cor_etapa}; border-radius: 10px; overflow: hidden; margin-bottom: 20px;">
                                <div style="background-color: {cor_etapa}; color: white; padding: 15px; text-align: center;">
                                    <h4 style="margin: 0; font-size: 16px; font-weight: 700;">{etapa.replace('_', ' ')}</h4>
                                    <p style="font-size: 38px; font-weight: 800; margin: 8px 0;">{dados['total']:,}</p>
                                    <p style="font-size: 12px; margin: 0;">Total de registros</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Descrição como texto normal
                            st.markdown(f"**Descrição:** {descricoes_metricas.get(etapa, '')}")
                            
                            # Estatísticas usando colunas nativas do Streamlit
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown(f"""
                                <div style="background-color: #f0f7ff; padding: 10px; border-radius: 5px; text-align: center;">
                                    <p style="margin: 0; font-size: 12px; color: #555; font-weight: 600;">Média por Dia Ativo</p>
                                    <p style="font-size: 20px; font-weight: bold; margin: 5px 0; color: {cor_etapa};">{dados['media_diaria']:.1f}</p>
                                    <p style="font-size: 11px; margin: 0; color: #555;">{dados['num_dias']} dias ativos</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col_b:
                                st.markdown(f"""
                                <div style="background-color: #f0f7ff; padding: 10px; border-radius: 5px; text-align: center;">
                                    <p style="margin: 0; font-size: 12px; color: #555; font-weight: 600;">Dia mais Produtivo</p>
                                    <p style="font-size: 20px; font-weight: bold; margin: 5px 0; color: {cor_etapa};">{dados['dia_max'].strftime('%d/%m')}</p>
                                    <p style="font-size: 11px; margin: 0; color: #555;">{dados['valor_max']} registros</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Registros únicos como texto normal
                            if 'ID' in df.columns and etapa in ids_por_etapa:
                                num_ids = len(ids_por_etapa[etapa])
                                st.markdown(f"**Registros únicos:** {num_ids}")
    
    # Seção para etapas de perda (em vermelho)
    if campos_perda:
        st.markdown("""
        <div style="background: #ffebee; border-radius: 10px; padding: 15px; margin: 25px 0 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <h4 style="color: #c62828; margin-top: 0; font-size: 18px; border-bottom: 2px solid #e53935; padding-bottom: 8px; margin-bottom: 15px;">
                ⚠️ Devoluções e Duplicações
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Criar linhas de cards para etapas de perda
        for i in range(0, len(campos_perda), NUM_COLUNAS):
            # Obter o grupo de etapas para esta linha
            etapas_linha = campos_perda[i:i+NUM_COLUNAS]
            
            # Criar colunas
            cols = st.columns(NUM_COLUNAS)
            
            # Preencher cada coluna
            for j, etapa in enumerate(etapas_linha):
                if j < len(cols):  # Verificar se ainda há colunas disponíveis
                    with cols[j]:
                        dados = dados_campos[etapa]
                        cor_etapa = "#E53935"  # Vermelho para todas as etapas de perda
                        
                        # Usar componentes nativos do Streamlit em vez de HTML complexo
                        with st.container():
                            # Card principal com borda colorida
                            st.markdown(f"""
                            <div style="border: 2px solid {cor_etapa}; border-radius: 10px; overflow: hidden; margin-bottom: 20px;">
                                <div style="background-color: {cor_etapa}; color: white; padding: 15px; text-align: center;">
                                    <h4 style="margin: 0; font-size: 16px; font-weight: 700;">{etapa.replace('_', ' ')}</h4>
                                    <p style="font-size: 38px; font-weight: 800; margin: 8px 0;">{dados['total']:,}</p>
                                    <p style="font-size: 12px; margin: 0;">Total de registros</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Descrição como texto normal
                            st.markdown(f"**Descrição:** {descricoes_metricas.get(etapa, '')}")
                            
                            # Estatísticas usando colunas nativas do Streamlit
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown(f"""
                                <div style="background-color: #fff5f5; padding: 10px; border-radius: 5px; text-align: center;">
                                    <p style="margin: 0; font-size: 12px; color: #555; font-weight: 600;">Média por Dia Ativo</p>
                                    <p style="font-size: 20px; font-weight: bold; margin: 5px 0; color: {cor_etapa};">{dados['media_diaria']:.1f}</p>
                                    <p style="font-size: 11px; margin: 0; color: #555;">{dados['num_dias']} dias ativos</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col_b:
                                st.markdown(f"""
                                <div style="background-color: #fff5f5; padding: 10px; border-radius: 5px; text-align: center;">
                                    <p style="margin: 0; font-size: 12px; color: #555; font-weight: 600;">Dia mais Produtivo</p>
                                    <p style="font-size: 20px; font-weight: bold; margin: 5px 0; color: {cor_etapa};">{dados['dia_max'].strftime('%d/%m')}</p>
                                    <p style="font-size: 11px; margin: 0; color: #555;">{dados['valor_max']} registros</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Registros únicos como texto normal
                            if 'ID' in df.columns and etapa in ids_por_etapa:
                                num_ids = len(ids_por_etapa[etapa])
                                st.markdown(f"**Registros únicos:** {num_ids}")
    
    # Criar tabela de resumo com estilo aprimorado
    st.markdown("""
    <div style="background: #f8f9fa; border-radius: 10px; padding: 15px; margin: 25px 0 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h4 style="color: #1565C0; margin-top: 0; font-size: 18px; border-bottom: 2px solid #1976D2; padding-bottom: 8px; margin-bottom: 15px;">
            📋 Resumo Consolidado
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Criar dataframe de resumo
    df_resumo = pd.DataFrame([
        {
            'Etapa': etapa,
            'Total': dados['total'],
            'Média Diária': round(dados['media_diaria'], 1),
            'Dia Mais Produtivo': dados['dia_max'].strftime('%d/%m/%Y'),
            'Máximo em Um Dia': dados['valor_max'],
            'Dias Com Atividade': dados['num_dias'],
            'Percentual': dados['total'] / total_geral * 100 if total_geral > 0 else 0,
            'Registros Únicos': len(ids_por_etapa.get(etapa, set())) if 'ID' in df.columns else None
        }
        for etapa, dados in dados_campos.items()
    ])
    
    # Ordenar pelo total (maior para menor)
    df_resumo = df_resumo.sort_values('Total', ascending=False)
    
    # Adicionar linha de totais
    if 'ID' in df.columns:
        df_totais = pd.DataFrame([{
            'Etapa': 'TOTAL GERAL',
            'Total': total_geral,
            'Média Diária': None,
            'Dia Mais Produtivo': None,
            'Máximo em Um Dia': None,
            'Dias Com Atividade': num_dias_com_atividade,
            'Percentual': 100.0,
            'Registros Únicos': len(todos_ids)
        }])
        
        df_resumo = pd.concat([df_resumo, df_totais])
    
    # Configuração de colunas para a tabela
    col_config = {
        "Etapa": st.column_config.TextColumn("Etapa do Processo"),
        "Total": st.column_config.NumberColumn("Total", format="%d"),
        "Média Diária": st.column_config.NumberColumn("Média Diária", format="%.1f"),
        "Dia Mais Produtivo": st.column_config.TextColumn("Dia Mais Produtivo"),
        "Máximo em Um Dia": st.column_config.NumberColumn("Máximo", format="%d"),
        "Dias Com Atividade": st.column_config.NumberColumn("Dias Ativos", format="%d"),
        "Percentual": st.column_config.ProgressColumn(
            "% do Total",
            format="%.1f%%",
            min_value=0,
            max_value=100
        )
    }
    
    # Adicionar coluna de registros únicos se disponível
    if 'ID' in df.columns:
        col_config["Registros Únicos"] = st.column_config.NumberColumn("Registros Únicos", format="%d")
    
    # Exibir tabela formatada
    st.dataframe(
        df_resumo,
        column_config=col_config,
        use_container_width=True,
        hide_index=True
    )

    # Para o caso de precisar formatar nomes em colunas de resumo
    if isinstance(df_resumo, pd.DataFrame) and 'Etapa' in df_resumo.columns:
        df_resumo['Etapa'] = df_resumo['Etapa'].apply(lambda x: str(x).replace('_', ' ') if '_' in str(x) else x)

def mostrar_grafico_diario(df, campos_data):
    """
    Mostra gráficos de evolução diária de produtividade
    
    Args:
        df (pandas.DataFrame): DataFrame com dados filtrados
        campos_data (list): Lista de campos de data para análise
    """
    # Adicionar estilo visual para a seção
    st.markdown("""
    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 10px; border-left: 5px solid #E91E63; margin-bottom: 20px;">
        <h3 style="margin-top: 0; color: #C2185B; font-size: 18px;">Evolução Diária de Produtividade</h3>
        <p style="margin-bottom: 0; font-size: 14px; color: #333333;">
            Análise da produtividade ao longo do tempo, com detalhamento por dia e etapa.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Coletar dados para gráficos diários
    dados_diarios = []
    
    # Campos para calcular "Busca Realizada"
    ganho_busca_campo = 'UF_CRM_DATA_SOLICITAR_REQUERIMENTO'
    perca_busca_campo = 'UF_CRM_DEVOLUTIVA_BUSCA'
    
    # Dados de ganho e perca para cálculo de busca total
    dados_ganho_busca = {}
    dados_perca_busca = {}
    
    for campo in campos_data:
        # Pular campos sem dados
        if df[campo].isna().all():
            continue
            
        # Obter série temporal filtrada
        serie_data = df[campo].dropna()
        
        # Nome amigável para o campo
        nome_etapa = formatar_nome_etapa(campo)
        
        # Agrupar por dia
        contagem_diaria = serie_data.dt.date.value_counts().sort_index()
        
        # Guardar dados especiais para cálculo de busca total
        if campo == ganho_busca_campo:
            dados_ganho_busca = {data: qtd for data, qtd in contagem_diaria.items()}
        elif campo == perca_busca_campo:
            dados_perca_busca = {data: qtd for data, qtd in contagem_diaria.items()}
        
        for data, qtd in contagem_diaria.items():
            dados_diarios.append({
                'Data': data,
                'Quantidade': qtd,
                'Etapa': nome_etapa
            })
    
    # Adicionar dados de "Busca Realizada" - combinação de ganho e perca
    todas_datas = set(list(dados_ganho_busca.keys()) + list(dados_perca_busca.keys()))
    for data in todas_datas:
        ganho = dados_ganho_busca.get(data, 0)
        perca = dados_perca_busca.get(data, 0)
        total_busca = ganho + perca
        if total_busca > 0:
            dados_diarios.append({
                'Data': data,
                'Quantidade': total_busca,
                'Etapa': 'Busca Realizada'
            })
    
    # Se não houver dados, mostra mensagem e sai
    if not dados_diarios:
        st.warning("Não há dados disponíveis para análise diária no período selecionado.")
        return
    
    # Criar DataFrame para análise
    df_dias = pd.DataFrame(dados_diarios)
    
    # Criar gráfico de produção diária total (todas as etapas)
    st.subheader("Produtividade Total por Dia")
    
    # Agrupar por data para todas as etapas
    total_por_dia = df_dias.groupby('Data')['Quantidade'].sum().reset_index()
    
    # Ordenar por data
    total_por_dia = total_por_dia.sort_values('Data')
    
    # Formatar datas para exibição
    total_por_dia['Data_Formatada'] = total_por_dia['Data'].apply(lambda x: x.strftime('%d/%m'))
    
    # Calcular média móvel de 3 dias se tivermos dados suficientes
    if len(total_por_dia) >= 3:
        total_por_dia['Media_Movel'] = total_por_dia['Quantidade'].rolling(window=3, min_periods=1).mean()
    
    # Criar gráfico combinado de barras e linha
    fig_total = go.Figure()
    
    # Adicionar barras para quantidade diária
    fig_total.add_trace(
        go.Bar(
            x=total_por_dia['Data_Formatada'],
            y=total_por_dia['Quantidade'],
            name='Atividades Diárias',
            marker_color='#E91E63',
            opacity=0.7,
            text=total_por_dia['Quantidade'],
            textposition='outside',
            textfont=dict(size=10, color='black'),
            hovertemplate='<b>%{x}</b><br>Atividades: %{y}<extra></extra>'
        )
    )
    
    # Adicionar linha para média móvel se disponível
    if 'Media_Movel' in total_por_dia.columns:
        fig_total.add_trace(
            go.Scatter(
                x=total_por_dia['Data_Formatada'],
                y=total_por_dia['Media_Movel'],
                name='Média Móvel (3 dias)',
                line=dict(color='#2196F3', width=3),
                hovertemplate='<b>%{x}</b><br>Média: %{y:.1f}<extra></extra>'
            )
        )
    
    # Configurar layout
    fig_total.update_layout(
        title='Total de Atividades por Dia',
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=50, b=50),
        xaxis_title='Dia',
        yaxis_title='Quantidade',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_total, use_container_width=True)
    
    # Informações sobre o dia com mais atividades
    if not total_por_dia.empty:
        max_dia = total_por_dia.loc[total_por_dia['Quantidade'].idxmax()]
        st.info(f"**Dia com mais atividades:** {max_dia['Data'].strftime('%d/%m/%Y')} com {int(max_dia['Quantidade'])} registros")
    
    # Seção de análise de pesquisas
    st.subheader("Análise de Pesquisas")
    
    # Filtrar apenas as etapas de pesquisa
    etapas_pesquisa = ['Deu ganho na Busca', 'Deu perca na Busca', 'Busca Realizada']
    df_pesquisa = df_dias[df_dias['Etapa'].isin(etapas_pesquisa)]
    
    if not df_pesquisa.empty:
        # Criar gráfico de evolução de pesquisas
        fig_pesquisa = px.line(
            df_pesquisa,
            x='Data',
            y='Quantidade',
            color='Etapa',
            title='Evolução de Pesquisas por Dia',
            labels={
                'Data': 'Data', 
                'Quantidade': 'Quantidade', 
                'Etapa': 'Tipo de Pesquisa'
            },
            markers=True
        )
        
        fig_pesquisa.update_layout(
            height=450,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=20, r=20, t=50, b=50),
            xaxis_title='Dia',
            yaxis_title='Quantidade',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_pesquisa, use_container_width=True)
    else:
        st.info("Não há dados de pesquisa disponíveis para o período selecionado.")
    
    # Gráfico de produção por etapa ao longo do tempo
    st.subheader("Produtividade por Etapa ao Longo do Tempo")
    
    # Permitir seleção de etapas para visualizar
    etapas_disponiveis = sorted(df_dias['Etapa'].unique())
    
    # Cálculo de etapas com maior volume para seleção padrão
    etapas_volume = df_dias.groupby('Etapa')['Quantidade'].sum().sort_values(ascending=False)
    etapas_principais = etapas_volume.index.tolist()[:5] if len(etapas_volume) > 5 else etapas_volume.index.tolist()
    
    etapas_selecionadas = st.multiselect(
        "Selecione as etapas para visualizar:",
        options=etapas_disponiveis,
        default=etapas_principais,
        key="grafico_diario_etapas"
    )
    
    if not etapas_selecionadas:
        st.warning("Selecione pelo menos uma etapa para visualizar o gráfico.")
    else:
        # Filtrar dados para as etapas selecionadas
        df_etapas_selecionadas = df_dias[df_dias['Etapa'].isin(etapas_selecionadas)]
        
        # Criar DataFrame pivot com datas nas linhas e etapas nas colunas
        df_pivot = df_etapas_selecionadas.pivot_table(
            index='Data',
            columns='Etapa',
            values='Quantidade',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Formatar datas para exibição
        df_pivot['Data_Formatada'] = df_pivot['Data'].apply(lambda x: x.strftime('%d/%m'))
        
        # Criar gráfico de linhas
        fig_etapas = go.Figure()
        
        # Adicionar uma linha para cada etapa
        for etapa in etapas_selecionadas:
            if etapa in df_pivot.columns:
                fig_etapas.add_trace(
                    go.Scatter(
                        x=df_pivot['Data_Formatada'],
                        y=df_pivot[etapa],
                        mode='lines+markers',
                        name=etapa,
                        hovertemplate='<b>%{x}</b><br>' + etapa + ': %{y}<extra></extra>'
                    )
                )
        
        # Configurar layout
        fig_etapas.update_layout(
            title='Evolução Diária por Etapa',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=20, r=20, t=50, b=100),
            xaxis_title='Dia',
            yaxis_title='Quantidade',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_etapas, use_container_width=True)
        
        # Tabela com os dados diários
        st.subheader("Detalhamento por Dia")
        
        # Preparar tabela formatada
        df_tabela = df_pivot.drop(columns=['Data_Formatada']).copy()
        
        # Adicionar coluna de total por dia
        etapas_cols = [col for col in df_tabela.columns if col != 'Data']
        df_tabela['Total'] = df_tabela[etapas_cols].sum(axis=1)
        
        # Formatar datas
        df_tabela['Data'] = df_tabela['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))
        
        # Ordenar por data (mais recente primeiro)
        df_tabela = df_tabela.sort_values('Data', ascending=False)
        
        # Exibir tabela
        st.dataframe(
            df_tabela,
            column_config={
                "Data": st.column_config.TextColumn("Data"),
                "Total": st.column_config.NumberColumn("Total do Dia", format="%d"),
                **{etapa: st.column_config.NumberColumn(etapa, format="%d") for etapa in etapas_cols}
            },
            use_container_width=True,
            hide_index=True
        )

def mostrar_visao_produtividade(df, campos_data, titulo_visao, freq):
    """
    Mostra a visão de produtividade agregada por período
    
    Args:
        df (pandas.DataFrame): DataFrame com dados filtrados
        campos_data (list): Lista de campos de data para análise
        titulo_visao (str): Título da visão (Diária, Semanal, Mensal)
        freq (str): Frequência para agrupamento (D, W, M)
    """
    st.markdown(f"### Visão {titulo_visao} de Produtividade")
    
    # Criar contagem para cada etapa por período
    dados_grafico = []
    
    # Campos para calcular "Busca Realizada"
    ganho_busca_campo = 'UF_CRM_DATA_SOLICITAR_REQUERIMENTO'
    perca_busca_campo = 'UF_CRM_DEVOLUTIVA_BUSCA'
    
    # Dados de ganho e perca para cálculo de busca total
    dados_ganho_busca = {}
    dados_perca_busca = {}
    
    for campo in campos_data:
        # Pular campos sem dados
        if df[campo].isna().all():
            continue
        
        # Formatar data de acordo com a frequência
        serie_data = df[campo].dropna()
        
        # Nome amigável para o campo
        nome_etapa = formatar_nome_etapa(campo)
        
        # Agrupar por período
        if freq == 'D':
            contagem = serie_data.dt.date.value_counts().sort_index()
            nome_periodo = 'Data'
            
            # Guardar dados especiais para cálculo de busca total
            if campo == ganho_busca_campo:
                dados_ganho_busca = {data: qtd for data, qtd in contagem.items()}
            elif campo == perca_busca_campo:
                dados_perca_busca = {data: qtd for data, qtd in contagem.items()}
                
        elif freq == 'W':
            # Agrupar por semana, usando a data de início da semana
            contagem = serie_data.dt.to_period('W').dt.start_time.dt.date.value_counts().sort_index()
            nome_periodo = 'Semana'
            
            # Guardar dados especiais para cálculo de busca total
            if campo == ganho_busca_campo:
                dados_ganho_busca = {data: qtd for data, qtd in contagem.items()}
            elif campo == perca_busca_campo:
                dados_perca_busca = {data: qtd for data, qtd in contagem.items()}
                
        else:  # 'M'
            # Agrupar por mês, usando o primeiro dia do mês
            contagem = serie_data.dt.to_period('M').dt.start_time.dt.date.value_counts().sort_index()
            nome_periodo = 'Mês'
            
            # Guardar dados especiais para cálculo de busca total
            if campo == ganho_busca_campo:
                dados_ganho_busca = {data: qtd for data, qtd in contagem.items()}
            elif campo == perca_busca_campo:
                dados_perca_busca = {data: qtd for data, qtd in contagem.items()}
        
        # Criar DataFrame temporário para este campo
        df_temp = pd.DataFrame({
            nome_periodo: contagem.index,
            'Quantidade': contagem.values,
            'Etapa': [nome_etapa for _ in range(len(contagem))]
        })
        
        # Adicionar aos dados do gráfico
        dados_grafico.append(df_temp)
    
    # Adicionar dados de "Busca Realizada" - combinação de ganho e perca
    todas_datas = set(list(dados_ganho_busca.keys()) + list(dados_perca_busca.keys()))
    if todas_datas:
        dados_busca_realizada = []
        for data in todas_datas:
            ganho = dados_ganho_busca.get(data, 0)
            perca = dados_perca_busca.get(data, 0)
            total_busca = ganho + perca
            if total_busca > 0:
                dados_busca_realizada.append({
                    nome_periodo: data,
                    'Quantidade': total_busca,
                    'Etapa': 'Busca Realizada'
                })
        
        if dados_busca_realizada:
            dados_grafico.append(pd.DataFrame(dados_busca_realizada))
    
    if not dados_grafico:
        st.warning(f"Não há dados suficientes para criar a visão {titulo_visao.lower()}.")
        return
    
    # Combinar todos os dados
    df_grafico = pd.concat(dados_grafico, ignore_index=True)
    
    # Criar gráfico
    fig = px.bar(
        df_grafico,
        x=nome_periodo,
        y='Quantidade',
        color='Etapa',
        barmode='group',
        title=f"Produtividade {titulo_visao} por Etapa",
        labels={
            nome_periodo: f"{nome_periodo}",
            'Quantidade': 'Quantidade de Registros',
            'Etapa': 'Etapa do Processo'
        },
        text='Quantidade'  # Adicionar rótulos de texto nas barras
    )
    
    # Melhorar formatação do gráfico
    fig.update_layout(
        height=500,
        xaxis={'categoryorder': 'category ascending'},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=20, r=20, t=50, b=100)
    )
    
    # Configurar a exibição do texto acima das barras
    fig.update_traces(
        textposition='outside',
        textfont=dict(size=10, color='black'),
        cliponaxis=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Adicionar visualização específica para pesquisas
    etapas_pesquisa = ['Deu ganho na Busca', 'Deu perca na Busca', 'Busca Realizada']
    df_pesquisa = df_grafico[df_grafico['Etapa'].isin(etapas_pesquisa)]
    
    if not df_pesquisa.empty:
        st.subheader(f"Análise de Pesquisas - Visão {titulo_visao}")
        
        fig_pesquisa = px.bar(
            df_pesquisa,
            x=nome_periodo,
            y='Quantidade',
            color='Etapa',
            barmode='group',
            title=f"Pesquisas {titulo_visao}",
            labels={
                nome_periodo: f"{nome_periodo}",
                'Quantidade': 'Quantidade de Registros',
                'Etapa': 'Tipo de Pesquisa'
            },
            text='Quantidade'
        )
        
        # Configurar a exibição do gráfico
        fig_pesquisa.update_layout(
            height=450,
            xaxis={'categoryorder': 'category ascending'},
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=20, r=20, t=50, b=100)
        )
        
        # Configurar a exibição do texto acima das barras
        fig_pesquisa.update_traces(
            textposition='outside',
            textfont=dict(size=10, color='black'),
            cliponaxis=False
        )
        
        st.plotly_chart(fig_pesquisa, use_container_width=True)
    
    # Tabela de resumo
    resumo = df_grafico.pivot_table(
        index='Etapa',
        columns=nome_periodo,
        values='Quantidade',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Adicionar total por etapa
    resumo['Total'] = resumo.iloc[:, 1:].sum(axis=1)
    
    # Ordenar pelo total (maior para menor)
    resumo = resumo.sort_values('Total', ascending=False)
    
    # Adicionar linha de total geral
    total_por_periodo = resumo.iloc[:, 1:].sum(axis=0)
    total_por_periodo['Etapa'] = 'TOTAL GERAL'
    resumo = pd.concat([resumo, pd.DataFrame([total_por_periodo])], ignore_index=True)
    
    st.dataframe(resumo, use_container_width=True)
    
    # Explicação da análise
    with st.expander(f"Como interpretar a visão {titulo_visao.lower()}"):
        st.markdown(f"""
        **Análise {titulo_visao}:**
        
        * O gráfico mostra a quantidade de registros por etapa do processo em cada {nome_periodo.lower()}.
        * A tabela apresenta os mesmos dados em formato numérico, com totais por etapa e por {nome_periodo.lower()}.
        * Etapas com maiores valores indicam maior volume de trabalho naquele período.
        * Compare diferentes períodos para identificar tendências e variações na carga de trabalho.
        """)

def analisar_produtividade_responsavel(df, campos_data):
    """
    Analisa a produtividade por responsável
    
    Args:
        df (pandas.DataFrame): DataFrame com dados filtrados
        campos_data (list): Lista de campos de data para análise
    """
    if 'ASSIGNED_BY_NAME' not in df.columns:
        st.info("Dados de responsável não disponíveis para análise.")
        return
    
    # Criar dados para análise por responsável
    dados_resp = []
    
    # Campos para calcular "Busca Realizada"
    ganho_busca_campo = 'UF_CRM_DATA_SOLICITAR_REQUERIMENTO'
    perca_busca_campo = 'UF_CRM_DEVOLUTIVA_BUSCA'
    
    # Dados de ganho e perca por responsável
    dados_ganho_resp = {}
    dados_perca_resp = {}
    
    for campo in campos_data:
        # Pular campos sem dados
        if df[campo].isna().all():
            continue
        
        # Filtrar registros que têm data e responsável
        df_valido = df.dropna(subset=[campo, 'ASSIGNED_BY_NAME'])
        
        # Nome da etapa formatado
        nome_etapa = formatar_nome_etapa(campo)
        
        # Agrupar por responsável e contar
        contagem = df_valido.groupby('ASSIGNED_BY_NAME').size().reset_index()
        contagem.columns = ['Responsável', 'Quantidade']
        contagem['Etapa'] = nome_etapa
        
        # Guardar dados especiais para cálculo de busca total
        if campo == ganho_busca_campo:
            dados_ganho_resp = {resp: qtd for resp, qtd in zip(contagem['Responsável'], contagem['Quantidade'])}
        elif campo == perca_busca_campo:
            dados_perca_resp = {resp: qtd for resp, qtd in zip(contagem['Responsável'], contagem['Quantidade'])}
        
        # Adicionar aos dados
        dados_resp.append(contagem)
    
    # Adicionar dados de "Busca Realizada" - combinação de ganho e perca
    todos_resp = set(list(dados_ganho_resp.keys()) + list(dados_perca_resp.keys()))
    if todos_resp:
        dados_busca_realizada = []
        for resp in todos_resp:
            ganho = dados_ganho_resp.get(resp, 0)
            perca = dados_perca_resp.get(resp, 0)
            total_busca = ganho + perca
            if total_busca > 0:
                dados_busca_realizada.append({
                    'Responsável': resp,
                    'Quantidade': total_busca,
                    'Etapa': 'Busca Realizada'
                })
        
        if dados_busca_realizada:
            dados_resp.append(pd.DataFrame(dados_busca_realizada))
    
    if not dados_resp:
        st.warning("Não há dados suficientes para análise por responsável.")
        return
    
    # Combinar todos os dados
    df_resp = pd.concat(dados_resp, ignore_index=True)
    
    # Análise de pesquisas por responsável
    etapas_pesquisa = ['Deu ganho na Busca', 'Deu perca na Busca', 'Busca Realizada']
    df_pesquisa_resp = df_resp[df_resp['Etapa'].isin(etapas_pesquisa)]
    
    if not df_pesquisa_resp.empty:
        st.subheader("Análise de Pesquisas por Responsável")
        
        # Criar gráfico de pesquisas por responsável
        fig_pesquisa = px.bar(
            df_pesquisa_resp,
            x='Responsável',
            y='Quantidade',
            color='Etapa',
            barmode='group',
            title="Pesquisas por Responsável",
            labels={
                'Responsável': "Responsável",
                'Quantidade': 'Quantidade de Registros',
                'Etapa': 'Tipo de Pesquisa'
            },
            text='Quantidade'
        )
        
        # Melhorar formatação do gráfico
        fig_pesquisa.update_layout(
            height=500,
            xaxis={'categoryorder': 'total descending'},
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=20, r=20, t=50, b=100)
        )
        
        # Configurar a exibição do texto acima das barras
        fig_pesquisa.update_traces(
            textposition='outside', 
            textfont=dict(size=10, color='black'),
            cliponaxis=False
        )
        
        st.plotly_chart(fig_pesquisa, use_container_width=True)
        
        # Calcular taxa de sucesso por responsável
        resumo_pesquisa = df_pesquisa_resp.pivot_table(
            index='Responsável',
            columns='Etapa',
            values='Quantidade',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Calcular taxa de sucesso
        if 'Deu ganho na Busca' in resumo_pesquisa.columns and 'Busca Realizada' in resumo_pesquisa.columns:
            resumo_pesquisa['Taxa de Sucesso (%)'] = resumo_pesquisa['Deu ganho na Busca'] / resumo_pesquisa['Busca Realizada'] * 100
            
            # Ordenar por taxa de sucesso
            resumo_pesquisa = resumo_pesquisa.sort_values('Taxa de Sucesso (%)', ascending=False)
            
            # Formatar a tabela
            st.dataframe(
                resumo_pesquisa,
                column_config={
                    'Responsável': st.column_config.TextColumn("Responsável"),
                    'Deu ganho na Busca': st.column_config.NumberColumn("Ganhos", format="%d"),
                    'Deu perca na Busca': st.column_config.NumberColumn("Perdas", format="%d"),
                    'Busca Realizada': st.column_config.NumberColumn("Total de Buscas", format="%d"),
                    'Taxa de Sucesso (%)': st.column_config.ProgressColumn(
                        "Taxa de Sucesso",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100
                    )
                },
                use_container_width=True,
                hide_index=True
            )
    
    # Criar gráfico geral
    st.subheader("Produtividade Geral por Responsável")
    
    fig = px.bar(
        df_resp,
        x='Responsável',
        y='Quantidade',
        color='Etapa',
        barmode='group',
        title="Produtividade por Responsável e Etapa",
        labels={
            'Responsável': "Responsável",
            'Quantidade': 'Quantidade de Registros',
            'Etapa': 'Etapa do Processo'
        },
        text='Quantidade'  # Adicionar rótulos de texto nas barras
    )
    
    # Melhorar formatação do gráfico
    fig.update_layout(
        height=600,
        xaxis={'categoryorder': 'total descending'},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=20, r=20, t=50, b=100)
    )
    
    # Configurar a exibição do texto acima das barras
    fig.update_traces(
        textposition='outside', 
        textfont=dict(size=10, color='black'),
        cliponaxis=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de resumo
    resumo_resp = df_resp.pivot_table(
        index='Responsável',
        columns='Etapa',
        values='Quantidade',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Adicionar total por responsável
    resumo_resp['Total'] = resumo_resp.iloc[:, 1:].sum(axis=1)
    
    # Ordenar pelo total (maior para menor)
    resumo_resp = resumo_resp.sort_values('Total', ascending=False)
    
    # Adicionar linha de total geral
    total_por_etapa = resumo_resp.iloc[:, 1:].sum(axis=0)
    total_por_etapa['Responsável'] = 'TOTAL GERAL'
    resumo_resp = pd.concat([resumo_resp, pd.DataFrame([total_por_etapa])], ignore_index=True)
    
    st.dataframe(resumo_resp, use_container_width=True)
    
    # Explicação da análise
    with st.expander("Como interpretar a análise por responsável"):
        st.markdown("""
        **Análise por Responsável:**
        
        * O gráfico mostra a quantidade de registros por etapa do processo para cada responsável.
        * A tabela apresenta os mesmos dados em formato numérico, com totais por responsável e por etapa.
        * Responsáveis com maiores valores indicam maior volume de trabalho.
        * Compare diferentes responsáveis para identificar distribuição da carga de trabalho.
        * Para pesquisas, observe a taxa de sucesso (proporção de ganhos sobre o total de buscas).
        """)
    
    # Análise de eficiência por responsável (média de registros por dia)
    st.markdown("### Eficiência por Responsável")
    
    # Calcular dias úteis no período analisado
    dias_uteis = len(set([d.date() for d in df[campos_data].stack().dropna()]))
    
    if dias_uteis > 0:
        # Adicionar coluna de média diária
        resumo_resp['Média Diária'] = resumo_resp['Total'] / dias_uteis
        
        # Criar gráfico de média diária
        fig_media = px.bar(
            resumo_resp[resumo_resp['Responsável'] != 'TOTAL GERAL'],
            x='Responsável',
            y='Média Diária',
            title=f"Média Diária de Produtividade por Responsável (baseado em {dias_uteis} dias)",
            color='Média Diária',
            color_continuous_scale='Viridis',
            labels={
                'Responsável': "Responsável",
                'Média Diária': 'Média de Registros por Dia'
            },
            text=resumo_resp[resumo_resp['Responsável'] != 'TOTAL GERAL']['Média Diária'].round(1)  # Adicionar rótulos arredondados para 1 casa decimal
        )
        
        fig_media.update_layout(
            height=500,
            xaxis={'categoryorder': 'total descending'},
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        # Configurar a exibição do texto acima das barras
        fig_media.update_traces(
            textposition='outside',
            textfont=dict(size=10, color='black'),
            cliponaxis=False
        )
        
        st.plotly_chart(fig_media, use_container_width=True)
        
        # Exibir análise de eficiência em tabela
        df_eficiencia = resumo_resp[['Responsável', 'Total', 'Média Diária']].copy()
        df_eficiencia['Média Diária'] = df_eficiencia['Média Diária'].round(2)
        
        st.dataframe(
            df_eficiencia, 
            use_container_width=True,
            column_config={
                'Responsável': st.column_config.TextColumn("Responsável"),
                'Total': st.column_config.NumberColumn("Total de Registros", format="%d"),
                'Média Diária': st.column_config.NumberColumn("Média Diária", format="%.2f")
            }
        )
    else:
        st.info("Dados insuficientes para calcular a eficiência diária.") 