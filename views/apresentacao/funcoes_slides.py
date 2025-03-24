import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
import sys
import os
from pathlib import Path

# Este arquivo contém funções de slide para suportar a migração
# Foram copiadas e aprimoradas a partir do arquivo apresentacao_conclusoes.py

def slide_metricas_destaque(df, df_todos, date_from, date_to):
    """
    Slide com as métricas principais de conclusões
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Métricas de Destaque</h2>', unsafe_allow_html=True)
    
    # Usar dados originais sem filtro
    df_filtrado = df
    
    # Calcular métricas com dados originais
    total_conclusoes = len(df_filtrado)
    
    # Carregar métricas totais
    try:
        # Total de negócios (todos os registros)
        total_negocios = len(df_todos)
        
        # Total de concluídos
        concluidos = total_conclusoes
        
        # Calcular taxa de conclusão
        taxa_conclusao = round((concluidos / max(1, total_negocios)) * 100, 1)
        
        # Pendentes
        pendentes = total_negocios - concluidos
    except Exception as e:
        st.error(f"Erro ao calcular métricas: {str(e)}")
        taxa_conclusao = 0
        pendentes = 0
        total_negocios = 0
    
    # Converter para datetime se não for
    if not isinstance(date_from, datetime):
        date_from = datetime.combine(date_from, datetime.min.time())
    if not isinstance(date_to, datetime):
        date_to = datetime.combine(date_to, datetime.min.time())
    
    # Encontrar a data da primeira conclusão (se houver registros)
    data_primeira_conclusao = None
    if not df_filtrado.empty and 'DATA_CONCLUSAO' in df_filtrado.columns:
        df_com_data = df_filtrado.dropna(subset=['DATA_CONCLUSAO'])
        if not df_com_data.empty:
            data_primeira_conclusao = df_com_data['DATA_CONCLUSAO'].min().date()
    
    # Se não houver conclusões, usar a data inicial
    if data_primeira_conclusao is None:
        data_primeira_conclusao = date_from.date()
    
    # Ajustar a data inicial para ser a data da primeira conclusão
    data_inicio_efetiva = max(date_from.date(), data_primeira_conclusao)
    
    # Contar dias úteis naturais (dias em que houve trabalho)
    dias_uteis_naturais = 0
    horas_uteis = 0
    
    # Calcular dia a dia a partir da primeira conclusão
    data_atual = datetime.combine(data_inicio_efetiva, datetime.min.time())
    while data_atual.date() <= date_to.date():
        # Dia da semana: 0 = segunda, 6 = domingo
        dia_semana = data_atual.weekday()
        
        # Segunda a sábado são considerados dias úteis
        if 0 <= dia_semana <= 5:  # Segunda a sábado
            dias_uteis_naturais += 1
            
            # Registrar horas para média horária
            if 0 <= dia_semana <= 4:  # Segunda a sexta
                horas_uteis += 12  # 7h - 19h (12 horas)
            else:  # Sábado
                horas_uteis += 3   # 9h - 12h (3 horas)
        
        # Avançar para o próximo dia
        data_atual += timedelta(days=1)
    
    # Calcular médias
    # Média diária baseada em dias naturais (dias em que houve trabalho)
    media_diaria = round(total_conclusoes / max(1, dias_uteis_naturais), 1)
    
    # Média horária
    media_horaria = round(total_conclusoes / max(1, horas_uteis), 1)
    
    # Layout de cards otimizados para TV vertical
    col1, col2 = st.columns(2, gap="large")
    
    # Card 1: Total de conclusões - DESIGN MELHORADO
    with col1:
        st.markdown(f"""
        <div class="metric-card-tv total" style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);">
            <div class="metric-title-tv">Total Conclusões</div>
            <div class="metric-value-tv">{f"{total_conclusoes:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">processos concluídos</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 2: Média diária - DESIGN MELHORADO
    with col2:
        st.markdown(f"""
        <div class="metric-card-tv media" style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);">
            <div class="metric-title-tv">Média Diária</div>
            <div class="metric-value-tv">{f"{media_diaria:.1f}".replace(".", ",")}</div>
            <div class="metric-subtitle-tv">conclusões/dia</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 3: Média por hora - DESIGN MELHORADO
    with col1:
        st.markdown(f"""
        <div class="metric-card-tv media" style="background: linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%);">
            <div class="metric-title-tv">Média Horária</div>
            <div class="metric-value-tv">{f"{media_horaria:.1f}".replace(".", ",")}</div>
            <div class="metric-subtitle-tv">conclusões/hora</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 4: Taxa de conclusão - DESIGN MELHORADO
    with col2:
        st.markdown(f"""
        <div class="metric-card-tv taxa" style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);">
            <div class="metric-title-tv">Taxa Conclusão</div>
            <div class="metric-value-tv">{taxa_conclusao}%</div>
            <div class="metric-subtitle-tv">de todos os processos</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Informação do período analisado - DESIGN MELHORADO
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); border-left: 10px solid #7B1FA2; padding: 20px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); text-align: center; border-radius: 10px;">
        <div style="font-size: 2rem; font-weight: 700; color: #4A148C; margin-bottom: 10px;">
            Período Analisado
        </div>
        <div style="font-size: 1.8rem; font-weight: 700;">
            {data_inicio_efetiva.strftime('%d/%m/%Y')} a {date_to.strftime('%d/%m/%Y')}
        </div>
        <div style="font-size: 1.5rem; margin-top: 15px;">
            <span style="font-weight: 700; color: #4A148C;">Dias úteis:</span> 
            <span style="font-weight: 800; font-size: 1.8rem;">{dias_uteis_naturais}</span>
            <span style="margin: 0 10px;">|</span>
            <span style="font-weight: 700; color: #4A148C;">Horas úteis:</span> 
            <span style="font-weight: 800; font-size: 1.8rem;">{horas_uteis}h</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def slide_ranking_produtividade(df, df_todos):
    """
    Slide com ranking de produtividade por responsável
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Ranking de Produtividade</h2>', unsafe_allow_html=True)
    
    try:
        # Verificar se a coluna de responsáveis existe
        if 'ASSIGNED_BY_NAME' not in df_todos.columns:
            st.error("Não foi possível gerar o ranking: coluna de responsáveis não encontrada.")
            return
        
        # Agrupar por responsável e contar o número de conclusões
        if not df.empty and 'ASSIGNED_BY_NAME' in df.columns:
            ranking_conclusoes = df.groupby('ASSIGNED_BY_NAME').size().reset_index(name='TOTAL_CONCLUSOES')
        else:
            ranking_conclusoes = pd.DataFrame(columns=['ASSIGNED_BY_NAME', 'TOTAL_CONCLUSOES'])
        
        # Calcular a taxa de conclusão por responsável
        total_por_responsavel = df_todos.groupby('ASSIGNED_BY_NAME').size().reset_index(name='TOTAL_ATRIBUIDOS')
        
        # Fazer merge outer para incluir todos os responsáveis
        ranking = pd.merge(total_por_responsavel, ranking_conclusoes, on='ASSIGNED_BY_NAME', how='left')
        
        # Preencher valores NaN de conclusões com 0
        ranking['TOTAL_CONCLUSOES'] = ranking['TOTAL_CONCLUSOES'].fillna(0)
        ranking['TOTAL_CONCLUSOES'] = ranking['TOTAL_CONCLUSOES'].astype(int)
        
        # Calcular pendentes e taxa de conclusão
        ranking['PENDENTES'] = ranking['TOTAL_ATRIBUIDOS'] - ranking['TOTAL_CONCLUSOES']
        ranking['TAXA_CONCLUSAO'] = (ranking['TOTAL_CONCLUSOES'] / ranking['TOTAL_ATRIBUIDOS'] * 100).round(1)
        
        # Ordenar pelo total de conclusões em ordem decrescente
        ranking = ranking.sort_values('TOTAL_CONCLUSOES', ascending=False).reset_index(drop=True)
        
        # Adicionar coluna de posição
        ranking.insert(0, 'POSICAO', ranking.index + 1)
        
        # Calcular a média global para estabelecer a meta
        media_global = df.groupby('DATA_CONCLUSAO').size().mean() if 'DATA_CONCLUSAO' in df.columns else 0
        meta_diaria = round(media_global, 1)  # Meta = 100% da média global diária
        
        # Calcular total de pendentes do mês
        total_pendentes = ranking['PENDENTES'].sum()
        
        # Calcular dias restantes até o fim do mês
        hoje = datetime.now()
        ultimo_dia_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        dias_restantes = (ultimo_dia_mes - hoje).days + 1  # +1 para incluir o dia atual
        
        # Calcular meta diária para concluir todos até o fim do mês
        meta_diaria_fim_mes = round(total_pendentes / max(1, dias_restantes), 1)
        
        # Calcular dias trabalhados e média diária para cada responsável
        if 'DATA_CONCLUSAO' in df.columns:
            # Lista para armazenar dados dos responsáveis com suas estatísticas
            dados_responsaveis = []
            
            # Para cada responsável no ranking
            for i, (idx, row) in enumerate(ranking.iterrows()):
                responsavel = row['ASSIGNED_BY_NAME']
                df_resp = df[df['ASSIGNED_BY_NAME'] == responsavel]
                
                if not df_resp.empty:
                    # Dias úteis entre primeira e última conclusão
                    primeira_conclusao = df_resp['DATA_CONCLUSAO'].min().date()
                    ultima_conclusao = df_resp['DATA_CONCLUSAO'].max().date()
                    
                    dias_uteis = 0
                    data_atual = datetime.combine(primeira_conclusao, datetime.min.time())
                    
                    while data_atual.date() <= ultima_conclusao:
                        dia_semana = data_atual.weekday()
                        if dia_semana <= 5:  # Segunda a sábado
                            dias_uteis += 1
                        data_atual += timedelta(days=1)
                    
                    # Dias em que o responsável realmente trabalhou
                    dias_com_conclusao = df_resp['DATA_CONCLUSAO'].dt.date.nunique()
                    
                    # Média diária
                    media_diaria = row['TOTAL_CONCLUSOES'] / max(1, dias_uteis)
                    
                    # Verificar se atingiu a meta
                    atingiu_meta = media_diaria >= meta_diaria
                    
                    # Adicionar dados
                    dados_responsaveis.append({
                        'posicao': int(row['POSICAO']),
                        'nome': responsavel,
                        'total': int(row['TOTAL_CONCLUSOES']),
                        'pendentes': int(row['PENDENTES']),
                        'taxa': row['TAXA_CONCLUSAO'],
                        'dias_uteis': dias_uteis,
                        'dias_com_conclusao': dias_com_conclusao,
                        'media_diaria': round(media_diaria, 1),
                        'atingiu_meta': atingiu_meta,
                        'destaque': i < 3  # Top 3 = destaque especial
                    })
                else:
                    # Responsável sem conclusões
                    dados_responsaveis.append({
                        'posicao': int(row['POSICAO']),
                        'nome': responsavel,
                        'total': int(row['TOTAL_CONCLUSOES']),
                        'pendentes': int(row['PENDENTES']),
                        'taxa': row['TAXA_CONCLUSAO'],
                        'dias_uteis': 0,
                        'dias_com_conclusao': 0,
                        'media_diaria': 0.0,
                        'atingiu_meta': False,
                        'destaque': False
                    })
        else:
            # Caso não tenha a coluna de data de conclusão
            dados_responsaveis = [
                {
                    'posicao': int(row['POSICAO']),
                    'nome': row['ASSIGNED_BY_NAME'],
                    'total': int(row['TOTAL_CONCLUSOES']),
                    'pendentes': int(row['PENDENTES']),
                    'taxa': row['TAXA_CONCLUSAO'],
                    'dias_uteis': 0,
                    'dias_com_conclusao': 0,
                    'media_diaria': 0.0,
                    'atingiu_meta': False,
                    'destaque': i < 3  # Top 3 = destaque especial
                } for i, (idx, row) in enumerate(ranking.iterrows())
            ]
        
        # Exibir informação sobre as metas - DESIGN MELHORADO
        st.markdown(f"""
        <div style="margin-bottom: 25px;">
            <div style="background: linear-gradient(135deg, #ede7f6 0%, #d1c4e9 100%); border-radius: 15px; padding: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); text-align: center; border-left: 10px solid #9C27B0;">
                <div style="font-size: 2rem; font-weight: 800; color: #6A1B9A; margin-bottom: 8px;">
                    META ATÉ FIM DO MÊS: {f"{meta_diaria_fim_mes:.1f}".replace(".", ",")}/dia
                </div>
                <div style="font-size: 1.3rem; color: #9C27B0; font-weight: 600;">
                    Para concluir {f"{total_pendentes:,}".replace(",", ".")} pendentes nos próximos {dias_restantes} dias
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Função para renderizar o card de cada responsável
        def renderizar_card_responsavel(resp, compacto=False):
            posicao = resp['posicao']
            nome = resp['nome']
            total = resp['total']
            pendentes = resp['pendentes']
            taxa = resp['taxa']
            media_diaria = resp['media_diaria']
            dias_uteis = resp['dias_uteis']
            atingiu_meta = resp['atingiu_meta']
            destaque = resp['destaque']
            
            # Determinar cor baseada na posição
            if posicao == 1:
                cor = '#FFD700'  # Ouro para 1º lugar
                icone = '🥇'
            elif posicao == 2:
                cor = '#C0C0C0'  # Prata para 2º lugar
                icone = '🥈'
            elif posicao == 3:
                cor = '#CD7F32'  # Bronze para 3º lugar
                icone = '🥉'
            else:
                cor = '#607D8B'  # Cinza para os demais
                icone = f"{posicao}º"
            
            # Ícone para quem atingiu a meta
            meta_icon = "🎯" if atingiu_meta else ""
            
            # Aplicar estilo diferenciado para os 3 primeiros
            estilo_card = ""
            if destaque:
                estilo_card = "box-shadow: 0 6px 16px rgba(0,0,0,0.18);"
            
            # Estilo para o fundo baseado em atingir a meta
            fundo_meta = "linear-gradient(135deg, rgba(46, 125, 50, 0.1) 0%, rgba(200, 230, 201, 0.6) 100%)" if atingiu_meta else "white"
            
            if compacto:
                # Versão compacta para os não-destaques
                return f"""
                <div style="background: {fundo_meta}; border-radius: 8px; padding: 8px 8px; margin-bottom: 10px; 
                        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); position: relative; border-left: 4px solid {cor};">
                    <div style="position: absolute; top: 5px; right: 5px; font-size: 1rem;">{icone}{meta_icon}</div>
                    <div style="font-size: 1rem; font-weight: 600; margin-bottom: 5px; color: #1A237E; 
                            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 30px;">{nome}</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.7rem; color: #666;">Concl.</div>
                            <div style="font-size: 1rem; font-weight: 900; color: #2E7D32;">{total}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.7rem; color: #666;">Média</div>
                            <div style="font-size: 1rem; font-weight: 900; color: #1565C0;">{f"{media_diaria:.1f}".replace(".", ",")}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.7rem; color: #666;">Taxa</div>
                            <div style="font-size: 1rem; font-weight: 900; color: #FF9800;">{taxa}%</div>
                        </div>
                    </div>
                </div>
                """
            else:
                # Versão normal para os destaques
                return f"""
                <div style="background: {fundo_meta}; border-radius: 10px; padding: 10px 8px; margin-bottom: 15px; 
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); position: relative; border-left: 6px solid {cor}; {estilo_card}
                        width: 100%; max-width: 100%; overflow: hidden;">
                    <div style="position: absolute; top: 6px; right: 8px; font-size: 1.2rem;">{icone}{meta_icon}</div>
                    <div style="font-size: 1.1rem; font-weight: 800; margin-bottom: 8px; color: #1A237E; 
                            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 40px;">{nome}</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.8rem; color: #666;">Conclusões</div>
                            <div style="font-size: 1.1rem; font-weight: 900; color: #2E7D32;">{total}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.8rem; color: #666;">Média/dia</div>
                            <div style="font-size: 1.1rem; font-weight: 900; color: #1565C0;">{f"{media_diaria:.1f}".replace(".", ",")}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.8rem; color: #666;">Taxa</div>
                            <div style="font-size: 1.1rem; font-weight: 900; color: #FF9800;">{taxa}%</div>
                        </div>
                    </div>
                </div>
                """
            
        # Separar entre destaques (top 3) e demais
        destaques = [resp for resp in dados_responsaveis if resp['destaque']]
        outros = [resp for resp in dados_responsaveis if not resp['destaque']]
        
        # Layout para os destaques
        st.markdown('<div style="margin-bottom: 10px;"><h3 style="font-size: 1.3rem; color: #1A237E; text-align: center;">Top 3 Produtividade</h3></div>', unsafe_allow_html=True)
        
        # Mostrar os destaques em formato maior
        for resp in destaques:
            st.markdown(renderizar_card_responsavel(resp, compacto=False), unsafe_allow_html=True)
            
        # Layout para os demais em colunas compactas
        if outros:
            st.markdown('<div style="margin: 10px 0;"><h3 style="font-size: 1.3rem; color: #424242; text-align: center;">Demais Colaboradores</h3></div>', unsafe_allow_html=True)
            
            # Dividir em 3 colunas para caber mais na tela
            col1, col2, col3 = st.columns(3)
            
            # Distribuir os outros responsáveis entre as três colunas
            terco = (len(outros) + 2) // 3
            col1_resp = outros[:terco]
            col2_resp = outros[terco:2*terco]
            col3_resp = outros[2*terco:]
            
            # Coluna 1
            with col1:
                for resp in col1_resp:
                    st.markdown(renderizar_card_responsavel(resp, compacto=True), unsafe_allow_html=True)
            
            # Coluna 2
            with col2:
                for resp in col2_resp:
                    st.markdown(renderizar_card_responsavel(resp, compacto=True), unsafe_allow_html=True)
            
            # Coluna 3
            with col3:
                for resp in col3_resp:
                    st.markdown(renderizar_card_responsavel(resp, compacto=True), unsafe_allow_html=True)
        
        # Adicionar legenda explicativa mais compacta
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%); border-radius: 10px; padding: 10px; margin-top: 10px; text-align: center;">
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.3rem; margin-right: 5px;">🥇 🥈 🥉</span>
                    <span style="font-size: 0.9rem; color: #455A64;">Top 3</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.3rem; margin-right: 5px;">🎯</span>
                    <span style="font-size: 0.9rem; color: #455A64;">Meta atingida</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background: linear-gradient(135deg, rgba(46, 125, 50, 0.1) 0%, rgba(200, 230, 201, 0.6) 100%); border-radius: 3px; margin-right: 5px;"></div>
                    <span style="font-size: 0.9rem; color: #455A64;">Fundo verde = meta</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erro ao gerar ranking de produtividade: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def slide_analise_diaria(df, date_from, date_to):
    """
    Slide com análise diária de conclusões
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Análise de Conclusões por Dia</h2>', unsafe_allow_html=True)
    
    try:
        if df.empty or 'DATA_CONCLUSAO' not in df.columns:
            st.warning("Não há dados disponíveis para análise diária.")
            return
        
        # Preparar dados
        df_valido = df.dropna(subset=['DATA_CONCLUSAO']).copy()
        df_diario = df_valido.groupby(df_valido['DATA_CONCLUSAO'].dt.date).size().reset_index(name='CONCLUSOES')
        
        if df_diario.empty:
            st.warning("Não há dados disponíveis para análise diária.")
            return
    
        # Encontrar a data da primeira conclusão
        data_primeira_conclusao = df_valido['DATA_CONCLUSAO'].min().date()
        
        # Ajustar a data inicial para ser a data da primeira conclusão
        if isinstance(date_from, datetime):
            data_inicio_efetiva = max(date_from.date(), data_primeira_conclusao)
        else:
            data_inicio_efetiva = max(date_from, data_primeira_conclusao)
        
        # Média simples (média aritmética diária)
        media_diaria_simples = df_diario['CONCLUSOES'].mean()
        
        # Calcular dias úteis naturais a partir da primeira conclusão
        dias_uteis_naturais = 0
        
        # Converter para datetime se não for
        if not isinstance(date_from, datetime):
            date_from = datetime.combine(date_from, datetime.min.time())
        if not isinstance(date_to, datetime):
            date_to = datetime.combine(date_to, datetime.min.time())
        
        # Calcular dia a dia
        data_atual = datetime.combine(data_inicio_efetiva, datetime.min.time())
        while data_atual.date() <= date_to.date():
            dia_semana = data_atual.weekday()
            if dia_semana <= 5:  # Segunda a sábado
                dias_uteis_naturais += 1
            data_atual += timedelta(days=1)
        
        # Média ajustada (por dia útil natural)
        total_conclusoes = df_diario['CONCLUSOES'].sum()
        media_diaria_ajustada = round(total_conclusoes / dias_uteis_naturais, 1)
        
        # Criar gráfico para TV vertical
        fig = go.Figure()
        
        # Adicionar barras para conclusões diárias
        fig.add_trace(go.Bar(
            x=df_diario['DATA_CONCLUSAO'],
            y=df_diario['CONCLUSOES'],
            name='Conclusões',
            text=df_diario['CONCLUSOES'],
            textposition='auto',
            textfont=dict(size=16),
            hovertemplate='%{x|%d/%m/%Y}<br>Conclusões: %{y}',
            marker=dict(
                color='#1976D2',
                line=dict(color='#0D47A1', width=2)
            )
        ))
        
        # Adicionar linha de média simples
        fig.add_trace(go.Scatter(
            x=df_diario['DATA_CONCLUSAO'],
            y=[media_diaria_simples] * len(df_diario),
            mode='lines',
            name='Média Simples',
            line=dict(color='#FF5722', width=3, dash='dash')
        ))
        
        # Adicionar linha de média ajustada por dias úteis
        fig.add_trace(go.Scatter(
            x=df_diario['DATA_CONCLUSAO'],
            y=[media_diaria_ajustada] * len(df_diario),
            mode='lines',
            name='Média Dias Úteis',
            line=dict(color='#9C27B0', width=3, dash='dot')
        ))
        
        # Configurar layout otimizado para TV vertical
        fig.update_layout(
            title={
                'text': f'Conclusões Diárias',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24, 'color': '#1A237E', 'family': 'Arial, Helvetica, sans-serif'}
            },
            xaxis_title={'text': 'Data', 'font': {'size': 18}},
            yaxis_title={'text': 'Conclusões', 'font': {'size': 18}},
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'center',
                'x': 0.5,
                'font': {'size': 16}
            },
            height=500,
            margin=dict(l=50, r=50, t=100, b=100), # Aumentar margin bottom para acomodar rótulos
            template='plotly_white',
            hovermode='x unified',
            bargap=0.3  # Espaçar barras para melhor visualização
        )
        
        # Melhorar a formatação das datas no eixo x
        fig.update_xaxes(
            tickformat='%d/%m',
            tickfont={'size': 14},
            tickangle=0,  # Zero graus para exibir datas na horizontal
            tickmode='array',
            tickvals=df_diario['DATA_CONCLUSAO'],
            ticktext=[d.strftime('%d/%m') for d in df_diario['DATA_CONCLUSAO']]
        )
        
        # Melhorar a formatação dos números no eixo y
        fig.update_yaxes(
            tickfont={'size': 14}
        )
        
        # Exibir o gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas de destaque para análise diária
        col1, col2 = st.columns(2)
        
        # Encontrar o dia mais produtivo
        idx_max = df_diario['CONCLUSOES'].idxmax()
        dia_mais_produtivo = df_diario.iloc[idx_max]
        data_mais_produtiva = dia_mais_produtivo['DATA_CONCLUSAO'].strftime('%d/%m/%Y')
        conclusoes_mais_produtivo = int(dia_mais_produtivo['CONCLUSOES'])
        
        # Encontrar o dia menos produtivo
        idx_min = df_diario['CONCLUSOES'].idxmin()
        dia_menos_produtivo = df_diario.iloc[idx_min]
        data_menos_produtiva = dia_menos_produtivo['DATA_CONCLUSAO'].strftime('%d/%m/%Y')
        conclusoes_menos_produtivo = int(dia_menos_produtivo['CONCLUSOES'])
        
        # Métricas mais relevantes - DESIGN MELHORADO
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 15px; padding: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #1976D2; text-align: center;">
                <div style="font-size: 1.6rem; font-weight: 700; color: #1565C0; margin-bottom: 10px;">
                    Dia Mais Produtivo
                </div>
                <div style="font-size: 2.2rem; font-weight: 900; color: #0D47A1;">
                    {conclusoes_mais_produtivo}
                </div>
                <div style="font-size: 1.4rem; color: #1976D2; font-weight: 600;">
                    conclusões em {data_mais_produtiva}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%); border-radius: 15px; padding: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #FF9800; text-align: center;">
                <div style="font-size: 1.6rem; font-weight: 700; color: #FFA000; margin-bottom: 10px;">
                    Média Dias Úteis
                </div>
                <div style="font-size: 2.2rem; font-weight: 900; color: #FF6F00;">
                    {f"{media_diaria_ajustada:.1f}".replace(".", ",")}
                </div>
                <div style="font-size: 1.4rem; color: #FFA000; font-weight: 600;">
                    conclusões/dia útil
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao gerar análise diária: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def slide_analise_semanal(df):
    """
    Slide com análise de conclusões por semana
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Análise de Conclusões por Semana</h2>', unsafe_allow_html=True)
    
    try:
        if df.empty or 'DATA_CONCLUSAO' not in df.columns:
            st.warning("Não há dados disponíveis para análise semanal.")
            return
    
        # Preparar dados
        df_valido = df.dropna(subset=['DATA_CONCLUSAO']).copy()
        
        # Adicionar coluna de semana no formato YYYY-WW
        df_valido['SEMANA'] = df_valido['DATA_CONCLUSAO'].dt.strftime('%Y-%V')
    
    # Agrupar por semana
        df_semanal = df_valido.groupby('SEMANA').size().reset_index(name='CONCLUSOES')
        
        if df_semanal.empty:
            st.warning("Não há dados disponíveis para análise semanal.")
            return
        
        # Adicionar coluna de texto para semana
        df_semanal['SEMANA_TEXTO'] = df_semanal['SEMANA'].apply(
            lambda x: f'Semana {x.split("-")[1]} de {x.split("-")[0]}'
        )
        
        # Média semanal
        media_semanal = df_semanal['CONCLUSOES'].mean()
        
        # Criar gráfico
        fig = go.Figure()
        
        # Adicionar barras para conclusões semanais
        fig.add_trace(go.Bar(
            x=df_semanal['SEMANA'],
            y=df_semanal['CONCLUSOES'],
            name='Conclusões',
            text=df_semanal['CONCLUSOES'],
            textposition='auto',
            textfont=dict(size=16),
            hovertemplate='<b>%{customdata}</b><br>Conclusões: %{text}',
            customdata=df_semanal['SEMANA_TEXTO'],
            marker=dict(
                color='#2196F3',
                line=dict(color='#1565C0', width=2)
            )
        ))
        
        # Adicionar linha de média
        fig.add_trace(go.Scatter(
            x=df_semanal['SEMANA'],
            y=[media_semanal] * len(df_semanal),
            mode='lines',
            name='Média',
            line=dict(color='#FF5722', width=3, dash='dash')
        ))
        
        # Configurar layout otimizado para TV vertical
        fig.update_layout(
            title={
                'text': f'Conclusões por Semana',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24, 'color': '#1A237E', 'family': 'Arial, Helvetica, sans-serif'}
            },
            xaxis_title={'text': 'Semana', 'font': {'size': 18}},
            yaxis_title={'text': 'Conclusões', 'font': {'size': 18}},
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'center',
                'x': 0.5,
                'font': {'size': 16}
            },
            height=500,
            margin=dict(l=50, r=50, t=100, b=100),  # Aumentar margem inferior
            template='plotly_white',
            hovermode='x unified',
            bargap=0.3  # Espaçar barras para melhor visualização
        )
        
        # Personalizar eixos
        fig.update_xaxes(
            tickangle=0,  # Zero graus para exibir na horizontal
            tickfont={'size': 14},
            tickmode='array',
            tickvals=df_semanal['SEMANA'],
            ticktext=[f"Semana {x.split('-')[1]}" for x in df_semanal['SEMANA']]
        )
        
        fig.update_yaxes(
            tickfont={'size': 14}
        )
        
        # Exibir o gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas de destaque
        semana_mais_produtiva = df_semanal.loc[df_semanal['CONCLUSOES'].idxmax()]
        
        # Remover grid e colocar os cards um abaixo do outro
        st.markdown(f"""
        <div style="margin-top: 20px;">
            <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-radius: 15px; padding: 18px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #4CAF50; text-align: center; margin-bottom: 20px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #2E7D32; margin-bottom: 10px;">
                    Semana Mais Produtiva
                </div>
                <div style="font-size: 2rem; font-weight: 900; color: #1B5E20;">
                    {int(semana_mais_produtiva['CONCLUSOES'])}
                </div>
                <div style="font-size: 1.2rem; color: #4CAF50; font-weight: 600;">
                    conclusões na {semana_mais_produtiva['SEMANA_TEXTO']}
                </div>
            </div>
        </div>

        <div style="margin-top: 20px;">
            <div style="background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); border-radius: 15px; padding: 18px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #9C27B0; text-align: center; margin-bottom: 20px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #7B1FA2; margin-bottom: 10px;">
                    Média por Semana
                </div>
                <div style="font-size: 2rem; font-weight: 900; color: #6A1B9A;">
                    {f"{media_semanal:.1f}".replace(".", ",")}
                </div>
                <div style="font-size: 1.2rem; color: #9C27B0; font-weight: 600;">
                    conclusões/semana
                </div>
            </div>
        </div>

        <div style="margin-top: 20px;">
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 15px; padding: 18px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #2196F3; text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #1565C0; margin-bottom: 10px;">
                    Total de Semanas
                </div>
                <div style="font-size: 2rem; font-weight: 900; color: #0D47A1;">
                    {len(df_semanal)}
                </div>
                <div style="font-size: 1.2rem; color: #2196F3; font-weight: 600;">
                    semanas com registros
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao gerar análise semanal: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def slide_analise_dia_semana(df):
    """
    Slide com análise de conclusões por dia da semana
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Análise por Dia da Semana</h2>', unsafe_allow_html=True)
    
    try:
        if df.empty or 'DATA_CONCLUSAO' not in df.columns:
            st.warning("Não há dados disponíveis para análise por dia da semana.")
            return
    
        # Preparar dados
        df_valido = df.dropna(subset=['DATA_CONCLUSAO']).copy()
        
        # Mapeamento para traduzir dias da semana
        dias_semana_pt = {
            'Monday': 'Segunda-feira',
            'Tuesday': 'Terça-feira',
            'Wednesday': 'Quarta-feira',
            'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
    # Adicionar coluna de dia da semana
        df_valido['DIA_SEMANA'] = df_valido['DATA_CONCLUSAO'].dt.day_name().map(dias_semana_pt)
    
    # Agrupar por dia da semana
        df_dia_semana = df_valido.groupby('DIA_SEMANA').agg({
            'DATA_CONCLUSAO': 'count',
            'ID': 'nunique'
        }).reset_index()
        df_dia_semana.columns = ['DIA_SEMANA', 'CONCLUSOES', 'PROCESSOS_UNICOS']
        
        # Ordenar os dias da semana
        ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
        df_dia_semana['DIA_ORDEM'] = pd.Categorical(df_dia_semana['DIA_SEMANA'], categories=ordem_dias, ordered=True)
        df_dia_semana = df_dia_semana.sort_values('DIA_ORDEM')
        
        # Média de conclusões por dia
        media_conclusoes = df_dia_semana['CONCLUSOES'].mean()
        
        # Criar gráfico
        fig = go.Figure()
        
        # Adicionar barras para conclusões por dia da semana
        fig.add_trace(go.Bar(
            x=df_dia_semana['DIA_SEMANA'],
            y=df_dia_semana['CONCLUSOES'],
            name='Conclusões',
            text=df_dia_semana['CONCLUSOES'],
            textposition='auto',
            hovertemplate='%{x}<br>Conclusões: %{y}',
            marker=dict(
                color='#673AB7',
                line=dict(color='#512DA8', width=2)
            )
        ))
        
        # Adicionar linha de média
        fig.add_trace(go.Scatter(
            x=df_dia_semana['DIA_SEMANA'],
            y=[media_conclusoes] * len(df_dia_semana),
            mode='lines',
            name='Média',
            line=dict(color='#FF5722', width=3, dash='dash')
        ))
        
        # Configurar layout otimizado para TV vertical
        fig.update_layout(
            title={
                'text': f'Conclusões por Dia da Semana',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24, 'color': '#1A237E', 'family': 'Arial, Helvetica, sans-serif'}
            },
            xaxis_title={'text': 'Dia da Semana', 'font': {'size': 18}},
            yaxis_title={'text': 'Conclusões', 'font': {'size': 18}},
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'center',
                'x': 0.5,
                'font': {'size': 16}
            },
            height=500,
            margin=dict(l=50, r=50, t=100, b=80),
            template='plotly_white',
            hovermode='x unified'
        )
        
        # Personalizar eixos
        fig.update_xaxes(
            tickfont={'size': 14}
        )
        
        fig.update_yaxes(
            tickfont={'size': 14}
        )
        
        # Exibir o gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas de destaque
        dia_mais_produtivo = df_dia_semana.loc[df_dia_semana['CONCLUSOES'].idxmax()]
        
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ede7f6 0%, #d1c4e9 100%); border-radius: 15px; padding: 18px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #673AB7; text-align: center; height: 100%;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #512DA8; margin-bottom: 10px;">
                    Dia Mais Produtivo
                </div>
                <div style="font-size: 2rem; font-weight: 900; color: #311B92;">
                    {dia_mais_produtivo['DIA_SEMANA']}
                </div>
                <div style="font-size: 1.2rem; color: #673AB7; font-weight: 600;">
                    {int(dia_mais_produtivo['CONCLUSOES'])} conclusões
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); border-radius: 15px; padding: 18px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #FF9800; text-align: center; height: 100%;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #F57C00; margin-bottom: 10px;">
                    Média por Dia
                </div>
                <div style="font-size: 2.2rem; font-weight: 900; color: #E65100;">
                    {f"{media_conclusoes:.1f}".replace(".", ",")}
                </div>
                <div style="font-size: 1.4rem; color: #FF9800; font-weight: 600;">
                    conclusões/dia
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Adicionar informação adicional sobre processos únicos
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-radius: 15px; padding: 18px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #4CAF50; text-align: center; margin-top: 20px;">
            <div style="font-size: 1.5rem; font-weight: 700; color: #2E7D32; margin-bottom: 10px;">
                Processos Únicos no Dia Mais Produtivo
            </div>
            <div style="font-size: 2rem; font-weight: 900; color: #1B5E20;">
                {int(dia_mais_produtivo['PROCESSOS_UNICOS'])}
            </div>
            <div style="font-size: 1.2rem; color: #4CAF50; font-weight: 600;">
                processos concluídos às {dia_mais_produtivo['DIA_SEMANA']}s
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao gerar análise por dia da semana: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def slide_analise_horario(df):
    """
    Slide com análise de conclusões por horário do dia
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Análise por Hora do Dia</h2>', unsafe_allow_html=True)
    
    try:
        if df.empty or 'DATA_CONCLUSAO' not in df.columns:
            st.warning("Não há dados disponíveis para análise por horário.")
            return
    
        # Preparar dados
        df_valido = df.dropna(subset=['DATA_CONCLUSAO']).copy()
        df_valido['HORA'] = df_valido['DATA_CONCLUSAO'].dt.hour
    
    # Agrupar por hora
        df_hora = df_valido.groupby('HORA').size().reset_index(name='CONCLUSOES')
        
        # Certificar que todas as horas estão representadas (0-23)
        todas_horas = pd.DataFrame({'HORA': range(24)})
        df_hora = pd.merge(todas_horas, df_hora, on='HORA', how='left').fillna(0)
        
        # Calcular médias
        media_hora = df_hora['CONCLUSOES'].mean()
        
        # Categorizar períodos do dia
        manha = df_hora[df_hora['HORA'].between(6, 11)]['CONCLUSOES'].sum()
        tarde = df_hora[df_hora['HORA'].between(12, 17)]['CONCLUSOES'].sum()
        noite = df_hora[df_hora['HORA'].between(18, 23)]['CONCLUSOES'].sum()
        madrugada = df_hora[df_hora['HORA'].between(0, 5)]['CONCLUSOES'].sum()
        
        # Determinar o período mais produtivo
        periodos = [
            ("Manhã", manha),
            ("Tarde", tarde),
            ("Noite", noite),
            ("Madrugada", madrugada)
        ]
        periodo_mais_produtivo = max(periodos, key=lambda x: x[1])
        
        # Criar gráfico
        fig = go.Figure()
        
        # Cores para cada período do dia
        cores_periodo = {
            'manha': '#FF9800',  # Laranja para manhã
            'tarde': '#2196F3',  # Azul para tarde
            'noite': '#673AB7',  # Roxo para noite
            'madrugada': '#78909C'  # Cinza para madrugada
        }
        
        # Cores para cada barra com base no período
        cores_barras = []
        for hora in df_hora['HORA']:
            if 6 <= hora <= 11:
                cores_barras.append(cores_periodo['manha'])
            elif 12 <= hora <= 17:
                cores_barras.append(cores_periodo['tarde'])
            elif 18 <= hora <= 23:
                cores_barras.append(cores_periodo['noite'])
            else:
                cores_barras.append(cores_periodo['madrugada'])
        
        # Adicionar barras para conclusões por hora
        fig.add_trace(go.Bar(
            x=df_hora['HORA'],
            y=df_hora['CONCLUSOES'],
            name='Conclusões',
            text=df_hora['CONCLUSOES'].astype(int),
            textposition='auto',
            hovertemplate='%{x}:00h<br>Conclusões: %{y}',
            marker=dict(
                color=cores_barras,
                line=dict(width=1, color='#212121')
            )
        ))
        
        # Adicionar linha de média
        fig.add_trace(go.Scatter(
            x=df_hora['HORA'],
            y=[media_hora] * len(df_hora),
            mode='lines',
            name='Média',
            line=dict(color='#E91E63', width=3, dash='dash')
        ))
        
        # Configurar layout otimizado para TV vertical
        fig.update_layout(
            title={
                'text': f'Conclusões por Hora do Dia',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24, 'color': '#1A237E', 'family': 'Arial, Helvetica, sans-serif'}
            },
            xaxis_title={'text': 'Hora', 'font': {'size': 18}},
            yaxis_title={'text': 'Conclusões', 'font': {'size': 18}},
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'center',
                'x': 0.5,
                'font': {'size': 16}
            },
            height=500,
            margin=dict(l=50, r=50, t=100, b=80),
            template='plotly_white',
            hovermode='x unified'
        )
        
        # Personalizar eixos
        fig.update_xaxes(
            tickvals=list(range(24)),
            ticktext=[f"{i:02d}:00" for i in range(24)],
            tickangle=45,
            tickfont={'size': 14}
        )
        
        fig.update_yaxes(
            tickfont={'size': 14}
        )
        
        # Exibir o gráfico
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Métricas de destaque em cards
        hora_mais_produtiva = df_hora.loc[df_hora['CONCLUSOES'].idxmax()]
        hora_mais_produtiva_valor = int(hora_mais_produtiva['HORA'])
        
        # Exibir métricas em cards
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            # Horário mais produtivo
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 15px; padding: 18px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #2196F3; text-align: center; height: 100%;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #1565C0; margin-bottom: 10px;">
                    Horário Mais Produtivo
                </div>
                <div style="font-size: 2rem; font-weight: 900; color: #0D47A1;">
                    {hora_mais_produtiva_valor:02d}:00
                </div>
                <div style="font-size: 1.2rem; color: #2196F3; font-weight: 600;">
                    {int(hora_mais_produtiva['CONCLUSOES'])} conclusões
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Período mais produtivo
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%); border-radius: 15px; padding: 18px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #FFC107; text-align: center; height: 100%;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #FFA000; margin-bottom: 10px;">
                    Período Mais Produtivo
                </div>
                <div style="font-size: 2rem; font-weight: 900; color: #FF6F00;">
                    {periodo_mais_produtivo[0]}
                </div>
                <div style="font-size: 1.2rem; color: #FFA000; font-weight: 600;">
                    {int(periodo_mais_produtivo[1])} conclusões
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Resumo por período
        st.markdown(f"""
        <div style="margin-top: 20px; text-align: center;">
            <div style="font-size: 1.5rem; font-weight: 700; color: #1A237E; margin-bottom: 15px;">
                Conclusões por Período do Dia
            </div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
                <div style="background: linear-gradient(135deg, rgba(255, 152, 0, 0.2) 0%, rgba(255, 152, 0, 0.4) 100%); border-radius: 10px; padding: 12px; border: 2px solid {cores_periodo['manha']}; flex: 1;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #E65100;">Manhã</div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: {cores_periodo['manha']};">{int(manha)}</div>
                    <div style="font-size: 1rem; color: #E65100;">(6h - 11h)</div>
                </div>
                <div style="background: linear-gradient(135deg, rgba(33, 150, 243, 0.2) 0%, rgba(33, 150, 243, 0.4) 100%); border-radius: 10px; padding: 12px; border: 2px solid {cores_periodo['tarde']}; flex: 1;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #0D47A1;">Tarde</div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: {cores_periodo['tarde']};">{int(tarde)}</div>
                    <div style="font-size: 1rem; color: #0D47A1;">(12h - 17h)</div>
                </div>
                <div style="background: linear-gradient(135deg, rgba(103, 58, 183, 0.2) 0%, rgba(103, 58, 183, 0.4) 100%); border-radius: 10px; padding: 12px; border: 2px solid {cores_periodo['noite']}; flex: 1;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #311B92;">Noite</div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: {cores_periodo['noite']};">{int(noite)}</div>
                    <div style="font-size: 1rem; color: #311B92;">(18h - 23h)</div>
                </div>
                <div style="background: linear-gradient(135deg, rgba(120, 144, 156, 0.2) 0%, rgba(120, 144, 156, 0.4) 100%); border-radius: 10px; padding: 12px; border: 2px solid {cores_periodo['madrugada']}; flex: 1;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #263238;">Madrugada</div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: {cores_periodo['madrugada']};">{int(madrugada)}</div>
                    <div style="font-size: 1rem; color: #263238;">(0h - 5h)</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao gerar análise por horário: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def slide_producao_metricas_macro(df):
    """
    Slide com métricas macro de produção para apresentação automática
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Métricas de Produção</h2>', unsafe_allow_html=True)
    
    # Usar os dados de produção da sessão para garantir que temos os dados corretos
    if 'df_producao' in st.session_state and st.session_state['df_producao'] is not None and not st.session_state['df_producao'].empty:
        df = st.session_state['df_producao']
    
    if df is None or df.empty:
        st.warning("Não há dados disponíveis para análise de produção.")
        return
    
    # Calcular contagem por status
    status_counts = {}
    if 'UF_CRM_HIGILIZACAO_STATUS' in df.columns:
        # Substituir valores nulos no status por 'PENDENCIA'
        df['UF_CRM_HIGILIZACAO_STATUS'] = df['UF_CRM_HIGILIZACAO_STATUS'].fillna('PENDENCIA')
        
        # Contar por status
        status_series = df['UF_CRM_HIGILIZACAO_STATUS'].value_counts()
        
        # Garantir que todos os status estão presentes
        for status in ['COMPLETO', 'INCOMPLETO', 'PENDENCIA']:
            status_counts[status] = status_series.get(status, 0)
    else:
        status_counts = {'COMPLETO': 0, 'INCOMPLETO': 0, 'PENDENCIA': 0}
    
    # Total de registros
    total_registros = sum(status_counts.values())
    
    # Layout de cards otimizados para TV vertical
    col1, col2 = st.columns(2, gap="large")
    
    # Card 1: Total de Registros - DESIGN MELHORADO
    with col1:
        st.markdown(f"""
        <div class="metric-card-tv total" style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);">
            <div class="metric-title-tv">Total Registros</div>
            <div class="metric-value-tv">{f"{total_registros:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">em higienização</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 2: Processos Completos - DESIGN MELHORADO
    with col2:
        st.markdown(f"""
        <div class="metric-card-tv total" style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);">
            <div class="metric-title-tv">Completos</div>
            <div class="metric-value-tv">{f"{status_counts['COMPLETO']:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">processos</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 3: Processos Incompletos - DESIGN MELHORADO
    with col1:
        st.markdown(f"""
        <div class="metric-card-tv media" style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); border-color: #FF9800;">
            <div class="metric-title-tv">Incompletos</div>
            <div class="metric-value-tv">{f"{status_counts['INCOMPLETO']:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">processos</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 4: Processos Pendentes - DESIGN MELHORADO
    with col2:
        st.markdown(f"""
        <div class="metric-card-tv taxa" style="background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%); border-color: #F44336;">
            <div class="metric-title-tv">Pendentes</div>
            <div class="metric-value-tv">{f"{status_counts['PENDENCIA']:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">processos</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 5: Taxa de Conclusão - DESIGN MELHORADO
    taxa_conclusao = round((status_counts['COMPLETO'] / max(1, total_registros) * 100), 1)
    
    # Criar um grande card com a taxa de conclusão
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                border-left: 10px solid #2E7D32; 
                padding: 20px; 
                margin: 20px 0; 
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); 
                text-align: center; 
                border-radius: 10px;">
        <div style="font-size: 2.2rem; font-weight: 700; color: #2E7D32; margin-bottom: 10px;">
            Taxa de Conclusão
        </div>
        <div style="font-size: 4.5rem; font-weight: 900; color: #2E7D32;">
            {taxa_conclusao}%
        </div>
        <div style="font-size: 1.5rem; margin-top: 15px;">
            <span style="font-weight: 700;">{status_counts['COMPLETO']} concluídos</span> 
            <span style="margin: 0 10px;">de</span>
            <span style="font-weight: 700;">{total_registros} processos</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def slide_producao_status_responsavel(df):
    """
    Slide com status por responsável para apresentação automática
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Status por Responsável</h2>', unsafe_allow_html=True)
    
    # Usar os dados de produção da sessão para garantir que temos os dados corretos
    if 'df_producao' in st.session_state and st.session_state['df_producao'] is not None and not st.session_state['df_producao'].empty:
        df = st.session_state['df_producao']
    
    if df is None or df.empty:
        st.warning("Não há dados disponíveis para análise de status por responsável.")
        return
    
    # Verificar colunas necessárias
    if 'ASSIGNED_BY_NAME' not in df.columns or 'UF_CRM_HIGILIZACAO_STATUS' not in df.columns:
        st.warning("Dados não contêm as colunas necessárias para análise de status por responsável.")
        return
    
    try:
        # Substituir valores nulos no status por 'PENDENCIA'
        df['UF_CRM_HIGILIZACAO_STATUS'] = df['UF_CRM_HIGILIZACAO_STATUS'].fillna('PENDENCIA')
        
        # Agrupar por responsável e status e contar ocorrências
        status_counts = df.groupby(['ASSIGNED_BY_NAME', 'UF_CRM_HIGILIZACAO_STATUS']).size().unstack(fill_value=0)
        
        # Garantir que todas as colunas de status existem
        for status in ['COMPLETO', 'INCOMPLETO', 'PENDENCIA']:
            if status not in status_counts.columns:
                status_counts[status] = 0
        
        # Selecionar apenas as colunas que nos interessam
        display_df = status_counts[['COMPLETO', 'INCOMPLETO', 'PENDENCIA']].copy()
        
        # Resetar o índice
        display_df = display_df.reset_index()
        
        # Remover linhas com 'TOTAL' no nome do responsável
        display_df = display_df[~display_df['ASSIGNED_BY_NAME'].astype(str).str.lower().str.contains('total')]
        
        # Calcular o total para cada responsável
        display_df['TOTAL'] = display_df[['COMPLETO', 'INCOMPLETO', 'PENDENCIA']].sum(axis=1)
        
        # Calcular o percentual de conclusão
        display_df['TAXA_CONCLUSAO'] = (display_df['COMPLETO'] / display_df['TOTAL'] * 100).round(1)
        
        # Remover registros com TOTAL igual a zero
        display_df = display_df[display_df['TOTAL'] > 0]
        
        # Remover registros com COMPLETO igual a zero
        display_df = display_df[display_df['COMPLETO'] > 0]
        
        # Ordenar por taxa de conclusão descendente (em vez de total)
        display_df = display_df.sort_values('TAXA_CONCLUSAO', ascending=False)
        
        # Calcular totais
        totais = display_df[['COMPLETO', 'INCOMPLETO', 'PENDENCIA', 'TOTAL']].sum()
        taxa_total = (totais['COMPLETO'] / totais['TOTAL'] * 100).round(1)
        
        # Exibir informação do total de processos e taxa de conclusão no topo
        st.markdown(f"""
        <div style="margin-bottom: 25px;">
            <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-radius: 15px; padding: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); text-align: center; border-left: 10px solid #4CAF50;">
                <div style="font-size: 2rem; font-weight: 800; color: #2E7D32; margin-bottom: 8px;">
                    TAXA DE CONCLUSÃO: {taxa_total}%
                </div>
                <div style="font-size: 1.3rem; color: #4CAF50; font-weight: 600;">
                    {int(totais['COMPLETO'])} concluídos de {int(totais['TOTAL'])} processos
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Função para renderizar o card de cada responsável
        def renderizar_card_status(row, i, destaque=False):
            # Extrair valores da linha
            nome = row['ASSIGNED_BY_NAME']
            completos = int(row['COMPLETO'])
            incompletos = int(row['INCOMPLETO'])
            pendentes = int(row['PENDENCIA'])
            total = int(row['TOTAL'])
            taxa = row['TAXA_CONCLUSAO']
            
            # Determinar cor baseada na taxa de conclusão
            if taxa >= 80:
                cor = '#4CAF50'  # Verde para alto desempenho
                icone = '🏆'
            elif taxa >= 50:
                cor = '#2196F3'  # Azul para médio desempenho
                icone = '📈'
            elif taxa >= 20:
                cor = '#FFC107'  # Amarelo para baixo desempenho
                icone = '📊'
            else:
                cor = '#F44336'  # Vermelho para muito baixo desempenho
                icone = '⚠️'
            
            # Determinar cor da posição no ranking baseada no índice
            if i < 3:
                pos_cor = ['#FFD700', '#C0C0C0', '#CD7F32'][i]  # Ouro, Prata, Bronze
                pos_icone = ['🥇', '🥈', '🥉'][i]
            else:
                pos_cor = '#607D8B'  # Cinza para os demais
                pos_icone = f"{i+1}º"
            
            # Aplicar estilo diferenciado para os 3 primeiros
            estilo_card = ""
            if destaque:
                estilo_card = "box-shadow: 0 6px 16px rgba(0,0,0,0.18);"
            
            # Fundo baseado na conclusão
            fundo = f"linear-gradient(135deg, rgba({','.join(str(int(x)) for x in bytes.fromhex(cor[1:]))}, 0.1) 0%, rgba({','.join(str(int(x)) for x in bytes.fromhex(cor[1:]))}, 0.3) 100%)"
            
            if destaque:
                # Versão normal para os destaques
                return f"""
                <div style="background: {fundo}; border-radius: 10px; padding: 12px 10px; margin-bottom: 15px; 
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); position: relative; border-left: 6px solid {pos_cor}; {estilo_card}
                        width: 100%; max-width: 100%; overflow: hidden;">
                    <div style="position: absolute; top: 6px; right: 8px; font-size: 1.2rem;">{pos_icone} {icone}</div>
                    <div style="font-size: 1.1rem; font-weight: 800; margin-bottom: 8px; color: #1A237E; 
                            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 40px;">{nome}</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.8rem; color: #666;">Completos</div>
                            <div style="font-size: 1.1rem; font-weight: 900; color: #4CAF50;">{completos}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.8rem; color: #666;">Incompletos</div>
                            <div style="font-size: 1.1rem; font-weight: 900; color: #FFA000;">{incompletos}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.8rem; color: #666;">Pendentes</div>
                            <div style="font-size: 1.1rem; font-weight: 900; color: #F44336;">{pendentes}</div>
                        </div>
                    </div>
                    <div style="margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <div style="font-size: 0.9rem; font-weight: 700; color: #1A237E;">Taxa de Conclusão:</div>
                            <div style="font-size: 1.2rem; font-weight: 900; color: {cor};">{taxa}%</div>
                        </div>
                        <div style="background-color: #E0E0E0; height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="width: {taxa}%; height: 100%; background-color: {cor};"></div>
                        </div>
                    </div>
                </div>
                """
            else:
                # Versão compacta para os não-destaques
                return f"""
                <div style="background: {fundo}; border-radius: 8px; padding: 8px 8px; margin-bottom: 10px; 
                        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); position: relative; border-left: 4px solid {pos_cor};">
                    <div style="position: absolute; top: 5px; right: 5px; font-size: 1rem;">{pos_icone} {icone}</div>
                    <div style="font-size: 1rem; font-weight: 600; margin-bottom: 5px; color: #1A237E; 
                            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 30px;">{nome}</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.7rem; color: #666;">Comp.</div>
                            <div style="font-size: 1rem; font-weight: 900; color: #4CAF50;">{completos}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.7rem; color: #666;">Inc.</div>
                            <div style="font-size: 1rem; font-weight: 900; color: #FFA000;">{incompletos}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.7rem; color: #666;">Pend.</div>
                            <div style="font-size: 1rem; font-weight: 900; color: #F44336;">{pendentes}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.7rem; color: #666;">Taxa</div>
                            <div style="font-size: 1rem; font-weight: 900; color: {cor};">{taxa}%</div>
                        </div>
                    </div>
                </div>
                """
        
        # Separar destaques (top 3) e demais
        destaques = display_df.head(3)
        outros = display_df.iloc[3:] if len(display_df) > 3 else pd.DataFrame()
        
        # Layout para os destaques
        st.markdown('<div style="margin-bottom: 10px;"><h3 style="font-size: 1.3rem; color: #1A237E; text-align: center;">Top 3 Responsáveis por Volume</h3></div>', unsafe_allow_html=True)
        
        # Mostrar os destaques em formato maior
        for i, (_, row) in enumerate(destaques.iterrows()):
            st.markdown(renderizar_card_status(row, i, destaque=True), unsafe_allow_html=True)
        
        # Layout para os demais em colunas compactas
        if not outros.empty:
            st.markdown('<div style="margin: 10px 0;"><h3 style="font-size: 1.3rem; color: #424242; text-align: center;">Demais Responsáveis</h3></div>', unsafe_allow_html=True)
            
            # Dividir em 3 colunas para caber mais na tela
            col1, col2, col3 = st.columns(3)
            
            # Distribuir os outros responsáveis entre as três colunas
            terco = (len(outros) + 2) // 3
            col1_resp = outros.iloc[:terco]
            col2_resp = outros.iloc[terco:2*terco]
            col3_resp = outros.iloc[2*terco:]
            
            # Coluna 1
            with col1:
                for i, (_, row) in enumerate(col1_resp.iterrows()):
                    st.markdown(renderizar_card_status(row, i + 3, destaque=False), unsafe_allow_html=True)
            
            # Coluna 2
            with col2:
                for i, (_, row) in enumerate(col2_resp.iterrows()):
                    st.markdown(renderizar_card_status(row, i + 3 + len(col1_resp), destaque=False), unsafe_allow_html=True)
            
            # Coluna 3
            with col3:
                for i, (_, row) in enumerate(col3_resp.iterrows()):
                    st.markdown(renderizar_card_status(row, i + 3 + len(col1_resp) + len(col2_resp), destaque=False), unsafe_allow_html=True)
        
        # Adicionar resumo dos totais
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ede7f6 0%, #d1c4e9 100%); border-radius: 10px; padding: 15px; margin-top: 20px; text-align: center;">
            <div style="font-size: 1.5rem; font-weight: 700; color: #4527A0; margin-bottom: 15px;">Resumo Total</div>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px;">
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <div style="font-size: 0.9rem; color: #4CAF50; font-weight: 600;">Completos</div>
                    <div style="font-size: 1.3rem; font-weight: 900; color: #4CAF50;">{int(totais['COMPLETO'])}</div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <div style="font-size: 0.9rem; color: #FFA000; font-weight: 600;">Incompletos</div>
                    <div style="font-size: 1.3rem; font-weight: 900; color: #FFA000;">{int(totais['INCOMPLETO'])}</div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <div style="font-size: 0.9rem; color: #F44336; font-weight: 600;">Pendentes</div>
                    <div style="font-size: 1.3rem; font-weight: 900; color: #F44336;">{int(totais['PENDENCIA'])}</div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <div style="font-size: 0.9rem; color: #1A237E; font-weight: 600;">Total</div>
                    <div style="font-size: 1.3rem; font-weight: 900; color: #1A237E;">{int(totais['TOTAL'])}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Adicionar legenda explicativa mais compacta
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%); border-radius: 10px; padding: 10px; margin-top: 10px; text-align: center;">
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.3rem; margin-right: 5px;">🏆</span>
                    <span style="font-size: 0.9rem; color: #455A64;">Alta conclusão (>80%)</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.3rem; margin-right: 5px;">📈</span>
                    <span style="font-size: 0.9rem; color: #455A64;">Média conclusão (50-80%)</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.3rem; margin-right: 5px;">📊</span>
                    <span style="font-size: 0.9rem; color: #455A64;">Baixa conclusão (20-50%)</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.3rem; margin-right: 5px;">⚠️</span>
                    <span style="font-size: 0.9rem; color: #455A64;">Muito baixa conclusão (<20%)</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao gerar status por responsável: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def slide_producao_pendencias_responsavel(df):
    """
    Slide com pendências por responsável para apresentação automática
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Produção - Pendências por Responsável</h2>', unsafe_allow_html=True)
    
    # Usar os dados de produção da sessão para garantir que temos os dados corretos
    if 'df_producao' in st.session_state and st.session_state['df_producao'] is not None and not st.session_state['df_producao'].empty:
        df = st.session_state['df_producao']
    
    if df is None or df.empty:
        st.warning("Não há dados disponíveis para análise de pendências por responsável.")
        return
    
    # Verificar colunas necessárias
    if 'ASSIGNED_BY_NAME' not in df.columns:
        st.warning("Dados não contêm as colunas necessárias para análise de pendências.")
        return
    
    try:
        # Verificar campos de higienização disponíveis
        from api.bitrix_connector import get_higilizacao_fields
        higilizacao_fields = get_higilizacao_fields()
        
        # Campos específicos para pendências
        campos_pendencia = {
            'UF_CRM_1741183785848': 'Documentação',  # Documentação
            'UF_CRM_1741183721969': 'Cadastro',      # Cadastro
            'UF_CRM_1741183685327': 'Estrutura',     # Estrutura
            'UF_CRM_1741183828129': 'Requerimento',  # Requerimento
            'UF_CRM_1741198696': 'Emissões'          # Emissões
        }
        
        # Verificar quais campos estão disponíveis
        campos_disponiveis = {}
        for campo_id, nome in campos_pendencia.items():
            if campo_id in df.columns:
                campos_disponiveis[campo_id] = nome
        
        # Se não encontrar nenhum campo, usar um conjunto padrão para demonstração
        if not campos_disponiveis:
            st.info("Não foram encontrados campos específicos de higienização. Usando campos padrão para demonstração.")
            campos_disponiveis = {
                'campo_demo_1': 'Documentação',
                'campo_demo_2': 'Cadastro',
                'campo_demo_3': 'Estrutura'
            }
            
            # Adicionar campos demo ao dataframe
            for campo_id in campos_disponiveis.keys():
                df[campo_id] = ['SIM', 'NÃO', 'SIM', 'NÃO', 'SIM'] * (len(df) // 5 + 1)
                df[campo_id] = df[campo_id].iloc[:len(df)]
        
        # Filtrar apenas registros não completos (PENDENCIA ou INCOMPLETO)
        incompletos = df[
            (df['UF_CRM_HIGILIZACAO_STATUS'] != 'COMPLETO') & 
            (~df['UF_CRM_HIGILIZACAO_STATUS'].isna())
        ].copy()
        
        if incompletos.empty:
            st.success("Não há pendências! Todos os processos estão completos.")
            return
        
        # Inicializar DataFrame para pendências
        pendencias_df = pd.DataFrame()
        
        # Agrupar por responsável
        responsaveis = incompletos['ASSIGNED_BY_NAME'].unique()
        
        # Para cada campo, verificar quais registros estão com "NÃO"
        pendencias_data = []
        
        for responsavel in responsaveis:
            # Filtrar registros deste responsável
            df_resp = incompletos[incompletos['ASSIGNED_BY_NAME'] == responsavel]
            
            # Contar pendências em cada campo
            pendencias_row = {'Responsável': responsavel}
            
            for campo_id, nome in campos_disponiveis.items():
                # Contar quantos registros têm "NÃO" neste campo
                pendencias_row[nome] = sum(df_resp[campo_id] == 'NÃO')
            
            # Calcular total de pendências
            pendencias_row['Total'] = sum(pendencias_row.get(nome, 0) for nome in campos_disponiveis.values())
            
            # Adicionar à lista de dados
            pendencias_data.append(pendencias_row)
        
        # Criar DataFrame com os dados
        pendencias_df = pd.DataFrame(pendencias_data)
        
        # Ordenar por total descendente
        pendencias_df = pendencias_df.sort_values('Total', ascending=False)
        
        # Exibir a tabela de pendências usando HTML personalizado
        if not pendencias_df.empty:
            # Usar componentes nativos do Streamlit em vez de HTML
            st.markdown("### Tabela de Pendências por Responsável")
            
            # Aplicar formatação condicional para destacar valores
            def destacar_celula(val):
                if pd.isna(val) or val == 0:
                    return 'background-color: transparent'
                elif val == 1:
                    return 'background-color: rgba(244, 67, 54, 0.5); color: black; font-weight: bold'
                else:
                    return 'background-color: rgba(244, 67, 54, 1.0); color: white; font-weight: bold'
            
            # Destacar a coluna Total com cor diferente
            def destacar_total(val):
                return 'background-color: #1A237E; color: white; font-weight: bold'
            
            # Aplicar estilos ao dataframe
            df_styled = pendencias_df.style.applymap(
                destacar_celula, 
                subset=[col for col in pendencias_df.columns if col != 'Responsável' and col != 'Total']
            ).applymap(
                destacar_total,
                subset=['Total']
            ).format('{:.0f}', subset=[col for col in pendencias_df.columns if col != 'Responsável'])
            
            # Exibir dataframe estilizado
            st.dataframe(
                df_styled,
                use_container_width=True,
                height=min(400, 80 + 35 * len(pendencias_df)),
                column_config={
                    "Responsável": st.column_config.TextColumn("Responsável", width="large"),
                    **{nome: st.column_config.NumberColumn(nome, format="%d") 
                       for nome in campos_disponiveis.values() if nome in pendencias_df.columns},
                    "Total": st.column_config.NumberColumn("Total", format="%d", width="medium")
                }
            )
            
            # Criar dois cards para mostrar informações de resumo usando elementos nativos do Streamlit
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Resumo de Pendências")
                st.markdown(f"""
                - **Total de pendências:** {int(total_geral):,}
                - **Responsáveis com pendência:** {len(pendencias_df)}
                - **Categoria mais crítica:** {max(total_por_categoria, key=total_por_categoria.get)}
                """.replace(",", "."))
            
            with col2:
                st.markdown("#### Ações Recomendadas")
                st.markdown("""
                - Priorize a resolução das pendências em vermelho
                - Distribua tarefas entre a equipe
                - Monitore diariamente a evolução das pendências
                """)
        
        # Adicionar gráfico de barras empilhadas
        st.markdown("<h3 style='margin-top: 30px;'>Distribuição de Pendências</h3>", unsafe_allow_html=True)
        
        # Preparar dados para o gráfico
        df_grafico = pendencias_df.copy()
        
        # Filtrar apenas as colunas de categorias
        colunas_categorias = [col for col in campos_disponiveis.values() if col in df_grafico.columns]
        
        if len(colunas_categorias) > 0:
            # Construir a tabela HTML
            html_table = """
            <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-family: Arial, sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #1A237E; color: white;">
                        <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Responsável</th>
            """
            
            # Adicionar colunas para cada tipo de pendência
            for nome in campos_disponiveis.values():
                html_table += f"""
                        <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">{nome}</th>
                """
            
            html_table += """
                        <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Total</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            # Adicionar linhas para cada responsável (limitando a 10 para melhor visualização)
            for i, (_, row) in enumerate(pendencias_df.head(10).iterrows()):
                # Alternar cores de fundo para as linhas
                row_bg = "#FFECB3" if i % 2 == 0 else "#FFF9C4"
                
                html_table += f"""
                <tr style="background-color: {row_bg};">
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: left; font-weight: bold;">{row['Responsável']}</td>
                """
                
                # Adicionar células para cada tipo de pendência
                for nome in campos_disponiveis.values():
                    if nome in row:
                        value = int(row[nome])
                        if value == 0:
                            html_table += f"""
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{value}</td>
                            """
                        elif value == 1:
                            html_table += f"""
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold; background-color: rgba(244, 67, 54, 0.5); color: black;">{value}</td>
                            """
                        else:
                            html_table += f"""
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold; background-color: rgba(244, 67, 54, 1.0); color: white;">{value}</td>
                            """
                    else:
                        html_table += """
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">0</td>
                        """
                
                # Adicionar célula do total
                total = int(row['Total'])
                html_table += f"""
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold; background-color: #1A237E; color: white;">{total}</td>
                </tr>
                """
            
            # Adicionar linha de totais
            total_por_categoria = {
                nome: pendencias_df[nome].sum() if nome in pendencias_df.columns else 0
                for nome in campos_disponiveis.values()
            }
            total_geral = pendencias_df['Total'].sum()
            
            html_table += f"""
            <tr style="background-color: #E3F2FD; font-weight: bold;">
                <td style="padding: 10px; border: 1px solid #ddd; text-align: left;">TOTAL</td>
            """
            
            for nome in campos_disponiveis.values():
                if nome in total_por_categoria:
                    value = int(total_por_categoria[nome])
                    html_table += f"""
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{value}</td>
                    """
                else:
                    html_table += """
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">0</td>
                    """
            
            html_table += f"""
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center; background-color: #1A237E; color: white;">{int(total_geral)}</td>
            </tr>
            """
            
            # Fechar a tabela
            html_table += """
                </tbody>
            </table>
            </div>
            """
            
            # Criar cards para mostrar informações de resumo
            resumo_html = f"""
            <div style="display: flex; justify-content: space-between; margin: 20px 0;">
                <div style="background-color: #E8F5E9; border-radius: 8px; border-left: 5px solid #4CAF50; padding: 15px; width: 48%;">
                    <div style="font-size: 18px; font-weight: 700; color: #2E7D32; margin-bottom: 10px;">Resumo de Pendências</div>
                    <div style="font-size: 16px;">
                        • <b>Total de pendências:</b> {int(total_geral):,}<br>
                        • <b>Responsáveis com pendência:</b> {len(pendencias_df)}<br>
                        • <b>Categorias mais críticas:</b> {max(total_por_categoria, key=total_por_categoria.get)}
                    </div>
                </div>
                
                <div style="background-color: #FFF3E0; border-radius: 8px; border-left: 5px solid #FF9800; padding: 15px; width: 48%;">
                    <div style="font-size: 18px; font-weight: 700; color: #E65100; margin-bottom: 10px;">Ações Recomendadas</div>
                    <div style="font-size: 16px;">
                        • Priorize a resolução das pendências em vermelho<br>
                        • Distribua tarefas entre a equipe<br>
                        • Monitore diariamente a evolução das pendências
                    </div>
                </div>
            </div>
            """.replace(",", ".")
            
            # Exibir a tabela HTML
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Exibir cards de resumo
            st.markdown(resumo_html, unsafe_allow_html=True)
            
            # Adicionar gráfico de barras empilhadas
            st.markdown("<h3 style='margin-top: 30px;'>Distribuição de Pendências</h3>", unsafe_allow_html=True)
            
            # Preparar dados para o gráfico
            df_grafico = pendencias_df.copy()
            
            # Filtrar apenas as colunas de categorias
            colunas_categorias = [col for col in campos_disponiveis.values() if col in df_grafico.columns]
            
            if len(colunas_categorias) > 0:
                # Limitar a 8 responsáveis para melhor visualização
                if len(df_grafico) > 8:
                    df_grafico = df_grafico.head(8)
                
                # Criar gráfico
                fig = go.Figure()
                
                # Definir cores para as categorias - usar cores mais vibrantes
                cores = {
                    'Documentação': '#E57373',  # Vermelho claro
                    'Cadastro': '#FFB74D',      # Laranja
                    'Estrutura': '#FFF176',     # Amarelo
                    'Requerimento': '#81C784',  # Verde
                    'Emissões': '#64B5F6'       # Azul
                }
                
                # Adicionar barras para cada categoria
                for categoria in colunas_categorias:
                    cor = cores.get(categoria, px.colors.qualitative.Safe[colunas_categorias.index(categoria) % len(px.colors.qualitative.Safe)])
                    fig.add_trace(go.Bar(
                        name=categoria,
                        x=df_grafico['Responsável'],
                        y=df_grafico[categoria],
                        marker_color=cor,
                        text=df_grafico[categoria],
                        textposition='auto'
                    ))
                
                # Atualizar layout
                fig.update_layout(
                    barmode='stack',
                    title={
                        'text': 'Pendências por Categoria e Responsável',
                        'y': 0.95,
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': {'size': 20, 'color': '#1A237E'}
                    },
                    xaxis_title='Responsável',
                    yaxis_title='Número de Pendências',
                    legend_title='Categoria',
                    height=400,
                    margin=dict(l=50, r=50, t=80, b=50),
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                    font=dict(
                        family="Arial, Helvetica, sans-serif",
                        size=14
                    )
                )
                
                # Melhorar grid e eixos
                fig.update_xaxes(
                    tickangle=30,
                    title_font={"size": 14},
                    tickfont={"size": 12},
                )
                fig.update_yaxes(
                    gridcolor='lightgray',
                    title_font={"size": 14},
                    tickfont={"size": 12},
                )
                
                # Exibir o gráfico
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não foram encontradas pendências nos dados filtrados.")
        
    except Exception as e:
        st.error(f"Erro ao gerar análise de pendências por responsável: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def slide_cartorio_visao_geral(df):
    """
    Slide com visão geral do cartório para apresentação automática
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Visão Geral do Cartório</h2>', unsafe_allow_html=True)
    
    # Buscar dados de cartório na sessão
    if 'df_cartorio' in st.session_state and st.session_state['df_cartorio'] is not None and not st.session_state['df_cartorio'].empty:
        df_cartorio = st.session_state['df_cartorio']
        
        # Verificar se precisamos adicionar colunas de métricas
        if 'TOTAL_CERTIDOES' not in df_cartorio.columns or 'CERTIDOES_ENTREGUES' not in df_cartorio.columns:
            # Importar função de análise do módulo cartório
            try:
                from views.cartorio.analysis import analisar_familia_certidoes
                # Atualizar df_cartorio com os dados de análise de certidões
                resultados = analisar_familia_certidoes()
                if resultados is not None and not isinstance(resultados, tuple):
                    # Se temos os dados de certidões, usamos eles
                    df_cartorio = resultados
            except Exception as e:
                st.warning(f"Não foi possível analisar certidões: {str(e)}")
    else:
        # Se não temos dados do cartório na sessão, tentamos carregar do módulo cartório
        try:
            from views.cartorio.data_loader import carregar_dados_cartorio
            df_cartorio = carregar_dados_cartorio()
            
            # Adicionar à sessão para uso futuro
            if df_cartorio is not None and not df_cartorio.empty:
                st.session_state['df_cartorio'] = df_cartorio
            else:
                raise ValueError("Dados de cartório vazios")
        except Exception as e:
            st.warning(f"Não foi possível carregar dados do cartório: {str(e)}")
            
            # Criar dados de exemplo para demonstração visual
            df_cartorio = pd.DataFrame({
                'NOME_CARTORIO': ['CARTÓRIO CASA VERDE', 'CARTÓRIO TATUÁPE'] * 5,
                'ID': range(1, 11),
                'STATUS': ['Em Andamento', 'Concluído', 'Pendente', 'Em Andamento', 'Concluído',
                           'Pendente', 'Em Andamento', 'Concluído', 'Pendente', 'Em Andamento'],
                'TOTAL_CERTIDOES': [10, 15, 8, 12, 20, 7, 14, 18, 9, 11],
                'CERTIDOES_ENTREGUES': [5, 15, 2, 8, 20, 0, 9, 18, 3, 7]
            })
    
    # Layout de cards
    total_processos = len(df_cartorio)
    total_certidoes = df_cartorio['TOTAL_CERTIDOES'].sum() if 'TOTAL_CERTIDOES' in df_cartorio.columns else 0
    certidoes_entregues = df_cartorio['CERTIDOES_ENTREGUES'].sum() if 'CERTIDOES_ENTREGUES' in df_cartorio.columns else 0
    
    # Taxa de entrega
    taxa_entrega = round((certidoes_entregues / max(1, total_certidoes) * 100), 1)
    
    # Processos por status
    status_counts = df_cartorio['STATUS'].value_counts() if 'STATUS' in df_cartorio.columns else pd.Series()
    
    # Layout de cards otimizados para TV vertical
    col1, col2 = st.columns(2, gap="large")
    
    # Card 1: Total de Processos - DESIGN MELHORADO
    with col1:
        st.markdown(f"""
        <div class="metric-card-tv total" style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);">
            <div class="metric-title-tv">Total Processos</div>
            <div class="metric-value-tv">{f"{total_processos:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">em cartório</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 2: Total de Certidões - DESIGN MELHORADO
    with col2:
        st.markdown(f"""
        <div class="metric-card-tv total" style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);">
            <div class="metric-title-tv">Total Certidões</div>
            <div class="metric-value-tv">{f"{total_certidoes:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">solicitadas</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 3: Certidões Entregues - DESIGN MELHORADO
    with col1:
        st.markdown(f"""
        <div class="metric-card-tv media" style="background: linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%); border-color: #3F51B5;">
            <div class="metric-title-tv">Entregues</div>
            <div class="metric-value-tv">{f"{certidoes_entregues:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">certidões</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 4: Taxa de Entrega - DESIGN MELHORADO
    with col2:
        st.markdown(f"""
        <div class="metric-card-tv taxa" style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);">
            <div class="metric-title-tv">Taxa Entrega</div>
            <div class="metric-value-tv">{taxa_entrega}%</div>
            <div class="metric-subtitle-tv">de certidões</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Gráfico de status
    if not status_counts.empty:
        st.markdown("### Distribuição por Status")
        
        # Cores para cada status
        cores_status = {
            'Concluído': '#4CAF50',
            'Em Andamento': '#2196F3',
            'Pendente': '#FFC107',
            'Cancelado': '#F44336'
        }
        
        # Criar gráfico de pizza com plotly
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Distribuição por Status",
            template="plotly_white",
            color=status_counts.index,
            color_discrete_map=cores_status,
            height=500
        )
        
        fig.update_traces(
            textinfo='percent+label',
            textfont_size=16,
            marker=dict(line=dict(color='#FFFFFF', width=2))
        )
        
        fig.update_layout(
            font=dict(size=14),
            margin=dict(l=20, r=20, t=80, b=20),
            legend=dict(font=dict(size=14)),
            title_font=dict(size=22)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def slide_cartorio_analise_familias(df):
    """
    Slide com análise de famílias para apresentação automática
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Análise de Famílias</h2>', unsafe_allow_html=True)
    
    # Buscar dados de famílias na sessão
    if 'df_familias' in st.session_state and st.session_state['df_familias'] is not None and not st.session_state['df_familias'].empty:
        df_familias = st.session_state['df_familias']
    else:
        st.warning("Não há dados de famílias disponíveis. Os dados serão carregados na próxima execução.")
        
        # Criar dados de exemplo para demonstração visual
        df_familias = pd.DataFrame({
            'ID_FAMILIA': ['1x1', '2x1', '3x2', '4x1', '5x3', '6x2', '7x1'],
            'MEMBROS': [3, 4, 5, 2, 6, 4, 3],
            'CONCLUIDOS': [3, 2, 3, 1, 4, 2, 3],
            'CARTORIO': ['Cartório A', 'Cartório B', 'Cartório A', 'Cartório C', 'Cartório B', 'Cartório A', 'Cartório C'],
            'TOTAL_CERTIDOES': [9, 12, 15, 6, 18, 12, 9],
            'CERTIDOES_ENTREGUES': [9, 6, 10, 2, 12, 5, 9],
            'DATA_INICIO': pd.date_range(start='2023-01-01', periods=7, freq='7D')
        })
    
    # Calcular estatísticas
    total_familias = len(df_familias)
    media_membros = df_familias['MEMBROS'].mean() if 'MEMBROS' in df_familias.columns else 0
    total_certidoes = df_familias['TOTAL_CERTIDOES'].sum() if 'TOTAL_CERTIDOES' in df_familias.columns else 0
    certidoes_entregues = df_familias['CERTIDOES_ENTREGUES'].sum() if 'CERTIDOES_ENTREGUES' in df_familias.columns else 0
    total_requerentes = df_familias['TOTAL_REQUERENTES'].sum() if 'TOTAL_REQUERENTES' in df_familias.columns else 0
    
    # Taxa de entrega global
    taxa_entrega = round((certidoes_entregues / max(1, total_certidoes) * 100), 1)
    
    # Layout de cards otimizados para TV vertical
    col1, col2 = st.columns(2, gap="large")
    
    # Card 1: Total de Famílias
    with col1:
        st.markdown(f"""
        <div class="metric-card-tv total" style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);">
            <div class="metric-title-tv">Total Famílias</div>
            <div class="metric-value-tv">{f"{total_familias:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">registradas</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 2: Média de Membros
    with col2:
        st.markdown(f"""
        <div class="metric-card-tv media" style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);">
            <div class="metric-title-tv">Média Membros</div>
            <div class="metric-value-tv">{f"{media_membros:.1f}".replace(".", ",")}</div>
            <div class="metric-subtitle-tv">por família</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 3: Taxa de Entrega
    with col1:
        st.markdown(f"""
        <div class="metric-card-tv taxa" style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);">
            <div class="metric-title-tv">Taxa Entrega</div>
            <div class="metric-value-tv">{taxa_entrega}%</div>
            <div class="metric-subtitle-tv">de certidões</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 4: Certidões Entregues
    with col2:
        st.markdown(f"""
        <div class="metric-card-tv media" style="background: linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%); border-color: #3F51B5;">
            <div class="metric-title-tv">Certidões</div>
            <div class="metric-value-tv">{f"{certidoes_entregues:,}/{f"{total_certidoes:,}"}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">entregues/total</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Card 5: Total de Requerentes
    with col1:
        st.markdown(f"""
        <div class="metric-card-tv requerentes" style="background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); border-color: #9C27B0;">
            <div class="metric-title-tv">Requerentes</div>
            <div class="metric-value-tv">{f"{total_requerentes:,}".replace(",", ".")}</div>
            <div class="metric-subtitle-tv">cadastrados</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Gráfico de barras por cartório
    if 'CARTORIO' in df_familias.columns:
        st.markdown("### Distribuição de Famílias por Cartório")
        
        # Contar famílias por cartório
        cartorio_counts = df_familias['CARTORIO'].value_counts().reset_index()
        cartorio_counts.columns = ['Cartório', 'Famílias']
        
        fig = px.bar(
            cartorio_counts,
            x='Cartório',
            y='Famílias',
            title="Famílias por Cartório",
            template="plotly_white",
            color='Famílias',
            color_continuous_scale=px.colors.sequential.Blues,
            height=500
        )
        
        fig.update_traces(
            texttemplate='%{y}',
            textposition='inside',
            textfont_size=16,
            marker_line_width=0
        )
        
        fig.update_layout(
            font=dict(size=14),
            xaxis_title="",
            yaxis_title="",
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=80, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=22)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def slide_cartorio_ids_familia(df):
    """
    Slide com análise de IDs de Família
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Análise de IDs de Família</h2>', unsafe_allow_html=True)
    
    # Usar dados do dataframe principal ou buscar na sessão
    if 'df_producao' in st.session_state and st.session_state['df_producao'] is not None and not st.session_state['df_producao'].empty:
        df = st.session_state['df_producao']
    
    if df is None or df.empty:
        st.warning("Não há dados disponíveis para análise de IDs de família.")
        return
    
    # Verificar campo de ID de família
    if 'UF_CRM_1722605592778' not in df.columns:
        st.warning("Campo de ID de família não encontrado nos dados.")
        return
    
    try:
        # Função para verificar o padrão do ID
        def check_id_pattern(id_str):
            # Verificar todos os tipos de valores vazios
            if pd.isna(id_str) or id_str == '' or id_str is None or (isinstance(id_str, str) and id_str.strip() == ''):
                return 'Vazio'
            if not isinstance(id_str, str):
                return 'Formato Inválido'
            # Remover espaços em branco
            id_str = id_str.strip()
            pattern = r'^\d+x\d+$'
            if re.match(pattern, id_str):
                return 'Padrão Correto'
            return 'Formato Inválido'
        
        # Analisar IDs
        df_analise = df.copy()
        df_analise['ID_STATUS'] = df_analise['UF_CRM_1722605592778'].apply(check_id_pattern)
        
        # Identificar duplicados
        validos_mask = (df_analise['ID_STATUS'] == 'Padrão Correto')
        ids_validos = df_analise.loc[validos_mask, 'UF_CRM_1722605592778'].str.strip()
        duplicados_mask = ids_validos.duplicated(keep=False)
        df_analise.loc[ids_validos[duplicados_mask].index, 'ID_STATUS'] = 'Duplicado'
        
        # Calcular resumo
        summary_counts = df_analise['ID_STATUS'].value_counts()
        
        # Criar DataFrame com os status e contagens
        summary = pd.DataFrame({
            'Status': ['Padrão Correto', 'Duplicado', 'Vazio', 'Formato Inválido'],
            'Quantidade': [
                summary_counts.get('Padrão Correto', 0),
                summary_counts.get('Duplicado', 0),
                summary_counts.get('Vazio', 0),
                summary_counts.get('Formato Inválido', 0)
            ]
        })
        
        # Calcular totais
        total_ids = summary['Quantidade'].sum()
        total_validos = summary.loc[summary['Status'] == 'Padrão Correto', 'Quantidade'].sum()
        
        # Layout de cards otimizados para TV vertical
        col1, col2 = st.columns(2, gap="large")
        
        # Card 1: Total de IDs
        with col1:
            st.markdown(f"""
            <div class="metric-card-tv total" style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);">
                <div class="metric-title-tv">Total IDs</div>
                <div class="metric-value-tv">{f"{total_ids:,}".replace(",", ".")}</div>
                <div class="metric-subtitle-tv">analisados</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Card 2: IDs Válidos
        with col2:
            # Calcular porcentagem
            pct_validos = round((total_validos / max(1, total_ids) * 100), 1)
            
            st.markdown(f"""
            <div class="metric-card-tv media" style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);">
                <div class="metric-title-tv">IDs Válidos</div>
                <div class="metric-value-tv">{f"{total_validos:,}".replace(",", ".")}</div>
                <div class="metric-subtitle-tv">{pct_validos}% do total</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Card 3: IDs Duplicados
        with col1:
            # Obter contagem de duplicados
            duplicados = summary.loc[summary['Status'] == 'Duplicado', 'Quantidade'].sum()
            pct_duplicados = round((duplicados / max(1, total_ids) * 100), 1)
            
            st.markdown(f"""
            <div class="metric-card-tv taxa" style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);">
                <div class="metric-title-tv">Duplicados</div>
                <div class="metric-value-tv">{f"{duplicados:,}".replace(",", ".")}</div>
                <div class="metric-subtitle-tv">{pct_duplicados}% do total</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Card 4: IDs Inválidos ou Vazios
        with col2:
            # Calcular inválidos + vazios
            invalidos = summary.loc[summary['Status'] == 'Formato Inválido', 'Quantidade'].sum()
            vazios = summary.loc[summary['Status'] == 'Vazio', 'Quantidade'].sum()
            total_problemas = invalidos + vazios
            pct_problemas = round((total_problemas / max(1, total_ids) * 100), 1)
            
            st.markdown(f"""
            <div class="metric-card-tv media" style="background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%); border-color: #F44336;">
                <div class="metric-title-tv">Problemas</div>
                <div class="metric-value-tv">{f"{total_problemas:,}".replace(",", ".")}</div>
                <div class="metric-subtitle-tv">{pct_problemas}% do total</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráfico de barras
        fig = px.bar(
            summary,
            x='Status',
            y='Quantidade',
            title="Distribuição por Status de ID",
            template="plotly_white",
            color='Status',
            color_discrete_map={
                'Padrão Correto': '#4CAF50',
                'Duplicado': '#FFC107',
                'Vazio': '#F44336',
                'Formato Inválido': '#FF5722'
            },
            height=500
        )
        
        fig.update_traces(
            texttemplate='%{y}',
            textposition='inside',
            textfont_size=16,
            marker_line_width=0
        )
        
        fig.update_layout(
            font=dict(size=14),
            xaxis_title="",
            yaxis_title="",
            showlegend=False,
            margin=dict(l=20, r=20, t=80, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=22)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    except Exception as e:
        st.error(f"Erro ao analisar IDs de família: {str(e)}")
