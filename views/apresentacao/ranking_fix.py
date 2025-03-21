import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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
        
        # Exibir informação sobre as metas
        st.markdown(f"""
        <div style="margin-bottom: 25px;">
            <div style="background-color: #ede7f6; border-radius: 15px; padding: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); text-align: center; border-left: 10px solid #9C27B0;">
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
        <div style="background-color: #f5f5f5; border-radius: 10px; padding: 10px; margin-top: 10px; text-align: center;">
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
