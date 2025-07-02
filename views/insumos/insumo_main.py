import streamlit as st
from .data_loader import get_bitrix_data
from utils.dataframe_utils import ensure_pandas_df
from .mapa_inicial import show_mapa_inicial
from .fluxo_financeiro import show_fluxo_financeiro
from .ia import show_ia
from .criacao_adendo import show_criacao_adendo
from .consulta_familia import show_consulta_familia

def show_insumos(sub_page):
    """
    Exibe a página de Insumos, carregando os dados uma vez e passando-os
    para a sub-página correta para renderização.
    """
    df_insumos = get_bitrix_data()
    df_insumos = ensure_pandas_df(df_insumos)

    if df_insumos.empty:
        st.warning("Nenhum dado de insumos foi carregado do Bitrix.")
        return

    # Mapeamento de páginas que usam um DataFrame filtrado por uma única categoria
    page_map_single_category = {
        'MAPA INICIAL': (show_mapa_inicial, 114),
        'FLUXO FINANCEIRO': (show_fluxo_financeiro, 116),
        'IA': (show_ia, 118)
    }
    
    # Lógica para a nova página de consulta
    if sub_page == 'CONSULTA DE FAMÍLIAS':
        # Filtra para as categorias relevantes para a consulta
        df_consulta = df_insumos[df_insumos['CATEGORY_ID'].isin([114, 116, 118])].copy()
        show_consulta_familia(df_consulta)
        
    elif sub_page == 'CRIAÇÃO DE ADENDO':
        show_criacao_adendo()

    elif sub_page in page_map_single_category:
        show_function, category_id = page_map_single_category[sub_page]
        
        # Filtra o DataFrame para a categoria específica da página
        df_page = df_insumos[df_insumos['CATEGORY_ID'] == category_id].copy()
        
        # Chama a função de renderização da página com os dados já filtrados
        show_function(df_page)
    else:
        st.info("Selecione uma sub-página no menu 'Insumos'.")
        # Página padrão
        show_mapa_inicial(df_insumos[df_insumos['CATEGORY_ID'] == 114].copy()) 