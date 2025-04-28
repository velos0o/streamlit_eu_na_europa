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
4.  **Compile o SASS (se necessário):**
    Se houver alterações nos arquivos `.scss`, execute:
    ```bash
    python compile_sass.py
    ```
5.  **Configure as variáveis de ambiente (se aplicável):**
    - Verifique se existe um arquivo `.env` ou `.env.example`. Se existir, renomeie para `.env` e preencha as credenciais necessárias (ex: API do Bitrix24).
      ```dotenv
      # Exemplo:
      # BITRIX_TOKEN=seu_token_bi_aqui
      # BITRIX_URL=sua_url_base_bitrix_aqui
      ```
    - Alternativamente, configure como Secrets no Streamlit Cloud se for fazer deploy lá.

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