import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def slide_producao_metricas_macro():
    """
    Slide com métricas macro da produção, otimizado para tela 9:16
    Apresenta uma visão geral da distribuição dos status de produção
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Produção - Métricas Macro</h2>', unsafe_allow_html=True)
    
    try:
        # Carregar dados de produção (carregados em show_apresentacao_conclusoes)
        df_producao = st.session_state.get('df_producao', None)
        
        if df_producao is None or df_producao.empty:
            st.warning("Não há dados de produção disponíveis.")
            return
        
        # Calcular métricas
        total_registros = len(df_producao)
        
        # Status de higienização
        df_producao['UF_CRM_HIGILIZACAO_STATUS'] = df_producao['UF_CRM_HIGILIZACAO_STATUS'].fillna('PENDENCIA')
        status_counts = df_producao['UF_CRM_HIGILIZACAO_STATUS'].value_counts()
        
        completos = status_counts.get('COMPLETO', 0)
        incompletos = status_counts.get('INCOMPLETO', 0)
        pendentes = status_counts.get('PENDENCIA', 0)
        
        # Calcular porcentagens
        pct_completos = round((completos / total_registros) * 100, 1) if total_registros > 0 else 0
        pct_incompletos = round((incompletos / total_registros) * 100, 1) if total_registros > 0 else 0
        pct_pendentes = round((pendentes / total_registros) * 100, 1) if total_registros > 0 else 0
        
        # Layout de cards otimizados para TV vertical
        col1, col2 = st.columns(2, gap="large")
        
        # Card 1: Total de Registros
        with col1:
            st.markdown(f"""
            <div class="metric-card-tv total">
                <div class="metric-title-tv">Total de Registros</div>
                <div class="metric-value-tv">{total_registros:,}</div>
                <div class="metric-subtitle-tv">processos cadastrados</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)
        
        # Card 2: Completos
        with col2:
            st.markdown(f"""
            <div class="metric-card-tv" style="border-color: #4CAF50;">
                <div class="metric-title-tv" style="color: #4CAF50;">Completos</div>
                <div class="metric-value-tv" style="color: #4CAF50;">{completos:,}</div>
                <div class="metric-subtitle-tv">({pct_completos}% do total)</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)
        
        # Card 3: Incompletos
        with col1:
            st.markdown(f"""
            <div class="metric-card-tv" style="border-color: #FFA000;">
                <div class="metric-title-tv" style="color: #FFA000;">Incompletos</div>
                <div class="metric-value-tv" style="color: #FFA000;">{incompletos:,}</div>
                <div class="metric-subtitle-tv">({pct_incompletos}% do total)</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)
        
        # Card 4: Pendentes
        with col2:
            st.markdown(f"""
            <div class="metric-card-tv" style="border-color: #F44336;">
                <div class="metric-title-tv" style="color: #F44336;">Pendentes</div>
                <div class="metric-value-tv" style="color: #F44336;">{pendentes:,}</div>
                <div class="metric-subtitle-tv">({pct_pendentes}% do total)</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)
        
        # Gráfico de pizza para status com legenda e números mais claros
        status_df = pd.DataFrame({
            'Status': ['COMPLETO', 'INCOMPLETO', 'PENDENCIA'],
            'Valor': [completos, incompletos, pendentes],
            'Percentual': [pct_completos, pct_incompletos, pct_pendentes]
        })
        
        # Ordenar por status mais comum para menos comum
        status_df = status_df.sort_values('Valor', ascending=False)
        
        cores_status = {
            'COMPLETO': '#4CAF50',
            'INCOMPLETO': '#FFA000',
            'PENDENCIA': '#F44336'
        }
        
        fig = px.pie(
            status_df, 
            names='Status',
            values='Valor',
            title='Distribuição por Status',
            color='Status',
            color_discrete_map=cores_status,
            hole=0.4
        )
        
        # Adicionar anotações personalizadas para maior clareza
        anotacoes = []
        for i, row in status_df.iterrows():
            status = row['Status']
            valor = row['Valor']
            percentual = row['Percentual']
            
            if status == 'COMPLETO':
                anotacoes.append(dict(
                    text=f"<b>COMPLETOS</b><br>{valor:,}<br>({percentual}%)".replace(",", "."),
                    x=0.5, y=0.85,
                    font=dict(size=16, color='#4CAF50'),
                    showarrow=False
                ))
            elif status == 'INCOMPLETO':
                anotacoes.append(dict(
                    text=f"<b>INCOMPLETOS</b><br>{valor:,}<br>({percentual}%)".replace(",", "."),
                    x=0.2, y=0.2,
                    font=dict(size=16, color='#FFA000'),
                    showarrow=False
                ))
            elif status == 'PENDENCIA':
                anotacoes.append(dict(
                    text=f"<b>PENDENTES</b><br>{valor:,}<br>({percentual}%)".replace(",", "."),
                    x=0.8, y=0.2,
                    font=dict(size=16, color='#F44336'),
                    showarrow=False
                ))
        
        # Configurar aparência
        fig.update_layout(
            title={
                'text': "Status de Higienização",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24, 'color': '#1A237E', 'family': 'Arial, Helvetica, sans-serif'}
            },
            height=450, # Aumentar altura para melhor visibilidade
            margin=dict(l=20, r=20, t=80, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=18)
            ),
            annotations=anotacoes
        )
        
        # Adicionar informação sobre quantidade e porcentagem
        fig.update_traces(
            textposition='inside',
            textinfo='percent',
            textfont_size=18,
            marker=dict(line=dict(color='#FFFFFF', width=2)),
            hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Porcentagem: %{percent:.1%}"
        )
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Adicionar informações extras se houver espaço
        st.markdown("""
        <div class="info-text">
          <strong>📊 Métricas de Produção:</strong><br>
          • <span style="color: #4CAF50; font-weight: bold;">Completos</span>: Processos com higienização finalizada<br>
          • <span style="color: #FFA000; font-weight: bold;">Incompletos</span>: Processos com higienização parcial<br>
          • <span style="color: #F44336; font-weight: bold;">Pendentes</span>: Processos aguardando higienização
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Erro ao gerar métricas macro de produção: {str(e)}")
        import traceback
        st.error(traceback.format_exc()) 