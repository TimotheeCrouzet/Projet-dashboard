# app.py — Dashboard 
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from scripts.data_utils import load_data, preparation

#--Configuration de la page Streamlit--
st.set_page_config(page_title="Projet Dashboard", layout="wide")
st.title("Projet Dashboard - Analyse des Activités Sportives")

@st.cache_data(show_spinner=False)
def cached_preparation():
    return preparation()


(summary, activity_available, distance_min, distance_max, 
 distance_total, total_traces, dplus_min, dplus_max, 
 dplus_total, duration_heures) = cached_preparation()

selected_activities = st.sidebar.multiselect(
    "type d'activité", 
    activity_available, 
    default=activity_available, 
    key="activity_filter")

distance_range = st.sidebar.slider(
    "distance (km)", 
    distance_min, 
    distance_max, 
    value = (distance_min, distance_max),
    key="distance_filter")

dplus_range = st.sidebar.slider(
    "dénivelé positif (m)", 
    dplus_min, 
    dplus_max, 
    (dplus_min, dplus_max), 
    key="dplus_filter")

time_range = st.sidebar.slider(
    "durée (heures)", 
    min_value=float(duration_heures.min()), 
    max_value=float(duration_heures.max()), 
    value=(float(duration_heures.min()), float(duration_heures.max())), 
    step=0.5,
    key="time_filter")

#Filtrage des données selon les sélections
mask = (
    (summary["activity_type"].isin(selected_activities)) &
    (summary["total_distance_km"] >= distance_range[0]) &
    (summary["total_distance_km"] <= distance_range[1]) &
    (summary["total_dplus_m"] >= dplus_range[0]) &
    (summary["total_dplus_m"] <= dplus_range[1]) &
    (summary["duration_heures"] >= time_range[0]) &
    (summary["duration_heures"] <= time_range[1])
)  


filtered_summary = summary[mask]

if filtered_summary.empty:
    st.info("Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

#Affiche une vue d''ensemble des KPIs
st.subheader("Vues d'ensemble")
kpi_cols = st.columns(4)
kpi_cols[0].metric("Traces", f"{len(filtered_summary)}")
kpi_cols[1].metric("Distance totale (km)", f"{filtered_summary['total_distance_km'].sum():.1f}")
kpi_cols[2].metric("D+ total (m)", f"{filtered_summary['total_dplus_m'].sum():.0f}")
kpi_cols[3].metric("Durée totale (h)", f"{filtered_summary['duration_heures'].sum():.1f}")

st.subheader("Répartition des types d'activités")

#---camebert de répartition des types d'activités---
activity_counts = ( 
    filtered_summary["activity_type"]
    .fillna("Inconnu")
    .value_counts()
    .reset_index(name="count")
    .rename(columns={"index": "activity_type"})
    )

fig_pie = px.pie(
    data_frame = activity_counts, 
    names="activity_type", 
    values="count",
    title="Répartition des types d'activités",
    color_discrete_sequence=px.colors.qualitative.Set2,
    hole=0,
)
st.plotly_chart(fig_pie, width='stretch')

# ---Histogramme des distances et D+---
st.subheader("Exploration des distances et dénivelés")
col1, col2 = st.columns(2)
with col1:
    fig_dist = px.histogram(
        filtered_summary, 
        x="total_distance_km", 
        nbins=30,
        title="Distribution des distances (km)",
        labels={"total_distance_km": "Distance (km)"},
        color_discrete_sequence=["#636EFA"],
    )
    st.plotly_chart(fig_dist, width='stretch')
with col2:
    fig_dplus = px.histogram(
        filtered_summary, 
        x="total_dplus_m", 
        nbins=30,
        title="Distribution du dénivelé positif (m)",
        labels={"total_dplus_m": "D+ (m)"},
        color_discrete_sequence=["#EF553B"],
    )
    st.plotly_chart(fig_dplus, width='stretch')

#---Scatter plot Distance vs D+---
st.subheader("Distance vs D+")
fig_scatter = px.scatter(
    filtered_summary, 
    x="total_distance_km", 
    y="total_dplus_m",
    color="activity_type",
    labels={
        "total_distance_km": "Distance (km)",
        "total_dplus_m": "D+ (m)", 
        "activity_type": "Type d'activité"
    },
    title="Distance vs D+",
)
st.plotly_chart(fig_scatter, width='stretch')



