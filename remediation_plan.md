# Plan de Remediación: Mejora de UX Venta Manual Mobile

## Objetivo
Optimizar la terminal de ventas para dispositivos móviles, facilitando la selección manual de productos mediante categorías visuales y un flujo vertical.

## Tareas
1. [ ] Crear `remediation_plan.md` (Este documento).
2. [ ] Modificar `src/ui/index.html` para reordenar la `Ventas View` (Mobile-First: Selector -> Carrito -> Cobro).
3. [ ] Implementar grid de categorías con iconos SVG en `src/ui/index.html`.
4. [ ] Crear o actualizar endpoints de `CommandDispatcher` para listar productos por categoría rápidamente si es necesario.
5. [ ] Validar con `audit/automated_audit.py`.

## Checklist de Validación
- [ ] La interfaz se adapta correctamente a pantallas pequeñas.
- [ ] Las categorías son accesibles y visualmente claras (iconos).
- [ ] El flujo de venta manual es más rápido.
