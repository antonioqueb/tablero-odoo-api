from flask import Blueprint, request, jsonify
from ...odoo_connector import OdooConnector
from datetime import datetime

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

        # === Ventas periodo actual ===
        domain_current = [
            ["invoice_date", ">=", start_date],
            ["invoice_date", "<=", end_date],
            ["move_type", "=", "out_invoice"],
            ["state", "=", "posted"]
        ]
        current = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            "account.move", "read_group",
            [domain_current, ["amount_total"], ["currency_id"]]
        )
        current_total = current[0]["amount_total"] if current else 0.0

        # === Conteo de ventas confirmadas ===
        sales_ids = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            "account.move", "search",
            [domain_current]
        )
        sales_count = len(sales_ids)

        # === Ventas periodo anterior ===
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
            [domain_prev, ["amount_total"], ["currency_id"]]
        )
        previous_total = previous[0]["amount_total"] if previous else 0.0

        # === Cálculo de tendencia ===
        if previous_total > 0:
            trend_value = ((current_total - previous_total) / previous_total) * 100
        else:
            trend_value = 100.0 if current_total > 0 else 0.0

        is_positive = trend_value >= 0
        trend_str = f"{trend_value:+.1f}%"

        if trend_value > 0:
            footer_main = "Ventas incrementaron"
        elif trend_value < 0:
            footer_main = "Ventas disminuyeron"
        else:
            footer_main = "Ventas se mantuvieron"

        footer_detail = "Comparado al periodo anterior"

        # === Respuesta final ===
        result = {
            "section": "Ventas",
            "icon": "DollarSignIcon",
            "description": "Ingresos Totales",
            "value": f"${current_total:,.2f}",
            "trend": trend_str,
            "isPositive": is_positive,
            "footerMain": footer_main,
            "footerDetail": footer_detail,
            "salesCount": sales_count
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
