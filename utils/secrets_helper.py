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
        # DEBUG: Verificar se há secrets disponíveis
        if hasattr(st, 'secrets'):
            print("[DEBUG] st.secrets existe")
            
            # DEBUG: Listar as chaves disponíveis em st.secrets
            print(f"[DEBUG] Chaves em st.secrets: {list(st.secrets.keys() if hasattr(st.secrets, 'keys') else ['<não é um dicionário>'])}")
            
            # Verificar se há secrets configurados no Streamlit
            if "gcp_service_account" in st.secrets:
                print("[DEBUG] gcp_service_account encontrado em st.secrets")
                
                # DEBUG: Verificar as chaves dentro de gcp_service_account
                gcp_keys = list(st.secrets["gcp_service_account"].keys()) if hasattr(st.secrets["gcp_service_account"], 'keys') else ['<não é um dicionário>']
                print(f"[DEBUG] Chaves em gcp_service_account: {gcp_keys}")
                
                # Verificar se tem as chaves mínimas necessárias
                chaves_necessarias = ["type", "project_id", "private_key", "client_email"]
                chaves_faltantes = [k for k in chaves_necessarias if k not in gcp_keys]
                
                if chaves_faltantes:
                    print(f"[ERRO] Chaves faltantes em gcp_service_account: {chaves_faltantes}")
                    raise ValueError(f"Credenciais incompletas. Faltam as chaves: {chaves_faltantes}")
                
                # Criar dicionário de credenciais a partir dos secrets
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
                    
                    print("[INFO] Usando credenciais do Google armazenadas nos secrets do Streamlit (via gcp_service_account)")
                    
                    # Criar credenciais com os escopos apropriados
                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_dict, 
                        scopes=SCOPES
                    )
                    return credentials
                    
                except Exception as e:
                    print(f"[ERRO] Falha ao criar credenciais a partir de st.secrets[\"gcp_service_account\"]: {str(e)}")
                    raise e
            else:
                print("[DEBUG] gcp_service_account NÃO encontrado em st.secrets")
                
                # Ver se temos secrets de outro formato (google.sheets por exemplo)
                if "google" in st.secrets and "sheets" in st.secrets["google"]:
                    print("[DEBUG] Tentando usar formato alternativo: st.secrets[\"google\"][\"sheets\"]")
                    try:
                        # Extrair e verificar a private_key
                        private_key = st.secrets["google"]["sheets"]["private_key"]
                        
                        # Debug para mostrar a forma da private_key
                        print(f"[DEBUG] Tamanho da private_key: {len(private_key)} caracteres")
                        print(f"[DEBUG] Primeiros 30 caracteres: {private_key[:30]}...")
                        
                        # Certificar que a private_key está formatada corretamente
                        # Às vezes o Streamlit não preserva as quebras de linha corretamente
                        if "-----BEGIN PRIVATE KEY-----" in private_key and "-----END PRIVATE KEY-----" in private_key:
                            # Remover quebras de linha existentes
                            private_key_content = private_key.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").replace("\n", "").strip()
                            
                            # Reconstruir com o formato correto
                            private_key_formatted = "-----BEGIN PRIVATE KEY-----\n"
                            # Adicionar quebras de linha a cada 64 caracteres
                            for i in range(0, len(private_key_content), 64):
                                private_key_formatted += private_key_content[i:i+64] + "\n"
                            private_key_formatted += "-----END PRIVATE KEY-----\n"
                            
                            # Substituir a chave original
                            print("[DEBUG] Private key reformatada para garantir quebras de linha corretas")
                        else:
                            private_key_formatted = private_key
                            print("[DEBUG] Private key mantida como está (não contém os marcadores padrão)")
                            
                        credentials_dict = {
                            "type": st.secrets["google"]["sheets"]["type"],
                            "project_id": st.secrets["google"]["sheets"]["project_id"],
                            "private_key_id": st.secrets["google"]["sheets"]["private_key_id"],
                            "private_key": private_key_formatted,  # Usar a versão formatada
                            "client_email": st.secrets["google"]["sheets"]["client_email"],
                            "client_id": st.secrets["google"]["sheets"]["client_id"],
                            "auth_uri": st.secrets["google"]["sheets"]["auth_uri"],
                            "token_uri": st.secrets["google"]["sheets"]["token_uri"],
                            "auth_provider_x509_cert_url": st.secrets["google"]["sheets"]["auth_provider_x509_cert_url"],
                            "client_x509_cert_url": st.secrets["google"]["sheets"]["client_x509_cert_url"]
                        }
                        if "universe_domain" in st.secrets["google"]["sheets"]:
                            credentials_dict["universe_domain"] = st.secrets["google"]["sheets"]["universe_domain"]
                        
                        print("[INFO] Usando credenciais do Google armazenadas em formato alternativo (google.sheets)")
                        credentials = service_account.Credentials.from_service_account_info(
                            credentials_dict, 
                            scopes=SCOPES
                        )
                        return credentials
                    except Exception as e:
                        print(f"[ERRO] Falha ao criar credenciais do formato alternativo: {str(e)}")
                        # Adicionar mais detalhes para debug
                        if "private_key" in str(e).lower() or "padding" in str(e).lower():
                            print("[DEBUG] Erro parece estar relacionado à formatação da private_key.")
                            print("[DEBUG] Verifique se a private_key nos secrets está formatada corretamente com as quebras de linha adequadas.")
                            print("[DEBUG] A private_key deve estar formatada com: -----BEGIN PRIVATE KEY-----\\n...conteúdo...\\n-----END PRIVATE KEY-----")
                        # Continuar para método de arquivo local
        else:
            print("[DEBUG] st.secrets NÃO existe neste ambiente")
            
        # Tentar encontrar arquivo de credenciais local (apenas para desenvolvimento)
        print("[DEBUG] Tentando usar arquivo de credenciais local")
        # Lista de possíveis caminhos para o arquivo de credenciais
        possible_paths = [
            "views/cartorio_new/chaves/leitura-planilhas-459604-84a6f83793a3.json",
            "chaves/leitura-planilhas-459604-84a6f83793a3.json",
            ".streamlit/chaves/leitura-planilhas-459604-84a6f83793a3.json"
        ]
        
        # Verificar cada caminho
        for path in possible_paths:
            if os.path.exists(path):
                print(f"[INFO] Usando arquivo local de credenciais: {path}")
                print("[AVISO] Recomendamos migrar para Streamlit Secrets em produção!")
                return service_account.Credentials.from_service_account_file(
                    path,
                    scopes=SCOPES
                )
        
        # Se chegou aqui, não encontrou credenciais
        print("[ERRO] Nenhuma credencial encontrada (nem secrets nem arquivo local)")
        raise FileNotFoundError("Arquivo de credenciais do Google não encontrado e st.secrets não configurado corretamente")
            
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