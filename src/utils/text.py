"""Text normalization and text processing utilities."""

import re
import unicodedata
import pandas as pd


def slugify(texto: str) -> str:
    """Convert text to slug format (lowercase, underscores)."""
    texto = str(texto).strip().lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def pretty_name_from_slug(slug: str) -> str:
    """Convert slug to pretty display name."""
    return str(slug).replace("_", " ").strip().title()


def normalizar_texto(texto: str) -> str:
    """Normalize text for comparison (lowercase, remove accents, etc)."""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def detectar_columnas(df: pd.DataFrame):
    """Auto-detect 'nombre' and 'limpieza' columns from DataFrame."""
    col_nombre = col_limpieza = None
    for col in df.columns:
        cn = str(col).strip().lower()
        if col_nombre is None and any(k in cn for k in ["nombre", "aloj", "apart", "propiedad"]):
            col_nombre = col
        if col_limpieza is None and any(k in cn for k in ["limp", "clean", "coste"]):
            col_limpieza = col
    return col_nombre, col_limpieza
