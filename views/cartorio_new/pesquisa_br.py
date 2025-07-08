import streamlit as st
import pandas as pd
from datetime import datetime, date
from .utils import simplificar_nome_estagio, categorizar_estagio
from utils.dataframe_utils import ensure_pandas_df

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

    st.subheader("🔍 Pesquisa BR")

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

    # --- Filtros ---
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            # Filtro de Estágio
            estagios_unicos = sorted(df_pesquisa['ESTAGIO_LEGIVEL'].unique().tolist())
            filtro_estagio = st.selectbox(
                "Filtrar por Estágio",
                options=['Todos'] + estagios_unicos,
                index=0,
                key="filtro_estagio_pesquisa_br"
            )

        with col2:
            # Filtro de Protocolizado
            coluna_protocolizado = 'UF_CRM_34_PROTOCOLIZADO'
            filtro_protocolizado_habilitado = coluna_protocolizado in df_pesquisa.columns
            if filtro_protocolizado_habilitado:
                filtro_protocolizado = st.selectbox(
                    "Protocolizado:",
                    options=["Todos", "Protocolizado", "Não Protocolizado"],
                    index=0,
                    key="filtro_protocolizado_pesquisa_br"
                )
            else:
                st.caption(f":warning: Campo protocolizado não encontrado.")
                filtro_protocolizado = "Todos"

    # --- Aplicar filtro de protocolizado ANTES de calcular as métricas ---
    df_metricas = df_pesquisa.copy()
    if filtro_protocolizado != "Todos" and filtro_protocolizado_habilitado:
        if coluna_protocolizado in df_metricas.columns:
            df_metricas['PROTO_NORMALIZADO'] = df_metricas[coluna_protocolizado].fillna('').astype(str).str.strip().str.upper()
            
            if filtro_protocolizado == "Protocolizado":
                df_metricas = df_metricas[df_metricas['PROTO_NORMALIZADO'] == 'PROTOCOLIZADO']
            elif filtro_protocolizado == "Não Protocolizado":
                df_metricas = df_metricas[df_metricas['PROTO_NORMALIZADO'] == 'NÃO SELECIONADA']
            
            df_metricas = df_metricas.drop(columns=['PROTO_NORMALIZADO'])
        else:
            st.warning(f"Coluna {coluna_protocolizado} não encontrada ao aplicar filtro.")

    # --- Métricas Gerais (com base no filtro de protocolizado) ---
    total_pesquisas = len(df_metricas)
    total_requerentes = df_metricas[df_metricas['UF_CRM_34_ID_REQUERENTE'] != 'Req. Desconhecido']['UF_CRM_34_ID_REQUERENTE'].nunique()
    total_familias = df_metricas[df_metricas['UF_CRM_34_NOME_FAMILIA'] != 'Família Desconhecida']['UF_CRM_34_NOME_FAMILIA'].nunique()
    
    # Contar por estágio (com base no filtro de protocolizado)
    aguardando_pesquisador = len(df_metricas[df_metricas['ESTAGIO_LEGIVEL'] == 'AGUARDANDO PESQUISADOR'])
    pesquisa_andamento = len(df_metricas[df_metricas['ESTAGIO_LEGIVEL'] == 'PESQUISA EM ANDAMENTO'])
    pesquisa_pronta = len(df_metricas[df_metricas['ESTAGIO_LEGIVEL'] == 'PESQUISA PRONTA PARA EMISSÃO'])
    pesquisa_nao_encontrada = len(df_metricas[df_metricas['ESTAGIO_LEGIVEL'] == 'PESQUISA NÃO ENCONTRADA'])
    
    # Calcular taxa de conclusão
    pesquisas_finalizadas = pesquisa_pronta + pesquisa_nao_encontrada
    taxa_conclusao = (pesquisas_finalizadas / total_pesquisas * 100) if total_pesquisas > 0 else 0

    # --- Exibir Métricas ---
    st.markdown("#### 📊 Métricas Gerais")
    
    # Criar métricas customizadas com HTML puro
    st.markdown(f"""
    <style>
    .metrica-custom-pesquisa {{
        background: #F8F9FA;
        border: 2px solid #DEE2E6;
        border-radius: 6px;
        padding: 16px;
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }}
    
    .metrica-custom-pesquisa:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: #ADB5BD;
    }}
    
    .metrica-custom-pesquisa .label {{
        color: #6C757D;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
        line-height: 1.2;
    }}
    
    .metrica-custom-pesquisa .valor {{
        color: #495057;
        font-weight: 700;
        font-size: 30px;
        line-height: 1.2;
        margin-bottom: 4px;
    }}
    
    .metricas-container-pesquisa {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }}
    </style>
    
    <div class="metricas-container-pesquisa">
        <div class="metrica-custom-pesquisa">
            <div class="label">Total Pesquisas</div>
            <div class="valor">{total_pesquisas:,}</div>
        </div>
        <div class="metrica-custom-pesquisa">
            <div class="label">Requerentes</div>
            <div class="valor">{total_requerentes:,}</div>
        </div>
        <div class="metrica-custom-pesquisa">
            <div class="label">Famílias</div>
            <div class="valor">{total_familias:,}</div>
        </div>
        <div class="metrica-custom-pesquisa">
            <div class="label">Finalizadas</div>
            <div class="valor">{pesquisas_finalizadas:,}</div>
        </div>
        <div class="metrica-custom-pesquisa">
            <div class="label">Taxa Conclusão</div>
            <div class="valor">{taxa_conclusao:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Detalhamento por Estágio ---
    st.markdown("#### Andamento por Estágio")
    
    col_est1, col_est2, col_est3, col_est4 = st.columns(4)
    
    # Cards com classes SCSS e fundos coloridos (sem emojis)
    col_est1.markdown(f"""
    <style>
    .stage-card-pesquisa {{
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: all 0.2s ease;
        border: 2px solid;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}
    
    .stage-card-pesquisa:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }}
    
    .stage-card-pesquisa--aguardando {{
        background: #E3F2FD;
        border-color: #2196F3;
        color: #0D47A1;
    }}
    
    .stage-card-pesquisa--andamento {{
        background: #FFF8E1;
        border-color: #FF9800;
        color: #E65100;
    }}
    
    .stage-card-pesquisa--prontas {{
        background: #E8F5E8;
        border-color: #4CAF50;
        color: #1B5E20;
    }}
    
    .stage-card-pesquisa--nao-encontradas {{
        background: #FFEBEE;
        border-color: #F44336;
        color: #B71C1C;
    }}
    
    .stage-card-pesquisa__title {{
        font-weight: 700;
        font-size: 16px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .stage-card-pesquisa__value {{
        font-weight: 900;
        font-size: 36px;
        line-height: 1;
        margin-bottom: 4px;
    }}
    
    .stage-card-pesquisa__subtitle {{
        font-size: 12px;
        font-weight: 500;
        opacity: 0.8;
    }}
    </style>
    
    <div class="stage-card-pesquisa stage-card-pesquisa--aguardando">
        <div class="stage-card-pesquisa__title">Aguardando</div>
        <div class="stage-card-pesquisa__value">{aguardando_pesquisador}</div>
        <div class="stage-card-pesquisa__subtitle">Aguardando Pesquisador</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_est2.markdown(f"""
    <div class="stage-card-pesquisa stage-card-pesquisa--andamento">
        <div class="stage-card-pesquisa__title">Em Andamento</div>
        <div class="stage-card-pesquisa__value">{pesquisa_andamento}</div>
        <div class="stage-card-pesquisa__subtitle">Pesquisa em Andamento</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_est3.markdown(f"""
    <div class="stage-card-pesquisa stage-card-pesquisa--prontas">
        <div class="stage-card-pesquisa__title">Prontas</div>
        <div class="stage-card-pesquisa__value">{pesquisa_pronta}</div>
        <div class="stage-card-pesquisa__subtitle">Pronta para Emissão</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_est4.markdown(f"""
    <div class="stage-card-pesquisa stage-card-pesquisa--nao-encontradas">
        <div class="stage-card-pesquisa__title">Não Encontradas</div>
        <div class="stage-card-pesquisa__value">{pesquisa_nao_encontrada}</div>
        <div class="stage-card-pesquisa__subtitle">Pesquisa Não Encontrada</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Aplicar filtros para a tabela ---
    df_filtrado = df_metricas.copy()

    # Filtro de Estágio (aplicado sobre o df que já foi filtrado por protocolizado)
    if filtro_estagio != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['ESTAGIO_LEGIVEL'] == filtro_estagio]

    if df_filtrado.empty:
        st.warning("Nenhum registro encontrado para os filtros selecionados.")
        return

    # --- Tabela Detalhada ---
    st.markdown("#### 📋 Detalhamento das Pesquisas")
    
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
    
    analise_responsavel = df_filtrado.groupby('ASSIGNED_BY_NAME').agg({
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
        contagem_estagio = df_filtrado[df_filtrado['ESTAGIO_LEGIVEL'] == estagio].groupby('ASSIGNED_BY_NAME').size().reset_index(name=estagio)
        contagem_estagio = contagem_estagio.rename(columns={'ASSIGNED_BY_NAME': 'Responsável'})
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