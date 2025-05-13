"""
Utilitário para manipulação de secrets no projeto Eu na Europa.
Este módulo disponibiliza funções para gerenciar e acessar secrets do Streamlit
de maneira consistente, tanto em ambiente de desenvolvimento quanto em produção.
"""

import json
import streamlit as st
import os
from google.oauth2 import service_account
from pathlib import Path
import toml
import dotenv

# Carregar variáveis de ambiente do arquivo .env, se existir
dotenv.load_dotenv()

def get_project_root():
    """Retorna o caminho da raiz do projeto"""
    return Path(__file__).parent.parent

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
        if hasattr(st, 'secrets'):
            print("[DEBUG] Secrets do Streamlit disponíveis")
            
            # Verificar se a seção google existe
            if "google" in st.secrets:
                print("[DEBUG] Seção 'google' encontrada nos secrets")
                
                # Verificar se a subseção sheets existe
                if "sheets" in st.secrets["google"]:
                    print("[DEBUG] Subseção 'sheets' encontrada nos secrets")
                    
                    # Listar as chaves disponíveis para diagnóstico
                    available_keys = list(st.secrets["google"]["sheets"].keys())
                    print(f"[DEBUG] Chaves disponíveis em google.sheets: {available_keys}")
                    
                    # Verificar se as chaves necessárias existem
                    required_keys = ["type", "project_id", "private_key_id", "private_key", 
                                    "client_email", "client_id", "auth_uri", "token_uri", 
                                    "auth_provider_x509_cert_url", "client_x509_cert_url"]
                    
                    missing_keys = [key for key in required_keys if key not in available_keys]
                    if missing_keys:
                        print(f"[ERRO] Chaves ausentes em google.sheets: {missing_keys}")
                        raise KeyError(f"Chaves obrigatórias ausentes: {missing_keys}")
                    
                    # Criar dicionário de credenciais a partir dos secrets
                    credentials_dict = {}
                    for key in required_keys:
                        value = st.secrets["google"]["sheets"][key]
                        credentials_dict[key] = value
                    
                    # Adicionar universe_domain se disponível
                    if "universe_domain" in available_keys:
                        credentials_dict["universe_domain"] = st.secrets["google"]["sheets"]["universe_domain"]
                    else:
                        # Usar valor padrão se não existir
                        credentials_dict["universe_domain"] = "googleapis.com"
                    
                    print("[INFO] Usando credenciais do Google armazenadas nos secrets do Streamlit")
                    return service_account.Credentials.from_service_account_info(credentials_dict)
                else:
                    print("[ERRO] Subseção 'sheets' não encontrada nos secrets")
            else:
                print("[ERRO] Seção 'google' não encontrada nos secrets")
            
            # FALLBACK 1: Verificar se existe uma seção google_sheets direta
            if "google_sheets" in st.secrets:
                print("[DEBUG] Encontrada seção google_sheets nos secrets")
                sheets_info = st.secrets["google_sheets"]
                
                credentials_dict = {
                    "type": "service_account",
                    "project_id": sheets_info.get("project_id", ""),
                    "private_key_id": sheets_info.get("private_key_id", ""),
                    "private_key": sheets_info.get("private_key", ""),
                    "client_email": sheets_info.get("client_email", ""),
                    "client_id": sheets_info.get("client_id", ""),
                    "auth_uri": sheets_info.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                    "token_uri": sheets_info.get("token_uri", "https://oauth2.googleapis.com/token"),
                    "auth_provider_x509_cert_url": sheets_info.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
                    "client_x509_cert_url": sheets_info.get("client_x509_cert_url", ""),
                    "universe_domain": sheets_info.get("universe_domain", "googleapis.com")
                }
                
                if credentials_dict["private_key"] and credentials_dict["client_email"]:
                    print("[INFO] Usando credenciais da seção google_sheets")
                    return service_account.Credentials.from_service_account_info(credentials_dict)
        
        # Se chegou aqui, não encontrou nas secrets, tentar arquivo local
        print("[DEBUG] Tentando encontrar arquivo de credenciais local")
        
        # Caminhos possíveis para o arquivo de credenciais
        possible_paths = [
            "views/cartorio_new/chaves/leitura-planilhas-459604-84a6f83793a3.json",
            "chaves/leitura-planilhas-459604-84a6f83793a3.json",
            ".streamlit/chaves/leitura-planilhas-459604-84a6f83793a3.json",
            os.path.join("data", "leitura-planilhas-459604-84a6f83793a3.json"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "leitura-planilhas-459604-84a6f83793a3.json")
        ]
        
        # Verificar cada caminho
        for path in possible_paths:
            full_path = os.path.join(get_project_root(), path)
            print(f"[DEBUG] Verificando existência do arquivo: {full_path}")
            
            if os.path.exists(full_path):
                print(f"[AVISO] Usando arquivo local de credenciais: {full_path}")
                print("[AVISO] Recomendamos migrar para Streamlit Secrets em produção!")
                return service_account.Credentials.from_service_account_file(full_path)
        
        # SOLUÇÃO ALTERNATIVA PARA DESENVOLVIMENTO: Criar credenciais falsas (dummy)
        if os.getenv('ENVIRONMENT') != 'production':
            print("[AVISO] Ambiente de desenvolvimento detectado - usando credenciais dummy")
            # Retornar um objeto falso que permite que a aplicação continue
            class DummyCredentials:
                def __init__(self):
                    self.token = "dummy_token"
                    self.expired = False
                    self.valid = True
                
                def refresh(self, request):
                    pass
            
            return DummyCredentials()
            
        # Se chegou aqui, não encontrou credenciais
        print("[ERRO] Nenhuma fonte de credenciais Google encontrada")
        raise FileNotFoundError("Arquivo de credenciais do Google não encontrado e secrets não configurados")
                
    except Exception as e:
        print(f"[ERRO] Falha ao obter credenciais do Google: {str(e)}")
        import traceback
        print(f"[DEBUG] Traceback completo: {traceback.format_exc()}")
        st.error(f"Erro ao carregar credenciais do Google. Verifique se as secrets estão configuradas corretamente.")
        
        # Em desenvolvimento, permite continuar com um erro mais suave
        if os.getenv('ENVIRONMENT') != 'production':
            print("[AVISO] Ambiente de desenvolvimento detectado - retornando None")
            return None
            
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

def get_bitrix_credentials():
    """
    Obtém as credenciais do Bitrix24 de forma segura.
    
    Returns:
        dict: Dicionário com as credenciais do Bitrix24
    """
    try:
        # Verificar se estamos em ambiente Streamlit Cloud ou similar
        if hasattr(st, 'secrets') and 'bitrix' in st.secrets:
            creds = {
                'webhook_token': st.secrets.bitrix.get('webhoook_token'),
                'bitrix_url': st.secrets.bitrix.get('bitrix_url'),
                'oauth_client_id': st.secrets.bitrix.get('oauth_client_id', None),
                'oauth_client_secret': st.secrets.bitrix.get('oauth_client_secret', None)
            }
        # Verificar se existe arquivo de secrets local
        elif os.path.exists(os.path.join(get_project_root(), '.streamlit', 'secrets.toml')):
            with open(os.path.join(get_project_root(), '.streamlit', 'secrets.toml'), 'r') as f:
                secrets = toml.load(f)
                if 'bitrix' in secrets:
                    creds = {
                        'webhook_token': secrets['bitrix'].get('webhoook_token'),
                        'bitrix_url': secrets['bitrix'].get('bitrix_url'),
                        'oauth_client_id': secrets['bitrix'].get('oauth_client_id', None),
                        'oauth_client_secret': secrets['bitrix'].get('oauth_client_secret', None)
                    }
                else:
                    raise KeyError("Seção 'bitrix' não encontrada no arquivo de secrets")
        # Última alternativa: variáveis de ambiente
        else:
            creds = {
                'webhook_token': os.getenv('BITRIX_TOKEN'),
                'bitrix_url': os.getenv('BITRIX_URL'),
                'oauth_client_id': os.getenv('BITRIX_CLIENT_ID'),
                'oauth_client_secret': os.getenv('BITRIX_CLIENT_SECRET')
            }
        
        # Verificar se credenciais essenciais existem
        if not creds['webhook_token'] or not creds['bitrix_url']:
            if os.getenv('ENVIRONMENT') == 'production':
                raise ValueError("Credenciais do Bitrix24 não encontradas no ambiente de produção")
            print("AVISO: Credenciais do Bitrix24 incompletas")
            
        return creds
    except Exception as e:
        print(f"Erro ao obter credenciais do Bitrix24: {e}")
        # Em produção, propagar o erro; em dev, retornar credenciais vazias
        if os.getenv('ENVIRONMENT') == 'production':
            raise
        return {
            'webhook_token': None,
            'bitrix_url': None,
            'oauth_client_id': None,
            'oauth_client_secret': None
        }

def get_database_credentials():
    """
    Obtém as credenciais do banco de dados de forma segura.
    
    Returns:
        dict: Dicionário com as credenciais do banco de dados
    """
    try:
        # Similar à função get_bitrix_credentials
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            return {
                'host': st.secrets.database.get('host'),
                'port': st.secrets.database.get('port', 3306),
                'username': st.secrets.database.get('username'),
                'password': st.secrets.database.get('password'),
                'name': st.secrets.database.get('name')
            }
        elif os.path.exists(os.path.join(get_project_root(), '.streamlit', 'secrets.toml')):
            with open(os.path.join(get_project_root(), '.streamlit', 'secrets.toml'), 'r') as f:
                secrets = toml.load(f)
                if 'database' in secrets:
                    return {
                        'host': secrets['database'].get('host'),
                        'port': secrets['database'].get('port', 3306),
                        'username': secrets['database'].get('username'),
                        'password': secrets['database'].get('password'),
                        'name': secrets['database'].get('name')
                    }
                else:
                    raise KeyError("Seção 'database' não encontrada no arquivo de secrets")
        else:
            return {
                'host': os.getenv('DB_HOST'),
                'port': os.getenv('DB_PORT', 3306),
                'username': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD'),
                'name': os.getenv('DB_NAME')
            }
    except Exception as e:
        print(f"Erro ao obter credenciais do banco de dados: {e}")
        if os.getenv('ENVIRONMENT') == 'production':
            raise
        return {
            'host': None,
            'port': None,
            'username': None,
            'password': None,
            'name': None
        }

def json_to_toml_converter():
    """
    Ferramenta interativa para converter credenciais JSON para o formato TOML do Streamlit.
    Útil para migrar credenciais de serviços como Google para o formato Streamlit.
    
    Uso:
        python -m utils.secrets_helper
    """
    print("\n=== Conversor de JSON para TOML para Streamlit Secrets ===\n")
    
    # Solicitar caminho do arquivo JSON
    json_path = input("Digite o caminho completo para o arquivo JSON de credenciais: ")
    
    try:
        with open(json_path, 'r') as f:
            credentials = json.load(f)
        
        # Determinar o tipo de credencial com base no conteúdo
        cred_type = "google"  # Padrão
        if "type" in credentials:
            if credentials["type"] == "service_account":
                cred_type = "google_service_account"
            elif "oauth" in credentials["type"]:
                cred_type = "google_oauth"
            elif "bitrix" in json_path.lower():
                cred_type = "bitrix"
        
        # Solicitar confirmação e personalização
        print(f"\nTipo de credencial detectado: {cred_type}")
        custom_section = input(f"Digite o nome da seção TOML (ou pressione Enter para usar '{cred_type}'): ")
        
        if custom_section:
            section_name = custom_section
        else:
            section_name = cred_type
        
        # Converter para TOML
        toml_output = f"[{section_name}]\n"
        
        # Adicionar cada campo do JSON como uma linha no TOML
        for key, value in credentials.items():
            if isinstance(value, str):
                toml_output += f'{key} = "{value}"\n'
            elif isinstance(value, (int, float, bool)):
                toml_output += f'{key} = {value}\n'
            elif isinstance(value, dict):
                # Dicionários aninhados são representados como subseções no TOML
                # Mas o Streamlit não suporta bem subseções aninhadas, então achatamos
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, str):
                        toml_output += f'{key}_{subkey} = "{subvalue}"\n'
                    else:
                        toml_output += f'{key}_{subkey} = {subvalue}\n'
            else:
                # Para outros tipos (listas, etc.), usamos representação JSON como string
                toml_output += f'{key} = "{json.dumps(value)}"\n'
        
        # Exibir resultado
        print("\n=== Resultado TOML ===\n")
        print(toml_output)
        
        # Perguntar se quer salvar
        save_option = input("\nDeseja salvar este conteúdo? (s/n): ").lower()
        
        if save_option == 's':
            save_path = input("Digite o caminho onde salvar (ou Enter para .streamlit/secrets.toml): ")
            
            if not save_path:
                # Cria diretório .streamlit se não existir
                streamlit_dir = os.path.join(get_project_root(), '.streamlit')
                os.makedirs(streamlit_dir, exist_ok=True)
                save_path = os.path.join(streamlit_dir, 'secrets.toml')
            
            # Verificar se o arquivo já existe
            append_mode = False
            if os.path.exists(save_path):
                append_option = input(f"O arquivo {save_path} já existe. Deseja anexar (a) ou sobrescrever (s)? ").lower()
                append_mode = append_option == 'a'
            
            # Salvar o arquivo
            with open(save_path, 'a' if append_mode else 'w') as f:
                if append_mode:
                    f.write("\n\n# Credenciais convertidas automaticamente\n")
                f.write(toml_output)
            
            print(f"\nConteúdo salvo em {save_path}")
        
        print("\nConversão concluída!")
        
    except FileNotFoundError:
        print(f"Erro: Arquivo {json_path} não encontrado.")
    except json.JSONDecodeError:
        print(f"Erro: O arquivo {json_path} não é um JSON válido.")
    except Exception as e:
        print(f"Erro inesperado: {e}")

# Se este arquivo for executado diretamente, iniciar o conversor
if __name__ == "__main__":
    json_to_toml_converter() 