# 🎪 Renta de Productos por Evento

Fixed-price product rentals per event for Odoo 19, kept separate from regular sales quotations.

![Odoo](https://img.shields.io/badge/Odoo-19.0-875A7B?logo=odoo&logoColor=white)
![Version](https://img.shields.io/badge/version-19.0.1.0.0-green)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-LGPL--3-blue)
![Tests](https://img.shields.io/badge/tests-manual-lightgrey)

## Description

`sale_rental_fixed` adds a rental mode to Odoo's sales flow for businesses that rent products per event — party gear, audio equipment, furniture, tools — charging a fixed tariff for the whole event regardless of its duration. A quotation is either a sale or a rental, never both, and rentals live in their own **Rentas** menu with their own lifecycle, PDF confirmation and reports. A single product can be sold and rented at the same time, with a separate rental tariff and an optional dedicated rental income account.

## Table of Contents

- [Description](#description)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Development](#development)
- [Available Commands](#available-commands)
- [Configuration](#configuration)
- [Rental Lifecycle](#rental-lifecycle)
- [Module Structure](#module-structure)
- [Reports and Automations](#reports-and-automations)
- [Scope and Limitations](#scope-and-limitations)
- [Contributing](#contributing)
- [License](#license)

## Tech Stack

- **Platform:** Odoo 19.0 Community
- **Language:** Python 3
- **Framework:** Odoo ORM, QWeb reports, XML data and views
- **Dependencies:** `sale`, `stock`, `account`, `mail` (standard Odoo only)
- **Database:** PostgreSQL
- **Interface language:** Spanish (es_MX)

## Prerequisites

- **Odoo 19.0 Community** with the `sale`, `stock`, `account` and `mail` modules available (they ship with Odoo).
- **Python 3.10 or newer**, matching the interpreter of your Odoo 19 installation.
- **PostgreSQL** at the version supported by your Odoo 19 deployment.
- The module folder placed **one level below** a directory listed in `addons_path`, keeping the folder name `sale_rental_fixed`.

## Installation

1. Clone the repository into an addons directory:

   ```bash
   git clone <repository-url> /path/to/custom-addons/sale_rental_fixed
   ```

   > [!IMPORTANT]
   > Odoo scans one level under each `addons_path` entry. Do not nest the module deeper than `/path/to/custom-addons/sale_rental_fixed`.

2. Add the parent directory to `addons_path` in your `odoo.conf`:

   ```ini
   [options]
   addons_path = /path/to/odoo/addons,/path/to/custom-addons
   ```

3. Install the module (the technical name equals the folder name):

   ```bash
   odoo -d <db> -i sale_rental_fixed --stop-after-init
   ```

   If you run Odoo from source, use `odoo-bin` instead of `odoo`.

4. Restart Odoo and open **Apps**, then search for **Renta de Productos por Evento**.

## Environment Variables

The module reads **no environment variables** of its own.

| Variable | Description | Environment | Required |
|---|---|---|---|
| — | The module has no configuration through environment variables | All | — |

Deployment settings come from the standard Odoo configuration file:

| Option | Description | Environment | Required |
|---|---|---|---|
| `addons_path` | Directory that contains `sale_rental_fixed` | All | Yes |
| `db_name` | Database where the module is installed | All | Yes |
| `db_user` / `db_password` | PostgreSQL credentials | All | Per deployment |

> [!NOTE]
> Never commit `odoo.conf`, database dumps, or credentials to this repository.

## Usage

1. **Enable a product for rental.** Go to **Sales → Products**, open a product and use the **Renta** tab:
   - Check **Se puede rentar**.
   - Set **Tarifa de renta (por evento)**.
   - Optionally set **Cuenta de ingreso de renta** (visible to accounting users).

2. **Create a rental quotation.** Go to **Rentas → Cotizaciones de renta → New**. The order opens with **Es renta** enabled; pick the customer, fill **Fecha del evento**, **Entrega** and **Recolección**, and add products. Only products with *Se puede rentar* are accepted.

3. **Confirm the order.** Confirmation requires the three dates and the collection must not precede delivery. The tariff is copied to each line and stays editable.

4. **Run the rental** from the order header:
   - **Entregar** — validates the outgoing stock pickings and moves the rental to *Activo*.
   - **Devolver** — creates and validates the return picking, moving the rental to *Devuelto*.
   - **Cerrar renta** — closes a returned rental.
   - **Confirmación de renta** — prints the rental PDF.

5. **Review the reports.** Go to **Rentas → Reportes** for active rentals, late rentals, and a rent-vs-sale income pivot/graph.

> [!NOTE]
> Deliveries and returns can also be validated from **Inventory**. The module syncs the rental status when a picking is validated, but closing a rental is always a manual step on the order.

## Development

There is **no test suite, linter or formatter** in this repository; verification is manual. After changing any Python, XML or data file, update the module — restarting Odoo alone does not reload them:

```bash
odoo -d <db> -u sale_rental_fixed --stop-after-init
```

To exercise the scheduled notification logic from an Odoo shell:

```bash
odoo shell -d <db>
```

```python
env['sale.order']._cron_rental_notifications()
```

Manual acceptance check:

1. Product → **Renta** tab: `Se puede rentar` on, tariff set.
2. Rental quotation with the three dates and a rentable product, confirmed.
3. **Entregar** → *Activo*; **Devolver** → *Devuelto*; **Cerrar renta** → *Cerrado*.
4. **Rentas → Reportes**: active rentals, late rentals, income.

> [!WARNING]
> `data/ir_cron.xml` and `data/rental_mail_templates.xml` are loaded with `noupdate="1"`. A module update will **not** overwrite records that already exist in the database; edit them through the UI or add a migration.

## Available Commands

| Command | What it does |
|---|---|
| `odoo -d <db> -i sale_rental_fixed --stop-after-init` | Installs the module and exits |
| `odoo -d <db> -u sale_rental_fixed --stop-after-init` | Upgrades the module after code, view or data changes |
| `odoo shell -d <db>` | Opens an interactive shell for debugging and cron testing |
| `odoo-bin ...` | Same commands when running Odoo from source |

## Configuration

**Access rights.** Assign users in **Settings → Users** under the **Rentas** section:

| Group | Grants |
|---|---|
| **Usuario de rentas** | Access to the **Rentas** menu, own rental quotations (implies *Sales / User*) |
| **Administrador de rentas** | All rental quotations, sales and rental configuration (implies *Usuario de rentas* and *Sales / Administrator*) |

Administrators (`base.user_root`, `base.user_admin`) are added to **Administrador de rentas** on install.

**Accounting.** Rental invoice lines use **Cuenta de ingreso de renta** when the product defines one; otherwise the product or category income account is used. The field is company-dependent and cannot point to receivable, payable, cash, credit card or off-balance accounts.

**Notifications.** The daily cron **Rentas: recordatorios y retrasos** emails, once per event:

- a collection reminder when the collection datetime falls within the next 24 hours;
- a late alert when the collection datetime has passed and the rental is still *Por entregar* or *Activo*.

Recipients are the active users of **Administrador de rentas** plus the order's creator and salesperson, with duplicate addresses removed. Changing **Recolección** re-arms both notifications.

## Rental Lifecycle

```
pending (Por entregar) ──Entregar──> active (Activo) ──Devolver──> returned (Devuelto) ──Cerrar renta──> closed (Cerrado)
```

Rules enforced by the module:

- A quotation is **sale XOR rental**. Once confirmed, `is_rental` cannot be changed: cancel and return the order to quotation first.
- Rental quotations only accept products marked as rentable; confirmation requires event, delivery and collection dates.
- Collection cannot be earlier than delivery.
- The price is the product's **fixed per-event tariff**, converted to the order currency when they differ, and remains editable per line — it is never prorated by duration.
- Deliver and return create **real stock moves** (outgoing and incoming).
- `rental_is_late` is a non-stored computed field with a hand-written search method, so it works in filters and report domains.
- Only the exact lifecycle transitions above are accepted; the form buttons are hidden when the action is not applicable.

## Module Structure

| Path | What it contains |
|---|---|
| `__manifest__.py` | Manifest: metadata, dependencies and ordered data files (also holds the long description) |
| `models/product.py` | `rental_ok`, `rental_price`, `rental_income_account_id` |
| `models/sale_order.py` | `is_rental`, event dates, `rental_status` lifecycle, constraints, cron notifications, `write()` overrides |
| `models/sale_order_line.py` | Rental tariff in `_get_display_price`, rental account in `_prepare_invoice_line` |
| `models/stock_picking.py` | `_action_done` → `_sync_rental_status` keeps status aligned when a picking is validated natively |
| `views/sale_order_views.xml` | Rental fields and lifecycle buttons on the sale order form |
| `views/product_views.xml` | **Renta** tab on the product form |
| `views/rental_active_views.xml` | "Artículos en renta" list and search |
| `views/rental_report_views.xml` | Active/late rental lists, income pivot and graph, report actions |
| `views/menus.xml` | **Rentas** menu and its actions |
| `security/rental_security.xml` | Rental user and manager groups (Odoo 19 privilege-based) |
| `report/rental_report.xml` | Sale order PDF extension and the **Confirmación de renta** report |
| `data/ir_cron.xml` | Daily notification cron (`noupdate="1"`) |
| `data/rental_mail_templates.xml` | Reminder and late-alert mail templates (`noupdate="1"`) |
| `i18n/es.po` | Translation header only — source strings are already Spanish |

## Reports and Automations

- **Confirmación de renta** — PDF built on `sale.report_saleorder_document`, adding event, delivery and collection dates and replacing the document title for confirmed rentals. Print it from the order header.
- **Rentas activas** — confirmed rentals in *Activo*, with partner, dates, status and amount.
- **Retrasos** — confirmed rentals past their collection datetime that are still *Por entregar* or *Activo*; late rows are highlighted in red in the rental list.
- **Ingresos (renta vs venta)** — pivot and bar graph comparing rental and sales revenue on confirmed orders.
- **Artículos en renta** — line-level view of everything currently rented, groupable by product or order.

## Scope and Limitations

Out of scope for this version:

- Partial returns (returns validate the full delivered quantity).
- Damage or late-return charges.
- Recurring or prorated billing; the tariff is fixed per event.
- Deposits (`CFDI de anticipo`) and other localization-specific invoicing flows.
- Automated closing: a returned rental stays *Devuelto* until someone clicks **Cerrar renta**.

The module ships **no customer data, domains or credentials**: each deployment lives in its own repository.

## Contributing

This is a small, single-maintainer addon with no enforced branch model or commit convention. If you send a change:

- Keep the technical name `sale_rental_fixed`; it is embedded in XML IDs, `env.ref` calls, report names and the manifest.
- Bump `version` in `__manifest__.py` (keep the `19.0.x.y.z` format) when behavior changes, and add new XML files to the `data` list in load order.
- Preserve the business field names (`fecha_evento`, `entrega_dt`, `recoleccion_dt`) and technical switches (`is_rental`, `rental_status`); views, reports and translations depend on them.
- Keep dependencies to standard Odoo modules; do not add OCA or custom addons.
- Write user-facing Python errors with `_()`; XML labels and help texts stay in Spanish.
- Verify manually following the acceptance check above — there are no automated tests.
- Never add client names, domains, emails, credentials or deployment data.

## License

This module is free and open-source software, released for anyone to use, study, modify and redistribute under the **GNU Lesser General Public License v3.0 (LGPL-3)**. The full text is in [`LICENSE`](LICENSE) and is declared as `LGPL-3` in [`__manifest__.py`](__manifest__.py).
