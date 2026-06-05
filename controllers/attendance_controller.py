from datetime import datetime, timezone

from models.attendance_model import (
    create_attendance,
    get_all_attendance,
    get_attendance_by_id,
    update_attendance,
)

ALLOWED_ATTENDANCE_UPDATE_FIELDS = {"check_in", "check_out", "status", "working_hours"}


def format_attendance_record(record_id, record):
    return {
        "id": record_id,
        **record
    }


def find_today_attendance(employee_id):
    today = datetime.now(timezone.utc).date().isoformat()
    records = get_all_attendance()

    for record_id, record in records.items():
        if record.get("employee_id") == employee_id and record.get("date") == today:
            return record_id, record

    return None, None


def check_in_employee(employee_id):
    if not employee_id:
        raise ValueError("employee_id is required")

    record_id, record = find_today_attendance(employee_id)

    if record:
        raise ValueError("employee already checked in today")

    now = datetime.now(timezone.utc)
    attendance_data = {
        "employee_id": employee_id,
        "date": now.date().isoformat(),
        "check_in": now.isoformat(),
        "check_out": None,
        "status": "present",
        "working_hours": 0
    }

    new_attendance_ref = create_attendance(attendance_data)
    return format_attendance_record(new_attendance_ref.key, attendance_data)


def check_out_employee(employee_id):
    if not employee_id:
        raise ValueError("employee_id is required")

    record_id, record = find_today_attendance(employee_id)

    if not record:
        raise ValueError("employee has not checked in today")

    if record.get("check_out"):
        raise ValueError("employee already checked out today")

    now = datetime.now(timezone.utc)
    check_in_time = datetime.fromisoformat(record["check_in"])
    working_hours = round((now - check_in_time).total_seconds() / 3600, 2)

    updates = {
        "check_out": now.isoformat(),
        "working_hours": working_hours,
        "status": "completed"
    }

    update_attendance(record_id, updates)
    record.update(updates)

    return format_attendance_record(record_id, record)


def get_all_attendance_records():
    records = get_all_attendance()

    return [
        format_attendance_record(record_id, record)
        for record_id, record in records.items()
    ]


def get_employee_attendance_records(employee_id):
    if not employee_id:
        raise ValueError("employee_id is required")

    records = get_all_attendance()

    return [
        format_attendance_record(record_id, record)
        for record_id, record in records.items()
        if record.get("employee_id") == employee_id
    ]


def get_today_attendance_record(employee_id):
    if not employee_id:
        raise ValueError("employee_id is required")

    record_id, record = find_today_attendance(employee_id)

    if not record:
        raise ValueError("attendance record not found for today")

    return format_attendance_record(record_id, record)


def update_attendance_record(attendance_id, data):
    if not attendance_id:
        raise ValueError("attendance_id is required")

    updates = {
        key: value
        for key, value in (data or {}).items()
        if key in ALLOWED_ATTENDANCE_UPDATE_FIELDS
    }

    if not updates:
        raise ValueError("provide at least one valid field to update")

    record = get_attendance_by_id(attendance_id)

    if not record:
        raise ValueError("attendance record not found")

    update_attendance(attendance_id, updates)
    record.update(updates)

    return format_attendance_record(attendance_id, record)
