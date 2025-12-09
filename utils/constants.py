"""
constants.py

Centralized global constants used across the application.
This file contains mappings, catalogues, and static configuration
values needed for feature engineering or geographic lookups.
"""

# ------------------------------------------------------------
# PARIS ARRONDISSEMENT MAPPINGS
# Used for one-hot encoding, heatmap visuals, and KPI calculations.
# ------------------------------------------------------------

# One-hot encoded model column names for each arrondissement
ARRONDISSEMENT_MAP = {
    1: "Arrondissement_1er",
    2: "Arrondissement_2e",
    3: "Arrondissement_3e",
    4: "Arrondissement_4e",
    5: "Arrondissement_5e",
    6: "Arrondissement_6e",
    7: "Arrondissement_7e",
    8: "Arrondissement_8e",
    9: "Arrondissement_9e",
    10: "Arrondissement_10e",
    11: "Arrondissement_11e",
    12: "Arrondissement_12e",
    13: "Arrondissement_13e",
    14: "Arrondissement_14e",
    15: "Arrondissement_15e",
    16: "Arrondissement_16e",
    17: "Arrondissement_17e",
    18: "Arrondissement_18e",
    19: "Arrondissement_19e",
    20: "Arrondissement_20e",
}

# Official INSEE 5-digit geographic codes, required by the GeoJSON file
INSEE_MAP = {
    1: 75101, 2: 75102, 3: 75103, 4: 75104, 5: 75105,
    6: 75106, 7: 75107, 8: 75108, 9: 75109, 10: 75110,
    11: 75111, 12: 75112, 13: 75113, 14: 75114, 15: 75115,
    16: 75116, 17: 75117, 18: 75118, 19: 75119, 20: 75120,
}

# Human-readable arrondissement names for display/hover tooltips
ARRONDISSEMENT_NAMES = {
    1: "1er Ardt - Louvre",           2: "2e Ardt - Bourse",
    3: "3e Ardt - Temple",            4: "4e Ardt - Hôtel-de-Ville",
    5: "5e Ardt - Panthéon",          6: "6e Ardt - Luxembourg",
    7: "7e Ardt - Palais-Bourbon",    8: "8e Ardt - Élysée",
    9: "9e Ardt - Opéra",             10: "10e Ardt - Entrepôt",
    11: "11e Ardt - Popincourt",      12: "12e Ardt - Reuilly",
    13: "13e Ardt - Gobelins",        14: "14e Ardt - Observatoire",
    15: "15e Ardt - Vaugirard",       16: "16e Ardt - Passy",
    17: "17e Ardt - Batignolles-Monceau",
    18: "18e Ardt - Buttes-Montmartre",
    19: "19e Ardt - Buttes-Chaumont",
    20: "20e Ardt - Ménilmontant",
}

# List of all one-hot arrondissement feature column names
ARRONDISSEMENT_COLUMNS = list(ARRONDISSEMENT_MAP.values())


# ------------------------------------------------------------
# KEY DEFAULT SETTINGS
# ------------------------------------------------------------

# Middle arrondissement used for KPI comparison (Median)
MEDIAN_ARRONDISSEMENT = 10

