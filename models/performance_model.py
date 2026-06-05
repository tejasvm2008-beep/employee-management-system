from firebase.firebase_config import database


def get_performance_ref():
    if database is None:
        raise RuntimeError("Firebase database is not initialized")

    return database.reference("performance_reviews")


def get_all_performance_reviews():
    return get_performance_ref().get() or {}


def create_performance_review(review_data):
    return get_performance_ref().push(review_data)


def update_performance_review(review_id, updates):
    get_performance_ref().child(review_id).update(updates)
