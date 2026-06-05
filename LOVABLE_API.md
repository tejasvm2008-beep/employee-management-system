# Employee Management System — API for Lovable UI

Use this document to generate a React frontend (Lovable) that talks to the Flask REST API.

## Base URL

| Environment | URL |
|-------------|-----|
| Local dev | `http://127.0.0.1:5000` |
| Production | Set your deployed Flask/Gunicorn URL |

Start backend locally:

```bash
cd employee_management_system
source .venv/bin/activate
python app.py
```

---

## Authentication

Protected routes require:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

Login/register responses include:

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT-like signed token (24h expiry) |
| `token_type` | `"Bearer"` | Always Bearer |
| `expires_in` | number | `86400` seconds |
| `user.id` | string | Firebase user ID — use as `employee_id` everywhere |
| `user.role` | string | `employee` \| `manager` \| `admin` |
| `user.approval_status` | string | Managers: `pending` until admin approves |
| `user.is_active` | boolean | Managers inactive until approved |

Store `access_token` and `user` in app state (localStorage/session). Attach token to every protected request.

---

## Roles & suggested screens

| Role | Screens |
|------|---------|
| **Employee** | Login, Register, Dashboard, Check-in/out, My attendance, Apply leave, My leaves, Leave balance, Performance summary |
| **Manager** | Same as employee (after approval) + All attendance, All leaves, Approve/reject leave, Performance reviews |
| **Admin** | Admin login, Manager approval queue, All attendance/leaves/reviews, Edit attendance |

---

## API endpoints (verified with curl)

### Health

```bash
curl -s http://127.0.0.1:5000/health
```

**Response `200`:**

```json
{
  "message": "server is running"
}
```

---

### Auth — Public

#### Register (employee or manager)

`POST /register`

```bash
curl -s -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@company.com",
    "password": "SecurePass123",
    "role": "employee"
  }'
```

| Body field | Required | Notes |
|------------|----------|-------|
| `name` | yes | |
| `email` | yes | Normalized to lowercase |
| `password` | yes | |
| `role` | no | Default `employee`. Allowed: `employee`, `manager` |

**Response `200` (employee):**

```json
{
  "message": "User registered successfully",
  "user": {
    "id": "-OuG1VBJkN_iJa6T4fkb",
    "name": "Test Employee",
    "email": "emp@test.com",
    "role": "employee",
    "approval_status": "approved",
    "is_active": true
  }
}
```

**Manager registration:** `approval_status: "pending"`, `is_active: false` — cannot login until admin approves.

**Errors:** `400` — validation (e.g. email already registered, invalid role)

---

#### Login

`POST /login`

```bash
curl -s -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "jane@company.com", "password": "SecurePass123"}'
```

**Response `200`:**

```json
{
  "message": "login successful",
  "access_token": "<token>",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": "-OuG1VBJkN_iJa6T4fkb",
    "name": "Jane Doe",
    "email": "jane@company.com",
    "role": "employee",
    "approval_status": "approved",
    "is_active": true
  }
}
```

**Errors:**

| Status | Message example |
|--------|-----------------|
| `400` | `invalid email or password` |
| `400` | `manager account is waiting for admin approval` |
| `400` | `account is not active` |

---

#### Admin register

`POST /admin/register` — only `admin@gmail.com`

```bash
curl -s -X POST http://127.0.0.1:5000/admin/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Admin", "email": "admin@gmail.com", "password": "YourAdminPass"}'
```

**Response `201`** — same user shape as register, `role: "admin"`.

---

#### Admin login

`POST /admin/login`

```bash
curl -s -X POST http://127.0.0.1:5000/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@gmail.com", "password": "YourAdminPass"}'
```

Same response shape as `/login`.

---

### Auth — Protected

#### Reset password

`PATCH /forgot-password` — requires Bearer token

- Employees/managers: can only reset **their own** email.
- Admin: can reset any user.

```bash
curl -s -X PATCH http://127.0.0.1:5000/forgot-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"email": "jane@company.com", "new_password": "NewPass456!"}'
```

**Response `200`:**

```json
{
  "message": "password reset successfully",
  "user": {
    "id": "-OuG1VBJkN_iJa6T4fkb",
    "name": "Jane Doe",
    "email": "jane@company.com"
  }
}
```

---

#### List manager approval requests

`GET /admin/manager-requests` — **admin only**

```bash
curl -s http://127.0.0.1:5000/admin/manager-requests \
  -H "Authorization: Bearer <admin_token>"
```

**Response `200`:**

```json
{
  "message": "manager approval requests fetched successfully",
  "managers": [
    {
      "id": "-OuG1VHe-C3CI40KA5VZ",
      "name": "Test Manager",
      "email": "mgr@test.com",
      "role": "manager",
      "approval_status": "pending",
      "is_active": false,
      "created_at": "2026-06-04T05:10:12.000000+00:00"
    }
  ]
}
```

---

#### Approve / reject manager

`PATCH /admin/manager-requests/<user_id>` — **admin only**

```bash
curl -s -X PATCH http://127.0.0.1:5000/admin/manager-requests/-OuG1VHe-C3CI40KA5VZ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"approval_status": "approved"}'
```

| `approval_status` | Effect |
|-------------------|--------|
| `approved` | Manager can login (`is_active: true`) |
| `rejected` | Manager blocked |
| `pending` | Waiting state |

**Response `200`:** `{ "message": "...", "manager": { ... } }`

---

## Attendance

`employee_id` in requests = logged-in `user.id` from login.

### Check in

`POST /attendance/check-in` — employee (own id), manager, admin

```bash
curl -s -X POST http://127.0.0.1:5000/attendance/check-in \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"employee_id": "-OuG1VBJkN_iJa6T4fkb"}'
```

**Response `201`:**

```json
{
  "message": "check-in successful",
  "attendance": {
    "id": "-OuG1VTdRmD60cMZ7Xnz",
    "employee_id": "-OuG1VBJkN_iJa6T4fkb",
    "date": "2026-06-04",
    "check_in": "2026-06-04T05:10:14.083073+00:00",
    "check_out": null,
    "status": "present",
    "working_hours": 0
  }
}
```

**Errors:** `400` — `employee already checked in today`

---

### Check out

`PATCH /attendance/check-out`

```bash
curl -s -X PATCH http://127.0.0.1:5000/attendance/check-out \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"employee_id": "-OuG1VBJkN_iJa6T4fkb"}'
```

**Response `200`:**

```json
{
  "message": "check-out successful",
  "attendance": {
    "id": "-OuG1VTdRmD60cMZ7Xnz",
    "employee_id": "-OuG1VBJkN_iJa6T4fkb",
    "date": "2026-06-04",
    "check_in": "2026-06-04T05:10:14.083073+00:00",
    "check_out": "2026-06-04T05:10:38.684077+00:00",
    "status": "completed",
    "working_hours": 0.01
  }
}
```

---

### Today's attendance

`GET /attendance/today/<employee_id>` — own id or manager/admin

```bash
curl -s http://127.0.0.1:5000/attendance/today/-OuG1VBJkN_iJa6T4fkb \
  -H "Authorization: Bearer <token>"
```

**Response `200`:** `{ "message": "...", "attendance": { ... } }`  
**Response `404`:** no record for today

---

### Employee attendance history

`GET /attendance/<employee_id>`

```bash
curl -s http://127.0.0.1:5000/attendance/-OuG1VBJkN_iJa6T4fkb \
  -H "Authorization: Bearer <token>"
```

**Response `200`:**

```json
{
  "message": "employee attendance fetched successfully",
  "attendance": [
    {
      "id": "-OuG1VTdRmD60cMZ7Xnz",
      "employee_id": "-OuG1VBJkN_iJa6T4fkb",
      "date": "2026-06-04",
      "check_in": "...",
      "check_out": "...",
      "status": "completed",
      "working_hours": 0.01
    }
  ]
}
```

---

### All attendance (manager/admin)

`GET /attendance`

```bash
curl -s http://127.0.0.1:5000/attendance \
  -H "Authorization: Bearer <manager_or_admin_token>"
```

**Response `200`:** `{ "message": "...", "attendance": [ ... ] }`

---

### Update attendance record (manager/admin)

`PATCH /attendance/<attendance_id>`

Allowed body fields: `check_in`, `check_out`, `status`, `working_hours`

```bash
curl -s -X PATCH http://127.0.0.1:5000/attendance/-OuG1VTdRmD60cMZ7Xnz \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <manager_token>" \
  -d '{"status": "completed", "working_hours": 8}'
```

---

## Leave

### Leave types

| Code | Meaning | Balance tracked |
|------|---------|-----------------|
| `CL` | Casual leave | Yes (16/year) |
| `EL` | Earned leave | Yes (accrues monthly) |
| `OH` | Optional holiday | Yes (2/year) |
| `WFH` | Work from home | No |
| `OD` | On duty | No |

Statuses: `pending`, `approved`, `rejected`

---

### Apply for leave

`POST /leave/apply`

```bash
curl -s -X POST http://127.0.0.1:5000/leave/apply \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "employee_id": "-OuG1VBJkN_iJa6T4fkb",
    "leave_type": "CL",
    "start_date": "2026-06-10",
    "end_date": "2026-06-11",
    "reason": "Personal"
  }'
```

Dates: `YYYY-MM-DD`

**Response `201`:**

```json
{
  "message": "leave application submitted successfully",
  "leave": {
    "id": "-OuG1VhETEtKmgF-zJ1D",
    "employee_id": "-OuG1VBJkN_iJa6T4fkb",
    "leave_type": "CL",
    "start_date": "2026-06-10",
    "end_date": "2026-06-11",
    "days": 2,
    "reason": "Personal",
    "status": "pending",
    "applied_at": "2026-06-04T05:10:14.987104+00:00",
    "updated_at": null
  }
}
```

---

### Leave balance

`GET /leave/balance/<employee_id>?year=2026`

```bash
curl -s "http://127.0.0.1:5000/leave/balance/-OuG1VBJkN_iJa6T4fkb?year=2026" \
  -H "Authorization: Bearer <token>"
```

**Response `200`:**

```json
{
  "message": "leave balance fetched successfully",
  "balance": {
    "employee_id": "-OuG1VBJkN_iJa6T4fkb",
    "year": 2026,
    "balances": {
      "CL": {
        "available": 16,
        "approved": 0,
        "pending": 2,
        "remaining": 14
      },
      "EL": {
        "available": 6,
        "approved": 0,
        "pending": 0,
        "remaining": 6
      },
      "OH": {
        "available": 2,
        "approved": 0,
        "pending": 0,
        "remaining": 2
      }
    },
    "untracked_leave_types": ["WFH", "OD"]
  }
}
```

---

### My leave applications

`GET /leave/employee/<employee_id>`

```bash
curl -s http://127.0.0.1:5000/leave/employee/-OuG1VBJkN_iJa6T4fkb \
  -H "Authorization: Bearer <token>"
```

**Response `200`:** `{ "message": "...", "leaves": [ ... ] }`

---

### All leave applications (manager/admin)

`GET /leave`

```bash
curl -s http://127.0.0.1:5000/leave \
  -H "Authorization: Bearer <manager_token>"
```

---

### Single leave by ID (manager/admin)

`GET /leave/<leave_id>`

---

### Update leave status (manager/admin)

`PATCH /leave/<leave_id>/status`

```bash
curl -s -X PATCH http://127.0.0.1:5000/leave/-OuG1VhETEtKmgF-zJ1D/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <manager_token>" \
  -d '{"status": "approved", "manager_comment": "Approved"}'
```

---

## Performance

### Monthly summary (computed from completed attendance)

`GET /performance/summary/<employee_id>?year=2026&month=6`

```bash
curl -s "http://127.0.0.1:5000/performance/summary/-OuG1VBJkN_iJa6T4fkb?year=2026&month=6" \
  -H "Authorization: Bearer <token>"
```

**Response `200`:**

```json
{
  "message": "performance summary fetched successfully",
  "summary": {
    "employee_id": "-OuG1VBJkN_iJa6T4fkb",
    "year": 2026,
    "month": 6,
    "working_days": 0,
    "standard_daily_hours": 8,
    "expected_hours": 0,
    "total_working_hours": 0,
    "average_daily_hours": 0,
    "extra_hours": 0,
    "short_hours": 0,
    "extra_hour_score": 0,
    "performance_label": "satisfactory"
  }
}
```

`performance_label`: `excellent` | `good` | `satisfactory` | `needs_attention`

---

### Create/update performance review (manager/admin)

`POST /performance/review`

```bash
curl -s -X POST http://127.0.0.1:5000/performance/review \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <manager_token>" \
  -d '{
    "employee_id": "-OuG1VBJkN_iJa6T4fkb",
    "year": 2026,
    "month": 6,
    "manager_rating": 4,
    "manager_comment": "Good month"
  }'
```

---

### All reviews (manager/admin)

`GET /performance/reviews`

---

### Employee reviews

`GET /performance/reviews/<employee_id>`

---

## HTTP status codes (common)

| Code | When |
|------|------|
| `200` | Success |
| `201` | Created (check-in, leave apply, admin register) |
| `400` | Validation / business rule error |
| `401` | Missing or invalid token |
| `403` | Wrong role or accessing another employee's data |
| `404` | Resource not found |
| `500` | Server / Firebase error |

Error body shape:

```json
{
  "message": "human readable error"
}
```

---

## Lovable implementation notes

### API client pattern

```typescript
const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:5000";

async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("access_token");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message ?? "Request failed");
  return data as T;
}
```

### Route guards (frontend)

| Route pattern | Allowed roles |
|---------------|---------------|
| `/login`, `/register` | Public |
| `/admin/*` | `admin` |
| `/manager/*` | `manager`, `admin` |
| `/employee/*` | `employee`, `manager`, `admin` |

After login, redirect by `user.role`. Block manager UI if `approval_status !== "approved"`.

### Key UX flows

1. **Register** → optional auto-login → employee dashboard  
2. **Manager register** → show “Pending admin approval” (login will fail with message)  
3. **Admin** → manager requests table → Approve/Reject → manager can login  
4. **Daily** → Check-in button → Check-out button → show `working_hours`  
5. **Leave** → form with type + date range → show balance cards (CL/EL/OH)  
6. **Manager** → pending leaves list → approve/reject with comment  

### Environment variable for Lovable

```
VITE_API_URL=http://127.0.0.1:5000
```

Enable CORS on Flask if the UI runs on a different origin (add `flask-cors` or proxy in dev).

---

## Quick test script

Save as `test-api.sh` and run while `python app.py` is up:

```bash
#!/bin/bash
BASE="http://127.0.0.1:5000"
curl -s "$BASE/health" | jq .
# Register + login + check-in flow — see curl examples above
```

---

*Generated from live curl tests against the Flask API on 2026-06-04.*
