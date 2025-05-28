import streamlit as st
import pandas as pd
import altair as alt
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

# Mapeamento das colunas da planilha
COLUNAS_DA_PLANILHA = [
    'BUISCADOR',
    'ID FAMILIA',
    'Nome da\nfamilia ',
    'Certidão a emitir ',
    'DATA \nSOLICITAÇÃO',
    'PROTROCOLADO',
    'ITALIA',
    'HIGIENIZAÇÃO\nHENRIQUE',
    'HIGIENIZAÇÃO\nHENRIQUE\nData Higienização'
]

MAPEAMENTO_COLUNAS = {
    'BUISCADOR': 'buscador',
    'ID FAMILIA': 'id_familia',
    'Nome da\nfamilia ': 'nome_familia',
    'Certidão a emitir ': 'certidao_a_emitir',
    'DATA \nSOLICITAÇÃO': 'data_solicitacao',
    'PROTROCOLADO': 'protocolado',
    'ITALIA': 'italia',
    'HIGIENIZAÇÃO\nHENRIQUE': 'status_higienizacao_henrique', 
    'HIGIENIZAÇÃO\nHENRIQUE\nData Higienização': 'data_higienizacao_henrique'
}

# Nomes das colunas após mapeamento
NOME_COLUNA_STATUS_HIGIENIZACAO = 'status_higienizacao_henrique'
NOME_COLUNA_DATA_HIGIENIZACAO = 'data_higienizacao_henrique'

@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados_bitrix_funil46():
    """Carrega dados do Bitrix24 funil 46 para cruzamento."""
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
                'UF_CRM_1746046353172'   # Campo de informação adicional
            ]
            
            # Verificar quais colunas existem
            colunas_existentes = [col for col in colunas_necessarias if col in df_bitrix.columns]
            
            if colunas_existentes:
                # st.info(f"✅ Dados do Bitrix24 funil 46 carregados: {len(df_bitrix)} registros")
                return df_bitrix[colunas_existentes].copy()
            else:
                st.warning(f"⚠️ Colunas necessárias não encontradas no Bitrix. Disponíveis: {list(df_bitrix.columns)}")
                # Retornar pelo menos as colunas que existem
                colunas_disponiveis = [col for col in df_bitrix.columns if 'UF_CRM_' in col or col == 'ID'][:10]
                if colunas_disponiveis:
                    return df_bitrix[colunas_disponiveis].copy()
                else:
                    return df_bitrix.copy()
        else:
            st.warning("⚠️ Nenhum dado encontrado no funil 46 do Bitrix24.")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do Bitrix24: {str(e)}")
        return pd.DataFrame()

def fazer_cruzamento_bitrix(df_planilha):
    """Faz o cruzamento entre dados da planilha e Bitrix24."""
    
    # Carregar dados do Bitrix
    df_bitrix = carregar_dados_bitrix_funil46()
    
    if df_bitrix.empty:
        st.warning("⚠️ Nenhum dado foi retornado do Bitrix24 funil 46.")
        return df_planilha.copy(), df_bitrix
    
    # Debug: mostrar informações das colunas
    # st.info(f"📊 Bitrix24: {len(df_bitrix)} registros com colunas: {list(df_bitrix.columns)}")
    
    # Preparar dados para cruzamento
    if 'id_familia' not in df_planilha.columns:
        st.warning("⚠️ Coluna 'id_familia' não encontrada na planilha.")
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
            # st.info(f"💡 Usando coluna similar: {coluna_match_bitrix}")
        else:
            st.error("❌ Campo UF_CRM_1722605592778 não encontrado no Bitrix24.")
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
        
        # Log do resultado
        # matches = df_cruzado[coluna_match_bitrix].notna().sum()
        # st.success(f"✅ Cruzamento realizado: {matches} matches de {len(df_planilha)} famílias")
        
        return df_cruzado, df_bitrix
        
    except Exception as e:
        st.error(f"❌ Erro no cruzamento de dados: {str(e)}")
        return df_planilha.copy(), df_bitrix

def show_producao_comune():
    """Exibe a página de Produção Comune com métricas e análises."""
    
    # Carregar estilos CSS
    try:
        with open('assets/styles/css/main.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS não encontrado. Execute a compilação SCSS.")

    # Título principal
    st.markdown('<h1 class="producao-comune-title">Produção Comune</h1>', unsafe_allow_html=True)
    st.markdown("**Análise de dados da planilha de produção do Comune.**")

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

    # Processamento dos dados
    df_processado = processar_dados(df)
    if df_processado is None:
        return

    # Fazer cruzamento com Bitrix24
    df_cruzado, df_bitrix = fazer_cruzamento_bitrix(df_processado)

    # Renderizar seções
    renderizar_metricas(df_processado, df_cruzado)
    renderizar_analise_protocolizacao(df_cruzado, df_bitrix)
    renderizar_status_higienizacao(df_processado)
    renderizar_grafico_temporal(df_processado)
    renderizar_tabela_dados(df_processado)

def processar_dados(df):
    """Processa e limpa os dados da planilha."""
    
    # Converter ID FAMILIA para string
    if 'ID FAMILIA' in df.columns:
        try:
            df['ID FAMILIA'] = df['ID FAMILIA'].astype(str)
        except Exception as e:
            st.warning(f"⚠️ Erro ao converter ID FAMILIA: {e}")

    # Verificar colunas existentes
    colunas_existentes = [col for col in COLUNAS_DA_PLANILHA if col in df.columns]
    if not colunas_existentes:
        st.error("❌ Nenhuma das colunas esperadas foi encontrada na planilha.")
        return None
    
    # Selecionar e renomear colunas
    df_selecionado = df[colunas_existentes].copy()
    df_renomeado = df_selecionado.rename(columns=MAPEAMENTO_COLUNAS)
    
    return df_renomeado

def renderizar_metricas(df_processado, df_cruzado=None):
    """Renderiza as métricas principais."""
    
    st.markdown('<h2 class="producao-comune-subtitle">Métricas Principais</h2>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="producao-comune-metricas producao-comune-metricas--neutral">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_familias = calcular_total_familias(df_processado)
            st.metric("👨‍👩‍👧‍👦 Total de Famílias", total_familias)
        
        with col2:
            num_higienizadas = calcular_familias_higienizadas(df_processado)
            st.metric("✅ Famílias Higienizadas", num_higienizadas)
        
        with col3:
            # Calcular famílias protocolizadas do cruzamento Bitrix
            num_protocolizadas = 0
            if df_cruzado is not None and not df_cruzado.empty:
                # Buscar campo UF_CRM_1746046353172 no cruzamento
                if 'UF_CRM_1746046353172' in df_cruzado.columns:
                    num_protocolizadas = df_cruzado['UF_CRM_1746046353172'].str.contains('PROTOCOL', case=False, na=False).sum()
            
            st.metric("📋 Famílias Protocolizadas", num_protocolizadas)
        
        st.markdown('</div>', unsafe_allow_html=True)

def renderizar_analise_protocolizacao(df_cruzado, df_bitrix):
    """Renderiza tabela simples com as famílias protocolizadas."""
    
    if df_bitrix.empty:
        return
    
    # Descobrir qual coluna foi usada no match
    coluna_match_encontrada = None
    for col in df_cruzado.columns:
        if 'UF_CRM_1722605592778' in str(col) and not col.endswith('_bitrix'):
            coluna_match_encontrada = col
            break
    
    if not coluna_match_encontrada or df_cruzado[coluna_match_encontrada].notna().sum() == 0:
        return
    
    # Filtrar famílias com dados do Bitrix
    df_com_bitrix = df_cruzado[df_cruzado[coluna_match_encontrada].notna()].copy()
    
    # Filtrar famílias protocolizadas
    if 'UF_CRM_1746046353172' in df_com_bitrix.columns:
        mask_protocolizado = df_com_bitrix['UF_CRM_1746046353172'].str.contains('PROTOCOL', case=False, na=False)
        df_protocolizadas = df_com_bitrix[mask_protocolizado].copy()
        
        if not df_protocolizadas.empty:
            st.markdown('<h2 class="producao-comune-subtitle">📋 Famílias Protocolizadas</h2>', unsafe_allow_html=True)
            
            # Preparar dados para a tabela
            colunas_tabela = []
            dados_tabela = []
            
            # Adicionar número da linha
            dados_tabela.append(range(1, len(df_protocolizadas) + 1))
            colunas_tabela.append("Nº")
            
            # ID Família
            if 'id_familia' in df_protocolizadas.columns:
                dados_tabela.append(df_protocolizadas['id_familia'].values)
                colunas_tabela.append("ID Família")
            
            # Nome da Família  
            if 'nome_familia' in df_protocolizadas.columns:
                dados_tabela.append(df_protocolizadas['nome_familia'].values)
                colunas_tabela.append("Nome da Família")
            
            # Status de Protocolização
            dados_tabela.append(df_protocolizadas['UF_CRM_1746046353172'].values)
            colunas_tabela.append("Status Protocolização")
            
            # Procurar campo de prioridade (comuns: PRIORITY, PRIORIDADE, etc.)
            campos_prioridade = [col for col in df_protocolizadas.columns 
                               if any(termo in col.upper() for termo in ['PRIORITY', 'PRIORIDADE', 'URGENT', 'PRIORIT'])]
            
            if campos_prioridade:
                dados_tabela.append(df_protocolizadas[campos_prioridade[0]].values)
                colunas_tabela.append("Prioridade")
            
            # Outras colunas relevantes do Bitrix (limitadas)
            outras_colunas = [col for col in df_protocolizadas.columns 
                            if 'UF_CRM_' in col 
                            and col not in ['UF_CRM_1722605592778', 'UF_CRM_1746046353172']
                            and col not in colunas_tabela][:2]  # Máximo 2 colunas extras
            
            for col in outras_colunas:
                dados_tabela.append(df_protocolizadas[col].values)
                # Limpar nome da coluna
                nome_limpo = col.replace('UF_CRM_', '').replace('_', ' ').title()
                colunas_tabela.append(nome_limpo)
            
            # Criar DataFrame para exibição
            df_tabela = pd.DataFrame(dict(zip(colunas_tabela, dados_tabela)))
            
            with st.container():
                st.markdown('<div class="producao-comune-data-table">', unsafe_allow_html=True)
                st.caption(f"📋 Mostrando {len(df_protocolizadas)} famílias com status relacionado a PROTOCOLIZADO")
                st.dataframe(df_tabela, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

def renderizar_status_higienizacao(df):
    """Renderiza a tabela de status de higienização."""
    
    if NOME_COLUNA_STATUS_HIGIENIZACAO not in df.columns:
        return
        
    st.markdown('<h2 class="producao-comune-subtitle">Status de Higienização</h2>', unsafe_allow_html=True)
    
    contagem_higienizacao = df[NOME_COLUNA_STATUS_HIGIENIZACAO].value_counts()
    if not contagem_higienizacao.empty:
        with st.container():
            st.markdown('<div class="producao-comune-status-table">', unsafe_allow_html=True)
            df_status_display = contagem_higienizacao.reset_index()
            df_status_display.columns = ['Status', 'Contagem']
            st.dataframe(df_status_display, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

def renderizar_grafico_temporal(df):
    """Renderiza o gráfico de higienizações por data."""
    
    if NOME_COLUNA_DATA_HIGIENIZACAO not in df.columns:
        return
        
    st.markdown('<h2 class="producao-comune-subtitle">Higienizações por Data</h2>', unsafe_allow_html=True)
    
    if df[NOME_COLUNA_DATA_HIGIENIZACAO].replace('', pd.NaT).isna().all():
        st.info("📅 Não há dados de data de higienização disponíveis.")
        return

    try:
        df[NOME_COLUNA_DATA_HIGIENIZACAO] = pd.to_datetime(
            df[NOME_COLUNA_DATA_HIGIENIZACAO], errors='coerce'
        )
    except Exception as e:
        st.error(f"❌ Erro ao converter as datas: {e}")
        return

    df_datas_validas = df.dropna(subset=[NOME_COLUNA_DATA_HIGIENIZACAO])

    if not df_datas_validas.empty:
        with st.container():
            st.markdown('<div class="adm-evolucao-grafico">', unsafe_allow_html=True)
            
            # Agrupar por data e contar higienizações
            df_agg = df_datas_validas.groupby(
                df_datas_validas[NOME_COLUNA_DATA_HIGIENIZACAO].dt.date
            ).size().reset_index(name='Higienizacoes')
            df_agg.rename(columns={NOME_COLUNA_DATA_HIGIENIZACAO: 'Data'}, inplace=True)
            
            # Converter Data para string formatada para evitar problemas com o tipo temporal
            df_agg['Data Formatada'] = pd.to_datetime(df_agg['Data']).dt.strftime('%d/%m/%Y')

            # Criar gráfico de barras com estilo do producao_adm.py
            barras = alt.Chart(df_agg).mark_bar(
                color='#4CAF50',  # Verde igual ao producao_adm.py
                size=60  # Barras largas
            ).encode(
                x=alt.X('Data Formatada:O', title='Data', sort=alt.SortField('Data')),
                y=alt.Y('Higienizacoes:Q', title='Quantidade de Higienizações'),
                tooltip=['Data Formatada:O', 'Higienizacoes:Q']
            )
            
            # Adicionar números em cima das barras
            texto = alt.Chart(df_agg).mark_text(
                align='center',
                baseline='bottom',
                dy=-5,  # Deslocamento vertical (acima da barra)
                fontSize=16,
                fontWeight='bold'
            ).encode(
                x='Data Formatada:O',
                y='Higienizacoes:Q',
                text='Higienizacoes:Q'
            )
            
            # Combinar gráficos (barras + texto)
            chart = (barras + texto).properties(
                title='Total de Higienizações Diárias (Henrique)',
                height=300
            ).configure_title(
                fontSize=16
            )
            
            st.altair_chart(chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📅 Não há dados de data válidos para gerar o gráfico.")

def renderizar_tabela_dados(df):
    """Renderiza a tabela com todos os dados detalhados."""
    
    st.markdown('<h2 class="producao-comune-subtitle">Dados Detalhados</h2>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="producao-comune-data-table">', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

def calcular_total_familias(df):
    """Calcula o total de famílias únicas."""
    if 'id_familia' in df.columns:
        return len(df['id_familia'].unique())
    return len(df)

def calcular_familias_higienizadas(df):
    """Calcula o número de famílias higienizadas."""
    if NOME_COLUNA_STATUS_HIGIENIZACAO in df.columns:
        contagem = df[NOME_COLUNA_STATUS_HIGIENIZACAO].value_counts()
        return contagem.get('Higienizado', 0)
    return 0

# Para testes locais (opcional)
# if __name__ == '__main__':
#     show_producao_comune() 