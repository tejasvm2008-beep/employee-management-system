import os

from flask import Flask, jsonify
from flask_cors import CORS

from routes.attendance_routes import attendance_routes
from routes.auth_routes import auth_routes
from routes.leave_applyroutes import leave_routes
from routes.performance_routes import performance_routes

app = Flask(__name__)


def _cors_origins():
    """Allow Vite dev server on localhost, 127.0.0.1, and private LAN IPs."""
    origins = [
        r"http://localhost(:\d+)?",
        r"http://127\.0\.0\.1(:\d+)?",
        r"http://192\.168\.\d{1,3}\.\d{1,3}(:\d+)?",
        r"http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?",
        r"http://172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}(:\d+)?",
    ]
    extra = os.environ.get("CORS_ORIGINS", "")
    for origin in extra.split(","):
        origin = origin.strip()
        if origin:
            origins.append(origin)
    return origins


CORS(
    app,
    origins=_cors_origins(),
    allow_headers=["Content-Type", "Authorization"],
)
app.register_blueprint(auth_routes)
app.register_blueprint(attendance_routes)
app.register_blueprint(leave_routes)
app.register_blueprint(performance_routes)


@app.get("/health")
def health():
    return jsonify({"message": "server is running"}), 200


if __name__ == "__main__":
    app.run(debug=True)
