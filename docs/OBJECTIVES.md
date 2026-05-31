# 🎯 OBJETIVOS MAESTROS: Sistema de Stock y Escaneo

Este documento es la ley del proyecto. Todo desarrollo debe alinearse con estos objetivos.

## 🛡️ 1. Filosofía "Pure Python"
- **Mínimas Dependencias:** Cero librerías externas a menos que la complejidad sea "extrema".
- **Extracción de Código:** Si una librería es pesada y solo necesitamos 2 funciones, extraeremos esas funciones y las integraremos en el código propio.
- **Sin Capas Web:** No se usará HTML/JS/CSS para la lógica interna. Todo será Python Nativo.

## ⌨️ 2. Sistema de Interacción por Comandos
- **Control Total:** Cada función de la app debe ser ejecutable mediante un comando de texto.
- **Ejemplos de Comandos:** 
    - `stock.cargar` $ightarrow$ Abre flujo de carga de stock.
    - `camara.abrir` $ightarrow$ Activa el escaneo.
    - `logs.ver` $ightarrow$ Muestra el registro de eventos.
    - `ui.pestaña.cambiar [nombre]` $ightarrow$ Cambia la vista actual.
- **Documentación:** Todos los comandos deben estar listados en `COMMANDS.md`.

## 🎨 3. Personalización y UX Avanzada
- **Modos Visuales:** Sistema de temas dinámico (Modo Claro / Modo Oscuro / Modo Noche) configurable vía JSON.
- **Idiomas:** Cambio rápido de idiomas mediante archivos de traducción `.json`.
- **Aesthetics:** Interfaz pulida, profesional y moderna, optimizada para el flujo de trabajo de un almacén.

## 💰 4. Modelo de Monetización (SaaS/Freemium)
- **Feature Gating:** Arquitectura diseñada desde el día 1 para habilitar/deshabilitar funciones.
- **Sectores:**
    - **Gratis:** Funciones básicas de stock y escaneo.
    - **Pago (PRO):** Reportes avanzados, sincronización, gestión multi-usuario, etc.
- **Sistema de Bloqueo:** Interceptor de comandos que verifica el estado de la licencia antes de ejecutar funciones PRO.

## 📱 5. Portabilidad Android Nativa
- **Sustitución de Dependencias:** El código debe ser compatible con el entorno de ejecución de Python en Android (ej. Chaquopy).
- **HAL (Hardware Abstraction Layer):** El acceso a la cámara y al almacenamiento debe ser agnóstico al sistema operativo.
- **Auto-Suficiente:** El APK resultante debe contener todo lo necesario para funcionar sin dependencias externas.

## 🔄 6. Mantenibilidad y Actualizaciones
- **Hot-Swap:** Sistema para corregir errores y actualizar funciones mediante la carga dinámica de módulos sin necesidad de reinstalar la app.
- **Trazabilidad:** Registro estricto de cambios en `CHANGELOG.md`.
- **Validación:** No se considera terminada una función sin su correspondiente test en `/tests`.
