"""
Exemplo de como usar as secrets do projeto.
Este arquivo serve como referência e não deve ser executado diretamente em produção.
"""

import streamlit as st
from utils.secrets_helper import get_bitrix_credentials, get_database_credentials, get_google_credentials

def exemplo_acesso_bitrix():
    """Exemplo de como acessar as credenciais do Bitrix24"""
    print("Exemplo de acesso às credenciais do Bitrix24:")
    
    # Obter credenciais do helper centralizado
    creds = get_bitrix_credentials()
    
    # Usar as credenciais (exemplo)
    print(f"URL do Bitrix: {creds['bitrix_url']}")
    print(f"Token disponível: {'Sim' if creds['webhook_token'] else 'Não'}")
    
    # Alternativa: acessando diretamente pelo st.secrets (não recomendado)
    if hasattr(st, 'secrets') and 'bitrix' in st.secrets:
        print("Acesso direto via st.secrets:")
        print(f"URL: {st.secrets.bitrix.get('bitrix_url', 'N/D')}")
    
    # Construir URL de API completa
    api_url = f"{creds['bitrix_url']}/rest/1/{creds['webhook_token']}/crm.deal.list"
    print(f"URL da API construída: {api_url}")
    
    return creds

def exemplo_acesso_banco_dados():
    """Exemplo de como acessar as credenciais do banco de dados"""
    print("\nExemplo de acesso às credenciais do banco de dados:")
    
    # Obter credenciais do helper centralizado
    db_creds = get_database_credentials()
    
    # Usar as credenciais (exemplo)
    print(f"Host: {db_creds['host']}")
    print(f"Banco: {db_creds['name']}")
    print(f"Usuário: {db_creds['username']}")
    print(f"Senha disponível: {'Sim' if db_creds['password'] else 'Não'}")
    
    # Exemplo de string de conexão
    conn_string = f"mysql+mysqlconnector://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}:{db_creds['port']}/{db_creds['name']}"
    print(f"String de conexão (censurada): {conn_string.replace(db_creds['password'] or '', '********')}")
    
    return db_creds

def exemplo_acesso_google():
    """Exemplo de como acessar as credenciais do Google"""
    print("\nExemplo de acesso às credenciais do Google:")
    
    try:
        # Obter credenciais do Google
        credentials = get_google_credentials()
        
        if credentials:
            print("Credenciais do Google obtidas com sucesso!")
            # Exemplo de uso com gspread
            print("Exemplo de como usar com gspread:")
            print("```python")
            print("import gspread")
            print("gc = gspread.authorize(credentials)")
            print("spreadsheet = gc.open_by_key('ID_DA_PLANILHA')")
            print("worksheet = spreadsheet.worksheet('Nome da Aba')")
            print("data = worksheet.get_all_records()")
            print("```")
        else:
            print("Credenciais do Google não disponíveis.")
    except Exception as e:
        print(f"Erro ao acessar credenciais do Google: {e}")
    
if __name__ == "__main__":
    print("=" * 50)
    print("EXEMPLO DE USO DAS SECRETS")
    print("=" * 50)
    print("IMPORTANTE: Este é apenas um exemplo e não deve ser usado em produção.")
    print("As credenciais reais não devem ser exibidas no console.")
    print("=" * 50)
    
    # Exemplos
    exemplo_acesso_bitrix()
    exemplo_acesso_banco_dados()
    exemplo_acesso_google()
    
    print("\nObs: Em um ambiente Streamlit, você não veria estas saídas no console,")
    print("elas seriam visíveis apenas nos logs do servidor.") 