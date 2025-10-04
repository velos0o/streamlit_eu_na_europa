"""
Módulo Ficha da Família - Relatório Individual de Famílias
===========================================================

Estrutura modular para escalabilidade:
- ficha_familia_main.py: Função principal e orquestração
- data_loader.py: Carregamento de dados
- pdf_generator.py: Geração de PDFs
- display_components.py: Componentes visuais
- business_logic.py: Lógica de negócio
- metrics.py: Métricas e estatísticas
- utils.py: Funções auxiliares
"""

from .ficha_familia_main import show_ficha_familia

__all__ = ['show_ficha_familia']


