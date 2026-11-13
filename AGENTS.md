# AGENTS.md — sale_rental_fixed

Standalone Odoo **19.0 Community** addon `sale_rental_fixed`, listed in Apps as
**Renta de Productos por Evento**: fixed-price product rentals per event, kept
separate from regular sales quotations. LGPL-3. UI, field labels, help texts
and comments are in Spanish (es_MX).

This repository **is** the addon: `__manifest__.py` sits at the repo root. It
has no dev stack, Makefile, CI, tests, linter or formatter.

## Run and verify

Put the repo folder in an Odoo 19 `addons_path` and install or update it with
the Odoo CLI:

```bash
odoo -d <db> -i sale_rental_fixed --stop-after-init
odoo -d <db> -u sale_rental_fixed --stop-after-init
```

The technical module name is the folder name, `sale_rental_fixed`; the Apps
listing shows **Renta de Productos por Evento** from the manifest `name`. A
module update is required after Python, XML or data changes; restarting Odoo
alone does not reload them.

There are no automated tests. Verify manually:

1. Product → **Renta** tab: enable **Se puede rentar** and set the tariff.
2. Create a rental quotation with the three dates and the delivery address,
   add a rentable product, confirm it.
3. **Entregar** → Activo; **Devolver** → Devuelto; **Cerrar renta**.
4. Review the Rentas reports (activas, retrasos, ingresos).

## Naming and publishing

The technical name `sale_rental_fixed` is the folder name and is embedded in
XML IDs and `env.ref` calls. If it ever changes, update all of these together:

- `views/sale_order_views.xml` — `%(<module>.action_report_rental_order)d`
- `report/rental_report.xml` — `report_name` and `report_file`
- `models/sale_order.py` — `env.ref("<module>.mail_template_rental_*")` and
  `env.ref("<module>.group_rental_manager")`
- `i18n/es.po` — module header
- `__manifest__.py` — `version` (keep `19.0.x.y.z`)
- the folder and GitHub repository name

Keep the repo root as the addon root: Odoo scans one level under an addons
path, so do not nest the module in a subfolder.

`.agents/` and `skills-lock.json` are local agent-tooling artifacts, not module
code; both are ignored by `.gitignore` and must not be packaged with the addon.
`__pycache__/`, `.codegraph/`, local Odoo configs, logs and database dumps are
ignored too; `.gitignore` is the source of truth for what stays out of the
repository.

## Module layout

| Path | What matters |
|---|---|
| `models/sale_order.py` | `is_rental`, event dates, `rental_status` lifecycle, cron notifications, `write()` overrides |
| `models/sale_order_line.py` | `_get_display_price` (rental tariff) and `_prepare_invoice_line` (rental income account) |
| `models/product.py` | `rental_ok`, `rental_price`, `rental_income_account_id` |
| `models/stock_picking.py` | `_action_done` → `_sync_rental_status` keeps status consistent when a picking is validated from the native UI |
| `views/` | order form/header buttons, product "Renta" tab, active-rental list, reports, menus |
| `security/rental_security.xml` | rental user/manager groups |
| `report/rental_report.xml` | sale-order PDF inheritance + "Confirmación de renta" report |
| `data/` | daily cron and mail templates, both `noupdate="1"` |
| `i18n/es.po` | header only: source strings are already Spanish |
| `README.md` | public documentation: install, usage, lifecycle, scope |
| `LICENSE` | GNU LGPL-3 full text |
| `.gitignore` | excludes Python/Odoo artifacts, secrets and local agent tooling |

## Rental rules to preserve

- A quotation is **sale XOR rental**. Changing `is_rental` is blocked once the
  order is confirmed; the user must cancel and return to quotation.
- Rental orders only accept products with `rental_ok`; confirmation requires
  `fecha_evento`, `entrega_dt`, `recoleccion_dt` and `domicilio_entrega`, and
  return must not precede delivery.
- `domicilio_entrega` is typed on each quotation instead of using the contact
  address: the same customer may receive rentals at different addresses, and
  the field must stay out of the invoicing address.
- Rental PDFs (standard quotation/order and "Confirmación de renta") print only
  the customer name and RFC: the contact's billing and shipping addresses are
  suppressed in `report/rental_report.xml`. Do not re-add them; the operational
  address is `domicilio_entrega`.
- Price is the product's **fixed per-event tariff** (`rental_price`), not
  prorated by duration, and remains editable per line.
- Lifecycle is `pending → active → returned → closed`, enforced by
  `_check_rental_action`. The form buttons use matching `invisible` conditions;
  keep model and view conditions in sync.
- Deliveries/returns create real stock moves. Partial returns, damage charges,
  recurring invoicing and CFDI de anticipo are out of scope for v1.
- Confirmed rental PDFs end with a blank black signature line for the customer.
  It is print layout only: no field is added and nothing is stored, so the
  signature is captured by hand on the printed copy.
- Rental invoice lines use `rental_income_account_id` when set; otherwise the
  native product/category income account.
- Notifications are sent once. `write()` resets `rental_late_notified` and
  `rental_reminder_sent` whenever `recoleccion_dt` changes; do not remove that
  without providing another re-arm mechanism.

## Odoo 19 gotchas in this module

- `rental_is_late` is a **non-stored computed field** with a hand-written
  `_search_rental_is_late`. Any domain using it depends on that method — update
  both when changing late logic.
- Security groups use `res.groups.privilege` + `privilege_id`, **not**
  `category_id` (Odoo 19 changed this).
- Views use Odoo 19 tags: `<list>`, `<pivot>`, `<graph>` (not `<tree>`).
- `sale.report_saleorder_document` builds the customer block in
  `t-set="address"` (contact widget) and the billing/shipping addresses in
  `t-set="information_block"`. `report/rental_report.xml` overrides those nodes
  by XPath, so re-check the selectors when upgrading Odoo.
- `data/ir_cron.xml` and `data/rental_mail_templates.xml` use
  `noupdate="1"`: a module update will not overwrite records already in the
  database. For changes to existing records, edit them via UI/shell or add a
  migration; editing the XML only affects fresh installs.
- The cron calls `model._cron_rental_notifications()`; the method is on
  `sale.order`. To test it, run `env['sale.order']._cron_rental_notifications()`
  from an Odoo shell.
- New XML files must be added to the `data` list in `__manifest__.py`; the list
  order is the load order.

## Conventions

- Keep `version` in `__manifest__.py` at `19.0.x.y.z`; bump it when behavior
  changes.
- Dependencies are standard Odoo only: `sale`, `stock`, `account`, `mail`. Do
  not add OCA or other custom-addon dependencies.
- Match existing naming: business fields in Spanish (`fecha_evento`,
  `entrega_dt`, `recoleccion_dt`, `domicilio_entrega`), technical switches in
  English (`is_rental`, `rental_status`). Do not rename them casually — views,
  reports and translation keys depend on them.
- Use `_()` for user-facing Python errors; XML strings and labels are written
  directly in Spanish.
- Never add client names, domains, emails, credentials or deployment data.
- `README.md` and `LICENSE` are public-facing: keep the README accurate when
  behavior changes, and keep the license LGPL-3. `docs/` does not exist yet.
