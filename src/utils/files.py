"""Configuration and file I/O utilities."""

import json
import os
import pandas as pd
from pathlib import Path
import streamlit as st
from .text import slugify, pretty_name_from_slug, normalizar_texto


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "datos"
CONFIG_DIR = BASE_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "empresas_config.json"

DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)


def default_empresa_config(nombre_empresa: str, archivo_csv: str) -> dict:
    """Create default configuration for a company."""
    return {
        "nombre": nombre_empresa,
        "archivo_csv": archivo_csv,
        "markups": {
            "Airbnb": 0.0,
            "Booking": 0.0,
            "Web": 0.0,
        },
        "descuentos": [],
        "pricelabs_files": {},  # {year: filename}
        "pricelabs_timestamps": {},
    }


def load_config_from_disk() -> dict:
    """Load configuration from disk."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def save_config_to_disk(config: dict):
    """Save configuration to disk."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def bootstrap_config_with_existing_csvs(config: dict) -> dict:
    """Bootstrap configuration with existing CSV files in datos directory."""
    changed = False

    for ruta in sorted(DATA_DIR.glob("*.csv")):
        empresa_id = slugify(ruta.stem)
        if empresa_id not in config:
            config[empresa_id] = default_empresa_config(
                nombre_empresa=pretty_name_from_slug(ruta.stem),
                archivo_csv=ruta.name,
            )
            changed = True
        else:
            if not config[empresa_id].get("archivo_csv"):
                config[empresa_id]["archivo_csv"] = ruta.name
                changed = True
            if not config[empresa_id].get("nombre"):
                config[empresa_id]["nombre"] = pretty_name_from_slug(ruta.stem)
                changed = True
            if "markups" not in config[empresa_id]:
                config[empresa_id]["markups"] = default_empresa_config("", "")["markups"]
                changed = True
            if "descuentos" not in config[empresa_id]:
                config[empresa_id]["descuentos"] = []
                changed = True
            if "pricelabs_files" not in config[empresa_id]:
                config[empresa_id]["pricelabs_files"] = {}
                changed = True
            if "pricelabs_timestamps" not in config[empresa_id]:
                config[empresa_id]["pricelabs_timestamps"] = {}
                changed = True

    if changed:
        save_config_to_disk(config)

    return config


@st.cache_data(show_spinner=False)
def cargar_config() -> dict:
    """Load and bootstrap configuration."""
    config = load_config_from_disk()
    return bootstrap_config_with_existing_csvs(config)


def guardar_config(config: dict):
    """Save configuration and clear cache."""
    from .company_data import obtener_empresas, obtener_apartamentos
    save_config_to_disk(config)
    cargar_config.clear()
    obtener_empresas.clear()
    obtener_apartamentos.clear()


def invalidar_config():
    """Invalidate configuration cache."""
    from .company_data import obtener_empresas, obtener_apartamentos
    cargar_config.clear()
    obtener_empresas.clear()
    obtener_apartamentos.clear()


def ruta_csv_empresa(empresa_id: str) -> Path:
    """Get CSV file path for a company."""
    config = cargar_config()
    archivo = config.get(empresa_id, {}).get("archivo_csv", f"{empresa_id}.csv")
    return DATA_DIR / archivo


def guardar_pricelabs_excel(empresa_id: str, archivos: list) -> bool:
    """
    Save multiple PriceLabs Excel files to disk with auto-detection of years.
    Also processes and caches DataFrames in session_state for cloud compatibility.
    
    Args:
        empresa_id: Company ID
        archivos: List of uploaded file objects (from st.file_uploader with accept_multiple_files=True)
    
    Returns:
        bool: True if at least one file was saved successfully, False otherwise
    """
    import sys
    config = cargar_config()
    if empresa_id not in config:
        config[empresa_id] = default_empresa_config(pretty_name_from_slug(empresa_id), f"{empresa_id}.csv")
    
    pricelabs_files = {}
    timestamps = {}
    procesados = {}  # NEW: Store processed DataFrames for session_state
    
    print(f"[DEBUG] guardar_pricelabs_excel: Procesando {len(archivos)} archivos para {empresa_id}", file=sys.stderr)
    
    for archivo in archivos:
        try:
            from io import BytesIO
            from src.utils.pricelabs import procesar_pricelabs_excel
            
            # Auto-detect year from the data
            df_raw = pd.read_excel(BytesIO(archivo.getvalue()))
            year_detectado = _detectar_anyo_archivo(df_raw)
            
            print(f"[DEBUG] Archivo {archivo.name}: Año detectado = {year_detectado}", file=sys.stderr)
            
            if year_detectado is None:
                st.warning(f"⚠️ No se pudo detectar el año en {archivo.name}. Se saltará.")
                continue
            
            # NEW: Process the DataFrame for cloud compatibility
            try:
                df_procesado = procesar_pricelabs_excel(df_raw, archivo.name, year_detectado)
                procesados[year_detectado] = df_procesado
                print(f"[DEBUG] ✓ Procesado {archivo.name} para año {year_detectado}: {df_procesado.shape[0]} filas", file=sys.stderr)
            except Exception as e:
                st.warning(f"⚠️ No se pudo procesar {archivo.name}: {e}")
                print(f"[DEBUG] ✗ Error procesando {archivo.name}: {e}", file=sys.stderr)
                # Still save the raw file even if processing fails
            
            # Nombre seguro para el archivo
            nombre_archivo = f"{empresa_id}_pricelabs_{year_detectado}.xlsx"
            ruta = DATA_DIR / nombre_archivo
            
            # Guardar archivo
            contenido = archivo.getvalue()
            with open(ruta, "wb") as f:
                f.write(contenido)
            
            pricelabs_files[year_detectado] = nombre_archivo
            timestamps[str(year_detectado)] = os.path.getmtime(ruta)
        except Exception as e:
            st.warning(f"❌ Error procesando {archivo.name}: {e}")
            print(f"[DEBUG] ✗ Excepción en archivo {archivo.name}: {e}", file=sys.stderr)
            import traceback
            print(traceback.format_exc(), file=sys.stderr)
            continue
    
    if pricelabs_files:
        config[empresa_id]["pricelabs_files"] = pricelabs_files
        config[empresa_id]["pricelabs_timestamps"] = timestamps
        guardar_config(config)
        
        # NEW: Cache processed DataFrames in session_state for cloud environments
        if procesados:
            st.session_state[f"pricelabs_data_{empresa_id}"] = procesados
            print(f"[DEBUG] ✓ Cacheado en session_state: {list(procesados.keys())}", file=sys.stderr)
        else:
            print(f"[DEBUG] ⚠ No hay DataFrames procesados para cachear (solo se guardó a disco)", file=sys.stderr)
        
        # Limpiar cachés
        detectar_cambios_pricelabs.clear()
        return True
    
    print(f"[DEBUG] ✗ No se guardó ningún archivo", file=sys.stderr)
    return False


def _detectar_anyo_archivo(df: pd.DataFrame) -> int:
    """
    Auto-detect the year from a PriceLabs DataFrame by examining date columns.
    Returns the predominant year found, or None if no year detected.
    """
    # Normalizar nombres de columnas
    columnas_norm = {c: normalizar_texto(c) for c in df.columns}
    
    col_fecha = None
    for col, norm in columnas_norm.items():
        if "fecha" in norm:
            col_fecha = col
            break
    
    if col_fecha is None:
        return None
    
    try:
        df_temp = df.copy()
        df_temp["fecha"] = pd.to_datetime(df_temp[col_fecha], errors="coerce")
        años = df_temp["fecha"].dt.year.dropna()
        
        if len(años) == 0:
            return None
        
        # Retornar el año más frecuente
        año_predominante = años.value_counts().idxmax()
        return int(año_predominante)
    except Exception:
        return None


def cargar_pricelabs_excel(empresa_id: str) -> dict:
    """
    Load stored PriceLabs Excel files.
    Priority: session_state → disk files
    
    Returns:
        Dictionary with format {year: dataframe} for all stored files
        Example: {2025: df_2025, 2026: df_2026, 2027: df_2027}
    """
    import sys
    import streamlit as st
    
    session_key = f"pricelabs_data_{empresa_id}"
    
    # PRIMERO: Intentar leer del session_state (para Streamlit Cloud)
    if session_key in st.session_state:
        cached_data = st.session_state[session_key]
        if cached_data and isinstance(cached_data, dict):
            print(f"[DEBUG] cargar_pricelabs_excel: Encontrado en session_state: {list(cached_data.keys())}", file=sys.stderr)
            return cached_data
        else:
            print(f"[DEBUG] cargar_pricelabs_excel: session_state['{session_key}'] existe pero está vacío o inválido", file=sys.stderr)
    else:
        print(f"[DEBUG] cargar_pricelabs_excel: No encontrado en session_state (key: '{session_key}')", file=sys.stderr)
    
    # SEGUNDA OPCIÓN: Leer del disco (para localhost)
    print(f"[DEBUG] cargar_pricelabs_excel: Buscando en disco...", file=sys.stderr)
    config = cargar_config()
    empresa_config = config.get(empresa_id, {})
    pricelabs_files = empresa_config.get("pricelabs_files", {})
    print(f"[DEBUG] Archivos en config: {pricelabs_files}", file=sys.stderr)
    
    resultado = {}
    for year, nombre_archivo in pricelabs_files.items():
        ruta = DATA_DIR / nombre_archivo
        if ruta.exists():
            try:
                df = pd.read_excel(ruta)
                resultado[int(year)] = df
                print(f"[DEBUG] Cargado del disco: {nombre_archivo} ({df.shape[0]} filas)", file=sys.stderr)
            except Exception as e:
                print(f"[DEBUG] Error cargando {nombre_archivo}: {e}", file=sys.stderr)
                pass
        else:
            print(f"[DEBUG] Archivo no existe: {ruta}", file=sys.stderr)
    
    # Guardar en session_state para futuros accesos
    if resultado:
        st.session_state[session_key] = resultado
        print(f"[DEBUG] Cacheado en session_state desde disco: {list(resultado.keys())}", file=sys.stderr)
    else:
        print(f"[DEBUG] No se encontró ningún archivo en disco", file=sys.stderr)
    
    return resultado


@st.cache_data(ttl=60, show_spinner=False)
def detectar_cambios_pricelabs(empresa_id: str) -> bool:
    """Detect if PriceLabs files were modified externally."""
    config = cargar_config()
    empresa_config = config.get(empresa_id, {})
    timestamps_guardados = empresa_config.get("pricelabs_timestamps", {})
    pricelabs_files = empresa_config.get("pricelabs_files", {})
    
    if not timestamps_guardados:
        return False
    
    # Check each file
    for year, nombre_archivo in pricelabs_files.items():
        ruta = DATA_DIR / nombre_archivo
        if ruta.exists():
            timestamp_actual = os.path.getmtime(ruta)
            timestamp_guardado = timestamps_guardados.get(str(year))
            if timestamp_guardado and timestamp_actual != timestamp_guardado:
                return True
    
    return False


def obtener_descuentos_empresa(empresa_id: str) -> pd.DataFrame:
    """Get discount table for a company."""
    config = cargar_config()
    descuentos = config.get(empresa_id, {}).get("descuentos", [])
    if descuentos:
        return pd.DataFrame(descuentos)
    return pd.DataFrame(columns=["Desde", "Hasta", "Descuento (%)"])


def guardar_descuentos_empresa(empresa_id: str, df: pd.DataFrame):
    """Save discount table for a company."""
    filas = []
    for _, fila in df.iterrows():
        try:
            desde = int(float(str(fila.get("Desde", "")).replace(",", ".")))
            hasta = int(float(str(fila.get("Hasta", "")).replace(",", ".")))
            desc = float(str(fila.get("Descuento (%)", "")).replace(",", "."))
        except Exception:
            continue
        if desde >= 1 and hasta >= desde:
            filas.append({"Desde": desde, "Hasta": hasta, "Descuento (%)": desc})
    config = cargar_config()
    if empresa_id not in config:
        config[empresa_id] = default_empresa_config(pretty_name_from_slug(empresa_id), f"{empresa_id}.csv")
    config[empresa_id]["descuentos"] = filas
    guardar_config(config)
