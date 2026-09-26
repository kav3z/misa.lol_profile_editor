# misa.lol — Profile Editor (Full-Stack Assessment)

A standalone mini profile editor built with **FastAPI**, **SQLModel**, and **Jinja2 Templates**, following a clean **MVC (Model-View-Controller)** architecture.

---

## 🏗️ Architecture & Project Structure (MVC)

The codebase is organized cleanly according to the MVC pattern:

```text
misa.lol/
├── app/
│   ├── config.py              # Application settings, database path, initial seed data
│   ├── database.py            # SQLModel engine, session dependency, database initialization
│   ├── models/                # [MODEL LAYER]
│   │   ├── __init__.py
│   │   └── profile.py         # SQLModel database entity (UserProfile) & Pydantic DTOs (ProfilePayload)
│   ├── controllers/           # [CONTROLLER LAYER]
│   │   ├── __init__.py
│   │   ├── api_controller.py  # REST API endpoints (GET /api/profile, PUT /api/profile)
│   │   └── web_controller.py  # Web view endpoint rendering Jinja2 template (GET /)
│   └── views/                 # [VIEW LAYER]
│       ├── templates/
│       │   ├── base.html      # Base HTML layout
│       │   └── editor.html    # Profile editor interface and live preview card
│       └── static/
│           ├── css/
│           │   └── style.css  # Modern, responsive, accessible dark styling
│           └── js/
│               └── editor.js  # Live typing preview, client-side validation, AJAX save
├── tests/
│   ├── __init__.py
│   └── test_profile_api.py    # 27 automated tests covering all contracts & edge cases
├── main.py                    # Application factory, lifespan, custom 400 validation handlers
├── requirements.txt           # Project dependencies
└── README.md                  # Assessment documentation and walkthrough notes
```

---

## ⚙️ Requirements & Installation

- **Runtime:** Python 3.10+ (Tested on Python 3.13)
- **Dependencies:** `fastapi`, `uvicorn`, `sqlmodel`, `jinja2`, `pydantic`, `pytest`, `httpx`

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
*(or using uv: `uv pip install -r requirements.txt`)*

### 2. Run the Application
```bash
uvicorn main:app --reload
```
Open your browser at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### 3. Run Automated Tests
```bash
pytest -v
```
*(All 27 automated tests verify starting state, valid updates, whitespace trimming, boundary limits, URL validation, type rejection, malformed JSON, and immutability on failure).*

## ⏱️ Time Spent & Completion Status

- **Approximate time spent:** ~55 minutes total (10 min setup & design, 30 min implementation, 15 min verification & testing).
- **What works:** 100% of all required features (load & edit, live safe preview, valid/invalid link states, save with pending/disabled state, backend persistence, strict server validation, and custom HTTP 400 error handling).
- **Anything unfinished:** None. Everything specified in the assessment is fully implemented and tested.
- **Starter code:** None. Built from scratch with FastAPI, SQLModel, and Jinja2.

---

## 🎯 What Works & Implementation Summary

- **Initial State:** Starts seeded with:
  ```json
  {
    "displayName": "Nova",
    "bio": "Music, late nights, and things I make.",
    "link": {
      "label": "My website",
      "url": "https://example.com"
    }
  }
  ```
- **Live Preview:**
  - Updates display name, bio, avatar initial, and link button in real time as the user types.
  - Safe rendering: Content is strictly treated as plain text (`textContent`), preventing XSS and HTML injection.
  - **Live URL validity check:** A valid `https://` URL enables the clickable link. An invalid or non-https URL immediately swaps to a disabled, non-clickable state.
- **Saving & State Handling:**
  - Submits via `PUT /api/profile`.
  - Disables save button and displays spinner while pending to prevent double-submissions.
  - Displays green success notification only after `200 OK` server response.
  - Failed saves preserve user inputs on screen and highlight specific field errors.
- **Persistence Across Browser Refresh:**
  - Backed by SQLModel with SQLite (`misa_profile.db`).
  - Refreshing the browser loads and renders the saved profile directly from the backend.
- **Strict Server Validation (Contract Compliance):**
  - All four fields are strictly enforced as strings (`StrictStr`), rejecting integers, booleans, and arrays with HTTP 400.
  - Strips leading and trailing whitespace prior to length calculations and saving.
  - `displayName`: 1–40 characters after trimming.
  - `bio`: 0–160 characters after trimming (empty bio allowed).
  - `link.label`: 1–30 characters after trimming.
  - `link.url`: Must be absolute `https://` with a valid hostname. Other schemes (`http:`, `javascript:`, `data:`) and missing hostnames are rejected with HTTP 400.
  - Malformed JSON is caught by a custom exception handler and returns HTTP 400 instead of crashing or returning 422/500.
  - **Immutability on Failure:** Any validation failure leaves the stored profile unchanged.

---

## 🧪 Verification Results

### 1. Successful Save & Browser Refresh Check
1. Start server: `uvicorn main:app --reload`.
2. Open `http://127.0.0.1:8000`. Form loads with `Nova`.
3. Change fields:
   - Display Name: `Nova Explorer`
   - Bio: `Creating sounds and code.`
   - Link Label: `GitHub`
   - Link URL: `https://github.com/nova`
4. Click **"Save Profile"**.
5. Save spinner displays, followed by `"Profile saved successfully!"`.
6. Press `F5` / Refresh the browser page.
7. **Result:** All updated values are immediately loaded and rendered from the server database.

### 2. Invalid API Request Verification (Profile Remains Unchanged)
Using PowerShell, curl, or Python:
```bash
curl -X PUT http://127.0.0.1:8000/api/profile `
  -H "Content-Type: application/json" `
  -d '{"displayName": "Attacker", "bio": "Bad", "link": {"label": "Evil", "url": "http://insecure.com"}}'
```
**Response:**
```json
HTTP/1.1 400 Bad Request
{
  "error": "Validation Error",
  "message": "The submitted profile data failed validation.",
  "details": [
    {
      "field": "link.url",
      "message": "Link URL must be an absolute URL starting with 'https://'. Other schemes (http, javascript, data) are rejected.",
      "type": "value_error"
    }
  ]
}
```
Querying `GET http://127.0.0.1:8000/api/profile` confirms the stored profile remains completely unchanged.

---

## ⚖️ Implementation Tradeoffs & Production Improvements

- **Tradeoff made for this exercise:**
  - A single-record table (`id=1`) was used in SQLModel to adhere to the single-profile trial scope without unnecessary authentication or multi-tenant complexity.
- **First thing to improve for production:**
  - **Multi-tenancy & User Authentication:** Introduce user accounts with JWT/session-based auth and foreign keys linking profiles to `user_id`, permitting multiple users and usernames/handles (e.g. `misa.lol/{username}`).
  - **Rate Limiting & CSRF:** Add rate-limiting middleware (such as `slowapi`) to mitigate automated spam on `PUT /api/profile` and add CSRF token verification for form submissions.

---

## 🛠️ Tools Used
- **Stack:** Python 3.13, FastAPI, SQLModel, Jinja2, Uvicorn, Pytest.
- **AI Assistant:** Antigravity (Google DeepMind) used for scaffolding tests, refining validation logic against edge-case schemes, and styling.
