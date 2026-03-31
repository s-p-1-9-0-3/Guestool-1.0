# Guestool 1.0 - Revenue Dashboard

Sistema de gestión de precios y análisis de rentabilidad para alojamientos vacacionales.

## Instalación

1. Crear entorno virtual:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # En PowerShell
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Ejecutar

```bash
streamlit run app.py --logger.level=warning
```

La app estará disponible en `http://localhost:8501`

## Estructura del Proyecto

```
Guestool 1.0/
├── app.py                 # Aplicación principal
├── requirements.txt       # Dependencias Python
├── .gitignore            # Archivos ignorados por git
├── src/                  # Código fuente modular
│   ├── styles.py
│   ├── ui/
│   ├── utils/
│   └── static/
├── config/               # Configuración (empresas_config.json)
├── datos/                # Datos CSV y Excel
├── docs/                 # Documentación
├── dev/                  # Scripts de desarrollo
└── backups/              # Copias de seguridad
```

## Funcionalidades

- **Rentabileitor PRO:** Análisis comparativo de precios PriceLabs (multi-año)
- **Guestool:** Gestión de markups y descuentos por empresa
- **Wizard:** Importación de datos CSV
- **Comparativas dinámicas:** 2026 vs 2025, 2025 vs 2024, etc.

## Notas para Desarrollo

Ver documentación en `docs/` para más detalles sobre la arquitectura y cambios recientes.

