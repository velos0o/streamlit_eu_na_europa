import gspread
import pandas as pd
import os
from datetime import datetime

# Importar a função de obter credenciais do helper
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
        # Obter credenciais usando o helper
        try:
            credentials = get_google_credentials()
            if credentials is None:
                print("Erro: Não foi possível obter as credenciais do Google via helper.")
                return None
        except Exception as e:
            print(f"Erro ao obter credenciais via helper: {str(e)}")
            return None

        client = gspread.authorize(credentials)

        # Abre a planilha pelo URL fornecido
        sheet_url = "https://docs.google.com/spreadsheets/d/1mOQY1Rc22KnjJDlB054G0ZvWV_l5v5SIRoMBJllRZQ0/edit#gid=0"
        sheet = client.open_by_url(sheet_url).sheet1

        # Pega todos os dados da planilha como lista de listas
        all_values = sheet.get_all_values()

        # Imprimir os cabeçalhos lidos da linha 2 (índice 1) para debug
        print("[DEBUG] Cabeçalhos da planilha:", all_values[1])
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
        
        # Funções auxiliares para encontrar colunas independente de maiúsculas/minúsculas
        def encontrar_coluna_similar(nome_coluna_procurada, todas_colunas):
            """Busca coluna por similaridade, ignorando maiúsculas/minúsculas e acentos"""
            # Versão exata
            if nome_coluna_procurada in todas_colunas:
                return nome_coluna_procurada
                
            # Versão insensível a maiúsculas/minúsculas
            nome_lower = nome_coluna_procurada.lower()
            for col in todas_colunas:
                if col.lower() == nome_lower:
                    print(f"[DEBUG] Coluna '{nome_coluna_procurada}' encontrada como '{col}' (case-insensitive)")
                    return col
                    
            # Versão que procura substring
            for col in todas_colunas:
                if nome_lower in col.lower():
                    print(f"[DEBUG] Coluna '{nome_coluna_procurada}' encontrada como substring em '{col}'")
                    return col
            
            # Algumas variações comuns de nome para 'data'
            if nome_coluna_procurada == 'data':
                for alternativa in ['data conclusão', 'data_conclusao', 'dt', 'date', 'data conclusao']:
                    for col in todas_colunas:
                        if alternativa in col.lower():
                            print(f"[DEBUG] Coluna 'data' encontrada na alternativa '{col}'")
                            return col
            
            return None
                
        # Mapeamento das colunas encontradas para os nomes padrão
        colunas_encontradas = {}
        colunas_ausentes = []
        
        print("[DEBUG] Verificando colunas da planilha...")
        for coluna in colunas_necessarias:
            coluna_encontrada = encontrar_coluna_similar(coluna, df.columns)
            if coluna_encontrada:
                colunas_encontradas[coluna_encontrada] = coluna  # Mapeia nome real -> nome padrão
            else:
                colunas_ausentes.append(coluna)
                print(f"[AVISO] Coluna '{coluna}' não encontrada na planilha, nem versões similares.")
        
        if colunas_ausentes:
            print(f"[ERRO] Colunas ausentes: {colunas_ausentes}")
            print("[DEBUG] Todas as colunas disponíveis na planilha:", list(df.columns))
            # Se faltam colunas essenciais como 'responsavel' e 'mesa', não podemos continuar
            if 'responsavel' in colunas_ausentes or 'mesa' in colunas_ausentes:
                print("[ERRO] Colunas responsavel e/ou mesa ausentes, não é possível continuar.")
                return None
            # Se apenas 'data' estiver ausente, podemos criar uma coluna padrão
            if 'data' in colunas_ausentes and len(colunas_ausentes) == 1:
                print("[AVISO] Criando coluna 'data' padrão com data atual")
                df['data'] = datetime.now().strftime('%Y-%m-%d')
                colunas_encontradas['data'] = 'data'
                colunas_ausentes.remove('data')
        
        # Se ainda temos colunas ausentes, podemos criar colunas vazias para elas
        for coluna in colunas_ausentes:
            print(f"[AVISO] Criando coluna vazia para '{coluna}'")
            df[coluna] = None
            colunas_encontradas[coluna] = coluna
        
        # Seleciona e renomeia as colunas encontradas
        # Atualizar o dicionário de colunas para usar os nomes encontrados -> nomes padrão
        colunas_selecionadas = {
            col_encontrada: (
                'data' if col_padrao == 'data' else
                'responsavel' if col_padrao == 'responsavel' else
                'nome_familia' if col_padrao == 'nome da família' else
                'id_familia' if col_padrao == 'id da família' else
                'mesa' if col_padrao == 'mesa' else
                'status' if col_padrao == 'status' else
                'motivo_devolucao'
            )
            for col_encontrada, col_padrao in colunas_encontradas.items()
        }
        
        print("[DEBUG] Mapeamento final de colunas:", colunas_selecionadas)
        
        # Selecionar apenas as colunas encontradas e renomear
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

        # << DEBUG: Imprimir valores únicos da coluna status >>
        # if 'status' in df.columns: # Removido ou comentado
        #     print("Valores únicos na coluna 'status' da planilha:", df['status'].unique()) # Removido ou comentado
        # else: # Removido ou comentado
        #     print("Coluna 'status' não encontrada para debug.") # Removido ou comentado

        # Define critérios para as novas colunas (ajuste conforme necessário)
        # status_sucesso = ['CARDS VALIDADOS', 'HIGIENIZAÇÃO COMPLETA', 'CARDS CRIADOS BITRIX'] # Linha original
        # status_sucesso = ['CARDS VALIDADOS', 'HIGIENIZAÇÃO COMPLETA'] # Modificação anterior
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