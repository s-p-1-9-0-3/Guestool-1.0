"""Company data management utilities."""

import pandas as pd
from pathlib import Path
from typing import Optional
import streamlit as st
from .files import (
    cargar_config, ruta_csv_empresa, guardar_config, 
    obtener_descuentos_empresa, DATA_DIR
)
from .text import pretty_name_from_slug, slugify
from .data_normalization import normalizar_df_alojamientos


@st.cache_data(show_spinner=False)
def obtener_empresas():
    """Get list of all companies."""
    config = cargar_config()
    empresas = []
    for empresa_id, data in config.items():
        ruta = DATA_DIR / data.get("archivo_csv", f"{empresa_id}.csv")
        if ruta.exists() and ruta.stat().st_size > 0:
            empresas.append((empresa_id, data.get("nombre", pretty_name_from_slug(empresa_id))))
    return sorted(empresas, key=lambda x: x[1].lower())


def obtener_markups_empresa(empresa_id: str):
    """Get markup percentages for a company."""
    config = cargar_config()
    m = config.get(empresa_id, {}).get("markups", {})
    return {
        "Airbnb": float(m.get("Airbnb", 0.0) or 0.0),
        "Booking": float(m.get("Booking", 0.0) or 0.0),
        "Web": float(m.get("Web", 0.0) or 0.0),
    }


def guardar_markups_empresa(empresa_id: str, airbnb: float, booking: float, web: float):
    """Save markup percentages for a company."""
    from .files import default_empresa_config
    config = cargar_config()
    if empresa_id not in config:
        config[empresa_id] = default_empresa_config(pretty_name_from_slug(empresa_id), f"{empresa_id}.csv")
    config[empresa_id]["markups"] = {"Airbnb": airbnb, "Booking": booking, "Web": web}
    guardar_config(config)


def obtener_descuento_para_noches(empresa_id: str, noches: int) -> Optional[float]:
    """Get discount percentage for given nights."""
    df = obtener_descuentos_empresa(empresa_id)
    for _, fila in df.iterrows():
        try:
            if int(fila["Desde"]) <= noches <= int(fila["Hasta"]):
                return float(fila["Descuento (%)"])
        except Exception:
            continue
    return None


@st.cache_data(show_spinner=False)
def obtener_apartamentos(empresa_id: str):
    """Get list of accommodations for a company."""
    ruta = ruta_csv_empresa(empresa_id)
    if not ruta.exists():
        return []
    try:
        df = pd.read_csv(ruta)
    except Exception:
        return []
    if not {"nombre", "coste_limpieza"}.issubset(set(df.columns)):
        try:
            df = normalizar_df_alojamientos(df)
        except Exception:
            return []
    df["coste_limpieza"] = pd.to_numeric(df["coste_limpieza"], errors="coerce")
    df = df.dropna(subset=["nombre", "coste_limpieza"])
    return list(df[["nombre", "coste_limpieza"]].sort_values("nombre").itertuples(index=False, name=None))
