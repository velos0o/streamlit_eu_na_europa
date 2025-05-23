import streamlit as st
import pandas as pd
from datetime import datetime, date
from .utils import simplificar_nome_estagio, categorizar_estagio

def exibir_pesquisa_br(df_cartorio):
    """
    Exibe relatório básico do andamento da Pesquisa BR (Pipeline 104).
    Mostra métricas de andamento das pesquisas e uma tabela detalhada.
    """
    # --- Carregar CSS Compilado ---
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS principal (main.css) não encontrado.")
    # --- Fim Carregar CSS ---

    st.subheader("🔍 Pesquisa BR - Pipeline 104")

    if df_cartorio is None or df_cartorio.empty:
        st.warning("Dados de cartório não disponíveis para o relatório de Pesquisa BR.")
        return

    # Filtrar apenas registros do pipeline 104
    df_pesquisa = df_cartorio[df_cartorio['CATEGORY_ID'].astype(str) == '104'].copy()
    
    if df_pesquisa.empty:
        st.info("Nenhum registro encontrado no Pipeline 104 (Pesquisa BR).")
        return

    # Verificar colunas necessárias
    colunas_requeridas = ['ID', 'STAGE_ID', 'UF_CRM_34_ID_REQUERENTE', 'UF_CRM_34_NOME_FAMILIA', 'ASSIGNED_BY_NAME']
    colunas_faltantes = [col for col in colunas_requeridas if col not in df_pesquisa.columns]

    if colunas_faltantes:
        st.error(f"Colunas necessárias não encontradas: {', '.join(colunas_faltantes)}")
        return

    # --- Pré-processamento ---
    df_pesquisa['STAGE_ID'] = df_pesquisa['STAGE_ID'].astype(str)
    df_pesquisa['ESTAGIO_LEGIVEL'] = df_pesquisa['STAGE_ID'].apply(simplificar_nome_estagio)
    df_pesquisa['CATEGORIA_ESTAGIO'] = df_pesquisa['ESTAGIO_LEGIVEL'].apply(categorizar_estagio)
    
    # Tratar campos nulos
    df_pesquisa['UF_CRM_34_ID_REQUERENTE'] = df_pesquisa['UF_CRM_34_ID_REQUERENTE'].fillna('Req. Desconhecido').astype(str)
    df_pesquisa['UF_CRM_34_NOME_FAMILIA'] = df_pesquisa['UF_CRM_34_NOME_FAMILIA'].fillna('Família Desconhecida').astype(str)
    df_pesquisa['ASSIGNED_BY_NAME'] = df_pesquisa['ASSIGNED_BY_NAME'].fillna('Responsável Desconhecido').astype(str)

    # --- Métricas Gerais ---
    total_pesquisas = len(df_pesquisa)
    total_requerentes = df_pesquisa[df_pesquisa['UF_CRM_34_ID_REQUERENTE'] != 'Req. Desconhecido']['UF_CRM_34_ID_REQUERENTE'].nunique()
    total_familias = df_pesquisa[df_pesquisa['UF_CRM_34_NOME_FAMILIA'] != 'Família Desconhecida']['UF_CRM_34_NOME_FAMILIA'].nunique()
    
    # Contar por estágio
    aguardando_pesquisador = len(df_pesquisa[df_pesquisa['ESTAGIO_LEGIVEL'] == 'AGUARDANDO PESQUISADOR'])
    pesquisa_andamento = len(df_pesquisa[df_pesquisa['ESTAGIO_LEGIVEL'] == 'PESQUISA EM ANDAMENTO'])
    pesquisa_pronta = len(df_pesquisa[df_pesquisa['ESTAGIO_LEGIVEL'] == 'PESQUISA PRONTA PARA EMISSÃO'])
    pesquisa_nao_encontrada = len(df_pesquisa[df_pesquisa['ESTAGIO_LEGIVEL'] == 'PESQUISA NÃO ENCONTRADA'])
    
    # Calcular taxa de conclusão
    pesquisas_finalizadas = pesquisa_pronta + pesquisa_nao_encontrada
    taxa_conclusao = (pesquisas_finalizadas / total_pesquisas * 100) if total_pesquisas > 0 else 0

    # --- Exibir Métricas ---
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total Pesquisas", f"{total_pesquisas:,}")
    col2.metric("Requerentes", f"{total_requerentes:,}")
    col3.metric("Famílias", f"{total_familias:,}")
    col4.metric("Finalizadas", f"{pesquisas_finalizadas:,}")
    col5.metric("Taxa Conclusão", f"{taxa_conclusao:.1f}%")

    st.markdown("---")

    # --- Detalhamento por Estágio ---
    st.markdown("#### 📊 Andamento por Estágio")
    
    col_est1, col_est2, col_est3, col_est4 = st.columns(4)
    
    # Cards com classes SCSS (substituindo CSS inline)
    col_est1.markdown(f"""
    <div class="stage-card stage-card--aguardando">
        <div class="stage-card__icon">🕐</div>
        <div class="stage-card__title">Aguardando</div>
        <div class="stage-card__value">{aguardando_pesquisador}</div>
        <div class="stage-card__subtitle">Aguardando Pesquisador</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_est2.markdown(f"""
    <div class="stage-card stage-card--andamento">
        <div class="stage-card__icon">🔄</div>
        <div class="stage-card__title">Em Andamento</div>
        <div class="stage-card__value">{pesquisa_andamento}</div>
        <div class="stage-card__subtitle">Pesquisa em Andamento</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_est3.markdown(f"""
    <div class="stage-card stage-card--prontas">
        <div class="stage-card__icon">✅</div>
        <div class="stage-card__title">Prontas</div>
        <div class="stage-card__value">{pesquisa_pronta}</div>
        <div class="stage-card__subtitle">Pronta para Emissão</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_est4.markdown(f"""
    <div class="stage-card stage-card--nao-encontradas">
        <div class="stage-card__icon">❌</div>
        <div class="stage-card__title">Não Encontradas</div>
        <div class="stage-card__value">{pesquisa_nao_encontrada}</div>
        <div class="stage-card__subtitle">Pesquisa Não Encontrada</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Filtros ---
    with st.expander("Filtros", expanded=False):
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            estagios_unicos = sorted(df_pesquisa['ESTAGIO_LEGIVEL'].unique().tolist())
            filtro_estagio = st.selectbox(
                "Filtrar por Estágio",
                options=['Todos'] + estagios_unicos,
                index=0,
                key="filtro_estagio_pesquisa_br"
            )
        
        with col_filtro2:
            responsaveis_unicos = sorted(df_pesquisa['ASSIGNED_BY_NAME'].unique().tolist())
            filtro_responsavel = st.selectbox(
                "Filtrar por Responsável",
                options=['Todos'] + responsaveis_unicos,
                index=0,
                key="filtro_responsavel_pesquisa_br"
            )

    # Aplicar filtros
    df_filtrado = df_pesquisa.copy()
    
    if filtro_estagio != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['ESTAGIO_LEGIVEL'] == filtro_estagio]
    
    if filtro_responsavel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['ASSIGNED_BY_NAME'] == filtro_responsavel]

    # --- Tabela Detalhada ---
    st.markdown("#### 📋 Detalhamento das Pesquisas")
    
    if df_filtrado.empty:
        st.warning("Nenhum registro encontrado com os filtros aplicados.")
    else:
        # Preparar dados para exibição
        df_display = df_filtrado[[
            'UF_CRM_34_NOME_FAMILIA',
            'UF_CRM_34_ID_REQUERENTE', 
            'ESTAGIO_LEGIVEL',
            'ASSIGNED_BY_NAME'
        ]].copy()
        
        df_display = df_display.rename(columns={
            'UF_CRM_34_NOME_FAMILIA': 'Nome da Família',
            'UF_CRM_34_ID_REQUERENTE': 'ID Requerente',
            'ESTAGIO_LEGIVEL': 'Estágio Atual',
            'ASSIGNED_BY_NAME': 'Responsável'
        })
        
        # Ordenar por estágio e família
        ordem_estagios = [
            'AGUARDANDO PESQUISADOR',
            'PESQUISA EM ANDAMENTO',
            'PESQUISA PRONTA PARA EMISSÃO',
            'PESQUISA NÃO ENCONTRADA'
        ]
        
        df_display['ORDEM_ESTAGIO'] = df_display['Estágio Atual'].map({
            estágio: i for i, estágio in enumerate(ordem_estagios)
        }).fillna(999)
        
        df_display = df_display.sort_values(['ORDEM_ESTAGIO', 'Nome da Família'])
        df_display = df_display.drop(columns=['ORDEM_ESTAGIO'])
        
        # Configurar cores por estágio
        def color_estagio(val):
            colors = {
                'AGUARDANDO PESQUISADOR': 'background-color: #FFF3E0',
                'PESQUISA EM ANDAMENTO': 'background-color: #E3F2FD',
                'PESQUISA PRONTA PARA EMISSÃO': 'background-color: #E8F5E8',
                'PESQUISA NÃO ENCONTRADA': 'background-color: #FFEBEE'
            }
            return colors.get(val, '')
        
        # Aplicar estilo
        styled_df = df_display.style.applymap(
            color_estagio, 
            subset=['Estágio Atual']
        )
        
        st.dataframe(
            styled_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Nome da Família": st.column_config.TextColumn("Nome da Família", width="medium"),
                "ID Requerente": st.column_config.TextColumn("ID Requerente", width="small"),
                "Estágio Atual": st.column_config.TextColumn("Estágio Atual", width="medium"),
                "Responsável": st.column_config.TextColumn("Responsável", width="medium")
            }
        )
        
        st.caption(f"Exibindo {len(df_filtrado)} de {total_pesquisas} pesquisas")

    # --- Análise por Responsável ---
    st.markdown("---")
    st.markdown("#### 👥 Análise por Responsável")
    
    analise_responsavel = df_pesquisa.groupby('ASSIGNED_BY_NAME').agg({
        'ID': 'count',
        'UF_CRM_34_ID_REQUERENTE': pd.Series.nunique
    }).reset_index()
    
    analise_responsavel = analise_responsavel.rename(columns={
        'ASSIGNED_BY_NAME': 'Responsável',
        'ID': 'Total Pesquisas',
        'UF_CRM_34_ID_REQUERENTE': 'Requerentes Únicos'
    })
    
    # Adicionar estatísticas por estágio para cada responsável
    for estagio in ['AGUARDANDO PESQUISADOR', 'PESQUISA EM ANDAMENTO', 'PESQUISA PRONTA PARA EMISSÃO', 'PESQUISA NÃO ENCONTRADA']:
        contagem_estagio = df_pesquisa[df_pesquisa['ESTAGIO_LEGIVEL'] == estagio].groupby('ASSIGNED_BY_NAME').size().reset_index(name=estagio)
        analise_responsavel = analise_responsavel.merge(contagem_estagio, on='Responsável', how='left')
        analise_responsavel[estagio] = analise_responsavel[estagio].fillna(0).astype(int)
    
    # Calcular taxa de conclusão por responsável
    analise_responsavel['Finalizadas'] = (
        analise_responsavel['PESQUISA PRONTA PARA EMISSÃO'] + 
        analise_responsavel['PESQUISA NÃO ENCONTRADA']
    )
    
    analise_responsavel['Taxa Conclusão (%)'] = (
        analise_responsavel['Finalizadas'] / analise_responsavel['Total Pesquisas'] * 100
    ).round(1)
    
    # Ordenar por total de pesquisas
    analise_responsavel = analise_responsavel.sort_values('Total Pesquisas', ascending=False)
    
    st.dataframe(
        analise_responsavel,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Taxa Conclusão (%)": st.column_config.ProgressColumn(
                "Taxa Conclusão (%)",
                format="%.1f%%",
                min_value=0,
                max_value=100
            )
        }
    ) 