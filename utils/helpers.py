"""
helpers.py

Collection of small reusable helper functions used across
multiple parts of the application. Includes text cleaning,
amenity label transformations, and safe JSON read/write utilities.
"""

import json
import os


# ------------------------------------------------------------
# AMENITY LABEL HELPERS
# ------------------------------------------------------------

def clean_amenity_name(model_column: str) -> str:
    """
    Convert a model feature column name (amenity__) into a
    user-friendly amenity label.

    Example:
        "amenity__wifi_high_speed" -> "Wifi High Speed"

    Parameters
    ----------
    model_column : str
        Raw model column name beginning with 'amenity__'.

    Returns
    -------
    str
        Clean, human-readable amenity name.
    """
    name = model_column.replace("amenity__", "").rstrip("_")
    name = name.replace("_", " ")
    name = name.replace("u2013", "–")  # special dash fix
    return name.strip().title()


def build_amenity_maps(feature_list):
    """
    Create two dictionaries mapping between model amenity column names
    and human-readable labels.

    Parameters
    ----------
    feature_list : list[str]
        Full list of model input columns.

    Returns
    -------
    (dict, dict)
        label_to_col : maps clean label -> model column
        col_to_label : maps model column -> clean label
    """
    amenity_cols = [c for c in feature_list if c.startswith("amenity__")]

    label_to_col = {clean_amenity_name(c): c for c in amenity_cols}
    col_to_label = {c: clean_amenity_name(c) for c in amenity_cols}

    return label_to_col, col_to_label


# ------------------------------------------------------------
# JSON STORAGE UTILITIES
# ------------------------------------------------------------

def load_json(path: str, default=None):
    """
    Safely load a JSON file. If file does not exist or is corrupted,
    return a provided default value.

    Parameters
    ----------
    path : str
        Path to JSON file.
    default : Any
        Fallback value if loading fails.

    Returns
    -------
    Any
        Parsed JSON content or default value.
    """
    if default is None:
        default = {}

    if not os.path.exists(path):
        return default

    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default


def save_json(path: str, data):
    """
    Save Python data as JSON with indentation.

    Parameters
    ----------
    path : str
        Output file location.
    data : Any
        Serializable Python object.
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ------------------------------------------------------------
# GENERAL HELPERS
# ------------------------------------------------------------

def safe_get(d: dict, key, default=None):
    """
    Shortcut to safely fetch a key from a dictionary
    without raising errors.

    Parameters
    ----------
    d : dict
        Input dictionary.
    key : Any
        Dictionary key.
    default : Any
        Fallback return value.

    Returns
    -------
    Any
        d[key] if exists, otherwise default
    """
    return d.get(key, default)
