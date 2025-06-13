import streamlit as st
import pandas as pd

def show_pendencias_futuras(df_filtrado):
    """
    Exibe a análise de pendências futuras, prevendo a demanda com base
    nas etapas que cada família já concluiu.
    """
    st.header("Previsão de Demanda (Pendências Futuras)", divider='rainbow')
    st.write("Esta seção antecipa a demanda futura com base nas etapas que cada família já concluiu.")

    if df_filtrado.empty:
        st.warning("Não há dados para exibir com os filtros selecionados.")
        return

    # Ordem do processo e colunas de conclusão correspondentes
    pipeline = {
        'Procuração': 'PROCURAÇÃO - DATA CONCLUSÃO',
        'Análise Documental': 'ANALISE - DATA CONCLUSÃO',
        'Tradução': 'TRADUÇÃO - DATA DE ENTREGA',
        'Apostila': 'APOSTILA - DATA DE ENTREGA',
        'Drive': 'DRIVE - DATA DE ENTREGA'
    }
    
    # Garante que as colunas de data existam e as converte
    df = df_filtrado.copy()
    for etapa, col in pipeline.items():
        if col not in df.columns:
            st.error(f"A coluna de conclusão '{col}' para a etapa '{etapa}' não foi encontrada.")
            return
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Lógica de "Trabalho Total Pendente"
    demanda_futura = {}
    
    # Para cada etapa, a demanda é o total de famílias que ainda não a concluíram.
    for etapa, col_conclusao in pipeline.items():
        familias_pendentes = df[df[col_conclusao].isna()]
        demanda_futura[etapa] = familias_pendentes['ID FAMÍLIA'].tolist()

    st.subheader("Trabalho Total Pendente por Etapa", divider='blue')

    # Exibir a demanda futura em métricas e permitir detalhamento
    if not any(demanda_futura.values()):
        st.success("Nenhuma demanda futura identificada com base nas etapas concluídas.")
        return

    num_cols = 3
    cols = st.columns(num_cols)
    col_idx = 0

    for etapa, familias in demanda_futura.items():
        count = len(set(familias)) # Usa set para garantir contagem única
        if count > 0:
            with cols[col_idx % num_cols]:
                st.metric(f"Pendentes em {etapa}", count)
                with st.expander(f"Ver {count} famílias"):
                    st.dataframe(pd.DataFrame(list(set(familias)), columns=['ID FAMÍLIA']), hide_index=True)
            col_idx += 1
            
    # Se nenhuma demanda foi exibida (porque todas eram 0)
    if col_idx == 0:
        st.success("Todas as famílias que iniciaram o processo já o concluíram.") 