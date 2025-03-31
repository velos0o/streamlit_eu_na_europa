import streamlit as st

def create_toc_container():
    """
    Cria um contêiner para o sumário que pode ser acessado em qualquer página.
    
    Returns:
        container: O contêiner do Streamlit para ser preenchido
    """
    return st.container()

def add_toc_item(container, label, anchor, level=1, icon=None):
    """
    Adiciona um item ao sumário com um link para a âncora na página.
    
    Args:
        container: O contêiner do Streamlit para o sumário
        label (str): O texto do item do sumário
        anchor (str): A âncora para rolar até a seção correspondente
        level (int, optional): O nível de indentação (1-3). Padrão é 1.
        icon (str, optional): Ícone para mostrar antes do texto. Padrão é None.
    """
    indent = "&nbsp;" * (4 * (level - 1))
    icon_str = f"{icon} " if icon else ""
    
    # O link usa javascript para navegar suavemente para a âncora
    container.markdown(
        f"{indent}• <a href='#{anchor}' style='text-decoration: none; color: inherit;' "
        f"onclick='document.getElementById(\"{anchor}\").scrollIntoView({{behavior:\"smooth\"}}); return false;'>"
        f"{icon_str}{label}</a>",
        unsafe_allow_html=True
    )

def render_toc(sections, title="Índice da Página", horizontal=False):
    """
    Renderiza o sumário completo para a página atual.
    
    Args:
        sections (list): Lista de dicionários com as seções da página.
                        Cada dicionário deve ter: 
                        - 'label': Texto do item 
                        - 'anchor': ID da seção 
                        - 'level': (opcional) Nível de indentação (1-3)
                        - 'icon': (opcional) Ícone para mostrar
        title (str, optional): Título do sumário. Padrão é "Índice da Página".
        horizontal (bool, optional): Se True, exibe o sumário horizontalmente.
    """
    if not sections:
        return
    
    # Cria o estilo para o sumário
    st.markdown("""
    <style>
    .toc-header {
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .toc-container {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: #f8f9fa;
    }
    .toc-horizontal {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
    }
    .toc-horizontal a {
        display: inline-block;
        padding: 5px 10px;
        border: 1px solid #e0e0e0;
        border-radius: 3px;
        background-color: white;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Cria o contêiner para o sumário
    with st.container():
        st.markdown(f"<div class='toc-container'><div class='toc-header'>{title}</div>", unsafe_allow_html=True)
        
        if horizontal:
            # Sumário horizontal
            html_items = []
            for section in sections:
                icon_str = f"{section.get('icon', '')} " if section.get('icon') else ""
                html_items.append(
                    f"<a href='#{section['anchor']}' onclick='document.getElementById(\"{section['anchor']}\").scrollIntoView({{behavior:\"smooth\"}}); return false;'>"
                    f"{icon_str}{section['label']}</a>"
                )
            
            st.markdown(
                f"<div class='toc-horizontal'>{''.join(html_items)}</div></div>",
                unsafe_allow_html=True
            )
        else:
            # Sumário vertical
            for section in sections:
                level = section.get('level', 1)
                icon = section.get('icon')
                add_toc_item(st, section['label'], section['anchor'], level, icon)
            
            st.markdown("</div>", unsafe_allow_html=True)

def create_section_anchor(title, container=None):
    """
    Cria uma âncora para uma seção e retorna o ID.
    
    Args:
        title (str): O título da seção
        container: O contêiner do Streamlit (opcional)
    
    Returns:
        str: O ID da âncora
    """
    # Criar um ID a partir do título (remover espaços, caracteres especiais)
    anchor_id = "".join(c if c.isalnum() else "_" for c in title.lower())
    
    # Cria a âncora HTML
    anchor_html = f"<div id='{anchor_id}'></div>"
    
    # Adiciona a âncora ao contêiner ou ao streamlit diretamente
    if container:
        container.markdown(anchor_html, unsafe_allow_html=True)
    else:
        st.markdown(anchor_html, unsafe_allow_html=True)
    
    return anchor_id

def create_section_header(title, level=2, anchor=True, container=None):
    """
    Cria um cabeçalho de seção com uma âncora para navegação.
    
    Args:
        title (str): O título da seção
        level (int, optional): O nível do cabeçalho (1-6). Padrão é 2.
        anchor (bool, optional): Se True, adiciona uma âncora. Padrão é True.
        container: O contêiner do Streamlit (opcional)
    
    Returns:
        str: O ID da âncora se anchor=True, caso contrário None
    """
    anchor_id = None
    
    if anchor:
        anchor_id = create_section_anchor(title, container)
    
    # Cria o cabeçalho HTML
    header_tag = f"h{level}"
    header_html = f"<{header_tag}>{title}</{header_tag}>"
    
    # Adiciona o cabeçalho ao contêiner ou ao streamlit diretamente
    if container:
        container.markdown(header_html, unsafe_allow_html=True)
    else:
        st.markdown(header_html, unsafe_allow_html=True)
    
    return anchor_id 