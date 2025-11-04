# app.py — Dashboard minimal d'histogrammes Strava GPX
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="GPX Dashboard", layout="wide")

# ---------- 1️⃣ Chargement des données ----------
@st.cache_data
def load_data():
    path_enriched = "data/dataset_enriched.csv"
    path_raw = "data/dataset.csv"
    path = path_enriched if os.path.exists(path_enriched) else path_raw

    df = pd.read_csv(path)

    # Nettoyage basique
    for c in ["distance_m", "dplus_cum_m"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Une ligne = une trace (distance max, D+ max)
    if "dplus_cum_m" in df.columns:
        traces = (
            df.groupby(["file_name", "activity_type"], dropna=False)
              .agg(distance_m=("distance_m", "max"),
                   dplus_m=("dplus_cum_m", "max"))
              .reset_index()
        )
    else:
        traces = (
            df.groupby(["file_name", "activity_type"], dropna=False)
              .agg(distance_m=("distance_m", "max"))
              .assign(dplus_m=0.0)
              .reset_index()
        )

    traces["distance_km"] = traces["distance_m"] / 1000.0

    # Types d’activités simplifiés
    short_map = {
        "Ride": "Road", "VirtualRide": "Virtual", "GravelRide": "Gravel",
        "MountainBikeRide": "MTB", "Run": "Run", "TrailRun": "Trail",
        "Walk": "Walk", "Hike": "Hike", "EBikeRide": "E-Bike"
    }
    traces["activity_short"] = traces["activity_type"].map(short_map)\
        .fillna(traces["activity_type"].fillna("Other"))

    return traces, path


traces, source_path = load_data()
n_traces = len(traces)

st.caption(f"Source : `{source_path}` • {n_traces} traces")

# ---------- 2️⃣ Histogrammes ----------
col1, col2 = st.columns(2)

# Distances
fig_dist = px.histogram(
    traces, x="distance_km", nbins=30,
    title=f"Distances (km) — {n_traces} traces",
    labels={"distance_km": "Distance (km)"}
)
col1.plotly_chart(fig_dist, width="stretch")

# Dénivelé positif
fig_dplus = px.histogram(
    traces, x="dplus_m", nbins=30,
    title=f"Dénivelé positif (m) — {n_traces} traces",
    labels={"dplus_m": "D+ (m)"}
)
col2.plotly_chart(fig_dplus, width="stretch")

# Répartition des activités
counts = traces["activity_short"].replace("", np.nan).dropna().value_counts()
if counts.sum() > 0:
    fig_act = px.bar(
        counts.sort_values(ascending=False),
        title=f"Répartition des activités — {n_traces} traces",
        labels={"index": "Type", "value": "Nombre de traces"}
    )
    st.plotly_chart(fig_act, width="stretch")
else:
    st.info("Aucun type d’activité disponible dans le dataset.")
