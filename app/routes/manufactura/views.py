from flask import Blueprint, request, jsonify
from ...odoo_connector import OdooConnector
from datetime import datetime

manufactura_bp = Blueprint('manufactura', __name__)

@manufactura_bp.route("/", methods=["GET"])
def manufactura_summary():
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if not start_date or not end_date:
        return jsonify({"error": "Parámetros 'start' y 'end' requeridos en formato YYYY-MM-DD"}), 400

    try:
        connector = OdooConnector()

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta = end - start
        prev_start = (start - delta).strftime("%Y-%m-%d")
        prev_end = (end - delta).strftime("%Y-%m-%d")

        # === Producción actual (mrp.production) ===
        domain_current = [
            ['create_date', '>=', start_date],
            ['create_date', '<=', end_date]
        ]
        production_orders = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'mrp.production', 'search_read',
            [domain_current],
            {'fields': ['product_qty', 'state']}
        )

        total_orders = len(production_orders)
        completed_orders = sum(1 for p in production_orders if p['state'] == 'done')
        pending_orders = sum(1 for p in production_orders if p['state'] in ['confirmed', 'planned', 'progress'])
        total_units = sum(p['product_qty'] for p in production_orders)

        # === Producción anterior ===
        domain_previous = [
            ['create_date', '>=', prev_start],
            ['create_date', '<=', prev_end]
        ]
        production_prev = connector.models.execute_kw(
            connector.db, connector.uid, connector.password,
            'mrp.production', 'search_read',
            [domain_previous],
            {'fields': ['product_qty', 'state']}
        )

        total_units_prev = sum(p['product_qty'] for p in production_prev)
        trend_produccion = ((total_units - total_units_prev) / total_units_prev) * 100 if total_units_prev > 0 else (100.0 if total_units > 0 else 0.0)
        is_positive = trend_produccion >= 0
        trend_str = f"{trend_produccion:+.1f}%"
        mensaje = (
            "Producción aumentó" if trend_produccion > 0
            else "Producción disminuyó" if trend_produccion < 0
            else "Producción se mantuvo"
        )

        # === Eficiencia de producción ===
        eficiencia = (completed_orders / total_orders * 100) if total_orders > 0 else 0.0

        result = {
            "ordenes_produccion": {
                "total_ordenes": total_orders,
                "ordenes_completadas": completed_orders,
                "ordenes_pendientes": pending_orders
            },
            "volumen_producido": {
                "unidades_fabricadas": total_units
            },
            "eficiencia": {
                "porcentaje_completado": f"{eficiencia:.1f}%",
                "mensaje": "Buena eficiencia" if eficiencia >= 80 else "Revisar eficiencia"
            },
            "analisis_periodo": {
                "comparativa": trend_str,
                "esPositivo": is_positive,
                "mensaje": mensaje + " respecto al periodo anterior"
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
