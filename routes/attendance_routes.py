from flask import Blueprint, jsonify, request

from controllers.attendance_controller import (
    check_in_employee,
    check_out_employee,
    get_all_attendance_records,
    get_employee_attendance_records,
    get_today_attendance_record,
    update_attendance_record,
)
from middleware.auth_middleware import employee_or_role_required, role_required

attendance_routes = Blueprint("attendance_routes", __name__)


@attendance_routes.post("/attendance/check-in")
@employee_or_role_required(
    lambda *args, **kwargs: (request.get_json() or {}).get("employee_id"),
    "manager",
    "admin"
)
def check_in():
    data = request.get_json() or {}

    try:
        attendance = check_in_employee(data.get("employee_id"))
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "check-in successful",
        "attendance": attendance
    }), 201


@attendance_routes.patch("/attendance/check-out")
@employee_or_role_required(
    lambda *args, **kwargs: (request.get_json() or {}).get("employee_id"),
    "manager",
    "admin"
)
def check_out():
    data = request.get_json() or {}

    try:
        attendance = check_out_employee(data.get("employee_id"))
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "check-out successful",
        "attendance": attendance
    }), 200


@attendance_routes.get("/attendance")
@role_required("manager", "admin")
def get_all_attendance():
    try:
        attendance = get_all_attendance_records()
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "attendance records fetched successfully",
        "attendance": attendance
    }), 200


@attendance_routes.get("/attendance/<employee_id>")
@employee_or_role_required(lambda *args, **kwargs: kwargs.get("employee_id"), "manager", "admin")
def get_employee_attendance(employee_id):
    try:
        attendance = get_employee_attendance_records(employee_id)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "employee attendance fetched successfully",
        "attendance": attendance
    }), 200


@attendance_routes.get("/attendance/today/<employee_id>")
@employee_or_role_required(lambda *args, **kwargs: kwargs.get("employee_id"), "manager", "admin")
def get_today_attendance(employee_id):
    try:
        attendance = get_today_attendance_record(employee_id)
    except ValueError as error:
        return jsonify({"message": str(error)}), 404
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "today attendance fetched successfully",
        "attendance": attendance
    }), 200


@attendance_routes.patch("/attendance/<attendance_id>")
@role_required("manager", "admin")
def update_attendance(attendance_id):
    data = request.get_json() or {}

    try:
        attendance = update_attendance_record(attendance_id, data)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "attendance updated successfully",
        "attendance": attendance
    }), 200
