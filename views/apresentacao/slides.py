import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Este arquivo contém funções de slide simplificadas para suportar a migração
# Essas funções serão usadas se o arquivo original apresentacao_conclusoes.py 
# não contiver as funções necessárias.

def slide_metricas_destaque(df, df_todos, date_from, date_to):
    """Versão simplificada da função slide_metricas_destaque"""
    st.subheader("Métricas de Destaque")
    
    # Calcular métricas básicas
    total_conclusoes = len(df) if not df.empty else 0
    total_negocios = len(df_todos) if not df_todos.empty else 0
    
    # Mostrar as métricas em cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total de Conclusões", total_conclusoes)
        
    with col2:
        st.metric("Total de Registros", total_negocios)
    
    # Mostrar taxa de conclusão
    if total_negocios > 0:
        taxa_conclusao = round((total_conclusoes / total_negocios * 100), 1)
        st.metric("Taxa de Conclusão", f"{taxa_conclusao}%")
    
    # Informar sobre datas
    st.info(f"Período analisado: {date_from.strftime('%d/%m/%Y')} a {date_to.strftime('%d/%m/%Y')}")

def slide_ranking_produtividade(df, df_todos):
    """Versão simplificada da função slide_ranking_produtividade"""
    st.subheader("Ranking de Produtividade")
    
    # Verificar se há dados suficientes
    if df.empty or 'ASSIGNED_BY_NAME' not in df.columns:
        st.warning("Não há dados suficientes para gerar o ranking.")
        return
    
    # Agrupar por responsável e contar conclusões
    ranking = df.groupby('ASSIGNED_BY_NAME').size().reset_index(name='Total')
    
    # Ordenar pelo total em ordem decrescente
    ranking = ranking.sort_values('Total', ascending=False)
    
    # Mostrar tabela
    st.write("Ranking de Produtividade por Responsável:")
    st.dataframe(ranking)

def slide_analise_diaria(df, date_from, date_to):
    """Versão simplificada da função slide_analise_diaria"""
    st.subheader("Análise Diária")
    
    if df.empty or 'DATA_CONCLUSAO' not in df.columns:
        st.warning("Não há dados suficientes para análise diária.")
        return
    
    # Agrupar por data de conclusão
    df_diario = df.groupby(df['DATA_CONCLUSAO'].dt.date).size().reset_index(name='Conclusões')
    
    # Mostrar gráfico
    st.line_chart(df_diario.set_index('DATA_CONCLUSAO'))
    
    # Informações sobre o período
    st.info(f"Período analisado: {date_from.strftime('%d/%m/%Y')} a {date_to.strftime('%d/%m/%Y')}")

def slide_analise_semanal(df):
    """Versão simplificada da função slide_analise_semanal"""
    st.subheader("Análise Semanal")
    
    if df.empty or 'DATA_CONCLUSAO' not in df.columns:
        st.warning("Não há dados suficientes para análise semanal.")
        return
    
    # Adicionar coluna de semana
    df_temp = df.copy()
    df_temp['Semana'] = df_temp['DATA_CONCLUSAO'].dt.strftime('%Y-%V')
    
    # Agrupar por semana
    df_semanal = df_temp.groupby('Semana').size().reset_index(name='Conclusões')
    
    # Mostrar gráfico
    st.bar_chart(df_semanal.set_index('Semana'))

def slide_analise_dia_semana(df):
    """Versão simplificada da função slide_analise_dia_semana"""
    st.subheader("Análise por Dia da Semana")
    
    if df.empty or 'DATA_CONCLUSAO' not in df.columns:
        st.warning("Não há dados suficientes para análise por dia da semana.")
        return
    
    # Adicionar coluna de dia da semana
    df_temp = df.copy()
    df_temp['Dia da Semana'] = df_temp['DATA_CONCLUSAO'].dt.day_name()
    
    # Agrupar por dia da semana
    df_dia_semana = df_temp.groupby('Dia da Semana').size().reset_index(name='Conclusões')
    
    # Mostrar gráfico
    st.bar_chart(df_dia_semana.set_index('Dia da Semana'))

def slide_analise_horario(df):
    """Versão simplificada da função slide_analise_horario"""
    st.subheader("Análise por Hora do Dia")
    
    if df.empty or 'DATA_CONCLUSAO' not in df.columns:
        st.warning("Não há dados suficientes para análise por horário.")
        return
    
    # Adicionar coluna de hora
    df_temp = df.copy()
    df_temp['Hora'] = df_temp['DATA_CONCLUSAO'].dt.hour
    
    # Agrupar por hora
    df_hora = df_temp.groupby('Hora').size().reset_index(name='Conclusões')
    
    # Mostrar gráfico
    st.bar_chart(df_hora.set_index('Hora'))

def slide_producao_metricas_macro(df):
    """Versão simplificada da função slide_producao_metricas_macro"""
    st.subheader("Produção - Métricas Macro")
    
    st.write("Métricas de produção")
    
    # Verificar dados de produção na sessão
    df_producao = st.session_state.get('df_producao', None)
    
    if df_producao is None or df_producao.empty:
        st.warning("Não há dados de produção disponíveis.")
        return
    
    # Mostrar total de registros
    st.metric("Total de Registros", len(df_producao))
    
    # Análise por status
    if 'UF_CRM_HIGILIZACAO_STATUS' in df_producao.columns:
        status_counts = df_producao['UF_CRM_HIGILIZACAO_STATUS'].value_counts()
        st.write("Distribuição por Status:")
        st.dataframe(status_counts)

def slide_producao_status_responsavel(df):
    """Versão simplificada da função slide_producao_status_responsavel"""
    st.subheader("Produção - Status por Responsável")
    
    # Verificar dados de produção na sessão
    df_producao = st.session_state.get('df_producao', None)
    
    if df_producao is None or df_producao.empty:
        st.warning("Não há dados de produção disponíveis.")
        return
    
    # Verificar colunas necessárias
    if 'ASSIGNED_BY_NAME' not in df_producao.columns or 'UF_CRM_HIGILIZACAO_STATUS' not in df_producao.columns:
        st.warning("Dados não contêm as colunas necessárias.")
        return
    
    # Mostrar tabela de status por responsável
    st.write("Status por Responsável:")
    status_resp = pd.crosstab(df_producao['ASSIGNED_BY_NAME'], df_producao['UF_CRM_HIGILIZACAO_STATUS'])
    st.dataframe(status_resp)

def slide_producao_pendencias_responsavel(df):
    """Versão simplificada que redireciona para a função completa em producao/pendencias_responsavel.py"""
    # Importar a versão completa da função do módulo correspondente
    from views.apresentacao.producao.pendencias_responsavel import slide_producao_pendencias_responsavel as slide_pendencias_completo
    
    # Verificar dados de produção na sessão
    df_producao = st.session_state.get('df_producao', None)
    
    if df_producao is None or df_producao.empty:
        st.warning("Não há dados de produção disponíveis.")
        return
    
    # Chamar a implementação completa
    slide_pendencias_completo(df_producao)

def slide_cartorio_visao_geral(df):
    """Versão simplificada da função slide_cartorio_visao_geral"""
    st.subheader("Cartório - Visão Geral")
    
    # Verificar dados de cartório na sessão
    df_cartorio = st.session_state.get('df_cartorio', None)
    
    if df_cartorio is None or df_cartorio.empty:
        st.warning("Não há dados de cartório disponíveis.")
        return
    
    # Mostrar visão geral
    st.metric("Total de Registros", len(df_cartorio))
    
    # Mostrar distribuição por cartório
    if 'NOME_CARTORIO' in df_cartorio.columns:
        cartorio_counts = df_cartorio['NOME_CARTORIO'].value_counts()
        st.write("Distribuição por Cartório:")
        st.dataframe(cartorio_counts)

def slide_cartorio_analise_familias(df):
    """Versão simplificada da função slide_cartorio_analise_familias"""
    st.subheader("Cartório - Análise de Famílias")
    
    # Verificar dados de famílias na sessão
    df_familias = st.session_state.get('df_familias', None)
    
    if df_familias is None or df_familias.empty:
        st.warning("Não há dados de famílias disponíveis.")
        return
    
    # Mostrar visão geral
    st.metric("Total de Famílias", len(df_familias))
    
    # Mostrar estatísticas básicas
    if 'TOTAL_CERTIDOES' in df_familias.columns and 'CERTIDOES_ENTREGUES' in df_familias.columns:
        total_certidoes = df_familias['TOTAL_CERTIDOES'].sum()
        certidoes_entregues = df_familias['CERTIDOES_ENTREGUES'].sum()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total de Certidões", total_certidoes)
        
        with col2:
            st.metric("Certidões Entregues", certidoes_entregues)
            
        if total_certidoes > 0:
            taxa_entrega = round((certidoes_entregues / total_certidoes * 100), 1)
            st.metric("Taxa de Entrega", f"{taxa_entrega}%")

def slide_cartorio_ids_familia(df):
    """Versão simplificada da função slide_cartorio_ids_familia"""
    st.subheader("Cartório - IDs de Família")
    
    # Verificar dados de cartório na sessão
    df_cartorio = st.session_state.get('df_cartorio', None)
    
    if df_cartorio is None or df_cartorio.empty:
        st.warning("Não há dados de cartório disponíveis.")
        return
    
    # Mostrar mensagem simples
    st.write("Análise de IDs de família - versão simplificada")
    st.info("Para visualização completa, acessar através do arquivo original ou implementar a análise no novo módulo.") 