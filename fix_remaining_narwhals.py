#!/usr/bin/env python3
"""
Script para corrigir automaticamente todos os usos restantes de st.dataframe, st.bar_chart, etc.
que ainda não foram corrigidos com ensure_pandas_df().
"""

import os
import re
from pathlib import Path

# Arquivos críticos que devem ser corrigidos primeiro
ARQUIVOS_CRITICOS = [
    'views/tickets.py',
    'views/ficha_familia.py', 
    'views/comune/visualization.py',
    'views/comune/comune_main.py',
    'views/cartorio_new/producao_adm.py',
    'views/cartorio_new/higienizacao_desempenho.py',
    'views/apresentacao/slides.py'
]

def has_ensure_pandas_import(filepath):
    """Verifica se o arquivo já tem o import do ensure_pandas_df"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return 'from utils.dataframe_utils import ensure_pandas_df' in content
    except:
        return False

def add_ensure_pandas_import(filepath):
    """Adiciona o import do ensure_pandas_df no arquivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Encontrar onde inserir o import (após os imports pandas/streamlit)
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import pandas') or line.strip().startswith('import streamlit'):
                insert_pos = i + 1
        
        # Verificar se já existe
        for line in lines:
            if 'from utils.dataframe_utils import ensure_pandas_df' in line:
                return True  # Já existe
        
        # Inserir o import
        new_line = "from utils.dataframe_utils import ensure_pandas_df\n"
        lines.insert(insert_pos, new_line)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ Import adicionado em: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar import em {filepath}: {e}")
        return False

def fix_dataframe_calls(filepath):
    """Corrige as chamadas st.dataframe() no arquivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern para encontrar st.dataframe( sem ensure_pandas_df
        pattern = r'st\.dataframe\(\s*([^,\)]+)'
        
        def replace_func(match):
            df_arg = match.group(1).strip()
            # Verifica se já está usando ensure_pandas_df
            if 'ensure_pandas_df(' in df_arg:
                return match.group(0)  # Não modifica se já está correto
            else:
                return f'st.dataframe(ensure_pandas_df({df_arg})'
        
        new_content = re.sub(pattern, replace_func, content)
        
        # Contar quantas mudanças foram feitas
        changes = len(re.findall(pattern, content)) - len(re.findall(pattern, new_content))
        
        if changes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ {changes} correções aplicadas em: {filepath}")
            return True
        else:
            print(f"ℹ️  Nenhuma correção necessária em: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao corrigir {filepath}: {e}")
        return False

def fix_chart_calls(filepath):
    """Corrige as chamadas st.bar_chart(), st.line_chart(), etc."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Patterns para diferentes tipos de gráficos
        chart_patterns = [
            r'st\.bar_chart\(\s*([^,\)]+)',
            r'st\.line_chart\(\s*([^,\)]+)',
            r'st\.scatter_chart\(\s*([^,\)]+)',
            r'st\.area_chart\(\s*([^,\)]+)'
        ]
        
        for pattern in chart_patterns:
            def replace_func(match):
                df_arg = match.group(1).strip()
                chart_func = match.group(0).split('(')[0]  # ex: st.bar_chart
                if 'ensure_pandas_df(' in df_arg:
                    return match.group(0)
                else:
                    return f'{chart_func}(ensure_pandas_df({df_arg})'
            
            content = re.sub(pattern, replace_func, content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Correções de gráficos aplicadas em: {filepath}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Erro ao corrigir gráficos em {filepath}: {e}")
        return False

def process_file(filepath):
    """Processa um arquivo completo"""
    print(f"\n🔧 Processando: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"❌ Arquivo não encontrado: {filepath}")
        return False
    
    success = True
    
    # Adicionar import se necessário
    if not has_ensure_pandas_import(filepath):
        success &= add_ensure_pandas_import(filepath)
    
    # Corrigir chamadas
    success &= fix_dataframe_calls(filepath)
    success &= fix_chart_calls(filepath)
    
    return success

def main():
    print("🚀 Iniciando correção automática dos arquivos restantes...")
    
    # Processar arquivos críticos primeiro
    print("\n📋 Processando arquivos críticos...")
    for arquivo in ARQUIVOS_CRITICOS:
        process_file(arquivo)
    
    print("\n✅ Correção concluída!")
    print("\n💡 Próximos passos:")
    print("1. Teste a aplicação localmente")
    print("2. Faça commit e push das mudanças")
    print("3. O Streamlit Community Cloud será atualizado automaticamente")

if __name__ == "__main__":
    main() 