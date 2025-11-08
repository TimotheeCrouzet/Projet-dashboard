# scripts/get_data.py
"""
Télécharge les données brutes (GPX) depuis la release GitHub
et les stocke dans data/raw/, sans modification.
"""

import os
import urllib.request
import zipfile

URL = "https://github.com/TimotheeCrouzet/Projet-dashboard/releases/download/v1.0.3/gpx.zip"

# Dossier de destination
RAW_DIR = os.path.join("data", "raw")
ZIP_PATH = os.path.join("data", "traces_strava.zip")

def download_file(url, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print(f"Téléchargement depuis : {url}")
    urllib.request.urlretrieve(url, out_path)
    print(f"Fichier enregistré : {out_path}")

def extract_zip(zip_path, dest_dir):
    print(f"Décompression de {zip_path} → {dest_dir}")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest_dir)
    print("Extraction terminée ")

def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    download_file(URL, ZIP_PATH)
    extract_zip(ZIP_PATH, RAW_DIR)
    print("Les données brutes sont prêtes dans data/raw/")

if __name__ == "__main__":
    main()
