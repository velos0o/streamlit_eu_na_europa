import streamlit as st
import pandas as pd

def get_funil_html(etapa, valor, tipo=""):
    """
    Gera o HTML para um card de etapa do funil com base nas classes CSS do projeto.
    - etapa: O nome da etapa (ex: "Emissão").
    - valor: O número a ser exibido (ex: 15).
    - tipo: 'sucesso', 'andamento', ou 'perca' para definir a cor.
    """
    # Mapeia o tipo para a classe CSS modificadora
    if tipo == 'sucesso':
        modificador_classe = "stage-card--sucesso"
    elif tipo == 'andamento':
        modificador_classe = "stage-card--andamento"
    elif tipo == 'perca':
        modificador_classe = "stage-card--perca"
    else:
        modificador_classe = "" # Sem cor específica

    return f"""
    <div class="stage-card {modificador_classe}">
        <div class="stage-card__title">{etapa.upper()}</div>
        <div class="stage-card__value">{valor}</div>
    </div>
    """

def show_funil_etapas(df_filtrado):
    """Exibe o funil de etapas do processo com base nas pendências."""
    
    # Injetando o CSS diretamente para garantir a renderização
    st.markdown("""
    <style>
    .stage-card {
        text-align: center;
        padding: 1rem;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        transition: all 0.2s ease-in-out;
        border-radius: 0.5rem;
        background: #FFFFFF;
        border: 2px solid #E2E8F0;
        margin-bottom: 1rem; /* Adiciona espaço entre os cards */
    }
    .stage-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    .stage-card__title {
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #4A5568;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    .stage-card__value {
        font-size: 2.25rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
        color: #1A202C;
    }
    .stage-card--sucesso {
        background: rgba(76, 175, 80, 0.08);
        border-color: #4CAF50;
    }
    .stage-card--sucesso .stage-card__title, .stage-card--sucesso .stage-card__value {
        color: #388E3C;
    }
    .stage-card--andamento {
        background: rgba(255, 193, 7, 0.08);
        border-color: #FFC107;
    }
    .stage-card--andamento .stage-card__title, .stage-card--andamento .stage-card__value {
        color: #FFA000;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("Funil de Pendências por Etapa", divider='blue')

    if df_filtrado.empty:
        st.warning("Não há dados para exibir com os filtros selecionados.")
        return

    # Ordem das etapas do funil, conforme solicitado
    ordem_etapas = [
        'Emissão',
        'Comune',
        'Procuração',
        'Analise Documental',
        'Tradução',
        'Apostilamento',
        'Drive'
    ]

    # 1. Exibir o total de famílias no topo (estilo neutro)
    total_familias = df_filtrado['ID FAMÍLIA'].nunique()
    st.markdown(get_funil_html("Total de Famílias", total_familias), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True) # Espaçamento

    # DataFrame contendo apenas famílias com alguma pendência
    df_com_pendencias = df_filtrado[df_filtrado['PENDENCIAS'] != 'SEM PENDENCIAS'].copy()

    # 2. Contagem e exibição para cada tipo de pendência (estilo 'andamento')
    st.markdown("##### PENDÊNCIAS ATUAIS")
    # Usando st.columns para organizar os cards
    num_cols = 4  # Ajuste o número de colunas conforme necessário
    cols = st.columns(num_cols)
    col_idx = 0

    for etapa in ordem_etapas:
        count = df_com_pendencias['PENDENCIAS'].str.contains(etapa, case=False, na=False).sum()
        html = get_funil_html(etapa, count, tipo='andamento')
        with cols[col_idx]:
            st.markdown(html, unsafe_allow_html=True)
        col_idx = (col_idx + 1) % num_cols

    st.markdown("---") # Divisor

    # 3. Contagem de famílias "SEM PENDENCIAS" no final (estilo 'sucesso')
    sem_pendencias_count = df_filtrado[df_filtrado['PENDENCIAS'] == 'SEM PENDENCIAS']['ID FAMÍLIA'].nunique()
    st.markdown(get_funil_html("Sem Pendências", sem_pendencias_count, tipo='sucesso'), unsafe_allow_html=True) 