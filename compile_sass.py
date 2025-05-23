import subprocess
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import sys

# Obtém o diretório absoluto onde o script está localizado
script_dir = os.path.dirname(os.path.abspath(__file__))
# Assume que a pasta 'assets' está no mesmo nível que o script
base_dir = script_dir # Diretório pai é onde está 'assets'

class SassCompiler(FileSystemEventHandler):
    def __init__(self):
        # Usa caminhos absolutos baseados na localização do script
        self.scss_dir = os.path.join(base_dir, 'assets', 'styles', 'scss')
        self.css_dir = os.path.join(base_dir, 'assets', 'styles', 'css')
        
        print(f"[Debug] SCSS Dir: {self.scss_dir}")
        print(f"[Debug] CSS Dir: {self.css_dir}")
        
        # Criar diretório CSS se não existir
        if not os.path.exists(self.css_dir):
            os.makedirs(self.css_dir)
    
    def check_sass_installation(self):
        """Verifica se o sass está instalado"""
        try:
            result = subprocess.run(['sass', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Dart Sass encontrado: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        print("❌ Dart Sass não encontrado!")
        print("📥 Para instalar:")
        print("   npm install -g sass")
        print("   ou")
        print("   choco install sass (Windows)")
        print("   ou")
        print("   pip install libsass (fallback)")
        return False
    
    def compile_sass(self):
        try:
            # Compilar main.scss para main.css
            scss_path = os.path.join(self.scss_dir, 'main.scss')
            css_path = os.path.join(self.css_dir, 'main.css')
            map_path = os.path.join(self.css_dir, 'main.css.map')
            
            if not os.path.exists(scss_path):
                print(f'❌ Arquivo não encontrado: {scss_path}')
                return
            
            # Tentar usar Dart Sass primeiro
            if self.check_sass_installation():
                cmd = [
                    'sass',
                    scss_path,
                    css_path,
                    '--style=expanded',
                    '--source-map',
                    '--load-path=' + self.scss_dir
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f'✅ SCSS compilado com sucesso usando Dart Sass: {css_path}')
                    if result.stdout:
                        print(f"📋 Output: {result.stdout}")
                else:
                    print(f'❌ Erro no Dart Sass: {result.stderr}')
                    # Fallback para libsass
                    self.compile_with_libsass(scss_path, css_path)
            else:
                # Fallback para libsass
                self.compile_with_libsass(scss_path, css_path)
                
        except Exception as e:
            print(f'❌ Erro ao compilar SCSS: {str(e)}')
    
    def compile_with_libsass(self, scss_path, css_path):
        """Fallback usando libsass (suporte limitado a @use)"""
        try:
            import sass
            print("⚠️  Usando libsass como fallback (suporte limitado a @use)")
            
            css = sass.compile(
                filename=scss_path,
                include_paths=[self.scss_dir],
                output_style='expanded'
            )
            
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(css)
            print(f'✅ SCSS compilado com libsass: {css_path}')
            
        except ImportError:
            print("❌ libsass não encontrado. Instale com: pip install libsass")
        except Exception as e:
            print(f'❌ Erro no libsass: {str(e)}')
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.scss'):
            print(f'🔄 Arquivo modificado: {event.src_path}')
            self.compile_sass()

def main():
    compiler = SassCompiler()
    
    # Compilação inicial
    print('🚀 Iniciando compilação SCSS...')
    compiler.compile_sass()
    
    # Configurar observador para mudanças
    observer = Observer()
    observer.schedule(compiler, compiler.scss_dir, recursive=True)
    observer.start()
    
    print(f'👀 Observando mudanças em {compiler.scss_dir}...')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print('\n🛑 Observador parado')
    
    observer.join()

if __name__ == '__main__':
    main() 