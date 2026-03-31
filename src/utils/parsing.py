"""Parsing and input validation utilities."""

import pandas as pd
from io import BytesIO
from typing import Optional


def parse_int_input(valor, nombre, minimo=None, maximo=None) -> int:
    """Parse integer input with validation."""
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        raise ValueError(f"'{nombre}' no puede estar vacío")
    n = float(texto)
    if not n.is_integer():
        raise ValueError(f"'{nombre}' debe ser un número entero")
    n = int(n)
    if minimo is not None and n < minimo:
        raise ValueError(f"'{nombre}' debe ser ≥ {minimo}")
    if maximo is not None and n > maximo:
        raise ValueError(f"'{nombre}' debe ser ≤ {maximo}")
    return n


def parse_float_input(valor, nombre, minimo=None, maximo=None) -> float:
    """Parse float input with validation."""
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        raise ValueError(f"'{nombre}' no puede estar vacío")
    n = float(texto)
    if minimo is not None and n < minimo:
        raise ValueError(f"'{nombre}' debe ser ≥ {minimo}")
    if maximo is not None and n > maximo:
        raise ValueError(f"'{nombre}' debe ser ≤ {maximo}")
    return n


def leer_archivo_datos(archivo):
    """Read data file (CSV or XLSX) and return DataFrame."""
    nombre = archivo.name.lower()
    if nombre.endswith(".xlsx"):
        archivo.seek(0)
        return pd.read_excel(archivo)
    if nombre.endswith(".csv"):
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                archivo.seek(0)
                return pd.read_csv(archivo, encoding=enc, sep=None, engine="python")
            except Exception:
                continue
        raise Exception("No se pudo leer el CSV")
    raise Exception("Formato no soportado. Usa CSV o XLSX")
