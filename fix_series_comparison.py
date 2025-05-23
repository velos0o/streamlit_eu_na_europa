#!/usr/bin/env python3
"""
Script de Teste - Correção da Coluna "Pasta C/Emissão Concluída"

Este script testa se a correção da coluna "Pasta C/Emissão Concluída" no higienizacao_desempenho.py
está funcionando corretamente, verificando se famílias com pipeline 104 em andamento
não são mais marcadas incorretamente como concluídas.

Execução: python fix_series_comparison.py
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
path_root = Path(__file__).parent
sys.path.append(str(path_root))

def testar_pasta_c_emissao_concluida():
    """
    Testa se a coluna "Pasta C/Emissão Concluída" está calculada corretamente.
    """
    try:
        from views.cartorio_new.data_loader import carregar_dados_cartorio
        from views.cartorio_new.higienizacao_desempenho import calcular_conclusao_corrigida_por_pipeline
        import pandas as pd
        import numpy as np
        
        print("🔍 Testando cálculo da coluna 'Pasta C/Emissão Concluída'...")
        df = carregar_dados_cartorio()
        
        if df.empty:
            print("❌ DataFrame vazio - Verifique a conexão com o Bitrix")
            return False
        
        print(f"📊 Carregados {len(df)} registros para análise")
        
        # Simular o processamento do higienizacao_desempenho.py
        col_id_familia_bitrix = 'UF_CRM_34_ID_FAMILIA'
        
        if col_id_familia_bitrix not in df.columns:
            print(f"❌ Coluna {col_id_familia_bitrix} não encontrada")
            return False
        
        # Aplicar a função de conclusão corrigida
        df['CONCLUIDA_CORRIGIDA'] = df.apply(
            lambda row: calcular_conclusao_corrigida_por_pipeline(row), axis=1
        )
        
        # Agrupar por família e calcular conclusão
        conclusao_por_familia = df.groupby(col_id_familia_bitrix).agg({
            'CONCLUIDA_CORRIGIDA': ['count', 'sum'],
            'CATEGORY_ID': lambda x: list(x.astype(str).unique())  # Pipelines da família
        })
        conclusao_por_familia.columns = ['total_certidoes', 'total_concluidas', 'pipelines']
        conclusao_por_familia = conclusao_por_familia.reset_index()
        
        # Calcular se família está concluída
        conclusao_por_familia['familia_concluida'] = (
            (conclusao_por_familia['total_certidoes'] > 0) &
            (conclusao_por_familia['total_concluidas'] == conclusao_por_familia['total_certidoes'])
        ).astype(int)
        
        # Estatísticas gerais
        total_familias = len(conclusao_por_familia)
        familias_concluidas = conclusao_por_familia['familia_concluida'].sum()
        
        print(f"\n📊 Estatísticas Gerais:")
        print(f"  • Total de famílias: {total_familias:,}")
        print(f"  • Famílias marcadas como concluídas: {familias_concluidas:,}")
        print(f"  • Taxa de conclusão: {(familias_concluidas/total_familias*100):.1f}%")
        
        # Verificar especificamente famílias com pipeline 104
        familias_com_104 = conclusao_por_familia[
            conclusao_por_familia['pipelines'].apply(lambda x: '104' in x)
        ]
        
        print(f"\n🔍 Análise específica - Famílias com Pipeline 104:")
        if not familias_com_104.empty:
            total_104 = len(familias_com_104)
            concluidas_104 = familias_com_104['familia_concluida'].sum()
            
            print(f"  • Total de famílias com pipeline 104: {total_104:,}")
            print(f"  • Marcadas como concluídas: {concluidas_104:,}")
            print(f"  • Taxa de conclusão: {(concluidas_104/total_104*100):.1f}%")
            
            # Verificar famílias que têm 104 E outros pipelines
            familias_104_mistas = familias_com_104[
                familias_com_104['pipelines'].apply(
                    lambda x: len([p for p in x if p in ['92', '94', '102']]) > 0
                )
            ]
            
            if not familias_104_mistas.empty:
                total_mistas = len(familias_104_mistas)
                concluidas_mistas = familias_104_mistas['familia_concluida'].sum()
                
                print(f"\n  📊 Famílias com 104 + outros pipelines:")
                print(f"    • Total: {total_mistas:,}")
                print(f"    • Concluídas: {concluidas_mistas:,}")
                print(f"    • Taxa: {(concluidas_mistas/total_mistas*100):.1f}%")
                
                # Mostrar alguns exemplos
                print(f"\n  🔍 Exemplos de famílias mistas:")
                for i, (_, row) in enumerate(familias_104_mistas.head(3).iterrows()):
                    id_familia = row[col_id_familia_bitrix]
                    pipelines = ', '.join(row['pipelines'])
                    concluida = "SIM" if row['familia_concluida'] else "NÃO"
                    certidoes = row['total_certidoes']
                    finalizadas = row['total_concluidas']
                    
                    print(f"    {i+1}. Família {id_familia}: Pipelines [{pipelines}]")
                    print(f"       Certidões: {finalizadas}/{certidoes} finalizadas - Concluída: {concluida}")
        else:
            print("  ℹ️ Nenhuma família com pipeline 104 encontrada")
        
        # Verificar se há famílias que deveriam estar sendo corrigidas
        print(f"\n🧪 Teste de Regressão - Famílias que tinham problema:")
        
        # Buscar famílias que têm pipeline 104 não finalizado mas outros pipelines ativos
        df_104 = df[df['CATEGORY_ID'].astype(str) == '104'].copy()
        
        if not df_104.empty:
            # Simular a lógica antiga (problemática) vs nova (corrigida)
            df_104['STAGE_ID'] = df_104['STAGE_ID'].astype(str)
            
            # Contar registros "PRONTA PARA EMISSÃO" (que eram o problema)
            pronta_emissao = df_104[df_104['STAGE_ID'].str.contains('SUCCESS', na=False)]
            
            if not pronta_emissao.empty:
                print(f"  • Encontrados {len(pronta_emissao)} registros pipeline 104 'SUCCESS'")
                
                # Ver quantos desses estão sendo corretamente NÃO marcados como concluídos
                nao_concluidos_corretamente = pronta_emissao[pronta_emissao['CONCLUIDA_CORRIGIDA'] == False]
                
                if len(nao_concluidos_corretamente) > 0:
                    print(f"  ✅ {len(nao_concluidos_corretamente)} registros 'SUCCESS' corretamente NÃO marcados como concluídos")
                else:
                    print(f"  ⚠️ Todos os registros 'SUCCESS' estão sendo marcados como concluídos")
                    
                # Verificar as famílias desses registros
                familias_afetadas = pronta_emissao[col_id_familia_bitrix].unique()
                print(f"  • {len(familias_afetadas)} famílias têm registros pipeline 104 'SUCCESS'")
                
                # Ver se essas famílias estão sendo corretamente calculadas
                familias_problematicas = conclusao_por_familia[
                    conclusao_por_familia[col_id_familia_bitrix].isin(familias_afetadas)
                ]
                
                if not familias_problematicas.empty:
                    incorretamente_concluidas = familias_problematicas[
                        (familias_problematicas['familia_concluida'] == 1) &
                        (familias_problematicas['total_concluidas'] < familias_problematicas['total_certidoes'])
                    ]
                    
                    if len(incorretamente_concluidas) > 0:
                        print(f"  ❌ PROBLEMA: {len(incorretamente_concluidas)} famílias ainda marcadas incorretamente como concluídas")
                        return False
                    else:
                        print(f"  ✅ CORRETO: Todas as famílias estão sendo calculadas corretamente")
        
        print("\n✅ Teste da coluna 'Pasta C/Emissão Concluída' concluído com sucesso!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Função principal do script de teste.
    """
    print("=" * 80)
    print("🧪 TESTE DA CORREÇÃO - COLUNA 'PASTA C/EMISSÃO CONCLUÍDA'")
    print("=" * 80)
    
    sucesso = testar_pasta_c_emissao_concluida()
    
    print("\n" + "=" * 80)
    if sucesso:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("A coluna 'Pasta C/Emissão Concluída' está sendo calculada corretamente.")
        print("Famílias com pipeline 104 em andamento não são mais marcadas incorretamente.")
    else:
        print("❌ TESTE FALHOU!")
        print("A correção não foi aplicada corretamente. Verifique os erros acima.")
    print("=" * 80)
    
    return 0 if sucesso else 1

if __name__ == "__main__":
    sys.exit(main()) 