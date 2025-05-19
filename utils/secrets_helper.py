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
    # Definir escopos necessários para planilhas e drive
    SCOPES = ['https://spreadsheets.google.com/feeds', 
              'https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/spreadsheets']
              
    try:
        print("[DEBUG] Iniciando obtenção de credenciais do Google")
        
        # DEBUG: Verificar se há secrets disponíveis
        if hasattr(st, 'secrets'):
            print("[DEBUG] st.secrets existe")
            
            # DEBUG: Listar as chaves disponíveis em st.secrets
            print(f"[DEBUG] Chaves em st.secrets: {list(st.secrets.keys() if hasattr(st.secrets, 'keys') else ['<não é um dicionário>'])}")
            
            # Verificar se há secrets no novo formato
            if "google" in st.secrets and "sheets" in st.secrets["google"]:
                print("[DEBUG] Encontrado formato google.sheets")
                try:
                    # Extrair e verificar a private_key
                    private_key = st.secrets["google"]["sheets"]["private_key"]
                    
                    # Debug para mostrar a forma da private_key
                    print(f"[DEBUG] Tamanho da private_key: {len(private_key)} caracteres")
                    print(f"[DEBUG] Primeiros 50 caracteres: {private_key[:50]}...")
                    print(f"[DEBUG] Últimos 50 caracteres: {private_key[-50:]}...")
                    
                    # Verificar se a private_key está formatada corretamente
                    if "-----BEGIN PRIVATE KEY-----" not in private_key or "-----END PRIVATE KEY-----" not in private_key:
                        print("[ERRO] Private key não está no formato correto")
                        raise ValueError("Private key não está no formato correto")
                    
                    credentials_dict = {
                        "type": st.secrets["google"]["sheets"]["type"],
                        "project_id": st.secrets["google"]["sheets"]["project_id"],
                        "private_key_id": st.secrets["google"]["sheets"]["private_key_id"],
                        "private_key": private_key,
                        "client_email": st.secrets["google"]["sheets"]["client_email"],
                        "client_id": st.secrets["google"]["sheets"]["client_id"],
                        "auth_uri": st.secrets["google"]["sheets"]["auth_uri"],
                        "token_uri": st.secrets["google"]["sheets"]["token_uri"],
                        "auth_provider_x509_cert_url": st.secrets["google"]["sheets"]["auth_provider_x509_cert_url"],
                        "client_x509_cert_url": st.secrets["google"]["sheets"]["client_x509_cert_url"]
                    }
                    
                    if "universe_domain" in st.secrets["google"]["sheets"]:
                        credentials_dict["universe_domain"] = st.secrets["google"]["sheets"]["universe_domain"]
                    
                    print("[INFO] Criando credenciais com o dicionário montado")
                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_dict, 
                        scopes=SCOPES
                    )
                    print("[INFO] Credenciais criadas com sucesso!")
                    return credentials
                    
                except Exception as e:
                    print(f"[ERRO] Falha ao criar credenciais do formato google.sheets: {str(e)}")
                    print(f"[DEBUG] Tipo do erro: {type(e)}")
                    print(f"[DEBUG] Detalhes do erro: {str(e)}")
                    raise e
            
            # Verificar se há secrets no formato antigo
            elif "gcp_service_account" in st.secrets:
                print("[DEBUG] Encontrado formato gcp_service_account (formato antigo)")
                try:
                    credentials_dict = {
                        "type": st.secrets["gcp_service_account"]["type"],
                        "project_id": st.secrets["gcp_service_account"]["project_id"],
                        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
                        "private_key": st.secrets["gcp_service_account"]["private_key"],
                        "client_email": st.secrets["gcp_service_account"]["client_email"],
                        "client_id": st.secrets["gcp_service_account"]["client_id"],
                        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
                        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
                        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
                        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
                    }
                    
                    if "universe_domain" in st.secrets["gcp_service_account"]:
                        credentials_dict["universe_domain"] = st.secrets["gcp_service_account"]["universe_domain"]
                    
                    print("[INFO] Criando credenciais com o formato antigo")
                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_dict, 
                        scopes=SCOPES
                    )
                    print("[INFO] Credenciais criadas com sucesso!")
                    return credentials
                    
                except Exception as e:
                    print(f"[ERRO] Falha ao criar credenciais do formato antigo: {str(e)}")
                    print(f"[DEBUG] Tipo do erro: {type(e)}")
                    print(f"[DEBUG] Detalhes do erro: {str(e)}")
                    raise e
            
            else:
                print("[ERRO] Nenhum formato de credenciais conhecido encontrado em st.secrets")
        
        # Se não encontrou secrets, tentar arquivo local
        print("[DEBUG] Tentando usar arquivo de credenciais local")
        possible_paths = [
            "views/cartorio_new/chaves/leitura-planilhas-459604-84a6f83793a3.json",
            "chaves/leitura-planilhas-459604-84a6f83793a3.json",
            ".streamlit/chaves/leitura-planilhas-459604-84a6f83793a3.json"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"[INFO] Usando arquivo local de credenciais: {path}")
                return service_account.Credentials.from_service_account_file(
                    path,
                    scopes=SCOPES
                )
        
        print("[ERRO] Nenhuma credencial encontrada (nem secrets nem arquivo local)")
        raise FileNotFoundError("Arquivo de credenciais do Google não encontrado e st.secrets não configurado corretamente")
            
    except Exception as e:
        print(f"[ERRO] Falha ao obter credenciais do Google: {str(e)}")
        print(f"[DEBUG] Tipo do erro: {type(e)}")
        print(f"[DEBUG] Detalhes completos do erro: {str(e)}")
        st.error(f"Erro ao carregar credenciais do Google. Verifique se as secrets estão configuradas corretamente. Detalhes: {str(e)}")
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