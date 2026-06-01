# Mapeo de Funcionalidades V1: JS Original vs Python Actual

| Funcionalidad | Componente JS Original | Módulo Python Actual | Estado |
| :--- | :--- | :--- | :--- |
| **Gestión Inventario** | `StockScreen.js` | `src/core/stock_service.py` | ✅ Migrada |
| **Terminal Ventas** | `VentasScreen.js` | `src/core/sales_service.py` | ✅ Migrada |
| **Gestión de Caja** | `SettingsScreen.js` | `src/core/sales_service.py` | ✅ Migrada |
| **Escáner Barcode** | `components/Scanner.js` | `src/scanner/scanner_service.py` | ✅ Migrada |
| **Reportes / BI** | `DashboardScreen.js` | `src/core/sales_service.py` | ✅ Migrada |
| **Gestión Aliados** | `SettingsScreen.js` | `src/core/sales_service.py` | ✅ Migrada |
| **Catálogo Predefinido**| `utils/catalog.js` | N/A | ~~⚠️ Pendiente~~ |
| **Monitor Remoto** | `App.js` | N/A | ~~❌ Pendiente~~ |
| **Update System** | `App.js` | N/A | ~~❌ Pendiente~~ |
