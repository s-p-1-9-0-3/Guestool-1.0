"""
Funciones de cálculo para Rentabileitor PRO
"""
import pandas as pd


def safe_mean(col_name, df):
    """Calcula media segura de una columna"""
    if col_name not in df.columns:
        return None
    vals = pd.to_numeric(df[col_name], errors="coerce").dropna()
    return vals.mean() if len(vals) > 0 else None


def calcular_adr_ocupados(df_periodo, col_adr, col_occ):
    """
    Calcula ADR promedio solo para días ocupados (ocupación > 0)
    """
    occ_vals = pd.to_numeric(df_periodo[col_occ], errors="coerce").fillna(0)
    adr_vals = pd.to_numeric(df_periodo[col_adr], errors="coerce")
    
    # Filtrar solo días ocupados
    dias_ocupados = adr_vals[occ_vals > 0].dropna()
    return dias_ocupados.mean() if len(dias_ocupados) > 0 else None


def calcular_ocupacion(df_periodo, col_occ):
    """
    Calcula ocupación = (días con ocupación > 0) / total días * 100
    """
    occ_vals = pd.to_numeric(df_periodo[col_occ], errors="coerce").fillna(0)
    dias_ocupados = (occ_vals > 0).sum()
    total_dias = len(df_periodo)
    if total_dias > 0:
        return (dias_ocupados / total_dias) * 100
    return None


def calcular_revpar(adr, ocupacion):
    """
    Calcula RevPAR = ADR * (Ocupación / 100)
    """
    if adr is None or ocupacion is None:
        return None
    return adr * (ocupacion / 100)


def calcular_cambio(val_nuevo, val_anterior):
    """
    Calcula el porcentaje de cambio y retorna (pct_cambio, es_positivo)
    """
    if val_nuevo is None or val_anterior is None or pd.isna(val_nuevo) or pd.isna(val_anterior):
        return None, None
    if val_anterior == 0:
        return None, None
    pct = ((val_nuevo - val_anterior) / val_anterior) * 100
    return pct, pct >= 0
