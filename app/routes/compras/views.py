from flask import Blueprint, request, jsonify
from ...odoo_connector import OdooConnector
from datetime import datetime

def format_mxn(value):
    return f"${value:,.2f}"

compras_bp = Blueprint('compras', __name__)

@compras_bp.route("/", methods=["GET"])
def compras_summary():
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if not start_date or not end_date:
        return jsonify({"error": "Parámetros 'start' y 'end' requeridos en formato YYYY-MM-DD"}), 400

    try:
        connector = OdooConnector()

        # Fechas actuales y previas
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta = end - start
        prev_start = (start - delta).strftime("%Y-%m-%d")
        prev_end = (end - delta).strftime("%Y-%m-%d")

        # === Compras Confirmadas (purchase.order) ===
        domain_orders = [
            ['date_order', '>=', start_date],
            ['date_order', '<=', end_date],
            ['state', '=', 'purchase']
        ]

        orders_total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'purchase.order', 'read_group',
            [domain_orders, ['amount_total'], []]
        )
        orders_count = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'purchase.order', 'search_count',
            [domain_orders]
        )

        total_confirmed_purchases = orders_total[0]['amount_total'] if orders_total else 0.0

        # === Compras periodo anterior ===
        domain_orders_prev = [
            ['date_order', '>=', prev_start],
            ['date_order', '<=', prev_end],
            ['state', '=', 'purchase']
        ]
        orders_prev_total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'purchase.order', 'read_group',
            [domain_orders_prev, ['amount_total'], []]
        )
        previous_confirmed_purchases = orders_prev_total[0]['amount_total'] if orders_prev_total else 0.0

        if previous_confirmed_purchases > 0:
            trend_compras = ((total_confirmed_purchases - previous_confirmed_purchases) / previous_confirmed_purchases) * 100
        else:
            trend_compras = 100.0 if total_confirmed_purchases > 0 else 0.0

        is_positive_compras = trend_compras >= 0
        trend_str_compras = f"{trend_compras:+.1f}%"
        mensaje_compras = (
            "Compras incrementaron" if trend_compras > 0
            else "Compras disminuyeron" if trend_compras < 0
            else "Compras se mantuvieron"
        )

        # === Facturas proveedores (account.move) ===
        domain_bills_posted = [
            ['invoice_date', '>=', start_date],
            ['invoice_date', '<=', end_date],
            ['move_type', '=', 'in_invoice'],
            ['state', '=', 'posted']
        ]
        domain_bills_draft = [
            ['invoice_date', '>=', start_date],
            ['invoice_date', '<=', end_date],
            ['move_type', '=', 'in_invoice'],
            ['state', '=', 'draft']
        ]

        bills_posted_total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.move', 'read_group',
            [domain_bills_posted, ['amount_total'], []]
        )
        bills_posted_count = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.move', 'search_count',
            [domain_bills_posted]
        )
        bills_draft_count = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.move', 'search_count',
            [domain_bills_draft]
        )

        total_billed_purchases = bills_posted_total[0]['amount_total'] if bills_posted_total else 0.0

        # === Facturación anterior ===
        domain_bills_prev = [
            ['invoice_date', '>=', prev_start],
            ['invoice_date', '<=', prev_end],
            ['move_type', '=', 'in_invoice'],
            ['state', '=', 'posted']
        ]
        prev_bills = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.move', 'read_group',
            [domain_bills_prev, ['amount_total'], []]
        )
        previous_billed = prev_bills[0]['amount_total'] if prev_bills else 0.0

        trend_facturacion = ((total_billed_purchases - previous_billed) / previous_billed) * 100 if previous_billed > 0 else (100.0 if total_billed_purchases > 0 else 0.0)
        is_positive_facturacion = trend_facturacion >= 0
        trend_str_facturacion = f"{trend_facturacion:+.1f}%"
        mensaje_facturacion = (
            "Facturación de proveedor incrementó" if trend_facturacion > 0
            else "Facturación disminuyó" if trend_facturacion < 0
            else "Facturación se mantuvo"
        )

        # === Pagos realizados (account.payment) ===
        domain_payments = [
            ['date', '>=', start_date],
            ['date', '<=', end_date],
            ['payment_type', '=', 'outbound'],
            ['state', '=', 'posted']
        ]
        payments_total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.payment', 'read_group',
            [domain_payments, ['amount'], []]
        )
        payments_count = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.payment', 'search_count',
            [domain_payments]
        )
        total_paid = payments_total[0]['amount'] if payments_total else 0.0

        # === Pagos anteriores ===
        domain_payments_prev = [
            ['date', '>=', prev_start],
            ['date', '<=', prev_end],
            ['payment_type', '=', 'outbound'],
            ['state', '=', 'posted']
        ]
        payments_prev_total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.payment', 'read_group',
            [domain_payments_prev, ['amount'], []]
        )
        previous_paid = payments_prev_total[0]['amount'] if payments_prev_total else 0.0

        trend_pagos = ((total_paid - previous_paid) / previous_paid) * 100 if previous_paid > 0 else (100.0 if total_paid > 0 else 0.0)
        is_positive_pagos = trend_pagos >= 0
        trend_str_pagos = f"{trend_pagos:+.1f}%"
        mensaje_pagos = (
            "Pagos realizados incrementaron" if trend_pagos > 0
            else "Pagos disminuyeron" if trend_pagos < 0
            else "Pagos se mantuvieron"
        )

        return jsonify({
            "compras_confirmadas": {
                "total_comprado": format_mxn(total_confirmed_purchases),
                "ordenes_compra": orders_count
            },
            "facturacion_proveedor": {
                "total_facturado": format_mxn(total_billed_purchases),
                "facturas_posteadas": bills_posted_count,
                "facturas_borrador": bills_draft_count
            },
            "pagos_realizados": {
                "total_pagado": format_mxn(total_paid),
                "pagos_efectuados": payments_count
            },
            "analisis_periodo": {
                "compras": {
                    "comparativa": trend_str_compras,
                    "esPositivo": is_positive_compras,
                    "mensaje": mensaje_compras + " respecto al periodo anterior"
                },
                "facturacion": {
                    "comparativa": trend_str_facturacion,
                    "esPositivo": is_positive_facturacion,
                    "mensaje": mensaje_facturacion + " respecto al periodo anterior"
                },
                "pagos": {
                    "comparativa": trend_str_pagos,
                    "esPositivo": is_positive_pagos,
                    "mensaje": mensaje_pagos + " respecto al periodo anterior"
                }
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
