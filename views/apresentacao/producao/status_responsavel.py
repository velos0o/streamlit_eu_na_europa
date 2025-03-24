import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import plotly.express as px

def slide_producao_status_responsavel():
    """
    Slide com status por responsável, otimizado para telas 9:16
    """
    # Forçar limpeza de elementos persistentes
    st.empty()
    
    st.markdown('<h2 class="slide-title">Produção - Status por Responsável</h2>', unsafe_allow_html=True)
    
    try:
        # Carregar dados de produção (deve estar na sessão)
        df_producao = st.session_state.get('df_producao', None)
        
        if df_producao is None or df_producao.empty:
            st.warning("Não há dados de produção disponíveis.")
            # Tentar carregar dados de demonstração
            try:
                from views.producao import generate_demo_data
                df_producao = generate_demo_data()
                st.session_state['df_producao'] = df_producao
                st.success(f"Carregados {len(df_producao)} registros de demonstração")
            except Exception as e:
                st.error(f"Erro ao carregar dados de demonstração: {str(e)}")
                return
        
        # Verificar se temos as colunas necessárias
        if 'ASSIGNED_BY_NAME' not in df_producao.columns or 'UF_CRM_HIGILIZACAO_STATUS' not in df_producao.columns:
            st.warning("Dados de produção não contêm as colunas necessárias para análise.")
            return
        
        # Substituir valores nulos no status por 'PENDENCIA'
        df_producao['UF_CRM_HIGILIZACAO_STATUS'] = df_producao['UF_CRM_HIGILIZACAO_STATUS'].fillna('PENDENCIA')
        
        # Agrupar por responsável e status e contar ocorrências
        status_counts = df_producao.groupby(['ASSIGNED_BY_NAME', 'UF_CRM_HIGILIZACAO_STATUS']).size().unstack(fill_value=0)
        
        # Certificar que todas as colunas de status existem
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
        
        # Limitar a 8 responsáveis para melhor visualização em tela vertical
        if len(display_df) > 8:
            display_df = display_df.head(8)
        
        # Mostrar um gráfico de barras horizontais empilhadas otimizado para tela vertical
        fig = go.Figure()
        
        # Adicionar barras em ordem de status (pendentes, incompletos, completos)
        fig.add_trace(go.Bar(
            y=display_df['ASSIGNED_BY_NAME'],
            x=display_df['PENDENCIA'],
            name='Pendentes',
            orientation='h',
            marker=dict(color='#F44336'),
            hovertemplate='%{y}: %{x} pendentes'
        ))
        
        fig.add_trace(go.Bar(
            y=display_df['ASSIGNED_BY_NAME'],
            x=display_df['INCOMPLETO'],
            name='Incompletos',
            orientation='h',
            marker=dict(color='#FFA000'),
            hovertemplate='%{y}: %{x} incompletos'
        ))
        
        fig.add_trace(go.Bar(
            y=display_df['ASSIGNED_BY_NAME'],
            x=display_df['COMPLETO'],
            name='Completos',
            orientation='h',
            marker=dict(color='#4CAF50'),
            hovertemplate='%{y}: %{x} completos'
        ))
        
        # Adicionar anotações para os totais
        anotacoes = []
        for i, row in display_df.iterrows():
            nome = row['ASSIGNED_BY_NAME']
            total = row['TOTAL']
            taxa = row['TAXA_CONCLUSAO']
            
            # Encontrar a posição do último responsável na lista
            y_pos = display_df['ASSIGNED_BY_NAME'].tolist().index(nome)
            
            # Adicionar anotação do total
            anotacoes.append(dict(
                x=total + (total * 0.05),  # Adicionar pequeno espaço após a barra
                y=y_pos,
                text=f"<b>{total}</b> ({taxa}%)",
                font=dict(size=14, color='#000000'),
                showarrow=False,
                xanchor='left'
            ))
        
        # Configurar layout
        fig.update_layout(
            barmode='stack',
            title={
                'text': 'Distribuição de Status por Responsável',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 20, 'color': '#1A237E', 'family': 'Arial, Helvetica, sans-serif'}
            },
            yaxis=dict(
                title='',
                tickfont=dict(size=16, family='Arial, Helvetica, sans-serif'),
                automargin=True
            ),
            xaxis=dict(
                title='Quantidade de Processos',
                tickfont=dict(size=14, family='Arial, Helvetica, sans-serif'),
                automargin=True
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5,
                font=dict(size=14, family='Arial, Helvetica, sans-serif')
            ),
            annotations=anotacoes,
            height=500,  # Altura otimizada para tela vertical
            margin=dict(l=20, r=50, t=80, b=100)
        )
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Calcular totais para a tabela de resumo
        totais = {
            'COMPLETO': display_df['COMPLETO'].sum(),
            'INCOMPLETO': display_df['INCOMPLETO'].sum(),
            'PENDENCIA': display_df['PENDENCIA'].sum(),
            'TOTAL': display_df['TOTAL'].sum()
        }
        
        # Calcular taxa de conclusão do total
        taxa_total = (totais['COMPLETO'] / totais['TOTAL'] * 100).round(1) if totais['TOTAL'] > 0 else 0.0
        
        # Criar dois cards para mostrar informações de resumo
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="info-text" style="background-color: #E8F5E9; border-color: #4CAF50;">
              <div style="font-size: 18px; font-weight: 700; color: #2E7D32; margin-bottom: 10px;">Resumo de Produtividade</div>
              <div style="font-size: 16px;">
                • <b>Conclusões:</b> {int(totais['COMPLETO']):,}<br>
                • <b>Taxa média:</b> {taxa_total}%<br>
                • <b>Total atribuído:</b> {int(totais['TOTAL']):,}
              </div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)
            
        with col2:
            # Criar um segundo gráfico (donut) para complementar a visualização
            status_data = pd.DataFrame({
                'Status': ['Completos', 'Incompletos', 'Pendentes'],
                'Valor': [totais['COMPLETO'], totais['INCOMPLETO'], totais['PENDENCIA']],
            })
            
            cores = {'Completos': '#4CAF50', 'Incompletos': '#FFA000', 'Pendentes': '#F44336'}
            
            fig2 = px.pie(
                status_data,
                names='Status',
                values='Valor',
                hole=0.6,
                color='Status',
                color_discrete_map=cores
            )
            
            fig2.update_layout(
                showlegend=False,
                height=200,
                margin=dict(l=5, r=5, t=5, b=5),
                annotations=[dict(
                    text=f"{taxa_total}%",
                    x=0.5, y=0.5,
                    font_size=22,
                    font_color='#1A237E',
                    showarrow=False
                )]
            )
            
            fig2.update_traces(
                textposition='outside',
                textinfo='percent',
                textfont_size=12,
                marker=dict(line=dict(color='#FFFFFF', width=1))
            )
            
            # Exibir gráfico de donut
            st.plotly_chart(fig2, use_container_width=True)
    
    except Exception as e:
        st.error(f"Erro ao gerar análise de status por responsável: {str(e)}")
        import traceback
        st.error(traceback.format_exc()) 