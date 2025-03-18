import streamlit as st
import requests
import json
import random
import time
import os
from pathlib import Path
from datetime import datetime

# Verificar se a biblioteca streamlit-lottie está disponível
LOTTIE_AVAILABLE = False
try:
    from streamlit_lottie import st_lottie
    LOTTIE_AVAILABLE = True
    print("Biblioteca streamlit-lottie encontrada e importada com sucesso!")
except ImportError:
    # Biblioteca não está instalada
    print("AVISO: Biblioteca streamlit-lottie não encontrada.")
    pass

# IDs das animações fornecidas
ANIMATION_FILES = [
    "Animation - 1741456141736.json",
    "Animation - 1741456218200.json", 
    "Animation - 1741456230117.json"
]

# URLs base para carregamento de animações
LOTTIE_URL_BASE = "https://assets1.lottiefiles.com/animations/"

def load_lottie_from_url(url):
    """
    Carrega uma animação Lottie a partir de uma URL
    
    Args:
        url (str): URL da animação
        
    Returns:
        dict: Objeto JSON da animação, ou None em caso de erro
    """
    if not LOTTIE_AVAILABLE:
        return None
        
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except Exception as e:
        print(f"Erro ao carregar animação da URL: {str(e)}")
        return None

def load_lottie_from_file(filepath):
    """
    Carrega uma animação Lottie a partir de um arquivo local
    
    Args:
        filepath (str): Caminho para o arquivo de animação
        
    Returns:
        dict: Objeto JSON da animação, ou None em caso de erro
    """
    if not LOTTIE_AVAILABLE:
        return None
        
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(filepath):
            print(f"Arquivo não encontrado: {filepath}")
            # Tentar procurar no diretório atual
            current_dir = os.getcwd()
            alternate_path = os.path.join(current_dir, os.path.basename(filepath))
            
            if os.path.exists(alternate_path):
                filepath = alternate_path
                print(f"Arquivo encontrado em: {filepath}")
            else:
                print(f"Arquivo também não encontrado em: {alternate_path}")
                return None
        
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar animação do arquivo: {str(e)}")
        return None

def load_lottie_by_id(animation_id):
    """
    Carrega uma animação Lottie usando seu ID do LottieFiles
    
    Args:
        animation_id (str): ID da animação no LottieFiles
        
    Returns:
        dict: Objeto JSON da animação, ou None em caso de erro
    """
    if not LOTTIE_AVAILABLE:
        return None
        
    url = f"{LOTTIE_URL_BASE}{animation_id}.json"
    return load_lottie_from_url(url)

def get_random_animation():
    """
    Seleciona uma animação Lottie aleatória da lista de arquivos
    
    Returns:
        dict: Objeto JSON da animação, ou None em caso de erro
    """
    # Tratamento de erros global para esta função
    try:
        if not LOTTIE_AVAILABLE:
            print("Biblioteca streamlit-lottie não disponível, não é possível carregar animações.")
            return None
        
        print("Tentando carregar uma animação aleatória...")
        
        # Diagnóstico para depuração
        print(f"Diretório atual: {os.getcwd()}")
        print(f"Diretório do módulo: {os.path.dirname(__file__)}")
        
        # Verificar se as pastas de animação existem
        animation_paths = [
            "assets/animations",
            os.path.join(os.getcwd(), "assets", "animations"),
            os.path.join(os.path.dirname(__file__), "..", "assets", "animations")
        ]
        
        for path in animation_paths:
            if os.path.exists(path):
                print(f"✓ Diretório encontrado: {path}")
                # Listar arquivos neste diretório
                try:
                    files = os.listdir(path)
                    print(f"  Arquivos em {path}: {files}")
                except Exception as e:
                    print(f"  Erro ao listar arquivos em {path}: {str(e)}")
            else:
                print(f"✗ Diretório não encontrado: {path}")
        
        # Primeiro, tente carregar de arquivos locais
        animation_file = random.choice(ANIMATION_FILES)
        
        # Tenta diferentes locais possíveis para o arquivo
        possible_paths = [
            os.path.join("assets", "animations", animation_file),  # Novo local após reorganização
            os.path.join(os.getcwd(), "assets", "animations", animation_file),  # Caminho absoluto para novo local
            animation_file,  # No diretório atual
            os.path.join(".", animation_file),  # Explicitamente no diretório atual
            os.path.join(os.getcwd(), animation_file),  # Caminho absoluto no diretório atual
            os.path.join(os.path.dirname(__file__), "..", animation_file),  # Um nível acima do utils
            os.path.join(os.path.dirname(__file__), "..", "assets", animation_file),  # Na pasta assets
            os.path.join(os.path.dirname(__file__), "..", "assets", "animations", animation_file),  # Na pasta assets/animations
        ]
        
        # Tentar cada caminho
        for path in possible_paths:
            print(f"Tentando carregar de: {path}")
            try:
                animation_data = load_lottie_from_file(path)
                if animation_data:
                    print(f"Animação carregada com sucesso de: {path}")
                    return animation_data
            except Exception as e:
                print(f"Erro ao carregar de {path}: {str(e)}")
                # Continuar tentando outros caminhos
        
        # Se não conseguiu carregar de arquivo local, tenta pela URL
        print("Não foi possível carregar de arquivos locais, tentando URL...")
        try:
            animation_id = animation_file.split(" - ")[1].split(".")[0]
            animation_data = load_lottie_by_id(animation_id)
            
            if animation_data:
                print("Animação carregada com sucesso da URL.")
                return animation_data
            else:
                print("Não foi possível carregar a animação de nenhuma fonte.")
        except Exception as e:
            print(f"Erro ao carregar animação da URL: {str(e)}")
            
        return None
    except Exception as e:
        # Tratamento global de erros para garantir que falhas aqui não afetem o resto do aplicativo
        print(f"Erro ao tentar carregar qualquer animação: {str(e)}")
        return None

def load_lottieurl(url: str):
    """
    Carrega uma animação Lottie a partir de uma URL.
    
    Args:
        url (str): URL da animação Lottie
        
    Returns:
        dict: JSON da animação ou None em caso de falha
    """
    try:
        # Adicionar um timeout para evitar que a requisição fique pendente por muito tempo
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Levantar exceção para códigos de erro HTTP
        
        # Retornar o JSON da animação
        return response.json()
    except Exception as e:
        # Em caso de erro, imprimir mensagem se em modo debug e retornar None
        if st.session_state.get('DEBUG_MODE', False):
            st.warning(f"Não foi possível carregar animação de {url}: {str(e)}")
        return None

def display_loading_animation(message="Carregando...", animation_url=None, min_display_time=0):
    """
    Exibe uma animação de carregamento com mensagem.
    
    Args:
        message (str): Mensagem a ser exibida durante o carregamento
        animation_url (str, optional): URL da animação Lottie. Se None, usa a animação padrão.
        min_display_time (float): Tempo mínimo em segundos para exibir a animação
        
    Returns:
        tuple: (barra_progresso, container_animacao, texto_status)
    """
    # Registrar o horário inicial se um tempo mínimo for especificado
    if min_display_time > 0:
        st.session_state['animation_start_time'] = datetime.now()
        st.session_state['min_animation_time'] = min_display_time
    
    # Criar containers para elementos da UI
    animation_container = st.empty()
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Definir mensagem de status inicial
    status_text.info(message)
    
    # Tentar carregar e exibir a animação
    try:
        # Se URL não especificada, usar animação padrão
        if animation_url is None:
            animation_url = "https://assets9.lottiefiles.com/packages/lf20_b88nh30c.json"
        
        # Carregar animação
        lottie_loading = load_lottieurl(animation_url)
        
        # Exibir animação se disponível
        if lottie_loading:
            import streamlit_lottie as st_lottie
            with animation_container:
                st_lottie.st_lottie(lottie_loading, speed=1, height=200, key="loading")
    except Exception as e:
        # Se houver erro na animação, usar spinner padrão do Streamlit
        if st.session_state.get('DEBUG_MODE', False):
            animation_container.warning(f"Não foi possível exibir animação: {str(e)}")
        else:
            animation_container.info("Carregando...")
    
    return progress_bar, animation_container, status_text

def update_progress(progress_bar, progress_value, status_text=None, message=None):
    """
    Atualiza a barra de progresso e mensagem.
    
    Args:
        progress_bar: Objeto da barra de progresso
        progress_value (float): Valor do progresso (0.0 a 1.0)
        status_text: Objeto de texto para atualizar
        message (str, optional): Nova mensagem a ser exibida
    """
    # Atualizar barra de progresso
    progress_bar.progress(progress_value)
    
    # Atualizar mensagem se necessário
    if status_text is not None and message is not None:
        status_text.info(message)

def clear_loading_animation(progress_bar, animation_container, status_text):
    """
    Limpa a animação de carregamento, respeitando o tempo mínimo de exibição.
    
    Args:
        progress_bar: Objeto da barra de progresso
        animation_container: Container da animação
        status_text: Objeto de texto com status
    """
    # Verificar se há um tempo mínimo definido
    if 'animation_start_time' in st.session_state:
        # Calcular quanto tempo a animação está sendo exibida
        elapsed_time = (datetime.now() - st.session_state['animation_start_time']).total_seconds()
        min_time = st.session_state.get('min_animation_time', 0)
        
        # Se não atingiu o tempo mínimo, esperar
        if elapsed_time < min_time:
            time.sleep(min_time - elapsed_time)
    
    # Completar a barra de progresso
    progress_bar.progress(1.0)
    
    # Limpar os elementos da UI
    animation_container.empty()
    status_text.empty()
    progress_bar.empty()
    
    # Remover a informação de tempo
    if 'animation_start_time' in st.session_state:
        del st.session_state['animation_start_time']
        if 'min_animation_time' in st.session_state:
            del st.session_state['min_animation_time'] 