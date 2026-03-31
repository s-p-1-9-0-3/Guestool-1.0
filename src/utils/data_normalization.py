"""Data normalization utilities for accommodations."""

import pandas as pd
from .text import detectar_columnas


def normalizar_df_alojamientos(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize accommodations DataFrame with name and cleaning cost columns."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    col_nombre, col_limpieza = detectar_columnas(df)
    if not col_nombre or not col_limpieza:
        raise ValueError("No se detectan columnas válidas de nombre y limpieza")
    salida = df[[col_nombre, col_limpieza]].copy()
    salida.columns = ["nombre", "coste_limpieza"]
    salida["nombre"] = salida["nombre"].astype(str).str.strip()
    salida["coste_limpieza"] = pd.to_numeric(
        salida["coste_limpieza"].astype(str).str.replace(",", ".", regex=False).str.strip(),
        errors="coerce"
    )
    salida = salida.dropna(subset=["nombre", "coste_limpieza"])
    salida = salida[salida["nombre"] != ""]
    return salida.drop_duplicates(subset=["nombre"]).sort_values("nombre").reset_index(drop=True)
