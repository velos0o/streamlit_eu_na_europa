# Arquivo de inicialização para o pacote utils
# Torna a pasta utils um módulo Python importável

# Importar funções úteis para serem acessíveis diretamente através do pacote
from .animation_utils import (
    load_lottieurl,
    display_loading_animation,
    update_progress,
    clear_loading_animation
) 