"""
Componentes reutilizables de UI para Guestool.
Funciones de renderizado para Wizard, Guestool, Simuleitor, etc.
"""
import os
from pathlib import Path
import streamlit as st

from src.utils import (
    parse_int_input, parse_float_input, leer_archivo_datos,
    slugify, fmt_markup, fmt_num,
    cargar_config, guardar_config, invalidar_config, 
    default_empresa_config,
    normalizar_df_alojamientos,
    obtener_empresas, obtener_markups_empresa, guardar_markups_empresa,
    obtener_descuento_para_noches, obtener_apartamentos,
    obtener_descuentos_empresa, guardar_descuentos_empresa,
)

# Constants
WIZARD_STEPS = ["Empresa", "Archivo", "PriceLabs", "Markups", "Descuentos"]
DATA_DIR = Path("datos")


# =========================================================
# MARKUPS UI
# =========================================================
def render_markups_inputs_ui(empresa_id: str, key_prefix: str, labels_prefix: str = "Markup") -> tuple:
    """
    Renderiza los 3 campos de entrada para Airbnb, Booking, Web markups.
    Devuelve tupla (airbnb_txt, booking_txt, web_txt).
    
    Args:
        empresa_id: ID de la empresa
        key_prefix: Prefijo para las keys (ej: "wiz_m", "edit_airbnb")
        labels_prefix: Prefijo para las etiquetas (ej: "Markup", "")
    """
    m = obtener_markups_empresa(empresa_id)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        airbnb_txt = st.text_input(
            f"{labels_prefix} Airbnb (%)" if labels_prefix else "Airbnb (%)",
            value=fmt_markup(m["Airbnb"]),
            placeholder="0",
            key=f"{key_prefix}_airbnb"
        )
    with c2:
        booking_txt = st.text_input(
            f"{labels_prefix} Booking (%)" if labels_prefix else "Booking (%)",
            value=fmt_markup(m["Booking"]),
            placeholder="0",
            key=f"{key_prefix}_booking"
        )
    with c3:
        web_txt = st.text_input(
            f"{labels_prefix} Web (%)" if labels_prefix else "Web (%)",
            value=fmt_markup(m["Web"]),
            placeholder="0",
            key=f"{key_prefix}_web"
        )
    
    return airbnb_txt, booking_txt, web_txt


# =========================================================
# DESCUENTOS UI
# =========================================================
def render_descuentos_ui(key_prefix: str) -> list:
    """Tabla mejorada de descuentos por noches, sin spinners. Con botón para eliminar."""
    rows_key = f"{key_prefix}_rows"
    if rows_key not in st.session_state:
        st.session_state[rows_key] = []

    rows = st.session_state[rows_key]
    resultado = []

    if rows:
        cols_header = st.columns([1.5, 1.5, 1.5, 0.8])
        with cols_header[0]:
            st.markdown('<small style="color:#7a8fa6;font-weight:500">Desde (noches)</small>', unsafe_allow_html=True)
        with cols_header[1]:
            st.markdown('<small style="color:#7a8fa6;font-weight:500">Hasta (noches)</small>', unsafe_allow_html=True)
        with cols_header[2]:
            st.markdown('<small style="color:#7a8fa6;font-weight:500">Descuento (%)</small>', unsafe_allow_html=True)
        with cols_header[3]:
            st.markdown('<small style="color:#7a8fa6;font-weight:500">Acción</small>', unsafe_allow_html=True)
        
        for i, row in enumerate(rows):
            cols = st.columns([1.5, 1.5, 1.5, 0.8])
            with cols[0]:
                desde_str = st.text_input(
                    "Desde", value="",
                    key=f"{key_prefix}_desde_{i}",
                    label_visibility="collapsed",
                    placeholder=str(int(row.get("Desde", 1)))
                )
                try:
                    desde = int(desde_str) if desde_str else int(row.get("Desde", 1))
                    desde = max(1, min(365, desde))
                except:
                    desde = int(row.get("Desde", 1))
            
            with cols[1]:
                hasta_str = st.text_input(
                    "Hasta", value="",
                    key=f"{key_prefix}_hasta_{i}",
                    label_visibility="collapsed",
                    placeholder=str(int(row.get("Hasta", 1)))
                )
                try:
                    hasta = int(hasta_str) if hasta_str else int(row.get("Hasta", 1))
                    hasta = max(1, min(365, hasta))
                except:
                    hasta = int(row.get("Hasta", 1))
            
            with cols[2]:
                desc_val = float(row.get("Descuento (%)", 0.0))
                desc_str = st.text_input(
                    "Desc", value="",
                    key=f"{key_prefix}_desc_{i}",
                    label_visibility="collapsed",
                    placeholder="0" if desc_val == 0.0 else str(desc_val)
                )
                try:
                    desc = float(desc_str) if desc_str else desc_val
                    desc = max(0.0, min(100.0, desc))
                except:
                    desc = desc_val
            
            with cols[3]:
                if st.button("❌", key=f"{key_prefix}_del_{i}", help="Eliminar este rango", use_container_width=True):
                    st.session_state[rows_key].pop(i)
                    st.rerun()
            
            resultado.append({"Desde": desde, "Hasta": hasta, "Descuento (%)": desc})

    if st.button("Agregar rango", key=f"{key_prefix}_add", use_container_width=True):
        if rows:
            ultimo = max(int(r.get("Hasta", 1)) for r in rows)
            nd, nh = ultimo + 1, min(ultimo + 5, 365)
        else:
            nd, nh = 2, 3
        st.session_state[rows_key].append({"Desde": nd, "Hasta": nh, "Descuento (%)": 0.0})
        st.rerun()

    return resultado


def cargar_descuentos_en_ui(empresa_id: str, key_prefix: str, es_wizard_nuevo: bool = False):
    """Carga descuentos guardados o 3 rangos por defecto si no existen."""
    rows_key = f"{key_prefix}_rows"
    if rows_key not in st.session_state:
        if es_wizard_nuevo:
            st.session_state[rows_key] = [
                {"Desde": 1, "Hasta": 3, "Descuento (%)": 0.0},
                {"Desde": 4, "Hasta": 7, "Descuento (%)": 0.0},
                {"Desde": 8, "Hasta": 365, "Descuento (%)": 0.0}
            ]
        else:
            df = obtener_descuentos_empresa(empresa_id)
            if not df.empty:
                st.session_state[rows_key] = df.to_dict("records")
            else:
                st.session_state[rows_key] = [
                    {"Desde": 1, "Hasta": 3, "Descuento (%)": 0.0},
                    {"Desde": 4, "Hasta": 7, "Descuento (%)": 0.0},
                    {"Desde": 8, "Hasta": 365, "Descuento (%)": 0.0}
                ]


# =========================================================
# WIZARD STEPPER
# =========================================================
def render_stepper(paso_actual: int):
    partes = []
    for i, label in enumerate(WIZARD_STEPS, 1):
        if i < paso_actual:
            estado, icono = "done", "✓"
        elif i == paso_actual:
            estado, icono = "active", str(i)
        else:
            estado, icono = "pending", str(i)

        partes.append(f"""
        <div class="wizard-step-wrap">
            <div class="wizard-step-circle {estado}">{icono}</div>
            <div class="wizard-step-label {estado}">{label}</div>
        </div>
        """)
        if i < len(WIZARD_STEPS):
            line_cls = "done" if i < paso_actual else ""
            partes.append(f'<div class="wizard-step-line {line_cls}"></div>')

    st.markdown(f'<div class="wizard-stepper">{"".join(partes)}</div>', unsafe_allow_html=True)


# =========================================================
# WIZARD STEPS
# =========================================================
def wizard_paso1():
    st.write('<div id="wizard-paso-1" style="scroll-margin-top: 120px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="wizard-step-content">', unsafe_allow_html=True)
    st.markdown("#### Nombre de la empresa")
    st.markdown('<p style="color:#7a8fa6;font-size:0.9rem;margin-top:-0.5rem;">Introduce el nombre tal como quieres que aparezca en la app.</p>', unsafe_allow_html=True)

    nombre = st.text_input(
        "Nombre", value=st.session_state.wizard_empresa_nombre,
        placeholder="Ej: Inmalaga", key="wiz_nombre"
    )
    st.markdown('<div style="height:0.8rem"></div>', unsafe_allow_html=True)

    if st.button("Continuar →", key="wiz_p1_next"):
        nombre = nombre.strip()
        if not nombre:
            st.error("Introduce un nombre para continuar.")
        else:
            empresa_id = slugify(nombre)
            config = cargar_config()
            if empresa_id in config:
                ruta = DATA_DIR / config[empresa_id].get("archivo_csv", f"{empresa_id}.csv")
                if ruta.exists():
                    st.warning(f"⚠️ Ya existe **{config[empresa_id]['nombre']}**. Continuando sobreescribirás sus datos.")
            
            # 🔧 LIMPIAR CACHE DE SESSION_STATE AL CAMBIAR DE EMPRESA
            old_id = st.session_state.get("wizard_empresa_id", "")
            if old_id and old_id != empresa_id:
                # Limpiar datos de la empresa anterior
                st.session_state.pop(f"pricelabs_data_{old_id}", None)
                print(f"[DEBUG] Limpiado session_state para empresa anterior: {old_id}", file=sys.stderr)
            
            st.session_state.wizard_empresa_nombre = nombre
            st.session_state.wizard_empresa_id     = empresa_id
            st.session_state.wizard_step           = 2
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def wizard_paso2():
    st.write('<div id="wizard-paso-2" style="scroll-margin-top: 120px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="wizard-step-content">', unsafe_allow_html=True)
    empresa = st.session_state.wizard_empresa_nombre
    st.markdown(f"#### Archivo de alojamientos · *{empresa}*")
    st.markdown('<p style="color:#7a8fa6;font-size:0.9rem;margin-top:-0.5rem;">Sube un CSV o Excel con columna de nombre y coste de limpieza.</p>', unsafe_allow_html=True)

    archivo = st.file_uploader("Selecciona archivo", type=["csv", "xlsx"], key="wiz_archivo")
    if archivo:
        try:
            df = leer_archivo_datos(archivo)
            df_limpio = normalizar_df_alojamientos(df)
            st.success(f"✅ {len(df_limpio)} alojamientos detectados")
            with st.expander("Vista previa", expanded=False):
                st.dataframe(df_limpio, use_container_width=True, hide_index=True)
            st.session_state.wizard_df_limpio = df_limpio
        except Exception as e:
            st.error(f"❌ {e}")
            st.session_state.wizard_df_limpio = None

    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("← Atrás", key="wiz_p2_back"):
            st.session_state.wizard_step = 1
            st.rerun()
    with cols[1]:
        if st.button("Continuar →", key="wiz_p2_next"):
            if st.session_state.wizard_df_limpio is None:
                st.error("Sube un archivo válido para continuar.")
            else:
                st.session_state.wizard_step = 3
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def wizard_paso3_data():
    st.write('<div id="wizard-paso-3" style="scroll-margin-top: 120px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="wizard-step-content">', unsafe_allow_html=True)
    empresa = st.session_state.wizard_empresa_nombre
    st.markdown(f"#### 📊 Datos de PriceLabs · *{empresa}*")
    st.markdown('<p style="color:#7a8fa6;font-size:0.9rem;margin-top:-0.5rem;">Carga excels de PriceLabs para todos los años que tengas. El sistema detectará automáticamente el año de cada archivo. <strong>(Opcional)</strong></p>', unsafe_allow_html=True)

    archivos = st.file_uploader(
        "Selecciona uno o varios archivos Excel/CSV",
        type=["xlsx", "csv"],
        accept_multiple_files=True,
        key="wiz_pricelabs_files"
    )

    archivos_pricelabs = st.session_state.get("wiz_pricelabs_archivos", {})
    
    if archivos:
        st.markdown("#### 📋 Archivos cargados:")
        try:
            from io import BytesIO
            import pandas as pd
            from src.utils.text import normalizar_texto
            import sys
            
            print(f"[DEBUG PASO3] Cargando {len(archivos)} archivos en paso 3", file=sys.stderr)
            
            for archivo in archivos:
                df_raw = pd.read_excel(BytesIO(archivo.getvalue())) if archivo.name.endswith('.xlsx') else pd.read_csv(BytesIO(archivo.getvalue()))
                
                # Detectar año
                columnas_norm = {c: normalizar_texto(c) for c in df_raw.columns}
                col_fecha = None
                for col, norm in columnas_norm.items():
                    if "fecha" in norm:
                        col_fecha = col
                        break
                
                if col_fecha:
                    df_temp = df_raw.copy()
                    df_temp["fecha"] = pd.to_datetime(df_temp[col_fecha], errors="coerce")
                    año_predominante = df_temp["fecha"].dt.year.value_counts().idxmax() if len(df_temp["fecha"].dt.year.dropna()) > 0 else None
                else:
                    año_predominante = None
                
                if año_predominante:
                    archivos_pricelabs[int(año_predominante)] = archivo
                    print(f"[DEBUG PASO3] ✓ {archivo.name} → Año {año_predominante}", file=sys.stderr)
                    st.success(f"✅ {archivo.name} → **Año {año_predominante}** ({len(df_raw)} filas)")
                else:
                    print(f"[DEBUG PASO3] ✗ {archivo.name} → No se pudo detectar año", file=sys.stderr)
                    st.warning(f"⚠️ {archivo.name} → No se pudo detectar el año")
            
            st.session_state["wiz_pricelabs_archivos"] = archivos_pricelabs
            print(f"[DEBUG PASO3] Guardado en session_state: {list(archivos_pricelabs.keys())}", file=sys.stderr)
        except Exception as e:
            st.error(f"❌ Error procesando archivos: {e}")
            print(f"[DEBUG PASO3] Excepción: {e}", file=sys.stderr)
            import traceback
            print(traceback.format_exc(), file=sys.stderr)
    elif archivos_pricelabs:
        print(f"[DEBUG PASO3] Archivos ya cargados previamente: {list(archivos_pricelabs.keys())}", file=sys.stderr)
        st.markdown("#### 📋 Archivos previsamente cargados:")
        años_cargados = sorted(archivos_pricelabs.keys())
        for año in años_cargados:
            st.success(f"✅ Año {año}")

    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("← Atrás", key="wiz_p3_back"):
            st.session_state.wizard_step = 2
            st.rerun()
    with cols[1]:
        if st.button("Continuar →", key="wiz_p3_next"):
            st.session_state.wizard_step = 4
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def wizard_paso4_markups():
    st.write('<div id="wizard-paso-4" style="scroll-margin-top: 120px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="wizard-step-content">', unsafe_allow_html=True)
    empresa_id = st.session_state.wizard_empresa_id
    empresa    = st.session_state.wizard_empresa_nombre
    st.markdown(f"#### 💳 Markups por canal · *{empresa}*")
    st.markdown('<p style="color:#7a8fa6;font-size:0.9rem;margin-top:-0.5rem;">Porcentaje de comisión que aplica cada OTA. Define tus markups por canal.</p>', unsafe_allow_html=True)

    airbnb_txt, booking_txt, web_txt = render_markups_inputs_ui(empresa_id, "wiz_m", labels_prefix="Markup")

    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("← Atrás", key="wiz_p4_back"):
            st.session_state.wizard_step = 3
            st.rerun()
    with cols[1]:
        if st.button("Continuar →", key="wiz_p4_next"):
            try:
                airbnb  = parse_float_input(airbnb_txt  or "0", "Markup Airbnb")
                booking = parse_float_input(booking_txt or "0", "Markup Booking")
                web     = parse_float_input(web_txt     or "0", "Markup Web")
                st.session_state["wiz_markups"] = {"Airbnb": airbnb, "Booking": booking, "Web": web}
                st.session_state.wizard_step = 5
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")

    st.markdown('</div>', unsafe_allow_html=True)


def wizard_paso5_estrategia():
    st.write('<div id="wizard-paso-5" style="scroll-margin-top: 120px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="wizard-step-content">', unsafe_allow_html=True)
    empresa_id = st.session_state.wizard_empresa_id
    empresa    = st.session_state.wizard_empresa_nombre
    st.markdown(f"#### 💰 Estrategia tarifaria · *{empresa}*")
    st.markdown('<p style="color:#7a8fa6;font-size:0.9rem;margin-top:-0.5rem;">Define descuentos por duración de estancia para optimizar conversiones.</p>', unsafe_allow_html=True)

    cargar_descuentos_en_ui(empresa_id, "wiz_desc", es_wizard_nuevo=True)
    filas_desc = render_descuentos_ui("wiz_desc")

    st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)

    markups = st.session_state.get("wiz_markups", {})
    df_prev = st.session_state.wizard_df_limpio
    archivos_pl = st.session_state.get("wiz_pricelabs_archivos", {})
    
    import sys
    print(f"[DEBUG PASO5] Archivos en session_state: {list(archivos_pl.keys()) if archivos_pl else 'NINGUNO'}", file=sys.stderr)

    with st.expander("📋 Resumen antes de guardar", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Empresa",      empresa)
        c2.metric("Alojamientos", len(df_prev) if df_prev is not None else 0)
        c3.metric("Años PriceLabs", len(archivos_pl) if archivos_pl else 0)
        
        if archivos_pl:
            años_cargados = ", ".join(map(str, sorted(archivos_pl.keys())))
            st.success(f"✅ Datos PriceLabs: {años_cargados}")
        else:
            st.info("ℹ️ Sin datos de PriceLabs (opcional)")

    st.markdown('<div style="height:0.4rem"></div>', unsafe_allow_html=True)
    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("← Atrás", key="wiz_p5_back"):
            st.session_state.wizard_step = 4
            st.rerun()
    with cols[1]:
        if st.button("✅ Guardar todo", key="wiz_p5_save", type="primary"):
            try:
                from src.utils.files import guardar_pricelabs_excel, default_empresa_config, cargar_config, guardar_config, invalidar_config
                from src.utils.company_data import guardar_markups_empresa
                import sys
                
                print(f"[DEBUG PASO5_SAVE] Iniciando guardado...", file=sys.stderr)
                print(f"[DEBUG PASO5_SAVE] Archivos a guardar: {len(archivos_pl)} años", file=sys.stderr)
                
                config = cargar_config()
                if empresa_id not in config:
                    config[empresa_id] = default_empresa_config(empresa, f"{empresa_id}.csv")
                else:
                    config[empresa_id]["nombre"]      = empresa
                    config[empresa_id]["archivo_csv"] = f"{empresa_id}.csv"
                guardar_config(config)

                ruta_csv = DATA_DIR / f"{empresa_id}.csv"
                df_prev.to_csv(ruta_csv, index=False, encoding="utf-8")

                m = markups
                guardar_markups_empresa(empresa_id, m.get("Airbnb", 0), m.get("Booking", 0), m.get("Web", 0))

                filas_validas = [f for f in filas_desc if f["Hasta"] >= f["Desde"]]
                config2 = cargar_config()
                config2[empresa_id]["descuentos"] = filas_validas
                guardar_config(config2)
                
                # Guardar PriceLabs archivos si existen
                if archivos_pl:
                    archivos_list = list(archivos_pl.values())
                    print(f"[DEBUG PASO5_SAVE] Pasando {len(archivos_list)} archivos a guardar_pricelabs_excel", file=sys.stderr)
                    guardar_pricelabs_excel(empresa_id, archivos_list)
                else:
                    print(f"[DEBUG PASO5_SAVE] Sin archivos de PriceLabs para guardar", file=sys.stderr)
                
                invalidar_config()
                st.session_state.pop("wiz_desc_rows", None)

                msg = f"✓ **{empresa}** guardada con {len(df_prev)} alojamientos"
                if archivos_pl:
                    msg += f" y datos de {len(archivos_pl)} año(s)"
                st.success(msg + ".")

                # 🔧 LIMPIAR TODOS LOS CACHES DEL WIZARD Y PRICELABS
                import sys
                st.session_state.wizard_step           = 1
                st.session_state.wizard_empresa_nombre = ""
                old_empresa_id = st.session_state.get("wizard_empresa_id", "")
                st.session_state.wizard_empresa_id     = ""
                st.session_state.wizard_df_limpio      = None
                st.session_state.pop("wiz_markups", None)
                st.session_state.pop("wiz_pricelabs_archivos", None)
                
                # Limpiar session_state del pricelabs cacheado
                if old_empresa_id:
                    st.session_state.pop(f"pricelabs_data_{old_empresa_id}", None)
                    print(f"[DEBUG PASO5_SAVE] Limpiado session_state para: {old_empresa_id}", file=sys.stderr)
                
                # También limpiar de TODOS los empresas cacheadas (por si hay contaminación)
                keys_a_limpiar = [k for k in st.session_state.keys() if k.startswith("pricelabs_data_")]
                for key in keys_a_limpiar:
                    st.session_state.pop(key, None)
                    print(f"[DEBUG PASO5_SAVE] Limpiado key: {key}", file=sys.stderr)

            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
                import traceback
                print(f"[DEBUG PASO5_SAVE] Excepción: {e}", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                st.error(traceback.format_exc())

    st.markdown('</div>', unsafe_allow_html=True)


def wizard_editar():
    st.markdown("#### Editar empresa existente")
    st.markdown('<p style="color:#7a8fa6;font-size:0.9rem;margin-top:-0.5rem;">Selecciona la empresa y modifica lo que necesites. Cada bloque se guarda por separado.</p>', unsafe_allow_html=True)

    empresas = obtener_empresas()
    if not empresas:
        st.info("No hay empresas registradas. Usa 'Nueva empresa' para crear una.")
        return

    opciones    = {nombre: eid for eid, nombre in empresas}
    empresa_sel = st.selectbox("Empresa", list(opciones.keys()), key="edit_empresa_sel")
    empresa_id  = opciones[empresa_sel]

    st.markdown("---")

    with st.expander("📁 Reemplazar archivo de alojamientos", expanded=False):
        archivo = st.file_uploader("Nuevo CSV o Excel", type=["csv", "xlsx"], key=f"edit_archivo_{empresa_id}")
        if archivo:
            try:
                df_nuevo = normalizar_df_alojamientos(leer_archivo_datos(archivo))
                st.success(f"✅ {len(df_nuevo)} alojamientos detectados")
                with st.expander("Vista previa", expanded=False):
                    st.dataframe(df_nuevo, use_container_width=True, hide_index=True)
                if st.button("Guardar archivo", key=f"edit_save_archivo_{empresa_id}"):
                    ruta = DATA_DIR / f"{empresa_id}.csv"
                    df_nuevo.to_csv(ruta, index=False, encoding="utf-8")
                    invalidar_config()
                    st.success("✅ Archivo actualizado.")
            except Exception as e:
                st.error(f"❌ {e}")

    with st.expander("📊 Datos de PriceLabs", expanded=False):
        st.markdown("Carga nuevos excels para **reemplazar o añadir** años de datos de PriceLabs.")
        archivos = st.file_uploader(
            "Selecciona uno o varios archivos Excel/CSV",
            type=["xlsx", "csv"],
            accept_multiple_files=True,
            key=f"edit_pricelabs_{empresa_id}"
        )
        
        if archivos:
            st.markdown("##### 📋 Archivos a cargar:")
            archivos_nuevos = {}
            try:
                from io import BytesIO
                import pandas as pd
                from src.utils.text import normalizar_texto
                
                for archivo in archivos:
                    df_raw = pd.read_excel(BytesIO(archivo.getvalue())) if archivo.name.endswith('.xlsx') else pd.read_csv(BytesIO(archivo.getvalue()))
                    
                    # Detectar año
                    columnas_norm = {c: normalizar_texto(c) for c in df_raw.columns}
                    col_fecha = None
                    for col, norm in columnas_norm.items():
                        if "fecha" in norm:
                            col_fecha = col
                            break
                    
                    if col_fecha:
                        df_temp = df_raw.copy()
                        df_temp["fecha"] = pd.to_datetime(df_temp[col_fecha], errors="coerce")
                        año_predominante = df_temp["fecha"].dt.year.value_counts().idxmax() if len(df_temp["fecha"].dt.year.dropna()) > 0 else None
                    else:
                        año_predominante = None
                    
                    if año_predominante:
                        archivos_nuevos[int(año_predominante)] = archivo
                        st.success(f"✅ {archivo.name} → **Año {año_predominante}** ({len(df_raw)} filas)")
                    else:
                        st.warning(f"⚠️ {archivo.name} → No se pudo detectar el año")
                
                if archivos_nuevos:
                    if st.button("💾 Guardar datos PriceLabs", key=f"edit_save_pricelabs_{empresa_id}"):
                        try:
                            from src.utils.files import guardar_pricelabs_excel
                            
                            guardar_pricelabs_excel(empresa_id, list(archivos_nuevos.values()))
                            st.success(f"✅ Datos PriceLabs actualizados: {', '.join(map(str, sorted(archivos_nuevos.keys())))} años guardados.")
                        except Exception as e:
                            st.error(f"❌ Error al guardar: {e}")
                            import traceback
                            st.error(traceback.format_exc())
            except Exception as e:
                st.error(f"❌ Error procesando archivos: {e}")

    with st.expander("⚙️ Markups por canal", expanded=False):
        a_txt, b_txt, w_txt = render_markups_inputs_ui(empresa_id, f"edit_{empresa_id}", labels_prefix="")
        if st.button("Guardar markups", key=f"edit_save_markups_{empresa_id}"):
            try:
                guardar_markups_empresa(
                    empresa_id,
                    parse_float_input(a_txt or "0", "Airbnb"),
                    parse_float_input(b_txt or "0", "Booking"),
                    parse_float_input(w_txt or "0", "Web"),
                )
                st.success("✅ Markups guardados.")
            except ValueError as e:
                st.error(f"❌ {e}")

    with st.expander("📊 Descuentos por noches", expanded=False):
        kp = f"edit_desc_{empresa_id}"
        cargar_descuentos_en_ui(empresa_id, kp)
        filas = render_descuentos_ui(kp)
        if st.button("Guardar descuentos", key=f"edit_save_desc_{empresa_id}"):
            filas_validas = [f for f in filas if f["Hasta"] >= f["Desde"]]
            config = cargar_config()
            config[empresa_id]["descuentos"] = filas_validas
            guardar_config(config)
            invalidar_config()
            st.success("✅ Descuentos guardados.")

    # ===== ELIMINAR EMPRESA (ZONA PELIGROSA) =====
    with st.expander("🗑️ Eliminar empresa (irreversible)", expanded=False):
        st.markdown('<p style="color:#ff6b6b;font-weight:bold;">⚠️ Esta acción eliminará TODOS los datos de la empresa: archivo de alojamientos, datos de PriceLabs, markups y descuentos.</p>', unsafe_allow_html=True)
        
        # Mostrar selector de empresa para confirmar
        empresa_confirmar = st.selectbox(
            "Selecciona la empresa a eliminar para confirmar:",
            options=list(opciones.keys()),
            index=0,
            key=f"delete_confirm_select_{empresa_id}"
        )
        
        if st.button("🗑️ Eliminar empresa completamente", key=f"delete_empresa_{empresa_id}", type="secondary"):
            if empresa_confirmar == empresa_sel:
                try:
                    import os
                    from pathlib import Path
                    
                    # Eliminar archivo CSV de alojamientos
                    ruta_csv = DATA_DIR / f"{empresa_id}.csv"
                    if ruta_csv.exists():
                        os.remove(ruta_csv)
                    
                    # Eliminar TODOS los archivos de PriceLabs (excels)
                    for archivo_pricelabs in DATA_DIR.glob(f"{empresa_id}_pricelabs_*"):
                        try:
                            os.remove(archivo_pricelabs)
                        except Exception as e:
                            st.warning(f"⚠️ No se pudo eliminar {archivo_pricelabs.name}: {e}")
                    
                    # Eliminar de configuración
                    config = cargar_config()
                    if empresa_id in config:
                        del config[empresa_id]
                        guardar_config(config)
                    
                    invalidar_config()
                    
                    st.success(f"✅ Empresa '{empresa_sel}' eliminada completamente (incluidos todos sus excels).")
                    st.session_state.wizard_mode = "nuevo"
                    st.session_state.wizard_step = 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al eliminar: {e}")
                    import traceback
                    st.error(traceback.format_exc())
            else:
                st.error(f"❌ La empresa seleccionada no coincide. Debes seleccionar '{empresa_sel}' para confirmar.")



# =========================================================
# SECTION WIZARD
# =========================================================
def section_wizard():
    st.markdown(
        '<div class="dashboard-card">'
        '<div class="section-title">🧙 Wizard</div>'
        '<div class="section-subtitle">Alta y edición de empresas en un flujo guiado</div>',
        unsafe_allow_html=True
    )

    modo       = st.session_state.wizard_mode
    tab_nuevo  = "active" if modo == "nuevo"  else ""
    tab_editar = "active" if modo == "editar" else ""

    st.markdown(f"""
    <div class="wizard-mode-tabs">
        <div class="wizard-mode-tab {tab_nuevo}"  id="wiz-tab-nuevo">✨ Nueva empresa</div>
        <div class="wizard-mode-tab {tab_editar}" id="wiz-tab-editar">✏️ Editar empresa</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="display:none!important;visibility:hidden;height:0;overflow:hidden;position:absolute;">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("tab_nuevo", key="wiz_tab_nuevo_btn"):
            st.session_state.wizard_mode = "nuevo"
            st.session_state.wizard_step = 1
            st.rerun()
    with c2:
        if st.button("tab_editar", key="wiz_tab_editar_btn"):
            st.session_state.wizard_mode = "editar"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <script>
    (function() {
        function wireWizardTabs() {
            ['wiz-tab-nuevo', 'wiz-tab-editar'].forEach(elemId => {
                const elem = document.getElementById(elemId);
                if (!elem || elem._wired) return;
                elem._wired = true;
                elem.style.cursor = 'pointer';
                
                elem.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const label = elemId === 'wiz-tab-nuevo' ? 'tab_nuevo' : 'tab_editar';
                    const btns = window.parent.document.querySelectorAll('button');
                    for (const btn of btns) {
                        if (btn.innerText.trim() === label) { btn.click(); break; }
                    }
                });
            });
        }
        wireWizardTabs();
        let attempts = 0;
        const t = setInterval(() => { wireWizardTabs(); if (++attempts > 50) clearInterval(t); }, 100);
    })();
    </script>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:0.3rem"></div>', unsafe_allow_html=True)

    if modo == "nuevo":
        render_stepper(st.session_state.wizard_step)
        paso = st.session_state.wizard_step
        if paso == 1:   wizard_paso1()
        elif paso == 2: wizard_paso2()
        elif paso == 3: wizard_paso3_data()
        elif paso == 4: wizard_paso4_markups()
        elif paso == 5: wizard_paso5_estrategia()
    else:
        wizard_editar()

    paso_actual = st.session_state.wizard_step
    st.markdown(f"""
    <script>
    (function() {{
        const targetId = 'wizard-paso-{paso_actual}';
        const scrollWait = () => {{
            const el = document.getElementById(targetId);
            if (el) {{
                el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }} else {{
                setTimeout(scrollWait, 50);
            }}
        }};
        scrollWait();
    }})();
    </script>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# SECTION GUESTOOL
# =========================================================
def section_guestool(section_simuleitor, section_rentabileitor):
    """Selector entre Simuleitor y Rentabileitor PRO."""
    sub = st.session_state.guestool_sub

    if sub is None:
        st.markdown(
            '<div class="dashboard-card">'
            '<div class="section-title">⚡ Guestool</div>'
            '<div class="section-subtitle">Herramientas de precio · elige una opción</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="subnav-grid">
            <div class="subnav-card" id="sub-sim">
                <div class="subnav-card-icon">📊</div>
                <div class="subnav-card-title">Simuleitor</div>
                <div class="subnav-card-desc">Comparativa de precio por canal</div>
            </div>
            <div class="subnav-card" id="sub-rent">
                <div class="subnav-card-icon">📈</div>
                <div class="subnav-card-title">Rentabileitor PRO</div>
                <div class="subnav-card-desc">Forecast 2026 vs 2025 · precio objetivo</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="display:none!important;visibility:hidden;height:0;overflow:hidden;position:absolute;">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("sub_sim", key="sub_sim_btn"):
                st.session_state.guestool_sub = "Simuleitor"
                st.rerun()
        with c2:
            if st.button("sub_rent", key="sub_rent_btn"):
                st.session_state.guestool_sub = "Rentabileitor"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <script>
        (function() {
            function wireGuestoolLinks() {
                ['sub-sim', 'sub-rent'].forEach(elemId => {
                    const elem = document.getElementById(elemId);
                    if (!elem || elem._wired) return;
                    elem._wired = true;
                    elem.style.cursor = 'pointer';
                    elem.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const label = elemId === 'sub-sim' ? 'sub_sim' : 'sub_rent';
                        const btns = window.parent.document.querySelectorAll('button');
                        for (const btn of btns) {
                            if (btn.innerText.trim() === label) { btn.click(); break; }
                        }
                    });
                });
            }
            wireGuestoolLinks();
            let attempts = 0;
            const interval = setInterval(() => { wireGuestoolLinks(); if (++attempts > 50) clearInterval(interval); }, 100);
        })();
        </script>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    elif sub == "Simuleitor":
        if st.button("← Guestool", key="back_to_guestool_sim"):
            st.session_state.guestool_sub = None
            st.rerun()
        section_simuleitor()

    elif sub == "Rentabileitor":
        if st.button("← Guestool", key="back_to_guestool_rent"):
            st.session_state.guestool_sub = None
            st.rerun()
        section_rentabileitor()


# =========================================================
# SIMULEITOR
# =========================================================
def section_simuleitor():
    st.markdown(
        '<div class="dashboard-card">'
        '<div class="section-title">📊 Simuleitor</div>'
        '<div class="section-subtitle">Compara los tres canales usando el apartamento seleccionado.</div>',
        unsafe_allow_html=True
    )

    empresas = obtener_empresas()
    if not empresas:
        st.info("No hay empresas todavía. Crea una desde el Wizard.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    opciones    = {nombre: eid for eid, nombre in empresas}
    empresa_sel = st.selectbox("Empresa", list(opciones.keys()), key="sim_empresa")
    empresa_id  = opciones[empresa_sel]

    datos = obtener_apartamentos(empresa_id)
    if not datos:
        st.info("Esta empresa no tiene alojamientos.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    apartamentos = {nombre: float(limpieza) for nombre, limpieza in datos}
    apt      = st.selectbox("Apartamento", list(apartamentos.keys()), key="sim_apartamento")
    limpieza = apartamentos[apt]

    c1, c2 = st.columns(2)
    with c1:
        precio_txt = st.text_input("Precio medio", "0", key="sim_precio")
    with c2:
        noches_txt = st.text_input("Noches", "2", key="sim_noches")

    c3, c4 = st.columns(2)
    with c3:
        st.text_input("Limpieza (€)", value=f"{limpieza:.2f}", disabled=True, key=f"sim_limp_{apt}")
    with c4:
        promo = st.selectbox("Promo Booking", ["Sin promo", "Genius 2 (23.5%)", "Genius 3 (27.75%)"], key="sim_promo")

    promo_val = 0.0
    if "23.5"  in promo: promo_val = 23.5
    if "27.75" in promo: promo_val = 27.75

    if st.button("Calcular", key="sim_calc_btn"):
        try:
            precio    = parse_float_input(precio_txt, "Precio medio", minimo=0)
            noches    = parse_int_input(noches_txt, "Noches", minimo=1)
            descuento = obtener_descuento_para_noches(empresa_id, noches)

            if descuento is None:
                st.error("No hay descuento configurado para ese número de noches.")
            else:
                markups   = obtener_markups_empresa(empresa_id)
                resultados = {}
                for canal in ["Airbnb", "Booking", "Web"]:
                    pc = precio * (1 + markups[canal] / 100)
                    if canal == "Booking":
                        pc *= (1 - promo_val / 100)
                    pf    = pc * (1 - descuento / 100) + limpieza / noches
                    total = pf * noches
                    resultados[canal] = {"noche": pf, "total": total}

                mejor = min(r["total"] for r in resultados.values())
                st.write("### Resultado")
                cols = st.columns(3)
                for i, (col, canal) in enumerate(zip(cols, ["Airbnb", "Booking", "Web"])):
                    data = resultados[canal]
                    css  = "kpi-card" + (" kpi-good" if data["total"] == mejor else "")
                    with col:
                        st.markdown(f"""
                        <div class="{css}" style="animation-delay:{i*0.1}s">
                            <div class="kpi-title">{canal}</div>
                            <div class="kpi-sub">precio por noche</div>
                            <div class="kpi-value">{data["noche"]:.2f} <span style="font-size:0.85rem;color:#9aafbf">€</span></div>
                            <div class="kpi-sub" style="margin-top:14px">total estancia</div>
                            <div class="kpi-total">{data["total"]:,.2f}<span class="kpi-currency">€</span></div>
                        </div>""", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# NAVEGACIÓN
# =========================================================
def render_nav():
    st.markdown('<div class="header-wrap">', unsafe_allow_html=True)
    col_logo, col_title = st.columns([1.1, 4.9], gap="small")
    with col_logo:
        st.markdown('<div class="header-logo-wrap">', unsafe_allow_html=True)
        if os.path.exists("logo.png"):
            st.image("logo.png", width=140)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_title:
        st.markdown("""
        <div class="header-text-wrap">
            <div class="top-eyebrow">Panel de control</div>
            <div class="top-title">Revenue <span>Dashboard</span></div>
            <div class="top-subtitle">Elige un módulo para trabajar</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:1.4rem"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="nav-grid">
        <div class="nav-card" id="nc-wizard">
            <div class="nav-card-icon">🧙</div>
            <div class="nav-card-title">Wizard</div>
            <div class="nav-card-desc">Alta y edición de empresas · alojamientos · markups · descuentos</div>
        </div>
        <div class="nav-card" id="nc-guestool">
            <div class="nav-card-icon">⚡</div>
            <div class="nav-card-title">Guestool</div>
            <div class="nav-card-desc">Simuleitor y Rentabileitor · herramientas de precio</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hidden-nav-btns" style="display:none!important;visibility:hidden;height:0;overflow:hidden;position:absolute;">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Wizard", key="nav_wizard"):
            st.session_state.active_section = "Wizard"
            st.session_state.wizard_step = 1
            st.session_state.wizard_mode = "nuevo"
            st.rerun()
    with c2:
        if st.button("Guestool", key="nav_guestool"):
            st.session_state.active_section = "Guestool"
            st.session_state.guestool_sub = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <script>
    (function() {
        const wireMap = {
            'nc-wizard': 'Wizard',
            'nc-guestool': 'Guestool',
            'wiz-tab-nuevo': 'tab_nuevo',
            'wiz-tab-editar': 'tab_editar',
            'sub-sim': 'sub_sim',
            'sub-rent': 'sub_rent'
        };
        
        function findButtonByText(btnLabel) {
            const allBtns = window.parent.document.querySelectorAll('button');
            for (const btn of allBtns) {
                const btnText = btn.innerText.trim();
                if (btnText === btnLabel) { return btn; }
            }
            return null;
        }
        
        function wireCardClicks() {
            Object.entries(wireMap).forEach(([elemId, btnLabel]) => {
                const elem = document.getElementById(elemId);
                if (!elem || elem._card_wired) return;
                elem._card_wired = true;
                elem.style.cursor = 'pointer';
                elem.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const btn = findButtonByText(btnLabel);
                    if (btn) { btn.click(); }
                });
            });
        }
        
        wireCardClicks();
        let attempts = 0;
        const interval = setInterval(() => {
            wireCardClicks();
            if (++attempts > 50) clearInterval(interval);
        }, 100);
    })();
    </script>
    """, unsafe_allow_html=True)

    st.markdown('<div class="cards-divider"></div>', unsafe_allow_html=True)


def render_header_compacto():
    """Header reducido cuando hay sección activa."""
    col_logo, col_title = st.columns([1.1, 4.9], gap="small")
    with col_logo:
        st.markdown('<div style="display:flex;align-items:center;justify-content:center;min-height:54px;">', unsafe_allow_html=True)
        if os.path.exists("logo.png"):
            st.image("logo.png", width=90)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_title:
        st.markdown(
            '<div style="display:flex;flex-direction:column;justify-content:center;min-height:54px;">'
            '<div class="top-eyebrow">Panel de control</div>'
            '<div class="top-title" style="font-size:1.55rem;letter-spacing:-0.03em;">'
            'Revenue <span>Dashboard</span></div>'
            '</div>',
            unsafe_allow_html=True
        )
    st.markdown('<div class="cards-divider" style="margin:10px 0 14px 0;"></div>', unsafe_allow_html=True)


def render_back(label="← Volver al inicio"):
    st.markdown('<div class="back-btn-wrap">', unsafe_allow_html=True)
    if st.button(label, key="btn_back_main"):
        st.session_state.active_section = None
        st.session_state.guestool_sub   = None
        st.session_state.wizard_step    = 1
        st.session_state.wizard_mode    = "nuevo"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
