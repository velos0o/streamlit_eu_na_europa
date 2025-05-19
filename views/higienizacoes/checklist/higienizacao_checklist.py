import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import gspread
import os
import traceback

# Importar a função de obter credenciais do helper
from utils.secrets_helper import get_google_credentials

# Função utilitária para garantir que colunas numéricas sejam exibidas corretamente
def ensure_numeric_display(df):
    """Converte colunas percentuais para formato numérico seguro para exibição."""
    # Crie uma cópia para evitar SettingWithCopyWarning
    df_safe = df.copy()
    
    # Identifique colunas que contenham '%' nos valores (potencialmente percentuais formatados como string)
    cols_to_fix = []
    for col in df_safe.columns:
        # Verificar apenas colunas de string
        if df_safe[col].dtype == 'object':
            # Verifique apenas algumas linhas para eficiência
            sample = df_safe[col].astype(str).head(10)
            if sample.str.contains('%').any():
                cols_to_fix.append(col)
    
    # Converta cada coluna percentual para formato numérico
    for col in cols_to_fix:
        try:
            # Remova o símbolo '%' e converta para float
            df_safe[col] = df_safe[col].astype(str).str.replace('%', '').str.replace(',', '.').astype(float) / 100
        except Exception as e:
            print(f"Erro ao converter coluna {col}: {e}")
    
    return df_safe

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
            # Obter credenciais usando o helper
            try:
                credentials = get_google_credentials()
                if credentials is None:
                    st.error("Não foi possível obter as credenciais do Google.")
                    return pd.DataFrame()
            except Exception as e:
                st.error(f"Erro ao obter credenciais via helper: {str(e)}")
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
                # Mapeamento por posição das colunas (A-G)
                # Os cabeçalhos são valores da linha 1 mas o conteúdo é mais importante que os nomes
                mapeamento_colunas_posicao = {
                    0: 'data',                  # Coluna A 
                    1: 'responsavel',           # Coluna B
                    2: 'nome da família',       # Coluna C
                    3: 'id da família',         # Coluna D
                    4: 'mesa',                  # Coluna E
                    5: 'status',                # Coluna F
                    6: 'motivo'                 # Coluna G
                }
                
                # Construir um dicionário de renomeação baseado em posição, não em conteúdo
                final_rename_map = {}
                for posicao, nome_coluna in mapeamento_colunas_posicao.items():
                    if posicao < len(fixed_headers):
                        print(f"Mapeando coluna na posição {posicao} (valor: '{fixed_headers[posicao]}') para '{nome_coluna}'")
                        final_rename_map[fixed_headers[posicao]] = nome_coluna
                    else:
                        print(f"AVISO: Posição {posicao} está fora do intervalo (total de colunas: {len(fixed_headers)})")
                
                # Log do mapeamento final (apenas para console, não para interface)
                print(f"DEBUG: Cabeçalhos originais da planilha: {fixed_headers}")
                print(f"DEBUG: Mapeamento final de colunas: {final_rename_map}")

                # Renomear as colunas encontradas para nomes padrão
                df.rename(columns=final_rename_map, inplace=True)

                # Selecionar APENAS as colunas padrão que foram encontradas e renomeadas
                standard_cols_to_keep = list(mapeamento_colunas_posicao.values())
                
                # Manter apenas as colunas padrão identificadas que existem no DataFrame
                colunas_existentes = [col for col in standard_cols_to_keep if col in df.columns]
                if colunas_existentes:
                    print(f"Colunas mapeadas encontradas: {colunas_existentes}")
                    df = df[colunas_existentes]
                else:
                    print("ALERTA: Nenhuma coluna mapeada foi encontrada no DataFrame após renomeação!")
                    # Manter o DataFrame original para não quebrar o processamento subsequente
                
                # Verificar os dados após o mapeamento (apenas no console)
                print(f"DEBUG: Colunas após o mapeamento: {list(df.columns)}")
                print(f"DEBUG: Valores únicos de status: {df['status'].unique().tolist() if 'status' in df.columns else 'Coluna status não existe'}")
                print(f"DEBUG: Quantidade de registros: {len(df)}")

                # --- Fim da Lógica Revisada ---

                # Verificar se a coluna 'data' existe e convertê-la para o tipo data
                if 'data' in df.columns:
                    try:
                        # Limpar espaços extras e caracteres problemáticos
                        df['data'] = df['data'].astype(str).str.strip()
                        
                        # Tentar diferentes formatos de data
                        # Primeiro tenta o formato padrão (dia/mês/ano)
                        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y', errors='coerce')
                        
                        # Se houver valores nulos, tentar outros formatos comuns
                        mask_null = df['data'].isna()
                        if mask_null.any():
                            # Tentar formato ano-mês-dia
                            df.loc[mask_null, 'data'] = pd.to_datetime(
                                df.loc[mask_null, 'data'].astype(str), 
                                format='%Y-%m-%d', 
                                errors='coerce'
                            )
                            
                            # Tentar formato mês/dia/ano
                            mask_null = df['data'].isna()
                            if mask_null.any():
                                df.loc[mask_null, 'data'] = pd.to_datetime(
                                    df.loc[mask_null, 'data'].astype(str), 
                                    format='%m/%d/%Y', 
                                    errors='coerce'
                                )
                        
                        # Verificar se há valores nulos após todas as tentativas
                        if df['data'].isna().any():
                            # Log para registros problemáticos
                            problemas = df[df['data'].isna()]['data'].astype(str).unique()
                            print(f"Valores de data que não puderam ser convertidos: {problemas}")
                    except Exception as e:
                        print(f"Erro ao converter coluna 'data': {str(e)}")
                        # Continuar sem a conversão, mas manter o DataFrame

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
    
    # --- SEÇÃO DE FILTROS DIRETAMENTE NA PÁGINA PRINCIPAL ---
    st.subheader("Filtros")
    
    # Opção para desabilitar filtro de data completamente
    ignorar_filtro_data = st.checkbox("Mostrar todos os registros (ignorar filtro de data)", value=False)
    
    # Se o usuário escolher ignorar o filtro de data, mostrar um aviso visual
    if ignorar_filtro_data:
        st.success("✅ Filtro de data desativado - mostrando TODOS os registros independentemente da data")
    
    # Filtro de data (mostrado mesmo se ignorado, mas com cor diferente)
    if data_valida:
        # Adicionar um contêiner com estilo diferente se o filtro estiver sendo ignorado
        date_filter_container = st.container()
        if ignorar_filtro_data:
            date_filter_container.markdown(
                """
                <div style="opacity: 0.6; border: 1px dashed #ccc; padding: 10px; border-radius: 5px; background-color: #f8f9fa;">
                <p style="color: #6c757d; font-style: italic; margin-bottom: 5px;">⚠️ Filtro de data desabilitado (será ignorado)</p>
                """, 
                unsafe_allow_html=True
            )
        
        with date_filter_container:
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                # Determinar valores mín/máx para os inputs de data
                min_date = df["data"].min().date() if not df["data"].empty else (datetime.now() - timedelta(days=365)).date()
                max_date = df["data"].max().date() if not df["data"].empty else datetime.now().date()
                
                # Calcular um valor padrão seguro (30 dias atrás ou o mínimo, o que for maior)
                default_start_date = max(min_date, (datetime.now() - timedelta(days=30)).date())
                
                data_inicial = st.date_input("Data Inicial", 
                                    value=default_start_date,
                                    min_value=min_date,
                                    max_value=max_date,
                                    disabled=False)  # Não desabilitar visualmente
            with col_date2:
                # Valor padrão para data final (hoje ou max_date, o que for menor)
                today = datetime.now().date()
                default_end_date = min(today, max_date)
                
                data_final = st.date_input("Data Final", 
                                    value=default_end_date,
                                    min_value=min_date,
                                    max_value=max_date,
                                    disabled=False)  # Não desabilitar visualmente
        
        if ignorar_filtro_data:
            date_filter_container.markdown("</div>", unsafe_allow_html=True)
    
    # Filtros de responsável e status em colunas
    col_filtro1, col_filtro2 = st.columns(2)
    
    # Filtro por responsável
    with col_filtro1:
        responsaveis = ["Todos"] + sorted(df["responsavel"].unique().tolist())
        responsavel_filtro = st.selectbox("Responsável", options=responsaveis, index=0)
    
    # Filtro por status
    with col_filtro2:
        status_unicos = ["Todos"] + sorted(df["status"].unique().tolist())
        status_filtro = st.selectbox("Status", options=status_unicos, index=0)
    
    # Botão para aplicar filtros centralizado
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        aplicar_filtro = st.button("Aplicar Filtros", use_container_width=True)
    
    # Divisor visual
    st.markdown("---")
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if responsavel_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["responsavel"] == responsavel_filtro]
    
    if status_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["status"] == status_filtro]
    
    # Filtrar por data apenas se a coluna data for válida E o usuário não escolheu ignorar o filtro
    if data_valida and not ignorar_filtro_data:
        # Converter para datetime para garantir comparação consistente
        data_inicial_dt = pd.to_datetime(data_inicial)
        data_final_dt = pd.to_datetime(data_final)
        
        # Adicionar 23:59:59 à data final para incluir todo o dia
        data_final_dt = data_final_dt + pd.Timedelta(hours=23, minutes=59, seconds=59)
        
        # Imprimir informações de debug para resolver o problema
        total_antes = len(df_filtrado)
        
        # Contar valores nulos na coluna data
        nulos_data = df_filtrado["data"].isna().sum()
        print(f"Registros com data nula: {nulos_data}")
        
        # Aplicar filtro incluindo registros sem data
        mask_data_valida = df_filtrado["data"].notna()
        mask_intervalo = (df_filtrado["data"] >= data_inicial_dt) & (df_filtrado["data"] <= data_final_dt)
        df_filtrado = df_filtrado[mask_intervalo | ~mask_data_valida]
        
        # Verificar quantos registros ficaram de fora
        total_depois = len(df_filtrado)
        diferenca = total_antes - total_depois
        if diferenca > 0:
            print(f"ATENÇÃO: {diferenca} registros foram filtrados pela data!")
            # Exibir informações sobre os registros filtrados para debugging
            registros_antes_filtro = set(df.index)
            registros_depois_filtro = set(df_filtrado.index)
            registros_filtrados = registros_antes_filtro - registros_depois_filtro
            if registros_filtrados:
                df_filtrados_fora = df.loc[list(registros_filtrados)]
                print("Exemplo de registros que não passaram no filtro:")
                if "data" in df_filtrados_fora.columns:
                    print(df_filtrados_fora[["data"]].head())
    
    # Exibir mensagem de feedback sobre os filtros aplicados
    registros_antes = len(df)
    registros_depois = len(df_filtrado)
    
    if registros_antes != registros_depois:
        msg_filtros = f"Exibindo {registros_depois} de {registros_antes} registros após aplicação dos filtros"
        if registros_depois < registros_antes and ignorar_filtro_data:
            msg_filtros += " (filtro de data ignorado)"
        st.info(msg_filtros)
    
    # --- FIM DA SEÇÃO DE FILTROS DIRETAMENTE NA PÁGINA PRINCIPAL ---
    
    # Criar métricas para STATUS
    st.subheader("Métricas de Status")
    
    # Contagem de ocorrências por status
    status_counts = df_filtrado["status"].value_counts().reset_index()
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
        
        # Calcular percentual em relação ao total de todos os status do DataFrame filtrado
        # (para refletir corretamente os filtros aplicados)
        percentual = (status_total / df_filtrado["status"].count() * 100) if df_filtrado["status"].count() > 0 else 0
        
        with current_col:
            # Definir cor do card com base no dicionário de cores
            bgcolor = status_colors.get(status_nome, "#6c757d")  # Cor padrão cinza se não estiver no dicionário
            
            # Criar uma div personalizada com estilo
            card_html = f"""
            <div style="padding: 1rem; border-radius: 0.5rem; background-color: {bgcolor}20; border-left: 5px solid {bgcolor}; margin-bottom: 1rem;">
                <h4 style="color: {bgcolor}; margin-bottom: 0.5rem;">{status_nome}</h4>
                <div style="font-size: 1.5rem; font-weight: bold;">{status_total:,}</div>
                <div style="font-size: 0.8rem; color: #666;">{percentual:.1f}% do total</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
    
    # Tabela de responsáveis por status (tabela cruzada)
    st.subheader("Responsáveis por Status")
    
    # Verificar se há dados para criar a tabela cruzada
    if df_filtrado.empty:
        st.warning("Não há dados disponíveis para criar a tabela de responsáveis por status.")
    else:
        try:
            # Criar tabela cruzada (crosstab) de responsáveis x status
            if 'responsavel' in df_filtrado.columns and 'status' in df_filtrado.columns:
                crosstab = pd.crosstab(df_filtrado["responsavel"], df_filtrado["status"], margins=True, margins_name="Total")
                
                # Reordenar as colunas para ter o Total no final
                cols = [col for col in crosstab.columns if col != "Total"] + ["Total"]
                crosstab = crosstab[cols]
                
                # Verificar se a tabela cruzada tem conteúdo
                if crosstab.empty or crosstab.shape[0] <= 1 or crosstab.shape[1] <= 1:
                    st.warning("Tabela cruzada vazia ou com apenas uma linha/coluna.")
                else:
                    # Renderização HTML pura para melhor formatação
                    
                    # Convertemos a tabela para HTML completamente customizado
                    html_table = "<div style='overflow-x: auto;'><table style='width:100%; border-collapse: collapse;'>"
                    
                    # Cabeçalho da tabela
                    html_table += "<thead><tr><th></th>"  # Coluna vazia para o índice
                    for col in crosstab.columns:
                        bgcolor = status_colors.get(col, "#6c757d") if col != "Total" else "#007bff"
                        text_color = "white"
                        html_table += f"<th style='padding: 8px; background-color: {bgcolor}; color: {text_color}; text-align: center;'>{col}</th>"
                    html_table += "</tr></thead>"
                    
                    # Corpo da tabela
                    html_table += "<tbody>"
                    for idx, row in crosstab.iterrows():
                        html_table += f"<tr><th style='padding: 8px; background-color: #f8f9fa; text-align: left;'>{idx}</th>"
                        for col in crosstab.columns:
                            value = row[col]
                            # Aplicar estilo para valores zero
                            if value == 0:
                                cell_style = "color: #aaa; opacity: 0.7;"
                            else:
                                cell_style = ""
                            html_table += f"<td style='padding: 8px; text-align: center; {cell_style}'>{int(value)}</td>"
                        html_table += "</tr>"
                    html_table += "</tbody>"
                    html_table += "</table></div>"
                    
                    # Mostrar HTML puro em vez do dataframe estilizado
                    st.write(html_table, unsafe_allow_html=True)
                    st.caption("Tabela de responsáveis por status (cabeçalhos coloridos)")
                
        except Exception as e:
            # Se falhar ao criar a crosstab, mostre um erro e uma visualização alternativa
            st.error(f"Erro ao criar a tabela cruzada: {str(e)}")
            
            # Criar uma visualização alternativa mais simples como fallback
            try:
                # Contar por responsável e status
                status_resp_counts = df_filtrado.groupby(['responsavel', 'status']).size().reset_index(name='contagem')
                if not status_resp_counts.empty:
                    # Mostrar agrupamento simplificado sem estilização
                    st.write("Visualização alternativa:")
                    st.dataframe(status_resp_counts, use_container_width=True)
            except Exception as inner_e:
                st.error(f"Não foi possível criar visualização alternativa: {str(inner_e)}")
    
    # Tabela Detalhes dos Dados
    st.subheader("Higienização Detalhada por Família")

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

    # Verificar se o dataframe tem dados após a filtragem
    if df_filtrado.empty:
        st.warning("Não há dados disponíveis para exibir após a aplicação dos filtros.")
    else:
        try:
            # Filtrar df_filtrado para colunas padrão existentes
            colunas_existentes_em_df = [col for col in colunas_padrao_exibir if col in df_filtrado.columns]
            
            if not colunas_existentes_em_df:
                st.warning("Nenhuma das colunas esperadas foi encontrada nos dados carregados.")
            else:
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

                # Garantir que colunas numéricas estejam formatadas corretamente
                df_exibir = ensure_numeric_display(df_exibir)

                # Renomear colunas padrão para nomes de exibição
                renomear_colunas = {col: nomes_display[col] for col in colunas_existentes_em_df if col in nomes_display}
                df_exibir.rename(columns=renomear_colunas, inplace=True)

                # Resetar o índice para st.dataframe
                df_exibir = df_exibir.reset_index(drop=True)

                # Verificar se a tabela resultante tem conteúdo
                if df_exibir.empty:
                    st.warning("A tabela de detalhes está vazia após o processamento.")
                else:
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
                        try:
                            # Abordagem 1: Tentar aplicar estilo usando .style do pandas
                            try:
                                # Aplicar estilo apenas à coluna 'Status' usando .map()
                                styled_df = df_exibir.style.map(highlight_single_status, subset=[display_status_col_name])
                                # Exibir a tabela ESTILIZADA
                                st.dataframe(styled_df, use_container_width=True, height=400)
                            except Exception as style_error:
                                st.warning(f"Não foi possível aplicar estilo: {str(style_error)}. Tentando abordagem alternativa...")
                                
                                # Abordagem 2: Alternativa usando HTML manual para casos onde o .style falha
                                st.markdown("<h5>Visualização dos registros:</h5>", unsafe_allow_html=True)
                                
                                # Criar tabela HTML formatada manualmente
                                html_table = "<div style='overflow-x: auto;'><table style='width:100%; border-collapse: collapse;'>"
                                
                                # Cabeçalho
                                html_table += "<thead><tr>"
                                for col in df_exibir.columns:
                                    html_table += f"<th style='padding: 8px; background-color: #f1f1f1; text-align: left;'>{col}</th>"
                                html_table += "</tr></thead><tbody>"
                                
                                # Dados (limitar a 100 linhas para performance)
                                max_rows = min(100, len(df_exibir))
                                for i in range(max_rows):
                                    html_table += "<tr>"
                                    for col in df_exibir.columns:
                                        cell_value = df_exibir.iloc[i][col]
                                        
                                        # Aplicar formatação especial para status
                                        if col == display_status_col_name:
                                            status_value = str(cell_value)
                                            bgcolor = status_colors.get(status_value, '#6c757d')
                                            html_table += f"<td style='padding: 8px; background-color: {bgcolor}30; color: {bgcolor}; font-weight: bold;'>{status_value}</td>"
                                        else:
                                            html_table += f"<td style='padding: 8px; border-bottom: 1px solid #ddd;'>{cell_value}</td>"
                                    html_table += "</tr>"
                                
                                html_table += "</tbody></table></div>"
                                
                                if len(df_exibir) > max_rows:
                                    html_table += f"<p><em>Mostrando {max_rows} de {len(df_exibir)} registros...</em></p>"
                                
                                st.markdown(html_table, unsafe_allow_html=True)
                                
                        except Exception as e:
                            st.warning(f"Erro ao aplicar estilo à tabela: {str(e)}")
                            # Exibir a tabela sem estilo como fallback final
                            st.dataframe(df_exibir, use_container_width=True, height=400)
                    else:
                        # Exibir a tabela sem estilo se a coluna 'Status' não existir
                        st.dataframe(df_exibir, use_container_width=True, height=400)
                        st.warning(f"Coluna '{display_status_col_name}' não encontrada para estilização.")
        except Exception as e:
            st.error(f"Erro ao processar tabela de detalhes: {str(e)}") 
            # Como fallback, mostrar o DataFrame filtrado original sem processamento adicional
            st.dataframe(df_filtrado, use_container_width=True, height=400)

    # Adicionar exportação de dados apenas se houver dados para exportar
    if not df_filtrado.empty:
        try:
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar dados filtrados (CSV)",
                data=csv,
                file_name=f"higienizacao_checklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Erro ao gerar arquivo CSV para download: {str(e)}")
    else:
        st.info("Não há dados para exportar com os filtros atuais.") 