"""
Este arquivo serve como um endpoint de verificação de saúde simplificado para o Streamlit Cloud.
Pode ser chamado pelo servidor para verificar se a aplicação está funcionando corretamente.
"""

import os
import sys
import requests
import time
import json

def check_health():
    """
    Verifica se o servidor Streamlit está respondendo.
    Retorna True se estiver saudável, False caso contrário.
    """
    try:
        response = requests.get('http://localhost:8501/healthz', timeout=5)
        return response.status_code == 200
    except:
        return False

def load_environment():
    """
    Verifica se as variáveis de ambiente necessárias estão configuradas.
    """
    required_vars = ['BITRIX_TOKEN', 'BITRIX_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"AVISO: As seguintes variáveis de ambiente estão faltando: {', '.join(missing_vars)}")
        return False
    return True

def check_dependencies():
    """
    Verifica se as dependências Python necessárias estão instaladas.
    """
    try:
        import streamlit
        import pandas
        import numpy
        import requests
        import plotly
        return True
    except ImportError as e:
        print(f"ERRO: Dependência faltando: {str(e)}")
        return False

def main():
    """
    Função principal que realiza todas as verificações de saúde.
    """
    print("Iniciando verificação de saúde...")
    
    # Verificar dependências
    print("Verificando dependências...")
    deps_ok = check_dependencies()
    if not deps_ok:
        print("FALHA: Faltam dependências.")
        return False
    
    # Verificar ambiente
    print("Verificando variáveis de ambiente...")
    env_ok = load_environment()
    if not env_ok:
        print("AVISO: Problemas com variáveis de ambiente.")
    
    # Verificar servidor
    print("Verificando servidor Streamlit...")
    max_attempts = 3
    for i in range(max_attempts):
        health_ok = check_health()
        if health_ok:
            print("SUCESSO: Servidor Streamlit está respondendo!")
            return True
        else:
            print(f"Tentativa {i+1}/{max_attempts}: Servidor não está respondendo. Aguardando...")
            time.sleep(2)
    
    print("FALHA: Servidor Streamlit não está respondendo após várias tentativas.")
    return False

if __name__ == "__main__":
    # Executar verificações
    health_status = main()
    
    # Salvar status em arquivo para consulta posterior
    with open('health_status.json', 'w') as f:
        json.dump({
            'status': 'healthy' if health_status else 'unhealthy',
            'timestamp': time.time()
        }, f)
    
    # Retornar código de saída apropriado
    sys.exit(0 if health_status else 1) 