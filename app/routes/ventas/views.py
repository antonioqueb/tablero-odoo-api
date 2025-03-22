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

        # === Cálculo de tendencia ===
        prev_start = (start - delta).strftime("%Y-%m-%d")
        prev_end = (end - delta).strftime("%Y-%m-%d")
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
            trend_value = ((total_invoiced_sales - previous_total) / previous_total) * 100
        else:
            trend_value = 100.0 if total_invoiced_sales > 0 else 0.0

        is_positive = trend_value >= 0
        trend_str = f"{trend_value:+.1f}%"

        if trend_value > 0:
            footer_main = "Ventas incrementaron"
        elif trend_value < 0:
            footer_main = "Ventas disminuyeron"
        else:
            footer_main = "Ventas se mantuvieron"

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
            "analisis_periodo": {
                "comparativa": trend_str,
                "esPositivo": is_positive,
                "mensaje": footer_main + " respecto al periodo anterior"
            }
        }


        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
