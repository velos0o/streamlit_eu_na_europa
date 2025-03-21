import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def slide_producao_ranking_pendencias(df):
    """
    Exibe um ranking dos responsáveis com mais pendências no formato de pódio
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados de produção (ignorado, usamos df_producao da session_state)
    """
    # Usar os dados de produção armazenados na session_state
    if 'df_producao' in st.session_state and not st.session_state['df_producao'].empty:
        df = st.session_state['df_producao']
    
    if df.empty:
        st.warning("Não há dados disponíveis para exibir o ranking de pendências.")
        return
    
    st.markdown('<h2 class="slide-title">Ranking de Pendências por Responsável</h2>', unsafe_allow_html=True)
    
    # Verificar se temos os campos necessários
    campos_higienizacao = {
        'UF_CRM_1741183785848': 'Documentação',
        'UF_CRM_1741183721969': 'Cadastro',
        'UF_CRM_1741183685327': 'Estrutura', 
        'UF_CRM_1741183828129': 'Requerimento',
        'UF_CRM_1741198696': 'Emissões'
    }
    
    # Verificar quais campos existem no DataFrame
    campos_existentes = [campo for campo in campos_higienizacao.keys() if campo in df.columns]
    
    if not campos_existentes:
        st.error("Não foram encontrados campos de higienização nos dados.")
        return
    
    # Filtrar apenas os registros pendentes ou incompletos
    df_pendencias = df[df['UF_CRM_HIGILIZACAO_STATUS'].isin(['PENDENCIA', 'INCOMPLETO'])].copy()
    
    if df_pendencias.empty:
        st.success("Não há pendências! Todos os processos estão completos.")
        return
    
    # Criar DataFrame para armazenar as contagens de pendências
    pendencias_data = []
    
    # Processar cada responsável
    for responsavel in df_pendencias['ASSIGNED_BY_NAME'].unique():
        # Filtrar dados do responsável
        df_resp = df_pendencias[df_pendencias['ASSIGNED_BY_NAME'] == responsavel]
        
        # Inicializar contadores
        contagem = {'Responsável': responsavel}
        total_pendencias = 0
        
        # Contar pendências por categoria
        for campo_id, campo_nome in campos_higienizacao.items():
            if campo_id in df_resp.columns:
                # Lista de valores que contam como pendência
                valores_pendencia = [
                    'NÃO', 'Não', 'NAO', 'nao', 'não', 'N', 'n',
                    'NÃO SELECIONADO', 'Não Selecionado', 'NAO SELECIONADO', 
                    'Nao Selecionado', 'não selecionado', 'não selecionada',
                    'n/s', 'N/S', False, 'false', 'FALSE'
                ]
                
                # Criar máscara para identificar registros que são 'NÃO', 'NÃO SELECIONADO' ou equivalentes
                mascara_nao = df_resp[campo_id].astype(str).str.upper().isin([str(v).upper() for v in valores_pendencia])
                
                # Máscara para valores vazios ou nulos
                mascara_vazio = (
                    df_resp[campo_id].isna() | 
                    (df_resp[campo_id].astype(str).str.strip() == '') |
                    (df_resp[campo_id].astype(str).str.upper() == 'NAN') |
                    (df_resp[campo_id].astype(str).str.upper() == 'NONE') |
                    (df_resp[campo_id].astype(str).str.upper() == 'NULL')
                )
                
                # Contar todas as ocorrências de pendências
                pendencias = (mascara_nao | mascara_vazio).sum()
                contagem[campo_nome] = pendencias
                total_pendencias += pendencias
        
        # Adicionar total
        contagem['Total'] = total_pendencias
        
        # Adicionar à lista de dados
        pendencias_data.append(contagem)
    
    # Criar DataFrame com os dados de pendências
    df_pendencias_resumo = pd.DataFrame(pendencias_data)
    
    # Classificar por total de pendências (maior primeiro)
    df_pendencias_resumo = df_pendencias_resumo.sort_values('Total', ascending=False)
    
    # Preencher valores NaN com 0
    for campo in campos_higienizacao.values():
        if campo in df_pendencias_resumo.columns:
            df_pendencias_resumo[campo] = df_pendencias_resumo[campo].fillna(0).astype(int)
    
    # Exibir ranking de pendências
    if not df_pendencias_resumo.empty:
        # Mostrar pódio (top 3)
        st.markdown("### 🏆 Pódio de Pendências")
        
        # Pegar top 3 responsáveis
        top3 = df_pendencias_resumo.head(3).reset_index(drop=True)
        
        # Criar colunas para o pódio
        if len(top3) >= 3:
            col1, col2, col3 = st.columns(3)
            
            # Segundo lugar
            with col1:
                st.markdown(f"""
                <div style="background-color: #E0E0E0; border-radius: 10px; padding: 15px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: flex-end;">
                    <div style="font-size: 24px; margin-bottom: 10px;">🥈</div>
                    <div style="font-weight: bold; font-size: 18px;">{top3.iloc[1]['Responsável']}</div>
                    <div style="font-size: 24px; color: #f44336; font-weight: bold;">{int(top3.iloc[1]['Total'])}</div>
                    <div style="font-size: 12px; margin-top: 5px;">pendências</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Primeiro lugar
            with col2:
                st.markdown(f"""
                <div style="background-color: #FFD700; border-radius: 10px; padding: 15px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: flex-end;">
                    <div style="font-size: 30px; margin-bottom: 10px;">🥇</div>
                    <div style="font-weight: bold; font-size: 20px;">{top3.iloc[0]['Responsável']}</div>
                    <div style="font-size: 30px; color: #f44336; font-weight: bold;">{int(top3.iloc[0]['Total'])}</div>
                    <div style="font-size: 14px; margin-top: 5px;">pendências</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Terceiro lugar
            with col3:
                st.markdown(f"""
                <div style="background-color: #CD7F32; border-radius: 10px; padding: 15px; text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: flex-end;">
                    <div style="font-size: 20px; margin-bottom: 10px;">🥉</div>
                    <div style="font-weight: bold; font-size: 16px;">{top3.iloc[2]['Responsável']}</div>
                    <div style="font-size: 20px; color: #f44336; font-weight: bold;">{int(top3.iloc[2]['Total'])}</div>
                    <div style="font-size: 12px; margin-top: 5px;">pendências</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Mostrar tabela de ranking completo
        st.markdown("### Ranking Completo")
        
        # Adicionar coluna de posição
        df_pendencias_resumo = df_pendencias_resumo.reset_index(drop=True)
        df_pendencias_resumo['Posição'] = df_pendencias_resumo.index + 1
        
        # Reordenar colunas para ter Posição primeiro
        cols = ['Posição', 'Responsável'] + [col for col in df_pendencias_resumo.columns if col not in ['Posição', 'Responsável', 'Total']] + ['Total']
        df_pendencias_resumo = df_pendencias_resumo[cols]
        
        # Aplicar formatação condicional
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
        
        # Destacar a posição
        def destacar_posicao(val):
            if val == 1:
                return 'background-color: gold; color: black; font-weight: bold'
            elif val == 2:
                return 'background-color: silver; color: black; font-weight: bold'
            elif val == 3:
                return 'background-color: #CD7F32; color: black; font-weight: bold'
            else:
                return ''
        
        # Aplicar estilos ao dataframe
        df_styled = df_pendencias_resumo.style.applymap(
            destacar_celula, 
            subset=[col for col in df_pendencias_resumo.columns if col not in ['Posição', 'Responsável', 'Total']]
        ).applymap(
            destacar_total,
            subset=['Total']
        ).applymap(
            destacar_posicao,
            subset=['Posição']
        ).format('{:.0f}', subset=[col for col in df_pendencias_resumo.columns if col not in ['Responsável']])
        
        # Exibir dataframe estilizado
        st.dataframe(
            df_styled,
            use_container_width=True,
            height=min(400, 80 + 35 * len(df_pendencias_resumo)),
            column_config={
                "Posição": st.column_config.NumberColumn("Posição", format="%d", width="small"),
                "Responsável": st.column_config.TextColumn("Responsável", width="large"),
                **{campo: st.column_config.NumberColumn(campo, format="%d") 
                   for campo in campos_higienizacao.values() if campo in df_pendencias_resumo.columns},
                "Total": st.column_config.NumberColumn("Total", format="%d", width="medium")
            }
        )
        
        # Gráfico horizontal de barras para o ranking
        st.markdown("### Distribuição de Pendências por Categoria")
        
        # Preparar dados para o gráfico
        top10 = df_pendencias_resumo.head(10).copy()
        
        # Converter para formato longo para o gráfico
        melted_df = pd.melt(
            top10, 
            id_vars=['Posição', 'Responsável', 'Total'],
            value_vars=[col for col in campos_higienizacao.values() if col in top10.columns],
            var_name='Categoria', 
            value_name='Pendências'
        )
        
        # Criar gráfico de barras horizontais para top 10
        fig = px.bar(
            melted_df,
            y='Responsável',
            x='Pendências',
            color='Categoria',
            orientation='h',
            height=500,
            barmode='stack',
            color_discrete_map={
                'Documentação': '#E57373',  # Vermelho claro
                'Cadastro': '#FFB74D',      # Laranja
                'Estrutura': '#FFF176',     # Amarelo
                'Requerimento': '#81C784',  # Verde
                'Emissões': '#64B5F6'       # Azul
            }
        )
        
        # Customizar o layout
        fig.update_layout(
            title={
                'text': 'Ranking de Pendências por Categoria',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 20, 'color': '#1A237E'}
            },
            xaxis_title='Número de Pendências',
            yaxis_title=None,
            yaxis={'categoryorder': 'total ascending'},
            legend_title='Categoria',
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
            title_font={"size": 14},
            tickfont={"size": 12},
            gridcolor='lightgray'
        )
        fig.update_yaxes(
            title_font={"size": 14},
            tickfont={"size": 12},
        )
        
        # Adicionar totais à direita das barras
        for i, row in top10.iterrows():
            fig.add_annotation(
                x=row['Total'],
                y=row['Responsável'],
                text=f" {int(row['Total'])}",
                showarrow=False,
                font=dict(size=14, color="#1A237E", family="Arial, Helvetica, sans-serif"),
                xanchor="left"
            )
        
        # Exibir o gráfico
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não foram encontradas pendências nos dados filtrados.") 