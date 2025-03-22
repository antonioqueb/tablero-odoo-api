from flask import Blueprint, jsonify
from ...odoo_connector import OdooConnector

health_bp = Blueprint('health', __name__)

@health_bp.route("/", methods=["GET"])
def health_check():
    try:
        connector = OdooConnector()
        status, info = connector.is_connected()
        return jsonify({
            "status": "success" if status else "error",
            "details": info
        }), 200 if status else 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "details": str(e)
        }), 500
