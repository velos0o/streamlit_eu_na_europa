import sass
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class SassCompiler(FileSystemEventHandler):
    def __init__(self):
        self.scss_dir = 'assets/styles/scss'
        self.css_dir = 'assets/styles/css'
        
        # Criar diretório CSS se não existir
        if not os.path.exists(self.css_dir):
            os.makedirs(self.css_dir)
    
    def compile_sass(self):
        try:
            # Compilar main.scss para main.css
            scss_path = os.path.join(self.scss_dir, 'main.scss')
            css_path = os.path.join(self.css_dir, 'main.css')
            
            if os.path.exists(scss_path):
                css = sass.compile(filename=scss_path)
                with open(css_path, 'w', encoding='utf-8') as f:
                    f.write(css)
                print(f'✅ SCSS compilado com sucesso: {css_path}')
            else:
                print(f'❌ Arquivo não encontrado: {scss_path}')
        except Exception as e:
            print(f'❌ Erro ao compilar SCSS: {str(e)}')
    
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