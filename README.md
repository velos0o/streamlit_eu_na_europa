# Dashboard Analítico - CRM Bitrix24

## Sobre o Projeto

Dashboard desenvolvido em Streamlit para análise de dados do CRM Bitrix24, com foco na visualização e análise do status de higienização de processos, tickets de suporte e reclamações de clientes.

## Estrutura do Projeto

```
dash_higilizacao/ # Nome da pasta raiz (pode variar)
├── main.py                    # Arquivo principal da aplicação
├── requirements.txt           # Dependências do projeto
├── .env.example               # Exemplo de arquivo para variáveis de ambiente
├── .streamlit/                # Configurações do Streamlit
│   └── config.toml            # Arquivo de configuração do tema e opções
├── assets/                    # Recursos estáticos (CSS, imagens, logos)
│   ├── styles.css             # Estilos CSS globais (se houver)
│   └── LOGO-*.svg             # Arquivos de logo
├── api/                       # Módulos de conexão com APIs
│   └── bitrix_connector.py    # Conector para a API do Bitrix24 (BI e REST)
│   └── __init__.py
├── components/                # Componentes reutilizáveis da UI
│   ├── report_guide.py       # Guia/ajuda contextual
│   ├── search_component.py   # Componente de busca global
│   ├── table_of_contents.py  # Sumário de navegação (TOC)
│   ├── refresh_button.py     # Botão de atualização global
│   └── __init__.py
├── views/                     # Módulos representando cada página/seção
│   ├── inicio.py              # Página: Macro Higienização
│   ├── producao.py            # Página: Produção Higienização
│   ├── conclusoes.py          # Página: Conclusões Higienização
│   ├── apresentacao.py       # Página: Apresentação modo TV
│   ├── tickets.py             # Página: Tickets de Suporte
│   ├── cartorio/              # Módulo: Funil Emissões Bitrix
│   │   ├── cartorio_main.py  # -> Página Principal
│   │   └── __init__.py
│   ├── comune/                # Módulo: Comune Bitrix24
│   │   ├── comune_main.py    # -> Página Principal
│   │   └── __init__.py
│   ├── extracoes/             # Módulo: Extrações de Dados
│   │   ├── extracoes_main.py # -> Página Principal
│   │   └── __init__.py
│   ├── reclamacoes/           # Módulo: Reclamações de Clientes
│   │   ├── reclamacoes_main.py # -> Página Principal
│   │   ├── data_loader.py    # -> Lógica de carregamento de dados
│   │   ├── styles.py         # -> Estilos específicos da página
│   │   ├── metrics_cards.py  # -> Componentes de cards de métricas
│   │   ├── charts.py         # -> Componentes de gráficos
│   │   ├── details.py        # -> Seção de detalhes e filtros
│   │   └── __init__.py
│   └── __init__.py
└── utils/                     # Funções utilitárias gerais
    ├── data_processor.py      # Funções genéricas de processamento de dados
    ├── animation_utils.py     # Utilitários para animações (Lottie)
    ├── refresh_utils.py       # Utilitários para controle de refresh global
    └── __init__.py
```

## Funcionalidades Implementadas

O dashboard inclui as seguintes páginas e funcionalidades:

- **Higienização:**
    - **Macro:** Visão geral do status de higienização.
    - **Produção:** Métricas detalhadas, tabelas por responsável, pendências.
    - **Conclusões:** Métricas de conclusão e qualidade.
- **Funil Emissões (Cartório):** Análise do funil de emissões de documentos.
- **Comune:** Análise de dados relacionados a comunes.
- **Extrações:** Funcionalidades para exportar dados.
- **Tickets:** Análise de tickets de suporte (status, tempo, etc.).
- **Reclamações:** Gestão e visualização de reclamações de clientes (status, origem, tendência).
- **Apresentação:** Modo otimizado para exibição em TVs.

**Funcionalidades Globais:**
- Navegação via sidebar.
- Botão de atualização global de dados.
- Barra de pesquisa.
- Guia contextual por página.
- Sumário de navegação rápida (TOC) em páginas selecionadas.
- Tema claro/escuro customizável.
- Modo de depuração para desenvolvedores.

## Campos Analisados (Exemplos)

- **Higienização:** `UF_CRM_HIGILIZACAO_STATUS`, `UF_CRM_1741183785848`, `UF_CRM_1741183721969`, etc.
- **Reclamações:** `STAGE_NAME` (Status), `DATE_CREATE`, `ASSIGNED_BY_NAME`, `UF_CRM_28_DEPARTAMENTO`, `UF_CRM_28_ORIGEM`.
- **Tickets:** Campos relacionados a status, prioridade, tempo de resposta, etc. (conforme entidade no Bitrix).

## Como Executar

1.  **Clone o repositório:**
    ```bash
    git clone <url_do_repositorio>
    cd <nome_da_pasta>
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
4.  **Configure as variáveis de ambiente:**
    - Renomeie `.env.example` para `.env`.
    - Preencha as variáveis no arquivo `.env` com suas credenciais do Bitrix24:
      ```dotenv
      BITRIX_TOKEN=seu_token_bi_aqui
      BITRIX_URL=sua_url_base_bitrix_aqui # Ex: https://seu_dominio.bitrix24.com
      # BITRIX_REST_TOKEN=seu_token_rest_webhook_aqui (Opcional, se usado)
      # BITRIX_REST_URL=sua_url_rest_webhook_aqui (Opcional, se usado)
      ```
    - Alternativamente, configure como Secrets no Streamlit Cloud.

5.  **Execute a aplicação:**
    ```bash
    streamlit run main.py
    ```

## Otimização de Carregamento

- **Cache Inteligente:** Funções de carregamento de dados usam `@st.cache_data` para evitar recargas desnecessárias.
- **Modo de Demonstração:** Algumas páginas podem oferecer um modo de demonstração com dados simulados para testes rápidos ou offline.
- **Atualização Manual:** O botão "Atualizar Dados" limpa o cache e força a recarga dos dados da API.

## Design e Estilo

- Utiliza componentes nativos do Streamlit combinados com CSS personalizado inspirado no Tailwind CSS.
- Tema claro e escuro com cores definidas.
- Estilos globais e específicos por módulo para consistência.
- Animações sutis para melhorar a experiência do usuário.

## Notas de Desenvolvimento

- Última atualização: Agosto 2024
- A estrutura modular com subpastas em `views/` permite melhor organização e escalabilidade.
- O uso de `__init__.py` em cada subpasta as torna pacotes Python importáveis.

By Lucas