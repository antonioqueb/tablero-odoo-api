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

        # Parseo de fechas
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
        eficiencia = (completed_orders / total_orders * 100) if total_orders > 0 else 0.0

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

        total_orders_prev = len(production_prev)
        completed_orders_prev = sum(1 for p in production_prev if p['state'] == 'done')
        total_units_prev = sum(p['product_qty'] for p in production_prev)
        eficiencia_prev = (completed_orders_prev / total_orders_prev * 100) if total_orders_prev > 0 else 0.0

        # === Cálculos comparativos ===

        def calcular_tendencia(actual, anterior):
            if anterior > 0:
                cambio = ((actual - anterior) / anterior) * 100
            else:
                cambio = 100.0 if actual > 0 else 0.0
            return cambio

        # Producción (unidades fabricadas)
        trend_produccion = calcular_tendencia(total_units, total_units_prev)
        is_positive_produccion = trend_produccion >= 0
        trend_str_produccion = f"{trend_produccion:+.1f}%"
        mensaje_produccion = (
            "Producción aumentó" if trend_produccion > 0
            else "Producción disminuyó" if trend_produccion < 0
            else "Producción se mantuvo"
        )

        # Órdenes de producción
        trend_ordenes = calcular_tendencia(total_orders, total_orders_prev)
        is_positive_ordenes = trend_ordenes >= 0
        trend_str_ordenes = f"{trend_ordenes:+.1f}%"
        mensaje_ordenes = (
            "Órdenes de producción aumentaron" if trend_ordenes > 0
            else "Órdenes disminuyeron" if trend_ordenes < 0
            else "Órdenes se mantuvieron"
        )

        # Eficiencia
        trend_eficiencia = calcular_tendencia(eficiencia, eficiencia_prev)
        is_positive_eficiencia = trend_eficiencia >= 0
        trend_str_eficiencia = f"{trend_eficiencia:+.1f}%"
        mensaje_eficiencia = (
            "Eficiencia mejoró" if trend_eficiencia > 0
            else "Eficiencia disminuyó" if trend_eficiencia < 0
            else "Eficiencia se mantuvo"
        )

        # === Respuesta organizada estilo KPIs ===
        result = {
            "ordenes_produccion": {
                "total_ordenes": total_orders,
                "ordenes_completadas": completed_orders,
                "ordenes_pendientes": pending_orders,
                "analisis_periodo": {
                    "comparativa": trend_str_ordenes,
                    "esPositivo": is_positive_ordenes,
                    "mensaje": mensaje_ordenes + " respecto al periodo anterior"
                }
            },
            "volumen_producido": {
                "unidades_fabricadas": total_units,
                "analisis_periodo": {
                    "comparativa": trend_str_produccion,
                    "esPositivo": is_positive_produccion,
                    "mensaje": mensaje_produccion + " respecto al periodo anterior"
                }
            },
            "eficiencia": {
                "porcentaje_completado": f"{eficiencia:.1f}%",
                "analisis_periodo": {
                    "comparativa": trend_str_eficiencia,
                    "esPositivo": is_positive_eficiencia,
                    "mensaje": mensaje_eficiencia + " respecto al periodo anterior"
                }
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
