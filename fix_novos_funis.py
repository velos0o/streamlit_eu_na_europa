#!/usr/bin/env python3
"""
Script de Validação - Novos Funis 102 e 104

Este script valida se os novos funis estão sendo carregados corretamente
pelo data_loader após as correções implementadas.

Execução: python fix_novos_funis.py
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
path_root = Path(__file__).parent
sys.path.append(str(path_root))

def testar_carregamento_funis():
    """
    Testa se os novos funis 102 e 104 estão sendo carregados.
    """
    try:
        from views.cartorio_new.data_loader import carregar_dados_cartorio
        
        print("🔍 Testando carregamento dos dados de cartório...")
        df = carregar_dados_cartorio()
        
        if df.empty:
            print("❌ DataFrame vazio - Verifique a conexão com o Bitrix")
            return False
            
        # Verificar se a coluna CATEGORY_ID existe
        if 'CATEGORY_ID' not in df.columns:
            print("❌ Coluna CATEGORY_ID não encontrada")
            return False
            
        # Verificar quais categorias estão presentes
        categorias_presentes = sorted(df['CATEGORY_ID'].unique())
        print(f"📊 Categorias encontradas: {categorias_presentes}")
        
        # Contar registros por categoria
        contagens = df['CATEGORY_ID'].value_counts().sort_index()
        print("\n📈 Distribuição de registros:")
        
        nomes_funis = {
            92: "Cartório Casa Verde",
            94: "Cartório Tatuapé", 
            102: "Paróquia",
            104: "Pesquisa BR"
        }
        
        total_registros = 0
        funis_encontrados = []
        
        for categoria, count in contagens.items():
            nome = nomes_funis.get(categoria, f"Categoria {categoria}")
            print(f"  • {nome}: {count:,} registros")
            total_registros += count
            funis_encontrados.append(categoria)
            
        print(f"\n📊 Total de registros: {total_registros:,}")
        
        # Verificar se os novos funis estão presentes
        novos_funis = [102, 104]
        funis_novos_encontrados = [f for f in novos_funis if f in funis_encontrados]
        
        if len(funis_novos_encontrados) == len(novos_funis):
            print("✅ Sucesso! Ambos os novos funis (102 e 104) foram encontrados!")
            
            # Verificar se há dados nos novos funis
            tem_dados_102 = 102 in contagens and contagens[102] > 0
            tem_dados_104 = 104 in contagens and contagens[104] > 0
            
            if tem_dados_102 and tem_dados_104:
                print("✅ Excelente! Ambos os novos funis têm dados!")
            elif tem_dados_102 or tem_dados_104:
                print("⚠️ Atenção: Apenas um dos novos funis tem dados. Isso pode ser normal se um dos funis ainda não tem registros.")
            else:
                print("⚠️ Atenção: Os novos funis foram encontrados mas não têm dados. Verifique se há registros no Bitrix.")
                
        elif len(funis_novos_encontrados) > 0:
            print(f"⚠️ Parcial: Apenas {len(funis_novos_encontrados)} dos 2 novos funis foi encontrado: {funis_novos_encontrados}")
        else:
            print("❌ Erro: Nenhum dos novos funis (102 e 104) foi encontrado!")
            print("   Verifique se há dados dessas categorias no Bitrix ou se a API está funcionando.")
            return False
            
        # Verificar colunas importantes
        colunas_importantes = [
            'STAGE_ID', 
            'UF_CRM_34_ID_FAMILIA', 
            'UF_CRM_34_NOME_FAMILIA',
            'UF_CRM_34_ID_REQUERENTE',
            'ASSIGNED_BY_NAME'
        ]
        
        print("\n🔍 Verificando colunas importantes:")
        for coluna in colunas_importantes:
            if coluna in df.columns:
                valores_nao_nulos = df[coluna].notna().sum()
                print(f"  ✅ {coluna}: {valores_nao_nulos:,} valores não-nulos")
            else:
                print(f"  ❌ {coluna}: AUSENTE")
                
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("   Verifique se todas as dependências estão instaladas.")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def main():
    """
    Função principal do script de validação.
    """
    print("=" * 60)
    print("🧪 VALIDAÇÃO DOS NOVOS FUNIS 102 (PARÓQUIA) E 104 (PESQUISA BR)")
    print("=" * 60)
    
    sucesso = testar_carregamento_funis()
    
    print("\n" + "=" * 60)
    if sucesso:
        print("🎉 VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
        print("Os novos funis estão sendo carregados corretamente.")
    else:
        print("❌ VALIDAÇÃO FALHOU!")
        print("Verifique os erros acima e corrija antes de prosseguir.")
    print("=" * 60)
    
    return 0 if sucesso else 1

if __name__ == "__main__":
    sys.exit(main()) 