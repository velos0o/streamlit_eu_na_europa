import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from api.bitrix_connector import load_merged_data, get_higilizacao_fields
import os
from dotenv import load_dotenv

# Definir a função update_progress localmente para evitar problemas de importação
def update_progress(progress_bar, progress_value, message_container, message):
    """
    Atualiza a barra de progresso e mensagem durante o carregamento
    
    Args:
        progress_bar: Componente de barra de progresso do Streamlit
        progress_value: Valor de progresso entre 0 e 1
        message_container: Container para exibir mensagens de progresso
        message: Mensagem a ser exibida
    """
    # Atualizar a barra de progresso
    progress_bar.progress(progress_value)
    
    # Atualizar a mensagem
    message_container.info(message)

# Carregar variáveis de ambiente
load_dotenv()

def show_apresentacao_conclusoes(slide_inicial=0):
    """
    Exibe o modo de apresentação da página de conclusões,
    otimizado para telas verticais (9:16) como TVs.
    
    Args:
        slide_inicial (int): Índice do slide para iniciar a apresentação (0-11)
    """
    # ===================================================================
    # AVISO DE DEPRECIAÇÃO: Esta função será removida em versões futuras.
    # Use a função 'show_apresentacao' do módulo 'views.apresentacao' 
    # que é mais eficiente e otimizada.
    # ===================================================================
    import warnings
    warnings.warn(
        "DEPRECIADO: A função 'show_apresentacao_conclusoes' será removida em versões futuras. "
        "Use a nova função 'show_apresentacao' disponível em 'views.apresentacao'.",
        DeprecationWarning, stacklevel=2
    )
    
    print("DEPRECIADO: Use a nova função 'show_apresentacao'. Esta função será removida futuramente.")
    print(f"Iniciando apresentação com slide_inicial={slide_inicial}")
    
    # Verificar se há redirecionamento solicitado na sessão
    if 'slide_redirect' in st.session_state:
        slide_inicial = st.session_state['slide_redirect']
        print(f"Usando slide_redirect da sessão: {slide_inicial}")
        # Limpar para não influenciar futuras chamadas
        del st.session_state['slide_redirect'] 

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
    
    # Layout de cards otimizados para TV vertical - DESIGN ATUALIZADO
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
        <div class="metric-card-tv taxa" style="background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);">
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
        
        # Função para renderizar o card de cada responsável - DESIGN MELHORADO
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
                bg_gradient = 'linear-gradient(135deg, rgba(255, 215, 0, 0.2) 0%, rgba(255, 215, 0, 0.5) 100%)'
            elif posicao == 2:
                cor = '#C0C0C0'  # Prata para 2º lugar
                icone = '🥈'
                bg_gradient = 'linear-gradient(135deg, rgba(192, 192, 192, 0.2) 0%, rgba(192, 192, 192, 0.5) 100%)'
            elif posicao == 3:
                cor = '#CD7F32'  # Bronze para 3º lugar
                icone = '🥉'
                bg_gradient = 'linear-gradient(135deg, rgba(205, 127, 50, 0.2) 0%, rgba(205, 127, 50, 0.5) 100%)'
            else:
                cor = '#607D8B'  # Cinza para os demais
                icone = f"{posicao}º"
                bg_gradient = 'linear-gradient(135deg, rgba(96, 125, 139, 0.1) 0%, rgba(96, 125, 139, 0.3) 100%)'
            
            # Ícone para quem atingiu a meta
            meta_icon = "🎯" if atingiu_meta else ""
            
            # Aplicar estilo diferenciado para os 3 primeiros
            estilo_card = ""
            if destaque:
                estilo_card = "box-shadow: 0 6px 16px rgba(0,0,0,0.18);"
            
            # Estilo para o fundo baseado em atingir a meta
            fundo_meta = "linear-gradient(135deg, rgba(46, 125, 50, 0.1) 0%, rgba(200, 230, 201, 0.6) 100%)" if atingiu_meta else "white"
            
            if compacto:
                # Versão compacta para os não-destaques - DESIGN MELHORADO
                return f"""
                <div style="background: {bg_gradient}; border-radius: 8px; padding: 8px 8px; margin-bottom: 10px; 
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
                # Versão normal para os destaques - DESIGN MELHORADO
                return f"""
                <div style="background: {bg_gradient}; border-radius: 10px; padding: 10px 8px; margin-bottom: 15px; 
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
        
        # Layout para os destaques - DESIGN MELHORADO
        st.markdown('<div style="margin-bottom: 10px;"><h3 style="font-size: 1.3rem; color: #1A237E; text-align: center; background-color: #e8eaf6; padding: 8px; border-radius: 8px;">Top 3 Produtividade</h3></div>', unsafe_allow_html=True)
        
        # Mostrar os destaques em formato maior
        for resp in destaques:
            st.markdown(renderizar_card_responsavel(resp, compacto=False), unsafe_allow_html=True)
            
        # Layout para os demais em colunas compactas - DESIGN MELHORADO
        if outros:
            st.markdown('<div style="margin: 15px 0;"><h3 style="font-size: 1.3rem; color: #424242; text-align: center; background-color: #eeeeee; padding: 8px; border-radius: 8px;">Demais Colaboradores</h3></div>', unsafe_allow_html=True)
            
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
        
        # Adicionar legenda explicativa mais compacta - DESIGN MELHORADO
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
        
        # Criar gráfico melhorado para TV vertical
        fig = go.Figure()
        
        # Adicionar barras para conclusões diárias com design melhorado
        fig.add_trace(go.Bar(
            x=df_diario['DATA_CONCLUSAO'],
            y=df_diario['CONCLUSOES'],
            name='Conclusões',
            text=df_diario['CONCLUSOES'],
            textposition='auto',
            textfont=dict(size=16, color='white'),
            hovertemplate='%{x|%d/%m/%Y}<br>Conclusões: %{y}',
            marker=dict(
                color='rgba(25, 118, 210, 0.8)',
                line=dict(color='rgba(13, 71, 161, 1)', width=2)
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
            margin=dict(l=50, r=50, t=100, b=100), # Aumentar margem bottom para acomodar rótulos
            template='plotly_white',
            hovermode='x unified',
            bargap=0.3,  # Espaçar barras para melhor visualização
            plot_bgcolor='rgba(240, 240, 240, 0.8)',  # Cor de fundo mais suave
            paper_bgcolor='white'
        )
        
        # Melhorar a formatação das datas no eixo x
        fig.update_xaxes(
            tickformat='%d/%m',
            tickfont={'size': 14},
            tickangle=0,  # Zero graus para exibir datas na horizontal
            tickmode='array',
            tickvals=df_diario['DATA_CONCLUSAO'],
            ticktext=[d.strftime('%d/%m') for d in df_diario['DATA_CONCLUSAO']],
            gridcolor='rgba(200, 200, 200, 0.2)'
        )
        
        # Melhorar a formatação dos números no eixo y
        fig.update_yaxes(
            tickfont={'size': 14},
            gridcolor='rgba(200, 200, 200, 0.2)'
        )
        
        # Exibir o gráfico em um container com estilo melhorado
        st.markdown('<div class="chart-container-tv">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Métricas de destaque para análise diária - DESIGN MELHORADO
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
        
        # Métricas mais relevantes com design melhorado
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 15px; padding: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #1976D2; text-align: center; height: 100%;">
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
            <div style="background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%); border-radius: 15px; padding: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #FF9800; text-align: center; height: 100%;">
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
        
        # Adicionar informação sobre comparação entre maior e menor dia - NOVO ELEMENTO
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); border-radius: 15px; padding: 15px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-left: 10px solid #9C27B0; text-align: center; margin-top: 20px;">
            <div style="font-size: 1.4rem; font-weight: 700; color: #7B1FA2; margin-bottom: 10px;">
                Variação entre Menor e Maior Dia
            </div>
            <div style="display: flex; justify-content: space-around; align-items: center;">
                <div>
                    <div style="font-size: 1.2rem; color: #9C27B0; font-weight: 600;">Menor: {conclusoes_menos_produtivo}</div>
                    <div style="font-size: 1rem; color: #9C27B0;">em {data_menos_produtiva}</div>
                </div>
                <div style="font-size: 2rem; font-weight: 900; color: #4A148C;">
                    {conclusoes_mais_produtivo - conclusoes_menos_produtivo}
                </div>
                <div>
                    <div style="font-size: 1.2rem; color: #9C27B0; font-weight: 600;">Maior: {conclusoes_mais_produtivo}</div>
                    <div style="font-size: 1rem; color: #9C27B0;">em {data_mais_produtiva}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao gerar análise diária: {str(e)}")
        import traceback
        st.error(traceback.format_exc()) 

def iniciar_carrossel_metricas(df, df_todos, date_from, date_to, tempo_por_slide=15, slide_inicial=0):
    """
    Inicia o carrossel de métricas, exibindo cada uma por um tempo determinado
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados de conclusões
        df_todos (pandas.DataFrame): DataFrame com todos os dados (incluindo não concluídos)
        date_from (datetime): Data inicial do período analisado
        date_to (datetime): Data final do período analisado
        tempo_por_slide (int): Tempo em segundos para exibição de cada slide
        slide_inicial (int): Índice do slide para iniciar a apresentação (0-11)
    """
    # Log para depuração
    print("=" * 50)
    print(f"INICIANDO CARROSSEL - Slide inicial: {slide_inicial}")
    print(f"Total slides: 12 | Tempo por slide: {tempo_por_slide}s")
    print(f"Dados de produção na sessão: {'Sim' if 'df_producao' in st.session_state else 'Não'}")
    print(f"Dados de cartório na sessão: {'Sim' if 'df_cartorio' in st.session_state else 'Não'}")
    print("=" * 50)
    
    # Nomes dos slides para exibição no contador
    nomes_slides = [
        "Métricas de Destaque",
        "Ranking de Produtividade",
        "Análise Diária",
        "Análise Semanal",
        "Análise por Dia da Semana",
        "Análise por Hora",
        # Slides do módulo de produção
        "Produção - Métricas Macro",
        "Produção - Status por Responsável",
        "Produção - Pendências por Responsável",
        # Slides do módulo de cartório
        "Cartório - Visão Geral",
        "Cartório - Análise de Famílias",
        "Cartório - IDs de Família"
    ]
    
    # Número total de slides
    total_slides = len(nomes_slides)
    
    # Controle de atualização de dados (a cada 1 minuto)
    ultima_atualizacao = datetime.now()
    
    # ===== PRÉ-CARREGAMENTO FORÇADO DE TODOS OS DADOS NECESSÁRIOS =====
    # Garantir que os dados estejam pré-carregados antes de iniciar a apresentação
    
    st.toast("Preparando apresentação automática...", icon="🔄")
    
    # 1. Garantir que dados de produção estejam disponíveis
    if 'df_producao' not in st.session_state or st.session_state['df_producao'] is None or st.session_state['df_producao'].empty:
        print("Dados de produção não encontrados. Carregando dados de demonstração...")
        with st.spinner("Carregando dados de produção..."):
            try:
                # Tentar carregar dados reais primeiro
                date_from_str = date_from.strftime("%Y-%m-%d") if isinstance(date_from, datetime) else date_from
                date_to_str = date_to.strftime("%Y-%m-%d") if isinstance(date_to, datetime) else date_to
                
                from api.bitrix_connector import load_merged_data
                df_producao = load_merged_data(category_id=32, date_from=date_from_str, date_to=date_to_str)
                
                if df_producao is None or df_producao.empty:
                    # Se dados reais não funcionarem, usar dados de demonstração
                    from views.producao import generate_demo_data
                    df_producao = generate_demo_data()
                
                st.session_state['df_producao'] = df_producao
                print(f"Dados de produção carregados: {len(df_producao)} registros")
                st.toast("Dados de produção carregados com sucesso", icon="✅")
            except Exception as e:
                import traceback
                print(f"Erro ao carregar dados de produção: {str(e)}")
                print(traceback.format_exc())
                
                # Último recurso - criar um DataFrame vazio com colunas esperadas
                try:
                    from views.producao import generate_demo_data
                    df_producao = generate_demo_data()
                    st.session_state['df_producao'] = df_producao
                    st.toast("Usando dados de demonstração após erro", icon="⚠️")
                except:
                    # Criar mínimo viável para não quebrar a apresentação
                    df_producao = pd.DataFrame({
                        'ASSIGNED_BY_NAME': ['Demo'],
                        'UF_CRM_HIGILIZACAO_STATUS': ['COMPLETO']
                    })
                    st.session_state['df_producao'] = df_producao
                    st.toast("Usando dados mínimos para apresentação", icon="⚠️")
    else:
        print(f"Dados de produção já disponíveis: {len(st.session_state['df_producao'])} registros")
    
    # 2. Garantir que dados de cartório estejam disponíveis
    if 'df_cartorio' not in st.session_state or st.session_state['df_cartorio'] is None or st.session_state['df_cartorio'].empty:
        print("Dados de cartório não encontrados. Carregando...")
        with st.spinner("Carregando dados de cartório..."):
            try:
                # Carregar dados do cartório
                from views.cartorio.data_loader import load_data
                df_cartorio = load_data()
                
                if df_cartorio is not None and not df_cartorio.empty:
                    # Filtrar para os cartórios padrão
                    cartorio_filter = ["CARTÓRIO CASA VERDE", "CARTÓRIO TATUÁPE"]
                    df_cartorio = df_cartorio[df_cartorio['NOME_CARTORIO'].isin(cartorio_filter)]
                    
                    # Armazenar na sessão
                    st.session_state['df_cartorio'] = df_cartorio
                    print(f"Dados de cartório armazenados na sessão: {len(df_cartorio)} registros")
                    st.toast("Dados de cartório carregados com sucesso", icon="✅")
                else:
                    print("ALERTA: Dados de cartório vazios após carregamento")
                    st.toast("Dados de cartório estão vazios", icon="⚠️")
                    # Criar um dataframe básico para evitar erros
                    df_cartorio = pd.DataFrame({
                        'NOME_CARTORIO': ['CARTÓRIO CASA VERDE', 'CARTÓRIO TATUÁPE'],
                        'ID': list(range(10)),
                        'STAGE_ID': ['PENDING'] * 10
                    })
                    st.session_state['df_cartorio'] = df_cartorio
            except Exception as e:
                import traceback
                print(f"Erro geral ao carregar dados de cartório: {str(e)}")
                print(traceback.format_exc())
                st.toast("Falha ao carregar dados de cartório", icon="❌")
                
                # Criar um dataframe básico para evitar erros
                df_cartorio = pd.DataFrame({
                    'NOME_CARTORIO': ['CARTÓRIO CASA VERDE', 'CARTÓRIO TATUÁPE'],
                    'ID': list(range(10)),
                    'STAGE_ID': ['PENDING'] * 10
                })
                st.session_state['df_cartorio'] = df_cartorio
    else:
        print(f"Dados de cartório já disponíveis: {len(st.session_state['df_cartorio'])} registros")
    
    # 3. Garantir que dados de famílias estejam disponíveis
    if 'df_familias' not in st.session_state or st.session_state['df_familias'] is None or st.session_state['df_familias'].empty:
        print("Dados de famílias não encontrados. Carregando...")
        try:
            from views.cartorio.analysis import analisar_familia_certidoes
            df_familias = analisar_familia_certidoes()
            if df_familias is not None and not df_familias.empty:
                st.session_state['df_familias'] = df_familias
                print(f"Dados de famílias carregados: {len(df_familias)} registros")
                st.toast("Dados de famílias carregados com sucesso", icon="✅")
            else:
                print("ALERTA: Dados de famílias vazios após carregamento")
                st.toast("Dados de famílias estão vazios", icon="⚠️")
                # Criar um dataframe básico para evitar erros
                df_familias = pd.DataFrame({
                    'ID_FAMILIA': list(range(10)),
                    'CARTORIO': ['CARTÓRIO CASA VERDE', 'CARTÓRIO TATUÁPE'] * 5,
                    'TOTAL_CERTIDOES': [10] * 10,
                    'CERTIDOES_ENTREGUES': [5] * 10,
                    'STATUS_HIGILIZACAO': ['PENDENTE'] * 10
                })
                st.session_state['df_familias'] = df_familias
        except Exception as e:
            import traceback
            print(f"Erro ao carregar dados de famílias: {str(e)}")
            print(traceback.format_exc())
            st.toast("Falha ao carregar dados de famílias", icon="❌")
            
            # Criar um dataframe básico para evitar erros
            df_familias = pd.DataFrame({
                'ID_FAMILIA': list(range(10)),
                'CARTORIO': ['CARTÓRIO CASA VERDE', 'CARTÓRIO TATUÁPE'] * 5,
                'TOTAL_CERTIDOES': [10] * 10,
                'CERTIDOES_ENTREGUES': [5] * 10,
                'STATUS_HIGILIZACAO': ['PENDENTE'] * 10
            })
            st.session_state['df_familias'] = df_familias
    
    # Confirmar que podemos prosseguir com a apresentação
    st.toast("Iniciando apresentação automática", icon="▶️")
    
    # Loop infinito para apresentação contínua
    slide_atual = slide_inicial
    
    # Variável para garantir que o carrossel continue mesmo se houver erros
    continuar_apresentacao = True
    
    # Adicionar CSS para melhorar a animação e transição entre slides
    st.markdown("""
    <style>
    .slide-transition {
        animation: fadeIn 0.8s ease-in-out;
    }
    
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    .navigation-controls {
        position: fixed;
        bottom: 80px;
        left: 20px;
        background: linear-gradient(135deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.9) 100%);
        padding: 10px;
        border-radius: 8px;
        z-index: 1000;
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    .nav-button {
        cursor: pointer;
        background: rgba(255,255,255,0.2);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        text-align: center;
        margin: 5px 3px;
        transition: all 0.3s ease;
    }
    
    .nav-button:hover {
        background: rgba(255,255,255,0.3);
        transform: translateY(-2px);
    }
    
    .slide-indicators {
        position: fixed;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 1000;
        display: flex;
        gap: 5px;
    }
    
    .indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    
    .indicator.active {
        background: linear-gradient(135deg, #3949AB 0%, #1A237E 100%);
        border: 2px solid white;
    }
    
    .indicator:not(.active) {
        background: rgba(255,255,255,0.3);
        border: 2px solid rgba(255,255,255,0.5);
    }
    
    .module-header {
        background: linear-gradient(90deg, #1976D2 0%, #42A5F5 100%);
        padding: 5px 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .module-header h3 {
        color: white;
        margin: 0;
        text-align: center;
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    .module-header.producao {
        background: linear-gradient(90deg, #1976D2 0%, #42A5F5 100%);
    }
    
    .module-header.cartorio {
        background: linear-gradient(90deg, #7B1FA2 0%, #9C27B0 100%);
    }
    
    .config-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
        border-radius: 50%;
        text-align: center;
        line-height: 40px;
        color: white;
        text-decoration: none;
        font-size: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    
    .config-button:hover {
        transform: rotate(30deg);
        box-shadow: 0 6px 12px rgba(0,0,0,0.4);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Adicionar controles de navegação (sempre visível)
    st.markdown("""
    <div class="navigation-controls">
        <p style="margin: 0; font-size: 0.9rem;">Pressione ESC para sair</p>
        <div style="display: flex; gap: 10px; margin-top: 5px;">
            <a href="?slide=0" class="nav-button">Conclusões</a>
            <a href="?slide=6" class="nav-button">Produção</a>
            <a href="?slide=9" class="nav-button">Cartório</a>
        </div>
    </div>
    
    <a href="?config=1" class="config-button">⚙️</a>
    """, unsafe_allow_html=True)
    
    while continuar_apresentacao:
        try:
            # Verificar se é hora de atualizar os dados (a cada 1 minuto)
            agora = datetime.now()
            if (agora - ultima_atualizacao).total_seconds() >= 60:  # 60 segundos = 1 minuto
                st.rerun()  # Força o recarregamento da aplicação
            
            # Gerar indicadores de slide
            indicators_html = '<div class="slide-indicators">'
            for i in range(total_slides):
                active_class = "active" if i == slide_atual else ""
                indicators_html += f'<a href="?slide={i}" class="indicator {active_class}"></a>'
            indicators_html += '</div>'
            
            # Mostrar indicadores
            indicators_container = st.empty()
            indicators_container.markdown(indicators_html, unsafe_allow_html=True)
            
            # Criar containers principais
            main_area = st.empty()
            progress_container = st.empty()
            
            # Preparar o slide
            print(f"Preparando slide {slide_atual+1}/{total_slides}: {nomes_slides[slide_atual]}")
            
            # Criar container para o slide atual com animação de transição
            with main_area.container():
                st.markdown('<div class="slide-transition">', unsafe_allow_html=True)
                
                try:
                    # Adicionar cabeçalho de módulo quando necessário
                    if slide_atual >= 6 and slide_atual <= 8:
                        # Slides de produção
                        st.markdown('<div class="module-header producao"><h3>➡️ MÓDULO DE PRODUÇÃO</h3></div>', unsafe_allow_html=True)
                    elif slide_atual >= 9:
                        # Slides de cartório
                        st.markdown('<div class="module-header cartorio"><h3>➡️ MÓDULO DE CARTÓRIO</h3></div>', unsafe_allow_html=True)
                    
                    # Chamar a função correspondente ao slide atual
                    if slide_atual == 0:
                        slide_metricas_destaque(df, df_todos, date_from, date_to)
                    elif slide_atual == 1:
                        slide_ranking_produtividade(df, df_todos)
                    elif slide_atual == 2:
                        slide_analise_diaria(df, date_from, date_to)
                    elif slide_atual == 3:
                        slide_analise_semanal(df)
                    elif slide_atual == 4:
                        slide_analise_dia_semana(df)
                    elif slide_atual == 5:
                        slide_analise_horario(df)
                    # Slides de produção
                    elif slide_atual == 6:
                        if 'df_producao' in st.session_state and st.session_state['df_producao'] is not None and not st.session_state['df_producao'].empty:
                            slide_producao_metricas_macro(df)
                        else:
                            st.error("Dados de produção não disponíveis")
                            # Tentar carregar dados de demonstração
                            from views.producao import generate_demo_data
                            df_producao = generate_demo_data()
                            st.session_state['df_producao'] = df_producao
                            st.success(f"Carregados {len(df_producao)} registros de demonstração")
                            slide_producao_metricas_macro(df)
                    elif slide_atual == 7:
                        if 'df_producao' in st.session_state and st.session_state['df_producao'] is not None and not st.session_state['df_producao'].empty:
                            slide_producao_status_responsavel(df)
                        else:
                            st.error("Dados de produção não disponíveis")
                            # Tentar carregar dados de demonstração
                            from views.producao import generate_demo_data
                            df_producao = generate_demo_data()
                            st.session_state['df_producao'] = df_producao
                            st.success(f"Carregados {len(df_producao)} registros de demonstração")
                            slide_producao_status_responsavel(df)
                    elif slide_atual == 8:
                        if 'df_producao' in st.session_state and st.session_state['df_producao'] is not None and not st.session_state['df_producao'].empty:
                            slide_producao_pendencias_responsavel(df)
                        else:
                            st.error("Dados de produção não disponíveis")
                            # Tentar carregar dados de demonstração
                            from views.producao import generate_demo_data
                            df_producao = generate_demo_data()
                            st.session_state['df_producao'] = df_producao
                            st.success(f"Carregados {len(df_producao)} registros de demonstração")
                            slide_producao_pendencias_responsavel(df)
                    # Slides de cartório
                    elif slide_atual == 9:
                        if 'df_cartorio' in st.session_state and st.session_state['df_cartorio'] is not None and not st.session_state['df_cartorio'].empty:
                            slide_cartorio_visao_geral(df)
                        else:
                            st.error("Dados de cartório não disponíveis")
                            st.warning("Tentando continuar com a apresentação...")
                    elif slide_atual == 10:
                        if 'df_cartorio' in st.session_state and st.session_state['df_cartorio'] is not None and not st.session_state['df_cartorio'].empty:
                            slide_cartorio_analise_familias(df)
                        else:
                            st.error("Dados de cartório não disponíveis")
                            st.warning("Tentando continuar com a apresentação...")
                    elif slide_atual == 11:
                        if 'df_cartorio' in st.session_state and st.session_state['df_cartorio'] is not None and not st.session_state['df_cartorio'].empty:
                            slide_cartorio_ids_familia(df)
                        else:
                            st.error("Dados de cartório não disponíveis")
                            st.warning("Tentando continuar com a apresentação...")
                
                except Exception as e:
                    import traceback
                    st.error(f"Erro ao exibir slide {slide_atual+1}: {str(e)}")
                    st.code(traceback.format_exc())
                    print(f"Erro ao exibir slide {slide_atual+1}: {str(e)}")
                    print(traceback.format_exc())
                
                st.markdown('</div>', unsafe_allow_html=True)  # Fechando div de animação
                
                # Exibir contador de slides e informação de atualização
                st.markdown(f"""
                <div class="slide-counter">
                    {slide_atual + 1}/{total_slides} - {nomes_slides[slide_atual]}
                </div>
                <div class="slide-info">
                    <span class="updated-at">Atualizado às {datetime.now().strftime('%H:%M')}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Atualizar barra de progresso com design melhorado
            for i in range(tempo_por_slide * 10):
                progress_percent = (i + 1) / (tempo_por_slide * 10)
                progress_container.markdown(f"""
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {progress_percent * 100}%;">
                        <span style="position: absolute; left: 10px; font-size: 10px; color: white; mix-blend-mode: difference;">
                            {int(progress_percent * 100)}%
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.1)
            
            # Avançar para o próximo slide
            print(f"Avançando do slide {slide_atual} para {(slide_atual + 1) % total_slides}")
            slide_atual = (slide_atual + 1) % total_slides
            
            # Limpar containers
            main_area.empty()
            progress_container.empty()
            indicators_container.empty()
        
        except Exception as e:
            import traceback
            print(f"Erro crítico na apresentação: {str(e)}")
            print(traceback.format_exc())
            
            # Tentar continuar com o próximo slide
            slide_atual = (slide_atual + 1) % total_slides
            time.sleep(2)  # Pausa para não entrar em loop infinito de erros