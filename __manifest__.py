{
    "name": "Renta de Productos por Evento",
    "version": "19.0.1.3.0",
    "summary": "Renta de productos por evento, con cotizaciones separadas de venta.",
    "description": """
Renta de Productos por Evento
=============================

Módulo genérico para rentar productos con una tarifa fija **por evento**, sin
importar la duración del mismo. Un mismo producto puede venderse y rentarse.

- Una cotización es de **venta o de renta**, nunca las dos.
- Menú **Rentas** separado de Ventas, reutilizando el flujo de `sale.order`.
- Productos con tarifa de renta propia y cuenta de ingreso de renta separada.
- Fechas del evento, entrega y recolección a nivel de cotización.
- Domicilio de entrega capturado manualmente en cada cotización de renta.
- Movimientos reales de inventario al entregar y devolver.
- PDF de renta con nombre y RFC del cliente, sin su domicilio.
- PDF de confirmación propio con línea de firma manual del cliente.
- Reportes de rentas activas y retrasos.

Este módulo no incluye datos, dominios ni credenciales de ningún cliente: cada
despliegue vive en su propio repositorio.
""",
    "author": "ssant0",
    "website": "https://github.com/ssant0/sale_rental_fixed",
    "license": "LGPL-3",
    "category": "Sales/Sales",
    "depends": ["sale", "stock", "account", "mail"],
    "data": [
        "security/rental_security.xml",
        "views/product_views.xml",
        "report/rental_report.xml",
        "views/sale_order_views.xml",
        "views/rental_active_views.xml",
        "views/rental_report_views.xml",
        "views/menus.xml",
        "data/rental_mail_templates.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
