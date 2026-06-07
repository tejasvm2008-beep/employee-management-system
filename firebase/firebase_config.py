import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, db
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SERVICE_ACCOUNT_PATH = BASE_DIR / "serivce_account_key.json"
DATABASE_URL = "https://employee-management-syst-e6369-default-rtdb.asia-southeast1.firebasedatabase.app/"


try:
    if not firebase_admin._apps:
        # Load credentials dynamically from an environment variable if set (e.g. on Render)
        firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
        if firebase_creds_json:
            try:
                creds_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(creds_dict)
                print("Firebase initialized using credentials from environment variable")
            except Exception as json_err:
                print(f"Error parsing FIREBASE_CREDENTIALS env var, falling back to file: {json_err}")
                cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))
        else:
            cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))
            print("Firebase initialized using local service_account_key.json")

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

