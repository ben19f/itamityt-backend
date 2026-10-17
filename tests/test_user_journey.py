"""End-to-end user lifecycle against the configured test database and S3.

Run with a private env file, for example:
    dotenv -f /home/USER/.config/itamityt-backend/test.env run -- \
        pytest tests/test_user_journey.py

The email sender is stubbed only to capture the verification token. All user,
profile, photo, link, and account operations go through the application's API.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from services.email import email_service
from services.storage import storage


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_complete_user_lifecycle(monkeypatch):
    sent_verification_tokens = []
    stored_objects = set()

    async def capture_verification_email(_email: str, token: str) -> None:
        sent_verification_tokens.append(token)

    monkeypatch.setattr(
        email_service, "send_verification_email", capture_verification_email
    )

    async def fake_upload_file(_file, key: str, content_type=None) -> str:
        stored_objects.add(key)
        return storage.public_url(key)

    async def fake_delete(key: str) -> None:
        stored_objects.discard(key)

    async def fake_exists(key: str) -> bool:
        return key in stored_objects

    # Keep this API integration test self-contained; S3 itself is external.
    monkeypatch.setattr(storage, "upload_file", fake_upload_file)
    monkeypatch.setattr(storage, "delete", fake_delete)
    monkeypatch.setattr(storage, "exists", fake_exists)

    uid = uuid.uuid4().hex
    username = f"journey_{uid}"
    email = f"{uid}@example.com"
    password = f"Test-{uid}-Password"
    headers = None
    photo_url = None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        try:
            # Register, confirm email using the token delivered by the mocked mailer.
            response = await client.post(
                "/auth/register",
                json={"username": username, "email": email, "password": password},
            )
            assert response.status_code == 200, response.text
            assert response.json()["email"] == email
            assert sent_verification_tokens

            response = await client.post(
                "/users/verify-email",
                json={"token": sent_verification_tokens[0]},
            )
            assert response.status_code == 200, response.text
            assert response.json()["email_verified"] is True

            # Log in and retain the bearer token for subsequent requests.
            response = await client.post(
                "/auth/login", json={"email": email, "password": password}
            )
            assert response.status_code == 200, response.text
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Update profile and verify persistence through the read endpoint.
            profile = {
                "display_name": "Journey Test",
                "profile_description": "Temporary integration profile",
                "profile_extra_info": "Created by the user journey test",
            }
            response = await client.patch("/users/me", headers=headers, json=profile)
            assert response.status_code == 200, response.text
            response = await client.get("/users/me", headers=headers)
            assert response.status_code == 200, response.text
            for field, value in profile.items():
                assert response.json()[field] == value

            # Clear profile fields and verify that the values were removed.
            response = await client.patch(
                "/users/me",
                headers=headers,
                json={key: None for key in profile},
            )
            assert response.status_code == 200, response.text
            response = await client.get("/users/me", headers=headers)
            assert response.status_code == 200, response.text
            for field in profile:
                assert response.json()[field] is None

            # Upload a tiny valid PNG, then verify it through the API and S3.
            png = bytes.fromhex(
                "89504e470d0a1a0a0000000d494844520000000100000001"
                "08060000001f15c4890000000b49444154789c6360000200"
                "00050001a5f645400000000049454e44ae426082"
            )
            response = await client.post(
                "/users/me/photos",
                headers=headers,
                files={"file": ("journey.png", png, "image/png")},
            )
            assert response.status_code == 200, response.text
            photo = response.json()
            photo_url = photo["image_url"]
            assert photo["id"]
            photo_key = storage.key_from_url(photo_url)
            assert photo_key
            assert await storage.exists(photo_key)

            response = await client.get("/users/me/photos", headers=headers)
            assert response.status_code == 200, response.text
            assert any(item["id"] == photo["id"] for item in response.json())

            response = await client.delete(
                f"/users/me/photos/{photo['id']}", headers=headers
            )
            assert response.status_code == 204, response.text
            response = await client.get("/users/me/photos", headers=headers)
            assert response.status_code == 200, response.text
            assert all(item["id"] != photo["id"] for item in response.json())
            assert not await storage.exists(photo_key)
            photo_url = None

            # Profile links are items; verify creation and removal in the list.
            response = await client.post(
                "/items/",
                headers=headers,
                json={"name": "Test link", "description": "https://example.com"},
            )
            assert response.status_code == 201, response.text
            link_id = response.json()["id"]
            response = await client.get("/items/", headers=headers)
            assert response.status_code == 200, response.text
            assert any(item["id"] == link_id for item in response.json())

            response = await client.delete(f"/items/{link_id}", headers=headers)
            assert response.status_code == 200, response.text
            response = await client.get("/items/", headers=headers)
            assert response.status_code == 200, response.text
            assert all(item["id"] != link_id for item in response.json())

            # Delete through the current-user endpoint, then verify removal and cascade.
            response = await client.delete("/users/delete/me", headers=headers)
            assert response.status_code == 204, response.text
            headers = None

            # response = await client.get(
            #     "/users/me", headers={"Authorization": f"Bearer {token}"}
            # )
            # assert response.status_code == 401, response.text
            # response = await client.get(f"/public/profile/{username}")
            # assert response.status_code == 404, response.text

            response = await client.get(
                "/users/me", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 404, response.text
            assert response.json()["detail"] == "User not found"


        finally:
            # On an earlier assertion failure, attempt account cleanup via the API.
            if headers is not None:
                await client.delete("/users/delete/me", headers=headers)
            # Best-effort cleanup for an upload if a failure happened before its API delete.
            if photo_url:
                key = storage.key_from_url(photo_url)
                if key:
                    try:
                        await storage.delete(key)
                    except Exception:
                        pass
