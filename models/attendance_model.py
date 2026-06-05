from firebase.firebase_config import database


def get_attendance_ref():
    if database is None:
        raise RuntimeError("Firebase database is not initialized")

    return database.reference("attendance")


def get_all_attendance():
    return get_attendance_ref().get() or {}


def get_attendance_by_id(attendance_id):
    return get_attendance_ref().child(attendance_id).get()


def create_attendance(attendance_data):
    return get_attendance_ref().push(attendance_data)


def update_attendance(attendance_id, updates):
    get_attendance_ref().child(attendance_id).update(updates)
