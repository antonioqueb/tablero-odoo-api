from flask import Blueprint, request, jsonify
from ...odoo_connector import OdooConnector

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route("/", methods=["GET"])
def ventas_summary():
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if not start_date or not end_date:
        return jsonify({"error": "Parámetros 'start' y 'end' requeridos en formato YYYY-MM-DD"}), 400

    try:
        connector = OdooConnector()
        domain = [
            ["invoice_date", ">=", start_date],
            ["invoice_date", "<=", end_date],
            ["move_type", "=", "out_invoice"],
            ["state", "=", "posted"]
        ]

        print(f"Dominio usado para consulta: {domain}", flush=True)  # DEPURACIÓN

        total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            "account.move", "read_group",
            [domain, ["amount_total"], []]
        )

        print(f"Respuesta completa de read_group: {total}", flush=True)  # DEPURACIÓN

        if total and isinstance(total, list) and 'amount_total' in total[0]:
            total_value = total[0]["amount_total"]
        else:
            print("La respuesta 'total' está vacía o mal estructurada.", flush=True)  # DEPURACIÓN
            total_value = 0.0

        result = {
            "section": "Ventas",
            "icon": "DollarSignIcon",
            "description": "Ingresos Totales",
            "value": f"${total_value:,.2f}",
            "trend": "+8%",  # Valor estático
            "isPositive": True,
            "footerMain": "Ventas incrementaron",
            "footerDetail": "Último mes comparado al anterior"
        }

        print(f"Resultado final a retornar: {result}", flush=True)  # DEPURACIÓN

        return jsonify(result)

    except Exception as e:
        print(f"Error al ejecutar consulta: {str(e)}", flush=True)  # DEPURACIÓN
        return jsonify({"error": str(e)}), 500
