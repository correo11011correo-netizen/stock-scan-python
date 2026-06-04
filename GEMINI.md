# Project Guidelines: Stock Scan Python

Este archivo contiene las directrices técnicas para el desarrollo y la integración de nuevas funcionalidades en el sistema.

## 🛠️ Arquitectura de Comandos (Dispatcher Pattern)
El sistema utiliza un `CommandDispatcher` para desacoplar la interfaz de la lógica de negocio.

### Cómo agregar un nuevo comando:
1. **Implementar la lógica** en el servicio correspondiente (`src/core/stock_service.py`, etc.).
2. **Crear un handler** en `src/commands/dispatcher.py` (ej. `_handle_mi_comando`).
3. **Mapear el comando** en el `commands_map` del `CommandDispatcher` definiendo:
   - El handler a ejecutar.
   - El nivel de acceso mínimo (`gratis`, `empleado`, `admin`).
   - Si es una característica `PRO` (boolean).
   - La llave de permiso granular (`perm_...`).

## 🔍 Sistema de Auditoría Técnica (`debug.call`)
Para evitar la proliferación de comandos solo para testeo, se ha implementado el comando `debug.call`.

### Uso para Herramientas de Testeo:
Cualquier agente de IA o herramienta de auditoría puede validar la integridad de una función interna sin necesidad de un comando público.
- **Service Map**:
  - `stock` -> `StockService`
  - `sales` -> `SalesService`
  - `system` -> `SystemService`
  - `auth` -> `AuthService`

### Registro de Auditoría:
Todas las llamadas a `debug.call` y los procesos del **Sistema de Importación Universal** se registran en la tabla `audit` de la base de datos con el prefijo `AUDIT-DEBUG`. 

**Trazabilidad de Importaciones:**
Cada paso del proceso de importación (Lectura, Mapeo, Inserción y Errores) se persiste línea por línea. Esto permite que cualquier bug o fallo en el mapeo de un archivo POS sea rastreable y auditable mediante el comando `logs.view` o la interfaz de logs, eliminando falsos positivos y permitiendo la corrección precisa de perfiles de importación.

Para verificar los resultados, use el comando `logs.view`.

## 🎨 Integración con UI (HTML/JS)
Para exponer una función en la interfaz:
1. Asegúrese de que exista un comando mapeado en el `Dispatcher`.
2. En `src/ui/index.html`, utilice el método `app.apiCall('comando', params)` para comunicarse con el servidor.
