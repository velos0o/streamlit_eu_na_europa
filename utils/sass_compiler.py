import os
import sass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class SassCompiler(FileSystemEventHandler):
    def __init__(self, sass_dir, css_dir):
        self.sass_dir = sass_dir
        self.css_dir = css_dir
        
    def compile_sass(self):
        """Compila todos os arquivos SASS/SCSS para CSS."""
        try:
            # Compilar arquivo principal
            main_scss = os.path.join(self.sass_dir, 'main.scss')
            if os.path.exists(main_scss):
                css = sass.compile(
                    filename=main_scss,
                    output_style='compressed',
                    include_paths=[self.sass_dir]
                )
                
                # Criar diretório CSS se não existir
                os.makedirs(self.css_dir, exist_ok=True)
                
                # Salvar CSS compilado
                css_file = os.path.join(self.css_dir, 'main.css')
                with open(css_file, 'w', encoding='utf-8') as f:
                    f.write(css)
                    
                print(f"✅ SASS compilado com sucesso: {css_file}")
            else:
                print(f"❌ Arquivo principal não encontrado: {main_scss}")
                
        except sass.CompileError as e:
            print(f"❌ Erro ao compilar SASS: {str(e)}")
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
    
    def on_modified(self, event):
        """Chamado quando um arquivo é modificado."""
        if not event.is_directory and event.src_path.endswith(('.scss', '.sass')):
            print(f"🔄 Arquivo modificado: {event.src_path}")
            self.compile_sass()

def watch_sass(sass_dir, css_dir):
    """Inicia o observador para recompilar quando arquivos SASS forem modificados."""
    compiler = SassCompiler(sass_dir, css_dir)
    
    # Compilação inicial
    compiler.compile_sass()
    
    # Configurar observador
    observer = Observer()
    observer.schedule(compiler, sass_dir, recursive=True)
    observer.start()
    
    print(f"👀 Observando mudanças em: {sass_dir}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n⏹️ Observador interrompido")
    
    observer.join()

if __name__ == '__main__':
    # Caminhos relativos ao diretório do projeto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SASS_DIR = os.path.join(BASE_DIR, 'assets', 'styles', 'scss')
    CSS_DIR = os.path.join(BASE_DIR, 'assets', 'styles', 'css')
    
    watch_sass(SASS_DIR, CSS_DIR) 