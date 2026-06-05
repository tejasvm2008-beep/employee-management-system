from flask import Blueprint, g, jsonify, request

from controllers.auth_controller import (
    get_employees_list,
    get_manager_approval_requests,
    login_admin,
    login_user,
    register_admin,
    registration,
    reset_password,
    update_manager_approval,
)
from middleware.auth_middleware import role_required, token_required

auth_routes = Blueprint("auth_routes", __name__)


@auth_routes.post("/register")
def register():
    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "employee")

    try:
        user = registration(name, email, password, role)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "User registered successfully",
        "user": user
    }), 200


@auth_routes.post("/login")
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    try:
        login_data = login_user(email, password)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "login successful",
        **login_data
    }), 200


@auth_routes.post("/admin/register")
def admin_register():
    data = request.get_json() or {}

    try:
        admin = register_admin(
            data.get("name"),
            data.get("email"),
            data.get("password")
        )
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "admin registered successfully",
        "admin": admin
    }), 201


@auth_routes.post("/admin/login")
def admin_login():
    data = request.get_json() or {}

    try:
        login_data = login_admin(
            data.get("email"),
            data.get("password")
        )
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "admin login successful",
        **login_data
    }), 200


@auth_routes.patch("/forgot-password")
@token_required
def forgot_password():
    data = request.get_json() or {}

    email = data.get("email")
    new_password = data.get("new_password")
    current_user = g.current_user

    if current_user.get("role") != "admin" and email != current_user.get("email"):
        return jsonify({
            "message": "you can only reset your own password"
        }), 403

    try:
        user = reset_password(email, new_password)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "password reset successfully",
        "user": user
    }), 200


@auth_routes.get("/employees")
@role_required("manager", "admin")
def list_employees():
    try:
        employees = get_employees_list()
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "employees fetched successfully",
        "employees": employees,
    }), 200


@auth_routes.get("/admin/manager-requests")
@role_required("admin")
def get_manager_requests():
    try:
        managers = get_manager_approval_requests()
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "manager approval requests fetched successfully",
        "managers": managers
    }), 200


@auth_routes.patch("/admin/manager-requests/<user_id>")
@role_required("admin")
def approve_or_reject_manager(user_id):
    data = request.get_json() or {}

    try:
        manager = update_manager_approval(
            user_id,
            data.get("approval_status")
        )
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "manager approval status updated successfully",
        "manager": manager
    }), 200
