import streamlit as st
import pandas as pd
import plotly.express as px
from .styles import THEME

# Função auxiliar para converter HEX para RGBA
def hex_to_rgba(h, alpha=0.1):
    # Remove '#' se presente
    h = h.lstrip('#')
    # Converte pares hexadecimais para inteiros
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    # Retorna a string no formato correto rgba(R, G, B, A)
    return f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})'

def display_main_charts(df):
    """Exibe os gráficos principais (status, origem, tendência)."""
    try:
        theme_mode = "dark" if st.session_state.get("dark_mode", False) else "light"
    except:
        theme_mode = "light"
    
    theme = THEME[theme_mode]
    
    st.markdown('<div class="tw-fade-in" style="animation-delay: 0.1s;">', unsafe_allow_html=True)
    
    # Gráficos lado a lado: Status e Origem
    col_grafico1, col_grafico2 = st.columns(2)
    
    with col_grafico1:
        st.subheader("Status das Reclamações")
        status_counts = df["STATUS"].value_counts().reset_index()
        status_counts.columns = ["Status", "Quantidade"]
        
        fig_status = px.pie(
            status_counts, 
            values="Quantidade", 
            names="Status",
            color="Status",
            color_discrete_map={
                "Nova": theme["primary"],
                "Em análise": theme["info"],
                "Respondida": theme["warning"],
                "Resolvida": theme["success"],
                "Cancelada": theme["error"]
            },
            hole=0.4
        )
        fig_status.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', # Fundo transparente
            plot_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            font=dict(color=theme["text"]),
            legend=dict(bgcolor='rgba(0,0,0,0)') # Legenda transparente
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col_grafico2:
        st.subheader("Reclamações por Origem")
        origem_counts = df["ORIGEM"].value_counts().reset_index()
        origem_counts.columns = ["Origem", "Quantidade"]
        
        fig_origem = px.bar(
            origem_counts, 
            x="Origem", 
            y="Quantidade",
            color="Origem",
            text="Quantidade",
            color_discrete_sequence=px.colors.qualitative.Pastel # Esquema de cores padrão
        )
        fig_origem.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme["text"]),
            xaxis=dict(title='Origem', color=theme["text"], showgrid=False),
            yaxis=dict(title='Quantidade', color=theme["text"], gridcolor=hex_to_rgba(theme["primary"], alpha=0.1)) # Linhas de grade sutis
        )
        st.plotly_chart(fig_origem, use_container_width=True)
    
    # Gráfico de tendência
    st.subheader("Tendência de Reclamações", anchor="tendencia")
    df_trend = df.copy()
    df_trend["DATA_CRIACAO_DIA"] = df_trend["DATA_CRIACAO"].dt.strftime("%Y-%m-%d")
    df_trend_grouped = df_trend.groupby("DATA_CRIACAO_DIA").size().reset_index()
    df_trend_grouped.columns = ["Data", "Quantidade"]
    df_trend_grouped["Data"] = pd.to_datetime(df_trend_grouped["Data"])
    df_trend_grouped = df_trend_grouped.sort_values("Data")
    
    fig_trend = px.line(
        df_trend_grouped, 
        x="Data", 
        y="Quantidade",
        markers=True,
        line_shape='spline' # Linha suavizada
    )
    fig_trend.update_traces(line=dict(color=theme["primary"])) # Cor da linha
    fig_trend.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=theme["text"]),
        xaxis=dict(title='Data', color=theme["text"], showgrid=False),
        yaxis=dict(title='Quantidade de Reclamações', color=theme["text"], gridcolor=hex_to_rgba(theme["primary"], alpha=0.1))
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

def display_distribution_charts(df):
    """Exibe os gráficos de distribuição (departamento, responsável)."""
    try:
        theme_mode = "dark" if st.session_state.get("dark_mode", False) else "light"
    except:
        theme_mode = "light"
    
    theme = THEME[theme_mode]

    st.markdown('<div class="tw-fade-in" style="animation-delay: 0.15s;">', unsafe_allow_html=True)

    col_dept, col_resp = st.columns(2)
    
    with col_dept:
        st.subheader("Por Departamento")
        dept_counts = df["DEPARTAMENTO"].value_counts().reset_index()
        dept_counts.columns = ["Departamento", "Quantidade"]
        
        fig_dept = px.bar(
            dept_counts, 
            y="Departamento", 
            x="Quantidade",
            orientation="h",
            color="Quantidade",
            color_continuous_scale=px.colors.sequential.Blues, # Escala azul
            text="Quantidade"
        )
        fig_dept.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme["text"]),
            xaxis=dict(title='Quantidade', color=theme["text"], showgrid=False),
            yaxis=dict(title='', color=theme["text"], gridcolor=hex_to_rgba(theme["primary"], alpha=0.1)),
            coloraxis_showscale=False # Oculta a barra de escala de cor
        )
        fig_dept.update_traces(textposition='outside')
        st.plotly_chart(fig_dept, use_container_width=True)
    
    with col_resp:
        st.subheader("Por Responsável")
        resp_counts = df["ADM_RESPONSAVEL"].value_counts().reset_index()
        resp_counts.columns = ["Responsável", "Quantidade"]
        
        fig_resp = px.bar(
            resp_counts, 
            y="Responsável", 
            x="Quantidade",
            orientation="h",
            color="Quantidade",
            color_continuous_scale=px.colors.sequential.Purples, # Escala roxa
            text="Quantidade"
        )
        fig_resp.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme["text"]),
            xaxis=dict(title='Quantidade', color=theme["text"], showgrid=False),
            yaxis=dict(title='', color=theme["text"], gridcolor=hex_to_rgba(theme["secondary"], alpha=0.1)),
            coloraxis_showscale=False
        )
        fig_resp.update_traces(textposition='outside')
        st.plotly_chart(fig_resp, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True) 