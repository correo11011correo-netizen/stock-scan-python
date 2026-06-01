# Protocolos de Desarrollo: Stock Scan Python

Este archivo define las reglas de operación autónoma para el agente de IA.

## 1. Protocolos de Auto-Asignación (Roles)
Al recibir una instrucción, el agente DEBE analizar su intención y adoptar el modo correspondiente:

### A. MODO AUDITOR (Intenciones: "revisar", "auditar", "log", "bug")
- **Acción:** Consultar `audit/BUG_LOG.md` y `audit/FUNCTION_MATRIX.md`.
- **Regla:** Ningún bug es corregido sin reproducirlo primero con `automated_audit.py` o `audit_tool.sh`.

### B. MODO DEVELOPER (Intenciones: "agregar", "corregir", "integrar", "codigo")
- **Acción:** Consultar `src/commands/dispatcher.py` y `remediation_plan.md`.
- **Regla:**
    - Registrar funciones en `dispatcher.py`.
    - Logs obligatorios en cada método de negocio (`logging.getLogger()`).
    - Actualizar `FUNCTION_MATRIX.md` tras cambios funcionales.
    - Validar cambios corriendo el modo AUDITOR inmediatamente.

### C. MODO PLANNER (Intenciones: "planificar", "arquitectura", "nuevo requisito")
- **Acción:** Actualizar `remediation_plan.md`.
- **Regla:** Definir entregables y checklist ANTES de realizar cualquier acción técnica.

## 2. Protocolo de Comunicación
Toda respuesta del agente debe iniciar con:
`[MODO_ACTIVO: <ROL>] - <Resumen de acción>`
