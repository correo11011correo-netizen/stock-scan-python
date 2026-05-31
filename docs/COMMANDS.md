# 📖 COMMANDS.md

Este archivo documenta todos los comandos disponibles en el sistema. Cada comando puede ser invocado desde la consola de control.

## 📦 Gestión de Stock
| Comando | Descripción | Parámetros | Acceso |
| :--- | :--- | :--- | :--- |
| `stock.list` | Lista todos los productos | `filter` (opcional) | Gratis |
| `stock.add` | Agrega un nuevo producto | `nombre, precio, cant, cat` | Dueño |
| `stock.edit` | Modifica un producto existente | `codigo, campo, valor` | Dueño |
| `stock.delete` | Elimina un producto | `codigo` | Dueño |
| `stock.update_qty` | Actualiza la cantidad de stock | `codigo, cantidad` | Empleado |

## 🛒 Gestión de Ventas
| Comando | Descripción | Parámetros | Acceso |
| :--- | :--- | :--- | :--- |
| `venta.nueva` | Inicia un nuevo carrito de venta | - | Empleado |
| `venta.add` | Agrega producto al carrito | `codigo` | Empleado |
| `venta.cobrar` | Finaliza la venta y resta stock | `metodo_pago, paga_con` | Empleado |
| `venta.cancelar` | Vacía el carrito actual | - | Empleado |

## 📊 Reportes y Estadísticas
| Comando | Descripción | Parámetros | Acceso |
| :--- | :--- | :--- | :--- |
| `reporte.resumen` | Muestra facturación y ganancias | - | PRO (Dueño) |
| `reporte.top` | Lista los productos más vendidos | `limit` | PRO (Dueño) |
| `reporte.alertas` | Lista productos con stock bajo | - | PRO (Dueño) |

## ⚙️ Configuración y Sistema
| Comando | Descripción | Parámetros | Acceso |
| :--- | :--- | :--- | :--- |
| `sys.theme.set` | Cambia el tema visual | `light/dark/night` | Gratis |
| `sys.lang.set` | Cambia el idioma del sistema | `es/en` | Gratis |
| `caja.abrir` | Abre el turno de caja | `monto_inicial` | Dueño |
| `caja.cerrar` | Cierra el turno de caja | `monto_real` | Dueño |
| `sys.export_csv` | Exporta inventario a CSV | - | PRO (Dueño) |
| `logs.view` | Muestra los últimos logs | `limit` | Dueño |
