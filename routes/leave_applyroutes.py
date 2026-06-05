from flask import Blueprint, jsonify, request

from controllers.leave_controller import (
    apply_leave,
    get_all_leave_applications,
    get_employee_leave_applications,
    get_leave_balance,
    get_leave_application,
    update_leave_status,
)
from middleware.auth_middleware import employee_or_role_required, role_required

leave_routes = Blueprint("leave_routes", __name__)


@leave_routes.post("/leave/apply")
@employee_or_role_required(
    lambda *args, **kwargs: (request.get_json() or {}).get("employee_id"),
    "manager",
    "admin"
)
def create_leave_application():
    data = request.get_json() or {}

    try:
        leave = apply_leave(
            data.get("employee_id"),
            data.get("leave_type"),
            data.get("start_date"),
            data.get("end_date"),
            data.get("reason")
        )
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "leave application submitted successfully",
        "leave": leave
    }), 201


@leave_routes.get("/leave")
@role_required("manager", "admin")
def get_all_leaves():
    try:
        leaves = get_all_leave_applications()
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "leave applications fetched successfully",
        "leaves": leaves
    }), 200


@leave_routes.get("/leave/employee/<employee_id>")
@employee_or_role_required(lambda *args, **kwargs: kwargs.get("employee_id"), "manager", "admin")
def get_employee_leaves(employee_id):
    try:
        leaves = get_employee_leave_applications(employee_id)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "employee leave applications fetched successfully",
        "leaves": leaves
    }), 200


@leave_routes.get("/leave/balance/<employee_id>")
@employee_or_role_required(lambda *args, **kwargs: kwargs.get("employee_id"), "manager", "admin")
def get_employee_leave_balance(employee_id):
    year = request.args.get("year")

    try:
        balance = get_leave_balance(employee_id, year)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "leave balance fetched successfully",
        "balance": balance
    }), 200


@leave_routes.get("/leave/<leave_id>")
@role_required("manager", "admin")
def get_leave(leave_id):
    try:
        leave = get_leave_application(leave_id)
    except ValueError as error:
        return jsonify({"message": str(error)}), 404
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "leave application fetched successfully",
        "leave": leave
    }), 200


@leave_routes.patch("/leave/<leave_id>/status")
@role_required("manager", "admin")
def change_leave_status(leave_id):
    data = request.get_json() or {}

    try:
        leave = update_leave_status(
            leave_id,
            data.get("status"),
            data.get("manager_comment")
        )
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "leave status updated successfully",
        "leave": leave
    }), 200
