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
        file_name=f"tempo_solicitacao_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
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
        "Entregas": "#4CAF50",  # Verde
        "Processos Cancelados/Inativos": "#E53935"  # Vermelho mais forte
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

    # Filtrar e excluir os estágios conforme solicitado
    estagios_excluidos = [
        "DT1052_22:UC_2QZ8S2",  # PENDENTE
        "DT1052_22:UC_E1VKYT",  # PESQUISA NÃO FINALIZADA
        "DT1052_22:UC_MVS02R",  # DEVOLUTIVA EMISSOR
        "DT1052_22:CLIENT",     # ENTREGUE PDF
        "DT1052_22:NEW",        # SOLICITAR
        "DT1052_22:FAIL",       # CANCELADO
        "DT1052_22:SUCCESS"     # DOCUMENTO FISICO ENTREGUE
    ]
    
    # Verificar se STAGE_ID existe no DataFrame
    if 'STAGE_ID' in df_comune.columns:
        # Filtrar o DataFrame excluindo os estágios mencionados
        df_filtrado = df_comune[~df_comune['STAGE_ID'].isin(estagios_excluidos)].copy()
        # Mostrar aviso sobre os registros filtrados
        registros_excluidos = len(df_comune) - len(df_filtrado)
        if registros_excluidos > 0:
            st.info(f"Foram excluídos {registros_excluidos} registros dos estágios: PENDENTE, PESQUISA NÃO FINALIZADA, DEVOLUTIVA EMISSOR, ENTREGUE PDF, SOLICITAR, CANCELADO e DOCUMENTO FISICO ENTREGUE.")
    else:
        df_filtrado = df_comune.copy()
        st.warning("Coluna STAGE_ID não encontrada. Não foi possível aplicar o filtro de estágios.")

    # Colunas necessárias (verifique os IDs corretos no seu Bitrix)
    cols_necessarias = {
        'id_processo': 'ID', 
        'titulo': 'TITLE',
        'comprovante_validado_id': 'UF_CRM_12_1743013093', # Comprovante Validado (Sim/Não)
        'evidencia_anexo_id': 'UF_CRM_12_1743013064',      # Evidência Anexo (Arquivo)
        'provincia_id': 'UF_CRM_12_1743018869',        # Província 
        'comune_paroquia_id': 'UF_CRM_12_1722881735827', # Comune/Paróquia
        'data_solicitacao_original': 'DATA_SOLICITACAO_ORIGINAL', # Data
        'stage_name': 'STAGE_NAME',  # Nome do estágio
        'data_alteracao': 'DATE_MODIFY',  # Data da última alteração
    }

    # Verificar colunas existentes
    cols_presentes_map = {k: v for k, v in cols_necessarias.items() if v in df_filtrado.columns}
    
    # Verificar se colunas essenciais estão presentes
    if 'id_processo' not in cols_presentes_map or 'evidencia_anexo_id' not in cols_presentes_map:
        st.error("Colunas essenciais (ID, Evidência Anexada) não encontradas. Verifique os mapeamentos de campos.")
        return

    # Selecionar e renomear colunas presentes
    df_analise = df_filtrado[[v for v in cols_presentes_map.values()]].copy()
    df_analise = df_analise.rename(columns={v: k for k, v in cols_presentes_map.items()})

    # --- Processamento das Colunas de Status (Comprovante e Evidência) --- 

    # 1. Comprovante Validado 
    if 'comprovante_validado_id' in df_analise.columns:
        df_analise['COMPROVANTE_VALIDADO'] = df_analise['comprovante_validado_id'].astype(str).str.lower().isin(['sim', 'yes', 'true', '1', 's', 'y', 't'])
        df_analise['Comprovante Validado?'] = df_analise['COMPROVANTE_VALIDADO'].map({True: 'Sim', False: 'Não'})
    else:
        df_analise['Comprovante Validado?'] = 'N/A'
        df_analise['COMPROVANTE_VALIDADO'] = False # Default para cálculo

    # 2. Evidência Anexada (Arquivo)
    if 'evidencia_anexo_id' in df_analise.columns:
        # Verifica se tem um valor válido no campo de evidência
        df_analise['EVIDENCIA_ANEXADA'] = df_analise['evidencia_anexo_id'].notna() & (~df_analise['evidencia_anexo_id'].astype(str).isin(['', '[]', '{}', 'null', 'None', '0', 'nan']))
        df_analise['Evidência Anexada?'] = df_analise['EVIDENCIA_ANEXADA'].map({True: 'Sim', False: 'Não'})
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
    df_comp_sim_evid_nao = pd.DataFrame()
    if 'COMPROVANTE_VALIDADO' in df_analise.columns and 'EVIDENCIA_ANEXADA' in df_analise.columns:
        df_comp_sim_evid_nao = df_analise[(df_analise['COMPROVANTE_VALIDADO'] == True) & (df_analise['EVIDENCIA_ANEXADA'] == False)].copy()
        comp_sim_evid_nao = len(df_comp_sim_evid_nao)
    
    # Novo caso específico: Comprovante Não E Evidência Sim
    comp_nao_evid_sim = 0
    df_comp_nao_evid_sim = pd.DataFrame()
    if 'COMPROVANTE_VALIDADO' in df_analise.columns and 'EVIDENCIA_ANEXADA' in df_analise.columns:
        df_comp_nao_evid_sim = df_analise[(df_analise['COMPROVANTE_VALIDADO'] == False) & (df_analise['EVIDENCIA_ANEXADA'] == True)].copy()
        comp_nao_evid_sim = len(df_comp_nao_evid_sim)
        
    # Novo caso específico: Evidência Não (independente do comprovante)
    df_sem_evidencia = pd.DataFrame()
    if 'EVIDENCIA_ANEXADA' in df_analise.columns:
        df_sem_evidencia = df_analise[df_analise['EVIDENCIA_ANEXADA'] == False].copy()
        evidencia_nao = len(df_sem_evidencia)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Processos", total_processos)
        st.metric("Comprovante Validado (Sim)", comprovante_sim)
        st.metric("Comprovante Validado (Não)", comprovante_nao)
        
    with col2:
        st.metric("Evidência Anexada (Sim)", evidencia_sim)
        st.metric("Evidência Anexada (Não)", evidencia_nao)
        
    with col3:
        metric_container = st.container()
        metric_container.metric("⚠️ Comprovante 'Sim' SEM Evidência Anexada", comp_sim_evid_nao)
        metric_container.metric("⚠️ Comprovante 'Não' COM Evidência Anexada", comp_nao_evid_sim)
    
    # --- Continuar com expanders originais ---
    st.markdown("---") # Divisor
    
    # Adicionar expander com detalhes dos registros com problema (Comprovante Sim SEM Evidência)
    if comp_sim_evid_nao > 0:
        with st.expander("Detalhamento dos registros com Comprovante 'Sim' SEM Evidência Anexada", expanded=False):
            st.markdown("""
            <div style="background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #f44336;">
            <h4 style="color: #b71c1c; margin-top: 0;">Atenção: Registros Incompletos</h4>
            <p style="margin-bottom: 5px;">Os registros abaixo possuem o campo <strong>Comprovante Validado</strong> marcado como <strong>Sim</strong>, 
            porém não têm <strong>Evidência Anexada</strong>. Isso pode indicar:</p>
            <ul style="margin-bottom: 0;">
            <li>Falha no procedimento de anexar a evidência</li>
            <li>Erro de preenchimento do campo "Comprovante Validado"</li>
            <li>Possíveis documentos perdidos ou não escaneados</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Selecionar colunas relevantes para exibição na tabela
            colunas_tabela = ['id_processo', 'titulo', 'provincia_id', 'comune_paroquia_id', 'Comprovante Validado?', 'Evidência Anexada?', 'data_solicitacao_original', 'stage_name']
            colunas_tabela_presentes = [col for col in colunas_tabela if col in df_comp_sim_evid_nao.columns]
            
            # Exibir tabela com os dados
            st.dataframe(df_comp_sim_evid_nao[colunas_tabela_presentes], use_container_width=True)

            # Adicionar opção de download
            csv = df_comp_sim_evid_nao[colunas_tabela_presentes].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name=f'comprovantes_sem_evidencia_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
                key='download-comp-sem-evid-csv',
                use_container_width=False
            )
    
    # Adicionar expander com detalhes dos registros com problema (Comprovante Não COM Evidência)
    if comp_nao_evid_sim > 0:
        with st.expander("Detalhamento dos registros com Comprovante 'Não' COM Evidência Anexada", expanded=False):
            st.markdown("""
            <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #43a047;">
            <h4 style="color: #1b5e20; margin-top: 0;">Atenção: Registros para Validação</h4>
            <p style="margin-bottom: 5px;">Os registros abaixo possuem <strong>Evidência Anexada</strong> mas o campo <strong>Comprovante Validado</strong> está marcado como <strong>Não</strong>. Isso pode indicar:</p>
            <ul style="margin-bottom: 0;">
            <li>Evidência anexada aguardando validação</li>
            <li>Esquecimento de atualizar o status do comprovante após anexar evidência</li>
            <li>Evidência anexada que precisa ser revisada</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Selecionar colunas relevantes para exibição na tabela
            colunas_tabela = ['id_processo', 'titulo', 'provincia_id', 'comune_paroquia_id', 'Comprovante Validado?', 'Evidência Anexada?', 'data_solicitacao_original', 'stage_name']
            colunas_tabela_presentes = [col for col in colunas_tabela if col in df_comp_nao_evid_sim.columns]
            
            # Exibir tabela com os dados
            st.dataframe(df_comp_nao_evid_sim[colunas_tabela_presentes], use_container_width=True)

            # Adicionar opção de download
            csv = df_comp_nao_evid_sim[colunas_tabela_presentes].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name=f'comprovantes_nao_com_evidencia_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
                key='download-comp-nao-com-evid-csv',
                use_container_width=False
            )

    # --- Processamento da Tabela Detalhada ---

    # 3. Tempo desde Solicitação
    if 'data_solicitacao_original' in df_analise.columns:
        # Garantir que a coluna é datetime, tratando erros
        df_analise['data_solicitacao_original'] = pd.to_datetime(df_analise['data_solicitacao_original'], errors='coerce')
        
        # Calcular diferença em dias
        # Usar pd.Timestamp('now') para consistência com pandas
        hoje = pd.Timestamp('now')
        df_analise['TEMPO_SOLICITACAO_DIAS'] = (hoje - df_analise['data_solicitacao_original']).dt.days
        
        # Formatar para exibição (tratar NaT e valores negativos)
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
        'stage_name': 'Estágio do Processo'
        # As colunas 'Comprovante Validado?', 'Evidência Anexada?', 'Tempo Desde Solicitação' já foram criadas com os nomes desejados
    }
    # Renomear apenas as colunas que existem no df_analise
    df_display = df_analise.rename(columns={k: v for k, v in rename_final.items() if k in df_analise.columns})


    # Definir a ordem final das colunas para exibição
    cols_finais_ordem = [
        'ID Processo', 'Título Processo', 'Província', 'Comune/Paróquia', 'Estágio do Processo',
        'Comprovante Validado?', 'Evidência Anexada?', 'Tempo Desde Solicitação'
    ]
    
    # Filtrar pelas colunas que realmente existem no df_display
    cols_exibicao_final = [col for col in cols_finais_ordem if col in df_display.columns]

    st.markdown("#### Detalhamento Completo por Processo")
    st.info("Tabela abaixo mostra todos os processos com status de evidências e tempo desde a solicitação original. Use os filtros das colunas para explorar.")
    
    # Exibir a tabela
    st.dataframe(df_display[cols_exibicao_final], use_container_width=True)

    # Adicionar opção de download
    csv = df_display[cols_exibicao_final].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar dados completos da análise em CSV",
        data=csv,
        file_name=f'analise_evidencia_comprovante_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv',
        key='download-evidencia-csv' # Adicionar chave única
    )
    
    # NOVA SEÇÃO: Detalhe expandido dos processos sem comprovante anexado (MOVIDO PARA O FINAL)    
    st.markdown("---") # Divisor adicional para separar
    st.markdown("#### Evidência Anexada (Não)")
    
    if 'EVIDENCIA_ANEXADA' in df_analise.columns:
        # Extrair apenas os registros sem evidência anexada
        df_sem_evidencia = df_analise[df_analise['EVIDENCIA_ANEXADA'] == False].copy()
        
        # Verificar se há registros
        if not df_sem_evidencia.empty:
            # Exibir alerta sobre os registros sem evidência
            st.markdown("""
            <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #f44336;">
            <h4 style="color: #b71c1c; margin-top: 0;">Alerta: Comprovantes sem Evidências Anexadas</h4>
            <p style="margin-bottom: 5px;">Os processos abaixo não possuem evidências anexadas. Estes documentos precisam ser verificados com prioridade.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Selecionar colunas para exibição na tabela expandida
            colunas_exibir = ['id_processo', 'titulo', 'Comprovante Validado?', 'stage_name', 'provincia_id', 'comune_paroquia_id']
            colunas_presentes = [col for col in colunas_exibir if col in df_sem_evidencia.columns]
            
            # Ordenar por ID para facilitar a visualização
            df_sem_evidencia_exibir = df_sem_evidencia.sort_values(by='id_processo')[colunas_presentes].copy()
            
            # Renomear colunas para melhor exibição
            colunas_renomear = {
                'id_processo': 'ID',
                'titulo': 'Título do Processo', 
                'stage_name': 'Estágio',
                'provincia_id': 'Província',
                'comune_paroquia_id': 'Comune'
            }
            df_sem_evidencia_exibir = df_sem_evidencia_exibir.rename(columns={k: v for k, v in colunas_renomear.items() if k in df_sem_evidencia_exibir.columns})
            
            # Exibir a tabela com os IDs expandidos
            with st.expander("Evidência Anexada (Não) - Expandir IDs Detalhados", expanded=True):
                # Adicionar filtros interativos
                cols = st.columns(3)
                
                # Verificar e criar filtros para colunas disponíveis
                if 'Estágio' in df_sem_evidencia_exibir.columns:
                    with cols[0]:
                        estagios = ['Todos'] + sorted(df_sem_evidencia_exibir['Estágio'].dropna().unique().tolist())
                        estagio_filtro = st.selectbox('Filtrar por Estágio:', estagios)
                
                if 'Província' in df_sem_evidencia_exibir.columns:
                    with cols[1]:
                        provincias = ['Todas'] + sorted(df_sem_evidencia_exibir['Província'].dropna().astype(str).unique().tolist())
                        provincia_filtro = st.selectbox('Filtrar por Província:', provincias)
                
                with cols[2]:
                    busca = st.text_input('Buscar por texto:', placeholder='Digite para filtrar...')
                
                # Aplicar filtros
                df_filtrado = df_sem_evidencia_exibir.copy()
                
                if 'Estágio' in df_sem_evidencia_exibir.columns and estagio_filtro != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['Estágio'] == estagio_filtro]
                
                if 'Província' in df_sem_evidencia_exibir.columns and provincia_filtro != 'Todas':
                    df_filtrado = df_filtrado[df_filtrado['Província'].astype(str) == provincia_filtro]
                
                if busca:
                    # Aplicar filtro de texto em todas as colunas que são do tipo string
                    mask = pd.Series(False, index=df_filtrado.index)
                    for col in df_filtrado.columns:
                        if df_filtrado[col].dtype == 'object':  # Se for texto
                            mask = mask | df_filtrado[col].astype(str).str.contains(busca, case=False, na=False)
                    df_filtrado = df_filtrado[mask]
                
                # Mostrar contador de resultados
                st.write(f"Exibindo {len(df_filtrado)} de {len(df_sem_evidencia_exibir)} registros sem evidência anexada")
                
                # Exibir tabela com resultados filtrados
                st.dataframe(df_filtrado, use_container_width=True, height=400)
                
                # Adicionar botão de download
                csv = df_filtrado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar lista sem evidência anexada",
                    data=csv,
                    file_name=f'registros_sem_evidencia_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    mime='text/csv',
                    key='download-sem-evidencia-csv'
                )
        else:
            st.success("Parabéns! Todos os processos possuem evidências anexadas.")
    else:
        st.warning("Não foi possível verificar evidências anexadas. Campo não encontrado nos dados.")

def visualizar_providencias(df_comune):
    """
    Exibe um mapa, métricas de correspondência e tabelas separadas agrupadas 
    por Província e por Comune/Paróquia, com algoritmo de geocodificação aprimorado.
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
        # Backup dos dados originais antes de aplicar melhorias
        df_original = df_comune.copy()
        
        # --- NOVO: Aplicar algoritmo de correspondência aprimorado ---
        try:
            from thefuzz import process, fuzz
            # Instale as bibliotecas necessárias
            try:
                import folium
                from streamlit_folium import folium_static
            except ImportError:
                st.warning("Para visualização aprimorada de mapas, instale: pip install folium streamlit-folium")
                
            # Carregar dados geográficos de referência (usando o mesmo procedimento do data_loader)
            import os
            import json
            
            # Dicionário de correções manuais para casos específicos (pode ser expandido)
            correcoes_manuais = {
                # Comune: (latitude, longitude, fonte)
                "piavon": (45.7167, 12.4333, "Correção Manual"),
                "vazzola": (45.8333, 12.3333, "Correção Manual"),
                "oderzo": (45.7833, 12.4833, "Correção Manual"),
                "valdobbiadene": (45.9000, 12.0333, "Correção Manual"),
                "motta di livenza": (45.7833, 12.6167, "Correção Manual"),
                "susegana": (45.8500, 12.2500, "Correção Manual"),
                "vittorio veneto": (45.9833, 12.3000, "Correção Manual"),
                "boara polesine": (45.0333, 11.7833, "Correção Manual"),
                "mansuè": (45.8333, 12.5167, "Correção Manual"),
                "san dona di piave": (45.6333, 12.5667, "Correção Manual"),
                "godego": (45.7000, 11.8667, "Correção Manual"),
                "castello di godego": (45.7000, 11.8667, "Correção Manual"),
                "legnago": (45.1833, 11.3167, "Correção Manual"),
                "stienta": (44.9500, 11.5500, "Correção Manual"),
                "montebelluna": (45.7833, 12.0500, "Correção Manual"),
                "vigasio": (45.3167, 10.9333, "Correção Manual"),
                "villorba": (45.7333, 12.2333, "Correção Manual"),
                "bondeno": (44.8833, 11.4167, "Correção Manual"),
                "trevignano": (45.7333, 12.1000, "Correção Manual"),
                "cavarzere": (45.1333, 12.0667, "Correção Manual"),
                "arcade": (45.7333, 12.2000, "Correção Manual"),
                "castelfranco veneto": (45.6667, 11.9333, "Correção Manual"),
                "gaiarine": (45.9000, 12.4833, "Correção Manual"),
                "borso del grappa": (45.8167, 11.8000, "Correção Manual"),
                "cittadella": (45.6500, 11.7833, "Correção Manual"),
                "albignasego": (45.3667, 11.8500, "Correção Manual"),
                "zero branco": (45.6167, 12.1667, "Correção Manual"),
                "sona": (45.4333, 10.8333, "Correção Manual"),
                "lendinara": (45.0833, 11.5833, "Correção Manual"),
            }
            
            # Adicionar correções de províncias típicas italianas
            provincias_manuais = {
                "treviso": (45.6667, 12.2500, "Correção Província"),
                "venezia": (45.4375, 12.3358, "Correção Província"),
                "padova": (45.4167, 11.8667, "Correção Província"),
                "verona": (45.4386, 10.9928, "Correção Província"),
                "vicenza": (45.5500, 11.5500, "Correção Província"),
                "rovigo": (45.0667, 11.7833, "Correção Província"),
                "mantova": (45.1500, 10.7833, "Correção Província"),
                "belluno": (46.1333, 12.2167, "Correção Província"),
                "pordenone": (45.9667, 12.6500, "Correção Província"),
                "udine": (46.0667, 13.2333, "Correção Província"),
                "cremona": (45.1333, 10.0333, "Correção Província"),
                "brescia": (45.5417, 10.2167, "Correção Província"),
                "bergamo": (45.6950, 9.6700, "Correção Província"),
                "milano": (45.4669, 9.1900, "Correção Província"),
                "cosenza": (39.3000, 16.2500, "Correção Província"),
                "salerno": (40.6806, 14.7594, "Correção Província"),
                "caserta": (41.0667, 14.3333, "Correção Província"),
                "napoli": (40.8333, 14.2500, "Correção Província"),
                "potenza": (40.6333, 15.8000, "Correção Província"),
                "ferrara": (44.8333, 11.6167, "Correção Província"),
                "bologna": (44.4939, 11.3428, "Correção Província"),
                "lucca": (43.8428, 10.5039, "Correção Província"),
                "roma": (41.9000, 12.5000, "Correção Província"),
                "benevento": (41.1333, 14.7833, "Correção Província"),
                "campobasso": (41.5667, 14.6667, "Correção Província"),
                "cagliari": (39.2278, 9.1111, "Correção Província"),
                "messina": (38.1936, 15.5542, "Correção Província"),
                "catanzaro": (38.9000, 16.6000, "Correção Província"),
                "palermo": (38.1111, 13.3517, "Correção Província"),
            }
            
            df_mapa_ref = None
            
            # Tentar carregar o arquivo de referência geográfica existente
            script_dir = os.path.dirname(__file__)
            json_path = os.path.join(script_dir, 'Mapa', 'mapa_italia.json')
            
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data_json = json.load(f)
                df_mapa_ref = pd.DataFrame(data_json)
                
                # Verificar e processar colunas
                if 'city' in df_mapa_ref.columns and 'admin_name' in df_mapa_ref.columns and 'lat' in df_mapa_ref.columns and 'lng' in df_mapa_ref.columns:
                    # Renomear colunas para clareza
                    df_mapa_ref = df_mapa_ref.rename(columns={
                        'city': 'comune',
                        'admin_name': 'provincia',
                        'lat': 'lat',
                        'lng': 'lng'
                    })
                    
                    # Criar versões normalizadas para matching
                    df_mapa_ref['comune_norm'] = df_mapa_ref['comune'].astype(str).str.lower()
                    df_mapa_ref['provincia_norm'] = df_mapa_ref['provincia'].astype(str).str.lower()
                    
                    # Remover acentos e caracteres especiais
                    import unicodedata
                    import re
                    
                    def normalizar_texto(texto):
                        if not isinstance(texto, str):
                            return ""
                        # Converter para lowercase
                        texto = texto.lower()
                        # Remover acentos
                        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
                        # Remover caracteres especiais
                        texto = re.sub(r'[^\w\s]', '', texto)
                        # Remover prefixos comuns
                        prefixos = [
                            'comune di ', 'provincia di ', 'san ', 'santa ', 'santo ', 's ', 'ss ', 
                            'parrocchia di ', 'parrocchia ', 'chiesa di ', 'chiesa ', 'natti', 'matri'
                        ]
                        for prefixo in prefixos:
                            if texto.startswith(prefixo):
                                texto = texto[len(prefixo):]
                        # Remover sufixos comuns
                        sufixos = [
                            ' ve', ' tv', ' pd', ' vr', ' vi', ' ro', ' mn', ' bl', ' pn', ' ud', 
                            ' cr', ' bs', ' bg', ' mi', ' cs', ' sa', ' ce', ' na', ' pz', ' fe', 
                            ' bo', ' lu', ' rm', ' bn', ' cb', ' ca', ' me', ' cz', ' pa'
                        ]
                        for sufixo in sufixos:
                            if texto.endswith(sufixo):
                                texto = texto[:-len(sufixo)]
                        return texto.strip()
                    
                    df_mapa_ref['comune_norm'] = df_mapa_ref['comune_norm'].apply(normalizar_texto)
                    df_mapa_ref['provincia_norm'] = df_mapa_ref['provincia_norm'].apply(normalizar_texto)
                    
                    st.success(f"Carregadas {len(df_mapa_ref)} referências geográficas italianas.")
                else:
                    st.warning("Arquivo de referência não possui as colunas necessárias.")
                    df_mapa_ref = None
            except Exception as e:
                st.warning(f"Não foi possível carregar o arquivo de referência: {e}")
                df_mapa_ref = None
            
            # ---- IMPLEMENTAR ALGORITMO DE MATCHING AVANÇADO ----
            if df_mapa_ref is not None:
                with st.spinner("Aplicando algoritmo de geocodificação avançado..."):
                    # Criar função de normalização de nomes para o dataframe atual
                    def normalizar_nome_para_match(nome):
                        if not isinstance(nome, str):
                            return ""
                        # Normalizar: lowercase, remover acentos, remover caracteres especiais
                        nome = nome.lower()
                        # Remover acentos
                        nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
                        # Remover caracteres especiais e símbolos
                        nome = re.sub(r'[^\w\s]', '', nome)
                        # Remover prefixos comuns italianos
                        prefixos = [
                            'comune di ', 'provincia di ', 'chiesa di ', 'chiesa parrocchiale di ',
                            'parrocchia di ', 'parrocchia ', 'paroquia ', 'diocesi di ', 'diocesi ',
                            'san ', 'santa ', 'santo ', 's ', 'ss ', 'st ', 'nativita ', 'santangelo ',
                            'santambrogio ', 'frazione ', 'comune ', 'citta di ', 'beato ', 'beata '
                        ]
                        for prefixo in prefixos:
                            if nome.startswith(prefixo):
                                nome = nome[len(prefixo):]
                                
                        # Remover sufixos comuns como códigos de província italianos
                        sufixos = [
                            ' ve', ' tv', ' pd', ' vr', ' vi', ' ro', ' mn', ' bl', ' pn', ' ud', 
                            ' cr', ' bs', ' bg', ' mi', ' cs', ' sa', ' ce', ' na', ' pz', ' fe', 
                            ' bo', ' lu', ' rm', ' bn', ' cb', ' ca', ' me', ' cz', ' pa', ' to',
                            ' ar', ' fg', ' ch', ' en', ' ag', ' ct', ' tp', ' mc', ' ta',
                            ' veneto', ' italia', ' al', ' ap', ' ao', ' at', ' bz', ' fm', ' fr',
                            ' ge', ' go', ' im', ' aq', ' le', ' lt', ' mb', ' no', ' nu',
                            ' or', ' pc', ' pe', ' pg', ' pi', ' pn', ' po', ' pt', ' pu',
                            ' ra', ' rc', ' re', ' ri', ' rn', ' si', ' so', ' sp', ' sr',
                            ' ss', ' sv', ' te', ' tn', ' tp', ' ts', ' va', ' vb', ' vc',
                            ' vs', ' vt'
                        ]
                        for sufixo in sufixos:
                            if nome.endswith(sufixo):
                                nome = nome[:-len(sufixo)]
                                
                        # Tratar casos específicos comuns na Itália
                        substituicoes = {
                            'monte s ': 'monte san ',
                            'sangiovanni': 'san giovanni',
                            'sanmartino': 'san martino',
                            'sanpietro': 'san pietro',
                            'santangelo': 'san angelo',
                            'santantonio': 'san antonio',
                            'santamaria': 'santa maria',
                            'vescov': 'vescovo',
                            'battist': 'battista',
                            'evangelist': 'evangelista',
                            'maggior': 'maggiore',
                            'martir': 'martire',
                            'dadig': 'd adige',
                            'delladig': 'dell adige',
                            'delgrapp': 'del grappa',
                            'deltagliament': 'del tagliamento',
                            'apostol': 'apostolo',
                            'vergine mari': 'vergine maria',
                            ' ve': '',
                            ' tv': '',
                            ' pd': '',
                            ' vr': '',
                            ' vi': '',
                            ' ro': '',
                            ' mn': '',
                            ' bl': '',
                            ' pn': '',
                            ' ud': ''
                        }
                        for velho, novo in substituicoes.items():
                            nome = nome.replace(velho, novo)
                            
                        # Remover palavras que não ajudam no matching
                        palavras_remover = [
                            'chiesa', 'parrocchia', 'parrocchiale', 'paroquia', 'comune', 'provincia',
                            'diocesi', 'frazione', 'nativita', 'annunciazione', 'assunzione', 'abate',
                            'apostolo', 'dottore', 'martire', 'sacerdote', 'vescovo', 'beata', 'beato',
                            'vergine', 'evangelista', 'maria', 'santissima', 'ssma', 'padre', 'madre'
                        ]
                        
                        nome_partes = nome.split()
                        nome_partes = [parte for parte in nome_partes if parte not in palavras_remover]
                        nome = ' '.join(nome_partes)
                        
                        return nome.strip()
                    
                    # Aplicar normalização adicional para melhorar matching
                    df_comune['comune_match'] = df_comune[col_comune_orig].apply(normalizar_nome_para_match)
                    df_comune['provincia_match'] = df_comune[col_provincia_orig].apply(normalizar_nome_para_match)
                    
                    # 0. APLICAR CORREÇÕES MANUAIS
                    registros_atualizados = 0
                    
                    for idx, row in df_comune.iterrows():
                        # Pular se já tem coordenadas
                        if pd.notna(row[col_lat]) and pd.notna(row[col_lon]):
                            continue
                            
                        # Verificar nome do comune nas correções manuais
                        comune_match = row['comune_match']
                        if comune_match in correcoes_manuais:
                            lat, lon, source = correcoes_manuais[comune_match]
                            df_comune.at[idx, col_lat] = lat
                            df_comune.at[idx, col_lon] = lon
                            df_comune.at[idx, col_coord_source] = source
                            registros_atualizados += 1
                            continue
                            
                        # Verificar província se o comune não foi encontrado
                        provincia_match = row['provincia_match']
                        if (pd.isna(row[col_lat]) or pd.isna(row[col_lon])) and provincia_match in provincias_manuais:
                            lat, lon, source = provincias_manuais[provincia_match]
                            df_comune.at[idx, col_lat] = lat
                            df_comune.at[idx, col_lon] = lon
                            df_comune.at[idx, col_coord_source] = source
                            registros_atualizados += 1
                    
                    print(f"Aplicadas {registros_atualizados} correções manuais")

                    # 1. MATCHING EXATO (Comune + Província)
                    df_mapa_exact = df_mapa_ref.copy()
                    df_comune_sem_coord = df_comune[df_comune[col_lat].isna() | df_comune[col_lon].isna()].copy()
                    
                    # Função para encontrar correspondências exatas
                    def encontrar_match_exato(row):
                        # Se já tem coordenadas, não precisa de matching
                        if pd.notna(row[col_lat]) and pd.notna(row[col_lon]):
                            return row
                        
                        # Tentar correspondência exata (Comune + Província)
                        mask_exact = (df_mapa_exact['comune_norm'] == row['comune_match']) & (df_mapa_exact['provincia_norm'] == row['provincia_match'])
                        if mask_exact.any():
                            match_row = df_mapa_exact[mask_exact].iloc[0]
                            row[col_lat] = match_row['lat']
                            row[col_lon] = match_row['lng']
                            row[col_coord_source] = 'ExactMatch_ComuneProv'
                        return row
                    
                    # Aplicar correspondência exata
                    df_comune_matched = df_comune_sem_coord.apply(encontrar_match_exato, axis=1)
                    
                    # Atualizar o dataframe original com as correspondências exatas
                    df_comune.update(df_comune_matched)
                    
                    # 2. MATCHING FUZZY AVANÇADO (múltiplos algoritmos e critérios)
                    df_sem_coord_apos_exato = df_comune[df_comune[col_lat].isna() | df_comune[col_lon].isna()].copy()
                    
                    # Obter comunes únicos sem correspondência
                    comunes_sem_match = df_sem_coord_apos_exato['comune_match'].dropna().unique()
                    
                    # Dicionário para armazenar resultados de matching
                    matches_fuzzy = {}
                    
                    # Lista de comunes de referência para matching
                    ref_comunes = df_mapa_ref['comune_norm'].unique().tolist()
                    
                    # Aplicar múltiplos algoritmos de matching com threshold reduzido
                    for comune in comunes_sem_match:
                        if not comune or comune == 'nao especificado':
                            continue
                        
                        # Verificar se o nome tem pelo menos 3 caracteres para evitar falsos positivos
                        if len(comune) < 3:
                            continue
                        
                        # Combinar diferentes métricas para um matching mais robusto
                        best_matches = []
                        
                        # 1. Token Sort Ratio (melhor para palavras na ordem errada)
                        token_sort_matches = process.extractBests(
                            comune, 
                            ref_comunes,
                            scorer=fuzz.token_sort_ratio,
                            score_cutoff=70,  # Threshold mais baixo para aumentar matches
                            limit=3
                        )
                        if token_sort_matches:
                            best_matches.extend(token_sort_matches)
                        
                        # 2. Token Set Ratio (melhor para palavras parciais)
                        token_set_matches = process.extractBests(
                            comune, 
                            ref_comunes,
                            scorer=fuzz.token_set_ratio,
                            score_cutoff=75,
                            limit=3
                        )
                        if token_set_matches:
                            best_matches.extend(token_set_matches)
                        
                        # 3. Partial Ratio (melhor para substrings)
                        partial_matches = process.extractBests(
                            comune, 
                            ref_comunes,
                            scorer=fuzz.partial_ratio,
                            score_cutoff=80,
                            limit=3
                        )
                        if partial_matches:
                            best_matches.extend(partial_matches)
                            
                        # 4. Ratio básico (distância de Levenshtein)
                        ratio_matches = process.extractBests(
                            comune, 
                            ref_comunes,
                            scorer=fuzz.ratio,
                            score_cutoff=75,
                            limit=3
                        )
                        if ratio_matches:
                            best_matches.extend(ratio_matches)
                            
                        # Caso especial para nomes muito curtos, ser mais flexível
                        if len(comune) <= 5 and not best_matches:
                            special_matches = process.extractBests(
                                comune, 
                                ref_comunes,
                                scorer=fuzz.ratio,
                                score_cutoff=65,  # Threshold ainda mais baixo para nomes curtos
                                limit=2
                            )
                            if special_matches:
                                best_matches.extend(special_matches)
                            
                        # Consolidar e escolher o melhor match
                        if best_matches:
                            # Agrupar por nome do match
                            match_scores = {}
                            for match, score in best_matches:
                                if match in match_scores:
                                    match_scores[match] = max(match_scores[match], score)
                                else:
                                    match_scores[match] = score
                            
                            # Obter o melhor match
                            best_match = max(match_scores.items(), key=lambda x: x[1])
                            matches_fuzzy[comune] = (best_match[0], best_match[1])
                    
                    # Aplicar os matches fuzzy encontrados
                    for idx, row in df_sem_coord_apos_exato.iterrows():
                        comune_match = row['comune_match']
                        if comune_match in matches_fuzzy:
                            best_match, score = matches_fuzzy[comune_match]
                            
                            # Encontrar as coordenadas do match
                            match_row = df_mapa_ref[df_mapa_ref['comune_norm'] == best_match].iloc[0]
                            
                            # Atualizar as coordenadas
                            df_comune.at[idx, col_lat] = match_row['lat']
                            df_comune.at[idx, col_lon] = match_row['lng']
                            df_comune.at[idx, col_coord_source] = f'FuzzyMatch_Comune_{score}'
                    
                    # 3. ADICIONA CASOS ESPECÍFICOS - BUSCA POR FRAGMENTOS NOS NOMES
                    df_sem_coord_apos_fuzzy = df_comune[df_comune[col_lat].isna() | df_comune[col_lon].isna()].copy()
                    
                    # Dividir nomes de comune em partes para tentar encontrar fragmentos
                    fragmentos_matches = {}
                    
                    for idx, row in df_sem_coord_apos_fuzzy.iterrows():
                        comune_match = row['comune_match']
                        if not comune_match or comune_match == 'nao especificado' or len(comune_match) < 4:
                            continue
                            
                        # Dividir o nome em partes
                        partes = comune_match.split()
                        partes = [p for p in partes if len(p) >= 4]  # Filtrar partes muito pequenas
                        
                        # Procurar cada parte separadamente
                        for parte in partes:
                            # Ignorar partes muito comuns como artigos e preposições
                            if parte in ['alla', 'del', 'con', 'per', 'sul', 'della', 'delle', 'dal', 'dei', 'dal', 'dagli', 'degli', 'che', 'nel']:
                                continue
                                
                            # Filtrar referências que contêm esta parte
                            matches = [(c, fuzz.partial_ratio(parte, c)) for c in ref_comunes if parte in c]
                            
                            # Pegar os melhores matches (se houver)
                            if matches:
                                # Ordenar por score (decrescente)
                                matches.sort(key=lambda x: x[1], reverse=True)
                                best_match, score = matches[0]
                                
                                if score >= 85:  # Usar threshold alto para fragmentos
                                    match_row = df_mapa_ref[df_mapa_ref['comune_norm'] == best_match].iloc[0]
                                    
                                    # Atualizar as coordenadas
                                    df_comune.at[idx, col_lat] = match_row['lat']
                                    df_comune.at[idx, col_lon] = match_row['lng']
                                    df_comune.at[idx, col_coord_source] = f'PartialMatch_Fragment_{score}'
                                    break  # Sair do loop de partes se encontrou match
                    
                    # 4. BUSCA POR TERMOS FIXOS - DETECTAR PADRÕES DE LOCALIZAÇÃO
                    df_sem_coord_apos_fragmentos = df_comune[df_comune[col_lat].isna() | df_comune[col_lon].isna()].copy()
                    
                    # Lista de localidades italianas populares para buscar
                    termos_localidades = [
                        ('venezia', 45.4375, 12.3358),
                        ('roma', 41.9000, 12.5000),
                        ('milano', 45.4669, 9.1900),
                        ('napoli', 40.8333, 14.2500),
                        ('torino', 45.0703, 7.6869),
                        ('palermo', 38.1300, 13.3417),
                        ('genova', 44.4056, 8.9464),
                        ('bologna', 44.4939, 11.3428),
                        ('firenze', 43.7800, 11.2500),
                        ('bari', 41.1253, 16.8667),
                        ('verona', 45.4386, 10.9928),
                        ('torino', 45.0700, 7.6800),
                        ('padova', 45.4167, 11.8667),
                        ('bergamo', 45.6950, 9.6700),
                        ('siena', 43.3178, 11.3317),
                        ('lecce', 40.3500, 18.1700),
                        ('parma', 44.8015, 10.3280)
                    ]
                    
                    for idx, row in df_sem_coord_apos_fragmentos.iterrows():
                        # Verificar se há menção a localidades conhecidas no texto
                        texto_completo = str(row.get(col_comune_orig, '')) + ' ' + str(row.get(col_provincia_orig, ''))
                        texto_completo = texto_completo.lower()
                        
                        for localidade, lat, lon in termos_localidades:
                            if localidade in texto_completo:
                                df_comune.at[idx, col_lat] = lat
                                df_comune.at[idx, col_lon] = lon
                                df_comune.at[idx, col_coord_source] = f'TextMatch_{localidade}'
                                break
                    
                    # Remover colunas temporárias
                    df_comune.drop(['comune_match', 'provincia_match'], axis=1, errors='ignore', inplace=True)
                    
                    # Calcular estatísticas de correspondência
                    registros_mapeados = df_comune[df_comune[col_lat].notna() & df_comune[col_lon].notna()]
                    total_mapeados = len(registros_mapeados)
                    
                    # Mostrar resultados do processamento
                    st.success(f"Processamento concluído! Taxa de correspondência: {total_mapeados}/{len(df_comune)} registros ({total_mapeados/len(df_comune)*100:.1f}%).")
            else:
                st.warning("Não foi possível aplicar o algoritmo avançado sem dados de referência.")
        except ImportError:
            st.warning("Para melhor processamento, instale: pip install thefuzz python-Levenshtein")
        except Exception as e:
            st.error(f"Erro ao aplicar algoritmo de correspondência: {e}")
            # Restaurar dados originais em caso de erro
            df_comune = df_original
        
        # Filtrar dados que possuem coordenadas válidas
        # Primeiro tentar converter para numérico, ignorando erros
        for col in [col_lat, col_lon]:
            if col in df_comune.columns:
                try:
                    # Converter para numérico, preservando apenas valores válidos
                    df_comune[col] = pd.to_numeric(df_comune[col], errors='coerce')
                except Exception as e:
                    st.warning(f"Erro ao converter coluna {col} para numérico: {e}")
        
        # Agora filtrar apenas linhas com coordenadas numéricas válidas
        df_mapa = df_comune[pd.notna(df_comune[col_lat]) & pd.notna(df_comune[col_lon])].copy()
        pontos_no_mapa = len(df_mapa)
        total_processos = len(df_comune)
        percentual_mapeado = (pontos_no_mapa / total_processos * 100) if total_processos > 0 else 0
        
        # Calcular contagens por tipo de match
        count_exact = 0
        count_fuzzy = 0
        count_partial = 0
        count_text = 0
        count_manual = 0
        count_provincia = 0
        
        if col_coord_source in df_comune.columns:
            # Contar matches por tipo
            count_exact = df_comune[df_comune[col_coord_source].str.contains('ExactMatch', na=False)].shape[0]
            count_fuzzy = df_comune[df_comune[col_coord_source].str.contains('FuzzyMatch', na=False)].shape[0]
            count_partial = df_comune[df_comune[col_coord_source].str.contains('PartialMatch', na=False)].shape[0]
            count_text = df_comune[df_comune[col_coord_source].str.contains('TextMatch', na=False)].shape[0]
            count_manual = df_comune[df_comune[col_coord_source].str.contains('Correção Manual', na=False)].shape[0]
            count_provincia = df_comune[df_comune[col_coord_source].str.contains('Correção Província', na=False)].shape[0]
            
        count_no_match = total_processos - count_exact - count_fuzzy - count_partial - count_text - count_manual - count_provincia

        # Exibir Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Processos", total_processos)
        with col2:
            st.metric("Processos Mapeados", pontos_no_mapa, f"{percentual_mapeado:.1f}%", delta_color="off")
        with col3:
            st.metric("Sem Coordenadas", count_no_match)

        # Mostrar estatísticas detalhadas por tipo de correspondência
        st.markdown("### Estatísticas de Correspondência")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"*   **Match Exato (Comune+Província):** {count_exact}")
            st.markdown(f"*   **Match Fuzzy (Comune):** {count_fuzzy}")
            st.markdown(f"*   **Match Parcial (Fragmentos):** {count_partial}")
        
        with col2:
            st.markdown(f"*   **Match por Texto:** {count_text}")
            st.markdown(f"*   **Correções Manuais:** {count_manual}")
            st.markdown(f"*   **Correções por Província:** {count_provincia}")

        # Exibir Mapa aprimorado com Folium (se disponível)
        if not df_mapa.empty:
            try:
                import folium
                from streamlit_folium import folium_static
                from folium.plugins import MarkerCluster
                
                # Criar um mapa interativo centrado na Itália
                m = folium.Map(location=[42.5, 12.5], zoom_start=6)
                
                # Adicionar um cluster de marcadores para melhor visualização com muitos pontos
                marker_cluster = MarkerCluster().add_to(m)
                
                # Definir cores para cada tipo de correspondência
                cores = {
                    'ExactMatch': 'green',
                    'FuzzyMatch': 'orange',
                    'PartialMatch': 'blue',
                    'TextMatch': 'cadetblue',
                    'Correção Manual': 'purple',
                    'Correção Província': 'red',
                    'default': 'gray'
                }
                
                # Adicionar marcadores para cada ponto com cores diferentes por tipo de match
                for idx, row in df_comune[df_comune[col_lat].notna() & df_comune[col_lon].notna()].iterrows():
                    # Determinar a cor do marcador com base no tipo de match
                    color = 'default'  # padrão
                    if col_coord_source in row and pd.notna(row[col_coord_source]):
                        for key in cores.keys():
                            if key in str(row[col_coord_source]):
                                color = cores[key]
                                break
                    
                    # Função para formatar coordenadas com segurança
                    def format_coord(val):
                        try:
                            if pd.notna(val):
                                return f"{float(val):.4f}"
                            return "N/A"
                        except (ValueError, TypeError):
                            return str(val)
                    
                    # Criar popup com informações detalhadas
                    lat_formatted = format_coord(row[col_lat])
                    lon_formatted = format_coord(row[col_lon])
                    
                    popup_html = f"""
                    <div style="font-family: Arial; width: 250px">
                        <h4 style="color: #1A237E; margin-bottom: 5px">{row.get('TITLE', 'Processo')}</h4>
                        <p><strong>ID:</strong> {row.get(col_id, 'N/A')}</p>
                        <p><strong>Comune:</strong> {row.get(col_comune_orig, 'N/A')}</p>
                        <p><strong>Província:</strong> {row.get(col_provincia_orig, 'N/A')}</p>
                        <p><strong>Estágio:</strong> {row.get('STAGE_NAME', 'N/A')}</p>
                        <p><strong>Tipo de Match:</strong> {row.get(col_coord_source, 'N/A')}</p>
                        <p><strong>Coordenadas:</strong> [{lat_formatted}, {lon_formatted}]</p>
                    </div>
                    """
                    
                    # Adicionar marcador ao cluster
                    try:
                        # Garantir que as coordenadas são numéricas
                        lat_num = float(row[col_lat])
                        lon_num = float(row[col_lon])
                        
                        folium.Marker(
                            location=[lat_num, lon_num],
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=row.get(col_comune_orig, 'Localidade'),
                            icon=folium.Icon(color=cores.get(color, 'gray'))
                        ).add_to(marker_cluster)
                    except (ValueError, TypeError) as e:
                        # Registrar erro de conversão (opcionalmente)
                        print(f"Erro ao converter coordenadas para o registro {row.get(col_id, 'ID?')}: {e}")
                
                # Adicionar legenda ao mapa
                legend_html = '''
                <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; 
                            background-color: white; padding: 10px; border: 2px solid grey; border-radius: 5px">
                    <p><strong>Legenda</strong></p>
                    <p><i class="fa fa-circle" style="color:green"></i> Match Exato</p>
                    <p><i class="fa fa-circle" style="color:orange"></i> Match Fuzzy</p>
                    <p><i class="fa fa-circle" style="color:blue"></i> Match Parcial</p>
                    <p><i class="fa fa-circle" style="color:cadetblue"></i> Match por Texto</p>
                    <p><i class="fa fa-circle" style="color:purple"></i> Correção Manual</p>
                    <p><i class="fa fa-circle" style="color:red"></i> Correção Província</p>
                </div>
                '''
                m.get_root().html.add_child(folium.Element(legend_html))
                
                # Exibir o mapa
                st.subheader("Mapa Interativo de Processos")
                
                # Adicionar CSS para que o mapa ocupe toda a largura da tela e remova margens laterais
                st.markdown("""
                <style>
                /* Estilo para o container do Streamlit - remove margens laterais */
                [data-testid="stAppViewContainer"] > .main {
                    max-width: 100vw !important;
                    padding-left: 0 !important;
                    padding-right: 0 !important;
                }
                
                /* Estilo específico para a seção do mapa */
                .mapa-container {
                    margin-left: -4rem !important;
                    margin-right: -4rem !important;
                    width: 100vw !important;
                }
                
                /* Estilos para o mapa */
                .folium-map {
                    width: 100% !important;
                    height: 500px !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                iframe {
                    width: 100% !important;
                    height: 600px !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    border: none !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Usar um container HTML com a classe especial para o mapa
                st.markdown('<div class="mapa-container">', unsafe_allow_html=True)
                folium_static(m, width=None, height=600)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Adicionar explicação abaixo do mapa
                st.info("""
                **Informações do Mapa:**
                - **Marcadores verdes:** Correspondência exata (Comune+Província)
                - **Marcadores laranjas:** Correspondência fuzzy (apenas Comune)
                - **Marcadores azuis:** Correspondência parcial (fragmentos do nome)
                - **Marcadores azul claro:** Correspondência por texto
                - **Marcadores roxos:** Correção manual
                - **Marcadores vermelhos:** Correção por província
                
                Clique nos marcadores para ver informações detalhadas de cada processo.
                """)
            except ImportError:
                # Fallback para o mapa padrão do Streamlit
                st.markdown("""
                <style>
                /* Estilo para o container do Streamlit - remove margens laterais */
                [data-testid="stAppViewContainer"] > .main {
                    max-width: 100vw !important;
                    padding-left: 0 !important;
                    padding-right: 0 !important;
                }
                
                /* Estilo específico para o mapa do Streamlit */
                .mapa-container {
                    margin-left: -4rem !important;
                    margin-right: -4rem !important;
                    width: 100vw !important;
                }
                
                /* Estilos para o mapa do Streamlit */
                .element-container:has([data-testid="stDecoration"]) {
                    width: 100% !important;
                    max-width: 100vw !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="mapa-container">', unsafe_allow_html=True)
                st.map(df_mapa, latitude=col_lat, longitude=col_lon, size=10, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.info("Para uma visualização mais detalhada, instale as bibliotecas folium e streamlit-folium.")
        else:
            st.warning("Nenhum processo com coordenadas válidas encontrado para exibir no mapa.")
        
        # Interface para melhorias manuais
        with st.expander("🔍 Ferramenta de Correção Manual", expanded=False):
            st.markdown("""
            <h4 style="color: #1A237E;">Corrigir Coordenadas Manualmente</h4>
            <p>Use esta ferramenta para adicionar coordenadas manualmente aos processos sem correspondência geográfica.</p>
            """, unsafe_allow_html=True)
            
            # Selecionar um processo para corrigir
            processos_sem_coord = df_comune[(df_comune[col_lat].isna()) | (df_comune[col_lon].isna())]
            
            if not processos_sem_coord.empty:
                # Criar lista de opções para seleção
                opcoes_processo = [f"{row.get('TITLE', 'Sem título')} - {row.get(col_comune_orig, 'Sem comune')} ({row.get(col_id, 'ID?')})" 
                                for _, row in processos_sem_coord.iterrows()]
                
                processo_selecionado = st.selectbox(
                    "Selecione um processo para corrigir:",
                    options=opcoes_processo
                )
                
                # Extrair ID do processo selecionado
                id_selecionado = None
                if processo_selecionado:
                    import re
                    match = re.search(r'\(([^)]+)\)$', processo_selecionado)
                    if match:
                        id_selecionado = match.group(1)
                
                if id_selecionado:
                    # Mostrar informações do processo
                    processo_row = df_comune[df_comune[col_id] == id_selecionado].iloc[0]
                    
                    st.markdown(f"""
                    **Detalhes do processo:**
                    - **ID:** {processo_row.get(col_id, 'N/A')}
                    - **Título:** {processo_row.get('TITLE', 'N/A')}
                    - **Comune:** {processo_row.get(col_comune_orig, 'N/A')}
                    - **Província:** {processo_row.get(col_provincia_orig, 'N/A')}
                    """)
                    
                    # Adicionar sugestão de busca
                    st.markdown("""
                    **Dica:** Você pode buscar coordenadas de localidades italianas usando:
                    - Google Maps: https://www.google.com/maps
                    - OpenStreetMap: https://www.openstreetmap.org
                    - GeoNames: http://www.geonames.org
                    """)
                    
                    # Campos para inserir coordenadas
                    col1, col2 = st.columns(2)
                    with col1:
                        latitude = st.number_input("Latitude", value=42.0, format="%.6f", min_value=35.0, max_value=48.0, step=0.000001)
                    with col2:
                        longitude = st.number_input("Longitude", value=12.5, format="%.6f", min_value=6.0, max_value=19.0, step=0.000001)
                    
                    # Botão para salvar
                    if st.button("Salvar Coordenadas"):
                        # Esta implementação apenas mostra como seria feito
                        # Em uma implementação real, seria necessário atualizar o banco de dados
                        st.success(f"Coordenadas atualizadas para o processo {id_selecionado}!")
                        st.info("Nota: Esta é uma demonstração. Em um ambiente real, estas coordenadas seriam salvas no banco de dados.")
                        
                        # Mostrar como ficaria no mapa
                        try:
                            import folium
                            from streamlit_folium import folium_static
                            
                            # Garantir que temos valores numéricos para o mapa
                            lat_num = float(latitude)
                            lon_num = float(longitude)
                            
                            st.subheader("Prévia do Mapa com Nova Coordenada")
                            m_preview = folium.Map(location=[lat_num, lon_num], zoom_start=10)
                            folium.Marker(
                                location=[lat_num, lon_num],
                                popup=f"<b>{processo_row.get('TITLE', 'Processo')}</b><br>Coordenadas atualizadas manualmente",
                                icon=folium.Icon(color='red')
                            ).add_to(m_preview)
                            folium_static(m_preview)
                        except ImportError:
                            st.info(f"Latitude: {latitude}, Longitude: {longitude}")
                        except (ValueError, TypeError) as e:
                            st.error(f"Erro ao criar prévia do mapa: {e}")
                            st.info(f"Latitude: {latitude}, Longitude: {longitude}")
            else:
                st.success("Todos os processos já possuem coordenadas! 🎉")
        
        # Tabela de Diagnóstico Expansível
        with st.expander("Ver Detalhes da Correspondência de Coordenadas", expanded=False):
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
            
            # Adicionar filtros para a tabela
            st.subheader("Filtros da tabela de diagnóstico")
            
            col1, col2 = st.columns(2)
            with col1:
                tipo_match = st.multiselect(
                    "Filtrar por tipo de match:",
                    options=['ExactMatch_ComuneProv', 'FuzzyMatch_Comune', 'PartialMatch_Fragment', 
                            'TextMatch', 'Correção Manual', 'Correção Província', 'No Match'],
                    default=[]
                )
            
            with col2:
                search_term = st.text_input("Pesquisar por comune ou província:", "")
            
            # Aplicar filtros
            df_diag_filtered = df_diag.copy()
            
            if tipo_match:
                mask_tipo = pd.Series(False, index=df_diag_filtered.index)
                for tm in tipo_match:
                    mask_tipo = mask_tipo | df_diag_filtered[col_coord_source].str.contains(tm, case=False, na=False)
                df_diag_filtered = df_diag_filtered[mask_tipo]
            
            if search_term:
                mask_search = (
                    df_diag_filtered[col_comune_orig].astype(str).str.contains(search_term, case=False, na=False) | 
                    df_diag_filtered[col_provincia_orig].astype(str).str.contains(search_term, case=False, na=False)
                )
                df_diag_filtered = df_diag_filtered[mask_search]
            
            # Exibir tabela filtrada
            st.dataframe(df_diag_filtered, use_container_width=True)
            
            # Download da tabela de diagnóstico
            csv_diag = df_diag.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Detalhes da Correspondência (CSV)",
                data=csv_diag,
                file_name=f'diagnostico_coordenadas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
                key='download-diag-coord-csv'
            )
            
            # Dicas de uso
            st.markdown("""
            **Dicas para melhorar o matching:**
            1. Padronize a entrada de dados nos campos de Comune e Província
            2. Verifique os nomes sem correspondência (No Match) e tente padronizá-los
            3. Use a ferramenta de correção manual para casos difíceis
            4. Adicione mais entradas ao dicionário de correções manuais para casos recorrentes
            """)

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

    # Nova seção: Instruções para melhoria contínua
    st.markdown("---")
    st.subheader("💡 Recomendações para Melhorar a Correspondência Geográfica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Padronização de Dados:**
        - Padronizar a entrada de dados no Bitrix24
        - Separar claramente Comune e Província
        - Usar nomes oficiais das localidades
        - Evitar abreviações e variações de nomes
        """)
        
        st.markdown("""
        **Enriquecimento de Dados:**
        - Atualizar regularmente a base geográfica de referência
        - Adicionar variações comuns de nomes à base
        - Incluir códigos postais e outras referências
        - Manter um dicionário de correções manuais atualizado
        """)
    
    with col2:
        st.markdown("""
        **Melhoria de Processo:**
        - Verificar e corrigir manualmente casos sem correspondência
        - Criar uma lista de equivalências para casos problemáticos
        - Documentar padrões de nomenclatura para referência futura
        - Implementar um sistema de feedback para correções
        """)
        
        st.markdown("""
        **Configuração do Sistema:**
        - Reduzir o threshold de similaridade para casos específicos
        - Utilizar a API de Geocodificação Google para casos difíceis
        - Implementar um sistema de cache para correspondências já encontradas
        - Considerar usar aprendizado de máquina para casos complexos
        """)

# Funções auxiliares para formatação de tempo
def formatar_tempo_meses(meses):
    return f"{int(meses)} {'mês' if int(meses) == 1 else 'meses'}"

def formatar_tempo_dias(dias):
    return f"{int(dias)} {'dia' if int(dias) == 1 else 'dias'}"

def formatar_tempo_horas(horas):
    return f"{int(horas)} {'hora' if int(horas) == 1 else 'horas'}" 