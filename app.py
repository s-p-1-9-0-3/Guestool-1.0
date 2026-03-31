"""
Revenue Dashboard - Guestool
Sistema de gestión de precios para alojamientos vacacionales.

Reestructurado en Paso 2/3: Componentes extraídos a src/ui/components.py
"""
import streamlit as st
from src.styles import apply_custom_styles
from src.ui.components import (
    render_nav, render_header_compacto, render_back,
    section_wizard, section_guestool, section_simuleitor
)
from src.ui.sections.rentabileitor import section_rentabileitor as section_rentabileitor_impl
from src.utils import (
    parse_int_input, parse_float_input,
    obtener_empresas, obtener_apartamentos,
    cargar_pricelabs_excel, detectar_cambios_pricelabs,
    procesar_pricelabs_excel, buscar_mejor_match_apartamento,
    calcular_los_desde_ocupacion, guardar_pricelabs_excel,
    obtener_descuento_para_noches, obtener_markups_empresa,
    calcular_rentabileitor_pro_2026_vs_2025, fmt_num, cargar_config
)

# =========================================================
# CONFIGURACIÓN
# =========================================================
st.set_page_config(page_title="Revenue Dashboard", layout="wide", initial_sidebar_state="collapsed")
apply_custom_styles()

# =========================================================
# ESTADO INICIAL
# =========================================================
def init_state():
    defaults = {
        "active_section":        None,
        "guestool_sub":          None,
        "wizard_mode":           "nuevo",
        "wizard_step":           1,
        "wizard_empresa_nombre": "",
        "wizard_empresa_id":     "",
        "wizard_df_limpio":      None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v



# =========================================================
# WRAPPER: SECTION_RENTABILEITOR
# =========================================================
def section_rentabileitor_wrapper():
    """Delega a la implementación en src.ui.sections.rentabileitor"""
    section_rentabileitor_impl(
        obtener_empresas=obtener_empresas,
        obtener_apartamentos=obtener_apartamentos,
        cargar_pricelabs_excel=cargar_pricelabs_excel,
        detectar_cambios_pricelabs=detectar_cambios_pricelabs,
        procesar_pricelabs_excel=procesar_pricelabs_excel,
        buscar_mejor_match_apartamento=buscar_mejor_match_apartamento,
        calcular_los_desde_ocupacion=calcular_los_desde_ocupacion,
        guardar_pricelabs_excel=guardar_pricelabs_excel,
        parse_int_input=parse_int_input,
        parse_float_input=parse_float_input,
        fmt_num=fmt_num,
        obtener_descuento_para_noches=obtener_descuento_para_noches,
        obtener_markups_empresa=obtener_markups_empresa,
        calcular_rentabileitor_pro_2026_vs_2025=calcular_rentabileitor_pro_2026_vs_2025,
    )

init_state()

# =========================================================
# RENDER PRINCIPAL
# =========================================================
section = st.session_state.active_section

if section is None:
    render_nav()
else:
    render_header_compacto()
    render_back()
    if section == "Wizard":
        section_wizard()
    elif section == "Guestool":
        section_guestool(section_simuleitor, section_rentabileitor_wrapper)


