# Módulo Ficha da Família

## 📋 Visão Geral

Este módulo foi refatorado de um único arquivo de 3000+ linhas para uma estrutura modular e escalável. Ele fornece uma interface completa para visualizar e gerar relatórios detalhados de famílias no sistema.

## 🏗️ Estrutura do Módulo

```
views/ficha_familia/
├── __init__.py                  # Exporta função principal
├── ficha_familia_main.py        # Arquivo principal - busca e orquestração
├── ficha_exibicao.py           # Exibição completa da ficha HTML
├── data_loader.py              # Carregamento de dados do CRM
├── pdf_generator.py            # Geração de PDFs
├── display_components.py       # Componentes visuais (alertas, CSS, etc)
├── business_logic.py           # Lógica de negócio (categorização, precedência)
├── emissoes_processor.py       # Processamento de emissões brasileiras
├── metrics.py                  # Métricas macro e estatísticas
├── utils.py                    # Funções auxiliares
└── README.md                   # Esta documentação
```

## 📦 Responsabilidades dos Módulos

### `ficha_familia_main.py`
- **Função principal**: `show_ficha_familia()`
- Responsável pela interface de busca
- Orquestra a exibição dos componentes
- Gerencia estado da sessão

### `ficha_exibicao.py`
- **Função principal**: `exibir_ficha_familia(familia_serie, emissoes_df)`
- Renderiza o HTML completo da ficha
- Coordena alertas visuais
- Gerencia seções (dados básicos, emissões, resumo)
- Preparação dos dados para PDF
- **Nova funcionalidade**: `_gerar_csv_status_simplificado()` - Exporta tabela simplificada de status em CSV

### `data_loader.py`
- **Função principal**: `load_crm_deal_data(category_id)`
- Carrega dados do CRM via Bitrix API
- Validação de colunas essenciais
- Tratamento de erros de carregamento

### `pdf_generator.py`
- **Função principal**: `gerar_pdf_ficha(contexto_pdf)`
- Gera PDF completo da ficha
- Funções auxiliares de formatação
- Carregamento e conversão de logos

### `display_components.py`
- **`inject_all_ficha_css()`** - 🎨 **PRINCIPAL:** Injeta TODO o CSS necessário
- Componentes visuais reutilizáveis:
  - `render_alert_box()` - Alertas flutuantes
  - `render_mapa_inicial_notification()` - Notificação especial
- Configurações de canais especiais
- **IMPORTANTE:** CSS é injetado UMA VEZ no início via `inject_all_ficha_css()`

### `business_logic.py`
- **Funções principais**:
  - `determinar_categoria_por_pipeline_status()` - Categorização de emissões
  - `aplicar_precedencia_pipelines()` - Lógica de precedência Pipeline 104
  - `normalizar_id_requerente()` - Normalização de IDs
  - `ordenar_requerentes_por_posicao()` - Ordenação por hierarquia
- Mapeamento de pipelines (92, 94, 102, 104)

### `emissoes_processor.py`
- **Função principal**: `processar_emissoes(emissoes_df, familia_serie)`
- Processa dados de emissões brasileiras
- Agrupa por requerente
- Aplica lógica de precedência
- Calcula resumo por categorias

### `metrics.py`
- **Função principal**: `exibir_metricas_macro(df_crm_deals, df_spa_base)`
- Métricas gerais de famílias
- Status de protocolo
- Acompanhamento de emissões
- Tabelas de progresso

### `utils.py`
- Funções auxiliares diversas:
  - `obter_url_card()` - Construção de URLs Bitrix
  - `construir_link_card_pipeline()` - Links específicos por pipeline
  - `montar_nome_arquivo_pdf()` - Nome de arquivos PDF
  - `_slugify()` - Conversão de texto para slug
- Constantes e configurações (URLs, paths)

## 🚀 Uso

### Importação Básica
```python
from views.ficha_familia import show_ficha_familia

# Exibir página completa
show_ficha_familia()
```

### Uso Individual de Componentes
```python
from views.ficha_familia.data_loader import load_crm_deal_data
from views.ficha_familia.pdf_generator import gerar_pdf_ficha

# Carregar dados
df_familias = load_crm_deal_data(category_id=46)

# Gerar PDF
contexto = {...}  # Preparar contexto
pdf_bytes = gerar_pdf_ficha(contexto)
```

## 🔧 Manutenção

### Adicionar Nova Funcionalidade

1. **Nova lógica de negócio** → `business_logic.py`
2. **Novo componente visual** → `display_components.py`
3. **Nova fonte de dados** → `data_loader.py`
4. **Nova métrica** → `metrics.py`
5. **Novo processamento** → `emissoes_processor.py`

### Modificar Exibição

- Layout e estrutura HTML → `ficha_exibicao.py`
- Estilos CSS → `display_components.py`
- Formato PDF → `pdf_generator.py`

## 📊 Fluxo de Dados

```
main.py
  └─> show_ficha_familia()                [ficha_familia_main.py]
        ├─> load_crm_deal_data()          [data_loader.py]
        ├─> Busca e Filtros                [ficha_familia_main.py]
        └─> exibir_ficha_familia()         [ficha_exibicao.py]
              ├─> _exibir_alertas()
              ├─> _extrair_dados_familia()
              ├─> processar_emissoes()     [emissoes_processor.py]
              │     ├─> simplificar_nome_estagio()
              │     ├─> aplicar_precedencia_pipelines()
              │     └─> calcular_resumo_emissoes()
              ├─> _carregar_documentos_spa()
              ├─> _construir_html_ficha()
              ├─> _preparar_dados_pdf()
              ├─> gerar_pdf_ficha()        [pdf_generator.py]
              └─> _exibir_documentos_spa()
```

## 🐛 Troubleshooting

### Erro de Importação
- Verificar se `__init__.py` existe e exporta as funções necessárias
- Confirmar que todos os módulos estão na pasta `views/ficha_familia/`

### Dados Não Carregam
- Verificar logs no console: `[DEBUG]` e `[ERRO]`
- Confirmar conexão com Bitrix API
- Validar `category_id` correto

### PDF Não Gera
- Verificar instalação de `reportlab` e `cairosvg`
- Confirmar que arquivos de logo existem em `/assets`
- Ver mensagem de erro detalhada

## ✨ Funcionalidades

### 📄 Download de PDF Completo
- Ficha completa formatada para impressão
- Logo da empresa incluída
- Otimizado para papel A4
- Design minimalista e profissional

### 📊 Download de Tabela Status (CSV)
- **Novo recurso!** Exporta planilha simplificada
- Status claros e diretos (Emitida ✓, Solicitada, Pendência, etc.)
- Tabela por requerente (Nascimento, Casamento, Óbito)
- Resumo geral de quantidades
- Compatível com Excel, Google Sheets e qualquer planilha
- Arquivo: `Status_Certidoes_[ID].csv`

Ver detalhes completos em: [TABELA_STATUS_SIMPLIFICADA.md](./TABELA_STATUS_SIMPLIFICADA.md)

### 🔍 Busca Inteligente
- Busca por nome da família
- Busca por ID da família
- Filtro por status
- Navegação rápida

### 📋 Dados Consolidados
- Informações da família
- Requerentes e certidões
- Status de emissões brasileiras
- Documentos da SPA
- Procurações e observações

## 🔄 Changelog

### Versão 2.2 (Tabela Status Simplificada)
- ✅ **Novo botão** "📊 Baixar Tabela Status (CSV)"
- ✅ **Status simplificados** em 7 categorias principais
- ✅ **Formato CSV** compatível com Excel/Sheets
- ✅ **Resumo automático** de quantidades
- ✅ Documentação completa

### Versão 2.1 (Correção CSS)
- ✅ **CSS centralizado** via `inject_all_ficha_css()`
- ✅ Carregamento 100% confiável
- ✅ Remoção de verificações condicionais de `st.session_state`
- ✅ Injeção única no início da página
- ✅ Problema de "CSS não carrega às vezes" **RESOLVIDO**

### Versão 2.0 (Refatoração)
- ✅ Modularização completa de 3000+ linhas
- ✅ Separação de responsabilidades
- ✅ Documentação inline
- ✅ Estrutura escalável
- ✅ Facilidade de manutenção

### Versão 1.0 (Original)
- Arquivo único `ficha_familia.py`
- 3047 linhas
- Todas funcionalidades em um arquivo

## 📝 Notas Técnicas

### Pipelines Suportados
- **92**: Cartório Casa Verde
- **94**: Cartório Tatuapé
- **102**: Paróquia
- **104**: Pesquisa BR

### Lógica de Precedência Pipeline 104
Quando uma pessoa tem "PESQUISA PRONTA PARA EMISSÃO" no pipeline 104 E também possui registros nos pipelines superiores (92, 94, 102), o sistema mostra apenas o status dos pipelines superiores, pois após a pesquisa estar pronta, o card é duplicado para os outros pipelines onde o processo continua.

### Métrica Derivada "Pasta C/Emissão Concluída"
Calculada quando TODAS as certidões ativas de uma família estão no status "Brasileiras Emitida". Baseada na mesma lógica do `higienizacao_desempenho.py`.

## 👥 Contato

Para dúvidas ou sugestões sobre este módulo, consulte a documentação do projeto principal ou o time de desenvolvimento.


