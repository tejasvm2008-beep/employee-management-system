import os
from datetime import datetime, timezone

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from models.employee_model import (
    create_user,
    find_user_by_email,
    get_all_users,
    get_user_by_id,
    update_user,
)

ACCESS_TOKEN_MAX_AGE = 24 * 60 * 60
ADMIN_EMAIL = "admin@gmail.com"
PUBLIC_REGISTRATION_ROLES = {"employee", "manager"}
VALID_ROLES = {"employee", "manager", "admin"}
MANAGER_APPROVAL_STATUSES = {"pending", "approved", "rejected"}


def generate_access_token(user_id, email, role):
    serializer = URLSafeTimedSerializer(
        os.environ.get("ACCESS_TOKEN_SECRET", "dev-access-token-secret")
    )
    return serializer.dumps({
        "user_id": user_id,
        "email": email,
        "role": role,
        "type": "access"
    })


def verify_access_token(access_token):
    serializer = URLSafeTimedSerializer(
        os.environ.get("ACCESS_TOKEN_SECRET", "dev-access-token-secret")
    )

    try:
        payload = serializer.loads(access_token, max_age=ACCESS_TOKEN_MAX_AGE)
    except SignatureExpired as error:
        raise ValueError("access token has expired") from error
    except BadSignature as error:
        raise ValueError("invalid access token") from error

    if payload.get("type") != "access":
        raise ValueError("invalid access token")

    if payload.get("role") not in VALID_ROLES:
        raise ValueError("invalid access token role")

    user = get_user_by_id(payload.get("user_id", ""))

    if not user:
        raise ValueError("user account no longer exists")

    email = user.get("email")
    role = user.get("role", "employee")
    if email == ADMIN_EMAIL:
        role = "admin"

    if role != payload.get("role"):
        raise ValueError("access token role is no longer valid")

    approval_status = user.get("approval_status", "approved")
    is_active = user.get("is_active", True)

    if role == "manager" and approval_status != "approved":
        raise ValueError("manager account is not approved")

    if not is_active:
        raise ValueError("account is not active")

    return {
        **payload,
        "email": email,
        "role": role,
        "approval_status": approval_status,
        "is_active": is_active
    }


def registration(name, email, password, role="employee"):
    if not name or not email or not password:
        raise ValueError("name, email and password are required")

    normalized_email = email.strip().lower()
    normalized_role = (role or "employee").strip().lower()

    if normalized_role not in PUBLIC_REGISTRATION_ROLES:
        raise ValueError("role must be employee or manager")

    _, existing_user = find_user_by_email(normalized_email)
    if existing_user:
        raise ValueError("email is already registered")

    approval_status = "approved"
    is_active = True
    if normalized_role == "manager":
        approval_status = "pending"
        is_active = False

    user_data = {
        "name": name.strip(),
        "email": normalized_email,
        "role": normalized_role,
        "approval_status": approval_status,
        "is_active": is_active,
        "password": generate_password_hash(password),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    new_user_ref = create_user(user_data)

    return {
        "id": new_user_ref.key,
        "name": user_data["name"],
        "email": user_data["email"],
        "role": user_data["role"],
        "approval_status": user_data["approval_status"],
        "is_active": user_data["is_active"]
    }


def register_admin(name, email, password):
    if not name or not email or not password:
        raise ValueError("name, email and password are required")

    normalized_email = email.strip().lower()

    if normalized_email != ADMIN_EMAIL:
        raise ValueError("only admin@gmail.com can register as admin")

    _, existing_user = find_user_by_email(normalized_email)
    if existing_user:
        raise ValueError("admin email is already registered")

    user_data = {
        "name": name.strip(),
        "email": normalized_email,
        "role": "admin",
        "approval_status": "approved",
        "is_active": True,
        "password": generate_password_hash(password),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    new_user_ref = create_user(user_data)

    return {
        "id": new_user_ref.key,
        "name": user_data["name"],
        "email": user_data["email"],
        "role": user_data["role"],
        "approval_status": user_data["approval_status"],
        "is_active": user_data["is_active"]
    }


def login_user(email, password):
    if not email or not password:
        raise ValueError("email and password are required")

    normalized_email = email.strip().lower()
    user_id, user = find_user_by_email(normalized_email)

    if user:
        if not check_password_hash(user.get("password", ""), password):
            raise ValueError("invalid email or password")

        role = user.get("role", "employee")
        if user.get("email") == ADMIN_EMAIL:
            role = "admin"

        if role not in VALID_ROLES:
            role = "employee"

        approval_status = user.get("approval_status", "approved")
        is_active = user.get("is_active", True)

        if role == "manager" and approval_status != "approved":
            raise ValueError("manager account is waiting for admin approval")

        if not is_active:
            raise ValueError("account is not active")

        access_token = generate_access_token(user_id, user.get("email"), role)

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_TOKEN_MAX_AGE,
            "user": {
                "id": user_id,
                "name": user.get("name"),
                "email": user.get("email"),
                "role": role,
                "approval_status": approval_status,
                "is_active": is_active
            }
        }

    raise ValueError("invalid email or password")


def login_admin(email, password):
    if not email or not password:
        raise ValueError("email and password are required")

    normalized_email = email.strip().lower()

    if normalized_email != ADMIN_EMAIL:
        raise ValueError("invalid admin credentials")

    return login_user(normalized_email, password)


def reset_password(email, new_password):
    if not email or not new_password:
        raise ValueError("email and new_password are required")

    normalized_email = email.strip().lower()
    user_id, user = find_user_by_email(normalized_email)
    if user:
        update_user(user_id, {
            "password": generate_password_hash(new_password),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

        return {
            "id": user_id,
            "name": user.get("name"),
            "email": user.get("email")
        }

    raise ValueError("email is not registered")


def get_employees_list():
    users = get_all_users()

    return [
        {
            "id": user_id,
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
        }
        for user_id, user in users.items()
        if user.get("role") in {"employee", "manager"}
        and user.get("is_active", True)
        and (
            user.get("role") != "manager"
            or user.get("approval_status", "approved") == "approved"
        )
    ]


def get_manager_approval_requests():
    users = get_all_users()

    return [
        {
            "id": user_id,
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "approval_status": user.get("approval_status", "approved"),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at")
        }
        for user_id, user in users.items()
        if user.get("role") == "manager"
    ]


def update_manager_approval(user_id, approval_status):
    if not user_id:
        raise ValueError("user_id is required")

    normalized_status = (approval_status or "").strip().lower()
    if normalized_status not in MANAGER_APPROVAL_STATUSES:
        raise ValueError("approval_status must be pending, approved or rejected")

    user = get_user_by_id(user_id)

    if not user:
        raise ValueError("user not found")

    if user.get("role") != "manager":
        raise ValueError("only manager accounts can be approved or rejected")

    updates = {
        "approval_status": normalized_status,
        "is_active": normalized_status == "approved",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    update_user(user_id, updates)
    user.update(updates)

    return {
        "id": user_id,
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "approval_status": user.get("approval_status"),
        "is_active": user.get("is_active")
    }
