import streamlit as st
from .data_loader import carregar_dados_comune, carregar_dados_negocios, carregar_estagios_bitrix, mapear_estagios_comune, mapear_estagios_macro
from .analysis import criar_visao_geral_comune, criar_visao_macro, cruzar_comune_deal, analisar_distribuicao_deals, analisar_registros_sem_correspondencia, calcular_tempo_solicitacao, criar_metricas_certidoes, criar_metricas_tempo_dias, calcular_tempo_solicitacao_providencia
from .mapa_cat58 import visualizar_mapa_cat58
from .producao_comune import show_producao_comune
from .funil_certidoes_italianas import show_funil_certidoes_italianas

import pandas as pd
import io
from datetime import datetime
import time
import sys
from pathlib import Path

# Adicionar caminhos para importação
api_path = Path(__file__).parents[2] / 'api'
utils_path = Path(__file__).parents[2] / 'utils'
sys.path.insert(0, str(api_path))
sys.path.insert(0, str(utils_path))

# Importar funções necessárias
from bitrix_connector import load_bitrix_data
from refresh_utils import handle_refresh_trigger, get_force_reload_status, clear_force_reload_flag
from utils.dataframe_utils import ensure_pandas_df

@st.cache_data(ttl=3600) # Cache de 1 hora
def cached_load_comune_data(force_reload=False):
    """
    Carrega e cacheia os dados do COMUNE especificamente para a categoria 22.
    """
    print(f"Tentando carregar dados para Categoria 22... Force Reload: {force_reload}")
    df = carregar_dados_comune(category_id="22", force_reload=force_reload)
    print(f"Dados para Categoria 22 carregados. {len(df) if df is not None else 0} registros.")
    return df

@st.cache_data(ttl=3600) # Cache de 1 hora
def cached_load_comune_data_cat58(force_reload=False):
    """
    Carrega e cacheia os dados do COMUNE especificamente para a categoria 58.
    """
    print(f"Tentando carregar dados para Categoria 58... Force Reload: {force_reload}")
    df = carregar_dados_comune(category_id="58", force_reload=force_reload)
    print(f"Dados para Categoria 58 carregados. {len(df) if df is not None else 0} registros.")
    return df

def show_comune():
    """
    Exibe a página principal do COMUNE
    """
    # Importar funções de visualização aqui para evitar importação circular
    from .visualization import (
        visualizar_comune_dados, visualizar_funil_comune, visualizar_grafico_macro,
        visualizar_cruzamento_deal, visualizar_analise_sem_correspondencia,
        visualizar_tempo_solicitacao, visualizar_metricas_certidoes,
        visualizar_metricas_tempo_dias, visualizar_analise_evidencia,
        visualizar_providencias, visualizar_tempo_solicitacao_providencia,
        visualizar_tempo_solicitacao_individual, visualizar_estagios_detalhados
    )
    
    # Aplicar estilo personalizado para botão de atualização
    st.markdown("""
    <style>
    div[data-testid="stButton"] button.atualizar-btn {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 4px;
        transition-duration: 0.3s;
    }
    div[data-testid="stButton"] button.atualizar-btn:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Título centralizado
    st.markdown("""
    <h1 style="font-size: 2.8rem; font-weight: 900; color: #1A237E; text-align: center; 
    margin-bottom: 1.5rem; padding-bottom: 10px; border-bottom: 4px solid #1976D2;
    font-family: Arial, Helvetica, sans-serif;">
    <strong>Comune Bitrix24</strong></h1>
    """, unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px; color: #555; font-family: Arial, Helvetica, sans-serif;'>Monitoramento completo do processo de emissão de documentos de Comune.</p>", unsafe_allow_html=True)
    
    # Botão de atualização no topo da página
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Atualizar Dados", key="btn_atualizar_comune", help="Força a atualização dos dados ignorando o cache", type="primary", use_container_width=True):
            with st.spinner("Atualizando dados e limpando cache..."):
                # Mostrar mensagem de feedback
                st.info("Limpando cache e recarregando dados em tempo real...")
                
                # Limpar todos os caches antes de recarregar
                st.cache_data.clear()
                
                # Limpar também o cache específico da API Bitrix
                load_bitrix_data.clear()
                
                # Definir flags no estado da sessão para consistência com o resto do projeto
                st.session_state['full_refresh'] = True
                st.session_state['force_reload'] = True
                st.session_state['loading_state'] = 'loading'
                
                # Pequena pausa para garantir que o cache seja completamente limpo
                time.sleep(0.5)
                st.success("Cache limpo! Recarregando página...")
                time.sleep(0.5)
                st.rerun()
        
        # Texto de ajuda para o botão de atualização
        st.caption("""
        Use este botão para forçar a atualização 
        dos dados em tempo real e limpar o cache
        """)
    
    # Verificar se há atualização global acionada por outro botão do sistema
    if handle_refresh_trigger():
        # Indicar que estamos atualizando
        st.info("⏳ Atualizando dados como parte de uma atualização global...")
        time.sleep(0.5)
        st.rerun()
    
    # Se estiver forçando recarregamento, exibir indicador
    force_reload = get_force_reload_status()
    if force_reload:
        st.info("⏳ Dados sendo atualizados diretamente da API (ignorando cache)...")
        # Limpar a flag após seu uso
        clear_force_reload_flag()
    
    # Carregar os dados
    with st.spinner("Carregando dados..."):
        df_comune = cached_load_comune_data(force_reload)
        df_deal, df_deal_uf = carregar_dados_negocios(force_reload=force_reload)
        
        # Salvar o df_comune na sessão para uso em outras funções
        st.session_state['df_comune'] = df_comune
    
    if df_comune.empty:
        st.warning("Não foi possível carregar os dados de COMUNE. Verifique a conexão com o Bitrix24.")
        return
    else:
        st.success(f"Dados carregados com sucesso: {len(df_comune)} registros encontrados.")
    
    # Adicionar CSS para aumentar o contraste das abas
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab"] {
        font-weight: 900 !important;
        color: #1A237E !important;
        height: 60px !important;
        padding: 10px 20px !important;
        font-size: 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-right: 5px !important;
        border-radius: 8px 8px 0 0 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1976D2 !important;
        color: white !important;
        font-weight: 900 !important;
        border-bottom: 4px solid #FF9800 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        margin-bottom: 20px !important;
        gap: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Mostrar todas as informações relevantes em abas
    if not df_comune.empty:
        # Criar abas para organizar o conteúdo
        tab_nomes = [
            "Distribuição por Estágio",
            "Dados Detalhados",
            "Funil Detalhado",
            "Cruzamento CRM_DEAL",
            "📊 Métricas de Certidões",
            "⏳ Tempo em Dias",
            "⏱️ Tempo Individual",
            "🗺️ Tempo x Província",
            "📄 Evidencia Comprovante",
            "🇮🇹 PROVÍNCIA",
            "🗺️ MAPA PROVÍNCIA - Angélica",
        ]
        tabs = st.tabs(tab_nomes)

        # Mapear nomes para índices para facilitar acesso
        tab_map = {name: i for i, name in enumerate(tab_nomes)}

        # Aba 1: Distribuição por Estágio
        with tabs[tab_map["Distribuição por Estágio"]]:
            # Criar visão macro
            visao_macro = criar_visao_macro(df_comune)
            
            # Exibir métricas principais
            if not visao_macro.empty:
                # Exibir gráfico com visão macro usando um estilo melhorado
                st.markdown("""
                <h3 style="font-size: 28px; font-weight: 900; color: #1A237E; text-align: center; 
                margin: 30px 0 20px 0; padding-bottom: 10px; border-bottom: 3px solid #E0E0E0;
                font-family: Arial, Helvetica, sans-serif;">
                DISTRIBUIÇÃO POR ESTÁGIO</h3>
                <p style="text-align: center; font-size: 18px; color: #555; margin-bottom: 25px; font-family: Arial, Helvetica, sans-serif;">
                Visão detalhada da distribuição de processos em cada estágio</p>
                """, unsafe_allow_html=True)
                
                # Adicionar um comentário explicativo antes do gráfico
                st.markdown("""
                <div style="background-color: #f5f5f5; 
                            padding: 15px; 
                            border-radius: 8px; 
                            margin-bottom: 20px;
                            border-left: 5px solid #1976D2;
                            font-family: Arial, Helvetica, sans-serif;">
                    <p style="font-size: 16px; margin: 0; color: #333; font-weight: 500;">
                        O gráfico abaixo mostra a distribuição dos registros entre todos os estágios do processo.
                        Visualize a proporção de cada tipo para identificar possíveis gargalos ou oportunidades de melhoria.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Exibir o gráfico
                visualizar_grafico_macro(visao_macro)
            else:
                st.info("Não foi possível criar a visão macro. Verifique se os dados estão corretos.")
        
        # Aba 2: Dados Detalhados
        with tabs[tab_map["Dados Detalhados"]]:
            # Exibir tabela com os dados
            visualizar_comune_dados(df_comune)
        
        # Aba 3: Funil Detalhado
        with tabs[tab_map["Funil Detalhado"]]:
            # Criar visão geral
            visao_geral = criar_visao_geral_comune(df_comune)
            
            # Exibir visão geral em tabela
            if not visao_geral.empty:
                st.subheader("Visão Geral dos Estágios")
                st.dataframe(visao_geral, use_container_width=True)
                
                # Exibir gráfico de funil
                visualizar_funil_comune(visao_geral)
            else:
                st.info("Não foi possível criar a visão geral. Verifique se os dados estão corretos.")
        
        # Aba 4: Cruzamento com CRM_DEAL
        with tabs[tab_map["Cruzamento CRM_DEAL"]]:
            # Adicionar informações sobre o cruzamento
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #1A237E; margin-top: 0;">Cruzamento COMUNE x CRM_DEAL</h3>
                <p>Este cruzamento relaciona registros do COMUNE (CRM_DYNAMIC_1052, Category ID 22) com 
                negócios do CRM (CRM_DEAL, Category ID 32).</p>
                <p><strong>Campos utilizados para o cruzamento:</strong></p>
                <ul>
                    <li>COMUNE: <code>UF_CRM_12_1723552666</code></li>
                    <li>CRM_DEAL: <code>UF_CRM_1722605592778</code></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Verificar se temos dados de negócios
            if not df_deal.empty and not df_deal_uf.empty:
                try:
                    # Mostrar contagem de registros
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            label="Registros COMUNE", 
                            value=len(df_comune),
                            delta=None
                        )
                    with col2:
                        st.metric(
                            label="Negócios (Category ID 32)", 
                            value=len(df_deal),
                            delta=None
                        )
                    
                    # Cruzar dados
                    with st.spinner("Processando cruzamento de dados..."):
                        df_cruzado = cruzar_comune_deal(df_comune, df_deal, df_deal_uf)
                    
                    if not df_cruzado.empty and 'STAGE_NAME' in df_cruzado.columns and 'TEM_DEAL' in df_cruzado.columns:
                        # Calcular estatísticas básicas
                        total_registros = len(df_cruzado)
                        registros_com_match = df_cruzado['TEM_DEAL'].sum()
                        registros_sem_match = total_registros - registros_com_match
                        
                        # Adicionar controles de filtro
                        st.markdown("""
                        <hr style="margin: 1.5rem 0">
                        <h3 style="color: #1A237E; margin-top: 1rem;">Filtros de Análise</h3>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        
                        # Filtro para tipo de correspondência
                        with col1:
                            tipo_correspondencia = st.radio(
                                "Mostrar registros:",
                                options=["Todos", "Apenas com correspondência", "Apenas sem correspondência"],
                                index=0,
                                horizontal=True
                            )
                        
                        # Filtro para estágio
                        with col2:
                            # Obter lista de estágios únicos
                            estagios = ["Todos"] + sorted(df_cruzado['STAGE_NAME'].unique().tolist())
                            estagio_selecionado = st.selectbox(
                                "Filtrar por estágio:",
                                options=estagios,
                                index=0
                            )
                        
                        # Aplicar filtros ao DataFrame
                        df_filtrado = df_cruzado.copy()
                        
                        # Filtrar por tipo de correspondência
                        if tipo_correspondencia == "Apenas com correspondência":
                            df_filtrado = df_filtrado[df_filtrado['TEM_DEAL']]
                            st.success(f"Mostrando {len(df_filtrado)} registros que possuem correspondência em CRM_DEAL")
                        elif tipo_correspondencia == "Apenas sem correspondência":
                            df_filtrado = df_filtrado[~df_filtrado['TEM_DEAL']]
                            st.warning(f"Mostrando {len(df_filtrado)} registros que NÃO possuem correspondência em CRM_DEAL")
                        
                        # Filtrar por estágio
                        if estagio_selecionado != "Todos":
                            df_filtrado = df_filtrado[df_filtrado['STAGE_NAME'] == estagio_selecionado]
                            st.info(f"Filtrado para estágio: {estagio_selecionado} ({len(df_filtrado)} registros)")
                        
                        # Opções adicionais de filtro e pesquisa
                        if not df_filtrado.empty:
                            st.markdown("#### Opções adicionais de filtro")
                            pesquisa_texto = st.text_input(
                                "Pesquisar por texto no título ou ID:",
                                placeholder="Digite o texto para pesquisar..."
                            )
                            
                            # Aplicar pesquisa por texto
                            if pesquisa_texto:
                                if 'TITLE' in df_filtrado.columns:
                                    mask_title = df_filtrado['TITLE'].astype(str).str.contains(pesquisa_texto, case=False, na=False)
                                    df_filtrado = df_filtrado[mask_title]
                                    st.info(f"Pesquisando por '{pesquisa_texto}' - {len(df_filtrado)} resultados encontrados")
                            
                            # Adicionar botão para exportar registros filtrados
                            col1, col2 = st.columns(2)
                            with col1:
                                # Preparar buffer para o arquivo Excel
                                buffer = io.BytesIO()
                                
                                # Criar um escritor Excel
                                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                                    # Escrever o DataFrame filtrado em uma planilha
                                    df_filtrado.to_excel(writer, sheet_name='Registros_Filtrados', index=False)
                                
                                # Oferecer download do arquivo
                                st.download_button(
                                    label="📥 Exportar registros filtrados",
                                    data=buffer.getvalue(),
                                    file_name=f"comune_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.ms-excel"
                                )
                            
                            with col2:
                                if "Apenas sem correspondência" in tipo_correspondencia:
                                    st.info("Use esta exportação para identificar todos os registros que precisam ser verificados em CRM_DEAL")
                        
                        # Adicionar tabela de IDs de Família que não existem no Comune
                        st.markdown("<hr style='margin: 1.5rem 0'>", unsafe_allow_html=True)
                        st.subheader("IDs de Família que não existem no Comune")
                        
                        # Obter valores únicos de UF_CRM_12_1723552666 do Comune (pode conter múltiplos valores separados por vírgula)
                        valores_comune = set()
                        for valor in df_comune['UF_CRM_12_1723552666'].dropna():
                            if isinstance(valor, str) and ',' in valor:
                                # Separar valores divididos por vírgula
                                for v in valor.split(','):
                                    v_limpo = v.strip()
                                    if v_limpo:
                                        valores_comune.add(v_limpo)
                            else:
                                valores_comune.add(valor)
                        
                        # Criar um DataFrame com IDs de família que não existem no Comune
                        ids_nao_existentes = []
                        for valor in df_deal_uf['UF_CRM_1722605592778'].dropna().unique():
                            if isinstance(valor, str) and ',' in valor:
                                # Separar valores divididos por vírgula
                                for v in valor.split(','):
                                    v_limpo = v.strip()
                                    if v_limpo and v_limpo not in valores_comune:
                                        ids_nao_existentes.append({
                                            'ID_FAMILIA': v_limpo
                                        })
                            elif valor not in valores_comune:
                                ids_nao_existentes.append({
                                    'ID_FAMILIA': valor
                                })
                        
                        # Criar DataFrame com os IDs não existentes
                        df_ids_nao_existentes = pd.DataFrame(ids_nao_existentes)
                        
                        if not df_ids_nao_existentes.empty:
                            st.write(f"Foram encontrados {len(df_ids_nao_existentes)} IDs de família em CRM_DEAL que não existem no Comune.")
                            
                            # Exibir tabela com os IDs
                            st.dataframe(df_ids_nao_existentes, use_container_width=True)
                            
                            # Botão para exportar IDs não existentes
                            buffer_ids = io.BytesIO()
                            with pd.ExcelWriter(buffer_ids, engine='xlsxwriter') as writer:
                                df_ids_nao_existentes.to_excel(writer, sheet_name='IDs_Nao_Existentes', index=False)
                            
                            st.download_button(
                                label="📥 Exportar IDs não existentes em Comune",
                                data=buffer_ids.getvalue(),
                                file_name=f"ids_familia_nao_existentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.ms-excel"
                            )
                        else:
                            st.success("Todos os IDs de família em CRM_DEAL existem no Comune.")
                        
                        # Analisar distribuição de deals
                        distribuicao = analisar_distribuicao_deals(df_cruzado)
                        
                        if not distribuicao.empty:
                            st.markdown("<hr style='margin: 1.5rem 0'>", unsafe_allow_html=True)
                            st.subheader("Distribuição por Estágio")
                            
                            # Exibir visualização do cruzamento
                            visualizar_cruzamento_deal(distribuicao)
                            
                            # Adicionar análise detalhada para registros sem correspondência
                            if registros_sem_match > 0:
                                st.markdown("<hr style='margin: 1.5rem 0'>", unsafe_allow_html=True)
                                
                                # Expandir para mostrar análise detalhada
                                with st.expander("Análise Detalhada - Registros sem Correspondência", expanded=tipo_correspondencia=="Apenas sem correspondência"):
                                    # Fazer análise detalhada dos registros sem correspondência
                                    resumo_sem_match = analisar_registros_sem_correspondencia(df_cruzado)
                                    
                                    # Visualizar análise
                                    visualizar_analise_sem_correspondencia(resumo_sem_match)
                            
                            # Exibir registros filtrados em tabela
                            if not df_filtrado.empty:
                                st.subheader(f"Registros Filtrados ({len(df_filtrado)})")
                                
                                # Selecionar colunas relevantes para exibição
                                colunas_exibicao = [
                                    'TITLE', 'STAGE_NAME', 'UF_CRM_12_1723552666', 
                                    'DEAL_ID', 'UF_CRM_1722605592778', 'ASSIGNED_BY_NAME'
                                ]
                                
                                # Verificar quais colunas existem no DataFrame
                                colunas_disponiveis = [col for col in colunas_exibicao if col in df_filtrado.columns]
                                
                                # Exibir os registros filtrados
                                st.dataframe(df_filtrado[colunas_disponiveis], use_container_width=True)
                            else:
                                st.warning("Nenhum registro encontrado com os filtros aplicados.")
                        else:
                            st.info("Não foi possível gerar a distribuição dos dados. Verifique a estrutura dos dados.")
                    else:
                        st.info("O cruzamento dos dados não possui as colunas necessárias para análise.")
                except Exception as e:
                    st.error(f"Erro ao processar o cruzamento: {str(e)}")
                    st.info("Detalhes do erro podem ser encontrados no console do Streamlit.")
            else:
                st.warning("Não foi possível carregar os dados de negócios para cruzamento.")
                
                # Exibir detalhes sobre os dados
                if df_deal.empty:
                    st.error("Nenhum registro encontrado em CRM_DEAL com CATEGORY_ID=32")
                else:
                    st.success(f"Encontrados {len(df_deal)} registros em CRM_DEAL")
                
                if df_deal_uf.empty:
                    st.error("Nenhum registro encontrado em CRM_DEAL_UF para os negócios filtrados")
                else:
                    st.success(f"Encontrados {len(df_deal_uf)} registros em CRM_DEAL_UF")
        
        # Aba: Métricas de Certidões
        with tabs[tab_map["📊 Métricas de Certidões"]]:
            # Criar métricas de certidões
            metricas_certidoes = criar_metricas_certidoes(df_comune)
            
            # Exibir métricas de certidões
            visualizar_metricas_certidoes(metricas_certidoes)
        
        # Aba: Tempo em Dias
        with tabs[tab_map["⏳ Tempo em Dias"]]:
            # Criar métricas de tempo em dias
            metricas_tempo_dias = criar_metricas_tempo_dias(df_comune)
            
            # Exibir métricas de tempo em dias
            visualizar_metricas_tempo_dias(metricas_tempo_dias)
        
        # Aba: Tempo Individual
        with tabs[tab_map["⏱️ Tempo Individual"]]:
            st.markdown("""
            ### Análise Individual de Tempo de Solicitação
            Esta seção permite visualizar o tempo decorrido para cada solicitação individualmente,
            calculado a partir da data original da solicitação.
            """, unsafe_allow_html=True)
            # Chamar a nova função de visualização passando o df_comune completo
            visualizar_tempo_solicitacao_individual(df_comune)
        
        # Aba: Tempo x Província
        with tabs[tab_map["🗺️ Tempo x Província"]]:
            # Calcular o tempo de solicitação por providência (AGREGADO)
            # Chamar a função SEM o parâmetro extra ou com ele False
            df_tempo_providencia = calcular_tempo_solicitacao_providencia(df_comune, retornar_dados_individuais=False)
            # Visualizar o cruzamento entre tempo de solicitação e providência
            visualizar_tempo_solicitacao_providencia(df_tempo_providencia)
        
        # Aba Evidencia
        with tabs[tab_map["📄 Evidencia Comprovante"]]:
            # Chamar a função de visualização da análise de evidência
            # Nota: Esta função pode precisar de dados de uma análise específica.
            # Se ocorrer erro aqui, verificar a função visualizar_analise_evidencia.
            try:
                visualizar_analise_evidencia(df_comune)
            except Exception as e:
                st.error(f"Erro ao gerar visualização de Evidência: {e}")
                st.warning("Verifique se a função 'visualizar_analise_evidencia' tem os dados necessários.")
        
        # Aba PROVÍNCIA
        with tabs[tab_map["🇮🇹 PROVÍNCIA"]]:
            # Chamar a função de visualização por providência
            visualizar_providencias(df_comune)
            
        # Nova aba para o Mapa Província Categoria 58
        with tabs[tab_map["🗺️ MAPA PROVÍNCIA - Angélica"]]:
            # Carregar dados da categoria 58
            if 'df_comune_cat58' not in locals():
                with st.spinner("Carregando dados da categoria 58..."):
                    df_comune_cat58 = cached_load_comune_data_cat58(force_reload)
            
            # Visualizar o mapa com os dados da categoria 58
            if df_comune_cat58 is not None and not df_comune_cat58.empty:
                visualizar_mapa_cat58(df_comune_cat58)
            else:
                st.warning("Não foi possível carregar os dados da categoria 58 para o mapa de província.")
                st.info("Verifique se os dados da categoria 58 estão disponíveis no Bitrix24.")
    
    # Adicionar download dos dados
    if not df_comune.empty:
        st.markdown("---")
        st.subheader("Download dos Dados")
        
        # Preparar buffer para o arquivo Excel
        buffer = io.BytesIO()
        
        # Criar um escritor Excel
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Escrever os DataFrames em diferentes planilhas
            df_comune.to_excel(writer, sheet_name='Dados_COMUNE', index=False)
            
            # Se tiver visão geral, adicionar também
            try:
                visao_geral = criar_visao_geral_comune(df_comune)
                if not visao_geral.empty:
                    visao_geral.to_excel(writer, sheet_name='Visao_Geral', index=False)
                
                visao_macro = criar_visao_macro(df_comune)
                if not visao_macro.empty:
                    visao_macro.to_excel(writer, sheet_name='Visao_Macro', index=False)
            except Exception as e:
                st.error(f"Erro ao criar planilhas auxiliares: {str(e)}")
        
        # Oferecer download do arquivo
        st.download_button(
            label="📥 Baixar Dados em Excel",
            data=buffer.getvalue(),
            file_name=f"comune_bitrix24_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.ms-excel"
        )

    # 1.1 Carregar dados COMUNE Categoria 58 (cacheado)
    start_time_cat58 = datetime.now()
    df_comune_cat58 = cached_load_comune_data_cat58(force_reload)
    end_time_cat58 = datetime.now()
    st.info(f"Tempo de carregamento (Comune - Cat 58): {(end_time_cat58 - start_time_cat58).total_seconds():.2f} segundos")

    # --- SEÇÃO 7: Análise de Tempo Individual ---
    st.markdown("--- <br> **Análise de Tempo Individual**", unsafe_allow_html=True)
    if 'df_comune' in st.session_state and not st.session_state['df_comune'].empty:
        st.info("Para ver a análise de tempo individual, acesse a aba '⏱️ Tempo Individual' no menu acima.")
    else:
        st.warning("Dados do Comune (Cat 22) não carregados para análise de tempo individual.")

def show_comune_main(sub_page=None):
    """
    Função principal que controla a exibição das subpáginas do Comune
    baseada no parâmetro sub_page ou no estado da sessão.
    """
    # Título principal da página
    st.title("Comune")
    
    # Determinar qual subpágina exibir
    # Priorizar o parâmetro sub_page se fornecido, senão usar o estado da sessão
    if sub_page is not None:
        subpagina = sub_page
    else:
        subpagina = st.session_state.get('comune_subpagina', 'Produção Comune')
    
    # Exibir a subpágina selecionada
    if subpagina == 'Produção Comune':
        show_producao_comune()
    elif subpagina == 'Funil Certidões Italianas':
        show_funil_certidoes_italianas()
    else:
        # Fallback para a subpágina padrão se não for encontrada
        st.warning(f"Subpágina '{subpagina}' não encontrada. Exibindo Produção Comune.")
        show_producao_comune()

# Este if __name__ == "__main__": é para testes locais e pode ser removido ou comentado
# if __name__ == "__main__":
#     # Para testar esta página individualmente, você pode precisar simular 
#     # o estado da sessão ou carregar dados de exemplo.
#     # Exemplo simples:
#     if 'df_comune' not in st.session_state:
#         # Simular carregamento de dados ou deixar vazio para a lógica da página lidar com isso
#         st.session_state['df_comune'] = None # Ou um DataFrame de exemplo
#     show_comune_main() 