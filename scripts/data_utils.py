import os
import pandas as pd
import numpy as np


INPUT_CSV = "data/dataset_enriched.csv"


def load_data():

    """Charge et résume les données d'activités sportives."""
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Fichier introuvable : {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)

    summary = df.groupby(["file_name", "track_id"], as_index=False).agg(
        total_distance_m=("distance_m", "max"),
        total_dplus_m=("dplus_cum_m", "max"),
        activity_type= ("activity_short" , "first"),
        time_debut = ("time", "min"),
        time_fin = ("time", "max"),
        lat_start=("lat", "first"),
        lon_start=("lon", "first"),) 
    
    summary["total_distance_km"] = summary["total_distance_m"] / 1000

    return summary


def preparation():
    summary = load_data()

    activity_available = summary["activity_type"].unique().tolist()
    distance_min = float(summary["total_distance_km"].min())
    distance_max = float(summary["total_distance_km"].max()) + 1
    distance_total = float(summary["total_distance_km"].sum())
    total_traces = int(len(summary))
    dplus_min = float(summary["total_dplus_m"].min())
    dplus_max = float(summary["total_dplus_m"].max()) + 1
    dplus_total = float(summary["total_dplus_m"].sum())

    #Calcul du temps des randonnées
    duration = pd.to_datetime(summary["time_fin"])-pd.to_datetime(summary["time_debut"])
    duration_heures = duration.dt.total_seconds() / 3600
    summary["duration_heures"] = duration_heures

    
    return (summary, activity_available, distance_min, distance_max, 
            distance_total, total_traces, dplus_min, dplus_max, dplus_total, duration_heures)

if __name__ == "__main__":
    summary = load_data()
    print(
        summary["activity_type"]
          .value_counts()
          .fillna("Inconnu")
          .reset_index()
    )
