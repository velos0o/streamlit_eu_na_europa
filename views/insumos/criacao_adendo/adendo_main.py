import streamlit as st

# Importa as funções de renderização das sub-páginas
from .visao_geral import show_visao_geral
from .tipo_contrato import show_tipo_contrato
from .analise_motivos import show_analise_motivos
from .acompanhamento import show_acompanhamento

def show_criacao_adendo_main(sub_page):
    """
    Controlador principal para o módulo de Criação de Adendo.
    Renderiza a sub-página correta ('Visão Geral' ou 'Tipo de Contrato')
    com base na seleção do usuário.
    """
    
    # Mapeamento de sub-páginas para as suas respectivas funções
    pages = {
        "Visão Geral": show_visao_geral,
        "Tipo de Contrato": show_tipo_contrato,
        "Análise Adendos e Distratos": show_analise_motivos,
        "Acompanhamento Operacional": show_acompanhamento,
    }
    
    # Obtém a função da página selecionada
    page_function = pages.get(sub_page)
    
    # Se uma página válida for selecionada, a executa.
    # Caso contrário, mostra a página padrão (Visão Geral).
    if page_function:
        page_function()
    else:
        # Define 'Visão Geral' como a página padrão se nenhuma for selecionada
        show_visao_geral() 