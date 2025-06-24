#!/usr/bin/env python3
"""
Script para corrigir automaticamente o erro narwhals DataFrame em todo o projeto.

Este script procura por usos de st.dataframe, st.bar_chart, etc. e adiciona a correção
ensure_pandas_df() onde necessário.
"""

import os
import re
import sys
from pathlib import Path

def find_streamlit_dataframe_usage(file_path):
    """Encontra linhas que usam componentes Streamlit que precisam de DataFrames"""
    streamlit_functions = [
        'st.dataframe',
        'st.bar_chart',
        'st.line_chart',
        'st.scatter_chart',
        'st.area_chart'
    ]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = []
    for i, line in enumerate(lines, 1):
        for func in streamlit_functions:
            if func in line and 'ensure_pandas_df' not in line:
                issues.append({
                    'line': i,
                    'content': line.strip(),
                    'function': func
                })
    
    return issues

def add_import_if_needed(file_path):
    """Adiciona import do ensure_pandas_df se necessário"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica se já tem o import
    if 'from utils.dataframe_utils import ensure_pandas_df' in content:
        return False
    
    # Verifica se usa streamlit
    if 'import streamlit' not in content:
        return False
    
    # Adiciona o import após os imports existentes
    lines = content.split('\n')
    import_index = -1
    
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_index = i
    
    if import_index >= 0:
        lines.insert(import_index + 1, 'from utils.dataframe_utils import ensure_pandas_df')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return True
    
    return False

def scan_project():
    """Escaneia todo o projeto procurando por problemas"""
    python_files = []
    
    # Busca todos os arquivos Python
    for root, dirs, files in os.walk('.'):
        # Ignora diretórios específicos
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    issues_found = {}
    
    for file_path in python_files:
        try:
            issues = find_streamlit_dataframe_usage(file_path)
            if issues:
                issues_found[file_path] = issues
        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")
    
    return issues_found

def generate_report(issues_found):
    """Gera relatório dos problemas encontrados"""
    print("\n" + "="*80)
    print("RELATÓRIO DE PROBLEMAS NARWHALS DATAFRAME")
    print("="*80)
    
    if not issues_found:
        print("✅ Nenhum problema encontrado!")
        return
    
    total_issues = sum(len(issues) for issues in issues_found.values())
    print(f"❌ Encontrados {total_issues} problemas em {len(issues_found)} arquivos\n")
    
    for file_path, issues in issues_found.items():
        print(f"📁 {file_path}")
        for issue in issues:
            print(f"   Linha {issue['line']}: {issue['function']} -> {issue['content']}")
        print()
    
    print("RECOMENDAÇÕES:")
    print("1. Execute o script com --fix para aplicar correções automáticas")
    print("2. Ou aplique manualmente usando ensure_pandas_df() nos DataFrames")
    print("3. Teste em localhost antes de fazer deploy")

def auto_fix_issues(issues_found):
    """Aplica correções automáticas nos problemas encontrados"""
    print("\n" + "="*80)
    print("APLICANDO CORREÇÕES AUTOMÁTICAS")
    print("="*80)
    
    fixed_files = 0
    
    for file_path, issues in issues_found.items():
        print(f"🔧 Corrigindo {file_path}...")
        
        # Adiciona import se necessário
        add_import_if_needed(file_path)
        
        # Lê o arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Aplica correções
        original_content = content
        
        # Padrões de correção
        patterns = [
            (r'st\.dataframe\(([^)]+)\)', r'st.dataframe(ensure_pandas_df(\1))'),
            (r'st\.bar_chart\(([^)]+)\)', r'st.bar_chart(ensure_pandas_df(\1))'),
            (r'st\.line_chart\(([^)]+)\)', r'st.line_chart(ensure_pandas_df(\1))'),
            (r'st\.scatter_chart\(([^)]+)\)', r'st.scatter_chart(ensure_pandas_df(\1))'),
            (r'st\.area_chart\(([^)]+)\)', r'st.area_chart(ensure_pandas_df(\1))'),
        ]
        
        for pattern, replacement in patterns:
            # Evita duplicar ensure_pandas_df
            if 'ensure_pandas_df' not in content:
                content = re.sub(pattern, replacement, content)
        
        # Salva se houve mudanças
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_files += 1
            print(f"   ✅ Corrigido!")
        else:
            print(f"   ⚠️  Nenhuma mudança aplicada")
    
    print(f"\n🎉 Correções aplicadas em {fixed_files} arquivos!")
    print("⚠️  IMPORTANTE: Teste a aplicação antes de fazer commit!")

def main():
    print("🔍 Escaneando projeto para problemas narwhals DataFrame...")
    
    issues_found = scan_project()
    generate_report(issues_found)
    
    if issues_found and '--fix' in sys.argv:
        response = input("\n🤔 Deseja aplicar correções automáticas? (s/N): ")
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            auto_fix_issues(issues_found)
        else:
            print("❌ Correções não aplicadas.")
    elif issues_found:
        print("\n💡 Para aplicar correções automáticas, execute:")
        print("   python fix_narwhals_dataframes.py --fix")

if __name__ == "__main__":
    main() 