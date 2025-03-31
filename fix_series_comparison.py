"""
Script para corrigir o erro de comparação de Series na função analisar_matriz_responsavel_data
"""
import re

# Caminho para o arquivo
arquivo = "views/cartorio/produtividade.py"

# Ler o conteúdo do arquivo
with open(arquivo, "r", encoding="utf-8") as f:
    conteudo = f.read()

# Localizar o trecho problemático e substituí-lo
# Padrão para encontrar: row_sum > 0
padrao = r'(row_sum = heatmap_norm\.loc\[idx\]\.sum\(\))\n(\s+)(if row_sum > 0:)'

# Substituição que converte row_sum para float
substituicao = r'\1\n\2# Garantir que row_sum é um valor escalar\n\2row_sum = float(row_sum) if not isinstance(row_sum, (list, tuple)) else float(row_sum[0])\n\2\3'

# Aplicar a substituição
conteudo_corrigido = re.sub(padrao, substituicao, conteudo)

# Escrever o conteúdo modificado de volta ao arquivo
with open(arquivo, "w", encoding="utf-8") as f:
    f.write(conteudo_corrigido)

print(f"Arquivo {arquivo} atualizado com sucesso!")
print("Correção da comparação de Series em analisar_matriz_responsavel_data aplicada.") 