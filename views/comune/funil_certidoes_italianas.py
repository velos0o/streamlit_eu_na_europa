import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.google_sheets_connector import get_google_sheets_client, fetch_data_from_sheet

# Importar para conectar ao Bitrix24
import sys
from pathlib import Path
api_path = Path(__file__).parents[2] / 'api'
sys.path.insert(0, str(api_path))
from bitrix_connector import load_bitrix_data, load_merged_data

# Configurações da planilha
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1pB3HTFsaHyqAt3bhxzWG3RjfAxAzl97ydGqT35uYb-w/edit?gid=0#gid=0'
SHEET_NAME = 'Base Higienização'

# Mapeamento das colunas da planilha (baseado no producao_comune.py)
COLUNAS_DA_PLANILHA = [
    'BUISCADOR',
    'ID FAMILIA',
    'Nome da\nfamilia ',
    'DATA \nSOLICITAÇÃO',
    'PROTROCOLADO',
    'COMUNE',
    'STATUS\ncomune',  # Coluna AB - nossa coluna principal para o funil
    'HIGIENIZAÇÃO\nHENRIQUE'  # Coluna AT - para calcular famílias higienizadas
]

MAPEAMENTO_COLUNAS = {
    'BUISCADOR': 'buscador',
    'ID FAMILIA': 'id_familia',
    'Nome da\nfamilia ': 'nome_familia',
    'DATA \nSOLICITAÇÃO': 'data_solicitacao',
    'PROTROCOLADO': 'protocolado',
    'COMUNE': 'comune',
    'STATUS\ncomune': 'status_comune',  # Coluna principal do funil
    'HIGIENIZAÇÃO\nHENRIQUE': 'status_higienizacao_henrique'  # Para métricas de higienização
}

def categorizar_status_comune(status):
    """Categoriza o status do comune em GANHO, EM ANDAMENTO ou PERCA."""
    if pd.isna(status):
        return "DESCONHECIDO"
    
    status_str = str(status).strip().upper()
    
    # Categorias conforme especificado pelo usuário
    perca = [
        'PENDENTE HIGIENIZAR',
        'PENDENTE', 
        'DADOS PENDENTES',
        'DEVOLUTIVA EMISSOR',
        'NEGATIVA COMUNE',
        'CANCELADO'
    ]
    
    em_andamento = [
        'SOLICITAR',
        'URGENTE',
        'AGUARDANDO COMUNE',
        'AGUARDANDO PARÓQUIA',
        'AGUARDANDO PAGAMENTO DA TAXA',
        'TAXA PAGA',
        'NECESSÁRIO REQUERIMENTO',
        'REQUERIMENTO CONCLUÍDO',
        'AGUARDANDO COMUNE/PARÓQUIA - TEM INFO',
        'AGUARDANDO PDF DO DOC'
    ]
    
    ganho = [
        'PDF DO DOC ENTREGUE',
        'DOCUMENTO FÍSICO ENTREGUE'
    ]
    
    if status_str in [s.upper() for s in ganho]:
        return 'GANHO'
    elif status_str in [s.upper() for s in perca]:
        return 'PERCA'
    elif status_str in [s.upper() for s in em_andamento]:
        return 'EM ANDAMENTO'
    else:
        return 'DESCONHECIDO'

@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados_bitrix_funil46():
    """Carrega dados do Bitrix24 funil 46 para cruzamento de protocolização."""
    try:
        # Carregar dados do funil 46 usando load_merged_data
        df_bitrix = load_merged_data(
            category_id=46,
            debug=False,
            force_reload=False
        )
        
        if df_bitrix is not None and not df_bitrix.empty:
            # Selecionar apenas as colunas necessárias se existirem
            colunas_necessarias = [
                'ID', 
                'UF_CRM_1722605592778',  # Campo para match com ID FAMILIA
                'UF_CRM_1746046353172'   # Campo de informação de protocolização
            ]
            
            # Verificar quais colunas existem
            colunas_existentes = [col for col in colunas_necessarias if col in df_bitrix.columns]
            
            if colunas_existentes:
                return df_bitrix[colunas_existentes].copy()
            else:
                # Retornar pelo menos as colunas que existem
                colunas_disponiveis = [col for col in df_bitrix.columns if 'UF_CRM_' in col or col == 'ID'][:10]
                if colunas_disponiveis:
                    return df_bitrix[colunas_disponiveis].copy()
                else:
                    return df_bitrix.copy()
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do Bitrix24: {str(e)}")
        return pd.DataFrame()

def fazer_cruzamento_bitrix_funil(df_planilha):
    """Faz o cruzamento entre dados da planilha e Bitrix24 para protocolização."""
    
    # Carregar dados do Bitrix
    df_bitrix = carregar_dados_bitrix_funil46()
    
    if df_bitrix.empty:
        return df_planilha.copy(), df_bitrix
    
    # Preparar dados para cruzamento
    if 'id_familia' not in df_planilha.columns:
        return df_planilha.copy(), df_bitrix
    
    # Verificar qual coluna usar para o match
    coluna_match_bitrix = None
    if 'UF_CRM_1722605592778' in df_bitrix.columns:
        coluna_match_bitrix = 'UF_CRM_1722605592778'
    else:
        # Procurar colunas similares
        colunas_similares = [col for col in df_bitrix.columns if '1722605592778' in str(col)]
        if colunas_similares:
            coluna_match_bitrix = colunas_similares[0]
        else:
            return df_planilha.copy(), df_bitrix
    
    # Preparar dados para merge (garantir que sejam strings)
    df_planilha_prep = df_planilha.copy()
    df_bitrix_prep = df_bitrix.copy()
    
    df_planilha_prep['id_familia'] = df_planilha_prep['id_familia'].astype(str).str.strip()
    df_bitrix_prep[coluna_match_bitrix] = df_bitrix_prep[coluna_match_bitrix].astype(str).str.strip()
    
    # Fazer o merge baseado em ID FAMILIA
    try:
        df_cruzado = df_planilha_prep.merge(
            df_bitrix_prep,
            left_on='id_familia',
            right_on=coluna_match_bitrix,
            how='left',
            suffixes=('', '_bitrix')
        )
        
        return df_cruzado, df_bitrix
        
    except Exception as e:
        st.error(f"❌ Erro no cruzamento de dados: {str(e)}")
        return df_planilha.copy(), df_bitrix

def show_funil_certidoes_italianas():
    """Exibe o funil de certidões italianas baseado na coluna STATUS comune."""
    
    # Carregar estilos CSS
    try:
        with open('assets/styles/css/main.css', 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS não encontrado. Execute a compilação SCSS.")

    st.markdown('<div class="cartorio-container cartorio-container--bordered">', unsafe_allow_html=True)
    st.title("Funil Certidões Italianas")

    # Conectar ao Google Sheets e carregar dados
    client = get_google_sheets_client()
    if not client:
        st.error("❌ Não foi possível conectar ao Google Sheets. Verifique as credenciais.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    data = fetch_data_from_sheet(client, SPREADSHEET_URL, SHEET_NAME)
    if data is None:
        st.warning("⚠️ Não foi possível carregar os dados da planilha.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    df_original = pd.DataFrame(data)
    if df_original.empty:
        st.info("📋 A planilha está vazia ou não foi possível ler os dados.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Processar dados
    df_processado = processar_dados_funil(df_original)
    if df_processado is None:
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Fazer cruzamento com Bitrix24 para protocolização
    df_cruzado, df_bitrix = fazer_cruzamento_bitrix_funil(df_processado)

    # Definir colunas importantes
    coluna_status = 'status_comune'
    coluna_familia = 'nome_familia'
    coluna_data = 'data_solicitacao'
    coluna_comune = 'comune'

    # --- Filtros ---
    with st.expander("Filtros", expanded=True):
        # Linha 1: Comune, Família e Protocolização
        col_f1_comune, col_f1_familia, col_f1_protocolo = st.columns([0.4, 0.3, 0.3])

        with col_f1_comune:
            # Filtro de Comune - texto livre
            termo_busca_comune = st.text_input(
                "Buscar Comune:",
                key="busca_comune_funil",
                placeholder="Digite o nome do comune..."
            )
            
            # Mostrar sugestões se houver texto digitado
            if termo_busca_comune and coluna_comune in df_processado.columns:
                comunes_unicos = df_processado[coluna_comune].dropna().unique()
                sugestoes_comune = [
                    comune for comune in comunes_unicos 
                    if termo_busca_comune.lower() in str(comune).lower()
                ][:5]  # Limitar a 5 sugestões
                
                if sugestoes_comune:
                    st.caption("💡 Sugestões: " + ", ".join(sugestoes_comune))
                elif len(termo_busca_comune) > 1:
                    st.caption("❌ Nenhum comune encontrado com esse termo.")

        with col_f1_familia:
            # Filtro Família
            termo_busca_familia = st.text_input(
                "Buscar Família:",
                key="busca_familia_funil",
                placeholder="Digite o nome da família..."
            )

        with col_f1_protocolo:
            # Filtro de Protocolização
            filtro_protocolizado = st.selectbox(
                "Status Protocolização:",
                options=["TODOS", "PROTOCOLADO", "NÃO PROTOCOLADO"],
                index=0,
                key="filtro_protocolizado_funil"
            )

        # Linha 2: Filtro de Data
        col_data1, col_data2, col_data3 = st.columns([0.3, 0.35, 0.35])
        with col_data1:
            aplicar_filtro_data = st.checkbox("Data Solicitação", value=False, key="aplicar_filtro_data_funil")

        data_inicio = None
        data_fim = None
        if aplicar_filtro_data and coluna_data in df_processado.columns:
            # Converter datas
            df_processado[coluna_data] = pd.to_datetime(df_processado[coluna_data], errors='coerce')
            datas_validas = df_processado[coluna_data].dropna()
            
            if not datas_validas.empty:
                min_date = datas_validas.min().date()
                max_date = datas_validas.max().date()
                
                with col_data2:
                    data_inicio = st.date_input("De:", value=min_date, min_value=min_date, max_value=max_date, key="data_inicio_funil", label_visibility="collapsed")
                with col_data3:
                    data_fim = st.date_input("Até:", value=max_date, min_value=min_date, max_value=max_date, key="data_fim_funil", label_visibility="collapsed")

    # Aplicar filtros
    df = aplicar_filtros_funil(df_processado, termo_busca_comune, termo_busca_familia, aplicar_filtro_data, data_inicio, data_fim, coluna_comune, coluna_familia, coluna_data, filtro_protocolizado, df_cruzado)

    if df.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Processar categorização
    df['CATEGORIA'] = df[coluna_status].apply(categorizar_status_comune)

    # Calcular métricas
    total_solicitacoes = len(df)
    total_familias = df['id_familia'].nunique() if 'id_familia' in df.columns else 0
    
    # Calcular total de famílias higienizadas
    # Verificar se temos a coluna de status de higienização
    total_familias_higienizadas = 0
    if 'status_higienizacao_henrique' in df.columns:
        # Valores que indicam higienização (pode ajustar conforme necessário)
        valores_higienizados = [
            'HIGIENIZADO', 'HIGIENIZADA', 'COMPLETO', 'COMPLETA', 'FINALIZADO', 'FINALIZADA',
            'OK', 'PRONTO', 'CONCLUÍDO', 'CONCLUÍDA', 'SIM', 'YES'
        ]
        
        # Contar famílias onde o status indica higienização
        mask_higienizado = df['status_higienizacao_henrique'].fillna('').astype(str).str.upper().isin(valores_higienizados)
        
        # Alternativamente, considerar qualquer valor não vazio como higienizado
        # (descomente a linha abaixo e comente a linha acima se preferir)
        # mask_higienizado = (df['status_higienizacao_henrique'].notna()) & (df['status_higienizacao_henrique'].astype(str).str.strip() != '')
        
        if 'id_familia' in df.columns:
            total_familias_higienizadas = df[mask_higienizado]['id_familia'].nunique()
        else:
            total_familias_higienizadas = df[mask_higienizado].shape[0]

    # Métricas principais
    st.markdown("#### Métricas do Funil")
    
    st.markdown(f"""
    <style>
    .metrica-custom-funil {{
        background: #F8F9FA;
        border: 2px solid #DEE2E6;
        border-radius: 6px;
        padding: 16px;
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }}
    
    .metrica-custom-funil:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: #ADB5BD;
    }}
    
    .metrica-custom-funil .label {{
        color: #6C757D;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
        line-height: 1.2;
    }}
    
    .metrica-custom-funil .valor {{
        color: #495057;
        font-weight: 700;
        font-size: 30px;
        line-height: 1.2;
        margin-bottom: 4px;
    }}
    
    .metricas-container-funil {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }}
    </style>
    
    <div class="metricas-container-funil">
        <div class="metrica-custom-funil">
            <div class="label">Total Solicitações</div>
            <div class="valor">{total_solicitacoes:,}</div>
        </div>
        <div class="metrica-custom-funil">
            <div class="label">Famílias Únicas</div>
            <div class="valor">{total_familias:,}</div>
        </div>
        <div class="metrica-custom-funil">
            <div class="label">Famílias Higienizadas</div>
            <div class="valor">{total_familias_higienizadas:,}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Análise por categoria
    st.markdown("#### Detalhamento por Status Higienizadas")

    # Contar por status e categoria
    contagem_por_status = df.groupby(coluna_status).size().reset_index(name='QUANTIDADE')
    contagem_por_status['PERCENTUAL'] = (contagem_por_status['QUANTIDADE'] / total_solicitacoes * 100).round(1)
    contagem_por_status['CATEGORIA'] = contagem_por_status[coluna_status].apply(categorizar_status_comune)

    # Calcular totais por categoria
    contagem_por_categoria = df['CATEGORIA'].value_counts()
    total_categorias_validas = contagem_por_categoria.drop('DESCONHECIDO', errors='ignore').sum()
    
    ganho_count = contagem_por_categoria.get('GANHO', 0)
    andamento_count = contagem_por_categoria.get('EM ANDAMENTO', 0)
    perca_count = contagem_por_categoria.get('PERCA', 0)
    
    ganho_perc = (ganho_count / total_categorias_validas * 100) if total_categorias_validas > 0 else 0
    andamento_perc = (andamento_count / total_categorias_validas * 100) if total_categorias_validas > 0 else 0
    perca_perc = (perca_count / total_categorias_validas * 100) if total_categorias_validas > 0 else 0

    # Separar por categoria
    status_ganho = contagem_por_status[contagem_por_status['CATEGORIA'] == 'GANHO']
    status_andamento = contagem_por_status[contagem_por_status['CATEGORIA'] == 'EM ANDAMENTO']
    status_perca = contagem_por_status[contagem_por_status['CATEGORIA'] == 'PERCA']

    # Renderizar categorias lado a lado
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            renderizar_categoria_funil(status_ganho, "GANHO", "✅", ganho_count, ganho_perc)
        with col2:
            renderizar_categoria_funil(status_andamento, "EM ANDAMENTO", "⏳", andamento_count, andamento_perc)
        with col3:
            renderizar_categoria_funil(status_perca, "PERCA", "❌", perca_count, perca_perc)

    st.markdown('</div>', unsafe_allow_html=True)  # Fecha cartorio-container

def processar_dados_funil(df):
    """Processa e limpa os dados da planilha para o funil."""
    
    # Verificar colunas existentes
    colunas_existentes = [col for col in COLUNAS_DA_PLANILHA if col in df.columns]
    if not colunas_existentes:
        st.error("❌ Nenhuma das colunas esperadas foi encontrada na planilha.")
        return None
    
    # Selecionar e renomear colunas
    df_selecionado = df[colunas_existentes].copy()
    df_renomeado = df_selecionado.rename(columns=MAPEAMENTO_COLUNAS)
    
    # Verificar se a coluna principal existe
    if 'status_comune' not in df_renomeado.columns:
        st.error("❌ Coluna 'STATUS comune' não encontrada. Verifique se a coluna AB existe na planilha.")
        return None
    
    return df_renomeado

def aplicar_filtros_funil(df, termo_comune, termo_familia, aplicar_data, data_inicio, data_fim, col_comune, col_familia, col_data, filtro_protocolizado, df_cruzado):
    """Aplica os filtros selecionados aos dados."""
    
    df_filtrado = df.copy()
    
    # Filtro Comune
    if termo_comune and col_comune in df_filtrado.columns:
        # Converter para string para garantir que a busca funcione corretamente
        df_filtrado[col_comune] = df_filtrado[col_comune].fillna('').astype(str)
        df_filtrado = df_filtrado[df_filtrado[col_comune].str.contains(termo_comune, case=False, na=False)]
    
    # Filtro Família
    if termo_familia and col_familia in df_filtrado.columns:
        df_filtrado[col_familia] = df_filtrado[col_familia].fillna('').astype(str)
        df_filtrado = df_filtrado[df_filtrado[col_familia].str.contains(termo_familia, case=False, na=False)]
    
    # Filtro Data
    if aplicar_data and data_inicio and data_fim and col_data in df_filtrado.columns:
        start_datetime = pd.to_datetime(data_inicio)
        end_datetime = pd.to_datetime(data_fim) + pd.Timedelta(days=1)
        df_filtrado = df_filtrado[
            (df_filtrado[col_data].notna()) &
            (df_filtrado[col_data] >= start_datetime) &
            (df_filtrado[col_data] < end_datetime)
        ]
    
    # Filtro de Protocolização
    if filtro_protocolizado != "TODOS" and df_cruzado is not None:
        # Verificar se há dados do Bitrix para determinar protocolização
        if 'UF_CRM_1746046353172' in df_cruzado.columns:
            mask_protocolizado = df_cruzado['UF_CRM_1746046353172'].str.contains('PROTOCOL', case=False, na=False)
            
            if filtro_protocolizado == "PROTOCOLADO":
                indices_protocolizados = df_cruzado[mask_protocolizado].index
                df_filtrado = df_filtrado.loc[df_filtrado.index.intersection(indices_protocolizados)]
            elif filtro_protocolizado == "NÃO PROTOCOLADO":
                indices_nao_protocolizados = df_cruzado[~mask_protocolizado].index
                df_filtrado = df_filtrado.loc[df_filtrado.index.intersection(indices_nao_protocolizados)]
    
    return df_filtrado

def renderizar_categoria_funil(df_categoria, titulo, icone, total_count, total_perc):
    """Renderiza uma seção de categoria com seu total e status detalhados."""
    
    # Título da categoria
    st.markdown(f"""
    <div class="category-header" style="margin-bottom: 10px;">
        <h4 class="category-title" style="margin-bottom: 5px;">{icone} {titulo}</h4>
    </div>
    """, unsafe_allow_html=True)

    # Card de resumo da categoria
    st.markdown(f"""
    <div class="card-visao-geral card-visao-geral--summary card-visao-geral--{titulo.lower().replace(' ', '-')}">
        <div class="card-visao-geral__title">Total {titulo}</div>
        <div class="card-visao-geral__metrics">
            <span class="card-visao-geral__quantity">{total_count:,}</span>
            <span class="card-visao-geral__percentage">{total_perc:.1f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Cards dos status detalhados
    if not df_categoria.empty:
        st.markdown('<div class="cards-grid">', unsafe_allow_html=True)

        for _, row_data in df_categoria.iterrows():
            st.markdown(f"""
            <div class="card-visao-geral card-visao-geral--{titulo.lower().replace(' ', '-')}">
                <div class="card-visao-geral__title">{row_data['status_comune']}</div>
                <div class="card-visao-geral__metrics">
                    <span class="card-visao-geral__quantity">{row_data['QUANTIDADE']}</span>
                    <span class="card-visao-geral__percentage">{row_data['PERCENTUAL']:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption(f"Nenhum status detalhado em {titulo}.") 