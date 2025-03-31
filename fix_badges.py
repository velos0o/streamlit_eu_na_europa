"""
Script para corrigir badges no arquivo produtividade.py
"""
import re

# Caminho para o arquivo
arquivo = "views/cartorio/produtividade.py"

# Ler o conteúdo do arquivo
with open(arquivo, "r", encoding="utf-8") as f:
    conteudo = f.read()

# Expressão regular para encontrar st.badge() com o parâmetro variant
# Captura o texto dentro do parênteses e o parâmetro variant para substituir
padrao = r'st\.badge\((.*?),\s*variant=.*?\)'

# Substituir por st.badge() sem o parâmetro variant
conteudo_corrigido = re.sub(padrao, r'st.badge(\1)', conteudo)

# Escrever o conteúdo modificado de volta ao arquivo
with open(arquivo, "w", encoding="utf-8") as f:
    f.write(conteudo_corrigido)

print(f"Arquivo {arquivo} atualizado com sucesso!")
print("Todos os badges com parâmetro 'variant' foram corrigidos.") 