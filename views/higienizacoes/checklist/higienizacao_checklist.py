import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import gspread
from google.oauth2 import service_account
import os
import traceback

def show_higienizacao_checklist():
    """
    Exibe a página de checklist de produção de higienização.
    Esta página mostra um dashboard voltado para checklist de tarefas de higienização.
    """
    st.header("Controle de Conclusão Higienização")
    
    # Carregamento de estilo CSS
    try:
        # Construir o caminho para o arquivo CSS
        css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                             'assets', 'styles', 'css', 'main.css')
        
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Não foi possível carregar o arquivo CSS: {str(e)}")
    
    # Função para carregar dados da planilha
    @st.cache_data(ttl=300)
    def load_data():
        # Configurar credenciais e acessar a planilha
        try:
            # Caminho para o arquivo de credenciais
            credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                        "views", "cartorio_new", "chaves", "leitura-planilhas-459604-84a6f83793a3.json")
            
            # Verificar se o arquivo de credenciais existe
            if not os.path.exists(credentials_path):
                st.error(f"Arquivo de credenciais não encontrado")
                return pd.DataFrame()
            
            # Configurar credenciais
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                )
            except Exception as e:
                st.error(f"Erro ao configurar credenciais: {str(e)}")
                return pd.DataFrame()
            
            # Criar cliente gspread
            try:
                gc = gspread.authorize(credentials)
            except Exception as e:
                st.error(f"Erro ao autorizar gspread: {str(e)}")
                return pd.DataFrame()
            
            # Abrir a planilha por URL
            try:
                sheet_url = "https://docs.google.com/spreadsheets/d/1mOQY1Rc22KnjJDlB054G0ZvWV_l5v5SIRoMBJllRZQ0"
                sh = gc.open_by_url(sheet_url)
            except Exception as e:
                st.error(f"Erro ao abrir planilha: {str(e)}")
                return pd.DataFrame()
            
            # Selecionar a primeira aba (índice 0)
            try:
                worksheet = sh.get_worksheet(0)
            except Exception as e:
                st.error(f"Erro ao acessar worksheet: {str(e)}")
                return pd.DataFrame()
            
            # Obter todos os dados
            try:
                data = worksheet.get_all_values()
                if not data or len(data) < 3:  # Garantir que temos pelo menos cabeçalho e uma linha de dados
                    st.error("A planilha está vazia ou não contém dados suficientes")
                    return pd.DataFrame()
                
                # A linha 2 (índice 1) contém os nomes das colunas de acordo com a planilha
                headers = data[1]
                
                # Usar os dados a partir da linha 3 (índice 2)
                rows = data[2:]
                
                # Verificar se há colunas duplicadas e corrigir
                header_counts = {}
                fixed_headers = []
                
                for i, header in enumerate(headers):
                    if header == '':
                        header = f'unnamed_{i}'  # Dar um nome único para colunas vazias
                    elif header in header_counts:
                        header_counts[header] += 1
                        header = f'{header}_{header_counts[header]}'  # Adicionar sufixo para colunas duplicadas
                    else:
                        header_counts[header] = 0
                    
                    fixed_headers.append(header)
                
            except Exception as e:
                st.error(f"Erro ao obter dados da planilha: {str(e)}")
                return pd.DataFrame()
            
            # Criar DataFrame com pandas
            try:
                # Criar DataFrame com os cabeçalhos corrigidos
                df = pd.DataFrame(rows, columns=fixed_headers)

                # --- Lógica Revisada de Mapeamento e Renomeação ---
                standard_columns_keywords = {
                    'data': ['data'],
                    'responsavel': ['responsavel'],
                    'status': ['status'],
                    'nome da família': ['família', 'familia'], # Palavras-chave
                    'mesa': ['mesa'],
                    'motivo': ['motivo'] # Palavra-chave
                }

                final_rename_map = {} # Mapeia: fixed_header original -> nome padrão final
                found_standard_cols = {} # Rastreia: nome padrão -> fixed_header original encontrado

                # 1. Priorizar correspondências exatas (ignorando maiúsculas/minúsculas e espaços)
                for standard_name in standard_columns_keywords.keys():
                    if standard_name not in found_standard_cols: # Se ainda não encontramos este nome padrão
                        for header in fixed_headers:
                            if header.lower().strip() == standard_name:
                                if header not in final_rename_map: # Garantir que o header original não seja mapeado duas vezes
                                    final_rename_map[header] = standard_name
                                    found_standard_cols[standard_name] = header
                                    break # Passa para o próximo nome padrão

                # 2. Procurar por palavras-chave para os nomes padrão restantes
                for standard_name, keywords in standard_columns_keywords.items():
                    if standard_name not in found_standard_cols: # Se ainda não encontramos este nome padrão
                        for header in fixed_headers:
                            # Garantir que este header original ainda não foi mapeado
                            if header not in final_rename_map:
                                normalized_header = header.lower().strip()
                                if any(keyword in normalized_header for keyword in keywords):
                                    final_rename_map[header] = standard_name
                                    found_standard_cols[standard_name] = header
                                    break # Encontrou a primeira correspondência por palavra-chave, passa para o próximo nome padrão

                # Renomear as colunas encontradas para nomes padrão
                df.rename(columns=final_rename_map, inplace=True)

                # Selecionar APENAS as colunas padrão que foram encontradas e renomeadas
                standard_cols_to_keep = list(found_standard_cols.keys())
                
                # Manter apenas as colunas padrão identificadas
                # Filtrar df para manter apenas as colunas cujos nomes agora correspondem aos nomes padrão
                df = df[[col for col in standard_cols_to_keep if col in df.columns]]

                # --- Fim da Lógica Revisada ---

                # Verificar se a coluna 'data' existe e convertê-la para o tipo data
                if 'data' in df.columns:
                    try:
                        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y', errors='coerce')
                        # Verificar se há valores nulos após a conversão
                        if df['data'].isna().any():
                            pass
                    except Exception as e:
                        pass  # Continuar sem a conversão, mas manter o DataFrame

                return df

            except Exception as e:
                # Melhorar a mensagem de erro para incluir o traceback para depuração
                st.error(f"Erro ao processar DataFrame: {str(e)}\\nTraceback:\\n{traceback.format_exc()}")
                return pd.DataFrame()
        
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return pd.DataFrame()
    
    # Carregar dados
    df = load_data()
    
    if df.empty:
        st.warning("Não foi possível carregar os dados da planilha. Verifique as credenciais e a conexão.")
        return
    
    # Verificar se temos os dados necessários para continuar
    colunas_necessarias = ['responsavel', 'status']
    if not all(coluna in df.columns for coluna in colunas_necessarias):
        st.error(f"Faltam colunas necessárias. Precisamos de: {', '.join(colunas_necessarias)}")
        return
    
    # Verificar se a coluna data foi convertida corretamente
    data_valida = True
    if 'data' not in df.columns:
        data_valida = False
        st.warning("Coluna 'data' não encontrada. Alguns filtros serão desabilitados.")
    elif not pd.api.types.is_datetime64_dtype(df['data']):
        data_valida = False
        st.warning("Coluna 'data' não está no formato de data. Alguns filtros serão desabilitados.")
    
    # Adicionar filtros na barra lateral
    with st.sidebar.expander("Filtros", expanded=True):
        if data_valida:
            # Filtro de período
            st.subheader("Período")
            col1, col2 = st.columns(2)
            with col1:
                data_inicial = st.date_input("Data Inicial", 
                                        value=(datetime.now() - timedelta(days=30)).date(),
                                        max_value=datetime.now().date())
            with col2:
                data_final = st.date_input("Data Final", 
                                        value=datetime.now().date(),
                                        max_value=datetime.now().date())
        
        # Filtro por responsável
        responsaveis = ["Todos"] + sorted(df["responsavel"].unique().tolist())
        responsavel_filtro = st.selectbox("Responsável", options=responsaveis, index=0)
        
        # Filtro por status
        status_unicos = ["Todos"] + sorted(df["status"].unique().tolist())
        status_filtro = st.selectbox("Status", options=status_unicos, index=0)
        
        # Botão para aplicar filtros
        aplicar_filtro = st.button("Aplicar Filtros", use_container_width=True)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if responsavel_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["responsavel"] == responsavel_filtro]
    
    if status_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["status"] == status_filtro]
    
    # Filtrar por data apenas se a coluna data for válida
    if data_valida:
        df_filtrado = df_filtrado[(df_filtrado["data"] >= pd.to_datetime(data_inicial)) & 
                           (df_filtrado["data"] <= pd.to_datetime(data_final))]
    
    # Criar métricas para STATUS
    st.subheader("Métricas de Status")
    
    # Contagem de ocorrências por status
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Total"]
    
    # Adicionar cores para categorias de status
    status_colors = {
        "CARDS VALIDADOS": "#28a745",          # Verde
        "HIGIENIZAÇÃO COMPLETA": "#17a2b8",    # Azul
        "PENDENTE *ATENÇÃO": "#ffc107",        # Amarelo
        "CARDS CRIADOS BITRIX": "#6f42c1",     # Roxo
        "ENVIADO": "#fd7e14"                   # Laranja
    }
    
    # Adicionar cor padrão para status desconhecidos
    for status in status_counts["Status"]:
        if status not in status_colors:
            status_colors[status] = "#6c757d"  # Cinza para status não mapeados
    
    # Exibir os cards de status usando st.metric
    col1, col2, col3, col4 = st.columns(4)
    
    # Obter os 4 status mais comuns
    top_status = status_counts.nlargest(4, "Total")
    
    for i, (index, row) in enumerate(top_status.iterrows()):
        current_col = [col1, col2, col3, col4][i]
        status_nome = row["Status"]
        status_total = row["Total"]
        
        # Calcular percentual em relação ao total de todos os status do DataFrame original df
        # (não do df_filtrado, para que o percentual seja em relação ao universo total de status)
        percentual = (status_total / df["status"].count() * 100) if df["status"].count() > 0 else 0
        
        with current_col:
            # Usar st.metric para exibir os dados
            # O delta pode ser usado para mostrar a variação percentual ou outra informação
            # Para apenas mostrar o percentual, formatamos como string no label ou valor, ou usamos o delta
            # Vamos tentar colocar o percentual como "delta" simbólico, sem cor de up/down
            st.metric(label=status_nome, value=f"{status_total:,}", delta=f"{percentual:.1f}%", delta_color="off")
    
    # Distribuição de Status (tabela)
    st.subheader("Distribuição de Status")
    
    # Tabela de responsáveis por status (tabela cruzada)
    st.subheader("Responsáveis por Status")
    
    # Criar tabela cruzada (crosstab) de responsáveis x status
    crosstab = pd.crosstab(df["responsavel"], df["status"], margins=True, margins_name="Total")
    
    # Reordenar as colunas para ter o Total no final
    cols = [col for col in crosstab.columns if col != "Total"] + ["Total"]
    crosstab = crosstab[cols]
    
    # Função para aplicar estilo à tabela
    def highlight_status(val):
        # Verifique se é um valor numérico e igual a zero
        try:
            return 'opacity: 0.3; color: #aaa' if val == 0 or val == 0.0 else ''
        except:
            # Se não puder comparar diretamente (Series), retorne string vazia
            return ''
    
    # Estilizar a tabela
    # Primeiro, aplicamos o highlight para as células com valor 0
    styled_crosstab = crosstab.style.map(highlight_status) 
    
    # Depois, aplicamos as barras coloridas para cada status
    for status_col_name in crosstab.columns:
        if status_col_name != "Total" and status_col_name in status_colors:
            styled_crosstab = styled_crosstab.bar(
                subset=[status_col_name], 
                color=f'rgba{tuple(int(status_colors[status_col_name].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.2,)}', 
                vmin=0
            )
            
    st.dataframe(styled_crosstab, use_container_width=True)
    
    # Tabela Detalhes dos Dados
    st.subheader("Detalhes dos Dados")

    # Colunas padronizadas que esperamos do load_data e queremos exibir
    colunas_padrao_exibir = ['data', 'responsavel', 'nome da família', 'mesa', 'status', 'motivo']

    # Mapeamento de nomes padrão para nomes de exibição finais
    nomes_display = {
        'data': 'Data',
        'responsavel': 'Responsável',
        'nome da família': 'Nome da Família',
        'mesa': 'Mesa',
        'status': 'Status',
        'motivo': 'Motivo'
    }

    # Filtrar df_filtrado para colunas padrão existentes
    colunas_existentes_em_df = [col for col in colunas_padrao_exibir if col in df_filtrado.columns]
    
    if not colunas_existentes_em_df:
        st.warning("Nenhuma das colunas esperadas foi encontrada nos dados carregados.")
        return
        
    df_exibir = df_filtrado[colunas_existentes_em_df].copy() # Seleciona apenas as colunas padrão encontradas

    # Formatar a coluna de data (se existir e for válida)
    if 'data' in df_exibir.columns:
        if data_valida: # Verifica se a conversão original em load_data funcionou
            try:
                # Tenta formatar, tratando possíveis erros se a coluna não for datetime
                df_exibir['data'] = df_exibir['data'].dt.strftime('%d/%m/%Y')
            except AttributeError:
                 # Se não for datetime (ex: falhou a conversão), tenta converter para string
                 df_exibir['data'] = df_exibir['data'].astype(str)
                 st.warning("Não foi possível formatar a coluna 'Data' como DD/MM/YYYY.")
        else:
            # Se a coluna 'data' não era válida desde o início, converte para string
             df_exibir['data'] = df_exibir['data'].astype(str)

    # Renomear colunas padrão para nomes de exibição
    df_exibir.rename(columns=nomes_display, inplace=True)

    # Resetar o índice para st.dataframe
    df_exibir = df_exibir.reset_index(drop=True)

    # Função para destacar APENAS a célula de status
    def highlight_single_status(status_value):
        # Lida com possíveis valores NaN ou não string
        if pd.isna(status_value):
            return '' # Sem estilo para NaN
        status_value = str(status_value) # Garante que é string para .get()
        color = status_colors.get(status_value, '#6c757d') # Cor padrão cinza
        return f'background-color: {color}30; color: {color}; font-weight: bold'

    # Obter o nome de exibição da coluna Status
    display_status_col_name = nomes_display.get('status', 'Status') # Pega o nome do mapeamento

    # Verificar se a coluna de status existe para aplicar estilo
    if display_status_col_name in df_exibir.columns:
        # Aplicar estilo apenas à coluna 'Status' usando .map()
        styled_df = df_exibir.style.map(highlight_single_status, subset=[display_status_col_name])
        # Exibir a tabela ESTILIZADA
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        # Exibir a tabela sem estilo se a coluna 'Status' não existir
        st.dataframe(df_exibir, use_container_width=True, height=400)
        st.warning(f"Coluna '{display_status_col_name}' não encontrada para estilização.")

    # Adicionar exportação de dados (usando df_filtrado com nomes padrão)
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar dados filtrados (CSV)",
        data=csv,
        file_name=f"higienizacao_checklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    ) 