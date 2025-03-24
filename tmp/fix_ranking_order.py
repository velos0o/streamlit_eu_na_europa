import os
import re

def replace_in_file(file_path, search_pattern, replacement):
    """
    Substitui um padrão específico em um arquivo.
    """
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        return False
    
    # Ler o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Verificar se o padrão existe no arquivo
    if not re.search(search_pattern, content):
        print(f"Padrão não encontrado em: {file_path}")
        return False
    
    # Substituir o padrão pelo novo texto
    new_content = re.sub(search_pattern, replacement, content)
    
    # Se não houve alterações, não precisa salvar
    if new_content == content:
        print(f"Nenhuma alteração necessária em: {file_path}")
        return False
    
    # Salvar as alterações
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print(f"Alterações realizadas em: {file_path}")
    return True

# Padrões de busca e substituição
search_pattern = r'# Ordenar por total descendente\s+display_df = display_df\.sort_values\(\'TOTAL\', ascending=False\)'
replacement = "# Ordenar por taxa de conclusão descendente (em vez de total)\n        display_df = display_df.sort_values('TAXA_CONCLUSAO', ascending=False)"

# Lista de arquivos para verificar
files_to_fix = [
    "../views/apresentacao/producao/status_responsavel.py",
    "../views/apresentacao/funcoes_slides.py",
    "../views/apresentacao_conclusoes.py"
]

# Contar quantos arquivos foram alterados
count_fixed = 0

# Processar cada arquivo
for file_path in files_to_fix:
    if replace_in_file(file_path, search_pattern, replacement):
        count_fixed += 1

print(f"\nTotal de {count_fixed} arquivo(s) corrigido(s).") 