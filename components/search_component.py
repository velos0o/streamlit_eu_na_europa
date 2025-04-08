import streamlit as st
import re
import os

# Dicionário com termos de busca e seus destinos
SEARCH_INDEX = {
    # Termos para Macro Higienização
    "dashboard": "Macro Higienização",
    "visão geral": "Macro Higienização",
    "resumo": "Macro Higienização",
    "métricas gerais": "Macro Higienização",
    "status atual": "Macro Higienização",
    "última atualização": "Macro Higienização",
    "processos pendentes": "Macro Higienização",
    "processos em andamento": "Macro Higienização",
    "total de processos": "Macro Higienização",
    "status geral": "Macro Higienização",
    "overview": "Macro Higienização",
    "processos completos": "Macro Higienização",
    "situação atual": "Macro Higienização",
    "higienização geral": "Macro Higienização",
    "panorama geral": "Macro Higienização",
    "visão macro": "Macro Higienização",
    "dashboard principal": "Macro Higienização",
    
    # Termos para Produção Higienização
    "produção": "Produção Higienização",
    "produtividade": "Produção Higienização",
    "responsáveis": "Produção Higienização",
    "equipe": "Produção Higienização",
    "distribuição": "Produção Higienização",
    "tendências": "Produção Higienização",
    "gráficos": "Produção Higienização",
    "pendências": "Produção Higienização",
    "produtividade por pessoa": "Produção Higienização",
    "ranking de produção": "Produção Higienização",
    "processos atribuídos": "Produção Higienização",
    "atribuições": "Produção Higienização",
    "desempenho da equipe": "Produção Higienização",
    "evolução da produção": "Produção Higienização",
    "tempo médio por processo": "Produção Higienização",
    "processos por responsável": "Produção Higienização",
    "atrasos": "Produção Higienização",
    "status por responsável": "Produção Higienização",
    "volume de produção": "Produção Higienização",
    "eficiência operacional": "Produção Higienização",
    "métricas de produção": "Produção Higienização",
    "indicadores de produtividade": "Produção Higienização",
    "desempenho por colaborador": "Produção Higienização",
    
    # Termos para Conclusões Higienização
    "conclusões": "Conclusões Higienização",
    "finalizados": "Conclusões Higienização",
    "completados": "Conclusões Higienização",
    "qualidade": "Conclusões Higienização",
    "tempo médio": "Conclusões Higienização",
    "eficiência": "Conclusões Higienização",
    "processos concluídos": "Conclusões Higienização",
    "taxa de conclusão": "Conclusões Higienização",
    "histórico de conclusões": "Conclusões Higienização",
    "análise de qualidade": "Conclusões Higienização",
    "tempo de processamento": "Conclusões Higienização",
    "avaliação dos processos": "Conclusões Higienização",
    "finalizações por período": "Conclusões Higienização",
    "problemas identificados": "Conclusões Higienização",
    "métricas de qualidade": "Conclusões Higienização",
    "processos encerrados": "Conclusões Higienização",
    "detalhes de conclusão": "Conclusões Higienização",
    "análise de conclusões": "Conclusões Higienização",
    "métricas finais": "Conclusões Higienização",
    "resultados do processo": "Conclusões Higienização",
    
    # Termos gerais para Cartório
    "cartório": "Cartório",
    "funil": "Cartório",
    "emissões": "Cartório",
    "pipeline": "Cartório",
    "conversão": "Cartório",
    "estágios": "Cartório",
    "gargalos": "Cartório",
    "certidões": "Cartório", 
    "certidões entregues": "Cartório",
    "entrega de certidões": "Cartório",
    "documentos emitidos": "Cartório",
    "emissão de documentos": "Cartório",
    "documentos pendentes": "Cartório",
    "funil de emissões": "Cartório",
    "progresso das emissões": "Cartório",
    "certificados": "Cartório",
    "documentação": "Cartório",
    "etapas do processo": "Cartório",
    "tempo de emissão": "Cartório",
    "taxa de aprovação": "Cartório",
    "rejeições": "Cartório",
    "trâmites": "Cartório",
    "solicitações pendentes": "Cartório",
    "processos em tramitação": "Cartório",
    "bitrix cartório": "Cartório",
    "bitrix emissões": "Cartório",
    
    # Termos específicos para submódulos de Cartório
    "movimentações": "Cartório",
    "análise de movimentações": "Cartório",
    "movimentações de processos": "Cartório",
    "emissões de cartão": "Cartório",
    "cartão de identificação": "Cartório",
    "protocolado": "Cartório",
    "processos protocolados": "Cartório",
    "protocolo de documentos": "Cartório",
    "produtividade cartório": "Cartório",
    "tempo no crm": "Cartório",
    "análise de tempo": "Cartório",
    "tempo de processamento crm": "Cartório",
    "visualização cartório": "Cartório",
    "dados cartório": "Cartório",
    
    # Termos gerais para Comune
    "comune": "Comune",
    "comunidade": "Comune",
    "interações": "Comune",
    "usuários": "Comune",
    "engajamento": "Comune",
    "participação": "Comune",
    "atividade de usuários": "Comune",
    "comunicação interna": "Comune",
    "frequência de uso": "Comune",
    "colaboração": "Comune",
    "mensagens trocadas": "Comune",
    "grupos ativos": "Comune",
    "membros ativos": "Comune",
    "interação entre equipes": "Comune",
    "compartilhamento": "Comune",
    "bitrix comune": "Comune",
    "bitrix social": "Comune",
    
    # Termos específicos para submódulos de Comune
    "visualização comune": "Comune",
    "análise comune": "Comune",
    "dados comune": "Comune",
    "mapa de interações": "Comune",
    "mapa de usuários": "Comune",
    "mapa comune": "Comune",
    "rede social interna": "Comune",
    "atividades comune": "Comune",
    "padrões de comunicação": "Comune",
    "estatísticas de uso": "Comune",
    "dashboards comune": "Comune",
    "métricas comune": "Comune",
    "indicadores de comunicação": "Comune",
    
    # Termos para Extrações
    "extrações": "Extrações de Dados",
    "exportar": "Extrações de Dados",
    "relatórios": "Extrações de Dados",
    "consultas": "Extrações de Dados",
    "download": "Extrações de Dados",
    "csv": "Extrações de Dados",
    "excel": "Extrações de Dados",
    "exportação de dados": "Extrações de Dados",
    "relatórios personalizados": "Extrações de Dados",
    "dados brutos": "Extrações de Dados",
    "extração personalizada": "Extrações de Dados",
    "dados para análise": "Extrações de Dados",
    "baixar relatório": "Extrações de Dados",
    "exportar para excel": "Extrações de Dados",
    "formato de arquivo": "Extrações de Dados",
    "api bitrix": "Extrações de Dados",
    "dados do crm": "Extrações de Dados",
    "query personalizada": "Extrações de Dados",
    "consulta de dados": "Extrações de Dados",
    "extração de relatórios": "Extrações de Dados",
    "geração de relatórios": "Extrações de Dados",
    "planilhas de dados": "Extrações de Dados",
    "dados exportados": "Extrações de Dados",
    
    # Termos para Apresentação
    "apresentação": "Apresentação Conclusões",
    "slides": "Apresentação Conclusões",
    "tv": "Apresentação Conclusões",
    "modo tv": "Apresentação Conclusões",
    "automático": "Apresentação Conclusões",
    "apresentação em tela cheia": "Apresentação Conclusões",
    "modo de exibição": "Apresentação Conclusões",
    "apresentação de slides": "Apresentação Conclusões",
    "modo apresentação": "Apresentação Conclusões",
    "visualização para tv": "Apresentação Conclusões",
    "display automático": "Apresentação Conclusões",
    "rotação de slides": "Apresentação Conclusões",
    "apresentação de conclusões": "Apresentação Conclusões",
    "exibição de resultados": "Apresentação Conclusões",
    "demonstração": "Apresentação Conclusões",
    "exibição automática": "Apresentação Conclusões",
    "apresentação visual": "Apresentação Conclusões",
    "apresentação 9:16": "Apresentação Conclusões"
}

def search_report(query):
    """
    Realiza uma busca avançada no índice de termos do relatório.
    
    Args:
        query (str): O termo de busca do usuário
        
    Returns:
        list: Lista de tuplas (página, submódulo, score) relevantes para a busca
    """
    if not query or len(query.strip()) < 3:
        return []
    
    query = query.lower().strip()
    results = {}
    
    # Mapeamento de termos específicos para submódulos
    SUBMODULOS = {
        # Submódulos de Cartório
        "movimentações": "Movimentações",
        "análise de movimentações": "Movimentações",
        "movimentações de processos": "Movimentações",
        "emissões de cartão": "Emissões de Cartão",
        "cartão de identificação": "Emissões de Cartão",
        "protocolado": "Protocolado",
        "processos protocolados": "Protocolado",
        "protocolo de documentos": "Protocolado",
        "produtividade cartório": "Produtividade",
        "tempo no crm": "Análise de Tempo",
        
        # Submódulos de Comune
        "visualização comune": "Visualização",
        "mapa de interações": "Mapa",
        "mapa de usuários": "Mapa",
        "mapa comune": "Mapa",
        
        # Submódulos de Extrações
        "extração personalizada": "Extração Personalizada",
        "relatórios prontos": "Relatórios Prontos",
        "exportação": "Exportação"
    }
    
    # Busca exata
    for term, page in SEARCH_INDEX.items():
        if query == term.lower():
            submódulo = None
            for key, value in SUBMODULOS.items():
                if key in term.lower():
                    submódulo = value
                    break
            
            key = (page, submódulo)
            if key not in results:
                results[key] = 1.0
            else:
                results[key] += 1.0
    
    # Busca parcial
    for term, page in SEARCH_INDEX.items():
        # Correspondência parcial no início do termo (maior relevância)
        if term.lower().startswith(query):
            submódulo = None
            for key, value in SUBMODULOS.items():
                if key in term.lower():
                    submódulo = value
                    break
                
            key = (page, submódulo)
            if key not in results:
                results[key] = 0.8
            else:
                results[key] += 0.8
        
        # Correspondência parcial em qualquer parte do termo
        elif query in term.lower():
            submódulo = None
            for key, value in SUBMODULOS.items():
                if key in term.lower():
                    submódulo = value
                    break
                
            key = (page, submódulo)
            if key not in results:
                results[key] = 0.5
            else:
                results[key] += 0.5
        
        # Correspondência por palavras individuais
        else:
            query_words = query.split()
            for word in query_words:
                if len(word) > 2 and word in term.lower():
                    submódulo = None
                    for key, value in SUBMODULOS.items():
                        if key in term.lower():
                            submódulo = value
                            break
                    
                    key = (page, submódulo)
                    if key not in results:
                        results[key] = 0.3
                    else:
                        results[key] += 0.3
    
    # Ordenar resultados por relevância
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return [(page, submodule, score) for (page, submodule), score in sorted_results if score > 0.2]

def show_search_box():
    """
    Exibe uma caixa de pesquisa avançada para navegar pelo relatório.
    Inclui informações sobre submódulos específicos nos resultados.
    """
    with st.sidebar:
        st.markdown("### 🔍 Buscar no Relatório")
        query = st.text_input("Digite o que procura", key="search_query", placeholder="Ex: certidões entregues, produtividade...")
        
        if query:
            results = search_report(query)
            
            if results:
                st.success(f"Encontrado em {len(results)} seções")
                
                # Agrupar resultados por página
                grouped_results = {}
                for page, submodule, score in results:
                    if page not in grouped_results:
                        grouped_results[page] = []
                    if submodule:
                        grouped_results[page].append((submodule, score))
                    else:
                        # Adicionar um marcador para a página principal
                        grouped_results[page].append((None, score))
                
                # Exibir resultados agrupados
                for page, submodules in grouped_results.items():
                    # Criar função para ir para a página
                    page_function = lambda p=page: st.session_state.update({"pagina_atual": p})
                    
                    # Ordenar submódulos por pontuação
                    submodules.sort(key=lambda x: x[1], reverse=True)
                    
                    # Mostrar botão principal da página
                    st.button(f"Ir para: {page}", key=f"goto_{page}", on_click=page_function, use_container_width=True)
                    
                    # Mostrar submódulos encontrados, se houver
                    submods = [s for s, _ in submodules if s is not None]
                    if submods:
                        with st.expander(f"Detalhe em {page}"):
                            st.write("Encontrado nos seguintes submódulos:")
                            for submodule in set(submods):  # usar set para remover duplicatas
                                st.markdown(f"• {submodule}")
            else:
                st.warning("Nenhum resultado encontrado. Tente outros termos similares como 'documentos emitidos' ou 'certidões'.")
                
                # Sugestões de pesquisa quando não há resultados
                st.markdown("#### Sugestões:")
                sugestoes = {
                    "Certidões": "Cartório",
                    "Produtividade": "Produção Higienização",
                    "Concluídos": "Conclusões Higienização",
                    "Movimentações": "Cartório",
                    "Comune": "Comune",
                    "Extrações": "Extrações de Dados"
                }
                
                for termo, pagina in sugestoes.items():
                    page_function = lambda p=pagina: st.session_state.update({"pagina_atual": p})
                    st.button(f"Buscar: {termo}", key=f"suggest_{termo}", on_click=page_function)

def add_search_term(term, page):
    """
    Adiciona um novo termo ao índice de busca.
    Útil para manter o índice atualizado com novos conteúdos.
    
    Args:
        term (str): O termo a ser adicionado
        page (str): A página associada ao termo
    """
    global SEARCH_INDEX
    SEARCH_INDEX[term.lower()] = page 

def auto_build_search_index():
    """
    Função que automaticamente atualiza o índice de busca baseado nos módulos disponíveis.
    Útil para manter o índice sincronizado com novos módulos adicionados ao relatório.
    """
    global SEARCH_INDEX
    
    # Adicionar variáveis para rastrear novos termos
    novos_termos = 0
    
    # Coletar todos os nomes de arquivos Python em views/ e seus subdiretórios
    def extrair_termos_de_arquivo(arquivo, pagina):
        """Extrai termos de busca potenciais de um arquivo Python."""
        termos_encontrados = []
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
                # Buscar strings em português nas linhas contendo "title", "header", "label", etc.
                import re
                padrao = r'(?:title|header|label|subheader|st\.write|st\.markdown)\s*\(\s*[\'"]([^\'"]*[áàâãéèêíìîóòôõúùûçÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][^\'"]*)[\'"]'
                matches = re.findall(padrao, conteudo)
                
                # Filtrar resultados
                for match in matches:
                    # Ignorar strings muito curtas
                    if len(match) > 5:
                        # Ignorar linhas de código
                        if not match.startswith(('#', '//', '/*', '*', '```')):
                            # Limpar e adicionar o termo
                            termo = match.strip()
                            if termo:
                                termos_encontrados.append(termo)
        except Exception as e:
            print(f"Erro ao processar arquivo {arquivo}: {str(e)}")
            
        return termos_encontrados
    
    # Mapear diretórios para páginas
    mapeamento_dir_pagina = {
        ".": {
            "inicio.py": "Macro Higienização",
            "producao.py": "Produção Higienização",
            "conclusoes.py": "Conclusões Higienização"
        },
        "cartorio": "Cartório",
        "comune": "Comune",
        "extracoes": "Extrações de Dados",
        "apresentacao": "Apresentação Conclusões"
    }
    
    # Percorrer diretórios e arquivos
    diretorio_base = "views"
    for raiz, diretorios, arquivos in os.walk(diretorio_base):
        dir_atual = os.path.basename(raiz)
        
        if dir_atual == "views":
            dir_atual = "."
            
        for arquivo in arquivos:
            if arquivo.endswith(".py") and not arquivo.startswith("__"):
                caminho_completo = os.path.join(raiz, arquivo)
                
                # Determinar a página correta
                pagina = None
                if dir_atual in mapeamento_dir_pagina:
                    if isinstance(mapeamento_dir_pagina[dir_atual], dict):
                        pagina = mapeamento_dir_pagina[dir_atual].get(arquivo)
                    else:
                        pagina = mapeamento_dir_pagina[dir_atual]
                        
                if pagina:
                    # Extrair termos do arquivo
                    termos = extrair_termos_de_arquivo(caminho_completo, pagina)
                    
                    # Adicionar termos ao índice
                    for termo in termos:
                        if termo.lower() not in SEARCH_INDEX:
                            SEARCH_INDEX[termo.lower()] = pagina
                            novos_termos += 1
    
    print(f"Índice de busca atualizado: {novos_termos} novos termos adicionados.")
    return novos_termos

# Adicionar função para inicialização do módulo
def init_search_module():
    """Inicializa o módulo de busca."""
    if st.session_state.get('search_index_initialized') != True:
        # Executar apenas uma vez por sessão
        st.session_state['search_index_initialized'] = True
        try:
            # Atualizar o índice de busca com termos dos arquivos
            auto_build_search_index()
        except Exception as e:
            print(f"Erro ao inicializar módulo de busca: {str(e)}")

# Inicializar o módulo quando importado
init_search_module() 