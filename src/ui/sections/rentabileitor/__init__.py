"""
Módulo Rentabileitor - Refactorizado para mejor mantenibilidad
"""
from .calculations import (
    safe_mean,
    calcular_adr_ocupados,
    calcular_ocupacion,
    calcular_revpar,
    calcular_cambio,
)
from .data_processing import (
    fuzzy_match,
    filtrar_apartamentos_por_empresa,
)
from .display import (
    render_metrica_minimal,
)

__all__ = [
    # Calculations
    "safe_mean",
    "calcular_adr_ocupados",
    "calcular_ocupacion",
    "calcular_revpar",
    "calcular_cambio",
    # Data Processing
    "fuzzy_match",
    "filtrar_apartamentos_por_empresa",
    # Display
    "render_metrica_minimal",
]
