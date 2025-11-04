# main.py
import subprocess
import sys

if __name__ == "__main__":
    # Lancer Streamlit sur app.py
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur.")
