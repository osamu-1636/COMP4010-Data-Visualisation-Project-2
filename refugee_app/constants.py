"""Project-wide constants for the forced migration Shiny dashboard."""
from __future__ import annotations

INK = "#111827"
MUTED = "#64748b"
PAPER = "#f7f1e8"
CARD = "#fffdf8"
BLUE = "#2f66c5"
ORANGE = "#df7a26"
GREEN = "#6f9166"
PURPLE = "#8064b8"
RED = "#c2414b"
GOLD = "#d99a2b"
GRID = "rgba(17,24,39,.12)"

CROSS_BORDER_TYPES = ["Refugees", "Asylum-seekers", "Others of concern"]
ACTIVE_FORCED_TYPES = ["Refugees", "Asylum-seekers", "IDPs", "Others of concern"]

CRISIS_ORIGIN = {
    "All Crises": None,
    "Syrian Civil War": "Syrian Arab Republic",
    "Afghanistan displacement": "Afghanistan",
    "South Sudan crisis": "South Sudan",
    "Iraq conflict": "Iraq",
    "Somalia crisis": "Somalia",
}

CRISIS_EVENTS = {
    "Syrian Civil War": [
        (2011, "Conflict begins"),
        (2012, "Mass displacement intensifies"),
        (2015, "Major outflow to Europe"),
        (2016, "Regional hosting burden peaks in the dataset"),
    ],
    "Afghanistan displacement": [
        (1979, "Soviet invasion and first major displacement wave"),
        (1996, "Taliban rule"),
        (2001, "War and renewed displacement"),
        (2015, "Long-running cross-border displacement remains visible"),
    ],
    "South Sudan crisis": [(2011, "Independence"), (2013, "Civil conflict escalates"), (2016, "Large regional displacement burden")],
    "Iraq conflict": [(2003, "War and large-scale displacement"), (2006, "Sectarian violence intensifies"), (2014, "ISIS-related displacement")],
    "Somalia crisis": [(1991, "State collapse and civil war"), (2011, "Famine and conflict"), (2016, "Long-term regional displacement")],
}

# Approximate centroids for route-line storytelling only; not for official distance calculation.
CENTROIDS = {
    "Afghanistan": (33.94, 67.71), "Algeria": (28.03, 1.66), "Australia": (-25.27, 133.78),
    "Austria": (47.52, 14.55), "Bangladesh": (23.68, 90.36), "Belgium": (50.50, 4.47),
    "Brazil": (-14.24, -51.93), "Burundi": (-3.37, 29.92), "Cameroon": (7.37, 12.35),
    "Canada": (56.13, -106.35), "Central African Republic": (6.61, 20.94), "Chad": (15.45, 18.73),
    "China": (35.86, 104.20), "Colombia": (4.57, -74.30), "Democratic Republic of the Congo": (-4.04, 21.76),
    "Egypt": (26.82, 30.80), "Eritrea": (15.18, 39.78), "Ethiopia": (9.15, 40.49),
    "France": (46.23, 2.21), "Germany": (51.17, 10.45), "Greece": (39.07, 21.82),
    "India": (20.59, 78.96), "Iran": (32.43, 53.69), "Iraq": (33.22, 43.68),
    "Italy": (41.87, 12.57), "Jordan": (30.59, 36.24), "Kenya": (-0.02, 37.91),
    "Lebanon": (33.85, 35.86), "Liberia": (6.43, -9.43), "Malaysia": (4.21, 101.98),
    "Myanmar": (21.92, 95.96), "Netherlands": (52.13, 5.29), "Pakistan": (30.38, 69.35),
    "Russia": (61.52, 105.32), "Rwanda": (-1.94, 29.87), "Somalia": (5.15, 46.20),
    "South Africa": (-30.56, 22.94), "South Sudan": (6.88, 31.31), "Spain": (40.46, -3.75),
    "Sri Lanka": (7.87, 80.77), "Sudan": (12.86, 30.22), "Sweden": (60.13, 18.64),
    "Switzerland": (46.82, 8.23), "Syrian Arab Republic": (34.80, 38.99), "Thailand": (15.87, 100.99),
    "Turkey": (38.96, 35.24), "Uganda": (1.37, 32.29), "Ukraine": (48.38, 31.17),
    "United Kingdom": (55.38, -3.44), "United Republic of Tanzania": (-6.37, 34.89),
    "United States": (37.09, -95.71), "Venezuela": (6.42, -66.59), "Yemen": (15.55, 48.52),
    "Zambia": (-13.13, 27.85), "Zimbabwe": (-19.02, 29.15),
}
