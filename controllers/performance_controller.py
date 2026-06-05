from datetime import datetime, timezone

from models.attendance_model import get_all_attendance
from models.performance_model import (
    create_performance_review,
    get_all_performance_reviews as get_all_performance_review_records,
    update_performance_review,
)

STANDARD_DAILY_HOURS = 8
EXTRA_HOUR_SCORE_WEIGHT = 2
MAX_EXTRA_HOUR_SCORE = 40


def format_performance_record(record_id, record):
    return {
        "id": record_id,
        **record
    }


def parse_year_month(year, month):
    try:
        parsed_year = int(year)
        parsed_month = int(month)
    except (TypeError, ValueError) as error:
        raise ValueError("year and month must be numbers") from error

    if parsed_month < 1 or parsed_month > 12:
        raise ValueError("month must be between 1 and 12")

    return parsed_year, parsed_month


def is_record_in_month(record, year, month):
    record_date = record.get("date")
    if not record_date:
        return False

    try:
        attendance_date = datetime.fromisoformat(record_date).date()
    except ValueError:
        return False

    return attendance_date.year == year and attendance_date.month == month


def get_completed_monthly_attendance(employee_id, year, month):
    records = get_all_attendance()

    return [
        record
        for record in records.values()
        if (
            record.get("employee_id") == employee_id
            and record.get("status") == "completed"
            and is_record_in_month(record, year, month)
        )
    ]


def calculate_performance_summary(employee_id, year, month):
    if not employee_id:
        raise ValueError("employee_id is required")

    parsed_year, parsed_month = parse_year_month(year, month)
    attendance_records = get_completed_monthly_attendance(
        employee_id,
        parsed_year,
        parsed_month
    )

    working_days = len(attendance_records)
    total_working_hours = round(
        sum(float(record.get("working_hours", 0)) for record in attendance_records),
        2
    )
    expected_hours = working_days * STANDARD_DAILY_HOURS
    extra_hours = round(
        sum(
            max(float(record.get("working_hours", 0)) - STANDARD_DAILY_HOURS, 0)
            for record in attendance_records
        ),
        2
    )
    short_hours = round(
        sum(
            max(STANDARD_DAILY_HOURS - float(record.get("working_hours", 0)), 0)
            for record in attendance_records
        ),
        2
    )
    average_daily_hours = (
        round(total_working_hours / working_days, 2)
        if working_days
        else 0
    )
    extra_hour_score = min(
        round(extra_hours * EXTRA_HOUR_SCORE_WEIGHT, 2),
        MAX_EXTRA_HOUR_SCORE
    )

    if extra_hours >= 20:
        performance_label = "excellent"
    elif extra_hours >= 10:
        performance_label = "good"
    elif short_hours > 10:
        performance_label = "needs_attention"
    else:
        performance_label = "satisfactory"

    return {
        "employee_id": employee_id,
        "year": parsed_year,
        "month": parsed_month,
        "working_days": working_days,
        "standard_daily_hours": STANDARD_DAILY_HOURS,
        "expected_hours": expected_hours,
        "total_working_hours": total_working_hours,
        "average_daily_hours": average_daily_hours,
        "extra_hours": extra_hours,
        "short_hours": short_hours,
        "extra_hour_score": extra_hour_score,
        "performance_label": performance_label
    }


def create_or_update_performance_review(
    employee_id,
    year,
    month,
    manager_rating=None,
    manager_comment=None
):
    summary = calculate_performance_summary(employee_id, year, month)
    reviews = get_all_performance_review_records()

    review_data = {
        **summary,
        "manager_rating": manager_rating,
        "manager_comment": manager_comment,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    for review_id, review in reviews.items():
        if (
            review.get("employee_id") == summary["employee_id"]
            and review.get("year") == summary["year"]
            and review.get("month") == summary["month"]
        ):
            update_performance_review(review_id, review_data)
            return format_performance_record(review_id, review_data)

    review_data["created_at"] = datetime.now(timezone.utc).isoformat()
    new_review_ref = create_performance_review(review_data)
    return format_performance_record(new_review_ref.key, review_data)


def get_employee_performance_reviews(employee_id):
    if not employee_id:
        raise ValueError("employee_id is required")

    reviews = get_all_performance_review_records()

    return [
        format_performance_record(review_id, review)
        for review_id, review in reviews.items()
        if review.get("employee_id") == employee_id
    ]


def get_all_performance_reviews():
    reviews = get_all_performance_review_records()

    return [
        format_performance_record(review_id, review)
        for review_id, review in reviews.items()
    ]
