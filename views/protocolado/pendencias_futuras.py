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

    # Dicionário para armazenar a demanda futura e a lista de famílias
    demanda_futura = {etapa: [] for etapa in pipeline.keys()}
    pipeline_etapas = list(pipeline.keys())

    # Identifica o último estágio concluído para cada família
    for _, familia in df.iterrows():
        ultimo_estagio_concluido_idx = -1
        
        # Encontra o índice do último estágio com data de conclusão
        for i, col in enumerate(pipeline.values()):
            if pd.notna(familia[col]):
                ultimo_estagio_concluido_idx = i

        # Se um estágio foi concluído, os próximos são demanda futura
        if ultimo_estagio_concluido_idx > -1:
            # Itera a partir do estágio seguinte ao último concluído
            for i in range(ultimo_estagio_concluido_idx + 1, len(pipeline_etapas)):
                etapa_futura = pipeline_etapas[i]
                col_futura = pipeline[etapa_futura]
                # Adiciona a família à lista de demanda se ela ainda não concluiu essa etapa futura
                if pd.isna(familia[col_futura]):
                    demanda_futura[etapa_futura].append(familia['ID FAMÍLIA'])

    st.subheader("Demanda Futura por Etapa", divider='blue')

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
                st.metric(f"Demanda para {etapa}", count)
                with st.expander(f"Ver {count} famílias"):
                    st.dataframe(pd.DataFrame(list(set(familias)), columns=['ID FAMÍLIA']), hide_index=True)
            col_idx += 1
            
    # Se nenhuma demanda foi exibida (porque todas eram 0)
    if col_idx == 0:
        st.success("Todas as famílias que iniciaram o processo já o concluíram.") 