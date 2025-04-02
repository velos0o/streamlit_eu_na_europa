# Dashboard Analítico - CRM Bitrix24

## Sobre o Projeto

Dashboard desenvolvido em Streamlit para análise de dados do CRM Bitrix24, com foco na visualização e análise do status de higienização de processos.

## Estrutura do Projeto

```
dash_higilizacao/
├── main.py                    # Arquivo principal da aplicação
├── install_lottie.py          # Utilitário para instalar biblioteca de animações
├── .streamlit/                # Configurações do Streamlit
│   └── config.toml            # Arquivo de configuração do tema
├── assets/                    # Recursos estáticos (CSS, imagens)
│   └── styles.css             # Estilos CSS centralizados
├── api/                       # Módulos de conexão com APIs
│   └── bitrix_connector.py    # Conector para a API do Bitrix24
├── components/                # Componentes reutilizáveis
│   ├── filters.py             # Componentes de filtros
│   ├── metrics.py             # Componentes de métricas
│   └── tables.py              # Componentes de tabelas
├── views/                     # Visualizações da aplicação
│   ├── inicio.py              # Página inicial
│   ├── producao.py            # Página de produção
│   ├── conclusoes.py          # Página de conclusões
│   ├── cartorio/              # Seção de cartório
│   │   └── cartorio_main.py   # Página principal de cartório
│   └── extracoes/             # Seção de extrações
│       └── extracoes_main.py  # Página principal de extrações
└── utils/                     # Funções utilitárias
    ├── data_processor.py      # Processador de dados
    └── animation_utils.py     # Utilitários para animações
```

## Funcionalidades Implementadas

### Página de Produção
- Métricas macro com contagens por status de higienização
- Tabela de status por responsável
- Tabela de pendências detalhada
- Tabela de produção geral
- Filtros por data, responsável e status
- Animações de carregamento e barras de progresso
- Filtro por IDs específicos para consultas otimizadas

## Campos Analisados

Os principais campos utilizados para análise de higienização:

- `UF_CRM_HIGILIZACAO_STATUS`: Status geral de higienização (PENDENCIA, INCOMPLETO, COMPLETO)
- `UF_CRM_1741183785848`: Documentação Pend/Infos (sim/não)
- `UF_CRM_1741183721969`: Cadastro na Árvore Higielizado (sim/não)
- `UF_CRM_1741183685327`: Estrutura Árvore Higieniza (sim/não)
- `UF_CRM_1741183828129`: Requerimento (sim/não)
- `UF_CRM_1741198696`: Emissões Brasileiras Bitrix24 (sim/não)

## Como Executar

1. Instale as dependências necessárias:
```
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
   ```
   BITRIX_TOKEN=seu_token_aqui
   BITRIX_URL=sua_url_aqui
   BITRIX_REST_TOKEN=seu_token_rest_aqui
   BITRIX_REST_URL=sua_url_rest_aqui
   ```
   - Ou configure as mesmas variáveis nos Secrets do Streamlit Cloud:
     1. Acesse o dashboard do Streamlit Cloud
     2. Selecione seu aplicativo
     3. Vá em Settings > Secrets
     4. Adicione as mesmas variáveis no formato TOML:
     ```toml
     BITRIX_TOKEN = "seu_token_aqui"
     BITRIX_URL = "sua_url_aqui"
     BITRIX_REST_TOKEN = "seu_token_rest_aqui"
     BITRIX_REST_URL = "sua_url_rest_aqui"
     ```

3. (Opcional) Instale a biblioteca para animações de carregamento:
```
python install_lottie.py
```
Ou manualmente:
```
pip install streamlit-lottie==0.0.5
```

4. Execute a aplicação:
```
streamlit run main.py
```

## Otimização de Carregamento

O dashboard oferece várias formas de otimizar o carregamento de dados:

1. **Filtro por IDs específicos**: 
   - Nas "Opções Avançadas" da página de produção, ative "Filtrar por IDs específicos"
   - Insira os IDs desejados separados por vírgula
   - Isso reduz substancialmente o tempo de carregamento

2. **Modo de Demonstração**: 
   - Ative o "Modo de demonstração" para usar dados sintéticos 
   - Útil para testes ou quando a API estiver indisponível

3. **Cache de Sessão**:
   - Os dados são armazenados em cache para navegação rápida entre páginas
   - Use o botão "Atualizar Dados" para recarregar quando necessário

## Animações de Carregamento

O dashboard inclui animações profissionais durante o carregamento de dados:

- Barra de progresso mostrando o andamento real do processamento
- Animações Lottie para feedback visual (requer biblioteca adicional)
- Mensagens de status atualizadas durante o processo

Para habilitar as animações avançadas, execute `python install_lottie.py` ou instale manualmente a biblioteca streamlit-lottie.

## Design

O dashboard segue um design minimalista com esquema de cores em azul e branco, com:
- Interface limpa e profissional
- Estilo consistente em todos os componentes
- Opção para tema escuro
- Todo CSS centralizado para padronização

## Próximas Etapas

- Implementação das páginas de conclusões
- Implementação das páginas de cartório
- Implementação das páginas de extrações
- Refinamento de layouts e visualizações
- Adição de funcionalidades de exportação de dados

## Notas de Desenvolvimento

Última atualização: Agosto 2024

**Observação sobre estrutura:** A pasta `views` foi adotada em vez de `pages` para evitar a criação automática de menu pelo Streamlit, que gera navegação duplicada. 

By Lucas