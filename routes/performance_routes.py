from flask import Blueprint, jsonify, request

from controllers.performance_controller import (
    calculate_performance_summary,
    create_or_update_performance_review,
    get_all_performance_reviews,
    get_employee_performance_reviews,
)
from middleware.auth_middleware import employee_or_role_required, role_required

performance_routes = Blueprint("performance_routes", __name__)


@performance_routes.get("/performance/summary/<employee_id>")
@employee_or_role_required(lambda *args, **kwargs: kwargs.get("employee_id"), "manager", "admin")
def get_performance_summary(employee_id):
    year = request.args.get("year")
    month = request.args.get("month")

    try:
        summary = calculate_performance_summary(employee_id, year, month)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "performance summary fetched successfully",
        "summary": summary
    }), 200


@performance_routes.post("/performance/review")
@role_required("manager", "admin")
def create_performance_review():
    data = request.get_json() or {}

    try:
        review = create_or_update_performance_review(
            data.get("employee_id"),
            data.get("year"),
            data.get("month"),
            data.get("manager_rating"),
            data.get("manager_comment")
        )
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "performance review saved successfully",
        "review": review
    }), 200


@performance_routes.get("/performance/reviews")
@role_required("manager", "admin")
def get_all_reviews():
    try:
        reviews = get_all_performance_reviews()
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "performance reviews fetched successfully",
        "reviews": reviews
    }), 200


@performance_routes.get("/performance/reviews/<employee_id>")
@employee_or_role_required(lambda *args, **kwargs: kwargs.get("employee_id"), "manager", "admin")
def get_employee_reviews(employee_id):
    try:
        reviews = get_employee_performance_reviews(employee_id)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 500

    return jsonify({
        "message": "employee performance reviews fetched successfully",
        "reviews": reviews
    }), 200
