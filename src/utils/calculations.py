"""Calculation utilities for pricing and rentability analysis."""

from typing import Optional


def calcular_precio_rms_desde_objetivo(adr_objetivo: float, limpieza: float, noches: int, markup: float, descuento: float):
    """Calculate RMS price from target ADR, cleaning, nights, markup, and discount."""
    limpieza_noche = limpieza / noches
    factor_markup = 1 + markup / 100
    factor_descuento = 1 - descuento / 100

    if factor_markup <= 0 or factor_descuento <= 0:
        return None

    precio_rms = (adr_objetivo - limpieza_noche) / (factor_markup * factor_descuento)
    return max(precio_rms, 0.0)


def diagnosticar_forecast(yoy_adr_pct: Optional[float], adr_forecast: float, adr_recomendado: float) -> str:
    """Diagnose forecast accuracy."""
    if adr_forecast is None or adr_recomendado is None or adr_forecast <= 0:
        return "Sin forecast"

    gap_pct = ((adr_recomendado / adr_forecast) - 1) * 100

    if abs(gap_pct) <= 4:
        return "Forecast correcto"
    if gap_pct > 4:
        return "Forecast bajo"
    return "Forecast agresivo"


def calcular_rentabileitor_pro_2026_vs_2025(
    adr_2025: float,
    adr_2026_forecast: float,
    limpieza: float,
    noches: int,
    descuento: float,
    markup: float,
    los_2025: Optional[float] = None,
    los_2026: Optional[float] = None,
    ocupacion_2025: Optional[float] = None,
    ocupacion_2026: Optional[float] = None,
    margen_extra_pct: float = 0.0,
):
    """
    Calculate Rentabileitor PRO 2026 vs 2025 pricing recommendations.
    
    Uses weighted combination of ADRs when both available (55%/45%).
    If only one year's data exists (new property), uses that year as baseline with conservative growth (5%).
    """
    # NEW LOGIC: Handle missing historical data (new properties)
    es_primera_temporada = False
    
    if adr_2025 is None or adr_2025 <= 0:
        if adr_2026_forecast is None or adr_2026_forecast <= 0:
            return None
        # Property is new: use 2026 as baseline
        adr_2025 = adr_2026_forecast
        es_primera_temporada = True
    
    if adr_2026_forecast is None or adr_2026_forecast <= 0:
        if adr_2025 is None or adr_2025 <= 0:
            return None
        # Only 2025 exists: project to 2026 with conservative growth
        adr_2026_forecast = adr_2025 * 1.05
        es_primera_temporada = False
    
    # Original validation for other parameters
    if adr_2025 <= 0 or adr_2026_forecast <= 0:
        return None

    limpieza_noche = limpieza / noches
    factor_descuento = 1 - descuento / 100
    factor_markup = 1 + markup / 100

    if factor_descuento <= 0 or factor_markup <= 0:
        return None

    # Base ADR: 55% 2025 + 45% 2026 forecast
    adr_base = (adr_2025 * 0.55) + (adr_2026_forecast * 0.45)

    # YoY adjustment
    yoy_forecast_pct = ((adr_2026_forecast / adr_2025) - 1) * 100

    ajuste_yoy = 0.0
    if yoy_forecast_pct < 4:
        ajuste_yoy = adr_base * 0.04
    elif yoy_forecast_pct < 8:
        ajuste_yoy = adr_base * 0.02
    elif yoy_forecast_pct > 18:
        ajuste_yoy = -adr_base * 0.025
    elif yoy_forecast_pct > 12:
        ajuste_yoy = -adr_base * 0.01

    # Cleaning adjustment
    ajuste_limpieza = limpieza_noche * 0.70
    
    # Discount adjustment
    ajuste_descuento = adr_base * ((1 / factor_descuento) - 1) * 0.60
    
    # Markup adjustment
    ajuste_markup = adr_base * (factor_markup - 1) * 0.22

    # LOS adjustment
    ajuste_los = 0.0
    if los_2025 and los_2026 and los_2025 > 0:
        diff_los = los_2026 - los_2025
        ajuste_los = adr_base * diff_los * 0.008

    # Occupancy adjustment
    ajuste_ocupacion = 0.0
    if ocupacion_2025 is not None and ocupacion_2026 is not None:
        diff_occ = ocupacion_2026 - ocupacion_2025
        ajuste_ocupacion = adr_base * diff_occ * 0.0012

    # Calculate optimal ADR
    adr_optimo = (
        adr_base
        + ajuste_yoy
        + ajuste_limpieza
        + ajuste_descuento
        + ajuste_markup
        + ajuste_los
        + ajuste_ocupacion
    )

    # Apply extra margin
    adr_optimo *= (1 + margen_extra_pct / 100)

    # Apply floor and ceiling bounds
    suelo = min(adr_2025 * 1.01, adr_2026_forecast * 0.96)
    techo = max(adr_2025 * 1.30, adr_2026_forecast * 1.12)
    adr_optimo = min(max(adr_optimo, suelo), techo)

    # Conservative variant (5% above previous year ADR)
    adr_conservador = adr_2025 * 1.05

    # Aggressive variant (use ceiling as upper bound)
    adr_agresivo = techo

    # Calculate RMS prices
    precio_rms_optimo = calcular_precio_rms_desde_objetivo(adr_optimo, limpieza, noches, markup, descuento)
    precio_rms_conservador = calcular_precio_rms_desde_objetivo(adr_conservador, limpieza, noches, markup, descuento)
    precio_rms_agresivo = calcular_precio_rms_desde_objetivo(adr_agresivo, limpieza, noches, markup, descuento)

    # Diagnose forecast
    diagnostico = diagnosticar_forecast(((adr_2026_forecast / adr_2025) - 1) * 100, adr_2026_forecast, adr_optimo)

    return {
        "adr_conservador": adr_conservador,
        "adr_optimo": adr_optimo,
        "adr_agresivo": adr_agresivo,
        "precio_rms_conservador": precio_rms_conservador,
        "precio_rms_optimo": precio_rms_optimo,
        "precio_rms_agresivo": precio_rms_agresivo,
        "limpieza_noche": limpieza_noche,
        "ajuste_yoy": ajuste_yoy,
        "ajuste_limpieza": ajuste_limpieza,
        "ajuste_descuento": ajuste_descuento,
        "ajuste_markup": ajuste_markup,
        "ajuste_los": ajuste_los,
        "ajuste_ocupacion": ajuste_ocupacion,
        "diagnostico": diagnostico,
        "gap_vs_forecast_pct": ((adr_optimo / adr_2026_forecast) - 1) * 100,
        "yoy_forecast_pct": ((adr_2026_forecast / adr_2025) - 1) * 100,
        "es_primera_temporada": es_primera_temporada,  # Flag para nuevas propiedades
    }
