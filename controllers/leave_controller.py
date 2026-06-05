from datetime import date, datetime, timezone

from models.leave_model import (
    create_leave,
    get_all_leaves,
    get_leave_by_id,
    update_leave,
)

ALLOWED_LEAVE_TYPES = {"CL", "EL", "OH", "WFH", "OD"}
ALLOWED_LEAVE_STATUSES = {"pending", "approved", "rejected"}
TRACKED_LEAVE_TYPES = {"CL", "EL", "OH"}
CL_ANNUAL_LIMIT = 16
OH_ANNUAL_LIMIT = 2


def format_leave_record(leave_id, leave):
    return {
        "id": leave_id,
        **leave
    }


def normalize_leave_type(leave_type):
    return (leave_type or "").strip().upper()


def parse_leave_date(value, field_name):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format") from error


def calculate_leave_days(start_date, end_date):
    start = parse_leave_date(start_date, "start_date")
    end = parse_leave_date(end_date, "end_date")

    if end < start:
        raise ValueError("end_date cannot be before start_date")

    return (end - start).days + 1


def date_ranges_overlap(first_start, first_end, second_start, second_end):
    return first_start <= second_end and second_start <= first_end


def get_year_from_start_date(start_date):
    return parse_leave_date(start_date, "start_date").year


def get_leave_entitlement(leave_type, year=None):
    current_year = datetime.now(timezone.utc).year
    current_month = datetime.now(timezone.utc).month
    target_year = year or current_year

    if leave_type == "CL":
        return CL_ANNUAL_LIMIT

    if leave_type == "EL":
        if target_year < current_year:
            return 12
        if target_year > current_year:
            return 0
        return current_month

    if leave_type == "OH":
        return OH_ANNUAL_LIMIT

    return None


def calculate_employee_leave_usage(employee_id, year):
    leaves = get_all_leaves()
    usage = {
        leave_type: {
            "approved": 0,
            "pending": 0,
            "available": get_leave_entitlement(leave_type, year)
        }
        for leave_type in TRACKED_LEAVE_TYPES
    }

    for leave in leaves.values():
        leave_type = leave.get("leave_type")
        status = leave.get("status")

        if (
            leave.get("employee_id") != employee_id
            or leave_type not in TRACKED_LEAVE_TYPES
            or status not in {"pending", "approved"}
        ):
            continue

        try:
            leave_year = get_year_from_start_date(leave.get("start_date"))
        except ValueError:
            continue

        if leave_year != year:
            continue

        days = int(leave.get("days", 0))
        usage[leave_type][status] += days

    for leave_type, leave_usage in usage.items():
        leave_usage["remaining"] = (
            leave_usage["available"]
            - leave_usage["approved"]
            - leave_usage["pending"]
        )

    return usage


def validate_leave_balance(employee_id, leave_type, start_date, days):
    if leave_type not in TRACKED_LEAVE_TYPES:
        return

    year = get_year_from_start_date(start_date)
    usage = calculate_employee_leave_usage(employee_id, year)
    leave_usage = usage[leave_type]

    if days > leave_usage["remaining"]:
        raise ValueError(
            f"not enough {leave_type} balance. "
            f"available: {leave_usage['available']}, "
            f"approved: {leave_usage['approved']}, "
            f"pending: {leave_usage['pending']}, "
            f"remaining: {leave_usage['remaining']}"
        )


def validate_no_approved_leave_overlap(employee_id, leave_type, start_date, end_date):
    new_start = parse_leave_date(start_date, "start_date")
    new_end = parse_leave_date(end_date, "end_date")
    leaves = get_all_leaves()

    for leave in leaves.values():
        if (
            leave.get("employee_id") != employee_id
            or leave.get("status") != "approved"
        ):
            continue

        try:
            existing_start = parse_leave_date(leave.get("start_date"), "start_date")
            existing_end = parse_leave_date(leave.get("end_date"), "end_date")
        except ValueError:
            continue

        if date_ranges_overlap(new_start, new_end, existing_start, existing_end):
            existing_leave_type = leave.get("leave_type")
            if existing_leave_type == leave_type:
                raise ValueError(
                    f"{existing_leave_type} leave is already approved for this date"
                )

            raise ValueError(
                f"{existing_leave_type} leave is already approved for this date. "
                "employee cannot apply another leave type for the same day"
            )


def apply_leave(employee_id, leave_type, start_date, end_date, reason=None):
    if not employee_id:
        raise ValueError("employee_id is required")

    normalized_leave_type = normalize_leave_type(leave_type)
    if normalized_leave_type not in ALLOWED_LEAVE_TYPES:
        raise ValueError("leave_type must be CL, EL, OH, WFH or OD")

    if not start_date or not end_date:
        raise ValueError("start_date and end_date are required")

    days = calculate_leave_days(start_date, end_date)
    validate_no_approved_leave_overlap(
        employee_id,
        normalized_leave_type,
        start_date,
        end_date
    )
    validate_leave_balance(employee_id, normalized_leave_type, start_date, days)

    leave_data = {
        "employee_id": employee_id,
        "leave_type": normalized_leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "reason": reason,
        "status": "pending",
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }

    new_leave_ref = create_leave(leave_data)
    return format_leave_record(new_leave_ref.key, leave_data)


def get_all_leave_applications():
    leaves = get_all_leaves()

    return [
        format_leave_record(leave_id, leave)
        for leave_id, leave in leaves.items()
    ]


def get_employee_leave_applications(employee_id):
    if not employee_id:
        raise ValueError("employee_id is required")

    leaves = get_all_leaves()

    return [
        format_leave_record(leave_id, leave)
        for leave_id, leave in leaves.items()
        if leave.get("employee_id") == employee_id
    ]


def get_leave_application(leave_id):
    if not leave_id:
        raise ValueError("leave_id is required")

    leave = get_leave_by_id(leave_id)
    if not leave:
        raise ValueError("leave application not found")

    return format_leave_record(leave_id, leave)


def get_leave_balance(employee_id, year=None):
    if not employee_id:
        raise ValueError("employee_id is required")

    selected_year = int(year) if year else datetime.now(timezone.utc).year

    return {
        "employee_id": employee_id,
        "year": selected_year,
        "balances": calculate_employee_leave_usage(employee_id, selected_year),
        "untracked_leave_types": ["WFH", "OD"]
    }


def update_leave_status(leave_id, status, manager_comment=None):
    if not leave_id:
        raise ValueError("leave_id is required")

    normalized_status = (status or "").strip().lower()
    if normalized_status not in ALLOWED_LEAVE_STATUSES:
        raise ValueError("status must be pending, approved or rejected")

    leave = get_leave_by_id(leave_id)

    if not leave:
        raise ValueError("leave application not found")

    updates = {
        "status": normalized_status,
        "manager_comment": manager_comment,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    update_leave(leave_id, updates)
    leave.update(updates)

    return format_leave_record(leave_id, leave)
