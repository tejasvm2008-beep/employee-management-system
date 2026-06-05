from firebase.firebase_config import database


def get_leave_ref():
    if database is None:
        raise RuntimeError("Firebase database is not initialized")

    return database.reference("leave_applications")


def get_all_leaves():
    return get_leave_ref().get() or {}


def get_leave_by_id(leave_id):
    return get_leave_ref().child(leave_id).get()


def create_leave(leave_data):
    return get_leave_ref().push(leave_data)


def update_leave(leave_id, updates):
    get_leave_ref().child(leave_id).update(updates)
