# Arquivo de inicialização para o pacote components
# Facilita a importação dos módulos deste pacote

from components.report_guide import show_guide_sidebar, show_page_guide, show_contextual_help
from components.search_component import show_search_box, add_search_term
from components.table_of_contents import (
    render_toc, 
    create_section_anchor,
    create_section_header,
    create_toc_container,
    add_toc_item
)
from components.metrics import render_metrics_section, render_conclusion_item
from components.tables import create_responsible_status_table, create_pendencias_table, create_production_table
from components.filters import date_filter_section, responsible_filter, status_filter, create_filter_section 