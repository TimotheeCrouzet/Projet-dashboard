"""
Télécharge l'archive gpx.zip depuis la release GitHub
et extrait toutes les traces .gpx dans data/raw/gpx/.
"""

import os
import io
import zipfile
import requests
import certifi
from tqdm import tqdm

URL = "https://github.com/TimotheeCrouzet/Projet-dashboard/releases/download/v1.0.3/gpx.zip"
DEST_DIR = os.path.join("data", "raw", "gpx") 

def download_file(url: str) -> bytes:
    """Télécharge une archive ZIP depuis une URL avec barre de progression."""
    print("Téléchargement de l'archive depuis la release GitHub...")

    with requests.get(url, stream=True, timeout=60, verify=certifi.where()) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        data = io.BytesIO()

        with tqdm(
            total=total if total > 0 else None,
            unit="B", unit_scale=True, unit_divisor=1024,
            desc=os.path.basename(url),
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    data.write(chunk)
                    if total:  # si Content-Length connu
                        bar.update(len(chunk))

    print("Archive téléchargée en mémoire.")
    return data.getvalue()

def extract_gpx(zip_data: bytes, dest_dir: str) -> None:
    """Extrait toutes les traces .gpx d'une archive ZIP vers dest_dir."""
    os.makedirs(dest_dir, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        gpx_files = [name for name in z.namelist() if name.lower().endswith(".gpx")]

        for name in tqdm(gpx_files, desc="Extraction des fichiers", unit="fichier"):
            out_path = os.path.join(dest_dir, os.path.basename(name))
            with z.open(name) as src, open(out_path, "wb") as dst:
                dst.write(src.read())

    print(f"{len(gpx_files)} fichiers GPX extraits dans {dest_dir}")

def main():
    zip_data = download_file(URL)
    extract_gpx(zip_data, DEST_DIR)
    print("Les données brutes sont prêtes dans data/raw/gpx/")

if __name__ == "__main__":
    main()
