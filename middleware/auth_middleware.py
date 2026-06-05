from functools import wraps

from flask import g, jsonify, request

from controllers.auth_controller import verify_access_token


def get_bearer_token():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    return auth_header.split(" ", 1)[1].strip()


def token_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        access_token = get_bearer_token()

        if not access_token:
            return jsonify({
                "message": "Authorization header with Bearer token is required"
            }), 401

        try:
            g.current_user = verify_access_token(access_token)
        except ValueError as error:
            return jsonify({"message": str(error)}), 401

        return route_function(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    def decorator(route_function):
        @wraps(route_function)
        def wrapper(*args, **kwargs):
            access_token = get_bearer_token()

            if not access_token:
                return jsonify({
                    "message": "Authorization header with Bearer token is required"
                }), 401

            try:
                current_user = verify_access_token(access_token)
            except ValueError as error:
                return jsonify({"message": str(error)}), 401

            if current_user.get("role") not in allowed_roles:
                return jsonify({
                    "message": "you do not have permission to access this route"
                }), 403

            g.current_user = current_user
            return route_function(*args, **kwargs)

        return wrapper

    return decorator


def employee_or_role_required(employee_id_getter, *allowed_roles):
    def decorator(route_function):
        @wraps(route_function)
        def wrapper(*args, **kwargs):
            access_token = get_bearer_token()

            if not access_token:
                return jsonify({
                    "message": "Authorization header with Bearer token is required"
                }), 401

            try:
                current_user = verify_access_token(access_token)
            except ValueError as error:
                return jsonify({"message": str(error)}), 401

            requested_employee_id = employee_id_getter(*args, **kwargs)
            current_user_id = current_user.get("user_id")
            current_user_role = current_user.get("role")

            if (
                requested_employee_id != current_user_id
                and current_user_role not in allowed_roles
            ):
                return jsonify({
                    "message": "you can only access your own employee data"
                }), 403

            g.current_user = current_user
            return route_function(*args, **kwargs)

        return wrapper

    return decorator
