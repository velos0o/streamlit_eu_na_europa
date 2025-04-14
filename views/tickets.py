import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import mysql.connector
from datetime import datetime, timedelta
import calendar
import time

# Verificar e instalar bibliotecas adicionais se necessário
try:
    import streamlit_card
    from streamlit_extras.metric_cards import style_metric_cards
    from streamlit_extras.add_vertical_space import add_vertical_space
    from streamlit_extras.colored_header import colored_header
except ImportError:
    st.markdown("### Instalando bibliotecas de estilização...")
    import subprocess
    subprocess.call(["pip", "install", "streamlit-card", "streamlit-extras"])
    import streamlit_card
    from streamlit_extras.metric_cards import style_metric_cards
    from streamlit_extras.add_vertical_space import add_vertical_space
    from streamlit_extras.colored_header import colored_header

# CSS personalizado para estilização moderna
def load_custom_css():
    st.markdown("""
    <style>
    /* Customização geral */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Cards de métricas */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
    }
    
    div[data-testid="metric-container"] > label {
        color: #6c757d;
        font-size: 1rem;
        font-weight: 500;
    }
    
    div[data-testid="metric-container"] > div {
        color: #343a40;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        background-color: #f1f3f5;
        border: none;
        color: #495057;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4361ee !important;
        color: white !important;
    }
    
    /* DataFrame */
    .dataframe-container {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-weight: 800;
        color: #212529;
    }
    
    h1 {
        font-size: 2.2rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(90deg, #4361ee, #3a0ca3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }
    
    /* Botões */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 25px;
        background-color: #4361ee;
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #3a0ca3;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(67, 97, 238, 0.3);
    }
    
    /* Selectbox e Slider */
    div[data-baseweb="select"] {
        border-radius: 8px;
    }
    
    div[data-testid="stThumbValue"] {
        color: #4361ee;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

def connect_to_db():
    """Estabelece conexão com o banco de dados MySQL"""
    try:
        conn = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            port=int(st.secrets["DB_PORT"]),
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"]
        )
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {e}")
        return None

def get_tickets_data():
    """Obtém dados dos tickets do banco de dados"""
    # Mostrar loading animation
    with st.spinner("Carregando dados de tickets..."):
        conn = connect_to_db()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                
                # Query para obter tickets com informações do cliente
                query = """
                SELECT t.id, t.message, t.createdAt, t.departament, 
                       c.nome, c.email, c.telefone, c.idfamilia
                FROM tickets t
                LEFT JOIN customers c ON t.customerId = c.id
                ORDER BY t.createdAt DESC
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                # Converter para DataFrame
                df = pd.DataFrame(results)
                
                # Garantir que createdAt é datetime
                if 'createdAt' in df.columns:
                    df['createdAt'] = pd.to_datetime(df['createdAt'])
                    
                    # Adicionar colunas para análise de tempo
                    df['hora'] = df['createdAt'].dt.hour
                    df['dia_semana'] = df['createdAt'].dt.day_name()
                    df['dia'] = df['createdAt'].dt.day
                    df['mes'] = df['createdAt'].dt.month
                    df['ano'] = df['createdAt'].dt.year
                
                cursor.close()
                conn.close()
                return df
            
            except Exception as e:
                st.error(f"Erro ao obter dados: {e}")
                if conn:
                    conn.close()
                return pd.DataFrame()
        else:
            return pd.DataFrame()

def card_metric(title, value, description=None, icon=None, color="#4361ee"):
    """Renderiza um cartão de métrica estilizado"""
    icon_html = f'<i class="material-icons" style="font-size:2rem;color:{color};margin-right:10px">{icon}</i>' if icon else ""
    
    html = f"""
    <div style="
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        margin: 10px 0;
        border-left: 5px solid {color};
        display: flex;
        align-items: center;
    ">
        {icon_html}
        <div>
            <h3 style="margin:0;color:#6c757d;font-size:0.9rem;font-weight:500">{title}</h3>
            <p style="margin:0;color:#212529;font-size:1.5rem;font-weight:700">{value}</p>
            <p style="margin:0;color:#6c757d;font-size:0.8rem;margin-top:5px">{description if description else ''}</p>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def show_tickets():
    """Função principal para mostrar a página de Tickets"""
    # Carregar CSS customizado
    load_custom_css()
    
    # Injetar Material Icons
    st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    """, unsafe_allow_html=True)
    
    # Header gradiente com design moderno
    colored_header(
        label="Tickets de Suporte",
        description="Painel de monitoramento de tickets em tempo real",
        color_name="blue-70",
    )
    
    add_vertical_space(1)
    
    # Inicia o contador de tempo para estatísticas de carregamento
    start_time = time.time()
    
    # Obter dados
    df = get_tickets_data()
    
    if df.empty:
        st.warning("Não foi possível carregar os dados dos tickets.")
        return
    
    # Calcula tempo de carregamento
    load_time = round(time.time() - start_time, 2)
    
    # Mostrar estatísticas rápidas
    st.caption(f"✅ Carregados {len(df)} tickets em {load_time} segundos")
    
    add_vertical_space(1)
    
    # Totais e métricas
    total_tickets = len(df)
    
    # Tickets por departamento
    tickets_por_depto = df['departament'].value_counts().reset_index()
    tickets_por_depto.columns = ['Departamento', 'Quantidade']
    
    # Tickets dos últimos 7 dias
    hoje = datetime.now()
    semana_passada = hoje - timedelta(days=7)
    tickets_semana = df[df['createdAt'] >= semana_passada]
    total_semana = len(tickets_semana)
    
    # Tickets do dia
    tickets_hoje = df[df['createdAt'].dt.date == hoje.date()]
    total_hoje = len(tickets_hoje)
    
    # Layout em colunas para os KPIs com design de cartões modernos
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        card_metric("Total de Tickets", f"{total_tickets}", "Todos os tickets", "confirmation_number", "#4361ee")
    
    with col2:
        card_metric("Tickets na Semana", f"{total_semana}", "Últimos 7 dias", "date_range", "#3a0ca3")
        
    with col3:
        card_metric("Tickets Hoje", f"{total_hoje}", "Nas últimas 24h", "today", "#7209b7")
        
    with col4:
        if len(tickets_por_depto) > 0:
            depto_principal = tickets_por_depto.iloc[0]['Departamento']
            qtd_principal = tickets_por_depto.iloc[0]['Quantidade']
            card_metric(f"Depto. Principal", f"{depto_principal}", f"{qtd_principal} tickets", "star", "#f72585")
    
    add_vertical_space(1)
    
    # Guias para diferentes visualizações com design moderno
    tab1, tab2, tab3 = st.tabs([
        "📊 Visão Geral", 
        "⏱️ Análise Temporal", 
        "🔍 Detalhes"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de tickets por departamento com design moderno
            if len(tickets_por_depto) > 0:
                fig = px.pie(
                    tickets_por_depto, 
                    values='Quantidade', 
                    names='Departamento',
                    title='<b>Distribuição por Departamento</b>',
                    hole=0.6,
                    color_discrete_sequence=px.colors.sequential.Plasma_r
                )
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                    margin=dict(t=60, b=40, l=10, r=10),
                    title_x=0.5,
                    font=dict(family="Arial"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=18)
                )
                
                # Adicionar número total no centro
                fig.add_annotation(
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    text=f"<b>{total_tickets}</b><br>tickets",
                    showarrow=False,
                    font=dict(size=20)
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
        with col2:
            # Gráfico de tickets por dia da semana com design moderno
            dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            
            tickets_por_dia = df['dia_semana'].value_counts().reindex(dias_ordem, fill_value=0)
            tickets_por_dia.index = dias_pt
            
            fig = px.bar(
                x=tickets_por_dia.index, 
                y=tickets_por_dia.values,
                title='<b>Tickets por Dia da Semana</b>',
                labels={'x': 'Dia da Semana', 'y': 'Quantidade de Tickets'},
                color=tickets_por_dia.values,
                color_continuous_scale='Plasma_r',
                text=tickets_por_dia.values
            )
            fig.update_traces(
                texttemplate='%{text}', 
                textposition='inside',
                marker=dict(line=dict(width=1, color='white'))
            )
            fig.update_layout(
                margin=dict(t=60, b=40, l=10, r=10),
                title_x=0.5,
                font=dict(family="Arial"),
                coloraxis_showscale=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title_font=dict(size=18),
                xaxis=dict(
                    showgrid=False,
                    zeroline=False
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(230,230,230,0.5)',
                    zeroline=False
                )
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Status cards com distribuição dos tickets
        st.markdown("#### Distribuição de Tickets")
        st.caption("Visão geral da distribuição de tickets por dia e departamento")
        
        status_col1, status_col2, status_col3 = st.columns(3)
        
        dias_unicos = df['dia'].nunique()
        media_tickets_dia = round(total_tickets / dias_unicos if dias_unicos > 0 else 0, 1)
        usuarios_unicos = df['nome'].nunique()
        
        with status_col1:
            card_metric("Média Diária", f"{media_tickets_dia}", "Tickets por dia", "trending_up", "#4cc9f0")
            
        with status_col2:
            card_metric("Clientes Únicos", f"{usuarios_unicos}", "Total de clientes", "people", "#4895ef")
            
        with status_col3:
            departamentos_unicos = df['departament'].nunique()
            card_metric("Departamentos", f"{departamentos_unicos}", "Áreas atendidas", "business", "#4361ee")
    
    with tab2:
        st.markdown("#### Análise Temporal dos Tickets")
        st.caption("Visualização de como os tickets são distribuídos ao longo do tempo")
        
        time_col1, time_col2 = st.columns(2)
        
        with time_col1:
            # Gráfico de tickets por hora do dia
            tickets_por_hora = df['hora'].value_counts().sort_index()
            
            # Preencher horas vazias com zeros
            todas_horas = pd.Series(index=range(24), data=0)
            tickets_por_hora = tickets_por_hora.add(todas_horas, fill_value=0).sort_index()
            
            fig = px.area(
                x=tickets_por_hora.index, 
                y=tickets_por_hora.values,
                title='<b>Tickets por Hora do Dia</b>',
                labels={'x': 'Hora do Dia', 'y': 'Quantidade de Tickets'},
                color_discrete_sequence=['#4361ee']
            )
            fig.update_traces(
                mode='lines+markers',
                marker=dict(size=8, symbol='circle', color='#3a0ca3',
                          line=dict(width=2, color='white')),
                line=dict(width=3),
                fill='tozeroy',
                fillcolor='rgba(67, 97, 238, 0.2)'
            )
            fig.update_layout(
                xaxis=dict(tickmode='linear', dtick=2, showgrid=False),
                margin=dict(t=60, b=40, l=10, r=10),
                title_x=0.5,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title_font=dict(size=18),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(230,230,230,0.5)',
                    zeroline=False
                )
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with time_col2:
            # Gráfico de tendência mensal
            tickets_por_mes = df.groupby(['ano', 'mes']).size().reset_index(name='tickets')
            
            # Criar label de mês no formato Abr/23
            meses_abrev = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            tickets_por_mes['mes_ano'] = tickets_por_mes.apply(
                lambda x: f"{meses_abrev[int(x['mes'])-1]}/{str(x['ano'])[-2:]}", axis=1
            )
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=tickets_por_mes['mes_ano'],
                y=tickets_por_mes['tickets'],
                mode='lines+markers',
                name='Tickets',
                line=dict(width=4, color='#7209b7'),
                marker=dict(
                    size=12,
                    color='#7209b7',
                    line=dict(width=2, color='white')
                ),
            ))
            
            fig.update_layout(
                title='<b>Tendência Mensal de Tickets</b>',
                xaxis=dict(title='Mês', showgrid=False),
                yaxis=dict(
                    title='Quantidade de Tickets',
                    showgrid=True,
                    gridcolor='rgba(230,230,230,0.5)',
                    zeroline=False
                ),
                margin=dict(t=60, b=40, l=10, r=10),
                title_x=0.5,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title_font=dict(size=18),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Heatmap de atividade - hora x dia da semana com design moderno
        st.markdown("#### Mapa de Calor: Distribuição de Tickets")
        st.caption("Visualização da concentração de tickets por hora do dia e dia da semana")
        
        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        
        # Criar DataFrame para o heatmap mesmo se não houver dados
        try:
            heatmap_data = df.pivot_table(
                values='id', 
                index='dia_semana', 
                columns='hora', 
                aggfunc='count', 
                fill_value=0
            )
            
            # Reordenar os dias da semana
            heatmap_data = heatmap_data.reindex(dias_ordem)
        except:
            # Criar dataframe vazio se não houver dados suficientes
            heatmap_data = pd.DataFrame(0, index=dias_ordem, columns=range(24))
        
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Hora do Dia", y="Dia da Semana", color="Tickets"),
            x=heatmap_data.columns,
            y=dias_pt,
            color_continuous_scale='Plasma',
            aspect="auto"
        )
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=2),
            coloraxis_colorbar=dict(
                title="Tickets",
                thicknessmode="pixels", thickness=20,
                lenmode="pixels", len=300,
                yanchor="top", y=1,
                ticks="outside"
            ),
            margin=dict(t=10, b=40, l=10, r=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with tab3:
        # Filtros e tabela com design moderno
        st.markdown("""
        <h4 style="background: linear-gradient(90deg, #4361ee, #3a0ca3); 
                   -webkit-background-clip: text; 
                   -webkit-text-fill-color: transparent; 
                   display: inline-block;">
            Lista Detalhada de Tickets
        </h4>
        """, unsafe_allow_html=True)
        
        # Filtros modernos
        filter_col1, filter_col2, filter_col3 = st.columns([2,2,1])
        
        with filter_col1:
            departamentos = ['Todos'] + sorted(df['departament'].unique().tolist())
            filtro_depto = st.selectbox('Departamento:', departamentos)
        
        with filter_col2:
            dias = 7
            filtro_dias = st.slider('Mostrar tickets dos últimos X dias:', 1, 30, dias)
        
        with filter_col3:
            st.markdown("<br>", unsafe_allow_html=True)
            mostrar_todos = st.checkbox('Mostrar todos')
        
        # Aplicar filtros
        df_filtrado = df.copy()
        if filtro_depto != 'Todos' and not mostrar_todos:
            df_filtrado = df_filtrado[df_filtrado['departament'] == filtro_depto]
        
        if not mostrar_todos:
            data_corte = hoje - timedelta(days=filtro_dias)
            df_filtrado = df_filtrado[df_filtrado['createdAt'] >= data_corte]
        
        # Exibir tabela com estilo moderno
        if not df_filtrado.empty:
            # Mostrar contagem de tickets filtrados
            st.caption(f"Exibindo {len(df_filtrado)} tickets de um total de {len(df)}")
            
            colunas_exibir = ['id', 'nome', 'departament', 'createdAt', 'message']
            df_exibir = df_filtrado[colunas_exibir].rename(columns={
                'id': 'ID', 
                'nome': 'Cliente', 
                'departament': 'Departamento',
                'createdAt': 'Data Criação',
                'message': 'Mensagem'
            })
            
            # Formatando a data
            df_exibir['Data Criação'] = df_exibir['Data Criação'].dt.strftime('%d/%m/%Y %H:%M')
            
            # Truncando mensagens muito longas
            df_exibir['Mensagem'] = df_exibir['Mensagem'].str.slice(0, 50) + '...'
            
            # Destacar dados recentes (hoje)
            def highlight_today(val):
                hoje_str = datetime.now().strftime('%d/%m/%Y')
                if hoje_str in str(val):
                    return 'background-color: rgba(67, 97, 238, 0.1); font-weight: bold;'
                return ''
            
            # Aplicar estilo à tabela
            df_styled = df_exibir.style.applymap(highlight_today, subset=['Data Criação'])
            
            # Exibir tabela com classe CSS personalizada
            st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
            st.dataframe(df_styled, use_container_width=True, height=400)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Linha com estatísticas e botão de exportação
            stat_col, export_col = st.columns([3,1])
            
            with stat_col:
                # Resumo dos dados filtrados
                st.caption(f"Período: {df_filtrado['createdAt'].min().strftime('%d/%m/%Y')} até {df_filtrado['createdAt'].max().strftime('%d/%m/%Y')}")
            
            with export_col:
                # Botão para exportar dados
                csv = df_filtrado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar CSV",
                    data=csv,
                    file_name=f"tickets_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            # Mensagem estilizada quando não houver dados
            st.markdown("""
            <div style="
                padding: 20px; 
                border-radius: 10px; 
                background-color: #f8f9fa; 
                text-align: center;
                margin: 20px 0;
                border: 1px dashed #dee2e6;
            ">
                <img src="https://cdn-icons-png.flaticon.com/512/7486/7486754.png" width="80px">
                <p style="margin-top: 15px; color: #6c757d; font-weight: 500;">
                    Nenhum ticket encontrado com os filtros aplicados
                </p>
                <p style="color: #adb5bd; font-size: 0.9rem;">
                    Tente alterar os filtros para visualizar mais resultados
                </p>
            </div>
            """, unsafe_allow_html=True) 