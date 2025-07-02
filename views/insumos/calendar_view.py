import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def display_reuniao_schedule(df: pd.DataFrame):
    """
    Processa e exibe a contagem de reuniões por etapa em um layout de calendário dinâmico de 5 dias.
    """
    # Inicializa a data de início do calendário na sessão se não existir
    if 'calendar_start_date' not in st.session_state:
        st.session_state.calendar_start_date = pd.to_datetime('today').normalize()

    # Funções de callback para os botões de navegação
    def go_back_5_days():
        st.session_state.calendar_start_date -= timedelta(days=5)

    def go_forward_5_days():
        st.session_state.calendar_start_date += timedelta(days=5)
        
    # --- Cabeçalho com Navegação ---
    start_date = st.session_state.calendar_start_date
    end_date = start_date + timedelta(days=4)
    date_range_str = f"{start_date.strftime('%d/%m')} – {end_date.strftime('%d/%m')}"

    col1, col2, col3 = st.columns([2, 5, 2])
    with col1:
        st.button("❮ Anterior", on_click=go_back_5_days, use_container_width=True)
    with col2:
        st.markdown(f"""
        <div style="text-align: center; margin-top: -8px;">
            <h4 style="margin-bottom: 0.1rem; font-weight: 600;">Agenda de Reuniões</h4>
            <p style="color: #6a737d; font-size: 0.9em; margin-bottom: 0;">{date_range_str}</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.button("Próximo ❯", on_click=go_forward_5_days, use_container_width=True)

    dias_semana = {
        0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira",
        4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
    }

    date_col = 'UF_CRM_42_DATA_REUNIAO'
    stage_col = 'STAGE_NAME'
    
    if df.empty or date_col not in df.columns or stage_col not in df.columns:
        st.info("Não há dados de reunião ou etapas para exibir.")
        return

    schedule_df = df[['ID', date_col, stage_col]].copy()
    schedule_df[date_col] = pd.to_datetime(schedule_df[date_col], errors='coerce')
    schedule_df.dropna(subset=[date_col], inplace=True)
    
    if schedule_df.empty:
        st.info("Nenhuma reunião com data válida encontrada.")
        return

    reunioes_por_etapa = schedule_df.groupby([schedule_df[date_col].dt.date, schedule_df[stage_col]]) \
                                    .count()['ID'].unstack(fill_value=0)

    st.markdown("""
    <style>
    /* Estilo para os botões de navegação do calendário */
    div[data-testid="stHorizontalBlock"] > div:first-child button,
    div[data-testid="stHorizontalBlock"] > div:last-child button {
        border: 1px solid #24292e !important; /* Borda escura */
        color: #24292e !important; /* Texto escuro */
        background-color: #ffffff; /* Fundo branco */
        transition: all 0.2s ease;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child button:hover,
    div[data-testid="stHorizontalBlock"] > div:last-child button:hover {
        border-color: #24292e !important;
        color: #ffffff !important;
        background-color: #24292e !important; /* Inverte as cores no hover */
    }

    .day-box {
        border: 1px solid #e1e4e8; border-radius: 8px; padding: 10px;
        text-align: center; margin: 5px; height: 140px;
        display: flex; flex-direction: column; justify-content: space-between;
        background-color: #f6f8fa;
    }
    .day-box-today { border-color: #24292e; background-color: #f1f8ff; }
    .day-header { min-height: 2.5em; display: flex; flex-direction: column; justify-content: center; }
    .day-name { font-size: 0.9em; font-weight: 600; color: #586069; }
    .day-date { font-size: 0.8em; color: #6a737d; }
    .day-counts-container { display: flex; justify-content: space-around; align-items: center; padding-top: 10px; }
    .stage-count { 
        display: flex;
        flex-direction: column;
        width: 45%;
        text-align: center;
    }
    .count-number { font-size: 1.8em; font-weight: 700; line-height: 1.1; }
    .count-label { font-size: 0.7em; text-transform: uppercase; font-weight: 600; }
    
    /* Cores para FILA */
    .stage-count.fila .count-number,
    .stage-count.fila .count-label {
        color: #b45309; /* Cor âmbar/laranja */
    }
    
    /* Cores para PRONTO */
    .stage-count.pronto .count-number,
    .stage-count.pronto .count-label {
        color: #15803d; /* Cor verde */
    }
    </style>
    """, unsafe_allow_html=True)
    
    cols = st.columns(5)
    today_date = pd.to_datetime('today').normalize().date()
    
    for i in range(5):
        current_date = st.session_state.calendar_start_date + timedelta(days=i)
        date_key = current_date.date()
        
        fila_count = reunioes_por_etapa.get('FILA', {}).get(date_key, 0)
        pronto_count = reunioes_por_etapa.get('PRONTO', {}).get(date_key, 0)
        
        day_name = dias_semana[current_date.weekday()]
        day_str = current_date.strftime('%d/%m')
        
        is_today_class = "day-box-today" if date_key == today_date else ""

        with cols[i]:
            st.markdown(f"""
            <div class="day-box {is_today_class}">
                <div class="day-header">
                    <div class="day-name">{day_name}</div>
                    <div class="day-date">{day_str}</div>
                </div>
                <div class="day-counts-container">
                    <div class="stage-count fila">
                        <div class="count-number">{fila_count}</div>
                        <div class="count-label">Fila</div>
                    </div>
                    <div class="stage-count pronto">
                        <div class="count-number">{pronto_count}</div>
                        <div class="count-label">Pronto</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Exibir o dataframe completo abaixo do calendário, se houver agendamentos
    if not reunioes_por_etapa.empty:
        with st.expander("Ver todos os agendamentos por etapa"):
            st.dataframe(reunioes_por_etapa.sort_index()) 