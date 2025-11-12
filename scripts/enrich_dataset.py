#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
enrich_dataset.py
-----------------
À partir de data/dataset.csv (points bruts), produit data/dataset_enriched.csv
"""

import os
import numpy as np
import pandas as pd
from tqdm.auto import tqdm 
tqdm.pandas(desc=" Enrichissement")  

#---Paramètres principaux---

INPUT_CSV = os.path.join("data", "dataset.csv")
OUTPUT_CSV = os.path.join("data", "dataset_enriched.csv")

ALT_WINDOW = 7
DPLUS_EPS = 0.8
MAX_STEP_JUMP_M = 200.0


#---Chargement & préparation---
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


#---Lissage altitude pour éviter des D+ faussés---
def median_filter_series(s: pd.Series, window: int) -> pd.Series:
    if window is None or window < 3:
        return s
    w = window if window % 2 == 1 else window + 1
    return s.rolling(window=w, center=True, min_periods=1).median()

def enrich_group(g: pd.DataFrame) -> pd.DataFrame:
    g = g.copy()

    # --- altitude lissée ---
    g["altitude_smooth_m"] = median_filter_series(g["altitude_m"], ALT_WINDOW)

    # --- distance step ---
    g["distance_step_m"] = g["distance_m"].diff().clip(lower=0)
    g.loc[g["distance_step_m"] > MAX_STEP_JUMP_M, "distance_step_m"] = 0.0

    # --- D+ step & cum (avec epsilon) ---
    dalti = g["altitude_smooth_m"].diff()
    g["dplus_step_m"] = dalti.where(dalti > DPLUS_EPS, 0.0).fillna(0.0)
    g["dplus_cum_m"] = g["dplus_step_m"].cumsum()

    # --- temps relatif (s) ---
    if g["time"].notna().sum() >= 2:
        t0 = g["time"].iloc[0]
        g["time_s"] = (g["time"] - t0).dt.total_seconds()
    else:
        g["time_s"] = np.arange(len(g), dtype=float)
    return g


#---Appliquer l’enrichissement (avec barre tqdm)---

df = df.groupby("track_id", group_keys=False).progress_apply(enrich_group)


#---Normalisation activité & date---

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

# Conversion date 
if str(df["time"].dtype) == "datetime64[ns]":
    df["time"] = df["time"].dt.tz_localize("UTC", errors="coerce")
df["date"] = df["time"].dt.tz_convert("Europe/Paris").dt.date


#---Sauvegarde---

os.makedirs("data", exist_ok=True)
df.to_csv(OUTPUT_CSV, index=False)
print(df.head())
print(f" Enrichi → {OUTPUT_CSV}")
print("Colonnes disponibles :", ", ".join(df.columns))
