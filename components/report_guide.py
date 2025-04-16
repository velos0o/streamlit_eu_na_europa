import streamlit as st
import pandas as pd

def show_guide_sidebar():
    """
    Exibe um guia de navegação na barra lateral do Streamlit.
    Este guia ajuda os usuários a entender quais informações estão disponíveis em cada seção.
    """
    with st.sidebar.expander("📋 Guia do Relatório", expanded=False):
        st.markdown("### Guia de Navegação")
        st.markdown("Encontre rapidamente a informação que você precisa:")
        
        st.markdown("#### 📊 Macro Higienização")
        st.markdown("- Total de processos por status")
        st.markdown("- Percentual de conclusão")
        st.markdown("- Últimas atualizações de processos")
        
        st.markdown("#### 🛠️ Produção Higienização")
        st.markdown("- Processos por responsável/atendente")
        st.markdown("- Taxa de produtividade diária/semanal")
        st.markdown("- Tempo médio de processamento")
        st.markdown("- Pendências por responsável")
        
        st.markdown("#### ✅ Conclusões Higienização")
        st.markdown("- Processos finalizados por período")
        st.markdown("- Indicadores de qualidade por processo")
        st.markdown("- Tempo médio até conclusão")
        st.markdown("- Histórico completo de conclusões")
        
        st.markdown("#### 📋 Funil Emissões Bitrix")
        st.markdown("- **Certidões entregues** (total e por período)")
        st.markdown("- Certidões emitidas aguardando entrega")
        st.markdown("- Status das emissões por etapa")
        st.markdown("- Tempo médio de emissão de documentos")
        st.markdown("- Taxa de conversão entre etapas")
        
        st.markdown("#### 👥 Comune Bitrix24")
        st.markdown("- Atividade por usuário/grupo")
        st.markdown("- Métricas de interação entre equipes")
        st.markdown("- Frequência de uso por recurso")
        st.markdown("- Participação em grupos de trabalho")
        
        st.markdown("#### 📥 Extrações")
        st.markdown("- Exportação personalizada de dados")
        st.markdown("- Relatórios prontos para download")
        st.markdown("- Consultas específicas por período/tipo")
        st.markdown("- Exportação para Excel/CSV")
        
        st.markdown("#### 🎫 Tickets")
        st.markdown("- Visão geral dos tickets de suporte")
        st.markdown("- Estatísticas por departamento")
        st.markdown("- Tempo médio de resolução")
        st.markdown("- Histórico completo de tickets")
        
        st.markdown("#### ⚠️ Reclamações")
        st.markdown("- Gestão completa de reclamações")
        st.markdown("- Estatísticas por origem e departamento")
        st.markdown("- Tendências temporais de reclamações")
        st.markdown("- Filtros avançados por status e responsável")
        st.markdown("- **Modo escuro exclusivo** para análise noturna")
        
        # Adicionando uma seção específica para buscas comuns
        st.markdown("### Buscas frequentes")
        st.markdown("👉 [Certidões entregues](#) - Ver em Cartório")
        st.markdown("👉 [Pendências de processamento](#) - Ver em Produção")
        st.markdown("👉 [Tempo médio de conclusão](#) - Ver em Conclusões")
        st.markdown("👉 [Exportar relatórios](#) - Ver em Extrações")

def show_page_guide(pagina):
    """
    Exibe um guia de ajuda contextual específico para a página atual.
    
    Args:
        pagina (str): O nome da página atual
    """
    with st.expander("ℹ️ Sobre esta página", expanded=False):
        if pagina == "Macro Higienização":
            st.markdown("""
            ### Guia da Página: Macro Higienização
            
            Esta página fornece uma visão abrangente do processo de higienização:
            
            - **Métricas Gerais**: 
              - Total de processos no sistema
              - Quantidade por status (Completo, Incompleto, Pendente)
              - Percentual de progresso geral
            
            - **Últimas Conclusões**: 
              - Lista dos processos recentemente concluídos
              - Responsável de cada processo
              - Data/hora da conclusão
            
            **Como usar**: Utilize estas informações para ter uma visão rápida da situação atual e identificar os processos recentemente finalizados.
            
            **Dica**: Use o botão "Atualizar Dados" para obter os dados mais recentes do Bitrix24.
            """)
            
        elif pagina == "Produção Higienização":
            st.markdown("""
            ### Guia da Página: Produção Higienização
            
            Acompanhe detalhadamente a produtividade da equipe de higienização:
            
            - **Métricas por Responsável**: 
              - Quantidade de processos por atendente
              - Carga de trabalho atual
              - Proporção entre processos completos e pendentes
              
            - **Gráficos de Produção**: 
              - Evolução diária/semanal da produtividade
              - Comparativo entre responsáveis
              - Tendências de processamento ao longo do tempo
              
            - **Pendências**: 
              - Lista de processos pendentes por prioridade
              - Tempo em espera de cada processo
              - Responsáveis por pendências
            
            **Como usar**: Utilize os filtros de data e responsável para focar em períodos específicos ou membros da equipe.
            
            **Dica**: Observe as tendências temporais para identificar padrões de produtividade.
            """)
            
        elif pagina == "Conclusões Higienização":
            st.markdown("""
            ### Guia da Página: Conclusões Higienização
            
            Analise em profundidade os processos finalizados:
            
            - **Métricas de Conclusão**: 
              - Total de processos concluídos por período
              - Média diária/semanal/mensal de conclusões
              - Distribuição por tipo de conclusão
              
            - **Análise de Qualidade**: 
              - Indicadores de qualidade por processo
              - Identificação de erros comuns
              - Avaliação de conformidade
              
            - **Tendências de Conclusão**: 
              - Evolução temporal das conclusões
              - Comparativo com períodos anteriores
              - Previsão de conclusões futuras
            
            **Como usar**: Compare diferentes períodos para identificar melhorias no processo de higienização.
            
            **Dica**: Observe os padrões de qualidade para identificar oportunidades de treinamento da equipe.
            """)
            
        elif pagina == "Cartório":
            st.markdown("""
            ### Guia da Página: Funil Emissões Bitrix
            
            Acompanhe o pipeline completo de emissões de documentos:
            
            - **Certidões Entregues**: 
              - 📊 Total de certidões entregues no período
              - 📈 Evolução de entregas diárias/semanais
              - 📑 Lista detalhada de certidões entregues com data
              - 👤 Classificação por destinatário/cliente
            
            - **Visão do Funil**: 
              - Quantidade de processos em cada etapa
              - Certidões emitidas vs. entregues 
              - Status atual de cada documento
              
            - **Conversão Entre Etapas**: 
              - Taxa de aprovação entre etapas
              - Tempo médio em cada estágio
              - Identificação de gargalos no processo
              
            - **Detalhes de Emissão**: 
              - Tempo médio de emissão por tipo de documento
              - Taxa de rejeição/aprovação
              - Documentos pendentes de entrega
            
            **Como encontrar certidões entregues**: Use a tabela na seção "Certidões Entregues" ou aplique o filtro de status "Entregue" na seção "Visão do Funil".
            
            **Dica**: Para uma análise detalhada de entregas, exporte os dados usando o botão "Exportar Certidões Entregues" no topo da seção.
            """)
            
        elif pagina == "Comune":
            st.markdown("""
            ### Guia da Página: Comune Bitrix24
            
            Analise as interações e colaboração entre usuários no Bitrix24:
            
            - **Análise de Comunidades**: 
              - Grupos mais ativos
              - Distribuição de usuários por comunidade
              - Tópicos mais discutidos
              
            - **Métricas de Interação**: 
              - Frequência de comunicação
              - Volume de mensagens por usuário/grupo
              - Horários de maior atividade
              
            - **Engajamento dos Usuários**: 
              - Usuários mais ativos
              - Tempo médio de resposta
              - Índice de participação por departamento
            
            **Como usar**: Identifique padrões de comunicação e colaboração para melhorar a integração da equipe.
            
            **Dica**: Analise quais comunidades têm maior engajamento para replicar práticas bem-sucedidas.
            """)
            
        elif pagina == "Extrações de Dados":
            st.markdown("""
            ### Guia da Página: Extrações
            
            Acesse e exporte dados específicos do sistema:
            
            - **Extração Personalizada**: 
              - Filtros avançados por múltiplos critérios
              - Seleção de campos específicos para exportação
              - Personalização do formato de saída
              
            - **Relatórios Prontos**: 
              - Modelos pré-configurados de relatórios comuns
              - Exportações rápidas com um clique
              - Relatórios periódicos (diários/semanais)
              
            - **Opções de Exportação**: 
              - Formatos disponíveis (Excel, CSV, PDF)
              - Agendamento de exportações automáticas
              - Compartilhamento direto via email
            
            **Como usar**: Defina claramente os filtros antes de exportar para obter exatamente os dados necessários.
            
            **Dica**: Utilize os modelos de relatório para análises recorrentes, economizando tempo de configuração.
            """)
            
        elif pagina == "Tickets":
            st.markdown("""
            ### Guia da Página: Tickets de Suporte
            
            Acompanhe e analise os tickets de suporte:
            
            - **Visão Geral**: 
              - Total de tickets abertos e fechados
              - Distribuição por tipo e prioridade
              - Taxa de resolução e tempo médio
              
            - **Análise Temporal**: 
              - Evolução de tickets ao longo do tempo
              - Comparativo entre períodos
              - Identificação de picos de demanda
              
            - **Detalhamento**: 
              - Lista completa de tickets com filtros
              - Informações detalhadas por ticket
              - Histórico de interações
            
            **Como usar**: Utilize os filtros para focar em períodos específicos ou tipos de tickets.
            
            **Dica**: Compare diferentes períodos para identificar padrões e tendências na demanda de suporte.
            """)

        elif pagina == "Reclamações":
            st.markdown("""
            ### Guia da Página: Gestão de Reclamações
            
            Monitore e analise as reclamações de clientes com interface adaptativa:
            
            - **Visão Geral**: 
              - Total de reclamações recebidas
              - Distribuição por status (Novas, Em análise, Respondidas, etc.)
              - Taxa de resolução e estatísticas gerais
              
            - **Análises Visuais**: 
              - Gráficos de distribuição por origem e departamento
              - Tendências temporais de reclamações
              - Comparativo por responsável
              
            - **Detalhamento e Filtros**: 
              - Filtros avançados por status, departamento e origem
              - Lista detalhada com informações completas
              - Visualização individual de cada reclamação
            
            - **Modo Escuro**: 
              - Interface adaptativa com modo escuro exclusivo
              - Ideal para análise noturna e redução de fadiga visual
              - Ative com o botão de alternância no topo da página
            
            **Como usar**: Alterne entre os modos claro e escuro usando o botão no topo da página. Utilize os filtros para análises específicas por departamento ou status.
            
            **Dica**: Observe as tendências temporais para identificar padrões e picos de reclamações que possam indicar problemas sistemáticos.
            """)
            
        elif pagina == "Apresentação Conclusões":
            st.markdown("""
            ### Guia da Página: Apresentação em TV
            
            Modo otimizado para apresentações em monitores e TVs:
            
            - **Visualização Automática**: 
              - Rotação automática entre slides/painéis
              - Tempo ajustável entre transições
              - Ciclo contínuo de informações
              
            - **Layout Otimizado**: 
              - Formatação especial para visibilidade à distância
              - Destaque para métricas principais
              - Gráficos simplificados para melhor leitura
              
            - **Conteúdo Focado**: 
              - Resumo das informações mais relevantes
              - Atualização em tempo real dos dados
              - Indicadores de desempenho principais (KPIs)
            
            **Como usar**: Configure a apresentação na tela desejada e deixe em modo automático para reuniões ou monitores de equipe.
            
            **Dica**: Para controlar manualmente a apresentação, use as setas de navegação no canto inferior.
            """)

def show_contextual_help(section=None):
    """
    Exibe ajuda contextual para uma seção específica do relatório.
    
    Args:
        section (str, optional): A seção específica. Se None, mostra ajuda geral.
    """
    if section is None:
        st.info("""
        👋 **Precisa de ajuda?**
        
        Este dashboard contém diversas métricas organizadas por seção.
        
        Para encontrar informações específicas:
        1. Use a barra de pesquisa com termos específicos (ex: "certidões entregues", "tempo médio")
        2. Navegue pelo menu lateral para a seção apropriada
        3. Utilize o guia detalhado disponível em cada página
        
        Se não encontrar o que procura, tente termos alternativos na busca.
        """)
    elif section == "filtros":
        st.info("""
        🔍 **Usando Filtros**
        
        Os filtros permitem análises personalizadas:
        
        - **Filtros de Data**: 
          - Defina períodos específicos (dia, semana, mês)
          - Compare períodos diferentes
          - Analise tendências temporais
          
        - **Filtros de Responsável**:
          - Foque em membros específicos da equipe
          - Compare desempenho entre responsáveis
          - Analise distribuição de trabalho
          
        - **Filtros de Status**:
          - Concentre-se em processos completos, pendentes ou em andamento
          - Identifique gargalos por status
          - Analise tempos por etapa do processo
        
        As alterações nos filtros se aplicam a todos os gráficos e tabelas da página atual.
        """)
    elif section == "exportacao":
        st.info("""
        📤 **Exportando Dados**
        
        Para exportar dados para análise externa:
        
        1. Configure os filtros desejados para limitar os dados
        2. Procure pelos ícones de download nos gráficos e tabelas
        3. Ou acesse a seção "Extrações" para exportações mais completas
        
        **Formatos disponíveis**:
        - CSV: para importação em ferramentas de análise
        - Excel: para análises e relatórios detalhados
        - PDF: para documentação e apresentações
        
        **Dica**: Para relatórios regulares, crie e salve suas configurações de filtro na seção Extrações.
        """)
    elif section == "certidoes":
        st.info("""
        📑 **Encontrando Certidões Entregues**
        
        Para localizar informações sobre certidões entregues:
        
        1. **Método Rápido**: Na barra de pesquisa, digite "certidões entregues"
        
        2. **Navegação Manual**:
           - Acesse a seção "📋 Funil Emissões Bitrix" no menu lateral
           - Na seção "Certidões Entregues", você encontrará:
              * Total de certidões entregues no período selecionado
              * Lista detalhada com datas de entrega
              * Gráficos de evolução das entregas
        
        3. **Via Extrações**:
           - Acesse a seção "📥 Extrações"
           - Selecione o modelo "Relatório de Certidões Entregues"
           - Aplique os filtros de período desejados
           - Exporte os dados em Excel ou CSV
        
        **Dica**: Para análises recorrentes, salve os filtros ou favorite o relatório.
        """) 