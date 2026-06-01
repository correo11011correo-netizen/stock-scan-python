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

### Ejecución
Para iniciar el sistema en el entorno local:
```bash
python3 main.py
```

Accede a la interfaz en tu navegador:
- **Local:** `http://localhost:8889`
- **Tailscale (Remoto):** `http://<IP_TAILSCALE>:8889`

El servidor escucha en `0.0.0.0` para permitir accesos desde redes externas (VPN/Tailscale).

## 🛡️ Auditoría

Para ejecutar la suite de pruebas profesional:
```bash
python3 audit/automated_audit.py
```
Los reportes se generan automáticamente en `audit/FULL_AUDIT_REPORT.json` y `audit/BUG_LOG.md`.

## 🤝 Contribución
Este proyecto sigue convenciones de `Conventional Commits`.
**Antes de contribuir, lee las reglas de desarrollo en [GEMINI.md](./GEMINI.md).**
Todos los cambios deben pasar el CI (GitHub Actions) antes de ser integrados en `main`.
