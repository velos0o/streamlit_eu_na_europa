import streamlit as st
import pandas as pd
from .styles import tailwind_container, THEME

def get_status_badge(status):
    """Retorna um badge HTML estilizado para o status."""
    try:
        theme_mode = "dark" if st.session_state.get("dark_mode", False) else "light"
    except:
        theme_mode = "light"
    
    theme = THEME[theme_mode]
    
    color_map = {
        "Nova": "primary",
        "Em análise": "info",
        "Respondida": "warning",
        "Resolvida": "success",
        "Cancelada": "error"
    }
    badge_class = f"tw-badge-{color_map.get(status, 'primary')}"
    return f'<span class="tw-badge {badge_class}" style="white-space: nowrap;">{status}</span>'

def display_details_section(df):
    """Exibe a seção de filtros e detalhes das reclamações."""
    try:
        theme_mode = "dark" if st.session_state.get("dark_mode", False) else "light"
    except:
        theme_mode = "light"
    
    theme = THEME[theme_mode]

    st.markdown('<div class="tw-fade-in" style="animation-delay: 0.2s;">', unsafe_allow_html=True)
    st.markdown('<h2 class="tw-heading">Detalhes das Reclamações</h2>', unsafe_allow_html=True)
    
    # Card para filtros
    with st.container():
        st.markdown('<div class="tw-card tw-card-primary" style="margin-bottom: 1.5rem;">', unsafe_allow_html=True)
        
        # Adicionar filtros
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            # Garantir que opções sejam únicas e não nulas
            status_options = df["STATUS"].dropna().unique()
            status_filter = st.multiselect(
                "Filtrar por Status",
                options=status_options,
                default=list(status_options)
            )
            
        with col_filtro2:
            dept_options = df["DEPARTAMENTO"].dropna().unique()
            departamento_filter = st.multiselect(
                "Filtrar por Departamento",
                options=dept_options,
                default=list(dept_options)
            )
            
        with col_filtro3:
            origem_options = df["ORIGEM"].dropna().unique()
            origem_filter = st.multiselect(
                "Filtrar por Origem",
                options=origem_options,
                default=list(origem_options)
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Aplicar filtros
    df_filtered = df.copy()
    if status_filter:
        df_filtered = df_filtered[df_filtered["STATUS"].isin(status_filter)]
    if departamento_filter:
        df_filtered = df_filtered[df_filtered["DEPARTAMENTO"].isin(departamento_filter)]
    if origem_filter:
        df_filtered = df_filtered[df_filtered["ORIGEM"].isin(origem_filter)]
    
    # Mostrar tabela filtrada
    st.markdown("### Reclamações Filtradas")
    
    # Colunas a serem exibidas
    cols_to_display = ["DATA_CRIACAO", "ADM_RESPONSAVEL", "DEPARTAMENTO", "ORIGEM", "STATUS", "DESCRICAO_RECLAMACAO"]
    df_display = df_filtered[cols_to_display].copy()

    # Tentar aplicar o badge na coluna STATUS (pode não funcionar perfeitamente com st.dataframe)
    # Uma alternativa é usar st.markdown com uma tabela HTML, mas perde interatividade.
    # Vamos manter st.dataframe por enquanto e o badge será usado no detalhe.
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "DATA_CRIACAO": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "ADM_RESPONSAVEL": st.column_config.TextColumn("Responsável"),
            "DEPARTAMENTO": st.column_config.TextColumn("Departamento"),
            "ORIGEM": st.column_config.TextColumn("Origem"),
            "STATUS": st.column_config.TextColumn("Status"), # Idealmente seria um SelectboxColumn ou similar
            "DESCRICAO_RECLAMACAO": st.column_config.TextColumn("Descrição", width="large"),
        }
    )
    
    # Adicionar expansor para ver detalhes de uma reclamação específica
    tw_expander = tailwind_container("secondary")
    with tw_expander.expander("🔍 Ver detalhes de uma reclamação específica"):
        col_id, col_btn = st.columns([3, 1])
        
        with col_id:
            # Usar ID máximo do DataFrame original para o range
            max_id = df["ID"].max() if not df["ID"].empty else 1
            reclamacao_id = st.number_input("ID da Reclamação", min_value=1, 
                                            max_value=int(max_id), value=1, key="reclamacao_id_input")
            
        with col_btn:
            st.write("") # Espaço para alinhar com o input
            buscar = st.button("Buscar Detalhes", key="btn_buscar_detalhes")
            
        if buscar:
            reclamacao = df[df["ID"] == reclamacao_id]
            
            if not reclamacao.empty:
                reclamacao = reclamacao.iloc[0]
                
                # Card com os detalhes da reclamação
                st.markdown(f'<div class="tw-card tw-card-secondary tw-fade-in" style="margin-top: 1rem;">', unsafe_allow_html=True)
                st.subheader(f"Detalhes da Reclamação #{reclamacao_id}")
                
                # Adicionar badge do status
                status = reclamacao["STATUS"]
                st.markdown(get_status_badge(status), unsafe_allow_html=True)
                
                st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)
                
                # Informações em colunas
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**ID:** {reclamacao.get('ID', 'N/A')}")
                    st.markdown(f"**Data:** {reclamacao['DATA_CRIACAO'].strftime('%d/%m/%Y') if pd.notna(reclamacao.get('DATA_CRIACAO')) else 'N/A'}")
                    st.markdown(f"**Responsável:** {reclamacao.get('ADM_RESPONSAVEL', 'N/A')}")
                    st.markdown(f"**Departamento:** {reclamacao.get('DEPARTAMENTO', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Origem:** {reclamacao.get('ORIGEM', 'N/A')}")
                    st.markdown(f"**CPF:** {reclamacao.get('CPF', 'N/A')}")
                    st.markdown(f"**Email:** {reclamacao.get('EMAIL', 'N/A')}")
                    st.markdown(f"**Telefone:** {reclamacao.get('TELEFONE', 'N/A')}")
                
                # Descrição completa
                st.markdown('<div class="tw-divider"></div>', unsafe_allow_html=True)
                st.markdown("**Descrição da Reclamação:**")
                st.markdown(f"> {reclamacao.get('DESCRICAO_RECLAMACAO', 'N/A')}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(f"Reclamação com ID {reclamacao_id} não encontrada.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_reclamacao_details(df, selected_id=None):
    """Exibe detalhes de uma reclamação específica ou todas elas"""
    # Determinar o tema com base no session_state (verificação segura)
    try:
        theme_mode = "dark" if st.session_state.get("dark_mode", False) else "light"
    except:
        theme_mode = "light"
    
    theme = THEME[theme_mode] 