# generate_histos_final.py
import os
import pandas as pd
import matplotlib.pyplot as plt

OUTDIR = "outputs"
os.makedirs(OUTDIR, exist_ok=True)

# --------- 1) Charger et résumer par trace ---------
df = pd.read_csv("data/dataset.csv")

# 1 ligne = 1 trace (fichier)
summary = (
    df.groupby(["file_name", "activity_type"], as_index=False)
      .agg(distance_m=("distance_m", "max"),
           dplus_m=("dplus_m_cum", "max"))
)

# km pour la lisibilité
summary["distance_km"] = summary["distance_m"] / 1000

# (optionnel) couper quelques extrêmes pour des graphes lisibles
summary = summary[(summary["distance_km"] >= 0) & (summary["distance_km"] <= 300)]
summary = summary[(summary["dplus_m"] >= 0) & (summary["dplus_m"] <= 4000)]

# Nombre total de traces
n_traces = len(summary)

# --------- 2) Noms d’activités raccourcis ---------
short_map = {
    "Ride": "Road",
    "GravelRide": "Gravel",
    "MountainBikeRide": "MTB",
    "VirtualRide": "Virtual",
    "EBikeRide": "E-Bike",
    "Handcycle": "Hand",
    "Velomobile": "Velo",
    "Elliptical": "Ellip",
    "InlineSkate": "Skate",
    "NordicSki": "Ski",
    "BackcountrySki": "SkiBC",
    "AlpineSki": "SkiAlp",
    "Snowboard": "Snow",
    "Workout": "Workout",
    "Hike": "Hike",
    "Walk": "Walk",
    "Run": "Run",
    "TrailRun": "Trail",
    "Swim": "Swim",
}
summary["activity_short"] = summary["activity_type"].map(short_map).fillna(summary["activity_type"].fillna(""))

# ===================================================
# GRAPHE A — Distribution du D+ (par trace)
# ===================================================
plt.figure(figsize=(7,5))
plt.hist(summary["dplus_m"].dropna(), bins=30)
plt.title(f"Distribution du dénivelé positif (par trace) — {n_traces} traces")
plt.xlabel("D+ total (m)")
plt.ylabel("Nombre de traces")
plt.grid(True, axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "hist_dplus.png"), dpi=300, bbox_inches="tight")
plt.close()

# ===================================================
# GRAPHE B — Distribution des distances (par trace)
# ===================================================
plt.figure(figsize=(7,5))
plt.hist(summary["distance_km"].dropna(), bins=30)
plt.title(f"Distribution des distances (par trace) — {n_traces} traces")
plt.xlabel("Distance (km)")
plt.ylabel("Nombre de traces")
plt.grid(True, axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "hist_distance.png"), dpi=300, bbox_inches="tight")
plt.close()

# ===================================================
# GRAPHE C — Répartition des types d’activité (%)
# ===================================================
counts = summary["activity_short"].replace("", pd.NA).dropna().value_counts()
percent = (counts / counts.sum() * 100).sort_values(ascending=False)

plt.figure(figsize=(7,5))
plt.bar(percent.index, percent.values)
plt.title(f"Répartition des types d’activité — {n_traces} traces")
plt.xlabel("Type d’activité")
plt.ylabel("Part des traces (%)")
for i, v in enumerate(percent.values):
    plt.text(i, v + max(percent.values)*0.01, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
plt.grid(True, axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "bar_activity_percent.png"), dpi=300, bbox_inches="tight")
plt.close()

# ===================================================
# GRAPHE D — Boxplot des distances par type d’activité
# ===================================================
# Ordre des activités par médiane croissante de distance
order = (
    summary[summary["activity_short"] != ""]
    .groupby("activity_short")["distance_km"]
    .median()
    .sort_values()
    .index.tolist()
)

data = [summary.loc[summary["activity_short"] == a, "distance_km"].dropna().values for a in order]
labels = order

plt.figure(figsize=(9,5))
plt.boxplot(data, labels=labels, showfliers=False)
plt.title(f"Distance par type d’activité — {n_traces} traces")
plt.ylabel("Distance (km)")
plt.grid(True, axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "box_distance_by_activity.png"), dpi=300, bbox_inches="tight")
plt.close()

print(f" {n_traces} traces détectées")
print("Graphes enregistrés dans outputs :")
print(" - hist_dplus.png")
print(" - hist_distance.png")
print(" - bar_activity_percent.png")
print(" - box_distance_by_activity.png")
