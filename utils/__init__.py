"""
Módulo de utilitários para o dashboard.

Este arquivo __init__.py serve para facilitar a importação de funções
dos diversos módulos de utilitários.
"""

# Importações das funções utilitárias para DataFrames
from .dataframe_utils import ensure_pandas_df, ensure_pandas_series, safe_dataframe, safe_bar_chart, safe_line_chart, safe_scatter_chart, safe_area_chart

# Importação da função de atualização de dados
from .refresh_utils import handle_refresh_trigger, clear_file_cache

# Importação das funções de ajuda para credenciais
from .secrets_helper import get_google_credentials

# Importação de funções de animação
from .animation_utils import display_loading_animation, update_progress 