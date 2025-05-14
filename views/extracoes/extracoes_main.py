import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path

# Configurar caminho para utils
path_root = Path(__file__).parents[2]  # Subir dois níveis para chegar à raiz do projeto
sys.path.append(str(path_root))

# Importar módulos específicos do projeto
from api.bitrix_connector import load_merged_data

# Definir funções de animação localmente
def display_loading_animation(message="Carregando..."):
    """
    Exibe uma animação de carregamento com mensagem
    
    Args:
        message: Mensagem a ser exibida durante o carregamento
        
    Returns:
        Barra de progresso do Streamlit
    """
    # Criar e retornar uma barra de progresso
    st.write(message)
    return st.progress(0)

def clear_loading_animation(progress_bar, animation_container, message_container):
    """
    Limpa a animação de carregamento
    
    Args:
        progress_bar: Componente de barra de progresso do Streamlit
        animation_container: Container que contém a animação
        message_container: Container que contém a mensagem
    """
    if progress_bar:
        progress_bar.progress(1.0)
        
    # Limpar os containers
    if animation_container:
        animation_container.empty()
    if message_container:
        message_container.empty()

def show_extracoes():
    """
    Exibe a página principal de Extrações de Dados
    """
    st.title("Extrações de Dados")
    st.markdown("---")
    
    # Menu para os submódulos
    menu_options = ["Visualizar Dados", "Exportar CSV", "Consulta Personalizada"]
    selected = st.selectbox("Selecione uma opção:", menu_options)
    
    if selected == "Visualizar Dados":
        mostrar_visualizacao_dados()
    elif selected == "Exportar CSV":
        mostrar_exportar_csv()
    elif selected == "Consulta Personalizada":
        st.info("Funcionalidade de consulta personalizada será implementada nas próximas atualizações.")
    
    # Rodapé
    st.markdown("---")
    st.markdown("*Dados atualizados automaticamente. Última atualização: Agosto 2024*") 

def mostrar_visualizacao_dados():
    """
    Exibe os dados do Bitrix24 em uma tabela com filtros
    """
    st.subheader("Visualização de Dados do Bitrix24")
    
    # Filtros
    with st.expander("Filtros de Dados", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            categoria = st.selectbox(
                "Categoria:",
                [32, 33, 34, 35],
                format_func=lambda x: f"Categoria {x}"
            )
        
        with col2:
            data_inicial, data_final = st.date_input(
                "Período:",
                value=[pd.Timestamp.now() - pd.Timedelta(days=30), pd.Timestamp.now()],
                format="DD/MM/YYYY",
                key="extracao_visualizacao_periodo"
            )
    
    # Botão para carregar dados
    if st.button("Carregar Dados", key="btn_carregar", use_container_width=True, type="primary"):
        # Criar containers para animação e progresso
        animation_container = st.empty()
        progress_container = st.empty()
        message_container = st.empty()
        
        # Exibir animação de carregamento
        with animation_container:
            progress_bar = display_loading_animation("Carregando dados do Bitrix24...")
        
        try:
            # Converter datas para string no formato esperado
            date_from = data_inicial.strftime("%Y-%m-%d")
            date_to = data_final.strftime("%Y-%m-%d")
            
            # Carregar dados do Bitrix24
            df = load_merged_data(
                category_id=categoria,
                date_from=date_from,
                date_to=date_to,
                debug=False,
                progress_bar=progress_bar,
                message_container=message_container
            )
            
            # Limpar animação após carregamento
            clear_loading_animation(progress_bar, animation_container, message_container)
            
            if df.empty:
                st.warning("Não foram encontrados dados para os filtros selecionados.")
            else:
                # Mostrar estatísticas básicas
                st.success(f"Dados carregados com sucesso! Total de registros: {len(df)}")
                
                # Exibir dataframe
                st.dataframe(df, use_container_width=True)
                
                # Permitir download dos dados
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="Download dos Dados (CSV)",
                    data=csv,
                    file_name=f"dados_bitrix_{categoria}_{date_from}_{date_to}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        except Exception as e:
            # Limpar animação em caso de erro
            clear_loading_animation(progress_bar, animation_container, message_container)
            st.error(f"Erro ao carregar dados: {str(e)}")

def mostrar_exportar_csv():
    """
    Exibe a interface para exportar dados em CSV
    """
    st.subheader("Exportar Dados em CSV")
    
    # Filtros
    with st.expander("Configurações de Exportação", expanded=True):
        categoria = st.multiselect(
            "Categorias:",
            [32, 33, 34, 35],
            default=[32],
            format_func=lambda x: f"Categoria {x}"
        )
        
        data_inicial, data_final = st.date_input(
            "Período:",
            value=[pd.Timestamp.now() - pd.Timedelta(days=30), pd.Timestamp.now()],
            format="DD/MM/YYYY",
            key="extracao_exportar_periodo"
        )
        
        colunas_padrao = ["ID", "TITLE", "ASSIGNED_BY_NAME", "DATE_CREATE", "UF_CRM_HIGILIZACAO_STATUS"]
        colunas_selecionadas = st.multiselect(
            "Colunas para exportar:",
            colunas_padrao + ["STAGE_ID", "CATEGORY_ID", "OPPORTUNITY", "CURRENCY_ID"],
            default=colunas_padrao
        )
    
    # Botão para exportar
    if st.button("Gerar CSV para Exportação", key="btn_exportar", use_container_width=True, type="primary"):
        # Exibir mensagem de processamento
        with st.spinner("Gerando arquivo para exportação..."):
            try:
                # Converter datas para string no formato esperado
                date_from = data_inicial.strftime("%Y-%m-%d")
                date_to = data_final.strftime("%Y-%m-%d")
                
                # Carregar dados para cada categoria
                dfs = []
                for cat in categoria:
                    df_cat = load_merged_data(
                        category_id=cat,
                        date_from=date_from,
                        date_to=date_to,
                        debug=False
                    )
                    
                    if not df_cat.empty:
                        # Adicionar coluna de categoria se múltiplas categorias
                        if len(categoria) > 1:
                            df_cat['CATEGORIA_EXPORTACAO'] = f"Categoria {cat}"
                        
                        dfs.append(df_cat)
                
                if not dfs:
                    st.warning("Não foram encontrados dados para os filtros selecionados.")
                else:
                    # Combinar todos os dataframes
                    df_final = pd.concat(dfs, ignore_index=True)
                    
                    # Selecionar colunas desejadas (se existirem no dataframe)
                    colunas_exportar = [col for col in colunas_selecionadas if col in df_final.columns]
                    
                    # Verificar se há colunas para exportar
                    if not colunas_exportar:
                        st.warning("Nenhuma das colunas selecionadas existe nos dados. Exportando todas as colunas disponíveis.")
                        df_export = df_final
                    else:
                        df_export = df_final[colunas_exportar]
                    
                    # Exibir prévia
                    st.subheader("Prévia dos Dados para Exportação")
                    st.dataframe(df_export.head(10), use_container_width=True)
                    
                    # Permitir download dos dados
                    csv = df_export.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="Download dos Dados (CSV)",
                        data=csv,
                        file_name=f"exportacao_bitrix_{date_from}_{date_to}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                    st.success(f"Arquivo CSV gerado com sucesso! Total de registros: {len(df_export)}")
            except Exception as e:
                st.error(f"Erro ao gerar arquivo CSV: {str(e)}") 