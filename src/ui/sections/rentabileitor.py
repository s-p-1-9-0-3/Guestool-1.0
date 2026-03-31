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
        with st.expander("⚙️ 1. Empresa, datos y apartamento", expanded=True):
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
            
            # 🔧 LIMPIAR CACHE SI CAMBIAMOS DE EMPRESA - VERSIÓN AGRESIVA
            stored_empresa = st.session_state.get("rent_empresa_actual", None)
            import sys
            print(f"[DEBUG Rentabileitor] Empresa seleccionada: {empresa_sel} -> empresa_id: '{empresa_id}'", file=sys.stderr)
            print(f"[DEBUG Rentabileitor] Empresa anterior en sesion: {stored_empresa}", file=sys.stderr)
            
            if stored_empresa != empresa_id or stored_empresa is None:
                print(f"[DEBUG Rentabileitor] Cambiando de empresa o primera vez. Limpiando TODOS los caches de pricelabs.", file=sys.stderr)
                # Limpiar TODOS los caches de pricelabs para evitar contaminación cruzada
                keys_to_clean = [k for k in st.session_state.keys() if k.startswith("pricelabs_data_")]
                for key in keys_to_clean:
                    st.session_state.pop(key, None)
                    print(f"[DEBUG Rentabileitor] Limpiado: {key}", file=sys.stderr)
                st.session_state["rent_empresa_actual"] = empresa_id

            datos = obtener_apartamentos(empresa_id)
            if not datos:
                st.warning("No hay apartamentos en esta empresa")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            apartamentos_app = {nombre: float(limpieza) for nombre, limpieza in datos}
            
            # PASO 2: EXCELS
            st.markdown("**Datos de PriceLabs**")
            dfs_por_anyo = {}
            df_pl = None
            cargar_nuevos = False
            
            dfs_cached = cargar_pricelabs_excel(empresa_id)
            hay_archivos_cached = bool(dfs_cached)
            años_cached = sorted(list(dfs_cached.keys())) if dfs_cached else []
            
            if hay_archivos_cached:
                st.success(f"✅ {', '.join(map(str, años_cached))}")
                
                # DEBUG: Los DataFrames ya vienen procesados desde cargar_pricelabs_excel()
                df_pl_test = pd.concat(list(dfs_cached.values()), ignore_index=True) if dfs_cached else pd.DataFrame()
                apartamentos_en_excels = sorted(df_pl_test["apartamento_excel"].dropna().unique().tolist()) if not df_pl_test.empty else []
                
                with st.expander(f"🔍 Debug: empresa_id='{empresa_id}' ({empresa_sel})"):
                    st.write(f"**Empresa ID:** `{empresa_id}`")
                    st.write(f"**Empresa seleccionada:** {empresa_sel}")
                    st.write(f"**Apartamentos cargados de los excels ({len(apartamentos_en_excels)}):**")
                    st.write(apartamentos_en_excels)
                    st.write(f"**Apartamentos en CSV ({len(apartamentos_app)}):**")
                    st.write(sorted(list(apartamentos_app.keys())))
                
                hay_cambios = detectar_cambios_pricelabs(empresa_id)
                if hay_cambios:
                    if st.button("🔄 Recargar"):
                        cargar_nuevos = True
                else:
                    if st.checkbox("Cargar nuevos", key="force_reload_pricelabs"):
                        cargar_nuevos = True
                
                if not cargar_nuevos:
                    # Usar los DataFrames directamente (ya están procesados)
                    dfs_por_anyo = dfs_cached.copy()
            else:
                st.info("Sin datos cargados")
            
            if cargar_nuevos or not hay_archivos_cached:
                archivos = st.file_uploader(
                    "Selecciona Excel/CSV",
                    type=["xlsx", "csv"],
                    accept_multiple_files=True,
                    key="rent_pricelabs_files",
                    label_visibility="collapsed"
                )

                if archivos:
                    try:
                        for archivo in archivos:
                            from io import BytesIO
                            from src.utils.text import normalizar_texto
                            df_raw = pd.read_excel(BytesIO(archivo.getvalue()))
                            
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
                                df_procesado = procesar_pricelabs_excel(df_raw, archivo.name, int(año_predominante))
                                dfs_por_anyo[int(año_predominante)] = df_procesado
                        
                        if dfs_por_anyo:
                            guardar_pricelabs_excel(empresa_id, archivos)
                            st.success(f"✅ {', '.join(map(str, sorted(dfs_por_anyo.keys())))}")
                        else:
                            st.error("❌ No se pudieron procesar los archivos.")
                            st.markdown("</div>", unsafe_allow_html=True)
                            return
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                        st.markdown("</div>", unsafe_allow_html=True)
                        return
                else:
                    if hay_archivos_cached:
                        for anyo, df_raw in dfs_cached.items():
                            dfs_por_anyo[anyo] = procesar_pricelabs_excel(df_raw, f"pricelabs_{anyo}.xlsx", anyo)
                    else:
                        st.info("Sube un archivo para continuar.")
                        st.markdown("</div>", unsafe_allow_html=True)
                        return
            
            # Validar que tenemos datos
            if not dfs_por_anyo:
                st.error("No hay datos cargados.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            
            df_pl = pd.concat(list(dfs_por_anyo.values()), ignore_index=True)
            
            # PASO 3: APARTAMENTO
            st.markdown("---")
            st.markdown("**Alojamiento**")
            
            años_disponibles = sorted(list(dfs_por_anyo.keys()))
            
            if len(años_disponibles) < 2:
                st.warning(f"⚠️ Solo hay datos de {len(años_disponibles)} año/s. Se necesitan al menos 2.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            
            # Seleccionar años por defecto
            year_actual_real = datetime.now().year
            year_anterior_real = year_actual_real - 1
            index_year_actual = años_disponibles.index(year_actual_real) if year_actual_real in años_disponibles else len(años_disponibles) - 1
            index_year_anterior = años_disponibles.index(year_anterior_real) if year_anterior_real in años_disponibles else max(0, len(años_disponibles) - 2)
            
            c1, c2 = st.columns(2)
            with c1:
                year_actual = st.selectbox("Año actual", años_disponibles, index=index_year_actual, key="rent_year_actual", label_visibility="collapsed")
            with c2:
                year_anterior = st.selectbox("Año anterior", años_disponibles, index=index_year_anterior, key="rent_year_anterior", label_visibility="collapsed")
            
            if year_actual == year_anterior:
                st.error("⚠️ Los años no pueden ser iguales.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            
            df_año_actual = dfs_por_anyo.get(year_actual)
            df_año_anterior = dfs_por_anyo.get(year_anterior)

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
            # Canal fijo a Airbnb para markups, pero no lo mostramos en la UI
            canal = "Airbnb"
            markups = obtener_markups_empresa(empresa_id)
            markup = markups[canal]
        
        # ================== PASO 4: DETECTAR ALOJAMIENTO EN PRICELABS (CON FUZZY MATCHING) ==================
        from difflib import SequenceMatcher
        
        def fuzzy_match(nombre_app, lista_excel, threshold=0.6):
            """
            Busca coincidencias fuzzy en la lista de alojamientos.
            Retorna lista de (nombre_excel, score) ordenada por score descendente.
            """
            matches = []
            nombre_app_lower = nombre_app.lower()
            
            for nombre_excel in lista_excel:
                nombre_excel_lower = nombre_excel.lower()
                # Calcular similitud
                ratio = SequenceMatcher(None, nombre_app_lower, nombre_excel_lower).ratio()
                if ratio >= threshold:
                    matches.append((nombre_excel, ratio))
            
            # Ordenar por score descendente
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches
        
        # FILTRAR PARA SOLO MOSTRAR APARTAMENTOS DE LA EMPRESA SELECCIONADA
        # Usar lista de apartamentos de la empresa (no sacar de df_pl que contiene todas)
        lista_excel_de_empresa = sorted(list(apartamentos_app.keys()))
        
        # Pero también buscar en los excels por si hay coincidencias más cercanas
        lista_excel_en_excels = sorted(df_pl["apartamento_excel"].dropna().unique().tolist())
        
        # Filtrar lista_excel_en_excels para SOLO incluir apartamentos similares a los de la empresa
        lista_excel_filtrada = []
        for apt_repo in lista_excel_de_empresa:
            for apt_excel in lista_excel_en_excels:
                ratio = SequenceMatcher(None, apt_repo.lower(), apt_excel.lower()).ratio()
                if ratio >= 0.5:  # threshold bajo para encontrar variaciones
                    if apt_excel not in lista_excel_filtrada:
                        lista_excel_filtrada.append(apt_excel)
        
        # Si no encuentra coincidencias, usar solo la lista de la empresa
        lista_excel = sorted(lista_excel_filtrada) if lista_excel_filtrada else lista_excel_de_empresa
        
        # Buscar coincidencias fuzzy
        coincidencias = fuzzy_match(apt_app, lista_excel, threshold=0.6)
        
        if len(coincidencias) == 1:
            # Una única coincidencia: mostrar match automático
            apt_excel = coincidencias[0][0]
            st.success(f"✅ Coincidencia automática: **{apt_excel}**")
        elif len(coincidencias) > 1:
            # Múltiples coincidencias: dejar elegir
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
            # Sin coincidencias: seleccionar manualmente
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
        periodo_actual = st.selectbox(
            "Período",
            [
                "📅 Mes en curso",
                "📅 Desde 1 de enero a hoy",
                "📅 Próximo mes",
                "📅 Mes anterior",
                "📊 Este año",
                "🎯 Personalizado"
            ],
            key="periodo_actual_tipo",
            label_visibility="collapsed"
        )
        
        hoy = pd.to_datetime("2026-03-29")
        hoy_date = hoy.date()
        
        if periodo_actual == "📅 Mes en curso":
            start_date = pd.to_datetime(f"{year_actual}-03-01").date()
            end_date = (pd.to_datetime(f"{year_actual}-03-01") + pd.offsets.MonthEnd(0)).date()
        elif periodo_actual == "📅 Desde 1 de enero a hoy":
            start_date = pd.to_datetime(f"{year_actual}-01-01").date()
            end_date = hoy_date
        elif periodo_actual == "📅 Próximo mes":
            start_date = pd.to_datetime(f"{year_actual}-04-01").date()
            end_date = (pd.to_datetime(f"{year_actual}-04-01") + pd.offsets.MonthEnd(0)).date()
        elif periodo_actual == "📅 Mes anterior":
            start_date = pd.to_datetime(f"{year_actual}-02-01").date()
            end_date = (pd.to_datetime(f"{year_actual}-02-01") + pd.offsets.MonthEnd(0)).date()
        elif periodo_actual == "📊 Este año":
            start_date = pd.to_datetime(f"{year_actual}-01-01").date()
            end_date = pd.to_datetime(f"{year_actual}-12-31").date()
        else:
            start_date = st.date_input("Desde", value=pd.to_datetime(f"{year_actual}-01-01").date(), format="DD-MM-YYYY", key="start_fecha_actual", label_visibility="collapsed")
            end_date = st.date_input("Hasta", value=hoy_date, format="DD-MM-YYYY", key="end_fecha_actual", label_visibility="collapsed")
        
        st.markdown(f"**{year_anterior}**")
        periodo_anterior = st.selectbox(
            f"Comparación",
            ["🔄 Mismo período año pasado", "🎯 Personalizado"],
            key="periodo_anterior_tipo",
            label_visibility="collapsed"
        )
        
        if periodo_anterior == "🔄 Mismo período año pasado":
            start_anterior = start_date.replace(year=year_anterior)
            end_anterior = end_date.replace(year=year_anterior)
        else:
            start_anterior = st.date_input("Desde", value=pd.to_datetime(f"{year_anterior}-01-01").date(), format="DD-MM-YYYY", key="start_fecha_anterior", label_visibility="collapsed")
            end_anterior = st.date_input("Hasta", value=pd.to_datetime(f"{year_anterior}-12-31").date(), format="DD-MM-YYYY", key="end_fecha_anterior", label_visibility="collapsed")
        
        # ===== OPCIÓN DE ELEGIR LOS =====
        st.markdown("---")
        st.write("**¿Cuál LOS deseas usar para la estimación?**")
        
        # Pre-filtrar por apartamento una sola vez para calcular LOS
        df_apt_completo = df_pl[df_pl["apartamento_excel"] == apt_excel].copy()

        # Filter data por FECHAS
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

        if df_actual_period.empty or df_anterior_period.empty:
            st.error(f"❌ No hay datos para {apt_excel} en los períodos seleccionados.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

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
    
    # ================== COLUMNA DERECHA: RESULTADOS ==================
    with col_right:
        # ================== RESUMEN COMPACTO ==================
        st.markdown("### ✅ Configuración")
        
        # Mostrar resumen en una sola columna (compacto)
        st.metric("🏢", f"{empresa_sel}")
        st.metric("🏠", f"{apt_app}")
        st.metric("📊", f"{year_actual} vs {year_anterior}")
        
        # ================== VALIDACIÓN EN VIVO DE FECHAS ==================
        # Validar ambos años
        dias_actual = (end_date - start_date).days + 1 if start_date < end_date and (end_date - start_date).days <= 365 else None
        dias_anterior = (end_anterior - start_anterior).days + 1 if start_anterior < end_anterior and (end_anterior - start_anterior).days <= 365 else None
        
        # Mostrar en una línea compacta
        if dias_actual and dias_anterior:
            st.markdown(f"📋 **Comparando:** {year_actual} ({dias_actual}d) vs {year_anterior} ({dias_anterior}d)")
        else:
            if not dias_actual:
                st.error(f"⚠️ {year_actual}: fechas inválidas")
            if not dias_anterior:
                st.error(f"⚠️ {year_anterior}: fechas inválidas")
        
        # Display data - Visualización minimalista
        st.markdown(f"### 📊 Comparativa {year_actual} vs {year_anterior}")
        
        # Calculate daily averages (promedio de datos diarios)
        def safe_mean(col_name, df):
            if col_name not in df.columns:
                return None
            vals = pd.to_numeric(df[col_name], errors="coerce").dropna()
            return vals.mean() if len(vals) > 0 else None

        # ADR se calcula SOLO de días con ocupación > 0 (días reservados)
        def calcular_adr_ocupados(df_periodo, col_adr, col_occ):
            """Calcula ADR promedio solo para días ocupados (ocupación > 0)"""
            occ_vals = pd.to_numeric(df_periodo[col_occ], errors="coerce").fillna(0)
            adr_vals = pd.to_numeric(df_periodo[col_adr], errors="coerce")
            
            # Filtrar solo días ocupados
            dias_ocupados = adr_vals[occ_vals > 0].dropna()
            return dias_ocupados.mean() if len(dias_ocupados) > 0 else None
        
        def calcular_ocupacion(df_periodo, col_occ):
            """Calcula ocupación = (días con ocupación > 0) / total días * 100"""
            occ_vals = pd.to_numeric(df_periodo[col_occ], errors="coerce").fillna(0)
            dias_ocupados = (occ_vals > 0).sum()
            total_dias = len(df_periodo)
            if total_dias > 0:
                return (dias_ocupados / total_dias) * 100
            return None
        
        def calcular_revpar(adr, ocupacion):
            """Calcula Rev Par = ADR * (Ocupación / 100)"""
            if adr is None or ocupacion is None:
                return None
            return adr * (ocupacion / 100)
        
        # Obtener nombres de columnas dinámicamente
        col_adr_actual = f"adr_{year_actual}"
        col_adr_anterior = f"adr_{year_anterior}"
        
        # Calcular ADR y Ocupación primero para usarlos en RevPAR
        adr_actual = calcular_adr_ocupados(df_actual_period, col_adr_actual, col_occ_actual)
        ocupacion_actual = calcular_ocupacion(df_actual_period, col_occ_actual)
        revpar_actual = calcular_revpar(adr_actual, ocupacion_actual)
        
        adr_anterior = calcular_adr_ocupados(df_anterior_period, col_adr_anterior, col_occ_anterior)
        ocupacion_anterior = calcular_ocupacion(df_anterior_period, col_occ_anterior)
        revpar_anterior = calcular_revpar(adr_anterior, ocupacion_anterior)
        
        # Días para cálculo de ingresos
        days_actual = (end_date - start_date).days + 1
        days_anterior = (end_anterior - start_anterior).days + 1
        
        resumen_actual = {
            f"adr_{year_actual}": adr_actual,
            f"los_{year_actual}": los_actual if los_actual is not None else safe_mean(col_los_actual, df_actual_period),
            f"ocupacion_{year_actual}": ocupacion_actual,
            f"ingresos_{year_actual}": revpar_actual * days_actual if revpar_actual is not None else None,
            f"revpar_{year_actual}": revpar_actual,
            f"booking_window_{year_actual}": safe_mean(f"booking_window_{year_actual}", df_actual_period),
        }
        resumen_anterior = {
            f"adr_{year_anterior}": adr_anterior,
            f"los_{year_anterior}": los_anterior if los_anterior is not None else safe_mean(col_los_anterior, df_anterior_period),
            f"ocupacion_{year_anterior}": ocupacion_anterior,
            f"ingresos_{year_anterior}": revpar_anterior * days_anterior if revpar_anterior is not None else None,
            f"revpar_{year_anterior}": revpar_anterior,
            f"booking_window_{year_anterior}": safe_mean(f"booking_window_{year_anterior}", df_anterior_period),
        }
        
        # Validar que haya datos válidos
        if all(v is None or pd.isna(v) for v in resumen_actual.values()) or all(v is None or pd.isna(v) for v in resumen_anterior.values()):
            st.error(f"❌ No hay datos numéricos válidos para {apt_excel} en estos períodos.")
            st.markdown("</div>", unsafe_allow_html=True)
            return
        
        def calcular_cambio(val_nuevo, val_anterior):
            """Calcula el porcentaje de cambio y retorna (pct_cambio, es_positivo)"""
            if val_nuevo is None or val_anterior is None or pd.isna(val_nuevo) or pd.isna(val_anterior):
                return None, None
            if val_anterior == 0:
                return None, None
            pct = ((val_nuevo - val_anterior) / val_anterior) * 100
            return pct, pct >= 0
        
        def render_metrica_minimal(nombre, valor_actual, valor_anterior, unidad):
            """Renderiza métrica minimalista: año_actual | año_anterior | % cambio - FULL WIDTH"""
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
        
        st.markdown("---")
        
        # 5 Métricas principales - CADA UNA EN UNA LÍNEA (full width)
        render_metrica_minimal(
            "💰 ADR",
            resumen_actual[f'adr_{year_actual}'],
            resumen_anterior[f'adr_{year_anterior}'],
            "€"
        )
        
        render_metrica_minimal(
            "📊 Ocupación",
            resumen_actual[f'ocupacion_{year_actual}'],
            resumen_anterior[f'ocupacion_{year_anterior}'],
            "%"
        )
        
        render_metrica_minimal(
            "🌙 LOS",
            resumen_actual[f'los_{year_actual}'],
            resumen_anterior[f'los_{year_anterior}'],
            "noches"
        )
        
        render_metrica_minimal(
            "💵 Rev Par",
            revpar_actual,
            revpar_anterior,
            "€"
        )
        
        render_metrica_minimal(
            "💸 Ingresos",
            resumen_actual[f'ingresos_{year_actual}'],
            resumen_anterior[f'ingresos_{year_anterior}'],
            "€"
        )
        
        # ===== MOSTRAR RESULTADO SI SE CALCULA =====
        if calc_button:
            try:
                # Usar el valor actual del campo "Estancia (noches)"
                noches_modelo = parse_int_input(noches_manual_txt, "Estancia (noches)", minimo=1)
                margen_extra = parse_float_input(margen_extra_txt, "Margen extra (%)")

                descuento = obtener_descuento_para_noches(empresa_id, noches_modelo)
                if descuento is None:
                    st.error("No hay descuento configurado para ese rango de noches en esta empresa.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return

                markups = obtener_markups_empresa(empresa_id)
                markup = markups[canal]

                # Usar el LOS elegido
                los_usuario = float(noches_manual_txt)

                # Validación explícita de datos antes de calcular
                adr_2025 = resumen_anterior[f"adr_{year_anterior}"]
                adr_2026 = resumen_actual[f"adr_{year_actual}"]
                occ_2025 = resumen_anterior[f"ocupacion_{year_anterior}"]
                occ_2026 = resumen_actual[f"ocupacion_{year_actual}"]
                
                # NUEVA LÓGICA: Permitir apartamentos nuevos (sin datos en año anterior)
                if (adr_2025 is None or adr_2025 <= 0) and (adr_2026 is None or adr_2026 <= 0):
                    st.error(f"❌ No hay datos de ADR para {year_anterior} ni {year_actual}. Se necesita al menos un año con datos.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                
                # Si falta ocupación, usar valores por defecto
                if occ_2025 is None or occ_2025 <= 0:
                    occ_2025 = 50.0
                if occ_2026 is None or occ_2026 <= 0:
                    occ_2026 = 50.0
                
                # Detectar si es apartamento nuevo
                es_nuevo = (adr_2025 is None or adr_2025 <= 0) and (adr_2026 is not None and adr_2026 > 0)
                
                if es_nuevo:
                    st.info(f"ℹ️ **Primera temporada**: Este apartamento solo tiene datos de {year_actual}. Se usará como baseline.")


                resultado = calcular_rentabileitor_pro_2026_vs_2025(
                    adr_2025=adr_2025,
                    adr_2026_forecast=adr_2026,
                    limpieza=limpieza,
                    noches=noches_modelo,
                    descuento=descuento,
                    markup=markup,
                    los_2025=los_usuario,
                    los_2026=los_usuario,
                    ocupacion_2025=occ_2025,
                    ocupacion_2026=occ_2026,
                    margen_extra_pct=margen_extra,
                )

                if not resultado:
                    st.error("No se ha podido calcular el resultado.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return

                # Mostrar aviso si es primera temporada
                if resultado.get("es_primera_temporada", False):
                    st.warning("⚠️ **Sin histórico**: Esta estimación se basa únicamente en datos actuales (crecimiento conservador del 5%).")

                estado = resultado["diagnostico"]
                if estado == "Forecast correcto":
                    st.success(f"Diagnóstico: {estado}")
                elif estado == "Forecast bajo":
                    st.warning(f"Diagnóstico: {estado}")
                else:
                    st.error(f"Diagnóstico: {estado}")

                st.write("### Resultado final")

                rc1, rc2, rc3 = st.columns(3)
                with rc1:
                    st.markdown(
                        f"""
                        <div class="kpi-card">
                            <div class="kpi-title">Conservador</div>
                            <div class="kpi-sub">ADR 2026 recomendado</div>
                            <div class="kpi-total">{resultado['adr_conservador']:,.2f}<span class="kpi-currency">€</span></div>
                            <div class="kpi-sub">RMS sugerido</div>
                            <div class="kpi-value">{resultado['precio_rms_conservador']:,.2f} €</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with rc2:
                    st.markdown(
                        f"""
                        <div class="kpi-card kpi-good">
                            <div class="kpi-title">Óptimo</div>
                            <div class="kpi-sub">ADR 2026 recomendado</div>
                            <div class="kpi-total">{resultado['adr_optimo']:,.2f}<span class="kpi-currency">€</span></div>
                            <div class="kpi-sub">RMS sugerido</div>
                            <div class="kpi-value">{resultado['precio_rms_optimo']:,.2f} €</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with rc3:
                    st.markdown(
                        f"""
                        <div class="kpi-card">
                            <div class="kpi-title">Agresivo</div>
                            <div class="kpi-sub">ADR 2026 recomendado</div>
                            <div class="kpi-total">{resultado['adr_agresivo']:,.2f}<span class="kpi-currency">€</span></div>
                            <div class="kpi-sub">RMS sugerido</div>
                            <div class="kpi-value">{resultado['precio_rms_agresivo']:,.2f} €</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            except Exception as e:
                import traceback
                st.error(f"Error en Rentabileitor PRO: {e}")
                st.code(traceback.format_exc())
    
    st.markdown("</div>", unsafe_allow_html=True)
