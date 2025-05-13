# Instruções para Deploy no Streamlit Cloud

Este documento contém as instruções detalhadas para realizar o deploy da aplicação Eu na Europa no Streamlit Cloud.

## Pré-requisitos

1. Conta no Streamlit Cloud (https://streamlit.io/cloud)
2. Repositório Git configurado (GitHub, GitLab ou Bitbucket)
3. Arquivo `requirements.txt` atualizado com todas as dependências
4. Arquivo de secrets configurado localmente (`.streamlit/secrets.toml`)

## Preparação do Repositório

Antes de fazer o deploy, verifique se:

1. O arquivo `.streamlit/secrets.toml` está incluído no `.gitignore`
2. O arquivo `requirements.txt` está atualizado
3. O arquivo principal é o `main.py` na raiz do projeto

## Deploy no Streamlit Cloud

1. Acesse https://streamlit.io/cloud e faça login com sua conta
2. Clique em "New app"
3. Selecione o repositório onde você fez o upload do projeto
4. Configurações do app:
   - **Repository**: `https://github.com/velos0o/streamlit_eu_na_europa`
   - **Branch**: `master` (ou `main`, dependendo da configuração)
   - **Main file path**: `main.py`
   - **App URL**: Escolha um subdomínio único ou use o gerado automaticamente

5. Clique em "Advanced settings" e configure:
   - **Python version**: `3.10`
   - **Packages**: Deixe em branco (já temos o requirements.txt)

6. Clique em "Deploy!"

## Configuração de Secrets no Streamlit Cloud

Após o deploy inicial (mesmo que a aplicação apresente erros por falta das secrets):

1. Vá até a página do app no Streamlit Cloud
2. Clique nos três pontos (⋮) na parte superior direita
3. Selecione "Settings"
4. Na seção "Secrets", clique em "Edit secrets"
5. Cole o conteúdo do seu arquivo `.streamlit/secrets.toml` local
   ```toml
   # Secrets do projeto Eu na Europa
   
   [bitrix]
   webhoook_token = "seu_token_aqui"
   bitrix_url = "https://sua-instancia.bitrix24.com"
   oauth_client_id = "seu_client_id_aqui"
   oauth_client_secret = "seu_client_secret_aqui"
   
   [database]
   host = "hostname_db"
   port = 3306
   username = "usuario_db"
   password = "senha_db"
   name = "nome_db"
   
   # ... outras secrets ...
   ```
6. Clique em "Save"
7. Reinicie o app clicando em "Reboot app" nos três pontos (⋮)

## Verificação do Deploy

Para verificar se o deploy foi bem sucedido e se as secrets estão funcionando:

1. Acesse o app pela URL fornecida pelo Streamlit Cloud
2. Verifique se a aplicação está funcionando corretamente
3. Teste especificamente as funcionalidades que dependem das secrets (conexão com Bitrix24, banco de dados, etc.)

## Troubleshooting

Se encontrar problemas com o deploy:

### Problemas com Secrets

- Verifique nos logs se há mensagens de erro relacionadas às secrets
- Confirme se o formato no Streamlit Cloud está exatamente igual ao local
- Tente adicionar as secrets manualmente, uma a uma

### Problemas com Dependências

- Verifique os logs para erros de importação
- Certifique-se de que todas as dependências estão no `requirements.txt` com versões específicas
- Algumas dependências podem precisar de pacotes do sistema operacional; nesse caso, você precisará de um Dockerfile personalizado

### Problemas com Timeout

- O Streamlit Cloud tem um limite de tempo para inicialização (2 minutos)
- Se sua aplicação demora mais que isso para inicializar, considere otimizar o carregamento inicial
- Use `@st.cache_data` e `@st.cache_resource` para funções pesadas

## Mais Informações

- [Documentação oficial do Streamlit Cloud](https://docs.streamlit.io/streamlit-cloud)
- [Gerenciando secrets no Streamlit](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [GitHub do projeto](https://github.com/velos0o/streamlit_eu_na_europa) 