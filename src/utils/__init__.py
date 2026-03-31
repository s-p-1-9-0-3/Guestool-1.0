"""Utilidades compartidas del proyecto."""

# Parsing and input validation
from .parsing import parse_int_input, parse_float_input, leer_archivo_datos

# Text normalization
from .text import slugify, pretty_name_from_slug, normalizar_texto, detectar_columnas

# Formatting
from .formatting import fmt_markup, fmt_num

# File I/O
from .files import (
    load_config_from_disk, save_config_to_disk, 
    default_empresa_config, bootstrap_config_with_existing_csvs,
    cargar_config, guardar_config, invalidar_config,
    ruta_csv_empresa, guardar_pricelabs_excel, cargar_pricelabs_excel,
    detectar_cambios_pricelabs, obtener_descuentos_empresa,
    guardar_descuentos_empresa
)

# Data normalization
from .data_normalization import normalizar_df_alojamientos

# Company data management
from .company_data import (
    obtener_empresas, obtener_markups_empresa, guardar_markups_empresa,
    obtener_descuento_para_noches, obtener_apartamentos
)

# PriceLabs utilities
from .pricelabs import (
    procesar_pricelabs_excel, extraer_anyo_y_mes, MESES, MAPA_MESES,
    obtener_resumen_pricelabs_comparado, calcular_los_desde_ocupacion,
    calcular_metricas_periodo, buscar_mejor_match_apartamento
)

# Calculations
from .calculations import (
    calcular_precio_rms_desde_objetivo, diagnosticar_forecast,
    calcular_rentabileitor_pro_2026_vs_2025
)

__all__ = [
    # Parsing
    'parse_int_input', 'parse_float_input', 'leer_archivo_datos',
    # Text
    'slugify', 'pretty_name_from_slug', 'normalizar_texto', 'detectar_columnas',
    # Formatting
    'fmt_markup', 'fmt_num',
    # Files
    'load_config_from_disk', 'save_config_to_disk', 'default_empresa_config',
    'bootstrap_config_with_existing_csvs', 'cargar_config', 'guardar_config',
    'invalidar_config', 'ruta_csv_empresa', 'guardar_pricelabs_excel',
    'cargar_pricelabs_excel', 'detectar_cambios_pricelabs',
    'obtener_descuentos_empresa', 'guardar_descuentos_empresa',
    # Data normalization
    'normalizar_df_alojamientos',
    # Company data
    'obtener_empresas', 'obtener_markups_empresa', 'guardar_markups_empresa',
    'obtener_descuento_para_noches', 'obtener_apartamentos',
    # PriceLabs
    'procesar_pricelabs_excel', 'extraer_anyo_y_mes', 'MESES', 'MAPA_MESES',
    'obtener_resumen_pricelabs_comparado', 'calcular_los_desde_ocupacion',
    'calcular_metricas_periodo', 'buscar_mejor_match_apartamento',
    # Calculations
    'calcular_precio_rms_desde_objetivo', 'diagnosticar_forecast',
    'calcular_rentabileitor_pro_2026_vs_2025',
]
