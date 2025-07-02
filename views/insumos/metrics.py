import streamlit as st
import pandas as pd

def display_metrics(df: pd.DataFrame):
    """
    Calcula e exibe os cartões de métricas para um determinado DataFrame.
    """
    # Injetar CSS para estilizar os cartões de métrica
    st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f6f8fa;
        border: 1px solid #24292e;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if df.empty:
        st.warning("Não há dados para exibir as métricas.")
        return

    total_registros = len(df)
    
    # Assumindo que o estágio 'FILA' está na coluna 'STAGE_NAME'
    # O nome exato pode precisar de ajuste (ex: 'EM FILA', 'Fila', etc.)
    em_fila = df[df['STAGE_NAME'] == 'FILA'].shape[0] if 'STAGE_NAME' in df.columns else 'N/A'
    
    # Contar registros com status 'PRONTO'
    pronto = df[df['STAGE_NAME'] == 'PRONTO'].shape[0] if 'STAGE_NAME' in df.columns else 'N/A'

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Quantidade Total",
            value=total_registros,
            help="Número total de registros (IDs) nesta categoria."
        )

    with col2:
        st.metric(
            label="Em Fila",
            value=em_fila,
            help="Registros que estão atualmente no estágio 'FILA'."
        )
        
    with col3:
        st.metric(
            label="Pronto",
            value=pronto,
            help="Registros que estão atualmente no estágio 'PRONTO'."
        ) 