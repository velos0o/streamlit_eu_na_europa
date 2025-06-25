#!/usr/bin/env python3
"""
Script que simula exatamente a chamada do Streamlit para rastrear o problema narwhals.
"""

import pandas as pd
import sys
import traceback
from utils.dataframe_utils import ensure_pandas_df

def debug_dataframe_type(df, name="DataFrame"):
    """Debug detalhado do tipo de DataFrame."""
    print(f"\n🔍 DEBUG - {name}:")
    print(f"   Tipo: {type(df)}")
    print(f"   String do tipo: {str(type(df))}")
    print(f"   É pandas?: {isinstance(df, pd.DataFrame)}")
    print(f"   Contém 'narwhals'?: {'narwhals' in str(type(df))}")
    return df

def simulate_google_sheets_data():
    """Simula dados que vêm do Google Sheets exatamente como na função real."""
    print("📊 Simulando dados do Google Sheets...")
    
    # Dados exatamente como vêm do gspread
    data_rows = [
        ['', 'FAM001', 'Jhenifer', 'EM ANDAMENTO', 'SEM PENDENCIAS', 'CONCLUÍDO', 'ADM1', '01/05/2025', '05/05/2025'],
        ['', 'FAM002', 'Juliane', 'EM ANDAMENTO', 'Tradução', 'CONCLUÍDO', 'ADM2', '02/05/2025', '06/05/2025'],
        ['', 'FAM003', 'Layla', 'CONCLUÍDO', 'SEM PENDENCIAS', 'CONCLUÍDO', 'ADM3', '03/05/2025', '07/05/2025']
    ]
    
    # Criar DataFrame como faz a função carregar_dados_protocolados
    df = pd.DataFrame(data_rows)
    df = debug_dataframe_type(df, "DataFrame inicial do gspread")
    
    # Aplicar nomes de colunas como na função real
    num_cols = len(df.columns)
    col_names = [chr(ord('A') + i) for i in range(num_cols)]
    df.columns = col_names[:num_cols]
    df = debug_dataframe_type(df, "DataFrame após renomear colunas")
    
    # Aplicar ensure_pandas_df como na função corrigida
    df = ensure_pandas_df(df)
    df = debug_dataframe_type(df, "DataFrame após ensure_pandas_df em carregar_dados_protocolados")
    
    return df

def simulate_protocolado_main_processing():
    """Simula o processamento em protocolado_main.py"""
    print("\n🏗️ Simulando processamento em protocolado_main.py...")
    
    df_raw = simulate_google_sheets_data()
    
    # Mapeamento de colunas exatamente como na função real
    mapeamento_colunas = {
        'B': 'ID FAMÍLIA', 'C': 'CONSULTOR RESPONSÁVEL', 'D': 'STATUS GERAL', 'E': 'PENDENCIAS',
        'F': 'PROCURAÇÃO - STATUS', 'G': 'PROCURAÇÃO - ADM RESPONSAVEL', 'H': 'PROCURAÇÃO - DATA ENVIO', 
        'I': 'PROCURAÇÃO - DATA CONCLUSÃO'
    }
    
    # Renomear colunas
    df = df_raw.rename(columns=mapeamento_colunas)
    df = debug_dataframe_type(df, "DataFrame após rename columns")
    
    # Aplicar ensure_pandas_df como na correção
    df = ensure_pandas_df(df)
    df = debug_dataframe_type(df, "DataFrame após ensure_pandas_df do rename")
    
    # Processar PENDENCIAS
    if 'PENDENCIAS' in df.columns:
        df['PENDENCIAS'] = df['PENDENCIAS'].fillna('SEM PENDENCIAS').replace('', 'SEM PENDENCIAS')
        df = debug_dataframe_type(df, "DataFrame após processar PENDENCIAS")
    
    return df

def simulate_show_produtividade_call():
    """Simula a chamada completa da função show_produtividade."""
    print("\n🎯 Simulando chamada completa de show_produtividade...")
    
    # Obter dados processados
    df_protocolados = simulate_protocolado_main_processing()
    
    # Simular a chamada da função como no protocolado_main.py
    print("\n📞 Chamando show_produtividade com ensure_pandas_df...")
    df_protocolados_converted = ensure_pandas_df(df_protocolados)
    df_protocolados_converted = debug_dataframe_type(df_protocolados_converted, "DataFrame passado para show_produtividade")
    
    # Agora simular o início da função show_produtividade
    print("\n🔄 Início da função show_produtividade...")
    
    # Verificar se o DataFrame está vazio
    if df_protocolados_converted.empty:
        print("⚠️ DataFrame está vazio!")
        return
    
    # Mapeamento de etapas
    mapeamento_etapas = {
        'Procuração': 'PROCURAÇÃO - DATA CONCLUSÃO'
    }
    
    # Processar uma etapa para testar
    lista_tarefas = []
    for etapa, data_col in mapeamento_etapas.items():
        print(f"\n   📋 Processando etapa: {etapa}")
        
        if data_col in df_protocolados_converted.columns:
            # Este é o ponto crítico - slice do DataFrame
            df_etapa = df_protocolados_converted[['ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', data_col]].copy()
            df_etapa = debug_dataframe_type(df_etapa, f"df_etapa {etapa} após slice")
            
            # Verificar se o slice gerou narwhals
            if 'narwhals' in str(type(df_etapa)):
                print(f"🚨 ENCONTRADO! O slice gerou um DataFrame narwhals!")
                print(f"   DataFrame original: {type(df_protocolados_converted)}")
                print(f"   DataFrame após slice: {type(df_etapa)}")
                
                # Tentar diferentes métodos de conversão
                print("🔧 Tentando conversões...")
                try:
                    df_etapa_fixed = ensure_pandas_df(df_etapa)
                    print(f"   ensure_pandas_df: {type(df_etapa_fixed)}")
                except Exception as e:
                    print(f"   ensure_pandas_df falhou: {e}")
                
                try:
                    df_etapa_manual = pd.DataFrame(df_etapa)
                    print(f"   pd.DataFrame manual: {type(df_etapa_manual)}")
                except Exception as e:
                    print(f"   pd.DataFrame manual falhou: {e}")
        else:
            print(f"   ❌ Coluna {data_col} não encontrada!")

def main():
    """Função principal do debug."""
    print("🔍 DEBUG ESPECÍFICO - RASTREANDO NARWHALS NA CHAMADA REAL")
    print("=" * 70)
    
    try:
        simulate_show_produtividade_call()
        print("\n✅ Debug concluído!")
    except Exception as e:
        print(f"\n💥 ERRO: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 