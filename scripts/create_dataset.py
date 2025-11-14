import gpxpy
import gpxpy.gpx
import glob
import csv
import os
import re                   # pour normaliser les timestamps
from tqdm import tqdm 

# Dossiers et fichiers
GPX_DIR = "data/raw/gpx"
OUT_CSV = "data/dataset.csv"

# Liste des fichiers GPX
gpx_files = sorted(glob.glob(os.path.join(GPX_DIR, "**", "*.gpx"), recursive=True))
print(f" {len(gpx_files)} fichiers GPX détectés (récursif) dans {GPX_DIR}")
if not gpx_files:
    print(" Aucun fichier GPX trouvé dans data/raw/gpx/")
else:
    print(f" {len(gpx_files)} fichiers GPX détectés dans {GPX_DIR}")

# Création du CSV
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
with open(OUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "file_name", "activity_type", "lat", "lon", "altitude_m",
        "distance_m", "dplus_m_cum", "speed_kmh", "time"
    ])

    for file in tqdm(gpx_files, desc="Création du dataset", unit="fichier"):
        with open(file, "r", encoding="utf-8") as gpx_file:
            #conversion des timestamps
            content = gpx_file.read()
            content = re.sub(r"\+\d{2}:\d{2}Z", "Z", content)

            # Parse du texte normalisé
            gpx = gpxpy.parse(content)

            # Parcours des traces du fichier
            for track in gpx.tracks:
                activity_type = track.type or ""

                # Reset du cumul par trace
                cumulative_distance = 0.0
                cumulative_dplus = 0.0

                for segment in track.segments:
                    previous_point = None

                    for point in segment.points:
                        lat = point.latitude
                        lon = point.longitude
                        alt = point.elevation
                        time = point.time 
                        # --- Distance cumulée ---
                        dist = 0.0
                        if previous_point is not None:
                            try:
                                d = point.distance_2d(previous_point) or 0.0
                                dist = d if (0.0 <= d < 200.0) else 0.0
                                cumulative_distance += dist
                            except Exception:
                                dist = 0.0

                            # --- D+ ---
                            if alt is not None and previous_point.elevation is not None:
                                try:
                                    delta_e = float(alt) - float(previous_point.elevation)
                                    if delta_e > 0:
                                        cumulative_dplus += delta_e
                                except Exception:
                                    pass

                        # --- Vitesse (extensions ou calculée) --- (On ne s'en sert pas pour l'instant)
                        speed_kmh = 0.0
                        if point.extensions:
                            for ext in point.extensions:
                                for child in ext:
                                    if 'velocity_smooth' in child.tag:
                                        try:
                                            v = float(child.text)
                                            speed_kmh = v * 3.6 if v < 50 else v
                                        except Exception:
                                            pass
                        if speed_kmh == 0.0 and previous_point and time and previous_point.time:
                            try:
                                dt = (time - previous_point.time).total_seconds()
                                if dt > 0:
                                    speed_kmh = (dist / dt) * 3.6
                            except Exception:
                                pass

                        # --- Écriture CSV ---
                        writer.writerow([
                            os.path.basename(file),
                            activity_type,
                            lat,
                            lon,
                            round(alt, 2) if alt is not None else "",
                            round(cumulative_distance, 2),
                            round(cumulative_dplus, 2),
                            round(speed_kmh, 2),
                            time.isoformat() if time else ""
                        ])

                        previous_point = point

print(f"Dataset généré : {OUT_CSV}")
