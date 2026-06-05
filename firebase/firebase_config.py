import firebase_admin
from firebase_admin import credentials, firestore, db
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SERVICE_ACCOUNT_PATH = BASE_DIR / "serivce_account_key.json"
DATABASE_URL = "https://employee-management-syst-e6369-default-rtdb.asia-southeast1.firebasedatabase.app/"


try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))
        firebase_admin.initialize_app(cred, {
            "databaseURL": DATABASE_URL
        })

    database = db
    firestore_db = firestore.client()
    print("firebase initialized")
except Exception as error:
    print(f"there is something wrong in firebase initialized: {error}")
    database = None
    firestore_db = None

