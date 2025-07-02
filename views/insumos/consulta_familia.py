import streamlit as st
import pandas as pd
from datetime import datetime

def show_consulta_familia(df_insumos: pd.DataFrame):
    """
    Exibe a página de consulta de famílias com filtros e resultados em formato de lista.
    """
    st.title("Consulta de Famílias")
    st.markdown("Busque por famílias e veja o status delas nas etapas de Mapa Inicial, Financeiro e IA.")

    # --- CSS para a lista de resultados ---
    st.markdown("""
    <style>
    .list-container {
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        overflow: hidden; /* Garante que os cantos arredondados sejam aplicados às linhas internas */
    }
    .list-header, .family-row {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr 1fr; /* 4 colunas */
        gap: 1rem;
        padding: 0.75rem 1rem;
        align-items: center;
    }
    .list-header {
        background-color: #f6f8fa;
        color: #586069;
        font-weight: 600;
        font-size: 0.9em;
        border-bottom: 1px solid #e1e4e8;
    }
    .family-row {
        border-bottom: 1px solid #e1e4e8;
    }
    .family-row:last-child {
        border-bottom: none; /* Remove a borda da última linha */
    }
    .family-name {
        font-weight: 600;
        font-size: 1.1em;
        color: #24292e;
    }
    .family-id {
        font-size: 0.8em;
        color: #6a737d;
    }
    .status-pill {
        display: inline-block;
        padding: 0.3em 0.8em;
        font-size: 0.85em;
        font-weight: 700;
        border-radius: 16px;
        text-align: center;
        width: 90px; /* Largura fixa para alinhamento */
    }
    .status-pill.fila { background-color: #fffbeb; color: #b45309; }
    .status-pill.pronto { background-color: #f0fdf4; color: #15803d; }
    .status-pill.pendente { background-color: #e9ecef; color: #6c757d; }
    </style>
    """, unsafe_allow_html=True)

    # --- Filtros ---
    col1, col2 = st.columns([3, 2])
    with col1:
        search_term = st.text_input(
            "Buscar por nome da família:",
            placeholder="Digite o nome ou parte do nome"
        )
    with col2:
        date_filter = st.date_input(
            "Filtrar por data de reunião:",
            value=None
        )
        
    st.markdown("---")

    df_filtered = df_insumos.copy()
    
    if search_term:
        df_filtered = df_filtered[df_filtered['UF_CRM_42_NOME_FAMILIA'].str.contains(search_term, case=False, na=False)]

    if date_filter:
        df_filtered['UF_CRM_42_DATA_REUNIAO'] = pd.to_datetime(df_filtered['UF_CRM_42_DATA_REUNIAO'], errors='coerce')
        df_filtered = df_filtered[df_filtered['UF_CRM_42_DATA_REUNIAO'].dt.date == date_filter]

    if not search_term and not date_filter:
        st.info("Utilize os filtros acima para buscar por uma família.")
    elif df_filtered.empty:
        st.warning("Nenhuma família encontrada com os critérios de busca especificados.")
    else:
        family_status = pd.pivot_table(
            df_filtered,
            values='STAGE_NAME',
            index=['UF_CRM_42_ID_FAMILIA', 'UF_CRM_42_NOME_FAMILIA'],
            columns='CATEGORY_ID',
            aggfunc='first',
        ).rename(columns={114: 'Mapa Inicial', 116: 'Financeiro', 118: 'IA'})
        
        st.write(f"**{len(family_status)} família(s) encontrada(s):**")

        # --- Construção da lista HTML ---
        html_rows = []
        for index, row in family_status.iterrows():
            family_id, family_name = index
            
            status_map = {'Mapa Inicial': 'Pendente', 'Financeiro': 'Pendente', 'IA': 'Pendente'}
            for stage in status_map:
                if stage in row and pd.notna(row[stage]):
                    status_map[stage] = row[stage]
            
            status_cols_html_parts = []
            for stage_name, status in status_map.items():
                status_class = str(status).lower().replace(" ", "-")
                status_cols_html_parts.append(
                    f'<div style="text-align: center;"><div class="status-pill {status_class}">{status}</div></div>'
                )
            status_cols_html = "".join(status_cols_html_parts)
            
            row_html = (
                f'<div class="family-row">'
                f'<div><div class="family-name">{family_name}</div><div class="family-id">ID: {family_id}</div></div>'
                f'{status_cols_html}'
                f'</div>'
            )
            html_rows.append(row_html)

        # --- Renderização final ---
        final_html = f"""
        <div class="list-container">
            <div class="list-header">
                <div>Família</div>
                <div style="text-align: center;">MAPA INICIAL</div>
                <div style="text-align: center;">FINANCEIRO</div>
                <div style="text-align: center;">IA</div>
            </div>
            {''.join(html_rows)}
        </div>
        """
        st.markdown(final_html, unsafe_allow_html=True)

# Exemplo de como usar a função (para desenvolvimento)
if __name__ == '__main__':
    # Criar um DataFrame de exemplo
    data = {
        'UF_CRM_42_ID_FAMILIA': [1, 1, 2, 2, 2, 3],
        'UF_CRM_42_NOME_FAMILIA': ['Picoli', 'Picoli', 'Silva', 'Silva', 'Silva', 'Santos'],
        'CATEGORY_ID': [114, 116, 114, 116, 118, 114],
        'STAGE_NAME': ['FILA', 'PRONTO', 'PRONTO', 'FILA', 'PRONTO', 'FILA'],
        'UF_CRM_42_DATA_REUNIAO': [
            '2024-07-20', '2024-07-20', '2024-07-21',
            '2024-07-21', '2024-07-21', '2024-07-22'
        ]
    }
    sample_df = pd.DataFrame(data)
    show_consulta_familia(sample_df) 