"""
Script para corrigir o erro de conversão de Series para float na função analisar_matriz_responsavel_data
"""
import re

# Caminho para o arquivo
arquivo = "views/cartorio/produtividade.py"

# Ler o conteúdo do arquivo
with open(arquivo, "r", encoding="utf-8") as f:
    conteudo = f.read()

# Localizar o trecho problemático e substituí-lo
# Padrão para encontrar a linha problemática
padrao = r'(row_sum = heatmap_norm\.loc\[idx\]\.sum\(\))\n(\s+)# Garantir que row_sum é um valor escalar\n(\s+)(row_sum = float\(row_sum\) if not isinstance\(row_sum, \(list, tuple\)\) else float\(row_sum\[0\]\))'

# Substituição com método correto para converter Series para float
substituicao = r'\1\n\2# Garantir que row_sum é um valor escalar\n\2import pandas as pd  # Adicionar importação no topo se necessário\n\2if isinstance(row_sum, pd.Series):\n\2    # Se for uma pandas Series, pegar o primeiro valor como float\n\2    if len(row_sum) > 0:\n\2        row_sum = float(row_sum.iloc[0])\n\2    else:\n\2        row_sum = 0.0\n\2elif isinstance(row_sum, (list, tuple)):\n\2    # Se for lista ou tupla, pegar o primeiro elemento\n\2    row_sum = float(row_sum[0]) if row_sum else 0.0\n\2else:\n\2    # Caso seja um escalar\n\2    row_sum = float(row_sum)'

# Aplicar a substituição
conteudo_corrigido = re.sub(padrao, substituicao, conteudo)

# Escrever o conteúdo modificado de volta ao arquivo
with open(arquivo, "w", encoding="utf-8") as f:
    f.write(conteudo_corrigido)

print(f"Arquivo {arquivo} atualizado com sucesso!")
print("Correção da conversão de Series para float em analisar_matriz_responsavel_data aplicada.") 