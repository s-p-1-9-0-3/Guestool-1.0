"""
Sección Rentabileitor PRO - Análisis comparativo de PriceLabs 2025 vs 2026
"""
import math
from datetime import datetime
import pandas as pd
import streamlit as st


def section_rentabileitor(
    obtener_empresas,
    obtener_apartamentos,
    cargar_pricelabs_excel,
    detectar_cambios_pricelabs,
    procesar_pricelabs_excel,
    buscar_mejor_match_apartamento,
    calcular_los_desde_ocupacion,
    guardar_pricelabs_excel,
    parse_int_input,
    parse_float_input,
    fmt_num,
    obtener_descuento_para_noches,
    obtener_markups_empresa,
    calcular_rentabileitor_pro_2026_vs_2025,
):
    """
    Renderiza la sección Rentabileitor PRO con análisis comparativo de PriceLabs.
    
    Requiere funciones auxiliares pasadas como parámetros para evitar circularidad.
    """
    st.markdown(
        '<div class="dashboard-card">'
        '<div class="section-title">📈 Rentabileitor PRO</div>'
        '<div class="section-subtitle">Configura los datos y ve los resultados de inmediato. Los pasos iniciales se pueden contraer.</div>',
        unsafe_allow_html=True
    )

    # ================== LAYOUT 2 COLUMNAS: INPUTS (IZQ 35%) + RESULTADOS (DER 65%) ==================
    col_left, col_right = st.columns([0.35, 0.65])

    # ================== COLUMNA IZQUIERDA: SELECTORES E INPUTS ==================
    with col_left:
        with st.expander("⚙️ 1. Empresa, datos y apartamento", expanded=False):
            # PASO 1: EMPRESA
            st.markdown("**Empresa**")
            empresas = obtener_empresas()
            if not empresas:
                st.info("No hay empresas todavía")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            opciones = {nombre: empresa_id for empresa_id, nombre in empresas}
            empresa_sel = st.selectbox("Empresa", list(opciones.keys()), index=None, placeholder="Selecciona...", key="rent_empresa", label_visibility="collapsed")
            
            if not empresa_sel:
                st.warning("Selecciona una empresa para continuar.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            
            empresa_id = opciones[empresa_sel]

            datos = obtener_apartamentos(empresa_id)
            if not datos:
                st.warning("No hay apartamentos en esta empresa")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            apartamentos_app = {nombre: float(limpieza) for nombre, limpieza in datos}
            
            # PASO 2: DATOS DE PRICELABS - CARGADOS DESDE EL WIZARD
            # Crear clave única para caché basada en empresa_id
            cache_key = f"pricelabs_procesados_{empresa_id}"
            
            dfs_por_anyo = {}
            dfs_cached = cargar_pricelabs_excel(empresa_id)
            hay_archivos_cached = bool(dfs_cached)
            años_cached = sorted(list(dfs_cached.keys())) if dfs_cached else []
            
            if not hay_archivos_cached:
                st.warning("⚠️ No hay datos de PriceLabs. Primero ve al Wizard para cargarlos.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            
            # Mostrar solo mensaje de carga correcta
            st.success(f"✅ Carga de datos correcta")
            
            # Usar caché de session_state para no reprocesar
            if cache_key not in st.session_state:
                # Primera vez: procesar y guardar en session_state
                try:
                    for anyo, df_raw in dfs_cached.items():
                        dfs_por_anyo[anyo] = procesar_pricelabs_excel(df_raw, f"pricelabs_{anyo}.xlsx", anyo)
                    st.session_state[cache_key] = dfs_por_anyo
                except Exception as e:
                    st.error(f"❌ Error procesando datos: {e}")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
            else:
                # Usar el caché
                dfs_por_anyo = st.session_state[cache_key]
            
            # Permite recargar si hay cambios
            hay_cambios = detectar_cambios_pricelabs(empresa_id)
            if hay_cambios:
                if st.button("🔄 Recargar datos", key="reload_pricelabs"):
                    del st.session_state[cache_key]
                    st.rerun()
            
            # Concatenar todos los DataFrames, filtrando los que estén vacíos
            dfs_validos = [df for df in dfs_por_anyo.values() if df is not None and not df.empty]
            if dfs_validos:
                df_pl = pd.concat(dfs_validos, ignore_index=True)
            else:
                df_pl = pd.DataFrame()
            
            # PASO 3: APARTAMENTO - Seleccionar los años disponibles
            años_disponibles = sorted(list(dfs_por_anyo.keys()), reverse=True)  # Descendente: últimos primero
            
            if len(años_disponibles) < 1:
                st.warning(f"⚠️ No hay datos cargados.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            
            # Seleccionar años manualmente
            st.markdown("---")
            st.markdown("**Años a analizar**")
            col_y1, col_y2 = st.columns(2)
            with col_y1:
                # Por defecto: año actual (2026)
                year_actual = st.selectbox("Año actual", options=años_disponibles, index=1 if len(años_disponibles) > 1 else 0, key="rent_year_actual", label_visibility="collapsed")
            with col_y2:
                # Por defecto: año anterior (2025)
                year_anterior = st.selectbox("Año anterior", options=años_disponibles, index=2 if len(años_disponibles) > 2 else (1 if len(años_disponibles) > 1 else 0), key="rent_year_anterior", label_visibility="collapsed")
            
            if year_actual == year_anterior and len(años_disponibles) > 1:
                st.error("⚠️ Selecciona años diferentes")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            
            # Obtener DataFrames, permitiendo que uno esté vacío
            df_año_actual = dfs_por_anyo.get(year_actual, pd.DataFrame())
            df_año_anterior = dfs_por_anyo.get(year_anterior, pd.DataFrame())

            st.markdown("**Alojamiento**")
            
            apt_app = st.selectbox(
                "Alojamiento",
                options=list(apartamentos_app.keys()),
                index=None,
                placeholder="Selecciona...",
                key="rent_apartamento_app",
                label_visibility="collapsed"
            )

            if not apt_app:
                st.warning("Selecciona un alojamiento.")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            limpieza = apartamentos_app[apt_app]
            canal = "Airbnb"
            
            # Cachear markups en session_state para no llamar dos veces
            markups_cache_key = f"markups_{empresa_id}"
            if markups_cache_key not in st.session_state:
                st.session_state[markups_cache_key] = obtener_markups_empresa(empresa_id)
            markups = st.session_state[markups_cache_key]
            markup = markups[canal]
        
        # ================== PASO 4: DETECTAR ALOJAMIENTO EN PRICELABS (CON FUZZY MATCHING CACHEADO) ==================
        from difflib import SequenceMatcher
        
        def fuzzy_match(nombre_app, lista_excel, threshold=0.6):
            """Busca coincidencias fuzzy en la lista de alojamientos."""
            matches = []
            nombre_app_lower = nombre_app.lower()
            
            for nombre_excel in lista_excel:
                nombre_excel_lower = nombre_excel.lower()
                ratio = SequenceMatcher(None, nombre_app_lower, nombre_excel_lower).ratio()
                if ratio >= threshold:
                    matches.append((nombre_excel, ratio))
            
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches
        
        def buscar_apartamento_excel(nombre_csv, lista_excel, umbral_minimo=0.5):
            """
            Busca el mejor match para un apartamento CSV en la lista de PriceLabs.
            Si no encuentra, retorna None.
            """
            coincidencias = fuzzy_match(nombre_csv, lista_excel, threshold=umbral_minimo)
            return coincidencias[0][0] if coincidencias else None
        
        # Caché para fuzzy matching
        fuzzy_cache_key = f"fuzzy_match_{apt_app}_{empresa_id}"
        lista_excel_completa = sorted(df_pl["apartamento_excel"].dropna().unique().tolist())
        
        # FILTRO: Construir lista SOLO con apartamentos que pertenecen a esta empresa
        # (basado en coincidencia con apartamentos del CSV)
        lista_excel_valida = []
        for apt_excel in lista_excel_completa:
            # Verificar si este apartamento de PriceLabs coincide con alguno del CSV
            coincide_con_csv = any(
                fuzzy_match(apt_csv, [apt_excel], threshold=0.5)
                for apt_csv in apartamentos_app.keys()
            )
            if coincide_con_csv:
                lista_excel_valida.append(apt_excel)
        
        # Si no encontramos ninguno con el filtro, usar la lista completa (evitar blancos)
        lista_excel = lista_excel_valida if lista_excel_valida else lista_excel_completa
        
        if fuzzy_cache_key not in st.session_state:
            coincidencias = fuzzy_match(apt_app, lista_excel, threshold=0.6)
            st.session_state[fuzzy_cache_key] = coincidencias
        else:
            coincidencias = st.session_state[fuzzy_cache_key]
        
        if len(coincidencias) == 1:
            apt_excel = coincidencias[0][0]
            st.success(f"✅ Coincidencia automática: **{apt_excel}**")
        elif len(coincidencias) > 1:
            opciones_match = {f"{nombre} (similitud: {score:.0%})" : nombre for nombre, score in coincidencias}
            st.warning(f"⚠️ Se encontraron {len(coincidencias)} coincidencias posibles. Selecciona una:")
            apt_excel_display = st.selectbox(
                "Selecciona el alojamiento correcto",
                list(opciones_match.keys()),
                index=0,
                key="rent_apartment_fuzzy_select"
            )
            apt_excel = opciones_match[apt_excel_display]
        else:
            st.warning("⚠️ No se encontraron coincidencias automáticas. Selecciona manualmente:")
            apt_excel = st.selectbox(
                "Alojamiento en PriceLabs",
                options=lista_excel,
                index=None,
                placeholder="Selecciona un alojamiento...",
                key="rent_apartamento_excel",
                label_visibility="collapsed"
            )
            if not apt_excel:
                st.info("Selecciona el alojamiento en PriceLabs para continuar.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
        
        # ====== PERÍODO A ANALIZAR (BLOQUE IZQUIERDA) ======
        st.markdown("### 📅 Período a analizar")
        
        # Agregar CSS para mejorar UX
        st.markdown("""
        <style>
            input[type="date"] {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            input[type="date"]::-webkit-calendar-picker-indicator {
                cursor: pointer;
                padding: 4px;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**{year_actual}**")
        
        hoy = pd.Timestamp.now()
        hoy_date = hoy.date()
        
        # Calcular fechas para cada opción
        mes_en_curso_start = pd.to_datetime(f"{year_actual}-{hoy.month:02d}-01").date()
        mes_en_curso_end = (pd.to_datetime(f"{year_actual}-{hoy.month:02d}-01") + pd.offsets.MonthEnd(0)).date()
        
        proximo_mes_num = (hoy.month % 12) + 1
        proximo_mes_start = pd.to_datetime(f"{year_actual}-{proximo_mes_num:02d}-01").date()
        proximo_mes_end = (pd.to_datetime(f"{year_actual}-{proximo_mes_num:02d}-01") + pd.offsets.MonthEnd(0)).date()
        
        mes_anterior_num = ((hoy.month - 2) % 12) + 1
        mes_anterior_start = pd.to_datetime(f"{year_actual}-{mes_anterior_num:02d}-01").date()
        mes_anterior_end = (pd.to_datetime(f"{year_actual}-{mes_anterior_num:02d}-01") + pd.offsets.MonthEnd(0)).date()
        
        opciones_periodo = {
            f"📅 Mes en curso ({mes_en_curso_start.strftime('%d/%m')} - {mes_en_curso_end.strftime('%d/%m')})": ("mes_en_curso", mes_en_curso_start, mes_en_curso_end),
            f"📅 Desde 1 ene a hoy (01/01 - {hoy_date.strftime('%d/%m')})": ("desde_enero", pd.to_datetime(f"{year_actual}-01-01").date(), hoy_date),
            f"📅 Próximo mes ({proximo_mes_start.strftime('%d/%m')} - {proximo_mes_end.strftime('%d/%m')})": ("proximo_mes", proximo_mes_start, proximo_mes_end),
            f"📅 Mes anterior ({mes_anterior_start.strftime('%d/%m')} - {mes_anterior_end.strftime('%d/%m')})": ("mes_anterior", mes_anterior_start, mes_anterior_end),
            f"📊 Este año (01/01 - 31/12)": ("este_año", pd.to_datetime(f"{year_actual}-01-01").date(), pd.to_datetime(f"{year_actual}-12-31").date()),
            "🎯 Personalizado": ("personalizado", None, None)
        }
        
        periodo_actual = st.selectbox(
            "Período",
            list(opciones_periodo.keys()),
            key="periodo_actual_tipo",
            label_visibility="collapsed"
        )
        
        tipo_periodo, start_date, end_date = opciones_periodo[periodo_actual]
        
        if tipo_periodo == "personalizado":
            c_desde, c_hasta = st.columns(2)
            with c_desde:
                start_date = st.date_input("Desde", value=pd.to_datetime(f"{year_actual}-01-01").date(), format="DD-MM-YYYY", key="start_fecha_actual", label_visibility="collapsed")
            with c_hasta:
                end_date = st.date_input("Hasta", value=hoy_date, format="DD-MM-YYYY", key="end_fecha_actual", label_visibility="collapsed")
        
        st.markdown(f"**{year_anterior}**")
        
        # Para año anterior, dar opciones
        opciones_anterior = {
            f"🔄 Mismo período ({start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')})": ("mismo", start_date.replace(year=year_anterior), end_date.replace(year=year_anterior)),
            "🎯 Personalizado": ("personalizado", None, None)
        }
        
        periodo_anterior_sel = st.selectbox(
            "Comparación",
            list(opciones_anterior.keys()),
            key="periodo_anterior_tipo",
            label_visibility="collapsed"
        )
        
        tipo_período_anterior, start_anterior, end_anterior = opciones_anterior[periodo_anterior_sel]
        
        if tipo_período_anterior == "personalizado":
            c_desde_ant, c_hasta_ant = st.columns(2)
            with c_desde_ant:
                start_anterior = st.date_input("Desde", value=start_date.replace(year=year_anterior), format="DD-MM-YYYY", key="start_fecha_anterior", label_visibility="collapsed")
            with c_hasta_ant:
                end_anterior = st.date_input("Hasta", value=end_date.replace(year=year_anterior), format="DD-MM-YYYY", key="end_fecha_anterior", label_visibility="collapsed")
        
        # Pre-filtrar por apartamento una sola vez para calcular LOS
        df_apt_completo = df_pl[df_pl["apartamento_excel"] == apt_excel].copy() if not df_pl.empty else pd.DataFrame()

        # Filter data por FECHAS
        if not df_apt_completo.empty:
            df_actual_period = df_apt_completo[
                (df_apt_completo["fecha"].dt.date >= start_date) & 
                (df_apt_completo["fecha"].dt.date <= end_date) & 
                (df_apt_completo["anyo"] == year_actual)
            ].copy()
            
            df_anterior_period = df_apt_completo[
                (df_apt_completo["fecha"].dt.date >= start_anterior) & 
                (df_apt_completo["fecha"].dt.date <= end_anterior) & 
                (df_apt_completo["anyo"] == year_anterior)
            ].copy()
        else:
            df_actual_period = pd.DataFrame()
            df_anterior_period = pd.DataFrame()

        # Permitir continuar aunque falten datos - mostraremos 0 en lugar de error
        if df_actual_period.empty and df_anterior_period.empty:
            st.warning(f"⚠️ No hay datos para {apt_excel} en los períodos seleccionados. Se mostrarán valores a 0.")

        # Calculate LOS
        col_los_actual = f"los_{year_actual}"
        col_los_anterior = f"los_{year_anterior}"
        col_occ_actual = f"ocupacion_{year_actual}"
        col_occ_anterior = f"ocupacion_{year_anterior}"
        
        los_actual = calcular_los_desde_ocupacion(df_actual_period, col_occ_actual, col_los_actual, df_apt_completo)
        los_anterior = calcular_los_desde_ocupacion(df_anterior_period, col_occ_anterior, col_los_anterior, df_apt_completo)
        
        los_actual_val = los_actual if los_actual is not None else 4
        los_anterior_val = los_anterior if los_anterior is not None else 4
        
        col_los_1, col_los_2 = st.columns(2)
        with col_los_1:
            st.write(f"📅 **{year_actual}:** {fmt_num(los_actual_val)} noches")
        with col_los_2:
            st.write(f"📅 **{year_anterior}:** {fmt_num(los_anterior_val)} noches")
        
        los_seleccion = st.radio(
            "Elige el LOS a usar",
            [f"Usar LOS {year_actual}", f"Usar LOS {year_anterior}", "Manual"],
            horizontal=True,
            key="rent_los_selection",
            label_visibility="collapsed"
        )

        # Determinar el LOS a usar según la selección
        if los_seleccion == f"Usar LOS {year_actual}":
            los_valor_elegido = los_actual_val
        elif los_seleccion == f"Usar LOS {year_anterior}":
            los_valor_elegido = los_anterior_val
        else:  # Manual
            los_valor_elegido = 3.0
        
        # Redondear hacia arriba si tiene decimales
        if los_valor_elegido is None or not isinstance(los_valor_elegido, (int, float)) \
                or math.isnan(float(los_valor_elegido)) or los_valor_elegido <= 0:
            los_valor_elegido = 4
            if los_seleccion != "Manual":
                st.warning("⚠️ El LOS seleccionado no tiene datos válidos. Se usará 4 noches por defecto.")
        else:
            los_valor_elegido = max(1, math.ceil(los_valor_elegido))

        st.session_state.los_elegido = los_valor_elegido
        
        st.divider()
        st.write("### 2️⃣ Configurar la estimación")
        
        # Actualizar session_state cuando cambia la selección de LOS
        if st.session_state.get("_last_los_selection") != los_seleccion:
            st.session_state.rent_noches_manual = str(int(los_valor_elegido))
            st.session_state._last_los_selection = los_seleccion
        
        # Determinar si el campo debe estar deshabilitado
        es_manual = los_seleccion == "Manual"
        
        noches_manual_txt = st.text_input(
            "Estancia (noches)", 
            value=st.session_state.get("rent_noches_manual", str(int(los_valor_elegido))),
            key="rent_noches_manual",
            disabled=not es_manual
        )
        margen_extra_txt = st.text_input("Margen extra (%)", "0", key="rent_margen_extra")

        calc_button = st.button("Calcular estimación", key="rent_calc_btn", use_container_width=True)
        
        # Guardar datos en session_state para usar en resultados
        st.session_state.rent_datos_procesados = {
            "df_actual_period": df_actual_period,
            "df_anterior_period": df_anterior_period,
            "year_actual": year_actual,
            "year_anterior": year_anterior,
            "start_date": start_date,
            "end_date": end_date,
            "start_anterior": start_anterior,
            "end_anterior": end_anterior,
            "los_valor_elegido": los_valor_elegido,
            "limpieza": limpieza,
        }
    
    # ================== COLUMNA DERECHA: RESULTADOS ==================
    with col_right:
        # Mostrar resumen de configuración
        st.markdown("### 📊 Análisis Rentabileitor")
        st.info("Configura los datos en la izquierda y presiona **Calcular** para ver los resultados.")
        
        if calc_button:
            try:
                # Recuperar datos de session_state
                df_actual_period = st.session_state.rent_datos_procesados["df_actual_period"]
                df_anterior_period = st.session_state.rent_datos_procesados["df_anterior_period"]
                year_actual = st.session_state.rent_datos_procesados["year_actual"]
                year_anterior = st.session_state.rent_datos_procesados["year_anterior"]
                start_date = st.session_state.rent_datos_procesados["start_date"]
                end_date = st.session_state.rent_datos_procesados["end_date"]
                start_anterior = st.session_state.rent_datos_procesados["start_anterior"]
                end_anterior = st.session_state.rent_datos_procesados["end_anterior"]
                los_valor_elegido = st.session_state.rent_datos_procesados["los_valor_elegido"]
                limpieza = st.session_state.rent_datos_procesados["limpieza"]
                
                # CALCULAR MÉTRICAS EN PARALELO
                col_occ_actual = f"ocupacion_{year_actual}"
                col_occ_anterior = f"ocupacion_{year_anterior}"
                col_adr_actual = f"adr_{year_actual}"
                col_adr_anterior = f"adr_{year_anterior}"
                col_los_actual = f"los_{year_actual}"
                col_los_anterior = f"los_{year_anterior}"
                
                def safe_mean(col_name, df):
                    if col_name not in df.columns:
                        return None
                    vals = pd.to_numeric(df[col_name], errors="coerce").dropna()
                    return vals.mean() if len(vals) > 0 else None

                def calcular_adr_ocupados(df_periodo, col_adr, col_occ):
                    occ_vals = pd.to_numeric(df_periodo[col_occ], errors="coerce").fillna(0)
                    adr_vals = pd.to_numeric(df_periodo[col_adr], errors="coerce")
                    dias_ocupados = adr_vals[occ_vals > 0].dropna()
                    return dias_ocupados.mean() if len(dias_ocupados) > 0 else None
                
                def calcular_ocupacion(df_periodo, col_occ):
                    occ_vals = pd.to_numeric(df_periodo[col_occ], errors="coerce").fillna(0)
                    dias_ocupados = (occ_vals > 0).sum()
                    total_dias = len(df_periodo)
                    return (dias_ocupados / total_dias) * 100 if total_dias > 0 else None
                
                def calcular_revpar(adr, ocupacion):
                    return adr * (ocupacion / 100) if adr is not None and ocupacion is not None else None
                
                adr_actual = calcular_adr_ocupados(df_actual_period, col_adr_actual, col_occ_actual)
                ocupacion_actual = calcular_ocupacion(df_actual_period, col_occ_actual)
                revpar_actual = calcular_revpar(adr_actual, ocupacion_actual)
                
                adr_anterior = calcular_adr_ocupados(df_anterior_period, col_adr_anterior, col_occ_anterior)
                ocupacion_anterior = calcular_ocupacion(df_anterior_period, col_occ_anterior)
                revpar_anterior = calcular_revpar(adr_anterior, ocupacion_anterior)
                
                days_actual = (end_date - start_date).days + 1
                days_anterior = (end_anterior - start_anterior).days + 1
                
                # Los valores de LOS ya fueron calculados en la sección izquierda - usar valores guardados
                los_valor_elegido = st.session_state.rent_datos_procesados["los_valor_elegido"]
                
                # MOSTRAR RESUMEN CONFIGURACIÓN (COMPACTO)
                col_setup1, col_setup2, col_setup3 = st.columns(3)
                with col_setup1:
                    st.metric("Empresa", empresa_sel)
                with col_setup2:
                    st.metric("Alojamiento", apt_app)
                with col_setup3:
                    st.metric("Período", f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}")
                
                st.markdown(f"### 📊 Comparativa {year_actual} vs {year_anterior}")
                
                def render_metrica(nombre, val_actual, val_anterior, unidad):
                    def get_cambio(nuevo, anterior):
                        if nuevo is None or anterior is None or pd.isna(nuevo) or pd.isna(anterior) or anterior == 0:
                            return None, "⚪", "#888888"
                        pct = ((nuevo - anterior) / anterior) * 100
                        return pct, ("↑" if pct >= 0 else "↓"), ("#00aa00" if pct >= 0 else "#dd0000")
                    
                    pct, sim, col = get_cambio(val_actual, val_anterior)
                    val_a = f"{val_actual:.2f}" if val_actual and not pd.isna(val_actual) else "—"
                    val_p = f"{val_anterior:.2f}" if val_anterior and not pd.isna(val_anterior) else "—"
                    pct_t = f"{pct:.1f}%" if pct is not None else "—"
                    
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;padding:12px 14px;border-left:4px solid #1f77b4;background:#f8f9fa;margin-bottom:10px;border-radius:4px'>"
                        f"<div style='font-weight:600;flex:0.6'>{nombre}</div>"
                        f"<div style='text-align:center;flex:1;font-size:12px'><span style='color:#999;font-size:10px'>2026</span><br><b>{val_a} {unidad}</b></div>"
                        f"<div style='text-align:center;flex:1;font-size:12px'><span style='color:#999;font-size:10px'>2025</span><br><b>{val_p} {unidad}</b></div>"
                        f"<div style='text-align:center;flex:0.8'><span style='color:#999;font-size:10px'>Cambio</span><br><span style='color:{col};font-weight:600'>{sim} {pct_t}</span></div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                
                st.markdown("---")
                render_metrica("💰 ADR", adr_actual, adr_anterior, "€")
                render_metrica("📊 Ocupación", ocupacion_actual, ocupacion_anterior, "%")
                render_metrica("🌙 LOS", los_actual_val, los_anterior_val, "noches")
                render_metrica("💵 Rev Par", revpar_actual, revpar_anterior, "€")
                render_metrica("💸 Ingresos", revpar_actual * days_actual if revpar_actual else None, revpar_anterior * days_anterior if revpar_anterior else None, "€")
                
                # CÁLCULO FINAL RENTABILEITOR
                noches_manual = parse_int_input(noches_manual_txt, "Estancia (noches)", minimo=1)
                margen_extra = parse_float_input(margen_extra_txt, "Margen extra (%)")

                los_para_calcular = noches_manual
                
                # Mostrar info si el usuario eligió un LOS diferente al calculado
                if los_para_calcular != los_valor_elegido:
                    st.warning(f"⚠️ Usando **{los_para_calcular}** noches (el LOS calculado sería {los_valor_elegido}). Los resultados pueden no ser representativos.")

                descuento = obtener_descuento_para_noches(empresa_id, los_para_calcular)
                if descuento is None:
                    st.error(f"No hay descuento configurado para {los_para_calcular} noches en esta empresa.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return

                # Usar les markups que ya están cacheados (no volver a llamar)
                # markups y markup ya están definidos en la sección izquierda

                if adr_anterior is None or adr_actual is None or adr_anterior <= 0 or adr_actual <= 0:
                    st.error(f"❌ No hay datos de ADR válidos.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                
                ocupacion_anterior_final = ocupacion_anterior or 50.0
                ocupacion_actual_final = ocupacion_actual or 50.0

                resultado = calcular_rentabileitor_pro_2026_vs_2025(
                    adr_2025=adr_anterior,
                    adr_2026_forecast=adr_actual,
                    limpieza=limpieza,
                    noches=los_para_calcular,
                    descuento=descuento,
                    markup=markup,
                    los_2025=float(los_para_calcular),
                    los_2026=float(los_para_calcular),
                    ocupacion_2025=ocupacion_anterior_final,
                    ocupacion_2026=ocupacion_actual_final,
                    margen_extra_pct=margen_extra,
                )

                if not resultado:
                    st.error("No se ha podido calcular el resultado.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return

                estado = resultado["diagnostico"]
                if estado == "Forecast correcto":
                    st.success(f"Diagnóstico: {estado}")
                elif estado == "Forecast bajo":
                    st.warning(f"Diagnóstico: {estado}")
                else:
                    st.error(f"Diagnóstico: {estado}")

                st.markdown("---")
                st.markdown("### 💰 Recomendaciones de Precios")

                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown(
                        f"""<div class="kpi-card">
                            <div class="kpi-title">Conservador</div>
                            <div class="kpi-sub">ADR 2026 recomendado</div>
                            <div class="kpi-total">{resultado['adr_conservador']:,.2f}<span class="kpi-currency">€</span></div>
                            <div class="kpi-sub">RMS sugerido</div>
                            <div class="kpi-value">{resultado['precio_rms_conservador']:,.2f} €</div>
                        </div>""",
                        unsafe_allow_html=True
                    )
                with rc2:
                    st.markdown(
                        f"""<div class="kpi-card kpi-good">
                            <div class="kpi-title">Óptimo</div>
                            <div class="kpi-sub">ADR 2026 recomendado</div>
                            <div class="kpi-total">{resultado['adr_optimo']:,.2f}<span class="kpi-currency">€</span></div>
                            <div class="kpi-sub">RMS sugerido</div>
                            <div class="kpi-value">{resultado['precio_rms_optimo']:,.2f} €</div>
                        </div>""",
                        unsafe_allow_html=True
                    )

            except Exception as e:
                import traceback
                st.error(f"Error en Rentabileitor PRO: {e}")
                st.code(traceback.format_exc())
    
    st.markdown("</div>", unsafe_allow_html=True)
