# 🎪 Renta de Productos por Evento

**[English](README.md)** · **Español**

Renta de productos con tarifa fija por evento para Odoo 19, separada de las cotizaciones de venta normales.

![Odoo](https://img.shields.io/badge/Odoo-19.0-875A7B?logo=odoo&logoColor=white)
![Version](https://img.shields.io/badge/version-19.0.1.2.0-green)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-LGPL--3-blue)
![Tests](https://img.shields.io/badge/tests-manual-lightgrey)

## Descripción

`sale_rental_fixed` agrega un modo de renta al flujo de ventas de Odoo para negocios que rentan productos por evento — equipo de fiesta, audio, mobiliario, herramienta — cobrando una tarifa fija por el evento completo sin importar su duración. Una cotización es de venta **o** de renta, nunca las dos, y las rentas viven en su propio menú **Rentas** con su ciclo de vida, su confirmación en PDF y sus reportes. Un mismo producto puede venderse y rentarse al mismo tiempo, con una tarifa de renta propia y una cuenta de ingreso de renta opcional y dedicada.

## Tabla de contenido

- [Descripción](#descripción)
- [Tecnologías](#tecnologías)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Variables de entorno](#variables-de-entorno)
- [Uso](#uso)
- [Desarrollo](#desarrollo)
- [Comandos disponibles](#comandos-disponibles)
- [Configuración](#configuración)
- [Ciclo de vida de la renta](#ciclo-de-vida-de-la-renta)
- [Estructura del módulo](#estructura-del-módulo)
- [Reportes y automatizaciones](#reportes-y-automatizaciones)
- [Alcance y limitaciones](#alcance-y-limitaciones)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## Tecnologías

- **Plataforma:** Odoo 19.0 Community
- **Lenguaje:** Python 3
- **Framework:** ORM de Odoo, reportes QWeb, datos y vistas XML
- **Dependencias:** `sale`, `stock`, `account`, `mail` (solo módulos estándar de Odoo)
- **Base de datos:** PostgreSQL
- **Idioma de la interfaz:** Español (es_MX)

## Requisitos previos

- **Odoo 19.0 Community** con los módulos `sale`, `stock`, `account` y `mail` disponibles (vienen incluidos en Odoo).
- **Python 3.10 o superior**, igual al intérprete de tu instalación de Odoo 19.
- **PostgreSQL** en la versión soportada por tu despliegue de Odoo 19.
- La carpeta del módulo colocada **un nivel debajo** de un directorio listado en `addons_path`, conservando el nombre de carpeta `sale_rental_fixed`.

## Instalación

1. Clona el repositorio dentro de un directorio de addons:

   ```bash
   git clone <repository-url> /path/to/custom-addons/sale_rental_fixed
   ```

   > [!IMPORTANT]
   > Odoo escanea un nivel debajo de cada entrada de `addons_path`. No anides el módulo más allá de `/path/to/custom-addons/sale_rental_fixed`.

2. Agrega el directorio padre a `addons_path` en tu `odoo.conf`:

   ```ini
   [options]
   addons_path = /path/to/odoo/addons,/path/to/custom-addons
   ```

3. Instala el módulo (el nombre técnico es igual al nombre de la carpeta):

   ```bash
   odoo -d <db> -i sale_rental_fixed --stop-after-init
   ```

   Si ejecutas Odoo desde el código fuente, usa `odoo-bin` en lugar de `odoo`.

4. Reinicia Odoo y abre **Aplicaciones**, luego busca **Renta de Productos por Evento**.

## Variables de entorno

El módulo **no lee variables de entorno** propias.

| Variable | Descripción | Entorno | Requerida |
|---|---|---|---|
| — | El módulo no se configura mediante variables de entorno | Todos | — |

La configuración del despliegue proviene del archivo de configuración estándar de Odoo:

| Opción | Descripción | Entorno | Requerida |
|---|---|---|---|
| `addons_path` | Directorio que contiene `sale_rental_fixed` | Todos | Sí |
| `db_name` | Base de datos donde se instala el módulo | Todos | Sí |
| `db_user` / `db_password` | Credenciales de PostgreSQL | Todos | Según el despliegue |

> [!NOTE]
> Nunca subas `odoo.conf`, respaldos de base de datos ni credenciales a este repositorio.

## Uso

1. **Habilita un producto para renta.** Ve a **Ventas → Productos**, abre un producto y usa la pestaña **Renta**:
   - Marca **Se puede rentar**.
   - Define la **Tarifa de renta (por evento)**.
   - Opcionalmente define la **Cuenta de ingreso de renta** (visible para usuarios de contabilidad).

2. **Crea una cotización de renta.** Ve a **Rentas → Cotizaciones de renta → Nuevo**. La orden se abre con **Es renta** habilitado; elige el cliente, llena **Fecha del evento**, **Entrega**, **Recolección** y **Domicilio de entrega**, y agrega productos. Solo se aceptan productos con *Se puede rentar*.

3. **Confirma la orden.** La confirmación requiere las tres fechas y el domicilio de entrega, y que la recolección no sea anterior a la entrega. La tarifa se copia a cada línea y permanece editable.

4. **Ejecuta la renta** desde el encabezado de la orden:
   - **Entregar** — valida las salidas de inventario y pasa la renta a *Activo*.
   - **Devolver** — crea y valida la entrada de devolución, y pasa la renta a *Devuelto*.
   - **Cerrar renta** — cierra una renta devuelta.
   - **Confirmación de renta** — imprime el PDF de la renta.

5. **Revisa los reportes.** Ve a **Rentas → Reportes** para ver rentas activas, rentas retrasadas y una tabla dinámica/gráfica de ingresos por renta vs venta.

> [!NOTE]
> Las entregas y devoluciones también se pueden validar desde **Inventario**. El módulo sincroniza el estado de la renta cuando se valida una transferencia, pero cerrar una renta siempre es un paso manual en la orden.

## Desarrollo

En este repositorio **no hay suite de pruebas, linter ni formateador**; la verificación es manual. Después de cambiar cualquier archivo Python, XML o de datos, actualiza el módulo — reiniciar Odoo no es suficiente para recargarlos:

```bash
odoo -d <db> -u sale_rental_fixed --stop-after-init
```

Para probar la lógica de notificaciones programadas desde una consola de Odoo:

```bash
odoo shell -d <db>
```

```python
env['sale.order']._cron_rental_notifications()
```

Verificación manual de aceptación:

1. Producto → pestaña **Renta**: `Se puede rentar` activo y tarifa definida.
2. Cotización de renta con las tres fechas, el domicilio de entrega y un producto rentable, confirmada.
3. **Entregar** → *Activo*; **Devolver** → *Devuelto*; **Cerrar renta** → *Cerrado*.
4. **Rentas → Reportes**: rentas activas, retrasos, ingresos.

> [!WARNING]
> `data/ir_cron.xml` y `data/rental_mail_templates.xml` se cargan con `noupdate="1"`. Una actualización del módulo **no** sobrescribe los registros que ya existen en la base de datos; edítalos desde la interfaz o agrega una migración.

## Comandos disponibles

| Comando | Qué hace |
|---|---|
| `odoo -d <db> -i sale_rental_fixed --stop-after-init` | Instala el módulo y termina |
| `odoo -d <db> -u sale_rental_fixed --stop-after-init` | Actualiza el módulo después de cambios en código, vistas o datos |
| `odoo shell -d <db>` | Abre una consola interactiva para depurar y probar el cron |
| `odoo-bin ...` | Los mismos comandos al ejecutar Odoo desde el código fuente |

## Configuración

**Permisos de acceso.** Asigna usuarios en **Ajustes → Usuarios**, en la sección **Rentas**:

| Grupo | Otorga |
|---|---|
| **Usuario de rentas** | Acceso al menú **Rentas** y a sus propias cotizaciones de renta (implica *Ventas / Usuario*) |
| **Administrador de rentas** | Todas las cotizaciones de renta, ventas y configuración de renta (implica *Usuario de rentas* y *Ventas / Administrador*) |

Los administradores (`base.user_root`, `base.user_admin`) se agregan a **Administrador de rentas** durante la instalación.

**Contabilidad.** Las líneas de factura de renta usan la **Cuenta de ingreso de renta** cuando el producto la define; de lo contrario, se usa la cuenta de ingreso del producto o de su categoría. El campo depende de la compañía y no puede apuntar a cuentas por cobrar, por pagar, de efectivo, de tarjeta de crédito ni fuera de balance.

**Notificaciones.** El cron diario **Rentas: recordatorios y retrasos** envía, una sola vez por evento:

- un recordatorio de recolección cuando la fecha de recolección cae dentro de las próximas 24 horas;
- una alerta de retraso cuando la fecha de recolección ya pasó y la renta sigue *Por entregar* o *Activo*.

Los destinatarios son los usuarios activos de **Administrador de rentas** más el creador y el vendedor de la orden, sin direcciones duplicadas. Cambiar **Recolección** rearma ambas notificaciones.

## Ciclo de vida de la renta

```
pending (Por entregar) ──Entregar──> active (Activo) ──Devolver──> returned (Devuelto) ──Cerrar renta──> closed (Cerrado)
```

Reglas que aplica el módulo:

- Una cotización es **venta XOR renta**. Una vez confirmada, `is_rental` no se puede cambiar: primero cancela y regresa la orden a cotización.
- Las cotizaciones de renta solo aceptan productos marcados como rentables; la confirmación requiere fecha del evento, entrega, recolección y domicilio de entrega.
- El domicilio de entrega (`domicilio_entrega`) se captura en cada cotización porque un mismo cliente puede recibir rentas en domicilios distintos; es independiente de la dirección del contacto y de la facturación.
- La recolección no puede ser anterior a la entrega.
- El precio es la **tarifa fija por evento** del producto, convertida a la moneda de la orden cuando difieren, y permanece editable por línea — nunca se prorratea por duración.
- Entregar y devolver crean **movimientos reales de inventario** (salida y entrada).
- `rental_is_late` es un campo calculado no almacenado con un método de búsqueda escrito a mano, por lo que funciona en filtros y dominios de reportes.
- Solo se aceptan las transiciones exactas del ciclo de vida anterior; los botones del formulario se ocultan cuando la acción no aplica.

## Estructura del módulo

| Ruta | Qué contiene |
|---|---|
| `__manifest__.py` | Manifiesto: metadatos, dependencias y archivos de datos en orden (también contiene la descripción larga) |
| `models/product.py` | `rental_ok`, `rental_price`, `rental_income_account_id` |
| `models/sale_order.py` | `is_rental`, fechas del evento, ciclo `rental_status`, restricciones, notificaciones del cron, sobrescrituras de `write()` |
| `models/sale_order_line.py` | Tarifa de renta en `_get_display_price`, cuenta de renta en `_prepare_invoice_line` |
| `models/stock_picking.py` | `_action_done` → `_sync_rental_status` mantiene el estado alineado cuando una transferencia se valida de forma nativa |
| `views/sale_order_views.xml` | Campos de renta y botones del ciclo de vida en el formulario de la orden de venta |
| `views/product_views.xml` | Pestaña **Renta** en el formulario del producto |
| `views/rental_active_views.xml` | Lista y búsqueda de "Artículos en renta" |
| `views/rental_report_views.xml` | Listas de rentas activas/retrasadas, tabla dinámica y gráfica de ingresos, acciones de reporte |
| `views/menus.xml` | Menú **Rentas** y sus acciones |
| `security/rental_security.xml` | Grupos de usuario y administrador de rentas (basados en privilegios de Odoo 19) |
| `report/rental_report.xml` | Extensión del PDF de la orden de venta y el reporte **Confirmación de renta** |
| `data/ir_cron.xml` | Cron diario de notificaciones (`noupdate="1"`) |
| `data/rental_mail_templates.xml` | Plantillas de correo de recordatorio y alerta de retraso (`noupdate="1"`) |
| `i18n/es.po` | Solo el encabezado de traducción — las cadenas fuente ya están en español |

## Reportes y automatizaciones

- **Confirmación de renta** — PDF construido sobre `sale.report_saleorder_document`, que agrega las fechas del evento, entrega y recolección, el domicilio de entrega y reemplaza el título del documento en rentas confirmadas. Las rentas confirmadas terminan con una línea en blanco para que el cliente firme la copia impresa a mano. Se imprime desde el encabezado de la orden.
- **Rentas activas** — rentas confirmadas en *Activo*, con cliente, fechas, estado e importe.
- **Retrasos** — rentas confirmadas cuya fecha de recolección ya pasó y que siguen *Por entregar* o *Activo*; las filas retrasadas se resaltan en rojo en la lista de rentas.
- **Ingresos (renta vs venta)** — tabla dinámica y gráfica de barras que comparan los ingresos de renta y de venta en órdenes confirmadas.
- **Artículos en renta** — vista a nivel de línea de todo lo que está rentado en este momento, agrupable por producto u orden.

## Alcance y limitaciones

Fuera del alcance de esta versión:

- Devoluciones parciales (las devoluciones validan la cantidad total entregada).
- Cargos por daños o por devolución tardía.
- Facturación recurrente o prorrateada; la tarifa es fija por evento.
- Anticipos (`CFDI de anticipo`) y otros flujos de facturación específicos de localización.
- Cierre automático: una renta devuelta permanece *Devuelto* hasta que alguien pulsa **Cerrar renta**.

El módulo **no incluye datos, dominios ni credenciales de clientes**: cada despliegue vive en su propio repositorio.

## Contribuir

Es un addon pequeño, mantenido por una sola persona, sin modelo de ramas ni convención de commits obligatoria. Si envías un cambio:

- Conserva el nombre técnico `sale_rental_fixed`; está incrustado en XML IDs, llamadas `env.ref`, nombres de reportes y el manifiesto.
- Sube `version` en `__manifest__.py` (manteniendo el formato `19.0.x.y.z`) cuando cambie el comportamiento, y agrega los archivos XML nuevos a la lista `data` en orden de carga.
- Conserva los nombres de los campos de negocio (`fecha_evento`, `entrega_dt`, `recoleccion_dt`, `domicilio_entrega`) y los interruptores técnicos (`is_rental`, `rental_status`); las vistas, reportes y traducciones dependen de ellos.
- Mantén las dependencias en módulos estándar de Odoo; no agregues OCA ni addons personalizados.
- Escribe los errores de Python visibles al usuario con `_()`; las etiquetas y textos de ayuda en XML siguen en español.
- Verifica manualmente siguiendo la lista de aceptación anterior — no hay pruebas automatizadas.
- Nunca agregues nombres de clientes, dominios, correos, credenciales ni datos de despliegue.
- Mantén este archivo sincronizado con [`README.md`](README.md) cuando cambie el comportamiento.

## Licencia

Este módulo es software libre y de código abierto, publicado para que cualquiera lo use, estudie, modifique y redistribuya bajo la **GNU Lesser General Public License v3.0 (LGPL-3)**. El texto completo está en [`LICENSE`](LICENSE) y se declara como `LGPL-3` en [`__manifest__.py`](__manifest__.py).
