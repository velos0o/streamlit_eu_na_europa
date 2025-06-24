import streamlit as st
import pandas as pd
from utils.google_sheets_connector import get_google_sheets_client, fetch_data_from_sheet
from utils.dataframe_utils import ensure_pandas_df

# Configurações da planilha (mesmas do producao_comune.py)
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1pB3HTFsaHyqAt3bhxzWG3RjfAxAzl97ydGqT35uYb-w/edit?gid=0#gid=0'
SHEET_NAME = 'Base Higienização'

def categorizar_status_comune(status):
    """Categoriza o status do comune em GANHO, EM ANDAMENTO ou PERCA."""
    if pd.isna(status):
        return "DESCONHECIDO"
    
    status_str = str(status).strip().upper()
    
    # Categorias conforme especificado no producao_comune.py
    ganho = [
        'PDF DO DOC ENTREGUE',
        'DOCUMENTO FÍSICO ENTREGUE'
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
    
    perca = [
        'PENDENTE HIGIENIZAR',
        'PENDENTE', 
        'DADOS PENDENTES',
        'DEVOLUTIVA EMISSOR',
        'NEGATIVA COMUNE',
        'CANCELADO'
    ]
    
    if status_str in [s.upper() for s in ganho]:
        return 'GANHO'
    elif status_str in [s.upper() for s in perca]:
        return 'PERCA'
    elif status_str in [s.upper() for s in em_andamento]:
        return 'EM ANDAMENTO'
    else:
        return 'DESCONHECIDO'

def show_status_certidao():
    """Exibe a página de status de certidões italianas com busca por nome."""
    
    # Carregar estilos CSS
    try:
        with open('assets/styles/css/main.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS não encontrado.")

    st.title("Status Certidão Italiana")
    st.markdown("**Consulta de status de certidões por nome ou ID da família**")

    # Conectar ao Google Sheets
    client = get_google_sheets_client()
    if not client:
        st.error("❌ Não foi possível conectar ao Google Sheets. Verifique as credenciais.")
        return

    # Carregar dados
    data = fetch_data_from_sheet(client, SPREADSHEET_URL, SHEET_NAME)
    if data is None:
        st.warning("⚠️ Não foi possível carregar os dados da planilha.")
        return

    df = pd.DataFrame(data)
    if df.empty:
        st.info("📋 A planilha está vazia ou não foi possível ler os dados.")
        return

    # Renomear colunas para facilitar o uso
    colunas_mapeamento = {
        'ID FAMILIA': 'id_familia',
        'Nome da\nfamilia ': 'nome_familia',
        'STATUS\ncomune': 'status_comune'
    }
    
    # Verificar quais colunas existem e renomear
    colunas_existentes = {k: v for k, v in colunas_mapeamento.items() if k in df.columns}
    if not colunas_existentes:
        st.error("❌ Colunas necessárias não encontradas na planilha.")
        return
    
    df = df.rename(columns=colunas_existentes)

    # Criar barra de busca
    col_busca1, col_busca2 = st.columns([0.7, 0.3])
    
    with col_busca1:
        termo_busca = st.text_input(
            "🔍 Buscar por nome da família ou ID:",
            placeholder="Digite o nome da família ou ID...",
            help="Digite parte do nome da família ou ID para filtrar"
        )

    with col_busca2:
        opcao_busca = st.selectbox(
            "Filtrar por:",
            options=["TODOS", "ENTREGUE", "NÃO ENTREGUE"],
            index=0
        )

    # Aplicar filtros
    if termo_busca:
        # Converter termo de busca e campos para string para garantir a busca
        termo_busca = str(termo_busca).strip().lower()
        
        # Criar máscaras de busca para nome e ID
        if 'nome_familia' in df.columns:
            mask_nome = df['nome_familia'].astype(str).str.lower().str.contains(termo_busca, na=False)
        else:
            mask_nome = pd.Series(False, index=df.index)
            
        if 'id_familia' in df.columns:
            mask_id = df['id_familia'].astype(str).str.lower().str.contains(termo_busca, na=False)
        else:
            mask_id = pd.Series(False, index=df.index)
            
        # Combinar máscaras
        df = df[mask_nome | mask_id]

    # Filtrar por status de entrega usando a mesma lógica do producao_comune.py
    if opcao_busca != "TODOS" and 'status_comune' in df.columns:
        df['CATEGORIA'] = df['status_comune'].apply(categorizar_status_comune)
        
        if opcao_busca == "ENTREGUE":
            df = df[df['CATEGORIA'] == 'GANHO']
        else:  # NÃO ENTREGUE
            df = df[df['CATEGORIA'] != 'GANHO']

    # Exibir resultados
    if not df.empty:
        st.markdown("### Resultados da Busca")
        
        # Preparar dados para exibição
        df_display = df.copy()
        
        # Adicionar coluna de status de entrega usando a mesma lógica do producao_comune.py
        if 'status_comune' in df_display.columns:
            df_display['ENTREGUE'] = df_display['status_comune'].apply(
                lambda x: '✅ SIM' if categorizar_status_comune(x) == 'GANHO' else '❌ NÃO'
            )
        
        # Selecionar e renomear colunas para exibição
        colunas_exibicao = {
            'id_familia': 'ID Família',
            'nome_familia': 'Nome da Família',
            'status_comune': 'Status',
            'ENTREGUE': 'Entregue'
        }
        
        # Filtrar apenas colunas que existem
        colunas_existentes = [col for col in colunas_exibicao.keys() if col in df_display.columns]
        df_display = df_display[colunas_existentes]
        
        # Renomear colunas
        df_display = df_display.rename(columns={k: v for k, v in colunas_exibicao.items() if k in colunas_existentes})
        
        # Exibir tabela com estilização
        st.markdown('<div class="status-certidao-table">', unsafe_allow_html=True)
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Mostrar total de resultados
        st.caption(f"Total de resultados encontrados: {len(df_display)}")
    else:
        st.info("Nenhum resultado encontrado para os critérios de busca.") 