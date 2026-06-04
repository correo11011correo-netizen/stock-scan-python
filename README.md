# Stock Scan Python

Sistema profesional de gestión de inventario, ventas y analítica, diseñado para entornos de alta eficiencia.

## 🚀 Características Principales

*   **Persistencia de Datos**: Motor de base de datos SQLite para gestión de inventario, ventas y sesiones de carrito persistentes.
*   **Gestión de Ventas ACID**: Procesamiento de ventas con integridad transaccional (Registro Venta -> Detalle -> Caja -> Stock).
*   **Suite de Auditoría Profesional**: Auditoría automatizada que incluye validación de integridad de BD, pruebas de rendimiento, Fuzzing de seguridad y validación de flujos de negocio.
*   **CI/CD Integrado**: Configuración automática de GitHub Actions para validar auditorías en cada push.
*   **Interfaz Nativa/Híbrida**: Servidor web ligero para acceso vía terminal o navegador.

## 🛠️ Estructura del Proyecto

```
/
├── .github/workflows/   # CI/CD (GitHub Actions)
├── audit/               # Suite de auditoría y reportes
├── data/                # Base de datos SQLite
├── src/                 # Código fuente
│   ├── core/            # Servicios de negocio
│   ├── commands/        # Orquestador de comandos (Dispatcher)
│   ├── ui/              # Servidor web y frontend
│   └── ...
├── tests/               # Tests unitarios e integración
└── main.py              # Punto de entrada del sistema
```

## ⚙️ Configuración y Ejecución

### Requisitos
- Python 3.10+
- `pip install requests` (para auditorías)

### Ejecución
Para iniciar el sistema en el entorno de desarrollo:
```bash
python3 main.py
```

Accede a la interfaz en `http://localhost:8888`.

## 🛡️ Auditoría y Depuración Técnica

Para ejecutar la suite de pruebas profesional:
```bash
python3 audit/automated_audit.py
```
Los reportes se generan automáticamente en `audit/FULL_AUDIT_REPORT.json` y `audit/BUG_LOG.md`.

### 🔍 Sistema de Debugging (Candado de Auditoría)
El sistema incluye un comando maestro de depuración llamado `debug.call` que permite invocar cualquier función interna de los servicios para validación técnica.

**Uso via API/Consola:**
```json
{
  "command": "debug.call",
  "params": {
    "service": "stock|sales|system|auth",
    "method": "nombre_de_la_funcion",
    "args": { "param1": "valor", "param2": "valor" }
  }
}
```
*Este comando está restringido al rol de administrador y genera logs detallados bajo la etiqueta `AUDIT-DEBUG`.*

## 🤝 Contribución
Este proyecto sigue convenciones de `Conventional Commits` y requiere que todos los cambios pasen el CI (GitHub Actions) antes de ser integrados en `main`.
