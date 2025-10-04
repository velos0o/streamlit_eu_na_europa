"""
Configurações de Performance para o Dashboard Streamlit

Este arquivo centraliza todas as configurações de cache e performance
para facilitar ajustes e manutenção.
"""

# ============================================================================
# CONFIGURAÇÕES DE CACHE (TTL em segundos)
# ============================================================================

# Cache de Dados da API
API_CACHE_TTL = 1800  # 1 hora - Dados do Bitrix24

# Cache de Processamento de Dados
DATA_PROCESSING_TTL = 600  # 10 minutos - Cálculos e agregações
FILTER_OPERATIONS_TTL = 300  # 5 minutos - Operações de filtro
QUICK_OPERATIONS_TTL = 60  # 1 minuto - Operações rápidas

# Cache de Componentes
TABLE_GENERATION_TTL = 600  # 10 minutos - Geração de tabelas
CHART_GENERATION_TTL = 600  # 10 minutos - Geração de gráficos

# Cache de Recursos Externos
GOOGLE_SHEETS_TTL = 900  # 15 minutos - Dados do Google Sheets
STATIC_FILES_TTL = 86400  # 24 horas - Arquivos estáticos (CSS, imagens)

# ============================================================================
# CONFIGURAÇÕES DE SESSION STATE
# ============================================================================

# Chaves do Session State que devem ser mantidas entre páginas
PERSISTENT_KEYS = [
    'pagina_atual',
    'user_preferences',
    'theme_settings',
    'last_refresh_timestamp',
]

# Chaves que devem ser limpas em refresh completo
CACHE_KEYS_TO_CLEAR = [
    'df_inicio',
    'df_producao', 
    'df_conclusoes',
    'df_cartorio',
    'df_comune',
    'df_extracoes',
    'filtered_df',
    'filtered_df_cat34',
]

# ============================================================================
# CONFIGURAÇÕES DE PERFORMANCE
# ============================================================================

# Tamanho máximo de DataFrame para exibição direta (linhas)
MAX_DATAFRAME_ROWS = 100000

# Número de linhas por página em tabelas paginadas
PAGINATION_SIZE = 50

# Timeout para requests HTTP (segundos)
HTTP_TIMEOUT = 30

# Número máximo de tentativas em caso de falha
MAX_RETRIES = 3

# Delay entre tentativas (segundos)
RETRY_DELAY = 2

# ============================================================================
# CONFIGURAÇÕES DE UI
# ============================================================================

# Tempo mínimo de exibição da animação de loading (segundos)
MIN_LOADING_TIME = 1.0

# Altura padrão de tabelas
DEFAULT_TABLE_HEIGHT = 400

# Largura da sidebar
SIDEBAR_WIDTH = 300

# ============================================================================
# CONFIGURAÇÕES DE LOG E DEBUG
# ============================================================================

# Habilitar logs de performance
ENABLE_PERFORMANCE_LOGS = False

# Habilitar logs de cache
ENABLE_CACHE_LOGS = False

# Nível de log (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"

# ============================================================================
# CONFIGURAÇÕES AVANÇADAS
# ============================================================================

# Habilitar compressão de DataFrames no session_state
ENABLE_DATAFRAME_COMPRESSION = False

# Usar pickle para serialização de objetos grandes
USE_PICKLE_SERIALIZATION = False

# Limpar automaticamente cache antigo
AUTO_CLEAR_OLD_CACHE = True

# Idade máxima do cache para limpeza automática (segundos)
MAX_CACHE_AGE = 7200  # 2 horas

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def get_cache_ttl(cache_type: str) -> int:
    """
    Retorna o TTL apropriado para um tipo de cache
    
    Args:
        cache_type: Tipo de cache ('api', 'processing', 'table', etc.)
    
    Returns:
        TTL em segundos
    """
    cache_ttls = {
        'api': API_CACHE_TTL,
        'processing': DATA_PROCESSING_TTL,
        'filter': FILTER_OPERATIONS_TTL,
        'quick': QUICK_OPERATIONS_TTL,
        'table': TABLE_GENERATION_TTL,
        'chart': CHART_GENERATION_TTL,
        'sheets': GOOGLE_SHEETS_TTL,
        'static': STATIC_FILES_TTL,
    }
    
    return cache_ttls.get(cache_type, DATA_PROCESSING_TTL)


def should_cache_operation(data_size: int, operation_complexity: str = 'medium') -> bool:
    """
    Determina se uma operação deve ser cacheada baseado em seu tamanho e complexidade
    
    Args:
        data_size: Número de registros ou tamanho dos dados
        operation_complexity: 'low', 'medium', ou 'high'
    
    Returns:
        True se deve cachear, False caso contrário
    """
    # Operações pequenas e simples não precisam de cache
    if operation_complexity == 'low' and data_size < 100:
        return False
    
    # Operações médias com poucos dados podem não precisar de cache
    if operation_complexity == 'medium' and data_size < 50:
        return False
    
    # Todas as outras operações devem ser cacheadas
    return True


def get_optimal_ttl(data_volatility: str) -> int:
    """
    Retorna o TTL ótimo baseado na volatilidade dos dados
    
    Args:
        data_volatility: 'high', 'medium', ou 'low'
    
    Returns:
        TTL em segundos
    """
    volatility_ttls = {
        'high': 60,      # 1 minuto - dados que mudam frequentemente
        'medium': 600,   # 10 minutos - dados que mudam ocasionalmente
        'low': 3600,     # 1 hora - dados relativamente estáticos
    }
    
    return volatility_ttls.get(data_volatility, 600)


# ============================================================================
# CONFIGURAÇÃO POR AMBIENTE
# ============================================================================

import os

# Detectar ambiente
ENVIRONMENT = os.getenv('STREAMLIT_ENV', 'development')

# Ajustar configurações por ambiente
if ENVIRONMENT == 'production':
    # Em produção, caches mais longos e logs mínimos
    ENABLE_PERFORMANCE_LOGS = False
    ENABLE_CACHE_LOGS = False
    LOG_LEVEL = "WARNING"
    
elif ENVIRONMENT == 'development':
    # Em desenvolvimento, logs detalhados e caches mais curtos
    ENABLE_PERFORMANCE_LOGS = True
    ENABLE_CACHE_LOGS = True
    LOG_LEVEL = "DEBUG"
    
    # Reduzir TTLs para desenvolvimento
    API_CACHE_TTL = 300  # 5 minutos
    DATA_PROCESSING_TTL = 180  # 3 minutos

# ============================================================================
# EXPORTAR CONFIGURAÇÕES
# ============================================================================

__all__ = [
    # TTLs
    'API_CACHE_TTL',
    'DATA_PROCESSING_TTL',
    'FILTER_OPERATIONS_TTL',
    'TABLE_GENERATION_TTL',
    'GOOGLE_SHEETS_TTL',
    
    # Session State
    'PERSISTENT_KEYS',
    'CACHE_KEYS_TO_CLEAR',
    
    # Performance
    'MAX_DATAFRAME_ROWS',
    'PAGINATION_SIZE',
    'HTTP_TIMEOUT',
    
    # Funções
    'get_cache_ttl',
    'should_cache_operation',
    'get_optimal_ttl',
]

