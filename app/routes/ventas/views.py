from flask import Blueprint, jsonify
from ...odoo_connector import OdooConnector

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route("/", methods=["GET"])
def ventas_summary():
    try:
        connector = OdooConnector()

        print(f"[DEBUG] Odoo DB: {connector.db}, UID: {connector.uid}, Username: {connector.username}", flush=True)

        domain = [
            ["state", "in", ["sale", "done"]]
        ]

        print(f"Dominio usado para consulta (sin fechas): {domain}", flush=True)

        total_confirmed_sales = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            "sale.order", "search_count",
            [domain]
        )

        print(f"[DEBUG] Total de ventas confirmadas encontradas: {total_confirmed_sales}", flush=True)

        result = {
            "section": "Ventas Confirmadas",
            "icon": "ClipboardCheckIcon",
            "description": "Número de Pedidos Confirmados",
            "value": f"{total_confirmed_sales}",
            "trend": "+5%",  # valor opcional
            "isPositive": True,
            "footerMain": "Pedidos activos",
            "footerDetail": "Confirmados o completados en total"
        }

        return jsonify(result)

    except Exception as e:
        print(f"Error al ejecutar consulta: {str(e)}", flush=True)
        return jsonify({"error": str(e)}), 500
