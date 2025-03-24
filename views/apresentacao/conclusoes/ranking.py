import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def slide_ranking_produtividade(df, df_todos):
    """
    Exibe um ranking de produtividade dos responsáveis com visual aprimorado
    Versão avançada baseada no módulo conclusoes.py
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados concluídos
        df_todos (pandas.DataFrame): DataFrame com todos os dados (incluindo não concluídos)
    """
    try:
        # Forçar limpeza de elementos persistentes
        st.empty()
        
        st.markdown('<h2 class="slide-title">Ranking de Produtividade</h2>', unsafe_allow_html=True)
        
        # Verificar se a coluna de responsáveis existe em df_todos
        if 'ASSIGNED_BY_NAME' not in df_todos.columns:
            st.error("Não foi possível gerar o ranking: coluna de responsáveis não encontrada.")
            return
        
        # Agrupar por responsável e contar o número de conclusões para os que concluíram
        if not df.empty and 'ASSIGNED_BY_NAME' in df.columns:
            ranking_conclusoes = df.groupby('ASSIGNED_BY_NAME').size().reset_index(name='TOTAL_CONCLUSOES')
        else:
            # Se não há conclusões, criar DataFrame vazio com as colunas necessárias
            ranking_conclusoes = pd.DataFrame(columns=['ASSIGNED_BY_NAME', 'TOTAL_CONCLUSOES'])
        
        # Calcular a taxa de conclusão por responsável
        total_por_responsavel = df_todos.groupby('ASSIGNED_BY_NAME').size().reset_index(name='TOTAL_ATRIBUIDOS')
        
        # Fazer merge outer para incluir todos os responsáveis, mesmo os que não tiveram conclusões
        ranking = pd.merge(total_por_responsavel, ranking_conclusoes, on='ASSIGNED_BY_NAME', how='left')
        
        # Preencher valores NaN de conclusões com 0
        ranking['TOTAL_CONCLUSOES'] = ranking['TOTAL_CONCLUSOES'].fillna(0)
        
        # Converter para inteiro
        ranking['TOTAL_CONCLUSOES'] = ranking['TOTAL_CONCLUSOES'].astype(int)
        
        # Calcular pendentes
        ranking['PENDENTES'] = ranking['TOTAL_ATRIBUIDOS'] - ranking['TOTAL_CONCLUSOES']
        
        # Calcular taxa de conclusão
        ranking['TAXA_CONCLUSAO'] = (ranking['TOTAL_CONCLUSOES'] / ranking['TOTAL_ATRIBUIDOS'] * 100).round(1)
        
        # Calcular dias trabalhados (dias em que cada responsável teve pelo menos uma conclusão)
        if not df.empty and 'DATA_CONCLUSAO' in df.columns:
            # Criar colunas auxiliares
            df_temp = df.copy()
            df_temp['DATA'] = df_temp['DATA_CONCLUSAO'].dt.date
            df_temp['DIA_SEMANA'] = df_temp['DATA_CONCLUSAO'].dt.weekday
            
            # Lista para armazenar os dados de dias trabalhados com primeira conclusão
            dados_dias_trabalhados = []
            
            # Para cada responsável, calcular dias úteis a partir da primeira conclusão
            for responsavel in df_temp['ASSIGNED_BY_NAME'].unique():
                # Filtrar dados do responsável
                df_resp = df_temp[df_temp['ASSIGNED_BY_NAME'] == responsavel]
                
                # Encontrar data da primeira conclusão
                primeira_conclusao = df_resp['DATA'].min()
                
                # Encontrar data da última conclusão
                ultima_conclusao = df_resp['DATA'].max()
                
                # Calcular dias úteis entre a primeira e a última conclusão
                dias_uteis = 0
                data_atual = datetime.combine(primeira_conclusao, datetime.min.time())
                
                while data_atual.date() <= ultima_conclusao:
                    dia_semana = data_atual.weekday()
                    if dia_semana <= 5:  # Segunda a sábado
                        dias_uteis += 1
                    data_atual += timedelta(days=1)
                
                # Dias em que o responsável realmente trabalhou (com conclusões)
                dias_com_conclusao = df_resp['DATA'].nunique()
                
                # Adicionar à lista de dados
                dados_dias_trabalhados.append({
                    'ASSIGNED_BY_NAME': responsavel,
                    'PRIMEIRA_CONCLUSAO': primeira_conclusao,
                    'ULTIMA_CONCLUSAO': ultima_conclusao,
                    'DIAS_UTEIS_PERIODO': dias_uteis,
                    'DIAS_COM_CONCLUSAO': dias_com_conclusao
                })
            
            # Converter para DataFrame
            df_dias = pd.DataFrame(dados_dias_trabalhados)
            
            # Mesclar com o ranking
            if not df_dias.empty:
                ranking = pd.merge(ranking, df_dias, on='ASSIGNED_BY_NAME', how='left')
                
                # Usar os dias úteis do período como dias trabalhados
                ranking['DIAS_TRABALHADOS'] = ranking['DIAS_UTEIS_PERIODO']
            else:
                ranking['DIAS_TRABALHADOS'] = 0
        else:
            ranking['DIAS_TRABALHADOS'] = 0
        
        # Preencher NaN em dias trabalhados com 0
        ranking['DIAS_TRABALHADOS'] = ranking['DIAS_TRABALHADOS'].fillna(0)
        
        # Calcular média diária (evitando divisão por zero)
        ranking['MEDIA_DIARIA'] = 0.0  # Valor padrão
        mask = ranking['DIAS_TRABALHADOS'] > 0
        ranking.loc[mask, 'MEDIA_DIARIA'] = (ranking.loc[mask, 'TOTAL_CONCLUSOES'] / ranking.loc[mask, 'DIAS_TRABALHADOS']).round(2)
        
        # Determinar o melhor valor para destaque (maior média diária)
        if not ranking.empty and 'MEDIA_DIARIA' in ranking.columns:
            melhor_media = ranking['MEDIA_DIARIA'].max()
            
            # Criar coluna de status para destacar
            ranking['STATUS'] = ''
            ranking.loc[ranking['MEDIA_DIARIA'] == melhor_media, 'STATUS'] = '🏆'
        
        # Ordenar pelo total de conclusões em ordem decrescente
        ranking = ranking.sort_values('TOTAL_CONCLUSOES', ascending=False).reset_index(drop=True)
        
        # Adicionar coluna de posição
        ranking.insert(0, 'POSICAO', ranking.index + 1)
        
        # Função para renderizar o card de cada responsável
        def renderizar_card_responsavel(resp, compacto=False):
            posicao = resp['POSICAO']
            nome = resp['ASSIGNED_BY_NAME']
            total = resp['TOTAL_CONCLUSOES']
            pendentes = resp['PENDENTES']
            taxa = resp['TAXA_CONCLUSAO']
            media_diaria = resp['MEDIA_DIARIA']
            dias_uteis = resp['DIAS_TRABALHADOS']
            status = resp['STATUS']
            destaque = posicao <= 3  # Top 3 = destaque especial
            
            # Calcular meta baseada na média global
            media_global = df.groupby('DATA_CONCLUSAO').size().mean() if 'DATA_CONCLUSAO' in df.columns else 0
            meta_diaria = round(media_global, 1)  # Meta = 100% da média global diária
            
            # Verificar se atingiu a meta
            atingiu_meta = media_diaria >= meta_diaria
            
            # Ícone para quem atingiu a meta
            meta_icon = "🎯" if atingiu_meta else ""
            status_icon = status  # Já tem 🏆 se for o melhor
            
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
            
            # Estilo para o fundo baseado em atingir a meta
            fundo_meta = "linear-gradient(135deg, rgba(46, 125, 50, 0.1) 0%, rgba(200, 230, 201, 0.6) 100%)" if atingiu_meta else "white"
            
            if compacto:
                # Versão compacta para os não-destaques
                return f"""
                <div style="background: {fundo_meta}; border-radius: 8px; padding: 10px; margin-bottom: 10px; 
                        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); position: relative; border-left: 5px solid {cor};">
                    <div style="position: absolute; top: 5px; right: 5px; font-size: 1.2rem;">{icone} {meta_icon} {status_icon}</div>
                    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; color: #1A237E; 
                            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 40px;">{nome}</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.8rem; color: #666;">Concl.</div>
                            <div style="font-size: 1.2rem; font-weight: 900; color: #2E7D32;">{total}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.8rem; color: #666;">Média</div>
                            <div style="font-size: 1.2rem; font-weight: 900; color: #1565C0;">{f"{media_diaria:.1f}".replace(".", ",")}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.8rem; color: #666;">Taxa</div>
                            <div style="font-size: 1.2rem; font-weight: 900; color: #FF9800;">{taxa}%</div>
                        </div>
                    </div>
                    <div style="font-size: 0.7rem; color: #757575; text-align: right;">
                        {int(dias_uteis)} dias úteis
                    </div>
                </div>
                """
            else:
                # Versão normal para os destaques
                return f"""
                <div style="background: {fundo_meta}; border-radius: 10px; padding: 15px; margin-bottom: 15px; 
                        box-shadow: 0 4px 10px rgba(0,0,0,0.15); position: relative; border-left: 8px solid {cor};">
                    <div style="position: absolute; top: 10px; right: 10px; font-size: 1.5rem;">{icone} {meta_icon} {status_icon}</div>
                    <div style="font-size: 1.3rem; font-weight: 800; margin-bottom: 10px; color: #1A237E; 
                            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 45px;">{nome}</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.9rem; color: #666;">Conclusões</div>
                            <div style="font-size: 1.5rem; font-weight: 900; color: #2E7D32;">{total}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.9rem; color: #666;">Média/dia</div>
                            <div style="font-size: 1.5rem; font-weight: 900; color: #1565C0;">{f"{media_diaria:.1f}".replace(".", ",")}</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 0.9rem; color: #666;">Taxa</div>
                            <div style="font-size: 1.5rem; font-weight: 900; color: #FF9800;">{taxa}%</div>
                        </div>
                    </div>
                    <div style="font-size: 0.8rem; color: #757575; text-align: right; margin-top: 5px;">
                        {int(dias_uteis)} dias úteis | {int(pendentes)} pendentes
                    </div>
                </div>
                """
            
        # Separar entre destaques (top 3) e demais
        destaques = ranking.head(3).to_dict('records')
        outros = ranking.iloc[3:].to_dict('records')
        
        # Layout para os destaques
        st.markdown('<div style="margin-bottom: 15px;"><h3 style="font-size: 1.4rem; color: #1A237E; text-align: center;">Top 3 Produtividade</h3></div>', unsafe_allow_html=True)
        
        # Mostrar os destaques em formato maior
        for resp in destaques:
            st.markdown(renderizar_card_responsavel(resp, compacto=False), unsafe_allow_html=True)
            
        # Layout para os demais em colunas compactas
        if outros:
            st.markdown('<div style="margin: 25px 0 15px 0;"><h3 style="font-size: 1.3rem; color: #424242; text-align: center;">Demais Colaboradores</h3></div>', unsafe_allow_html=True)
            
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
        <div style="background-color: #f5f5f5; border-radius: 10px; padding: 10px; margin-top: 15px; text-align: center;">
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
                    <span style="font-size: 1.3rem; margin-right: 5px;">🏆</span>
                    <span style="font-size: 0.9rem; color: #455A64;">Melhor média</span>
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