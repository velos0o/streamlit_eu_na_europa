import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io
from .data_loader import carregar_estagios_bitrix

def visualizar_cartorio_dados(df):
    """
    Visualiza os dados detalhados dos cartórios.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos cartórios
    """
    # Aplicar estilos aprimorados
    aplicar_estilos_cartorio()
    
    if df.empty:
        st.warning("Não há dados disponíveis para visualização.")
        return
    
    # Verificar se temos as colunas necessárias
    colunas_necessarias = ['STAGE_ID', 'ASSIGNED_BY_ID', 'ASSIGNED_BY_NAME']
    
    colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
    if colunas_faltantes:
        st.error(f"Colunas necessárias não encontradas: {', '.join(colunas_faltantes)}")
        # st.write("Colunas disponíveis:", df.columns.tolist()) # Log comentado
        return
    
    # Obter estágios
    df_stages = carregar_estagios_bitrix()
    
    # Filtrar apenas os estágios dos pipelines de cartório
    if 'ENTITY_ID' in df_stages.columns and 'STATUS_ID' in df_stages.columns and 'NAME' in df_stages.columns:
        # Encontrar os pipelines corretos
        pipeline_entities = df_stages[df_stages['NAME'].str.contains('CARTÓRIO', case=False, na=False)]['ENTITY_ID'].unique()
        
        # Filtrar estágios desses pipelines
        df_stages_filtered = df_stages[df_stages['ENTITY_ID'].isin(pipeline_entities)]
        
        # Criar um mapeamento de STAGE_ID para nome do estágio
        stage_mapping = dict(zip(df_stages_filtered['STATUS_ID'], df_stages_filtered['NAME']))
        
        # Adicionar nome do estágio ao DataFrame principal
        df['STAGE_NAME'] = df['STAGE_ID'].map(stage_mapping)
    else:
        # Caso não consiga obter o nome dos estágios, usar o ID
        df['STAGE_NAME'] = df['STAGE_ID']
    
    # Título principal
    st.markdown("""
    <h1 style="text-align: center; font-size: 36px; font-weight: 900; color: #1A237E; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 4px solid #1976D2;">
    <strong>MONITORAMENTO DE FUNIL DE EMISSÕES</strong>
    </h1>
    """, unsafe_allow_html=True)

    # Verificar se o DataFrame está vazio
    if df.empty:    
        st.warning("Não há dados disponíveis para exibição com os filtros selecionados.")
    else:
        # NÃO FILTRAR NOVAMENTE - usar apenas os dados já filtrados
        # Como os dados já foram filtrados na etapa de carregamento em cartorio_main.py,
        # não devemos aplicar filtros adicionais aqui para não causar inconsistências.
        
        # Apenas validar que os dados estão corretos
        if 'CATEGORY_ID' in df.columns:
            # Contar registros por categoria para exibição nas métricas
            total_registros = len(df)
            count_cat_16 = (df['CATEGORY_ID'] == 16).sum()
            count_cat_34 = (df['CATEGORY_ID'] == 34).sum()
            
            # Validar se os dados correspondem ao esperado
            if count_cat_16 + count_cat_34 != total_registros:
                st.warning(f"""
                **Atenção:** Inconsistência nos dados das métricas.
                Total: {total_registros}, Categorias: {count_cat_16 + count_cat_34}
                Isso pode afetar os resultados exibidos.
                """)
        else:
            # Se não temos a coluna, não podemos validar
            count_cat_16 = 0
            count_cat_34 = 0
            total_registros = len(df)
        
        # Contar total de processos na etapa SUCCESS
        success_count = 0
        
        # Definir todos os códigos que representam SUCCESS
        success_codes = [
            'SUCCESS', 
            'DT1052_16:SUCCESS', 
            'DT1052_34:SUCCESS',
            # Códigos para Certidão Física
            'DT1052_16:UC_JRGCW3',
            'DT1052_34:UC_84B1S2',
            'UC_JRGCW3',
            'UC_84B1S2',
            # Códigos para Certidão Emitida
            'DT1052_16:CLIENT',
            'DT1052_34:CLIENT',
            'DT1052_34:UC_D0RG5P',
            'CLIENT',
            'UC_D0RG5P'
        ]
        
        # Verificar quais colunas estão disponíveis
        success_columns = []
        if 'STAGE_NAME' in df.columns:
            success_columns.append('STAGE_NAME')
        if 'STAGE_ID' in df.columns:
            success_columns.append('STAGE_ID')
            
        # Se encontramos alguma coluna para verificar
        if success_columns:
            # Criar um filtro combinado para encontrar SUCCESS em qualquer coluna disponível
            success_mask = pd.Series(False, index=df.index)
            
            for column in success_columns:
                for code in success_codes:
                    # Verificar correspondência exata com os códigos de sucesso
                    success_mask = success_mask | (df[column] == code)
                    # Verificar também se contém o código (para caso de textos mais longos)
                    success_mask = success_mask | df[column].str.contains(f":{code}$", regex=True, na=False)
            
            # Contar registros que satisfazem o filtro
            success_count = df[success_mask].shape[0]
            
            # Adicionar coluna indicando se o processo foi concluído com sucesso
            df['IS_SUCCESS'] = success_mask
        else:
            st.warning("Não foi possível identificar processos concluídos (colunas STAGE_NAME e STAGE_ID não encontradas)")
            df['IS_SUCCESS'] = False
        
        # Criar métricas de destaque (sem título, já que ele foi adicionado na página principal)
        
        col1, col2, col3 = st.columns(3)
        
        # Calcular taxa de conclusão
        taxa_conclusao = round((success_count / len(df) * 100), 1) if len(df) > 0 else 0
        
        # Card 1 - Total de Cartórios e registros por cartório
        with col1:
            st.markdown(f"""
            <div class="metric-card cartorios">
                <div class="metric-value">{len(df['NOME_CARTORIO'].unique())}</div>
                <div class="metric-title">Cartórios</div>
                <div class="metric-subtitle">
                    <span style="white-space: nowrap; font-size: 0.85rem;">Casa Verde: {count_cat_16}</span><br>
                    <span style="white-space: nowrap; font-size: 0.85rem;">Tatuapé: {count_cat_34}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Card 2 - Total de Processos (soma exata)
        with col2:
            st.markdown(f"""
            <div class="metric-card processos">
                <div class="metric-value">{total_registros}</div>
                <div class="metric-title">Processos</div>
                <div class="metric-subtitle" style="font-size: 0.85rem; margin-top: 3px;">
                    Filtrados: {count_cat_16 + count_cat_34}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Card 3 - Processos Concluídos
        with col3:
            st.markdown(f"""
            <div class="metric-card concluidos">
                <div class="metric-value">
                    {success_count} <span style="font-size: 24px; background-color: #E8F5E9; padding: 4px 8px; border-radius: 20px; vertical-align: middle; color: #2E7D32; font-weight: 700;">{taxa_conclusao}%</span>
                </div>
                <div class="metric-title">Concluídos</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Verificar se temos os dados de comparação do CRM
        tem_dados_crm = any(col.startswith('CRM_') for col in df.columns)
        
        if tem_dados_crm:
            # Card 4 - Status de Correspondência com CRM
            st.markdown('<div class="section-subtitle"><strong>Status de Correspondência com CRM</strong></div>', unsafe_allow_html=True)
            
            # Calcular quantos IDs têm correspondência no CRM
            if 'CRM_UF_CRM_CAMPO_COMPARACAO' in df.columns:
                total_com_correspondencia = df['CRM_UF_CRM_CAMPO_COMPARACAO'].notna().sum()
                percentual_correspondencia = round((total_com_correspondencia / len(df) * 100), 1) if len(df) > 0 else 0
                
                col1, col2 = st.columns(2)
                
                # Card - Total de IDs com correspondência no CRM
                with col1:
                    st.markdown(f"""
                    <div class="metric-card cartorios">
                        <div class="metric-value">{total_com_correspondencia}</div>
                        <div class="metric-title">IDs com correspondência no CRM</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Card - Percentual de correspondência
                with col2:
                    st.markdown(f"""
                    <div class="metric-card processos">
                        <div class="metric-value">{percentual_correspondencia}%</div>
                        <div class="metric-title">Taxa de correspondência</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Métricas por estágio
        st.markdown('<div class="section-subtitle"><strong>Métricas por Estágio</strong></div>', unsafe_allow_html=True)
        
        # Usar nomes mais legíveis para os estágios
        if 'STAGE_NAME' in df.columns:
            df['STAGE_NAME_LEGIVEL'] = df['STAGE_NAME'].apply(simplificar_nome_estagio)
        else:
            df['STAGE_NAME_LEGIVEL'] = df['STAGE_ID'].apply(simplificar_nome_estagio)
        
        # Contar quantos processos estão em cada estágio
        contagem_por_estagio = df.groupby('STAGE_NAME_LEGIVEL').size().reset_index(name='QUANTIDADE')
        
        # Calcular o percentual
        contagem_por_estagio['PERCENTUAL'] = (contagem_por_estagio['QUANTIDADE'] / len(df) * 100).round(2)
        
        # Categorizar estágios
        contagem_por_estagio['CATEGORIA'] = contagem_por_estagio['STAGE_NAME_LEGIVEL'].apply(categorizar_estagio)
        
        # Definir cores por categoria
        contagem_por_estagio['COR'] = contagem_por_estagio['CATEGORIA'].map({
            'SUCESSO': '#4caf50',      # Verde
            'EM ANDAMENTO': '#ffb300', # Amarelo
            'FALHA': '#f44336'         # Vermelho
        })
        
        # Ordenar primeiro por categoria, depois por quantidade descendente
        contagem_por_estagio['ORDEM_CATEGORIA'] = contagem_por_estagio['CATEGORIA'].map({
            'SUCESSO': 1,
            'EM ANDAMENTO': 2,
            'FALHA': 3
        })
        
        contagem_por_estagio = contagem_por_estagio.sort_values(
            ['ORDEM_CATEGORIA', 'QUANTIDADE'], 
            ascending=[True, False]
        )
        
        # Separar por categoria
        estagios_sucesso = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'SUCESSO']
        estagios_andamento = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'EM ANDAMENTO']
        estagios_falha = contagem_por_estagio[contagem_por_estagio['CATEGORIA'] == 'FALHA']
        
        # Renderizar cada categoria em sua própria linha
        renderizar_linha_cards(estagios_sucesso, "SUCESSO")
        # Divisor visual entre categorias
        st.markdown('<div class="divisor"></div>', unsafe_allow_html=True)
        
        renderizar_linha_cards(estagios_andamento, "EM ANDAMENTO")
        # Divisor visual entre categorias
        st.markdown('<div class="divisor"></div>', unsafe_allow_html=True)
        
        renderizar_linha_cards(estagios_falha, "FALHA")
        
        # Se quiser ver todos os estágios em forma de tabela
        with st.expander("Ver todos os estágios detalhados", expanded=False):
            st.dataframe(
                contagem_por_estagio[['CATEGORIA', 'STAGE_NAME_LEGIVEL', 'QUANTIDADE', 'PERCENTUAL']],
                column_config={
                    "CATEGORIA": st.column_config.TextColumn("Categoria"),
                    "STAGE_NAME_LEGIVEL": st.column_config.TextColumn("Estágio"),
                    "QUANTIDADE": st.column_config.NumberColumn("Quantidade", format="%d"),
                    "PERCENTUAL": st.column_config.ProgressColumn(
                        "Percentual",
                        format="%.2f%%",
                        min_value=0,
                        max_value=100
                    )
                },
                use_container_width=True,
                hide_index=True
            )
        
        # Adicionar métricas de conversão por cartório
        visualizar_conversao_por_cartorio(df)
        
        # Visualizar gráfico de distribuição por cartório
        visualizar_grafico_cartorio(df)

def simplificar_nome_estagio(nome):
    """
    Simplifica o nome do estágio para exibição
    """
    if pd.isna(nome):
        return "Desconhecido"
    
    # Se o nome contém dois pontos, pegar a parte depois dos dois pontos
    if isinstance(nome, str) and ':' in nome:
        codigo_estagio = nome
    else:
        codigo_estagio = nome  # Usar o nome completo como código
    
    # Mapeamento completo dos códigos para nomes legíveis e curtos
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
        # Novos mapeamentos adicionados
        'UC_3LJ0KG': 'Não Trabalhar (Despriorizada)',
        'DT1052_16:UC_3LJ0KG': 'Não Trabalhar (Despriorizada)',
        'DT1052_34:UC_3LJ0KG': 'Não Trabalhar (Despriorizada)',
        'UC_RJC2DD': 'PRIO2 - Fazer Busca CRC',
        'DT1052_16:UC_RJC2DD': 'PRIO2 - Fazer Busca CRC',
        'DT1052_34:UC_RJC2DD': 'PRIO2 - Fazer Busca CRC',
        'UC_XM32IE': 'Sem Dados Suficientes para Busca',
        'DT1052_16:UC_XM32IE': 'Sem Dados Suficientes para Busca',
        'DT1052_34:UC_XM32IE': 'Sem Dados Suficientes para Busca',
        'UC_K85YX7': 'Solicitar Cartório de Origem Prioridade',
        'DT1052_16:UC_K85YX7': 'Solicitar Cartório de Origem Prioridade',
        'DT1052_34:UC_K85YX7': 'Solicitar Cartório de Origem Prioridade',
        'K85YX7': 'PRIO2 - Fazer Busca CRC',
        'DT1052_16:K85YX7': 'PRIO2 - Fazer Busca CRC',
        'DT1052_34:K85YX7': 'PRIO2 - Fazer Busca CRC',
        'UC_7L6CGJ': 'Cancelado',
        'DT1052_16:UC_7L6CGJ': 'Cancelado',
        'DT1052_34:UC_7L6CGJ': 'Cancelado',
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
    
    # Unificar todos os mapeamentos em um único dicionário
    mapeamento_completo = {**em_andamento, **sucesso, **falha}
    
    # Verificar se o código está no mapeamento completo
    if codigo_estagio in mapeamento_completo:
        return mapeamento_completo[codigo_estagio]
    
    # Se não encontrar o código completo, tentar verificar apenas a parte após os dois pontos
    if isinstance(codigo_estagio, str) and ':' in codigo_estagio:
        apenas_codigo = codigo_estagio.split(':')[-1]
        if apenas_codigo in mapeamento_completo:
            return mapeamento_completo[apenas_codigo]
    
    # Caso não encontre um mapeamento, retornar o nome original simplificado
    if isinstance(nome, str) and ':' in nome:
        return nome.split(':')[-1]
    return nome

def categorizar_estagio(estagio):
    """Categoriza o estágio em SUCESSO, FALHA ou EM ANDAMENTO"""
    # Lista de estágios considerados como SUCESSO
    sucesso_stages = ['Certidão Entregue', 'Certidão Física', 'Certidão Emitida']
    
    # Lista de estágios considerados como FALHA
    falha_stages = [
        'Devolução ADM', 'Dev. ADM Verificado', 'Devolutiva 2Busca', 
        'Solicitação Duplicada', 'Solic. Duplicada', 'Devolvido Requerimento',
        'Dev. Requerim.', 'Dev. ADM Verif.', 'Dev. Busca',
        'Cancelado', 'Sem Dados Suficientes para Busca', 'Não Trabalhar (Despriorizada)'
    ]
    
    # Verificar categoria
    if estagio in sucesso_stages:
        return 'SUCESSO'
    elif estagio in falha_stages:
        return 'FALHA'
    else:
        return 'EM ANDAMENTO'

def renderizar_linha_cards(df_categoria, titulo):
    """Renderiza uma linha de cards por categoria"""
    if not df_categoria.empty:
        # Título da categoria com a cor correspondente
        cor_titulo = df_categoria.iloc[0]['COR']
        
        # Adicionar ícones para cada categoria
        icone = "✅" if titulo == "SUCESSO" else "⏳" if titulo == "EM ANDAMENTO" else "❌"
        
        st.markdown(f"""
        <div style="margin-top: 35px; margin-bottom: 15px; padding: 10px 15px; background-color: #f8f9fa; border-radius: 8px; border-left: 8px solid {cor_titulo}; display: flex; align-items: center;">
            <div style="font-size: 22px; margin-right: 12px;">{icone}</div>
            <h4 style="margin: 0; color: {cor_titulo}; font-size: 20px; font-weight: 900; text-transform: uppercase;"><strong>{titulo}</strong></h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Aumentar para 3 colunas para mais compactação
        n_cols = min(3, len(df_categoria))
        
        # Calcular o número de linhas necessárias
        n_rows = (len(df_categoria) + n_cols - 1) // n_cols  # Divisão inteira arredondada para cima
        
        # Renderizar cards em várias linhas se necessário
        for row in range(n_rows):
            # Criar um conjunto de colunas para cada linha
            cols = st.columns(n_cols)
            
            # Renderizar cards para esta linha
            for col in range(n_cols):
                idx = row * n_cols + col
                
                # Verificar se ainda temos cards para mostrar
                if idx < len(df_categoria):
                    _, row_data = df_categoria.iloc[idx].name, df_categoria.iloc[idx]
                    cor = row_data['COR']
                    
                    # Calcular cor de fundo baseada na cor principal (versão bem clara)
                    bg_color = f"rgba({','.join([str(int(int(cor[1:3], 16) * 0.1 + 240)), str(int(int(cor[3:5], 16) * 0.1 + 240)), str(int(int(cor[5:7], 16) * 0.1 + 240))])}, 0.5)"
                    
                    with cols[col]:
                        st.markdown(f"""
                        <div class="stage-card" style="border-left: 4px solid {cor};">
                            <div class="stage-title">{row_data['STAGE_NAME_LEGIVEL']}</div>
                            <div class="stage-metrics">
                                <span class="stage-quantity" style="color: {cor};">{row_data['QUANTIDADE']}</span>
                                <span class="stage-percentage" style="background-color: {bg_color};">{row_data['PERCENTUAL']}%</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

def visualizar_grafico_cartorio(df):
    """
    Cria e exibe um gráfico de barras por cartório
    """
    st.markdown('<div class="section-title">Distribuição de Processos por Cartório</div>', unsafe_allow_html=True)
    
    # Verificar se há dados
    if df.empty:
        st.warning("Não há dados disponíveis para gerar o gráfico.")
        return
    
    # Agrupar por cartório e calcular métricas
    cartorio_counts = df.groupby('NOME_CARTORIO').size().reset_index(name='TOTAL')
    
    # Calcular percentuais
    cartorio_counts['PERCENTUAL'] = (cartorio_counts['TOTAL'] / cartorio_counts['TOTAL'].sum() * 100).round(2)
    
    # Ordenar por total (maior para menor)
    cartorio_counts = cartorio_counts.sort_values('TOTAL', ascending=False)
    
    # Definir paleta de cores mais contrastante
    cores_cartorio = px.colors.qualitative.Bold
    
    # Adicionar informações visuais sobre os cartórios
    cartorio_info = st.container()
    with cartorio_info:
        # Identificar cartório com mais processos
        maior_cartorio = cartorio_counts.iloc[0]
        
        # Diferença percentual em relação ao segundo maior (se existir)
        diff_texto = ""
        if len(cartorio_counts) > 1:
            segundo_maior = cartorio_counts.iloc[1]
            diff_pct = ((maior_cartorio['TOTAL'] - segundo_maior['TOTAL']) / segundo_maior['TOTAL'] * 100).round(1)
            diff_texto = f" ({diff_pct}% a mais que {segundo_maior['NOME_CARTORIO']})"
        
        # Destacar maior cartório
        st.markdown(f"""
        <div style="background-color: #f1f8e9; border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #4CAF50;">
            <h3 style="margin-top: 0; color: #2E7D32; font-size: 18px;">Cartório com Maior Volume</h3>
            <p style="font-size: 22px; font-weight: 800; margin: 5px 0; color: #1B5E20;">{maior_cartorio['NOME_CARTORIO']}</p>
            <p style="font-size: 16px; margin: 5px 0;">
                <span style="font-weight: 700;">{maior_cartorio['TOTAL']}</span> processos 
                (<span style="font-weight: 700;">{maior_cartorio['PERCENTUAL']}%</span> do total){diff_texto}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Gráficos lado a lado
    col1, col2 = st.columns(2)
    
    with col1:
        # Criar gráfico de pizza melhorado
        fig_pie = px.pie(
            cartorio_counts,
            values='TOTAL',
            names='NOME_CARTORIO',
            title="<b>Distribuição por Cartório</b>",
            hover_data=['PERCENTUAL', 'TOTAL'],
            labels={'NOME_CARTORIO': 'Cartório', 'TOTAL': 'Total de Processos'},
            color_discrete_sequence=cores_cartorio
        )
        
        # Configurar o texto mostrado no gráfico
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont_size=14,
            textfont_family="Arial, Helvetica, sans-serif",
            marker=dict(line=dict(color='white', width=2)),
            hovertemplate="<b>%{label}</b><br>" +
                        "Total: %{value} processos<br>" +
                        "Percentual: %{percent}<extra></extra>"
        )
        
        # Atualizar layout
        fig_pie.update_layout(
            showlegend=False,
            height=450,
            font=dict(
                family="Arial, Helvetica, sans-serif",
                size=14
            ),
            title={
                'font': {'size': 22, 'family': "Arial, Helvetica, sans-serif", 'color': '#1A237E'},
                'y': 0.95
            },
            margin=dict(t=80, b=30, l=30, r=30)
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Criar gráfico de barras horizontal (melhor visualização)
        fig_bar = px.bar(
            cartorio_counts,
            y='NOME_CARTORIO',
            x='TOTAL',
            title="<b>Volume de Processos por Cartório</b>",
            text='TOTAL',
            color='NOME_CARTORIO',
            color_discrete_sequence=cores_cartorio,
            labels={'NOME_CARTORIO': 'Cartório', 'TOTAL': 'Total de Processos'},
            height=450,
            orientation='h'  # Horizontal para melhor legibilidade
        )
        
        # Adicionar linhas de referência para média
        media_processos = cartorio_counts['TOTAL'].mean()
        fig_bar.add_vline(
            x=media_processos, 
            line_width=2, 
            line_dash="dash", 
            line_color="#FF5722",
            annotation_text=f"Média: {media_processos:.1f}",
            annotation_position="top right"
        )
        
        # Configurar barras
        fig_bar.update_traces(
            textposition='auto',
            textfont_size=14,
            textfont_family="Arial, Helvetica, sans-serif",
            marker_line_width=1.5,
            marker_line_color='white',
            hovertemplate="<b>%{y}</b><br>" +
                         "Total: %{x} processos<br>" +
                         "Percentual: %{customdata[0]:.2f}%<extra></extra>",
            customdata=cartorio_counts[['PERCENTUAL']]
        )
        
        # Atualizar layout
        fig_bar.update_layout(
            showlegend=False,
            font=dict(
                family="Arial, Helvetica, sans-serif",
                size=14
            ),
            title={
                'font': {'size': 22, 'family': "Arial, Helvetica, sans-serif", 'color': '#1A237E'},
                'y': 0.95
            },
            margin=dict(t=80, b=30, l=150, r=30),
            xaxis=dict(
                title=dict(
                    text="Total de Processos",
                    font=dict(size=16)
                ),
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title=dict(
                    text="",
                    font=dict(size=16)
                ),
                tickfont=dict(size=14)
            )
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Adicionar gráfico de comparação de percentuais
    st.markdown('<div class="section-subtitle">Comparação Percentual entre Cartórios</div>', unsafe_allow_html=True)
    
    # Gráfico de barras horizontal para percentuais
    fig_pct = px.bar(
        cartorio_counts,
        y='NOME_CARTORIO',
        x='PERCENTUAL',
        title=None,
        text=cartorio_counts['PERCENTUAL'].apply(lambda x: f"{x:.2f}%"),
        color='NOME_CARTORIO',
        color_discrete_sequence=cores_cartorio,
        labels={'NOME_CARTORIO': 'Cartório', 'PERCENTUAL': 'Percentual do Total (%)'},
        height=350,
        orientation='h'
    )
    
    # Configurar barras
    fig_pct.update_traces(
        textposition='auto',
        textfont_size=14,
        textfont_family="Arial, Helvetica, sans-serif",
        marker_line_width=1.5,
        marker_line_color='white',
        hovertemplate="<b>%{y}</b><br>" +
                     "Percentual: %{x:.2f}%<br>" +
                     "Total: %{customdata[0]} processos<extra></extra>",
        customdata=cartorio_counts[['TOTAL']]
    )
    
    # Atualizar layout
    fig_pct.update_layout(
        showlegend=False,
        font=dict(
            family="Arial, Helvetica, sans-serif",
            size=14
        ),
        margin=dict(t=30, b=30, l=150, r=30),
        xaxis=dict(
            title=dict(
                text="Percentual do Total (%)",
                font=dict(size=16)
            ),
            tickfont=dict(size=14),
            ticksuffix="%"
        ),
        yaxis=dict(
            title=dict(
                text="",
                font=dict(size=16)
            ),
            tickfont=dict(size=14)
        )
    )
    
    st.plotly_chart(fig_pct, use_container_width=True)
    
    # Fechar o container
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mostrar tabela com os números
    with st.expander("Ver números detalhados", expanded=False):
        # Adicionar mais métricas à tabela
        cartorios_qtd = len(cartorio_counts)
        media_processos = cartorio_counts['TOTAL'].mean()
        mediana_processos = cartorio_counts['TOTAL'].median()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Número de Cartórios", cartorios_qtd)
        with col2:
            st.metric("Média de Processos", f"{media_processos:.1f}")
        with col3:
            st.metric("Mediana de Processos", f"{mediana_processos:.1f}")
        
        st.dataframe(
            cartorio_counts,
            column_config={
                "NOME_CARTORIO": st.column_config.TextColumn("Cartório"),
                "TOTAL": st.column_config.NumberColumn("Total de Processos", format="%d"),
                "PERCENTUAL": st.column_config.ProgressColumn(
                    "Percentual",
                    format="%.2f%%",
                    min_value=0,
                    max_value=100
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Botão para exportar dados
        csv = cartorio_counts.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Exportar dados para CSV",
            data=csv,
            file_name=f"distribuicao_processos_cartorio_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="download_distribuicao_cartorio_grafico"
        )

def aplicar_estilos_cartorio():
    """
    Aplica estilos CSS para o dashboard de Cartório.
    """
    st.markdown("""
    <style>
    /* Cards de Métricas */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        text-align: center;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
        border-top: 3px solid #1976D2; /* Borda superior padrão azul */
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: 900;
        color: #1A237E;
        margin-bottom: 5px;
    }
    
    .metric-title {
        font-size: 16px;
        font-weight: 600;
        color: #546E7A;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-subtitle {
        font-size: 14px;
        color: #78909C;
        margin-top: 5px;
    }
    
    /* Subtítulos e divisores */
    .section-subtitle {
        color: #1A237E;
        font-size: 20px;
        margin: 30px 0 15px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #E0E0E0;
    }
    
    .divisor {
        margin: 15px 0;
        height: 1px;
        background-color: #EEEEEE;
    }
    
    /* Cards de estágios (Renomeado e estilizado) */
    .stage-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 12px 15px; /* Ajuste no padding */
        box-shadow: 0 1px 4px rgba(0,0,0,0.06); /* Sombra mais sutil */
        margin-bottom: 12px; /* Espaçamento ajustado */
        border-left: 4px solid #CCCCCC; /* Borda esquerda mantida */
        display: flex;
        flex-direction: column;
        justify-content: space-between; /* Espaço entre título e métricas */
        height: 90px; /* Altura ajustada */
        transition: box-shadow 0.2s ease-in-out;
    }

    .stage-card:hover {
        box-shadow: 0 3px 8px rgba(0,0,0,0.1); /* Sombra ao passar o mouse */
    }
    
    .stage-title {
        font-size: 14px; /* Tamanho da fonte ajustado */
        font-weight: 600; /* Peso da fonte ajustado */
        color: #333; /* Cor do título */
        margin-bottom: 8px;
        line-height: 1.3; /* Espaçamento entre linhas */
        /* Gerenciamento de texto longo */
        display: -webkit-box;
        -webkit-line-clamp: 2; /* Limita a 2 linhas */
        -webkit-box-orient: vertical;  
        overflow: hidden;
        text-overflow: ellipsis;
        min-height: 36px; /* Garante espaço para 2 linhas */
    }

    .stage-metrics {
        display: flex;
        justify-content: space-between; /* Alinha quantidade à esquerda, percentual à direita */
        align-items: baseline; /* Alinha pela base do texto */
        margin-top: auto; /* Empurra para baixo */
    }
    
    .stage-quantity {
        font-size: 20px; /* Tamanho da quantidade */
        font-weight: 700; /* Peso da quantidade */
        /* Cor é definida inline */
    }
    
    .stage-percentage {
        font-size: 12px; /* Tamanho do percentual */
        font-weight: 600; /* Peso do percentual */
        color: #555; /* Cor do percentual */
        padding: 2px 7px; /* Padding ajustado */
        border-radius: 12px; /* Bordas arredondadas */
        /* Background-color é definido inline */
    }
    </style>
    """, unsafe_allow_html=True)

def visualizar_conversao_por_cartorio(df):
    """
    Visualiza a taxa de conversão por cartório
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados dos cartórios
    """
    # Verificar se temos a coluna necessária
    if 'IS_SUCCESS' not in df.columns or 'NOME_CARTORIO' not in df.columns:
        st.warning("Não é possível calcular a taxa de conversão por cartório (colunas necessárias não encontradas)")
        return
    
    st.markdown('<div class="section-title">Percentual de Conversão por Cartório</div>', unsafe_allow_html=True)
    
    # Agrupar por cartório e calcular métricas
    conversao_cartorio = df.groupby('NOME_CARTORIO').agg(
        total_processos=('NOME_CARTORIO', 'size'),
        processos_sucesso=('IS_SUCCESS', 'sum')
    ).reset_index()
    
    # Calcular percentuais de conversão
    conversao_cartorio['taxa_conversao'] = (conversao_cartorio['processos_sucesso'] / conversao_cartorio['total_processos'] * 100).round(1)
    
    # Ordenar por taxa de conversão (maior para menor)
    conversao_cartorio = conversao_cartorio.sort_values('taxa_conversao', ascending=False)
    
    # Adicionar visualização de destaque para o melhor cartório
    if not conversao_cartorio.empty:
        melhor_cartorio = conversao_cartorio.iloc[0]
        
        # Calcular a média geral de conversão para comparação
        media_conversao = (df['IS_SUCCESS'].sum() / len(df) * 100).round(1)
        
        # Calcular quanto a conversão do melhor cartório está acima da média
        diferenca_media = (melhor_cartorio['taxa_conversao'] - media_conversao).round(1)
        texto_diferenca = f"{diferenca_media}% acima da média geral" if diferenca_media > 0 else f"{abs(diferenca_media)}% abaixo da média geral"
        
        st.markdown(f"""
        <div style="background-color: #e3f2fd; border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #2196F3;">
            <h3 style="margin-top: 0; color: #0d47a1; font-size: 18px;">Melhor Taxa de Conversão</h3>
            <p style="font-size: 22px; font-weight: 800; margin: 5px 0; color: #0d47a1;">{melhor_cartorio['NOME_CARTORIO']}</p>
            <p style="font-size: 16px; margin: 5px 0;">
                <span style="font-weight: 700;">{melhor_cartorio['taxa_conversao']}%</span> de taxa de conversão
                <span style="font-size: 14px; color: #666; margin-left: 5px;">({melhor_cartorio['processos_sucesso']} de {melhor_cartorio['total_processos']} processos)</span>
            </p>
            <p style="font-size: 14px; margin: 5px 0; color: #555;">
                <span style="background-color: #e8f5e9; padding: 2px 6px; border-radius: 10px; font-weight: 600;">{texto_diferenca}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Criar gráfico de barras para conversão
    fig = px.bar(
        conversao_cartorio,
        y='NOME_CARTORIO',
        x='taxa_conversao',
        title="<b>Taxa de Conversão por Cartório (%)</b>",
        text=conversao_cartorio['taxa_conversao'].apply(lambda x: f"{x}%"),
        color='taxa_conversao',
        color_continuous_scale='RdYlGn',  # Verde para maior conversão, vermelho para menor
        labels={'NOME_CARTORIO': 'Cartório', 'taxa_conversao': 'Taxa de Conversão (%)'},
        height=max(350, len(conversao_cartorio) * 25),  # Ajustar altura com base no número de cartórios
        orientation='h'
    )
    
    # Adicionar linha de referência para média
    media_conversao = conversao_cartorio['taxa_conversao'].mean()
    fig.add_vline(
        x=media_conversao, 
        line_width=2, 
        line_dash="dash", 
        line_color="#FF5722",
        annotation_text=f"Média: {media_conversao:.1f}%",
        annotation_position="top right"
    )
    
    # Configurar barras
    fig.update_traces(
        textposition='auto',
        textfont_size=14,
        textfont_family="Arial, Helvetica, sans-serif",
        marker_line_width=1.5,
        marker_line_color='white',
        hovertemplate="<b>%{y}</b><br>" +
                    "Conversão: %{x:.1f}%<br>" +
                    "Total: %{customdata[0]} processos<br>" +
                    "Sucesso: %{customdata[1]} processos<extra></extra>",
        customdata=conversao_cartorio[['total_processos', 'processos_sucesso']]
    )
    
    # Atualizar layout
    fig.update_layout(
        coloraxis_showscale=False,
        font=dict(
            family="Arial, Helvetica, sans-serif",
            size=14
        ),
        title={
            'font': {'size': 22, 'family': "Arial, Helvetica, sans-serif", 'color': '#1A237E'},
            'y': 0.95
        },
        margin=dict(t=80, b=30, l=150, r=30),
        xaxis=dict(
            title=dict(
                text="Taxa de Conversão (%)",
                font=dict(size=16)
            ),
            tickfont=dict(size=14),
            ticksuffix="%"
        ),
        yaxis=dict(
            title=dict(
                text="",
                font=dict(size=16)
            ),
            tickfont=dict(size=14)
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar tabela com os dados detalhados
    with st.expander("Ver detalhes de conversão por cartório", expanded=False):
        st.dataframe(
            conversao_cartorio,
            column_config={
                "NOME_CARTORIO": st.column_config.TextColumn("Cartório"),
                "total_processos": st.column_config.NumberColumn("Total de Processos", format="%d"),
                "processos_sucesso": st.column_config.NumberColumn("Processos Concluídos", format="%d"),
                "taxa_conversao": st.column_config.ProgressColumn(
                    "Taxa de Conversão",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Botão para exportar dados de conversão
        csv = conversao_cartorio.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Exportar dados de conversão para CSV",
            data=csv,
            file_name=f"conversao_cartorios_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="download_conversao_cartorio"
        ) 