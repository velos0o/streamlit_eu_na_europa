#!/usr/bin/env python3
"""
Script de Teste - Correção da Lógica de Conclusão Pipeline 104

Este script testa se a correção da lógica de conclusão está funcionando corretamente,
verificando se famílias com cards em andamento no Pesquisa BR não aparecem mais como 100% concluídas.

Execução: python fix_pandas_import.py
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
path_root = Path(__file__).parent
sys.path.append(str(path_root))

def testar_logica_conclusao():
    """
    Testa se a lógica de conclusão do pipeline 104 está correta.
    """
    try:
        from views.cartorio_new.data_loader import carregar_dados_cartorio
        from views.cartorio_new.acompanhamento import calcular_conclusao_por_pipeline
        from views.cartorio_new.utils import simplificar_nome_estagio, categorizar_estagio
        import pandas as pd
        
        print("🔍 Testando lógica de conclusão do pipeline 104...")
        df = carregar_dados_cartorio()
        
        if df.empty:
            print("❌ DataFrame vazio - Verifique a conexão com o Bitrix")
            return False
        
        # Filtrar apenas registros do pipeline 104
        df_104 = df[df['CATEGORY_ID'].astype(str) == '104'].copy()
        
        if df_104.empty:
            print("ℹ️ Nenhum registro do pipeline 104 encontrado para testar")
            return True
        
        print(f"📊 Encontrados {len(df_104)} registros do pipeline 104 para análise")
        
        # Processar estágios
        df_104['STAGE_ID'] = df_104['STAGE_ID'].astype(str)
        df_104['ESTAGIO_LEGIVEL'] = df_104['STAGE_ID'].apply(simplificar_nome_estagio)
        df_104['CATEGORIA_ESTAGIO'] = df_104['ESTAGIO_LEGIVEL'].apply(categorizar_estagio)
        
        # Aplicar função de conclusão
        df_104['CONCLUIDA'] = df_104.apply(lambda row: calcular_conclusao_por_pipeline(row), axis=1)
        
        # Analisar resultados por estágio
        print("\n📈 Análise de conclusão por estágio:")
        
        analise_estagios = df_104.groupby(['ESTAGIO_LEGIVEL', 'CATEGORIA_ESTAGIO']).agg({
            'CONCLUIDA': ['count', 'sum']
        }).round(2)
        
        analise_estagios.columns = ['Total_Registros', 'Marcados_Como_Concluidos']
        analise_estagios = analise_estagios.reset_index()
        
        # Verificar especificamente "PESQUISA PRONTA PARA EMISSÃO"
        pronta_emissao = analise_estagios[
            analise_estagios['ESTAGIO_LEGIVEL'].str.contains('PESQUISA PRONTA PARA EMISSÃO', na=False)
        ]
        
        print("\n🔍 Verificação específica - 'PESQUISA PRONTA PARA EMISSÃO':")
        if not pronta_emissao.empty:
            for _, row in pronta_emissao.iterrows():
                total = row['Total_Registros']
                concluidos = row['Marcados_Como_Concluidos']
                
                print(f"  • {row['ESTAGIO_LEGIVEL']}: {concluidos}/{total} marcados como concluídos")
                
                if concluidos > 0:
                    print("  ❌ ERRO: Registros 'PRONTA PARA EMISSÃO' estão sendo marcados como concluídos!")
                    print("  💡 Isso significa que a correção não foi aplicada corretamente.")
                    return False
                else:
                    print("  ✅ CORRETO: Registros 'PRONTA PARA EMISSÃO' NÃO estão sendo marcados como concluídos")
        else:
            print("  ℹ️ Nenhum registro 'PESQUISA PRONTA PARA EMISSÃO' encontrado")
        
        # Mostrar estatísticas gerais
        print(f"\n📊 Estatísticas gerais do pipeline 104:")
        print(f"  • Total de registros: {len(df_104)}")
        print(f"  • Marcados como concluídos: {df_104['CONCLUIDA'].sum()}")
        print(f"  • Taxa de conclusão: {df_104['CONCLUIDA'].mean() * 100:.1f}%")
        
        # Mostrar distribuição por estágio
        print(f"\n📋 Distribuição por estágio:")
        for _, row in analise_estagios.iterrows():
            estagio = row['ESTAGIO_LEGIVEL']
            categoria = row['CATEGORIA_ESTAGIO']
            total = int(row['Total_Registros'])
            concluidos = int(row['Marcados_Como_Concluidos'])
            taxa = (concluidos / total * 100) if total > 0 else 0
            
            status_icon = "✅" if concluidos == 0 and "PRONTA" in estagio else "📊"
            print(f"  {status_icon} {estagio} ({categoria}): {concluidos}/{total} ({taxa:.1f}%)")
        
        # Teste de família específica (se existir)
        if 'UF_CRM_34_NOME_FAMILIA' in df_104.columns:
            print(f"\n🏠 Teste de famílias específicas:")
            familias_104 = df_104['UF_CRM_34_NOME_FAMILIA'].value_counts().head(3)
            
            for familia, count in familias_104.items():
                if familia and familia != 'Família Desconhecida':
                    familia_data = df_104[df_104['UF_CRM_34_NOME_FAMILIA'] == familia]
                    concluidas_familia = familia_data['CONCLUIDA'].sum()
                    total_familia = len(familia_data)
                    perc_familia = (concluidas_familia / total_familia * 100) if total_familia > 0 else 0
                    
                    print(f"  • {familia}: {concluidas_familia}/{total_familia} concluídas ({perc_familia:.1f}%)")
                    
                    # Verificar se tem "PRONTA PARA EMISSÃO" não concluída
                    pronta_nao_concluida = familia_data[
                        (familia_data['ESTAGIO_LEGIVEL'].str.contains('PESQUISA PRONTA PARA EMISSÃO', na=False)) &
                        (familia_data['CONCLUIDA'] == False)
                    ]
                    
                    if not pronta_nao_concluida.empty:
                        print(f"    ✅ Tem {len(pronta_nao_concluida)} registros 'PRONTA' corretamente NÃO marcados como concluídos")
        
        print("\n✅ Teste da lógica de conclusão concluído com sucesso!")
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
    print("=" * 70)
    print("🧪 TESTE DA CORREÇÃO - LÓGICA DE CONCLUSÃO PIPELINE 104")
    print("=" * 70)
    
    sucesso = testar_logica_conclusao()
    
    print("\n" + "=" * 70)
    if sucesso:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("A lógica de conclusão do pipeline 104 está funcionando corretamente.")
        print("Famílias com 'PESQUISA PRONTA PARA EMISSÃO' não serão mais marcadas como 100% concluídas.")
    else:
        print("❌ TESTE FALHOU!")
        print("A correção não foi aplicada corretamente. Verifique os erros acima.")
    print("=" * 70)
    
    return 0 if sucesso else 1

if __name__ == "__main__":
    sys.exit(main()) 