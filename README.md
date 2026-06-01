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

## 🛡️ Auditoría

Para ejecutar la suite de pruebas profesional:
```bash
python3 audit/automated_audit.py
```
Los reportes se generan automáticamente en `audit/FULL_AUDIT_REPORT.json` y `audit/BUG_LOG.md`.

## 🤝 Contribución
Este proyecto sigue convenciones de `Conventional Commits` y requiere que todos los cambios pasen el CI (GitHub Actions) antes de ser integrados en `main`.
