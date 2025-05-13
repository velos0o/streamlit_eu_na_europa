import gspread
import pandas as pd
import os
import streamlit as st
from datetime import datetime
from utils.secrets_helper import get_google_credentials
import traceback

def load_conclusao_data(start_date=None, end_date=None):
    """
    Carrega e processa dados da planilha Google "CONCLUSÃO HIGIENIZAÇÃO".
    Filtra opcionalmente por data se start_date e end_date forem fornecidos.

    Args:
        start_date (datetime.date, optional): Data de início para filtrar os dados. Defaults to None.
        end_date (datetime.date, optional): Data de fim para filtrar os dados. Defaults to None.

    Returns:
        pandas.DataFrame: DataFrame com os dados processados (sem agregação),
                          por responsável e mesa, ou DataFrame vazio em caso de erro.
    """
    try:
        # Exibir mensagem de status
        if hasattr(st, 'status'):
            with st.status("Carregando dados da planilha de conclusão...") as status:
                status.update(label="Obtendo credenciais do Google...")
                
                # Obter credenciais usando o helper de secrets
                try:
                    credentials = get_google_credentials()
                    if not credentials:
                        st.error("Não foi possível obter as credenciais do Google. Verifique as configurações de secrets.")
                        return pd.DataFrame()  # Retorna DataFrame vazio
                    
                    status.update(label="Autorizando cliente gspread...")
                    # Autorizar o cliente gspread com as credenciais
                    client = gspread.authorize(credentials)
                    
                    status.update(label="Acessando planilha de conclusões...")
                    # Abre a planilha pelo URL fornecido
                    sheet_url = "https://docs.google.com/spreadsheets/d/1mOQY1Rc22KnjJDlB054G0ZvWV_l5v5SIRoMBJllRZQ0/edit#gid=0"
                    sheet = client.open_by_url(sheet_url).sheet1
                    
                    status.update(label="Carregando dados da planilha...")
                    # Pega todos os dados da planilha como lista de listas
                    all_values = sheet.get_all_values()
                    
                    df = pd.DataFrame(all_values[2:], columns=all_values[1]) # Usa linha 2 como cabeçalho, dados a partir da linha 3
                    
                    # Verifica se as colunas esperadas existem após carregar com cabeçalho correto
                    colunas_necessarias = [
                        'data',
                        'responsavel',
                        'nome da família',
                        'id da família',
                        'mesa',
                        'status',
                        'MOTIVO HIGIENIZAÇÃO \nDEVOLVIDA (LUCAS)'
                    ]
                    missing_columns = [col for col in colunas_necessarias if col not in df.columns]
                    if missing_columns:
                        st.warning(f"Colunas não encontradas na planilha: {', '.join(missing_columns)}")
                    
                    # Seleciona e renomeia as colunas conforme solicitado
                    colunas_selecionadas = {
                        'data': 'data',
                        'responsavel': 'responsavel',
                        'nome da família': 'nome_familia',
                        'id da família': 'id_familia',
                        'mesa': 'mesa',
                        'status': 'status',
                        'MOTIVO HIGIENIZAÇÃO \nDEVOLVIDA (LUCAS)': 'motivo_devolucao'
                    }
                    
                    # Selecionar apenas as colunas que existem
                    existing_columns = [col for col in colunas_selecionadas.keys() if col in df.columns]
                    df = df[existing_columns].rename(columns={col: colunas_selecionadas[col] for col in existing_columns})
                    
                    status.update(label="Processando e limpando dados...")
                    
                    # --- TRATAMENTO ID FAMILIA (Planilha) ---
                    if 'id_familia' in df.columns:
                        df['id_familia'] = df['id_familia'].astype(str).str.strip()
                    else:
                        print("[WARN] Coluna 'id_familia' não encontrada para tratamento.")
                    # --- FIM TRATAMENTO ---
                    
                    # Converte colunas relevantes para os tipos corretos
                    if 'data' in df.columns:
                        df['data'] = pd.to_datetime(df['data'], errors='coerce')
                    
                    # --- Filtragem por Data (Opcional) ---
                    if start_date and end_date and 'data' in df.columns:
                        # Garante que as datas de filtro sejam datetime para comparação correta
                        start_datetime = datetime.combine(start_date, datetime.min.time())
                        end_datetime = datetime.combine(end_date, datetime.max.time())
                        
                        # Remove linhas onde a data não pôde ser convertida (NaT)
                        df_filtrado = df.dropna(subset=['data']).copy()
                        
                        # Aplica o filtro
                        mask = (df_filtrado['data'] >= start_datetime) & (df_filtrado['data'] <= end_datetime)
                        df = df_filtrado[mask]
                        
                        if df.empty:
                            st.info(f"Nenhum dado encontrado entre {start_date.strftime('%d/%m/%Y')} e {end_date.strftime('%d/%m/%Y')}")
                    # --- FIM FILTRO ---
                    
                    # Define critérios para as novas colunas
                    status_sucesso = ['CARDS VALIDADOS', 'HIGIENIZAÇÃO COMPLETA', 'CARDS CRIADOS BITRIX']
                    status_incompleto = ['PENDENTE *ATENÇÃO']
                    
                    # Garantir que a coluna status existe
                    if 'status' in df.columns:
                        # Utilizar .loc para evitar SettingWithCopyWarning
                        df.loc[:, 'higienizacao_exito'] = df['status'].isin(status_sucesso)
                        df.loc[:, 'higienizacao_incompleta'] = df['status'].isin(status_incompleto)
                    else:
                        # Criar colunas vazias se 'status' não existir
                        df['higienizacao_exito'] = False
                        df['higienizacao_incompleta'] = False
                    
                    df.loc[:, 'higienizacao_tratadas'] = 1  # Coluna auxiliar para contagem
                    
                    status.update(label="Dados carregados com sucesso!", state="complete")
                    return df  # Retorna o DataFrame processado
                    
                except Exception as credentials_error:
                    error_traceback = traceback.format_exc()
                    st.error(f"Erro ao processar dados: {str(credentials_error)}")
                    st.code(error_traceback, language="python")
                    return pd.DataFrame()  # Retorna DataFrame vazio
        else:
            # Versão sem interface visual para chamadas fora do Streamlit
            try:
                credentials = get_google_credentials()
                if not credentials:
                    print("Erro: Não foi possível obter as credenciais do Google")
                    return pd.DataFrame()
                
                # Autorizar o cliente gspread com as credenciais
                client = gspread.authorize(credentials)
                
                # Abre a planilha pelo URL fornecido
                sheet_url = "https://docs.google.com/spreadsheets/d/1mOQY1Rc22KnjJDlB054G0ZvWV_l5v5SIRoMBJllRZQ0/edit#gid=0"
                sheet = client.open_by_url(sheet_url).sheet1
                
                # Resto do código igual, mas sem as atualizações de status
                all_values = sheet.get_all_values()
                df = pd.DataFrame(all_values[2:], columns=all_values[1])
                
                # Continuar com o processamento como antes...
                colunas_selecionadas = {
                    'data': 'data',
                    'responsavel': 'responsavel',
                    'nome da família': 'nome_familia',
                    'id da família': 'id_familia',
                    'mesa': 'mesa',
                    'status': 'status',
                    'MOTIVO HIGIENIZAÇÃO \nDEVOLVIDA (LUCAS)': 'motivo_devolucao'
                }
                
                existing_columns = [col for col in colunas_selecionadas.keys() if col in df.columns]
                df = df[existing_columns].rename(columns={col: colunas_selecionadas[col] for col in existing_columns})
                
                # --- TRATAMENTO ID FAMILIA ---
                if 'id_familia' in df.columns:
                    df['id_familia'] = df['id_familia'].astype(str).str.strip()
                
                # Converte data
                if 'data' in df.columns:
                    df['data'] = pd.to_datetime(df['data'], errors='coerce')
                
                # Filtragem por data
                if start_date and end_date and 'data' in df.columns:
                    start_datetime = datetime.combine(start_date, datetime.min.time())
                    end_datetime = datetime.combine(end_date, datetime.max.time())
                    df_filtrado = df.dropna(subset=['data']).copy()
                    mask = (df_filtrado['data'] >= start_datetime) & (df_filtrado['data'] <= end_datetime)
                    df = df_filtrado[mask]
                
                # Define novas colunas
                status_sucesso = ['CARDS VALIDADOS', 'HIGIENIZAÇÃO COMPLETA', 'CARDS CRIADOS BITRIX']
                status_incompleto = ['PENDENTE *ATENÇÃO']
                
                if 'status' in df.columns:
                    df.loc[:, 'higienizacao_exito'] = df['status'].isin(status_sucesso)
                    df.loc[:, 'higienizacao_incompleta'] = df['status'].isin(status_incompleto)
                else:
                    df['higienizacao_exito'] = False
                    df['higienizacao_incompleta'] = False
                
                df.loc[:, 'higienizacao_tratadas'] = 1
                
                return df
            
            except Exception as e:
                print(f"Ocorreu um erro inesperado: {e}")
                print(traceback.format_exc())
                return pd.DataFrame()

    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"Erro ao carregar dados: {str(e)}")
            st.code(traceback.format_exc(), language="python")
        else:
            print(f"Ocorreu um erro inesperado: {e}")
            print(traceback.format_exc())
        return pd.DataFrame()  # Retorna DataFrame vazio

# Exemplo de como usar a função (pode ser removido ou comentado depois)
if __name__ == '__main__':
    df_resultado = load_conclusao_data()
    if not df_resultado.empty:
        print("Dados carregados e processados:")
        print(df_resultado)
    else:
        print("Falha ao carregar os dados.") 