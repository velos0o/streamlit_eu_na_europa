"""
Script para remover o parâmetro autosize_columns das chamadas st.dataframe() no arquivo produtividade.py
"""
import re

# Caminho para o arquivo
arquivo = "views/cartorio/produtividade.py"

# Ler o conteúdo do arquivo
with open(arquivo, "r", encoding="utf-8") as f:
    conteudo = f.read()

# Expressão regular para encontrar o parâmetro autosize_columns
# Captura tanto "autosize_columns=True" quanto "autosize_columns=False"
padrao = r',\s*autosize_columns\s*=\s*(True|False)'

# Substituir removendo o parâmetro
conteudo_corrigido = re.sub(padrao, '', conteudo)

# Escrever o conteúdo modificado de volta ao arquivo
with open(arquivo, "w", encoding="utf-8") as f:
    f.write(conteudo_corrigido)

print(f"Arquivo {arquivo} atualizado com sucesso!")
print("Todas as chamadas st.dataframe() com o parâmetro 'autosize_columns' foram corrigidas.") 