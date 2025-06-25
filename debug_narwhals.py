#!/usr/bin/env python3
"""
Script de debug detalhado para rastrear DataFrames narwhals na função de produtividade.
"""

import pandas as pd
import sys
import traceback
from utils.dataframe_utils import ensure_pandas_df

def debug_dataframe_type(df, name="DataFrame"):
    """Debug detalhado do tipo de DataFrame."""
    print(f"\n🔍 DEBUG - {name}:")
    print(f"   Tipo: {type(df)}")
    print(f"   Módulo: {type(df).__module__}")
    print(f"   String do tipo: {str(type(df))}")
    print(f"   É pandas?: {isinstance(df, pd.DataFrame)}")
    print(f"   Tem to_pandas?: {hasattr(df, 'to_pandas')}")
    print(f"   Tem to_native?: {hasattr(df, 'to_native')}")
    print(f"   Contém 'narwhals'?: {'narwhals' in str(type(df))}")
    
    if hasattr(df, 'shape'):
        print(f"   Shape: {df.shape}")
    
    return df

def simulate_produtividade_processing():
    """Simula o processamento da função show_produtividade para detectar onde narwhals aparece."""
    print("🚀 Simulando processamento da função show_produtividade...")
    
    # Simular dados de entrada como se viessem do Google Sheets
    print("\n1️⃣ Criando DataFrame de entrada simulado...")
    df_protocolados = pd.DataFrame({
        'ID FAMÍLIA': ['FAM001', 'FAM002', 'FAM003'],
        'CONSULTOR RESPONSÁVEL': ['Jhenifer', 'Juliane', 'Layla'],
        'PROCURAÇÃO - DATA CONCLUSÃO': ['05/05/2025', '06/05/2025', '07/05/2025'],
        'ANALISE - DATA CONCLUSÃO': ['10/05/2025', '11/05/2025', '12/05/2025'],
        'TRADUÇÃO - DATA DE ENTREGA': ['15/05/2025', '16/05/2025', '17/05/2025']
    })
    
    df_protocolados = debug_dataframe_type(df_protocolados, "df_protocolados original")
    df_protocolados = ensure_pandas_df(df_protocolados)
    df_protocolados = debug_dataframe_type(df_protocolados, "df_protocolados após ensure_pandas_df")
    
    # Simular o mapeamento de etapas
    print("\n2️⃣ Processando etapas...")
    mapeamento_etapas = {
        'Procuração': 'PROCURAÇÃO - DATA CONCLUSÃO',
        'Análise Documental': 'ANALISE - DATA CONCLUSÃO',
        'Tradução': 'TRADUÇÃO - DATA DE ENTREGA'
    }
    
    lista_tarefas = []
    for etapa, data_col in mapeamento_etapas.items():
        print(f"\n   📋 Processando etapa: {etapa}")
        
        if data_col in df_protocolados.columns:
            # Simular o slice do DataFrame
            df_etapa = df_protocolados[['ID FAMÍLIA', 'CONSULTOR RESPONSÁVEL', data_col]].copy()
            df_etapa = debug_dataframe_type(df_etapa, f"df_etapa {etapa} após slice")
            
            df_etapa = ensure_pandas_df(df_etapa)
            df_etapa = debug_dataframe_type(df_etapa, f"df_etapa {etapa} após ensure_pandas_df")
            
            # Simular conversão de data
            df_etapa[data_col] = pd.to_datetime(df_etapa[data_col], format='%d/%m/%Y', dayfirst=True, errors='coerce')
            df_etapa = debug_dataframe_type(df_etapa, f"df_etapa {etapa} após to_datetime")
            
            df_etapa.rename(columns={data_col: 'Data Conclusão'}, inplace=True)
            df_etapa['Etapa'] = etapa
            df_etapa = debug_dataframe_type(df_etapa, f"df_etapa {etapa} final")
            
            lista_tarefas.append(ensure_pandas_df(df_etapa))
    
    # Simular concat
    print("\n3️⃣ Fazendo concat das tarefas...")
    if lista_tarefas:
        df_produtividade = pd.concat(lista_tarefas, ignore_index=True)
        df_produtividade = debug_dataframe_type(df_produtividade, "df_produtividade após concat")
        
        df_produtividade = ensure_pandas_df(df_produtividade)
        df_produtividade = debug_dataframe_type(df_produtividade, "df_produtividade após ensure_pandas_df")
    
    # Simular groupby
    print("\n4️⃣ Fazendo groupby...")
    try:
        produtividade_diaria = df_produtividade.groupby(df_produtividade['Data Conclusão'].dt.date).size().reset_index(name='Contagem')
        produtividade_diaria = debug_dataframe_type(produtividade_diaria, "produtividade_diaria após groupby")
        
        produtividade_diaria = ensure_pandas_df(produtividade_diaria)
        produtividade_diaria = debug_dataframe_type(produtividade_diaria, "produtividade_diaria após ensure_pandas_df")
        
        produtividade_diaria.rename(columns={'Data Conclusão': 'Data'}, inplace=True)
        produtividade_diaria = debug_dataframe_type(produtividade_diaria, "produtividade_diaria após rename")
        
        # Simular criação do gráfico Altair
        print("\n5️⃣ Testando criação do gráfico Altair...")
        import altair as alt
        
        print(f"   Tipo antes do alt.Chart: {type(produtividade_diaria)}")
        
        # Este é o ponto crítico onde pode estar ocorrendo o erro
        try:
            base = alt.Chart(ensure_pandas_df(produtividade_diaria))
            print("   ✅ alt.Chart criado com sucesso!")
        except Exception as e:
            print(f"   ❌ ERRO no alt.Chart: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            
    except Exception as e:
        print(f"❌ ERRO no groupby: {e}")
        print(f"Traceback: {traceback.format_exc()}")

def main():
    """Função principal do debug."""
    print("🔍 INICIANDO DEBUG DETALHADO DE NARWHALS DATAFRAMES")
    print("=" * 60)
    
    try:
        simulate_produtividade_processing()
        print("\n✅ Debug concluído sem erros fatais!")
    except Exception as e:
        print(f"\n💥 ERRO FATAL: {e}")
        print(f"Traceback completo: {traceback.format_exc()}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 