"""
Instalador para a biblioteca streamlit-lottie.
Execute este arquivo para instalar a biblioteca necessária para as animações de carregamento.
"""

import subprocess
import sys
import os

def install_lottie():
    """Instala a biblioteca streamlit-lottie."""
    print("Instalando streamlit-lottie...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-lottie==0.0.5"])
        print("\n\n✅ Instalação bem-sucedida! ✅")
        print("A biblioteca streamlit-lottie foi instalada com sucesso.")
        print("Agora você pode ver as animações de carregamento no dashboard.")
        print("\nExecute o dashboard com: streamlit run main.py")
        return True
    except Exception as e:
        print(f"\n❌ Erro durante a instalação: {str(e)}")
        print("\nTente instalar manualmente com o comando:")
        print("pip install streamlit-lottie==0.0.5")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  Instalador da Biblioteca Streamlit-Lottie para Dashboard")
    print("=" * 60)
    print("\nEsta ferramenta instalará a biblioteca necessária para")
    print("exibir animações de carregamento no dashboard.")
    print("\nA instalação não afetará o funcionamento básico do dashboard,")
    print("que continuará funcionando mesmo sem esta biblioteca.")
    
    choice = input("\nDeseja prosseguir com a instalação? (s/n): ")
    
    if choice.lower() in ["s", "sim", "y", "yes"]:
        success = install_lottie()
        if success:
            # Perguntar se deseja executar o dashboard
            choice = input("\nDeseja executar o dashboard agora? (s/n): ")
            if choice.lower() in ["s", "sim", "y", "yes"]:
                # Executar o dashboard
                try:
                    print("\nIniciando o dashboard...")
                    subprocess.Popen([sys.executable, "-m", "streamlit", "run", "main.py"])
                except Exception as e:
                    print(f"\n❌ Erro ao iniciar o dashboard: {str(e)}")
                    print("\nTente iniciar manualmente com o comando:")
                    print("streamlit run main.py")
    else:
        print("\nInstalação cancelada. O dashboard continuará funcionando,")
        print("mas sem as animações de carregamento.")
    
    # Esperar input antes de fechar (se executado diretamente)
    if os.name == 'nt':  # Windows
        print("\nPressione qualquer tecla para sair...")
        input() 