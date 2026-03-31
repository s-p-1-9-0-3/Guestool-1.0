"""
Estilos y configuración visual de Guestool
"""
import streamlit as st
import os


@st.cache_data(show_spinner=False)
def _cargar_archivo_texto(ruta: str) -> str:
    """Carga un archivo de texto y cachea el resultado."""
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()


def apply_custom_styles():
    """
    Aplica todos los estilos CSS y JavaScript personalizados de Guestool.
    Carga archivos externos desde src/static/
    Llamar una sola vez en app.py al inicio.
    """
    # Determinar la ruta base (directorio donde está app.py)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_path = os.path.join(base_dir, 'src', 'static', 'styles.css')
    js_path = os.path.join(base_dir, 'src', 'static', 'script.js')
    
    # Cargar CSS
    try:
        css_content = _cargar_archivo_texto(css_path)
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file not found: {css_path}")
    
    # Cargar JavaScript
    try:
        js_content = _cargar_archivo_texto(js_path)
        st.markdown(f"<script>{js_content}</script>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"JavaScript file not found: {js_path}")
