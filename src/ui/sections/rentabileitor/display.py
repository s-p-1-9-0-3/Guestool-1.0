"""
Funciones de renderizado/display para Rentabileitor PRO
"""
import streamlit as st
import pandas as pd
from .calculations import calcular_cambio


def render_metrica_minimal(nombre, valor_actual, valor_anterior, unidad, year_actual, year_anterior):
    """
    Renderiza métrica minimalista: año_actual | año_anterior | % cambio
    Una métrica por línea, full width.
    """
    pct_cambio, es_positivo = calcular_cambio(valor_actual, valor_anterior)
    
    # Determinar color y símbolo
    if pct_cambio is None:
        color_pct = "#888888"
        simbolo = "⚪"
        pct_text = "—"
    elif es_positivo:
        color_pct = "#00aa00"
        simbolo = "↑"
        pct_text = f"+{pct_cambio:.1f}%"
    else:
        color_pct = "#dd0000"
        simbolo = "↓"
        pct_text = f"{pct_cambio:.1f}%"
    
    val_actual_str = f"{valor_actual:.2f}" if valor_actual is not None and not pd.isna(valor_actual) else "—"
    val_anterior_str = f"{valor_anterior:.2f}" if valor_anterior is not None and not pd.isna(valor_anterior) else "—"
    
    st.markdown(
        f"<div style='display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; border-left: 4px solid #1f77b4; background: #f8f9fa; margin-bottom: 10px; border-radius: 4px;'>"
        f"<div style='font-weight: 600; flex: 0.6; font-size: 14px;'>{nombre}</div>"
        f"<div style='text-align: center; flex: 1; font-size: 12px;'><span style='color: #999; display: block; font-size: 10px; margin-bottom: 2px;'>{year_actual}</span><span style='font-weight: 600; font-size: 13px;'>{val_actual_str} <span style=\"color: #999; font-weight: 400;\">{unidad}</span></span></div>"
        f"<div style='text-align: center; flex: 1; font-size: 12px;'><span style='color: #999; display: block; font-size: 10px; margin-bottom: 2px;'>{year_anterior}</span><span style='font-weight: 600; font-size: 13px;'>{val_anterior_str} <span style=\"color: #999; font-weight: 400;\">{unidad}</span></span></div>"
        f"<div style='text-align: center; flex: 0.8; font-size: 12px;'><span style='color: #999; display: block; font-size: 10px; margin-bottom: 2px;'>Cambio</span><span style='color: {color_pct}; font-weight: 600; font-size: 13px;'>{simbolo} {pct_text}</span></div>"
        f"</div>",
        unsafe_allow_html=True
    )
