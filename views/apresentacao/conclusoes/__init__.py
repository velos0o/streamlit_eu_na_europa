# Módulo de slides de conclusões para apresentação TV
from views.apresentacao.conclusoes.metricas import slide_metricas_destaque
from views.apresentacao.conclusoes.ranking import slide_ranking_produtividade
from views.apresentacao.conclusoes.analise_diaria import slide_analise_diaria
from views.apresentacao.conclusoes.analise_semanal import slide_analise_semanal
from views.apresentacao.conclusoes.analise_dia_semana import slide_analise_dia_semana
from views.apresentacao.conclusoes.analise_horario import slide_analise_horario

__all__ = [
    'slide_metricas_destaque',
    'slide_ranking_produtividade',
    'slide_analise_diaria',
    'slide_analise_semanal',
    'slide_analise_dia_semana',
    'slide_analise_horario'
] 