#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
enrich_dataset.py
-----------------
À partir de data/dataset.csv (points bruts), produit data/dataset_enriched.csv
avec :
- altitude lissée (filtre médian)
- dplus_step / dplus_cum avec epsilon anti-bruit
- distance_step
- temps relatif (time_s) et moving_time_s (pauses exclues)
- vitesse lissée
- pente locale (slope_pct) calculée sur ~SLOPE_WINDOW_M
- id de trace (track_id) et index de point (point_idx)
- activité courte (activity_short) et date locale
"""

import os
import numpy as np
import pandas as pd

# ============================
# Paramètres principaux
# ============================

INPUT_CSV = os.path.join("data", "dataset.csv")
OUTPUT_CSV = os.path.join("data", "dataset_enriched.csv")

ALT_WINDOW = 7          # fenêtre du filtre médian (impair recommandé : 5,7,9)
DPLUS_EPS = 0.8         # seuil (m) pour compter une montée
SLOPE_WINDOW_M = 40.0   # distance (m) pour calculer la pente locale
MOVING_SPEED_MIN = 1.0  # km/h : en-dessous, on considère "pause"
MAX_STEP_JUMP_M = 200.0 # filtre anti-saut GPS entre deux points

# ============================
# Chargement & préparation
# ============================

if not os.path.exists(INPUT_CSV):
    raise FileNotFoundError(f"Fichier introuvable : {INPUT_CSV}")

print(f"Chargement : {INPUT_CSV}")
df = pd.read_csv(INPUT_CSV)

# Types
df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
for col in ["lat", "lon", "altitude_m", "distance_m", "speed_kmh", "dplus_m_cum"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Tri chronologique par trace
df.sort_values(["file_name", "time"], inplace=True, kind="mergesort")
df.reset_index(drop=True, inplace=True)

# Identifiants de trace et index de point
df["track_id"] = df.groupby("file_name").ngroup()
df["point_idx"] = df.groupby("track_id").cumcount()

# ============================
# Lissage altitude (médian)
# ============================

def median_filter_series(s: pd.Series, window: int) -> pd.Series:
    """Filtre médian glissant centré, bords gérés (min_periods=1)."""
    if window is None or window < 3:
        return s
    # impose impair
    w = window if window % 2 == 1 else window + 1
    return s.rolling(window=w, center=True, min_periods=1).median()

def enrich_group(g: pd.DataFrame) -> pd.DataFrame:
    """
    Enrichit un groupe (une trace) :
    - altitude_smooth_m
    - distance_step_m
    - dplus_step_m / dplus_cum_m (à partir de alt lissée)
    - time_s / moving_time_s
    - speed_smooth_kmh
    - slope_pct (sur ~SLOPE_WINDOW_M)
    """
    g = g.copy()

    # --- altitude lissée ---
    g["altitude_smooth_m"] = median_filter_series(g["altitude_m"], ALT_WINDOW)

    # --- distance step ---
    # On part de la distance cumulée fournie (distance_m).
    g["distance_step_m"] = g["distance_m"].diff().clip(lower=0)
    # filtre anti-saut GPS (ex: téléportation)
    g.loc[g["distance_step_m"] > MAX_STEP_JUMP_M, "distance_step_m"] = 0.0

    # --- D+ step & cum (avec epsilon) ---
    dalti = g["altitude_smooth_m"].diff()
    # seuls les gains > epsilon comptent
    g["dplus_step_m"] = dalti.where(dalti > DPLUS_EPS, 0.0).fillna(0.0)
    g["dplus_cum_m"] = g["dplus_step_m"].cumsum()

    # --- temps relatif (s) ---
    if g["time"].notna().sum() >= 2:
        t0 = g["time"].iloc[0]
        g["time_s"] = (g["time"] - t0).dt.total_seconds()
    else:
        # fallback si time manquant : index comme proxy
        g["time_s"] = np.arange(len(g), dtype=float)

    # --- moving_time_s (ne cumule que si speed_kmh > seuil) ---
    # si speed_kmh manquant, on dérive de distance_step_m / dt
    spd = g["speed_kmh"].copy()
    # complétion naïve des vitesses manquantes si possible
    dt = g["time_s"].diff().fillna(0.0)
    with np.errstate(divide='ignore', invalid='ignore'):
        est_speed = (g["distance_step_m"] / dt.replace(0, np.nan)) * 3.6
    spd = spd.fillna(est_speed)

    moving_mask = spd > MOVING_SPEED_MIN
    # on cumule dt uniquement quand on bouge
    g["moving_time_s"] = (dt.where(moving_mask, 0.0)).cumsum()

    # --- vitesse lissée (moyenne glissante simple sur 7 points) ---
    g["speed_smooth_kmh"] = spd.rolling(window=7, min_periods=1, center=True).mean()

    # --- pente locale (%) sur ~SLOPE_WINDOW_M ---
    # On utilise la distance cumulée et l'altitude lissée.
    dist = g["distance_m"].to_numpy(dtype=float)
    alt = g["altitude_smooth_m"].to_numpy(dtype=float)

    # indices j tels que dist[j] - dist[i] >= window
    # on pré-alloue le résultat
    slope = np.zeros(len(g), dtype=float)
    # utilisation de searchsorted pour trouver j rapidement
    # dist doit être non décroissante (assuré par le tri + clip)
    for i in range(len(g)):
        target = dist[i] + SLOPE_WINDOW_M
        j = np.searchsorted(dist, target, side="left")
        if j >= len(g):
            j = len(g) - 1
        dd = dist[j] - dist[i]
        dz = alt[j] - alt[i]
        slope[i] = (dz / dd * 100.0) if dd > 0 else 0.0

    g["slope_pct"] = slope

    return g

# Appliquer l’enrichissement par trace
df = df.groupby("track_id", group_keys=False).apply(enrich_group)

# ============================
# Normalisation activité & date
# ============================

type_map = {
    "Ride": "Road",
    "VirtualRide": "Virtual",
    "GravelRide": "Gravel",
    "MountainBikeRide": "MTB",
    "Run": "Run",
    "TrailRun": "Trail",
    "Walk": "Walk",
    "Hike": "Hike",
    "EBikeRide": "E-Bike",
}
df["activity_short"] = df["activity_type"].map(type_map).fillna(df["activity_type"].fillna("Other"))

# date locale (Europe/Paris) si time dispo
if "time" in df.columns:
    try:
        df["date"] = df["time"].dt.tz_convert("Europe/Paris").dt.date
    except Exception:
        df["date"] = pd.NaT

# ============================
# Sauvegarde
# ============================

os.makedirs("data", exist_ok=True)
df.to_csv(OUTPUT_CSV, index=False)
print(df.head())
print(f" Enrichi → {OUTPUT_CSV}")
print("Colonnes disponibles :", ", ".join(df.columns))
