import streamlit as st
from .data_loader import (
    get_bitrix_data, 
    get_mapa_inicial_data, 
    get_fluxo_financeiro_data, 
    get_ia_data
)
from utils.dataframe_utils import ensure_pandas_df

# Importa as funções de renderização das páginas
from .consulta_familia import show_consulta_familia
from .mapa_inicial import show_mapa_inicial
from .fluxo_financeiro import show_fluxo_financeiro
from .ia import show_ia
# Importa o novo controlador principal de Adendo
from .criacao_adendo.adendo_main import show_criacao_adendo_main

def show_insumos(sub_page, adendo_sub_page=None):
    """
    Renderiza a sub-página selecionada para 'Insumos', passando
    os dados necessários ou chamando o controlador correto.
    """
    if sub_page == "CRIAÇÃO DE ADENDO":
        # Chama o controlador de adendo e passa a sub-página dele
        show_criacao_adendo_main(adendo_sub_page)
        
    elif sub_page == "CONSULTA DE FAMÍLIAS":
        df_full = get_bitrix_data()
        df_full = ensure_pandas_df(df_full)
        if df_full.empty:
            st.warning("Nenhum dado de insumos foi carregado.")
            return
        df_consulta = df_full[df_full['CATEGORY_ID'].isin([114, 116, 118])].copy()
        show_consulta_familia(df_consulta)

    elif sub_page == "MAPA INICIAL":
        df_mapa = get_mapa_inicial_data()
        show_mapa_inicial(ensure_pandas_df(df_mapa))

    elif sub_page == "FLUXO FINANCEIRO":
        df_fluxo = get_fluxo_financeiro_data()
        show_fluxo_financeiro(ensure_pandas_df(df_fluxo))

    elif sub_page == "IA":
        df_ia = get_ia_data()
        show_ia(ensure_pandas_df(df_ia))
        
    else:
        # Página Padrão
        st.info("Selecione uma opção no menu lateral.")
        df_full = get_bitrix_data()
        if not df_full.empty:
            df_consulta = df_full[df_full['CATEGORY_ID'].isin([114, 116, 118])].copy()
            show_consulta_familia(df_consulta) 