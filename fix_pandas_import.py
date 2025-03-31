"""
Script para corrigir o erro de importação do pandas no arquivo produtividade.py
"""
import re

# Caminho para o arquivo
arquivo = "views/cartorio/produtividade.py"

# Ler o conteúdo do arquivo
with open(arquivo, "r", encoding="utf-8") as f:
    conteudo = f.read()

# 1. Remover a importação local de pandas dentro da função
conteudo_sem_import_local = re.sub(
    r'import pandas as pd  # Adicionar importação no topo se necessário', 
    '# pandas já importado no início do arquivo', 
    conteudo
)

# 2. Verificar se já existe uma importação de pandas no início do arquivo
primeiras_linhas = '\n'.join(conteudo_sem_import_local.split('\n')[0:20])
if not re.search(r'import pandas as pd', primeiras_linhas):
    # Se não existir, adicionar a importação no início do arquivo
    linhas = conteudo_sem_import_local.split('\n')
    linhas.insert(0, "import pandas as pd  # Importação adicionada automaticamente")
    conteudo_final = '\n'.join(linhas)
else:
    conteudo_final = conteudo_sem_import_local

# Escrever o conteúdo modificado de volta ao arquivo
with open(arquivo, "w", encoding="utf-8") as f:
    f.write(conteudo_final)

print(f"Arquivo {arquivo} atualizado com sucesso!")
print("Importação do pandas corrigida.") 