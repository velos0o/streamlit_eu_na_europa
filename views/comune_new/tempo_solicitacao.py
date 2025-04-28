import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Importar função de simplificação de estágio
from .visao_geral import simplificar_nome_estagio_comune

def exibir_tempo_solicitacao(df_comune):
    """
    Exibe a análise do tempo de solicitação (em dias) para os processos de Comune,
    agrupado por faixas de tempo e com filtro por nome (TITLE).
    """
    st.subheader("Análise de Tempo de Solicitação")

    if df_comune.empty:
        st.warning("Não há dados de Comune para analisar o tempo de solicitação.")
        return

    # --- Colunas Necessárias ---
    coluna_data_criacao = 'CREATED_TIME'
    coluna_titulo = 'TITLE' # Coluna para busca por família/nome
    coluna_estagio = 'STAGE_ID' # Coluna original do estágio

    colunas_necessarias = [coluna_data_criacao, coluna_titulo, coluna_estagio]
    colunas_ausentes = [col for col in colunas_necessarias if col not in df_comune.columns]
    if colunas_ausentes:
        st.error(f"Colunas necessárias não encontradas: {', '.join(colunas_ausentes)}.")
        return

    # --- Pré-processamento --- 
    # Garantir que a coluna de data está no formato correto
    df_comune[coluna_data_criacao] = pd.to_datetime(df_comune[coluna_data_criacao], errors='coerce')
    df_processar = df_comune.dropna(subset=[coluna_data_criacao]).copy() # Usar .copy() para evitar SettingWithCopyWarning

    if df_processar.empty:
        st.warning("Não há datas de criação válidas nos dados.")
        return

    # Calcular tempo em dias desde a criação até hoje
    data_hoje = pd.to_datetime(datetime.now().date())
    df_processar['TEMPO_DIAS'] = (data_hoje - df_processar[coluna_data_criacao]).dt.days

    # Remover tempos negativos (caso haja datas futuras)
    df_processar = df_processar[df_processar['TEMPO_DIAS'] >= 0]

    if df_processar.empty:
        st.warning("Nenhum processo com tempo de criação válido encontrado.")
        return

    # --- Filtro por Nome (TITLE) ---
    termo_busca_titulo = st.text_input("Buscar por Nome/Família (Título):", key="busca_titulo_tempo")
    
    df_filtrado = df_processar.copy()
    if termo_busca_titulo:
        termo_busca_titulo = termo_busca_titulo.strip()
        # Filtrar usando str.contains (case-insensitive)
        df_filtrado = df_filtrado[df_filtrado[coluna_titulo].str.contains(termo_busca_titulo, case=False, na=False)]

    if df_filtrado.empty:
        st.info("Nenhum processo encontrado para o termo de busca.")
        # Poderíamos parar aqui ou mostrar as métricas/gráfico vazios
        # Vamos continuar para mostrar a estrutura vazia
        # st.stop()
        
    # --- Métricas Resumo (Calculadas sobre dados filtrados pela busca) --- 
    st.markdown("##### Métricas de Tempo (Dias) - Filtro Aplicado")
    if not df_filtrado.empty:
        med_tempo_medio = df_filtrado['TEMPO_DIAS'].mean()
        med_tempo_mediana = df_filtrado['TEMPO_DIAS'].median()
        med_tempo_max = df_filtrado['TEMPO_DIAS'].max()
    else:
        med_tempo_medio, med_tempo_mediana, med_tempo_max = 0, 0, 0

    col_met1, col_met2, col_met3 = st.columns(3)
    with col_met1:
        st.metric("Tempo Médio", f"{med_tempo_medio:.1f}")
    with col_met2:
        st.metric("Tempo Mediano", f"{med_tempo_mediana:.1f}")
    with col_met3:
        st.metric("Tempo Máximo", f"{med_tempo_max:.0f}")

    st.markdown("---")

    # --- Criação das Faixas de Tempo --- 
    bins = [-1, 30, 60, 100, 120, 160, 180, 200, 220, 240, float('inf')] # -1 para incluir 0
    labels = ['0-30', '31-60', '61-100', '101-120', '121-160', '161-180', '181-200', '201-220', '221-240', '241+'] # Labels mais curtos
    
    # Aplicar apenas se houver dados após o filtro
    if not df_filtrado.empty:
        df_filtrado['FAIXA_TEMPO'] = pd.cut(df_filtrado['TEMPO_DIAS'], bins=bins, labels=labels, right=True)
        # Agrupar para o gráfico de barras
        contagem_por_faixa = df_filtrado.groupby('FAIXA_TEMPO', observed=False).size().reset_index(name='CONTAGEM')
    else:
        # Criar DataFrame vazio com as colunas certas para evitar erro no gráfico
        contagem_por_faixa = pd.DataFrame({'FAIXA_TEMPO': labels, 'CONTAGEM': [0]*len(labels)})
        # Garantir a ordem correta das faixas
        contagem_por_faixa['FAIXA_TEMPO'] = pd.Categorical(contagem_por_faixa['FAIXA_TEMPO'], categories=labels, ordered=True)
        contagem_por_faixa = contagem_por_faixa.sort_values('FAIXA_TEMPO')

    # --- Gráfico de Barras por Faixa de Tempo --- 
    st.markdown("##### Distribuição por Faixa de Tempo (Dias)")
    
    # Definir uma cor base (azul do seu título)
    cor_barra = '#3B82F6'

    try:
        fig = px.bar(
            contagem_por_faixa, 
            x='FAIXA_TEMPO', 
            y='CONTAGEM',
            text='CONTAGEM', # Adiciona o valor da contagem na barra
            title="Número de Processos por Faixa de Tempo", # Título mais curto
            labels={'FAIXA_TEMPO': 'Faixa de Tempo (Dias)', 'CONTAGEM': 'Nº Processos'} # Labels mais curtos
        )
        fig.update_traces(
            textposition='outside', # Posição do texto (pode ser 'auto', 'inside')
            marker_color=cor_barra, # Definir cor da barra
            textfont_size=12, # Tamanho da fonte do texto na barra
            hovertemplate='<b>%{x}</b><br>Processos: %{y}<extra></extra>' # Tooltip personalizado
        )
        fig.update_layout(
            xaxis_title=None, # Remover título do eixo X (já está claro pelas labels)
            yaxis_title="Número de Processos",
            xaxis=dict(
                categoryorder='array', # Garante a ordem correta das barras
                categoryarray=labels,
                showgrid=False # Remover grid X
            ),
            template="plotly_white", # Template mais limpo
            title_font_size=18, # Ajustar tamanho do título
            yaxis=dict(
                showgrid=True, # Manter grid Y
                gridcolor='LightGray'
            ),
            bargap=0.2, # Aumentar um pouco o espaço entre barras
            margin=dict(t=50, b=50, l=50, r=30) # Ajustar margens
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar o gráfico de barras: {e}")

    # --- Tabela com Processos mais Antigos (Filtrada pela busca) ---
    st.markdown("---")
    st.markdown("##### Detalhes dos Processos Exibidos (Top 10 Mais Antigos)")
    if not df_filtrado.empty:
        df_top10_antigos = df_filtrado.nlargest(10, 'TEMPO_DIAS').copy() # Usar .copy()
        
        # --- Adicionar nome legível do estágio --- 
        if coluna_estagio in df_top10_antigos.columns:
            df_top10_antigos['Estágio Legível'] = df_top10_antigos[coluna_estagio].apply(simplificar_nome_estagio_comune)
        else:
            df_top10_antigos['Estágio Legível'] = "N/A"

        # Selecionar colunas relevantes para exibir - REMOVER STAGE_ID, ADICIONAR LEGÍVEL
        colunas_exibir = ['ID', 'TITLE', coluna_data_criacao, 'TEMPO_DIAS', 'FAIXA_TEMPO', 'Estágio Legível']
        colunas_exibir = [col for col in colunas_exibir if col in df_top10_antigos.columns] # Garantir que existem
        
        if not colunas_exibir:
            st.warning("Não foi possível encontrar colunas para exibir na tabela.")
        else: 
            st.dataframe(
                df_top10_antigos[colunas_exibir],
                use_container_width=True,
                column_config={
                    coluna_data_criacao: st.column_config.DateColumn("Data Criação", format="DD/MM/YYYY"),
                    "TEMPO_DIAS": st.column_config.NumberColumn("Tempo (Dias)"),
                    "FAIXA_TEMPO": st.column_config.TextColumn("Faixa Tempo"), # Usar TextColumn
                    "Estágio Legível": st.column_config.TextColumn("Estágio") # Configurar nova coluna
                }
            )
    else:
         st.caption("Nenhum processo para exibir na tabela com os filtros atuais.") 