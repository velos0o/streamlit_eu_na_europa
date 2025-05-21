import sass
import os
import sys
import glob

# Diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Caminhos para os diretórios
scss_dir = os.path.join(script_dir, 'assets', 'styles', 'scss')
css_dir = os.path.join(script_dir, 'assets', 'styles', 'css')

# Criar diretório CSS se não existir
if not os.path.exists(css_dir):
    os.makedirs(css_dir)

def compile_scss():
    """Compila o arquivo SCSS principal para CSS com logs detalhados"""
    try:
        print(f"Diretório SCSS: {scss_dir}")
        print(f"Diretório CSS: {css_dir}")
        
        # Listar todos os arquivos SCSS para verificação
        scss_files = glob.glob(os.path.join(scss_dir, '**', '*.scss'), recursive=True)
        print(f"Arquivos SCSS encontrados: {len(scss_files)}")
        for file in scss_files:
            print(f"  - {os.path.relpath(file, script_dir)}")
        
        # Verificar se o arquivo main.scss existe
        main_scss_path = os.path.join(scss_dir, 'main.scss')
        if not os.path.exists(main_scss_path):
            print(f"ERRO: Arquivo main.scss não encontrado em {main_scss_path}")
            return False
            
        # Verificar se o componente _producao_adm.scss existe
        producao_adm_scss_path = os.path.join(scss_dir, 'components', '_producao_adm.scss')
        if not os.path.exists(producao_adm_scss_path):
            print(f"ERRO: Arquivo _producao_adm.scss não encontrado em {producao_adm_scss_path}")
            return False
            
        print(f"Compilando {main_scss_path} para CSS...")
        
        # Verificar o conteúdo do main.scss
        with open(main_scss_path, 'r', encoding='utf-8') as f:
            main_scss_content = f.read()
            print(f"Conteúdo do main.scss: primeiras 200 caracteres")
            print(main_scss_content[:200] + "...")
            
            # Verificar se o arquivo _producao_adm.scss está importado no main.scss
            if 'components/producao_adm' not in main_scss_content:
                print("AVISO: _producao_adm.scss parece não estar importado no main.scss")
                
        # Compilar SCSS para CSS
        print("Iniciando compilação...")
        css_output = sass.compile(filename=main_scss_path, output_style='compressed')
        print(f"Compilação concluída! Tamanho do CSS: {len(css_output)} bytes")
        
        # Salvar no arquivo CSS
        css_path = os.path.join(css_dir, 'main.css')
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_output)
            
        print(f"✅ SCSS compilado com sucesso! Arquivo CSS salvo em: {css_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao compilar SCSS: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = compile_scss()
    sys.exit(0 if success else 1) 