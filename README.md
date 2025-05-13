# Dashboard Analítico - Streamlit Eu na Europa

## Sobre o Projeto

Dashboard desenvolvido em Streamlit para análise de dados da operação Eu na Europa, com foco na visualização e análise de processos, produtividade, conclusões e outros indicadores relevantes, utilizando dados do CRM Bitrix24 e outras fontes.

## Estrutura do Projeto

```
📂 streamlit_eu_na_europa/
│
├── 📄 main.py                   # Arquivo principal da aplicação
│
├── 📂 assets/                   # Recursos estáticos
│   └── 📂 styles/             # Estilos CSS e SCSS
│       ├── 📂 css/
│       └── 📂 scss/
│           └── 📂 components/
│   └── 📂 animations/         # Animações (Lottie)
│
├── 📂 views/                    # Páginas (abas) do dashboard
│   ├── 📂 apresentacao/         # Módulo: Apresentação modo TV
│   │   ├── 📂 cartorio/
│   │   ├── 📂 conclusoes/
│   │   ├── 📂 producao/
│   │   └── 📂 slides/
│   ├── 📂 cartorio/             # Módulo: Cartório (Análise Funil Emissões - antigo)
│   ├── 📂 cartorio_new/         # Módulo: Cartório (Análise Funil Emissões - novo)
│   ├── 📂 comune/               # Módulo: Comune (Análise Comune)
│   ├── 📂 extracoes/            # Módulo: Extrações de Dados
│   └── 📂 reclamacoes/          # Módulo: Reclamações de Clientes (se aplicável)
│
├── 📂 components/               # Componentes reutilizáveis da UI
│   ├── 📄 report_guide.py       # Guia e ajuda contextual
│   ├── 📄 search_component.py   # Componente de busca
│   ├── 📄 table_of_contents.py  # Sumário de navegação
│   └── 📄 refresh_button.py     # Botões de atualização
│
├── 📂 api/                      # Módulos de conexão com APIs (ex: Bitrix24)
├── 📂 data/                     # Dados processados ou estáticos
├── 📂 utils/                    # Funções utilitárias gerais
│
├── 📄 requirements.txt          # Dependências do projeto
├── 📄 compile_sass.py         # Script de compilação SASS
├── 📄 .gitignore                # Arquivos ignorados pelo Git
└── ... (outros arquivos e pastas de configuração)
```

## Gerenciamento Seguro de Credenciais

Este projeto utiliza o sistema de Secrets do Streamlit para gerenciar credenciais de forma segura.

### Configuração para Desenvolvimento

1. **Crie o arquivo de secrets local:**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. **Preencha as credenciais no arquivo secrets.toml:**
   - Bitrix24 API
   - Google Sheets/Drive
   - Banco de dados
   - Outras credenciais necessárias

3. **Convertendo credenciais existentes:**
   Para migrar credenciais JSON do Google para o formato do Streamlit:
   ```bash
   python utils/secrets_helper.py
   ```
   Esse utilitário ajudará você a converter o formato JSON para o formato TOML usado pelo Streamlit.

### Uso em Produção

1. **No Streamlit Cloud:**
   - Navegue até Configurações > Secrets
   - Cole o conteúdo do seu arquivo secrets.toml
   - Nunca compartilhe essas informações

2. **Em outros serviços de hospedagem:**
   - Configure variáveis de ambiente seguindo a documentação do Streamlit

### Como acessar as credenciais no código

```python
# Para acessar credenciais do Google
from utils.secrets_helper import get_google_credentials

credentials = get_google_credentials()
```

Para outras credenciais:
```python
import streamlit as st

# Credenciais do Bitrix
webhook_url = st.secrets["bitrix"]["webhook_url"]

# Credenciais do banco de dados
db_password = st.secrets["database"]["password"]
```

### Boas Práticas de Segurança

- **NUNCA comite credenciais no Git**
- Mantenha o arquivo `.streamlit/secrets.toml` no `.gitignore`
- Não armazene chaves em arquivos de código-fonte
- Rotacione credenciais regularmente
- Use chaves de serviço com permissões limitadas

## Funcionalidades Implementadas

O dashboard inclui as seguintes páginas (visualizações) e funcionalidades:

- **Páginas Principais (definidas em `main.py` e `views/`):**
    - **Apresentação:** Modo otimizado para exibição em TVs/slideshow.
        - **Cartório:** Dados específicos de cartório para apresentação.
        - **Conclusões:** Dados de conclusões para apresentação.
        - **Produção:** Dados de produção para apresentação.
    - **Cartório:** Análise detalhada do funil de emissões e processos relacionados a cartórios (versões antiga e nova).
    - **Comune:** Análise de dados relacionados a comunes, incluindo mapas e planilhas.
    - **Extrações:** Funcionalidades para exportar dados e relatórios personalizados.
    - **Reclamações:** Gestão e visualização de reclamações de clientes (se implementado).
    - *Nota: As páginas "Macro", "Produção" e "Conclusões" mencionadas anteriormente podem estar integradas dentro dos módulos acima ou na seção `apresentacao/`.*

**Funcionalidades Globais (definidas em `components/`):**
- Navegação via sidebar controlada pelo `main.py`.
- Botão de atualização global de dados (`refresh_button.py`).
- Barra de pesquisa (`search_component.py`).
- Guia contextual por página (`report_guide.py`).
- Sumário de navegação rápida (`table_of_contents.py`).
- Tema customizável (via CSS/SCSS e `.streamlit/config.toml`).

## Campos Analisados (Exemplos)

- Dependendo da visualização, podem incluir status de processos, datas, responsáveis, métricas de produtividade, dados geográficos (comune), etc.
- **Reclamações (se aplicável):** `STAGE_NAME` (Status), `DATE_CREATE`, `ASSIGNED_BY_NAME`, `UF_CRM_28_DEPARTAMENTO`, `UF_CRM_28_ORIGEM`.
- *Outros campos específicos do Bitrix24 ou das fontes de dados utilizadas.*

## Como Executar

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/velos0o/streamlit_eu_na_europa.git
    cd streamlit_eu_na_europa
    ```
2.  **Crie um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # ou
    .\venv\Scripts\activate  # Windows
    ```
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure as credenciais conforme a seção "Gerenciamento Seguro de Credenciais"**
5.  **Compile o SASS (se necessário):**
    Se houver alterações nos arquivos `.scss`, execute:
    ```bash
    python compile_sass.py
    ```
6.  **Execute a aplicação:**
    ```bash
    streamlit run main.py
    ```

## Otimização de Carregamento

- **Cache Inteligente:** Funções de carregamento de dados devem usar `@st.cache_data` ou `@st.cache_resource` para otimizar performance.
- **Atualização Manual:** O botão "Atualizar Dados" (se implementado globalmente ou por página) pode ser usado para limpar o cache e recarregar os dados.

## Design e Estilo

- Utiliza componentes nativos do Streamlit.
- Estilização customizada via arquivos SCSS compilados para CSS (`assets/styles/`).
- Possibilidade de tema claro/escuro definido em `.streamlit/config.toml`.
- Animações Lottie podem ser usadas (`assets/animations/`).

## Notas de Desenvolvimento

- Última atualização: Julho 2024
- A estrutura modular com subpastas em `views/` permite melhor organização e escalabilidade.
- O uso de `__init__.py` em cada subpasta as torna pacotes Python importáveis.

By Lucas