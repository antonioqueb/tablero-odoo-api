from flask import Blueprint, request, jsonify
from ...odoo_connector import OdooConnector
from datetime import datetime

def format_mxn(value):
    return f"${value:,.2f}"

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route("/", methods=["GET"])
def ventas_summary():
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if not start_date or not end_date:
        return jsonify({"error": "Parámetros 'start' y 'end' requeridos en formato YYYY-MM-DD"}), 400

    try:
        connector = OdooConnector()

        # Parseo de fechas
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta = end - start

        # === Ventas Confirmadas (sale.order) ===
        domain_orders = [
            ['date_order', '>=', start_date],
            ['date_order', '<=', end_date],
            ['state', '=', 'sale']
        ]

        orders_total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'sale.order', 'read_group',
            [domain_orders, ['amount_total'], []]
        )
        orders_count = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'sale.order', 'search_count',
            [domain_orders]
        )

        total_confirmed_sales = orders_total[0]['amount_total'] if orders_total else 0.0

        # === Ventas periodo anterior (sale.order) ===
        prev_start = (start - delta).strftime("%Y-%m-%d")
        prev_end = (end - delta).strftime("%Y-%m-%d")

        domain_orders_prev = [
            ['date_order', '>=', prev_start],
            ['date_order', '<=', prev_end],
            ['state', '=', 'sale']
        ]

        orders_prev_total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'sale.order', 'read_group',
            [domain_orders_prev, ['amount_total'], []]
        )

        previous_confirmed_sales = orders_prev_total[0]['amount_total'] if orders_prev_total else 0.0

        if previous_confirmed_sales > 0:
            trend_ventas = ((total_confirmed_sales - previous_confirmed_sales) / previous_confirmed_sales) * 100
        else:
            trend_ventas = 100.0 if total_confirmed_sales > 0 else 0.0

        is_positive_ventas = trend_ventas >= 0
        trend_str_ventas = f"{trend_ventas:+.1f}%"

        if trend_ventas > 0:
            mensaje_ventas = "Ventas incrementaron"
        elif trend_ventas < 0:
            mensaje_ventas = "Ventas disminuyeron"
        else:
            mensaje_ventas = "Ventas se mantuvieron"

        # === Facturas (account.move) ===
        domain_invoices_posted = [
            ['invoice_date', '>=', start_date],
            ['invoice_date', '<=', end_date],
            ['move_type', '=', 'out_invoice'],
            ['state', '=', 'posted']
        ]

        domain_invoices_pending = [
            ['invoice_date', '>=', start_date],
            ['invoice_date', '<=', end_date],
            ['move_type', '=', 'out_invoice'],
            ['state', '=', 'draft']
        ]

        invoices_posted_total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.move', 'read_group',
            [domain_invoices_posted, ['amount_total'], []]
        )

        invoices_posted_count = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.move', 'search_count',
            [domain_invoices_posted]
        )

        invoices_pending_count = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.move', 'search_count',
            [domain_invoices_pending]
        )

        total_invoiced_sales = invoices_posted_total[0]['amount_total'] if invoices_posted_total else 0.0

        # === Facturación periodo anterior (account.move) ===
        domain_prev = [
            ["invoice_date", ">=", prev_start],
            ["invoice_date", "<=", prev_end],
            ["move_type", "=", "out_invoice"],
            ["state", "=", "posted"]
        ]
        previous = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            "account.move", "read_group",
            [domain_prev, ["amount_total"], []]
        )
        previous_total = previous[0]["amount_total"] if previous else 0.0

        if previous_total > 0:
            trend_facturacion = ((total_invoiced_sales - previous_total) / previous_total) * 100
        else:
            trend_facturacion = 100.0 if total_invoiced_sales > 0 else 0.0

        is_positive_facturacion = trend_facturacion >= 0
        trend_str_facturacion = f"{trend_facturacion:+.1f}%"

        if trend_facturacion > 0:
            mensaje_facturacion = "Facturación incrementó"
        elif trend_facturacion < 0:
            mensaje_facturacion = "Facturación disminuyó"
        else:
            mensaje_facturacion = "Facturación se mantuvo"

        # === Cobros realizados (account.payment) ===
        domain_payments = [
            ['payment_date', '>=', start_date],
            ['payment_date', '<=', end_date],
            ['payment_type', '=', 'inbound'],
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

        total_collected = payments_total[0]['amount'] if payments_total else 0.0

        # === Cobros realizados periodo anterior ===
        domain_payments_prev = [
            ['payment_date', '>=', prev_start],
            ['payment_date', '<=', prev_end],
            ['payment_type', '=', 'inbound'],
            ['state', '=', 'posted']
        ]

        payments_prev_total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'account.payment', 'read_group',
            [domain_payments_prev, ['amount'], []]
        )

        previous_collected = payments_prev_total[0]['amount'] if payments_prev_total else 0.0

        if previous_collected > 0:
            trend_cobros = ((total_collected - previous_collected) / previous_collected) * 100
        else:
            trend_cobros = 100.0 if total_collected > 0 else 0.0

        is_positive_cobros = trend_cobros >= 0
        trend_str_cobros = f"{trend_cobros:+.1f}%"

        if trend_cobros > 0:
            mensaje_cobros = "Cobros incrementaron"
        elif trend_cobros < 0:
            mensaje_cobros = "Cobros disminuyeron"
        else:
            mensaje_cobros = "Cobros se mantuvieron"

        # === Respuesta final organizada ===
        result = {
            "ventas_confirmadas": {
                "ingresos_totales": format_mxn(total_confirmed_sales),
                "cantidad_ordenes": orders_count
            },
            "facturacion": {
                "total_facturado": format_mxn(total_invoiced_sales),
                "facturas_realizadas": invoices_posted_count,
                "facturas_pendientes": invoices_pending_count
            },
            "cobros_realizados": {
                "total_cobrado": format_mxn(total_collected),
                "pagos_recibidos": payments_count
            },
            "analisis_periodo": {
                "ventas": {
                    "comparativa": trend_str_ventas,
                    "esPositivo": is_positive_ventas,
                    "mensaje": mensaje_ventas + " respecto al periodo anterior"
                },
                "facturacion": {
                    "comparativa": trend_str_facturacion,
                    "esPositivo": is_positive_facturacion,
                    "mensaje": mensaje_facturacion + " respecto al periodo anterior"
                },
                "cobros": {
                    "comparativa": trend_str_cobros,
                    "esPositivo": is_positive_cobros,
                    "mensaje": mensaje_cobros + " respecto al periodo anterior"
                }
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
