import streamlit as st
import re

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
    
    # Termos para Cartório
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
    
    # Termos para Comune
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
    "rotação de slides": "Apresentação Conclusões"
}

def search_report(query):
    """
    Realiza uma busca no índice de termos do relatório.
    
    Args:
        query (str): O termo de busca do usuário
        
    Returns:
        list: Lista de páginas relevantes para a busca
    """
    if not query or len(query.strip()) < 3:
        return []
    
    query = query.lower().strip()
    results = {}
    
    # Busca exata
    for term, page in SEARCH_INDEX.items():
        if query == term.lower():
            if page not in results:
                results[page] = 1.0
            else:
                results[page] += 1.0
    
    # Busca parcial
    for term, page in SEARCH_INDEX.items():
        # Correspondência parcial no início do termo (maior relevância)
        if term.lower().startswith(query):
            if page not in results:
                results[page] = 0.8
            else:
                results[page] += 0.8
        
        # Correspondência parcial em qualquer parte do termo
        elif query in term.lower():
            if page not in results:
                results[page] = 0.5
            else:
                results[page] += 0.5
        
        # Correspondência por palavras individuais
        else:
            query_words = query.split()
            for word in query_words:
                if len(word) > 2 and word in term.lower():
                    if page not in results:
                        results[page] = 0.3
                    else:
                        results[page] += 0.3
    
    # Ordenar resultados por relevância
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return [page for page, score in sorted_results if score > 0.2]

def show_search_box():
    """
    Exibe uma caixa de pesquisa para navegar pelo relatório.
    """
    with st.sidebar:
        st.markdown("### 🔍 Buscar no Relatório")
        query = st.text_input("Digite o que procura", key="search_query", placeholder="Ex: certidões entregues, produtividade...")
        
        if query:
            results = search_report(query)
            
            if results:
                st.success(f"Encontrado em {len(results)} seções")
                
                for page in results:
                    # Extrai a função para a página correspondente
                    page_function = None
                    if page == "Macro Higienização":
                        page_function = lambda: st.session_state.update({"pagina_atual": "Macro Higienização"})
                    elif page == "Produção Higienização":
                        page_function = lambda: st.session_state.update({"pagina_atual": "Produção Higienização"})
                    elif page == "Conclusões Higienização":
                        page_function = lambda: st.session_state.update({"pagina_atual": "Conclusões Higienização"})
                    elif page == "Cartório":
                        page_function = lambda: st.session_state.update({"pagina_atual": "Cartório"})
                    elif page == "Comune":
                        page_function = lambda: st.session_state.update({"pagina_atual": "Comune"})
                    elif page == "Extrações de Dados":
                        page_function = lambda: st.session_state.update({"pagina_atual": "Extrações de Dados"})
                    elif page == "Apresentação Conclusões":
                        page_function = lambda: st.session_state.update({"pagina_atual": "Apresentação Conclusões"})
                    
                    # Cria um botão para navegar para a página
                    if page_function:
                        st.button(f"Ir para: {page}", key=f"goto_{page}", on_click=page_function, use_container_width=True)
            else:
                st.warning("Nenhum resultado encontrado. Tente outros termos similares como 'documentos emitidos' ou 'certidões'.")
                
                # Sugestões de pesquisa quando não há resultados
                st.markdown("#### Sugestões:")
                sugestoes = {
                    "Certidões": "Cartório",
                    "Produtividade": "Produção Higienização",
                    "Concluídos": "Conclusões Higienização"
                }
                
                for termo, pagina in sugestoes.items():
                    if page_function := {
                        "Macro Higienização": lambda: st.session_state.update({"pagina_atual": "Macro Higienização"}),
                        "Produção Higienização": lambda: st.session_state.update({"pagina_atual": "Produção Higienização"}),
                        "Conclusões Higienização": lambda: st.session_state.update({"pagina_atual": "Conclusões Higienização"}),
                        "Cartório": lambda: st.session_state.update({"pagina_atual": "Cartório"}),
                        "Comune": lambda: st.session_state.update({"pagina_atual": "Comune"}),
                        "Extrações de Dados": lambda: st.session_state.update({"pagina_atual": "Extrações de Dados"}),
                        "Apresentação Conclusões": lambda: st.session_state.update({"pagina_atual": "Apresentação Conclusões"})
                    }.get(pagina):
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