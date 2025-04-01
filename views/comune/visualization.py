import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import io

def visualizar_comune_dados(df_comune):
    """
    Exibe os dados detalhados de COMUNE em uma tabela
    """
    if df_comune.empty:
        st.warning("Nenhum dado disponível para visualização.")
        return
    
    # Colunas relevantes para exibição
    colunas_exibicao = [
        'ID', 'TITLE', 'STAGE_ID', 'STAGE_NAME', 'ASSIGNED_BY_NAME', 
        'DATE_CREATE', 'DATE_MODIFY', 'UF_CRM_12_1723552666'
    ]
    
    # Verificar quais colunas existem no DataFrame
    colunas_selecionadas = [coluna for coluna in colunas_exibicao if coluna in df_comune.columns]
    
    # Se STAGE_NAME não estiver presente, usar o mapeamento dos estágios
    if 'STAGE_NAME' not in df_comune.columns and 'STAGE_ID' in df_comune.columns:
        from .data_loader import mapear_estagios_comune
        mapa_estagios = mapear_estagios_comune()
        df_exibicao = df_comune.copy()
        df_exibicao['STAGE_NAME'] = df_exibicao['STAGE_ID'].map(mapa_estagios)
    else:
        df_exibicao = df_comune.copy()
    
    # Converter datas para formato legível
    for coluna in ['DATE_CREATE', 'DATE_MODIFY']:
        if coluna in df_exibicao.columns:
            df_exibicao[coluna] = pd.to_datetime(df_exibicao[coluna]).dt.strftime('%d/%m/%Y %H:%M')
    
    # Exibir tabela com os dados
    st.subheader("Dados Detalhados de COMUNE")
    st.dataframe(df_exibicao[colunas_selecionadas], use_container_width=True)

def visualizar_funil_comune(df_visao_geral):
    """
    Exibe um gráfico de funil com os estágios de COMUNE, incluindo os sem registros
    """
    if df_visao_geral.empty:
        st.warning("Nenhum dado disponível para visualização do funil.")
        return
    
    st.subheader("Funil de COMUNE")
    
    # Filtrar para exibir apenas estágios com registros
    df_funil_com_registros = df_visao_geral[df_visao_geral['QUANTIDADE'] > 0].copy()
    
    # Preparar dados para o funil
    df_funil = df_funil_com_registros.sort_values('QUANTIDADE', ascending=True)
    
    # Criar o gráfico de funil
    fig = go.Figure(go.Funnel(
        y=df_funil['STAGE_NAME'],
        x=df_funil['QUANTIDADE'],
        textposition="inside",
        textinfo="value+percent initial",
        opacity=0.8,
        marker={"color": ["#4B0082", "#0000CD", "#1E90FF", "#00BFFF", "#87CEEB", "#B0E0E6", "#F0F8FF"],
                "line": {"width": [0, 0, 0, 0, 0, 0, 0]}},
        connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}}
    ))
    
    # Configurar layout
    fig.update_layout(
        title="Funil de Processos COMUNE",
        font=dict(size=14),
        height=600,
        width=800
    )
    
    # Exibir o gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Exibir lista de estágios sem registros (se houver)
    df_zerados = df_visao_geral[df_visao_geral['QUANTIDADE'] == 0]
    if not df_zerados.empty:
        st.info(f"Existem {len(df_zerados)} estágios sem registros que não aparecem no funil acima")
        with st.expander("Ver estágios sem registros"):
            st.dataframe(
                df_zerados[['STAGE_NAME']].rename(columns={'STAGE_NAME': 'Estágio sem registros'}),
                hide_index=True
            )

def visualizar_grafico_macro(df_visao_macro):
    """
    Exibe um gráfico de barras com a visão detalhada dos estágios, incluindo os que estão zerados
    """
    if df_visao_macro.empty:
        st.warning("Nenhum dado disponível para visualização da visão macro.")
        return
    
    # Definir ordem específica para os estágios conforme solicitado
    ordem_estagios = [
        "PENDENTE",
        "PESQUISA NÃO FINALIZADA", 
        "DEVOLUTIVA EMISSOR",
        "SOLICITAR", 
        "URGENTE",
        "SOLICITAR - TEM INFO",
        "AGUARDANDO COMUNE/PARÓQUIA",
        "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO",
        "AGUARDANDO PDF",
        "ENTREGUE PDF",
        "NEGATIVA COMUNE",
        "DOCUMENTO FISICO ENTREGUE",
        "CANCELADO"
    ]
    
    # Criar um DataFrame com todos os estágios da ordem, com contagem zero para os que não existem
    df_todos_estagios = pd.DataFrame({'MACRO_STAGE': ordem_estagios})
    
    # Mesclar com os dados reais para obter as contagens
    df_ordenado = pd.merge(
        df_todos_estagios, 
        df_visao_macro, 
        on='MACRO_STAGE', 
        how='left'
    )
    
    # Preencher valores ausentes com zero
    df_ordenado['QUANTIDADE'] = df_ordenado['QUANTIDADE'].fillna(0)
    
    # Calcular percentuais para exibir nos rótulos
    total = df_ordenado['QUANTIDADE'].sum()
    df_ordenado['PERCENTUAL'] = (df_ordenado['QUANTIDADE'] / total * 100).round(1)
    df_ordenado['ROTULO'] = df_ordenado.apply(lambda x: f"{int(x['QUANTIDADE'])} ({x['PERCENTUAL']}%)", axis=1)
    
    # Definir cores para cada estágio
    cores = {
        "PENDENTE": "#FFD700",                           # Amarelo
        "PESQUISA NÃO FINALIZADA": "#FFA500",            # Laranja
        "DEVOLUTIVA EMISSOR": "#FF6347",                 # Tomate
        "SOLICITAR": "#1E90FF",                          # Azul
        "URGENTE": "#FF4500",                            # Vermelho
        "SOLICITAR - TEM INFO": "#4169E1",               # Azul real
        "AGUARDANDO COMUNE/PARÓQUIA": "#00BFFF",         # Azul céu profundo
        "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO": "#87CEEB", # Azul céu
        "AGUARDANDO PDF": "#6495ED",                     # Azul cobalto
        "ENTREGUE PDF": "#00CED1",                       # Turquesa
        "NEGATIVA COMUNE": "#DC143C",                    # Carmesim
        "DOCUMENTO FISICO ENTREGUE": "#32CD32",          # Verde
        "CANCELADO": "#A9A9A9"                           # Cinza
    }
    
    # Criar o gráfico de barras com Plotly
    fig = px.bar(
        df_ordenado, 
        x='MACRO_STAGE', 
        y='QUANTIDADE',
        color='MACRO_STAGE',
        color_discrete_map=cores,
        text='ROTULO',  # Usar rótulo personalizado com percentual
        title="",  # Remover título, pois já temos um no HTML
        labels={"MACRO_STAGE": "Estágio", "QUANTIDADE": "Quantidade"},
        category_orders={"MACRO_STAGE": ordem_estagios}  # Usar a ordem específica
    )
    
    # Adicionar padrão para barras com valor zero
    for i, row in df_ordenado.iterrows():
        if row['QUANTIDADE'] == 0:
            fig.add_trace(go.Bar(
                x=[row['MACRO_STAGE']],
                y=[0.5],  # Altura mínima visível
                marker=dict(
                    color='rgba(0,0,0,0)',  # Transparente
                    line=dict(
                        color=cores.get(row['MACRO_STAGE'], '#888888'),
                        width=2
                    ),
                    pattern=dict(shape="/", size=8)  # Padrão listrado
                ),
                showlegend=False,
                hovertemplate=f"<b>{row['MACRO_STAGE']}</b><br>Quantidade: 0<br>Percentual: 0.0%<extra></extra>"
            ))
    
    # Configurar layout
    fig.update_layout(
        xaxis_title={
            'text': "Estágio",
            'font': dict(size=16, family="Arial, Helvetica, sans-serif")
        },
        yaxis_title={
            'text': "Quantidade",
            'font': dict(size=16, family="Arial, Helvetica, sans-serif")
        },
        font=dict(
            family="Arial, Helvetica, sans-serif",
            size=14
        ),
        height=600,  # Aumentar altura para acomodar mais categorias
        showlegend=False,  # Esconder legenda pois as cores já são identificáveis
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        margin=dict(t=30, b=120, l=50, r=30),  # Aumentar margem inferior para os rótulos
        bargap=0.3,  # Mais espaço entre barras
    )
    
    # Configurar barras
    fig.update_traces(
        marker_line_width=1.5,  # Borda mais grossa
        marker_line_color='rgba(0,0,0,0.2)',  # Borda levemente escurecida
        opacity=0.9,  # Leve transparência
        textposition='outside',  # Texto acima das barras
        textfont=dict(size=14, family="Arial, Helvetica, sans-serif", color="black"),
        hovertemplate='<b>%{x}</b><br>Quantidade: %{y}<br>Percentual: %{text}<extra></extra>'
    )
    
    # Melhorar grid e eixos
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#E0E0E0',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='#E0E0E0',
        showline=True,
        linewidth=2,
        linecolor='#212121',
        tickfont=dict(size=13, family="Arial, Helvetica, sans-serif"),
        tickangle=45  # Rotacionar rótulos para melhor visualização
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#E0E0E0',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='#E0E0E0',
        showline=True,
        linewidth=2,
        linecolor='#212121',
        tickfont=dict(size=14, family="Arial, Helvetica, sans-serif")
    )
    
    # Calcular média apenas dos valores não-zero para ser mais realista
    valores_nao_zero = df_ordenado[df_ordenado['QUANTIDADE'] > 0]['QUANTIDADE']
    media = valores_nao_zero.mean() if not valores_nao_zero.empty else 0
    
    # Adicionar linha de média
    if media > 0:
        fig.add_shape(
            type="line",
            x0=-0.5,
            x1=len(df_ordenado) - 0.5,
            y0=media,
            y1=media,
            line=dict(
                color="#FF5722",
                width=2,
                dash="dash",
            ),
            name="Média"
        )
        
        # Adicionar anotação para a média
        fig.add_annotation(
            x=len(df_ordenado) - 0.5,
            y=media,
            text=f"Média: {media:.1f}",
            showarrow=False,
            xshift=60,
            yshift=0,
            font=dict(
                family="Arial, Helvetica, sans-serif",
                size=14,
                color="#FF5722"
            ),
            align="left"
        )
    
    # Exibir o gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Adicionar tabela com os dados para referência
    with st.expander("Ver dados detalhados"):
        # Preparar dados para exibição
        df_tabela = df_ordenado.copy()
        df_tabela['PERCENTUAL'] = df_tabela['PERCENTUAL'].apply(lambda x: f"{x:.1f}%")
        
        # Ordenar por nome de estágio
        df_tabela = df_tabela.sort_values('MACRO_STAGE')
        
        # Criar uma versão estilizada da tabela
        df_html = df_tabela.copy()
        df_html['ESTILO'] = df_html['QUANTIDADE'].apply(
            lambda x: 'background-color: #f8f9fa; color: #6c757d; font-style: italic;' if x == 0 else ''
        )
        
        # Mostrar tabela
        st.markdown("##### Distribuição por estágio (incluindo zerados)")
        st.dataframe(
            df_tabela[['MACRO_STAGE', 'QUANTIDADE', 'PERCENTUAL']].rename(
                columns={'MACRO_STAGE': 'Estágio', 'QUANTIDADE': 'Quantidade', 'PERCENTUAL': 'Percentual (%)'}
            ),
            use_container_width=True,
            column_config={
                "Estágio": st.column_config.TextColumn(
                    "Estágio",
                    help="Nome do estágio do processo",
                    width="large"
                ),
                "Quantidade": st.column_config.NumberColumn(
                    "Quantidade",
                    help="Quantidade de registros neste estágio",
                    format="%d"
                ),
                "Percentual (%)": st.column_config.TextColumn(
                    "Percentual (%)",
                    help="Percentual em relação ao total de registros"
                )
            },
            hide_index=True
        )
        
        # Mostrar total na parte inferior
        total_registros = df_tabela['QUANTIDADE'].sum()
        st.markdown(f"**Total de registros:** {int(total_registros)}")
        st.markdown(f"**Estágios sem registros:** {len(df_tabela[df_tabela['QUANTIDADE'] == 0])}")
        
        # Adicionar texto explicativo
        if len(df_tabela[df_tabela['QUANTIDADE'] == 0]) > 0:
            st.info("Os estágios com quantidade zero aparecem no gráfico com uma barra tracejada para destacar que estão disponíveis no sistema, mas não possuem registros atualmente.")
        
        # Adicionar opção para download
        csv = df_tabela.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar dados em CSV",
            data=csv,
            file_name=f'distribuicao_estagios_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
            mime='text/csv'
        )

def visualizar_cruzamento_deal(df_distribuicao):
    """
    Exibe a análise do cruzamento entre COMUNE e CRM_DEAL
    """
    if df_distribuicao.empty:
        st.warning("Nenhum dado disponível para visualização do cruzamento com CRM_DEAL.")
        return
    
    st.subheader("Cruzamento COMUNE x CRM_DEAL")
    
    # Criar gráfico de barras empilhadas
    fig = go.Figure(data=[
        go.Bar(
            name='Com Deal',
            x=df_distribuicao['STAGE_NAME'],
            y=df_distribuicao['COM_DEAL'],
            marker_color='#1E90FF'
        ),
        go.Bar(
            name='Sem Deal',
            x=df_distribuicao['STAGE_NAME'],
            y=df_distribuicao['SEM_DEAL'],
            marker_color='#FFD700'
        )
    ])
    
    # Configurar layout como barras empilhadas
    fig.update_layout(
        barmode='stack',
        title="Distribuição de Deals por Estágio",
        xaxis_title="Estágio",
        yaxis_title="Quantidade",
        legend_title="Status",
        font=dict(size=14),
        height=600
    )
    
    # Adicionar labels
    for i, row in df_distribuicao.iterrows():
        if row['TOTAL'] > 0:
            fig.add_annotation(
                x=row['STAGE_NAME'],
                y=row['TOTAL'],
                text=f"{row['PERCENTUAL_COM_DEAL']}%",
                showarrow=False,
                yshift=10,
                font=dict(size=12, color="black")
            )
    
    # Exibir o gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Exibir tabela com os dados
    st.dataframe(df_distribuicao, use_container_width=True)

def visualizar_analise_sem_correspondencia(resumo_analise):
    """
    Visualiza gráficos e tabelas com análise dos registros sem correspondência
    """
    if not resumo_analise:
        st.info("Não há registros sem correspondência ou não foi possível realizar a análise.")
        return
    
    # Título da seção
    st.markdown("""
    <h3 style="color: #FF5722; margin-top: 1rem;">Análise de Registros Sem Correspondência</h3>
    <p style="color: #555;">Esta análise detalha os registros que existem no Comune mas não foram encontrados em CRM_DEAL.</p>
    """, unsafe_allow_html=True)
    
    # Total de registros sem correspondência
    st.metric(
        label="Total de Registros sem Correspondência", 
        value=resumo_analise.get('total_sem_match', 0),
        delta=None
    )
    
    # Análise por estágio
    if 'por_estagio' in resumo_analise:
        por_estagio = resumo_analise['por_estagio']
        
        # Criar gráfico de barras para distribuição por estágio
        st.subheader("Distribuição por Estágio")
        fig = px.bar(
            por_estagio,
            x='STAGE_NAME',
            y='QUANTIDADE',
            text='QUANTIDADE',
            color='STAGE_NAME',
            labels={'STAGE_NAME': 'Estágio', 'QUANTIDADE': 'Quantidade'},
            title="Registros sem correspondência por estágio"
        )
        
        # Ajustar layout
        fig.update_layout(
            xaxis_title="Estágio",
            yaxis_title="Quantidade",
            xaxis={'categoryorder':'total descending'}
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Exibir tabela
        st.dataframe(por_estagio, use_container_width=True)
    
    # Análise por período
    if 'por_periodo' in resumo_analise:
        por_periodo = resumo_analise['por_periodo']
        
        if not por_periodo.empty:
            # Criar gráfico de linha para evolução temporal
            st.subheader("Evolução Temporal")
            fig = px.line(
                por_periodo,
                x='MES_ANO',
                y='QUANTIDADE',
                markers=True,
                labels={'MES_ANO': 'Mês/Ano', 'QUANTIDADE': 'Quantidade'},
                title="Evolução temporal dos registros sem correspondência"
            )
            
            # Ajustar layout
            fig.update_layout(
                xaxis_title="Período",
                yaxis_title="Quantidade"
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Exibir tabela
            st.dataframe(por_periodo, use_container_width=True)

def visualizar_estagios_detalhados(df_visao_geral):
    """
    Exibe um gráfico de barras horizontais com todos os estágios detalhados do COMUNE
    """
    if df_visao_geral.empty:
        st.warning("Nenhum dado disponível para visualização dos estágios detalhados.")
        return
    
    # Título da seção
    st.markdown("""
    <h3 style="font-size: 26px; font-weight: 800; color: #1A237E; margin: 30px 0 15px 0; 
    padding-bottom: 8px; border-bottom: 2px solid #E0E0E0; font-family: Arial, Helvetica, sans-serif;">
    DISTRIBUIÇÃO DETALHADA POR ESTÁGIO</h3>
    """, unsafe_allow_html=True)
    
    # Adicionar comentário explicativo
    st.markdown("""
    <div style="background-color: #f5f5f5; 
                padding: 15px; 
                border-radius: 8px; 
                margin-bottom: 20px;
                border-left: 5px solid #1976D2;
                font-family: Arial, Helvetica, sans-serif;">
        <p style="font-size: 16px; margin: 0; color: #333; font-weight: 500;">
            A visualização abaixo mostra a distribuição dos processos em cada estágio específico do fluxo,
            permitindo identificar com precisão em quais pontos do processo estão concentrados os processos.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Copiar e ordenar os dados
    df_ordenado = df_visao_geral.copy()
    
    # Calcular percentuais para exibir nos rótulos
    total = df_ordenado['QUANTIDADE'].sum()
    df_ordenado['PERCENTUAL'] = (df_ordenado['QUANTIDADE'] / total * 100).round(1)
    df_ordenado['ROTULO'] = df_ordenado.apply(lambda x: f"{int(x['QUANTIDADE'])} ({x['PERCENTUAL']}%)", axis=1)
    
    # Ordenar por quantidade (decrescente)
    df_ordenado = df_ordenado.sort_values('QUANTIDADE', ascending=False)
    
    # Definir cores para os estágios
    # Mapeamento de cores baseado em categorias de estágio
    cores_por_categoria = {
        "PENDENTE": "#FFD700",           # Amarelo
        "PESQUISA NÃO FINALIZADA": "#FFEB3B", # Amarelo mais claro
        "DEVOLUTIVA EMISSOR": "#FFC107",  # Âmbar
        "SOLICITAR": "#2196F3",          # Azul
        "SOLICITAR - TEM INFO": "#64B5F6", # Azul mais claro
        "URGENTE": "#FF4500",            # Vermelho alaranjado
        "AGUARDANDO COMUNE/PARÓQUIA": "#03A9F4", # Azul claro
        "AGUARDANDO COMUNE/PARÓQUIA - TEM INFO": "#4FC3F7", # Azul ainda mais claro
        "AGUARDANDO PDF": "#29B6F6",     # Azul claro
        "ENTREGUE PDF": "#81D4FA",       # Azul bem claro
        "NEGATIVA COMUNE": "#F44336",    # Vermelho
        "DOCUMENTO FISICO ENTREGUE": "#4CAF50", # Verde
        "CANCELADO": "#9E9E9E"           # Cinza
    }
    
    # Preparar cores para o gráfico
    cores_customizadas = [cores_por_categoria.get(estagio, "#9C27B0") for estagio in df_ordenado['STAGE_NAME']]
    
    # Criar o gráfico de barras horizontais
    fig = go.Figure()
    
    # Adicionar as barras
    fig.add_trace(go.Bar(
        x=df_ordenado['QUANTIDADE'],
        y=df_ordenado['STAGE_NAME'],
        orientation='h',
        marker=dict(
            color=cores_customizadas,
            line=dict(color='rgba(0,0,0,0.2)', width=1)
        ),
        text=df_ordenado['ROTULO'],
        textposition='auto',
        insidetextanchor='middle',
        textfont=dict(
            family="Arial, Helvetica, sans-serif",
            size=14
        ),
        hovertemplate='<b>%{y}</b><br>Quantidade: %{x}<br>Percentual: %{text}<extra></extra>'
    ))
    
    # Adicionar linha de média
    media = df_ordenado['QUANTIDADE'].mean()
    fig.add_shape(
        type="line",
        y0=-0.5,
        y1=len(df_ordenado) - 0.5,
        x0=media,
        x1=media,
        line=dict(
            color="#FF5722",
            width=2,
            dash="dash",
        ),
        name="Média"
    )
    
    # Adicionar anotação para a média
    fig.add_annotation(
        y=len(df_ordenado) - 0.5,
        x=media,
        text=f"Média: {media:.1f}",
        showarrow=False,
        yshift=15,
        xshift=0,
        font=dict(
            family="Arial, Helvetica, sans-serif",
            size=14,
            color="#FF5722"
        ),
        align="center"
    )
    
    # Layout do gráfico
    fig.update_layout(
        height=max(500, len(df_ordenado) * 35),  # Altura dinâmica baseada no número de estágios
        margin=dict(l=20, r=50, t=30, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            title=dict(
                text="Quantidade de Processos",
                font=dict(size=16, family="Arial, Helvetica, sans-serif")
            ),
            gridcolor='#E0E0E0',
            showgrid=True,
            zeroline=True,
            zerolinecolor='#E0E0E0',
            zerolinewidth=2,
            showline=True,
            linecolor='#212121',
            linewidth=2,
            tickfont=dict(size=14, family="Arial, Helvetica, sans-serif")
        ),
        yaxis=dict(
            title=None,
            autorange="reversed",  # Inverte a ordem para mostrar a maior quantidade no topo
            gridcolor='#E0E0E0',
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#212121',
            linewidth=2,
            tickfont=dict(size=14, family="Arial, Helvetica, sans-serif")
        ),
        showlegend=False
    )
    
    # Mostrar o gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Adicionar tabela com dados completos
    with st.expander("Ver tabela de dados completa", expanded=False):
        # Adicionar colunas formatadas à tabela
        df_tabela = df_ordenado.copy()
        df_tabela['PERCENTUAL'] = df_tabela['PERCENTUAL'].apply(lambda x: f"{x:.1f}%")
        
        # Ordenar para mostrar estágios em ordem alfabética
        df_tabela = df_tabela.sort_values('STAGE_NAME')
        
        # Mostrar tabela
        st.dataframe(
            df_tabela[['STAGE_NAME', 'QUANTIDADE', 'PERCENTUAL']],
            column_config={
                "STAGE_NAME": "Estágio",
                "QUANTIDADE": "Quantidade",
                "PERCENTUAL": "Percentual"
            },
            use_container_width=True
        )
    
    # Análise de distribuição
    with st.expander("Análise de Distribuição", expanded=True):
        # Calcular métricas
        total_registros = df_ordenado['QUANTIDADE'].sum()
        maior_estagio = df_ordenado.iloc[0]
        menor_estagio = df_ordenado.iloc[-1]
        acima_media = df_ordenado[df_ordenado['QUANTIDADE'] > media]
        percentual_acima_media = (acima_media['QUANTIDADE'].sum() / total_registros * 100).round(1)
        
        # Exibir métricas em grid
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; 
                 border-left: 5px solid #1976D2; margin-bottom: 10px; font-family: Arial, Helvetica, sans-serif;">
                <h4 style="color: #1565C0; margin-top: 0; margin-bottom: 5px; font-size: 18px;">Estágio com Maior Volume</h4>
                <p style="font-size: 22px; font-weight: 700; margin: 5px 0; color: #0D47A1;">
                    {maior_estagio['STAGE_NAME']}
                </p>
                <p style="font-size: 16px; margin: 5px 0;">
                    <span style="font-weight: 600;">{int(maior_estagio['QUANTIDADE'])}</span> processos 
                    (<span style="font-weight: 600;">{maior_estagio['PERCENTUAL']:.1f}%</span> do total)
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background-color: #fff8e1; padding: 15px; border-radius: 10px; 
                 border-left: 5px solid #FFC107; margin-bottom: 10px; font-family: Arial, Helvetica, sans-serif;">
                <h4 style="color: #F57F17; margin-top: 0; margin-bottom: 5px; font-size: 18px;">Estágio com Menor Volume</h4>
                <p style="font-size: 22px; font-weight: 700; margin: 5px 0; color: #E65100;">
                    {menor_estagio['STAGE_NAME']}
                </p>
                <p style="font-size: 16px; margin: 5px 0;">
                    <span style="font-weight: 600;">{int(menor_estagio['QUANTIDADE'])}</span> processos 
                    (<span style="font-weight: 600;">{menor_estagio['PERCENTUAL']:.1f}%</span> do total)
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; 
                 border-left: 5px solid #4CAF50; margin-bottom: 10px; font-family: Arial, Helvetica, sans-serif;">
                <h4 style="color: #2E7D32; margin-top: 0; margin-bottom: 5px; font-size: 18px;">Estágios Acima da Média</h4>
                <p style="font-size: 22px; font-weight: 700; margin: 5px 0; color: #1B5E20;">
                    {len(acima_media)} estágios
                </p>
                <p style="font-size: 16px; margin: 5px 0;">
                    Representam <span style="font-weight: 600;">{percentual_acima_media}%</span> dos processos
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background-color: #f3e5f5; padding: 15px; border-radius: 10px; 
                 border-left: 5px solid #9C27B0; margin-bottom: 10px; font-family: Arial, Helvetica, sans-serif;">
                <h4 style="color: #7B1FA2; margin-top: 0; margin-bottom: 5px; font-size: 18px;">Distribuição Geral</h4>
                <p style="font-size: 16px; margin: 5px 0;">
                    Total de <span style="font-weight: 600;">{len(df_ordenado)}</span> estágios com 
                    <span style="font-weight: 600;">{total_registros}</span> processos
                </p>
                <p style="font-size: 16px; margin: 5px 0;">
                    Média de <span style="font-weight: 600;">{media:.1f}</span> processos por estágio
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Adicionar recomendações baseadas na análise
        st.markdown("""
        <h4 style="color: #1A237E; font-size: 20px; margin-top: 20px; margin-bottom: 10px; 
             font-family: Arial, Helvetica, sans-serif;">Recomendações</h4>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background-color: #e8eaf6; 
                   padding: 15px; 
                   border-radius: 10px; 
                   margin-bottom: 10px;
                   border: 1px solid #c5cae9;
                   font-family: Arial, Helvetica, sans-serif;">
            <ul style="margin: 0; padding-left: 20px;">
                <li style="font-size: 15px; color: #333; font-weight: 500; margin-bottom: 8px;">
                    <strong>Atenção ao estágio {maior_estagio['STAGE_NAME']}:</strong> Por concentrar o maior volume de processos ({maior_estagio['PERCENTUAL']:.1f}%), 
                    considere alocar mais recursos para este estágio ou revisar o fluxo para reduzir acúmulos.
                </li>
                <li style="font-size: 15px; color: #333; font-weight: 500; margin-bottom: 8px;">
                    <strong>Verifique estágios com poucos processos:</strong> Estágios com volume muito baixo podem indicar 
                    processos que avançam rapidamente ou possíveis problemas de classificação.
                </li>
                <li style="font-size: 15px; color: #333; font-weight: 500; margin-bottom: 8px;">
                    <strong>Balance a distribuição:</strong> Busque nivelar a quantidade de processos em cada estágio para 
                    otimizar o fluxo de trabalho e evitar gargalos.
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def visualizar_tempo_solicitacao(df_tempo_solicitacao):
    """
    Visualiza a tabela de tempo médio de solicitação agrupado por UF_CRM_12_1723552666
    
    Args:
        df_tempo_solicitacao: DataFrame com o tempo médio de solicitação
    """
    if df_tempo_solicitacao.empty:
        st.warning("Não há dados disponíveis para cálculo do tempo de solicitação.")
        return
    
    # Título da seção
    st.markdown("""
    <h3 style="font-size: 1.5rem; font-weight: 700; color: #1A237E; 
    margin-top: 2rem; margin-bottom: 1rem; padding-bottom: 5px; border-bottom: 2px solid #1976D2;">
    Tempo Médio de Solicitação por Campo UF_CRM_12_1723552666</h3>
    """, unsafe_allow_html=True)
    
    # Renomear colunas para melhor visualização
    df_display = df_tempo_solicitacao.copy()
    
    # Adicionar colunas para meses, dias e horas
    df_display['MESES'] = (df_display['TEMPO_SOLICITACAO_HORAS'] / (24 * 30)).round(1)
    df_display['DIAS'] = (df_display['TEMPO_SOLICITACAO_HORAS'] / 24).round(1)
    df_display['HORAS'] = df_display['TEMPO_SOLICITACAO_HORAS'].round(2)
    
    # Renomear colunas
    df_display.columns = ['Campo UF_CRM_12_1723552666', 'Tempo Médio (horas)', 'Quantidade de Registros', 'Meses', 'Dias', 'Horas']
    
    # Adicionar métrica resumo
    col1, col2, col3 = st.columns(3)
    
    # Tempo médio geral
    tempo_medio_geral = df_tempo_solicitacao['TEMPO_SOLICITACAO_HORAS'].mean()
    tempo_medio_dias = tempo_medio_geral / 24
    
    with col1:
        st.metric(
            label="Tempo Médio Geral de Solicitação", 
            value=f"{int(tempo_medio_geral)} horas ({int(tempo_medio_dias)} dias)"
        )
    
    with col2:
        st.metric(
            label="Total de Registros Analisados", 
            value=f"{df_tempo_solicitacao['QUANTIDADE'].sum()}"
        )
    
    with col3:
        tempo_mediano = df_tempo_solicitacao['TEMPO_SOLICITACAO_HORAS'].median()
        tempo_mediano_dias = tempo_mediano / 24
        st.metric(
            label="Tempo Mediano de Solicitação",
            value=f"{int(tempo_mediano)} horas ({int(tempo_mediano_dias)} dias)"
        )
    
    # Formatar a tabela para exibição
    # Aplicar formatação para tempo em horas/dias/meses
    def formatar_tempo_meses(meses):
        return f"{int(meses)} {'mês' if int(meses) == 1 else 'meses'}"
    
    def formatar_tempo_dias(dias):
        return f"{int(dias)} {'dia' if int(dias) == 1 else 'dias'}"
    
    def formatar_tempo_horas(horas):
        return f"{int(horas)} {'hora' if int(horas) == 1 else 'horas'}"
    
    df_display['Meses'] = df_display['Meses'].apply(formatar_tempo_meses)
    df_display['Dias'] = df_display['Dias'].apply(formatar_tempo_dias)
    df_display['Horas'] = df_display['Horas'].apply(formatar_tempo_horas)
    
    # Remover a coluna original de tempo médio em horas para não duplicar a informação
    df_display = df_display.drop(columns=['Tempo Médio (horas)'])
    
    # Exibir tabela
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Adicionar botão para download
    csv_buffer = io.StringIO()
    df_tempo_solicitacao.to_csv(csv_buffer, index=False)
    csv_str = csv_buffer.getvalue()
    
    st.download_button(
        label="📥 Baixar Dados em CSV",
        data=csv_str,
        file_name=f"tempo_solicitacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

def visualizar_metricas_certidoes(metricas):
    """
    Exibe as métricas de certidões agrupadas por categoria
    """
    if not metricas:
        st.warning("Não há dados disponíveis para visualização das métricas.")
        return
    
    st.markdown("""
    <h2 style="font-size: 2.2rem; font-weight: 800; color: #1A237E; text-align: center; 
    margin: 30px 0 20px 0; padding-bottom: 10px; border-bottom: 3px solid #1976D2;
    font-family: Arial, Helvetica, sans-serif;">
    RESUMO DE CERTIDÕES</h2>
    <p style="text-align: center; font-size: 16px; color: #555; margin-bottom: 25px; font-family: Arial, Helvetica, sans-serif;">
    Visão consolidada do status das certidões por categoria</p>
    """, unsafe_allow_html=True)
    
    # Layout em duas colunas para os cards
    col1, col2 = st.columns(2)
    
    # Cores para os cards de cada categoria
    cores = {
        "Solicitado - Aguardando Retorno": "#3F51B5",  # Azul
        "Pendência de Solicitação Comune - Parceiro": "#FF9800",  # Laranja
        "Pendência de Solicitação Comune - Empresa": "#F44336",  # Vermelho
        "Entregas": "#4CAF50"  # Verde
    }
    
    # Exibir métricas em cards com tabelas
    for i, (categoria, metrica) in enumerate(metricas.items()):
        # Alternar entre colunas
        col = col1 if i % 2 == 0 else col2
        
        with col:
            st.markdown(f"""
            <div style="background-color: white; 
                        padding: 15px; 
                        border-radius: 10px; 
                        margin-bottom: 20px;
                        border-top: 5px solid {cores.get(categoria, '#1976D2')};
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <h3 style="font-size: 18px; 
                           color: {cores.get(categoria, '#1976D2')}; 
                           margin-bottom: 15px;
                           text-align: center;
                           font-weight: bold;">
                    {categoria}
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Exibir tabela com os dados desta categoria
            df = metrica['dados']
            df_formatado = df.copy()
            
            # Exibir a tabela com os dados
            st.dataframe(
                df_formatado,
                column_config={
                    "STAGE_NAME": "Etapa",
                    "Certidões": st.column_config.NumberColumn(
                        "Certidões",
                        format="%d",
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Mostrar total na parte inferior
            st.markdown(f"""
            <div style="background-color: {cores.get(categoria, '#1976D2')}; 
                        color: white; 
                        padding: 10px; 
                        border-radius: 5px; 
                        margin-top: 5px;
                        text-align: center;
                        font-weight: bold;">
                Total: {metrica['total']} certidões
            </div>
            """, unsafe_allow_html=True)
    
    # Exibir total geral
    total_geral = sum(metrica['total'] for metrica in metricas.values())
    
    st.markdown(f"""
    <div style="background-color: #263238; 
                color: white; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 30px 0 15px 0;
                text-align: center;
                font-size: 20px;
                font-weight: bold;">
        Total Geral: {total_geral} certidões
    </div>
    """, unsafe_allow_html=True)

def visualizar_metricas_tempo_dias(metricas_tempo):
    """
    Exibe as métricas de tempo em dias agrupadas por faixas de tempo
    """
    if not metricas_tempo:
        st.warning("Não há dados disponíveis para visualização das métricas de tempo.")
        return
    
    st.markdown("""
    <h2 style="font-size: 2.2rem; font-weight: 800; color: #1A237E; text-align: center; 
    margin: 30px 0 20px 0; padding-bottom: 10px; border-bottom: 3px solid #1976D2;
    font-family: Arial, Helvetica, sans-serif;">
    CERTIDÕES POR TEMPO DE PROCESSAMENTO</h2>
    <p style="text-align: center; font-size: 16px; color: #555; margin-bottom: 25px; font-family: Arial, Helvetica, sans-serif;">
    Visão por faixas de tempo (em dias) baseado no campo MOVED_TIME</p>
    """, unsafe_allow_html=True)
    
    # Layout em duas colunas para os cards
    col1, col2 = st.columns(2)
    
    # Cores para os cards de cada categoria de tempo
    cores = {
        "Até 7 dias": "#4CAF50",          # Verde
        "8 a 15 dias": "#8BC34A",         # Verde claro
        "16 a 30 dias": "#FFEB3B",        # Amarelo
        "31 a 60 dias": "#FF9800",        # Laranja
        "Mais de 60 dias": "#F44336"      # Vermelho
    }
    
    # Exibir métricas em cards com tabelas
    for i, (categoria, metrica) in enumerate(metricas_tempo.items()):
        # Alternar entre colunas
        col = col1 if i % 2 == 0 else col2
        
        with col:
            st.markdown(f"""
            <div style="background-color: white; 
                        padding: 15px; 
                        border-radius: 10px; 
                        margin-bottom: 20px;
                        border-top: 5px solid {cores.get(categoria, '#1976D2')};
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <h3 style="font-size: 18px; 
                           color: {cores.get(categoria, '#1976D2')}; 
                           margin-bottom: 15px;
                           text-align: center;
                           font-weight: bold;">
                    {categoria}
                </h3>
                <p style="text-align: center; font-size: 14px; color: #666; margin-bottom: 10px;">
                    Tempo médio: {metrica['tempo_medio']} dias
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Exibir tabela com os dados desta categoria de tempo
            df = metrica['dados']
            
            if not df.empty:
                st.dataframe(
                    df,
                    column_config={
                        "STAGE_NAME": "Etapa",
                        "Certidões": st.column_config.NumberColumn(
                            "Certidões",
                            format="%d",
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info(f"Não há certidões na faixa de tempo: {categoria}")
            
            # Mostrar total na parte inferior
            st.markdown(f"""
            <div style="background-color: {cores.get(categoria, '#1976D2')}; 
                        color: white; 
                        padding: 10px; 
                        border-radius: 5px; 
                        margin-top: 5px;
                        text-align: center;
                        font-weight: bold;">
                Total: {metrica['total']} certidões
            </div>
            """, unsafe_allow_html=True)
    
    # Exibir total geral
    total_geral = sum(metrica['total'] for metrica in metricas_tempo.values())
    
    # Calcular o tempo médio geral ponderado
    soma_produto = sum(metrica['tempo_medio'] * metrica['total'] for metrica in metricas_tempo.values())
    tempo_medio_geral = round(soma_produto / total_geral, 1) if total_geral > 0 else 0
    
    st.markdown(f"""
    <div style="background-color: #263238; 
                color: white; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 30px 0 15px 0;
                text-align: center;
                font-size: 20px;
                font-weight: bold;">
        Total Geral: {total_geral} certidões | Tempo Médio: {tempo_medio_geral} dias
    </div>
    """, unsafe_allow_html=True)
    
    # Adicionar gráfico de distribuição
    if total_geral > 0:
        st.markdown("### Distribuição por Faixa de Tempo")
        
        # Preparar dados para o gráfico
        labels = list(metricas_tempo.keys())
        valores = [metrica['total'] for metrica in metricas_tempo.values()]
        cores_grafico = [cores.get(categoria, '#1976D2') for categoria in metricas_tempo.keys()]
        
        # Criar gráfico de barras
        fig = go.Figure(data=[
            go.Bar(
                x=labels,
                y=valores,
                marker_color=cores_grafico,
                text=valores,
                textposition='auto',
            )
        ])
        
        # Configurar layout
        fig.update_layout(
            title="Distribuição de Certidões por Tempo de Processamento",
            xaxis_title="Faixa de Tempo",
            yaxis_title="Número de Certidões",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(family="Arial, Helvetica, sans-serif")
        )
        
        # Exibir o gráfico
        st.plotly_chart(fig, use_container_width=True)

def visualizar_analise_evidencia(df_comune):
    """
    Exibe a análise de evidências e comprovantes para certidões italianas.
    Verifica se o comprovante foi validado e se a evidência foi anexada,
    e calcula o tempo desde a data de solicitação original.
    """
    st.markdown("""
    <h3 style="font-size: 26px; font-weight: 800; color: #1A237E; margin: 30px 0 15px 0; 
    padding-bottom: 8px; border-bottom: 2px solid #E0E0E0; font-family: Arial, Helvetica, sans-serif;">
    ANÁLISE DE EVIDÊNCIAS E COMPROVANTES</h3>
    """, unsafe_allow_html=True)
    
    if df_comune.empty:
        st.warning("Nenhum dado de COMUNE disponível para análise.")
        return

    # Colunas necessárias (verifique os IDs corretos no seu Bitrix)
    cols_necessarias = {
        'id_processo': 'ID', 
        'titulo': 'TITLE',
        'comprovante_validado_id': 'UF_CRM_12_1743013093', # Comprovante Validado (Sim/Não)
        'evidencia_anexo_id': 'UF_CRM_12_1743013064',      # Evidência Anexo (Arquivo)
        'provincia_id': 'UF_CRM_12_1743018869',        # Provincia (Usado na tabela detalhada)
        'comune_paroquia_id': 'UF_CRM_12_1722881735827', # Comune/Paróquia (Usado na tabela detalhada)
        'data_solicitacao_original': 'DATA_SOLICITACAO_ORIGINAL' # Data vinda do CSV
    }

    # Verificar colunas existentes
    cols_presentes_map = {k: v for k, v in cols_necessarias.items() if v in df_comune.columns}
    cols_faltantes = set(cols_necessarias.values()) - set(df_comune.columns)
    
    if cols_faltantes:
        st.warning(f"Colunas necessárias ausentes nos dados carregados: {', '.join(cols_faltantes)}. A análise pode estar incompleta.")
        # Verificar se colunas cruciais para métricas estão faltando
        metric_cols_needed = ['id_processo', 'comprovante_validado_id', 'evidencia_anexo_id']
        if not all(k in cols_presentes_map for k in metric_cols_needed):
            st.error("Faltam colunas essenciais (ID, Comprovante, Evidência) para calcular as métricas macro. Verifique os mapeamentos de campos.")
            # Ainda tentar mostrar a tabela se possível
        # Verificar se colunas cruciais para a tabela estão faltando
        table_cols_needed = ['id_processo', 'data_solicitacao_original']
        if not all(k in cols_presentes_map for k in table_cols_needed):
             st.error("Faltam colunas essenciais (ID, Data Solicitação) para a tabela detalhada. Verifique os mapeamentos de campos e o carregamento de dados.")
             return # Não podemos continuar sem ID e data

    # Selecionar e renomear colunas presentes
    df_analise = df_comune[[v for v in cols_presentes_map.values()]].copy()
    df_analise = df_analise.rename(columns={v: k for k, v in cols_presentes_map.items()})

    # --- Processamento das Colunas de Status (Comprovante e Evidência) --- 

    # 1. Comprovante Validado 
    if 'comprovante_validado_id' in df_analise.columns:
        df_analise['COMPROVANTE_VALIDADO'] = df_analise['comprovante_validado_id'].fillna('').astype(str).str.strip().str.lower().isin(['sim', 'y', '1']) # Ajuste '1' se for o ID da opção 'Sim'
        df_analise['Comprovante Validado?'] = np.where(df_analise['COMPROVANTE_VALIDADO'], 'Sim', 'Não')
    else:
        df_analise['Comprovante Validado?'] = 'N/A'
        df_analise['COMPROVANTE_VALIDADO'] = False # Default para cálculo

    # 2. Evidência Anexada (Arquivo)
    if 'evidencia_anexo_id' in df_analise.columns:
        df_analise['EVIDENCIA_ANEXADA'] = df_analise['evidencia_anexo_id'].fillna('').astype(str).str.strip().apply(lambda x: x not in ['', '[]', '{}', 'null', 'None', '0'])
        df_analise['Evidência Anexada?'] = np.where(df_analise['EVIDENCIA_ANEXADA'], 'Sim', 'Não')
    else:
        df_analise['Evidência Anexada?'] = 'N/A'
        df_analise['EVIDENCIA_ANEXADA'] = False # Default para cálculo

    # --- Cálculo e Exibição das Métricas Macro ---
    st.markdown("#### Resumo Geral")
    total_processos = len(df_analise)
    
    # Verificar se as colunas existem antes de calcular
    comprovante_sim = df_analise[df_analise['Comprovante Validado?'] == 'Sim'].shape[0] if 'Comprovante Validado?' in df_analise.columns else 0
    comprovante_nao = df_analise[df_analise['Comprovante Validado?'] == 'Não'].shape[0] if 'Comprovante Validado?' in df_analise.columns else 0
    
    evidencia_sim = df_analise[df_analise['Evidência Anexada?'] == 'Sim'].shape[0] if 'Evidência Anexada?' in df_analise.columns else 0
    evidencia_nao = df_analise[df_analise['Evidência Anexada?'] == 'Não'].shape[0] if 'Evidência Anexada?' in df_analise.columns else 0
    
    # Caso específico: Comprovante Sim E Evidência Não
    comp_sim_evid_nao = 0
    if 'COMPROVANTE_VALIDADO' in df_analise.columns and 'EVIDENCIA_ANEXADA' in df_analise.columns:
         comp_sim_evid_nao = df_analise[(df_analise['COMPROVANTE_VALIDADO'] == True) & (df_analise['EVIDENCIA_ANEXADA'] == False)].shape[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Processos", total_processos)
        st.metric("Comprovante Validado (Sim)", comprovante_sim)
        st.metric("Comprovante Validado (Não)", comprovante_nao)
        
    with col2:
        st.metric("Evidência Anexada (Sim)", evidencia_sim)
        st.metric("Evidência Anexada (Não)", evidencia_nao)
        
    with col3:
         st.metric("⚠️ Comprovante 'Sim' SEM Evidência Anexada", comp_sim_evid_nao)


    st.markdown("---") # Divisor

    # --- Processamento da Tabela Detalhada (continua como antes) ---

    # 3. Tempo desde Solicitação
    if 'data_solicitacao_original' in df_analise.columns:
        # Garantir que a coluna é datetime, tratando erros
        df_analise['data_solicitacao_original'] = pd.to_datetime(df_analise['data_solicitacao_original'], errors='coerce')
        
        # Calcular diferença em dias
        # Usar pd.Timestamp('now') para consistência com pandas
        hoje = pd.Timestamp('now')
        df_analise['TEMPO_SOLICITACAO_DIAS'] = (hoje - df_analise['data_solicitacao_original']).dt.days
        
        # Formatar para exibição (tratar NaT e valores negativos se a data for futura)
        def formatar_dias(dias):
            if pd.isna(dias):
                return "Data Inválida/Ausente"
            elif dias < 0:
                return "Data Futura?"
            else:
                return f"{int(dias)} dias"
                
        df_analise['Tempo Desde Solicitação'] = df_analise['TEMPO_SOLICITACAO_DIAS'].apply(formatar_dias)
    else:
        df_analise['Tempo Desde Solicitação'] = 'Data Ausente'
        df_analise['TEMPO_SOLICITACAO_DIAS'] = np.nan # Adicionar para possível ordenação futura

    # 4. Renomear colunas finais e selecionar ordem
    rename_final = {
        'id_processo': 'ID Processo',
        'titulo': 'Título Processo',
        'provincia_id': 'Província',
        'comune_paroquia_id': 'Comune/Paróquia',
        # As colunas 'Comprovante Validado?', 'Evidência Anexada?', 'Tempo Desde Solicitação' já foram criadas com os nomes desejados
    }
    # Renomear apenas as colunas que existem no df_analise
    df_display = df_analise.rename(columns={k: v for k, v in rename_final.items() if k in df_analise.columns})


    # Definir a ordem final das colunas para exibição
    cols_finais_ordem = [
        'ID Processo', 'Título Processo', 'Província', 'Comune/Paróquia',
        'Comprovante Validado?', 'Evidência Anexada?', 'Tempo Desde Solicitação'
    ]
    
    # Filtrar pelas colunas que realmente existem no df_display
    cols_exibicao_final = [col for col in cols_finais_ordem if col in df_display.columns]

    st.markdown("#### Detalhamento por Processo")
    st.info("Tabela abaixo mostra cada processo individualmente com o status das evidências e o tempo desde a solicitação original (baseado no arquivo CSV). Use os filtros das colunas para explorar.")
    
    # Exibir a tabela
    st.dataframe(df_display[cols_exibicao_final], use_container_width=True)

    # Adicionar opção de download
    csv = df_display[cols_exibicao_final].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar dados da análise em CSV",
        data=csv,
        file_name=f'analise_evidencia_comprovante_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv',
        key='download-evidencia-csv' # Adicionar chave única
    )
    
    # --- Futuras Melhorias --- 
    # st.subheader("Visão Agregada por Província/Comune (Exemplo)")
    # if all(c in df_display.columns for c in ['Província', 'Comune/Paróquia', 'Comprovante Validado?', 'Evidência Anexada?']):
    #     df_agregado = df_display.groupby(['Província', 'Comune/Paróquia']).agg(
    #         Total_Processos = ('ID Processo', 'count'),
    #         Comprovante_Sim = ('Comprovante Validado?', lambda x: (x == 'Sim').sum()),
    #         Evidencia_Sim = ('Evidência Anexada?', lambda x: (x == 'Sim').sum()),
    #         Tempo_Medio_Dias = ('TEMPO_SOLICITACAO_DIAS', 'mean')
    #     ).reset_index()
    #     df_agregado['Tempo_Medio_Dias'] = df_agregado['Tempo_Medio_Dias'].round(1)
    #     st.dataframe(df_agregado, use_container_width=True)
    # else:
    #     st.warning("Não foi possível gerar visão agregada por falta de colunas.")
        
    # Adicionar Mapa aqui se necessário no futuro

def visualizar_providencias(df_comune):
    """
    Exibe um mapa, métricas de correspondência e tabelas separadas agrupadas 
    por Província e por Comune/Paróquia.
    """
    st.markdown("""
    <h3 style="font-size: 26px; font-weight: 800; color: #1A237E; margin: 30px 0 15px 0; 
    padding-bottom: 8px; border-bottom: 2px solid #E0E0E0; font-family: Arial, Helvetica, sans-serif;">
    PROCESSOS POR LOCALIZAÇÃO</h3>
    """, unsafe_allow_html=True)

    if df_comune.empty:
        st.warning("Nenhum dado de COMUNE disponível para análise.")
        return

    # IDs das colunas
    col_provincia_orig = 'PROVINCIA_ORIG' # Nome original guardado no data_loader
    col_comune_orig = 'COMUNE_ORIG'       # Nome original guardado no data_loader
    col_provincia_norm = 'PROVINCIA_NORM' # Normalizado no data_loader
    col_comune_norm = 'COMUNE_NORM'       # Normalizado no data_loader
    col_id = 'ID'
    col_lat = 'latitude' 
    col_lon = 'longitude' 
    col_coord_source = 'COORD_SOURCE' # Coluna que indica a fonte do match

    # --- Mapa e Métricas de Coordenadas --- 
    st.markdown("#### Mapa e Correspondência de Coordenadas")
    
    # Verificar se as colunas de coordenadas existem
    if col_lat in df_comune.columns and col_lon in df_comune.columns:
        # Filtrar dados que possuem coordenadas válidas
        df_mapa = df_comune[[col_lat, col_lon]].dropna()
        pontos_no_mapa = len(df_mapa)
        total_processos = len(df_comune)
        percentual_mapeado = (pontos_no_mapa / total_processos * 100) if total_processos > 0 else 0
        
        # Calcular contagens por tipo de match
        count_exact = 0
        count_fuzzy = 0
        if col_coord_source in df_comune.columns:
            counts = df_comune[col_coord_source].value_counts()
            count_exact = counts.get('ExactMatch_ComuneProv', 0)
            count_fuzzy = counts.get('FuzzyMatch_Comune', 0)
        count_no_match = total_processos - count_exact - count_fuzzy

        # Exibir Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Processos", total_processos)
        with col2:
            st.metric("Processos Mapeados", pontos_no_mapa, f"{percentual_mapeado:.1f}%", delta_color="off")
        with col3:
            st.metric("Sem Coordenadas", count_no_match)

        st.markdown(f"*   **Match Exato (Comune+Província):** {count_exact}")
        st.markdown(f"*   **Match Fuzzy (Apenas Comune):** {count_fuzzy}")

        # Exibir Mapa
        if not df_mapa.empty:
            st.map(df_mapa, latitude=col_lat, longitude=col_lon, size=10)
        else:
            st.warning("Nenhum processo com coordenadas válidas encontrado para exibir no mapa.")
            
        # Tabela de Diagnóstico Expansível
        with st.expander("Ver Detalhes da Correspondência de Coordenadas"):
            cols_diagnostico = [
                col_id, 
                col_provincia_orig, 
                col_comune_orig, 
                col_provincia_norm, 
                col_comune_norm, 
                col_coord_source, 
                col_lat, 
                col_lon
            ]
            # Filtrar colunas que realmente existem
            cols_diagnostico_presentes = [c for c in cols_diagnostico if c in df_comune.columns]
            df_diag = df_comune[cols_diagnostico_presentes].copy()
            df_diag[col_coord_source] = df_diag[col_coord_source].fillna('No Match') # Preencher nulos na fonte
            st.dataframe(df_diag, use_container_width=True)
            
            # Download da tabela de diagnóstico
            csv_diag = df_diag.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Detalhes da Correspondência (CSV)",
                data=csv_diag,
                file_name=f'diagnostico_coordenadas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
                key='download-diag-coord-csv'
            )

    else:
        st.error(f"Colunas de coordenadas ('{col_lat}', '{col_lon}') não encontradas nos dados carregados.")

    st.markdown("---") # Divisor

    # --- Tabela por Província --- 
    st.markdown("#### Contagem por Província")
    st.info(
        "Nota: Processos em estágios como 'Entregue PDF', 'Pendente', "
        "'Pesquisa Não Finalizada' ou 'Devolutiva Emissor' podem não ter "
        "o campo Província preenchido. Estes casos, juntamente com outros sem preenchimento, "
        "são agrupados em 'nao especificado'."
    )
    if col_provincia_norm in df_comune.columns and col_id in df_comune.columns:
        # Agrupar usando a coluna normalizada
        df_prov_agrupado = df_comune.groupby(col_provincia_norm).agg(
            Quantidade_Processos=(col_id, 'count')
        ).reset_index()
        
        # Renomear e ordenar
        df_prov_agrupado = df_prov_agrupado.rename(columns={
            col_provincia_norm: 'Província (Normalizada)', # Ajustar nome da coluna
            'Quantidade_Processos': 'Nº de Processos'
        })
        df_prov_agrupado = df_prov_agrupado.sort_values(by='Nº de Processos', ascending=False)
        
        # Exibir tabela
        st.dataframe(df_prov_agrupado, use_container_width=True, hide_index=True)
        
        # Download
        csv_prov = df_prov_agrupado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Contagem por Província (CSV)",
            data=csv_prov,
            file_name=f'contagem_por_provincia_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
            key='download-provincia-count-csv'
        )
    else:
        st.warning(f"Não foi possível gerar a tabela por província. Colunas necessárias: {col_provincia_norm}, {col_id}")

    st.markdown("---") # Divisor

    # --- Tabela por Comune/Paróquia --- 
    st.markdown("#### Contagem por Comune/Paróquia")
    if col_comune_norm in df_comune.columns and col_id in df_comune.columns:
        # Agrupar usando a coluna normalizada
        df_com_agrupado = df_comune.groupby(col_comune_norm).agg(
            Quantidade_Processos=(col_id, 'count')
        ).reset_index()
        
        # Renomear e ordenar
        df_com_agrupado = df_com_agrupado.rename(columns={
            col_comune_norm: 'Comune/Paróquia (Normalizada)', # Ajustar nome da coluna
            'Quantidade_Processos': 'Nº de Processos'
        })
        df_com_agrupado = df_com_agrupado.sort_values(by='Nº de Processos', ascending=False)
        
        # Exibir tabela
        st.dataframe(df_com_agrupado, use_container_width=True, hide_index=True)
        
        # Download
        csv_com = df_com_agrupado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Contagem por Comune/Paróquia (CSV)",
            data=csv_com,
            file_name=f'contagem_por_comune_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
            key='download-comune-count-csv'
        )
    else:
        st.warning(f"Não foi possível gerar a tabela por comune/paróquia. Colunas necessárias: {col_comune_norm}, {col_id}")


# Funções auxiliares para formatação de tempo
def formatar_tempo_meses(meses):
    return f"{int(meses)} {'mês' if int(meses) == 1 else 'meses'}"

def formatar_tempo_dias(dias):
    return f"{int(dias)} {'dia' if int(dias) == 1 else 'dias'}"

def formatar_tempo_horas(horas):
    return f"{int(horas)} {'hora' if int(horas) == 1 else 'horas'}" 