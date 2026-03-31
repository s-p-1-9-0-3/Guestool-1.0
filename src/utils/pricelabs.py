"""PriceLabs data processing and analysis utilities."""

import re
import pandas as pd
import streamlit as st
from typing import Optional, Tuple
from .text import normalizar_texto


MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

MAPA_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def extraer_anyo_y_mes(valor) -> Tuple[Optional[int], Optional[int]]:
    """Extract year and month from various date formats."""
    if pd.isna(valor):
        return None, None

    if isinstance(valor, pd.Timestamp):
        return int(valor.year), int(valor.month)

    texto = str(valor).strip()
    fecha = pd.to_datetime(texto, errors="coerce", dayfirst=True)
    if not pd.isna(fecha):
        return int(fecha.year), int(fecha.month)

    texto_norm = normalizar_texto(texto)
    partes = texto_norm.split()

    mes = None
    anyo = None

    for p in partes:
        if p in MAPA_MESES:
            mes = MAPA_MESES[p]
        if re.fullmatch(r"20\d{2}", p):
            anyo = int(p)

    m = re.search(r"(20\d{2})[-/](\d{1,2})", texto)
    if m:
        anyo = int(m.group(1))
        mes = int(m.group(2))

    return anyo, mes


@st.cache_data(show_spinner=False)
def procesar_pricelabs_excel(_df_original: pd.DataFrame, filename: str, year: int) -> pd.DataFrame:
    """Process PriceLabs daily Excel and return clean DataFrame."""
    df = _df_original.copy()
    df.columns = [str(c).strip() for c in df.columns]
    columnas_norm = {c: normalizar_texto(c) for c in df.columns}

    col_listado = col_fecha = col_occ = col_adr = col_los = col_ingresos = col_booking_window = None

    for col, norm in columnas_norm.items():
        if col_listado is None and ("nombre de listado" in norm or "listing name" in norm or norm == "listado"):
            col_listado = col
        if col_fecha is None and "fecha" in norm:
            col_fecha = col
        if col_occ is None and ("ocupacion" in norm or "occupancy" in norm):
            col_occ = col
        if col_adr is None and ("adr" in norm or "average daily rate" in norm):
            col_adr = col
        if col_los is None and ("los" in norm or "length of stay" in norm):
            col_los = col
        if col_ingresos is None and ("ingresos" in norm or "revenue" in norm):
            col_ingresos = col
        if col_booking_window is None and ("ventana de reserva" in norm or "booking window" in norm):
            col_booking_window = col

    if not all([col_listado, col_fecha, col_adr]):
        raise ValueError("El Excel debe tener: Nombre de Listado, Fecha, ADR")

    # DataFrame with daily data
    resultado = pd.DataFrame()
    resultado["apartamento_excel"] = df[col_listado].astype(str).str.strip()
    resultado["fecha"] = pd.to_datetime(df[col_fecha], errors="coerce")
    resultado["anyo"] = resultado["fecha"].dt.year
    resultado["mes_num"] = resultado["fecha"].dt.month
    
    # Add year suffix to metric columns
    suffix = f"_{year}"
    adr_col = pd.to_numeric(df[col_adr], errors="coerce")
    occ_col = pd.to_numeric(
        df[col_occ].astype(str).str.replace("%", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce"
    ) if col_occ else 0.0
    
    resultado[f"adr{suffix}"] = adr_col
    resultado[f"ocupacion{suffix}"] = occ_col
    resultado[f"los{suffix}"] = pd.to_numeric(df[col_los], errors="coerce") if col_los else 0.0
    # Calculate daily revenue (RevPar) = ADR × (Occupancy / 100)
    resultado[f"ingresos{suffix}"] = adr_col * (occ_col / 100)
    resultado[f"booking_window{suffix}"] = pd.to_numeric(df[col_booking_window], errors="coerce") if col_booking_window else 0.0

    # Clean invalid rows
    resultado = resultado.dropna(subset=["apartamento_excel", "fecha", f"adr{suffix}"])
    resultado = resultado[resultado["apartamento_excel"] != ""].reset_index(drop=True)

    return resultado


def calcular_metricas_periodo(df: pd.DataFrame, apartamento: str, fecha_inicio, fecha_fin, año) -> dict:
    """Calculate metrics for a specific period (same as PriceLabs)."""
    df_filtrado = df[
        (df["apartamento"] == apartamento) &
        (df["año"] == año) &
        (df["fecha"].dt.date >= fecha_inicio) &
        (df["fecha"].dt.date <= fecha_fin)
    ]
    
    if df_filtrado.empty:
        return None
    
    return {
        "adr": df_filtrado["adr"].mean(),
        "los": df_filtrado["los"].mean(),
        "ocupacion": df_filtrado["ocupacion"].mean(),
        "ingresos": df_filtrado["ingresos"].sum() if df_filtrado["ingresos"].sum() > 0 else df_filtrado["adr"].mean() * df_filtrado["los"].mean() * len(df_filtrado),
        "booking_window": df_filtrado["booking_window"].mean(),
        "dias": len(df_filtrado)
    }


def calcular_los_desde_ocupacion(df_periodo: pd.DataFrame, col_ocupacion: str, col_booking_window: str = None, df_completo: pd.DataFrame = None) -> float:
    """
    Calculate LOS = Total nights of all reservations / Number of reservations that pass through the month
    
    Logic:
    - Uses "Ventana de Reserva Promedio" (booking_window) column which contains days
    - One "reservation" = one day with booking_window value != 0
    - Only counts reservations that have at least 1 day in the target month
    - If a 7-night reservation starts on Apr 28, it will last until May 4 → COUNTS
    """
    # Paranoia check: verify all required parameters are valid
    if df_periodo.empty or col_booking_window is None or df_completo is None or df_completo.empty:
        return None
    
    # Check if booking_window column exists in df_completo
    if col_booking_window not in df_completo.columns:
        return None
    
    # Get period dates
    if df_periodo.empty:
        return None
        
    primer_fecha_mes = pd.to_datetime(df_periodo["fecha"].iloc[0])
    ultima_fecha_mes = pd.to_datetime(df_periodo["fecha"].iloc[-1])
    
    # Filter: previous month + current month (to capture reservations that come from behind)
    mes_anterior_inicio = primer_fecha_mes.replace(day=1) - pd.Timedelta(days=1)
    mes_anterior_inicio = mes_anterior_inicio.replace(day=1)
    
    df_busqueda = df_completo[
        (pd.to_datetime(df_completo["fecha"]) >= mes_anterior_inicio) &
        (pd.to_datetime(df_completo["fecha"]) <= ultima_fecha_mes)
    ].copy()
    
    if df_busqueda.empty:
        return None
    
    # Convert dates and LOS values
    df_busqueda["fecha"] = pd.to_datetime(df_busqueda["fecha"])
    los_vals = pd.to_numeric(df_busqueda[col_booking_window], errors="coerce").fillna(0)
    df_busqueda["los"] = los_vals
    
    # Find reservations that PASS THROUGH the month (have at least 1 day in the month)
    reservas_validas = []
    
    for idx, row in df_busqueda.iterrows():
        los_value = row["los"]
        if los_value > 0:  # Has a stay duration
            fecha_inicio = row["fecha"]
            duracion = int(los_value)
            fecha_fin = fecha_inicio + pd.Timedelta(days=duracion - 1)
            
            # The reservation "passes through the month" if its end date >= first day of month
            if fecha_fin >= primer_fecha_mes:
                reservas_validas.append(duracion)
    
    # Calculate LOS = sum of durations / number of reservations
    if not reservas_validas:
        return None
    
    num_reservas = len(reservas_validas)
    suma_noches = sum(reservas_validas)
    los = suma_noches / num_reservas
    
    return float(los)


def obtener_resumen_pricelabs_comparado(df_pricelabs: pd.DataFrame, apartamento_excel: str, mes_num: int):
    """Get comparison summary for a property in a month."""
    df_mes = df_pricelabs[
        (df_pricelabs["apartamento_excel"] == apartamento_excel) &
        (df_pricelabs["mes_num"] == mes_num)
    ].copy()

    if df_mes.empty:
        return None

    fila = df_mes.iloc[0]

    adr_2025 = float(fila["adr_2025"]) if pd.notna(fila["adr_2025"]) else None
    adr_2026 = float(fila["adr_2026"]) if pd.notna(fila["adr_2026"]) else None
    los_2025 = float(fila["los_2025"]) if pd.notna(fila["los_2025"]) else None
    los_2026 = float(fila["los_2026"]) if pd.notna(fila["los_2026"]) else None
    occ_2025 = float(fila["ocupacion_2025"]) if pd.notna(fila["ocupacion_2025"]) else None
    occ_2026 = float(fila["ocupacion_2026"]) if pd.notna(fila["ocupacion_2026"]) else None
    ing_2025 = float(fila["ingresos_2025"]) if pd.notna(fila["ingresos_2025"]) else None
    ing_2026 = float(fila["ingresos_2026"]) if pd.notna(fila["ingresos_2026"]) else None
    bw_2025 = float(fila["booking_window_2025"]) if pd.notna(fila["booking_window_2025"]) else None
    bw_2026 = float(fila["booking_window_2026"]) if pd.notna(fila["booking_window_2026"]) else None

    yoy_adr_pct = None
    if adr_2025 and adr_2025 > 0 and adr_2026 is not None:
        yoy_adr_pct = ((adr_2026 / adr_2025) - 1) * 100

    return {
        "anyo_mes": fila["anyo_mes"],
        "adr_2025": adr_2025,
        "adr_2026_forecast": adr_2026,
        "los_2025": los_2025,
        "los_2026": los_2026,
        "ocupacion_2025": occ_2025,
        "ocupacion_2026": occ_2026,
        "ingresos_2025": ing_2025,
        "ingresos_2026": ing_2026,
        "booking_window_2025": bw_2025,
        "booking_window_2026": bw_2026,
        "yoy_adr_pct": yoy_adr_pct,
    }


def buscar_mejor_match_apartamento(nombre_app: str, lista_excel: list) -> Optional[str]:
    """Find best matching accommodation name from Excel."""
    objetivo = normalizar_texto(nombre_app)

    exactos = [x for x in lista_excel if normalizar_texto(x) == objetivo]
    if exactos:
        return exactos[0]

    incluidos = [x for x in lista_excel if objetivo in normalizar_texto(x) or normalizar_texto(x) in objetivo]
    if incluidos:
        return incluidos[0]

    tokens_obj = set(objetivo.split())
    mejor = None
    mejor_score = 0.0

    for x in lista_excel:
        tokens_x = set(normalizar_texto(x).split())
        if not tokens_x:
            continue
        inter = len(tokens_obj & tokens_x)
        union = len(tokens_obj | tokens_x)
        score = inter / union if union else 0.0
        if score > mejor_score:
            mejor_score = score
            mejor = x

    if mejor_score >= 0.45:
        return mejor

    return None
