import streamlit as st
import pandas as pd
import altair as alt
from utils.dataframe_utils import ensure_pandas_df

def debug_dataframe_type(df, name="DataFrame"):
    """Debug detalhado do tipo de DataFrame dentro do Streamlit."""
    st.write(f"🔍 DEBUG - {name}:")
    st.write(f"   Tipo: {type(df)}")
    st.write(f"   String do tipo: {str(type(df))}")
    st.write(f"   É pandas?: {isinstance(df, pd.DataFrame)}")
    st.write(f"   Contém 'narwhals'?: {'narwhals' in str(type(df))}")
    
    if hasattr(df, 'shape'):
        st.write(f"   Shape: {df.shape}")
    
    return df

def show_produtividade_debug(df_protocolados):
    """
    Versão DEBUG da análise de produtividade para rastrear problemas narwhals.
    """
    st.header("🔍 DEBUG - Análise de Produtividade", divider='rainbow')
    st.write("Versão debug para rastrear problemas de DataFrames narwhals.")
    
    # Debug do DataFrame de entrada
    st.subheader("1️⃣ DataFrame de Entrada")
    df_protocolados = debug_dataframe_type(df_protocolados, "df_protocolados recebido")

    if df_protocolados.empty:
        st.warning("Não há dados de protocolados para exibir.")
        return

    # Mapeamento de Etapas e Colunas de Conclusão
    mapeamento_etapas = {
        'Procuração': 'PROCURAÇÃO - DATA CONCLUSÃO',
        'Análise Documental': 'ANALISE - DATA CONCLUSÃO',
        'Tradução': 'TRADUÇÃO - DATA DE ENTREGA',
        'Apostila': 'APOSTILA - DATA DE ENTREGA',
        'Drive': 'DRIVE - DATA DE ENTREGA'
    }

    # Preparação dos Dados com debug detalhado
    st.subheader("2️⃣ Processamento de Etapas")
    lista_tarefas = []
    
    for etapa, data_col in mapeamento_etapas.items():
        if data_col in df_protocolados.columns:
            st.write(f"📋 Processando etapa: **{etapa}**")
            
            # Slice do DataFrame - PONTO CRÍTICO
            try:
                df_etapa = df_protocolados[['ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', data_col]].copy()
                df_etapa = debug_dataframe_type(df_etapa, f"df_etapa {etapa} após slice")
                
                # Verificar se o slice gerou narwhals
                if 'narwhals' in str(type(df_etapa)):
                    st.error(f"🚨 PROBLEMA ENCONTRADO! O slice da etapa {etapa} gerou um DataFrame narwhals!")
                    st.write(f"DataFrame original: {type(df_protocolados)}")
                    st.write(f"DataFrame após slice: {type(df_etapa)}")
                    
                    # Tentar corrigir
                    st.write("🔧 Tentando correção...")
                    df_etapa = ensure_pandas_df(df_etapa)
                    df_etapa = debug_dataframe_type(df_etapa, f"df_etapa {etapa} após correção")
                
                # Continuar processamento
                df_etapa.dropna(subset=[data_col, 'CONSULTOR RESPONSÁVEL'], inplace=True)
                df_etapa = df_etapa[df_etapa['CONSULTOR RESPONSÁVEL'].str.strip() != '']

                if df_etapa.empty:
                    st.write(f"   ⚠️ Etapa {etapa} vazia após filtros")
                    continue

                # Conversão de data
                df_etapa[data_col] = pd.to_datetime(df_etapa[data_col], format='%d/%m/%Y', dayfirst=True, errors='coerce')
                df_etapa = debug_dataframe_type(df_etapa, f"df_etapa {etapa} após to_datetime")
                
                df_etapa.dropna(subset=[data_col], inplace=True)
                
                df_etapa.rename(columns={data_col: 'Data Conclusão'}, inplace=True)
                df_etapa['Etapa'] = etapa
                df_etapa = debug_dataframe_type(df_etapa, f"df_etapa {etapa} final")
                
                lista_tarefas.append(ensure_pandas_df(df_etapa))
                st.success(f"   ✅ Etapa {etapa} processada com sucesso")
                
            except Exception as e:
                st.error(f"❌ Erro ao processar etapa {etapa}: {e}")
                st.write(f"Traceback: {str(e)}")
    
    if not lista_tarefas:
        st.info("Nenhuma tarefa concluída foi encontrada.")
        return
    
    # Concat com debug
    st.subheader("3️⃣ Concatenação de Dados")
    try:
        df_produtividade = pd.concat(lista_tarefas, ignore_index=True)
        df_produtividade = debug_dataframe_type(df_produtividade, "df_produtividade após concat")
        
        df_produtividade = ensure_pandas_df(df_produtividade)
        df_produtividade = debug_dataframe_type(df_produtividade, "df_produtividade após ensure_pandas_df")
        
    except Exception as e:
        st.error(f"❌ Erro no concat: {e}")
        return

    # Filtros simplificados para debug
    st.subheader("4️⃣ Filtros (Simplificados para Debug)")
    
    consultores_unicos = sorted(df_produtividade['CONSULTOR RESPONSÁVEL'].unique())
    consultores_selecionados = st.multiselect(
        "Selecione o(s) Consultor(es)",
        options=consultores_unicos,
        default=consultores_unicos[:2] if len(consultores_unicos) > 2 else consultores_unicos
    )
    
    if not consultores_selecionados:
        st.warning("Selecione pelo menos um consultor.")
        return
    
    # Aplicação dos Filtros com debug
    st.subheader("5️⃣ Aplicação de Filtros")
    try:
        df_filtrado_prod = df_produtividade[
            df_produtividade['CONSULTOR RESPONSÁVEL'].isin(consultores_selecionados)
        ]
        df_filtrado_prod = debug_dataframe_type(df_filtrado_prod, "df_filtrado_prod após filtro")
        
        df_filtrado_prod = ensure_pandas_df(df_filtrado_prod)
        df_filtrado_prod = debug_dataframe_type(df_filtrado_prod, "df_filtrado_prod após ensure_pandas_df")
        
    except Exception as e:
        st.error(f"❌ Erro na aplicação de filtros: {e}")
        return

    if df_filtrado_prod.empty:
        st.warning("Nenhuma tarefa concluída encontrada para os filtros selecionados.")
        return

    # Métricas Gerais
    total_tarefas = len(df_filtrado_prod)
    st.metric("Total de Tarefas Concluídas", f"{total_tarefas}")

    # Gráficos com debug detalhado
    st.subheader("6️⃣ Criação de Gráficos - PONTO CRÍTICO")
    
    try:
        # Groupby com debug
        st.write("📊 Fazendo groupby...")
        produtividade_diaria = df_filtrado_prod.groupby(df_filtrado_prod['Data Conclusão'].dt.date).size().reset_index(name='Contagem')
        produtividade_diaria = debug_dataframe_type(produtividade_diaria, "produtividade_diaria após groupby")
        
        produtividade_diaria = ensure_pandas_df(produtividade_diaria)
        produtividade_diaria = debug_dataframe_type(produtividade_diaria, "produtividade_diaria após ensure_pandas_df")
        
        produtividade_diaria.rename(columns={'Data Conclusão': 'Data'}, inplace=True)
        produtividade_diaria = debug_dataframe_type(produtividade_diaria, "produtividade_diaria após rename")
        
        # Verificação final antes do Altair
        if 'narwhals' in str(type(produtividade_diaria)):
            st.error("🚨 PROBLEMA! DataFrame ainda é narwhals antes do Altair!")
            st.write(f"Tipo: {type(produtividade_diaria)}")
            
            # Tentativa de correção forçada
            produtividade_diaria = pd.DataFrame(produtividade_diaria)
            st.write(f"Após pd.DataFrame forçado: {type(produtividade_diaria)}")
        
        # Criação do gráfico Altair - MOMENTO CRÍTICO
        st.write("🎨 Criando gráfico Altair...")
        
        # Conversão forçada para evitar problemas com narwhals interno do Altair
        from utils import force_pandas_for_altair
        df_for_altair = force_pandas_for_altair(produtividade_diaria)
        df_for_altair = debug_dataframe_type(df_for_altair, "df_for_altair (forçado)")
        
        base = alt.Chart(df_for_altair).encode(
            x=alt.X('Data:T', title='Data da Conclusão'),
            y=alt.Y('Contagem:Q', title='Nº de Tarefas Concluídas'),
            tooltip=['Data:T', 'Contagem:Q']
        )

        linha = base.mark_line(color='#1E88E5', point=True)
        pontos = base.mark_point(size=80, filled=True, color='#1E88E5')
        
        chart = (linha + pontos).interactive().properties(
            title='Produtividade Diária (Tarefas Concluídas) - DEBUG'
        )
        
        st.altair_chart(chart, use_container_width=True)
        st.success("✅ Gráfico Altair criado com sucesso!")
        
    except Exception as e:
        st.error(f"❌ ERRO na criação do gráfico: {e}")
        st.write(f"Tipo do DataFrame problemático: {type(produtividade_diaria) if 'produtividade_diaria' in locals() else 'Não definido'}")
        
        # Mostrar traceback completo
        import traceback
        st.code(traceback.format_exc())

    # Tabela de Produtividade com debug
    st.subheader("7️⃣ Tabela de Produtividade")
    try:
        tabela_produtividade = pd.pivot_table(
            ensure_pandas_df(df_filtrado_prod),
            values='ID FAMÍLIA',
            index='CONSULTOR RESPONSÁVEL',
            columns='Etapa',
            aggfunc='count',
            fill_value=0,
            margins=True,
            margins_name='Total Geral'
        )
        tabela_produtividade = debug_dataframe_type(tabela_produtividade, "tabela_produtividade")
        
        st.dataframe(ensure_pandas_df(tabela_produtividade), use_container_width=True)
        st.success("✅ Tabela criada com sucesso!")
        
    except Exception as e:
        st.error(f"❌ Erro na criação da tabela: {e}")
        import traceback
        st.code(traceback.format_exc()) 