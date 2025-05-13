import gspread
import pandas as pd
import os
from datetime import datetime
from utils.secrets_helper import get_google_credentials

def load_conclusao_data(start_date=None, end_date=None):
    """
    Carrega e processa dados da planilha Google "CONCLUSÃO HIGIENIZAÇÃO".
    Filtra opcionalmente por data se start_date e end_date forem fornecidos.

    Args:
        start_date (datetime.date, optional): Data de início para filtrar os dados. Defaults to None.
        end_date (datetime.date, optional): Data de fim para filtrar os dados. Defaults to None.

    Returns:
        pandas.DataFrame: DataFrame com os dados processados (sem agregação),
                          por responsável e mesa, ou None em caso de erro.
    """
    try:
        # Obter credenciais usando o helper de secrets
        try:
            credentials = get_google_credentials()
            if not credentials:
                print("Erro: Não foi possível obter as credenciais do Google")
                return None
        except Exception as e:
            print(f"Erro ao obter credenciais: {e}")
            return None

        # Autorizar o cliente gspread com as credenciais
        client = gspread.authorize(credentials)

        # Abre a planilha pelo URL fornecido
        sheet_url = "https://docs.google.com/spreadsheets/d/1mOQY1Rc22KnjJDlB054G0ZvWV_l5v5SIRoMBJllRZQ0/edit#gid=0"
        sheet = client.open_by_url(sheet_url).sheet1

        # Pega todos os dados da planilha como lista de listas
        all_values = sheet.get_all_values()

        # << DEBUG: Imprimir os cabeçalhos lidos da linha 2 (índice 1) >>
        # print("Cabeçalhos lidos da Planilha:", all_values[1]) # Removido ou comentado
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
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                print(f"Erro: Coluna '{coluna}' não encontrada na planilha.")
                return None

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
        df = df[list(colunas_selecionadas.keys())].rename(columns=colunas_selecionadas)

        # --- TRATAMENTO ID FAMILIA (Planilha) ---
        if 'id_familia' in df.columns:
            df['id_familia'] = df['id_familia'].astype(str).str.strip()
        else:
            print("[WARN] Coluna 'id_familia' não encontrada para tratamento.")
        # --- FIM TRATAMENTO ---

        # Converte colunas relevantes para os tipos corretos (opcional, mas recomendado)
        df['data'] = pd.to_datetime(df['data'], errors='coerce') # Ajuste o formato se necessário

        # --- Filtragem por Data (Opcional) --- REINTRODUZIDO
        if start_date and end_date:
            # Garante que as datas de filtro sejam datetime para comparação correta
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Remove linhas onde a data não pôde ser convertida (NaT)
            df_filtrado = df.dropna(subset=['data']).copy()
            
            # Aplica o filtro
            mask = (df_filtrado['data'] >= start_datetime) & (df_filtrado['data'] <= end_datetime)
            df = df_filtrado[mask]
            
            if df.empty:
                print(f"Nenhum dado encontrado entre {start_date.strftime('%d/%m/%Y')} e {end_date.strftime('%d/%m/%Y')}")
                # Retorna um DataFrame vazio com as colunas corretas para evitar erros posteriores
                return pd.DataFrame(columns=df.columns) # Retorna com as mesmas colunas do df original
        # --- FIM FILTRO ---

        # Define critérios para as novas colunas (ajuste conforme necessário)
        status_sucesso = ['CARDS VALIDADOS', 'HIGIENIZAÇÃO COMPLETA', 'CARDS CRIADOS BITRIX'] # CORRIGIDO conforme definição do usuário
        status_incompleto = ['PENDENTE *ATENÇÃO']

        # Utilizar .loc para evitar SettingWithCopyWarning
        df.loc[:, 'higienizacao_exito'] = df['status'].isin(status_sucesso)
        df.loc[:, 'higienizacao_incompleta'] = df['status'].isin(status_incompleto)
        df.loc[:, 'higienizacao_tratadas'] = 1 # Coluna auxiliar para contagem

        # return df # Retorna o DataFrame processado, mas NÃO agregado
        return df # Retorna o DataFrame processado, mas NÃO agregado

    except gspread.exceptions.SpreadsheetNotFound:
        print("Erro: Planilha não encontrada. Verifique o URL.")
        return None
    except gspread.exceptions.APIError as e:
        print(f"Erro na API do Google Sheets: {e}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return None

# Exemplo de como usar a função (pode ser removido ou comentado depois)
if __name__ == '__main__':
    df_resultado = load_conclusao_data()
    if df_resultado is not None:
        print("Dados carregados e processados:")
        print(df_resultado)
    else:
        print("Falha ao carregar os dados.") 