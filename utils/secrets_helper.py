import json
import streamlit as st
import os
from google.oauth2 import service_account
from pathlib import Path

def get_google_credentials():
    """
    Obtém credenciais do Google de forma segura, priorizando:
    1. Secrets do Streamlit (para produção)
    2. Arquivo local (para desenvolvimento)
    
    Returns:
        google.oauth2.service_account.Credentials: Credenciais de serviço do Google
    """
    try:
        # Verificar se há secrets configurados no Streamlit
        if "google" in st.secrets and "sheets" in st.secrets["google"]:
            # Criar dicionário de credenciais a partir dos secrets
            credentials_dict = {
                "type": st.secrets["google"]["sheets"]["type"],
                "project_id": st.secrets["google"]["sheets"]["project_id"],
                "private_key_id": st.secrets["google"]["sheets"]["private_key_id"],
                "private_key": st.secrets["google"]["sheets"]["private_key"],
                "client_email": st.secrets["google"]["sheets"]["client_email"],
                "client_id": st.secrets["google"]["sheets"]["client_id"],
                "auth_uri": st.secrets["google"]["sheets"]["auth_uri"],
                "token_uri": st.secrets["google"]["sheets"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["google"]["sheets"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["google"]["sheets"]["client_x509_cert_url"],
                "universe_domain": st.secrets["google"]["sheets"]["universe_domain"] 
            }
            
            print("[INFO] Usando credenciais do Google armazenadas nos secrets do Streamlit")
            return service_account.Credentials.from_service_account_info(credentials_dict)
        
        # Tentar encontrar arquivo de credenciais local (apenas para desenvolvimento)
        else:
            # Lista de possíveis caminhos para o arquivo de credenciais
            possible_paths = [
                "views/cartorio_new/chaves/leitura-planilhas-459604-84a6f83793a3.json",
                "chaves/leitura-planilhas-459604-84a6f83793a3.json",
                ".streamlit/chaves/leitura-planilhas-459604-84a6f83793a3.json"
            ]
            
            # Verificar cada caminho
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"[AVISO] Usando arquivo local de credenciais: {path}")
                    print("[AVISO] Recomendamos migrar para Streamlit Secrets em produção!")
                    return service_account.Credentials.from_service_account_file(path)
            
            # Se chegou aqui, não encontrou credenciais
            raise FileNotFoundError("Arquivo de credenciais do Google não encontrado")
                
    except Exception as e:
        print(f"[ERRO] Falha ao obter credenciais do Google: {str(e)}")
        st.error(f"Erro ao carregar credenciais do Google. Verifique se as secrets estão configuradas corretamente.")
        raise e

def migrate_json_to_secrets():
    """
    Utilitário para migrar credenciais de um arquivo JSON para o formato de secrets do Streamlit.
    Apenas para uso em desenvolvimento.
    """
    # Lista de possíveis caminhos para o arquivo de credenciais
    possible_paths = [
        "views/cartorio_new/chaves/leitura-planilhas-459604-84a6f83793a3.json",
        "chaves/leitura-planilhas-459604-84a6f83793a3.json",
        ".streamlit/chaves/leitura-planilhas-459604-84a6f83793a3.json"
    ]
    
    # Verificar cada caminho
    json_path = None
    for path in possible_paths:
        if os.path.exists(path):
            json_path = path
            break
    
    if not json_path:
        print("Arquivo de credenciais JSON não encontrado")
        return
    
    # Ler o arquivo JSON
    with open(json_path, 'r') as f:
        creds = json.load(f)
    
    # Formatar para o formato de secrets.toml
    output = """[google.sheets]
"""
    for key, value in creds.items():
        if key == "private_key":
            output += f'{key} = """{value}"""\n'
        else:
            output += f'{key} = "{value}"\n'
    
    print("\n=== Copie o conteúdo abaixo para seu arquivo .streamlit/secrets.toml ===\n")
    print(output)
    print("\n=== Fim do conteúdo para copiar ===\n")
    
    # Opcionalmente, salvar em um arquivo temporário
    with open("temp_secrets_snippet.toml", "w") as f:
        f.write(output)
    
    print(f"O snippet também foi salvo em 'temp_secrets_snippet.toml'")

# Exemplo de uso do helper
if __name__ == "__main__":
    # Se rodar este arquivo diretamente, tenta migrar as credenciais
    migrate_json_to_secrets() 