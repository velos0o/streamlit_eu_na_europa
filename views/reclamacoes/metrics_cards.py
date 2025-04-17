import streamlit as st
from .styles import THEME

# Função alternativa usando componentes nativos do Streamlit
def show_metric_card(col, value, title, change=None, is_positive=True):
    """Exibe um cartão de métrica usando componentes nativos do Streamlit"""
    theme_mode = "dark" if st.session_state.get("dark_mode", False) else "light"
    theme = THEME[theme_mode]
    
    # Cria uma div estilizada na coluna
    with col:
        # O estilo do st.metric já está sendo tratado globalmente em apply_tailwind_styles
        # Não precisamos mais de CSS específico aqui, a menos que haja uma necessidade especial.
        
        # Exibir o valor usando o componente nativo
        delta_str = f"{change}%" if change is not None else None
        delta_color = "normal" if is_positive else "inverse"
        
        # Tentar formatar se for numérico
        formatted_value = value
        try:
            if isinstance(value, (int, float)):
                formatted_value = f"{value:,.0f}".replace(",", ".")
            elif isinstance(value, str) and '%' in value:
                # Manter strings com % como estão
                pass
            else:
                # Tentar converter para número antes de formatar
                num_value = float(str(value).replace('.','').replace(',','.')) # Ajustar para formato numérico PT-BR
                formatted_value = f"{num_value:,.0f}".replace(",", ".")
        except (ValueError, TypeError):
            formatted_value = value # Mantém original se não for numérico

        st.metric(
            label=title,
            value=formatted_value,
            delta=delta_str,
            delta_color=delta_color
        )

def display_metrics_cards(df):
    """Exibe os cards de métricas principais."""
    theme_mode = "dark" if st.session_state.get("dark_mode", False) else "light"
    
    st.markdown('<div class="tw-fade-in">', unsafe_allow_html=True)
    
    # Métricas principais em cards
    col1, col2, col3, col4 = st.columns(4)
    
    # Total de reclamações
    total_reclamacoes = len(df)
    show_metric_card(
        col1,
        total_reclamacoes, 
        "Total de Reclamações", 
        change=None, # Definir change como None se não houver valor real
        is_positive=False
    )

    # Reclamações em aberto
    reclamacoes_em_aberto = len(df[df["STATUS"].isin(["Nova", "Em análise"])])
    show_metric_card(
        col2,
        reclamacoes_em_aberto, 
        "Em Aberto", 
        change=None, 
        is_positive=False
    )

    # Reclamações resolvidas
    reclamacoes_resolvidas = len(df[df["STATUS"] == "Resolvida"])
    show_metric_card(
        col3,
        reclamacoes_resolvidas, 
        "Resolvidas", 
        change=None, 
        is_positive=True
    )
    
    # Taxa de resolução
    taxa_resolucao = 0
    if total_reclamacoes > 0:
        taxa_resolucao = int((reclamacoes_resolvidas / total_reclamacoes) * 100)
    
    show_metric_card(
        col4,
        f"{taxa_resolucao}%", 
        "Taxa de Resolução", 
        change=None, 
        is_positive=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True) 