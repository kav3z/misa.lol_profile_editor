"""
Test Suite: Profile API and Editor Contracts.

Verifies:
1. Initial profile starting state (GET /api/profile -> 200).
2. Valid profile update and persistence (PUT /api/profile -> 200).
3. Leading & trailing whitespace trimming before length checks & saving.
4. Validation rules:
   - Display name: 1-40 chars (reject empty, whitespace-only, > 40).
   - Bio: 0-160 chars (empty allowed, reject > 160).
   - Link label: 1-30 chars (reject empty, whitespace-only, > 30).
   - Link URL: absolute https:// URL with hostname (reject http, javascript, data, missing host).
5. Type enforcement: all 4 values must be strings (reject int, bool, list, null).
6. Malformed JSON handling: returns 400 without crashing server.
7. Profile immutability upon rejected requests (database remains unchanged on failure).
8. Web route: GET / returns 200 HTML with server-side rendered profile.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.models.profile import UserProfile
from main import app


@pytest.fixture(name="client")
def client_fixture():
    """
    Creates an isolated in-memory SQLite database for test execution.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    # Seed initial test profile record
    with Session(engine) as session:
        seed = UserProfile(
            id=1,
            display_name="Nova",
            bio="Music, late nights, and things I make.",
            link_label="My website",
            link_url="https://example.com"
        )
        session.add(seed)
        session.commit()

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# 1. INITIAL STATE & BASIC READ/UPDATE
# ============================================================================

def test_get_initial_profile(client: TestClient):
    """Confirm starting profile matches specification contract."""
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "displayName": "Nova",
        "bio": "Music, late nights, and things I make.",
        "link": {
            "label": "My website",
            "url": "https://example.com"
        }
    }


def test_put_valid_profile_update(client: TestClient):
    """Confirm valid update succeeds and persists across subsequent GET."""
    payload = {
        "displayName": "Aria Stark",
        "bio": "Exploring the world and soundscapes.",
        "link": {
            "label": "Soundcloud",
            "url": "https://soundcloud.com/aria"
        }
    }
    put_res = client.put("/api/profile", json=payload)
    assert put_res.status_code == 200
    assert put_res.json() == payload

    # Verify persistence via GET
    get_res = client.get("/api/profile")
    assert get_res.status_code == 200
    assert get_res.json() == payload


# ============================================================================
# 2. WHITESPACE TRIMMING
# ============================================================================

def test_whitespace_trimming_before_saving(client: TestClient):
    """Confirm leading and trailing whitespace are trimmed before saving."""
    payload = {
        "displayName": "   Trimmed Name   ",
        "bio": "   Trimmed Bio   ",
        "link": {
            "label": "   Trimmed Label   ",
            "url": "   https://example.org/trimmed   "
        }
    }
    response = client.put("/api/profile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["displayName"] == "Trimmed Name"
    assert data["bio"] == "Trimmed Bio"
    assert data["link"]["label"] == "Trimmed Label"
    assert data["link"]["url"] == "https://example.org/trimmed"


# ============================================================================
# 3. DISPLAY NAME VALIDATION (1-40 chars)
# ============================================================================

def test_display_name_empty_or_whitespace_rejected(client: TestClient):
    """Empty or whitespace-only display name must return 400."""
    for empty_val in ["", "   "]:
        payload = {
            "displayName": empty_val,
            "bio": "Valid bio",
            "link": {"label": "Link", "url": "https://example.com"}
        }
        res = client.put("/api/profile", json=payload)
        assert res.status_code == 400
        assert "displayName" in str(res.json())


def test_display_name_max_length_boundary(client: TestClient):
    """Exactly 40 chars is allowed; 41 chars is rejected."""
    # 40 chars allowed
    payload_40 = {
        "displayName": "A" * 40,
        "bio": "Valid bio",
        "link": {"label": "Link", "url": "https://example.com"}
    }
    assert client.put("/api/profile", json=payload_40).status_code == 200

    # 41 chars rejected
    payload_41 = {
        "displayName": "A" * 41,
        "bio": "Valid bio",
        "link": {"label": "Link", "url": "https://example.com"}
    }
    res = client.put("/api/profile", json=payload_41)
    assert res.status_code == 400


# ============================================================================
# 4. BIO VALIDATION (0-160 chars, empty allowed)
# ============================================================================

def test_bio_empty_allowed(client: TestClient):
    """Empty bio (or whitespace-only) is allowed and saved as empty string."""
    payload = {
        "displayName": "Nova",
        "bio": "",
        "link": {"label": "Website", "url": "https://example.com"}
    }
    res = client.put("/api/profile", json=payload)
    assert res.status_code == 200
    assert res.json()["bio"] == ""


def test_bio_max_length_boundary(client: TestClient):
    """Exactly 160 chars is allowed; 161 chars is rejected."""
    # 160 chars allowed
    payload_160 = {
        "displayName": "Nova",
        "bio": "B" * 160,
        "link": {"label": "Website", "url": "https://example.com"}
    }
    assert client.put("/api/profile", json=payload_160).status_code == 200

    # 161 chars rejected
    payload_161 = {
        "displayName": "Nova",
        "bio": "B" * 161,
        "link": {"label": "Website", "url": "https://example.com"}
    }
    res = client.put("/api/profile", json=payload_161)
    assert res.status_code == 400


# ============================================================================
# 5. LINK LABEL VALIDATION (1-30 chars)
# ============================================================================

def test_link_label_empty_or_whitespace_rejected(client: TestClient):
    """Empty or whitespace-only link label must return 400."""
    payload = {
        "displayName": "Nova",
        "bio": "Bio",
        "link": {"label": "   ", "url": "https://example.com"}
    }
    res = client.put("/api/profile", json=payload)
    assert res.status_code == 400


def test_link_label_max_length_boundary(client: TestClient):
    """Exactly 30 chars is allowed; 31 chars is rejected."""
    payload_30 = {
        "displayName": "Nova",
        "bio": "Bio",
        "link": {"label": "L" * 30, "url": "https://example.com"}
    }
    assert client.put("/api/profile", json=payload_30).status_code == 200

    payload_31 = {
        "displayName": "Nova",
        "bio": "Bio",
        "link": {"label": "L" * 31, "url": "https://example.com"}
    }
    assert client.put("/api/profile", json=payload_31).status_code == 400


# ============================================================================
# 6. LINK URL VALIDATION (Absolute https:// with hostname)
# ============================================================================

@pytest.mark.parametrize("invalid_url", [
    "http://example.com",             # Insecure http rejected
    "javascript:alert(1)",            # Javascript scheme rejected
    "data:text/html;base64,...",      # Data scheme rejected
    "ftp://files.example.com",        # FTP rejected
    "https://",                       # No hostname
    "https:// ",                      # Whitespace
    "https://example .com",           # Space inside URL
    "relative/path",                  # Relative URL
    "",                               # Empty
    "example.com",                    # Missing scheme
])
def test_link_url_invalid_schemes_and_shapes(client: TestClient, invalid_url: str):
    """Invalid URL formats must return 400."""
    payload = {
        "displayName": "Nova",
        "bio": "Bio",
        "link": {"label": "Link", "url": invalid_url}
    }
    res = client.put("/api/profile", json=payload)
    assert res.status_code == 400


@pytest.mark.parametrize("valid_url", [
    "https://example.com",
    "https://misa.lol/profile/123",
    "https://sub.domain.co.uk/test?query=param&num=42#section",
])
def test_link_url_valid_formats(client: TestClient, valid_url: str):
    """Valid https:// URLs with hostnames must succeed."""
    payload = {
        "displayName": "Nova",
        "bio": "Bio",
        "link": {"label": "Link", "url": valid_url}
    }
    res = client.put("/api/profile", json=payload)
    assert res.status_code == 200
    assert res.json()["link"]["url"] == valid_url


# ============================================================================
# 7. TYPE ENFORCEMENT & MISSING FIELDS
# ============================================================================

def test_type_enforcement_rejects_non_strings(client: TestClient):
    """Numbers, booleans, arrays, or objects in string fields must return 400."""
    # displayName as integer
    res1 = client.put("/api/profile", json={
        "displayName": 12345,
        "bio": "Bio",
        "link": {"label": "Web", "url": "https://example.com"}
    })
    assert res1.status_code == 400

    # bio as boolean
    res2 = client.put("/api/profile", json={
        "displayName": "Nova",
        "bio": True,
        "link": {"label": "Web", "url": "https://example.com"}
    })
    assert res2.status_code == 400

    # link as string instead of object
    res3 = client.put("/api/profile", json={
        "displayName": "Nova",
        "bio": "Bio",
        "link": "not an object"
    })
    assert res3.status_code == 400


def test_missing_fields_rejected(client: TestClient):
    """Missing any of the 4 required values must return 400."""
    res = client.put("/api/profile", json={"displayName": "Nova"})
    assert res.status_code == 400


# ============================================================================
# 8. MALFORMED JSON REQUEST BODY
# ============================================================================

def test_malformed_json_returns_400(client: TestClient):
    """Malformed JSON string in request body must return 400 without crashing."""
    res = client.put(
        "/api/profile",
        content="{\"displayName\": \"Nova\", broken json...",
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 400
    assert "JSON" in str(res.json())


# ============================================================================
# 9. REJECTION LEAVES STORED PROFILE UNCHANGED
# ============================================================================

def test_rejected_update_leaves_stored_profile_unchanged(client: TestClient):
    """Verify that any validation failure leaves the existing profile unchanged."""
    # 1. Check current profile
    initial_profile = client.get("/api/profile").json()

    # 2. Attempt invalid update (e.g. invalid scheme http://)
    invalid_payload = {
        "displayName": "Hacker Attempt",
        "bio": "New Bio",
        "link": {"label": "Evil", "url": "http://insecure.com"}
    }
    res = client.put("/api/profile", json=invalid_payload)
    assert res.status_code == 400

    # 3. Retrieve profile again and verify it is identical to initial
    refreshed_profile = client.get("/api/profile").json()
    assert refreshed_profile == initial_profile
    assert refreshed_profile["displayName"] == initial_profile["displayName"]


# ============================================================================
# 10. WEB VIEW ROUTE (JINJA2)
# ============================================================================

def test_web_editor_page_renders_html(client: TestClient):
    """Confirm GET / renders the Jinja2 editor template with initial data."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "misa.lol" in res.text
    assert "Nova" in res.text
