# Módulo de Apresentação - Dashboard Higilização

Este módulo implementa uma apresentação tipo carrossel para ser exibida em monitores verticais (formato 9:16), como TVs em corredores ou recepções. O sistema permite visualizar métricas, gráficos e estatísticas de três áreas principais:

1. **Conclusões** - Métricas e análises sobre processos concluídos
2. **Produção** - Status e acompanhamento da produção
3. **Cartório** - Análise de documentos e certidões de cartório

## Melhorias Recentes

### Design
- Interface totalmente redesenhada com gradientes modernos
- Cards com efeitos visuais e animações de transição
- Indicadores de navegação e controles flutuantes
- Barra de progresso animada entre slides
- Design responsivo otimizado para telas verticais

### Funcionalidade
- Carregamento otimizado de dados para evitar falhas
- Sistema de fallback para dados de demonstração quando necessário
- Navegação aprimorada entre slides e módulos
- Indicação visual clara da posição atual no carrossel
- Transições suaves entre slides

### Performance
- Código otimizado para carregar apenas os dados necessários
- Melhor gerenciamento de memória e recursos
- Tratamento de erros robusto para garantir funcionamento contínuo
- Cache de dados para evitar requisições desnecessárias à API

## Como Usar

### Modo de Apresentação Automática
Para iniciar a apresentação automática em modo carrossel:

1. Execute a página principal `main.py`
2. Adicione o parâmetro `?slide=N` na URL para iniciar em um slide específico (0-11)
   - Exemplo: `http://localhost:8501/?slide=0` para iniciar nas métricas de destaque

### Parâmetros de URL

- `?slide=N` - Inicia a apresentação no slide N (0-11)
- `?config=1` - Ativa o modo de configuração
- `?tempo=X` - Define o tempo de exibição por slide em segundos (padrão: 15)

### Navegação durante Apresentação

Durante a apresentação, você pode:

- Usar os botões de navegação flutuantes para pular para diferentes módulos
- Clicar nos indicadores de slides na parte inferior para navegar diretamente
- Pressionar ESC para sair da apresentação
- Clicar no botão ⚙️ para acessar o modo de configuração

### Modo de Configuração

No modo de configuração, você pode:

- Ajustar o tempo de exibição por slide
- Selecionar quais módulos exibir
- Definir o período de análise dos dados
- Recarregar os dados manualmente
- Testar a visualização de slides específicos

## Estrutura do Código

```
views/apresentacao/
├── __init__.py               # Inicialização do módulo
├── apresentacao.py           # Página principal
├── apresentacao_conclusoes.py# Lógica do carrossel e slides 
├── funcoes_slides.py         # Funções auxiliares para slides
├── styles.py                 # Estilos CSS para apresentação
└── data_loader.py            # Funções para carregar dados
```

## Slides Disponíveis

1. **Conclusões**
   - Métricas de Destaque
   - Ranking de Produtividade
   - Análise Diária
   - Análise Semanal
   - Análise por Dia da Semana
   - Análise por Hora

2. **Produção**
   - Métricas Macro
   - Status por Responsável
   - Pendências por Responsável

3. **Cartório**
   - Visão Geral
   - Análise de Famílias
   - IDs de Família

## Desenvolvimento e Customização

Para desenvolver novos slides ou customizar os existentes:

1. Adicione a função do slide em `apresentacao_conclusoes.py`
2. Registre o novo slide na lista `nomes_slides` dentro da função `iniciar_carrossel_metricas`
3. Adicione o caso correspondente no switch dentro do loop principal

## Requisitos

- Streamlit 1.22+
- Plotly 5.14+
- Pandas 1.5+
- Python 3.9+ 