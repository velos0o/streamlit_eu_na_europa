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
    nome = campo.replace('UF_CRM_DATA_', '').replace('UF_CRM_', '').replace('UF_CRM_RESPONSAVEL_', '')
    # Garantir que todos os underlines são substituídos por espaços
    while '_' in nome:
        nome = nome.replace('_', ' ')
    return nome.title()

# Dicionário para mapear campos de data com seus respectivos campos de responsável
def obter_mapeamento_campos():
    """
    Retorna um dicionário que mapeia campos de data com seus respectivos campos de responsável
    
    Returns:
        dict: Dicionário de mapeamento entre campos de data e campos de responsável
    """
    return {
        'UF_CRM_DATA_SOLICITAR_REQUERIMENTO': 'UF_CRM_RESPONSAVEL__BUSCA',
        'UF_CRM_DEVOLUTIVA_BUSCA': 'UF_CRM_RESPONSAVEL_DEVOLUTIVA_BUSCA',
        'UF_CRM_DATA_SOLICITAR_CARTORIO_ORIGEM': 'UF_CRM_RESPONSAVEL_SOLICITAR_CARTORIO_ORIGEM',
        'UF_CRM_DATA_AGUARDANDOCARTORIO_ORIGEM': 'UF_CRM_RESPONSAVEL_AGUARDANDO_CARTORIO_DE_ORIGEM',
        'UF_CRM_DATA_CERTIDAO_EMITIDA': 'UF_CRM_RESPONSAVEL_CERTIDAO_EMITIDA',
        'UF_CRM_DATA_CERTIDAO_FISICA_ENTREGUE': 'UF_CRM_RESPONSAVEL_CERTIDO_FISICA_ENTREGUE',
        'UF_CRM_DATA_CERTIDAO_FISICA_ENVIADA': 'UF_CRM_RESPONSAVEL_CERTIDO_FISICA_ENVIADA',
        'UF_CRM_DEVOLUCAO_ADM': 'UF_CRM_RESPONSAVEL_DEVOLUCAO_ADM',
        'UF_CRM_DEVOLUCAO_ADM_VERIFICADO': 'UF_CRM_RESPONSAVEL_DEVOLUCAO_ADM_VERIFICADO',
        'UF_CRM_DEVOLUTIVA_REQUERIMENTO': 'UF_CRM_RESPONSAVEL_DEVOLVIDOREQUERIMENTO',
        'UF_CRM_SOLICITACAO_DUPLICADO': 'UF_CRM_RESPONSAVEL_SOLICITACAO_DUPLICADA',
        'UF_CRM_DATA_MONTAR_REQUERIMENTO': 'UF_CRM_MONTAGEM_PASTA_RESPONSAVEL'  # Adicionando o par que faltava
    }

def aplicar_filtros_produtividade(df_analise, campos_data, periodo_inicio, periodo_fim):
    """
    Aplica filtros de período aos dados de produtividade
    
    Args:
        df_analise (pandas.DataFrame): DataFrame com dados a serem filtrados
        campos_data (list): Lista de campos de data para análise
        periodo_inicio (datetime): Data inicial do período
        periodo_fim (datetime): Data final do período
        
    Returns:
        pandas.DataFrame: DataFrame filtrado pelo período especificado
    """
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
        
    return df_filtrado

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
    
    # Lista de campos de responsáveis específicos
    campos_responsavel = [
        'UF_CRM_RESPONSAVEL__BUSCA',
        'UF_CRM_RESPONSAVEL_AGUARDANDO_CARTORIO_DE_ORIGEM',
        'UF_CRM_RESPONSAVEL_CERTIDAO_EMITIDA',
        'UF_CRM_RESPONSAVEL_CERTIDO_FISICA_ENTREGUE',
        'UF_CRM_RESPONSAVEL_CERTIDO_FISICA_ENVIADA',
        'UF_CRM_RESPONSAVEL_DEVOLUCAO_ADM',
        'UF_CRM_RESPONSAVEL_DEVOLUCAO_ADM_VERIFICADO',
        'UF_CRM_RESPONSAVEL_DEVOLUTIVA_BUSCA',
        'UF_CRM_RESPONSAVEL_DEVOLVIDOREQUERIMENTO',
        'UF_CRM_RESPONSAVEL_SOLICITACAO_DUPLICADA',
        'UF_CRM_RESPONSAVEL_SOLICITAR_CARTORIO_ORIGEM',
        'UF_CRM_MONTAGEM_PASTA_RESPONSAVEL'
    ]
    
    # Mapeamento entre campos de data e campos de responsável
    mapeamento_campos = obter_mapeamento_campos()
    
    # Verificar se temos as colunas necessárias para a análise
    colunas_faltantes = [col for col in campos_data if col not in df.columns]
    if colunas_faltantes:
        st.warning(f"Algumas colunas de datas não foram encontradas: {', '.join(colunas_faltantes)}")
        campos_data = [col for col in campos_data if col in df.columns]
    
    # Verificar se os campos de responsáveis existem
    responsaveis_faltantes = [col for col in campos_responsavel if col not in df.columns]
    if responsaveis_faltantes:
        st.warning(f"Alguns campos de responsáveis não foram encontrados: {', '.join(responsaveis_faltantes)}")
    
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
    
    # Header principal com estilo melhorado
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1565C0 0%, #64B5F6 100%); padding: 20px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h2 style="color: white; text-align: center; margin: 0; font-size: 28px; font-weight: 700;">📊 Análise de Produtividade</h2>
        <p style="color: white; text-align: center; margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">
            Monitoramento completo da produtividade por etapas, períodos e responsáveis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    **O que é a Análise de Produtividade?**
    • Esta análise mostra os registros de datas e horas para cada etapa do processo.
    • Permite identificar a velocidade de processamento, produtividade e distribuição do trabalho.
    • Os dados são exibidos por dia, semana e mês para facilitar diferentes níveis de análise.
    • Agora também é possível analisar por responsável específico de cada etapa.
    """)
    
    # MAPA DO RELATÓRIO - Adicionando índice visual
    st.markdown("""
    <div style="background: linear-gradient(135deg, #3949AB 0%, #5C6BC0 100%); padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h3 style="color: white; text-align: center; margin: 0 0 15px 0; font-size: 22px; font-weight: 700;">🗺️ MAPA DO RELATÓRIO</h3>
        <p style="color: white; text-align: center; margin-bottom: 20px; font-size: 14px; opacity: 0.9;">
            Use este guia para encontrar rapidamente as informações que você precisa
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Layout em colunas para o mapa do relatório
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px;">
            <h4 style="color: #1976D2; font-size: 16px; border-bottom: 2px solid #1976D2; padding-bottom: 5px; margin-bottom: 10px;">📊 Números Gerais</h4>
            <p style="font-size: 13px; color: #555;">Aqui você vê os números totais de cada etapa do seu processo.</p>
            <p style="font-size: 12px; color: #666; font-style: italic;">Ideal para ter uma visão geral e comparar qual etapa tem mais volume.</p>
        </div>
        
        <div style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px;">
            <h4 style="color: #E53935; font-size: 16px; border-bottom: 2px solid #E53935; padding-bottom: 5px; margin-bottom: 10px;">📈 Como está evoluindo?</h4>
            <p style="font-size: 13px; color: #555;">Mostra os números dia a dia, para ver como o trabalho está evoluindo.</p>
            <p style="font-size: 12px; color: #666; font-style: italic;">Perfeito para identificar dias com mais produtividade ou quedas no rendimento.</p>
        </div>
        
        <div style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px;">
            <h4 style="color: #43A047; font-size: 16px; border-bottom: 2px solid #43A047; padding-bottom: 5px; margin-bottom: 10px;">📅 Visão por Períodos</h4>
            <p style="font-size: 13px; color: #555;">Veja o trabalho agrupado por dia, semana ou mês, como preferir.</p>
            <p style="font-size: 12px; color: #666; font-style: italic;">Útil para descobrir os melhores períodos e observar tendências ao longo do tempo.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px;">
            <h4 style="color: #7B1FA2; font-size: 16px; border-bottom: 2px solid #7B1FA2; padding-bottom: 5px; margin-bottom: 10px;">👤 Quem fez o quê?</h4>
            <p style="font-size: 13px; color: #555;">Análise completa do trabalho por pessoa, mostrando quem está fazendo cada etapa.</p>
            <p style="font-size: 12px; color: #666; font-style: italic;">Ótimo para ver como o trabalho está distribuído e reconhecer quem está produzindo mais.</p>
        </div>
        
        <div style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px;">
            <h4 style="color: #4527A0; font-size: 16px; border-bottom: 2px solid #4527A0; padding-bottom: 5px; margin-bottom: 10px;">🔄 Mapa de Calor</h4>
            <p style="font-size: 13px; color: #555;">Visualização colorida que mostra quando e quem produziu mais em cada período.</p>
            <p style="font-size: 12px; color: #666; font-style: italic;">Excelente para identificar padrões e picos de trabalho de cada pessoa.</p>
        </div>
        
        <div style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px;">
            <h4 style="color: #FF8F00; font-size: 16px; border-bottom: 2px solid #FF8F00; padding-bottom: 5px; margin-bottom: 10px;">📑 Lista Completa</h4>
            <p style="font-size: 13px; color: #555;">Todas as informações organizadas por tipo de etapa, sem precisar filtrar nada.</p>
            <p style="font-size: 12px; color: #666; font-style: italic;">Perfeito para consultar casos específicos ou exportar listas para Excel.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Instruções de uso simplificadas
    st.markdown("""
    <div style="background-color: #f0f7ff; border-radius: 8px; padding: 15px; margin: 10px 0 20px 0; border-left: 5px solid #3182ce;">
        <h4 style="margin-top: 0; color: #2c5282; font-size: 16px;">Como usar este relatório:</h4>
        <p style="font-size: 14px; color: #333; margin-bottom: 0;">
            1. <strong>Selecione o período</strong> usando os seletores de data acima ⏱️<br>
            2. <strong>Escolha a aba</strong> correspondente à análise desejada 📂<br>
            3. <strong>Utilize os filtros específicos</strong> para refinar sua análise 🔍<br>
            4. <strong>Faça download dos dados</strong> usando os botões disponíveis 📥
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Converter todas as colunas de data para datetime
    for campo in campos_data:
        df[campo] = pd.to_datetime(df[campo], errors='coerce')
    
    # Pré-calcular os responsáveis mais produtivos para destaque na página principal
    destaques_responsaveis = {}
    for campo_data in campos_data:
        if campo_data in df.columns and campo_data in mapeamento_campos:
            campo_resp = mapeamento_campos.get(campo_data)
            if campo_resp and campo_resp in df.columns:
                # Filtrar dados válidos
                df_etapa = df.dropna(subset=[campo_data, campo_resp])
                if not df_etapa.empty:
                    # Contar registros por responsável
                    contagem = df_etapa[campo_resp].value_counts()
                    if not contagem.empty:
                        # Obter top 3 responsáveis para esta etapa
                        top_resp = contagem.nlargest(3)
                        nome_etapa = formatar_nome_etapa(campo_data)
                        destaques_responsaveis[nome_etapa] = {
                            'responsaveis': [(resp, qtd) for resp, qtd in zip(top_resp.index, top_resp.values)],
                            'campo_data': campo_data,
                            'campo_resp': campo_resp
                        }
    
    # Botão para mostrar o mapeamento de campos
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Ver Mapeamento de Etapas e Responsáveis", help="Visualize como os campos de data estão conectados aos campos de responsável correspondentes"):
            visualizar_mapeamento_campos(mapeamento_campos, campos_data, campos_responsavel)
            st.divider()
    
    # Remover o botão de destaques já que agora teremos uma aba dedicada
    
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
    
    # Filtro de responsável geral
    responsavel_geral_selecionado = None
    if 'ASSIGNED_BY_NAME' in df.columns:
        responsaveis = df['ASSIGNED_BY_NAME'].dropna().unique().tolist()
        responsavel_geral_selecionado = st.multiselect(
            "Responsável Geral",
            options=responsaveis,
            default=[],
            key="prod_responsavel_geral"
        )
    
    # Filtro de responsável específico por etapa
    st.markdown("#### Filtrar por Responsável de Etapa Específica")
    
    # Coletar todos os responsáveis únicos de todos os campos de responsável
    todos_responsaveis = set()
    for campo in campos_responsavel:
        if campo in df.columns:
            responsaveis_etapa = df[campo].dropna().unique().tolist()
            todos_responsaveis.update(responsaveis_etapa)
    
    todos_responsaveis = sorted(list(todos_responsaveis))
    
    # Dropdown para selecionar campo de etapa
    etapas_nomes = [formatar_nome_etapa(campo) for campo in campos_data if campo in df.columns]
    etapa_selecionada = st.selectbox("Selecione a Etapa", options=["Todas as Etapas"] + etapas_nomes, key="filtro_etapa")
    
    responsavel_etapa_selecionado = None
    if etapa_selecionada != "Todas as Etapas":
        # Encontrar o campo de data correspondente à etapa selecionada
        campo_data_selecionado = None
        for campo in campos_data:
            if formatar_nome_etapa(campo) == etapa_selecionada and campo in df.columns:
                campo_data_selecionado = campo
                break
        
        # Encontrar o campo de responsável correspondente
        campo_resp_selecionado = None
        if campo_data_selecionado in mapeamento_campos:
            campo_resp_selecionado = mapeamento_campos[campo_data_selecionado]
        
        # Filtrar por responsável da etapa se o campo existir
        if campo_resp_selecionado and campo_resp_selecionado in df.columns:
            responsaveis_etapa = sorted(df[campo_resp_selecionado].dropna().unique().tolist())
            responsavel_etapa_selecionado = st.multiselect(
                f"Responsável pela Etapa: {etapa_selecionada}",
                options=responsaveis_etapa,
                default=[],
                key="prod_responsavel_etapa"
            )
    else:
        # Opção para filtrar por qualquer responsável em qualquer etapa
        responsavel_etapa_selecionado = st.multiselect(
            "Responsável por Qualquer Etapa",
            options=todos_responsaveis,
            default=[],
            key="prod_responsavel_qualquer_etapa"
        )
    
    # Explicação sobre filtros
    with st.expander("Sobre os Filtros", expanded=False):
        st.markdown("""
        **Como usar os filtros:**
        • **Data Inicial e Final**: Selecione o período que deseja analisar.
        • **Responsável Geral**: Filtre pelo responsável geral do registro.
        • **Etapa + Responsável pela Etapa**: Filtre por uma etapa específica e seu respectivo responsável.
        
        Todos os filtros são aplicados em conjunto (operação AND).
        """)
    
    # Preparar dados filtrados para o período selecionado
    periodo_inicio = pd.to_datetime(data_inicio)
    periodo_fim = pd.to_datetime(data_fim) + timedelta(days=1) - timedelta(seconds=1)
    
    # Criar dataframe apenas com as colunas de data e informações relevantes
    colunas_selecionadas = campos_data.copy()
    colunas_responsavel_presentes = [col for col in campos_responsavel if col in df.columns]
    colunas_info = ['ID', 'TITLE', 'ASSIGNED_BY_NAME', 'UF_CRM_12_1723552666'] if 'UF_CRM_12_1723552666' in df.columns else ['ID', 'TITLE']
    
    # Adicionar colunas de informação
    for col in colunas_info:
        if col in df.columns:
            colunas_selecionadas.append(col)
    
    # Adicionar colunas de responsável
    for col in colunas_responsavel_presentes:
        colunas_selecionadas.append(col)
    
    # Remover duplicatas
    colunas_selecionadas = list(dict.fromkeys(colunas_selecionadas))
    
    df_analise = df[colunas_selecionadas].copy()
    
    # Filtra por responsável geral se selecionado
    if responsavel_geral_selecionado and 'ASSIGNED_BY_NAME' in df_analise.columns:
        df_analise = df_analise[df_analise['ASSIGNED_BY_NAME'].isin(responsavel_geral_selecionado)]
    
    # Filtrar por responsável específico da etapa
    if etapa_selecionada != "Todas as Etapas" and responsavel_etapa_selecionado:
        # Encontrar campo de responsável correspondente
        campo_data_selecionado = None
        for campo in campos_data:
            if formatar_nome_etapa(campo) == etapa_selecionada:
                campo_data_selecionado = campo
                break
        
        if campo_data_selecionado in mapeamento_campos:
            campo_resp = mapeamento_campos[campo_data_selecionado]
            if campo_resp in df_analise.columns:
                df_analise = df_analise[df_analise[campo_resp].isin(responsavel_etapa_selecionado)]
    elif responsavel_etapa_selecionado:  # Filtrar por responsável em qualquer etapa
        # Criar máscaras para cada campo de responsável
        mascara_final = pd.Series(False, index=df_analise.index)
        for campo_resp in colunas_responsavel_presentes:
            mascara = df_analise[campo_resp].isin(responsavel_etapa_selecionado)
            mascara_final = mascara_final | mascara
        
        df_analise = df_analise[mascara_final]
    
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
    
    # Criar abas para diferentes visualizações
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Métricas Gerais", 
        "📅 Análise Temporal", 
        "👥 Por Responsável Específico",
        "🏆 Destaques de Produtividade",
        "📑 Tabelas por Etapa"
    ])
    
    # Filtrar DF para o período selecionado para uso nas abas
    df_filtrado = aplicar_filtros_produtividade(df_analise, campos_data, periodo_inicio, periodo_fim)
    
    with tab1:
        mostrar_metricas_etapa(df_filtrado, campos_data, periodo_inicio, periodo_fim)
    
    with tab2:
        analisar_distribuicao_temporal(df_filtrado, campos_data)
    
    with tab3:
        analisar_matriz_responsavel_data(df_filtrado, campos_data, mapeamento_campos)
    
    with tab4:
        # Nova aba para destaques de produtividade
        mostrar_destaques_produtividade(destaques_responsaveis)
    
    with tab5:
        mostrar_tabelas_por_etapa(df_filtrado, campos_data)

def mostrar_destaques_produtividade(destaques):
    """
    Exibe os destaques de produtividade por etapa
    
    Args:
        destaques (dict): Dicionário com informações de destaque por etapa
    """
    if not destaques:
        st.warning("Não foram encontrados dados suficientes para exibir destaques de produtividade.")
        return
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #FF8C00 0%, #FFC107 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h3 style="margin-top: 0; color: white; font-size: 22px; font-weight: 700; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
            🏆 DESTAQUES DE PRODUTIVIDADE
        </h3>
        <p style="margin-bottom: 0; font-size: 14px; color: rgba(255,255,255,0.9); text-align: center; text-shadow: 1px 1px 1px rgba(0,0,0,0.1);">
            Responsáveis com maior produtividade em cada etapa do processo
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Medalhas para os três primeiros lugares
    medal_badges = ["🥇 Primeiro Lugar", "🥈 Segundo Lugar", "🥉 Terceiro Lugar"]
    
    # Agrupar etapas em categorias para melhor organização
    categorias = {
        "Pesquisa": ["Deu ganho na Busca", "Deu perca na Busca", "Busca Realizada"],
        "Documentação": ["Requerimento Montado", "Montar Requerimento"],
        "Processamento": ["Solicitado ao Cartório Origem", "Aguardandocartorio Origem"],
        "Finalização": ["Certidao Emitida", "Certidao Fisica Enviada", "Certidao Fisica Entregue"],
        "Exceções": ["Devolucao Adm", "Devolucao Adm Verificado", "Devolutiva Requerimento", "Solicitacao Duplicado"]
    }
    
    # Mapear etapas para suas categorias
    etapa_para_categoria = {}
    for categoria, etapas in categorias.items():
        for etapa in etapas:
            for destaque_etapa in destaques.keys():
                if etapa.lower() in destaque_etapa.lower():
                    etapa_para_categoria[destaque_etapa] = categoria
    
    # Usar as categorias não vazias
    categorias_usadas = set(etapa_para_categoria.values())
    
    # Badge para cada categoria no topo
    st.write("### Categorias de Produtividade")
    for categoria in sorted(categorias_usadas):
        st.badge(categoria)
    
    # Criar colunas para as categorias
    num_categorias = len(categorias_usadas)
    if num_categorias > 0:
        # Para cada categoria, mostrar os destaques
        for categoria in sorted(categorias_usadas):
            st.subheader(categoria)
            
            # Pegar etapas desta categoria
            etapas_categoria = [etapa for etapa, cat in etapa_para_categoria.items() if cat == categoria]
            
            # Para cada etapa na categoria, criar um container
            for etapa in etapas_categoria:
                responsaveis = destaques[etapa]['responsaveis']
                campo_data = destaques[etapa]['campo_data']
                campo_resp = destaques[etapa]['campo_resp']
                
                # Usar container com borda para cada etapa
                with st.container(border=True):
                    # Usar badge para etapa
                    st.badge(etapa)
                    
                    # Mostrar top 3 responsáveis com métricas em colunas horizontais
                    cols = st.columns(min(3, len(responsaveis)))
                    
                    # Distribuir os responsáveis nas colunas
                    for i, (resp, qtd) in enumerate(responsaveis):
                        if i < len(cols):  # Garantir que temos colunas suficientes
                            with cols[i]:
                                # Usar layout vertical para cada responsável
                                st.badge(medal_badges[i])
                                st.write(f"**{resp}**")
                                st.metric(
                                    label="",
                                    value=qtd,
                                    help=f"Registros processados por {resp}"
                                )
                    
                    # Adicionar detalhes em popover
                    with st.popover("📊 Detalhes", use_container_width=True):
                        st.caption("Campos técnicos:")
                        st.code(f"Data: {campo_data}\nResponsável: {campo_resp}", language="python")
    else:
        st.info("Não foram encontradas categorias de produtividade para exibir.")
    
    # Adicionar instrução sobre como usar os destaques
    with st.container(border=True):
        st.subheader("Como usar estes destaques")
        st.write("""
        Estes destaques mostram os responsáveis mais produtivos em cada etapa do processo. 
        Para ver uma análise completa por responsável, navegue até a aba **👥 Por Responsável Específico** 
        e selecione a etapa desejada.
        """)
        
        # Adicionar ícones de medalha como referência
        st.markdown("""
        **Legenda:**
        🥇 Primeiro Lugar - Maior produtividade
        🥈 Segundo Lugar - Segunda maior produtividade
        🥉 Terceiro Lugar - Terceira maior produtividade
        """)

def mostrar_metricas_etapa(df, campos_data, periodo_inicio, periodo_fim):
    """
    Mostra as métricas de produtividade por etapa
    
    Args:
        df (pandas.DataFrame): DataFrame com dados filtrados
        campos_data (list): Lista de campos de data para análise
        periodo_inicio (datetime): Data inicial do período
        periodo_fim (datetime): Data final do período
    """
    # Usando st.markdown em vez de st.html
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
    
    # Usando colunas com bordas para as métricas principais
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        # Usar st.metric com borda em vez de HTML customizado
        st.metric(
            label="📊 Total de Atividades",
            value=f"{total_geral:,}",
            help="Total em todas as etapas",
            delta=None,
            border=True
        )
    
    with col2:
        # Usar st.metric com borda
        st.metric(
            label="📅 Dias com Atividades",
            value=f"{num_dias_com_atividade} de {num_dias_periodo}",
            help=f"{taxa_dias_ativos:.0f}% do período",
            delta=None,
            border=True
        )
    
    with col3:
        media_valor = total_geral/num_dias_com_atividade if num_dias_com_atividade > 0 else 0
        # Usar st.metric com borda
        st.metric(
            label="📈 Média Diária",
            value=f"{media_valor:.1f}",
            help="Atividades por dia",
            delta=None,
            border=True
        )
    
    # Exibir informações sobre a contagem
    if 'ID' in df.columns:
        with st.popover("ℹ️ Informações sobre a contagem", use_container_width=True):
            st.info(f"**Total de registros únicos**: {len(todos_ids)}")
            st.info(f"**Total de atividades somadas**: {total_geral}")
            st.write("A diferença ocorre porque um mesmo registro pode estar em múltiplas etapas.")
    
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
    
    # Criar cards para métricas de pesquisa usando colunas com bordas
    if "Deu ganho na Busca" in dados_campos and "Deu perca na Busca" in dados_campos and "Busca Realizada" in dados_campos:
        ganho_busca = dados_campos["Deu ganho na Busca"]["total"]
        perca_busca = dados_campos["Deu perca na Busca"]["total"]
        total_busca = dados_campos["Busca Realizada"]["total"]
        
        # Taxa de sucesso
        taxa_sucesso = (ganho_busca / total_busca * 100) if total_busca > 0 else 0
        
        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            # Usar métricas com borda e badges
            st.metric(
                label="💹 Ganhos de Pesquisa",
                value=f"{ganho_busca:,}",
                help=f"{taxa_sucesso:.1f}% de sucesso",
                delta="Positivo",
                delta_color="normal",
                border=True
            )
            st.badge("SUCESSO")
            
            # Usar popover para mostrar a descrição
            with st.popover("📝 Descrição", use_container_width=True):
                st.write(descricoes_metricas["Deu ganho na Busca"])
        
        with col2:
            # Usar métricas com borda e badges
            st.metric(
                label="📉 Percas de Pesquisa",
                value=f"{perca_busca:,}",
                help=f"{100-taxa_sucesso:.1f}% de insucesso",
                delta="Negativo",
                delta_color="inverse",
                border=True
            )
            st.badge("INSUCESSO")
            
            # Usar popover para mostrar a descrição
            with st.popover("📝 Descrição", use_container_width=True):
                st.write(descricoes_metricas["Deu perca na Busca"])
        
        with col3:
            # Usar métricas com borda e badges
            st.metric(
                label="Busca Realizada",
                value=f"{total_busca:,}",
                help=f"Soma de ganhos e percas ({ganho_busca:,} + {perca_busca:,})",
                delta=None,
                border=True
            )
            st.badge("TOTAL")
            
            # Usar popover para mostrar a descrição
            with st.popover("📝 Descrição", use_container_width=True):
                st.write(descricoes_metricas["Busca Realizada"])
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
            
            # Criar colunas com borda
            cols = st.columns(NUM_COLUNAS, gap="medium")
            
            # Preencher cada coluna
            for j, etapa in enumerate(etapas_linha):
                if j < len(cols):  # Verificar se ainda há colunas disponíveis
                    with cols[j]:
                        dados = dados_campos[etapa]
                        
                        # Usar métricas nativas do Streamlit
                        st.metric(
                            label=etapa.replace('_', ' '),
                            value=f"{dados['total']:,}",
                            help="Total de registros",
                            delta=None,
                            border=True
                        )
                        
                        # Usar badge para status
                        st.badge(etapa)
                        
                        # Descrição como texto normal
                        if etapa in descricoes_metricas:
                            with st.popover("📝 Descrição", use_container_width=True):
                                st.write(descricoes_metricas.get(etapa, ''))
                        
                        # Estatísticas usando colunas nativas do Streamlit
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric(
                                label="Média por Dia",
                                value=f"{dados['media_diaria']:.1f}",
                                help=f"{dados['num_dias']} dias ativos",
                                delta=None
                            )
                        
                        with col_b:
                            st.metric(
                                label="Dia Mais Produtivo",
                                value=f"{dados['dia_max'].strftime('%d/%m')}",
                                help=f"{dados['valor_max']} registros",
                                delta=None
                            )
                        
                        # Registros únicos como texto normal
                        if 'ID' in df.columns and etapa in ids_por_etapa:
                            num_ids = len(ids_por_etapa[etapa])
                            st.write(f"**Registros únicos:** {num_ids}")
    
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
            cols = st.columns(NUM_COLUNAS, gap="medium")
            
            # Preencher cada coluna
            for j, etapa in enumerate(etapas_linha):
                if j < len(cols):  # Verificar se ainda há colunas disponíveis
                    with cols[j]:
                        dados = dados_campos[etapa]
                        
                        # Usar métricas nativas do Streamlit com badge de erro
                        st.metric(
                            label=etapa.replace('_', ' '),
                            value=f"{dados['total']:,}",
                            help="Total de registros",
                            delta=None,
                            border=True
                        )
                        
                        # Badge indicando problemas
                        st.badge(etapa)
                        
                        # Descrição como texto normal
                        if etapa in descricoes_metricas:
                            with st.popover("📝 Descrição", use_container_width=True):
                                st.write(descricoes_metricas.get(etapa, ''))
                        
                        # Estatísticas usando colunas nativas do Streamlit
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric(
                                label="Média por Dia",
                                value=f"{dados['media_diaria']:.1f}",
                                help=f"{dados['num_dias']} dias ativos",
                                delta=None
                            )
                        
                        with col_b:
                            st.metric(
                                label="Dia Mais Produtivo",
                                value=f"{dados['dia_max'].strftime('%d/%m')}",
                                help=f"{dados['valor_max']} registros",
                                delta=None
                            )
                        
                        # Registros únicos como texto normal
                        if 'ID' in df.columns and etapa in ids_por_etapa:
                            num_ids = len(ids_por_etapa[etapa])
                            st.write(f"**Registros únicos:** {num_ids}")
    
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
        "Dia Mais Produtivo": st.column_config.DateColumn("Dia Mais Produtivo", format="DD/MM/YYYY"),
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
        hide_index=True,
        height=400
    )
    
    # Para o caso de precisar formatar nomes em colunas de resumo
    if isinstance(df_resumo, pd.DataFrame) and 'Etapa' in df_resumo.columns:
        df_resumo['Etapa'] = df_resumo['Etapa'].apply(lambda x: str(x).replace('_', ' ') if '_' in str(x) else x)

def analisar_distribuicao_temporal(df, campos_data):
    """
    Análise de distribuição temporal dos dados
    
    Args:
        df (pandas.DataFrame): DataFrame com dados filtrados
        campos_data (list): Lista de campos de data para análise
    """
    st.markdown("### Análise de Distribuição Temporal")
    
    # Verificar se temos dados suficientes para análise
    if df.empty:
        st.warning("Não há dados suficientes para análise temporal.")
        return
    
    # Preparar os dados para visualização
    dados_temporais = []
    
    # Processar cada campo de data
    for campo in campos_data:
        if campo in df.columns:
            # Filtrar registros que têm data neste campo
            serie_data = df[campo].dropna()
            
            if not serie_data.empty:
                # Converter para datetime se ainda não estiver nesse formato
                serie_data = pd.to_datetime(serie_data)
                
                # Agrupar por data (sem hora)
                contagem_diaria = serie_data.dt.date.value_counts().sort_index()
                
                # Converter para DataFrame
                df_campo = pd.DataFrame({
                    'Data': contagem_diaria.index,
                    'Quantidade': contagem_diaria.values,
                    'Etapa': formatar_nome_etapa(campo)
                })
                
                dados_temporais.append(df_campo)
    
    # Combinar todos os dados
    if not dados_temporais:
        st.warning("Não há dados temporais disponíveis para análise.")
        return
        
    df_temporal = pd.concat(dados_temporais, ignore_index=True)
    
    # Criar gráfico de linha para visualizar a distribuição temporal
    fig = px.line(
        df_temporal,
        x='Data',
        y='Quantidade',
        color='Etapa',
        title='Distribuição Temporal dos Dados',
        labels={
            'Data': 'Data',
            'Quantidade': 'Quantidade de Registros',
            'Etapa': 'Etapa do Processo'
        },
        markers=True
    )
    
    fig.update_layout(
        height=500,
        xaxis_title='Data',
        yaxis_title='Quantidade de Registros',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Adicionar informações sobre o gráfico
    st.info("""
    **Análise de Distribuição Temporal:**
    • O gráfico de linha mostra a distribuição dos registros ao longo do tempo.
    • Cada linha representa uma etapa do processo.
    • Compare as alturas das linhas para entender como as etapas variam no tempo.
    """)

def analisar_matriz_responsavel_data(df, campos_data, mapeamento_campos):
    """
    Cria uma matriz de visualização de responsáveis por data para cada par de campos
    
    Args:
        df (pandas.DataFrame): DataFrame com dados filtrados
        campos_data (list): Lista de campos de data para análise
        mapeamento_campos (dict): Dicionário que mapeia campos de data para campos de responsável
    """
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4338CA 0%, #6366F1 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h3 style="margin-top: 0; color: white; font-size: 22px; font-weight: 700; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); color: #FFFFFF !important;">
            🔄 MATRIZ RESPONSÁVEL x DATA
        </h3>
        <p style="margin-bottom: 0; font-size: 14px; color: rgba(255,255,255,0.9); text-align: center; color: #FFFFFF !important;">
            Visualização detalhada de responsáveis por data para cada etapa do processo
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Usar badges para informações
    col1, col2, col3 = st.columns(3)
    with col1:
        st.badge("Distribuição de Registros")
    with col2:
        st.badge("Análise Temporal") 
    with col3:
        st.badge("Detalhamento por Responsável")
    
    st.info("""
    **O que mostra esta análise?**
    • Distribuição de registros por responsável em cada data
    • Visão detalhada do volume de trabalho diário por responsável
    • Identificação de padrões de produtividade ao longo do tempo
    • Comparação visual da distribuição de carga de trabalho
    """)
    
    # Verificar pares de campos válidos (data e responsável)
    pares_validos = []
    for campo_data in campos_data:
        if campo_data in df.columns and campo_data in mapeamento_campos:
            campo_resp = mapeamento_campos[campo_data]
            if campo_resp in df.columns:
                # Verificar se existem dados para este par
                df_temp = df.dropna(subset=[campo_data, campo_resp])
                if not df_temp.empty:
                    nome_etapa = formatar_nome_etapa(campo_data)
                    pares_validos.append({
                        'campo_data': campo_data,
                        'campo_resp': campo_resp,
                        'nome_etapa': nome_etapa,
                        'num_registros': len(df_temp)
                    })
    
    if not pares_validos:
        st.warning("Não foram encontrados pares válidos de campos de data e responsável para análise.")
        return
    
    # Ordenar pares por número de registros (decrescente)
    pares_validos = sorted(pares_validos, key=lambda x: x['num_registros'], reverse=True)
    
    # Mostrar todas as etapas diretamente sem necessidade de seleção
    st.write("### Relatórios por Etapa")
    
    # Opção de granularidade temporal para aplicar em todas as etapas
    opcoes_temporais = ["Diária", "Semanal", "Mensal"]
    granularidade = st.radio(
        "Selecione a granularidade temporal para todos os relatórios:",
        options=opcoes_temporais,
        horizontal=True,
        key="matriz_granularidade_global"
    )
    
    # Para cada etapa, criar um expansor com suas análises
    for i, par in enumerate(pares_validos):
        campo_data = par['campo_data']
        campo_resp = par['campo_resp']
        nome_etapa = par['nome_etapa']
        num_registros = par['num_registros']
        
        # Criar um expansor para esta etapa (expandido por padrão para as primeiras 3)
        with st.expander(f"{nome_etapa} ({num_registros} registros)", expanded=(i < 3)):
            # Filtrar dados para o par atual
            df_filtrado = df.dropna(subset=[campo_data, campo_resp]).copy()
            
            # Converter campo de data para datetime se necessário
            df_filtrado[campo_data] = pd.to_datetime(df_filtrado[campo_data])
            
            # Extrair data (sem hora)
            df_filtrado['data_apenas'] = df_filtrado[campo_data].dt.date
            
            # Ajustar agrupamento temporal conforme granularidade
            if granularidade == "Semanal":
                # Agrupar por semana (primeiro dia da semana)
                df_filtrado['periodo'] = df_filtrado[campo_data].apply(
                    lambda x: (x - pd.Timedelta(days=x.weekday())).date()
                )
                formato_data = "%d/%m/%Y"
                descricao_periodo = "Semana"
            elif granularidade == "Mensal":
                # Agrupar por mês (primeiro dia do mês)
                df_filtrado['periodo'] = df_filtrado[campo_data].apply(
                    lambda x: x.replace(day=1).date()
                )
                formato_data = "%b/%Y"
                descricao_periodo = "Mês"
            else:  # Diária
                # Usar a data sem alteração
                df_filtrado['periodo'] = df_filtrado['data_apenas']
                formato_data = "%d/%m/%Y"
                descricao_periodo = "Data"
            
            # Contar registros por responsável e período
            contagem = df_filtrado.groupby([campo_resp, 'periodo']).size().reset_index()
            contagem.columns = ['responsavel', 'periodo', 'quantidade']
            
            # Se não houver dados, mostrar mensagem e continuar com próxima etapa
            if contagem.empty:
                st.warning(f"Não há dados suficientes para a etapa '{nome_etapa}' com a granularidade {granularidade.lower()}.")
                continue
            
            # Criar DataFrame pivot para a matriz
            matriz = contagem.pivot_table(
                index='responsavel',
                columns='periodo',
                values='quantidade',
                fill_value=0
            )
            
            # Adicionar totais
            matriz['Total'] = matriz.sum(axis=1)
            totais_coluna = matriz.sum(axis=0)
            totais_coluna.name = 'Total'
            matriz = pd.concat([matriz, pd.DataFrame([totais_coluna])], axis=0)
            
            # Ordenar matriz por total (decrescente)
            matriz = matriz.sort_values('Total', ascending=False)
            
            # Formatar colunas de data
            matriz_display = matriz.copy()
            colunas_formatadas = {}
            for col in matriz_display.columns:
                if hasattr(col, 'strftime'):
                    colunas_formatadas[col] = col.strftime(formato_data)
                else:
                    colunas_formatadas[col] = col
            matriz_display = matriz_display.rename(columns=colunas_formatadas)
            
            # Exibir título da seção com badge destacado
            st.subheader(f"Matriz de Responsáveis por {descricao_periodo}")
            st.badge(nome_etapa)
            
            # Criar um container com informações sobre o total de registros
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    # Informações sobre o conjunto de dados
                    st.metric(
                        label="Total de Registros",
                        value=f"{len(df_filtrado):,}",
                        help=f"Número total de registros para {nome_etapa}"
                    )
                with col2:
                    # Informações sobre períodos e responsáveis
                    st.metric(
                        label="Distribuição",
                        value=f"{len(matriz)-1} resp. x {len(matriz.columns)-1} períodos",
                        help=f"Matriz de {len(matriz)-1} responsáveis por {len(matriz.columns)-1} períodos"
                    )
            
            # Limite para número de responsáveis a exibir
            num_responsaveis = len(matriz) - 1  # -1 para excluir a linha de total
            
            # Se tivermos até 10 responsáveis, mostrar todos
            # Se tivermos mais, mostrar apenas os top 10
            if num_responsaveis <= 10:
                responsaveis_filtrados = list(matriz.iloc[:-1].index) + ['Total']
            else:
                responsaveis_filtrados = list(matriz.iloc[:-1].index[:10]) + ['Total']
                
            matriz_filtrada = matriz_display.loc[responsaveis_filtrados]
            
            # Configurar colunas para exibição da tabela
            config_colunas = {}
            colunas_periodo = [col for col in matriz_filtrada.columns if col != 'Total']
            
            # Configuração de colunas melhorada para datas
            for col in colunas_periodo:
                config_colunas[col] = st.column_config.NumberColumn(
                    col,
                    format="%d",
                    help=f"Registros em {col}"
                )
            
            # Configuração especial para coluna de total
            config_colunas['Total'] = st.column_config.NumberColumn(
                "Total",
                format="%d",
                help="Total de registros por responsável"
            )
            
            # Exibir tabela com formatação
            st.dataframe(
                matriz_filtrada,
                column_config=config_colunas,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Visualização de heatmap
            st.subheader(f"Heatmap de Produtividade: {nome_etapa}")
            
            # Tab para escolher diferentes visualizações
            tab1, tab2 = st.tabs(["Heatmap Normal", "Heatmap Normalizado"])
            
            with tab1:
                # Preparar dados para heatmap (excluindo coluna de total)
                heatmap_data = matriz_filtrada.drop(columns=['Total'])
                
                # Criar figura do heatmap
                fig = px.imshow(
                    heatmap_data,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="Viridis",
                    title=f"Distribuição de {nome_etapa} por Responsável e {descricao_periodo}",
                    labels=dict(x=descricao_periodo, y="Responsável", color="Quantidade")
                )
                
                # Melhorar layout
                fig.update_layout(
                    height=max(400, 50 * len(responsaveis_filtrados)),
                    xaxis_title=descricao_periodo,
                    yaxis_title="Responsável",
                    coloraxis_showscale=True,
                    margin=dict(l=50, r=20, t=50, b=50),
                    template="plotly_white"
                )
                
                # Ajustar texto do heatmap
                fig.update_traces(
                    texttemplate="%{z}",
                    textfont={"size": 10}
                )
                
                st.plotly_chart(fig, use_container_width=True, theme="streamlit")
            
            with tab2:
                # Preparar dados para heatmap normalizado (excluindo coluna de total)
                heatmap_norm = matriz_filtrada.drop(columns=['Total']).copy()
                
                # Normalizar por linha (responsável)
                for idx in heatmap_norm.index:
                    row_sum = heatmap_norm.loc[idx].sum()
                    # Garantir que row_sum é um valor escalar
                    # pandas já importado no início do arquivo
                    if isinstance(row_sum, pd.Series):
                        # Se for uma pandas Series, pegar o primeiro valor como float
                        if len(row_sum) > 0:
                            row_sum = float(row_sum.iloc[0])
                        else:
                            row_sum = 0.0
                    elif isinstance(row_sum, (list, tuple)):
                        # Se for lista ou tupla, pegar o primeiro elemento
                        row_sum = float(row_sum[0]) if row_sum else 0.0
                    else:
                        # Caso seja um escalar
                        row_sum = float(row_sum)
                    if row_sum > 0:  # Evitar divisão por zero
                        heatmap_norm.loc[idx] = heatmap_norm.loc[idx] / row_sum * 100
                
                # Criar figura do heatmap normalizado
                fig_norm = px.imshow(
                    heatmap_norm,
                    text_auto='.1f',
                    aspect="auto",
                    color_continuous_scale="RdBu_r",
                    title=f"Distribuição Percentual de {nome_etapa} por Responsável",
                    labels=dict(x=descricao_periodo, y="Responsável", color="% do Total")
                )
                
                # Melhorar layout
                fig_norm.update_layout(
                    height=max(400, 50 * len(responsaveis_filtrados)),
                    xaxis_title=descricao_periodo,
                    yaxis_title="Responsável",
                    coloraxis_showscale=True,
                    margin=dict(l=50, r=20, t=50, b=50),
                    template="plotly_white"
                )
                
                # Ajustar texto do heatmap
                fig_norm.update_traces(
                    texttemplate="%{z:.1f}%",
                    textfont={"size": 10}
                )
                
                st.plotly_chart(fig_norm, use_container_width=True, theme="streamlit")
            
            # Análise de tendência por período
            st.subheader(f"Tendência de Produtividade ao Longo do Tempo: {nome_etapa}")
            
            # Tendência por responsável
            fig_tendencia = px.line(
                contagem,
                x='periodo',
                y='quantidade',
                color='responsavel',
                markers=True,
                title=f"Evolução de {nome_etapa} por Responsável ao Longo do Tempo",
                labels={
                    'periodo': descricao_periodo,
                    'quantidade': 'Quantidade',
                    'responsavel': 'Responsável'
                },
            )
            
            # Melhorar layout
            fig_tendencia.update_layout(
                height=500,
                xaxis_title=descricao_periodo,
                yaxis_title="Quantidade",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(l=20, r=20, t=50, b=100),
                template="plotly_white"
            )
            
            st.plotly_chart(fig_tendencia, use_container_width=True, theme="streamlit")
            
            # Separador visual entre as etapas
            st.divider()
    
    # Adicionar explicação sobre a utilidade da matriz
    with st.expander("Como utilizar esta análise", expanded=False):
        st.markdown("""
        ### Como interpretar a Matriz Responsável x Data
        
        Esta visualização permite analisar a distribuição do trabalho entre os responsáveis ao longo do tempo para cada etapa.
        
        **Principais insights que você pode obter:**
        
        1. **Distribuição da carga de trabalho:**
           - Identifique quais responsáveis estão realizando mais atividades
           - Detecte possíveis desequilíbrios na distribuição do trabalho
        
        2. **Padrões temporais:**
           - Observe picos de atividade em determinados períodos
           - Identifique tendências sazonais ou cíclicas
        
        3. **Produtividade individual:**
           - Compare o volume de trabalho entre diferentes responsáveis
           - Identifique responsáveis com maior consistência ao longo do tempo
        
        4. **Oportunidades de melhoria:**
           - Redistribuição mais equilibrada da carga de trabalho
           - Reforço em períodos de maior demanda
        """)

def mostrar_tabelas_por_etapa(df, campos_data):
    """
    Exibe tabelas separadas para cada etapa do processo, sem necessidade de filtros
    
    Args:
        df (pandas.DataFrame): DataFrame com dados filtrados
        campos_data (list): Lista de campos de data para análise
    """
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4E7CF6 0%, #8FADFA 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h3 style="margin-top: 0; color: white; font-size: 22px; font-weight: 700; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); color: #FFFFFF !important;">
            📑 TABELAS POR ETAPA DO PROCESSO
        </h3>
        <p style="margin-bottom: 0; font-size: 14px; color: rgba(255,255,255,0.9); text-align: center; color: #FFFFFF !important;">
            Visualização detalhada de registros para cada etapa, sem necessidade de filtros
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    **Tabelas por Etapa do Processo**
    • Visualize os registros de cada etapa em tabelas separadas
    • Todos os dados são mostrados sem necessidade de aplicar filtros
    • Use os expansores abaixo para visualizar cada etapa específica
    """)
    
    # Lista das etapas solicitadas e seus campos correspondentes
    etapas_para_mostrar = [
        ("Deu ganho na Busca", "UF_CRM_DATA_SOLICITAR_REQUERIMENTO"),
        ("Deu perca na Busca", "UF_CRM_DEVOLUTIVA_BUSCA"),
        ("Certidao Emitida", "UF_CRM_DATA_CERTIDAO_EMITIDA"),
        ("Certidao Fisica Entregue", "UF_CRM_DATA_CERTIDAO_FISICA_ENTREGUE"),
        ("Certidao Fisica Enviada", "UF_CRM_DATA_CERTIDAO_FISICA_ENVIADA"),
        ("DEVOLUÇÃO ADM", "UF_CRM_DEVOLUCAO_ADM"),
        ("DEVOLUÇÃO ADM VERIFICADO", "UF_CRM_DEVOLUCAO_ADM_VERIFICADO"),
        ("Devolutiva Requerimento", "UF_CRM_DEVOLUTIVA_REQUERIMENTO"),
        ("Montar Requerimento", "UF_CRM_DATA_MONTAR_REQUERIMENTO"),
        ("SOLICITAÇÃO DUPLICADA", "UF_CRM_SOLICITACAO_DUPLICADA")
    ]
    
    # Obter o mapeamento de campos para poder mostrar os responsáveis específicos
    mapeamento_campos = obter_mapeamento_campos()
    
    # Definir as colunas que sempre serão exibidas (informações básicas)
    colunas_basicas = ['ID', 'TITLE', 'ASSIGNED_BY_NAME']
    
    # Para cada etapa, criar um expansor com a tabela correspondente
    for nome_etapa, campo_data in etapas_para_mostrar:
        # Verificar se o campo existe no DataFrame
        if campo_data not in df.columns:
            continue
            
        # Filtrar os registros que têm valor não nulo para esta etapa
        df_etapa = df.dropna(subset=[campo_data]).copy()
        
        # Se não houver registros, pular esta etapa
        if df_etapa.empty:
            continue
        
        # Formatar a coluna de data para exibição
        df_etapa['Data_Formatada'] = pd.to_datetime(df_etapa[campo_data]).dt.strftime('%d/%m/%Y %H:%M')
        
        # Obter contagem de registros para esta etapa
        num_registros = len(df_etapa)
        
        # Verificar se existe um campo de responsável específico para esta etapa
        campo_resp = mapeamento_campos.get(campo_data, None)
        responsavel_disponivel = campo_resp in df_etapa.columns
        
        # Criar título para o expansor com contagem de registros
        titulo_expansor = f"{nome_etapa} ({num_registros} registros)"
        
        # Determinar se o expansor deve começar expandido (para etapas com mais registros)
        etapas_principais = ["Deu ganho na Busca", "Certidao Emitida", "Deu perca na Busca"]
        expandir_inicial = nome_etapa in etapas_principais
        
        # Criar o expansor para esta etapa
        with st.expander(titulo_expansor, expanded=expandir_inicial):
            # Adicionar informações adicionais sobre a etapa
            st.markdown(f"""
            <div style="background-color: #f0f7ff; border-radius: 8px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #3182ce;">
                <h4 style="margin-top: 0; color: #2c5282; font-size: 16px;">{nome_etapa}</h4>
                <p style="margin-bottom: 5px;">
                    <strong>Total de registros:</strong> {num_registros}<br>
                    <strong>Campo no sistema:</strong> {campo_data}<br>
                    <strong>Campo de responsável:</strong> {campo_resp if responsavel_disponivel else "Não disponível"}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Selecionar as colunas a exibir
            colunas_exibir = colunas_basicas.copy()
            
            # Adicionar coluna de responsável específico se disponível
            if responsavel_disponivel:
                colunas_exibir.append(campo_resp)
            
            # Adicionar data formatada
            colunas_exibir.append('Data_Formatada')
            
            # Verificar quais colunas realmente existem no DataFrame
            colunas_disponiveis = [col for col in colunas_exibir if col in df_etapa.columns or col == 'Data_Formatada']
            
            # Remover possíveis duplicatas da lista
            colunas_disponiveis = list(dict.fromkeys(colunas_disponiveis))
            
            # Configuração de colunas para exibição
            config_colunas = {
                "ID": st.column_config.TextColumn("ID"),
                "TITLE": st.column_config.TextColumn("Título"),
                "ASSIGNED_BY_NAME": st.column_config.TextColumn("Responsável Geral"),
                "Data_Formatada": st.column_config.TextColumn("Data e Hora")
            }
            
            # Adicionar configuração para o responsável específico se disponível
            if responsavel_disponivel and campo_resp in df_etapa.columns:
                config_colunas[campo_resp] = st.column_config.TextColumn("Responsável Específico")
            
            # Exibir tabela com todas as informações
            st.dataframe(
                df_etapa[colunas_disponiveis],
                column_config=config_colunas,
                use_container_width=True,
                hide_index=True
            )
            
            # Adicionar informações resumidas sobre os responsáveis
            if responsavel_disponivel and campo_resp in df_etapa.columns:
                st.subheader("Resumo por Responsável")
                
                # Contar registros por responsável
                contagem_resp = df_etapa[campo_resp].value_counts().reset_index()
                contagem_resp.columns = ['Responsável', 'Quantidade']
                
                # Calcular percentual
                contagem_resp['Percentual'] = (contagem_resp['Quantidade'] / contagem_resp['Quantidade'].sum() * 100).round(2)
                
                # Ordenar por quantidade (decrescente)
                contagem_resp = contagem_resp.sort_values('Quantidade', ascending=False)
                
                # Exibir resumo por responsável
                st.dataframe(
                    contagem_resp,
                    column_config={
                        "Responsável": st.column_config.TextColumn("Responsável"),
                        "Quantidade": st.column_config.NumberColumn("Quantidade", format="%d"),
                        "Percentual": st.column_config.ProgressColumn(
                            "% do Total",
                            format="%.2f%%",
                            min_value=0,
                            max_value=100
                        )
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Mostrar gráfico de distribuição por responsável
                fig = px.pie(
                    contagem_resp,
                    values='Quantidade',
                    names='Responsável',
                    title=f"Distribuição de {nome_etapa} por Responsável",
                    hole=0.4
                )
                
                fig.update_layout(
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Adicionar explicação sobre o uso desta visualização
    with st.expander("Como usar as tabelas por etapa", expanded=False):
        st.markdown("""
        ### Como utilizar as Tabelas por Etapa
        
        Esta visualização permite acessar facilmente os registros de cada etapa do processo sem necessidade de aplicar filtros. Cada expansor contém:
        
        1. **Tabela completa** com todos os registros para a etapa selecionada
        2. **Opção de download** para exportar os dados em formato CSV
        3. **Resumo por responsável** (quando disponível) mostrando a distribuição do trabalho
        
        **Dicas de uso:**
        
        - Clique nos expansores para abrir/fechar cada etapa
        - Use a função de busca nas tabelas para encontrar registros específicos
        - Para exportar dados para análise externa, use o botão "Baixar dados em CSV"
        - Para ver a quantidade de registros por etapa, observe o número entre parênteses
        """)
    
    # Adicionar botão para imprimir todas as tabelas
    if st.button("🖨️ Imprimir Todas as Tabelas", help="Prepara a página para impressão de todas as tabelas"):
        st.markdown("""
        <style>
        @media print {
            .stButton, .css-ch5dnh {
                display: none !important;
            }
            .css-1rs6os {
                padding: 0 !important;
            }
            .css-1y4p8pa {
                margin: 0 !important;
                padding: 0 !important;
            }
        }
        </style>
        <script>
        window.print();
        </script>
        """, unsafe_allow_html=True)
        st.success("Página preparada para impressão. Use a função de impressão do seu navegador (Ctrl+P).")