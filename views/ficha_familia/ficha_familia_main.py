"""
Arquivo principal do módulo Ficha da Família
Responsável pela busca e orquestração da exibição
"""
import time
import streamlit as st
import pandas as pd
from utils.dataframe_utils import ensure_pandas_df

from .data_loader import load_crm_deal_data
from .display_components import inject_all_ficha_css
from .metrics import exibir_metricas_macro
from .ficha_exibicao import exibir_ficha_familia
from .visao_esteiras import exibir_visao_esteiras


def show_ficha_familia():
    """Função principal que exibe a página de Ficha da Família"""
    # Imports lazy para evitar importação circular
    from views.cartorio_new.data_loader import carregar_dados_cartorio, load_data_all_pipelines
    
    # 🎨 INJETA TODO O CSS NO INÍCIO - GARANTE QUE SEMPRE CARREGUE
    inject_all_ficha_css()
    
    st.markdown("<h1 class='page-title initial-page-title'>Ficha da Família</h1>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Busque por uma famílias para encontrar status do processo da mesma.</p>", unsafe_allow_html=True)

    # Carregar os dados das famílias antecipadamente
    df_crm_deals_full = load_crm_deal_data(category_id=46)
    
    # Preparar estado da sessão
    if "familia_selecionada_id" not in st.session_state:
        st.session_state.familia_selecionada_id = None
    if "resultados_busca" not in st.session_state:
        st.session_state.resultados_busca = pd.DataFrame()

    # Container para busca
    with st.container():
        col1, col2 = st.columns([5, 1])
        
        with col1:
            campo_busca_familia_principal = 'UF_CRM_1722883482527'
            termo_busca = st.text_input(
                "Busca Nome da Família",
                placeholder="Digite o nome da família...", 
                key="busca_familia_principal_input",
                label_visibility="collapsed"
            ).strip()

            if "busca_avancada_loading" not in st.session_state:
                st.session_state.busca_avancada_loading = False

        with col2:
            if st.button("🔍 BUSCAR", help="Buscar famílias"):
                with st.spinner('Carregando busca...'):
                    time.sleep(0.8)
                    st.session_state.busca_avancada_loading = True
    
    # Processamento da busca
    familia_selecionada_data = pd.Series(dtype=object)
    df_emissoes_filtradas = pd.DataFrame()
    
    if df_crm_deals_full is not None and not df_crm_deals_full.empty:
        if campo_busca_familia_principal in df_crm_deals_full.columns:
            df_crm_deals_full[campo_busca_familia_principal] = df_crm_deals_full[campo_busca_familia_principal].astype(str).fillna('')
            
            # Se houver termo de busca, filtrar resultados
            if termo_busca:
                resultados_busca_df = df_crm_deals_full[
                    df_crm_deals_full[campo_busca_familia_principal].str.contains(termo_busca, case=False, na=False)
                ].copy()
                
                # Limitar a 10 resultados
                resultados_busca_df = resultados_busca_df.head(10)
                st.session_state.resultados_busca = resultados_busca_df
                
                # Exibir resultados da busca
                if not resultados_busca_df.empty:
                    st.markdown(f"<div class='results-count'>Encontrados {len(resultados_busca_df)} resultados para '{termo_busca}'</div>", unsafe_allow_html=True)
                    
                    # Preparar dados para exibição
                    dados_para_exibicao = []
                    for idx, row in resultados_busca_df.iterrows():
                        nome_familia = row.get(campo_busca_familia_principal, "")
                        id_familia = row.get('UF_CRM_1722605592778', "N/D")
                        
                        nome_requerente = "Não informado"
                        if 'UF_CRM_1723029889441' in row and row['UF_CRM_1723029889441']:
                            nome_requerente = row['UF_CRM_1723029889441']
                        elif 'TITLE' in row and row['TITLE']:
                            nome_requerente = row['TITLE']
                        
                        dados_para_exibicao.append({
                            "Nome da Família": nome_familia,
                            "ID da Família": id_familia,
                            "Requerente": nome_requerente
                        })
                    
                    # Exibir tabela
                    df_resultados = pd.DataFrame(dados_para_exibicao)
                    st.dataframe(
                        ensure_pandas_df(df_resultados),
                        column_config={
                            "Nome da Família": st.column_config.TextColumn("Nome da Família", width="large"),
                            "ID da Família": st.column_config.TextColumn("ID da Família", width="medium"),
                            "Requerente": st.column_config.TextColumn("Requerente", width="large")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Seletor de família
                    familia_ids = resultados_busca_df['UF_CRM_1722605592778'].astype(str).tolist() if 'UF_CRM_1722605592778' in resultados_busca_df.columns else []
                    familia_nomes = resultados_busca_df[campo_busca_familia_principal].astype(str).tolist()
                    
                    opcoes_selecao = []
                    for idx, id_familia in enumerate(familia_ids):
                        nome = familia_nomes[idx] if idx < len(familia_nomes) else "Família"
                        opcoes_selecao.append(f"{id_familia} - {nome}")
                    
                    if opcoes_selecao:
                        familia_selecionada_option = st.selectbox(
                            "👇 Selecione uma família para ver detalhes completos:",
                            options=["Selecione..."] + opcoes_selecao,
                            key="family_selector"
                        )
                        
                        if familia_selecionada_option != "Selecione...":
                            id_familia_selecionada = familia_selecionada_option.split(" - ")[0]
                            print(f"[DEBUG] ID da Família Selecionada: '{id_familia_selecionada}'")
                            
                            # Obter dados da família
                            familia_selecionada_data = resultados_busca_df[
                                resultados_busca_df['UF_CRM_1722605592778'].astype(str) == id_familia_selecionada
                            ].iloc[0]
                            
                            # Buscar emissões relacionadas
                            df_cartorio_completo = load_data_all_pipelines()
                            campo_ligacao_emissoes = 'UF_CRM_34_ID_FAMILIA'
                            
                            if df_cartorio_completo is not None and not df_cartorio_completo.empty and campo_ligacao_emissoes in df_cartorio_completo.columns:
                                df_cartorio_completo[campo_ligacao_emissoes] = df_cartorio_completo[campo_ligacao_emissoes].astype(str).fillna('')
                                df_emissoes_filtradas = df_cartorio_completo[
                                    df_cartorio_completo[campo_ligacao_emissoes] == id_familia_selecionada
                                ].copy()
                            
                            print(f"[DEBUG] Emissões encontradas: {len(df_emissoes_filtradas)}")
                            st.success(f"Família selecionada: {familia_selecionada_data.get(campo_busca_familia_principal, '')}")
                else:
                    st.info(f"Nenhuma família encontrada para '{termo_busca}'.")
        else:
            st.error(f"Coluna de busca '{campo_busca_familia_principal}' não existe nos dados do CRM.")
    elif df_crm_deals_full is None:
        st.error("Falha ao carregar dados do CRM.")
    
    st.markdown("---")
    
    # Exibir ficha ou métricas macro
    if not familia_selecionada_data.empty:
        exibir_ficha_familia(familia_selecionada_data, df_emissoes_filtradas)

        # Links para cards do Bitrix
        link_pasta_pronta = str(
            familia_selecionada_data.get('UF_CRM_48_LINK_PASTA_PRONTA')
            or familia_selecionada_data.get('UF_CRM_LINK_PASTA_PRONTA')
            or ''
        ).strip()
        link_emissao_brasileira = str(
            familia_selecionada_data.get('UF_CRM_48_LINK_EMISSAO_BRASILEIRA')
            or familia_selecionada_data.get('UF_CRM_LINK_EMISSAO_BRASILEIRA')
            or ''
        ).strip()

        with st.container():
            col_link1, col_link2 = st.columns([1, 1])
            with col_link1:
                if link_pasta_pronta.lower().startswith('http'):
                    st.link_button('Abrir card Pasta Pronta', url=link_pasta_pronta)
                else:
                    st.caption('Card Pasta Pronta: N/D')
            with col_link2:
                if link_emissao_brasileira.lower().startswith('http'):
                    st.link_button('Abrir card Emissão Brasileira', url=link_emissao_brasileira)
                else:
                    st.caption('Card Emissão Brasileira: N/D')
    else:
        if not termo_busca:
            # Carregar dados para métricas
            df_cartorio_all = carregar_dados_cartorio()
            df_spa_base = pd.DataFrame()

            if df_cartorio_all is not None and not df_cartorio_all.empty:
                col_id_familia_spa = 'UF_CRM_34_ID_FAMILIA'
                col_nome_familia_spa = 'UF_CRM_34_NOME_FAMILIA'
                col_resp_spa = 'ASSIGNED_BY_NAME'
                df_spa_base = df_cartorio_all[[c for c in [col_id_familia_spa, 'STAGE_ID', 'STAGE_NAME', col_nome_familia_spa, col_resp_spa] if c in df_cartorio_all.columns]].copy()

            exibir_metricas_macro(df_crm_deals_full, df_spa_base)

            if df_cartorio_all is not None and not df_cartorio_all.empty:
                exibir_visao_esteiras(df_crm_deals_full, df_cartorio_all)


# Para testar isoladamente (opcional)
if __name__ == '__main__':
    if 'pagina_atual' not in st.session_state:
        st.session_state['pagina_atual'] = "Ficha da Família"
    show_ficha_familia()


