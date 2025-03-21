from views.apresentacao.apresentacao import show_apresentacao

# IMPORTANTE: Removing deprecated file import
# from views.apresentacao.apresentacao_conclusoes import show_apresentacao_conclusoes

# Importar as funções de slide para facilitar o acesso
from views.apresentacao.funcoes_slides import (
    slide_metricas_destaque,
    slide_ranking_produtividade,
    slide_analise_diaria,
    slide_analise_semanal,
    slide_analise_dia_semana,
    slide_analise_horario,
    slide_producao_metricas_macro,
    slide_producao_status_responsavel,
    slide_producao_pendencias_responsavel,
    slide_cartorio_visao_geral,
    slide_cartorio_analise_familias,
    slide_cartorio_ids_familia
)

__all__ = [
    'show_apresentacao', 
    # Removed deprecated function
    # 'show_apresentacao_conclusoes',
    'slide_metricas_destaque',
    'slide_ranking_produtividade',
    'slide_analise_diaria',
    'slide_analise_semanal',
    'slide_analise_dia_semana',
    'slide_analise_horario',
    'slide_producao_metricas_macro',
    'slide_producao_status_responsavel',
    'slide_producao_pendencias_responsavel',
    'slide_cartorio_visao_geral',
    'slide_cartorio_analise_familias',
    'slide_cartorio_ids_familia'
]

# Garantir compatibilidade com código existente enquanto fazemos a transição
# O show_apresentacao_conclusoes foi removido pois está causando erros de importação
