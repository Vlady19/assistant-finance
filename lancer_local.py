"""Lance Streamlit avec une clé déjà conservée dans un .env externe si souhaité.

python lancer_local.py --env-file /chemin/vers/.env
Le secret est chargé en mémoire, pas copié dans les livrables.
Sans argument : .env local ou variable OPENAI_API_KEY ; le calcul local reste
accessible même sans clé.
"""
import argparse
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',type=Path)
    parser.add_argument('--port',type=int,default=8501)
    args=parser.parse_args()
    if args.env_file:
        if not args.env_file.is_file(): parser.error('Le fichier de configuration indiqué est absent.')
        load_dotenv(args.env_file,override=False)
    racine=Path(__file__).resolve().parent
    raise SystemExit(subprocess.call([sys.executable,'-m','streamlit','run',str(racine/'app_streamlit.py'),
        '--server.address','127.0.0.1','--server.port',str(args.port),'--server.headless','true',
        '--browser.gatherUsageStats','false'],cwd=racine))

if __name__=='__main__': main()
