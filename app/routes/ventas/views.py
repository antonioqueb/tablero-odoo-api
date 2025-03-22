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

        # DEBUG ADDED: Verifica la DB, el UID y el usuario obtenido tras la autenticación
        print(f"[DEBUG] Odoo DB: {connector.db}, UID: {connector.uid}, Username: {connector.user}", flush=True)

        # DEBUG ADDED: Prueba de acceso simple al modelo "sale.order" para confirmar permisos
        try:
            test_search = connector.models.execute_kw(
                connector.db, connector.uid, connector.password,
                "sale.order", "search",
                [[[]]]  # dominio vacío para obtener cualquier registro
            )
            print(f"[DEBUG] Resultado de test_search: Se encontraron {len(test_search)} registros.", flush=True)
        except Exception as test_e:
            print(f"[DEBUG] Error en test_search (prueba de permisos): {test_e}", flush=True)

        # Filtrar solo pedidos confirmados en las fechas indicadas
        domain = [
            ["date_order", ">=", start_date],
            ["date_order", "<=", end_date],
            ["state", "in", ["sale", "done"]]
        ]

        print(f"Dominio usado para consulta: {domain}", flush=True)  # DEPURACIÓN

        # Ejecutar read_group para sumar monto total de los pedidos
        total = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            "sale.order", "read_group",
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
            "description": "Ingresos Totales por Pedidos",
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
