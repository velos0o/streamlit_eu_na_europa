import streamlit as st
import requests
import json
import random
import time
import os
from pathlib import Path

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
    if not LOTTIE_AVAILABLE:
        print("Biblioteca streamlit-lottie não disponível, não é possível carregar animações.")
        return None
    
    print("Tentando carregar uma animação aleatória...")
    
    # Primeiro, tente carregar de arquivos locais
    animation_file = random.choice(ANIMATION_FILES)
    
    # Tenta diferentes locais possíveis para o arquivo
    possible_paths = [
        animation_file,  # No diretório atual
        os.path.join(".", animation_file),  # Explicitamente no diretório atual
        os.path.join(os.getcwd(), animation_file),  # Caminho absoluto no diretório atual
        os.path.join(os.path.dirname(__file__), "..", animation_file),  # Um nível acima do utils
        os.path.join(os.path.dirname(__file__), "..", "assets", animation_file),  # Na pasta assets
    ]
    
    # Tentar cada caminho
    for path in possible_paths:
        print(f"Tentando carregar de: {path}")
        animation_data = load_lottie_from_file(path)
        if animation_data:
            print(f"Animação carregada com sucesso de: {path}")
            return animation_data
    
    # Se não conseguiu carregar de arquivo local, tenta pela URL
    print("Não foi possível carregar de arquivos locais, tentando URL...")
    animation_id = animation_file.split(" - ")[1].split(".")[0]
    animation_data = load_lottie_by_id(animation_id)
    
    if animation_data:
        print("Animação carregada com sucesso da URL.")
    else:
        print("Não foi possível carregar a animação de nenhuma fonte.")
        
    return animation_data

def display_loading_animation(message="Carregando dados...", min_display_time=5):
    """
    Exibe uma animação de carregamento com barra de progresso
    
    Args:
        message (str): Mensagem para exibir junto com a animação
        min_display_time (int): Tempo mínimo em segundos para exibir a animação
        
    Returns:
        tuple: Placeholders para atualização (progress_bar, animation_container, message_container)
    """
    # Armazenar o tempo de início
    st.session_state['animation_start_time'] = time.time()
    st.session_state['min_display_time'] = min_display_time
    
    # Estilos para a animação de carregamento em tela cheia
    st.markdown("""
    <style>
    .loading-animation {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 50px auto;
        max-width: 800px;
    }
    .loading-message {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
        text-align: center;
    }
    .loading-progress {
        width: 100%;
        margin: 20px 0;
    }
    .loading-emoji {
        font-size: 48px;
        margin: 10px;
        animation: pulse 1.5s infinite alternate;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        100% { transform: scale(1.2); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container principal para centralizar tudo
    st.markdown('<div class="loading-animation">', unsafe_allow_html=True)
    
    # Criar placeholders para os elementos da animação
    message_container = st.empty()
    message_container.markdown(f'<div class="loading-message">{message}</div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    animation_container = st.empty()
    
    # Verificar se a biblioteca Lottie está disponível
    if LOTTIE_AVAILABLE:
        # Carregar e exibir uma animação aleatória
        animation_data = get_random_animation()
        
        if animation_data:
            with animation_container:
                try:
                    st_lottie(animation_data, height=400, key="loading_animation")
                except Exception as e:
                    st.error(f"Erro ao renderizar animação: {str(e)}")
        else:
            with animation_container:
                st.markdown("""
                <div style="display: flex; justify-content: center; align-items: center; height: 300px;">
                    <div class="loading-emoji">⏳</div>
                    <div class="loading-emoji">📊</div>
                    <div class="loading-emoji">📈</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Versão alternativa sem a biblioteca Lottie
        loading_emojis = ["⏳", "🔄", "📊", "📈", "📋", "💼", "📁", "🗂️", "📑", "🔍"]
        
        with animation_container:
            st.markdown("""
            <div style="display: flex; justify-content: center; align-items: center; flex-wrap: wrap; height: 300px;">
            """, unsafe_allow_html=True)
            
            for emoji in loading_emojis[:5]:
                st.markdown(f'<div class="loading-emoji">{emoji}</div>', unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Fechar o container principal
    st.markdown('</div>', unsafe_allow_html=True)
    
    return progress_bar, animation_container, message_container

def update_progress(progress_bar, value, message_container=None, message=None):
    """
    Atualiza a barra de progresso e opcionalmente a mensagem
    
    Args:
        progress_bar: Placeholder da barra de progresso do streamlit
        value (float): Valor entre 0 e 1 para atualizar a barra
        message_container: Placeholder da mensagem (opcional)
        message (str): Nova mensagem (opcional)
    """
    progress_bar.progress(value)
    if message_container and message:
        message_container.markdown(f'<div class="loading-message">{message}</div>', unsafe_allow_html=True)

def clear_loading_animation(progress_bar, animation_container, message_container):
    """
    Limpa a animação de carregamento, respeitando o tempo mínimo de exibição
    
    Args:
        progress_bar: Placeholder da barra de progresso
        animation_container: Placeholder da animação
        message_container: Placeholder da mensagem
    """
    # Verificar se precisamos esperar mais tempo
    if 'animation_start_time' in st.session_state and 'min_display_time' in st.session_state:
        elapsed_time = time.time() - st.session_state['animation_start_time']
        remaining_time = st.session_state['min_display_time'] - elapsed_time
        
        if remaining_time > 0:
            time.sleep(remaining_time)
    
    # Limpar os elementos
    progress_bar.empty()
    animation_container.empty()
    message_container.empty()
    
    # Limpar as variáveis de estado
    if 'animation_start_time' in st.session_state:
        del st.session_state['animation_start_time']
    if 'min_display_time' in st.session_state:
        del st.session_state['min_display_time'] 