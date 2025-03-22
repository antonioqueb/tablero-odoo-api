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
        domain = [["invoice_date", ">=", start_date], ["invoice_date", "<=", end_date], ["move_type", "=", "out_invoice"], ["state", "=", "posted"]]
        total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            "account.move", "read_group",
            [domain, ["amount_total"], []]
        )


        total_value = total[0]["amount_total"] if total else 0.0

        result = {
            "section": "Ventas",
            "icon": "DollarSignIcon",
            "description": "Ingresos Totales",
            "value": f"${total_value:,.2f}",
            "trend": "+8%",  # Valor estático para el ejemplo
            "isPositive": True,
            "footerMain": "Ventas incrementaron",
            "footerDetail": "Último mes comparado al anterior"
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
