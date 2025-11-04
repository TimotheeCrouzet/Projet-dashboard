import gpxpy
import gpxpy.gpx
import glob
import csv
import os

# Dossiers et fichiers
GPX_DIR = "data/raw/gpx"
OUT_CSV = "data/dataset.csv"

# Liste des fichiers GPX dans data/gpx/
gpx_files = sorted(glob.glob(os.path.join(GPX_DIR, "**", "*.gpx"), recursive=True))
print(f" {len(gpx_files)} fichiers GPX détectés (récursif) dans {GPX_DIR}")

# Vérification
if not gpx_files:
    print(" Aucun fichier GPX trouvé dans data/gpx/")
else:
    print(f" {len(gpx_files)} fichiers GPX détectés dans {GPX_DIR}")

# Création du CSV
with open(OUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "file_name", "activity_type", "lat", "lon", "altitude_m",
        "distance_m", "dplus_m_cum", "speed_kmh", "time"
    ])

    # Boucle sur chaque fichier GPX
    for file in gpx_files:
        with open(file, "r", encoding="utf-8") as gpx_file:
            gpx = gpxpy.parse(gpx_file)

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
                                d = point.distance_3d(previous_point) or 0.0
                                dist = d if (0.0 <= d < 200.0) else 0.0
                                cumulative_distance += dist
                            except:
                                dist = 0.0

                            # --- D+ ---
                            if alt is not None and previous_point.elevation is not None:
                                delta_e = float(alt) - float(previous_point.elevation)
                                if delta_e > 0:
                                    cumulative_dplus += delta_e

                        # --- Vitesse (extensions ou calculée) ---
                        speed_kmh = 0.0
                        if point.extensions:
                            for ext in point.extensions:
                                for child in ext:
                                    if 'velocity_smooth' in child.tag:
                                        try:
                                            v = float(child.text)
                                            speed_kmh = v * 3.6 if v < 50 else v
                                        except:
                                            pass
                        if speed_kmh == 0.0 and previous_point and time and previous_point.time:
                            try:
                                dt = (time - previous_point.time).total_seconds()
                                if dt > 0:
                                    speed_kmh = (dist / dt) * 3.6
                            except:
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

print(f" Dataset généré : {OUT_CSV}")
