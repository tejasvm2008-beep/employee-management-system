from firebase.firebase_config import database


def get_users_ref():
    if database is None:
        raise RuntimeError("Firebase database is not initialized")

    return database.reference("users")


def get_all_users():
    users = get_users_ref().get() or {}

    if not isinstance(users, dict):
        return {}

    return {
        user_id: user
        for user_id, user in users.items()
        if isinstance(user, dict)
    }


def get_user_by_id(user_id):
    user = get_users_ref().child(user_id).get()

    if not isinstance(user, dict):
        return None

    return user


def find_user_by_name(name):
    if not name:
        return None, None

    normalized = name.strip().lower()
    exact_match = None, None
    partial_matches = []

    for user_id, user in get_all_users().items():
        user_name = (user.get("name") or "").strip()
        if not user_name:
            continue
        if user_name.lower() == normalized:
            return user_id, user
        if normalized in user_name.lower():
            partial_matches.append((user_id, user))

    if len(partial_matches) == 1:
        return partial_matches[0]

    return None, None


def find_user_by_email(email):
    if not email:
        return None, None

    normalized_email = email.strip().lower()

    for user_id, user in get_all_users().items():
        if user.get("email") == normalized_email:
            return user_id, user

    return None, None


def create_user(user_data):
    return get_users_ref().push(user_data)


def update_user(user_id, updates):
    get_users_ref().child(user_id).update(updates)
